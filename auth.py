# Import fitur Blueprint untuk memisahkan rute aplikasi
# Import request (untuk mengambil input form/JSON), session (menyimpan info login), 
# redirect (mengarahkan URL), url_for (membangun URL), dan render_template (menampilkan HTML)
from flask import Blueprint, request, session, redirect, url_for, render_template
# Import fungsi load (baca file JSON), save (tulis file JSON), dan next_id (buat ID) dari utils.py
from utils import load, save, next_id

# Membuat Blueprint khusus bernama 'auth' untuk menangani segala urusan otentikasi (login/logout/setup)
auth_bp = Blueprint('auth', __name__)

# Membuat rute untuk alamat dasar '/' dan '/login'. Bisa menangani method GET (tampil form) dan POST (kirim form)
@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Menginisialisasi variabel error dengan nilai None (tidak ada error di awal)
    error = None
    
    # Mengecek apakah method request adalah POST (artinya user baru saja menekan tombol Login di form)
    if request.method == 'POST':
        # Mengambil data dari inputan form ber-name 'username', menghilangkan spasi berlebih dengan strip()
        username = request.form.get('username', '').strip()
        # Mengambil data dari inputan form ber-name 'password', menghilangkan spasi berlebih
        password = request.form.get('password', '').strip()
        
        # Memuat (load) seluruh daftar pengguna dari database JSON (users.json)
        users = load('users')
        
        # Mencari pengguna (user) di list 'users' yang cocok username DAN password-nya.
        # Fungsi next() akan mengembalikan dictionary pengguna tersebut jika ketemu, jika tidak maka return None
        user = next((u for u in users if u['username'] == username and u['password'] == password), None)
        
        # Jika user ditemukan (username dan password benar)
        if user:
            # Simpan data user ke dalam Session Flask (menyatakan user sudah login)
            session['user'] = {'username': user['username'], 'fullName': user['fullName'], 'role': user['role']}
            # Arahkan pengguna ke halaman Dashboard menggunakan fungsi redirect dan url_for
            return redirect(url_for('dashboard.dashboard'))
        
        # Jika user tidak ditemukan, set pesan error
        error = 'Username atau password salah'
        
    # Render file HTML login.html dengan mengirimkan variabel error (jika ada pesan error akan ditampilkan di HTML)
    return render_template('login.html', error=error)

# Membuat rute '/logout' untuk mengeluarkan (logout) pengguna dari sistem
@auth_bp.route('/logout')
def logout():
    # Membersihkan semua data yang ada di session, termasuk data user yang login
    session.clear()
    # Mengarahkan kembali pengguna ke halaman form login
    return redirect(url_for('auth.login'))

# Membuat rute '/setup-admin' untuk proses pendaftaran akun Admin (jika belum ada)
@auth_bp.route('/setup-admin', methods=['GET', 'POST'])
def setup_admin():
    # Memuat seluruh daftar pengguna dari file users.json
    users = load('users')
    
    # Mengecek apakah di dalam list users sudah ada setidaknya 1 pengguna dengan role 'Admin'
    admin_exists = any(u['role'] == 'Admin' for u in users)
    
    # Jika akun Admin sudah ada, cegah akses halaman setup dan lempar kembali ke halaman login
    if admin_exists:
        return redirect(url_for('auth.login'))
        
    # Jika method yang dikirim adalah POST (user submit form untuk membuat admin baru)
    if request.method == 'POST':
        # Mengambil nilai username dari form HTML
        username = request.form.get('username', '').strip()
        # Mengambil nilai password dari form HTML
        password = request.form.get('password', '').strip()
        # Mengambil nama lengkap (fullName) dari form HTML
        full_name = request.form.get('fullName', '').strip()
        
        # Membuat dictionary object yang merepresentasikan data akun Admin baru,
        # dengan ID otomatis menggunakan fungsi next_id()
        new_user = {"id": next_id(users), "username": username, "password": password, "fullName": full_name, "role": "Admin"}
        
        # Menambahkan object admin baru tersebut ke dalam list 'users'
        users.append(new_user)
        # Menyimpan kembali list 'users' yang sudah terupdate ke file JSON
        save('users', users)
        
        # Setelah admin berhasil dibuat, arahkan kembali ke halaman login
        return redirect(url_for('auth.login'))
        
    # Jika method yang dipakai adalah GET (pengguna baru pertama kali membuka URL), tampilkan form setup_admin.html
    return render_template('setup_admin.html')
