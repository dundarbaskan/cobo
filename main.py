import logging
import threading
import time
import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# Config ve Servisler
from config.settings import logger, PORT, ENVIRONMENT, ALLOWED_TEST_IP
from servisler.db_service import ensure_transaction_index

# API Routers
from api.home_router import router as home_router
from api.wallet_router import router as wallet_router
from api.webhook_router import router as webhook_router
from api.system_router import router as system_router
from api.telegram_router import router as telegram_router
from api.iban_router import router as iban_router
from api.onramper_router import router as onramper_router
from admin_api import router as admin_router

# Telegram Bot
from bot.telegram_bot import run_telegram_bot

# FastAPI App Nesnesi
app = FastAPI(title="COBO API", version="2.0")

# --- Güvenlik ve Rate Limit Ayarları ---
REQUEST_COUNTS = {}

@app.middleware("http")
async def verify_and_rate_limit(request: Request, call_next):
    forwarded_for = request.headers.get("X-Forwarded-For")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else request.client.host
    path = request.url.path

    # İstisnalar: Statik dosyalar, webhook ve localhost istekleri
    if path.startswith("/static") or path.startswith("/logolar") or path == "/cobo/callback" or path == "/api/onramper/callback" or client_ip in ["127.0.0.1", "localhost", "::1"]:
        return await call_next(request)

    # Sadece TEST modunda kısıtlamaları uygula
    if ENVIRONMENT == "test":
        # 1. Rate Limiting (IP Başına 1 Dakikada 10 İstek)
        current_time = time.time()
        if client_ip not in REQUEST_COUNTS:
            REQUEST_COUNTS[client_ip] = {"count": 1, "start_time": current_time}
        else:
            ip_data = REQUEST_COUNTS[client_ip]
            if current_time - ip_data["start_time"] < 60:
                if ip_data["count"] >= 10:
                    return JSONResponse(
                        status_code=429, 
                        content={"status": "error", "message": "Çok fazla istek gönderdiniz. Lütfen 1 dakika bekleyin."}
                    )
                ip_data["count"] += 1
            else:
                REQUEST_COUNTS[client_ip] = {"count": 1, "start_time": current_time}

        # 2. Test Ortamı IP Doğrulaması (Bakım Modu)
        if client_ip != ALLOWED_TEST_IP:
            content = "<h1>Sistem Bakımda (Test Aşaması)</h1>"
            if os.path.exists("testing.html"):
                with open("testing.html", "r", encoding="utf-8") as f:
                    content = f.read()
            return HTMLResponse(content=content, status_code=503)

    return await call_next(request)

# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Uygulama başlatılıyor...")
    try:
        await ensure_transaction_index()
        logger.info("✅ Unique Index güvenceye alındı (Çift işlem koruması aktif)")
    except Exception as e:
        logger.error(f"❌ Index oluşturulurken hata: {e}")
    logger.info("✅ Sistem tamamen hazır!")

# Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Router Bağlantıları
app.include_router(home_router)
app.include_router(wallet_router)
app.include_router(webhook_router)
app.include_router(system_router)
app.include_router(telegram_router)
app.include_router(iban_router)
app.include_router(admin_router)
app.include_router(onramper_router)

if __name__ == "__main__":
    # Botu sadece canlı modda başlat
    if ENVIRONMENT != "test":
        bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
        bot_thread.start()
        time.sleep(2)
    else:
        logger.info("ℹ️ Test modu aktif, Telegram botu başlatılmadı.")

    uvicorn.run(app, host="0.0.0.0", port=PORT, proxy_headers=True, forwarded_allow_ips='*')