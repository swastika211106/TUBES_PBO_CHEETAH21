# Import Blueprint, jsonify dan utilitas penting lainnya
from flask import Blueprint, render_template, request, jsonify
from utils import load, save, next_id, login_required

# Deklarasi module Rute Khusus Modul User / Administrator Account
user_bp = Blueprint('user', __name__)

# Halaman Web Daftar User (HTML View)
@user_bp.route('/user')
@login_required # Memerlukan user login aktif pada Session Web
def user_page():
    return render_template('user.html')

# Endpoint API Daftar (GET) User JSON (Keperluan Refresh Tabel HTML)
@user_bp.route('/api/users', methods=['GET'])
@login_required
def api_users_list():
    # Ambil data User dari storage
    items = load('users')
    
    # Query param pencarian
    q = request.args.get('q', '').lower()
    if q:
        # Validasi Search mencocokkan kata ke Username, FullName, atau Role Hak Akses.
        items = [i for i in items if q in i.get('username','').lower() or q in i.get('fullName','').lower() or q in i.get('role','').lower()]
        
    # [KEAMANAN PENTING - SECURITY] 
    # Mencegah ter-eksposnya string kata sandi (password) plaintext di REST API kita melalui Network Layer Inspector / Frontend
    # Menggunakan Dict Comprehension: Copy key dan value, jika atribut tsb BUKAN password, maka masukkan.
    safe = [{k: v for k, v in u.items() if k != 'password'} for u in items]
    
    # Return array 'safe' ke aplikasi JS
    return jsonify(safe)

# Endpoint API Tambah Akun / Register Admin Internal via API
@user_bp.route('/api/users', methods=['POST'])
@login_required
def api_users_add():
    items = load('users')
    # Menangkap body json API 
    data = request.json
    
    # Buatkan ID berurut otomatis
    data['id'] = next_id(items)
    
    # Tambahkan User Ke Array List Database
    items.append(data)
    
    # Write ke Storage
    save('users', items)
    return jsonify({'success': True})

# Endpoint API Ganti Data / Edit Akses / Reset Password via API
@user_bp.route('/api/users/<int:item_id>', methods=['PUT'])
@login_required
def api_users_update(item_id):
    items = load('users')
    data = request.json
    
    # Scanning index
    for i, item in enumerate(items):
        if item['id'] == item_id:
            # Overwrite dictionary user yang di-target
            items[i] = {**item, **data, 'id': item_id}
            # Simpan File JSON
            save('users', items)
            # Lapor Success
            return jsonify({'success': True})
            
    # Lapor Kesalahan (Bila ID tak ada)
    return jsonify({'success': False})

# Endpoint API Untuk Menghapus / Memblokir Akses Admin User
@user_bp.route('/api/users/<int:item_id>', methods=['DELETE'])
@login_required
def api_users_delete(item_id):
    items = load('users')
    
    # Gunakan Filter List Comprehension untuk meng-eksklusikan/meng-ignore ID yang mau di delete dari array memori
    items = [i for i in items if i['id'] != item_id]
    
    # Timpa db asli tanpa row tsb
    save('users', items)
    return jsonify({'success': True})
