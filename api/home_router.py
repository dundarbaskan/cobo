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

@router.get("/frontend/test_appzone.html", response_class=HTMLResponse)
async def test_appzone():
    """AppZone test sayfası"""
    with open("frontend/test_appzone.html", "r", encoding="utf-8") as f:
        return f.read()

@router.get("/frontend/index.html", response_class=HTMLResponse)
async def index_html():
    """Index.html direkt erişim"""
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return f.read()
