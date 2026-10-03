import sys
import os
import html
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from database import init_db, save_scraped_data
from scraper import KahhveComScraper
from model import train_and_detect_deals
from notifier import send_telegram_alert

def run_pipeline():
    print("=" * 60)
    print("0. [DATABASE] Veritabanı tabloları ve indeksleri hazırlanıyor...")
    init_db()

    print("\n1. [SCRAPING] Canlı kahve fiyatları toplanıyor...")
    scraper = KahhveComScraper()
    products = scraper.scrape(max_pages=3)
    
    if products:
        print(f"-> {len(products)} adet ürün ayrıştırıldı. Veritabanına kaydediliyor...")
        save_scraped_data(products)
    else:
        print("-> Ürün bulunamadı veya sayfaya erişilemedi.")

    print("\n2. [ML MODEL] Özellikler çıkarılıyor ve indirimler analiz ediliyor...")
    deals_df = train_and_detect_deals()

    if deals_df.empty:
        print("-> Model çalıştırılamadı: Veri yetersiz.")
        return

    print("\n3. [SONUÇLAR VE BİLDİRİM] Fırsatlar filtreleniyor...")
    # Yeni izlenmeye başlanan ürünleri bildirim kirliliği yapmaması için hariç tut
    alerts = deals_df[
        (deals_df["recommendation"] != "Yeni Ürün (İzleniyor)") &
        ((deals_df["deal_score"] >= 40) | (deals_df["recommendation"] == "Sahte İndirim Şüphesi"))
    ].sort_values(by="deal_score", ascending=False)

    if not alerts.empty:
        msg_lines = ["<b>☕ Günün Kahve Fiyat Zekası Raporu</b>\n"]
        for _, row in alerts.head(5).iterrows():
            badge = "🚨" if row["recommendation"] == "Sahte İndirim Şüphesi" else "🔥"
            clean_title = html.escape(str(row['title']))
            clean_roaster = html.escape(str(row.get('roaster', 'Bilinmiyor')))
            product_url = row.get("url", "https://kahhve.com")
            weight = row.get("weight_g", 250)
            price_100g = row.get("price_per_100g", 0.0)

            msg_lines.append(
                f"{badge} <b>{clean_title}</b> ({clean_roaster})\n"
                f"• <b>Fiyat:</b> {row['price']:.2f} TL (7G Ort: {row['rolling_mean_7d']:.2f} TL)\n"
                f"• <b>Birim Fiyat:</b> {price_100g:.2f} TL/100g (Paket: {weight}g)\n"
                f"• <b>Skor:</b> {row['deal_score']}/100 | <b>Durum:</b> {row['recommendation']}\n"
                f"• 🔗 <a href=\"{product_url}\">Ürünü İncele / Satın Al</a>\n"
            )
        full_msg = "\n".join(msg_lines)
        print("\n--- Telegram'a Gönderilecek Mesaj ---")
        try:
            print(full_msg)
        except Exception:
            print("Mesaj konsola yazdırılamadı (encoding kısıtı).")
        send_telegram_alert(full_msg, parse_mode="HTML")
    else:
        print("Bugün eşiği aşan bir fırsat bulunamadı.")
        send_telegram_alert("<b>☕ Kahve Takipçisi:</b> Bugün kayda değer bir indirim dalgalanması tespit edilmedi.", parse_mode="HTML")

    print("=" * 60)

if __name__ == "__main__":
    run_pipeline()