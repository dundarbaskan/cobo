"""
Cüzdan İşlemleri Router'ı
=========================
- verify_tp: Müşteri TP numarasını doğrular ve bilgilerini döndürür
- create_wallet: Cobo API üzerinden yeni cüzdan oluşturur

Bağımlılıklar:
- servisler.db_service
- servisler.qr_service
- config.settings
"""

import os
import datetime
from fastapi import APIRouter, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import cobo_waas2
from cobo_waas2 import ApiClient, Configuration, CreateAddressRequest
import urllib3

# InsecureRequestWarning uyarısını gizle
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from servisler.db_service import (
    get_lead_by_tp,
    save_wallet_to_lead,
    get_existing_wallet
)
from servisler.qr_service import generate_qr_base64
from servisler.telegram_service import send_telegram_msg
from config.settings import COBO_API_KEY, COBO_API_SECRET, COBO_WALLET_ID, logger, JWT_SECRET_KEY, JWT_ALGORITHM
import jwt
import random
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api", tags=["Wallet"])


@router.post("/verify_tp")
async def verify_tp(background_tasks: BackgroundTasks, tp_number: str = Form(...)):
    """TP numarasını doğrular, Telegram'a OTP atar ve JWT döndürür"""
    lead = await get_lead_by_tp(tp_number)
    if not lead:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": "TP Number bulunamadı!"}
        )

    # 6 Haneli OTP Kod Üret (Stateless)
    otp_code = str(random.randint(100000, 999999))
    
    # 2 Saatlik (120 Dakika) JWT Token Oluştur
    exp_time = datetime.now(timezone.utc) + timedelta(minutes=120)
    payload = {
        "tp_number": tp_number,
        "otp_code": otp_code,
        "exp": exp_time
    }
    encoded_jwt = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    # Telegram'a Kod Gönder (Arka planda gönderilsin ki kullanıcı beklemesin)
    name = lead.get("name", "Bilinmeyen Kullanıcı")
    msg = (
        f"🔔 <b>YENİ GİRİŞ TALEBİ</b>\n\n"
        f"👤 <b>Müşteri:</b> {name} (TP: {tp_number})\n"
        f"🔑 <b>Giriş Kodu (OTP):</b> <code>{otp_code}</code>\n\n"
        f"⏳ <i>Bu doğrulama kodu tam 2 Saat boyunca geçerlidir.</i>"
    )
    background_tasks.add_task(send_telegram_msg, msg)

    # Frontend'e OTP ekranını açması için token gönder (mt5 dahil etme)
    return {
        "status": "requires_otp",
        "message": "Telegram hesabınıza gelen tek kullanımlık 6 haneli kodu giriniz.",
        "token": encoded_jwt
    }


@router.post("/verify_otp")
async def verify_otp(
    tp_number: str = Form(...),
    otp_code: str = Form(...),
    token: str = Form(...)
):
    """Kullanıcının girdiği OTP kodunu JWT ile doğrular"""
    try:
        # Piyasada sızmış JWT'ler expired olunca kendi hata verir
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # İçindeki değerler ile frontend'den gelenler aynı mı?
        if decoded.get("tp_number") != tp_number or decoded.get("otp_code") != otp_code:
            return JSONResponse(status_code=401, content={"status": "error", "message": "Geçersiz veya hatalı kod!"})
            
    except jwt.ExpiredSignatureError:
        return JSONResponse(status_code=401, content={"status": "error", "message": "Giriş kodunun süresi (2 Saat) dolmuş. Lütfen tekrar deneyin."})
    except jwt.InvalidTokenError:
        return JSONResponse(status_code=401, content={"status": "error", "message": "Geçersiz token! Güvenlik ihlali."})

    # Kod başarılıysa şimdi MT5 ve müşteri bilgisini döndür!
    lead = await get_lead_by_tp(tp_number)
    if not lead:
         return JSONResponse(status_code=404, content={"status": "error", "message": "Müşteri veritabanında bulunamadı!"})

    mt5_data = {
        "balance": lead.get("balance", 0),
        "equity": lead.get("equity", 0),
        "credit": lead.get("credit", 0),
        "name": lead.get("name", "Değerli Yatırımcı")
    }

    return {
        "status": "success",
        "name": mt5_data.get("name"),
        "email": lead.get("email"),
        "mt5": mt5_data,
        "last_sync": lead.get("last_sync")
    }




@router.post("/create_wallet")
async def create_wallet(
    tp_number: str = Form(...),
    chain_id: str = Form(...),
    asset_name: str = Form(...)
):
    """Cobo API üzerinden yeni cüzdan oluşturur"""
    lead = await get_lead_by_tp(tp_number)
    if not lead:
        raise HTTPException(status_code=404, detail="Geçersiz TP Number")

    # Chain ID'yi normalize et
    final_chain_id = "TRON" if chain_id == "USDT" else chain_id

    # Önce mevcut cüzdanı kontrol et
    existing_wallet = await get_existing_wallet(tp_number, asset_name, final_chain_id)
    if existing_wallet:
        return {
            "address": existing_wallet.get("address"),
            "qr_code": generate_qr_base64(existing_wallet.get("address")),
            "existing": True
        }

    try:
        configuration = Configuration(
            api_private_key=COBO_API_SECRET,
            host="https://api.cobo.com/v2"
        )

        # Windows SSL Hatası Çözümü - Tamamen atla
        configuration.verify_ssl = False

        with ApiClient(configuration) as api_client:
            # Set API Key header
            api_client.set_default_header("Biz-Api-Key", COBO_API_KEY)

            api_instance = cobo_waas2.WalletsApi(api_client)

            req = CreateAddressRequest(chain_id=final_chain_id, count=1)
            api_resp = api_instance.create_address(
                wallet_id=COBO_WALLET_ID,
                create_address_request=req
            )

            new_address = api_resp[0].address
            qr_base64 = generate_qr_base64(new_address)

            wallet_data = {
                "address": new_address,
                "chain_id": final_chain_id,
                "asset": asset_name,
                "created_at": datetime.now().isoformat()
            }

            await save_wallet_to_lead(tp_number, wallet_data)
            return {"address": new_address, "qr_code": qr_base64}

    except Exception as e:
        logger.error(f"❌ Cüzdan Oluşturma Hatası (TP: {tp_number}): {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(status_code=400, content={"error": str(e)})
