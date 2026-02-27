"""
Merkezi Telegram Bildirim Servisi
==================================
Tüm sistem bildirimleri (yatırım, hata, durum) bu servis üzerinden gönderilir.

Parse mode: HTML — <b>, <code>, <i> tag'leri desteklenir.

ÖNEMLİ: Projenin HER YERİNDEN tek bu dosya import edilerek kullanılmalıdır.
"""

import logging
import threading
import requests
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

def _send_sync(url, payload):
    """Senkron gönderimi ayrı thread'de yapar, async loop'u bloke etmez."""
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if not resp.ok:
            logger.error(f"❌ Telegram Hatası: {resp.text}")
    except Exception as e:
        logger.error(f"❌ Telegram İstek Hatası: {e}")

def send_telegram_msg(message: str):
    """
    Telegram Bot API kullanarak mesaj gönderir.
    Async event loop'u bloke etmemek için ayrı thread'de çalışır.

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

    t = threading.Thread(target=_send_sync, args=(url, payload), daemon=True)
    t.start()
