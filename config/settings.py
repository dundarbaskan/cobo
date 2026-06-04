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
PORT = int(os.getenv("PORT", 8001))
SERVER_IP = os.getenv("SERVER_IP")
ENVIRONMENT = os.getenv("ENVIRONMENT", "test")

# Bakım (Maintenance) Ayarları
MAINTENANCE_ACTIVE = os.getenv("MAINTENANCE_ACTIVE", "False").lower() == "true"
ADMIN_IP = os.getenv("ADMIN_IP", "")  # Eğer IP sildiğimde herkese açık olacaksa...
MAINTENANCE_MINUTES = int(os.getenv("MAINTENANCE_MINUTES", 120))  # 2 Saatlik global bakım sayacı

# Güvenlik (JWT) Ayarları
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "4aw^DQ9'0a/(")
JWT_ALGORITHM = "HS256"

# Admin Panel Ayarları
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "besimtrump18")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Bg180913*")


# V2.0 - Yetkili Telegram Admin ID'leri. Bu listedeki kişiler onay/ret butonlarını kullanabilir.
#         .env veya dışarıdan alınmaz; statik olarak burada yönetilir.
ALLOWED_ADMIN_IDS = [7996564741, 7595772716, 6667266455, 965219313 , 6793216435]

# V2.0 - Cobo Cüzdan Yönlendirme Adresleri (.env'den okunur)
MAIN_WALLET = os.getenv("MAIN_WALLET", "")
ETH_CONVERTER_WALLET = os.getenv("ETH_CONVERTER_WALLET", "")
BTC_CONVERTER_WALLET = os.getenv("BTC_CONVERTER_WALLET", "")
TRX_CONVERTER_WALLET = os.getenv("TRX_CONVERTER_WALLET", "")


# V2.0 - Onramper Ayarları (.env'den okunur)
ONRAMPER_API_KEY = os.getenv("ONRAMPER_API_KEY")
ONRAMPER_SECRET_KEY = os.getenv("ONRAMPER_SECRET_KEY")
ONRAMPER_WIDGET_URL = os.getenv("ONRAMPER_WIDGET_URL")


def get_mt5_manager():
    """Yeni bir MT5 Manager instance döndürür (Concurrent işlemler için güvenli)"""
    from servisler.mt5service import MT5UserManager
    return MT5UserManager(MT5_SERVER, MT5_LOGIN, MT5_PASSWORD)

