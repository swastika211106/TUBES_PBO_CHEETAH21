import re

with open('dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

clean_top = """{% extends "base.html" %}
{% set active = "dashboard" %}
{% block page_title %}<i class="emote-animate" style="font-style:normal; margin-right:8px;">📊</i> Dashboard{% endblock %}

{% block content %}"""

content = re.sub(r'\{% extends "base\.html" %\}.*?\{% block content %\}', clean_top, content, flags=re.DOTALL)

clean_bottom = """<!-- MODAL DETAIL DASHBOARD -->
<div class="modal-overlay" id="modalDetail">
  <div class="modal" style="width: 800px; max-width: 90vw;">
    <div class="modal-header">
      <span class="modal-title" id="modalDetailTitle">Detail</span>
      <button class="modal-close" onclick="closeDetailModal()"><i class="fas fa-xmark"></i></button>
    </div>
    <div class="modal-body" style="max-height: 400px; overflow-y: auto;">
      <table class="table">
        <thead id="modalDetailHead"></thead>
        <tbody id="modalDetailBody"></tbody>
      </table>
    </div>
  </div>
</div>
<script>
  const invData = {{ inventory_data | safe }};
  const inData = {{ masuk_data | safe }};
  const outData = {{ keluar_data | safe }};

  function openDetailModal(type) {
    const title = document.getElementById('modalDetailTitle');
    const thead = document.getElementById('modalDetailHead');
    const tbody = document.getElementById('modalDetailBody');
    tbody.innerHTML = '';
    thead.innerHTML = '';
    
    if (type === 'jenis' || type === 'stok') {
      title.textContent = 'Detail Master Barang';
      thead.innerHTML = '<tr><th>Kode</th><th>Kategori</th><th>Nama</th><th>Stok</th><th>Harga Beli</th><th>Harga Jual</th></tr>';
      invData.forEach(i => {
        tbody.innerHTML += `<tr><td>${i.code}</td><td>${i.category||'-'}</td><td>${i.name}</td><td>${i.stock||0}</td><td>Rp ${(i.buyPrice||0).toLocaleString('id-ID')}</td><td>Rp ${(i.sellPrice||0).toLocaleString('id-ID')}</td></tr>`;
      });
    } else if (type === 'masuk' || type === 'nilaibeli') {
      title.textContent = 'Detail Transaksi Barang Masuk';
      thead.innerHTML = '<tr><th>ID</th><th>Tanggal</th><th>Kategori</th><th>Barang</th><th>Jumlah</th><th>Harga Beli</th><th>Total Beli</th></tr>';
      inData.forEach(i => {
        let total = (i.quantity||0) * (i.buyPrice||0);
        tbody.innerHTML += `<tr><td>${i.transactionId||'-'}</td><td>${i.date||'-'}</td><td>${i.category||'-'}</td><td>${i.itemName||'-'}</td><td>${i.quantity||0}</td><td>Rp ${(i.buyPrice||0).toLocaleString('id-ID')}</td><td>Rp ${total.toLocaleString('id-ID')}</td></tr>`;
      });
    } else if (type === 'keluar' || type === 'nilaijual' || type === 'keuntungan') {
      title.textContent = 'Detail Transaksi Barang Keluar';
      thead.innerHTML = '<tr><th>ID</th><th>Tanggal</th><th>Barang</th><th>Jumlah</th><th>Harga Jual</th><th>Total Jual</th><th>Keuntungan</th></tr>';
      outData.forEach(i => {
        let h_jual = i.sellPrice || 0;
        let h_beli = i.buyPrice || 0;
        let t_jual = (i.quantity||0) * h_jual;
        let profit = (i.quantity||0) * (h_jual - h_beli);
        tbody.innerHTML += `<tr><td>${i.transactionId||'-'}</td><td>${i.date||'-'}</td><td>${i.itemName||'-'}</td><td>${i.quantity||0}</td><td>Rp ${h_jual.toLocaleString('id-ID')}</td><td>Rp ${t_jual.toLocaleString('id-ID')}</td><td style="color:${profit >= 0 ? '#10b981' : '#ef4444'}">Rp ${profit.toLocaleString('id-ID')}</td></tr>`;
      });
    }
    
    document.getElementById('modalDetail').classList.add('show');
  }

  function closeDetailModal() {
    document.getElementById('modalDetail').classList.remove('show');
  }
</script>
{% endblock %}"""

content = re.sub(r'<!-- MODAL DETAIL DASHBOARD -->.*\{% endblock %\}', clean_bottom, content, flags=re.DOTALL)

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
