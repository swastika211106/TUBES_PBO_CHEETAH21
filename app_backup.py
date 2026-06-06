from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
from datetime import datetime, date
import csv
import io

app = Flask(__name__, template_folder='.')
app.secret_key = 'inventory_secret_key_2024'

# ─────────────────────────────────────────────
# DATA STORAGE (JSON files sebagai pengganti Google Sheets)
# ─────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

FILES = {
    'users':      os.path.join(DATA_DIR, 'users.json'),
    'inventory':  os.path.join(DATA_DIR, 'inventory.json'),
    'barang_masuk':  os.path.join(DATA_DIR, 'barang_masuk.json'),
    'barang_keluar': os.path.join(DATA_DIR, 'barang_keluar.json'),
    'supplier':   os.path.join(DATA_DIR, 'supplier.json'),
    'kategori':   os.path.join(DATA_DIR, 'kategori.json'),
}

def load(key):
    path = FILES[key]
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save(key, data):
    with open(FILES[key], 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def init_data():
    """Initialize default data if not exists."""
    if not os.path.exists(FILES['users']) or load('users') == []:
        save('users', [
            {"id": 1, "username": "admin",   "password": "admin123",   "fullName": "Administrator", "role": "Admin"},
            {"id": 2, "username": "manager", "password": "manager123", "fullName": "Manager",       "role": "Manajemen"},
        ])
    for key in ['inventory', 'barang_masuk', 'barang_keluar', 'supplier', 'kategori']:
        if not os.path.exists(FILES[key]):
            save(key, [])

init_data()

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def next_id(items):
    return max((i.get('id', 0) for i in items), default=0) + 1

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def format_rupiah(value):
    try:
        return f"Rp {int(value):,}".replace(',', '.')
    except:
        return "Rp 0"

# ─────────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────────
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        users = load('users')
        user = next((u for u in users if u['username'] == username and u['password'] == password), None)
        if user:
            session['user'] = {'username': user['username'], 'fullName': user['fullName'], 'role': user['role']}
            return redirect(url_for('dashboard'))
        error = 'Username atau password salah'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/setup-admin', methods=['GET', 'POST'])
def setup_admin():
    users = load('users')
    admin_exists = any(u['role'] == 'Admin' for u in users)
    if admin_exists:
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        full_name = request.form.get('fullName', '').strip()
        new_user = {"id": next_id(users), "username": username, "password": password, "fullName": full_name, "role": "Admin"}
        users.append(new_user)
        save('users', users)
        return redirect(url_for('login'))
    return render_template('setup_admin.html')

# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    inventory = load('inventory')
    barang_masuk = load('barang_masuk')
    barang_keluar = load('barang_keluar')

    total_jenis = len(set(i['code'] for i in inventory))
    total_stok = sum(i.get('stock', 0) for i in inventory)
    total_masuk = sum(i.get('quantity', 0) for i in barang_masuk)
    total_keluar = sum(i.get('quantity', 0) for i in barang_keluar)

    inv_map = {i['code']: i for i in inventory}
    total_nilai_beli = sum(i.get('stock', 0) * i.get('buyPrice', 0) for i in inventory)
    total_nilai_jual = sum(i.get('stock', 0) * i.get('sellPrice', 0) for i in inventory)

    total_keuntungan = 0
    for bk in barang_keluar:
        item = inv_map.get(bk.get('itemCode'))
        if item:
            total_keuntungan += bk.get('quantity', 0) * (item.get('sellPrice', 0) - item.get('buyPrice', 0))

    return render_template('dashboard.html',
        total_jenis=total_jenis,
        total_stok=total_stok,
        total_masuk=total_masuk,
        total_keluar=total_keluar,
        total_nilai_beli=format_rupiah(total_nilai_beli),
        total_nilai_jual=format_rupiah(total_nilai_jual),
        total_keuntungan=format_rupiah(total_keuntungan),
    )

# ─────────────────────────────────────────────
# MASTER BARANG
# ─────────────────────────────────────────────
@app.route('/master-barang')
@login_required
def master_barang():
    return render_template('master_barang.html')

@app.route('/api/inventory', methods=['GET'])
@login_required
def api_inventory_list():
    items = load('inventory')
    q = request.args.get('q', '').lower()
    if q:
        items = [i for i in items if q in i.get('code','').lower() or q in i.get('name','').lower() or q in i.get('category','').lower()]
    return jsonify(items)

@app.route('/api/inventory', methods=['POST'])
@login_required
def api_inventory_add():
    items = load('inventory')
    data = request.json
    codes = [i['code'] for i in items]
    if not data.get('code'):
        n = len(items) + 1
        data['code'] = f"BRG{n:03d}"
        while data['code'] in codes:
            n += 1
            data['code'] = f"BRG{n:03d}"
    data['id'] = next_id(items)
    data['stock'] = int(data.get('stock', 0))
    data['buyPrice'] = float(data.get('buyPrice', 0))
    data['sellPrice'] = float(data.get('sellPrice', 0))
    items.append(data)
    save('inventory', items)
    return jsonify({'success': True, 'code': data['code']})

@app.route('/api/inventory/<int:item_id>', methods=['PUT'])
@login_required
def api_inventory_update(item_id):
    items = load('inventory')
    data = request.json
    for i, item in enumerate(items):
        if item['id'] == item_id:
            items[i] = {**item, **data, 'id': item_id}
            items[i]['stock'] = int(items[i].get('stock', 0))
            items[i]['buyPrice'] = float(items[i].get('buyPrice', 0))
            items[i]['sellPrice'] = float(items[i].get('sellPrice', 0))
            save('inventory', items)
            return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Item tidak ditemukan'})

@app.route('/api/inventory/<int:item_id>', methods=['DELETE'])
@login_required
def api_inventory_delete(item_id):
    items = load('inventory')
    items = [i for i in items if i['id'] != item_id]
    save('inventory', items)
    return jsonify({'success': True})

# ─────────────────────────────────────────────
# BARANG MASUK
# ─────────────────────────────────────────────
@app.route('/barang-masuk')
@login_required
def barang_masuk():
    return render_template('barang_masuk.html')

@app.route('/api/barang-masuk', methods=['GET'])
@login_required
def api_barang_masuk_list():
    items = load('barang_masuk')
    q = request.args.get('q', '').lower()
    start = request.args.get('start', '')
    end = request.args.get('end', '')
    if q:
        items = [i for i in items if q in i.get('transactionId','').lower() or q in i.get('itemCode','').lower() or q in i.get('itemName','').lower() or q in i.get('supplier','').lower()]
    if start and end:
        items = [i for i in items if start <= i.get('date','') <= end]
    return jsonify(items)

@app.route('/api/barang-masuk', methods=['POST'])
@login_required
def api_barang_masuk_add():
    items = load('barang_masuk')
    data = request.json
    if not data.get('transactionId'):
        n = len(items) + 1
        ids = [i['transactionId'] for i in items]
        data['transactionId'] = f"TRX{n:03d}"
        while data['transactionId'] in ids:
            n += 1
            data['transactionId'] = f"TRX{n:03d}"
    data['id'] = next_id(items)
    data['quantity'] = int(data.get('quantity', 0))
    items.append(data)
    save('barang_masuk', items)
    # Update stock
    update_stock(data['itemCode'], data['quantity'], 'in')
    return jsonify({'success': True, 'transactionId': data['transactionId']})

@app.route('/api/barang-masuk/<int:item_id>', methods=['PUT'])
@login_required
def api_barang_masuk_update(item_id):
    items = load('barang_masuk')
    data = request.json
    for i, item in enumerate(items):
        if item['id'] == item_id:
            old_qty = item.get('quantity', 0)
            old_code = item.get('itemCode', '')
            items[i] = {**item, **data, 'id': item_id}
            items[i]['quantity'] = int(items[i].get('quantity', 0))
            save('barang_masuk', items)
            diff = items[i]['quantity'] - old_qty
            if old_code == items[i]['itemCode']:
                update_stock(old_code, diff, 'in')
            else:
                update_stock(old_code, -old_qty, 'in')
                update_stock(items[i]['itemCode'], items[i]['quantity'], 'in')
            return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/barang-masuk/<int:item_id>', methods=['DELETE'])
@login_required
def api_barang_masuk_delete(item_id):
    items = load('barang_masuk')
    item = next((i for i in items if i['id'] == item_id), None)
    if item:
        update_stock(item['itemCode'], -item['quantity'], 'in')
    items = [i for i in items if i['id'] != item_id]
    save('barang_masuk', items)
    return jsonify({'success': True})

# ─────────────────────────────────────────────
# BARANG KELUAR
# ─────────────────────────────────────────────
@app.route('/barang-keluar')
@login_required
def barang_keluar():
    return render_template('barang_keluar.html')

@app.route('/api/barang-keluar', methods=['GET'])
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

@app.route('/api/barang-keluar', methods=['POST'])
@login_required
def api_barang_keluar_add():
    items = load('barang_keluar')
    inventory = load('inventory')
    data = request.json
    # Cek stok
    item_inv = next((i for i in inventory if i['code'] == data.get('itemCode')), None)
    if item_inv and item_inv.get('stock', 0) < int(data.get('quantity', 0)):
        return jsonify({'success': False, 'message': f"Stok tidak mencukupi. Stok saat ini: {item_inv.get('stock', 0)}"})
    if not data.get('transactionId'):
        n = len(items) + 1
        ids = [i['transactionId'] for i in items]
        data['transactionId'] = f"TRX{n:03d}"
        while data['transactionId'] in ids:
            n += 1
            data['transactionId'] = f"TRX{n:03d}"
    data['id'] = next_id(items)
    data['quantity'] = int(data.get('quantity', 0))
    items.append(data)
    save('barang_keluar', items)
    update_stock(data['itemCode'], data['quantity'], 'out')
    return jsonify({'success': True, 'transactionId': data['transactionId']})

@app.route('/api/barang-keluar/<int:item_id>', methods=['PUT'])
@login_required
def api_barang_keluar_update(item_id):
    items = load('barang_keluar')
    data = request.json
    for i, item in enumerate(items):
        if item['id'] == item_id:
            old_qty = item.get('quantity', 0)
            old_code = item.get('itemCode', '')
            items[i] = {**item, **data, 'id': item_id}
            items[i]['quantity'] = int(items[i].get('quantity', 0))
            save('barang_keluar', items)
            diff = items[i]['quantity'] - old_qty
            if old_code == items[i]['itemCode']:
                update_stock(old_code, diff, 'out')
            else:
                update_stock(old_code, -old_qty, 'out')
                update_stock(items[i]['itemCode'], items[i]['quantity'], 'out')
            return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/barang-keluar/<int:item_id>', methods=['DELETE'])
@login_required
def api_barang_keluar_delete(item_id):
    items = load('barang_keluar')
    item = next((i for i in items if i['id'] == item_id), None)
    if item:
        update_stock(item['itemCode'], -item['quantity'], 'out')
    items = [i for i in items if i['id'] != item_id]
    save('barang_keluar', items)
    return jsonify({'success': True})

# ─────────────────────────────────────────────
# SUPPLIER
# ─────────────────────────────────────────────
@app.route('/supplier')
@login_required
def supplier():
    return render_template('supplier.html')

@app.route('/api/supplier', methods=['GET'])
@login_required
def api_supplier_list():
    items = load('supplier')
    q = request.args.get('q', '').lower()
    if q:
        items = [i for i in items if q in i.get('supplierId','').lower() or q in i.get('name','').lower() or q in i.get('address','').lower() or q in i.get('phone','').lower()]
    return jsonify(items)

@app.route('/api/supplier', methods=['POST'])
@login_required
def api_supplier_add():
    items = load('supplier')
    data = request.json
    if not data.get('supplierId'):
        n = len(items) + 1
        ids = [i['supplierId'] for i in items]
        data['supplierId'] = f"SUP{n:03d}"
        while data['supplierId'] in ids:
            n += 1
            data['supplierId'] = f"SUP{n:03d}"
    data['id'] = next_id(items)
    items.append(data)
    save('supplier', items)
    return jsonify({'success': True, 'supplierId': data['supplierId']})

@app.route('/api/supplier/<int:item_id>', methods=['PUT'])
@login_required
def api_supplier_update(item_id):
    items = load('supplier')
    data = request.json
    for i, item in enumerate(items):
        if item['id'] == item_id:
            items[i] = {**item, **data, 'id': item_id}
            save('supplier', items)
            return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/supplier/<int:item_id>', methods=['DELETE'])
@login_required
def api_supplier_delete(item_id):
    items = load('supplier')
    items = [i for i in items if i['id'] != item_id]
    save('supplier', items)
    return jsonify({'success': True})

# ─────────────────────────────────────────────
# KATEGORI
# ─────────────────────────────────────────────
@app.route('/kategori-barang')
@login_required
def kategori_barang():
    return render_template('kategori_barang.html')

@app.route('/api/kategori', methods=['GET'])
@login_required
def api_kategori_list():
    items = load('kategori')
    q = request.args.get('q', '').lower()
    if q:
        items = [i for i in items if q in i.get('kategoriId','').lower() or q in i.get('name','').lower()]
    return jsonify(items)

@app.route('/api/kategori', methods=['POST'])
@login_required
def api_kategori_add():
    items = load('kategori')
    data = request.json
    if not data.get('kategoriId'):
        n = len(items) + 1
        ids = [i['kategoriId'] for i in items]
        data['kategoriId'] = f"KTG{n:03d}"
        while data['kategoriId'] in ids:
            n += 1
            data['kategoriId'] = f"KTG{n:03d}"
    data['id'] = next_id(items)
    items.append(data)
    save('kategori', items)
    return jsonify({'success': True, 'kategoriId': data['kategoriId']})

@app.route('/api/kategori/<int:item_id>', methods=['PUT'])
@login_required
def api_kategori_update(item_id):
    items = load('kategori')
    data = request.json
    for i, item in enumerate(items):
        if item['id'] == item_id:
            items[i] = {**item, **data, 'id': item_id}
            save('kategori', items)
            return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/kategori/<int:item_id>', methods=['DELETE'])
@login_required
def api_kategori_delete(item_id):
    items = load('kategori')
    items = [i for i in items if i['id'] != item_id]
    save('kategori', items)
    return jsonify({'success': True})

# ─────────────────────────────────────────────
# USER
# ─────────────────────────────────────────────
@app.route('/user')
@login_required
def user_page():
    return render_template('user.html')

@app.route('/api/users', methods=['GET'])
@login_required
def api_users_list():
    items = load('users')
    q = request.args.get('q', '').lower()
    if q:
        items = [i for i in items if q in i.get('username','').lower() or q in i.get('fullName','').lower() or q in i.get('role','').lower()]
    # Don't send passwords to frontend
    safe = [{k: v for k, v in u.items() if k != 'password'} for u in items]
    return jsonify(safe)

@app.route('/api/users', methods=['POST'])
@login_required
def api_users_add():
    items = load('users')
    data = request.json
    data['id'] = next_id(items)
    items.append(data)
    save('users', items)
    return jsonify({'success': True})

@app.route('/api/users/<int:item_id>', methods=['PUT'])
@login_required
def api_users_update(item_id):
    items = load('users')
    data = request.json
    for i, item in enumerate(items):
        if item['id'] == item_id:
            items[i] = {**item, **data, 'id': item_id}
            save('users', items)
            return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/users/<int:item_id>', methods=['DELETE'])
@login_required
def api_users_delete(item_id):
    items = load('users')
    items = [i for i in items if i['id'] != item_id]
    save('users', items)
    return jsonify({'success': True})

# ─────────────────────────────────────────────
# DROPDOWN DATA
# ─────────────────────────────────────────────
@app.route('/api/dropdown-data')
@login_required
def api_dropdown():
    suppliers = [s['name'] for s in load('supplier')]
    categories = [k['name'] for k in load('kategori')]
    items = [{'code': i['code'], 'name': i['name'], 'stock': i.get('stock', 0), 'unit': i.get('unit','')} for i in load('inventory')]
    return jsonify({'suppliers': suppliers, 'categories': categories, 'items': items})

# ─────────────────────────────────────────────
# STOCK HELPER
# ─────────────────────────────────────────────
def update_stock(item_code, quantity, type_):
    inventory = load('inventory')
    for i, item in enumerate(inventory):
        if item['code'] == item_code:
            curr = int(item.get('stock', 0))
            if type_ == 'in':
                inventory[i]['stock'] = max(0, curr + quantity)
            else:
                inventory[i]['stock'] = max(0, curr - quantity)
            save('inventory', inventory)
            return
        
# ─────────────────────────────────────────────
# EXPORT CSV (pengganti Excel)
# ─────────────────────────────────────────────
@app.route('/api/export/<string:sheet_name>')
@login_required
def api_export(sheet_name):
    from flask import Response
    key_map = {
        'inventory': 'inventory', 'barang-masuk': 'barang_masuk',
        'barang-keluar': 'barang_keluar', 'supplier': 'supplier',
        'kategori': 'kategori', 'users': 'users',
    }
    key = key_map.get(sheet_name)
    if not key:
        return jsonify({'success': False, 'message': 'Sheet tidak ditemukan'})
    items = load(key)
    if not items:
        return jsonify({'success': False, 'message': 'Tidak ada data'})
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=items[0].keys())
    writer.writeheader()
    writer.writerows(items)
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={"Content-Disposition": f"attachment;filename={sheet_name}.csv"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)