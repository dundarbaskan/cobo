"""
Cobo Withdrawal Service
=======================
Para çekme ve transfer işlemlerini yöneten servis.

Cobo WaaS 2.0 SDK kullanır. source ve destination alanlarında
ham dict DEĞİL, SDK'nın kendi model nesneleri kullanılır.
Bu, error_code=2006 "Parameter source is not valid dict" hatasını önler.
"""
import uuid
import certifi
from cobo_waas2 import ApiClient, Configuration
import cobo_waas2

from config.settings import COBO_API_KEY, COBO_API_SECRET, COBO_API_HOST


class CoboWithdrawalService:
    def __init__(self):
        self.configuration = Configuration(
            api_private_key=COBO_API_SECRET,
            host=COBO_API_HOST
        )
        # SSL sertifika doğrulaması (Windows/uzak sunucu uyumluluğu için)
        self.configuration.ssl_ca_cert = certifi.where()

    def create_withdrawal(
        self,
        wallet_id: str,
        to_address: str,
        amount,
        token_id: str = "USDT",
        chain_id: str = "TRON",
        note: str = ""
    ) -> dict:
        """
        Para çekme / transfer işlemi oluştur.

        Args:
            wallet_id:  Kaynak Org-Controlled cüzdan ID'si
            to_address: Hedef blockchain adresi
            amount:     Çekilecek miktar (float veya string)
            token_id:   Token sembolü (ör: USDT, ETH, BTC)
            chain_id:   Blockchain (ör: TRON, ETH, BTC)
            note:       İşlem açıklaması

        Returns:
            dict: {"success": bool, "data": dict, "request_id": str}
                  Hata durumunda: {"success": False, "error": str}
        """
        try:
            with ApiClient(self.configuration) as api_client:
                api_client.set_default_header("Biz-Api-Key", COBO_API_KEY)
                transactions_api = cobo_waas2.TransactionsApi(api_client)

                request_id = f"withdrawal_{uuid.uuid4().hex[:16]}"

                # ── Source: Org-Controlled cüzdan (SDK model nesnesi) ────────
                transfer_source = cobo_waas2.OrgControlledTransferSource(
                    source_type=cobo_waas2.TransferSourceType.ORG_CONTROLLED,
                    wallet_id=wallet_id
                )

                # ── Destination: Hedef adres (SDK model nesnesi) ─────────────
                account_output = cobo_waas2.AddressTransferDestinationAccountOutput(
                    address=to_address,
                    amount=str(amount)
                )
                transfer_destination = cobo_waas2.AddressTransferDestination(
                    destination_type=cobo_waas2.TransferDestinationType.ADDRESS,
                    account_output=account_output
                )

                # ── Transfer parametreleri ────────────────────────────────────
                transfer_params = cobo_waas2.TransferParams(
                    request_id=request_id,
                    source=transfer_source,
                    token_id=token_id,
                    destination=transfer_destination,
                    category_names=["Withdrawal"],
                    description=note if note else "Manual withdrawal"
                )

                result = transactions_api.create_transfer_transaction(
                    transfer_params=transfer_params
                )

                return {
                    "success": True,
                    "data": result.to_dict() if hasattr(result, "to_dict") else result,
                    "request_id": request_id
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_transaction_status(self, transaction_id: str) -> dict:
        """
        İşlem durumunu kontrol et.

        Args:
            transaction_id: Cobo transaction ID

        Returns:
            dict: {"success": bool, "data": dict}
        """
        try:
            with ApiClient(self.configuration) as api_client:
                api_client.set_default_header("Biz-Api-Key", COBO_API_KEY)
                transactions_api = cobo_waas2.TransactionsApi(api_client)

                result = transactions_api.get_transaction_by_id(
                    transaction_id=transaction_id
                )

                return {
                    "success": True,
                    "data": result.to_dict() if hasattr(result, "to_dict") else result
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def estimate_fee(
        self,
        wallet_id: str,
        to_address: str,
        amount,
        token_id: str = "USDT"
    ) -> dict:
        """
        İşlem ücretini tahmin et.

        Args:
            wallet_id:  Kaynak cüzdan ID'si
            to_address: Hedef adres
            amount:     Tahmin için miktar
            token_id:   Token sembolü

        Returns:
            dict: {"success": bool, "fee": dict}
        """
        try:
            with ApiClient(self.configuration) as api_client:
                api_client.set_default_header("Biz-Api-Key", COBO_API_KEY)
                transactions_api = cobo_waas2.TransactionsApi(api_client)

                fee_source = cobo_waas2.OrgControlledTransferSource(
                    source_type=cobo_waas2.TransferSourceType.ORG_CONTROLLED,
                    wallet_id=wallet_id
                )

                fee_account_output = cobo_waas2.AddressTransferDestinationAccountOutput(
                    address=to_address,
                    amount=str(amount)
                )
                fee_destination = cobo_waas2.AddressTransferDestination(
                    destination_type=cobo_waas2.TransferDestinationType.ADDRESS,
                    account_output=fee_account_output
                )

                fee_params = cobo_waas2.EstimateFeeParams(
                    source=fee_source,
                    token_id=token_id,
                    destination=fee_destination
                )

                result = transactions_api.estimate_fee(
                    estimate_fee_params=fee_params
                )

                return {
                    "success": True,
                    "fee": result.to_dict() if hasattr(result, "to_dict") else result
                }

        except Exception as e:
            return {"success": False, "error": str(e), "fee": "Unknown"}
