"""
QR Kod Üretim Servisi
=====================
Cüzdan adresleri ve herhangi bir veri için PNG formatında QR kod üretir.

Çıktı: Base64 encoded PNG string (HTML <img> tag'inde kullanılabilir)
"""

import qrcode
import io
import base64

def generate_qr_base64(data: str) -> str:
    """
    Verilen string'den QR kod üretir ve base64 string döndürür.

    Args:
        data: QR koda dönüştürülecek veri (cüzdan adresi, URL vb.)

    Returns:
        Base64 encoded PNG image string
    """
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()
