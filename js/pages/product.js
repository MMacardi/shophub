'use strict';
// ── ShopHub ── pages/product.js ──────────────────────────

const params    = new URLSearchParams(location.search);
const productId = parseInt(params.get('id'));
const session   = Auth.getSession();
let   product   = null;
let   myRating  = 0;

if (!productId) { window.location.href = '/'; }

// ── Stars helpers ────────────────────────────────────────
function stars(rating, max = 5) {
  const full  = Math.floor(rating);
  const half  = rating - full >= 0.5;
  let   html  = '';
  for (let i = 1; i <= max; i++) {
    if (i <= full)              html += '<i class="bi bi-star-fill pd-star-filled"></i>';
    else if (i === full + 1 && half) html += '<i class="bi bi-star-half pd-star-filled"></i>';
    else                        html += '<i class="bi bi-star pd-star-empty"></i>';
  }
  return html;
}

// ── Render product ───────────────────────────────────────
function renderProduct(p) {
  product = p;
  document.title = `${p.name} — ShopHub`;

  document.getElementById('pd-emoji').textContent = p.emoji;
  if (p.originalPrice) document.getElementById('pd-sale-badge').style.display = '';

  // Breadcrumb
  document.getElementById('breadcrumb').innerHTML =
    `<a href="/" style="color:inherit">Home</a> ›
     <a href="#" onclick="window.location='/?cat=${p.category}'" style="color:inherit">${p.category}</a> ›
     <span style="color:#333">${p.name}</span>`;

  // Price
  const priceEl = document.getElementById('pd-price-row');
  if (p.originalPrice) {
    priceEl.innerHTML =
      `<span class="pd-sale-price">¥${p.price}</span>
       <span class="pd-orig-price">¥${p.originalPrice}</span>
       <span class="discount-pill" style="font-size:13px;">−${p.discountPct}%</span>`;
  } else {
    priceEl.innerHTML = `<span class="pd-sale-price">¥${p.price}</span>`;
  }

  // Stock
  const stockEl = document.getElementById('pd-stock');
  if (p.stock === 0) {
    stockEl.innerHTML = '<span class="stock-badge stock-out">Out of stock</span>';
    document.getElementById('pd-add-btn').disabled = true;
  } else {
    stockEl.innerHTML = `<span class="stock-badge stock-ok">${p.stock} in stock</span>`;
  }

  // Auth state for buy button
  if (!session) {
    document.getElementById('pd-add-btn').style.display   = 'none';
    document.getElementById('pd-login-btn').style.display = '';
  } else if (session.role !== 'buyer') {
    document.getElementById('pd-add-btn').style.display   = 'none';
    document.getElementById('pd-login-btn').style.display = 'none';
  }

  // Name / category
  document.getElementById('pd-category').innerHTML =
    `<span class="badge bg-secondary">${p.category}</span>`;
  document.getElementById('pd-name').textContent = p.name;

  // Rating
  document.getElementById('pd-stars').innerHTML =
    stars(p.avgRating) + `<span class="pd-avg-num">${p.avgRating || 0}</span>`;
  document.getElementById('pd-review-link').textContent =
    `${p.reviewCount} review${p.reviewCount !== 1 ? 's' : ''}`;

  // Seller (clickable link + shop rating badge)
  const sellerRatingBadge = p.sellerReviewCount
    ? `<span class="pd-seller-rating" title="${p.sellerReviewCount} reviews across this shop">★ ${p.sellerRating} shop rating</span>`
    : '';
  document.getElementById('pd-seller').innerHTML =
    `🏪 Sold by <a href="/pages/store.html?id=${p.sellerId}" class="pd-seller-link">${p.sellerName}</a>${sellerRatingBadge}`;

  // Description
  document.getElementById('pd-desc').textContent = p.description;

  // Details table
  document.getElementById('pd-details-tbody').innerHTML = [
    ['Category',    p.category],
    ['Seller',      p.sellerName],
    ['Stock',       p.stock > 0 ? `${p.stock} units available` : 'Out of stock'],
    ['Sale Price',  `¥${p.price}`],
    ...(p.originalPrice ? [['Original Price', `¥${p.originalPrice}`]] : []),
  ].map(([k, v]) => `<tr><th>${k}</th><td>${v}</td></tr>`).join('');

  document.getElementById('product-loading').style.display = 'none';
  document.getElementById('product-main').style.display    = '';

  // Top bar
  if (session) {
    document.getElementById('topbar-left').innerHTML =
      `<span>Hello, <strong>${session.username}</strong>
       <span class="sh-role-badge sh-role-${session.role}" style="font-size:10px">${session.role}</span></span>`;
  }
}

// ── Add to cart ──────────────────────────────────────────
async function addToCart() {
  if (!session || session.role !== 'buyer') { window.location.href = '/login.html'; return; }
  const btn = document.getElementById('pd-add-btn');
  btn.disabled = true;
  try {
    await API.addToCart(productId, 1);
    toast('Added to cart! 🛒');
  } catch (err) {
    toast(err.message || 'Could not add to cart.', 'error');
  } finally {
    btn.disabled = false;
  }
}

