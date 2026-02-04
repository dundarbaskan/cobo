import asyncio
import httpx
import uuid
import time

# Hedef URL (Sunucu adresi veya localhost)
API_URL = "http://localhost:8000/cobo/callback"
# API_URL = "https://srv.cepteportfoy.com/cobo/callback" # Canlı test için bunu aç

# Test Verisi
TP_NUMBER = "999999" # Test Kullanıcısı
AMOUNT = "10.50"
SYMBOL = "USDT"
STATUS = "SUCCESS"

async def send_webhook(session, tx_id, i):
    payload = {
        "event_id": str(uuid.uuid4()),
        "event_type": "transaction.deposit",
        "content": {
            "transaction_id": tx_id, # HEPSİ AYNI OLACAK!
            "address": "TEST_ADDRESS_RACE_CONDITION", # Sahte adres
            "amount": AMOUNT,
            "symbol": SYMBOL,
            "status": STATUS,
            "chain_id": "TRON"
        }
    }
    
    start = time.time()
    try:
        response = await session.post(API_URL, json=payload)
        end = time.time()
        print(f"🚀 İstek {i} Bitti: Kod={response.status_code} Süre={end-start:.3f}s")
        return response.text
    except Exception as e:
        print(f"❌ İstek {i} Hatası: {e}")

async def run_race_test():
    # Benzersiz ama sabit bir işlem ID üretelim
    tx_id = f"RACE-TEST-{int(time.time())}"
    print(f"🏁 TEST BAŞLIYOR! Transaction ID: {tx_id}")
    print(f"🎯 Hedef: Aynı anda 5 istek gönderilecek.")
    print("-" * 40)

    async with httpx.AsyncClient() as session:
        # 5 tane isteği AYNI ANDA (concurrent) hazırla
        tasks = [send_webhook(session, tx_id, i+1) for i in range(5)]
        
        # Hepsini ateşle!
        await asyncio.gather(*tasks)

    print("-" * 40)
    print("✅ TEST TAMAMLANDI. Logları (pm2 logs) kontrol et!")
    print("Beklenen Sonuç: Sadece 1 tane 'Başarılı', 4 tane 'Zaten İşlenmiş' olmalı.")

if __name__ == "__main__":
    # Windows SelectorPolicy hatası için fix (gerekirse)
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_race_test())
