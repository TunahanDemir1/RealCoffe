@"
# ☕ Coffee Price Intelligence & Deal Anomaly Detection

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-orange.svg)](https://scikit-learn.org/)
[![Actions](https://img.shields.io/badge/Automation-GitHub_Actions-2088FF.svg)](https://github.com/features/actions)

Türkiye'deki 3. nesil kahve kavurucuları ve e-ticaret platformlarındaki fiyat hareketlerini periyodik olarak izleyen, zaman serisi analizi ve makine öğrenimi (*Isolation Forest*) algoritmalarıyla **"Sahte İndirimleri" (Fake Discounts)** tespit edip **gerçek dip fiyat fırsatlarını** Telegram üzerinden bildiren uçtan uca veri bilimi projesidir.

---

## 🏛️ Mimari ve Katman Tasarımı (Layered Architecture)

```text
[ kahhve.com / E-Commerce ]
           │  (Pagination & data-enhanced JSON Parsing)
           ▼
┌────────────────────────────────────────────────────────┐
│ Katman 1: Veri Toplama & Depolama                      │
│ • Requests, BeautifulSoup4                             │
│ • SQLite (products, price_history tabloları)           │
└──────────────────────────┬─────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────┐
│ Katman 2: Öznitelik Mühendisliği (Feature Engineering) │
│ • 100g Başına Birim Fiyat                             │
│ • 7 & 14 Günlük Hareketli Ortalama (Rolling Mean)      │
│ • Fiyat Volatilitesi (Rolling Std) & Z-Score           │
│ • Sahte İndirim Filtresi (Suni Şişirme Kuralı)         │
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
│ • Telegram Bot API (Anlık Fırsat Bildirimleri)         │
│ • GitHub Actions (Her sabah 09:00 Cron Job)            │
└────────────────────────────────────────────────────────┘
