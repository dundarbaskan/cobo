"""
Sistem Bakım Endpoint'leri
==========================
- fix-db: Veritabanı index onarımı ve duplicate kontrol

DİKKAT: Bu endpoint production'da sadece yetkili kişiler tarafından kullanılmalıdır.
"""

from fastapi import APIRouter
from servisler.db_service import ensure_transaction_index

router = APIRouter(prefix="/api/system", tags=["System"])


@router.get("/fix-db")
async def manual_fix_db():
    """
    MANUEL BAKIM BUTONU:
    Eğer sistemde çift kayıt varsa veya index bozulduysa bu endpoint'i kullan.
    Otomatik olarak temizlik yapar ve korumayı açar.
    """
    try:
        await ensure_transaction_index()
        return {
            "status": "success",
            "message": "✅ Veritabanı temizlendi ve Unique Index oluşturuldu!"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Hata: {str(e)}"
        }