// ── Render reviews ───────────────────────────────────────
function renderReviews(reviews) {
  const section = document.getElementById('reviews-section');
  const list    = document.getElementById('reviews-list');
  const empty   = document.getElementById('reviews-empty');
  section.style.display = '';

  // Summary
  const count = reviews.length;
  const avg   = count ? +(reviews.reduce((s, r) => s + r.rating, 0) / count).toFixed(1) : 0;
  document.getElementById('avg-score').textContent = avg || '—';
  document.getElementById('avg-stars').innerHTML   = stars(avg);
  document.getElementById('avg-label').textContent =
    count ? `${count} review${count !== 1 ? 's' : ''}` : 'No reviews yet';

  // Distribution bars
  const dist = [5,4,3,2,1].map(n => ({
    n, count: reviews.filter(r => r.rating === n).length,
  }));
  document.getElementById('rating-bars').innerHTML = dist.map(d => {
    const pct = count ? Math.round(d.count / count * 100) : 0;
    return `<div class="pd-bar-row">
      <span class="pd-bar-label">${d.n}★</span>
      <div class="pd-bar-track"><div class="pd-bar-fill" style="width:${pct}%"></div></div>
      <span class="pd-bar-count">${d.count}</span>
    </div>`;
  }).join('');

  // Review form gate
  if (session && session.role === 'buyer') {
    const already = reviews.find(r => r.userId === session.id);
    if (already) {
      document.getElementById('review-gate').style.display = '';
      document.getElementById('review-gate').textContent   = '✅ You have already reviewed this product.';
    } else {
      document.getElementById('review-form-wrap').style.display = '';
    }
  } else if (!session) {
    document.getElementById('review-gate').style.display = '';
    document.getElementById('review-gate').innerHTML = '<a href="/login.html">Sign in</a> to leave a review.';
  }

  // List
  if (!reviews.length) {
    list.innerHTML = ''; empty.style.display = ''; return;
  }
  empty.style.display = 'none';

  const myReviews = session ? reviews.filter(r => r.userId === session.id) : [];

  list.innerHTML = reviews.map(r => `
    <div class="pd-review-card">
      <div class="d-flex justify-content-between align-items-start">
        <div>
          <span class="pd-reviewer">👤 ${r.username}</span>
          <span class="ms-2">${stars(r.rating)}</span>
        </div>
        <div class="d-flex align-items-center gap-2">
          <span class="pd-review-date">${fmtDate(r.createdAt)}</span>
          ${(session && (r.userId === session.id || session.role === 'admin'))
            ? `<button class="btn-icon danger" title="Delete" onclick="removeReview(${r.id})"><i class="bi bi-trash" style="font-size:13px"></i></button>`
            : ''}
        </div>
      </div>
      <p class="pd-review-text">${escapeHtml(r.comment)}</p>
    </div>`).join('');
}

// ── Star picker ──────────────────────────────────────────
document.querySelectorAll('.pick-star').forEach(el => {
  el.addEventListener('click', () => {
    myRating = parseInt(el.dataset.v);
    document.querySelectorAll('.pick-star').forEach((s, i) => {
      s.classList.toggle('active', i < myRating);
    });
  });
  el.addEventListener('mouseenter', () => {
    const hv = parseInt(el.dataset.v);
    document.querySelectorAll('.pick-star').forEach((s, i) => {
      s.classList.toggle('hover', i < hv);
    });
  });
});
document.getElementById('star-picker')?.addEventListener('mouseleave', () => {
  document.querySelectorAll('.pick-star').forEach(s => s.classList.remove('hover'));
});

// ── Submit review ────────────────────────────────────────
async function submitReview() {
  if (!myRating) { toast('Please select a star rating.', 'warning'); return; }
  const comment = document.getElementById('review-comment').value.trim();
  if (!comment)  { toast('Please write a comment.', 'warning'); return; }

  try {
    await API.createReview(productId, myRating, comment);
    toast('Review published! Thank you 🎉');
    await loadReviews();
  } catch (err) {
    toast(err.message || 'Could not publish review.', 'error');
  }
}

async function removeReview(rid) {
  if (!confirm('Delete this review?')) return;
  try {
    await API.deleteReview(productId, rid);
    toast('Review deleted.', 'info');
    await loadReviews();
  } catch (err) {
    toast(err.message || 'Could not delete review.', 'error');
  }
}

async function loadReviews() {
  // Reset form state
  document.getElementById('review-form-wrap').style.display = 'none';
  document.getElementById('review-gate').style.display      = 'none';
  const reviews = await API.getReviews(productId);
  renderReviews(reviews);
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}

// ── Init ─────────────────────────────────────────────────
(async function init() {
  try {
    const data = await API.getProducts({ id: productId });
    // Fetch single product
    const res  = await fetch(`/api/products/${productId}`);
    const json = await res.json();
    renderProduct(json.product);
    await loadReviews();
  } catch {
    document.getElementById('product-loading').textContent = 'Product not found.';
  }
})();
