import re

with open('dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Insert the scripts at the bottom before {% endblock %}
scripts = """
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
<script>
  function exportDashboardExcel() {
    const wb = XLSX.utils.book_new();
    
    // Sheet 1: Ringkasan
    const summaryData = [
      ["LAPORAN RINGKASAN TOKO"],
      [""],
      ["Total Jenis Barang", invData.length],
      ["Total Stok Barang", invData.reduce((sum, item) => sum + (parseInt(item.stock)||0), 0)],
      ["Total Transaksi Masuk", inData.length],
      ["Total Transaksi Keluar", outData.length],
      ["Total Nilai Beli", "Rp " + inData.reduce((sum, item) => sum + (item.quantity||0)*(item.buyPrice||0), 0).toLocaleString('id-ID')],
      ["Total Nilai Jual", "Rp " + outData.reduce((sum, item) => sum + (item.quantity||0)*(item.sellPrice||0), 0).toLocaleString('id-ID')],
      ["Total Keuntungan", "Rp " + outData.reduce((sum, item) => sum + ((item.quantity||0)*(item.sellPrice||0) - (item.quantity||0)*(item.buyPrice||0)), 0).toLocaleString('id-ID')],
    ];
    const ws1 = XLSX.utils.aoa_to_sheet(summaryData);
    // make cols wider
    ws1['!cols'] = [{wch: 25}, {wch: 20}];
    XLSX.utils.book_append_sheet(wb, ws1, "Ringkasan Dasbor");
    
    // Sheet 2: Master Barang
    const invSheetData = invData.map(i => ({
      "Kode": i.code, "Kategori": i.category||'-', "Nama": i.name, "Stok": i.stock, "Harga Beli": i.buyPrice, "Harga Jual": i.sellPrice
    }));
    const ws2 = XLSX.utils.json_to_sheet(invSheetData);
    XLSX.utils.book_append_sheet(wb, ws2, "Master Barang");
    
    // Sheet 3: Barang Masuk
    const inSheetData = inData.map(i => ({
      "ID Transaksi": i.transactionId, "Tanggal": i.date, "Kategori": i.category||'-', "Nama Barang": i.itemName, "Jumlah": i.quantity, "Total Beli": (i.quantity||0) * (i.buyPrice||0)
    }));
    const ws3 = XLSX.utils.json_to_sheet(inSheetData);
    XLSX.utils.book_append_sheet(wb, ws3, "Riwayat Barang Masuk");

    // Sheet 4: Barang Keluar
    const outSheetData = outData.map(i => {
      let hb = i.buyPrice || 0;
      let hj = i.sellPrice || 0;
      let invItem = invData.find(x => x.code === i.itemCode);
      if(invItem){ if(!hj) hj=invItem.sellPrice||0; if(!hb) hb=invItem.buyPrice||0; }
      return {
        "ID Transaksi": i.transactionId, "Tanggal": i.date, "Nama Barang": i.itemName, "Jumlah Terjual": i.quantity, "Total Jual": i.quantity * hj, "Keuntungan": i.quantity * (hj - hb)
      }
    });
    const ws4 = XLSX.utils.json_to_sheet(outSheetData);
    XLSX.utils.book_append_sheet(wb, ws4, "Riwayat Barang Keluar");

    XLSX.writeFile(wb, "Laporan_Kinerja_Toko.xlsx");
  }

  function exportDashboardPDF() {
    const printDiv = document.createElement('div');
    printDiv.style.padding = '30px';
    printDiv.style.fontFamily = 'Arial, sans-serif';
    printDiv.style.color = '#333';
    
    let invTable = `<table border="1" cellpadding="5" style="width:100%; border-collapse:collapse; margin-bottom:20px; font-size:12px;">
      <tr style="background:#f1f5f9;"><th>Kode</th><th>Kategori</th><th>Nama Barang</th><th>Stok</th><th>H. Beli</th><th>H. Jual</th></tr>`;
    invData.slice(0, 15).forEach(i => {
      invTable += `<tr><td>${i.code}</td><td>${i.category||'-'}</td><td>${i.name}</td><td>${i.stock||0}</td><td>Rp ${(i.buyPrice||0).toLocaleString('id-ID')}</td><td>Rp ${(i.sellPrice||0).toLocaleString('id-ID')}</td></tr>`;
    });
    invTable += `</table>`;

    let outTable = `<table border="1" cellpadding="5" style="width:100%; border-collapse:collapse; margin-bottom:20px; font-size:12px;">
      <tr style="background:#f1f5f9;"><th>Tanggal</th><th>Nama Barang</th><th>Jumlah Terjual</th><th>Keuntungan</th></tr>`;
    outData.slice(0, 15).forEach(i => {
      let hb = i.buyPrice || 0; let hj = i.sellPrice || 0;
      let invItem = invData.find(x => x.code === i.itemCode);
      if(invItem){ if(!hj) hj=invItem.sellPrice||0; if(!hb) hb=invItem.buyPrice||0; }
      let profit = (i.quantity||0) * (hj - hb);
      outTable += `<tr><td>${i.date}</td><td>${i.itemName}</td><td>${i.quantity}</td><td style="color:${profit>0?'green':'red'}">Rp ${profit.toLocaleString('id-ID')}</td></tr>`;
    });
    outTable += `</table>`;

    printDiv.innerHTML = `
      <h2 style="text-align:center;margin-bottom:5px; color:#0f172a;">Laporan Kinerja & Pengembangan Toko</h2>
      <p style="text-align:center; font-size:12px; margin-bottom:20px; color:#64748b;">Dicetak pada: ${new Date().toLocaleString('id-ID')}</p>
      <hr style="border:0; border-top:2px solid #cbd5e1; margin-bottom:20px;"/>
      
      <h3 style="color:#0f172a; margin-bottom:10px;">1. Ringkasan Eksekutif</h3>
      <table border="1" cellpadding="8" style="width:100%; border-collapse:collapse; margin-bottom:20px; font-size:14px; text-align:left;">
        <tr>
          <th style="background:#f1f5f9; width:25%;">Total Jenis Barang</th><td>${invData.length}</td>
          <th style="background:#f1f5f9; width:25%;">Total Keuntungan</th>
          <td style="font-weight:bold; color:green;">Rp ${outData.reduce((sum, item) => sum + ((item.quantity||0)*(item.sellPrice||0) - (item.quantity||0)*(item.buyPrice||0)), 0).toLocaleString('id-ID')}</td>
        </tr>
        <tr>
          <th style="background:#f1f5f9;">Total Transaksi Masuk</th><td>${inData.length}</td>
          <th style="background:#f1f5f9;">Total Transaksi Keluar</th><td>${outData.length}</td>
        </tr>
      </table>
      
      <h3 style="color:#0f172a; margin-bottom:10px;">2. Daftar Master Barang Saat Ini (Top 15)</h3>
      ${invTable}

      <h3 style="color:#0f172a; margin-bottom:10px;">3. Riwayat Penjualan Terakhir (Top 15)</h3>
      ${outTable}
      
      <p style="text-align:center; font-size:10px; margin-top:40px; color:#94a3b8;">Laporan ini di-generate otomatis oleh Sistem Inventory.</p>
    `;
    
    const opt = {
      margin: 0.4,
      filename: 'Laporan_Pengembangan_Toko.pdf',
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' }
    };
    html2pdf().set(opt).from(printDiv).save();
  }
</script>
{% endblock %}
"""

# Replace the last {% endblock %} with our scripts + {% endblock %}
content = re.sub(r'\{%\s*endblock\s*%\}$', scripts, content)

# Inject the buttons above the STAT CARDS ROW 1
buttons_html = """
<!-- ACTION BUTTONS -->
<div style="display: flex; gap: 12px; margin-bottom: 24px;">
  <button class="btn btn-primary" onclick="exportDashboardPDF()" style="background:#dc2626; border-color:#dc2626; box-shadow: 0 4px 6px -1px rgba(220, 38, 38, 0.2);">
    <i class="fas fa-file-pdf" style="margin-right:6px;"></i> Cetak Laporan PDF
  </button>
  <button class="btn btn-success" onclick="exportDashboardExcel()" style="background:#16a34a; border-color:#16a34a; box-shadow: 0 4px 6px -1px rgba(22, 163, 74, 0.2);">
    <i class="fas fa-file-excel" style="margin-right:6px;"></i> Export Laporan Excel
  </button>
</div>

<!-- STAT CARDS ROW 1 -->
"""

content = content.replace('<!-- STAT CARDS ROW 1 -->', buttons_html)

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

