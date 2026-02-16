"""
Merkezi Telegram Bildirim Servisi
==================================
Tüm sistem bildirimleri (yatırım, hata, durum) bu servis üzerinden gönderilir.

Parse mode: HTML — <b>, <code>, <i> tag'leri desteklenir.

ÖNEMLİ: Projenin HER YERİNDEN tek bu dosya import edilerek kullanılmalıdır.
"""

import logging
import requests
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

def send_telegram_msg(message: str):
    """
    Telegram Bot API kullanarak mesaj gönderir.

    Args:
        message: Gönderilecek mesaj (HTML formatında)
    """
    token = TELEGRAM_BOT_TOKEN
    chat_id = TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        resp = requests.post(url, json=payload)
        if not resp.ok:
            logger.error(f"❌ Telegram Hatası: {resp.text}")
    except Exception as e:
        logger.error(f"❌ Telegram İstek Hatası: {e}")
