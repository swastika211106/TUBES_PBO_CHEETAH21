# Import Blueprint untuk membagi modul rute transaksi, serta pustaka request/jsonify untuk API
from flask import Blueprint, render_template, request, jsonify
# Import fungsi dari utils. Perhatikan tambahan fungsi update_stock() yang sangat kritikal untuk log transaksi 
from utils import load, save, next_id, login_required, update_stock

# Mendaftarkan blueprint ber-nama 'transactions'
transactions_bp = Blueprint('transactions', __name__)

# ─────────────────────────────────────────────
# BARANG MASUK (Transaksi Pembelian / Pemasukan Stok)
# ─────────────────────────────────────────────

# Rute HTML Halaman Barang Masuk
@transactions_bp.route('/barang-masuk')
@login_required
def barang_masuk():
    # Menampilkan View barang_masuk.html
    return render_template('barang_masuk.html')

# API GET List Transaksi Barang Masuk
@transactions_bp.route('/api/barang-masuk', methods=['GET'])
@login_required
def api_barang_masuk_list():
    # Memuat isi data riwayat barang masuk
    items = load('barang_masuk')
    
    # Variabel parameter filter query (Pencarian Text)
    q = request.args.get('q', '').lower()
    # Variabel parameter filter batas awal Tanggal (Start Date)
    start = request.args.get('start', '')
    # Variabel parameter filter batas akhir Tanggal (End Date)
    end = request.args.get('end', '')
    
    # Jika diisi keyword pencarian 'q'
    if q:
        # Filter array hanya menampilkan ID transaksi, Kode, Nama Barang, atau Supplier yang mengandung kata kunci q
        items = [i for i in items if q in i.get('transactionId','').lower() or q in i.get('itemCode','').lower() or q in i.get('itemName','').lower() or q in i.get('supplier','').lower()]
    # Jika pengguna memilih filter rentang batas waktu tanggal 'start' dan 'end'
    if start and end:
        # Filter array dan ambil data transaksi dimana tanggal 'date' berada di antara rentang waktu tsb
        items = [i for i in items if start <= i.get('date','') <= end]
        
    return jsonify(items)

# API POST Menyimpan Transaksi Barang Masuk Baru (Input Pembelian)
@transactions_bp.route('/api/barang-masuk', methods=['POST'])
@login_required
def api_barang_masuk_add():
    # Membaca data barang masuk saat ini
    items = load('barang_masuk')
    # Menerima payload kiriman JSON
    data = request.json
    
    # Paksa ubah tipe string ke float agar dihitung benar pada matematika di JS/Python
    data['buyPrice'] = float(data.get('buyPrice', 0))
    data['sellPrice'] = float(data.get('sellPrice', 0))
    
    # [LOGIKA OTOMATIS TAMBAH MASTER BARANG BARU]
    # Apabila payload POST menyertakan atribut 'category', maka diasumsikan ini adalah 'BARANG BARU'
    # yang belum pernah ada di tabel Master Barang. Maka sistem akan menyisipkannya ke Master Barang otomatis.
    if 'category' in data and data.get('itemName'):
        # Muat Master Inventaris
        inventory = load('inventory')
        # Buang 'category' dari array 'data' menggunakan fungsi pop(), agar tidak ikut masuk tersimpan ke file transaksi masuk
        cat = data.pop('category')
        iname = data['itemName']
        
        # Mencari apakah nama barang itu sebenarnya sudah ada di inventory atau tidak (agar tidak duplikat)
        inv_item = next((i for i in inventory if i['name'].lower() == iname.lower()), None)
        
        # Jika benar-benar belum terdaftar di Master Barang
        if not inv_item:
            # Siapkan Kode Barang format 'BRG...' baru
            c = f"BRG{len(inventory)+1:03d}"
            # Cek looping jika bertabrakan kode barangnya dengan yang ada
            while any(x['code'] == c for x in inventory):
                c = f"BRG{int(c[3:])+1:03d}"
                
            # Siapkan Object data untuk Master Inventaris (stok akan nol dulu, lalu ditambahkan di bagian update_stock nanti)
            inv_item = {'id': next_id(inventory), 'code': c, 'name': iname, 'category': cat, 'stock': 0, 'unit': 'Pcs', 'buyPrice': data['buyPrice'], 'sellPrice': data['sellPrice']}
            # Tambahkan object barang ke array memory inventory
            inventory.append(inv_item)
        else:
            # Jika namanya sudah ada di Master Barang, kita perbarui (Update) Harga Beli dan Jual barang tersebut dengan yg terbaru
            inv_item['buyPrice'] = data['buyPrice']
            inv_item['sellPrice'] = data['sellPrice']
            
        # Simpan kembali database inventory
        save('inventory', inventory)
        # Ambil 'code' barang yg telah di-generate/dicari, lalu sematkan pada data transaksi 'Barang Masuk' yg akan disimpan
        data['itemCode'] = inv_item['code']

    # [LOGIKA MEMBUAT NOMOR TRANSAKSI BARANG MASUK FORMAT TRX...]
    if not data.get('transactionId'):
        n = len(items) + 1
        ids = [i['transactionId'] for i in items]
        data['transactionId'] = f"TRX{n:03d}"
        while data['transactionId'] in ids:
            n += 1
            data['transactionId'] = f"TRX{n:03d}"
            
    # Set unique row ID internal
    data['id'] = next_id(items)
    # Parse jumlah/kuantitas kuantiti menjadi angka desimal Integer asli
    data['quantity'] = int(data.get('quantity', 0))
    
    # Tambahkan catatan transaksi ini ke memory
    items.append(data)
    # Tulis pembaruan log ini ke file barang_masuk.json
    save('barang_masuk', items)
    
    # [TRIGGER PENTING] Panggil helper update_stock! 
    # Karena ini transaksi MASUK (in), maka jumlah (quantity) akan MENAMBAH nilai 'stock' di database Master Barang (inventory)
    update_stock(data['itemCode'], data['quantity'], 'in')
    
    # Kembalikan response sukses berserta nomor Transaksi (ID trx) ke Front-end Javascript
    return jsonify({'success': True, 'transactionId': data['transactionId']})

