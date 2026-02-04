"""
Race Condition Testi
Aynı transaction_id ile 5 paralel istek gönderir.
Beklenen: Sadece 1 tanesi işlensin, diğerleri "Zaten İşlenmiş" diye bloklanmalı.
"""
import asyncio
import httpx
import uuid

# Hedef URL (Sunucu adresi veya localhost)
API_URL = "http://localhost:8000/cobo/callback"
# API_URL = "https://srv.cepteportfoy.com/cobo/callback" # Canlı test için bunu aç

# SABİT Test Verileri (Kolay temizleme için)
TRANSACTION_ID = "TEST-TX-12345-RACE"
TEST_ADDRESS = "TEST_ADDRESS_999999"  # MongoDB'deki test kullanıcısının adresi
TP_NUMBER = "999999"
AMOUNT = "15.75"
SYMBOL = "USDT"
CHAIN_ID = "TRON"

async def send_webhook(session, request_number):
    """
    Cobo'nun gerçek webhook formatında istek gönderir.
    """
    payload = {
        "event_id": f"evt-{request_number}-{uuid.uuid4().hex[:8]}",
        "type": "transaction.deposit",  # event_type yerine type!
        "data": {  # content yerine data!
            "transaction": {
                "transaction_id": TRANSACTION_ID,  # Hepsi aynı ID
                "to_address": TEST_ADDRESS,
                "amount": AMOUNT,
                "token_id": SYMBOL,
                "chain_id": CHAIN_ID,
                "status": "SUCCESS",
                "type": "DEPOSIT"
            }
        }
    }
    
    try:
        response = await session.post(API_URL, json=payload, timeout=10.0)
        status = response.status_code
        text = response.text[:100] if response.text else "OK"
        
        print(f"{'✅' if status == 200 else '❌'} İstek #{request_number}: HTTP {status} - {text}")
        return status
    except Exception as e:
        print(f"❌ İstek #{request_number} Hata: {e}")
        return None

async def run_race_test():
    print("=" * 60)
    print("🏁 RACE CONDITION TEST BAŞLIYOR")
    print("=" * 60)
    print(f"📍 Transaction ID: {TRANSACTION_ID}")
    print(f"👤 TP Number: {TP_NUMBER}")
    print(f"💰 Tutar: {AMOUNT} {SYMBOL}")
    print(f"🎯 Test: 5 paralel istek gönderilecek (Aynı TX ID)")
    print("-" * 60)

    async with httpx.AsyncClient() as session:
        # 5 paralel istek hazırla
        tasks = [send_webhook(session, i+1) for i in range(5)]
        
        # Hepsini aynı anda ateşle!
        results = await asyncio.gather(*tasks)
    
    print("-" * 60)
    print("✅ TEST TAMAMLANDI!")
    print("\n📊 Beklenen Sonuç:")
    print("   - MongoDB'de SADECE 1 kayıt olmalı (transaction_id: TEST-TX-12345-RACE)")
    print("   - Telegram'a SADECE 1 mesaj gitmeli")
    print("   - Logda 4 tane 'Zaten İşlenmiş' olmalı")
    print("\n🔍 Kontrol Komutları:")
    print("   pm2 logs COBO-API --lines 50")
    print("   mongo -> use cobo_system -> db.transactions.find({transaction_id: 'TEST-TX-12345-RACE'})")
    print("\n🗑️ Temizlik (Test sonrası):")
    print("   db.transactions.deleteMany({transaction_id: 'TEST-TX-12345-RACE'})")

if __name__ == "__main__":
    # Windows için async fix
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except:
        pass
    
    asyncio.run(run_race_test())
