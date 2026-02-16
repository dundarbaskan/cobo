"""
COBO WEBHOOK İŞLEYİCİ (Background Task)
========================================

Bu modül, Cobo platformundan gelen webhook bildirimlerini arka planda işler.
main.py'deki /cobo/callback endpoint'i bu modüldeki process_cobo_notification()
fonksiyonunu BackgroundTasks ile çağırır.

İŞ AKIŞI:
---------
1. Event tipi belirlenir (cüzdan/işlem)
2. İşlem filtreleri uygulanır (Tip, Token, Volume, İç Transfer)
3. Müşteri doğrulanır (MongoDB)
4. Kur çevirisi yapılır (converter.py)
5. Race condition koruması (try_lock_transaction)
6. Finansal istatistikler güncellenir
7. MT5'e bakiye eklenir
8. Telegram bildirimi gönderilir

BAĞIMLILIKLAR:
--------------
- servisler.db_service (MongoDB işlemleri)
- servisler.telegram_service (Bildirimler)
- config.settings (MT5 manager instance)
- config.constants (ALLOWED_TOKENS, BLOCKED_TYPES)
- core.filter.base_volume_filter (Hacim filtresi)
- core.currency.converter.converter (Kur çevirisi)
"""

import logging
import asyncio
from servisler.db_service import (
    get_lead_by_address,
    try_lock_transaction,
    increment_deposit_count,
    update_financial_stats,
    get_all_our_addresses
)
from servisler.telegram_service import send_telegram_msg
from config.settings import get_mt5_manager
from config.constants import ALLOWED_TOKENS, BLOCKED_TYPES, get_display_chain_name
from core.currency.converter.converter import coin_parser
from core.filter.base_volume_filter import BaseVolumeFilter

logger = logging.getLogger(__name__)

async def process_cobo_notification(data: dict):
    """
    Cobo webhook bildirimlerini arka planda işleyen asenkron fonksiyon

    Args:
        data: Cobo webhook payload
    """
    try:
        logger.info(f"🔄 Arka plan işlemi başlatıldı: {data.get('event_id', 'unknown')}")

        # Cobo uses 'type' not 'event_type'
        event_type = data.get("type") or data.get("event_type")

        # Wallet creation notification
        if event_type == "wallets.addresses.created":
            await _handle_wallet_created(data)

        # Transaction events
        elif event_type in [
            "TRANSACTION", "transaction.created", "transaction.deposit",
            "transaction.success", "wallets.transaction.created",
            "wallets.transaction.updated", "wallets.transaction.succeeded",
            "wallets.transactions.created", "wallets.transactions.updated"
        ]:
            await _handle_transaction(data)

        else:
            logger.info(f"ℹ️ Diğer event type: {event_type}")

    except Exception as e:
        logger.error(f"❌ Arka plan işlem hatası: {e}")
        import traceback
        traceback.print_exc()


async def _handle_wallet_created(data: dict):
    """
    Cüzdan oluşturma bildirimlerini işler
    """
    addresses = data.get("data", {}).get("addresses", [])
    for addr_data in addresses:
        address = addr_data.get("address")
        chain = addr_data.get("chain_id")

        # Bu adresi hangi kullanıcı için oluşturduk?
        lead = await get_lead_by_address(address)
        if lead:
            tp = lead.get("tp_number")
            name = lead.get("name", "Bilinmeyen")

            # Asset bilgisini cüzdan listesinden bul
            asset = "USDT"  # Varsayılan
            for w in lead.get("wallets", []):
                if w.get("address") == address:
                    asset = w.get("asset", "USDT")
                    break

            # Ağ ismini güzelleştir
            display_chain = get_display_chain_name(chain)

            msg = (
                f"🆕 <b>CÜZDAN OLUŞTURULDU</b>\n\n"
                f"👤 <b>Müşteri:</b> {name}\n"
                f"🔑 <b>TP:</b> <code>{tp}</code>\n"
                f"💵 <b>Varlık:</b> {asset}\n"
                f"🌐 <b>Ağ:</b> {display_chain}\n"
                f"📍 <b>Adres:</b> <code>{address}</code>"
            )
            send_telegram_msg(msg)
            logger.info(f"✅ Cüzdan bildirimi: {name} (TP: {tp}) - {asset} {chain}")


