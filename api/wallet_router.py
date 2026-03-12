"""
Cüzdan İşlemleri Router'ı
=========================
- verify_tp: Müşteri TP numarasını doğrular ve bilgilerini döndürür
- create_wallet: Cobo API üzerinden yeni cüzdan oluşturur

Bağımlılıklar:
- servisler.db_service
- servisler.qr_service
- config.settings
"""

import os
from datetime import datetime
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
import cobo_waas2
from cobo_waas2 import ApiClient, Configuration, CreateAddressRequest
import urllib3

# InsecureRequestWarning uyarısını gizle
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from servisler.db_service import (
    get_lead_by_tp,
    save_wallet_to_lead,
    get_existing_wallet
)
from servisler.qr_service import generate_qr_base64
from config.settings import COBO_API_KEY, COBO_API_SECRET, COBO_WALLET_ID, logger
from servisler.mt5_sync_util import force_sync_single_user

router = APIRouter(prefix="/api", tags=["Wallet"])


@router.post("/verify_tp")
async def verify_tp(tp_number: str = Form(...)):
    """TP numarasını doğrular ve müşteri bilgilerini döndürür"""
    lead = await get_lead_by_tp(tp_number)
    
    if not lead:
        # Fallback: manuel senkronizasyon tetikle ve tekrar kontrol et
        sync_success = await force_sync_single_user(tp_number)
        if sync_success:
            lead = await get_lead_by_tp(tp_number)
            
    if not lead:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": "TP Number bulunamadı!"}
        )

    mt5_data = {
        "balance": lead.get("balance", 0),
        "equity": lead.get("equity", 0),
        "credit": lead.get("credit", 0),
        "name": lead.get("name", "Değerli Yatırımcı")
    }

    return {
        "status": "success",
        "name": mt5_data.get("name"),
        "email": lead.get("email"),
        "mt5": mt5_data,
        "last_sync": lead.get("last_sync")
    }






@router.post("/create_wallet")
async def create_wallet(
    tp_number: str = Form(...),
    chain_id: str = Form(...),
    asset_name: str = Form(...)
):
    """Cobo API üzerinden yeni cüzdan oluşturur"""
    lead = await get_lead_by_tp(tp_number)
    
    if not lead:
        # Fallback: manuel senkronizasyon tetikle ve tekrar kontrol et
        sync_success = await force_sync_single_user(tp_number)
        if sync_success:
            lead = await get_lead_by_tp(tp_number)
            
    if not lead:
        raise HTTPException(status_code=404, detail="Geçersiz TP Number")

    # Chain ID'yi normalize et
    final_chain_id = "TRON" if chain_id == "USDT" else chain_id

    # Önce mevcut cüzdanı kontrol et
    existing_wallet = await get_existing_wallet(tp_number, asset_name, final_chain_id)
    if existing_wallet:
        return {
            "address": existing_wallet.get("address"),
            "qr_code": generate_qr_base64(existing_wallet.get("address")),
            "existing": True
        }

    try:
        configuration = Configuration(
            api_private_key=COBO_API_SECRET,
            host="https://api.cobo.com/v2"
        )

        # Windows SSL Hatası Çözümü - Tamamen atla
        configuration.verify_ssl = False

        with ApiClient(configuration) as api_client:
            # Set API Key header
            api_client.set_default_header("Biz-Api-Key", COBO_API_KEY)

            api_instance = cobo_waas2.WalletsApi(api_client)

            req = CreateAddressRequest(chain_id=final_chain_id, count=1)
            api_resp = api_instance.create_address(
                wallet_id=COBO_WALLET_ID,
                create_address_request=req
            )

            new_address = api_resp[0].address
            qr_base64 = generate_qr_base64(new_address)

            wallet_data = {
                "address": new_address,
                "chain_id": final_chain_id,
                "asset": asset_name,
                "created_at": datetime.now().isoformat()
            }

            await save_wallet_to_lead(tp_number, wallet_data)
            return {"address": new_address, "qr_code": qr_base64}

    except Exception as e:
        logger.error(f"❌ Cüzdan Oluşturma Hatası (TP: {tp_number}): {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(status_code=400, content={"error": str(e)})
