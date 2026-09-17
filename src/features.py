import sqlite3
import pandas as pd
import numpy as np
import os

DB_PATH = os.path.join("Data", "coffee_tracker.db")

def build_feature_dataset() -> pd.DataFrame:
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
    ORDER BY p.id, ph.scraped_at ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    df["scraped_at"] = pd.to_datetime(df["scraped_at"])

    # 1. 100g Başına Standart Fiyat
    df["price_per_100g"] = (df["price"] / df["weight_g"]) * 100

    # 2. Zaman Serisi Öznitelikleri (Grup: Ürün Bazında)
    grouped = df.groupby("product_id")["price"]

    # 7 ve 14 Günlük Hareketli Ortalama (Rolling Mean)
    df["rolling_mean_7d"] = grouped.transform(lambda x: x.rolling(7, min_periods=1).mean())
    df["rolling_mean_14d"] = grouped.transform(lambda x: x.rolling(14, min_periods=1).mean())

    # Fiyat Volatilitesi (7 Günlük Standart Sapma)
    df["rolling_std_7d"] = grouped.transform(lambda x: x.rolling(7, min_periods=1).std()).fillna(0)

    # Önceki güne göre fiyat değişim miktarı ve yüzdesi
    df["price_diff_1d"] = grouped.diff().fillna(0)
    df["pct_change_1d"] = (grouped.pct_change() * 100).fillna(0)

    # 3. İstatistiksel İndirim & Anomali Skorları
    # Z-Score: Fiyatın son 7 güne göre kaç standart sapma saptığı (Negatif ve büyükse dip fiyattır)
    df["z_score"] = np.where(
        df["rolling_std_7d"] > 0,
        (df["price"] - df["rolling_mean_7d"]) / df["rolling_std_7d"],
        0.0
    )

    # Gerçek İndirim Derinliği (0 ile 1 arası oran)
    df["discount_ratio"] = (df["rolling_mean_14d"] - df["price"]) / df["rolling_mean_14d"]
    df["discount_ratio"] = df["discount_ratio"].apply(lambda x: max(0.0, x))

    # 4. Sahte İndirim Tespiti Kuralı (Fake Discount Indicator)
    # Fiyat son 3 günde önce %10'dan fazla artıp hemen ardından düşmüş mü?
    df["max_price_last_7d"] = grouped.transform(lambda x: x.rolling(7, min_periods=1).max())
    df["is_fake_discount"] = (
        (df["max_price_last_7d"] > df["rolling_mean_14d"] * 1.08) & 
        (df["price"] < df["max_price_last_7d"]) &
        (df["price"] >= df["rolling_mean_14d"] * 0.95)
    ).astype(int)

    return df

if __name__ == "__main__":
    print("Öznitelik mühendisliği pipeline'ı çalıştırılıyor...")
    feature_df = build_feature_dataset()
    print(f"Toplam Satır: {len(feature_df)}, Toplam Kolon: {feature_df.shape[1]}")
    
    print("\nÜretilen Örnek Feature Matrisi (Son 5 Kayıt):")
    cols_to_show = ["title", "price", "rolling_mean_7d", "z_score", "discount_ratio", "is_fake_discount"]
    print(feature_df[cols_to_show].tail())