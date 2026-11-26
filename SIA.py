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

            st.write("")
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

                baris_item_html = ""
                baris_item_txt = ""
                for it in s["items"]:
                    baris_item_html += f"""
                    <tr>
                        <td style="padding:2px 0;">{it['nama']}<br><small>{it['qty']} x Rp {it['harga']:,.0f}</small></td>
                        <td style="text-align:right; vertical-align:bottom;">Rp {it['subtotal']:,.0f}</td>
                    </tr>
                    """
                    baris_item_txt += f"{it['nama']} ({it['qty']}x @ {it['harga']:,.0f}) = Rp {it['subtotal']:,.0f}\n"

                html_struk = f"""
                <div id="area-struk" style="font-family: 'Courier New', monospace; background:#FFFDF7; padding:14px; border:1px dashed #9CA3AF; border-radius:6px; color:#111827; font-size:12px;">
                    <div style="text-align:center; font-weight:bold; font-size:14px;">KEDAI KOPI & RESTO MAHASISWA</div>
                    <div style="text-align:center; font-size:11px; margin-bottom:8px;">Sistem Informasi Akuntansi FnB</div>
                    <div style="border-top:1px dashed #9CA3AF; margin:6px 0;"></div>
                    <div>No. Faktur : {s['no_faktur']}</div>
                    <div>Waktu      : {s['waktu']}</div>
                    <div>Pembayaran : {s['metode']}</div>
                    <div style="border-top:1px dashed #9CA3AF; margin:6px 0;"></div>
                    <table style="width:100%; border-collapse:collapse; font-size:12px;">
                        {baris_item_html}
                    </table>
                    <div style="border-top:1px dashed #9CA3AF; margin:6px 0;"></div>
                    <table style="width:100%; font-size:12px;">
                        <tr><td>Subtotal (DPP)</td><td style="text-align:right;">Rp {s['subtotal']:,.0f}</td></tr>
                        <tr><td>Pajak PB1 (10%)</td><td style="text-align:right;">Rp {s['pajak']:,.0f}</td></tr>
                        <tr style="font-weight:bold; font-size:13px;"><td>TOTAL BAYAR</td><td style="text-align:right;">Rp {s['total']:,.0f}</td></tr>
                    </table>
                    <div style="border-top:1px dashed #9CA3AF; margin:8px 0;"></div>
                    <div style="text-align:center; font-size:11px;">Terima Kasih Atas Kunjungan Anda!</div>
                </div>
                <button onclick="printStruk()" style="margin-top:8px; width:100%; background:#2563EB; color:white; border:none; padding:8px; border-radius:6px; font-weight:bold; cursor:pointer;">
                    🖨️ Cetak Struk / Simpan PDF
                </button>
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
                components.html(html_struk, height=340, scrolling=True)

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

            produk_tampil = [
                p for p in PRODUK_F
