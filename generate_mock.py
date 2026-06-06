import os
import json
import random
import datetime

data_dir = 'data'
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

def save(filename, data):
    with open(os.path.join(data_dir, f'{filename}.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

categories = [
    {'id': 1, 'name': 'Elektronik', 'description': 'Perangkat & Aksesoris Komputer'},
    {'id': 2, 'name': 'Fashion', 'description': 'Pakaian Pria dan Wanita'},
    {'id': 3, 'name': 'Kebutuhan Harian', 'description': 'Sembako dan bahan makanan'},
]
save('kategori', categories)

suppliers = [
    {'id': 1, 'name': 'PT Teknologi Maju', 'contact': '0812345001', 'address': 'Jl. Sudirman 1'},
    {'id': 2, 'name': 'CV Fashion Style', 'contact': '0812345002', 'address': 'Jl. Merdeka 2'},
    {'id': 3, 'name': 'Toko Grosir Abadi', 'contact': '0812345003', 'address': 'Jl. Pahlawan 3'},
    {'id': 4, 'name': 'Mega Elektronik', 'contact': '0812345004', 'address': 'Jl. Gajah Mada 4'},
    {'id': 5, 'name': 'Sembako Jaya', 'contact': '0812345005', 'address': 'Jl. Diponegoro 5'},
]
save('supplier', suppliers)

items = [
    {'id': 1, 'code': 'BRG001', 'name': 'Laptop Asus ROG', 'category': 'Elektronik', 'stock': 0, 'unit': 'Pcs', 'buyPrice': 15000000, 'sellPrice': 17500000},
    {'id': 2, 'code': 'BRG002', 'name': 'Mouse Logitech', 'category': 'Elektronik', 'stock': 0, 'unit': 'Pcs', 'buyPrice': 150000, 'sellPrice': 250000},
    {'id': 3, 'code': 'BRG003', 'name': 'Kemeja Flannel', 'category': 'Fashion', 'stock': 0, 'unit': 'Pcs', 'buyPrice': 75000, 'sellPrice': 120000},
    {'id': 4, 'code': 'BRG004', 'name': 'Beras Maknyus 5kg', 'category': 'Kebutuhan Harian', 'stock': 0, 'unit': 'Sak', 'buyPrice': 60000, 'sellPrice': 75000},
    {'id': 5, 'code': 'BRG005', 'name': 'Minyak Goreng 2L', 'category': 'Kebutuhan Harian', 'stock': 0, 'unit': 'Pouch', 'buyPrice': 28000, 'sellPrice': 34000},
]

bm_data = []
for i in range(10):
    item = random.choice(items)
    qty = random.randint(10, 50)
    sup = random.choice(suppliers)['name']
    dt = (datetime.date.today() - datetime.timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')
    bm = {
        'id': i + 1,
        'transactionId': f'TRX{i+1:03d}',
        'date': dt,
        'itemCode': item['code'],
        'itemName': item['name'],
        'category': item['category'],
        'quantity': qty,
        'buyPrice': item['buyPrice'],
        'sellPrice': item['sellPrice'],
        'supplier': sup
    }
    bm_data.append(bm)
    # add stock
    item['stock'] += qty

save('barang_masuk', bm_data)

bk_data = []
for i in range(7):
    # filter items that have stock
    valid_items = [it for it in items if it['stock'] > 0]
    if not valid_items: break
    item = random.choice(valid_items)
    qty = random.randint(1, min(5, item['stock']))
    dt = (datetime.date.today() - datetime.timedelta(days=random.randint(0, 10))).strftime('%Y-%m-%d')
    bk = {
        'id': i + 1,
        'transactionId': f'OUT{i+1:03d}',
        'date': dt,
        'itemCode': item['code'],
        'itemName': item['name'],
        'quantity': qty,
        'buyPrice': item['buyPrice'],
        'sellPrice': item['sellPrice'],
        'destination': 'Pelanggan Toko'
    }
    bk_data.append(bk)
    item['stock'] -= qty

save('barang_keluar', bk_data)
save('inventory', items)

print("Mock data generated successfully!")
