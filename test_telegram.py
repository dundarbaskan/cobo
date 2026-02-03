import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

url = f"https://api.telegram.org/bot{token}/sendMessage"
payload = {
    "chat_id": chat_id, 
    "text": "🧪 TEST MESAJI - Telegram bağlantısı çalışıyor!",
    "parse_mode": "HTML"
}

print(f"📤 Telegram'a mesaj gönderiliyor...")
print(f"Chat ID: {chat_id}")

try:
    resp = requests.post(url, json=payload, timeout=10)
    print(f"\n📊 Status Code: {resp.status_code}")
    print(f"📝 Response: {resp.json()}")
    
    if resp.ok:
        print("\n✅ Mesaj başarıyla gönderildi!")
    else:
        print(f"\n❌ Hata: {resp.text}")
except Exception as e:
    print(f"\n❌ Exception: {e}")
