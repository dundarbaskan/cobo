"""
Telegram Bot Komut API'si
=========================
Telegram bot handler'larından gelen komutları işler.

Komutlar:
- /sweep → Cobo wallet durum raporu oluşturur ve Telegram'a gönderir
- /admin → Admin panel linkini paylaşır

Bağımlılıklar:
- servisler.sweep_service
- servisler.telegram_service
- config.settings
"""

import logging
from fastapi import APIRouter, Form
from servisler.sweep_service import CoboSweepService
from servisler.telegram_service import send_telegram_msg
from config.settings import COBO_WALLET_ID

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Telegram"])


@router.post("/telegram_command")
async def telegram_command(command: str = Form(...)):
    """
    Telegram bot komutlarını işle
    """
    logger.info(f"📨 Telegram komutu alındı: {command}")

    try:
        if command.strip().lower() == "/sweep":
            return await _handle_sweep_command()

        elif command.strip().lower() == "/admin":
            return _handle_admin_command()

        else:
            return {"status": "error", "message": "Unknown command"}

    except Exception as e:
        logger.error(f"❌ Telegram command error: {e}")
        send_telegram_msg(f"❌ <b>KOMUT HATASI</b>\n⚠️ {str(e)}")
        return {"status": "error", "message": str(e)}


async def _handle_sweep_command():
    """
    /sweep komutunu işler - Wallet durumunu gösterir
    """
    logger.info("🔍 /sweep komutu işleniyor...")
    sweep_service = CoboSweepService()

    logger.info(f"💼 Wallet ID: {COBO_WALLET_ID}")

    if not COBO_WALLET_ID:
        logger.error("❌ Wallet ID bulunamadı!")
        send_telegram_msg("❌ COBO_WALLET_ID .env dosyasında tanımlı değil!")
        return {"status": "error", "message": "Wallet ID not configured"}

    send_telegram_msg("🔍 <b>WALLET DURUMU KONTROL EDİLİYOR...</b>")

    try:
        # Wallet bilgilerini al
        wallet_info = sweep_service.get_wallet_info(COBO_WALLET_ID)

        if not wallet_info.get("success"):
            error_detail = wallet_info.get("error", "Bilinmeyen hata")
            send_telegram_msg(
                f"❌ <b>WALLET BİLGİSİ ALINAMADI</b>\n\n"
                f"⚠️ {error_detail}\n\n"
                f"💡 <i>API Key izinlerini kontrol edin "
                f"(Cobo Portal → Developer Console → API Keys)</i>"
            )
            return {"status": "error", "message": error_detail}

        # Son işlemleri listele
        transactions = sweep_service.list_transactions(COBO_WALLET_ID, limit=10)

        # Rapor oluştur
        msg = "📊 <b>COBO WALLET RAPORU</b>\n\n"
        msg += f"🆔 <b>Wallet ID:</b> <code>{COBO_WALLET_ID[:8]}...</code>\n"

        if wallet_info.get("data"):
            w_data = wallet_info["data"]
            msg += f"📛 <b>İsim:</b> {w_data.get('name', 'N/A')}\n"
            msg += f"🏷️ <b>Tip:</b> {w_data.get('wallet_type', 'N/A')}\n"

        # Son işlemler
        if transactions.get("success") and transactions.get("data"):
            tx_list = transactions["data"].get("data", [])
            if tx_list:
                msg += f"\n📝 <b>Son {len(tx_list)} İşlem:</b>\n"
                for tx in tx_list[:5]:  # İlk 5 işlem
                    tx_type = tx.get("type", "N/A")
                    amount = tx.get("amount", "0")
                    status = tx.get("status", "N/A")
                    msg += f"  • {tx_type}: {amount} ({status})\n"
            else:
                msg += "\n📝 <b>İşlem:</b> Henüz işlem yok\n"
        else:
            msg += "\n📝 <b>İşlemler:</b> Yüklenemedi\n"

        msg += "\n💡 <i>Auto Sweep Cobo Portal'da otomatik çalışıyor.</i>"

        send_telegram_msg(msg)
        return {"status": "success", "message": "Wallet info retrieved"}

    except Exception as e:
        error_msg = str(e)
        send_telegram_msg(
            f"❌ <b>HATA</b>\n"
            f"⚠️ {error_msg}\n\n"
            f"💡 <i>Detaylar için logları kontrol edin.</i>"
        )
        return {"status": "error", "message": error_msg}


def _handle_admin_command():
    """
    /admin komutunu işler - Admin panel linkini gönderir
    """
    admin_url = "https://srv.cepteportfoy.com/admin.html"
    msg = (
        f"🔑 <b>ADMIN PANEL ERİŞİMİ</b>\n\n"
        f"🌐 {admin_url}\n\n"
        f"💡 <i>Panel üzerinden para çekme ve istatistikleri yönetebilirsiniz.</i>"
    )
    send_telegram_msg(msg)
    return {"status": "success", "message": "Admin link sent"}
