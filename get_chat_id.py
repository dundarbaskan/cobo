"""
Telegram Chat ID Bulma Aracı
Botunuzu gruba ekleyin ve bu scripti çalıştırın
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_chat_id():
    """Telegram bot'a gelen son mesajları göster"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN bulunamadı!")
        return
    
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    
    print("🔍 Telegram bot güncellemeleri alınıyor...\n")
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if not data.get("ok"):
            print(f"❌ API Hatası: {data}")
            return
        
        updates = data.get("result", [])
        
        if not updates:
            print("⚠️ Henüz mesaj yok!")
            print("\n📝 Yapmanız gerekenler:")
            print("1. Botunuzu yeni gruba ekleyin")
            print("2. Grupta herhangi bir mesaj yazın (örn: /start)")
            print("3. Bu scripti tekrar çalıştırın")
            return
        
        print(f"✅ {len(updates)} güncelleme bulundu!\n")
        print("="*60)
        
        seen_chats = {}
        
        for update in updates:
            # Mesaj varsa
            if "message" in update:
                msg = update["message"]
                chat = msg.get("chat", {})
                chat_id = chat.get("id")
                chat_type = chat.get("type")
                chat_title = chat.get("title", "Özel Mesaj")
                
                if chat_id and chat_id not in seen_chats:
                    seen_chats[chat_id] = {
                        "title": chat_title,
                        "type": chat_type,
                        "username": chat.get("username", "N/A")
                    }
            
            # Callback query varsa
            elif "callback_query" in update:
                msg = update["callback_query"]["message"]
                chat = msg.get("chat", {})
                chat_id = chat.get("id")
                
                if chat_id and chat_id not in seen_chats:
                    seen_chats[chat_id] = {
                        "title": chat.get("title", "Özel Mesaj"),
                        "type": chat.get("type"),
                        "username": chat.get("username", "N/A")
                    }
        
        # Sonuçları göster
        for chat_id, info in seen_chats.items():
            print(f"\n📱 Chat Bilgileri:")
            print(f"   🆔 Chat ID: {chat_id}")
            print(f"   📛 İsim: {info['title']}")
            print(f"   🏷️ Tip: {info['type']}")
            if info['username'] != "N/A":
                print(f"   👤 Username: @{info['username']}")
            print("-"*60)
        
        print("\n💡 Kullanım:")
        print("   .env dosyasına ekleyin:")
        print(f"   TELEGRAM_CHAT_ID={list(seen_chats.keys())[0]}")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    print("="*60)
    print("🤖 TELEGRAM CHAT ID BULMA ARACI")
    print("="*60)
    get_chat_id()
    print("\n" + "="*60)
