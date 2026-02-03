"""
Cobo Withdrawal Service
Para çekme işlemlerini yöneten servis
"""
import os
import uuid
from dotenv import load_dotenv
import cobo_waas2
from cobo_waas2 import ApiClient, Configuration

load_dotenv()

class CoboWithdrawalService:
    def __init__(self):
        self.api_key = os.getenv("COBO_API_KEY")
        self.api_secret = os.getenv("COBO_API_SECRET")
        
        self.configuration = Configuration(
            api_private_key=self.api_secret,
            host="https://api.cobo.com/v2"
        )
    
    def create_withdrawal(self, wallet_id, to_address, amount, token_id="USDT", chain_id="TRON", note=""):
        """
        Para çekme işlemi oluştur
        
        Args:
            wallet_id: Kaynak wallet ID
            to_address: Hedef adres
            amount: Çekilecek miktar (float veya string)
            token_id: Token adı (varsayılan: USDT)
            chain_id: Blockchain (varsayılan: TRON)
            note: İşlem notu
        
        Returns:
            dict: {"success": bool, "data": dict, "request_id": str}
        """
        try:
            with ApiClient(self.configuration) as api_client:
                api_client.set_default_header("Biz-Api-Key", self.api_key)
                api_instance = cobo_waas2.TransactionsApi(api_client)
                
                request_id = f"withdrawal_{uuid.uuid4().hex[:16]}"
                
                # Transfer parametreleri
                from cobo_waas2.models import TransferParams
                
                transfer_params = TransferParams(
                    request_id=request_id,
                    source={
                        "source_type": "Org-Controlled",
                        "wallet_id": wallet_id
                    },
                    token_id=token_id,
                    destination={
                        "destination_type": "Address",
                        "account_output": {
                            "address": to_address,
                            "amount": str(amount)
                        }
                    },
                    category_names=["Withdrawal"],
                    description=note if note else "Manual withdrawal"
                )
                
                result = api_instance.create_transfer_transaction(transfer_params=transfer_params)
                
                return {
                    "success": True,
                    "data": result.to_dict() if hasattr(result, 'to_dict') else result,
                    "request_id": request_id
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_transaction_status(self, transaction_id):
        """
        İşlem durumunu kontrol et
        
        Args:
            transaction_id: İşlem ID
        
        Returns:
            dict: {"success": bool, "data": dict}
        """
        try:
            with ApiClient(self.configuration) as api_client:
                api_client.set_default_header("Biz-Api-Key", self.api_key)
                api_instance = cobo_waas2.TransactionsApi(api_client)
                
                result = api_instance.get_transaction_by_id(transaction_id=transaction_id)
                
                return {
                    "success": True,
                    "data": result.to_dict() if hasattr(result, 'to_dict') else result
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def estimate_fee(self, wallet_id, to_address, amount, token_id="USDT"):
        """
        İşlem ücretini tahmin et
        
        Args:
            wallet_id: Kaynak wallet ID
            to_address: Hedef adres
            amount: Miktar
            token_id: Token adı
        
        Returns:
            dict: {"success": bool, "fee": str}
        """
        try:
            with ApiClient(self.configuration) as api_client:
                api_client.set_default_header("Biz-Api-Key", self.api_key)
                api_instance = cobo_waas2.TransactionsApi(api_client)
                
                # Fee estimation request
                from cobo_waas2.models import EstimateFeeParams
                
                params = EstimateFeeParams(
                    source={
                        "source_type": "Org-Controlled",
                        "wallet_id": wallet_id
                    },
                    token_id=token_id,
                    destination={
                        "destination_type": "Address",
                        "account_output": {
                            "address": to_address,
                            "amount": str(amount)
                        }
                    }
                )
                
                result = api_instance.estimate_fee(estimate_fee_params=params)
                
                return {
                    "success": True,
                    "fee": result.to_dict() if hasattr(result, 'to_dict') else result
                }
        except Exception as e:
            # Fee estimation başarısız olursa varsayılan değer dön
            return {"success": False, "error": str(e), "fee": "Unknown"}
