import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, Defaults
import pytz
import asyncio

load_dotenv()

async def sweep_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Telegram'dan /sweep komutu"""
    await update.message.reply_text("✅ TEST - Komut alındı!")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Telegram /start komutu"""
    await update.message.reply_text("🤖 Bot çalışıyor!")

async def main():
    print("🤖 Telegram Bot test ediliyor...")
    
    defaults = Defaults(tzinfo=pytz.UTC)
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).defaults(defaults).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("sweep", sweep_command))
    
    print("✅ Bot başlatılıyor...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    
    print("✅ Bot çalışıyor! /sweep yazın...")
    
    # Sonsuza kadar çalış
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
