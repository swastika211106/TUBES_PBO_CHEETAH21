# Import module Flask Blueprint untuk sub-rute, jsonify untuk JSON return payload, Response untuk meng-Handle File Download stream
from flask import Blueprint, jsonify
from flask import Response

# Import Fungsi utilitas read db file dan pelindung Rute Auth Session
from utils import load, login_required

# Import CSV library buatan internal python guna menulis baris data sheet
import csv
# Import io stream memory yang memungkinkan manipulasi/pembuatan file string di RAM tanpa membuat fisik file di harddisk langsung
import io

# Inisialisasi API blueprint
api_bp = Blueprint('api', __name__)

# ─────────────────────────────────────────────
# DROPDOWN DATA API (Untuk Mengisi Select Option di Frontend)
# ─────────────────────────────────────────────
@api_bp.route('/api/dropdown-data')
@login_required
def api_dropdown():
    # Membuat 1 list flat array yg isinya cuma 'nama supplier' saja, diambil iteratif dari load('supplier')
    suppliers = [s['name'] for s in load('supplier')]
    
    # Membuat 1 list flat array nama kategori saja
    categories = [k['name'] for k in load('kategori')]
    
    # Membuat 1 list object (List of Dicts) untuk Items Inventaris. Diperlukan lebih banyak data
    # Seperti stok dan satuan unit, untuk fungsi validasi di form Javascript FrontEnd
    items = [{'code': i['code'], 'name': i['name'], 'category': i.get('category',''), 'stock': i.get('stock', 0), 'unit': i.get('unit','')} for i in load('inventory')]
    
    # Return ketiganya digabung pada 1 payload agar cukup panggil API 1x saja per halaman muat.
    return jsonify({'suppliers': suppliers, 'categories': categories, 'items': items})

# ─────────────────────────────────────────────
# EXPORT DATA KE CSV (PENGGANTI EXCEL AGAR LEBIH RINGAN DAN UNIVERSAL)
# ─────────────────────────────────────────────
@api_bp.route('/api/export/<string:sheet_name>')
@login_required
def api_export(sheet_name):
    # Mapping Dictionary dari Nama Request URL ke Nama File JSON Target di Internal
    # Contoh user meminta "inventory", maka target di load adalah key 'inventory' json table
    key_map = {
        'inventory': 'inventory', 
        'barang-masuk': 'barang_masuk',
        'barang-keluar': 'barang_keluar', 
        'supplier': 'supplier',
        'kategori': 'kategori', 
        'users': 'users',
    }
    
    # Menerjemahkan map parameter url string ke key. Jika tidak diketemukan maka key = None
    key = key_map.get(sheet_name)
    
    # Validasi awal bila URL yang diketik aneh/salah mapping
    if not key:
        return jsonify({'success': False, 'message': 'Sheet tidak ditemukan'})
        
    # Tarik Data dari target key JSON yg valid
    items = load(key)
    
    # Bila tabel JSON masih kosong tak bersisa row sedikit pun
    if not items:
        return jsonify({'success': False, 'message': 'Tidak ada data'})
        
    # Gunakan StringIO buffer untuk menulis / mengkonversi string menjadi file bytes di memori (Virtual File)
    output = io.StringIO()
    
    # Menginisiasi object pembuat CSV (Comma Separated Value).
    # Parameter fieldnames di set menggunakan keys() (Daftar nama kolom Header) diambil otomatis dari Row 1/index[0] Data Items kita
    writer = csv.DictWriter(output, fieldnames=items[0].keys())
    
    # Perintahkan module CSV menulis 1 baris Judul Kolom (Header Tabel) terlebih dahulu
    writer.writeheader()
    
    # Tulis/DUMP semua seluruh sisa object items kedalam bentuk CSV Lines/Rows secara bertahap / sekaligus
    writer.writerows(items)
    
    # Persiapkan Response object Flask untuk mengirim Virtual File ini ke Browser pengguna (Force Download file)
    # mimetype 'text/csv' memberitahu browser bahwa ini adalah file sheet
    # Content-Disposition "attachment;" Memaksa Chrome/Browser otomatis mendownload dengan nama file yg kita custom 
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={"Content-Disposition": f"attachment;filename={sheet_name}.csv"})
