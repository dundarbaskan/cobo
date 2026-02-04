"""
MongoDB'e Test Kullanıcısı Ekler
TP: 999999
Test adresi: TEST_ADDRESS_999999
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# .env dosyasını yükle
load_dotenv(Path(__file__).parent / '.env')

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = "cobo_system"

async def setup_test_user():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DB_NAME]
    
    test_user = {
        "tp_number": "999999",
        "name": "Test Kullanıcısı (Race Condition)",
        "wallets": [
            {
                "address": "TEST_ADDRESS_999999",
                "chain_id": "TRON",
                "asset": "USDT"
            }
        ],
        "total_deposit": 0.0,
        "total_withdrawal": 0.0,
        "deposit_count": 0
    }
    
    # Eğer zaten varsa sil, temiz başla
    await db.leads.delete_many({"tp_number": "999999"})
    
    # Ekle
    result = await db.leads.insert_one(test_user)
    print(f"✅ Test kullanıcısı eklendi: {result.inserted_id}")
    print(f"👤 TP Number: 999999")
    print(f"📍 Test Adresi: TEST_ADDRESS_999999")
    print(f"\nArtık 'python test_race.py' ile test edebilirsin!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(setup_test_user())
