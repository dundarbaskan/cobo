"""
Cobo Coin Yönlendirme Modülü (Routing)
========================================
Gelen kripto para türüne göre hangi Cobo cüzdanına yönlendirileceğini belirler.

.env değişkenleri:
  MAIN_WALLET             → USDT yatırımları için ana kasa
  ETH_CONVERTER_WALLET    → ETH dönüşüm cüzdanı
  BTC_CONVERTER_WALLET    → BTC dönüşüm cüzdanı
  TRX_CONVERTER_WALLET    → TRX/TRON dönüşüm cüzdanı
"""

import os

# V2.0 - Cüzdan adresleri .env'den okunur. Yönlendirme bu adreslere göre yapılır.
MAIN_WALLET = os.getenv("MAIN_WALLET", "")
ETH_CONVERTER_WALLET = os.getenv("ETH_CONVERTER_WALLET", "")
BTC_CONVERTER_WALLET = os.getenv("BTC_CONVERTER_WALLET", "")
TRX_CONVERTER_WALLET = os.getenv("TRX_CONVERTER_WALLET", "")


def get_target_wallet(symbol: str) -> tuple:
    """
    V2.0 - Coin türüne göre hedef cüzdan adresini ve etiketini döner.

    Args:
        symbol: Cobo'dan gelen token_id (ör: USDT, ETH, BTC, TRX, TRON)

    Returns:
        tuple: (wallet_address: str, wallet_label: str, is_main: bool)
               is_main=True  → Ana kasaya yönlendirildi (USDT)
               is_main=False → Convert cüzdanına yönlendirildi
    """
    symbol_upper = (symbol or "").upper()

    # USDT → Ana kasa
    if "USDT" in symbol_upper or "USDC" in symbol_upper:
        return (MAIN_WALLET, "Ana Kasa", True)

    # ETH → ETH Convert cüzdanı
    if "ETH" in symbol_upper:
        return (ETH_CONVERTER_WALLET, "ETH Convert Cüzdanı", False)

    # BTC → BTC Convert cüzdanı
    if "BTC" in symbol_upper:
        return (BTC_CONVERTER_WALLET, "BTC Convert Cüzdanı", False)

    # TRX / TRON → TRX Convert cüzdanı
    if "TRX" in symbol_upper or "TRON" in symbol_upper:
        return (TRX_CONVERTER_WALLET, "TRX Convert Cüzdanı", False)

    # Bilinmeyen coin → Varsayılan olarak ana kasaya yönlendir
    return (MAIN_WALLET, "Ana Kasa (Varsayılan)", True)
