import os
import json
import asyncio
import qrcode
import io
import base64
import logging
import datetime
from fastapi import FastAPI, Request, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import uvicorn
import requests
import cobo_waas2
from cobo_waas2 import ApiClient, Configuration, CreateAddressRequest
from servisler.db_service import (
    get_lead_by_tp, save_wallet_to_lead, get_lead_by_address, 
    increment_deposit_count, get_existing_wallet, 
    try_lock_transaction, ensure_transaction_index, update_financial_stats,
    get_all_our_addresses
)
from servisler.mt5service import MT5UserManager
from servisler.sweep_service import CoboSweepService
from core.currency.converter.converter import coin_parser

from pathlib import Path

# .env dosyasını tam yol ile yükle (PM2 uyumluluğu için)
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Startup Event: Veritabanı ve Index Kontrolleri
@app.on_event("startup")
async def startup_event():
    """
    Uygulama başlarken çalışır.
    1. Veritabanı bağlantılarını kontrol eder.
    2. Race Condition için 'transactions' tablosunda UNIQUE INDEX oluşturur.
    3. Varsa duplicate (çift) kayıtları temizler.
    """
    logger.info("🚀 Uygulama başlatılıyor...")
    
    try:
        # DB Servisinden index fonksiyonunu çağır
        await ensure_transaction_index()
        logger.info("✅ 1. Adım: Unique Index Güvenceye Alındı (Çift İşlem Koruması Aktif)")
    except Exception as e:
        logger.error(f"❌ Index oluşturulurken hata: {e}")

    logger.info("✅ Sistem Tamamen Hazır!")

# MT5 Configuration
MT5_SERVER = os.getenv("MT5_SERVER")
MT5_LOGIN = int(os.getenv("MT5_LOGIN", 10000))
MT5_PASSWORD = os.getenv("MT5_PASSWORD")

mt5_manager = MT5UserManager(MT5_SERVER, MT5_LOGIN, MT5_PASSWORD)

# Logos and Static Files
if not os.path.exists("logolar"):
    os.makedirs("logolar")
app.mount("/logolar", StaticFiles(directory="logolar"), name="logolar")

