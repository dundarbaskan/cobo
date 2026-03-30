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


# V2.0 - MT5 aktarım onayı için inline butonlu Telegram mesajı gönderir.
def send_telegram_approval_request(transaction_id: str, name: str, symbol: str,
                                   chain_id: str, gross_usd: float,
                                   comision: float, net_usd: float) -> None:
    """
    MT5 aktarımı için Telegram'a ONAYLA / REDDET butonlu onay mesajı gönderir.
    Buton callback_data formatı: 'approve:<transaction_id>' ve 'reject:<transaction_id>'

    Args:
        transaction_id: İşlem kimliği (pending_store key'i)
        name:           Müşteri adı
        symbol:         Coin sembolü
        chain_id:       Ağ kimliği
        gross_usd:      Gelen brüt USD tutarı
        comision:       Kesilen komisyon tutarı
        net_usd:        MT5'e geçirilecek net tutar
    """
    token = TELEGRAM_BOT_TOKEN
    chat_id = TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    text = (
        f"⚠️ <b>MT5 AKTARIM ONAYI GEREKİYOR</b>\n\n"
        f"👤 <b>Müşteri:</b> {name}\n"
        f"💵 <b>Coin:</b> {symbol.upper()} ({chain_id.upper()})\n\n"
        f"📥 <b>Gelen Tutar:</b> <code>{gross_usd:,.2f} $</code>\n"
        f"✂️ <b>Komisyon (%5):</b> <code>-{comision:,.2f} $</code>\n"
        f"✅ <b>Net MT5 Tutarı:</b> <code>{net_usd:,.2f} $</code>\n\n"
        f"<i>Meta Hesabına paranın geçişini onaylıyor musunuz?</i>"
    )

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [[
                {
                    "text": "✅ ONAYLA",
                    "callback_data": f"approve:{transaction_id}"
                },
                {
                    "text": "❌ REDDET",
                    "callback_data": f"reject:{transaction_id}"
                }
            ]]
        }
    }

    t = threading.Thread(target=_send_sync, args=(url, payload), daemon=True)
    t.start()
