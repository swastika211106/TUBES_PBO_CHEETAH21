# Mengimpor Blueprint untuk sistem modularisasi rute di Flask
# render_template (menampilkan UI HTML), request (menangkap input), jsonify (format output jadi JSON)
from flask import Blueprint, render_template, request, jsonify
# Mengimpor utilitas pembaca/penyimpan data JSON, dan dekorator pengaman rute
from utils import load, save, next_id, login_required

# Inisiasi blueprint supplier_bp
supplier_bp = Blueprint('supplier', __name__)

# Rute URL untuk Halaman Master Supplier (Frontend HTML)
@supplier_bp.route('/supplier')
@login_required # Blokir jika belum login
def supplier():
    # Menjalankan mesin Jinja dan mengembalikan halaman supplier.html ke user browser
    return render_template('supplier.html')

# Endpoint API GET Daftar Supplier
@supplier_bp.route('/api/supplier', methods=['GET'])
@login_required
def api_supplier_list():
    # Membaca data list supplier dari database JSON kita
    items = load('supplier')
    # Mengambil kata kunci query pencarian
    q = request.args.get('q', '').lower()
    # Logika Pencarian:
    if q:
        # Array List akan difilter menggunakan sintaks List Comprehension.
        # Jika nilai ID, nama supplier, Alamat, ATAU Nomor Hp mengandung kata kunci yg dicari, item tsb akan dipertahankan.
        items = [i for i in items if q in i.get('supplierId','').lower() or q in i.get('name','').lower() or q in i.get('address','').lower() or q in i.get('phone','').lower()]
    
    # Kembalikan daftar List hasil filter/semua data dalam format payload JSON API
    return jsonify(items)

# Endpoint API POST Menambah Data Supplier
@supplier_bp.route('/api/supplier', methods=['POST'])
@login_required
def api_supplier_add():
    items = load('supplier')
    # Parsing body payload yg dikirim Client
    data = request.json
    
    # Logika Pembuatan Kode Auto ID untuk Supplier
    # Cek jika tidak dikasih dari form
    if not data.get('supplierId'):
        n = len(items) + 1
        ids = [i['supplierId'] for i in items]
        # Format "SUP001" misal panjang list masih kosong = 1
        data['supplierId'] = f"SUP{n:03d}"
        # Jika bentrok dengan data yg ada, maju iterasi n+1
        while data['supplierId'] in ids:
            n += 1
            data['supplierId'] = f"SUP{n:03d}"
            
    # Set ID increment tabel internal Database
    data['id'] = next_id(items)
    
    # Masukkan record baru ke RAM
    items.append(data)
    # Tulis pembaruan dari RAM List tsb ke storage (harddisk) via json.dump
    save('supplier', items)
    
    # Notifikasi Berhasil ke Aplikasi javascript
    return jsonify({'success': True, 'supplierId': data['supplierId']})

# Endpoint API PUT Mengedit Data Supplier
@supplier_bp.route('/api/supplier/<int:item_id>', methods=['PUT'])
@login_required
def api_supplier_update(item_id):
    items = load('supplier')
    data = request.json
    
    # Loop daftar supplier yg sudah terdaftar
    for i, item in enumerate(items):
        # Cari Supplier dgn primary ID yg cocok
        if item['id'] == item_id:
            # Gunakan unpack dictionary **item dan **data. Nilai atribut yg ada di 'data' akan MENIMPA 
            # atribut milik 'item'. ID asli kita paksa lagi di set untuk menghindari penyelewengan pengubahan id
            items[i] = {**item, **data, 'id': item_id}
            # Commit Perubahan JSON Storage
            save('supplier', items)
            # Keluar fungsi dan beri signal bahwa aksi sukses
            return jsonify({'success': True})
            
    # Kasus gagal bila ID invalid dan tidak ketemu sama sekali di array List
    return jsonify({'success': False})

# Endpoint API DELETE Menghapus Supplier
@supplier_bp.route('/api/supplier/<int:item_id>', methods=['DELETE'])
@login_required
def api_supplier_delete(item_id):
    items = load('supplier')
    # Saring ulang isi list. Hanya masukkan dictionary yg nilai ID nya BERBEDA (tidak ditarget penghapusan)
    # Ini merupakan teknik cara buang / remove element dari array pada python yg bersih & terhindar index bound error
    items = [i for i in items if i['id'] != item_id]
    
    # Simpan kembali List yg udah tanpa item yg di-Delete tsb
    save('supplier', items)
    
    # Return status OK
    return jsonify({'success': True})
