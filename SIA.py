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
                p for p in PRODUK_FNB
                if (kategori_pilih == "Semua" or p["kategori"] == kategori_pilih)
                and (cari_produk.lower() in p["nama"].lower())
            ]

            st.write("")
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

            if st.form_submit_button("Simpan Mutasi Kas Kecil", type="primary"):
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
# HALAMAN 3: LAPORAN KAS, JURNAL & PEMBATALAN SATUAN
# ==========================================================
elif menu_aktif == "📊 Laporan Kas & Jurnal":
    st.subheader("📊 Laporan Arus Kas & Jurnal Umum Otomatis")

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

    # --- MENYIAPKAN DATA BUKU KAS ---
    mutasi_kas = [
        {
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

    # --- MENYIAPKAN DATA JURNAL UMUM ---
    jurnal = []
    for _, row in df_penjualan.iterrows():
        akun_kas = "Kas di Tangan" if row["metode"] == "Cash" else "Bank / Piutang QRIS"
        jurnal.extend([
            {"Waktu": row["waktu"], "Ref": row["no_faktur"], "Akun": akun_kas, "Debit": row["total_harga"], "Kredit": 0},
            {"Waktu": "", "Ref": "", "Akun": f"    Pendapatan Penjualan ({row['item']})", "Debit": 0, "Kredit": row["subtotal"]},
            {"Waktu": "", "Ref": "", "Akun": "    Utang Pajak Restoran (PB1 10%)", "Debit": 0, "Kredit": row["pajak"]},
        ])
    for _, row in df_kas_kecil.iterrows():
        if row["jenis"] == "Masuk":
            jurnal.extend([
                {"Waktu": row["waktu"], "Ref": f"PC-IN-{row['id']:03d}", "Akun": f"Kas Kecil ({row['keterangan']})", "Debit": row["jumlah"], "Kredit": 0},
                {"Waktu": "", "Ref": "", "Akun": f"    {row['akun_lawan']}", "Debit": 0, "Kredit": row["jumlah"]},
            ])
        else:
            jurnal.extend([
                {"Waktu": row["waktu"], "Ref": f"PC-OUT-{row['id']:03d}", "Akun": f"{row['akun_lawan']} ({row['keterangan']})", "Debit": row["jumlah"], "Kredit": 0},
                {"Waktu": "", "Ref": "", "Akun": "    Kas Kecil", "Debit": 0, "Kredit": row["jumlah"]},
            ])

    df_j = pd.DataFrame(jurnal) if jurnal else pd.DataFrame(columns=["Waktu", "Ref", "Akun", "Debit", "Kredit"])

    # --- TOMBOL EXPORT EXCEL (.XLSX) MULTI-SHEET ---
    buffer_excel = io.BytesIO()
    with pd.ExcelWriter(buffer_excel, engine="openpyxl") as writer:
        df_kas.to_excel(writer, sheet_name="Buku_Kas", index=False)
        df_j.to_excel(writer, sheet_name="Jurnal_Umum", index=False)
        df_penjualan.to_excel(writer, sheet_name="Rincian_Penjualan", index=False)
        df_kas_kecil.to_excel(writer, sheet_name="Rincian_Kas_Kecil", index=False)

    st.download_button(
        label="📥 Download Laporan Lengkap Format Excel (.xlsx)",
        data=buffer_excel.getvalue(),
        file_name=f"Laporan_SIA_FnB_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )

    tab1, tab2, tab3 = st.tabs([
        "📒 Laporan Mutasi Kas (Buku Kas)",
        "📖 Jurnal Umum Otomatis",
        "🗑️ Pembatalan / Hapus 1 Transaksi",
    ])

    with tab1:
        df_tampil = df_kas.copy()
        for col in ["Pemasukan (Debit)", "Pengeluaran (Kredit)", "Saldo Kumulatif"]:
            df_tampil[col] = df_tampil[col].apply(lambda x: f"Rp {x:,.0f}")
        st.dataframe(df_tampil, use_container_width=True, hide_index=True)

    with tab2:
        if not df_j.empty:
            tot_d, tot_k = df_j["Debit"].sum(), df_j["Kredit"].sum()
            df_j_tampil = df_j.copy()
            df_j_tampil["Debit"] = df_j_tampil["Debit"].apply(lambda x: f"Rp {x:,.0f}" if x > 0 else "-")
            df_j_tampil["Kredit"] = df_j_tampil["Kredit"].apply(lambda x: f"Rp {x:,.0f}" if x > 0 else "-")
            st.table(df_j_tampil)
            if tot_d == tot_k:
                st.success(f"✅ JURNAL BALANCE: Total Debit (Rp {tot_d:,.0f}) = Total Kredit (Rp {tot_k:,.0f})")
        else:
            st.info("Belum ada transaksi tercatat.")

    # --- TAB 3: HAPUS / BATALKAN 1 TRANSAKSI (VOID) ---
    with tab3:
        st.markdown("#### 🚫 Pembatalan Transaksi Satuan (*Void / Correction*)")
        st.info(
            "Gunakan fitur ini apabila pelanggan membatalkan pesanan atau terjadi kesalahan input pada satu transaksi tertentu. "
            "Saldo kas dan Jurnal Umum akan otomatis disesuaikan kembali."
        )

        col_batal_jual, col_batal_kk = st.columns(2)

        # Kolom Kiri: Pembatalan Penjualan (Per Faktur)
        with col_batal_jual:
            with st.container(border=True):
                st.markdown("**1. Batalkan Transaksi Penjualan (Kasir)**")
                if not df_penjualan.empty:
                    # Kelompokkan per No. Faktur
                    ringkasan_faktur = (
                        df_penjualan.groupby(["no_faktur", "waktu", "metode"], as_index=False)
                        .agg(
                            daftar_item=("item", lambda x: ", ".join(x)),
                            total_tagihan=("total_harga", "sum"),
                        )
                        .sort_values(by="waktu", ascending=False)
                    )

                    opsi_faktur = {
                        f"{r['no_faktur']} | {r['daftar_item']} (Rp {r['total_tagihan']:,.0f} - {r['metode']})": r["no_faktur"]
                        for _, r in ringkasan_faktur.iterrows()
                    }

                    pilihan_faktur_label = st.selectbox(
                        "Pilih Nomor Faktur yang Dibatalkan:",
                        list(opsi_faktur.keys()),
                        key="pilih_hapus_faktur",
                    )
                    faktur_terpilih = opsi_faktur[pilihan_faktur_label]

                    # Tampilkan detail item di faktur tersebut
                    detail_hapus = df_penjualan[df_penjualan["no_faktur"] == faktur_terpilih][
                        ["item", "jumlah", "total_harga", "metode"]
                    ]
                    st.dataframe(detail_hapus, use_container_width=True, hide_index=True)

                    if st.button(f"🗑️ Batalkan Faktur {faktur_terpilih}", type="secondary", use_container_width=True):
                        c.execute("DELETE FROM penjualan WHERE no_faktur = ?", (faktur_terpilih,))
                        conn.commit()
                        if (
                            st.session_state.struk_terakhir
                            and st.session_state.struk_terakhir["no_faktur"] == faktur_terpilih
                        ):
                            st.session_state.struk_terakhir = None
                        st.success(f"✅ Faktur **{faktur_terpilih}** berhasil dibatalkan dan dihapus dari jurnal!")
                        st.rerun()
                else:
                    st.caption("Tidak ada transaksi penjualan yang dapat dibatalkan.")

        # Kolom Kanan: Pembatalan Mutasi Kas Kecil (Per ID)
        with col_batal_kk:
            with st.container(border=True):
                st.markdown("**2. Batalkan Mutasi Kas Kecil**")
                if not df_kas_kecil.empty:
                    df_kk_urut = df_kas_kecil.sort_values(by="id", ascending=False)
                    opsi_kk = {
                        f"PC-{r['id']:03d} | [{r['jenis']}] {r['keterangan']} (Rp {r['jumlah']:,.0f})": r["id"]
                        for _, r in df_kk_urut.iterrows()
                    }

                    pilihan_kk_label = st.selectbox(
                        "Pilih Transaksi Kas Kecil yang Dibatalkan:",
                        list(opsi_kk.keys()),
                        key="pilih_hapus_kk",
                    )
                    id_kk_terpilih = opsi_kk[pilihan_kk_label]

                    detail_kk = df_kas_kecil[df_kas_kecil["id"] == id_kk_terpilih][
                        ["waktu", "jenis", "keterangan", "jumlah", "penanggung_jawab"]
                    ]
                    st.dataframe(detail_kk, use_container_width=True, hide_index=True)

                    if st.button(f"🗑️ Hapus Mutasi PC-{id_kk_terpilih:03d}", type="secondary", use_container_width=True):
                        c.execute("DELETE FROM kas_kecil WHERE id = ?", (id_kk_terpilih,))
                        conn.commit()
                        st.success(f"✅ Transaksi Kas Kecil **PC-{id_kk_terpilih:03d}** berhasil dihapus!")
                        st.rerun()
                else:
                    st.caption("Tidak ada mutasi kas kecil yang dapat dihapus.")
