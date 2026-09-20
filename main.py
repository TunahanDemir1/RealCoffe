import sys
import os
from dotenv import load_dotenv

# .env varsa yerel ortamda yükle
load_dotenv()

# src klasörünü modül yolu olarak tanıt
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from scraper import KahhveComScraper
from database import save_scraped_data
from model import train_and_detect_deals
from notifier import send_telegram_alert

def run_pipeline():
    print("=" * 60)
    print("1. [SCRAPING] Canlı kahve fiyatları toplanıyor...")
    scraper = KahhveComScraper()
    products = scraper.scrape(max_pages=3)
    
    if products:
        print(f"-> {len(products)} adet ürün ayrıştırıldı. Veritabanına kaydediliyor...")
        save_scraped_data(products)
    else:
        print("-> Ürün bulunamadı veya sayfaya erişilemedi.")

    print("\n2. [ML MODEL] Özellikler çıkarılıyor ve indirimler analiz ediliyor...")
    deals_df = train_and_detect_deals()

    print("\n3. [SONUÇLAR VE BİLDİRİM] Fırsatlar filtreleniyor...")
    # Deal score 40 üstü veya sahte indirim olanları ayıkla
    alerts = deals_df[
        (deals_df["deal_score"] >= 40) | 
        (deals_df["recommendation"] == "Sahte İndirim Şüphesi")
    ]

    if not alerts.empty:
        msg_lines = ["☕ *Günün Kahve Fiyat Zekası Raporu*\n"]
        for _, row in alerts.head(5).iterrows():
            badge = "🚨" if row["recommendation"] == "Sahte İndirim Şüphesi" else "🔥"
            msg_lines.append(
                f"{badge} *{row['title'][:35]}* ({row['roaster']})\n"
                f"• Fiyat: {row['price']:.2f} TL (Ort: {row['rolling_mean_7d']:.2f} TL)\n"
                f"• Skor: {row['deal_score']}/100 | Durum: {row['recommendation']}\n"
            )
        full_msg = "\n".join(msg_lines)
        print(full_msg)
        send_telegram_alert(full_msg)
    else:
        print("Bugün eşiği aşan bir fırsat bulunamadı.")
        # Opsiyonel: Her şeyin çalıştığını teyit etmek için hafif bir nabız mesajı
        send_telegram_alert("☕ *Kahve Takipçisi*: Bugün kayda değer bir indirim dalgalanması tespit edilmedi.")

    print("=" * 60)

if __name__ == "__main__":
    run_pipeline()