"""
Cobo Wallet Manuel Yönetim Aracı
Bu script ile Cobo wallet'ınızı manuel olarak yönetebilirsiniz.
"""
import os
import sys
from dotenv import load_dotenv
from servisler.sweep_service import CoboSweepService

load_dotenv()

def print_menu():
    print("\n" + "="*50)
    print("🏦 COBO WALLET YÖNETİM PANELİ")
    print("="*50)
    print("1. 📊 Wallet Bilgilerini Görüntüle")
    print("2. 📝 Son İşlemleri Listele")
    print("3. 📍 Adresleri Listele")
    print("4. 💰 Bakiye Kontrolü")
    print("5. 🔄 Wallet Durumunu Telegram'a Gönder")
    print("0. ❌ Çıkış")
    print("="*50)

def view_wallet_info(service, wallet_id):
    """Wallet bilgilerini göster"""
    print("\n🔍 Wallet bilgileri alınıyor...")
    result = service.get_wallet_info(wallet_id)
    
    if result.get("success"):
        data = result["data"]
        print("\n✅ Wallet Bilgileri:")
        print(f"  📛 İsim: {data.get('name', 'N/A')}")
        print(f"  🆔 ID: {data.get('wallet_id', 'N/A')}")
        print(f"  🏷️ Tip: {data.get('wallet_type', 'N/A')}")
        print(f"  🌐 Org ID: {data.get('org_id', 'N/A')}")
    else:
        print(f"\n❌ Hata: {result.get('error')}")

def list_transactions(service, wallet_id):
    """Son işlemleri listele"""
    print("\n🔍 Son işlemler alınıyor...")
    result = service.list_transactions(wallet_id, limit=10)
    
    if result.get("success"):
        data = result["data"]
        tx_list = data.get("data", [])
        
        if tx_list:
            print(f"\n✅ Son {len(tx_list)} İşlem:")
            for i, tx in enumerate(tx_list, 1):
                tx_id = tx.get("transaction_id", "N/A")
                tx_type = tx.get("type", "N/A")
                amount = tx.get("amount", "0")
                token = tx.get("token_id", "")
                status = tx.get("status", "N/A")
                created = tx.get("created_timestamp", "N/A")
                
                print(f"\n  {i}. 📝 İşlem ID: {tx_id[:16]}...")
                print(f"     🔹 Tip: {tx_type}")
                print(f"     💵 Tutar: {amount} {token}")
                print(f"     📊 Durum: {status}")
                print(f"     📅 Tarih: {created}")
        else:
            print("\n📝 Henüz işlem yok.")
    else:
        print(f"\n❌ Hata: {result.get('error')}")

def list_addresses(service, wallet_id):
    """Adresleri listele"""
    print("\n🔍 Adresler alınıyor...")
    result = service.list_addresses(wallet_id, "TRON", limit=20)
    
    if result.get("success"):
        data = result["data"]
        addr_list = data.get("data", [])
        
        if addr_list:
            print(f"\n✅ Toplam {len(addr_list)} Adres:")
            for i, addr in enumerate(addr_list, 1):
                address = addr.get("address", "N/A")
                chain = addr.get("chain_id", "N/A")
                encoding = addr.get("encoding", "N/A")
                
                print(f"\n  {i}. 📍 {address}")
                print(f"     🌐 Chain: {chain}")
                print(f"     🔤 Encoding: {encoding}")
        else:
            print("\n📍 Henüz adres yok.")
    else:
        print(f"\n❌ Hata: {result.get('error')}")

def check_balances(service, wallet_id):
    """Bakiye kontrolü"""
    print("\n🔍 Bakiyeler kontrol ediliyor...")
    result = service.check_balances(wallet_id)
    
    print(f"\n✅ Bakiye Raporu:")
    print(f"  🆔 Wallet ID: {result['wallet_id']}")
    print(f"  📍 Adres Sayısı: {result['address_count']}")
    
    if result['wallet_info'].get('success'):
        w_data = result['wallet_info']['data']
        print(f"  📛 Wallet: {w_data.get('name', 'N/A')}")

def send_to_telegram(service, wallet_id):
    """Wallet durumunu Telegram'a gönder"""
    import requests
    
    print("\n🔍 Telegram'a gönderiliyor...")
    try:
        response = requests.post(
            "http://localhost:8000/api/telegram_command",
            data={"command": "/sweep"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print("\n✅ Wallet bilgileri Telegram'a gönderildi!")
            else:
                print(f"\n❌ Hata: {result.get('message')}")
        else:
            print(f"\n❌ API Hatası: {response.status_code}")
    except Exception as e:
        print(f"\n❌ Bağlantı Hatası: {e}")

def main():
    """Ana program"""
    wallet_id = os.getenv("COBO_WALLET_ID")
    
    if not wallet_id:
        print("❌ COBO_WALLET_ID .env dosyasında tanımlı değil!")
        sys.exit(1)
    
    service = CoboSweepService()
    
    while True:
        print_menu()
        choice = input("\n👉 Seçiminiz (0-5): ").strip()
        
        if choice == "1":
            view_wallet_info(service, wallet_id)
        elif choice == "2":
            list_transactions(service, wallet_id)
        elif choice == "3":
            list_addresses(service, wallet_id)
        elif choice == "4":
            check_balances(service, wallet_id)
        elif choice == "5":
            send_to_telegram(service, wallet_id)
        elif choice == "0":
            print("\n👋 Çıkış yapılıyor...")
            break
        else:
            print("\n❌ Geçersiz seçim! Lütfen 0-5 arası bir sayı girin.")
        
        input("\n⏸️  Devam etmek için Enter'a basın...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Program sonlandırıldı.")
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()
