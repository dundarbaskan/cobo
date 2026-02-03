import requests
import json

# Test /sweep komutu
url = "http://localhost:8000/api/telegram_command"
data = {"command": "/sweep"}

print("🔄 /sweep komutu test ediliyor...")
try:
    response = requests.post(url, data=data, timeout=30)
    
    print(f"\n📊 Yanıt Kodu: {response.status_code}")
    print(f"📝 Yanıt: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"\n❌ Hata: {e}")
    print(f"Detay: {type(e).__name__}")
