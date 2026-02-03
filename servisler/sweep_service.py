"""
Cobo WaaS 2.0 Wallet Info Service
Bu modül Cobo Portal'daki wallet bilgilerini ve işlemleri görüntüler.
"""
import os
from dotenv import load_dotenv
import cobo_waas2
from cobo_waas2 import ApiClient, Configuration

load_dotenv()

class CoboSweepService:
    def __init__(self):
        self.api_key = os.getenv("COBO_API_KEY")
        self.api_secret = os.getenv("COBO_API_SECRET")
        
        # Cobo WaaS2 SDK Configuration
        self.configuration = Configuration(
            api_private_key=self.api_secret,
            host="https://api.cobo.com/v2"
        )
    
    def get_wallet_info(self, wallet_id):
        """
        Wallet bilgilerini al
        
        Args:
            wallet_id: Cobo Portal'daki wallet ID
        
        Returns:
            Wallet bilgileri
        """
        try:
            with ApiClient(self.configuration) as api_client:
                api_client.set_default_header("Biz-Api-Key", self.api_key)
                api_instance = cobo_waas2.WalletsApi(api_client)
                
                result = api_instance.get_wallet_by_id(wallet_id=wallet_id)
                return {"success": True, "data": result.to_dict()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_addresses(self, wallet_id, chain_id="TRON", limit=50):
        """
        Wallet'taki tüm adresleri listele
        
        Args:
            wallet_id: Wallet ID
            chain_id: Blockchain
            limit: Maksimum adres sayısı
        
        Returns:
            Adres listesi
        """
        try:
            with ApiClient(self.configuration) as api_client:
                api_client.set_default_header("Biz-Api-Key", self.api_key)
                api_instance = cobo_waas2.WalletsApi(api_client)
                
                result = api_instance.list_addresses(
                    wallet_id=wallet_id,
                    chain_ids=chain_id,
                    limit=limit
                )
                return {"success": True, "data": result.to_dict()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def check_balances(self, wallet_id):
        """
        Tüm adreslerdeki bakiyeleri kontrol et
        
        Args:
            wallet_id: Wallet ID
        
        Returns:
            Bakiye raporu
        """
        print(f"💰 Bakiyeler kontrol ediliyor...")
        
        # TRX adresleri
        trx_addresses = self.list_addresses(wallet_id, "TRON")
        
        address_count = 0
        
        if trx_addresses.get("success") and trx_addresses.get("data"):
            addresses = trx_addresses["data"].get("data", [])
            address_count = len(addresses)
                
        wallet_info = self.get_wallet_info(wallet_id)
        
        return {
            "wallet_id": wallet_id,
            "address_count": address_count,
            "wallet_info": wallet_info
        }
    
    
    def get_token_balances(self, wallet_id, limit=50):
        """
        Wallet'taki bakiye bilgilerini al
        
        Args:
            wallet_id: Wallet ID
        
        Returns:
            Bakiye listesi
        """
        try:
            with ApiClient(self.configuration) as api_client:
                api_client.set_default_header("Biz-Api-Key", self.api_key)
                api_instance = cobo_waas2.WalletsApi(api_client)
                
                result = api_instance.list_token_balances_for_wallet(
                    wallet_id=wallet_id,
                    limit=limit
                )
                return {"success": True, "data": result.to_dict()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_transactions(self, wallet_id, limit=10):
        """
        Son işlemleri listele
        
        Args:
            wallet_id: Wallet ID
            limit: Maksimum kayıt sayısı
        
        Returns:
            İşlem listesi
        """
        try:
            with ApiClient(self.configuration) as api_client:
                api_client.set_default_header("Biz-Api-Key", self.api_key)
                api_instance = cobo_waas2.TransactionsApi(api_client)
                
                result = api_instance.list_transactions(
                    wallet_ids=wallet_id,
                    limit=limit
                )
                return {"success": True, "data": result.to_dict()}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Test fonksiyonu
if __name__ == "__main__":
    service = CoboSweepService()
    
    # Wallet ID'nizi buraya girin (Cobo Portal -> Wallets'tan alabilirsiniz)
    WALLET_ID = os.getenv("COBO_WALLET_ID", "YOUR_WALLET_ID_HERE")
    
    print("=" * 50)
    print("Cobo Wallet Info Test")
    print("=" * 50)
    
    # Wallet bilgilerini al
    result = service.get_wallet_info(WALLET_ID)
    print(f"\nWallet Info: {json.dumps(result, indent=2)}")
    
    # Son işlemleri listele
    transactions = service.list_transactions(WALLET_ID, limit=5)
    print(f"\nSon İşlemler: {json.dumps(transactions, indent=2)}")
