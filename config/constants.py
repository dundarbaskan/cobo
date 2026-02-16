"""
İş Kuralları Sabitleri
======================
Sistemin karar verme mekanizmasında kullanılan tüm sabit listeler ve eşlemeler.

DİKKAT: Bu sabitler doğrudan para akışını etkiler. Değişiklik yaparken dikkatli olun!
"""

# Engellenen İşlem Tipleri
# Sadece DEPOSIT ve RECEIVE kabul edilir, diğer her şey engellenir
BLOCKED_TYPES = [
    "WITHDRAWAL",
    "SWEEP",
    "TRANSFER",
    "TRANSFER_OUT",
    "TRANSFER_IN",
    "INTERNAL_TRANSFER",
    "CONSOLIDATION",
    "COLLECTION"
]

# Kabul Edilen Token'lar
# Diğerleri spam/fake token olarak değerlendirilir
ALLOWED_TOKENS = [
    "USDT",
    "USDC",
    "TRX",
    "ETH",
    "BTC",
    "LTC",
    "SOL",
    "MATIC",
    "BNB",
    "XRP",
    "ADA",
    "DOT",
    "TRON"
]

# Chain İsim Eşlemeleri (Kullanıcı Dostu)
CHAIN_DISPLAY_NAMES = {
    "MATIC": "Polygon (MATIC)",
    "TRON": "TRON (TRC20)",
    "ETH": "Ethereum (ERC20)"
}

def get_display_chain_name(chain_id: str) -> str:
    """Chain ID'yi kullanıcı dostu isme çevirir"""
    return CHAIN_DISPLAY_NAMES.get(chain_id, chain_id)