# API PUT Mengedit Transaksi Barang Masuk
@transactions_bp.route('/api/barang-masuk/<int:item_id>', methods=['PUT'])
@login_required
def api_barang_masuk_update(item_id):
    items = load('barang_masuk')
    data = request.json
    
    data['buyPrice'] = float(data.get('buyPrice', 0))
    data['sellPrice'] = float(data.get('sellPrice', 0))
    
    # Sama seperti logika add, bila mengupdate tapi ternyata merubah detail Barang, maka sesuaikan / buat kode barang di master inventaris
    if 'category' in data and data.get('itemName'):
        inventory = load('inventory')
        cat = data.pop('category')
        iname = data['itemName']
        inv_item = next((i for i in inventory if i['name'].lower() == iname.lower()), None)
        if not inv_item:
            c = f"BRG{len(inventory)+1:03d}"
            while any(x['code'] == c for x in inventory):
                c = f"BRG{int(c[3:])+1:03d}"
            inv_item = {'id': next_id(inventory), 'code': c, 'name': iname, 'category': cat, 'stock': 0, 'unit': 'Pcs', 'buyPrice': data['buyPrice'], 'sellPrice': data['sellPrice']}
            inventory.append(inv_item)
        else:
            inv_item['buyPrice'] = data['buyPrice']
            inv_item['sellPrice'] = data['sellPrice']
        save('inventory', inventory)
        data['itemCode'] = inv_item['code']

    # Update item-nya
    for i, item in enumerate(items):
        if item['id'] == item_id:
            # Kita simpan nilai kuantitas/kode lama sebelum ditimpa. Agar kita bisa menyesuaikan/mengembalikan total Stok dengan tepat!
            old_qty = item.get('quantity', 0)
            old_code = item.get('itemCode', '')
            
            # Ganti/Timpa row dengan payload baru
            items[i] = {**item, **data, 'id': item_id}
            items[i]['quantity'] = int(items[i].get('quantity', 0))
            
            # Simpan log transaksi (Barang Masuk)
            save('barang_masuk', items)
            
            # [LOGIKA PENYESUAIAN REVISI JUMLAH STOK DI MASTER BARANG]
            # Menghitung selisih/perbedaan kuantiti lama dan yg baru direvisi.
            diff = items[i]['quantity'] - old_qty
            
            # Jika user HANYA MENGUBAH JUMLAH KUANTITI BARANG-NYA SAJA (TIDAK GANTI BARANG-NYA):
            if old_code == items[i]['itemCode']:
                # Update tambahkan ke Master Barang HANYA SELISIH NYA (contoh, dari beli 10 direvisi 15, artinya tambah 5 aja)
                update_stock(old_code, diff, 'in')
            # Jika ternyata User malah MENGGANTI TOTAL PILIHAN BARANG-nya dari form drop down transaksi
            else:
                # 1. HAPUS efek pertambahan kuantitas barang lama di Master Stok (kembalikan stok dengan cara menambah qty negatif (-))
                update_stock(old_code, -old_qty, 'in')
                # 2. TAMBAH/Masukan stok kuantitas murni tersebut kepada Kode Barang yg baru diset
                update_stock(items[i]['itemCode'], items[i]['quantity'], 'in')
                
            return jsonify({'success': True})
    return jsonify({'success': False})

