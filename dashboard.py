# Import library json untuk melakukan encoding dictionary Python ke bentuk JSON Text
import json
# Import Blueprint untuk rute, dan render_template untuk me-render HTML dari Flask
from flask import Blueprint, render_template
# Import fungsi load (baca database), login_required (pelindung rute), format_rupiah (mengubah angka ke Rp) dari utils.py
from utils import load, login_required, format_rupiah

# Membuat instance Blueprint untuk memisahkan bagian kode yang mengurus logika Dashboard
dashboard_bp = Blueprint('dashboard', __name__)

# Menentukan alamat rute (URL) '/dashboard'
@dashboard_bp.route('/dashboard')
# Mengaplikasikan decorator login_required agar halaman ini hanya bisa dibuka oleh pengguna yang sudah login
@login_required
def dashboard():
    # Memuat seluruh data (list of dictionaries) dari tabel Master Barang (inventory)
    inventory = load('inventory')
    # Memuat seluruh riwayat data transaksi Barang Masuk dari file JSON
    barang_masuk = load('barang_masuk')
    # Memuat seluruh riwayat data transaksi Barang Keluar dari file JSON
    barang_keluar = load('barang_keluar')

    # Menghitung Total Jenis Barang. Dilakukan dengan membuat Set kode barang (yang tidak duplikat),
    # lalu menghitung panjang set (len) tersebut.
    total_jenis = len(set(i['code'] for i in inventory))
    
    # Menghitung Total Stok Barang. Menjumlahkan seluruh key 'stock' pada list inventory (nilai default 0 jika kosong).
    total_stok = sum(i.get('stock', 0) for i in inventory)
    
    # Menghitung Total Transaksi Barang Masuk. Menjumlahkan setiap kuantitas dari riwayat barang_masuk.
    total_masuk = sum(i.get('quantity', 0) for i in barang_masuk)
    
    # Menghitung Total Transaksi Barang Keluar. Menjumlahkan setiap kuantitas dari riwayat barang_keluar.
    total_keluar = sum(i.get('quantity', 0) for i in barang_keluar)

    # Menghitung Total Nilai Beli barang. Nilainya dihitung dari: Kuantitas barang_masuk dikalikan Harga Beli per barang_masuk.
    total_nilai_beli = sum(i.get('quantity', 0) * i.get('buyPrice', 0) for i in barang_masuk)
    
    # Menghitung Total Nilai Jual (Omset) barang. Nilainya dihitung dari: Kuantitas barang_keluar dikalikan Harga Jual per barang_keluar.
    total_nilai_jual = sum(i.get('quantity', 0) * i.get('sellPrice', 0) for i in barang_keluar)
    
    # Menghitung Keuntungan Kasar, yang didapat dengan mengurangi total uang penjualan dengan total modal pembelian.
    total_keuntungan = total_nilai_jual - total_nilai_beli

    # Mengembalikan (me-render) file dashboard.html dan sekaligus mengirimkan semua variabel
    # perhitungan di atas ke dalam HTML agar dapat ditampilkan (dikonsumsi Jinja2).
    return render_template('dashboard.html',
                           total_jenis=total_jenis,
                           total_stok=total_stok,
                           total_masuk=total_masuk,
                           total_keluar=total_keluar,
                           # Menerapkan fungsi format_rupiah() untuk nominal uang agar tampil cantik dengan pemisah koma/titik.
                           total_nilai_beli=format_rupiah(total_nilai_beli),
                           total_nilai_jual=format_rupiah(total_nilai_jual),
                           total_keuntungan=format_rupiah(total_keuntungan),
                           # Mengirim data array inventaris dengan format JSON.dumps agar bisa langsung dibaca oleh Javascript di Frontend (HTML)
                           inventory_data=json.dumps(inventory),
                           # Mengirim data array riwayat masuk
                           masuk_data=json.dumps(barang_masuk),
                           # Mengirim data array riwayat keluar
                           keluar_data=json.dumps(barang_keluar))
