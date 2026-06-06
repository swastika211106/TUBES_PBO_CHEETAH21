# Import Blueprint, render_template (untuk merender file html), request (mengambil data json dari body form API), 
# dan jsonify (untuk mengubah output tipe data Python ke format API JSON response)
from flask import Blueprint, render_template, request, jsonify
# Import utilitas untuk mengelola file json, ID otomatis, dan authentikasi sesi admin
from utils import load, save, next_id, login_required

# Membuat blueprint inventory untuk mengurus seluruh path/rute URL /master-barang dan /kategori-barang
inventory_bp = Blueprint('inventory', __name__)

# ─────────────────────────────────────────────
# BAGIAN MASTER BARANG
# ─────────────────────────────────────────────

# Rute URL untuk menampilkan halaman antar muka (UI/HTML) Master Barang
@inventory_bp.route('/master-barang')
@login_required # Memastikan user sudah login
def master_barang():
    # Menampilkan file master_barang.html ke pengguna
    return render_template('master_barang.html')

# Rute URL API untuk GET (Membaca/Mengambil List) Master Barang
@inventory_bp.route('/api/inventory', methods=['GET'])
@login_required
def api_inventory_list():
    # Mengambil list dictionary dari file inventory.json
    items = load('inventory')
    # Mengambil parameter query string 'q' (pencarian), diubah ke string huruf kecil (.lower())
    q = request.args.get('q', '').lower()
    
    # Jika parameter 'q' dikirimkan dari frontend (pengguna melakukan pencarian)
    if q:
        # Melakukan list comprehension untuk memfilter daftar barang yang cocok.
        # Mencocokkan teks 'q' di kode barang, di nama barang, ATAU di kategori barang
        items = [i for i in items if q in i.get('code','').lower() or q in i.get('name','').lower() or q in i.get('category','').lower()]
    
    # Mengembalikan hasil (bisa saja semua, bisa juga yg telah disaring) dalam bentuk Response JSON API
    return jsonify(items)

# Rute URL API untuk POST (Menambah Data Baru) Master Barang
@inventory_bp.route('/api/inventory', methods=['POST'])
@login_required
def api_inventory_add():
    # Memuat inventory dari file
    items = load('inventory')
    # Menangkap payload body JSON request yang dikirimkan oleh JS Frontend
    data = request.json
    
    # Membuat daftar list semua kode barang yang sudah dipakai saat ini
    codes = [i['code'] for i in items]
    
    # Jika pada data payload tidak disediakan 'code' barang secara spesifik oleh frontend
    if not data.get('code'):
        # Menghitung panjang array barang + 1
        n = len(items) + 1
        # Membuat format kode barang baru, contoh: BRG001, BRG002, dst. (3 digit trailing zero)
        data['code'] = f"BRG{n:03d}"
        # Jika kode yg di-generate masih bertabrakan / sudah ada, looping dan tambah n+1 hingga dapat kode unik
        while data['code'] in codes:
            n += 1
            data['code'] = f"BRG{n:03d}"
            
    # Membuat ID internal unik menggunakan fungsi next_id()
    data['id'] = next_id(items)
    # Mengambil value dari request 'stock' lalu dipaksa konversi tipe ke integer agar konsisten (default 0)
    data['stock'] = int(data.get('stock', 0))
    # Konversi Harga Beli ke nilai pecahan / desimal float (default 0)
    data['buyPrice'] = float(data.get('buyPrice', 0))
    # Konversi Harga Jual ke float
    data['sellPrice'] = float(data.get('sellPrice', 0))
    
    # Menambahkan data barang yang baru di-parsing ini ke array list
    items.append(data)
    # Timpa dan simpan ulang file JSON dengan tambahan barang ini
    save('inventory', items)
    
    # Mengembalikan response sukses ke frontend lengkap beserta info kode barang barunya
    return jsonify({'success': True, 'code': data['code']})

