"""
maintenance_server.py — Bakım Modu Sunucusu

Kullanım:
    python maintenance_server.py [--time HH:MM] [--day SAYI]

    --time HH:MM   : Açılış saati (Türkiye saati), örn. --time 17:00
    --day  SAYI    : Kaç gün sonra açılacağı, örn. --day 1
                     (her ikisi verilirse: SAYI gün sonra HH:MM'de)

PM2 ile:
    pm2 start ecosystem.config.js --only COBO-MAINTENANCE
    (veya doğrudan: pm2 start maintenance_server.py --interpreter python -- --time 17:00 --day 1)

Özellikler:
    - Tüm HTTP isteklerine 503 döner, sadece /static/* ve favicon geçer.
    - Geri sayım hedefi her ziyaretçiye aynı UTC milisaniyesi ile iletilir.
    - Backend hiç başlamaz; veritabanı, API, bot çalışmaz.
"""

import argparse
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# ─── Komut Satırı Argümanları ──────────────────────────────────────────────────
argument_parser = argparse.ArgumentParser(
    description="Cep Portföy — Bakım Modu Sunucusu"
)
argument_parser.add_argument(
    "--time",
    dest="opening_time",
    default="00:00",
    metavar="HH:MM",
    help="Tahmini açılış saati (Türkiye saati, 24 saat formatı). Örnek: --time 17:00",
)
argument_parser.add_argument(
    "--day",
    dest="days_from_now",
    type=float,
    default=0,
    metavar="SAYI",
    help="Kaç gün sonra açılacağı. Örnek: --day 1 (yarın)",
)
argument_parser.add_argument(
    "--port",
    dest="server_port",
    type=int,
    default=int(os.environ.get("PORT", 8000)),
    metavar="PORT",
    help="Dinlenecek port numarası (varsayılan: PORT env veya 8000)",
)

parsed_args, _unknown_args = argument_parser.parse_known_args()

# ─── Hedef Zamanı Hesapla ─────────────────────────────────────────────────────
TURKEY_UTC_OFFSET = timezone(timedelta(hours=3))  # Europe/Istanbul (UTC+3)

def calculate_maintenance_end_utc(opening_time_str: str, days_from_now: float) -> datetime:
    """
    Türkiye saatine göre hedef açılış zamanını UTC olarak hesaplar.
    """
    now_turkey = datetime.now(TURKEY_UTC_OFFSET)

    try:
        opening_hour, opening_minute = map(int, opening_time_str.split(":"))
    except ValueError:
        print(f"[HATA] Geçersiz saat formatı: '{opening_time_str}'. HH:MM formatını kullanın.")
        sys.exit(1)

    # Kaç tam gün ekleneceğini hesapla
    full_days = math.floor(days_from_now)
    extra_hours = (days_from_now - full_days) * 24

    # Hedef tarihi oluştur
    target_date = now_turkey.date() + timedelta(days=full_days)
    target_datetime_turkey = datetime(
        year=target_date.year,
        month=target_date.month,
        day=target_date.day,
        hour=opening_hour,
        minute=opening_minute,
        second=0,
        microsecond=0,
        tzinfo=TURKEY_UTC_OFFSET,
    ) + timedelta(hours=extra_hours)

    return target_datetime_turkey.astimezone(timezone.utc)


MAINTENANCE_END_UTC = calculate_maintenance_end_utc(
    opening_time_str=parsed_args.opening_time,
    days_from_now=parsed_args.days_from_now,
)
MAINTENANCE_END_MS = int(MAINTENANCE_END_UTC.timestamp() * 1000)

# ─── HTML Şablonu ─────────────────────────────────────────────────────────────
FRONTEND_DIRECTORY = Path(__file__).parent / "frontend"
MAINTENANCE_TEMPLATE_PATH = FRONTEND_DIRECTORY / "maintenance.html"

def load_maintenance_html() -> bytes:
    """
    maintenance.html şablonunu okur ve __MAINTENANCE_END_MS__
    yer tutucusunu gerçek UTC milisaniyesiyle değiştirerek döner.
    """
    if not MAINTENANCE_TEMPLATE_PATH.exists():
        fallback_html = f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="UTF-8"><title>Bakımda</title></head>
