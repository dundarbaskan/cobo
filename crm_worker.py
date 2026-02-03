import os
import time
import logging
import asyncio
from servisler.crmservice import scrape_crm_simple
from servisler.db_service import save_lead
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def sync_task():
    while True:
        try:
            logger.info("🔄 CRM Senkronizasyonu başlatılıyor...")
            # crmservice.py içindeki scraper'ı çalıştır
            # Not: scrape_crm_simple bir dict dönüyor {tp: tag, ...}
            # Bizim TP ve Mail/AdSoyad eşleşmesine ihtiyacımız var.
            # Scraper'ın döndüğü veriye göre MongoDB'ye kaydedeceğiz.
            
            data = scrape_crm_simple() # Bu fonksiyon crmservice.py içinde
            
            if data:
                for tp, name in data.items():
                    lead_data = {
                        "name": name,
                        "tp_number": str(tp),
                        "last_sync": time.time()
                    }
                    await save_lead(lead_data)
                logger.info(f"✅ {len(data)} kayıt senkronize edildi.")
            else:
                logger.warning("⚠️ CRM'den veri alınamadı.")
                
        except Exception as e:
            logger.error(f"❌ Senkronizasyon hatası: {e}")
        
        # 5 dakikada bir çalıştır
        logger.info("⏳ 5 dakika bekleniyor...")
        await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(sync_task())
