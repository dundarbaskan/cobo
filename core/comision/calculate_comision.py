"""
Komisyon Hesaplama Modülü
=========================
Kripto yatırım işlemlerinde uygulanacak komisyon tutarını hesaplar.

V2.0 - Komisyon Use Case. Oran statik %5, dışarıdan parametre alınmaz.
"""

# V2.0 - Statik komisyon oranı. .env veya dışarıdan alınmaz, buradan yönetilir.
COMISION_RATE = 5  # Yüzde olarak: %5


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
