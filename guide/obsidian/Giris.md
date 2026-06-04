# 🚀 Cobo - MT5 Entegrasyon Projesi

Bu dökümantasyon, projenin kripto ve fiat ödeme altyapısının MetaTrader 5 (MT5) ile entegrasyon süreçlerini, iş mantığını ve teknik detaylarını içermektedir. Projenin genel amacı, kullanıcıların kripto paralar ve banka havalesi (IBAN) yoluyla yaptıkları yatırımların kur çevirileri ve komisyon hesaplamalarıyla birlikte otomatik/onaylı bir şekilde MT5 hesaplarına bakiye olarak aktarılmasını sağlamaktır.

## 📌 Ana Süreçler ve Rehberler

Projenin tüm detaylarını soru-cevap mantığıyla açıklayan rehber bağlantıları aşağıdadır:

1. **Cobo WaaS Cüzdan Yönetimi:**
   * [[Cuzdan_Nasil_Olusturulur]]: Müşteri için yeni kripto cüzdan adresi üretimi ve doğrulama süreci nasıl işler?
2. **Cobo Webhook İşleyici:**
   * [[Webhook_Bildirimleri_Nasil_Calisir]]: Cobo'dan gelen anlık işlem bildirimleri nasıl yakalanır, filtrelenir ve kilitlenir?
3. **MT5 Entegrasyonu & Telegram Onay Akışı:**
   * [[MT5_Bakiye_Aktarimi_Nasil_Onaylanir]]: Yatırımlar MT5'e nasıl aktarılır, komisyonlar nasıl hesaplanır ve Telegram butonları üzerinden onay süreci nasıl yönetilir?
4. **Coin Routing & Sweep:**
   * [[Coin_Routing_Nasil_Calisir]]: Gelen kripto paralar otomatik olarak ana kasaya veya convert cüzdanlarına nasıl süpürülür (sweep)?
5. **IBAN & Çekim Süreçleri:**
   * [[Kullanici_Nasil_Yatirim_Yapacak]]: Banka havalesiyle yatırım, çekim talepleri ve kopyalama bildirimleri nasıl işler?

---

## 🎨 Obsidian Graph View Grupları ve Renk Şeması

Obsidian graph view'da süreçleri ve dosyaları kolayca ayırt edebilmek amacıyla aşağıdaki etiketler (`tags`) kullanılmıştır. Grafiğinizde grupları bu etiketlere göre renklendirebilirsiniz:

* 🔴 **`#group/fiat` (Kırmızı):** IBAN / Havale Yatırım & Çekim işlemleriyle ilgili süreçler.
* 🟠 **`#group/waas` (Turuncu):** Cobo WaaS API entegrasyonu, cüzdan adresi oluşturma ve webhook bildirimleri.
* 🟢 **`#group/mt5` (Yeşil):** MT5 bakiye işlemleri, dealer balance komutları ve veri senkronizasyonu.
* 🔵 **`#group/telegram` (Mavi/Cyan):** Telegram botu, komut API'si ve yetkili admin onay/ret butonları.
* 🟣 **`#group/coin-routing` (Mor):** Gelen kripto paraların cüzdanlar arası sweep edilme (routing) mantığı.

---

## 🗺️ Süreç Haritası (Canvas)

Süreçlerin görsel akış şemasını ve cüzdanlar arası ilişkileri görmek için:
📂 **[[Proje_Genel_Haritasi.canvas]]** dosyasını Obsidian üzerinde açabilirsiniz.

---
#guide #cobo #mt5 #integration #documentation
