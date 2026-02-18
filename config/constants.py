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


# ============================================================
# TÜRKİYE'DEKİ AKTİF BANKALAR
# Logo URL'leri clearbit CDN üzerinden çekilir:
#   https://logo.clearbit.com/{domain}
# Frontend'de fallback: /static/banks/default.png
# ============================================================

TR_BANKS = [
    {"name": "Ziraat Bankası",     "domain": "ziraatbank.com.tr"},
    {"name": "Halkbank",           "domain": "halkbank.com.tr"},
    {"name": "Vakıfbank",          "domain": "vakifbank.com.tr"},
    {"name": "İş Bankası",         "domain": "isbank.com.tr"},
    {"name": "Garanti BBVA",       "domain": "garantibbva.com.tr"},
    {"name": "Akbank",             "domain": "akbank.com"},
    {"name": "Yapı Kredi",         "domain": "yapikredi.com.tr"},
    {"name": "QNB Finansbank",     "domain": "qnbfinansbank.com"},
    {"name": "Denizbank",          "domain": "denizbank.com"},
    {"name": "TEB",                "domain": "teb.com.tr"},
    {"name": "Şekerbank",          "domain": "sekerbank.com.tr"},
    {"name": "Kuveyt Türk",        "domain": "kuveytturk.com.tr"},
    {"name": "Albaraka Türk",      "domain": "albarakaturk.com.tr"},
    {"name": "Ziraat Katılım",     "domain": "ziraatkatilim.com.tr"},
    {"name": "Vakıf Katılım",      "domain": "vakifkatilim.com.tr"},
    {"name": "ING Bank",           "domain": "ingbank.com.tr"},
    {"name": "HSBC Türkiye",       "domain": "hsbc.com.tr"},
    {"name": "Odeabank",           "domain": "odeabank.com.tr"},
    {"name": "Fibabanka",          "domain": "fibabanka.com.tr"},
    {"name": "Burgan Bank",        "domain": "burgan.com.tr"},
    {"name": "Türkiye Finans",     "domain": "turkiyefinans.com.tr"},
    {"name": "Halk Katılım",       "domain": "halkkatilim.com.tr"},
]
