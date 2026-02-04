import os
import time
import logging
import asyncio
from servisler.mt5service import MT5UserManager
from servisler.db_service import save_lead, get_lead_by_tp
from dotenv import load_dotenv

from pathlib import Path

# .env dosyasını garantiye al
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def sync_from_mt5():
    SERVER = os.getenv("MT5_SERVER")
    LOGIN = os.getenv("MT5_LOGIN")
    PASSWORD = os.getenv("MT5_PASSWORD")
    GROUP_MASK = os.getenv("MT5_GROUP_MASK", "*")
    
    manager = MT5UserManager(SERVER, LOGIN, PASSWORD)
    
    while True:
        try:
            logger.info(f"🔄 MT5 Senkronizasyonu başlatılıyor (Mask: {GROUP_MASK})...")
            if manager.connect():
                logins = manager.get_all_logins(group_mask=GROUP_MASK)
                logger.info(f"📋 {len(logins)} kullanıcı bulundu. İşleniyor...")
                
                count = 0
                for loginNum in logins:
                    user_info = manager.get_user_info(loginNum)
                    if user_info:
                        # Test gruplarını da dahil et (Kullanıcı 850023 gibi hesapları görmek istiyor)
                        
                        # Toplam Yatırım ve Çekimi Hesapla
                        total_dep, total_with = manager.get_financial_summary(loginNum)
                        
                        # Mevcut lead'i kontrol et (Yatırım sayısını korumak için)
                        existing_lead = await get_lead_by_tp(loginNum)
                        deposit_count = existing_lead.get("deposit_count", 0) if existing_lead else 0
                        
                        # Eğer geçmişte bakiye hareketleri varsa ve deposit_count 0 ise güncelle
                        if total_dep > 0 and deposit_count == 0:
                            deposit_count = 1 # En az 1 yatırımı var

                        lead_data = {
                            "name": user_info['name'],
                            "tp_number": str(loginNum),
                            "email": user_info['email'],
                            "group": user_info.get('group'),
                            "balance": user_info.get('balance', 0),
                            "equity": user_info.get('equity', 0),
                            "credit": user_info.get('credit', 0),
                            "total_deposit": total_dep,
                            "total_withdrawal": total_with,
                            "deposit_count": deposit_count,
                            "last_sync": time.time()
                        }
                        await save_lead(lead_data)
                        count += 1
                
                logger.info(f"✅ {count} kullanıcı MongoDB'ye senkronize edildi.")
                manager.disconnect()
            else:
                logger.warning("⚠️ MT5 bağlantısı kurulamadı.")
                
        except Exception as e:
            logger.error(f"❌ Senkronizasyon hatası: {e}")
        
        # 30 saniyede bir çalıştır (daha hızlı güncelleme)
        logger.info("⏳ 30 saniye bekleniyor...")
        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(sync_from_mt5())
