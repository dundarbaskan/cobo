"""
Bekleyen İşlem Store'u (In-Memory)
===================================
Telegram onayı beklenen işlemleri geçici olarak tutar.

V2.0 - Onay bekleyen işlemler için in-memory cache.
       key: transaction_id, value: işlem payload dict'i
       NOT: Sunucu restart olursa bekleyen onaylar silinir.
"""

# V2.0 - In-memory bekleyen işlem deposu. key=transaction_id
pending_transactions: dict = {}
