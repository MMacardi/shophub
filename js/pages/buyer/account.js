'use strict';
// ── ShopHub ── pages/buyer/account.js ───────────────────

const session = Auth.requireRole('buyer');

injectNav([
  { href:'/pages/buyer/account.html', label:'My Account', active:true },
  { href:'/',                         label:'Shop' },
  { href:'/pages/buyer/cart.html',    label:'Cart' },
  { href:'/pages/buyer/orders.html',  label:'My Orders' },
]);

document.getElementById('p-username').textContent = session.username;
document.getElementById('p-email').textContent    = session.email || '—';
document.getElementById('welcome-sub').textContent = `Welcome back, ${session.username}!`;

async function refreshAll() {
  const [orders, balance, cart] = await Promise.all([
    API.getOrders(),
    API.getWallet(),
    API.getCart(),
  ]);

  const totalSpent = orders.reduce((s, o) => s + o.total, 0);
  const totalItems = orders.reduce((s, o) => s + o.items.reduce((r, i) => r + i.qty, 0), 0);

  document.getElementById('st-orders').textContent  = orders.length;
  document.getElementById('st-spent').textContent   = fmt(totalSpent);
  document.getElementById('st-items').textContent   = totalItems;
  document.getElementById('st-cart').textContent    = cart.count || 0;
  document.getElementById('wallet-balance').textContent = fmt(balance);

  const recent = orders.slice(0, 5);
  const empty  = document.getElementById('recent-empty');
  const list   = document.getElementById('recent-orders');

  if (!recent.length) { list.innerHTML = ''; empty.style.display = ''; return; }
  empty.style.display = 'none';

  list.innerHTML = `
    <div class="table-responsive">
      <table class="table mb-0">
        <thead><tr><th>Order #</th><th>Items</th><th>Total</th><th>Date</th></tr></thead>
        <tbody>
          ${recent.map(o => `
            <tr>
              <td class="fw-bold">#${o.id}</td>
              <td style="font-size:12px">${o.items.map(i => `${i.name} ×${i.qty}`).join(', ')}</td>
              <td class="fw-bold" style="color:var(--primary)">${fmt(o.total)}</td>
              <td style="font-size:12px">${fmtDate(o.createdAt)}</td>
            </tr>`).join('')}
        </tbody>
      </table>
    </div>`;
}

async function topUp() {
  const amt = parseFloat(document.getElementById('topup-amount').value);
  if (!amt || amt <= 0) { toast('Enter a valid amount.', 'warning'); return; }
  try {
    await API.topupWallet(amt);
    document.getElementById('topup-amount').value = '';
    toast(`Added ${fmt(amt)} to your wallet!`);
    await refreshAll();
  } catch (err) {
    toast(err.message || 'Failed to top up.', 'error');
  }
}

async function quickTop(amount) {
  try {
    await API.topupWallet(amount);
    toast(`Added ${fmt(amount)} to your wallet!`);
    await refreshAll();
  } catch (err) {
    toast(err.message || 'Failed to top up.', 'error');
  }
}

refreshAll();
