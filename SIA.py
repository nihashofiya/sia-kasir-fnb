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

# --- DATA KATALOG PRODUK FNB ---
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
    "<h2 id='brand-title' style='margin-bottom:0; text-shadow: 2px 3px 6px rgba(0,0,0,0.14);'>🟢 SIA-POS FnB</h2>"
    "<p style='font-size:12px; opacity:0.85;'>Sistem Informasi Akuntansi</p>",
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
            "bg": "#E2E8F0",
            "card": "#FFFFFF",
            "text": "#0F172A",
            "border": "#64748B",
        },
        "Warm Coffee Shop (Cokelat & Krem)": {
            "primary": "#8B5A2B",
            "primary_dark": "#5E3A18",
            "bg": "#E6DDD2",
            "card": "#FFFDF9",
            "text": "#2C1A12",
            "border": "#8D6E63",
        },
        "Biru Profesional": {
            "primary": "#1D4ED8",
            "primary_dark": "#1E3A8A",
            "bg": "#DCE6F2",
            "card": "#FFFFFF",
            "text": "#0F172A",
            "border": "#475569",
        },
        "Dark Mode Elegan": {
            "primary": "#10B981",
            "primary_dark": "#059669",
            "bg": "#0B1120",
            "card": "#1E293B",
            "text": "#F8FAFC",
            "border": "#64748B",
        },
    }

    if preset_tema == "Custom Warna Sendiri...":
        warna_primary = st.color_picker("Warna Aksen / Tombol Utama", "#1E3A8A")
        warna_primary_dark = "#0F172A"
        warna_bg = st.color_picker("Warna Latar Belakang", "#E2E8F0")
        warna_card = st.color_picker("Warna Kartu & Sidebar", "#FFFFFF")
        warna_text = st.color_picker("Warna Teks", "#0F172A")
        warna_border = st.color_picker("Warna Garis Pembatas (Border)", "#475569")
    else:
        pilihan = PRESETS[preset_tema]
        warna_primary = pilihan["primary"]
        warna_primary_dark = pilihan["primary_dark"]
        warna_bg = pilihan["bg"]
        warna_card = pilihan["card"]
        warna_text = pilihan["text"]
        warna_border = pilihan["border"]

