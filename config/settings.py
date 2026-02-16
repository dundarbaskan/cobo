"""
Konfigürasyon ve Ortam Değişkenleri
====================================
Tüm .env okuma işlemleri ve merkezi konfigürasyon ayarları bu dosyada tutulur.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# .env dosyasını tam yol ile yükle (PM2 uyumluluğu için)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Logging Konfigürasyonu
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB Ayarları
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://wimcrm:edWfyiwTjpnkgAzx@data.drjzdcy.mongodb.net/maxipinfo?retryWrites=true&w=majority&appName=DATA")

# Cobo API Ayarları
COBO_API_KEY = os.getenv("COBO_API_KEY")
COBO_API_SECRET = os.getenv("COBO_API_SECRET")
COBO_WALLET_ID = os.getenv("COBO_WALLET_ID")

# Telegram Bot Ayarları
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# MT5 Ayarları
MT5_SERVER = os.getenv("MT5_SERVER")
MT5_LOGIN = int(os.getenv("MT5_LOGIN", 10000))
MT5_PASSWORD = os.getenv("MT5_PASSWORD")
MT5_GROUP_MASK = os.getenv("MT5_GROUP_MASK", "*")

# Server Ayarları
PORT = int(os.getenv("PORT", 8000))
SERVER_IP = os.getenv("SERVER_IP")

# Admin Panel Ayarları
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "besimtrump18")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Bg180913*")

# MT5 Manager Instance (Singleton)
# Import burada yapılıyor çünkü MT5UserManager servisler klasöründe
# Circular import'tan kaçınmak için lazy loading yapacağız
_mt5_manager = None

def get_mt5_manager():
    """MT5 Manager singleton instance döndürür"""
    global _mt5_manager
    if _mt5_manager is None:
        from servisler.mt5service import MT5UserManager
        _mt5_manager = MT5UserManager(MT5_SERVER, MT5_LOGIN, MT5_PASSWORD)
    return _mt5_manager
