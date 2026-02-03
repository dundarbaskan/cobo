"""
Telegram Bot Handler
Bu script Telegram botunuzdan gelen mesajları dinler ve /sweep komutunu işler.
"""
import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = "http://localhost:8000/api/telegram_command"

async def sweep_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /sweep komutunu işle
    """
    # API'ye komut gönder
    try:
        response = requests.post(API_URL, data={"command": "/sweep"}, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                await update.message.reply_text("✅ Wallet bilgileri Telegram grubuna gönderildi!")
            else:
                await update.message.reply_text(f"❌ Hata: {result.get('message', 'Bilinmeyen hata')}")
        else:
            await update.message.reply_text(f"❌ API Hatası: {response.status_code}")
    except Exception as e:
        await update.message.reply_text(f"❌ Bağlantı Hatası: {str(e)}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start komutu
    """
    await update.message.reply_text(
        "🤖 Cobo Wallet Bot\n\n"
        "Komutlar:\n"
        "/sweep - Wallet durumunu görüntüle\n"
        "/start - Bu mesajı göster"
    )

def main():
    """Bot'u başlat"""
    print("🤖 Telegram Bot başlatılıyor...")
    
    # Application oluştur
    from telegram.ext import Defaults
    import pytz
    
    defaults = Defaults(tzinfo=pytz.UTC)
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).defaults(defaults).build()
    
    # Komut handler'ları ekle
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("sweep", sweep_command))
    
    # Bot'u çalıştır
    print("✅ Bot hazır! /sweep komutunu kullanabilirsiniz.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
