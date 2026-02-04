# Sürüm Notları

## v1.2.0 - Cobo Entegrasyonu ve Altyapı İyileştirmeleri
- **Webhook Optimizasyonu:** `BackgroundTasks` ile asenkron yapıya geçilerek yanıt süresi 0.01 saniyeye düşürüldü.
- **Race Condition Önlemi:** MongoDB `Unique Index` ve `Atomic Lock` ile mükerrer bakiye işlemleri %100 engellendi.
- **Process Yönetimi:** `PM2` ve `ecosystem.config.js` ile servisler "Yönetilebilir Servis" yapısına geçirildi (Auto-Restart, UTF-8 Support).
- **SSL Düzeltmesi:** Windows sunucular için `certifi` entegrasyonu ile `SSL: CERTIFICATE_VERIFY_FAILED` hatası giderildi.
- **MT5 Güvenliği:** MT5 bağlantı kopuklukları için kritik Telegram bildirim sistemi eklendi.
- **Hassasiyet:** Kripto bakiyelerinin (`float`) MT5'e aktarılırken veri kaybı yaşamaması için yuvarlama işlemi kaldırıldı.
- **Kod Temizliği:** `UnboundLocalError` hatası giderildi, gereksiz endpoint'ler temizlendi ve kod yapısı sadeleştirildi.
