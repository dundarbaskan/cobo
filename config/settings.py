"""
Konfigürasyon ve Ortam Değişkenleri
====================================
Tüm .env okuma işlemleri ve merkezi konfigürasyon ayarları bu dosyada tutulur.
Hiçbir modül doğrudan os.getenv() çağırmamalı; tüm değerlere buradan ulaşılmalı.

Kritik ayarlar (şifre, secret, URL) için fallback bırakılmamıştır.
.env dosyasında tanımlı değilse uygulama başlamaz — bu kasıtlı bir güvenlik kararıdır.
"""

import os
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env dosyasını tam yol ile yükle (PM2 uyumluluğu için)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _require(variable_name: str) -> str:
    """
    .env'de zorunlu olan bir değişkeni okur.
    Tanımlı değilse uygulamayı güvenli şekilde durdurur.
    """
    value = os.getenv(variable_name)
    if not value:
        logger.critical(
            f"❌ Zorunlu ortam değişkeni eksik: '{variable_name}'. "
            f".env dosyasını kontrol edin."
        )
        sys.exit(1)
    return value


# ─── Veritabanı ──────────────────────────────────────────────────────────────
MONGODB_URL = _require("MONGODB_URL")

# ─── Cobo API ────────────────────────────────────────────────────────────────
COBO_API_KEY    = _require("COBO_API_KEY")
COBO_API_SECRET = _require("COBO_API_SECRET")
COBO_WALLET_ID  = _require("COBO_WALLET_ID")
COBO_API_HOST   = os.getenv("COBO_API_HOST", "https://api.cobo.com/v2")

# ─── Telegram Bot ─────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = _require("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = _require("TELEGRAM_CHAT_ID")

# ─── MT5 ─────────────────────────────────────────────────────────────────────
MT5_SERVER    = _require("MT5_SERVER")
MT5_LOGIN     = int(_require("MT5_LOGIN"))
MT5_PASSWORD  = _require("MT5_PASSWORD")
MT5_GROUP_MASK = os.getenv("MT5_GROUP_MASK", "*")

# ─── Sunucu ──────────────────────────────────────────────────────────────────
PORT         = int(os.getenv("PORT", 8001))
SERVER_IP    = os.getenv("SERVER_IP")
ENVIRONMENT  = os.getenv("ENVIRONMENT", "test")
APP_BASE_URL = os.getenv("APP_BASE_URL", "")

# ─── Güvenlik (JWT & Admin) ───────────────────────────────────────────────────
JWT_SECRET_KEY   = _require("JWT_SECRET_KEY")
JWT_ALGORITHM    = "HS256"

ADMIN_USERNAME        = _require("ADMIN_USERNAME")
ADMIN_PASSWORD        = _require("ADMIN_PASSWORD")
IBAN_MANAGER_USERNAME = _require("IBAN_MANAGER_USERNAME")
IBAN_MANAGER_PASSWORD = _require("IBAN_MANAGER_PASSWORD")

# ─── Erişim Kontrolü ──────────────────────────────────────────────────────────
# Test ortamında bu IP dışındaki tüm istekler bakım sayfasına yönlendirilir
ALLOWED_TEST_IP = os.getenv("ALLOWED_TEST_IP", "")

# Bakım (Maintenance) Ayarları — eski sistem uyumluluğu
MAINTENANCE_ACTIVE   = os.getenv("MAINTENANCE_ACTIVE", "False").lower() == "true"
ADMIN_IP             = os.getenv("ADMIN_IP", "")
MAINTENANCE_MINUTES  = int(os.getenv("MAINTENANCE_MINUTES", 120))

# ─── İş Kuralları ────────────────────────────────────────────────────────────
COMPANY_NAME            = os.getenv("COMPANY_NAME", "Cep Portföy")
DEFAULT_AGENT_NAME      = os.getenv("DEFAULT_AGENT_NAME", "")
COMMISSION_RATE_PERCENT = float(os.getenv("COMMISSION_RATE_PERCENT", 0))
MIN_DEPOSIT_USD_LIMIT   = float(os.getenv("MIN_DEPOSIT_USD_LIMIT", 1.0))

# ─── Cüzdan Yönlendirme ───────────────────────────────────────────────────────
MAIN_WALLET           = os.getenv("MAIN_WALLET", "")
ETH_CONVERTER_WALLET  = os.getenv("ETH_CONVERTER_WALLET", "")
BTC_CONVERTER_WALLET  = os.getenv("BTC_CONVERTER_WALLET", "")
TRX_CONVERTER_WALLET  = os.getenv("TRX_CONVERTER_WALLET", "")

# ─── Onramper ────────────────────────────────────────────────────────────────
ONRAMPER_API_KEY       = os.getenv("ONRAMPER_API_KEY")
ONRAMPER_SECRET_KEY    = os.getenv("ONRAMPER_SECRET_KEY")
ONRAMPER_WIDGET_URL    = os.getenv("ONRAMPER_WIDGET_URL")
ONRAMPER_DEFAULT_CRYPTO = os.getenv("ONRAMPER_DEFAULT_CRYPTO", "USDT")
ONRAMPER_DEFAULT_NETWORK = os.getenv("ONRAMPER_DEFAULT_NETWORK", "tron")
ONRAMPER_DEFAULT_FIAT  = os.getenv("ONRAMPER_DEFAULT_FIAT", "TRY")
ONRAMPER_DEFAULT_AMOUNT = os.getenv("ONRAMPER_DEFAULT_AMOUNT", "1000")

# ─── Yetkili Telegram Admin ID'leri ──────────────────────────────────────────
# .env'de ALLOWED_ADMIN_TELEGRAM_IDS=id1,id2,id3 formatında tanımlanabilir.
# Tanımlanmadıysa sabit liste kullanılır (geriye dönük uyumluluk).
_raw_admin_ids = os.getenv("ALLOWED_ADMIN_TELEGRAM_IDS", "")
if _raw_admin_ids:
    ALLOWED_ADMIN_IDS = [
        int(admin_id.strip())
        for admin_id in _raw_admin_ids.split(",")
        if admin_id.strip().isdigit()
    ]
else:
    ALLOWED_ADMIN_IDS = [7996564741, 7595772716, 6667266455, 965219313, 6793216435]


def get_mt5_manager():
    """Yeni bir MT5 Manager instance döndürür (Concurrent işlemler için güvenli)"""
    from servisler.mt5service import MT5UserManager
    return MT5UserManager(MT5_SERVER, MT5_LOGIN, MT5_PASSWORD)