<body style="background:#050c1a;color:#d4af37;font-family:sans-serif;text-align:center;padding:4rem;">
<h1>Sistem Bakımda</h1>
<p>Kısa süre içinde geri döneceğiz.</p>
</body></html>"""
        return fallback_html.encode("utf-8")

    with open(MAINTENANCE_TEMPLATE_PATH, "r", encoding="utf-8") as template_file:
        raw_html = template_file.read()

    # Sunucu tarafından enjeksiyon — herkes aynı zamayı görür
    rendered_html = raw_html.replace("__MAINTENANCE_END_MS__", str(MAINTENANCE_END_MS))
    return rendered_html.encode("utf-8")


MAINTENANCE_HTML_BYTES = load_maintenance_html()

# ─── Static Dosya Yardımcıları ────────────────────────────────────────────────
STATIC_DIRECTORY = Path(__file__).parent / "static"

MIME_TYPE_MAP = {
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif":  "image/gif",
    ".svg":  "image/svg+xml",
    ".ico":  "image/x-icon",
    ".webp": "image/webp",
    ".css":  "text/css; charset=utf-8",
    ".js":   "application/javascript; charset=utf-8",
    ".woff2": "font/woff2",
    ".woff":  "font/woff",
    ".ttf":   "font/ttf",
}


def get_mime_type(file_path: Path) -> str:
    return MIME_TYPE_MAP.get(file_path.suffix.lower(), "application/octet-stream")


# ─── HTTP İstek Yöneticisi ────────────────────────────────────────────────────
class MaintenanceRequestHandler(BaseHTTPRequestHandler):
    """
    Tüm HTTP GET isteklerini yönetir:
    - /static/* → static klasöründen dosya serve eder (favicon, logolar vs.)
    - Her şey   → 503 + bakım sayfası döner
    """

    def log_message(self, format_str, *args):
        """Erişim loglarını stderr'e yaz."""
        print(f"[{self.address_string()}] {format_str % args}", file=sys.stderr)

    def do_GET(self):  # noqa: N802 (HTTP method naming convention)
        request_path = self.path.split("?")[0]  # Query string'i at

        # Statik dosyalara izin ver (favicon, logolar, CSS, JS vb.)
        if request_path.startswith("/static/"):
            self._serve_static_file(request_path)
            return

        # Diğer tüm isteklere bakım sayfası döndür
        self._serve_maintenance_page()

    def do_POST(self):  # noqa: N802
        self._serve_maintenance_page()

    def do_PUT(self):  # noqa: N802
        self._serve_maintenance_page()

    def do_DELETE(self):  # noqa: N802
        self._serve_maintenance_page()

    def do_OPTIONS(self):  # noqa: N802
        self._serve_maintenance_page()

    def _serve_maintenance_page(self):
        self.send_response(503)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(MAINTENANCE_HTML_BYTES)))
        self.send_header("Retry-After", "3600")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(MAINTENANCE_HTML_BYTES)

    def _serve_static_file(self, request_path: str):
        # /static/ prefix'ini kaldır ve gerçek dosya yolunu bul
        relative_path = request_path[len("/static/"):]
        file_path = STATIC_DIRECTORY / relative_path

        # Dizin geçişlerine karşı güvenlik kontrolü
        try:
            file_path.resolve().relative_to(STATIC_DIRECTORY.resolve())
        except ValueError:
            self._send_not_found()
            return

        if not file_path.is_file():
            self._send_not_found()
            return

        file_content = file_path.read_bytes()
        mime_type = get_mime_type(file_path)

        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(file_content)))
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(file_content)

    def _send_not_found(self):
        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Not Found")


# ─── Giriş Noktası ───────────────────────────────────────────────────────────
def main():
    target_turkey_time = MAINTENANCE_END_UTC.astimezone(TURKEY_UTC_OFFSET)
    formatted_target = target_turkey_time.strftime("%d %B %Y %H:%M")

    print("=" * 60)
    print("  CEP PORTFÖY — BAKIM MODU AKTİF")
    print("=" * 60)
    print(f"  Port           : {parsed_args.server_port}")
    print(f"  Hedef Açılış   : {formatted_target} (Türkiye Saati)")
    print(f"  UTC Timestamp  : {MAINTENANCE_END_MS} ms")
    print(f"  Kalan Süre     : hesaplanıyor...")
    remaining_seconds = max(0, int((MAINTENANCE_END_UTC - datetime.now(timezone.utc)).total_seconds()))
    remaining_hours   = remaining_seconds // 3600
    remaining_minutes = (remaining_seconds % 3600) // 60
    remaining_secs    = remaining_seconds % 60
    print(f"  Kalan Süre     : {remaining_hours:02d}:{remaining_minutes:02d}:{remaining_secs:02d}")
    print("=" * 60)
    print("  Backend çalışmıyor. Sadece bakım ekranı serve ediliyor.")
    print("=" * 60)

    server = HTTPServer(("0.0.0.0", parsed_args.server_port), MaintenanceRequestHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[BİLGİ] Bakım sunucusu durduruldu.")
        server.shutdown()


if __name__ == "__main__":
    main()
