import os
import sys
import sqlite3
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# Proje dizinini sys.path'e ekle
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "src"))

from features import build_feature_dataset
from model import train_and_detect_deals
from scraper import KahhveComScraper
from database import save_scraped_data, init_db
from notifier import send_telegram_alert

st.set_page_config(
    page_title="Kahve Fiyat Radarı & Fırsat Dedektifi",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #d4a373;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #a0aab2;
        margin-bottom: 1.5rem;
    }
    .deal-card {
        padding: 1rem;
        border-radius: 10px;
        background: #1e2229;
        border-left: 5px solid #d4a373;
        margin-bottom: 0.8rem;
    }
    .fake-alert {
        border-left-color: #e63946 !important;
    }
    .badge-firsat {
        background-color: #2a9d8f;
        color: white;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
    }
    .badge-sahte {
        background-color: #e63946;
        color: white;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">☕ Kahve Fiyat Zekası & Fırsat Dedektifi</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">3. Nesil kahvelerdeki sahte indirimleri tespit edin, gerçek dip fiyatları yakalayın.</div>', unsafe_allow_html=True)

@st.cache_data(ttl=60)
def load_analysis_data():
    try:
        deals_df = train_and_detect_deals()
        return deals_df
    except Exception as e:
        st.error(f"Model çalıştırılırken hata oluştu: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_history_data():
    try:
        raw_df = build_feature_dataset()
        return raw_df
    except Exception as e:
        st.error(f"Fiyat geçmişi yüklenirken hata: {e}")
        return pd.DataFrame()

deals_df = load_analysis_data()
history_df = load_history_data()

# Üst KPI Kartları
col1, col2, col3, col4 = st.columns(4)

total_products = len(deals_df) if not deals_df.empty else 0
real_deals = len(deals_df[deals_df["recommendation"] == "Gerçek Dip Fiyat / Fırsat"]) if not deals_df.empty else 0
fake_discounts = len(deals_df[deals_df["recommendation"] == "Sahte İndirim Şüphesi"]) if not deals_df.empty else 0
avg_100g = deals_df["price_per_100g"].mean() if not deals_df.empty and "price_per_100g" in deals_df else 0.0

col1.metric("📦 Takip Edilen Ürün", f"{total_products} adet")
col2.metric("🔥 Gerçek Dip Fiyat", f"{real_deals} fırsat", delta=f"{real_deals} aktif" if real_deals > 0 else None)
col3.metric("🚨 Sahte İndirim Uyarısı", f"{fake_discounts} şüpheli", delta=f"-{fake_discounts}" if fake_discounts > 0 else None, delta_color="inverse")
col4.metric("⚖️ Ort. 100g Fiyatı", f"{avg_100g:.2f} TL")

tab1, tab2, tab3 = st.tabs(["🔥 Günün Fırsatları & Radarı", "📈 Fiyat Geçmişi & Grafik", "⚙️ Canlı Pipeline Kontrolü"])

with tab1:
    st.subheader("Günün Kahve İndirim Analizi")
    if not deals_df.empty:
        # Filtreleme Alanı
        fcol1, fcol2, fcol3 = st.columns([2, 2, 2])
        roasters = ["Tümü"] + sorted(list(deals_df["roaster"].dropna().unique()))
        selected_roaster = fcol1.selectbox("Kavurucu (Marka):", roasters)

        statuses = ["Tümü", "Gerçek Dip Fiyat / Fırsat", "Makul İndirim", "Sahte İndirim Şüphesi", "Yeni Ürün (İzleniyor)"]
        selected_status = fcol2.selectbox("Durum:", statuses)

        min_score = fcol3.slider("Minimum Fırsat Skoru:", 0, 100, 20)

        # Filtre uygulama
        filtered = deals_df.copy()
        if selected_roaster != "Tümü":
            filtered = filtered[filtered["roaster"] == selected_roaster]
        if selected_status != "Tümü":
            filtered = filtered[filtered["recommendation"] == selected_status]
        filtered = filtered[filtered["deal_score"] >= min_score]
        filtered = filtered.sort_values(by="deal_score", ascending=False)

        st.caption(f"Filtreye uyan **{len(filtered)}** ürün listeleniyor:")

        # Tablo Görünümü
        display_cols = [
            "title", "roaster", "price", "rolling_mean_7d", "price_per_100g",
            "weight_g", "deal_score", "recommendation", "url"
        ]
        
        # Kolonları yeniden adlandır
        table_df = filtered[display_cols].copy()
        table_df.columns = [
            "Kahve Adı", "Kavurucu", "Güncel Fiyat (TL)", "7G Ort. (TL)", 
            "100g Fiyatı (TL)", "Gramaj", "Fırsat Skoru", "Durum", "Ürün Linki"
        ]

        st.dataframe(
            table_df,
            column_config={
                "Ürün Linki": st.column_config.LinkColumn("Satın Al", display_text="Ürüne Git 🔗"),
                "Güncel Fiyat (TL)": st.column_config.NumberColumn(format="%.2f TL"),
                "7G Ort. (TL)": st.column_config.NumberColumn(format="%.2f TL"),
                "100g Fiyatı (TL)": st.column_config.NumberColumn(format="%.2f TL"),
                "Fırsat Skoru": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d"),
            },
            hide_index=True,
            width="stretch"
        )
    else:
        st.warning("Henüz analiz edilecek veri bulunmuyor. 'Pipeline Kontrolü' sekmesinden tarama yapabilirsiniz.")

with tab2:
    st.subheader("Ürün Bazında Zaman Serisi ve Anomali Analizi")
    if not history_df.empty:
        coffee_titles = sorted(history_df["title"].unique())
        selected_coffee = st.selectbox("İncelemek istediğiniz kahveyi seçin:", coffee_titles)

        coffee_history = history_df[history_df["title"] == selected_coffee].sort_values("scraped_at")

        if not coffee_history.empty:
            # Özet Bilgi
            c_info1, c_info2, c_info3, c_info4 = st.columns(4)
            current_p = coffee_history["price"].iloc[-1]
            min_p = coffee_history["price"].min()
            max_p = coffee_history["price"].max()
            roaster_name = coffee_history["roaster"].iloc[-1]

            c_info1.metric("Kavurucu", roaster_name)
            c_info2.metric("Güncel Fiyat", f"{current_p:.2f} TL")
            c_info3.metric("Görülen En Dip Fiyat", f"{min_p:.2f} TL")
            c_info4.metric("Görülen En Yüksek", f"{max_p:.2f} TL")

            # Plotly Grafiği
            fig = go.Figure()

            # Günlük Fiyat Çizgisi
            fig.add_trace(go.Scatter(
                x=coffee_history["scraped_at"],
                y=coffee_history["price"],
                mode='lines+markers',
                name='Anlık Fiyat',
                line=dict(color='#d4a373', width=2),
                marker=dict(size=6)
            ))

            # 7 Günlük Hareketli Ortalama
            if "rolling_mean_7d" in coffee_history.columns:
                fig.add_trace(go.Scatter(
                    x=coffee_history["scraped_at"],
                    y=coffee_history["rolling_mean_7d"],
                    mode='lines',
                    name='7 Günlük Hareketli Ortalama',
                    line=dict(color='#2a9d8f', width=2, dash='dash')
                ))

            # Sahte İndirim Noktaları Varsa Vurgula
            fakes = coffee_history[coffee_history.get("is_fake_discount", 0) == 1]
            if not fakes.empty:
                fig.add_trace(go.Scatter(
                    x=fakes["scraped_at"],
                    y=fakes["price"],
                    mode='markers',
                    name='🚨 Sahte İndirim Şüphesi',
                    marker=dict(color='#e63946', size=12, symbol='x')
                ))

            fig.update_layout(
                title=f"{selected_coffee} - Fiyat Değişim Trendi",
                xaxis_title="Tarih",
                yaxis_title="Fiyat (TL)",
                template="plotly_dark",
                height=450,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            st.plotly_chart(fig, use_container_width=True)
            
            # Ürünün link butonu
            prod_url = coffee_history["url"].iloc[-1] if "url" in coffee_history.columns else ""
            if prod_url:
                st.markdown(f"[🔗 Bu Kahveyi Satın Alma Sayfasında Aç]({prod_url})")
    else:
        st.info("Fiyat geçmişi verisi henüz yok.")

with tab3:
    st.subheader("Otomasyon & Boru Hattı Yönetimi")
    st.write("Verileri anlık olarak yeniden çekip makine öğrenimi modellerini güncellemek için aşağıdaki paneli kullanabilirsiniz:")

    p_col1, p_col2 = st.columns(2)
    with p_col1:
        if st.button("🚀 Canlı Kazıma (Scraping) & Analizi Başlat", use_container_width=True):
            with st.spinner("kahhve.com taranıyor ve modeller eğitiliyor..."):
                init_db()
                scraper = KahhveComScraper()
                scraped = scraper.scrape(max_pages=2)
                if scraped:
                    save_scraped_data(scraped)
                    st.success(f"{len(scraped)} adet ürün başarıyla güncellendi!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("Ürün çekilemedi.")

    with p_col2:
        if st.button("📲 Test Telegram Bildirimi Gönder", use_container_width=True):
            success = send_telegram_alert("<b>☕ Kahve Fiyat Radarı:</b> Dashboard üzerinden bağlantı testi başarılı!")
            if success:
                st.success("Test mesajı Telegram üzerinden başarıyla iletildi!")
            else:
                st.error("Telegram bildirimi gönderilemedi. Lütfen .env dosyasındaki TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID değerlerini kontrol edin.")