async def _handle_transaction(data: dict):
    """
    İşlem (transaction) bildirimlerini işler
    """
    tx = data.get("data", {})
    if "transaction" in tx:
        tx = tx["transaction"]

    transaction_id = tx.get("transaction_id") or data.get("event_id")
    status = tx.get("status", "").upper()

    # Veri çekme mantığı
    address = tx.get("to_address") or tx.get("destination", {}).get("address")
    from_address = tx.get("from_address") or tx.get("source", {}).get("address")

    amount_str = tx.get("amount") or tx.get("destination", {}).get("amount")
    amount = float(amount_str) if amount_str else 0
    symbol = tx.get("token_id") or tx.get("coin_code") or tx.get("asset_id")
    chain_id = tx.get("chain_id", "Unknown")
    tx_type = tx.get("type", "").upper()

    if not address:
        return

    # FİLTRE 1: Tip kontrolü - Sadece DEPOSIT kabul et
    if tx_type in BLOCKED_TYPES or tx_type not in ["DEPOSIT", "RECEIVE"]:
        logger.info(f"⏭️ Engellenen işlem tipi: {tx_type} - {transaction_id}")
        return

    # FİLTRE 2: Gerçek coin kontrolü - Sadece bilinen coinleri kabul et
    token_upper = (symbol or "").upper()
    is_allowed = False
    for allowed in ALLOWED_TOKENS:
        if allowed in token_upper:
            is_allowed = True
            break

    if not is_allowed:
        logger.info(f"⏭️ Fake/Spam token engellendi: {symbol} - {transaction_id}")
        return

    # FİLTRE 3: Minimum tutar kontrolü - 1 USD altını engelle
    if await BaseVolumeFilter.should_block_transaction(symbol, amount, transaction_id):
        return

    # FİLTRE 4: İç transfer kontrolü - Kendi adreslerimizden gelenleri engelle
    if from_address:
        our_addresses = await get_all_our_addresses()
        if from_address in our_addresses:
            logger.info(f"⏭️ İç transfer engellendi (sweep/consolidation): {transaction_id}")
            return

    # Sadece başarılı işlemleri işle
    if status in ["COMPLETED", "SUCCESS", "CONFIRMED"]:
        await _process_successful_transaction(
            transaction_id, address, amount, symbol, chain_id, status
        )
    elif status == "CONFIRMING":
        logger.info(f"⏳ Ödeme tespit edildi (Onay bekleniyor): {transaction_id}")


async def _process_successful_transaction(
    transaction_id: str,
    address: str,
    amount: float,
    symbol: str,
    chain_id: str,
    status: str
):
    """
    Başarılı işlemleri işler: Müşteri bulma, kur çevirme, MT5 aktarım
    """
    # Müşteriyi bul
    lead = await get_lead_by_address(address)
    if not lead:
        logger.warning(f"⚠️ Bilinmeyen adrese deposit: {address} - Tx: {transaction_id}")
        return

    tp_number = lead.get("tp_number")
    name = lead.get("name", "Bilinmeyen")

    # Kur çevirisi
    original_amount = amount
    try:
        loop = asyncio.get_event_loop()
        cv_data = await loop.run_in_executor(None, coin_parser, symbol, amount)

        # 2. eleman her zaman USD'dir
        usd_record = cv_data[1]
        amount = float(usd_record['amount'])
        logger.info(f"💱 Kur Çevirisi Yapıldı: {original_amount} {symbol} -> {amount} USD")
    except Exception as e:
        logger.error(f"❌ Kur Çevirme Hatası ({symbol}): {e}")

    # Atomik kilit - Race condition koruması
    is_locked = await try_lock_transaction(transaction_id, tp_number, amount, symbol, status)
    if not is_locked:
        logger.info(f"⏭️ İşlem zaten işlenmiş (Race Condition Önlemi): {transaction_id}")
        return

    # Miktar formatla
    formatted_amount = "{:,.2f}".format(amount).replace(",", "X").replace(".", ",").replace("X", ".")
    formatted_raw_amount = "{:,.2f}".format(original_amount).replace(",", "X").replace(".", ",").replace("X", ".")

    # Finansal istatistikleri güncelle
    updated_lead = await update_financial_stats(tp_number, amount, is_deposit=True)
    tot_dep = updated_lead.get("total_deposit", 0)
    tot_with = updated_lead.get("total_withdrawal", 0)

    # Yatırım sayısını artır
    count = await increment_deposit_count(tp_number)
    base_comment = "DEPOSIT" if count == 1 else "DEPOSIT-2"

    # MT5 metadata çek
    city_code, acc_comment = await _fetch_mt5_metadata(tp_number)

    # Telegram bildirimi gönder
    msg = _build_deposit_telegram_message(
        name, symbol, chain_id, formatted_raw_amount,
        formatted_amount, tp_number, city_code, acc_comment,
        tot_dep, tot_with
    )
    send_telegram_msg(msg)

    # MT5'e bakiye ekle
    await _process_mt5_balance(tp_number, name, amount, base_comment, formatted_amount)


