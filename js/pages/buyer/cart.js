'use strict';
// ── ShopHub ── pages/buyer/cart.js ───────────────────────

const session = Auth.requireRole('buyer');

injectNav([
  { href:'/pages/buyer/account.html', label:'My Account' },
  { href:'/',                         label:'Shop' },
  { href:'/pages/buyer/cart.html',    label:'Cart', active:true },
  { href:'/pages/buyer/orders.html',  label:'Orders' },
]);

let cartCache = [];

function renderCart() {
  const itemsEl   = document.getElementById('cart-items');
  const emptyEl   = document.getElementById('cart-empty');
  const summaryEl = document.getElementById('cart-summary');

  if (!cartCache.length) {
    itemsEl.innerHTML = ''; emptyEl.style.display = ''; summaryEl.style.display = 'none'; return;
  }
  emptyEl.style.display = 'none'; summaryEl.style.display = '';

  let subtotal = 0, totalCount = 0;

  itemsEl.innerHTML = cartCache.map(item => {
    const p = item.product;
    if (!p) return '';
    const lineTotal = p.price * item.qty;
    subtotal   += lineTotal;
    totalCount += item.qty;
    return `
      <div class="cart-item" id="cart-row-${item.pid}">
        <div class="d-flex align-items-center gap-3">
          <div class="cart-emoji ${CAT_BG[p.category] || 'bg-other'}">${p.emoji}</div>
          <div class="flex-grow-1">
            <div class="cart-product-name">${p.name}</div>
            <div class="cart-seller">🏪 ${p.sellerName} · <span class="badge bg-secondary" style="font-size:10px">${p.category}</span></div>
            <div class="cart-price mt-1">${fmt(p.price)}</div>
          </div>
          <div class="d-flex flex-column align-items-end gap-2">
            <button class="btn-icon danger" onclick="removeItem(${item.pid})" title="Remove">
              <i class="bi bi-trash"></i>
            </button>
            <div class="d-flex align-items-center gap-2">
              <button class="qty-btn" onclick="changeQty(${item.pid},-1)">−</button>
              <span class="qty-display">${item.qty}</span>
              <button class="qty-btn" onclick="changeQty(${item.pid},1)">+</button>
            </div>
            <div class="fw-bold" style="color:var(--primary);font-size:14px">${fmt(lineTotal)}</div>
          </div>
        </div>
      </div>`;
  }).join('');

  document.getElementById('sum-count').textContent    = totalCount;
  document.getElementById('sum-subtotal').textContent = fmt(subtotal);
  document.getElementById('sum-total').textContent    = fmt(subtotal);
}

async function changeQty(pid, delta) {
  const item = cartCache.find(i => i.pid === pid);
  if (!item) return;
  const newQty = item.qty + delta;
  if (newQty <= 0) { await removeItem(pid); return; }
  const p = item.product;
  if (p && newQty > p.stock) { toast('Not enough stock available.', 'warning'); return; }
  try {
    await API.updateCartQty(pid, newQty);
    await loadCart();
  } catch (err) {
    toast(err.message || 'Failed to update cart.', 'error');
  }
}

async function removeItem(pid) {
  try {
    await API.removeFromCart(pid);
    await loadCart();
    toast('Item removed from cart.', 'info');
  } catch (err) {
    toast(err.message || 'Failed to remove item.', 'error');
  }
}

async function loadCart() {
  const data = await API.getCart();
  cartCache  = data.cart || [];
  renderCart();
}

loadCart();
