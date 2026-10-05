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

# ==========================================
# ☕ KAHVE ÇEKİRDEĞİ ANİMASYONU VE LÜKS TEMA CSS
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;1,600&display=swap');

    /* Ana Arka Plan ve Tipografi */
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #0d0a08 !important;
        background: radial-gradient(circle at 50% 0%, #221711 0%, #120d0a 50%, #080605 100%) !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #f5eee6 !important;
    }

    [data-testid="stHeader"] {
        background-color: transparent !important;
    }

    .main .block-container {
        position: relative;
        z-index: 2;
        padding-top: 1.8rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    /* Ambient Warm Orbs */
    .coffee-ambient-glow {
        position: fixed;
        border-radius: 50%;
        filter: blur(120px);
        pointer-events: none;
        z-index: 1;
        opacity: 0.22;
        animation: ambientBreathe 10s ease-in-out infinite alternate;
    }
    .glow-top {
        top: -120px;
        right: 5%;
        width: 500px;
        height: 500px;
        background: radial-gradient(circle, rgba(212, 163, 115, 0.45) 0%, rgba(139, 90, 43, 0.2) 60%, transparent 100%);
    }
    .glow-bottom {
        bottom: -100px;
        left: 2%;
        width: 600px;
        height: 600px;
        background: radial-gradient(circle, rgba(162, 107, 56, 0.35) 0%, rgba(77, 44, 20, 0.15) 60%, transparent 100%);
        animation-duration: 14s;
    }
    @keyframes ambientBreathe {
        0% { transform: scale(0.9) translate(0, 0); opacity: 0.18; }
        100% { transform: scale(1.15) translate(30px, 20px); opacity: 0.32; }
    }

    /* ☕ Uçuşan Kahve Çekirdekleri Konteyneri */
    .coffee-particles-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        pointer-events: none;
        z-index: 1;
        overflow: hidden;
    }

    .coffee-bean {
        position: absolute;
        top: -120px;
        opacity: 0;
        transform-origin: center center;
        will-change: transform, opacity;
    }

    /* Çekirdek Düşüş ve Takla Animasyonları */
    @keyframes beanFall1 {
        0% {
            transform: translateY(-100px) translateX(0px) rotate(0deg) rotateY(0deg);
            opacity: 0;
        }
        8% { opacity: 0.35; }
        50% {
            transform: translateY(50vh) translateX(35px) rotate(190deg) rotateY(180deg);
            opacity: 0.38;
        }
        90% { opacity: 0.32; }
        100% {
            transform: translateY(105vh) translateX(-20px) rotate(380deg) rotateY(360deg);
            opacity: 0;
        }
    }

    @keyframes beanFall2 {
        0% {
            transform: translateY(-100px) translateX(0px) rotate(45deg) rotateX(0deg);
            opacity: 0;
        }
        10% { opacity: 0.40; }
        50% {
            transform: translateY(55vh) translateX(-45px) rotate(220deg) rotateX(180deg);
            opacity: 0.45;
        }
        88% { opacity: 0.35; }
        100% {
            transform: translateY(105vh) translateX(30px) rotate(430deg) rotateX(360deg);
            opacity: 0;
        }
    }

    @keyframes beanFall3 {
        0% {
            transform: translateY(-100px) translateX(0px) rotate(90deg);
            opacity: 0;
        }
        6% { opacity: 0.25; }
        50% {
            transform: translateY(48vh) translateX(55px) rotate(260deg);
            opacity: 0.28;
        }
        92% { opacity: 0.22; }
        100% {
            transform: translateY(105vh) translateX(-35px) rotate(480deg);
            opacity: 0;
        }
    }

    @keyframes beanFall4 {
        0% {
            transform: translateY(-100px) translateX(0px) rotate(15deg) rotateY(45deg);
            opacity: 0;
        }
        12% { opacity: 0.38; }
        50% {
            transform: translateY(52vh) translateX(-30px) rotate(195deg) rotateY(210deg);
            opacity: 0.40;
        }
        85% { opacity: 0.32; }
        100% {
            transform: translateY(105vh) translateX(45px) rotate(375deg) rotateY(360deg);
            opacity: 0;
        }
    }

    /* Farklı Çekirdek Boyutları ve Konumları */
    .b-1  { left: 3%;  width: 38px; animation: beanFall1 21s linear infinite -3s; }
    .b-2  { left: 11%; width: 48px; animation: beanFall2 24s linear infinite -14s; }
    .b-3  { left: 18%; width: 26px; animation: beanFall3 17s linear infinite -8s; filter: blur(1.5px); }
    .b-4  { left: 26%; width: 54px; animation: beanFall4 26s linear infinite -20s; }
    .b-5  { left: 34%; width: 32px; animation: beanFall1 19s linear infinite -6s; }
    .b-6  { left: 42%; width: 44px; animation: beanFall2 25s linear infinite -17s; }
    .b-7  { left: 51%; width: 22px; animation: beanFall3 16s linear infinite -11s; filter: blur(2px); }
    .b-8  { left: 59%; width: 58px; animation: beanFall4 23s linear infinite -5s; }
    .b-9  { left: 68%; width: 36px; animation: beanFall1 28s linear infinite -19s; }
    .b-10 { left: 76%; width: 28px; animation: beanFall2 18s linear infinite -9s; }
    .b-11 { left: 83%; width: 50px; animation: beanFall3 24s linear infinite -13s; }
    .b-12 { left: 91%; width: 34px; animation: beanFall4 20s linear infinite -7s; }
    .b-13 { left: 7%;  width: 20px; animation: beanFall2 27s linear infinite -15s; filter: blur(2.5px); }
    .b-14 { left: 22%; width: 42px; animation: beanFall1 22s linear infinite -2s; }
    .b-15 { left: 46%; width: 24px; animation: beanFall4 18s linear infinite -12s; filter: blur(1.2px); }
    .b-16 { left: 63%; width: 46px; animation: beanFall3 23s linear infinite -10s; }
    .b-17 { left: 88%; width: 30px; animation: beanFall2 19s linear infinite -4s; }
    .b-18 { left: 96%; width: 24px; animation: beanFall1 29s linear infinite -22s; filter: blur(1.8px); }

    /* Hero Header */
    .hero-container {
        background: linear-gradient(135deg, rgba(42, 28, 20, 0.7) 0%, rgba(24, 16, 11, 0.85) 100%);
        border: 1px solid rgba(212, 163, 115, 0.28);
        border-radius: 20px;
        padding: 2.2rem 2.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.55), inset 0 1px 0 rgba(255, 230, 200, 0.1);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        position: relative;
        overflow: hidden;
    }
    .hero-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #d4a373, #f39c12, #e76f51, #d4a373);
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(212, 163, 115, 0.15);
        border: 1px solid rgba(212, 163, 115, 0.35);
        color: #f7d794;
        font-size: 0.82rem;
        font-weight: 600;
        padding: 5px 14px;
        border-radius: 30px;
        margin-bottom: 0.8rem;
        letter-spacing: 0.5px;
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #2ec4b6;
        box-shadow: 0 0 10px #2ec4b6;
        animation: pulse 1.8s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(0.8); }
    }
    .hero-title {
        font-family: 'Playfair Display', serif;
        font-size: 2.6rem;
        font-weight: 700;
        background: linear-gradient(135deg, #ffffff 0%, #f7d794 50%, #d4a373 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 0.6rem 0;
        letter-spacing: -0.5px;
    }
    .hero-desc {
        color: #c9b097;
        font-size: 1.05rem;
        line-height: 1.6;
        max-width: 850px;
        margin-bottom: 1.2rem;
    }
    .hero-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }
    .hero-tag {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(212, 163, 115, 0.2);
        color: #e6ccb2;
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 500;
    }

    /* KPI Kartları - Modern Glassmorphism */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(38, 26, 18, 0.75) 0%, rgba(20, 14, 10, 0.85) 100%) !important;
        border: 1px solid rgba(212, 163, 115, 0.22) !important;
        border-radius: 16px !important;
        padding: 18px 22px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 230, 200, 0.08) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        position: relative !important;
        overflow: hidden !important;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px) !important;
        border-color: rgba(212, 163, 115, 0.55) !important;
        box-shadow: 0 15px 35px rgba(212, 163, 115, 0.18), 0 5px 15px rgba(0,0,0,0.5) !important;
    }
    [data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #d4a373, #e76f51, #d4a373);
        opacity: 0.7;
    }
    [data-testid="stMetricLabel"] {
        color: #c9b097 !important;
        font-size: 0.92rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.3px !important;
    }
    [data-testid="stMetricValue"] {
        color: #fff8f0 !important;
        font-weight: 700 !important;
        font-size: 1.85rem !important;
        text-shadow: 0 2px 10px rgba(0,0,0,0.5) !important;
    }

    /* Tabs Tasarımı */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(25, 18, 14, 0.7) !important;
        border: 1px solid rgba(212, 163, 115, 0.2) !important;
        border-radius: 14px !important;
        padding: 6px !important;
        gap: 8px !important;
        backdrop-filter: blur(10px) !important;
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        color: #c9b097 !important;
        font-weight: 600 !important;
        padding: 10px 22px !important;
        transition: all 0.25s ease !important;
        border: none !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #f7d794 !important;
        background: rgba(212, 163, 115, 0.12) !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(212, 163, 115, 0.25) 0%, rgba(162, 107, 56, 0.3) 100%) !important;
        color: #fff5eb !important;
        border: 1px solid rgba(212, 163, 115, 0.5) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
    }

    /* Butonlar */
    .stButton > button {
        background: linear-gradient(135deg, #a26b38 0%, #70441e 100%) !important;
        color: #fff9f4 !important;
        border: 1px solid rgba(247, 215, 148, 0.35) !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 0.65rem 1.4rem !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.35) !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #bd8147 0%, #855325 100%) !important;
        border-color: #f7d794 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(189, 129, 71, 0.4) !important;
        color: #ffffff !important;
    }

    /* Sidebar Tasarımı */
    [data-testid="stSidebar"] {
        background-color: #120d0a !important;
        background: linear-gradient(180deg, #18110c 0%, #0d0907 100%) !important;
        border-right: 1px solid rgba(212, 163, 115, 0.18) !important;
    }
    .sidebar-brand {
        padding: 1.2rem 0.5rem;
        text-align: center;
        border-bottom: 1px solid rgba(212, 163, 115, 0.15);
        margin-bottom: 1.5rem;
    }
    .sidebar-brand h3 {
        color: #f7d794;
        margin: 0;
        font-family: 'Playfair Display', serif;
        font-size: 1.35rem;
    }
    .sidebar-brand p {
        color: #a08c7d;
        font-size: 0.78rem;
        margin-top: 4px;
    }
    .sidebar-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(212, 163, 115, 0.15);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    /* Tablo Konteyneri */
    [data-testid="stDataFrame"] {
        border-radius: 14px !important;
        border: 1px solid rgba(212, 163, 115, 0.2) !important;
        background: rgba(22, 16, 12, 0.75) !important;
        backdrop-filter: blur(12px) !important;
        overflow: hidden !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# ☕ GERÇEKÇİ KAHVE ÇEKİRDEĞİ SVG BİLEŞENİ
# ==========================================
def get_coffee_bean_svg():
    return """
    <svg viewBox="0 0 100 130" xmlns="http://www.w3.org/2000/svg" style="width: 100%; height: 100%; display: block;">
      <defs>
        <radialGradient id="beanGrad" cx="36%" cy="32%" r="68%">
          <stop offset="0%" stop-color="#9a6232" />
          <stop offset="38%" stop-color="#5e3618" />
          <stop offset="78%" stop-color="#341b0b" />
          <stop offset="100%" stop-color="#1a0d05" />
        </radialGradient>
        <linearGradient id="creaseGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#140703" />
          <stop offset="100%" stop-color="#281206" />
        </linearGradient>
        <filter id="beanShadow" x="-30%" y="-30%" width="160%" height="160%">
          <feDropShadow dx="0" dy="8" stdDeviation="5" flood-color="#000000" flood-opacity="0.55"/>
        </filter>
      </defs>
      <!-- Çekirdek Gövdesi -->
      <path d="M50 7 C77 7, 95 33, 95 65 C95 97, 77 123, 50 123 C23 123, 5 97, 5 65 C5 33, 23 7, 50 7 Z" fill="url(#beanGrad)" filter="url(#beanShadow)"/>
      <!-- Sol Işık Yansıması -->
      <path d="M26 23 C16 41, 16 80, 27 102" stroke="rgba(255, 225, 185, 0.28)" stroke-width="4.5" stroke-linecap="round" fill="none"/>
      <!-- Kahve Çekirdeğinin İkonik S-Kıvrım Yarığı -->
      <path d="M50 11 Q64 41, 47 65 T50 119" stroke="url(#creaseGrad)" stroke-width="6.5" stroke-linecap="round" fill="none"/>
      <path d="M49 13 Q62 41, 48 65 T49 117" stroke="#0d0401" stroke-width="3" stroke-linecap="round" fill="none"/>
      <path d="M52 15 Q65 41, 51 66 T52 115" stroke="rgba(212, 163, 115, 0.22)" stroke-width="1.2" fill="none"/>
    </svg>
    """

# Sidebar Ayarları
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <h3>☕ RealCoffee Radar</h3>
        <p>3. Nesil Fiyat Zekası & Dedektif</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("🎨 Görsel Efektler")
    enable_beans = st.checkbox("☕ Arka Plan Kahve Çekirdekleri", value=True, help="Düşen kahve çekirdeği animasyonunu açıp kapatır.")
    
    st.markdown("---")
    st.subheader("⚡ Sistem Durumu")
    st.markdown("""
    <div class="sidebar-card">
        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
            <span style="color:#a08c7d; font-size:0.85rem;">Motor:</span>
            <span style="color:#2ec4b6; font-weight:600; font-size:0.85rem;">Aktif 🟢</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
            <span style="color:#a08c7d; font-size:0.85rem;">Model:</span>
            <span style="color:#f7d794; font-weight:600; font-size:0.85rem;">Isolation Forest</span>
        </div>
        <div style="display:flex; justify-content:space-between;">
            <span style="color:#a08c7d; font-size:0.85rem;">Tarayıcı:</span>
            <span style="color:#d4a373; font-weight:600; font-size:0.85rem;">kahhve.com</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.caption("💡 *Tavsiye: 7G ortalamasının %20 altında olan ve Z-Skoru negatif ürünler 'Gerçek Fırsat' olarak etiketlenir.*")

# Kahve Çekirdeği Animasyonunu Sayfaya Enjekte Et
if enable_beans:
    bean_svg_code = get_coffee_bean_svg()
    beans_html = f"""
    <div class="coffee-ambient-glow glow-top"></div>
    <div class="coffee-ambient-glow glow-bottom"></div>
    <div class="coffee-particles-container">
        <div class="coffee-bean b-1">{bean_svg_code}</div>
        <div class="coffee-bean b-2">{bean_svg_code}</div>
        <div class="coffee-bean b-3">{bean_svg_code}</div>
        <div class="coffee-bean b-4">{bean_svg_code}</div>
        <div class="coffee-bean b-5">{bean_svg_code}</div>
        <div class="coffee-bean b-6">{bean_svg_code}</div>
        <div class="coffee-bean b-7">{bean_svg_code}</div>
        <div class="coffee-bean b-8">{bean_svg_code}</div>
        <div class="coffee-bean b-9">{bean_svg_code}</div>
        <div class="coffee-bean b-10">{bean_svg_code}</div>
        <div class="coffee-bean b-11">{bean_svg_code}</div>
        <div class="coffee-bean b-12">{bean_svg_code}</div>
        <div class="coffee-bean b-13">{bean_svg_code}</div>
        <div class="coffee-bean b-14">{bean_svg_code}</div>
        <div class="coffee-bean b-15">{bean_svg_code}</div>
        <div class="coffee-bean b-16">{bean_svg_code}</div>
        <div class="coffee-bean b-17">{bean_svg_code}</div>
        <div class="coffee-bean b-18">{bean_svg_code}</div>
    </div>
    """
    st.markdown(beans_html, unsafe_allow_html=True)

# ==========================================
# 🏆 HERO BANNER BÖLÜMÜ
# ==========================================
st.markdown("""
<div class="hero-container">
    <div class="hero-badge">
        <span class="pulse-dot"></span> PİYASA RADARI & AI DEDEKTİFİ AKTİF
    </div>
    <h1 class="hero-title">☕ Kahve Fiyat Zekası</h1>
    <p class="hero-desc">
        3. Nesil nitelikli kahvelerdeki yapay fiyat şişirmelerini ve sahte indirimleri makine öğrenimi ile tespit edin; gerçek dip fiyat fırsatlarını anında yakalayın.
    </p>
    <div class="hero-tags">
        <span class="hero-tag">🔥 İndirim Doğrulama</span>
        <span class="hero-tag">📊 7G / 14G Hareketli Ortalamalar</span>
        <span class="hero-tag">🤖 Isolation Forest Anomali Radarı</span>
        <span class="hero-tag">⚖️ 100g Standart Fiyat Endeksi</span>
        <span class="hero-tag">📲 Telegram Otomasyonu</span>
    </div>
</div>
""", unsafe_allow_html=True)

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

col1.metric("📦 Takip Edilen Kahve", f"{total_products} adet")
col2.metric("🔥 Gerçek Dip Fiyat", f"{real_deals} fırsat", delta=f"{real_deals} aktif" if real_deals > 0 else None)
col3.metric("🚨 Sahte İndirim Uyarısı", f"{fake_discounts} şüpheli", delta=f"-{fake_discounts}" if fake_discounts > 0 else None, delta_color="inverse")
col4.metric("⚖️ Ort. 100g Endeksi", f"{avg_100g:.2f} TL")

tab1, tab2, tab3 = st.tabs(["🔥 Günün Fırsatları & Radarı", "📈 Fiyat Geçmişi & Grafik", "⚙️ Canlı Pipeline Kontrolü"])

with tab1:
    st.subheader("Günün Kahve İndirim Analizi")
    if not deals_df.empty:
        # Filtreleme Alanı
        fcol1, fcol2, fcol3 = st.columns([2, 2, 2])
        roasters = ["Tümü"] + sorted(list(deals_df["roaster"].dropna().unique()))
        selected_roaster = fcol1.selectbox("Kavurucu (Marka):", roasters)

        statuses = ["Tümü", "Gerçek Dip Fiyat / Fırsat", "Makul İndirim", "Sahte İndirim Şüphesi", "Normal Fiyat", "Yeni Ürün (İzleniyor)"]
        selected_status = fcol2.selectbox("Durum:", statuses)

        min_score = fcol3.slider("Minimum Fırsat Skoru:", 0, 100, 0)

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

            # Plotly Grafiği - Lüks Espresso Teması
            fig = go.Figure()

            # Günlük Fiyat Çizgisi
            fig.add_trace(go.Scatter(
                x=coffee_history["scraped_at"],
                y=coffee_history["price"],
                mode='lines+markers',
                name='Anlık Fiyat',
                line=dict(color='#f7d794', width=2.5),
                marker=dict(size=7, color='#d4a373', line=dict(width=1.5, color='#ffffff'))
            ))

            # 7 Günlük Hareketli Ortalama
            if "rolling_mean_7d" in coffee_history.columns:
                fig.add_trace(go.Scatter(
                    x=coffee_history["scraped_at"],
                    y=coffee_history["rolling_mean_7d"],
                    mode='lines',
                    name='7 Günlük Hareketli Ortalama',
                    line=dict(color='#2ec4b6', width=2, dash='dash')
                ))

            # Sahte İndirim Noktaları Varsa Vurgula
            fakes = coffee_history[coffee_history.get("is_fake_discount", 0) == 1]
            if not fakes.empty:
                fig.add_trace(go.Scatter(
                    x=fakes["scraped_at"],
                    y=fakes["price"],
                    mode='markers',
                    name='🚨 Sahte İndirim Şüphesi',
                    marker=dict(color='#ff5a5f', size=13, symbol='x', line=dict(width=2))
                ))

            fig.update_layout(
                title=dict(
                    text=f"<b>{selected_coffee}</b> — Fiyat Değişim Trendi",
                    font=dict(size=17, color="#f7d794")
                ),
                xaxis=dict(
                    title="Tarih",
                    gridcolor="rgba(212, 163, 115, 0.12)",
                    zerolinecolor="rgba(212, 163, 115, 0.2)",
                    tickfont=dict(color="#c9b097")
                ),
                yaxis=dict(
                    title="Fiyat (TL)",
                    gridcolor="rgba(212, 163, 115, 0.12)",
                    zerolinecolor="rgba(212, 163, 115, 0.2)",
                    tickfont=dict(color="#c9b097")
                ),
                paper_bgcolor="rgba(20, 14, 10, 0.8)",
                plot_bgcolor="rgba(14, 10, 7, 0.9)",
                font=dict(color="#e4d5c7"),
                template="plotly_dark",
                height=460,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(color="#f3ede2")
                ),
                margin=dict(l=40, r=40, t=60, b=40)
            )

            st.plotly_chart(fig, width='stretch')
            
            # Ürünün link butonu
            prod_url = coffee_history["url"].iloc[-1] if "url" in coffee_history.columns else ""
            if prod_url:
                st.markdown(f"""
                <div style="margin-top: 1rem;">
                    <a href="{prod_url}" target="_blank" style="
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                        background: linear-gradient(135deg, #a26b38 0%, #70441e 100%);
                        color: #ffffff;
                        text-decoration: none;
                        padding: 10px 20px;
                        border-radius: 10px;
                        font-weight: 600;
                        border: 1px solid rgba(247, 215, 148, 0.35);
                        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.35);
                    ">
                        🛒 Bu Kahveyi Satın Alma Sayfasında Aç 🔗
                    </a>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Fiyat geçmişi verisi henüz yok.")

with tab3:
    st.subheader("Otomasyon & Boru Hattı Yönetimi")
    st.write("Verileri anlık olarak yeniden çekip makine öğrenimi modellerini güncellemek için aşağıdaki paneli kullanabilirsiniz:")

    p_col1, p_col2 = st.columns(2)
    with p_col1:
        if st.button("🚀 Canlı Kazıma (Scraping) & Analizi Başlat", width="stretch"):
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
        if st.button("📲 Test Telegram Bildirimi Gönder", width="stretch"):
            success = send_telegram_alert("<b>☕ Kahve Fiyat Radarı:</b> Dashboard üzerinden bağlantı testi başarılı!")
            if success:
                st.success("Test mesajı Telegram üzerinden başarıyla iletildi!")
            else:
                st.error("Telegram bildirimi gönderilemedi. Lütfen .env dosyasındaki TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID değerlerini kontrol edin.")
