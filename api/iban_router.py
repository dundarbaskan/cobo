"""
IBAN Yatırım & Çekim Router'ı
==============================

Kullanıcı Endpoint'leri:
  GET  /api/iban/active          → Aktif IBAN bilgisini döner
  POST /api/iban/copy-notify     → IBAN kopyalandı bildirimi (Telegram)
  POST /api/iban/withdrawal      → Çekim talebi (Telegram)

Admin Endpoint'leri (HTTP Basic Auth):
  GET    /api/admin/ibans              → Tüm IBAN listesi
  POST   /api/admin/ibans              → Yeni IBAN ekle
  PUT    /api/admin/ibans/{id}/activate   → Aktif et
  PUT    /api/admin/ibans/{id}/deactivate → Pasif et
  DELETE /api/admin/ibans/{id}            → Sil

Bağımlılıklar:
  - servisler.db_service (IBAN CRUD)
  - servisler.telegram_service (Bildirim)
  - admin_api.authenticate (HTTP Basic Auth — DRY)
"""

import logging
from fastapi import APIRouter, Form, Depends, HTTPException
from fastapi.responses import JSONResponse

from servisler.db_service import (
    get_active_iban,
    get_all_ibans,
    save_iban,
    set_iban_active,
    set_iban_inactive,
    delete_iban,
    get_lead_by_tp,
)
from servisler.telegram_service import send_telegram_msg
from admin_api import authenticate

logger = logging.getLogger(__name__)

router = APIRouter(tags=["IBAN"])


# ─────────────────────────────────────────
# KULLANICI ENDPOİNT'LERİ
# ─────────────────────────────────────────

@router.get("/api/iban/active")
async def get_active_iban_endpoint():
    """
    Aktif IBAN bilgisini döner.
    Aktif IBAN yoksa 404 döner — frontend buna göre uyarı gösterir.
    """
    iban = await get_active_iban()
    if not iban:
        raise HTTPException(status_code=404, detail="Aktif IBAN bulunamadı.")
    return {
        "bank_name": iban.get("bank_name"),
        "iban": iban.get("iban"),
        "account_holder": iban.get("account_holder"),
    }


@router.post("/api/iban/copy-notify")
async def iban_copy_notify(tp_number: str = Form(...)):
    """
    Kullanıcı IBAN'ı kopyaladığında çağrılır.
    Telegram grubuna bildirim atar.
    """
    lead = await get_lead_by_tp(tp_number)
    if not lead:
        raise HTTPException(status_code=404, detail="TP Number bulunamadı.")

    iban = await get_active_iban()
    if not iban:
        raise HTTPException(status_code=404, detail="Aktif IBAN bulunamadı.")

    name = lead.get("name", "Bilinmeyen")

    msg = (
        f"📋 <b>IBAN KOPYALANDI</b>\n"
        f"MOBİL UYGULAMA\n\n"
        f"<b>Ad Soyad:</b> {name.upper()}\n"
        f"<b>TP NUMBER :</b> <code>{tp_number}</code>\n"
        f"<b>Kopyalanan IBAN:</b> <code>{iban.get('iban')}</code>\n"
        f"<b>Banka:</b> {iban.get('bank_name')}"
    )
    send_telegram_msg(msg)
    logger.info(f"📋 IBAN kopyalama bildirimi: {name} (TP: {tp_number})")

    return {"status": "success", "message": "Bildirim gönderildi."}


@router.post("/api/iban/withdrawal")
async def iban_withdrawal(
    tp_number: str = Form(...),
    alici_adi: str = Form(...),
    alici_iban: str = Form(...),
    tutar: str = Form(...),
    banka_adi: str = Form(...),
):
    """
    Çekim talebi oluşturur ve Telegram'a bildirim gönderir.
    """
    lead = await get_lead_by_tp(tp_number)
    if not lead:
        raise HTTPException(status_code=404, detail="TP Number bulunamadı.")

    name = lead.get("name", "Bilinmeyen")

    msg = (
        f"💸 <b>BANKA ÇEKİM TALEBİ</b>\n"
        f"MOBİL UYGULAMA\n\n"
        f"<b>Ad Soyad:</b> {name.upper()}\n"
        f"<b>TP NUMBER :</b> <code>{tp_number}</code>\n"
        f"<b>Alıcı Adı:</b> {alici_adi.upper()}\n"
        f"<b>Alıcı IBAN:</b> <code>{alici_iban.upper()}</code>\n"
        f"<b>Banka:</b> {banka_adi}\n"
        f"<b>Çekim Tutarı:</b> {tutar} ₺"
    )
    send_telegram_msg(msg)
    logger.info(f"💸 Çekim talebi: {name} (TP: {tp_number}) - {tutar} ₺")

    return {"status": "success", "message": "Çekim talebiniz alındı."}


# ─────────────────────────────────────────
# ADMİN ENDPOİNT'LERİ (HTTP Basic Auth)
# ─────────────────────────────────────────

@router.get("/api/admin/ibans")
async def admin_list_ibans(request: Request):
    """Tüm IBAN kayıtlarını döner."""
    authenticate_iban(request)
    ibans = await get_all_ibans()
    return {"status": "success", "ibans": ibans}


@router.post("/api/admin/ibans")
async def admin_add_iban(
    request: Request,
    bank_name: str = Form(...),
    iban: str = Form(...),
    account_holder: str = Form(...),
):
    """Yeni IBAN ekler (pasif olarak)."""
    authenticate_iban(request)
    iban_data = {
        "bank_name": bank_name,
        "iban": iban.upper().replace(" ", "").replace("\u00a0", ""),
        "account_holder": account_holder,
    }
    new_id = await save_iban(iban_data)
    logger.info(f"➕ Yeni IBAN eklendi: {bank_name} — {iban}")
    return {"status": "success", "id": new_id, "message": "IBAN eklendi."}


@router.put("/api/admin/ibans/{iban_id}/activate")
async def admin_activate_iban(iban_id: str, request: Request):
    """Belirtilen IBAN'ı aktif eder. Diğerleri otomatik pasife alınır."""
    authenticate_iban(request)
    try:
        await set_iban_active(iban_id)
        logger.info(f"✅ IBAN aktif edildi: {iban_id}")
        return {"status": "success", "message": "IBAN aktif edildi."}
    except Exception as e:
        logger.error(f"❌ IBAN aktifleştirme hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/api/admin/ibans/{iban_id}/deactivate")
async def admin_deactivate_iban(iban_id: str, request: Request):
    """Belirtilen IBAN'ı pasif eder."""
    authenticate_iban(request)
    try:
        await set_iban_inactive(iban_id)
        logger.info(f"⚫ IBAN pasif edildi: {iban_id}")
        return {"status": "success", "message": "IBAN pasif edildi."}
    except Exception as e:
        logger.error(f"❌ IBAN pasifleştirme hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api/admin/ibans/{iban_id}")
async def admin_delete_iban(iban_id: str, request: Request):
    """Belirtilen IBAN kaydını siler."""
    authenticate_iban(request)
    try:
        await delete_iban(iban_id)
        logger.info(f"🗑 IBAN silindi: {iban_id}")
        return {"status": "success", "message": "IBAN silindi."}
    except Exception as e:
        logger.error(f"❌ IBAN silme hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))

