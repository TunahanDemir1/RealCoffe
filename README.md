# ☕ Coffee Price Intelligence & Deal Anomaly Detection

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-orange.svg)](https://scikit-learn.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Actions](https://img.shields.io/badge/Automation-GitHub_Actions-2088FF.svg)](https://github.com/features/actions)

Türkiye'deki 3. nesil kahve kavurucuları ve e-ticaret platformlarındaki fiyat hareketlerini periyodik olarak izleyen, zaman serisi analizi ve makine öğrenimi (*Isolation Forest*) algoritmalarıyla **"Sahte İndirimleri" (Fake Discounts)** tespit edip **gerçek dip fiyat fırsatlarını** Telegram ve interaktif Web Dashboard üzerinden sunan uçtan uca veri bilimi projesidir.

---

## 🏛️ Mimari ve Katman Tasarımı (Layered Architecture)

```text
[ kahhve.com / E-Commerce ]
           │  (Pagination & JSON Payload Parsing + Akıllı Gramaj Tespiti)
           ▼
┌────────────────────────────────────────────────────────┐
│ Katman 1: Veri Toplama & Depolama                      │
│ • Requests, BeautifulSoup4 (Akıllı gramaj ayrıştırma) │
│ • SQLite (products, price_history tabloları & indexler)│
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ Katman 2: Öznitelik Mühendisliği (Feature Engineering) │
│ • 100g Başına Birim Fiyat                             │
│ • 7 & 14 Günlük Hareketli Ortalama (Rolling Mean)      │
│ • Fiyat Volatilitesi (Rolling Std) & Z-Score           │
│ • Sahte İndirim Filtresi (Suni Şişirme Kuralı)         │
│ • Cold-Start / Geçmiş Veri Eşik Kontrolü              │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ Katman 3: Makine Öğrenimi & Anomali Tespiti            │
│ • Isolation Forest (Uç fiyat hareketleri tespiti)      │
│ • Fırsat Skoru (Deal Score: 0 - 100) Hesaplama        │
│ • Fiyat Sınıflandırması (Dip Fiyat / Sahte İndirim)    │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ Katman 4: Orkestrasyon & Otomasyon                     │
│ • Telegram Bot API (HTML formatında doğrudan linkli)   │
│ • GitHub Actions (Her sabah 09:00 Cron Job)            │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ Katman 5: Dağıtım & İnteraktif Dashboard               │
│ • Streamlit Web Arayüzü (Filtreler & Canlı Tetikleme)  │
│ • Plotly İnteraktif Zaman Serisi & Fiyat Grafikleri    │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 Hızlı Başlangıç

### 1. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 2. Ortam Değişkenlerini Tanımlayın (`.env`)
```env
TELEGRAM_BOT_TOKEN="BOT_TOKENINIZ"
TELEGRAM_CHAT_ID="CHAT_IDNIZ"
```

### 3. Pipeline'ı Çalıştırın (Scrape + ML + Telegram)
```bash
python main.py
```

### 4. İnteraktif Web Dashboard'u Başlatın
```bash
streamlit run dashboard.py
```

---

## 🎯 Gelişmiş Özellikler

1. **Akıllı Gramaj Tespiti (Regex):** 250g, 500g, 1000g, 1 kg ve 2x250g gibi farklı paket gramajlarını otomatik yakalayarak **100g birim fiyatını** adil şekilde hesaplar.
2. **Sahte İndirim Kalkanı:** Fiyat önce yapay olarak şişirilip ardından indirim yapılmış gibi gösterildiğinde bunu tespit eder ve fırsat puanını kırpar.
3. **Cold-Start Koruması:** Henüz yeterli fiyat geçmişi bulunmayan yeni ürünlerin yanlış alarm üretmesini engeller.
4. **Tıklanabilir Telegram Bildirimleri:** Bulunan fırsatların satın alma sayfasına doğrudan tek tıkla erişim linki sağlar.
