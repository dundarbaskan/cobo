"""
Telegram Bot - Cobo Sweep Komutu
Bu script Telegram botunuza /sweep komutunu ekler.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://localhost:8000")  # Ana sunucunuzun URL'i

def send_sweep_command():
    """
    /sweep komutunu ana sunucuya gönder
    """
    url = f"{WEBHOOK_URL}/api/telegram_command"
    data = {"command": "/sweep"}
    
    try:
        response = requests.post(url, data=data)
        print(f"✅ Sweep komutu gönderildi!")
        print(f"📊 Yanıt: {response.json()}")
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    print("🔄 Manuel Sweep Başlatılıyor...")
    send_sweep_command()
