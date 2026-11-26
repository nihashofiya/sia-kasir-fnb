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

# --- CUSTOM CSS (DESAIN MODERN ALA NUTAPOS: PUTIH & HIJAU) ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #F4F6F9;
    }
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E5E7EB;
    }
    .total-display {
        background-color: #FFFFFF;
        border: 2px solid #E5E7EB;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        font-size: 32px;
        font-weight: 800;
        color: #1F2937;
        margin-bottom: 15px;
    }
    .product-box {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 12px 8px;
        text-align: center;
        margin-bottom: 8px;
        transition: all 0.2s;
    }
    .product-box:hover {
        border-color: #22C55E;
        box-shadow: 0 4px 8px rgba(34, 197, 94, 0.12);
    }
    .product-emoji {
        font-size: 36px;
        margin-bottom: 4px;
    }
    .product-name {
        font-weight: 600;
        font-size: 13px;
        color: #111827;
        margin-bottom: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .product-price {
        font-size: 12px;
        color: #6B7280;
        font-weight: 500;
    }
    div.stButton > button[kind="primary"] {
        background-color: #28A745;
        border-color: #28A745;
        color: white;
        font-weight: 600;
        border-radius: 8px;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #218838;
        border-color: #1E7E34;
    }
    </style>
    """,
    unsafe_allow_html=True,
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
    {"nama": "Black Burger", "harga": 40000, "kategori": "Makanan", "ikon": "🍔"},
    {"nama": "Mexican Burger", "harga": 45000, "kategori": "Makanan", "ikon": "🌮"},
    {"nama": "Ham Sandwich", "harga": 35000, "kategori": "Makanan", "ikon": "🥪"},
    {"nama": "Nasi Ayam Geprek", "harga": 25000, "kategori": "Makanan", "ikon": "🍗"},
    {"nama": "French Fries", "harga": 20000, "kategori": "Snack", "ikon": "🍟"},
    {"nama": "Croissant Butter", "harga": 22000, "kategori": "Snack", "ikon": "🥐"},
    {"nama": "Kopi Susu Aren", "harga": 18000, "kategori": "Minuman", "ikon": "🧋"},
    {"nama": "Americano Ice", "harga": 15000, "kategori": "Minuman", "ikon": "☕"},
    {"nama": "Matcha Latte", "harga": 24000, "kategori": "Minuman", "ikon": "🍵"},
    {"nama": "Fanta Strawberry", "harga": 12000, "kategori": "Minuman", "ikon": "🥤"},
    {"nama": "Fanta Orange", "harga": 12000, "kategori": "Minuman", "ikon": "🧃"},
    {"nama": "Es Teh Manis", "harga": 8000, "kategori": "Minuman", "ikon": "🧊"},
]

# --- SESSION STATE ---
if "keranjang" not in st.session_state:
    st.session_state.keranjang = {}
if "struk_terakhir" not in st.session_state:
    st.session_state.struk_terakhir = None

# --- SIDEBAR NAVIGASI ---
st.sidebar.markdown(
    "<h2 style='color:#28A745; margin-bottom:0;'>🟢 SIA-POS FnB</h2>"
    "<p style='color:#6B7280; font-size:12px;'>Sistem Informasi Akuntansi</p>",
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
        """
        <div style="background:#FFFFFF; padding:10px 18px; border-radius:10px; border:1px solid #E5E7EB; margin-bottom:15px; display:flex; justify-content:space-between; align-items:center;">
            <span style="color:#28A745; font-weight:700; font-size:14px;">● Online — Shift Pagi</span>
            <span style="color:#374151; font-weight:600; font-size:14px;">🏪 Kedai Kopi & Resto Mahasiswa</span>
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
                    c_harga.markdown(f"<div style='text-align:right; padding-top:5px;'>Rp {total_per_item:,.0f}</div>", unsafe
