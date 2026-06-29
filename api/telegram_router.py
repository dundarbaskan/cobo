"""
Telegram Bot Komut API'si
=========================
Telegram bot handler'larından gelen komutları işler.

Komutlar:
- /sweep → Cobo wallet durum raporu oluşturur ve Telegram'a gönderir
- /admin → Admin panel linkini paylaşır

V2.0 Eklemeleri:
- POST /api/telegram_callback → MT5 onay/ret buton callback'lerini işler

Bağımlılıklar:
- servisler.sweep_service
- servisler.telegram_service
- config.settings
"""

import logging
from fastapi import APIRouter, Form
from servisler.sweep_service import CoboSweepService
from servisler.telegram_service import send_telegram_msg
from config.settings import COBO_WALLET_ID, APP_BASE_URL

# V2.0 - Onay/ret işlemleri için gerekli import'lar
from workers.pending_store import pending_transactions
from workers.webhook_processor import _process_mt5_balance
from core.comision.calculate_comision import COMISION_RATE

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Telegram"])


@router.post("/telegram_command")
async def telegram_command(command: str = Form(...)):
    """
    Telegram bot komutlarını işle
    """
    logger.info(f"📨 Telegram komutu alındı: {command}")

    try:
        if command.strip().lower() == "/sweep":
            return await _handle_sweep_command()

        elif command.strip().lower() == "/admin":
            return _handle_admin_command()

        else:
            return {"status": "error", "message": "Unknown command"}

    except Exception as e:
        logger.error(f"❌ Telegram command error: {e}")
        send_telegram_msg(f"❌ <b>KOMUT HATASI</b>\n⚠️ {str(e)}")
        return {"status": "error", "message": str(e)}


# V2.0 - MT5 onay/ret callback endpoint'i. Telegram bot CallbackQueryHandler bu endpoint'i çağırır.
@router.post("/telegram_callback")
async def telegram_callback(
    action: str = Form(...),
    transaction_id: str = Form(...)
):
    """
    Telegram inline butonu tıklamalarını işler.

    Args:
        action: 'approve' veya 'reject'
        transaction_id: pending_store'daki bekleyen işlem anahtarı
    """
    logger.info(f"📥 Telegram callback alındı: action={action}, tx={transaction_id}")

    # pending_store'dan işlem verisini al
    payload = pending_transactions.get(transaction_id)
    if not payload:
        logger.warning(f"⚠️ Bekleyen işlem bulunamadı: {transaction_id}")
        send_telegram_msg(
            f"⚠️ <b>İŞLEM BULUNAMADI</b>\n"
            f"<code>{transaction_id}</code>\n"
            f"<i>Süre dolmuş veya daha önce işlenmiş olabilir.</i>"
        )
        return {"status": "error", "message": "Pending transaction not found"}

    # İşlem verisini çıkart
    tp_number = payload["tp_number"]
    name = payload["name"]
    net_amount = payload["net_amount"]
    gross_amount = payload["gross_amount"]
    comision_amount = payload["comision_amount"]
    symbol = payload["symbol"]
    chain_id = payload["chain_id"]
    formatted_net = payload["formatted_net"]
    city_code = payload.get("city_code", "N/A")
    acc_comment = payload.get("acc_comment", "N/A")
    base_comment = payload.get("base_comment", "DEPOSIT")
    tot_dep = payload.get("tot_dep", 0)
    tot_with = payload.get("tot_with", 0)
    formatted_raw_amount = payload.get("formatted_raw_amount", "")

    if action == "approve":
        # MT5'e bakiye ekle
        await _process_mt5_balance(tp_number, name, net_amount, base_comment, formatted_net)
        # pending_store'dan temizle
        pending_transactions.pop(transaction_id, None)
        return {"status": "success", "message": "MT5 aktarımı başlatıldı"}

    elif action == "reject":
        # V2.0 - Formatlı ret mesajı şablonu
        reject_msg = (
            f"📋 <b>Meta işlemi RET Taslağı</b>\n\n"
            f"<b>İŞLEM TÜRÜ :</b> KRİPTO YATIRIM (MT5 AKTARIMI)\n"
            f"<b>YATIRIMCI :</b> {name.upper()}\n"
            f"<b>AĞ :</b> {symbol.upper()} - {chain_id.upper()}\n"
            f"<b>TUTAR :</b> {formatted_raw_amount} {symbol.upper()}\n"
            f"<b>USD DEĞERİ :</b> ${gross_amount:,.2f}\n"
            f"<b>KESİLEN KOMİSYON TUTARI ( %{COMISION_RATE}) :</b> ${comision_amount:,.2f}\n"
            f"<b>HESAPCI :</b> CEP PORTFOY / {acc_comment}\n"
            f"<b>İŞLEM NO :</b> TP-{tp_number}\n"
            f"<b>AÇIKLAMA :</b> {city_code} - "
            f"(Toplam Yatırım: {tot_dep:,.2f} / Çekim: {tot_with:,.2f})\n"
            f"<b>DURUM :</b> ❌ MT5 BAKİYE EKLENMEDİ"
        )
        send_telegram_msg(reject_msg)
        # pending_store'dan temizle
        pending_transactions.pop(transaction_id, None)
        return {"status": "success", "message": "İşlem reddedildi"}

    else:
        return {"status": "error", "message": f"Bilinmeyen aksiyon: {action}"}


