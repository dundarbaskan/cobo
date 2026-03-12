import os
import time
import logging
from mt5service import MT5UserManager
from db_service import save_lead, get_lead_by_tp

logger = logging.getLogger(__name__)

async def force_sync_single_user(tp_number: str) -> bool:
    """
    Belirli bir TP numarası için anlık Meta senkronizasyonu yapar.
    'TP numarası bulunamadı' hataları için fallback olarak kullanılır.
    """
    SERVER = os.getenv("MT5_SERVER")
    LOGIN = os.getenv("MT5_LOGIN")
    PASSWORD = os.getenv("MT5_PASSWORD")
    
    if not SERVER or not LOGIN or not PASSWORD:
        logger.error("❌ MT5 kimlik bilgileri eksik, tekil senkronizasyon yapılamıyor.")
        return False
        
    manager = MT5UserManager(SERVER, LOGIN, PASSWORD)
    
    try:
        logger.info(f"🔄 MT5 Tekil Senkronizasyon başlatılıyor (TP: {tp_number})...")
        if manager.connect():
            user_info = manager.get_user_info(tp_number)
            if user_info:
                # Toplam Yatırım ve Çekimi Hesapla
                total_dep, total_with = manager.get_financial_summary(tp_number)
                
                # Mevcut lead'i kontrol et (Yatırım sayısını korumak için)
                existing_lead = await get_lead_by_tp(tp_number)
                deposit_count = existing_lead.get("deposit_count", 0) if existing_lead else 0
                
                # Eğer geçmişte bakiye hareketleri varsa ve deposit_count 0 ise güncelle
                if total_dep > 0 and deposit_count == 0:
                    deposit_count = 1 # En az 1 yatırımı var

                lead_data = {
                    "name": user_info['name'],
                    "tp_number": str(tp_number),
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
                logger.info(f"✅ TP {tp_number} kullanıcısı MongoDB'ye anlık senkronize edildi.")
                manager.disconnect()
                return True
            else:
                logger.warning(f"⚠️ MT5 üzerinde kullanıcı ({tp_number}) bulunamadı.")
                manager.disconnect()
                return False
        else:
            logger.warning("⚠️ MT5 bağlantısı kurulamadı (Tekil Senkronizasyon).")
            return False
            
    except Exception as e:
        logger.error(f"❌ Tekil senkronizasyon hatası (TP: {tp_number}): {e}")
        try:
            manager.disconnect()
        except:
            pass
        return False
