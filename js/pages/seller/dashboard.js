'use strict';
// ── ShopHub ── pages/seller/dashboard.js ────────────────

const session = Auth.requireRole('seller');

injectNav([
  { href:'/pages/seller/dashboard.html', label:'Dashboard', active:true },
  { href:'/pages/seller/products.html',  label:'Products' },
  { href:'/pages/seller/stats.html',     label:'Statistics' },
  { href:'/',                            label:'View Store' },
]);

(async function init() {
  document.getElementById('welcome-msg').textContent =
    `Welcome back, ${session.username}! 🏪 ${session.shopName || ''}`;

  const [products, orders] = await Promise.all([
    API.getMyProducts(),
    API.getOrders(),
  ]);

  const revenue = orders.reduce((s, o) =>
    s + o.items.filter(i => i.sellerId === session.id).reduce((r, i) => r + i.price * i.qty, 0), 0);
  const units = orders.reduce((s, o) =>
    s + o.items.filter(i => i.sellerId === session.id).reduce((r, i) => r + i.qty, 0), 0);

  document.getElementById('stat-products').textContent = products.length;
  document.getElementById('stat-orders').textContent   = orders.length;
  document.getElementById('stat-revenue').textContent  = fmt(revenue);
  document.getElementById('stat-units').textContent    = units;

  // ── Recent orders ──────────────────────────────────────
  const recent = [...orders].slice(0, 5);
  if (recent.length) {
    document.getElementById('recent-orders').innerHTML = `
      <div class="table-responsive">
        <table class="table">
          <thead><tr><th>Order #</th><th>Buyer</th><th>Items</th><th>My Revenue</th><th>Date</th></tr></thead>
          <tbody>
            ${recent.map(o => {
              const myItems = o.items.filter(i => i.sellerId === session.id);
              const myTotal = myItems.reduce((s, i) => s + i.price * i.qty, 0);
              return `<tr>
                <td>#${o.id}</td>
                <td>${o.buyerName}</td>
                <td style="font-size:12px">${myItems.map(i => `${i.name} ×${i.qty}`).join(', ')}</td>
                <td class="fw-bold" style="color:var(--primary)">${fmt(myTotal)}</td>
                <td>${fmtDate(o.createdAt)}</td>
              </tr>`;
            }).join('')}
          </tbody>
        </table>
      </div>`;
  }

  // ── Low stock ──────────────────────────────────────────
  const lowStock = products.filter(p => p.stock <= 10);
  if (lowStock.length) {
    document.getElementById('low-stock-card').style.display = '';
    document.getElementById('low-stock-list').innerHTML = lowStock.map(p =>
      `<div class="d-flex justify-content-between align-items-center py-2 border-bottom">
         <span>${p.emoji} ${p.name}</span>
         <span class="stock-badge ${p.stock === 0 ? 'stock-out' : 'stock-low'}">
           ${p.stock === 0 ? 'Out of stock' : `${p.stock} left`}
         </span>
       </div>`
    ).join('');
  }
})();
