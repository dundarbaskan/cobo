"""
Admin Panel API Endpoints
Bu dosyayı main.py'ye import edin
"""
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import os
from servisler.sweep_service import CoboSweepService
from servisler.withdrawal_service import CoboWithdrawalService

router = APIRouter()
security = HTTPBasic()

# Admin Kimlik Bilgileri
ADMIN_USERNAME = "besimtrump18"
ADMIN_PASSWORD = "Bg180913*"

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hatalı kullanıcı adı veya şifre",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def send_telegram_msg(message):
    """Telegram mesajı gönder"""
    import requests
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})

@router.get("/admin")
async def admin_panel(username: str = Depends(authenticate)):
    """Admin panel HTML sayfası"""
    with open("admin.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@router.get("/api/admin/dashboard")
async def admin_dashboard(username: str = Depends(authenticate)):
    """Dashboard istatistikleri"""
    try:
        sweep_service = CoboSweepService()
        wallet_id = os.getenv("COBO_WALLET_ID")
        
        addresses = sweep_service.list_addresses(wallet_id, "TRON", limit=100)
        transactions = sweep_service.list_transactions(wallet_id, limit=100)
        balances = sweep_service.get_token_balances(wallet_id)
        
        # Toplam USDT bakiyesini bul
        total_usdt = "0.00"
        if balances.get("success"):
            token_list = balances["data"].get("data", [])
            for token in token_list:
                if "USDT" in token.get("token_id", ""):
                    total_usdt = token.get("balance", {}).get("total", "0.00")
                    break
        
        return {
            "success": True,
            "balance": f"{total_usdt} USDT",
            "balances": balances.get("data", {}).get("data", []) if balances.get("success") else [],
            "addresses": len(addresses.get("data", {}).get("data", [])) if addresses.get("success") else 0,
            "transactions": len(transactions.get("data", {}).get("data", [])) if transactions.get("success") else 0
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/api/admin/wallet")
async def admin_wallet(username: str = Depends(authenticate)):
    """Wallet bilgileri"""
    try:
        sweep_service = CoboSweepService()
        wallet_id = os.getenv("COBO_WALLET_ID")
        
        result = sweep_service.get_wallet_info(wallet_id)
        
        if result.get("success"):
            return {"success": True, "data": result["data"]}
        else:
            return {"success": False, "error": result.get("error")}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/api/admin/addresses")
async def admin_addresses(username: str = Depends(authenticate)):
    """Adres listesi"""
    try:
        sweep_service = CoboSweepService()
        wallet_id = os.getenv("COBO_WALLET_ID")
        
        result = sweep_service.list_addresses(wallet_id, "TRON", limit=50)
        
        if result.get("success"):
            addresses = result["data"].get("data", [])
            return {"success": True, "data": addresses}
        else:
            return {"success": False, "error": result.get("error")}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/api/admin/transactions")
async def admin_transactions(type: str = None, username: str = Depends(authenticate)):
    """İşlem listesi"""
    try:
        sweep_service = CoboSweepService()
        wallet_id = os.getenv("COBO_WALLET_ID")
        
        result = sweep_service.list_transactions(wallet_id, limit=50)
        
        if result.get("success"):
            raw_transactions = result["data"].get("data", [])
            
            # Verileri normalize et (Miktar ve Token ID'yi düzleştir)
            transactions = []
            for tx in raw_transactions:
                # Cobo WaaS 2.0 structure flattening - Daha detaylı kontrol
                amount = tx.get("amount")
                token_id = tx.get("token_id") or tx.get("asset_id")
                to_addr = tx.get("to_address")

                # Eğer ana seviyede yoksa destination içinden bak (Örn: Çekim işlemleri)
                dest = tx.get("destination", {})
                if isinstance(dest, list) and len(dest) > 0:
                    dest = dest[0] # Listeyse ilkini al
                
                if not amount and isinstance(dest, dict):
                    amount = dest.get("amount")
                if not to_addr and isinstance(dest, dict):
                    to_addr = dest.get("address")
                
                # HALA YOKSA (Örn: Yatırım işlemleri - Source kısmında olabilir veya SDK farklı dönmüştür)
                if not amount: amount = "0"
                if not token_id: token_id = "USDT"
                if not to_addr: to_addr = "N/A"

                tx_data = {
                    "transaction_id": tx.get("transaction_id"),
                    "type": tx.get("type"),
                    "status": tx.get("status"),
                    "created_timestamp": tx.get("created_timestamp"),
                    "amount": amount,
                    "token_id": token_id,
                    "to_address": to_addr
                }
                
                # Tip filtreleme
                if not type or tx_data.get("type").upper() == type.upper():
                    transactions.append(tx_data)
            
            return {"success": True, "data": transactions}
        else:
            return {"success": False, "error": result.get("error")}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/api/admin/withdrawal")
async def admin_withdrawal(request: Request, username: str = Depends(authenticate)):
    """Para çekme işlemi"""
    try:
        data = await request.json()
        
        withdrawal_service = CoboWithdrawalService()
        wallet_id = os.getenv("COBO_WALLET_ID")
        
        result = withdrawal_service.create_withdrawal(
            wallet_id=wallet_id,
            to_address=data.get("to_address"),
            amount=data.get("amount"),
            token_id=data.get("token_id", "USDT"),
            chain_id=data.get("chain_id", "TRON"),
            note=data.get("note", "")
        )
        
        if result.get("success"):
            return {
                "success": True,
                "request_id": result.get("request_id"),
                "data": result.get("data")
            }
        else:
            return {"success": False, "error": result.get("error")}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/api/admin/sweep")
async def admin_sweep(request: Request, username: str = Depends(authenticate)):
    """Tüm bakiyeleri tek bir adrese topla (Sweep)"""
    try:
        data = await request.json()
        main_address = data.get("main_address")
        
        if not main_address:
            return {"success": False, "error": "Lütfen bir ana adres (Main Address) girin."}
            
        sweep_service = CoboSweepService()
        withdrawal_service = CoboWithdrawalService()
        wallet_id = os.getenv("COBO_WALLET_ID")
        
        # Bakiyeleri al
        balances_res = sweep_service.get_token_balances(wallet_id)
        if not balances_res.get("success"):
            return {"success": False, "error": "Bakiyeler alınamadı."}
            
        token_list = balances_res["data"].get("data", [])
        sweep_results = []
        
        for token in token_list:
            total_balance_str = token.get("balance", {}).get("total", "0")
            try:
                total_balance = float(total_balance_str)
            except:
                total_balance = 0
                
            token_id = token.get("token_id")
            blockchain_id = token.get("blockchain_id")
            
            if total_balance > 0:
                # Para çekme talebi oluştur
                result = withdrawal_service.create_withdrawal(
                    wallet_id=wallet_id,
                    to_address=main_address,
                    amount=total_balance_str,
                    token_id=token_id,
                    chain_id=blockchain_id,
                    note=f"Manual Sweep: {token_id}"
                )
                
                sweep_results.append({
                    "token": token_id,
                    "amount": total_balance_str,
                    "success": result.get("success"),
                    "request_id": result.get("request_id"),
                    "error": result.get("error") if not result.get("success") else None
                })
        
        # Telegram bildirimi kaldırıldı
            
        return {
            "success": True,
            "results": sweep_results
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
