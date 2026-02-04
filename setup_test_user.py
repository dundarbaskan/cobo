"""
MongoDB'e Test Kullanıcısı Ekler
TP: 999999
Test adresi: TEST_ADDRESS_999999
"""
import asyncio
import sys
from pathlib import Path

# Servisler klasörünü import path'e ekle
sys.path.insert(0, str(Path(__file__).parent))

# db_service'teki hazır DB bağlantısını kullan
from servisler.db_service import db

async def setup_test_user():
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
    result = await db.leads.delete_many({"tp_number": "999999"})
    if result.deleted_count > 0:
        print(f"🗑️ Eski test kullanıcısı silindi ({result.deleted_count} kayıt)")
    
    # Ekle
    result = await db.leads.insert_one(test_user)
    print(f"✅ Test kullanıcısı eklendi: {result.inserted_id}")
    print(f"👤 TP Number: 999999")
    print(f"📍 Test Adresi: TEST_ADDRESS_999999")
    print(f"\n🚀 Artık 'python test_race.py' ile test edebilirsin!")

if __name__ == "__main__":
    asyncio.run(setup_test_user())
