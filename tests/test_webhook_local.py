# -*- coding: utf-8 -*-
"""
COBO Webhook Lokal Test Script'i
=================================
Gerçek Cobo payload'larını kullanarak webhook pipeline'ını test eder.
Sunucuya HTTP isteği atar — sunucunun çalışır durumda olması gerekir.

Kullanım:
    python tests/test_webhook_local.py                     # Tüm payload'ları test et
    python tests/test_webhook_local.py tron_usdt           # Sadece TRON USDT
    python tests/test_webhook_local.py eth                 # Sadece ETH
    python tests/test_webhook_local.py trx                 # Sadece TRX

NOT: Her test çalıştırıldığında transaction_id otomatik olarak değiştirilir,
     böylece lock mekanizmasına takılmaz (tekrar tekrar test edilebilir).
"""

import json
import uuid
import sys
import os
import time
import requests
import traceback

# ─── Ayarlar ───────────────────────────────────────────────
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
WEBHOOK_ENDPOINT = f"{BASE_URL}/cobo/callback"

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# Test edilecek payload dosyaları
PAYLOADS = {
    "tron_usdt": {
        "file": "payload_tron_usdt_1.json",
        "label": "TRON USDT (5.970,04 USDT)",
        "expected_coin": "TRON_USDT",
        "expected_amount": "5970.04",
    },
    "eth": {
        "file": "payload_eth_1.json",
        "label": "ETH (1,59 ETH)",
        "expected_coin": "ETH",
        "expected_amount": "1.59638487",
    },
    "trx": {
        "file": "payload_trx_1.json",
        "label": "TRX (10.630,11 TRX)",
        "expected_coin": "TRON",
        "expected_amount": "10630.1118",
    },
}


def mask_sensitive(value: str, visible_chars: int = 6) -> str:
    """Hassas bilgileri maskeler: TXJ1EP...C18y"""
    if not value or len(value) <= visible_chars * 2:
        return value
    return f"{value[:visible_chars]}...{value[-4:]}"


def load_payload(filename: str) -> dict:
    """JSON payload'ını dosyadan yükler."""
    filepath = os.path.join(ASSETS_DIR, filename)
    if not os.path.exists(filepath):
        print(f"  ❌ Payload dosyası bulunamadı: {filepath}")
        sys.exit(1)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def prepare_payload(payload: dict) -> dict:
    """
    Payload'ı test için hazırlar:
    - Yeni benzersiz transaction_id üretir (lock'a takılmamak için)
    - Cobo webhook formatına sarar (event wrapper)
    """
    # Her testte unique ID
    original_tx_id = payload.get("transaction_id", "N/A")
    new_tx_id = f"TEST-{uuid.uuid4()}"
    payload["transaction_id"] = new_tx_id

    # Cobo webhook wrapper formatı
    wrapped = {
        "event_id": new_tx_id,
        "type": "wallets.transaction.updated",
        "data": {
            "transaction": payload
        }
    }

    return wrapped, original_tx_id, new_tx_id


