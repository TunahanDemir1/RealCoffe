import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join("Data", "coffee_tracker.db")

def load_data_from_db() -> pd.DataFrame:
    """Veritabanındaki ürünleri ve fiyat geçmişini birleştirerek DataFrame döner."""
    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT 
        p.id AS product_id,
        p.title,
        p.roaster,
        p.weight_g,
        ph.price,
        ph.in_stock,
        ph.scraped_at
    FROM products p
    JOIN price_history ph ON p.id = ph.product_id
    ORDER BY ph.scraped_at ASC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    df["scraped_at"] = pd.to_datetime(df["scraped_at"])
    return df

def generate_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Veri bilimi ve fiyat takip modelleri için temel öznitelikleri üretir.
    """
    # 1. 100g başına birim fiyat (Farklı gramajları adil karşılaştırmak için)
    df["price_per_100g"] = (df["price"] / df["weight_g"]) * 100
    
    # 2. Ürün bazında zaman serisi metrikleri (İleride çoklu scrape yapıldıkça dolacak)
    df = df.sort_values(by=["product_id", "scraped_at"])
    
    # Önceki fiyata göre değişim miktarı ve yüzdesi
    df["price_diff"] = df.groupby("product_id")["price"].diff()
    df["price_pct_change"] = df.groupby("product_id")["price"].pct_change() * 100
    
    # 7 günlük / 30 günlük hareketli ortalama (Rolling Mean)
    df["rolling_avg_price"] = df.groupby("product_id")["price"].transform(
        lambda x: x.rolling(window=3, min_periods=1).mean()
    )
    
    # Gerçek İndirim Skoru: Anlık fiyat, hareketli ortalamanın ne kadar altında?
    df["discount_depth"] = (df["rolling_avg_price"] - df["price"]) / df["rolling_avg_price"]
    
    return df

def display_summary():
    df = load_data_from_db()
    if df.empty:
        print("Veritabanında kayıtlı veri bulunamadı.")
        return
        
    df = generate_features(df)
    
    print("=" * 60)
    print(f"Toplam Çekilen Kayıt Sayısı: {len(df)}")
    print(f"Benzersiz Kahve Sayısı: {df['product_id'].nunique()}")
    print("=" * 60)
    
    print("\nMarka (Roaster) Bazında Fiyat Özeti (TL):")
    roaster_stats = df.groupby("roaster")["price"].agg(["count", "mean", "min", "max"]).round(2)
    roaster_stats.columns = ["Ürün Sayısı", "Ortalama Fiyat", "En Ucuz", "En Pahalı"]
    print(roaster_stats)
    
    print("\nEn Pahalı 3 Kahve:")
    print(df.nlargest(3, "price")[["title", "roaster", "price"]])
    
    print("\nEn Uygun Fiyatlı 3 Kahve:")
    print(df.nsmallest(3, "price")[["title", "roaster", "price"]])
    print("=" * 60)

if __name__ == "__main__":
    display_summary()