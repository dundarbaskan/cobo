# 🔀 Coin Routing Nasıl Çalışır?

Bu rehber, cüzdanlarımıza gelen kripto paraların, türlerine göre otomatik olarak ana kasaya ya da dönüşüm (convert) cüzdanlarına transfer edilmesini sağlayan **Coin Routing (Sweep/Süpürme)** mekanizmasını açıklamaktadır.

---

## 📋 İş Akış Şeması

```mermaid
flowchart TD
    A[Başarılı Kripto Yatırımı Webhook] --> B{get_target_wallet symbol}
    
    B -->|USDT / USDC| C[MAIN_WALLET \n 'Ana Kasa']
    B -->|ETH| D[ETH_CONVERTER_WALLET \n 'ETH Convert Cüzdanı']
    B -->|BTC| E[BTC_CONVERTER_WALLET \n 'BTC Convert Cüzdanı']
    B -->|TRX / TRON| F[TRX_CONVERTER_WALLET \n 'TRX Convert Cüzdanı']
    B -->|Diğer Coinler| G[MAIN_WALLET \n 'Ana Kasa (Varsayılan)']

    C & D & E & F & G --> H{Hedef Adres ve Wallet ID Mevcut mu?}
    H -->|Hayır| I[Routing Pas Geçilir / Log Atılır]
    H -->|Evet| J[CoboWithdrawalService.create_withdrawal]
    
    J --> K{Cobo API Transfer Sonucu?}
    K -->|Başarılı| L[Telegram Bildirimi Gönder]
    K -->|Başarısız / Hata| M[Telegram Hata Bildirimi Gönder]

    L -->|Ana Kasa ise| L1[🏦 ANA CÜZDANA PARA GÖNDERİLDİ]
    L -->|Convert ise| L2[🔄 CONVERT CÜZDANINA PARA GÖNDERİLDİ]
```

---

## 🛠️ Detaylı Süreç ve Teknik İnceleme

### 1. Hedef Cüzdanların Tanımlanması
Coin routing işleminin yapılabilmesi için hedef cüzdan adresleri projenin `.env` dosyası üzerinden okunur. Bu adresler şirket içi güvenli ana kasaları veya dönüşüm (convert) hesaplarını temsil eder:
* `MAIN_WALLET`: USDT ve USDC gibi stabil coinlerin toplanacağı ana kasa adresi.
* `ETH_CONVERTER_WALLET`: Ethereum yatırımlarının gönderileceği dönüşüm cüzdan adresi.
* `BTC_CONVERTER_WALLET`: Bitcoin yatırımlarının gönderileceği dönüşüm cüzdan adresi.
* `TRX_CONVERTER_WALLET`: Tron/TRX yatırımlarının gönderileceği dönüşüm cüzdan adresi.

### 2. Yönlendirme Kuralları (`core/routing/coin_router.py`)
Gelen coin sembolüne göre hedef cüzdan adresini ve etiketini belirleyen kurallar şunlardır:
1. **USDT / USDC:** Doğrudan `MAIN_WALLET` adresine yönlendirilir. Etiket: `"Ana Kasa"`, `is_main: True`.
2. **ETH:** `ETH_CONVERTER_WALLET` adresine yönlendirilir. Etiket: `"ETH Convert Cüzdanı"`, `is_main: False`.
3. **BTC:** `BTC_CONVERTER_WALLET` adresine yönlendirilir. Etiket: `"BTC Convert Cüzdanı"`, `is_main: False`.
4. **TRX / TRON:** `TRX_CONVERTER_WALLET` adresine yönlendirilir. Etiket: `"TRX Convert Cüzdanı"`, `is_main: False`.
5. **Diğer Tanımsız Kriptolar:** Güvenlik amacıyla varsayılan olarak `MAIN_WALLET` adresine yönlendirilir. Etiket: `"Ana Kasa (Varsayılan)"`, `is_main: True`.

### 3. Otomatik Sweep (Süpürme) Transfer Süreci
Yatırım işlemi webhook tarafından başarıyla algılanıp onay aşamasına geçildiğinde, arka planda **otomatik sweep** süreci tetiklenir:
1. **Servis Çağrısı:** `CoboWithdrawalService` sınıfı çağrılır. Ağ isteği olması nedeniyle, FastAPI event loop'unu engellememek için `run_in_executor` ile asenkron olarak çalıştırılır.
2. **Cobo Transfer Talebi (`create_withdrawal`):**
   * **Kaynak:** `Org-Controlled` (Kuruluş kontrollü cüzdan ve webhook'tan gelen cüzdanın `wallet_id`'si).
   * **Hedef:** `Address` (Yukarıdaki yönlendirme kurallarına göre belirlenen cüzdan adresi).
   * **Miktar:** Gelen orijinal kripto para miktarı (komisyon düşülmeden ham miktar gönderilir).
   * **Kategori:** `Withdrawal`.
   * **Açıklama:** `"Auto-routed to {wallet_label}"`.
3. **Talep Sonucu:**
   * Cobo API transferi başarıyla oluşturursa, Telegram grubuna transfer türüne göre formatlı bir bildirim gönderilir.
   * Transfer başarısız olursa (örneğin ağ ücreti yetersizliği veya API kısıtlaması gibi durumlarda), Telegram grubuna kırmızı ünlemli `❌ ROUTING BAŞARISIZ` uyarısı atılır.

---

## 📢 Telegram Bildirim Şablonları

### Ana Kasaya Gönderildiğinde
> 🏦 **ANA CÜZDANA PARA GÖNDERİLDİ**  
> 💵 **Coin:** USDT | **Tutar:** 1.000,00  
> 📍 **Hedef:** `TXXXXX...`  
> 🏷️ **Etiket:** Ana Kasa  

### Dönüşüm (Convert) Cüzdanına Gönderildiğinde
> 🔄 **CONVERT CÜZDANINA PARA GÖNDERİLDİ**  
> 💵 **Coin:** ETH | **Tutar:** 0,542  
> 📍 **Hedef:** `0xXXXX...`  
> 🏷️ **Etiket:** ETH Convert Cüzdanı  

---

## 🔗 İlgili Bağlantılar
* Webhook bildirimlerinin nasıl tetiklendiğini görmek için: [[Webhook_Bildirimleri_Nasil_Calisir]]
* MT5 bakiye aktarım ve onay süreçlerini incelemek için: [[MT5_Bakiye_Aktarimi_Nasil_Onaylanir]]
* Cüzdan oluşturma adımlarını incelemek için: [[Cuzdan_Nasil_Olusturulur]]

---
#group/coin-routing #group/waas #group/telegram
