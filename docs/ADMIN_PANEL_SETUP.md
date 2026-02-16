# 🏦 Cobo Admin Panel - Kurulum Rehberi

## ✅ Oluşturulan Dosyalar

1. **admin.html** - Web tabanlı admin paneli
2. **admin_api.py** - Admin panel API endpoint'leri
3. **servisler/withdrawal_service.py** - Para çekme servisi
4. **cobo_manager.py** - Komut satırı yönetim aracı

## 🚀 Kurulum

### 1. Admin API'yi main.py'ye Ekleyin

`main.py` dosyasının başına (satır 31'den sonra) şunu ekleyin:

```python
# Admin Panel Router
from admin_api import router as admin_router
app.include_router(admin_router)
```

### 2. main.py'yi Yeniden Başlatın

```bash
# Mevcut süreci durdurun (Ctrl+C)
# Sonra yeniden başlatın:
python main.py
```

## 📊 Kullanım

### Web Admin Paneli

1. Tarayıcınızda açın:
   ```
   http://localhost:8000/admin
   ```

2. **Özellikler:**
   - 📊 Dashboard - Genel bakış ve istatistikler
   - 💼 Wallet - Wallet bilgileri ve adresler
   - 📝 İşlemler - Tüm işlem geçmişi
   - 💸 Para Çekme - Manuel withdrawal işlemi

### Komut Satırı Aracı

```bash
python cobo_manager.py
```

**Menü Seçenekleri:**
1. Wallet Bilgilerini Görüntüle
2. Son İşlemleri Listele
3. Adresleri Listele
4. Bakiye Kontrolü
5. Wallet Durumunu Telegram'a Gönder

## 💸 Para Çekme İşlemi

### Web Panelinden:

1. Admin panelde "Para Çekme" sekmesine gidin
2. Formu doldurun:
   - **Hedef Adres**: TRX/ETH/BSC adresi
   - **Miktar**: Çekilecek miktar
   - **Token**: USDT, USDC, TRX vb.
   - **Blockchain**: TRON, ETH, BSC
   - **Not**: İsteğe bağlı açıklama

3. "Para Çek" butonuna tıklayın
4. İşlem onayı Telegram'a gelecek

### API ile:

```bash
curl -X POST http://localhost:8000/api/admin/withdrawal \
  -H "Content-Type: application/json" \
  -d '{
    "to_address": "TRX_ADDRESS_HERE",
    "amount": "100",
    "token_id": "USDT",
    "chain_id": "TRON",
    "note": "Test withdrawal"
  }'
```

## 🔐 Güvenlik

- Admin paneline erişim için şu anda kimlik doğrulama YOK
- Üretim ortamında mutlaka authentication ekleyin
- Withdrawal işlemleri Telegram'a bildirim gönderir

## 📱 Telegram Bildirimleri

Para çekme işlemi yapıldığında otomatik olarak Telegram'a bildirim gider:

```
💸 PARA ÇEKME İŞLEMİ

📍 Adres: TRX123...
💵 Miktar: 100 USDT
🌐 Chain: TRON
🆔 Request ID: withdrawal_abc123
```

## 🛠️ API Endpoint'leri

- `GET /admin` - Admin panel HTML
- `GET /api/admin/dashboard` - Dashboard verileri
- `GET /api/admin/wallet` - Wallet bilgileri
- `GET /api/admin/addresses` - Adres listesi
- `GET /api/admin/transactions` - İşlem listesi
- `POST /api/admin/withdrawal` - Para çekme

## ⚠️ Önemli Notlar

1. **Cobo API İzinleri**: API Key'inizin withdrawal yetkisi olmalı
2. **Test Edin**: İlk işlemi küçük miktarla test edin
3. **Adres Kontrolü**: Hedef adresi mutlaka kontrol edin
4. **Network Seçimi**: Doğru blockchain'i seçtiğinizden emin olun

## 🐛 Sorun Giderme

### Admin panel açılmıyor
- `admin_api.py` import edildi mi kontrol edin
- `main.py` yeniden başlatıldı mı?

### Withdrawal çalışmıyor
- Cobo API Key izinlerini kontrol edin
- Wallet ID doğru mu?
- Yeterli bakiye var mı?

### Telegram bildirimi gelmiyor
- `TELEGRAM_BOT_TOKEN` ve `TELEGRAM_CHAT_ID` doğru mu?
- `send_telegram_msg` fonksiyonu çalışıyor mu?

## 📞 Destek

Sorun yaşarsanız:
1. Terminal loglarını kontrol edin
2. Tarayıcı console'unu kontrol edin (F12)
3. Cobo Portal'da API loglarına bakın
