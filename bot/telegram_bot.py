"""
Telegram Bot Handler Modülü
============================
/start, /sweep, /admin komutlarını dinler ve localhost API'ye yönlendirir.
main.py tarafından ayrı bir thread'de başlatılır.

DİKKAT: Bu bot doğrudan iş mantığı ÇALIŞMAZ.
Sadece HTTP POST ile /api/telegram_command endpoint'ine komut gönderir.

Çalışma Şekli:
Telegram → Bot Handler → HTTP POST localhost:8000 → API → Servis
"""

import asyncio
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, ApplicationBuilder
from config.settings import TELEGRAM_BOT_TOKEN, PORT

logger = logging.getLogger(__name__)


async def telegram_sweep_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Telegram'dan /sweep komutu"""
    try:
        response = requests.post(
            f"http://localhost:{PORT}/api/telegram_command",
            data={"command": "/sweep"},
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                await update.message.reply_text("✅ Wallet bilgileri gruba gönderildi!")
            else:
                await update.message.reply_text(f"❌ Hata: {result.get('message', 'Bilinmeyen')}")
        else:
            await update.message.reply_text(f"❌ API Hatası: {response.status_code}")
    except Exception as e:
        await update.message.reply_text(f"❌ Bağlantı Hatası: {str(e)}")


async def telegram_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Telegram'dan /admin komutu"""
    try:
        response = requests.post(
            f"http://localhost:{PORT}/api/telegram_command",
            data={"command": "/admin"},
            timeout=30
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Bağlantı Hatası: {str(e)}")


async def telegram_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Telegram /start komutu"""
    await update.message.reply_text(
        "🤖 Cobo Wallet Bot\n\n"
        "Komutlar:\n"
        "/sweep - Wallet durumunu görüntüle\n"
        "/admin - Admin panel linkini al\n"
        "/start - Bu mesajı göster"
    )


def run_telegram_bot():
    """
    Telegram bot'u ayrı thread'de çalıştır

    Bu fonksiyon main.py tarafından threading.Thread içinde çağrılır.
    """
    try:
        logger.info("🤖 Telegram Bot başlatılıyor...")

        # Yeni bir event loop oluştur ve thread'e ata
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Telegram bot - job_queue'yu devre dışı bırak (timezone hatası önleme)
        application = (
            ApplicationBuilder()
            .token(TELEGRAM_BOT_TOKEN)
            .job_queue(None)  # Job queue'yu devre dışı bırak
            .build()
        )

        application.add_handler(CommandHandler("start", telegram_start_command))
        application.add_handler(CommandHandler("sweep", telegram_sweep_command))
        application.add_handler(CommandHandler("admin", telegram_admin_command))

        logger.info("✅ Telegram Bot hazır!")
        application.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)

    except Exception as e:
        logger.error(f"❌ Telegram Bot hatası: {e}")
        import traceback
        traceback.print_exc()
