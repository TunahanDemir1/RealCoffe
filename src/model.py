import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from features import build_feature_dataset

def train_and_detect_deals() -> pd.DataFrame:
    # 1. Feature mühendisliğinden geçmiş veriyi çek
    df = build_feature_dataset()

    # Sadece her ürünün en son (güncel) kaydına odaklanalım
    latest_df = df.sort_values("scraped_at").groupby("product_id").last().reset_index()

    # 2. Modele girecek sayısal öznitelikler
    feature_cols = [
        "price_per_100g",
        "rolling_mean_7d",
        "rolling_std_7d",
        "price_diff_1d",
        "pct_change_1d",
        "z_score",
        "discount_ratio"
    ]

    X = latest_df[feature_cols].fillna(0)

    # 3. Isolation Forest ile Anomali Tespiti
    # contamination=0.10 -> Verideki en belirgin %10'luk uç fiyat hareketlerini yakala
    iso = IsolationForest(contamination=0.10, random_state=42)
    latest_df["anomaly_label"] = iso.fit_predict(X)  # -1: Anomali (Olağan dışı fiyat), 1: Normal
    
    # Anomali skorunu 0-1 aralığına normalize et (Düşük skor = anomali)
    raw_scores = iso.score_samples(X)
    latest_df["anomaly_score"] = np.round((raw_scores.max() - raw_scores) / (raw_scores.max() - raw_scores.min()), 2)

    # 4. Fırsat Skoru (Deal Score: 0 - 100) Hesaplama
    # Mantık: Fiyat ortalamanın altındaysa + Z-Score negatifse + Sahte indirim değilse puan yükselir
    latest_df["deal_score"] = (
        (latest_df["discount_ratio"] * 50) + 
        (np.clip(-latest_df["z_score"], 0, 3) / 3 * 30) + 
        (latest_df["anomaly_score"] * 20)
    ).round(1)

    # Sahte indirim olarak işaretlenenlerin puanını düşür
    latest_df.loc[latest_df["is_fake_discount"] == 1, "deal_score"] = (
        latest_df["deal_score"] * 0.3
    ).round(1)

    # 5. Karar Sınıflandırması
    def classify_deal(row):
        if row["is_fake_discount"] == 1:
            return "Sahte İndirim Şüphesi"
        elif row["deal_score"] >= 65:
            return "Gerçek Dip Fiyat / Fırsat"
        elif row["deal_score"] >= 40:
            return "Makul İndirim"
        else:
            return "Normal Fiyat"

    latest_df["recommendation"] = latest_df.apply(classify_deal, axis=1)

    return latest_df

if __name__ == "__main__":
    print("Makine öğrenimi modeli çalıştırılıyor...")
    results = train_and_detect_deals()
    
    print("\nPuan Dağılımı Özeti:")
    print(results["deal_score"].describe().round(2))
    
    print("\nKarar Dağılımı:")
    print(results["recommendation"].value_counts())
    
    print("\nEn Yüksek Fırsat Puanına Sahip İlk 5 Ürün:")
    cols = ["title", "roaster", "price", "rolling_mean_7d", "deal_score", "recommendation"]
    top_deals = results.sort_values(by="deal_score", ascending=False)[cols].head(5)
    print(top_deals.to_string(index=False))