# API DELETE Menghapus Riwayat Transaksi Barang Masuk
@transactions_bp.route('/api/barang-masuk/<int:item_id>', methods=['DELETE'])
@login_required
def api_barang_masuk_delete(item_id):
    items = load('barang_masuk')
    # Cari spesifik baris record yang ingin didelete
    item = next((i for i in items if i['id'] == item_id), None)
    if item:
        # Jika transaksi ini dibatalkan/didelete, maka Jumlah stok yg sebelumnya sudah masuk ke Master Barang
        # Harus kita TARIK/KURANGI KEMBALI dari Master Barang! Itulah alasan kita kirimkan minus jumlah kuantitinya (negatif).
        update_stock(item['itemCode'], -item['quantity'], 'in')
        
    # Setelah kalkulasi stok selesai disesuaikan, barulah kita berani menghapus secara fisik data dari log transaksi JSON.
    items = [i for i in items if i['id'] != item_id]
    save('barang_masuk', items)
    return jsonify({'success': True})


# ─────────────────────────────────────────────
# BARANG KELUAR (Transaksi Penjualan / Pengeluaran Stok)
# Logika kerjanya sama persis seperti "Barang Masuk", namun untuk logika Validasi Stok di master sedikit berbeda!
# ─────────────────────────────────────────────

# Rute UI Halaman HTML
@transactions_bp.route('/barang-keluar')
@login_required
def barang_keluar():
    return render_template('barang_keluar.html')

# API GET List Transaksi Barang Keluar
@transactions_bp.route('/api/barang-keluar', methods=['GET'])
@login_required
def api_barang_keluar_list():
    items = load('barang_keluar')
    q = request.args.get('q', '').lower()
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    if q:
        items = [i for i in items if q in i.get('transactionId','').lower() or q in i.get('itemCode','').lower() or q in i.get('itemName','').lower()]
    if start and end:
        items = [i for i in items if start <= i.get('date','') <= end]
    return jsonify(items)

# API POST Tambah Transaksi Barang Keluar
@transactions_bp.route('/api/barang-keluar', methods=['POST'])
@login_required
def api_barang_keluar_add():
    items = load('barang_keluar')
    inventory = load('inventory') # Wajib buka master inventory untuk cek ketersediaan Stok
    data = request.json
    
    # [PENTING] VALIDASI SISA STOK! 
    # Mencari object barang yg mau dikeluarkan itu di dalam inventory list berdasarkan kodenya
    item_inv = next((i for i in inventory if i['code'] == data.get('itemCode')), None)
    
    # Jika barang ada di list, tetapi sisa stoknya (item_inv['stock']) TERNYATA LEBIH KECIL (Kurang dari) 
    # jumlah barang yg mau di Input keluar (data['quantity']) oleh Kasir/User
    if item_inv and int(item_inv.get('stock', 0)) < int(data.get('quantity', 0)):
        # BATALKAN Operasi dan Lemparkan pesan error (Feedback) ke aplikasi frontend agar user sadar!
        return jsonify({'success': False, 'message': f"Stok tidak mencukupi. Stok saat ini: {item_inv.get('stock', 0)}"})
    
    # Jika stok barang memenuhi kuota dan mencukupi, catat record Harga Beli & Jual-nya ke transaksi ini
    # sebagai pengunci (lock/snapshot). Jadi bila harga master barang berubah dikemudian hari, laba perhitungan lama ini tidak ikut rusak!
    if item_inv:
        data['buyPrice'] = float(item_inv.get('buyPrice', 0))
        data['sellPrice'] = float(item_inv.get('sellPrice', 0))
    else:
        # Jika barang aneh/tidak terdaftar, asumsikan nominal nol
        data['buyPrice'] = 0.0
        data['sellPrice'] = 0.0

    # Auto generate ID TRansaksi TRX untuk barang keluar
    if not data.get('transactionId'):
        n = len(items) + 1
        ids = [i['transactionId'] for i in items]
        data['transactionId'] = f"TRX{n:03d}"
        while data['transactionId'] in ids:
            n += 1
            data['transactionId'] = f"TRX{n:03d}"
            
    # Set internal row ID
    data['id'] = next_id(items)
    data['quantity'] = int(data.get('quantity', 0))
    
    # Sisipkan log penjualan ke array JSON dan commit ke save()
    items.append(data)
    save('barang_keluar', items)
    
    # [TRIGGER PENTING] Panggil helper update_stock dengan tipe 'out' ! 
    # 'out' berarti logika pada util function akan MENGURANGI Stok pada database Master Inventory.
    update_stock(data['itemCode'], data['quantity'], 'out')
    
    # Selesai, lempar status berhasil ke user UI
    return jsonify({'success': True, 'transactionId': data['transactionId']})

