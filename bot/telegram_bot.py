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
    """
    query = update.callback_query
    user_id = query.from_user.id

    # V2.0 - Admin yetki kontrolü. Yetkisiz kullanıcılar sessizce reddedilir.
    if user_id not in ALLOWED_ADMIN_IDS:
        await query.answer("Yetkiniz yok!", show_alert=True)
        return

    # UX 1: Ekranda yukarıdan inen loading pop-up'ı / toast mesajı gönder
    await query.answer("⏳ İşleminiz yapılıyor, lütfen bekleyin...")

    callback_data = query.data  # "approve:<tx_id>" veya "reject:<tx_id>"
    try:
        action, transaction_id = callback_data.split(":", 1)
    except ValueError:
        logger.error(f"❌ Geçersiz callback_data formatı: {callback_data}")
        return

    # UX 2: Çifte tıklamayı önlemek ve loading hissi vermek için butonları anında uçur
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception as e:
        logger.warning(f"Buton kaldırılamadı: {e}")

    # API'ye isteği at
    try:
        response = requests.post(
            f"http://localhost:{PORT}/api/telegram_callback",
            data={"action": action, "transaction_id": transaction_id},
            timeout=30
        )
        
        # UX 3: İşlem başarıyla bitince ilgili mesajın altına sonucu HTML olarak iliştir
        if response.ok:
            result_flag = "✅ <b>MT5 İŞLEMİ ONAYLANDI</b>" if action == "approve" else "❌ <b>İŞLEM REDDEDİLDİ</b>"
            try:
                # python-telegram-bot'un orijinal HTML formatlı metnini al
                original_html = query.message.text_html
                new_text = f"{original_html}\n\n{result_flag}"
                await query.edit_message_text(text=new_text, parse_mode="HTML")
            except Exception as loop_e:
                logger.warning(f"Metin düzenlenemedi: {loop_e}")
        else:
            logger.error(f"❌ Callback endpoint hatası: {response.status_code} - {response.text}")
            try:
                original_html = query.message.text_html
                await query.edit_message_text(text=f"{original_html}\n\n⚠️ <b>SİSTEM HATASI OLUŞTU!</b>", parse_mode="HTML")
            except:
                pass

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
