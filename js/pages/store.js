'use strict';
// ── ShopHub ── pages/store.js ────────────────────────────

const params   = new URLSearchParams(location.search);
const sellerId = parseInt(params.get('id'));
const session  = Auth.getSession();

if (!sellerId) { window.location.href = '/'; }

// ── Stars helpers ────────────────────────────────────────
function stars(rating, max = 5) {
  const full = Math.floor(rating);
  const half = rating - full >= 0.5;
  let html = '';
  for (let i = 1; i <= max; i++) {
    if (i <= full)               html += '<i class="bi bi-star-fill pd-star-filled"></i>';
    else if (i === full + 1 && half) html += '<i class="bi bi-star-half pd-star-filled"></i>';
    else                         html += '<i class="bi bi-star pd-star-empty"></i>';
  }
  return html;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}

// ── Render shop header ───────────────────────────────────
function renderHeader(seller) {
  document.title = `${seller.shopName} — ShopHub`;
  document.getElementById('breadcrumb').innerHTML =
    `<a href="/" style="color:inherit">Home</a> ›
     <span style="color:#333">${escapeHtml(seller.shopName)}</span>`;
  document.getElementById('store-name').textContent = seller.shopName;

  const ratingHtml = seller.reviewCount
    ? `${stars(seller.avgRating)} <span class="pd-avg-num">${seller.avgRating}</span>`
    : '<span class="text-muted">No ratings yet</span>';
  document.getElementById('store-rating').innerHTML = ratingHtml;

  document.getElementById('store-product-count').textContent =
    `${seller.productCount} product${seller.productCount !== 1 ? 's' : ''}`;
  document.getElementById('store-review-count').textContent =
    `${seller.reviewCount} customer review${seller.reviewCount !== 1 ? 's' : ''}`;
}

// ── Render products grid ─────────────────────────────────
function renderProducts(products) {
  const grid  = document.getElementById('store-products');
  const empty = document.getElementById('store-products-empty');
  if (!products.length) { grid.innerHTML = ''; empty.style.display = ''; return; }
  empty.style.display = 'none';

  grid.innerHTML = products.map(p => {
    const bg = CAT_BG[p.category] || 'bg-other';
    let action = '';
    if (!session) {
      action = `<a href="/login.html" class="btn-cart">Sign in to buy</a>`;
    } else if (session.role === 'buyer') {
      action = `<button class="btn-cart" onclick="addToCart(${p.id},event)">🛒 Add to Cart</button>`;
    }
    const priceBlock = p.originalPrice
      ? `<div class="d-flex align-items-baseline gap-2 flex-wrap">
           <div class="product-price">¥${p.price}</div>
           <div class="product-original">¥${p.originalPrice}</div>
           <span class="discount-pill">−${p.discountPct}%</span>
         </div>`
      : `<div class="product-price">¥${p.price}</div>`;
    const ratingHtml = p.reviewCount
      ? `<div class="product-rating">★ ${p.avgRating} <span class="product-rating-count">(${p.reviewCount})</span></div>`
      : '';
    return `
      <div class="col-6 col-sm-4 col-md-3">
        <div class="product-card" onclick="goToProduct(${p.id}, event)">
          <div class="product-img-box ${bg}">
            ${p.emoji}
            ${p.originalPrice ? `<span class="product-badge">SALE</span>` : ''}
            ${p.stock === 0 ? `<span class="product-badge" style="background:#888">OUT</span>` : ''}
          </div>
          <div class="product-info">
            <div class="product-name">${escapeHtml(p.name)}</div>
            ${ratingHtml}
            ${priceBlock}
            ${p.stock > 0 ? action : ''}
          </div>
        </div>
      </div>`;
  }).join('');
}

function goToProduct(id, event) {
  if (event && event.target.closest('.btn-cart, a')) return;
  window.location.href = `/pages/product.html?id=${id}`;
}

async function addToCart(productId, event) {
  event.stopPropagation();
  if (!session || session.role !== 'buyer') { window.location.href = '/login.html'; return; }
  try {
    await API.addToCart(productId, 1);
    if (typeof toast === 'function') toast('Added to cart! 🛒');
  } catch (err) {
    if (typeof toast === 'function') toast(err.message || 'Could not add to cart.', 'error');
  }
}

// ── Render shop-level reviews ────────────────────────────
function renderShopReviews(reviews) {
  const wrap  = document.getElementById('store-reviews');
  const empty = document.getElementById('store-reviews-empty');
  if (!reviews.length) { wrap.innerHTML = ''; empty.style.display = ''; return; }
  empty.style.display = 'none';

  wrap.innerHTML = reviews.map(r => `
    <div class="pd-review-card">
      <div class="d-flex justify-content-between align-items-start">
        <div>
          <span class="pd-reviewer">👤 ${escapeHtml(r.username)}</span>
          <span class="ms-2">${stars(r.rating)}</span>
        </div>
        <div class="pd-review-date">${(r.createdAt || '').slice(0, 10)}</div>
      </div>
      <p class="pd-review-text">${escapeHtml(r.comment)}</p>
    </div>`).join('');
}

// ── Tabs ─────────────────────────────────────────────────
function bindTabs() {
  document.querySelectorAll('.store-tabs .nav-link').forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      document.querySelectorAll('.store-tabs .nav-link').forEach(l => l.classList.remove('active'));
      link.classList.add('active');
      const tab = link.dataset.tab;
      document.getElementById('tab-products').style.display = tab === 'products' ? '' : 'none';
      document.getElementById('tab-reviews').style.display  = tab === 'reviews'  ? '' : 'none';
    });
  });
}

// ── Init ─────────────────────────────────────────────────
(async function init() {
  if (session) {
    document.getElementById('topbar-left').innerHTML =
      `<span>Hello, <strong>${session.username}</strong>
       <span class="sh-role-badge sh-role-${session.role}" style="font-size:10px">${session.role}</span></span>`;
  }
  try {
    const [seller, products, reviews] = await Promise.all([
      API.getSeller(sellerId),
      API.getSellerProducts(sellerId),
      API.getSellerReviews(sellerId),
    ]);
    if (!seller) throw new Error('not found');
    renderHeader(seller);
    renderProducts(products);
    renderShopReviews(reviews);
    bindTabs();
    document.getElementById('store-loading').style.display = 'none';
    document.getElementById('store-main').style.display    = '';
  } catch {
    document.getElementById('store-loading').textContent = 'Store not found.';
  }
})();
