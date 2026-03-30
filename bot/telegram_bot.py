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
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ApplicationBuilder
from config.settings import TELEGRAM_BOT_TOKEN, PORT, ALLOWED_ADMIN_IDS

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


# V2.0 - MT5 onay/ret buton callback handler'ı. Yalnızca yetkili adminler işlem yapabilir.
async def mt5_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Telegram inline buton callback'lerini işler.
    'approve:<transaction_id>' veya 'reject:<transaction_id>' formatındaki
    callback_data'yı parse edip yerel API endpoint'ine iletir.

    Güvenlik: Yalnızca ALLOWED_ADMIN_IDS listesindeki kullanıcılar işlem yapabilir.
    Yetkisiz tıklamalar sessizce görmezden gelinir.
    """
    query = update.callback_query
    user_id = query.from_user.id

    # V2.0 - Admin yetki kontrolü. Yetkisiz kullanıcılar sessizce reddedilir.
    if user_id not in ALLOWED_ADMIN_IDS:
        return

    await query.answer()  # Telegram'a "buton alındı" sinyali

    callback_data = query.data  # "approve:<tx_id>" veya "reject:<tx_id>"
    try:
        action, transaction_id = callback_data.split(":", 1)
    except ValueError:
        logger.error(f"❌ Geçersiz callback_data formatı: {callback_data}")
        return

    try:
        response = requests.post(
            f"http://localhost:{PORT}/api/telegram_callback",
            data={"action": action, "transaction_id": transaction_id},
            timeout=30
        )
        if not response.ok:
            logger.error(f"❌ Callback endpoint hatası: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"❌ Callback isteği başarısız: {e}")


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

        # V2.0 - MT5 onay/ret inline buton handler'ı
        application.add_handler(CallbackQueryHandler(mt5_approval_callback))

        logger.info("✅ Telegram Bot hazır!")
        application.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)

    except Exception as e:
        logger.error(f"❌ Telegram Bot hatası: {e}")
        import traceback
        traceback.print_exc()
