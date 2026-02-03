# Cobo Auto Sweep Kurulum Rehberi

## 🎯 Amaç
Cobo Portal'daki tüm deposit adreslerinden gelen paraları otomatik olarak ana cüzdana toplamak (sweep).

## 📋 Kurulum Adımları

### 1. Wallet ID'yi Bulun
1. [Cobo Portal](https://portal.cobo.com/login) adresine giriş yapın
2. **Wallets** menüsüne gidin
3. Kullandığınız Custodial Wallet'ı seçin
4. URL'deki wallet ID'yi kopyalayın (örn: `https://portal.cobo.com/wallets/WALLET_ID_BURAYA`)

### 2. .env Dosyasını Güncelleyin
`.env` dosyasındaki `COBO_WALLET_ID` değerini bulduğunuz ID ile değiştirin:
```
COBO_WALLET_ID=your_actual_wallet_id_here
```

### 3. Sunucuyu Yeniden Başlatın
```bash
# Mevcut main.py'yi durdurun (Ctrl+C)
# Yeniden başlatın:
python main.py
```

## 🚀 Kullanım

### Manuel Sweep Tetikleme
Sweep işlemini manuel olarak başlatmak için:

```bash
python trigger_sweep.py
```

### API Üzerinden
```bash
curl -X POST http://localhost:8000/api/telegram_command \
  -d "command=/sweep"
```

## 📊 Sweep Nasıl Çalışır?

1. **Otomatik Sweep (Cobo Portal'da yapılandırılır)**:
   - Cobo Portal → Wallets → Settings → Auto Sweep
   - Minimum threshold belirleyin (örn: 10 USDT)
   - Sistem otomatik olarak bu tutarı geçen adresleri ana cüzdana toplar

2. **Manuel Sweep (Bu entegrasyon)**:
   - `/sweep` komutu ile istediğiniz zaman tetikleyebilirsiniz
   - Tüm deposit adreslerindeki fonları hemen ana cüzdana toplar
   - Telegram'dan bildirim alırsınız

## ⚙️ Desteklenen Ağlar
- TRX (Tron) - USDT
- ETH (Ethereum) - USDT (isteğe bağlı, main.py'de yorum satırını kaldırın)
- BSC (Binance Smart Chain) - USDT (eklenebilir)

## 🔔 Telegram Bildirimleri
Sweep işlemi başladığında ve tamamlandığında Telegram'dan bildirim alırsınız:
- 🔄 "AUTO SWEEP BAŞLATILIYOR..."
- ✅ "SWEEP BAŞARILI! Tüm fonlar ana cüzdana toplandı."
- ❌ "SWEEP HATASI" (hata durumunda)

## 🛠️ Sorun Giderme

### "Wallet ID not configured" hatası
- `.env` dosyasında `COBO_WALLET_ID` değerini kontrol edin
- Sunucuyu yeniden başlatın

### Sweep çalışmıyor
1. Cobo Portal'da Auto Sweep özelliğinin aktif olduğundan emin olun
2. API Key'in gerekli izinlere sahip olduğunu kontrol edin:
   - Wallets → Read
   - Wallets → Write
   - Transactions → Read

### API İzinleri
Cobo Portal → Developer Console → API Keys:
- `Wallets` scope'u aktif olmalı
- `Auto Sweep` yetkisi verilmiş olmalı

## 📝 Notlar
- Sweep işlemi gas fee gerektirir (Cobo otomatik halleder)
- Minimum sweep tutarını Cobo Portal'dan ayarlayabilirsiniz
- Her sweep işlemi transaction history'de görünür
