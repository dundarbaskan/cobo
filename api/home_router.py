"""
Ana Sayfa Router'ı
==================
Kullanıcıya yatırım arayüzünü (index.html) sunar.

İlgili HTML: frontend/index.html
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import time

from config.settings import MAINTENANCE_ACTIVE, ADMIN_IP, MAINTENANCE_MINUTES

router = APIRouter()

# Server'ın başladığı anı kaydet (Milisaniye cinsinden bitiş zamanını hesapla)
SERVER_START_TIME = time.time()
MAINTENANCE_END_TIME_MS = int((SERVER_START_TIME + (MAINTENANCE_MINUTES * 60)) * 1000)

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Ana sayfa - Kullanıcı paneli veya Bakım Ekranı"""
    
    # Kullanıcının IP adresini al (Proxy arkasında olabilir diye x-forwarded-for'a da bakılır)
    client_ip = request.client.host
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    # Maintenance kontrolü (Eğer aktifse ve IP beyaz listede değilse bakım sayfasını göster)
    if MAINTENANCE_ACTIVE and client_ip != ADMIN_IP:
        with open("frontend/maintenance.html", "r", encoding="utf-8") as f:
            html = f.read()
            # Sunucunun hedef süresini HTML içine enjekte et
            html = html.replace("__MAINTENANCE_END_TIME__", str(MAINTENANCE_END_TIME_MS))
            return html

    # Maintenance aktif değilse veya IP admin ise normal index'i göster
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
