"""
Onramper Entegrasyon Router'ı
=============================
- GET /api/onramper/widget-url: Kullanıcıya özel Onramper widget linki üretir.
- POST /api/onramper/callback: Onramper webhook bildirimlerini işler.
"""

import hmac
import hashlib
import urllib.parse
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
import urllib3
import cobo_waas2
from cobo_waas2 import ApiClient, Configuration, CreateAddressRequest

# InsecureRequestWarning uyarısını gizle
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config.settings import (
    ONRAMPER_API_KEY,
    ONRAMPER_SECRET_KEY,
    ONRAMPER_WIDGET_URL,
    COBO_API_KEY,
    COBO_API_SECRET,
    COBO_WALLET_ID,
    logger
)
from servisler.db_service import (
    get_lead_by_tp,
    get_lead_by_address,
    save_wallet_to_lead,
    get_existing_wallet
)
from servisler.telegram_service import send_telegram_msg
from servisler.mt5_sync_util import force_sync_single_user

router = APIRouter(prefix="/api/onramper", tags=["Onramper"])


async def _get_or_create_usdt_tron_wallet(tp_number: str) -> str:
    """
    Kullanıcının USDT (TRON) cüzdan adresini döner. Yoksa Cobo API üzerinden yeni oluşturur.
    """
    # 1. Mevcut cüzdanı kontrol et
    existing_wallet = await get_existing_wallet(tp_number, "USDT", "TRON")
    if existing_wallet:
        return existing_wallet.get("address")

    # 2. Cüzdan yoksa Cobo API ile oluştur
    try:
        configuration = Configuration(
            api_private_key=COBO_API_SECRET,
            host="https://api.cobo.com/v2"
        )
        configuration.verify_ssl = False

        with ApiClient(configuration) as api_client:
            api_client.set_default_header("Biz-Api-Key", COBO_API_KEY)
            api_instance = cobo_waas2.WalletsApi(api_client)

            req = CreateAddressRequest(chain_id="TRON", count=1)
            api_resp = api_instance.create_address(
                wallet_id=COBO_WALLET_ID,
                create_address_request=req
            )

            new_address = api_resp[0].address
            wallet_data = {
                "address": new_address,
                "chain_id": "TRON",
                "asset": "USDT",
                "created_at": datetime.now().isoformat()
            }

            await save_wallet_to_lead(tp_number, wallet_data)
            logger.info(f"✅ Onramper: Yeni USDT-TRON cüzdanı oluşturuldu (TP: {tp_number}, Adres: {new_address})")
            return new_address

    except Exception as e:
        logger.error(f"❌ Onramper: Cüzdan oluşturma hatası (TP: {tp_number}): {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Cüzdan oluşturma sırasında hata meydana geldi: {str(e)}"
        )