def generate_qr_base64(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def send_telegram_msg(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    import html
    # Mesajı HTML formatına uygun hale getir (basit kaçış)
    # message = html.escape(message) # Bunu yaparsak <b> vb. bozulur. 
    # Sadece verileri kaçırmak lazım ama şimdilik parse_mode'u HTML yapıp mesajı ona göre düzenleyelim.
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, json=payload)
        if not resp.ok:
            logger.error(f"❌ Telegram Hatası: {resp.text}")
    except Exception as e:
        logger.error(f"❌ Telegram İstek Hatası: {e}")

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()



@app.post("/api/verify_tp")
async def verify_tp(tp_number: str = Form(...)):
    lead = await get_lead_by_tp(tp_number)
    if not lead:
        return JSONResponse(status_code=404, content={"status": "error", "message": "TP Number bulunamadı!"})
    
    # MongoDB'den mevcut verileri al
    mt5_data = {
        "balance": lead.get("balance", 0),
        "equity": lead.get("equity", 0),
        "credit": lead.get("credit", 0),
        "name": lead.get("name", "Değerli Yatırımcı")
    }

    return {
        "status": "success", 
        "name": mt5_data.get("name"), 
        "email": lead.get("email"),
        "mt5": mt5_data,
        "last_sync": lead.get("last_sync")
    }

@app.post("/api/create_wallet")
async def create_wallet(tp_number: str = Form(...), chain_id: str = Form(...), asset_name: str = Form(...)):
    lead = await get_lead_by_tp(tp_number)
    if not lead:
        raise HTTPException(status_code=404, detail="Geçersiz TP Number")

    # Chain ID'yi normalize et
    final_chain_id = "TRON" if chain_id == "USDT" else chain_id
    
    # Önce mevcut cüzdanı kontrol et (normalize edilmiş chain_id ile)
    existing_wallet = await get_existing_wallet(tp_number, asset_name, final_chain_id)
    if existing_wallet:
        # Mevcut cüzdanı döndür
        return {
            "address": existing_wallet.get("address"),
            "qr_code": generate_qr_base64(existing_wallet.get("address")),
            "existing": True
        }

    try:
        import certifi  # SSL Sertifikası için gerekli
        
        configuration = Configuration(
            api_private_key=os.getenv("COBO_API_SECRET"),
            host="https://api.cobo.com/v2"
        )
        
        # Windows SSL Hatası Çözümü:
        configuration.ssl_ca_cert = certifi.where()
        configuration.verify_ssl = True
        
        with ApiClient(configuration) as api_client:
            # Set API Key header
            api_client.set_default_header("Biz-Api-Key", os.getenv("COBO_API_KEY"))
            
            api_instance = cobo_waas2.WalletsApi(api_client)
            master_wallet_id = os.getenv("COBO_WALLET_ID")
            
            req = CreateAddressRequest(chain_id=final_chain_id, count=1)
            api_resp = api_instance.create_address(wallet_id=master_wallet_id, create_address_request=req)
            
            new_address = api_resp[0].address
            qr_base64 = generate_qr_base64(new_address)
            
            wallet_data = {
                "address": new_address,
                "chain_id": final_chain_id,
                "asset": asset_name,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            await save_wallet_to_lead(tp_number, wallet_data)
            return {"address": new_address, "qr_code": qr_base64}
            
    except Exception as e:
        logger.error(f"❌ Cüzdan Oluşturma Hatası (TP: {tp_number}): {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(status_code=400, content={"error": str(e)})

async def process_cobo_notification(data: dict):
    """
    Cobo webhook bildirimlerini arka planda işleyen asenkron fonksiyon
    """
    try:
        logger.info(f"🔄 Arka plan işlemi başlatıldı: {data.get('event_id', 'unknown')}")
        
        # Cobo uses 'type' not 'event_type'
        event_type = data.get("type") or data.get("event_type")
        
        # Wallet creation notification
        if event_type == "wallets.addresses.created":
            addresses = data.get("data", {}).get("addresses", [])
            for addr_data in addresses:
                address = addr_data.get("address")
                chain = addr_data.get("chain_id")
                
                # Bu adresi hangi kullanıcı için oluşturduk?
                lead = await get_lead_by_address(address)
                if lead:
                    tp = lead.get("tp_number")
                    name = lead.get("name", "Bilinmeyen")
                    
                    # Asset bilgisini cüzdan listesinden bul
                    asset = "USDT" # Varsayılan
                    for w in lead.get("wallets", []):
                        if w.get("address") == address:
                            asset = w.get("asset", "USDT")
                            break
                    
                    # Ağ ismini güzelleştir (Opsiyonel)
                    display_chain = chain
                    if chain == "MATIC": display_chain = "Polygon (MATIC)"
                    elif chain == "TRON": display_chain = "TRON (TRC20)"
                    elif chain == "ETH": display_chain = "Ethereum (ERC20)"
                    
                    msg = (
                        f"🆕 <b>CÜZDAN OLUŞTURULDU</b>\n\n"
                        f"👤 <b>Müşter:</b> {name}\n"
                        f"🔑 <b>TP:</b> <code>{tp}</code>\n"
                        f"💵 <b>Varlık:</b> {asset}\n"
                        f"🌐 <b>Ağ:</b> {display_chain}\n"
                        f"📍 <b>Adres:</b> <code>{address}</code>"
                    )
                    send_telegram_msg(msg)
                    logger.info(f"✅ Cüzdan bildirimi: {name} (TP: {tp}) - {asset} {chain}")
        
        # Transaction events
        elif event_type in ["TRANSACTION", "transaction.created", "transaction.deposit", "transaction.success", "wallets.transaction.created", "wallets.transaction.updated", "wallets.transaction.succeeded", "wallets.transactions.created", "wallets.transactions.updated"]:
            tx = data.get("data", {})
            if "transaction" in tx:
                tx = tx["transaction"]
            
            transaction_id = tx.get("transaction_id") or data.get("event_id")
            status = tx.get("status", "").upper()
            
            # Veri çekme mantığı
            address = tx.get("to_address") or tx.get("destination", {}).get("address")
            from_address = tx.get("from_address") or tx.get("source", {}).get("address")

            amount_str = tx.get("amount") or tx.get("destination", {}).get("amount")
            amount = float(amount_str) if amount_str else 0
            symbol = tx.get("token_id") or tx.get("coin_code") or tx.get("asset_id")
            chain_id = tx.get("chain_id", "Unknown")
            tx_type = tx.get("type", "").upper()
            
            if not address:
                return
            
            # ÇOK SIKI FİLTRE: Sadece gerçek müşteri yatırımları
            # 1. Tip kontrolü - Sadece DEPOSIT kabul et, diğer HER ŞEYİ engelle
            BLOCKED_TYPES = ["WITHDRAWAL", "SWEEP", "TRANSFER", "TRANSFER_OUT", "TRANSFER_IN", 
                           "INTERNAL_TRANSFER", "CONSOLIDATION", "COLLECTION"]
            
            if tx_type in BLOCKED_TYPES or tx_type not in ["DEPOSIT", "RECEIVE"]:
                logger.info(f"⏭️ Engellenen işlem tipi: {tx_type} - {transaction_id}")
                return

            # 2. Gerçek coin kontrolü - Sadece bilinen coinleri kabul et, fake tokenları engelle
            ALLOWED_TOKENS = ["USDT", "USDC", "TRX", "ETH", "BTC", "LTC", "SOL", "MATIC", "BNB", "XRP", "ADA", "DOT" , "TRON"]
            token_upper = (symbol or "").upper()
            
            is_allowed = False
            for allowed in ALLOWED_TOKENS:
                if allowed in token_upper:
                    is_allowed = True
                    break
            
            if not is_allowed:
                logger.info(f"⏭️ Fake/Spam token engellendi: {symbol} - {transaction_id}")
                return
                
            # 3. Minimum tutar kontrolü - 1 USDT/USD değeri altını engelle
            # 3. Minimum tutar kontrolü - 1 USD (Gerçek Değer) altını engelle
            # Manuel Filtreleme: core/filter/base_volume_filter.py
            from core.filter.base_volume_filter import BaseVolumeFilter
            if await BaseVolumeFilter.should_block_transaction(symbol, amount, transaction_id):
                return
            
            # 4. Sweep/birleştirme kontrolü - from_address bizim cüzdanlarımızdan biriyse engelle
            # (İç transferleri tespit et)
            if from_address:
                # Kendi adreslerimizden gelen işlemleri engelle
                our_addresses = await get_all_our_addresses()
                if from_address in our_addresses:
                    logger.info(f"⏭️ İç transfer engellendi (sweep/consolidation): {transaction_id}")
                    return

            # Mükerrer işlem kontrolü (Sadece Success durumunda bakıyoruz ki Onay mesajları gidebilsin)
            # Mükerrer işlem kontrolü (Sadece Success durumunda bakıyoruz ki Onay mesajları gidebilsin)
            if status in ["COMPLETED", "SUCCESS", "CONFIRMED"]:
                
                # Önce müşteriyi bul (TP Number lazım)
                lead = await get_lead_by_address(address)
                if not lead:
                     # Müşteri yoksa zaten işleyemeyiz
                     logger.warning(f"⚠️ Bilinmeyen adrese deposit: {address} - Tx: {transaction_id}")
                    #  send_telegram_msg(f"⚠️ <b>BİLİNMEYEN ADRESE ÖDEME</b>\n💵 {amount} {symbol}\n📍 {address}")
                     return

                tp_number = lead.get("tp_number")
                name = lead.get("name", "Bilinmeyen")
                
                # ATOMİK KİLİT MEKANİZMASI 🔒
                # TP Number'ı bulduktan sonra kilitlemeyi dene
                
                # --- CURRENCY CONVERTER INTEGRATION ---
                original_amount = amount  # Her ihtimale karşı başlangıçta tanımla
                try:
                    # Blocking request'i executor'da çalıştır (Async yapıyı bozmamak için)
                    loop = asyncio.get_event_loop()
                    cv_data = await loop.run_in_executor(None, coin_parser, symbol, amount)
                    
                    # 2. eleman her zaman USD'dir (converter.py yapısına göre)
                    # Örn: [{"currency": "TRX", "amount": 500}, {"currency": "USD", "amount": 65}]
                    usd_record = cv_data[1]
                    
                    # Ana tutarı USD'ye güncelle
                    amount = float(usd_record['amount'])
                    logger.info(f"💱 Kur Çevirisi Yapıldı: {original_amount} {symbol} -> {amount} USD")
                    
                except Exception as e:
                    logger.error(f"❌ Kur Çevirme Hatası ({symbol}): {e}")
                    # Hata alırsa amount değişmez (Orjinal değerle devam eder)

                # Güncel amount (USD) ile kilitleme yap
                is_locked = await try_lock_transaction(transaction_id, tp_number, amount, symbol, status)
                
                if not is_locked:
                    logger.info(f"⏭️ İşlem zaten işlenmiş (Race Condition Önlemi): {transaction_id}")
                    return

                # Miktar Formatlama (1.545,07 $)
                # Miktar Formatlama (1.545,07 $)
                formatted_amount = "{:,.2f}".format(amount).replace(",", "X").replace(".", ",").replace("X", ".")
                formatted_raw_amount = "{:,.2f}".format(original_amount).replace(",", "X").replace(".", ",").replace("X", ".")
                
                # ONAY BEKLENİYOR - SADECE LOGLA, TELEGRAM ATMA
                if status == "CONFIRMING":
                    logger.info(f"⏳ Ödeme tespit edildi (Onay bekleniyor): {transaction_id}")
                    return

                # TAMAMLANDI (Aktarım Yap)
                # Finansal istatistikleri güncelle
                updated_lead = await update_financial_stats(tp_number, amount, is_deposit=True)
                tot_dep = updated_lead.get("total_deposit", 0)
                tot_with = updated_lead.get("total_withdrawal", 0)
                
                # Yatırım sayısını artır ve yorumu belirle (1=DEPOSIT, 2+=DEPOSIT-2)
                count = await increment_deposit_count(tp_number)
                base_comment = "DEPOSIT" if count == 1 else "DEPOSIT-2"
                
                # MT5'ten City ve Comment bilgilerini çek (Yatırım Uzmanı ve Referans için)
                city_code = "N/A"
                acc_comment = "N/A"
                
                if mt5_manager.connect():
                    try:
                        user_info = mt5_manager.get_user_info(int(tp_number))
                        if user_info:
                            # City kısmından baş harfleri al (Örn: Ankara -> ANK)
                            raw_city = user_info.get('city', 'N/A')
                            city_code = raw_city[:3].upper() if raw_city and raw_city != 'N/A' else 'N/A'
                            acc_comment = user_info.get('comment', 'N/A')
                    finally:
                        mt5_manager.disconnect()

                # Yeni Telegram Formatı
                #Telegram Message 
                msg = (
                    f"🔥🔥💵 <b>KRİPTO YATIRIM</b> 💵🔥🔥\n"
                    f"MOBİL UYGULAMA\n\n"
                    f"<b>Ad Soyad:</b> {name.upper()}\n"
                    f"<b>Coin:</b> {symbol.upper()}\n"
                    f"<b>Ağ:</b> {chain_id.upper()}\n"
                    f"<b>Gelen Tutar:</b> {formatted_raw_amount} {symbol.upper()}\n"
                    f"<b>USD Değeri:</b> {formatted_amount} $\n\n"
                    f"<b>Firma Adı:</b> CEP PORTFOY\n\n"
                    f"<b>TP NUMBER :</b> <code>{tp_number}</code>\n"
                    f"<b>Yatırım Uzmanı :</b> {city_code}\n"
                    f"<b>Referans :</b> {acc_comment}\n"
                    f"<b>Toplam Yatırım:</b> {tot_dep:,.2f}\n"
                    f"<b>Toplam Çekim:</b> {tot_with:,.2f}"
                )
                send_telegram_msg(msg)
                
                # MT5'e bakiye ekle
                # MT5'e bakiye ekle
                if mt5_manager.connect():
                    try:
                        # Tutarın float olduğundan emin ol (Kripto hassasiyeti için yuvarlama YAPILMAZ)
                        # final_amount = round(float(amount), 2) -> İPTAL (BTC gibi değerli coinler için sakıncalı)
                        
                        # MT5'e sadece DEPOSIT veya DEPOSIT-2 yorumunu gönder
                        mt5_comment = base_comment
                        success = mt5_manager.add_balance(int(tp_number), float(amount), mt5_comment)
                        if success:
                            mt5_res = f"✅ <b>MT5 BAKİYE EKLENDİ</b>\n👤 {name}\n💰 {formatted_amount} $ (MT5 Aktarımı Başarılı)\n📝 Yorum: {mt5_comment}"
                            send_telegram_msg(mt5_res)
                        else:
                            send_telegram_msg(f"❌ <b>MT5 İŞLEM HATASI</b>\n👤 {name}\n🔑 {tp_number}\n⚠️ Bakiye eklenemedi (Add Balance False)!")
                    except Exception as e:
                        logger.error(f"MT5 Exception: {e}")
                        send_telegram_msg(f"❌ <b>MT5 KOD HATASI</b>\n👤 {name}\n⚠️ Hata: {str(e)}")
                    finally:
                        mt5_manager.disconnect()
                else:
                    # MT5 Bağlantısı Kurulamazsa
                    logger.error("MT5 Bağlantısı Başarısız!")
                    send_telegram_msg(f"🚨 <b>KRİTİK HATA: MT5 BAĞLANAMADI</b>\n👤 {name}\n💰 {formatted_amount} $\n⚠️ Para veritabanına işlendi ama MT5'e GEÇMEDİ! Manuel kontrol gerekli.")

        else:
            logger.info(f"ℹ️ Diğer event type: {event_type}")

    except Exception as e:
        logger.error(f"❌ Arka plan işlem hatası: {e}")
        import traceback
        traceback.print_exc()

@app.post("/cobo/callback")
async def cobo_callback(request: Request, background_tasks: BackgroundTasks):
    """
    Cobo webhook endpoint'i.
    Hızla 200 OK döner, işlemi background'a atar.
    """
    try:
        # JSON verisini hemen oku
        data = await request.json()
        logger.info(f"📥 Webhook alındı (Queue'ya eklendi): {data.get('event_id', 'unknown')}")
        
        # Ağır işlemi arka plana at
        background_tasks.add_task(process_cobo_notification, data)
        
        # Cobo'ya hemen "ok" (plain text) dön
        from fastapi.responses import Response
        return Response(content="ok", media_type="text/plain")

    except Exception as e:
        logger.error(f"❌ Webhook karşılama hatası: {e}")
        # Hata olsa bile 200 dönelim ki Cobo sürekli retry yapmasın (Loglardan bakarız hataya)
        from fastapi.responses import Response
        return Response(content="ok", media_type="text/plain")

@app.get("/api/system/fix-db")
async def manual_fix_db():
    """
    MANUEL BAKIM BUTONU:
    Eğer sistemde çift kayıt varsa veya index bozulduysa bu linke tıkla.
    Otomatik olarak temizlik yapar ve korumayı açar.
    """
    try:
        await ensure_transaction_index()
        return {"status": "success", "message": "✅ Veritabanı temizlendi ve Unique Index oluşturuldu!"}
    except Exception as e:
        return {"status": "error", "message": f"Hata: {str(e)}"}

@app.post("/api/telegram_command")
async def telegram_command(command: str = Form(...)):
    """
    Telegram bot komutlarını işle
    Kullanım: /sweep - Wallet durumunu ve son işlemleri göster
    """
    logger.info(f"📨 Telegram komutu alındı: {command}")
    try:
        if command.strip().lower() == "/sweep":
            logger.info("🔍 /sweep komutu işleniyor...")
            sweep_service = CoboSweepService()
            wallet_id = os.getenv("COBO_WALLET_ID")
            
            logger.info(f"💼 Wallet ID: {wallet_id}")
            
            if not wallet_id:
                logger.error("❌ Wallet ID bulunamadı!")
                send_telegram_msg("❌ COBO_WALLET_ID .env dosyasında tanımlı değil!")
                return {"status": "error", "message": "Wallet ID not configured"}
            
            send_telegram_msg("🔍 <b>WALLET DURUMU KONTROL EDİLİYOR...</b>")
            
            try:
                # Wallet bilgilerini al
                wallet_info = sweep_service.get_wallet_info(wallet_id)
                
                if not wallet_info.get("success"):
                    error_detail = wallet_info.get("error", "Bilinmeyen hata")
                    send_telegram_msg(f"❌ <b>WALLET BİLGİSİ ALINAMADI</b>\n\n⚠️ {error_detail}\n\n💡 <i>API Key izinlerini kontrol edin (Cobo Portal → Developer Console → API Keys)</i>")
                    return {"status": "error", "message": error_detail}
                
                # Son işlemleri listele
                transactions = sweep_service.list_transactions(wallet_id, limit=10)
                
                # Rapor oluştur
                msg = "📊 <b>COBO WALLET RAPORU</b>\n\n"
                msg += f"🆔 <b>Wallet ID:</b> <code>{wallet_id[:8]}...</code>\n"
                
                if wallet_info.get("data"):
                    w_data = wallet_info["data"]
                    msg += f"📛 <b>İsim:</b> {w_data.get('name', 'N/A')}\n"
                    msg += f"🏷️ <b>Tip:</b> {w_data.get('wallet_type', 'N/A')}\n"
                
                # Son işlemler
                if transactions.get("success") and transactions.get("data"):
                    tx_list = transactions["data"].get("data", [])
                    if tx_list:
                        msg += f"\n📝 <b>Son {len(tx_list)} İşlem:</b>\n"
                        for tx in tx_list[:5]:  # İlk 5 işlem
                            tx_type = tx.get("type", "N/A")
                            amount = tx.get("amount", "0")
                            status = tx.get("status", "N/A")
                            msg += f"  • {tx_type}: {amount} ({status})\n"
                    else:
                        msg += "\n📝 <b>İşlem:</b> Henüz işlem yok\n"
                else:
                    msg += "\n📝 <b>İşlemler:</b> Yüklenemedi\n"
                
                msg += "\n💡 <i>Auto Sweep Cobo Portal'da otomatik çalışıyor.</i>"
                
                send_telegram_msg(msg)
                return {"status": "success", "message": "Wallet info retrieved"}
                
            except Exception as e:
                error_msg = str(e)
                send_telegram_msg(f"❌ <b>HATA</b>\n⚠️ {error_msg}\n\n💡 <i>Detaylar için logları kontrol edin.</i>")
                return {"status": "error", "message": error_msg}
        elif command.strip().lower() == "/admin":
            admin_url = "https://srv.cepteportfoy.com/admin.html" # Frontend sunucusundaki path
            msg = f"🔑 <b>ADMIN PANEL ERİŞİMİ</b>\n\n🌐 {admin_url}\n\n💡 <i>Panel üzerinden para çekme ve istatistikleri yönetebilirsiniz.</i>"
            send_telegram_msg(msg)
            return {"status": "success", "message": "Admin link sent"}
        else:
            return {"status": "error", "message": "Unknown command"}
    except Exception as e:
        logger.error(f"❌ Telegram command error: {e}")
        send_telegram_msg(f"❌ <b>KOMUT HATASI</b>\n⚠️ {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import threading
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes, Defaults
    import requests
    
    # Telegram bot handler
    async def telegram_sweep_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Telegram'dan /sweep komutu"""
        try:
            response = requests.post("http://localhost:8000/api/telegram_command", 
                                    data={"command": "/sweep"}, 
                                    timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    await update.message.reply_text("✅ Wallet bilgileri gruba gönderildi!")
                else:
                    await update.message.reply_text(f"❌ Hata: {result.get('message', 'Bilinmeyen')}")
            else:
                await update.message.reply_text(f"❌ API Hatası: {response.status_code}")
        except Exception as e:
            await update.message.reply_text(f"❌ Bağlantı Hatası: {str(e)}")
    
    async def telegram_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Telegram'dan /admin komutu"""
        try:
            response = requests.post("http://localhost:8000/api/telegram_command", 
                                    data={"command": "/admin"}, 
                                    timeout=30)
        except Exception as e:
            await update.message.reply_text(f"❌ Bağlantı Hatası: {str(e)}")

    async def telegram_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Telegram /start komutu"""
        await update.message.reply_text(
            "🤖 Cobo Wallet Bot\n\n"
            "Komutlar:\n"
            "/sweep - Wallet durumunu görüntüle\n"
            "/admin - Admin panel linkini al\n"
            "/start - Bu mesajı göster"
        )
    
    def run_telegram_bot():
        """Telegram bot'u ayrı thread'de çalıştır"""
        try:
            logger.info("🤖 Telegram Bot başlatılıyor...")
            
            # Yeni bir event loop oluştur ve thread'e ata
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Telegram bot - job_queue'yu devre dışı bırak (timezone hatası önleme)
            from telegram.ext import ApplicationBuilder
            
            application = (
                ApplicationBuilder()
                .token(os.getenv("TELEGRAM_BOT_TOKEN"))
                .job_queue(None)  # Job queue'yu devre dışı bırak
                .build()
            )
            
            application.add_handler(CommandHandler("start", telegram_start_command))
            application.add_handler(CommandHandler("sweep", telegram_sweep_command))
            application.add_handler(CommandHandler("admin", telegram_admin_command))

            
            logger.info("✅ Telegram Bot hazır!")
            application.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)
        except Exception as e:
            logger.error(f"❌ Telegram Bot hatası: {e}")
            import traceback
            traceback.print_exc()
    
    # Telegram bot'u ayrı thread'de başlat
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    # Kısa bir bekleme - bot başlasın
    import time
    time.sleep(2)
    
    # Başlangıç mesajı kaldırıldı (User isteği)
    # send_telegram_msg("🚀 *Cobo, CRM & MT5 Entegre Sistem Yayında!*\n\n📋 Komutlar:\n/sweep - Wallet durumunu görüntüle")
    
    # FastAPI'yi başlat
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)), proxy_headers=True, forwarded_allow_ips='*')
