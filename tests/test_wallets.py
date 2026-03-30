"""
Cüzdan Adresi Doğrulama Testleri
==================================
.env içerisindeki kasa adreslerinin doğruluğunu teyit eder.

V2.0 - Adım 4: .env cüzdan adreslerini beklenen değerlerle karşılaştırır.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env dosyasını yükle
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)



def test_wallet_addresses():
    """
    Kullanıcıdan alınan beklenen cüzdan adreslerini,
    .env dosyasındaki değerlerle karşılaştırır.
    """
    print("=" * 50)
    print("🔍 Cüzdan Adresi Doğrulama Testi")
    print("=" * 50)

    # V2.0 - Kullanıcıdan beklenen adresleri dinamik olarak alır
    expected_wallets = {
        "MAIN_WALLET": input("Lütfen MAIN_WALLET (Ana Kasa) beklenen değerini girin: ").strip(),
        "ETH_CONVERTER_WALLET": input("Lütfen ETH_CONVERTER_WALLET beklenen değerini girin: ").strip(),
        "BTC_CONVERTER_WALLET": input("Lütfen BTC_CONVERTER_WALLET beklenen değerini girin: ").strip(),
        "TRX_CONVERTER_WALLET": input("Lütfen TRX_CONVERTER_WALLET beklenen değerini girin: ").strip(),
    }

    all_passed = True

    print("\nSonuçlar:")
    print("-" * 50)
    for env_key, expected_value in expected_wallets.items():
        actual_value = os.getenv(env_key, "").strip()

        if actual_value == expected_value:
            print(f"✅ Test Başarılı  | {env_key}")
        else:
            print(f"❌ Test Hatalı    | {env_key}")
            print(f"   Beklenen : {expected_value}")
            print(f"   Gerçek   : {actual_value if actual_value else '(boş veya tanımsız)'}")
            all_passed = False


    print("=" * 50)
    if all_passed:
        print("🎉 Tüm testler başarılı!")
    else:
        print("⚠️  Bazı testler başarısız. .env dosyasını kontrol edin.")
    print("=" * 50)

    return all_passed


if __name__ == "__main__":
    test_wallet_addresses()
