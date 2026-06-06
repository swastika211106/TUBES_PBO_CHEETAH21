import os
import json
import sqlite3
from flask import session, redirect, url_for
from functools import wraps

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, 'inventory.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_data():
    """Initialize SQLite database and migrate JSON data if available."""
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, fullName TEXT, role TEXT);
        CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY, code TEXT UNIQUE, name TEXT, category TEXT, stock INTEGER, buyPrice REAL, sellPrice REAL, unit TEXT);
        CREATE TABLE IF NOT EXISTS barang_masuk (id INTEGER PRIMARY KEY, transactionId TEXT UNIQUE, itemCode TEXT, itemName TEXT, supplier TEXT, quantity INTEGER, date TEXT, buyPrice REAL, sellPrice REAL);
        CREATE TABLE IF NOT EXISTS barang_keluar (id INTEGER PRIMARY KEY, transactionId TEXT UNIQUE, itemCode TEXT, itemName TEXT, quantity INTEGER, date TEXT, buyPrice REAL, sellPrice REAL);
        CREATE TABLE IF NOT EXISTS supplier (id INTEGER PRIMARY KEY, supplierId TEXT UNIQUE, name TEXT, address TEXT, phone TEXT);
        CREATE TABLE IF NOT EXISTS kategori (id INTEGER PRIMARY KEY, kategoriId TEXT UNIQUE, name TEXT);
        """)
        
        tables = ['users', 'inventory', 'barang_masuk', 'barang_keluar', 'supplier', 'kategori']
        for table in tables:
            cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
            if cur.fetchone()[0] == 0:
                json_path = os.path.join(DATA_DIR, f"{table}.json")
                if os.path.exists(json_path):
                    with open(json_path, 'r', encoding='utf-8') as f:
                        try:
                            data = json.load(f)
                            if data:
                                cur = conn.execute(f"PRAGMA table_info({table})")
                                valid_cols = [r['name'] for r in cur.fetchall()]
                                for row in data:
                                    filtered = {k: v for k, v in row.items() if k in valid_cols}
                                    if filtered:
                                        cols = ', '.join(f'"{k}"' for k in filtered.keys())
                                        vals = tuple(filtered.values())
                                        q = ', '.join('?' for _ in filtered)
                                        conn.execute(f'INSERT INTO {table} ({cols}) VALUES ({q})', vals)
                        except Exception as e:
                            print(f"Migration error on {table}: {e}")
                            pass
                elif table == 'users':
                    conn.executemany("INSERT INTO users (id, username, password, fullName, role) VALUES (?, ?, ?, ?, ?)", [
                        (1, 'admin', 'admin123', 'Administrator', 'Admin'),
                        (2, 'manager', 'manager123', 'Manager', 'Manajemen')
                    ])

def load(key):
    """Load all records from a SQLite table and return as list of dicts."""
    try:
        with get_db() as conn:
            cur = conn.execute(f"SELECT * FROM {key}")
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        print(f"Error loading {key}: {e}")
        return []

def save(key, data):
    """Save records to SQLite table by clearing and re-inserting (API compatible with JSON flow)."""
    with get_db() as conn:
        conn.execute(f"DELETE FROM {key}")
        if not data:
            return
        cur = conn.execute(f"PRAGMA table_info({key})")
        valid_cols = [r['name'] for r in cur.fetchall()]
        
        for row in data:
            filtered = {k: v for k, v in row.items() if k in valid_cols}
            if not filtered:
                continue
            cols = ', '.join(f'"{k}"' for k in filtered.keys())
            vals = tuple(filtered.values())
            q = ', '.join('?' for _ in filtered)
            conn.execute(f'INSERT INTO {key} ({cols}) VALUES ({q})', vals)

def next_id(items):
    return max((i.get('id', 0) for i in items), default=0) + 1

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def format_rupiah(value):
    try:
        return f"Rp {int(value):,}".replace(',', '.')
    except:
        return "Rp 0"

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
