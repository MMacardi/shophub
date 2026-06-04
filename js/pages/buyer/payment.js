'use strict';
// ── ShopHub ── pages/buyer/payment.js ───────────────────

const session = Auth.requireRole('buyer');

injectNav([
  { href:'/pages/buyer/account.html',   label:'My Account' },
  { href:'/',                           label:'Shop' },
  { href:'/pages/buyer/cart.html',      label:'Cart' },
  { href:'/pages/buyer/payment.html',   label:'Checkout', active:true },
  { href:'/pages/buyer/orders.html',    label:'Orders' },
]);

let orderTotal = 0;

async function refreshWallet() {
  const balance = await API.getWallet();
  document.getElementById('wallet-balance').textContent   = fmt(balance);
  document.getElementById('wallet-after-text').textContent =
    `After payment: ${fmt(Math.max(0, balance - orderTotal))}`;
  const insufficient = balance < orderTotal;
  document.getElementById('insufficient-warn').classList.toggle('d-none', !insufficient);
  document.getElementById('pay-btn').disabled = insufficient;
}

async function topUpWallet() {
  const amt = parseFloat(document.getElementById('topup-amount').value);
  if (!amt || amt <= 0) { toast('Enter a valid amount.', 'warning'); return; }
  try {
    await API.topupWallet(amt);
    document.getElementById('topup-amount').value = '';
    toast(`Added ${fmt(amt)} to your wallet!`);
    await refreshWallet();
  } catch (err) {
    toast(err.message || 'Failed to top up wallet.', 'error');
  }
}

async function confirmPayment() {
  document.getElementById('pay-btn').disabled = true;
  try {
    const order = await API.checkout();
    document.getElementById('payment-view').style.display = 'none';
    document.getElementById('success-view').style.display = '';
    document.getElementById('success-msg-text').textContent =
      `Order #${order.id} placed! ${fmt(order.total)} deducted from your wallet.`;
    setTimeout(() => { window.location.href = '/pages/buyer/orders.html'; }, 3000);
  } catch (err) {
    document.getElementById('pay-btn').disabled = false;
    toast(err.message || 'Payment failed.', 'error');
  }
}

// ── Init ─────────────────────────────────────────────────
(async function init() {
  const data = await API.getCart();
  const cart = data.cart || [];

  if (!cart.length) {
    document.getElementById('payment-view').style.display = 'none';
    document.getElementById('empty-view').style.display   = '';
    return;
  }

  let subtotal = 0;
  document.getElementById('order-items').innerHTML = cart.map(c => {
    const p = c.product;
    if (!p) return '';
    const lineTotal = p.price * c.qty;
    subtotal += lineTotal;
    return `<div class="order-row d-flex justify-content-between align-items-center">
      <div class="d-flex align-items-center gap-2">
        <span style="font-size:20px">${p.emoji}</span>
        <div>
          <div style="font-size:13px;font-weight:600">${p.name}</div>
          <div style="font-size:11px;color:#999">Qty: ${c.qty} × ${fmt(p.price)}</div>
        </div>
      </div>
      <div class="fw-bold" style="color:var(--primary)">${fmt(lineTotal)}</div>
    </div>`;
  }).join('');

  orderTotal = subtotal;
  document.getElementById('pay-subtotal').textContent = fmt(subtotal);
  document.getElementById('pay-total').textContent    = fmt(subtotal);
  await refreshWallet();
})();