# API PUT Edit Barang Keluar
@transactions_bp.route('/api/barang-keluar/<int:item_id>', methods=['PUT'])
@login_required
def api_barang_keluar_update(item_id):
    items = load('barang_keluar')
    data = request.json
    inventory = load('inventory')

    # Cek & samakan data harga di Master dengan yg mau diset di input. Agar tercatat dengan baik history-nya.
    item_inv = next((i for i in inventory if i['code'] == data.get('itemCode')), None)
    if item_inv:
        data['buyPrice'] = float(item_inv.get('buyPrice', 0))
        data['sellPrice'] = float(item_inv.get('sellPrice', 0))

    # Looping list record barang keluar yg lama untuk menemukan target
    for i, item in enumerate(items):
        if item['id'] == item_id:
            # Ambil memori historis (Berapa qty dan Apa itemCode sebelumnya yg dinput di awal?)
            old_qty = item.get('quantity', 0)
            old_code = item.get('itemCode', '')
            
            # Mulai modifikasi record baris ke-(i) JSON menjadi isi Data Request yang ter-update
            items[i] = {**item, **data, 'id': item_id}
            items[i]['quantity'] = int(items[i].get('quantity', 0))
            # Simpan overwrite isi list ke File db.json
            save('barang_keluar', items)
            
            # Hitung selisih qty lama dan baru (qty direvisi - qty tempo dulu = perbedaan revisi)
            diff = items[i]['quantity'] - old_qty
            
            # Jika user HANYA mengganti JUMLAH angkanya saja. Misal kasir salah ketik dari laku 3 direvisi jadi laku 2, maka diff nya (-1).
            if old_code == items[i]['itemCode']:
                # Update stok di inventori menggunakan tipe 'out'. Jika 'diff' (revisi selisih) itu (-1),
                # maka di 'out' fungsi util kita akan mengurangkan nilai negatif -> 'stock' - (-1) yang sama artinya Menambahkan Stok jadi kembali +1! 
                update_stock(old_code, diff, 'out')
            # Jika ternyata User yang salah menunjuk Pilihan Menu barang saat pencatatan transaksi awal
            else:
                # 1. Batalkan pengurangan stok yg udah terlanjur terjadi di Barang Lama dengan memberikannya nilai (-1 * old_qty) 
                # (Min x Min = Plus) sehingga stok barang lama di master KEMBALI KE ASAL (nambah lagi ke Gudang)
                update_stock(old_code, -old_qty, 'out')
                # 2. Barulah Lakukan pengurangan stok ke Kode Barang Baru secara normal dengan Qty Revisinya yg Valid untuk dikeluarkan.
                update_stock(items[i]['itemCode'], items[i]['quantity'], 'out')
                
            return jsonify({'success': True})
            
    # Kembalikan response kegagalan proses
    return jsonify({'success': False})

# API DELETE Hapus Barang Keluar
@transactions_bp.route('/api/barang-keluar/<int:item_id>', methods=['DELETE'])
@login_required
def api_barang_keluar_delete(item_id):
    items = load('barang_keluar')
    item = next((i for i in items if i['id'] == item_id), None)
    
    # Karena catatan barang sudah DIBATALKAN/DIBUANG dari sistem log, 
    # Maksudnya secara tidak langsung barang tersebut URUNG dikeluarkan dari gudang.
    if item:
        # Kita menggunakan tipe 'out' untuk me-reverse data. Memberinya angka MINUS qty negatif.
        # Sehingga fungsi utils `update_stock` akan memproses kalkulasi: [curr_stock - (-qty)] 
        # Yang mana secara matematis menghasilkan (Ditambah +) = Stok Fisik gudang master bertambah lagi!
        update_stock(item['itemCode'], -item['quantity'], 'out')
        
    # Buang dict item bersangkutan secara permanen dari memory list
    items = [i for i in items if i['id'] != item_id]
    # Update File Database Barang Keluar .json
    save('barang_keluar', items)
    # Lapor Success True
    return jsonify({'success': True})
