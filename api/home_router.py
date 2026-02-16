"""
Ana Sayfa Router'ı
==================
Kullanıcıya yatırım arayüzünü (index.html) sunar.

İlgili HTML: frontend/index.html
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def home():
    """Ana sayfa - Kullanıcı paneli"""
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return f.read()
