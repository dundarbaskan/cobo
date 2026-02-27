"""
COBO - Kripto Ödeme & MT5 Entegrasyon Sistemi
==============================================
Ana FastAPI uygulaması

Bu dosya sadece:
1. FastAPI app oluşturma
2. Router'ları bağlama
3. Startup event'leri
4. Static file mounting
5. Uvicorn başlatma

İş mantığı ayrı modüllerde:
- api/* - Endpoint'ler
- workers/* - Arka plan işlemleri
- servisler/* - Servisler
- config/* - Konfigürasyon
"""

import logging
import threading
import time
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Config
from config.settings import logger, PORT
from servisler.db_service import ensure_transaction_index
from config.settings import ENVIRONMENT

# API Routers
from api.home_router import router as home_router
from api.wallet_router import router as wallet_router
from api.webhook_router import router as webhook_router
from api.system_router import router as system_router
from api.telegram_router import router as telegram_router
from api.iban_router import router as iban_router
from admin_api import router as admin_router


# Telegram Bot
from bot.telegram_bot import run_telegram_bot

# FastAPI App
app = FastAPI(title="COBO API", version="2.0")


# Startup Event
@app.on_event("startup")
async def startup_event():
    """
    Uygulama Yaşam Döngüsü: Startup
    DB bağlantısı ve güvenlik index'lerini kontrol eder.
    """
    logger.info("🚀 Uygulama başlatılıyor...")

    try:
        await ensure_transaction_index()
        logger.info("✅ Unique Index güvenceye alındı (Çift işlem koruması aktif)")
    except Exception as e:
        logger.error(f"❌ Index oluşturulurken hata: {e}")

    logger.info("✅ Sistem tamamen hazır!")


# Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Router'ları Bağla
app.include_router(home_router)
app.include_router(wallet_router)
app.include_router(webhook_router)
app.include_router(system_router)
app.include_router(telegram_router)
app.include_router(iban_router)
app.include_router(admin_router)


if __name__ == "__main__":
    # Telegram bot'unu sadece 'release' (canlı) moddaysa başlat
    if ENVIRONMENT != "test":
        bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
        bot_thread.start()
        # Bot'un başlaması için kısa bekleme
        time.sleep(2)
    else:
        logger.info("ℹ️ Test modu aktif, Telegram botu başlatılmadı (Çakışmayı önlemek için).")

    # FastAPI'yi başlat
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        proxy_headers=True,
        forwarded_allow_ips='*'
    )
