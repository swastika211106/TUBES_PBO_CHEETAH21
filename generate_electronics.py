import os
import json
import datetime

data_dir = 'data'
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

def save(filename, data):
    with open(os.path.join(data_dir, f'{filename}.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

categories = [
    {'id': 1, 'name': 'PC & Laptop', 'description': 'Perangkat Komputer dan Laptop'},
    {'id': 2, 'name': 'Aksesoris Gaming', 'description': 'Keyboard mekanikal, mouse gaming'},
    {'id': 3, 'name': 'Audio & Visual', 'description': 'Speaker, headset, monitor'},
]
save('kategori', categories)

suppliers = [
    {'id': 1, 'name': 'PT Asusindo Global', 'contact': '0811111111', 'address': 'Jakarta'},
    {'id': 2, 'name': 'CV Razer Distribusi', 'contact': '0822222222', 'address': 'Bandung'},
    {'id': 3, 'name': 'Toko Sentra Komputer', 'contact': '0833333333', 'address': 'Surabaya'},
    {'id': 4, 'name': 'Mega Audio Nusantara', 'contact': '0844444444', 'address': 'Yogyakarta'},
    {'id': 5, 'name': 'Logitech Official Store', 'contact': '0855555555', 'address': 'Semarang'},
]
save('supplier', suppliers)

items = [
    {'id': 1, 'code': 'BRG001', 'name': 'PC Rakitan RTX 4070', 'category': 'PC & Laptop', 'stock': 3, 'unit': 'Unit', 'buyPrice': 20000000, 'sellPrice': 35000000},
    {'id': 2, 'code': 'BRG002', 'name': 'Laptop Gaming ROG', 'category': 'PC & Laptop', 'stock': 2, 'unit': 'Unit', 'buyPrice': 15000000, 'sellPrice': 25000000},
    {'id': 3, 'code': 'BRG003', 'name': 'Mechanical Keyboard', 'category': 'Aksesoris Gaming', 'stock': 10, 'unit': 'Pcs', 'buyPrice': 1000000, 'sellPrice': 2000000},
    {'id': 4, 'code': 'BRG004', 'name': 'Speaker Edifier', 'category': 'Audio & Visual', 'stock': 5, 'unit': 'Unit', 'buyPrice': 1000000, 'sellPrice': 2000000},
    {'id': 5, 'code': 'BRG005', 'name': 'Mouse Gaming Razer', 'category': 'Aksesoris Gaming', 'stock': 10, 'unit': 'Pcs', 'buyPrice': 500000, 'sellPrice': 1000000},
]
save('inventory', items)

def get_date(days_ago):
    return (datetime.date.today() - datetime.timedelta(days=days_ago)).strftime('%Y-%m-%d')

# 10 Incoming Transactions
in_txs = [
    (1, 'BRG001', 2, 20),
    (1, 'BRG001', 3, 18),
    (2, 'BRG002', 2, 16),
    (2, 'BRG002', 2, 15),
    (3, 'BRG003', 10, 14),
    (3, 'BRG003', 10, 12),
    (4, 'BRG004', 5, 10),
    (4, 'BRG004', 5, 8),
    (5, 'BRG005', 10, 6),
    (5, 'BRG005', 10, 5),
]

bm_data = []
for i, tx in enumerate(in_txs):
    item_id, code, qty, days = tx
    item = next(it for it in items if it['code'] == code)
    bm_data.append({
        'id': i + 1,
        'transactionId': f'TRX{i+1:03d}',
        'date': get_date(days),
        'itemCode': item['code'],
        'itemName': item['name'],
        'category': item['category'],
        'quantity': qty,
        'buyPrice': item['buyPrice'],
        'sellPrice': item['sellPrice'],
        'supplier': suppliers[i % len(suppliers)]['name']
    })
save('barang_masuk', bm_data)

# 7 Outgoing Transactions
out_txs = [
    ('BRG001', 2, 17),
    ('BRG002', 2, 13),
    ('BRG003', 5, 11),
    ('BRG003', 5, 9),
    ('BRG004', 5, 7),
    ('BRG005', 5, 4),
    ('BRG005', 5, 2),
]

bk_data = []
for i, tx in enumerate(out_txs):
    code, qty, days = tx
    item = next(it for it in items if it['code'] == code)
    bk_data.append({
        'id': i + 1,
        'transactionId': f'OUT{i+1:03d}',
        'date': get_date(days),
        'itemCode': item['code'],
        'itemName': item['name'],
        'quantity': qty,
        'buyPrice': item['buyPrice'],
        'sellPrice': item['sellPrice'],
        'destination': 'Pelanggan Toko'
    })
save('barang_keluar', bk_data)

print("Electronics mock data generated with exactly 35% profit!")