@router.get("/widget-url")
async def get_widget_url(tp_number: str):
    """
    Kullanıcı için imzalanmış Onramper Widget URL'si oluşturur ve Telegram bildirimini tetikler.
    """
    # 1. Kullanıcıyı veritabanından çek
    lead = await get_lead_by_tp(tp_number)
    
    if not lead:
        # Fallback: manuel senkronizasyon tetikle ve tekrar kontrol et
        sync_success = await force_sync_single_user(tp_number)
        if sync_success:
            lead = await get_lead_by_tp(tp_number)

    if not lead:
        raise HTTPException(status_code=404, detail="Kullanıcı (TP Number) bulunamadı!")

    name = lead.get("name", "Değerli Yatırımcı")

    # 2. USDT-TRON adresini al veya oluştur
    address = await _get_or_create_usdt_tron_wallet(tp_number)

    # 3. Onramper imzalama metnini hazırla (Sadece lowercase wallets parametresi imzalanır!)
    sign_content = f"wallets=usdt_tron:{address}"

    # 4. Gizli anahtar ile HMAC-SHA256 imzası oluştur
    if not ONRAMPER_SECRET_KEY:
        logger.error("❌ Onramper: ONRAMPER_SECRET_KEY konfigürasyonu eksik!")
        raise HTTPException(status_code=500, detail="Onramper imzalama anahtarı tanımlanmamış.")

    signature = hmac.new(
        ONRAMPER_SECRET_KEY.encode("utf-8"),
        sign_content.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    # 5. Tüm query parametrelerini hazırla (İmzasızlar + wallets + tema özellikleri)
    params = {
        "apiKey": ONRAMPER_API_KEY,
        "defaultCrypto": "usdt",
        "defaultNetwork": "tron",
        "defaultFiat": "TRY",
        "partnerContext": str(tp_number),
        "wallets": f"usdt_tron:{address}",
        "themeName": "light",
        "containerColor": "f5faf6",
        "primaryColor": "3e8e41",
        "secondaryColor": "f3f3f3",
        "cardColor": "ffffff",
        "primaryTextColor": "647365",
        "secondaryTextColor": "3e8e41",
        "primaryBtnTextColor": "ffffff",
        "borderRadius": "0.5",
        "wgBorderRadius": "1"
    }

    # 6. Parametreleri alfabetik sıralayıp querystring oluştur
    sorted_params = sorted(params.items())
    querystring = urllib.parse.urlencode(sorted_params)

    # 7. Nihai URL'yi oluştur
    final_url = f"{ONRAMPER_WIDGET_URL}?{querystring}&signature={signature}"

    # 8. Telegram bildirimini gönder
    telegram_msg = (
        "💳 <b>KART ÖDEME EKRANI AÇILDI</b>\n\n"
        f"👤 <b>Ad Soyad:</b> {name}\n"
        f"🔑 <b>TP NUMBER:</b> <code>{tp_number}</code>\n"
        f"📍 <b>Ödenecek Adres:</b> <code>{address}</code>\n\n"
        "<i>Kullanıcı kart ile ödeme adımına yönlendirildi. Onramper üzerinden işlem başlatması bekleniyor...</i>"
    )
    send_telegram_msg(telegram_msg)

    return {"status": "success", "widget_url": final_url}


@router.post("/callback")
async def onramper_callback(request: Request):
    """
    Onramper webhook bildirimlerini işler ve durum değişikliklerini Telegram'a raporlar.
    """
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"❌ Onramper Webhook: JSON ayrıştırma hatası: {e}")
        return PlainTextResponse("ok")

    logger.info(f"📥 Onramper Webhook tetiklendi: {payload}")

    wallet_address = payload.get("walletAddress")
    if not wallet_address:
        logger.warning("⚠️ Onramper Webhook: walletAddress parametresi bulunamadı.")
        return PlainTextResponse("ok")

    # Adrese göre kullanıcıyı (Lead) bul
    lead = await get_lead_by_address(wallet_address)
    if not lead:
        logger.error(f"❌ Onramper Webhook: {wallet_address} adresine bağlı Lead bulunamadı!")
        return PlainTextResponse("ok")

    name = lead.get("name", "Bilinmeyen Kullanıcı")
    tp_number = lead.get("tp_number", "Bilinmeyen TP")

    status = payload.get("status", "").lower()
    payment_method = payload.get("paymentMethod", "Bilinmeyen Yöntem")
    in_amount = payload.get("inAmount", 0)
    source_currency = payload.get("sourceCurrency", "").upper()
    out_amount = payload.get("outAmount", 0)
    target_currency = payload.get("targetCurrency", "").upper()

    if status in ["pending", "paid"]:
        telegram_msg = (
            "⏳ <b>KREDİ KART ÖDEMESİ BAŞLATILDI</b>\n\n"
            f"👤 <b>Ad Soyad:</b> {name}\n"
            f"🔑 <b>TP NUMBER:</b> <code>{tp_number}</code>\n"
            f"💳 <b>Yöntem:</b> {payment_method}\n"
            f"💵 <b>Ödenen Miktar:</b> {in_amount} {source_currency}\n\n"
            "<i>Ödeme işlemde. Onramper onayı bekleniyor...</i>"
        )
        send_telegram_msg(telegram_msg)

    elif status == "completed":
        telegram_msg = (
            "✅ <b>KART ÖDEMESİ BAŞARILI</b>\n\n"
            f"👤 <b>Ad Soyad:</b> {name}\n"
            f"🔑 <b>TP NUMBER:</b> <code>{tp_number}</code>\n"
            f"💳 <b>Yöntem:</b> {payment_method}\n"
            f"💵 <b>Yatırılan Tutar:</b> {in_amount} {source_currency} (Kripto: {out_amount} {target_currency})\n"
            f"📍 <b>Hedef Adres:</b> <code>{wallet_address}</code>\n\n"
            "<i>Ödeme onaylandı! Kripto paranın Cobo cüzdanına geçmesi bekleniyor. Cobo cüzdana geçince otomatik olarak MT5 hesabına aktarılacaktır.</i>"
        )
        send_telegram_msg(telegram_msg)

    elif status in ["failed", "canceled"]:
        failed_reason = payload.get("failedReason") or payload.get("onrampError") or "Bilinmeyen Hata"
        telegram_msg = (
            "❌ <b>KART ÖDEMESİ BAŞARISIZ</b>\n\n"
            f"👤 <b>Ad Soyad:</b> {name}\n"
            f"🔑 <b>TP NUMBER:</b> <code>{tp_number}</code>\n"
            f"💵 <b>Denenen Tutar:</b> {in_amount} {source_currency}\n"
            f"⚠️ <b>Hata Nedeni:</b> {status} ({failed_reason})\n\n"
            "<i>İşlem reddedildi veya iptal edildi.</i>"
        )
        send_telegram_msg(telegram_msg)

    else:
        logger.info(f"ℹ️ Onramper Webhook: İşlenmeyen status: {status}")

    return PlainTextResponse("ok")