# Rute URL API untuk PUT (Memperbarui Data Berdasarkan ID) Master Barang
@inventory_bp.route('/api/inventory/<int:item_id>', methods=['PUT'])
@login_required
def api_inventory_update(item_id):
    # Memuat seluruh inventory
    items = load('inventory')
    # Mengambil payload body update JSON dari frontend
    data = request.json
    
    # Melakukan perulangan iterasi terhadap index (i) dan dictionary item di dalam list items
    for i, item in enumerate(items):
        # Jika menemukan item di loop yang ID-nya cocok dengan item_id dari URL Endpoint API
        if item['id'] == item_id:
            # Melakukan penggabungan/timpa dictionary: properties lama dengan properties data baru, 
            # lalu pastikan ID tidak berubah
            items[i] = {**item, **data, 'id': item_id}
            # Paksa tipe data integer dan float agar tipe di JSON tetap valid dan tidak menjadi String
            items[i]['stock'] = int(items[i].get('stock', 0))
            items[i]['buyPrice'] = float(items[i].get('buyPrice', 0))
            items[i]['sellPrice'] = float(items[i].get('sellPrice', 0))
            
            # Simpan perubahan ini ke JSON
            save('inventory', items)
            # Karena item berhasil diupdate, kembalikan status success True ke Javascript client
            return jsonify({'success': True})
            
    # Jika selesai looping tetapi ID tak ditemukan, kembalikan response gagal dengan pesan peringatan
    return jsonify({'success': False, 'message': 'Item tidak ditemukan'})

# Rute URL API untuk DELETE (Menghapus Data Berdasarkan ID) Master Barang
@inventory_bp.route('/api/inventory/<int:item_id>', methods=['DELETE'])
@login_required
def api_inventory_delete(item_id):
    # Membaca seluruh database Master Barang
    items = load('inventory')
    
    # Memfilter array items dan hanya menyisakan item yang nilai ID-nya TIDAK SAMA dengan item_id (alias hapus yang sama)
    items = [i for i in items if i['id'] != item_id]
    
    # Simpan kembali array yang sudah difilter tadi (yang sudah tidak mengandung item terkait)
    save('inventory', items)
    # Kembalikan penanda sukses
    return jsonify({'success': True})

# ─────────────────────────────────────────────
# BAGIAN KATEGORI BARANG
# (Logikanya hampir sama persis dengan Master Barang di atas, perbedaan utamanya hanya target databasenya 'kategori.json')
# ─────────────────────────────────────────────

# Rute UI Kategori Barang
@inventory_bp.route('/kategori-barang')
@login_required
def kategori_barang():
    # Merender file UI kategori_barang.html
    return render_template('kategori_barang.html')

# Rute API Ambil Data (GET) Kategori Barang
@inventory_bp.route('/api/kategori', methods=['GET'])
@login_required
def api_kategori_list():
    items = load('kategori')
    q = request.args.get('q', '').lower()
    if q:
        # Filter data jika field kategoriId atau name (nama kategori) mengandung string yg diketik pencari
        items = [i for i in items if q in i.get('kategoriId','').lower() or q in i.get('name','').lower()]
    return jsonify(items)

# Rute API Menambahkan (POST) Kategori Barang
@inventory_bp.route('/api/kategori', methods=['POST'])
@login_required
def api_kategori_add():
    items = load('kategori')
    data = request.json
    
    # Logika pembuatan ID Auto-Generate format KTG001
    if not data.get('kategoriId'):
        n = len(items) + 1
        ids = [i['kategoriId'] for i in items]
        data['kategoriId'] = f"KTG{n:03d}"
        while data['kategoriId'] in ids:
            n += 1
            data['kategoriId'] = f"KTG{n:03d}"
            
    # Berikan Primary key id auto-increment
    data['id'] = next_id(items)
    # Masukkan data ke array list memory
    items.append(data)
    # Tulis hasil array ke storage file JSON
    save('kategori', items)
    return jsonify({'success': True, 'kategoriId': data['kategoriId']})

# Rute API Perbarui (PUT) Kategori Barang berdasarkan ID
@inventory_bp.route('/api/kategori/<int:item_id>', methods=['PUT'])
@login_required
def api_kategori_update(item_id):
    items = load('kategori')
    data = request.json
    for i, item in enumerate(items):
        if item['id'] == item_id:
            # Lakukan overwrite dict element item lama dengan yang baru (merge)
            items[i] = {**item, **data, 'id': item_id}
            # Commit / simpan di database file json
            save('kategori', items)
            return jsonify({'success': True})
    return jsonify({'success': False})

# Rute API Hapus (DELETE) Kategori Barang berdasarkan ID
@inventory_bp.route('/api/kategori/<int:item_id>', methods=['DELETE'])
@login_required
def api_kategori_delete(item_id):
    items = load('kategori')
    # Menggunakan metode list comprehension untuk re-construct array tanpa item yang di-hapus
    items = [i for i in items if i['id'] != item_id]
    save('kategori', items)
    return jsonify({'success': True})
