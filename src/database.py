import sqlite3
import os

DB_PATH = os.path.join("Data", "coffee_tracker.db") #Veritabanı dosyasının yolunu platformlar arası uyumlu oalcka şekilde tasarlar.

def init_db():
    os.makedirs("Data", exist_ok=True)  #Data adında bir klasör oluşturur, eğer var ise oluşturmaz.
    conn = sqlite3.connect(DB_PATH)  #Belirtilen yoldaki veritabanı dosyasına bağlanır
    cursor = conn.cursor()  #Veritabanı üzerinde SQL sorguları çalıştırmak ve sonuçları yönetmek için bir imleç     nesnesi yaratır.
    
    # 1. Ürünler tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  
        platform TEXT NOT NULL,
        title TEXT NOT NULL,
        roaster TEXT,
        weight_g INTEGER,
        url TEXT UNIQUE NOT NULL
    )
    """)
    
    # 2. Fiyat geçmişi tablosu (Zaman serisi)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS price_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        price REAL NOT NULL,
        in_stock BOOLEAN NOT NULL,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)
    
    conn.commit()  #Diske kalıcı olarak yazar.
    conn.close()   #Açık olan veri tabanı bağlantısını güvenlice kapatır.
    print("Veritabanı ve tablolar hazır!")

if __name__ == "__main__":  #Fonksiyon tetikleyici.
    init_db()


def save_scraped_data(products_list: list[dict]):
    """
    Scraper'dan gelen ürün listesini veritabanına yazar/günceller.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for item in products_list:
        # 1. Ürün tabloda var mı kontrol et (URL tekildir)
        cursor.execute("SELECT id FROM products WHERE url = ?", (item["url"],))
        product = cursor.fetchone()
        
        if product:
            product_id = product[0]
        else:
            # Yeni ürünse ekle
            cursor.execute("""
                INSERT INTO products (platform, title, roaster, weight_g, url)
                VALUES (?, ?, ?, ?, ?)
            """, (item["platform"], item["title"], item.get("roaster"), item.get("weight_g"), item["url"]))
            product_id = cursor.lastrowid
        
        # 2. Fiyat geçmişine yeni kaydı ekle
        cursor.execute("""
            INSERT INTO price_history (product_id, price, in_stock)
            VALUES (?, ?, ?)
        """, (product_id, item["price"], item["in_stock"]))
        
    conn.commit()
    conn.close()
    print(f"{len(products_list)} adet ürünün fiyat verisi kaydedildi.")