# --- TERAPKAN CSS BERDIMENSI 3D + EFEK POP-IT & HOVER WARNA TOMBOL BAYAR ---
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

    /* Garis Divider & Horizontal Rule Tegas di Semua Halaman */
    hr, div[data-testid="stDivider"] hr {{
        border: none !important;
        border-top: 2px solid {warna_border} !important;
        opacity: 0.75 !important;
        margin-top: 8px !important;
        margin-bottom: 8px !important;
    }}

    /* Sidebar Berdimensi dengan Garis Tegas */
    section[data-testid="stSidebar"] {{
        background-color: {warna_card};
        border-right: 2px solid {warna_border};
        box-shadow: 8px 0 28px rgba(0, 0, 0, 0.14), 2px 0 8px rgba(0, 0, 0, 0.08);
    }}
    #brand-title {{
        color: {warna_primary} !important;
    }}

    /* Container Berbingkai (Kartu Panel 3D dengan Garis Tegas) */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: {warna_card};
        border: 2px solid {warna_border} !important;
        border-bottom: 5px solid {warna_border} !important;
        border-radius: 16px;
        box-shadow:
            0 20px 35px -10px rgba(0, 0, 0, 0.16),
            0 8px 16px -6px rgba(0, 0, 0, 0.10);
        transition: all 0.25s ease;
    }}

    /* Kotak Input Teks, Angka & Selectbox agar Garisnya Tegas */
    div[data-baseweb="input"], div[data-baseweb="select"] > div {{
        border: 1.5px solid {warna_border} !important;
        border-radius: 10px !important;
    }}

    /* Kotak Total Harga Besar */
    .total-display {{
        background: linear-gradient(145deg, {warna_card}, {warna_bg});
        border: 2.5px solid {warna_primary};
        border-bottom: 6px solid {warna_primary};
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        font-size: 36px;
        font-weight: 900;
        color: {warna_text} !important;
        text-shadow: 1px 2px 4px rgba(0, 0, 0, 0.12);
        margin-bottom: 18px;
        box-shadow:
            0 18px 32px -8px rgba(0, 0, 0, 0.18),
            0 6px 14px -4px {warna_primary}55,
            inset 0 3px 8px rgba(0, 0, 0, 0.08);
    }}

    /* Header Bar Atas 3D */
    .header-bar-3d {{
        background: {warna_card};
        padding: 13px 22px;
        border-radius: 14px;
        border: 2px solid {warna_border};
        border-bottom: 5px solid {warna_border};
        margin-bottom: 18px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow:
            0 12px 24px -6px rgba(0, 0, 0, 0.14),
            0 4px 8px -2px rgba(0, 0, 0, 0.08);
    }}

    /* Kartu Produk Makanan & Minuman -> Berubah Warna Seperti Tombol "Bayar" + Efek Pop-It */
    .product-box {{
        background: linear-gradient(180deg, {warna_card} 0%, {warna_bg} 100%);
        border: 2px solid {warna_border};
        border-bottom: 5px solid {warna_border};
        border-radius: 15px;
        padding: 14px 8px;
        text-align: center;
        margin-bottom: 10px;
        cursor: pointer;
        box-shadow:
            0 12px 22px -6px rgba(0, 0, 0, 0.15),
            0 4px 8px -2px rgba(0, 0, 0, 0.08);
        transition: all 0.22s cubic-bezier(0.34, 1.56, 0.64, 1);
    }}
    .product-box:hover,
    div[data-testid="column"]:has(button:hover) .product-box {{
        background: linear-gradient(180deg, {warna_primary} 0%, {warna_primary_dark} 100%) !important;
        border-color: {warna_primary_dark} !important;
        border-bottom: 5px solid #0F172A !important;
        transform: translateY(-6px) scale(1.05);
        box-shadow:
            0 20px 32px -6px {warna_primary}AA,
            0 10px 18px rgba(0, 0, 0, 0.25);
    }}
    .product-box:active {{
        transform: translateY(2px) scale(0.97);
        border-bottom-width: 2px !important;
    }}
    .product-emoji {{
        font-size: 40px;
        margin-bottom: 6px;
        filter: drop-shadow(0 8px 6px rgba(0, 0, 0, 0.24));
        transition: transform 0.22s cubic-bezier(0.34, 1.56, 0.64, 1);
    }}
    .product-box:hover .product-emoji,
    div[data-testid="column"]:has(button:hover) .product-emoji {{
        transform: scale(1.18) translateY(-2px);
        filter: drop-shadow(0 10px 10px rgba(0, 0, 0, 0.35));
    }}
    .product-name {{
        font-weight: 700;
        font-size: 13px;
        color: {warna_text} !important;
        margin-bottom: 3px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        transition: color 0.2s ease;
    }}
    .product-price {{
        font-size: 12px;
        opacity: 0.9;
        font-weight: 600;
        color: {warna_text} !important;
        transition: color 0.2s ease;
    }}
    .product-box:hover .product-name,
    .product-box:hover .product-price,
    div[data-testid="column"]:has(button:hover) .product-name,
    div[data-testid="column"]:has(button:hover) .product-price {{
        color: #FFFFFF !important;
        opacity: 1 !important;
    }}

    /* Tombol Utama ("Bayar") 3D + Efek Pop-It */
    div.stButton > button[kind="primary"],
    div.stButton > button[data-testid="stBaseButton-primary"] {{
        background: linear-gradient(180deg, {warna_primary} 0%, {warna_primary_dark} 100%) !important;
        border: 1.5px solid {warna_primary_dark} !important;
        border-bottom: 5px solid #0F172A !important;
        color: #FFFFFF !important;
        font-weight: 700;
        border-radius: 12px;
        box-shadow:
            0 12px 22px -5px {warna_primary}88,
            0 6px 12px rgba(0, 0, 0, 0.22);
        transition: all 0.22s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    }}
    div.stButton > button[kind="primary"]:hover,
    div.stButton > button[data-testid="stBaseButton-primary"]:hover {{
        transform: translateY(-4px) scale(1.04) !important;
        box-shadow:
            0 18px 28px -5px {warna_primary}BB,
            0 10px 18px rgba(0, 0, 0, 0.28) !important;
    }}
    div.stButton > button[kind="primary"]:active,
    div.stButton > button[data-testid="stBaseButton-primary"]:active {{
        transform: translateY(3px) scale(0.97) !important;
        border-bottom-width: 1px !important;
    }}
    div.stButton > button[kind="primary"] *,
    div.stButton > button[data-testid="stBaseButton-primary"] * {{
        color: #FFFFFF !important;
    }}

    /* Semua Tombol Sekunder (+ Tambah, Batal, Hapus 🗑️, +, -, Reset) -> Berubah Warna Seperti "Bayar" + Pop-It */
    div.stButton > button[kind="secondary"],
    div.stButton > button[data-testid="stBaseButton-secondary"],
    div.stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]) {{
        background: linear-gradient(180deg, {warna_card} 0%, {warna_bg} 100%) !important;
        border: 1.5px solid {warna_border} !important;
        border-bottom: 4px solid {warna_border} !important;
        color: {warna_text} !important;
        font-weight: 600;
        border-radius: 11px;
        box-shadow:
            0 8px 16px -4px rgba(0, 0, 0, 0.14),
            0 3px 6px rgba(0, 0, 0, 0.08);
        transition: all 0.22s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    }}
    div.stButton > button[kind="secondary"]:hover:not(:disabled),
    div.stButton > button[data-testid="stBaseButton-secondary"]:hover:not(:disabled),
    div.stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):hover:not(:disabled) {{
        background: linear-gradient(180deg, {warna_primary} 0%, {warna_primary_dark} 100%) !important;
        border-color: {warna_primary_dark} !important;
        border-bottom: 5px solid #0F172A !important;
        color: #FFFFFF !important;
        transform: translateY(-4px) scale(1.06) !important;
        box-shadow:
            0 16px 26px -5px {warna_primary}AA,
            0 8px 15px rgba(0, 0, 0, 0.24) !important;
    }}
    div.stButton > button[kind="secondary"]:hover:not(:disabled) *,
    div.stButton > button[data-testid="stBaseButton-secondary"]:hover:not(:disabled) *,
    div.stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):hover:not(:disabled) * {{
        color: #FFFFFF !important;
    }}
    div.stButton > button[kind="secondary"]:active:not(:disabled),
    div.stButton > button[data-testid="stBaseButton-secondary"]:active:not(:disabled),
    div.stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):active:not(:disabled) {{
        transform: translateY(3px) scale(0.95) !important;
        border-bottom-width: 1px !important;
    }}

    /* Tombol Form Submit ("Simpan Mutasi Kas Kecil") -> Efek Pop-It & Berubah Warna Saat Disentuh */
    div[data-testid="stFormSubmitButton"] > button {{
        background: linear-gradient(180deg, {warna_card} 0%, {warna_bg} 100%) !important;
        border: 2px solid {warna_primary} !important;
        border-bottom: 5px solid {warna_primary} !important;
        color: {warna_text} !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        box-shadow:
            0 10px 20px -5px rgba(0, 0, 0, 0.16),
            0 4px 8px rgba(0, 0, 0, 0.08) !important;
        transition: all 0.22s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    }}
    div[data-testid="stFormSubmitButton"] > button:hover {{
        background: linear-gradient(180deg, {warna_primary} 0%, {warna_primary_dark} 100%) !important;
        border-color: {warna_primary_dark} !important;
        border-bottom: 5px solid #0F172A !important;
        color: #FFFFFF !important;
        transform: translateY(-4px) scale(1.04) !important;
        box-shadow:
            0 18px 28px -5px {warna_primary}AA,
            0 10px 18px rgba(0, 0, 0, 0.26) !important;
    }}
    div[data-testid="stFormSubmitButton"] > button:hover * {{
        color: #FFFFFF !important;
    }}
    div[data-testid="stFormSubmitButton"] > button:active {{
        transform: translateY(3px) scale(0.97) !important;
        border-bottom-width: 1px !important;
    }}

    /* Tombol Download ("Download Laporan Format Excel" & "Unduh File Struk") -> Efek Pop-It & Berubah Warna */
    div.stDownloadButton > button {{
        background: linear-gradient(180deg, {warna_card} 0%, {warna_bg} 100%) !important;
        border: 2px solid {warna_primary} !important;
        border-bottom: 5px solid {warna_primary} !important;
        color: {warna_text} !important;
        border-radius: 12px !important;
        box-shadow:
            0 10px 20px -5px rgba(0, 0, 0, 0.16),
            0 4px 8px rgba(0, 0, 0, 0.08) !important;
        font-weight: 700 !important;
        transition: all 0.22s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    }}
    div.stDownloadButton > button:hover {{
        background: linear-gradient(180deg, {warna_primary} 0%, {warna_primary_dark} 100%) !important;
        border-color: {warna_primary_dark} !important;
        border-bottom: 5px solid #0F172A !important;
        color: #FFFFFF !important;
        transform: translateY(-4px) scale(1.04) !important;
        box-shadow:
            0 18px 28px -5px {warna_primary}AA,
            0 10px 18px rgba(0, 0, 0, 0.26) !important;
    }}
    div.stDownloadButton > button:hover * {{
        color: #FFFFFF !important;
    }}
    div.stDownloadButton > button:active {{
        transform: translateY(3px) scale(0.97) !important;
        border-bottom-width: 1px !important;
    }}

    /* Kartu Metrik Keuangan 3D dengan Garis Tegas */
    div[data-testid="stMetric"] {{
        background: linear-gradient(180deg, {warna_card} 0%, {warna_bg} 100%);
        border: 2px solid {warna_border};
        border-bottom: 5px solid {warna_primary};
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow:
            0 14px 26px -6px rgba(0, 0, 0, 0.15),
            0 5px 10px -3px rgba(0, 0, 0, 0.09);
    }}

    /* Garis Tab Navigasi Laporan agar Tidak Samar */
    div[data-baseweb="tab-list"] {{
        border-bottom: 2px solid {warna_border} !important;
        gap: 8px;
    }}

    /* Tabel Jurnal Berbingkai Penuh & Garis Kolom Jelas */
    .jurnal-table {{
        width: 100%;
        border-collapse: collapse;
        background-color: {warna_card};
        color: {warna_text};
        font-size: 14px;
        border: 2px solid {warna_border};
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 8px 18px rgba(0,0,0,0.08);
    }}
    .jurnal-table th {{
        background-color: {warna_bg};
        color: {warna_text};
        font-weight: 700;
        text-align: left;
        padding: 12px 14px;
        border: 1.5px solid {warna_border};
    }}
    .jurnal-table td {{
        padding: 10px 14px;
        border: 1.5px solid {warna_border};
        color: {warna_text};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- PENGATURAN RESET DATA ---
st.sidebar.markdown("---")
st.sidebar.caption("⚙️ Pengaturan Data Simulasi")
konfirmasi_reset = st.sidebar.checkbox("Konfirmasi hapus semua data")
if st.sidebar.button("🗑️ Reset Semua Transaksi", disabled=not konfirmasi_reset, use_container_width=True):
    c.execute("DELETE FROM penjualan")
    c.execute("DELETE FROM kas_kecil")
    c.execute("DELETE FROM sqlite_sequence WHERE name='penjualan' OR name='kas_kecil'")
    conn.commit()
    st.session_state.keranjang = {}
    st.session_state.struk_terakhir = None
    st.sidebar.success("Semua data berhasil di-reset!")
    st.rerun()

# ==========================================================
# HALAMAN 1: KASIR POS & CETAK STRUK
# ==========================================================
if menu_aktif == "🛒 Kasir (POS)":
    st.markdown(
        f"""
        <div class="header-bar-3d">
            <span style="color:{warna_primary} !important; font-weight:800; font-size:14px;">● Online — Shift Pagi</span>
            <span style="font-weight:700; font-size:14px;">🏪 Kedai Kopi & Resto Mahasiswa</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    kolom_struk, kolom_katalog = st.columns([1.15, 1.85], gap="medium")

    # --- KOLOM TENGAH: STRUK & KERANJANG PESANAN ---
    with kolom_struk:
        subtotal_keranjang = 0
        for nama_item, qty in st.session_state.keranjang.items():
            harga_item = next(p["harga"] for p in PRODUK_FNB if p["nama"] == nama_item)
            subtotal_keranjang += harga_item * qty

        pajak_pb1 = subtotal_keranjang * 0.10
        total_akhir = subtotal_keranjang + pajak_pb1

        st.markdown(
            f'<div class="total-display">Rp {total_akhir:,.0f}</div>',
            unsafe_allow_html=True,
        )

        with st.container(border=True):
            st.markdown("**🧾 Daftar Pesanan Saat Ini**")
            st.divider()

            if not st.session_state.keranjang:
                st.info("Belum ada menu dipilih. Klik tombol **+ Tambah** di sebelah kanan.")
            else:
                item_dihapus = None
                for nama_item, qty in list(st.session_state.keranjang.items()):
                    harga_satuan = next(p["harga"] for p in PRODUK_FNB if p["nama"] == nama_item)
                    total_per_item = harga_satuan * qty

                    c_nama, c_kurang, c_qty, c_tambah, c_harga = st.columns([3.2, 0.8, 0.8, 0.8, 2.2])
                    c_nama.markdown(f"**{nama_item}**")
                    if c_kurang.button("➖", key=f"min_{nama_item}"):
                        if qty > 1:
                            st.session_state.keranjang[nama_item] -= 1
                        else:
                            item_dihapus = nama_item
                        st.rerun()
                    c_qty.markdown(f"<div style='text-align:center; padding-top:5px;'><b>{qty}</b></div>", unsafe_allow_html=True)
                    if c_tambah.button("➕", key=f"plus_{nama_item}"):
                        st.session_state.keranjang[nama_item] += 1
                        st.rerun()
                    c_harga.markdown(f"<div style='text-align:right; padding-top:5px;'>Rp {total_per_item:,.0f}</div>", unsafe_allow_html=True)

                if item_dihapus:
                    del st.session_state.keranjang[item_dihapus]
                    st.rerun()

            st.divider()
            r1, r2 = st.columns(2)
            r1.write("Total sebelum pajak")
            r2.markdown(f"<div style='text-align:right;'>Rp {subtotal_keranjang:,.0f}</div>", unsafe_allow_html=True)

            r3, r4 = st.columns(2)
            r3.write("PB1 (10%)")
            r4.markdown(f"<div style='text-align:right;'>Rp {pajak_pb1:,.0f}</div>", unsafe_allow_html=True)

            r5, r6 = st.columns(2)
            r5.markdown("**Total Harga**")
            r6.markdown(f"<div style='text-align:right;'><b>Rp {total_akhir:,.0f}</b></div>", unsafe_allow_html=True)

            st.divider()
            metode_bayar = st.radio("Metode Pembayaran:", ["Cash", "QRIS"], horizontal=True)

            btn_kosong, btn_bayar = st.columns([1, 2])
            if btn_kosong.button("Batal", use_container_width=True):
                st.session_state.keranjang = {}
                st.rerun()

            if btn_bayar.button("Bayar", type="primary", use_container_width=True, disabled=(total_akhir == 0)):
                waktu_skrg = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                no_faktur = f"INV-{datetime.now().strftime('%H%M%S')}"

                detail_struk = []
                for nama_item, qty in st.session_state.keranjang.items():
                    harga_satuan = next(p["harga"] for p in PRODUK_FNB if p["nama"] == nama_item)
                    sub = harga_satuan * qty
                    pjk = sub * 0.10
                    tot = sub + pjk
                    c.execute(
                        """INSERT INTO penjualan (no_faktur, waktu, item, jumlah, subtotal, pajak, total_harga, metode)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (no_faktur, waktu_skrg, nama_item, qty, sub, pjk, tot, metode_bayar),
                    )
                    detail_struk.append({
                        "nama": nama_item,
                        "qty": qty,
                        "harga": harga_satuan,
                        "subtotal": sub,
                    })
                conn.commit()

                st.session_state.struk_terakhir = {
                    "no_faktur": no_faktur,
                    "waktu": waktu_skrg,
                    "items": detail_struk,
                    "subtotal": subtotal_keranjang,
                    "pajak": pajak_pb1,
                    "total": total_akhir,
                    "metode": metode_bayar,
                }
                st.session_state.keranjang = {}
                st.toast(f"✅ Pembayaran {no_faktur} berhasil dicatat!", icon="🎉")
                st.rerun()

        # --- AREA CETAK STRUK TRANSAKSI TERAKHIR ---
        if st.session_state.struk_terakhir:
            s = st.session_state.struk_terakhir
            with st.container(border=True):
                st.markdown("**🖨️ Struk Transaksi Terakhir (Siap Cetak)**")
                st.divider()

                baris_item_html = ""
                baris_item_txt = ""
                for it in s["items"]:
                    baris_item_html += f"""
                    <tr>
                        <td style="padding:2px 0; color:#111827;">{it['nama']}<br><small>{it['qty']} x Rp {it['harga']:,.0f}</small></td>
                        <td style="text-align:right; vertical-align:bottom; color:#111827;">Rp {it['subtotal']:,.0f}</td>
                    </tr>
                    """
                    baris_item_txt += f"{it['nama']} ({it['qty']}x @ {it['harga']:,.0f}) = Rp {it['subtotal']:,.0f}\n"

                html_struk = f"""
                <style>
                .btn-print-pop {{
                    margin-top: 12px;
                    width: 100%;
                    background: linear-gradient(180deg, {warna_card} 0%, {warna_bg} 100%);
                    color: {warna_text};
                    border: 2px solid {warna_primary};
                    border-bottom: 5px solid {warna_primary};
                    padding: 10px;
                    border-radius: 12px;
                    font-weight: 700;
                    font-size: 14px;
                    cursor: pointer;
                    box-shadow: 0 10px 18px -4px rgba(0,0,0,0.18);
                    transition: all 0.22s cubic-bezier(0.34, 1.56, 0.64, 1);
                }}
                .btn-print-pop:hover {{
                    background: linear-gradient(180deg, {warna_primary} 0%, {warna_primary_dark} 100%);
                    border-color: {warna_primary_dark};
                    border-bottom: 5px solid #0F172A;
                    color: #FFFFFF;
                    transform: translateY(-4px) scale(1.03);
                    box-shadow: 0 16px 26px -5px {warna_primary}AA, 0 8px 15px rgba(0,0,0,0.24);
                }}
                .btn-print-pop:active {{
                    transform: translateY(3px) scale(0.97);
                    border-bottom-width: 1px;
                }}
                </style>
                <div style="padding: 4px 6px 10px 6px;">
                    <div id="area-struk" style="font-family: 'Courier New', monospace; background:#FFFDF7; padding:14px; border:2px dashed #475569; border-radius:10px; color:#111827; font-size:12px; box-shadow: 0 10px 20px rgba(0,0,0,0.12);">
                        <div style="text-align:center; font-weight:bold; font-size:14px; color:#111827;">KEDAI KOPI & RESTO MAHASISWA</div>
                        <div style="text-align:center; font-size:11px; margin-bottom:8px; color:#374151;">Sistem Informasi Akuntansi FnB</div>
                        <div style="border-top:1.5px dashed #475569; margin:6px 0;"></div>
                        <div style="color:#111827;">No. Faktur : {s['no_faktur']}</div>
                        <div style="color:#111827;">Waktu      : {s['waktu']}</div>
                        <div style="color:#111827;">Pembayaran : {s['metode']}</div>
                        <div style="border-top:1.5px dashed #475569; margin:6px 0;"></div>
                        <table style="width:100%; border-collapse:collapse; font-size:12px;">
                            {baris_item_html}
                        </table>
                        <div style="border-top:1.5px dashed #475569; margin:6px 0;"></div>
                        <table style="width:100%; font-size:12px; color:#111827;">
                            <tr><td>Subtotal (DPP)</td><td style="text-align:right;">Rp {s['subtotal']:,.0f}</td></tr>
                            <tr><td>Pajak PB1 (10%)</td><td style="text-align:right;">Rp {s['pajak']:,.0f}</td></tr>
                            <tr style="font-weight:bold; font-size:13px;"><td>TOTAL BAYAR</td><td style="text-align:right;">Rp {s['total']:,.0f}</td></tr>
                        </table>
                        <div style="border-top:1.5px dashed #475569; margin:8px 0;"></div>
                        <div style="text-align:center; font-size:11px; color:#374151;">Terima Kasih Atas Kunjungan Anda!</div>
                    </div>
                    <button class="btn-print-pop" onclick="printStruk()">
                        🖨️ Cetak Struk / Simpan PDF
                    </button>
                </div>
                <script>
                function printStruk() {{
                    var isi = document.getElementById('area-struk').innerHTML;
                    var win = window.open('', '', 'height=600,width=400');
                    win.document.write('<html><head><title>Struk {s['no_faktur']}</title></head><body>');
                    win.document.write(isi);
                    win.document.write('</body></html>');
                    win.document.close();
                    win.focus();
                    win.print();
                }}
                </script>
                """
                components.html(html_struk, height=370, scrolling=True)

                teks_struk = (
                    f"KEDAI KOPI & RESTO MAHASISWA\n"
                    f"==============================\n"
                    f"No. Faktur : {s['no_faktur']}\n"
                    f"Waktu      : {s['waktu']}\n"
                    f"Metode     : {s['metode']}\n"
                    f"------------------------------\n"
                    f"{baris_item_txt}"
                    f"------------------------------\n"
                    f"Subtotal   : Rp {s['subtotal']:,.0f}\n"
                    f"PB1 (10%)  : Rp {s['pajak']:,.0f}\n"
                    f"TOTAL      : Rp {s['total']:,.0f}\n"
                    f"==============================\n"
                    f"Terima Kasih!\n"
                )
                st.download_button(
                    label="📄 Unduh File Struk (.txt)",
                    data=teks_struk,
                    file_name=f"Struk_{s['no_faktur']}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

    # --- KOLOM KANAN: KATALOG MENU GRID ---
    with kolom_katalog:
        with st.container(border=True):
            cari_produk = st.text_input("🔍 Cari produk di sini...", placeholder="Ketik nama makanan atau minuman...")
            kategori_pilih = st.radio(
                "Kategori:",
                ["Semua", "Makanan", "Minuman", "Snack"],
                horizontal=True,
                label_visibility="collapsed",
            )
            st.divider()

            produk_tampil = [
                p for p in PRODUK_FNB
                if (kategori_pilih == "Semua" or p["kategori"] == kategori_pilih)
                and (cari_produk.lower() in p["nama"].lower())
            ]

            cols_per_row = 4
            for i in range(0, len(produk_tampil), cols_per_row):
                row_cols = st.columns(cols_per_row)
                for j in range(cols_per_row):
                    if i + j < len(produk_tampil):
                        item = produk_tampil[i + j]
                        with row_cols[j]:
                            st.markdown(
                                f"""
                                <div class="product-box">
                                    <div class="product-emoji">{item['ikon']}</div>
                                    <div class="product-name">{item['nama']}</div>
                                    <div class="product-price">Rp {item['harga']:,.0f}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                            if st.button("+ Tambah", key=f"add_{item['nama']}", use_container_width=True):
                                st.session_state.keranjang[item["nama"]] = (
                                    st.session_state.keranjang.get(item["nama"], 0) + 1
                                )
                                st.rerun()

# ==========================================================
# HALAMAN 2: KAS KECIL (MASUK & KELUAR)
# ==========================================================
elif menu_aktif == "💸 Kas Kecil (Masuk/Keluar)":
    st.subheader("💸 Siklus Kas Kecil (Petty Cash Management)")
    with st.container(border=True):
        jenis_transaksi = st.radio(
            "Pilih Jenis Mutasi Kas Kecil:",
            ["Pengeluaran Kas Kecil (Keluar)", "Pengisian Dana Kas Kecil (Masuk)"],
            horizontal=True,
        )
        st.divider()

        with st.form("form_kas_kecil", clear_on_submit=True):
            if "Masuk" in jenis_transaksi:
                keterangan = st.text_input("Keterangan (Contoh: Pengisian Saldo Awal Kas Kecil)")
                akun_lawan = st.selectbox("Sumber Dana (Kredit):", ["Kas Besar / Brankas", "Bank BCA"])
            else:
                keterangan = st.text_input("Keterangan Pengeluaran (Contoh: Beli Es Batu, Galon Air)")
                akun_lawan = st.selectbox(
                    "Kategori Beban (Debit):",
                    ["Beban Bahan Penolong Dapur", "Beban Perlengkapan Toko", "Beban Transportasi & Kurir", "Beban Lain-lain"],
                )

            nominal = st.number_input("Nominal (Rp):", min_value=1000, step=5000)
            pj = st.text_input("Nama Penanggung Jawab:")
            st.divider()

            if st.form_submit_button("Simpan Mutasi Kas Kecil"):
                if keterangan and pj:
                    waktu_skrg = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    tipe = "Masuk" if "Masuk" in jenis_transaksi else "Keluar"
                    c.execute(
                        """INSERT INTO kas_kecil (waktu, jenis, keterangan, akun_lawan, jumlah, penanggung_jawab)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (waktu_skrg, tipe, keterangan, akun_lawan, nominal, pj),
                    )
                    conn.commit()
                    st.success(f"✅ Transaksi Kas Kecil ({tipe}) berhasil disimpan!")
                else:
                    st.warning("Lengkapi keterangan dan nama penanggung jawab.")

# ==========================================================
# HALAMAN 3: LAPORAN KAS, JURNAL UMUM & JURNAL KAS KECIL TERPISAH
# ==========================================================
elif menu_aktif == "📊 Laporan Kas & Jurnal":
    st.subheader("📊 Laporan Arus Kas & Jurnal Akuntansi")

    df_penjualan = pd.read_sql_query("SELECT * FROM penjualan", conn)
    df_kas_kecil = pd.read_sql_query("SELECT * FROM kas_kecil", conn)

    kas_masuk_tunai = df_penjualan[df_penjualan["metode"] == "Cash"]["total_harga"].sum() if not df_penjualan.empty else 0
    kas_masuk_qris = df_penjualan[df_penjualan["metode"] == "QRIS"]["total_harga"].sum() if not df_penjualan.empty else 0
    kk_masuk = df_kas_kecil[df_kas_kecil["jenis"] == "Masuk"]["jumlah"].sum() if not df_kas_kecil.empty else 0
    kk_keluar = df_kas_kecil[df_kas_kecil["jenis"] == "Keluar"]["jumlah"].sum() if not df_kas_kecil.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Kas Laci Penjualan (Cash)", f"Rp {saldo_awal_kas + kas_masuk_tunai:,.0f}")
    c2.metric("Rekening Bank / QRIS", f"Rp {kas_masuk_qris:,.0f}")
    c3.metric("Dana Kas Kecil Masuk", f"Rp {kk_masuk:,.0f}")
    c4.metric("Sisa Saldo Kas Kecil", f"Rp {kk_masuk - kk_keluar:,.0f}")

    st.write("")

    # --- MENYIAPKAN DATA BUKU KAS ---
    mutasi_kas = [
        {
            "tipe_db": "awal",
            "id_db": None,
            "Waktu": "Awal Shift",
            "No. Bukti": "OPEN-00",
            "Pos Kas": "Kas Laci Kasir",
            "Keterangan": "Saldo Awal Modal Kasir",
            "Pemasukan (Debit)": saldo_awal_kas,
            "Pengeluaran (Kredit)": 0,
        }
    ]
    for _, row in df_penjualan.iterrows():
        mutasi_kas.append(
            {
                "tipe_db": "penjualan",
                "id_db": row["id"],
                "Waktu": row["waktu"],
                "No. Bukti": row["no_faktur"],
                "Pos Kas": "Kas Laci Kasir" if row["metode"] == "Cash" else "Bank / QRIS",
                "Keterangan": f"Penjualan {row['item']} ({row['jumlah']}x)",
                "Pemasukan (Debit)": row["total_harga"],
                "Pengeluaran (Kredit)": 0,
            }
        )
    for _, row in df_kas_kecil.iterrows():
        is_masuk = row["jenis"] == "Masuk"
        mutasi_kas.append(
            {
                "tipe_db": "kas_kecil",
                "id_db": row["id"],
                "Waktu": row["waktu"],
                "No. Bukti": f"PC-{row['id']:03d}",
                "Pos Kas": "Kas Kecil",
                "Keterangan": f"[{row['jenis'].upper()}] {row['keterangan']} ({row['penanggung_jawab']})",
                "Pemasukan (Debit)": row["jumlah"] if is_masuk else 0,
                "Pengeluaran (Kredit)": 0 if is_masuk else row["jumlah"],
            }
        )

    df_kas = pd.DataFrame(mutasi_kas)
    df_kas["Saldo Kumulatif"] = (df_kas["Pemasukan (Debit)"] - df_kas["Pengeluaran (Kredit)"]).cumsum()
    df_kas_excel = df_kas.drop(columns=["tipe_db", "id_db"])

    # --- 1. JURNAL UMUM KHUSUS PENJUALAN ---
    jurnal_umum_list = []
    for _, row in df_penjualan.iterrows():
        akun_kas = "Kas di Tangan" if row["metode"] == "Cash" else "Bank / Piutang QRIS"
        jurnal_umum_list.extend([
            {"Waktu": row["waktu"], "Ref": row["no_faktur"], "Akun": akun_kas, "Debit": row["total_harga"], "Kredit": 0},
            {"Waktu": "", "Ref": "", "Akun": f"\u00A0\u00A0\u00A0\u00A0Pendapatan Penjualan ({row['item']})", "Debit": 0, "Kredit": row["subtotal"]},
            {"Waktu": "", "Ref": "", "Akun": "\u00A0\u00A0\u00A0\u00A0Utang Pajak Restoran (PB1 10%)", "Debit": 0, "Kredit": row["pajak"]},
        ])
    df_jurnal_umum = (
        pd.DataFrame(jurnal_umum_list)
        if jurnal_umum_list
        else pd.DataFrame(columns=["Waktu", "Ref", "Akun", "Debit", "Kredit"])
    )

    # --- 2. JURNAL KAS KECIL TERPISAH ---
    jurnal_kk_list = []
    for _, row in df_kas_kecil.iterrows():
        if row["jenis"] == "Masuk":
            jurnal_kk_list.extend([
                {
                    "Waktu": row["waktu"],
                    "Ref": f"PC-IN-{row['id']:03d}",
                    "PJ": row["penanggung_jawab"],
                    "Akun": f"Kas Kecil ({row['keterangan']})",
                    "Debit": row["jumlah"],
                    "Kredit": 0,
                },
                {
                    "Waktu": "",
                    "Ref": "",
                    "PJ": "",
                    "Akun": f"\u00A0\u00A0\u00A0\u00A0{row['akun_lawan']}",
                    "Debit": 0,
                    "Kredit": row["jumlah"],
                },
            ])
        else:
            jurnal_kk_list.extend([
                {
                    "Waktu": row["waktu"],
                    "Ref": f"PC-OUT-{row['id']:03d}",
                    "PJ": row["penanggung_jawab"],
                    "Akun": f"{row['akun_lawan']} ({row['keterangan']})",
                    "Debit": row["jumlah"],
                    "Kredit": 0,
                },
                {
                    "Waktu": "",
                    "Ref": "",
                    "PJ": "",
                    "Akun": "\u00A0\u00A0\u00A0\u00A0Kas Kecil",
                    "Debit": 0,
                    "Kredit": row["jumlah"],
                },
            ])
    df_jurnal_kk = (
        pd.DataFrame(jurnal_kk_list)
        if jurnal_kk_list
        else pd.DataFrame(columns=["Waktu", "Ref", "PJ", "Akun", "Debit", "Kredit"])
    )

    # --- TOMBOL EXPORT EXCEL (.XLSX) ---
    buffer_excel = io.BytesIO()
    with pd.ExcelWriter(buffer_excel, engine="openpyxl") as writer:
        df_kas_excel.to_excel(writer, sheet_name="Buku_Kas", index=False)
        df_jurnal_umum.to_excel(writer, sheet_name="Jurnal_Umum_Penjualan", index=False)
        df_jurnal_kk.to_excel(writer, sheet_name="Jurnal_Kas_Kecil", index=False)
        df_penjualan.to_excel(writer, sheet_name="Rincian_Penjualan", index=False)
        df_kas_kecil.to_excel(writer, sheet_name="Rincian_Kas_Kecil", index=False)

    st.download_button(
        label="📥 Download Laporan Lengkap Format Excel (.xlsx)",
        data=buffer_excel.getvalue(),
        file_name=f"Laporan_SIA_FnB_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    tab1, tab2, tab3 = st.tabs([
        "📒 Laporan Mutasi Kas (Buku Kas)",
        "📖 Jurnal Umum (Penjualan)",
        "🧾 Jurnal Kas Kecil (Petty Cash)",
    ])

    # --- TAB 1: BUKU KAS DENGAN GARIS PEMBATAS TEGAS & TOMBOL HAPUS ---
    with tab1:
        st.caption("Klik tombol **🗑️** di ujung kanan baris apabila ingin membatalkan/menghapus transaksi tertentu.")
        with st.container(border=True):
            h_cols = st.columns([1.8, 1.2, 1.3, 2.7, 1.3, 1.3, 1.4, 0.7])
            headers = ["Waktu", "No. Bukti", "Pos Kas", "Keterangan", "Pemasukan", "Pengeluaran", "Saldo", "Aksi"]
            for col, text in zip(h_cols, headers):
                col.markdown(f"**{text}**")
            st.divider()

            for idx, r in df_kas.iterrows():
                row_cols = st.columns([1.8, 1.2, 1.3, 2.7, 1.3, 1.3, 1.4, 0.7])
                row_cols[0].write(r["Waktu"])
                row_cols[1].write(r["No. Bukti"])
                row_cols[2].write(r["Pos Kas"])
                row_cols[3].write(r["Keterangan"])
                row_cols[4].write(f"Rp {r['Pemasukan (Debit)']:,.0f}")
                row_cols[5].write(f"Rp {r['Pengeluaran (Kredit)']:,.0f}")
                row_cols[6].markdown(f"**Rp {r['Saldo Kumulatif']:,.0f}**")

                if r["tipe_db"] == "awal":
                    row_cols[7].markdown("<div style='padding-top:6px; opacity:0.6;'>🔒</div>", unsafe_allow_html=True)
                else:
                    if row_cols[7].button("🗑️", key=f"del_{r['tipe_db']}_{r['id_db']}", help="Batalkan / hapus transaksi ini"):
                        if r["tipe_db"] == "penjualan":
                            c.execute("DELETE FROM penjualan WHERE id = ?", (r["id_db"],))
                        elif r["tipe_db"] == "kas_kecil":
                            c.execute("DELETE FROM kas_kecil WHERE id = ?", (r["id_db"],))
                        conn.commit()
                        st.toast(f"Transaksi {r['No. Bukti']} berhasil dihapus!", icon="🗑️")
                        st.rerun()

                if idx < len(df_kas) - 1:
                    st.markdown(f"<hr style='margin: 6px 0; border-top: 1.5px solid {warna_border} !important;'>", unsafe_allow_html=True)

    # --- TAB 2: JURNAL UMUM KHUSUS PENJUALAN (TABEL BERGARIS TEGAS) ---
    with tab2:
        st.markdown("#### 📖 Jurnal Umum — Siklus Pendapatan (Penjualan)")
        if not df_jurnal_umum.empty:
            tot_d, tot_k = df_jurnal_umum["Debit"].sum(), df_jurnal_umum["Kredit"].sum()
            df_ju_tampil = df_jurnal_umum.copy()
            df_ju_tampil["Debit"] = df_ju_tampil["Debit"].apply(lambda x: f"Rp {x:,.0f}" if x > 0 else "-")
            df_ju_tampil["Kredit"] = df_ju_tampil["Kredit"].apply(lambda x: f"Rp {x:,.0f}" if x > 0 else "-")
            st.markdown(df_ju_tampil.to_html(index=False, classes="jurnal-table"), unsafe_allow_html=True)
            st.write("")
            if tot_d == tot_k:
                st.success(f"✅ JURNAL UMUM BALANCE: Total Debit (Rp {tot_d:,.0f}) = Total Kredit (Rp {tot_k:,.0f})")
        else:
            st.info("Belum ada transaksi penjualan yang tercatat pada Jurnal Umum.")

    # --- TAB 3: JURNAL KAS KECIL TERPISAH (TABEL BERGARIS TEGAS) ---
    with tab3:
        st.markdown("#### 🧾 Jurnal Kas Kecil (*Petty Cash Journal*)")
        if not df_jurnal_kk.empty:
            tot_d_kk, tot_k_kk = df_jurnal_kk["Debit"].sum(), df_jurnal_kk["Kredit"].sum()
            df_jkk_tampil = df_jurnal_kk.copy()
            df_jkk_tampil["Debit"] = df_jkk_tampil["Debit"].apply(lambda x: f"Rp {x:,.0f}" if x > 0 else "-")
            df_jkk_tampil["Kredit"] = df_jkk_tampil["Kredit"].apply(lambda x: f"Rp {x:,.0f}" if x > 0 else "-")
            st.markdown(df_jkk_tampil.to_html(index=False, classes="jurnal-table"), unsafe_allow_html=True)
            st.write("")
            if tot_d_kk == tot_k_kk:
                st.success(f"✅ JURNAL KAS KECIL BALANCE: Total Debit (Rp {tot_d_kk:,.0f}) = Total Kredit (Rp {tot_k_kk:,.0f})")
        else:
            st.info("Belum ada mutasi kas kecil (pengisian maupun pengeluaran) yang tercatat.")