async def _handle_sweep_command():
    """
    /sweep komutunu işler - Wallet durumunu gösterir
    """
    logger.info("🔍 /sweep komutu işleniyor...")
    sweep_service = CoboSweepService()

    logger.info(f"💼 Wallet ID: {COBO_WALLET_ID}")

    if not COBO_WALLET_ID:
        logger.error("❌ Wallet ID bulunamadı!")
        send_telegram_msg("❌ COBO_WALLET_ID .env dosyasında tanımlı değil!")
        return {"status": "error", "message": "Wallet ID not configured"}

    send_telegram_msg("🔍 <b>WALLET DURUMU KONTROL EDİLİYOR...</b>")

    try:
        # Wallet bilgilerini al
        wallet_info = sweep_service.get_wallet_info(COBO_WALLET_ID)

        if not wallet_info.get("success"):
            error_detail = wallet_info.get("error", "Bilinmeyen hata")
            send_telegram_msg(
                f"❌ <b>WALLET BİLGİSİ ALINAMADI</b>\n\n"
                f"⚠️ {error_detail}\n\n"
                f"💡 <i>API Key izinlerini kontrol edin "
                f"(Cobo Portal → Developer Console → API Keys)</i>"
            )
            return {"status": "error", "message": error_detail}

        # Son işlemleri listele
        transactions = sweep_service.list_transactions(COBO_WALLET_ID, limit=10)

        # Rapor oluştur
        msg = "📊 <b>COBO WALLET RAPORU</b>\n\n"
        msg += f"🆔 <b>Wallet ID:</b> <code>{COBO_WALLET_ID[:8]}...</code>\n"

        if wallet_info.get("data"):
            w_data = wallet_info["data"]
            msg += f"📛 <b>İsim:</b> {w_data.get('name', 'N/A')}\n"
            msg += f"🏷️ <b>Tip:</b> {w_data.get('wallet_type', 'N/A')}\n"

        # Son işlemler
        if transactions.get("success") and transactions.get("data"):
            tx_list = transactions["data"].get("data", [])
            if tx_list:
                msg += f"\n📝 <b>Son {len(tx_list)} İşlem:</b>\n"
                for tx in tx_list[:5]:  # İlk 5 işlem
                    tx_type = tx.get("type", "N/A")
                    amount = tx.get("amount", "0")
                    status = tx.get("status", "N/A")
                    msg += f"  • {tx_type}: {amount} ({status})\n"
            else:
                msg += "\n📝 <b>İşlem:</b> Henüz işlem yok\n"
        else:
            msg += "\n📝 <b>İşlemler:</b> Yüklenemedi\n"

        msg += "\n💡 <i>Auto Sweep Cobo Portal'da otomatik çalışıyor.</i>"

        send_telegram_msg(msg)
        return {"status": "success", "message": "Wallet info retrieved"}

    except Exception as e:
        error_msg = str(e)
        send_telegram_msg(
            f"❌ <b>HATA</b>\n"
            f"⚠️ {error_msg}\n\n"
            f"💡 <i>Detaylar için logları kontrol edin.</i>"
        )
        return {"status": "error", "message": error_msg}


def _handle_admin_command():
    """
    /admin komutunu işler - Admin panel linkini gönderir
    """
    admin_url = f"{APP_BASE_URL}/admin.html" if APP_BASE_URL else "/admin.html"
    msg = (
        f"🔑 <b>ADMİN PANEL ERİŞİMİ</b>\n\n"
        f"🌐 {admin_url}\n\n"
        f"💡 <i>Panel üzerinden para çekme ve istatistikleri yönetebilirsiniz.</i>"
    )
    send_telegram_msg(msg)
    return {"status": "success", "message": "Admin link sent"}


