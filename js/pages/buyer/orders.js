'use strict';
// ── ShopHub ── pages/buyer/orders.js ────────────────────

const session = Auth.requireRole('buyer');

injectNav([
  { href:'/pages/buyer/account.html', label:'My Account' },
  { href:'/',                         label:'Shop' },
  { href:'/pages/buyer/cart.html',    label:'Cart' },
  { href:'/pages/buyer/orders.html',  label:'Orders', active:true },
]);

(async function init() {
  const [orders, balance] = await Promise.all([
    API.getOrders(),
    API.getWallet(),
  ]);

  const totalSpent = orders.reduce((s, o) => s + o.total, 0);
  const totalItems = orders.reduce((s, o) => s + o.items.reduce((r, i) => r + i.qty, 0), 0);

  document.getElementById('st-orders').textContent  = orders.length;
  document.getElementById('st-spent').textContent   = fmt(totalSpent);
  document.getElementById('st-items').textContent   = totalItems;
  document.getElementById('wallet-bal').textContent = fmt(balance);

  if (!orders.length) {
    document.getElementById('orders-empty').style.display      = '';
    document.getElementById('orders-table-wrap').style.display = 'none';
  } else {
    document.getElementById('orders-tbody').innerHTML = orders.map(o => `
      <tr>
        <td class="fw-bold">#${o.id}</td>
        <td style="font-size:12px">
          ${o.items.map(i => `<div>${i.name} <span class="text-muted">×${i.qty}</span></div>`).join('')}
        </td>
        <td class="fw-bold" style="color:var(--primary)">${fmt(o.total)}</td>
        <td><span class="badge-completed">${o.status}</span></td>
        <td>${fmtDateTime(o.createdAt)}</td>
      </tr>`).join('');
  }
})();
