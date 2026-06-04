'use strict';
// ── ShopHub ── pages/seller/stats.js ────────────────────

const session = Auth.requireRole('seller');

injectNav([
  { href:'/pages/seller/dashboard.html', label:'Dashboard' },
  { href:'/pages/seller/products.html',  label:'Products' },
  { href:'/pages/seller/stats.html',     label:'Statistics', active:true },
  { href:'/',                            label:'View Store' },
]);

(async function init() {
  const myOrders = await API.getOrders();

  let totalRevenue = 0, totalUnits = 0;
  const productSales   = {};
  const monthlyRevenue = {};

  myOrders.forEach(o => {
    const myItems = o.items.filter(i => i.sellerId === session.id);
    myItems.forEach(i => {
      const rev = i.price * i.qty;
      totalRevenue += rev;
      totalUnits   += i.qty;
      if (!productSales[i.productId])
        productSales[i.productId] = { name: i.name, qty: 0, revenue: 0 };
      productSales[i.productId].qty     += i.qty;
      productSales[i.productId].revenue += rev;
    });
    const month   = o.createdAt.substring(0, 7);
    const myTotal = myItems.reduce((s, i) => s + i.price * i.qty, 0);
    monthlyRevenue[month] = (monthlyRevenue[month] || 0) + myTotal;
  });

  document.getElementById('st-revenue').textContent = fmt(totalRevenue);
  document.getElementById('st-orders').textContent  = myOrders.length;
  document.getElementById('st-units').textContent   = totalUnits;
  document.getElementById('st-avg').textContent     = myOrders.length ? fmt(totalRevenue / myOrders.length) : '¥0';

  // ── Revenue chart ────────────────────────────────────────
  const months = Object.keys(monthlyRevenue).sort();
  if (months.length) {
    const ctx = document.getElementById('revenueChart').getContext('2d');
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: months.map(m => {
          const [y, mo] = m.split('-');
          return new Date(y, mo - 1).toLocaleString('en-GB', { month:'short', year:'2-digit' });
        }),
        datasets: [{
          label: 'Revenue (¥)',
          data: months.map(m => monthlyRevenue[m]),
          backgroundColor: 'rgba(255,68,0,.7)',
          borderColor: 'rgba(255,68,0,1)',
          borderWidth: 1, borderRadius: 6,
        }],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { callback: v => '¥' + v } } },
      },
    });
  } else {
    document.getElementById('revenueChart').style.display = 'none';
    document.getElementById('chart-empty').style.display  = '';
  }

  // ── Top products ─────────────────────────────────────────
  const topProds = Object.values(productSales).sort((a, b) => b.revenue - a.revenue).slice(0, 5);
  if (topProds.length) {
    document.getElementById('top-products').innerHTML = topProds.map((p, i) => `
      <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
        <div class="d-flex align-items-center gap-2">
          <span class="fw-bold text-muted" style="width:18px">#${i + 1}</span>
          <span style="font-size:12px">${p.name}</span>
        </div>
        <div class="text-end">
          <div class="fw-bold" style="color:var(--primary);font-size:13px">${fmt(p.revenue)}</div>
          <div class="text-muted" style="font-size:11px">${p.qty} sold</div>
        </div>
      </div>`).join('');
  }

  // ── Orders table ─────────────────────────────────────────
  if (!myOrders.length) {
    document.getElementById('orders-empty').style.display      = '';
    document.getElementById('orders-table-wrap').style.display = 'none';
  } else {
    document.getElementById('orders-count').textContent = `${myOrders.length} total`;
    document.getElementById('orders-tbody').innerHTML = myOrders.map(o => {
      const myItems = o.items.filter(i => i.sellerId === session.id);
      const myTotal = myItems.reduce((s, i) => s + i.price * i.qty, 0);
      return `<tr>
        <td class="fw-bold">#${o.id}</td>
        <td>${o.buyerName}</td>
        <td style="font-size:12px">${myItems.map(i => `${i.name} ×${i.qty}`).join('<br>')}</td>
        <td class="fw-bold" style="color:var(--primary)">${fmt(myTotal)}</td>
        <td><span class="badge-completed">${o.status}</span></td>
        <td>${fmtDateTime(o.createdAt)}</td>
      </tr>`;
    }).join('');
  }
})();
