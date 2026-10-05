import os
import sys
import sqlite3
import textwrap
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

# Proje dizinini sys.path'e ekle
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "src"))

from features import build_feature_dataset
from model import train_and_detect_deals
from scraper import KahhveComScraper
from database import save_scraped_data, init_db, DB_PATH
from notifier import send_telegram_alert

# ==========================================
# ☕ STREAMLIT SAYFA KONFİGÜRASYONU
# ==========================================
st.set_page_config(
    page_title="BeanRadar™ | Coffee Bean & Price Radar",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Güvenli HTML render fonksiyonu (Markdown girinti hatasını ve kod bloklarını önler)
def render_html(html_str: str):
    st.markdown(textwrap.dedent(html_str).strip(), unsafe_allow_html=True)

# ==========================================
# 💎 ULTRA-LÜKS DARK ESPRESSO TASARIM (CSS)
# ==========================================
render_html("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;0,800;1,600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    /* Ana Arka Plan ve Tipografi */
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #0d0906 !important;
        background: radial-gradient(circle at 50% 0%, #1c130d 0%, #100b07 55%, #080504 100%) !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #f7eee4 !important;
    }

    [data-testid="stHeader"] {
        background: transparent !important;
    }

    .main .block-container {
        position: relative;
        z-index: 2;
        padding-top: 1rem;
        padding-bottom: 3.5rem;
        max-width: 1400px;
    }

    /* Üst Navigasyon ve Kontrol Çubuğu */
    .top-nav-container {
        background: rgba(28, 18, 13, 0.75);
        border: 1px solid rgba(226, 178, 131, 0.22);
        border-radius: 18px;
        padding: 8px 18px;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(16px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
    }

    .live-radar-pill {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        background: rgba(72, 187, 120, 0.14);
        border: 1px solid rgba(72, 187, 120, 0.4);
        color: #48bb78;
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.8px;
        padding: 3px 10px;
        border-radius: 20px;
        text-transform: uppercase;
    }

    .pulse-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #48bb78;
        box-shadow: 0 0 10px #48bb78;
        animation: pulseRadar 2s infinite ease-in-out;
    }
    @keyframes pulseRadar {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(0.8); }
    }

    /* ====================================================
       ✨ LÜKS, GÖSTERİŞLİ & BELİRGİN ÜST NAVİGASYON BARI
       ==================================================== */
    .top-brand-badge {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 6px 14px;
        background: linear-gradient(145deg, rgba(42, 28, 19, 0.88) 0%, rgba(20, 13, 9, 0.96) 100%);
        border: 1.5px solid rgba(245, 215, 158, 0.38);
        border-radius: 16px;
        margin-top: -10px; /* Belirgin şekilde yukarı hizalar */
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45), 0 0 16px rgba(212, 163, 115, 0.18);
        backdrop-filter: blur(14px);
    }
    .brand-text {
        font-family: 'Playfair Display', serif;
        font-size: 1.35rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #fae2b6 45%, #d4a373 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.4px;
        line-height: 1;
    }

    [data-testid="stSegmentedControl"] {
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
        margin-top: -8px !important; /* Yukarı hizalama */
    }
    [data-testid="stSegmentedControl"] > div {
        background: linear-gradient(145deg, rgba(45, 30, 20, 0.95) 0%, rgba(18, 12, 8, 0.98) 100%) !important;
        border: 1.5px solid rgba(245, 215, 158, 0.45) !important;
        border-radius: 18px !important;
        padding: 5px 8px !important;
        gap: 10px !important;
        backdrop-filter: blur(18px) !important;
        box-shadow: 0 10px 32px rgba(0, 0, 0, 0.65), 0 0 25px rgba(212, 163, 115, 0.28), inset 0 1px 0 rgba(255, 235, 205, 0.25) !important;
    }
    [data-testid="stSegmentedControl"] button {
        border-radius: 12px !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.96rem !important;
        padding: 9px 24px !important;
        color: #baa291 !important;
        border: 1px solid transparent !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
        letter-spacing: 0.3px !important;
    }
    [data-testid="stSegmentedControl"] button:hover {
        color: #ffffff !important;
        background: rgba(226, 178, 131, 0.22) !important;
        border-color: rgba(245, 215, 158, 0.35) !important;
        transform: translateY(-2px) !important;
    }
    [data-testid="stSegmentedControl"] button[aria-checked="true"],
    [data-testid="stSegmentedControl"] button[data-checked="true"] {
        background: linear-gradient(135deg, #d4a373 0%, #b87b44 50%, #7e461a 100%) !important;
        color: #ffffff !important;
        border: 1.2px solid #fae2b6 !important;
        box-shadow: 0 6px 22px rgba(189, 129, 71, 0.65), 0 0 18px rgba(245, 215, 158, 0.45) !important;
        transform: translateY(-2px) scale(1.02) !important;
        text-shadow: 0 1px 4px rgba(0, 0, 0, 0.6) !important;
    }

    div[data-testid="column"]:nth-of-type(3) [data-testid="stToggle"] {
        margin-top: -10px !important; /* Toggle'ı da tam hizaya getirir */
    }

    /* Hero Banner - Profesyonel BeanRadar */
    .hero-banner {
        background: linear-gradient(135deg, rgba(42, 28, 19, 0.82) 0%, rgba(20, 13, 9, 0.92) 100%);
        border: 1px solid rgba(226, 178, 131, 0.26);
        border-radius: 20px;
        padding: 2.2rem 2.6rem;
        margin-bottom: 2rem;
        box-shadow: 0 16px 45px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 235, 215, 0.12);
        backdrop-filter: blur(16px);
        position: relative;
        overflow: hidden;
    }
    .hero-banner::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #d4a373 0%, #f5d79e 35%, #e07a5f 70%, #d4a373 100%);
    }
    .hero-badge-row {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 10px;
        margin-bottom: 1rem;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(226, 178, 131, 0.14);
        border: 1px solid rgba(226, 178, 131, 0.35);
        color: #f5d79e;
        font-size: 0.8rem;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 20px;
        letter-spacing: 0.4px;
    }
    .hero-title {
        font-family: 'Playfair Display', serif;
        font-size: 2.7rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #fae2b6 45%, #d4a373 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 0.8rem 0;
        letter-spacing: -0.5px;
        line-height: 1.2;
    }
    .hero-desc {
        color: #d6beaa;
        font-size: 1.05rem;
        line-height: 1.65;
        max-width: 900px;
        margin-bottom: 1.4rem;
    }
    .hero-pills {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }
    .hero-pill {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(226, 178, 131, 0.22);
        color: #edd5bf;
        padding: 6px 14px;
        border-radius: 10px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    /* KPI Metrik Kartları */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(38, 25, 17, 0.76) 0%, rgba(18, 12, 8, 0.86) 100%) !important;
        border: 1px solid rgba(226, 178, 131, 0.22) !important;
        border-radius: 16px !important;
        padding: 18px 22px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4) !important;
        backdrop-filter: blur(14px) !important;
        transition: transform 0.25s ease, border-color 0.25s ease !important;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px) !important;
        border-color: rgba(245, 215, 158, 0.5) !important;
    }
    [data-testid="stMetricLabel"] {
        color: #baa291 !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] {
        color: #fff9f2 !important;
        font-weight: 800 !important;
        font-size: 1.85rem !important;
        font-family: 'Outfit', sans-serif !important;
    }

    /* Öne Çıkan Fırsat Kartları */
    .deal-card {
        background: linear-gradient(145deg, rgba(42, 28, 20, 0.8) 0%, rgba(22, 15, 10, 0.9) 100%);
        border: 1px solid rgba(226, 178, 131, 0.26);
        border-radius: 18px;
        padding: 22px 24px;
        margin-bottom: 1.2rem;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative;
        overflow: hidden;
        box-shadow: 0 12px 35px rgba(0,0,0,0.4);
    }
    .deal-card:hover {
        transform: translateY(-5px);
        border-color: rgba(245, 215, 158, 0.6);
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6), 0 0 20px rgba(212, 163, 115, 0.2);
    }
    .deal-badge {
        display: inline-block;
        background: rgba(245, 215, 158, 0.16);
        border: 1px solid rgba(245, 215, 158, 0.4);
        color: #f5d79e;
        font-size: 0.76rem;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 14px;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        width: fit-content;
    }
    .deal-title {
        font-family: 'Playfair Display', serif;
        font-size: 1.28rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0 0 8px 0;
        line-height: 1.35;
    }
    .deal-meta {
        color: #baa291;
        font-size: 0.86rem;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .deal-price-row {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        margin-top: auto;
        padding-top: 12px;
        border-top: 1px solid rgba(226, 178, 131, 0.14);
    }
    .deal-price-current {
        font-family: 'Outfit', sans-serif;
        font-size: 1.55rem;
        font-weight: 800;
        color: #48bb78;
    }
    .deal-price-unit {
        font-size: 0.82rem;
        color: #d4a373;
        font-weight: 600;
    }
    .deal-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        background: linear-gradient(135deg, #a56d39 0%, #6f431c 100%);
        color: #ffffff !important;
        text-decoration: none !important;
        padding: 10px 18px;
        border-radius: 12px;
        font-size: 0.88rem;
        font-weight: 700;
        border: 1px solid rgba(245, 215, 158, 0.35);
        margin-top: 14px;
        transition: all 0.25s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .deal-btn:hover {
        background: linear-gradient(135deg, #bc7e42 0%, #855325 100%);
        border-color: #f5d79e;
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(189, 129, 71, 0.4);
        color: #ffffff !important;
    }

    /* Butonlar */
    .stButton > button {
        background: linear-gradient(135deg, #9a6332 0%, #683e1a 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(245, 215, 158, 0.35) !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        padding: 0.65rem 1.4rem !important;
        transition: all 0.25s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #b3763f 0%, #7d4d23 100%) !important;
        border-color: #f5d79e !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(189, 129, 71, 0.4) !important;
    }

    /* Sol Panel (Sidebar) */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #160f0a 0%, #0d0906 100%) !important;
        border-right: 1px solid rgba(226, 178, 131, 0.18) !important;
    }
    .sidebar-brand-box {
        text-align: center;
        padding: 1.4rem 0.6rem 1.1rem 0.6rem;
        border-bottom: 1px solid rgba(226, 178, 131, 0.16);
        margin-bottom: 1.2rem;
    }
    .sidebar-brand-box h2 {
        font-family: 'Playfair Display', serif;
        font-size: 1.55rem;
        color: #f5d79e;
        margin: 0;
        font-weight: 800;
        letter-spacing: -0.3px;
    }
    .sidebar-brand-box p {
        font-size: 0.78rem;
        color: #a89382;
        margin: 4px 0 0 0;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        font-weight: 600;
    }

    /* Sidebar Tips Kartları */
    .sidebar-tip-card {
        background: rgba(35, 24, 17, 0.75);
        border: 1px solid rgba(226, 178, 131, 0.2);
        border-radius: 12px;
        padding: 12px 14px;
        margin-bottom: 10px;
        transition: all 0.2s ease;
    }
    .sidebar-tip-card:hover {
        border-color: rgba(245, 215, 158, 0.45);
        background: rgba(45, 30, 21, 0.85);
        transform: translateX(3px);
    }
    .sidebar-tip-title {
        color: #f5d79e;
        font-size: 0.86rem;
        font-weight: 700;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .sidebar-tip-text {
        color: #baa291;
        font-size: 0.78rem;
        line-height: 1.45;
        margin: 0;
    }

    /* Telegram Bölümü Özel Kartları */
    .tg-hero-card {
        background: linear-gradient(135deg, rgba(30, 80, 120, 0.25) 0%, rgba(20, 35, 55, 0.4) 100%);
        border: 1px solid rgba(42, 171, 238, 0.35);
        border-radius: 18px;
        padding: 24px 28px;
        margin-bottom: 1.8rem;
    }
    .tg-msg-preview {
        background: #182533;
        border: 1px solid rgba(42, 171, 238, 0.4);
        border-radius: 14px;
        padding: 18px 20px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #ffffff;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        margin: 1rem 0;
    }

    /* Tablo Konteyneri */
    [data-testid="stDataFrame"] {
        border-radius: 16px !important;
        border: 1px solid rgba(226, 178, 131, 0.22) !important;
        background: rgba(22, 15, 10, 0.85) !important;
        backdrop-filter: blur(14px) !important;
        overflow: hidden !important;
    }

    /* ====================================================
       ✨ YARATICI, SADE & AKICI ARKA PLAN ANİMASYONU
       ==================================================== */
    .ambient-glow-1 {
        position: fixed;
        top: -120px;
        right: 6%;
        width: 580px;
        height: 580px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(212, 163, 115, 0.25) 0%, rgba(139, 90, 43, 0.08) 60%, transparent 100%);
        filter: blur(120px);
        pointer-events: none;
        z-index: 1;
        animation: glowBreathe1 15s ease-in-out infinite alternate;
    }
    .ambient-glow-2 {
        position: fixed;
        bottom: -100px;
        left: 4%;
        width: 650px;
        height: 650px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(162, 107, 56, 0.22) 0%, rgba(77, 44, 20, 0.06) 65%, transparent 100%);
        filter: blur(140px);
        pointer-events: none;
        z-index: 1;
        animation: glowBreathe2 19s ease-in-out infinite alternate;
    }
    @keyframes glowBreathe1 {
        0% { transform: scale(0.92) translate(0, 0); opacity: 0.6; }
        100% { transform: scale(1.15) translate(30px, 20px); opacity: 0.95; }
    }
    @keyframes glowBreathe2 {
        0% { transform: scale(0.95) translate(0, 0); opacity: 0.5; }
        100% { transform: scale(1.18) translate(-25px, -20px); opacity: 0.9; }
    }

    /* Süzülen zarif kahve çekirdekleri */
    .floating-bean {
        position: fixed;
        pointer-events: none;
        z-index: 1;
        will-change: transform, opacity;
        opacity: 0;
    }

    @keyframes beanFlyA {
        0% {
            transform: translateY(106vh) translateX(0px) rotate(0deg);
            opacity: 0;
        }
        12% { opacity: 0.32; }
        50% {
            transform: translateY(50vh) translateX(30px) rotate(160deg);
            opacity: 0.36;
        }
        88% { opacity: 0.26; }
        100% {
            transform: translateY(-10vh) translateX(-20px) rotate(320deg);
            opacity: 0;
        }
    }

    @keyframes beanFlyB {
        0% {
            transform: translateY(106vh) translateX(0px) rotate(40deg);
            opacity: 0;
        }
        15% { opacity: 0.28; }
        50% {
            transform: translateY(54vh) translateX(-35px) rotate(200deg);
            opacity: 0.32;
        }
        85% { opacity: 0.24; }
        100% {
            transform: translateY(-10vh) translateX(25px) rotate(380deg);
            opacity: 0;
        }
    }

    .fb-1 { left: 6%;  width: 32px; animation: beanFlyA 26s linear infinite -3s; filter: blur(1.5px); }
    .fb-2 { left: 18%; width: 44px; animation: beanFlyB 31s linear infinite -14s; }
    .fb-3 { left: 32%; width: 26px; animation: beanFlyA 24s linear infinite -8s; filter: blur(2px); }
    .fb-4 { left: 47%; width: 48px; animation: beanFlyB 29s linear infinite -19s; }
    .fb-5 { left: 62%; width: 34px; animation: beanFlyA 27s linear infinite -5s; filter: blur(1px); }
    .fb-6 { left: 74%; width: 42px; animation: beanFlyB 33s linear infinite -16s; }
    .fb-7 { left: 86%; width: 28px; animation: beanFlyA 25s linear infinite -11s; filter: blur(1.8px); }
    .fb-8 { left: 94%; width: 38px; animation: beanFlyB 30s linear infinite -7s; }

    /* Altın rengi parıltı tanecikleri */
    .aroma-mote {
        position: fixed;
        border-radius: 50%;
        background: radial-gradient(circle, #fff0d4 0%, #f5d79e 60%, rgba(212, 163, 115, 0) 100%);
        box-shadow: 0 0 10px rgba(245, 215, 158, 0.7);
        pointer-events: none;
        z-index: 1;
        opacity: 0;
    }
    @keyframes moteRise {
        0% { transform: translateY(105vh) translateX(0); opacity: 0; }
        20% { opacity: 0.45; }
        50% { transform: translateY(50vh) translateX(15px); opacity: 0.55; }
        80% { opacity: 0.4; }
        100% { transform: translateY(-10vh) translateX(-15px); opacity: 0; }
    }
    .mote-1 { left: 12%; width: 5px; height: 5px; animation: moteRise 18s ease-in-out infinite -2s; }
    .mote-2 { left: 38%; width: 6px; height: 6px; animation: moteRise 22s ease-in-out infinite -10s; }
    .mote-3 { left: 58%; width: 4px; height: 4px; animation: moteRise 16s ease-in-out infinite -6s; }
    .mote-4 { left: 82%; width: 5px; height: 5px; animation: moteRise 20s ease-in-out infinite -14s; }

    /* Yasal Sorumluluk Reddi Kutusu */
    .legal-disclaimer-box {
        background: rgba(22, 14, 10, 0.75);
        border: 1px solid rgba(226, 178, 131, 0.18);
        border-radius: 14px;
        padding: 16px 22px;
        margin-top: 3rem;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(10px);
    }
</style>
""")

# ==========================================
# ☕ GERÇEKÇİ KAHVE ÇEKİRDEĞİ SVG
# ==========================================
def get_coffee_bean_svg():
    return """
    <svg viewBox="0 0 100 130" xmlns="http://www.w3.org/2000/svg" style="width: 100%; height: 100%; display: block;">
      <defs>
        <radialGradient id="beanGrad" cx="36%" cy="32%" r="68%">
          <stop offset="0%" stop-color="#9a6232" />
          <stop offset="38%" stop-color="#5e3618" />
          <stop offset="78%" stop-color="#341b0b" />
          <stop offset="100%" stop-color="#180c05" />
        </radialGradient>
        <linearGradient id="creaseGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#140703" />
          <stop offset="100%" stop-color="#281206" />
        </linearGradient>
      </defs>
      <path d="M50 7 C77 7, 95 33, 95 65 C95 97, 77 123, 50 123 C23 123, 5 97, 5 65 C5 33, 23 7, 50 7 Z" fill="url(#beanGrad)"/>
      <path d="M26 23 C16 41, 16 80, 27 102" stroke="rgba(255, 225, 185, 0.22)" stroke-width="4.5" stroke-linecap="round" fill="none"/>
      <path d="M50 11 Q64 41, 47 65 T50 119" stroke="url(#creaseGrad)" stroke-width="6.5" stroke-linecap="round" fill="none"/>
      <path d="M49 13 Q62 41, 48 65 T49 117" stroke="#0d0401" stroke-width="3" stroke-linecap="round" fill="none"/>
    </svg>
    """

# ==========================================
# 📊 VERİ MOTORU & YÜKLEME
# ==========================================
@st.cache_data(ttl=60)
def load_analysis_data():
    try:
        deals_df = train_and_detect_deals()
        return deals_df
    except Exception as e:
        st.error(f"Analiz motoru çalıştırılırken hata: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_history_data():
    try:
        raw_df = build_feature_dataset()
        return raw_df
    except Exception as e:
        st.error(f"Fiyat geçmişi okunurken hata: {e}")
        return pd.DataFrame()

deals_df = load_analysis_data()
history_df = load_history_data()


# ==========================================
# 🧭 SABİT ÜST BAR (TOP NAVIGATION BAR - ASLA HAREKET ETMEZ)
# ==========================================
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "🎯 Canlı Fırsatlar"

top_col1, top_col2, top_col3 = st.columns([1.6, 4.2, 1.4], vertical_alignment="center")

with top_col1:
    render_html("""
    <div class="top-brand-badge">
        <span class="live-radar-pill"><span class="pulse-dot"></span> CANLI</span>
        <span class="brand-text">☕ BeanRadar™</span>
    </div>
    """)

with top_col2:
    nav_page = st.segmented_control(
        "Sayfa Seçimi",
        options=[
            "🎯 Canlı Fırsatlar",
            "📈 Fiyat Analitiği",
            "📲 Telegram Radarı"
        ],
        default=st.session_state["current_page"],
        label_visibility="collapsed",
        key="top_navbar_segmented"
    )
    if nav_page:
        st.session_state["current_page"] = nav_page

current_page = st.session_state["current_page"]

with top_col3:
    animasyonu_kapat = st.toggle("Animasyonu Kapat", value=False, help="Arka plandaki hareketli ortam ışığı ve kahve çekirdekleri efektini kapatır.")

# Yaratıcı & Akıcı Arka Plan Efekti
if not animasyonu_kapat:
    bean_svg = get_coffee_bean_svg()
    render_html(f"""
    <div class="ambient-glow-1"></div>
    <div class="ambient-glow-2"></div>
    
    <!-- Yükselen Altın Işık Tanecikleri -->
    <div class="aroma-mote mote-1"></div>
    <div class="aroma-mote mote-2"></div>
    <div class="aroma-mote mote-3"></div>
    <div class="aroma-mote mote-4"></div>

    <!-- Dengeli Süzülen 8 Zarif Çekirdek -->
    <div class="floating-bean fb-1">{bean_svg}</div>
    <div class="floating-bean fb-2">{bean_svg}</div>
    <div class="floating-bean fb-3">{bean_svg}</div>
    <div class="floating-bean fb-4">{bean_svg}</div>
    <div class="floating-bean fb-5">{bean_svg}</div>
    <div class="floating-bean fb-6">{bean_svg}</div>
    <div class="floating-bean fb-7">{bean_svg}</div>
    <div class="floating-bean fb-8">{bean_svg}</div>
    """)


# ==========================================
# 🧭 SOL PANEL (SIDEBAR) & ARA TUŞU & AÇILIR KAPANIR TİPSLER
# ==========================================
with st.sidebar:
    render_html("""
    <div class="sidebar-brand-box">
        <h2>☕ BeanRadar™</h2>
        <p>COFFEE BEAN INTELLIGENCE & PRICE RADAR</p>
    </div>
    """)

    st.markdown("### 🔍 Radar Filtreleri")

    all_roasters = sorted(list(deals_df["roaster"].dropna().unique())) if not deals_df.empty else []

    with st.form(key="sidebar_search_filter_form"):
        form_search = st.text_input(
            "Kahve veya Kavurucu Ara:",
            value=st.session_state.get("applied_search", ""),
            placeholder="Örn: Yirgacheffe, Petra..."
        )
        form_roaster = st.multiselect(
            "Kavurucu (Roaster):",
            options=all_roasters,
            default=st.session_state.get("applied_roasters", [])
        )
        form_sort = st.selectbox(
            "Sıralama Ölçütü:",
            [
                "En Yüksek Fırsat Skoru",
                "Fiyat: Düşükten Yükseğe",
                "Fiyat: Yüksekten Düşüğe",
                "100g Birim Fiyatına Göre"
            ],
            index=st.session_state.get("applied_sort_idx", 0)
        )
        form_min_score = st.slider(
            "Minimum Fırsat Skoru:",
            min_value=0,
            max_value=100,
            value=st.session_state.get("applied_min_score", 0)
        )

        # Belirgin ARA TUŞU
        btn_ara = st.form_submit_button("🔍 Kahveleri Ara & Filtrele", use_container_width=True)
        if btn_ara:
            st.session_state["applied_search"] = form_search
            st.session_state["applied_roasters"] = form_roaster
            st.session_state["applied_sort"] = form_sort
            st.session_state["applied_min_score"] = form_min_score
            st.session_state["applied_sort_idx"] = [
                "En Yüksek Fırsat Skoru",
                "Fiyat: Düşükten Yükseğe",
                "Fiyat: Yüksekten Düşüğe",
                "100g Birim Fiyatına Göre"
            ].index(form_sort)
            st.rerun()

    active_search = st.session_state.get("applied_search", "")
    active_roasters = st.session_state.get("applied_roasters", [])
    active_sort = st.session_state.get("applied_sort", "En Yüksek Fırsat Skoru")
    active_min_score = st.session_state.get("applied_min_score", 0)

    # Filtreleri Sıfırla Butonu
    if active_search or active_roasters or active_min_score > 0:
        if st.button("🔄 Filtreleri Temizle", use_container_width=True):
            st.session_state["applied_search"] = ""
            st.session_state["applied_roasters"] = []
            st.session_state["applied_sort"] = "En Yüksek Fırsat Skoru"
            st.session_state["applied_sort_idx"] = 0
            st.session_state["applied_min_score"] = 0
            st.rerun()

    render_html("<hr style='border-color: rgba(226, 178, 131, 0.16); margin: 1.5rem 0 1rem 0;'>")

    # 💡 SOL AŞAĞIDAKİ TİPSLER (AÇILIR KAPANIR - EXPANDER)
    with st.expander("💡 Kahveler Nasıl Değerlendiriliyor? (Tips)", expanded=False):
        render_html("""
        <div class="sidebar-tip-card">
            <div class="sidebar-tip-title">⚖️ 1. 100g Taban Fiyat Endeksi</div>
            <p class="sidebar-tip-text">
                Farklı gramajlar (200g, 250g, 500g, 1000g) yanıltıcı olmasın diye tüm paketler 100 gramlık birim maliyete indirgenir ve adil kıyaslanır.
            </p>
        </div>

        <div class="sidebar-tip-card">
            <div class="sidebar-tip-title">📊 2. 7 ve 14 Günlük Ortalama</div>
            <p class="sidebar-tip-text">
                Anlık etiket fiyatı yerine, ürünün son 1-2 haftadaki ağırlıklı piyasa trendi baz alınır. Günlük fiyat sıçramalarından arındırılmış gerçek taban hesaplanır.
            </p>
        </div>

        <div class="sidebar-tip-card">
            <div class="sidebar-tip-title">🔥 3. Fırsat Skoru (0 - 100)</div>
            <p class="sidebar-tip-text">
                İndirim derinliği (%50 ağırlık), tarihi dip seviyeden sapma (%30 ağırlık) ve makine öğrenimi anomali puanı (%20) harmanlanarak türetilir.
            </p>
        </div>

        <div class="sidebar-tip-card">
            <div class="sidebar-tip-title">🛡️ 4. Sahte İndirim Filtresi</div>
            <p class="sidebar-tip-text">
                Satıcı önce fiyatı suni olarak %8+ artırıp hemen ardından "indirim" süsü verdiyse bu hareket yakalanır ve ürünün fırsat puanı otomatik %70 kırpılır.
            </p>
        </div>

        <div class="sidebar-tip-card">
            <div class="sidebar-tip-title">🎯 5. Değerlendirme Seviyeleri</div>
            <p class="sidebar-tip-text">
                • <b>65+ Puan:</b> Gerçek Dip Fiyat / Kaçırılmayacak Fırsat<br>
                • <b>40 - 64 Puan:</b> Makul İndirimli Ürün<br>
                • <b>0 - 39 Puan:</b> Standart Piyasa Fiyatı
            </p>
        </div>
        """)

    with st.expander("⚖️ Yasal Uyarı & Şeffaflık", expanded=False):
        st.markdown("""
        **Bağımsız Fiyat Takipçisi:** BeanRadar™, e-ticaret platformlarının kamuya açık fiyat verilerini tüketici faydası ve şeffaflık için derler.
        
        • Sitemiz doğrudan ürün satışı yapmaz; yetkili resmi satış sayfalarına yönlendirir.
        • Yönlendirmeler satış ortaklığı (affiliate) kapsamında olabilir ve kullanıcıya ek maliyet oluşturmaz.
        • Hak sahipleri veya içerik talepleri için GitHub repository üzerinden iletişime geçilebilir.
        """)

    render_html("""
    <div style="text-align: center; color: #8c786a; font-size: 0.74rem; margin-top: 1.5rem;">
        BeanRadar™ Coffee Intelligence Platform • v2.6
    </div>
    """)


# ==========================================
# 📑 3 ANA EKRAN İÇERİĞİ (ÜST BARDAN KONTROL EDİLİR)
# ==========================================

# -------------------------------------------------------------
# 1. SAYFA: CANLI FIRSATLAR & PİYASA TAKİBİ
# -------------------------------------------------------------
if current_page == "🎯 Canlı Fırsatlar":
    # Hero Banner
    render_html("""
    <div class="hero-banner">
        <div class="hero-badge-row">
            <div class="hero-badge">
                <span class="pulse-dot"></span> PİYASA İSTİHBARATI & FIRSAT RADARI
            </div>
        </div>
        <h1 class="hero-title">☕ BeanRadar™ | Coffee Bean & Price Radar</h1>
        <p class="hero-desc">
            Nitelikli kahve piyasasındaki dönemsel fiyat hareketlerini 7/24 tarayarak gerçek dip fiyat indirimlerini,
            birim maliyet avantajlarını ve yapay zeka ile tespit edilen fırsatları anında yakalayın.
        </p>
        <div class="hero-pills">
            <span class="hero-pill">🌿 3. Nesil Kavurucu Ağı</span>
            <span class="hero-pill">📊 7G & 14G Hareketli Ortalama Çapası</span>
            <span class="hero-pill">⚖️ 100g Adil Maliyet Endeksi</span>
            <span class="hero-pill">🛡️ Şişirilmiş İndirim Filtresi</span>
            <span class="hero-pill">📲 Telegram Anlık Fırsat Bildirimi</span>
        </div>
    </div>
    """)

    # 4 Büyük KPI Metriği (İzlenen Kahveler)
    total_products = len(deals_df) if not deals_df.empty else 0
    max_deal_score = deals_df["deal_score"].max() if not deals_df.empty else 0.0
    avg_100g = deals_df["price_per_100g"].mean() if not deals_df.empty and "price_per_100g" in deals_df else 0.0
    min_100g = deals_df["price_per_100g"].min() if not deals_df.empty and "price_per_100g" in deals_df else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("☕ İzlenen Kahveler", f"{total_products} Çeşit", help="Fiyat geçmişi ve stokları kaydedilen toplam nitelikli kahve sayısı")
    col2.metric("🔥 En Yüksek Fırsat Skoru", f"{max_deal_score:.0f} / 100", delta="İndirim Fırsatı", help="Portföydeki en avantajlı fiyat dalgalanmasına sahip ürün puanı")
    col3.metric("⚖️ Piyasa 100g Tabanı", f"{min_100g:.2f} TL", help="Tüm portföy içindeki en düşük 100 gramlık birim maliyet")
    col4.metric("📊 Ortalama 100g Maliyeti", f"{avg_100g:.2f} TL", help="Portföyün hacimsel ağırlıklı 100 gram başına düşen fiyat ortalaması")

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    if not deals_df.empty:
        filtered = deals_df.copy()

        # Arama
        if active_search:
            filtered = filtered[
                filtered["title"].str.contains(active_search, case=False, na=False) |
                filtered["roaster"].str.contains(active_search, case=False, na=False)
            ]

        # Kavurucu
        if active_roasters:
            filtered = filtered[filtered["roaster"].isin(active_roasters)]

        # Min Skor
        filtered = filtered[filtered["deal_score"] >= active_min_score]

        # Sıralama
        if active_sort == "En Yüksek Fırsat Skoru":
            filtered = filtered.sort_values(by="deal_score", ascending=False)
        elif active_sort == "Fiyat: Düşükten Yükseğe":
            filtered = filtered.sort_values(by="price", ascending=True)
        elif active_sort == "Fiyat: Yüksekten Düşüğe":
            filtered = filtered.sort_values(by="price", ascending=False)
        elif active_sort == "100g Birim Fiyatına Göre":
            filtered = filtered.sort_values(by="price_per_100g", ascending=True)

        # 🌟 GÜNÜN ÖNE ÇIKAN EN İYİ 3 FIRSATI (Vitrin Kartları)
        render_html("""
        <h3 style="color:#f5d79e; font-family:'Playfair Display', serif; margin-top:0.8rem; margin-bottom:1rem;">
            🔥 Günün Öne Çıkan En İyi Kahve Fırsatları
        </h3>
        """)
        
        top3 = deals_df.sort_values(by="deal_score", ascending=False).head(3)
        if not top3.empty:
            tcols = st.columns(len(top3))
            for idx, (_, row) in enumerate(top3.iterrows()):
                with tcols[idx]:
                    r_mean = row.get("rolling_mean_7d", row["price"])
                    p_100g = row.get("price_per_100g", 0.0)
                    weight = row.get("weight_g", 250)
                    url = row.get("url", "https://kahhve.com")
                    title = row.get("title", "Kahve")
                    roaster = row.get("roaster", "Bilinmiyor")
                    score = row.get("deal_score", 0.0)
                    price = row.get("price", 0.0)

                    render_html(f"""
                    <div class="deal-card">
                        <div>
                            <span class="deal-badge">🔥 Fırsat Skoru: {score:.0f}/100</span>
                            <h4 class="deal-title">{title}</h4>
                            <div class="deal-meta">🏛️ {roaster} • ⚖️ {weight}g</div>
                        </div>
                        <div>
                            <div class="deal-price-row">
                                <span class="deal-price-current">{price:.2f} TL</span>
                                <span class="deal-price-unit">{p_100g:.1f} TL / 100g</span>
                            </div>
                            <a href="{url}" target="_blank" class="deal-btn">
                                Resmi Satış Sayfasında İncele 🔗
                            </a>
                        </div>
                    </div>
                    """)

        render_html("<hr style='border-color: rgba(226, 178, 131, 0.16); margin: 2.2rem 0 1.5rem 0;'>")

        # TABLO KONTROL BARI & CSV İNDİRME
        tb_col1, tb_col2 = st.columns([4, 1.6])
        with tb_col1:
            st.markdown(f"#### ☕ Canlı Kahve Listesi ({len(filtered)} Ürün Listeleniyor)")
            st.caption("Piyasa fiyatları, 7 günlük hareketli ortalamalar ve 100 gram başına adil maliyet kıyaslaması:")
        with tb_col2:
            csv_data = filtered.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Piyasa Raporunu CSV İndir",
                data=csv_data,
                file_name="beanradar_kahve_fiyat_raporu.csv",
                mime="text/csv",
                help="Kurumsal analiz veya arşiv için filtreli verileri dışa aktarın."
            )

        # Tablo
        display_cols = [
            "title", "roaster", "price", "rolling_mean_7d", "price_per_100g",
            "weight_g", "deal_score", "url"
        ]
        
        table_df = filtered[display_cols].copy()
        table_df.columns = [
            "Kahve Adı", "Kavurucu", "Güncel Fiyat (TL)", "7G Ort. (TL)", 
            "100g Fiyatı (TL)", "Gramaj", "Fırsat Skoru", "Satın Al"
        ]

        st.dataframe(
            table_df,
            column_config={
                "Satın Al": st.column_config.LinkColumn("Satın Al", display_text="Ürüne Git 🔗"),
                "Güncel Fiyat (TL)": st.column_config.NumberColumn(format="%.2f TL"),
                "7G Ort. (TL)": st.column_config.NumberColumn(format="%.2f TL"),
                "100g Fiyatı (TL)": st.column_config.NumberColumn(format="%.2f TL"),
                "Gramaj": st.column_config.NumberColumn(format="%d g"),
                "Fırsat Skoru": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d"),
            },
            hide_index=True,
            width="stretch"
        )
    else:
        st.info("Filtre kriterlerinize uygun ürün bulunamadı. Sol panelden filtreleri temizleyebilirsiniz.")


# -------------------------------------------------------------
# 2. SAYFA: FİYAT ANALİTİĞİ & TREND GRAFİĞİ
# -------------------------------------------------------------
elif current_page == "📈 Fiyat Analitiği":
    st.subheader("📈 Zaman Serisi, Volatilite & Fiyat Analizi")
    st.caption("İncelemek istediğiniz kahveyi seçerek son 30 günlük fiyat dalgalanmasını ve 7 günlük hareketli ortalamasını inceleyin.")

    if not history_df.empty:
        coffee_titles = sorted(history_df["title"].unique())
        selected_coffee = st.selectbox("İncelenecek Kahveyi Seçin:", coffee_titles)

        coffee_history = history_df[history_df["title"] == selected_coffee].sort_values("scraped_at")

        if not coffee_history.empty:
            c_info1, c_info2, c_info3, c_info4 = st.columns(4)
            current_p = coffee_history["price"].iloc[-1]
            min_p = coffee_history["price"].min()
            max_p = coffee_history["price"].max()
            roaster_name = coffee_history["roaster"].iloc[-1]

            c_info1.metric("Kavurucu", roaster_name)
            c_info2.metric("Güncel Satış Fiyatı", f"{current_p:.2f} TL")
            c_info3.metric("Tarihi En Düşük", f"{min_p:.2f} TL")
            c_info4.metric("Tarihi En Yüksek", f"{max_p:.2f} TL")

            # Plotly Grafiği
            fig = go.Figure()

            # Günlük Fiyat Çizgisi
            fig.add_trace(go.Scatter(
                x=coffee_history["scraped_at"],
                y=coffee_history["price"],
                mode='lines+markers',
                name='Piyasa Fiyatı (TL)',
                line=dict(color='#f5d79e', width=3),
                marker=dict(size=7, color='#d4a373', line=dict(width=1.5, color='#ffffff'))
            ))

            # 7 Günlük Hareketli Ortalama Bandı
            if "rolling_mean_7d" in coffee_history.columns:
                fig.add_trace(go.Scatter(
                    x=coffee_history["scraped_at"],
                    y=coffee_history["rolling_mean_7d"],
                    mode='lines',
                    name='7G Hareketli Ortalama (Trend Çapası)',
                    line=dict(color='#48bb78', width=2, dash='dash')
                ))

            # Sahte İndirim Noktası Varsa Vurgula
            fakes = coffee_history[coffee_history.get("is_fake_discount", 0) == 1]
            if not fakes.empty:
                fig.add_trace(go.Scatter(
                    x=fakes["scraped_at"],
                    y=fakes["price"],
                    mode='markers',
                    name='⚠️ Şüpheli Fiyat Hareketi',
                    marker=dict(color='#e07a5f', size=12, symbol='x', line=dict(width=2))
                ))

            fig.update_layout(
                title=dict(
                    text=f"<b>{selected_coffee}</b> — Fiyat Değişim & Trend Analizi",
                    font=dict(size=17, color="#f5d79e", family="Playfair Display")
                ),
                xaxis=dict(
                    title="Kayıt Tarihi",
                    gridcolor="rgba(226, 178, 131, 0.1)",
                    zerolinecolor="rgba(226, 178, 131, 0.15)",
                    tickfont=dict(color="#baa291")
                ),
                yaxis=dict(
                    title="Birim Fiyat (TL)",
                    gridcolor="rgba(226, 178, 131, 0.1)",
                    zerolinecolor="rgba(226, 178, 131, 0.15)",
                    tickfont=dict(color="#baa291")
                ),
                paper_bgcolor="rgba(22, 15, 10, 0.75)",
                plot_bgcolor="rgba(16, 11, 7, 0.85)",
                font=dict(color="#edd5bf"),
                template="plotly_dark",
                height=450,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(color="#f7eee4")
                ),
                margin=dict(l=30, r=30, t=65, b=30)
            )

            st.plotly_chart(fig, width='stretch')
            
            # Ürünün orijinal linki
            prod_url = coffee_history["url"].iloc[-1] if "url" in coffee_history.columns else ""
            if prod_url:
                render_html(f"""
                <div style="margin-top: 1rem; display: flex; justify-content: flex-end;">
                    <a href="{prod_url}" target="_blank" class="deal-btn" style="padding: 11px 24px; font-size: 0.95rem;">
                        🛒 Bu Kahveyi Resmi Satış Sayfasında İncele 🔗
                    </a>
                </div>
                """)
    else:
        st.info("Fiyat geçmişi verisi henüz bulunamadı.")


# -------------------------------------------------------------
# 3. SAYFA: TELEGRAM FIRSAT RADARI & BİLDİRİMLER
# -------------------------------------------------------------
elif current_page == "📲 Telegram Radarı":
    render_html("""
    <div class="tg-hero-card">
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
            <span style="font-size:2rem;">📲</span>
            <div>
                <h3 style="color:#ffffff; margin:0; font-family:'Playfair Display', serif;">
                    Telegram VIP Fırsat Alarmı & Otomasyon
                </h3>
                <p style="color:#8ac8f0; font-size:0.86rem; margin:2px 0 0 0;">
                    Piyasadaki gerçek dip indirimler yakalandığında telefonunuza anlık tıklanabilir satın alma bildirimi iletilir.
                </p>
            </div>
        </div>
    </div>
    """)

    tg_col1, tg_col2 = st.columns([3, 2.5])

    with tg_col1:
        st.markdown("#### ⚡ Canlı Telegram Aksiyonları")
        st.caption("Telegram bot entegrasyonunu buradan test edebilir veya piyasayı taratarak bildirim gönderebilirsiniz:")

        # 1. Test Bildirimi
        if st.button("📲 Test Telegram Bildirimi Gönder", width="stretch"):
            test_msg = (
                "<b>☕ BeanRadar™ Fırsat Radarı:</b>\n"
                "Sistem bağlantısı aktif! Telegram bildirim motoru kusursuz çalışıyor. "
                "Yeni dip fiyat fırsatları anlık olarak bu kanala düşecektir."
            )
            success = send_telegram_alert(test_msg)
            if success:
                st.success("Test mesajı Telegram VIP kanalınıza başarıyla ulaştı! ✅")
            else:
                st.error("Telegram bildirimi gönderilemedi. .env dosyasındaki TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID bilgilerini kontrol edin.")

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        # 2. Canlı Kazıma & Fırsat Bildirimi Tetikleme
        if st.button("🚀 Canlı Piyasayı Tara & Fırsat Bildirimi Gönder", width="stretch"):
            with st.spinner("Piyasa taranıyor, modeller çalıştırılıyor ve Telegram'a fırsat raporu hazırlanıyor..."):
                init_db()
                scraper = KahhveComScraper()
                scraped = scraper.scrape(max_pages=2)
                if scraped:
                    save_scraped_data(scraped)
                    updated_deals = train_and_detect_deals()
                    
                    # Fırsatları filtrele ve telegrama at
                    best_deals = updated_deals[updated_deals["deal_score"] >= 10].sort_values("deal_score", ascending=False).head(3)
                    
                    if not best_deals.empty:
                        tg_lines = ["<b>🔥 Günün En İyi Kahve Fırsatları (BeanRadar Canlı):</b>\n"]
                        for _, row in best_deals.iterrows():
                            t = row['title']
                            p = row['price']
                            m = row.get('rolling_mean_7d', p)
                            u = row.get('url', 'https://kahhve.com')
                            s = row.get('deal_score', 0)
                            tg_lines.append(f"• <b>{t}</b>\n  Fiyat: <b>{p:.2f} TL</b> (7G Ort: {m:.2f} TL) | Skor: {s:.0f}/100\n  🔗 <a href='{u}'>Satın Al / İncele</a>\n")
                        send_telegram_alert("\n".join(tg_lines))
                    
                    st.success(f"İşlem Tamamlandı: {len(scraped)} adet ürün güncellendi ve en iyi fırsatlar Telegram'a iletildi!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("Veri çekilemedi. Bağlantınızı kontrol edin.")

    with tg_col2:
        st.markdown("#### 📱 Örnek Bildirim Görünümü")
        st.caption("Abonelerin telefonuna düşen anlık Telegram fırsat alarmı simülasyonu:")

        # Simüle edilmiş telefon Telegram kartı
        render_html("""
        <div class="tg-msg-preview">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <b style="color:#2aabee; font-size:0.86rem;">🤖 BeanRadar Bot • 12:45</b>
                <span style="font-size:0.75rem; color:#8ac8f0;">CANLI ALARM</span>
            </div>
            <div style="font-size:0.92rem; line-height:1.6; color:#e1eef6;">
                <b>🔥 KAÇIRILMAYACAK DİP FİYAT FIRSATI!</b><br><br>
                ☕ <b>Fluxus Türk Kahvesi</b><br>
                • <b>Güncel Fiyat:</b> 209.99 TL <span style="color:#48bb78; font-weight:700;">(%18 İndirim)</span><br>
                • <b>7 Günlük Trend:</b> 256.00 TL<br>
                • <b>100g Birim Maliyet:</b> 84.00 TL / 100g<br>
                • <b>Fırsat Skoru:</b> 88 / 100 (Doğrulanmış)<br><br>
                🛒 <a href="https://kahhve.com" target="_blank" style="color:#42bbf0; text-decoration:underline; font-weight:700;">
                    Ürünü İncele & Satın Al 🔗
                </a>
            </div>
        </div>
        """)

        # Sistem & Veritabanı Telemetrisi
        try:
            conn = sqlite3.connect(DB_PATH)
            p_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            h_count = conn.execute("SELECT COUNT(*) FROM price_history").fetchone()[0]
            conn.close()
            
            st.markdown("#### 📁 Canlı Sistem Telemetrisi")
            m_col1, m_col2 = st.columns(2)
            m_col1.metric("Kayıtlı Kahve", f"{p_count} Çeşit")
            m_col2.metric("Fiyat Geçmişi", f"{h_count} Satır")
        except Exception:
            pass

# ==========================================
# ⚖️ YASAL BİLGİLENDİRME & ŞEFFAFLIK BEYANI (LEGAL DISCLAIMER)
# ==========================================
render_html("""
<div class="legal-disclaimer-box">
    <div style="display:flex; align-items:flex-start; gap:12px;">
        <span style="font-size:1.35rem; line-height:1;">⚖️</span>
        <div style="font-size:0.77rem; color:#a08c7d; line-height:1.65;">
            <b style="color:#d4a373;">Yasal Bilgilendirme, Tüketici Şeffaflığı & Satış Ortaklığı Beyanı:</b><br>
            <b>BeanRadar™</b>, nitelikli kahve tüketicilerini bilgilendirmek ve piyasa fiyatlarını şeffaflaştırmak amacıyla geliştirilmiş bağımsız bir fiyat takip ve veri indeksleme platformudur.<br>
            • Sitemiz doğrudan ürün satışı yapmamaktadır. Tüm fiyat, gramaj, stok ve ürün verileri e-ticaret sitelerinden (kahhve.com ve resmi kavurucular) kamuya açık ticari bilgiler taranarak indekslenmiştir.<br>
            • <i>'Resmi Satış Sayfasında İncele'</i> butonları kullanıcıyı doğrudan ilgili ürünün yetkili resmi satış sayfasına yönlendirir. Mesafeli satış sözleşmesi, fatura, ödeme ve teslimat süreçleri kullanıcı ile yönlendirilen resmi e-ticaret platformları arasında gerçekleşir.<br>
            • Sitemizdeki yönlendirme bağlantıları satış ortaklığı (affiliate / gelir ortaklığı) kapsamında olabilir. Bu yönlendirmeler son kullanıcıya herhangi bir ek maliyet veya fiyat farkı yansıtmaz.<br>
            • Marka isimleri, ticari unvanlar ve logolar ilgili hak sahiplerine aittir.
        </div>
    </div>
</div>
""")

