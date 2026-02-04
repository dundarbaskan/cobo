"""
MongoDB'e Test Kullanıcısı Ekler
TP: 999999
Test adresi: TEST_ADDRESS_999999
Collection: COBO (maxipinfo.COBO)
"""
import asyncio
import sys
from pathlib import Path

# Servisler klasörünü import path'e ekle
sys.path.insert(0, str(Path(__file__).parent))

# db_service'teki hazır DB bağlantısını kullan
from servisler.db_service import cobo_collection

async def setup_test_user():
    """
    Gerçek COBO formatında test kullanıcısı ekler.
    """
    test_user = {
        "tp_number": "999999",
        "email": "test@race.condition",
        "name": "Test Kullanıcısı (Race)",
        "balance": 0,
        "credit": 0,
        "deposit_count": 0,
        "equity": 0,
        "group": "999999\\Test",
        "total_deposit": 0.0,
        "total_withdrawal": 0.0,
        "wallets": [
            {
                "address": "TEST_ADDRESS_999999",
                "chain_id": "TRON",
                "asset": "USDT"
            }
        ]
    }
    
    # Eğer zaten varsa sil, temiz başla
    result = await cobo_collection.delete_many({"tp_number": "999999"})
    if result.deleted_count > 0:
        print(f"🗑️ Eski test kullanıcısı silindi ({result.deleted_count} kayıt)")
    
    # COBO collection'ına ekle
    result = await cobo_collection.insert_one(test_user)
    print(f"✅ Test kullanıcısı COBO collection'ına eklendi!")
    print(f"   _id: {result.inserted_id}")
    print(f"   👤 TP Number: 999999")
    print(f"   📍 Test Adresi: TEST_ADDRESS_999999")
    print(f"   📁 Collection: maxipinfo.COBO")
    print(f"\n🚀 Artık 'python test_race.py' ile test edebilirsin!")

if __name__ == "__main__":
    asyncio.run(setup_test_user())
