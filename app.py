# Import modul Flask utama untuk membuat aplikasi web
from flask import Flask
# Import fungsi init_data dari file utils.py untuk inisialisasi data default
from utils import init_data

# Import semua blueprint (rute/endpoint) yang telah dipisah berdasarkan fungsinya
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.inventory import inventory_bp
from routes.transactions import transactions_bp
from routes.supplier import supplier_bp
from routes.user import user_bp
from routes.api import api_bp

# Membuat instance aplikasi Flask, mengatur template_folder ke '.' (folder saat ini) agar dapat membaca file HTML di root
app = Flask(__name__, template_folder='.')

# Mengatur kunci rahasia (secret key) yang dibutuhkan Flask untuk mengamankan session pengguna
app.secret_key = 'inventory_secret_key_2024'

# Memanggil fungsi init_data() untuk memastikan file-file JSON (database) sudah ada saat aplikasi pertama kali dijalankan
init_data()

# Mendaftarkan blueprint auth_bp ke dalam aplikasi utama agar rute login/logout bisa diakses
app.register_blueprint(auth_bp)
# Mendaftarkan blueprint dashboard_bp untuk rute halaman dashboard
app.register_blueprint(dashboard_bp)
# Mendaftarkan blueprint inventory_bp untuk rute master barang dan kategori
app.register_blueprint(inventory_bp)
# Mendaftarkan blueprint transactions_bp untuk rute barang masuk dan keluar
app.register_blueprint(transactions_bp)
# Mendaftarkan blueprint supplier_bp untuk rute pengelolaan supplier
app.register_blueprint(supplier_bp)
# Mendaftarkan blueprint user_bp untuk rute pengelolaan pengguna aplikasi
app.register_blueprint(user_bp)
# Mendaftarkan blueprint api_bp untuk rute API seperti dropdown data dan export CSV
app.register_blueprint(api_bp)

# Blok ini memastikan server web Flask hanya dijalankan jika file ini dieksekusi secara langsung (bukan di-import)
if __name__ == '__main__':
    # Menjalankan server pada mode debug (bisa reload otomatis jika kode berubah) di port 5000
    app.run(debug=True, port=5000)
