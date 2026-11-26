import io
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="SIA POS - Sistem Kasir & Akuntansi FnB",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- DATABASE SETUP ---
conn = sqlite3.connect("sia_fnb_pos.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS penjualan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    no_faktur TEXT,
    waktu TEXT,
    item TEXT,
    jumlah INTEGER,
    subtotal REAL,
    pajak REAL,
    total_harga REAL,
    metode TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS kas_kecil (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    waktu TEXT,
    jenis TEXT,
    keterangan TEXT,
    akun_lawan TEXT,
    jumlah REAL,
    penanggung_jawab TEXT
)
""")
conn.commit()

# --- DATA KATALOG PRODUK FNB (TERBARU) ---
PRODUK_FNB = [
    {"nama": "Burger", "harga": 20000, "kategori": "Makanan", "ikon": "🍔"},
    {"nama": "Sandwich", "harga": 15000, "kategori": "Makanan", "ikon": "🥪"},
    {"nama": "Nasi Ayam Geprek", "harga": 10000, "kategori": "Makanan", "ikon": "🍗"},
    {"nama": "Mie Goreng", "harga": 8000, "kategori": "Makanan", "ikon": "🍜"},
    {"nama": "French Fries", "harga": 10000, "kategori": "Snack", "ikon": "🍟"},
    {"nama": "Croissant Butter", "harga": 20000, "kategori": "Snack", "ikon": "🥐"},
    {"nama": "Kopi Susu Aren", "harga": 18000, "kategori": "Minuman", "ikon": "🧋"},
    {"nama": "Americano Ice", "harga": 15000, "kategori": "Minuman", "ikon": "☕"},
    {"nama": "Matcha Latte", "harga": 24000, "kategori": "Minuman", "ikon": "🍵"},
    {"nama": "Fanta Strawberry", "harga": 10000, "kategori": "Minuman", "ikon": "🥤"},
    {"nama": "Es Teh Manis", "harga": 8000, "kategori": "Minuman", "ikon": "🧊"},
]

# --- SESSION STATE ---
if "keranjang" not in st.session_state:
    st.session_state.keranjang = {}
if "struk_terakhir" not in st.session_state:
    st.session_state.struk_terakhir = None

# ==========================================================
# SIDEBAR: NAVIGASI & PENGATURAN TEMA WARNA MANDIRI
# ==========================================================
st.sidebar.markdown(
    "<h2 id='brand-title' style='margin-bottom:0; text-shadow: 1px 1px 2px rgba(0,0,0,0.08);'>🟢 SIA-POS FnB</h2>"
    "<p style='font-size:12px; opacity:0.8;'>Sistem Informasi Akuntansi</p>",
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")

menu_aktif = st.sidebar.radio(
    "MENU UTAMA",
    [
        "🛒 Kasir (POS)",
        "💸 Kas Kecil (Masuk/Keluar)",
        "📊 Laporan Kas & Jurnal",
    ],
)

st.sidebar.markdown("---")
saldo_awal_kas = st.sidebar.number_input(
    "Saldo Awal Kas Laci (Rp):",
    min_value=0,
    value=500000,
    step=50000,
)

# --- FITUR CUSTOM THEME / ADJUST WARNA SENDIRI ---
st.sidebar.markdown("---")
with st.sidebar.expander("🎨 Sesuaikan Warna Tampilan", expanded=False):
    preset_tema = st.selectbox(
        "Pilih Preset Warna:",
        [
            "Hijau Modern (Default)",
            "Warm Coffee Shop (Cokelat & Krem)",
            "Biru Profesional",
            "Dark Mode Elegan",
            "Custom Warna Sendiri...",
        ],
    )

    PRESETS = {
        "Hijau Modern (Default)": {
            "primary": "#28A745",
            "primary_dark": "#1B7A32",
            "bg": "#EAEFF5",
            "card": "#FFFFFF",
            "text": "#1F2937",
            "border": "#D1D9E6",
        },
        "Warm Coffee Shop (Cokelat & Krem)": {
            "primary": "#8B5A2B",
            "primary_dark": "#5E3A18",
            "bg": "#EFE9E1",
            "card": "#FFFDF9",
            "text": "#3E2723",
            "border": "#D8C7B4",
        },
        "Biru Profesional": {
            "primary": "#2563EB",
            "primary_dark": "#1A44A8",
            "bg": "#E8EEF6",
            "card": "#FFFFFF",
            "text": "#0F172A",
            "border": "#C5D2E3",
        },
        "Dark Mode Elegan": {
            "primary": "#10B981",
            "primary_dark": "#078058",
            "bg": "#0F172A",
            "card": "#1E293B",
            "text": "#F8FAFC",
            "border": "#334155",
        },
    }

    if preset_tema == "Custom Warna Sendiri...":
        warna_primary = st.color_picker("Warna Aksen / Tombol Utama", "#28A745")
        warna_primary_dark = "#1A1A1A"
        warna_bg = st.color_picker("Warna Latar Belakang", "#EAEFF5")
        warna_card = st.color_picker("Warna Kartu & Sidebar", "#FFFFFF")
        warna_text = st.color_picker("Warna Teks", "#1F2937")
        warna_border = "#C8D1DF"
    else:
        pilihan = PRESETS[preset_tema]
        warna_primary = pilihan["primary"]
        warna_primary_dark = pilihan["primary_dark"]
        warna_bg = pilihan["bg"]
        warna_card = pilihan["card"]
        warna_text = pilihan["text"]
        warna_border = pilihan["border"]

# --- TERAPKAN CSS BERDIMENSI 3D & ELEVATION ---
st.markdown(
    f"""
    <style>
    /* Latar Utama & Teks Global */
    .stApp {{
        background-color: {warna_bg};
        color: {warna_text};
    }}
    .stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp div {{
        color: {warna_text};
    }}

    /* Sidebar Berdimensi */
    section[data-testid="stSidebar"] {{
        background-color: {warna_card};
        border-right: 1px solid {warna_border};
        box-shadow: 4px 0 18px rgba(0, 0, 0, 0.06);
    }}
    #brand-title {{
        color: {warna_primary} !important;
    }}

    /* Container Berbingkai (Kartu Panel 3D Timbul) */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: {warna_card};
        border: 1px solid {warna_border} !important;
        border-bottom: 4px solid {warna_border} !important;
        border-radius: 14px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06), 0 2px 6px rgba(0, 0, 0, 0.04);
        transition: all 0.25s ease;
    }}

    /* Kotak Total Harga Besar (Layar Kasir 3D Cekung / Inset + Bingkai Timbul) */
    .total-display {{
        background: linear-gradient(145deg, {warna_card}, {warna_bg});
        border: 2px solid {warna_primary};
        border-bottom: 5px solid {warna_primary};
        border-radius: 14px;
        padding: 18px;
        text-align: center;
        font-size: 34px;
        font-weight: 900;
        color: {warna_text} !important;
        margin-bottom: 16px;
        box-shadow: 0 10px 22px rgba(0, 0, 0, 0.08), inset 0 2px 5px rgba(0, 0, 0, 0.05);
        letter-spacing: 0.5px;
    }}

    /* Header Bar Atas 3D */
    .header-bar-3d {{
        background: {warna_card};
        padding: 12px 20px;
        border-radius: 12px;
        border: 1px solid {warna_border};
        border-bottom: 4px solid {warna_border};
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.05);
    }}

    /* Kartu Produk di Katalog Kanan (Floating 3D Card) */
    .product-box {{
        background: linear-gradient(180deg, {warna_card} 0%, {warna_bg} 100%);
        border: 1px solid {warna_border};
        border-bottom: 4px solid {warna_border};
        border-radius: 14px;
        padding: 14px 8px;
        text-align: center;
        margin-bottom: 8px;
        box-shadow: 0 6px 14px rgba(0, 0, 0, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.6);
        transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.2s ease, border-color 0.2s ease;
    }}
    .product-box:hover {{
        transform: translateY(-4px);
        border-color: {warna_primary};
        border-bottom-color: {warna_primary};
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.12);
    }}
    .product-emoji {{
        font-size: 38px;
        margin-bottom: 6px;
        filter: drop-shadow(0 4px 4px rgba(0, 0, 0, 0.15));
        transition: transform 0.2s ease;
    }}
    .product-box:hover .product-emoji {{
        transform: scale(1.12);
    }}
    .product-name {{
        font-weight: 700;
        font-size: 13px;
        color: {warna_text} !important;
        margin-bottom: 3px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .product-price {{
        font-size: 12px;
        opacity: 0.8;
        font-weight: 600;
    }}

    /* Tombol Utama 3D Tactile Push-Button */
    div.stButton > button[kind="primary"] {{
        background: linear-gradient(180deg, {warna_primary} 0%, {warna_primary_dark} 100%) !important;
        border: 1px solid {warna_primary_dark} !important;
        border-bottom: 4px solid #111827 !important;
        color: #FFFFFF !important;
        font-weight: 700;
        border-radius: 10px;
        box-shadow: 0 6px 14px rgba(0, 0, 0, 0.16), inset 0 1px 1px rgba(255, 255, 255, 0.35);
        transition: all 0.15s ease !important;
    }}
    div.stButton > button[kind="primary"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 18px rgba(0, 0, 0, 0.22), inset 0 1px 2px rgba(255, 255, 255, 0.45);
    }}
    div.stButton > button[kind="primary"]:active {{
        transform: translateY(3px);
        border-bottom-width: 1px !important;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15);
    }}
    div.stButton > button[kind="primary"] * {{
        color: #FFFFFF !important;
    }}

    /* Tombol Sekunder (+ Tambah, Batal, Hapus) 3D Tactile */
    div.stButton > button[kind="secondary"] {{
        background: linear-gradient(180deg, {warna_card} 0%, {warna_bg} 100%) !important;
        border: 1px solid {warna_border} !important;
        border-bottom: 3px solid {warna_border} !important;
        color: {warna_text} !important;
        font-weight: 600;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.7);
        transition: all 0.15s ease !important;
    }}
    div.stButton > button[kind="secondary"]:hover {{
        transform: translateY(-2px);
        border-color: {warna_primary} !important;
        border-bottom-color: {warna_primary} !important;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
    }}
    div.stButton > button[kind="secondary"]:active {{
        transform: translateY(2px);
        border-bottom-width: 1px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    }}

    /* Tombol Download Excel & Str
