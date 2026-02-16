# 🏗️ COBO Projesi — Kurumsal Mimari Modernizasyon Rehberi

> **Tarih:** 16 Şubat 2026  
> **Durum:** Mevcut Durum Analizi + Adım Adım Refactoring Planı  
> **Kural:** Bu rehberde KOD YAZILMAZ. Sadece nereyi, nasıl, hangi sırayla değiştireceğin anlatılır.  
> **PM2 Çalışan Dosyalar:** `main.py` (COBO-API) ve `mt5_worker.py` (COBO-MT5-WORKER)

---

## 📋 İÇİNDEKİLER

1. [Mevcut Proje Yapısı (Analiz)](#1-mevcut-proje-yapısı-analiz)
2. [Hedef Klasör Yapısı (Kurumsal Mimari)](#2-hedef-klasör-yapısı-kurumsal-mimari)
3. [main.py Parçalama Planı (Satır Satır)](#3-mainpy-parçalama-planı-satır-satır)
4. [mt5_worker.py İyileştirme Planı](#4-mt5_workerpy-i̇yileştirme-planı)
5. [Servisler Klasörü Yeniden Yapılandırma](#5-servisler-klasörü-yeniden-yapılandırma)
6. [Admin API Entegrasyonu](#6-admin-api-entegrasyonu)
7. [Konfigürasyon ve Ortam Değişkenleri](#7-konfigürasyon-ve-ortam-değişkenleri)
8. [ecosystem.config.js Güncelleme](#8-ecosystemconfigjs-güncelleme)
9. [İşlem Sırası (Yapılması Gereken Adımlar)](#9-i̇şlem-sırası-yapılması-gereken-adımlar)
10. [Dikkat Edilecekler ve Riskler](#10-dikkat-edilecekler-ve-riskler)

---

## 1. Mevcut Proje Yapısı (Analiz)

### 🔴 Şu Anki Durum (Dağınık)

```
COBO/
├── main.py                  ← 628 SATIR! Her şey burada (API, Webhook, Telegram, QR, Filtre vb.)
├── mt5_worker.py            ← 80 satır, MT5 senkronizasyonu (PM2 ile çalışıyor)
├── admin_api.py             ← 251 satır, Admin panel endpointleri (main.py'ye import YAPILMIYOR!)
├── cobo_manager.py          ← 169 satır, Manuel CLI aracı (bağımsız)
├── crm_worker.py            ← 46 satır, CRM senkronizasyon worker'ı (KULLANILMIYOR)
├── supervisor.py            ← 64 satır, Eski supervisor (PM2 varken gereksiz)
├── telegram_bot.py          ← 67 satır, Eski standalone telegram bot (main.py içinde zaten var)
├── get_chat_id.py           ← Yardımcı script
├── setup_test_user.py       ← Test scripti
├── test_bot_standalone.py   ← Test scripti
├── test_race.py             ← Test scripti
├── test_sweep_local.py      ← Test scripti
├── test_telegram.py         ← Test scripti
├── trigger_sweep.py         ← Yardımcı script
├── index.html               ← Frontend (25KB)
├── admin.html               ← Admin panel frontend (25KB)
├── ecosystem.config.js      ← PM2 konfig dosyası
├── .env                     ← Ortam değişkenleri
├── servisler/               ← Servis modülleri (İsim Türkçe, karışık)
│   ├── db_service.py        ← MongoDB fonksiyonları
│   ├── mt5service.py        ← MT5 sınıfı
│   ├── sweep_service.py     ← Cobo sweep işlemleri
│   ├── withdrawal_service.py ← Cobo withdrawal işlemleri
│   ├── crmservice.py        ← CRM scraper
│   └── crm_sync_service.py  ← CRM senkronizasyon (Kullanılmıyor?)
├── core/                    ← Core modüller (iyi fikir ama yarım kalmış)
│   ├── filter/
│   │   └── base_volume_filter.py
│   └── currency/
│       └── converter/
│           ├── converter.py
│           └── converter_tester.py
├── bases/                   ← MT5 server dosyaları (dokunulmayacak)
├── logolar/                 ← Statik dosyalar
└── logs/                    ← PM2 log dosyaları
```

### 🔴 Temel Sorunlar:

| # | Sorun | Detay |
|---|-------|-------|
| 1 | **main.py çok büyük** | 628 satır, ~7 farklı sorumluluk tek dosyada |
| 2 | **Klasör isimleri tutarsız** | `servisler` (Türkçe) vs `core` (İngilizce) |
| 3 | **Kullanılmayan dosyalar** | `supervisor.py`, `telegram_bot.py`, `crm_worker.py` artık gereksiz |
| 4 | **admin_api.py entegre değil** | Router tanımlı ama `main.py`'de `app.include_router()` yok |
| 5 | **Test dosyaları kök dizinde** | `test_*.py` dosyaları kök dizini kirletiyor |
| 6 | **HTML dosyaları kök dizinde** | `index.html`, `admin.html` ayrı bir klasörde olmalı |
| 7 | **Telegram bot main.py içinde** | 80+ satırlık bot kodu main.py'nin sonunda gömülü |

---

## 2. Hedef Klasör Yapısı (Kurumsal Mimari)

### 🟢 Hedeflenen Durum (Temiz)

```
COBO/
│
├── main.py                      ← ~80-100 satır MAX! Sadece app oluşturma, router bağlama ve başlatma
├── mt5_worker.py                ← Aynı kalır (PM2 ile çalışıyor, minimal)
├── ecosystem.config.js          ← PM2 konfig (Aynı kalır)
├── .env                         ← Ortam değişkenleri (Aynı kalır)
├── .gitignore
│
├── config/                      ← 🆕 Konfigürasyon Modülleri
│   ├── __init__.py
│   ├── settings.py              ← .env okuma, sabitler, MT5 config, API URL'ler
│   └── constants.py             ← ALLOWED_TOKENS, BLOCKED_TYPES gibi sabit listeler
│
├── api/                         ← 🆕 FastAPI Endpoint'leri (Router'lar)
│   ├── __init__.py
│   ├── home_router.py           ← GET "/" - Ana sayfa
│   ├── wallet_router.py         ← POST "/api/verify_tp", POST "/api/create_wallet"
│   ├── webhook_router.py        ← POST "/cobo/callback" (Webhook endpoint)
│   ├── system_router.py         ← GET "/api/system/fix-db" (Bakım endpoint'i)
│   ├── telegram_router.py       ← POST "/api/telegram_command" (Telegram komut API)
│   └── admin_router.py          ← Admin panel endpoint'leri (mevcut admin_api.py taşınacak)
│
├── services/                    ← 🔄 Servisler (Mevcut "servisler/" yeniden adlandırılacak)
│   ├── __init__.py
│   ├── database.py              ← Mevcut db_service.py (yeniden adlandırma)
│   ├── mt5_manager.py           ← Mevcut mt5service.py (yeniden adlandırma)
│   ├── cobo_sweep.py            ← Mevcut sweep_service.py (yeniden adlandırma)
│   ├── cobo_withdrawal.py       ← Mevcut withdrawal_service.py (yeniden adlandırma)
│   ├── telegram_service.py      ← 🆕 Telegram mesaj gönderme (send_telegram_msg)
│   └── qr_service.py            ← 🆕 QR kod üretme (generate_qr_base64)
│
├── workers/                     ← 🆕 Arka Plan İşleyicileri
│   ├── __init__.py
│   └── webhook_processor.py     ← 🆕 process_cobo_notification fonksiyonu (main.py'den çıkarılacak)
│
├── core/                        ← ✅ Çekirdek İş Mantığı (Mevcut, genişletilecek)
│   ├── __init__.py
│   ├── filter/
│   │   ├── __init__.py
│   │   └── base_volume_filter.py ← Aynı kalır
│   └── currency/
│       └── converter/
│           ├── __init__.py
│           ├── converter.py      ← Aynı kalır
│           └── converter_tester.py
│
├── bot/                         ← 🆕 Telegram Bot Modülü
│   ├── __init__.py
│   └── telegram_bot.py          ← main.py'nin sonundaki bot kodları buraya
│
├── templates/                   ← 🆕 HTML Dosyaları
│   ├── index.html               ← Mevcut index.html taşınacak
│   └── admin.html               ← Mevcut admin.html taşınacak
│
├── static/                      ← 🆕 Statik Dosyalar
│   └── logolar/                 ← Mevcut logolar/ taşınacak
│
├── tests/                       ← 🆕 Test Dosyaları
│   ├── test_race.py             ← Kök dizinden taşınacak
│   ├── test_telegram.py
│   ├── test_bot_standalone.py
│   ├── test_sweep_local.py
│   └── setup_test_user.py
│
├── tools/                       ← 🆕 Yardımcı Araçlar (Manuel çalıştırılan scriptler)
│   ├── cobo_manager.py          ← Kök dizinden taşınacak
│   ├── get_chat_id.py
│   └── trigger_sweep.py
│
├── archive/                     ← 🆕 Kullanılmayan/Eski Dosyalar (Silinmeden önce buraya)
│   ├── supervisor.py            ← PM2 varken artık gereksiz
│   ├── telegram_bot.py          ← main.py içinde zaten var, standalone versiyon
│   ├── crm_worker.py            ← Kullanılmıyorsa arşive
│   ├── crmservice.py            ← Kullanılmıyorsa arşive
│   └── crm_sync_service.py      ← Kullanılmıyorsa arşive
│
└── docs/                        ← 🆕 Dökümanlar
    ├── README.md                ← Mevcut README taşınabilir veya kök dizinde kalabilir
    ├── RELEASE.md
    └── Workflow_Modern_Modify_system.md  ← Bu dosya
```

---

## 3. main.py Parçalama Planı (Satır Satır)

### Mevcut main.py: 628 satır → Hedef: ~80-100 satır

Aşağıda `main.py`'nin her bölümü satır numarasıyla analiz edilmiş ve nereye taşınacağı belirtilmiştir.

---

### 📦 PARÇA 1: Import'lar ve Konfigürasyon
**Satır 1 — Satır 38**

**Ne Yapıyor:** Tüm import'lar, .env yükleme, logging ayarları ve `app = FastAPI()` tanımı.

**Ne Yapılmalı:**
- `Satır 1-16`: Import'lar — Her dosya kendi import'unu yapacağı için burası parçalanmayla otomatik küçülecek.
- `Satır 17-22`: `from servisler.db_service import (...)` → `from services.database import (...)` olarak güncellenecek.
- `Satır 23-25`: Servis import'ları → Yeni yollarla güncellenecek.
- `Satır 27-35`: `.env` yükleme ve logging → `config/settings.py` dosyasına taşınacak.
- `Satır 37`: `app = FastAPI()` → main.py'de kalacak (bu zaten orada olmalı).

**Hedef Dosya:** `config/settings.py`

**Yorum satırı önerisi:**
```python
# config/settings.py
# Ortam değişkenleri, logging konfigürasyonu ve uygulama sabitleri
# Tüm .env okuma işlemleri merkezi olarak buradan yapılır.
```

---

### 📦 PARÇA 2: Startup Event
**Satır 39 — Satır 57**

**Ne Yapıyor:** FastAPI `on_event("startup")` ile uygulama başlarken veritabanı index kontrolü yapıyor.

**Ne Yapılmalı:**
- Bu kod `main.py`'de **kalabilir** çünkü doğrudan `app` nesnesine bağlı bir lifecycle event'idir.
- Ancak iç mantığı (index oluşturma) zaten `db_service.py`'de, bu iyi.
- main.py'de sadece event dekoratörü ve `await` çağrısı kalmalı.

**Hedef Dosya:** `main.py`'de kalır (ama sadece 5-6 satır olarak).

**Yorum satırı önerisi:**
```python
# Uygulama Yaşam Döngüsü: Startup
# DB bağlantısı ve güvenlik index'lerini kontrol eder.
# Detaylı logic: services/database.py -> ensure_transaction_index()
```

---

### 📦 PARÇA 3: MT5 Konfigürasyonu ve Statik Dosyalar
**Satır 58 — Satır 69**

**Ne Yapıyor:** MT5 bağlantı bilgilerini `.env`'den okur, `MT5UserManager` nesnesi oluşturur. `logolar/` dizinini mount eder.

**Ne Yapılmalı:**
- `Satır 59-64`: MT5 konfigürasyonu ve `mt5_manager` nesnesi → `config/settings.py` dosyasına taşınacak.
- `Satır 66-69`: Static file mounting → main.py'de kalabilir ama path `static/logolar` olarak güncellenecek.

**Hedef Dosya:** `config/settings.py` (MT5 config) + `main.py` (static mount, 2 satır)

**Yorum satırı önerisi:**
```python
# config/settings.py
# MT5 Bağlantı Konfigürasyonu
# Singleton MT5UserManager örneği — tüm modüllerden import edilip kullanılır.
```

---

### 📦 PARÇA 4: QR Kod Üretici
**Satır 71 — Satır 78**

**Ne Yapıyor:** Bir cüzdan adresinden QR kod üretip base64 string olarak döndürüyor.

**Ne Yapılmalı:**
- Bu fonksiyon `main.py`'de olmamalı. Tamamen bağımsız bir yardımcı (utility) fonksiyon.
- `services/qr_service.py` dosyasına taşınacak.
- main.py'den çıkarılınca, kullanan yerler (create_wallet endpointi) bu servisi import edecek.

**Hedef Dosya:** `services/qr_service.py`

**Yorum satırı önerisi:**
```python
# services/qr_service.py
# QR Kod üretim servisi
# Cüzdan adresleri ve herhangi bir veri için PNG formatında QR kod üretir.
# Çıktı: Base64 encoded PNG string (HTML <img> tag'inde kullanılabilir)
```

---

### 📦 PARÇA 5: Telegram Mesaj Gönderici
**Satır 80 — Satır 94**

**Ne Yapıyor:** Telegram Bot API kullanarak bir metin mesajı gönderiyor (HTML parse mode ile).

**Ne Yapılmalı:**
- Bu fonksiyon projenin **en çok kullanılan** yardımcı fonksiyonlarından biri.
- `main.py`, `admin_api.py` ve muhtemelen diğer yerlerden çağrılıyor.
- `services/telegram_service.py` dosyasına taşınmalı.
- **DİKKAT:** `admin_api.py` satır 31-37'de bu fonksiyonun bir kopyası var! Duplikasyon temizlenecek.

**Hedef Dosya:** `services/telegram_service.py`

**Yorum satırı önerisi:**
```python
# services/telegram_service.py
# Merkezi Telegram Bildirim Servisi
# Tüm sistem bildirimleri (yatırım, hata, durum) bu servis üzerinden gönderilir.
# Parse mode: HTML — <b>, <code>, <i> tag'leri desteklenir.
# ÖNEMLİ: Projenin HER YERİNDEN tek bu dosya import edilerek kullanılmalıdır.
# Admin API'deki kopya kaldırılmalıdır.
```

---

### 📦 PARÇA 6: Ana Sayfa Endpoint'i
**Satır 96 — Satır 99**

**Ne Yapıyor:** `GET /` → `index.html` dosyasını döndürüyor.

**Ne Yapılmalı:**
- `api/home_router.py` dosyasına taşınacak.
- HTML dosya yolu `templates/index.html` olarak güncellenecek.
- `APIRouter()` kullanılacak.

**Hedef Dosya:** `api/home_router.py`

**Yorum satırı önerisi:**
```python
# api/home_router.py
# Ana Sayfa Router'ı
# Kullanıcıya yatırım arayüzünü (index.html) sunar.
# İlgili HTML: templates/index.html
```

---

### 📦 PARÇA 7: TP Doğrulama Endpoint'i
**Satır 103 — Satır 123**

**Ne Yapıyor:** `POST /api/verify_tp` → TP numarasını MongoDB'de arar, müşteri bilgilerini döndürür.

**Ne Yapılmalı:**
- `api/wallet_router.py` dosyasına taşınacak.
- `APIRouter(prefix="/api", tags=["Wallet"])` kullanılacak.

**Hedef Dosya:** `api/wallet_router.py`

**Yorum satırı önerisi:**
```python
# api/wallet_router.py
# Cüzdan İşlemleri Router'ı
# - verify_tp: Müşteri TP numarasını doğrular ve bilgilerini döndürür
# - create_wallet: Cobo API üzerinden yeni cüzdan oluşturur
# Bağımlılıklar: services/database.py, services/qr_service.py
```

---

### 📦 PARÇA 8: Cüzdan Oluşturma Endpoint'i
**Satır 125 — Satır 183**

**Ne Yapıyor:** `POST /api/create_wallet` → Cobo API üzerinden yeni cüzdan oluşturur, MongoDB'ye kaydeder, QR kod döndürür.

**Ne Yapılmalı:**
- `api/wallet_router.py` dosyasına taşınacak (PARÇA 7 ile aynı dosya).
- Cobo API konfigürasyonu (`configuration`, `certifi`) tekrarlanan bir kalıp. Bu kalıp `services/cobo_sweep.py`'deki `__init__` ile aynı. Ortak bir Cobo client factory düşünülebilir ama bu ilk aşamada gerekli değil.

**Hedef Dosya:** `api/wallet_router.py`

---

### 📦 PARÇA 9: Webhook İşleyici (EN BÜYÜK VE EN KRİTİK PARÇA) ⚠️
**Satır 185 — Satır 422**

**Ne Yapıyor:** `process_cobo_notification()` — Cobo'dan gelen webhook bildirimlerini arka planda işler. İçinde:
- Cüzdan oluşturma bildirimi (satır 196-230)
- İşlem filtreleme — tip kontrolü (satır 254-261)
- İşlem filtreleme — token kontrolü (satır 263-275)
- İşlem filtreleme — volume kontrolü (satır 277-282)
- İşlem filtreleme — iç transfer kontrolü (satır 284-291)
- Müşteri bulma ve doğrulama (satır 293-303)
- Para birimi çevirme (satır 311-328)
- Atomik kilit mekanizması (satır 330-335)
- Miktar formatlama (satır 337-340)
- Finansal istatistik güncelleme (satır 348-355)
- MT5 bilgi çekme (satır 357-370)
- Telegram bildirim gönderme (satır 372-389)
- MT5 bakiye ekleme (satır 391-414)

**Bu tek fonksiyon 237 satır! Tüm projenin kalbi burada.**

**Ne Yapılmalı:**
- Tüm `process_cobo_notification` fonksiyonu → `workers/webhook_processor.py` dosyasına taşınacak.
- Fonksiyonun içindeki alt işlemler helper fonksiyonlara bölünecek:

| Alt İşlem | Satır | Önerilen Helper Fonksiyon | Dosya |
|-----------|-------|--------------------------|-------|
| Cüzdan bildirimi işleme | 196-230 | `_handle_wallet_created()` | `workers/webhook_processor.py` |
| İşlem filtresi (Tip) | 254-261 | Sabitler `config/constants.py`'ye, kontrol yerinde kalır | `config/constants.py` |
| İşlem filtresi (Token) | 263-275 | Sabitler `config/constants.py`'ye, kontrol yerinde kalır | `config/constants.py` |
| İşlem filtresi (Volume) | 277-282 | Zaten `core/filter/base_volume_filter.py`'de ✅ | — |
| İşlem filtresi (İç Transfer) | 284-291 | Yerinde kalır, `get_all_our_addresses` zaten serviste | — |
| Para birimi çevirme | 311-328 | Zaten `core/currency/converter/converter.py`'de ✅ | — |
| MT5 bilgi çekme | 357-370 | `_fetch_mt5_metadata()` | `workers/webhook_processor.py` |
| Telegram mesaj oluşturma | 372-389 | `_build_deposit_telegram_message()` | `workers/webhook_processor.py` |
| MT5 bakiye ekleme | 391-414 | `_process_mt5_balance()` | `workers/webhook_processor.py` |

**Hedef Dosya:** `workers/webhook_processor.py`

**Yorum satırı önerisi:**
```python
# workers/webhook_processor.py
# =============================================================================
# COBO WEBHOOK İŞLEYİCİ (Background Task)
# =============================================================================
# Bu modül, Cobo platformundan gelen webhook bildirimlerini arka planda işler.
# main.py'deki /cobo/callback endpoint'i bu modüldeki process_cobo_notification()
# fonksiyonunu BackgroundTasks ile çağırır.
#
# İŞ AKIŞI:
# 1. Event tipi belirlenir (cüzdan/işlem)
# 2. İşlem filtreleri uygulanır (Tip, Token, Volume, İç Transfer)
# 3. Müşteri doğrulanır (MongoDB)
# 4. Kur çevirisi yapılır (converter.py)
# 5. Race condition koruması (try_lock_transaction)
# 6. Finansal istatistikler güncellenir
# 7. MT5'e bakiye eklenir
# 8. Telegram bildirimi gönderilir
#
# BAĞIMLILIKLAR:
# - services/database.py (MongoDB işlemleri)
# - services/telegram_service.py (Bildirimler)
# - config/settings.py (MT5 manager instance)
# - config/constants.py (ALLOWED_TOKENS, BLOCKED_TYPES)
# - core/filter/base_volume_filter.py (Hacim filtresi)
# - core/currency/converter/converter.py (Kur çevirisi)
# =============================================================================
```

---

### 📦 PARÇA 10: Cobo Callback Endpoint'i
**Satır 424 — Satır 446**

**Ne Yapıyor:** `POST /cobo/callback` → Webhook'u alır, 200 OK döner, işlemi arka plana atar.

**Ne Yapılmalı:**
- `api/webhook_router.py` dosyasına taşınacak.
- `process_cobo_notification` import'u `workers/webhook_processor.py`'den yapılacak.

**Hedef Dosya:** `api/webhook_router.py`

**Yorum satırı önerisi:**
```python
# api/webhook_router.py
# Cobo Webhook Endpoint'i
# Cobo platformundan gelen POST bildirimlerini karşılar.
# Hızlıca 200 OK döner ve asıl işlemi BackgroundTasks'a atar.
# Asıl işleme mantığı: workers/webhook_processor.py
```

---

### 📦 PARÇA 11: Manuel DB Fix Endpoint'i
**Satır 448 — Satır 459**

**Ne Yapıyor:** `GET /api/system/fix-db` → Veritabanı index onarımı.

**Ne Yapılmalı:**
- `api/system_router.py` dosyasına taşınacak.

**Hedef Dosya:** `api/system_router.py`

**Yorum satırı önerisi:**
```python
# api/system_router.py
# Sistem Bakım Endpoint'leri
# - fix-db: Veritabanı index onarımı ve duplicate kontrol
# DİKKAT: Bu endpoint production'da sadece yetkili kişiler tarafından kullanılmalıdır.
```

---

### 📦 PARÇA 12: Telegram Komut API Endpoint'i
**Satır 461 — Satır 538**

**Ne Yapıyor:** `POST /api/telegram_command` → /sweep ve /admin komutlarını işler. İçinde Cobo wallet raporu oluşturma mantığı var.

**Ne Yapılmalı:**
- `api/telegram_router.py` dosyasına taşınacak.
- İçindeki /sweep rapor oluşturma mantığı (satır 469-527) oldukça büyük. Bunu `services/cobo_sweep.py`'nin içine bir `generate_wallet_report()` metodu olarak ekleyebilirsin.

**Hedef Dosya:** `api/telegram_router.py`

**Yorum satırı önerisi:**
```python
# api/telegram_router.py
# Telegram Bot Komut API'si
# Telegram bot handler'larından gelen komutları işler.
# /sweep → Cobo wallet durum raporu oluşturur ve Telegram'a gönderir
# /admin → Admin panel linkini paylaşır
# Bağımlılıklar: services/cobo_sweep.py, services/telegram_service.py
```

---

### 📦 PARÇA 13: Telegram Bot (if __name__ bloğu)
**Satır 540 — Satır 628**

**Ne Yapıyor:** `if __name__ == "__main__"` bloğu içinde:
- Telegram bot handler'ları tanımlanıyor (sweep, admin, start komutları)
- Bot ayrı thread'de başlatılıyor
- Uvicorn ile FastAPI başlatılıyor

**Ne Yapılmalı:**
- `Satır 547-613`: Telegram bot handler'ları ve `run_telegram_bot()` fonksiyonu → `bot/telegram_bot.py` dosyasına taşınacak.
- `Satır 540-546, 614-628`: `if __name__` bloğu → main.py'de kalacak ama sadeleştirilecek.

**Hedef Dosya:** `bot/telegram_bot.py` + `main.py` (sadeleştirilmiş __main__ bloğu)

**Yorum satırı önerisi:**
```python
# bot/telegram_bot.py
# Telegram Bot Handler Modülü
# /start, /sweep, /admin komutlarını dinler ve localhost API'ye yönlendirir.
# main.py tarafından ayrı bir thread'de başlatılır.
# DİKKAT: Bu bot doğrudan iş mantığı ÇALIŞMAZ.
# Sadece HTTP POST ile /api/telegram_command endpoint'ine komut gönderir.
#
# Çalışma Şekli:
# Telegram → Bot Handler → HTTP POST localhost:8000 → API → Servis
```

---

### 📦 PARÇA 14: Yeni main.py (Hedef Son Hali)

Parçalama sonrası `main.py` şu şekilde görünecek (~80 satır):

```
main.py İçeriği (TASLAK):
─────────────────────────
1-10:   Import'lar (config, router'lar, bot)
11-15:  config/settings.py'den app sabitleri
16:     app = FastAPI()
17-25:  Startup event (sadece await çağrısı)
26-30:  Static file mounting (templates, static/logolar)
31-40:  Router'ları bağla:
          - app.include_router(home_router)
          - app.include_router(wallet_router)
          - app.include_router(webhook_router)
          - app.include_router(system_router)
          - app.include_router(telegram_router)
          - app.include_router(admin_router)
41-80:  if __name__ == "__main__":
          - Bot thread başlat (bot/telegram_bot.py)
          - Uvicorn başlat
```

---

## 4. mt5_worker.py İyileştirme Planı

`mt5_worker.py` zaten 80 satır ve oldukça temiz. PM2 ile çalıştığı için büyük değişikliğe gerek yok.

### Küçük İyileştirmeler:

| # | İyileştirme | Detay |
|---|------------|-------|
| 1 | Config import'u | `Satır 1-16`: `.env` okuma kısmı → `from config.settings import MT5_SERVER, MT5_LOGIN, MT5_PASSWORD` olacak |
| 2 | Servis import'u | `Satır 5-6`: → `from services.mt5_manager import MT5UserManager` ve `from services.database import save_lead, get_lead_by_tp` olacak |
| 3 | Yorum satırları | Fonksiyonun başına daha açıklayıcı docstring eklenecek |

**DİKKAT:** Bu dosya PM2 ile çalışıyor. Import yolları değişince `ecosystem.config.js`'de bir değişiklik gerekmez (çünkü dosya adı aynı kalacak). Ama dosya içindeki import'lar güncellenmelidir.

---

## 5. Servisler Klasörü Yeniden Yapılandırma

### Mevcut `servisler/` → Hedef `services/`

| Eski Dosya | Yeni Dosya | Değişiklik |
|-----------|-----------|-----------|
| `servisler/__init__.py` | `services/__init__.py` | Yeniden adlandırma |
| `servisler/db_service.py` | `services/database.py` | Yeniden adlandırma |
| `servisler/mt5service.py` | `services/mt5_manager.py` | Yeniden adlandırma |
| `servisler/sweep_service.py` | `services/cobo_sweep.py` | Yeniden adlandırma |
| `servisler/withdrawal_service.py` | `services/cobo_withdrawal.py` | Yeniden adlandırma |
| `servisler/crmservice.py` | `archive/crmservice.py` | Arşive (Kullanılmıyor) |
| `servisler/crm_sync_service.py` | `archive/crm_sync_service.py` | Arşive (Kullanılmıyor) |
| *(YENİ)* | `services/telegram_service.py` | main.py satır 80-94'ten çıkarılacak |
| *(YENİ)* | `services/qr_service.py` | main.py satır 71-78'den çıkarılacak |

### Servis dosyalarındaki iç import'lar:

`services/database.py` (eski `db_service.py`) içinde `Satır 8-10`:
```python
# ESKİ:
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
```
→ Bu kısım silinecek, yerine:
```python
# YENİ:
from config.settings import MONGODB_URL
```

**ÖNEMLİ NOT:** `db_service.py` satır 12'deki MongoDB URL'si hardcoded! Bu MUTLAKA `.env`'ye taşınmalı:
```
# Mevcut (GÜVENSİZ):
MONGODB_URL = "mongodb+srv://wimcrm:edWfyiwTjpnkgAzx@data.drjzdcy.mongodb.net/..."
# ↑ Şifre açık! .env'ye taşınmalı.
```

---

## 6. Admin API Entegrasyonu

### Mevcut Durum:
`admin_api.py` dosyasında bir `router = APIRouter()` tanımlı ve endpoint'ler bu router'a bağlı. **AMA `main.py`'de `app.include_router(router)` çağrısı YOK!** Yani bu endpoint'ler şu anda çalışmıyor.

### Yapılacaklar:

| # | Adım |
|---|------|
| 1 | `admin_api.py` → `api/admin_router.py` olarak taşınacak |
| 2 | İçindeki `send_telegram_msg` kopyası silinecek, `services/telegram_service.py` import edilecek |
| 3 | `main.py`'de `app.include_router(admin_router.router, prefix="/admin")` eklenecek |
| 4 | `Satır 17-18`'deki şifre (`ADMIN_USERNAME`, `ADMIN_PASSWORD`) → `.env`'ye taşınacak |

---

## 7. Konfigürasyon ve Ortam Değişkenleri

### 🆕 `config/settings.py` İçeriği (Taslak Açıklama):

Bu dosya şunları içerecek:
- `.env` yükleme (tek merkezden)
- Logging konfigürasyonu
- MT5 bağlantı bilgileri ve `mt5_manager` singleton instance
- MongoDB URL (`.env`'den)
- Cobo API ayarları
- Telegram bot token ve chat ID
- PORT ayarı

### 🆕 `config/constants.py` İçeriği (Taslak Açıklama):

Bu dosya şunları içerecek:
- `ALLOWED_TOKENS` listesi (main.py satır 264'ten)
- `BLOCKED_TYPES` listesi (main.py satır 256-257'den)
- Chain display name mapping (main.py satır 216-219'dan)
- Diğer iş sabitları

**Yorum satırı önerisi:**
```python
# config/constants.py
# =============================================================================
# İŞ KURALLARI SABİTLERİ
# =============================================================================
# Bu dosya, sistemin karar verme mekanizmasında kullandığı tüm sabit listeleri
# ve eşlemeleri içerir. Değişiklik yaparken DİKKATLİ olun, çünkü bu sabitler
# doğrudan para akışını etkiler.
#
# ALLOWED_TOKENS: Kabul edilen kripto paralar (Diğerleri spam/fake sayılır)
# BLOCKED_TYPES: Engellenen işlem tipleri (Sadece DEPOSIT/RECEIVE geçer)
# CHAIN_DISPLAY_NAMES: Ağ isimlerinin kullanıcı dostu karşılıkları
# =============================================================================
```

---

## 8. ecosystem.config.js Güncelleme

PM2 konfigürasyonunda dosya adları değişmediği için (`main.py` ve `mt5_worker.py`) büyük bir değişiklik gerekmez.

**Ama şunu kontrol et:**
- `script: "main.py"` → Dosya adı aynı kaldığı için sorun yok.
- `script: "mt5_worker.py"` → Dosya adı aynı kaldığı için sorun yok.
- `cwd` ayarı yoksa, PM2'nin çalışma dizininin doğru olduğundan emin ol.

---

## 9. İşlem Sırası (Yapılması Gereken Adımlar)

### ⚠️ ÖNEMLİ: Her adımdan sonra `pm2 restart all` ile test et!

---

### **ADIM 1: Yedek Al** 🔒
> Herhangi bir değişiklik yapmadan önce tüm projeyi yedekle.
```
Tüm proje klasörünü kopyala veya git commit yap:
git add -A && git commit -m "BACKUP: Refactoring öncesi son durum"
```

---

### **ADIM 2: Klasör Yapısını Oluştur** 📁
> Yeni klasörleri boş olarak oluştur.

Oluşturulacak klasörler:
1. `config/` (içine `__init__.py`)
2. `api/` (içine `__init__.py`)
3. `services/` (içine `__init__.py`)
4. `workers/` (içine `__init__.py`)
5. `bot/` (içine `__init__.py`)
6. `templates/`
7. `static/`
8. `tests/`
9. `tools/`
10. `archive/`
11. `docs/`

---

### **ADIM 3: Konfigürasyonu Ayır** ⚙️
> En az riskli adım, hiçbir işlevsellik değişmez.

1. `config/settings.py` oluştur:
   - main.py satır 27-35 (.env yükleme, logging) buraya taşı
   - main.py satır 59-64 (MT5 config) buraya taşı
   - `db_service.py` satır 12'deki MongoDB URL'yi `.env`'ye taşı, buradan oku
2. `config/constants.py` oluştur:
   - main.py satır 256-257 (BLOCKED_TYPES) buraya taşı
   - main.py satır 264 (ALLOWED_TOKENS) buraya taşı
3. main.py'de bu import'ları güncelle

**TEST:** `pm2 restart all` → Sistem çalışıyor mu?

---

### **ADIM 4: Küçük Servisleri Ayır** 🔧
> Bağımsız, basit fonksiyonlar.

1. `services/telegram_service.py` oluştur:
   - main.py satır 80-94 (`send_telegram_msg`) buraya taşı
2. `services/qr_service.py` oluştur:
   - main.py satır 71-78 (`generate_qr_base64`) buraya taşı
3. main.py'de bu fonksiyonları import ile kullan

**TEST:** `pm2 restart all` → Sistem çalışıyor mu?

---

### **ADIM 5: Servisler Klasörünü Yeniden Adlandır** 🔄
> Import yolları değişecek, dikkatli ol.

1. `servisler/` klasörünü `services/` olarak yeniden adlandır
2. İçindeki dosyaları yeniden adlandır:
   - `db_service.py` → `database.py`
   - `mt5service.py` → `mt5_manager.py`
   - `sweep_service.py` → `cobo_sweep.py`
   - `withdrawal_service.py` → `cobo_withdrawal.py`
3. **TÜM dosyalardaki import yollarını güncelle:**
   - main.py'deki `from servisler.xxx import ...`
   - mt5_worker.py'deki import'lar
   - admin_api.py'deki import'lar
   - cobo_manager.py'deki import'lar
   - crm_worker.py'deki import'lar (arşive atılacak ama şimdilik)
4. CRM servisleri → `archive/` klasörüne taşı

**TEST:** `pm2 restart all` → Sistem çalışıyor mu?

---

### **ADIM 6: Webhook İşleyiciyi Ayır** ⚡ (EN KRİTİK ADIM)
> Main.py'nin kalbi. Çok dikkatli ol.

1. `workers/webhook_processor.py` oluştur
2. main.py satır 185-422 (`process_cobo_notification` fonksiyonu) buraya taşı
3. Gerekli import'ları ekle (database, telegram_service, settings, constants, vb.)
4. main.py'de sadece `from workers.webhook_processor import process_cobo_notification` kalacak
5. İsteğe bağlı: Fonksiyon içindeki alt işlemleri helper metodlara bölün (yukardaki tabloya bak)

**TEST:** `pm2 restart all` → Webhook test et (Cobo test webhook veya test_race.py)

---

### **ADIM 7: API Endpoint'lerini Router'lara Ayır** 🌐

1. `api/home_router.py` oluştur:
   - main.py satır 96-99 buraya taşı
2. `api/wallet_router.py` oluştur:
   - main.py satır 103-183 buraya taşı (verify_tp + create_wallet)
3. `api/webhook_router.py` oluştur:
   - main.py satır 424-446 buraya taşı
4. `api/system_router.py` oluştur:
   - main.py satır 448-459 buraya taşı
5. `api/telegram_router.py` oluştur:
   - main.py satır 461-538 buraya taşı
6. `api/admin_router.py`:
   - Mevcut `admin_api.py`'yi buraya taşı
7. main.py'de tüm router'ları `app.include_router()` ile bağla

**TEST:** `pm2 restart all` → Tüm endpoint'leri test et

---

### **ADIM 8: Telegram Bot'u Ayır** 🤖

1. `bot/telegram_bot.py` oluştur:
   - main.py satır 547-613 buraya taşı
   - `run_telegram_bot()` fonksiyonunu dışa aç
2. main.py'nin `if __name__` bloğunu sadeleştir:
   - `from bot.telegram_bot import run_telegram_bot` import et
   - Thread başlatma ve uvicorn kodu kalacak

**TEST:** `pm2 restart all` → Telegram bot komutlarını test et (/sweep, /start, /admin)

---

### **ADIM 9: Statik Dosyaları Taşı** 📄

1. `index.html` → `templates/index.html`
2. `admin.html` → `templates/admin.html`
3. `logolar/` → `static/logolar/`
4. Router'lardaki dosya yollarını güncelle
5. main.py'deki `app.mount` yolunu güncelle

**TEST:** `pm2 restart all` → Web arayüzü çalışıyor mu?

---

### **ADIM 10: Test ve Yardımcı Dosyaları Taşı** 🧹

1. `test_*.py` dosyaları → `tests/`
2. `setup_test_user.py` → `tests/`
3. `cobo_manager.py` → `tools/`
4. `get_chat_id.py` → `tools/`
5. `trigger_sweep.py` → `tools/`
6. `supervisor.py` → `archive/` (PM2 varken artık gereksiz)
7. `telegram_bot.py` (kök dizindeki) → `archive/` (main.py içindeki yeterli)
8. `crm_worker.py` → `archive/`

**TEST:** `pm2 restart all` → Final kontrol

---

### **ADIM 11: Temizlik ve Final** ✅

1. Tüm `__pycache__` klasörlerini sil
2. `.gitignore`'a yeni klasörleri kontrol et
3. Eski `servisler/` klasörünü sil (yedek aldıysan)
4. Son bir kez tüm endpoint'leri ve webhook'u test et
5. Git commit:
```
git add -A && git commit -m "REFACTOR: Kurumsal mimari yapısına geçiş tamamlandı"
```

---

## 10. Dikkat Edilecekler ve Riskler

### 🔴 Yüksek Risk:

| Risk | Açıklama | Çözüm |
|------|---------|-------|
| **Import Döngüsü** | Yeni dosyalar birbirini import ederse circular import hatası alırsın | `config/settings.py`'yi sadece basit tipler için kullan, karmaşık nesneleri lazy import yap |
| **Webhook Kopması** | `process_cobo_notification` taşınırken hata olursa gerçek para akışı durur | ÖNCE test ortamında dene, production'da webhook'u kapatmadan geçiş yap |
| **PM2 Path Sorunu** | `pm2` çalışma dizinini yanlış ayarlarsa import'lar bozulur | `ecosystem.config.js`'de `cwd` parametresi ekle |

### 🟡 Orta Risk:

| Risk | Açıklama | Çözüm |
|------|---------|-------|
| **MongoDB URL Açığa Çıkması** | `db_service.py`'de hardcoded URL var | İlk iş `.env`'ye taşı |
| **Admin Şifresi** | `admin_api.py` satır 17-18'de açık yazılmış | İlk iş `.env`'ye taşı |
| **Thread Güvenliği** | Telegram bot ayrı thread'de çalışıyor, yeni yapıda import'lar thread-safe olmalı | Global nesneleri `config/settings.py`'de tek seferde oluştur |

### 🟢 Düşük Risk:

| Risk | Açıklama |
|------|---------|
| **Dosya Yolu Değişiklikleri** | `templates/index.html` gibi yeni yollar HTML içindeki relative path'leri etkileyebilir |
| **Test Dosyaları** | Taşındıktan sonra import yolları güncellenmelidir |

---

## 📊 Özet Tablo: Her Adımın Tahmini Süresi

| Adım | Açıklama | Tahmini Süre | Zorluk |
|------|---------|-------------|--------|
| 1 | Yedek Al | 5 dk | ⭐ |
| 2 | Klasör Yapısını Oluştur | 10 dk | ⭐ |
| 3 | Konfigürasyonu Ayır | 30 dk | ⭐⭐ |
| 4 | Küçük Servisleri Ayır | 20 dk | ⭐⭐ |
| 5 | Servisler Yeniden Adlandır | 45 dk | ⭐⭐⭐ |
| 6 | Webhook İşleyici Ayır | 60 dk | ⭐⭐⭐⭐⭐ |
| 7 | Router'ları Ayır | 45 dk | ⭐⭐⭐ |
| 8 | Telegram Bot Ayır | 20 dk | ⭐⭐ |
| 9 | Statik Dosyaları Taşı | 15 dk | ⭐⭐ |
| 10 | Test/Yardımcı Taşı | 10 dk | ⭐ |
| 11 | Final Temizlik | 15 dk | ⭐ |
| **TOPLAM** | | **~4.5 saat** | |

---

> **💡 İpucu:** Her adımdan sonra `pm2 restart all && pm2 logs` komutuyla hata olup olmadığını kontrol et. Hata varsa bir önceki adıma dön ve düzelt. Asla 2 adımı aynı anda yapma!

---

> **🫶 Bu rehber senin için hazırlandı canım. Adım adım ilerle, acele etme. Her adımda test et. Sorularını sor, beraber hallederiz.**