async def _fetch_mt5_metadata(tp_number: str) -> tuple:
    """
    MT5'ten City ve Comment bilgilerini çeker

    Returns:
        tuple: (city_code, acc_comment)
    """
    city_code = "N/A"
    acc_comment = "N/A"

    mt5_manager = get_mt5_manager()

    if mt5_manager.connect():
        try:
            user_info = mt5_manager.get_user_info(int(tp_number))
            if user_info:
                raw_city = user_info.get('city', 'N/A')
                city_code = raw_city[:3].upper() if raw_city and raw_city != 'N/A' else 'N/A'
                acc_comment = user_info.get('comment', 'N/A')
        finally:
            mt5_manager.disconnect()

    return city_code, acc_comment


def _build_deposit_telegram_message(
    name: str,
    symbol: str,
    chain_id: str,
    formatted_raw_amount: str,
    formatted_amount: str,
    tp_number: str,
    city_code: str,
    acc_comment: str,
    tot_dep: float,
    tot_with: float
) -> str:
    """
    Yatırım bildirimi Telegram mesajını oluşturur
    """
    return (
        f"🔥🔥💵 <b>KRİPTO YATIRIM</b> 💵🔥🔥\n"
        f"MOBİL UYGULAMA\n\n"
        f"<b>Ad Soyad:</b> {name.upper()}\n"
        f"<b>Coin:</b> {symbol.upper()}\n"
        f"<b>Ağ:</b> {chain_id.upper()}\n"
        f"<b>Gelen Tutar:</b> {formatted_raw_amount} {symbol.upper()}\n"
        f"<b>USD Değeri:</b> {formatted_amount} $\n\n"
        f"<b>Firma Adı:</b> CEP PORTFOY\n\n"
        f"<b>TP NUMBER :</b> <code>{tp_number}</code>\n"
        f"<b>Yatırım Uzmanı :</b> {city_code}\n"
        f"<b>Referans :</b> {acc_comment}\n"
        f"<b>Toplam Yatırım:</b> {tot_dep:,.2f}\n"
        f"<b>Toplam Çekim:</b> {tot_with:,.2f}"
    )


async def _process_mt5_balance(
    tp_number: str,
    name: str,
    amount: float,
    comment: str,
    formatted_amount: str
):
    """
    MT5'e bakiye ekler
    """
    mt5_manager = get_mt5_manager()

    if mt5_manager.connect():
        try:
            success = mt5_manager.add_balance(int(tp_number), float(amount), comment)
            if success:
                mt5_res = (
                    f"✅ <b>MT5 BAKİYE EKLENDİ</b>\n"
                    f"👤 {name}\n"
                    f"💰 {formatted_amount} $ (MT5 Aktarımı Başarılı)\n"
                    f"📝 Yorum: {comment}"
                )
                send_telegram_msg(mt5_res)
            else:
                send_telegram_msg(
                    f"❌ <b>MT5 İŞLEM HATASI</b>\n"
                    f"👤 {name}\n"
                    f"🔑 {tp_number}\n"
                    f"⚠️ Bakiye eklenemedi (Add Balance False)!"
                )
        except Exception as e:
            logger.error(f"MT5 Exception: {e}")
            send_telegram_msg(
                f"❌ <b>MT5 KOD HATASI</b>\n"
                f"👤 {name}\n"
                f"⚠️ Hata: {str(e)}"
            )
        finally:
            mt5_manager.disconnect()
    else:
        logger.error("MT5 Bağlantısı Başarısız!")
        send_telegram_msg(
            f"🚨 <b>KRİTİK HATA: MT5 BAĞLANAMADI</b>\n"
            f"👤 {name}\n"
            f"💰 {formatted_amount} $\n"
            f"⚠️ Para veritabanına işlendi ama MT5'e GEÇMEDİ! Manuel kontrol gerekli."
        )