def send_webhook(payload: dict, label: str) -> bool:
    """Webhook'a POST isteği gönderir ve sonucu loglar."""
    print(f"\n  📤 POST {WEBHOOK_ENDPOINT}")
    print(f"  ⏳ İstek gönderiliyor...")

    start = time.time()
    try:
        resp = requests.post(
            WEBHOOK_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        elapsed = time.time() - start

        print(f"  📥 Yanıt: {resp.status_code} ({elapsed:.2f}s)")
        print(f"  📄 Body: {resp.text[:200]}")

        if resp.status_code == 200:
            print(f"  ✅ Webhook başarıyla kabul edildi!")
            return True
        else:
            print(f"  ❌ Webhook reddedildi! Status: {resp.status_code}")
            return False

    except requests.ConnectionError:
        print(f"  ❌ BAĞLANTI HATASI: Sunucu çalışmıyor olabilir ({BASE_URL})")
        return False
    except requests.Timeout:
        print(f"  ❌ TIMEOUT: Sunucu {15}s içinde yanıt vermedi")
        return False
    except Exception as e:
        print(f"  ❌ BEKLENMEDİK HATA: {e}")
        return False


def run_test(key: str, info: dict):
    """Tek bir payload testi çalıştırır."""
    print(f"\n{'='*60}")
    print(f"  🧪 TEST: {info['label']}")
    print(f"{'='*60}")

    # 1. Payload yükle
    raw_payload = load_payload(info["file"])
    print(f"  📂 Dosya        : {info['file']}")

    # 2. Veriyi analiz et (loglama)
    tx_id_original = raw_payload.get("transaction_id", "N/A")
    token_id = raw_payload.get("token_id", "N/A")
    asset_id = raw_payload.get("asset_id", "N/A")
    chain_id = raw_payload.get("chain_id", "N/A")
    status = raw_payload.get("status", "N/A")
    amount = raw_payload.get("destination", {}).get("amount", "N/A")
    address = raw_payload.get("destination", {}).get("address", "N/A")

    print(f"  🆔 Orijinal TxID: {mask_sensitive(tx_id_original, 8)}")
    print(f"  💎 Token ID     : {token_id}")
    print(f"  🏷️  Asset ID     : {asset_id}")
    print(f"  🌐 Chain        : {chain_id}")
    print(f"  💰 Miktar       : {amount}")
    print(f"  📍 Adres        : {mask_sensitive(address)}")
    print(f"  📊 Durum        : {status}")

    # 3. Payload'ı test formatına hazırla
    wrapped, orig_id, new_id = prepare_payload(raw_payload)
    print(f"\n  🔄 Test TxID    : {mask_sensitive(new_id, 10)}")
    print(f"  📦 Wrapper      : wallets.transaction.updated")

    # 4. Kontroller
    print(f"\n  ── Ön Kontroller ──")
    print(f"  ✓ Token '{token_id}' -> Beklenen: '{info['expected_coin']}'", end="")
    print(f" {'✅' if info['expected_coin'] in token_id else '⚠️ UYUMSUZ'}")
    print(f"  ✓ Miktar '{amount}' -> Beklenen: '{info['expected_amount']}'", end="")
    print(f" {'✅' if amount == info['expected_amount'] else '⚠️ UYUMSUZ'}")

    # 5. Webhook'a gönder
    print(f"\n  ── Webhook Gönderimi ──")
    success = send_webhook(wrapped, info["label"])

    if success:
        print(f"\n  💡 Şimdi sunucu loglarını kontrol et:")
        print(f"     1. Filtrelerden geçti mi?")
        print(f"     2. Kur çevirisi yapıldı mı? (converter.py)")
        print(f"     3. MongoDB'ye yazıldı mı? (try_lock)")
        print(f"     4. Telegram mesajı gitti mi?")
        print(f"     5. MT5'e bakiye eklendi mi?")

    return success


def main():
    print("\n" + "═"*60)
    print("  🚀 COBO WEBHOOK LOKAL TEST SİSTEMİ")
    print("  📡 Hedef: " + WEBHOOK_ENDPOINT)
    print("═"*60)

    # Hangi testleri çalıştıracağız?
    if len(sys.argv) > 1:
        selected = sys.argv[1].lower()
        if selected not in PAYLOADS:
            print(f"\n  ❌ Bilinmeyen test: '{selected}'")
            print(f"  📋 Mevcut testler: {', '.join(PAYLOADS.keys())}")
            sys.exit(1)
        tests = {selected: PAYLOADS[selected]}
    else:
        tests = PAYLOADS

    # Testleri çalıştır
    results = {}
    for key, info in tests.items():
        results[key] = run_test(key, info)
        if len(tests) > 1:
            print(f"\n  ⏳ Sonraki test için 2 saniye bekleniyor...")
            time.sleep(2)

    # Sonuç özeti
    print(f"\n\n{'═'*60}")
    print(f"  📊 TEST SONUÇLARI")
    print(f"{'═'*60}")
    for key, success in results.items():
        status = "✅ BAŞARILI" if success else "❌ BAŞARISIZ"
        print(f"  {status} — {PAYLOADS[key]['label']}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\n  Toplam: {total} | Geçen: {passed} | Kalan: {total - passed}")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\n\n❗ KRİTİK BİR HATA OLUŞTU:")
        traceback.print_exc()
    
    print("\n[Çıkmak için ENTER tuşuna basın]")
    input()
