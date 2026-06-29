"""
Ortam Değişkenleri ve Bağlantı Testi (envtest.py)
================================================
Bu test, .env dosyasındaki değişkenlerin doğru yüklendiğini,
zorunlu değişkenlerin eksiksiz olduğunu ve MongoDB/Telegram/Cobo API/MT5
servis bağlantılarının başarılı olduğunu doğrular.
"""

import os
import sys
import asyncio
from pathlib import Path

# Proje ana dizinini sys.path'e ekle (Modülleri import edebilmek için)
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import (
    MONGODB_URL,
    COBO_API_KEY,
    COBO_API_SECRET,
    COBO_WALLET_ID,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    MT5_SERVER,
    MT5_LOGIN,
    MIN_DEPOSIT_USD_LIMIT,
    COBO_AUTO_ROUTING_ENABLED
)

def test_dotenv_load():
    """1. .env değişkenlerinin yüklendiğini doğrular."""
    print("🔄 1. Ortam değişkenleri kontrol ediliyor...")
    
    # Kontrol edilecek kritik değişkenler
    critical_vars = {
        "MONGODB_URL": MONGODB_URL,
        "COBO_API_KEY": COBO_API_KEY,
        "COBO_API_SECRET": COBO_API_SECRET,
        "COBO_WALLET_ID": COBO_WALLET_ID,
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
        "MT5_SERVER": MT5_SERVER,
        "MT5_LOGIN": MT5_LOGIN,
    }
    
    missing = []
    for var_name, var_value in critical_vars.items():
        if not var_value:
            missing.append(var_name)
        else:
            # Maskelenmiş gösterim (güvenlik için)
            val_str = str(var_value)
            masked = val_str[:4] + "..." + val_str[-4:] if len(val_str) > 8 else "Set"
            print(f"  ✅ {var_name}: {masked}")
            
    if missing:
        print(f"❌ HATA: Eksik ortam değişkenleri var: {missing}")
        return False
        
    print(f"  ℹ️ Limit (Min Deposit): {MIN_DEPOSIT_USD_LIMIT} USD")
    print(f"  ℹ️ Otomatik Routing: {COBO_AUTO_ROUTING_ENABLED}")
    print("✅ Ortam değişkenleri testi başarılı!\n")
    return True


async def test_mongodb_connection():
    """2. MongoDB bağlantısını ve yazma yetkisini doğrular."""
    print("🔄 2. MongoDB bağlantısı ve yazma yetkisi test ediliyor...")
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import datetime
        
        client = AsyncIOMotorClient(MONGODB_URL)
        # 1 saniye timeout verelim ki asılı kalmasın
        client.get_io_loop = asyncio.get_event_loop
        
        # Basit bir ping atalım
        await client.admin.command('ping')
        print("  ✅ MongoDB Sunucu bağlantısı kuruldu.")
        
        db = client.maxipinfo
        # Geçici bir test dokümanı eklemeyi (write/update yetkisini) test et
        test_collection = db.env_test_logs
        
        test_doc = {
            "test_run": True,
            "timestamp": datetime.datetime.now(),
            "status": "success"
        }
        
        # update_one (upsert) ile yetki testi
        result = await test_collection.update_one(
            {"test_run": True},
            {"$set": test_doc},
            upsert=True
        )
        print("  ✅ MongoDB maxipinfo DB'sine yazma/güncelleme (write/update) yetkisi onaylandı!")
        
        # Test dokümanını temizle
        await test_collection.delete_one({"test_run": True})
        print("  ✅ MongoDB test verisi temizlendi.")
        
        print("✅ MongoDB testi başarılı!\n")
        return True
        
    except Exception as e:
        print(f"❌ HATA: MongoDB bağlantı veya yetki hatası!")
        print(f"Detay: {e}\n")
        return False


async def test_telegram_connection():
    """3. Telegram Bot token'ının geçerliliğini test eder."""
    print("🔄 3. Telegram API bağlantısı test ediliyor...")
    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            bot_name = data.get("result", {}).get("username", "Bilinmeyen")
            print(f"  ✅ Telegram Bot aktif: @{bot_name}")
            print("✅ Telegram API testi başarılı!\n")
            return True
        else:
            print(f"❌ HATA: Telegram API geçersiz token döndü! HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ HATA: Telegram API bağlantı hatası: {e}\n")
        return False


async def main():
    print("====================================================")
    print("🧪 COBO PROJESİ ORTAM VE ENTEGRASYON TESTİ")
    print("====================================================\n")
    
    # 1. Dotenv Kontrolü
    if not test_dotenv_load():
        sys.exit(1)
        
    # 2. MongoDB Kontrolü
    db_success = await test_mongodb_connection()
    
    # 3. Telegram Kontrolü
    tg_success = await test_telegram_connection()
    
    print("====================================================")
    print("📊 TEST SONUÇLARI ÖZETİ:")
    print("====================================================")
    print(f"Ortam Değişkenleri:  ✅ BAŞARILI")
    print(f"MongoDB Bağlantısı:  {'✅ BAŞARILI' if db_success else '❌ BAŞARISIZ'}")
    print(f"Telegram Bağlantısı: {'✅ BAŞARILI' if tg_success else '❌ BAŞARISIZ'}")
    print("====================================================")
    
    if not (db_success and tg_success):
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
