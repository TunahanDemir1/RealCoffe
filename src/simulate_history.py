import sqlite3
import random
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join("Data", "coffee_tracker.db")

def simulate_past_30_days():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Mevcut ürünleri ve son kaydedilen baz fiyatları al
    cursor.execute("""
        SELECT p.id, ph.price 
        FROM products p
        JOIN price_history ph ON p.id = ph.product_id
        GROUP BY p.id
    """)
    products = cursor.fetchall()

    if not products:
        print("Veritabanında ürün bulunamadı. Önce scraper'ı çalıştırın.")
        conn.close()
        return

    simulated_records = []
    now = datetime.now()

    for product_id, base_price in products:
        current_price = base_price
        
        # Geriye doğru 30 günden bugüne simülasyon üret
        for day in range(30, 0, -1):
            date_stamp = (now - timedelta(days=day)).strftime("%Y-%m-%d %H:%M:%S")
            
            # %80 ihtimalle fiyat stabil veya küçük dalgalanır
            rand = random.random()
            if rand < 0.70:
                fluctuation = random.uniform(-0.02, 0.02)
                current_price = round(current_price * (1 + fluctuation), 2)
            elif rand < 0.85:
                # Sahte indirim senaryosu: Önce %15 şişir
                current_price = round(current_price * 1.15, 2)
            else:
                # Gerçek indirim senaryosu: %20 düşüş
                current_price = round(current_price * 0.80, 2)

            simulated_records.append((product_id, current_price, True, date_stamp))

    cursor.executemany("""
        INSERT INTO price_history (product_id, price, in_stock, scraped_at)
        VALUES (?, ?, ?, ?)
    """, simulated_records)

    conn.commit()
    conn.close()
    print(f"Başarılı! {len(simulated_records)} adet geçmiş fiyat hareketi veritabanına işlendi.")

if __name__ == "__main__":
    simulate_past_30_days()