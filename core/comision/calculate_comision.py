"""
Komisyon Hesaplama Modülü
=========================
Kripto yatırım işlemlerinde uygulanacak komisyon tutarını hesaplar.

V2.0 - Komisyon oranı artık .env'den okunur (COMMISSION_RATE_PERCENT).
       Değeri değiştirmek için deploy gerekmez.
"""

import os
from config.settings import COMMISSION_RATE_PERCENT

# .env → COMMISSION_RATE_PERCENT (örn: 5 → %5, 0 → %0 komisyonsuz)
COMISION_RATE = COMMISSION_RATE_PERCENT


def calculate_comision(gross_amount: float) -> dict:
    """
    Brüt tutardan komisyon ve net tutarı hesaplar.

    Args:
        gross_amount: Gelen brüt USD tutarı

    Returns:
        dict: {
            "gross": brüt tutar,
            "comision": kesilen komisyon,
            "net": müşteriye geçecek net tutar,
            "rate": uygulanan oran (%)
        }

    Örnek:
        >>> calculate_comision(1000.0)
        {"gross": 1000.0, "comision": 50.0, "net": 950.0, "rate": 5}
    """
    comision = round(gross_amount * COMISION_RATE / 100, 2)
    net_amount = round(gross_amount - comision, 2)

    return {
        "gross": gross_amount,
        "comision": comision,
        "net": net_amount,
        "rate": COMISION_RATE
    }
