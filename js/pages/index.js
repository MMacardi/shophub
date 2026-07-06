'use strict';
// ── ShopHub ── pages/index.js ────────────────────────────

let activeCategory  = '';
let allProducts     = [];
let aiSuggestionIds = null;   // null = no AI filter active; array of ids = active
let aiSuggestionQ   = '';

// ── Filtering ────────────────────────────────────────────
function setSearch(term) {
  aiSuggestionIds = null;
  document.getElementById('search-input').value = term;
  filterProducts();
}

function setCategoryFilter(cat) {
  aiSuggestionIds = null;
  activeCategory = cat;
  filterProducts();
}

function filterProducts() {
  const q = document.getElementById('search-input').value.toLowerCase();
  let list;
  let label;

  if (aiSuggestionIds && aiSuggestionIds.length) {
    // AI Suggestion mode: only show products the bot just recommended.
    const idSet = new Set(aiSuggestionIds);
    list  = allProducts.filter(p => idSet.has(p.id));
    // Preserve the bot's relevance order
    list.sort((a, b) => aiSuggestionIds.indexOf(a.id) - aiSuggestionIds.indexOf(b.id));
    label = `🤖 AI Suggestion · "${aiSuggestionQ.length > 30 ? aiSuggestionQ.slice(0,30)+'…' : aiSuggestionQ}"`;
  } else {
    list = allProducts.filter(p => {
      const okCat  = !activeCategory || p.category === activeCategory;
      const okText = !q || p.name.toLowerCase().includes(q) || p.category.toLowerCase().includes(q);
      return okCat && okText && p.stock > 0;
    });
    label = activeCategory || (q ? `"${q}"` : 'All Products');
  }

  document.getElementById('products-section-title').textContent = label;
  document.getElementById('products-count').textContent = `${list.length} item${list.length !== 1 ? 's' : ''}`;
  renderProducts(list);
  renderAISuggestionChip();
}

function renderAISuggestionChip() {
  let chip = document.getElementById('ai-suggestion-chip');
  if (!aiSuggestionIds) { if (chip) chip.remove(); return; }
  if (!chip) {
    chip = document.createElement('div');
    chip.id = 'ai-suggestion-chip';
    chip.className = 'ai-suggestion-chip';
    const header = document.querySelector('#products-grid')?.parentElement
                   ?.querySelector('.section-header');
    if (header) header.parentElement.insertBefore(chip, header.nextSibling);
  }
  chip.innerHTML = `
    <span class="ai-chip-emoji">🤖</span>
    <div class="ai-chip-body">
      <div class="ai-chip-title">Showing AI Suggestions</div>
      <div class="ai-chip-q">"${escapeHtml(aiSuggestionQ)}" — ${aiSuggestionIds.length} item${aiSuggestionIds.length !== 1 ? 's' : ''}</div>
    </div>
    <button class="ai-chip-clear" onclick="clearAISuggestion()">Clear ✕</button>
  `;
}

function clearAISuggestion() {
  aiSuggestionIds = null;
  aiSuggestionQ   = '';
  filterProducts();
}

// Listen for bot search results emitted by the AI chat widget.
window.addEventListener('ai-suggestion', (ev) => {
  console.log('[Home] received ai-suggestion event', ev.detail);
  const { productIds, query } = ev.detail || {};
  if (!productIds || !productIds.length) return;
  aiSuggestionIds = productIds;
  aiSuggestionQ   = query || 'AI recommendation';
  activeCategory  = '';
  document.getElementById('search-input').value = '';
  filterProducts();
  document.getElementById('products-grid').scrollIntoView({ behavior: 'smooth' });
});

// ── Rendering ────────────────────────────────────────────
function renderProducts(products) {
  const grid  = document.getElementById('products-grid');
  const empty = document.getElementById('products-empty');
  const s     = Auth.getSession();

  if (!products.length) {
    grid.innerHTML = '';
    empty.style.display = '';
    return;
  }
  empty.style.display = 'none';

  grid.innerHTML = products.map(p => {
    const bg = CAT_BG[p.category] || 'bg-other';
    let action = '';
    if (!s) {
      action = `<a href="/login.html" class="btn-cart">Sign in to buy</a>`;
    } else if (s.role === 'buyer') {
      action = `<button class="btn-cart" onclick="addToCart(${p.id},event)">🛒 Add to Cart</button>`;
    } else {
      action = `<div style="font-size:11px;color:#bbb;text-align:center;margin-top:8px">Login as buyer to purchase</div>`;
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
      <div class="col-6 col-sm-4 col-md-3 col-lg-2">
        <div class="product-card" onclick="goToProduct(${p.id}, event)">
          <div class="product-img-box ${bg}">
            ${p.emoji}
            ${p.originalPrice ? `<span class="product-badge">SALE</span>` : ''}
          </div>
          <div class="product-info">
            <div class="product-name">${p.name}</div>
            <div class="product-seller">🏪 <a href="/pages/store.html?id=${p.sellerId}" onclick="event.stopPropagation()">${p.sellerName}</a></div>
            ${ratingHtml}
            ${priceBlock}
            ${action}
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
  const s = Auth.getSession();
  if (!s || s.role !== 'buyer') { window.location.href = '/login.html'; return; }
  try {
    const data  = await API.addToCart(productId, 1);
    const cnt   = data ? data.count : cartCount();
    const badge = document.getElementById('header-cart-count');
    if (badge) { badge.textContent = cnt; badge.style.display = ''; }
    toast('Added to cart! 🛒');
  } catch (err) {
    toast(err.message || 'Could not add to cart.', 'error');
  }
}

// ── Flash Sale ───────────────────────────────────────────
function renderFlashSale() {
  const discounted = allProducts.filter(p => p.originalPrice).slice(0, 4);
  const section = document.getElementById('flash-sale-section');
  const grid    = document.getElementById('flash-grid');
  if (!discounted.length) { section.style.display = 'none'; return; }
  section.style.display = '';

  grid.innerHTML = discounted.map((p, idx) => {
    const bgs = ['flash-img-1','flash-img-2','flash-img-3','flash-img-4'];
    const sold = 60 + ((p.id * 7) % 35);  // pseudo-random "% sold" for visual effect
    return `
      <div class="col-6 col-sm-3">
        <div class="flash-item" onclick="setSearch('${p.name.replace(/'/g, "\\'")}')">
          <div class="flash-img ${bgs[idx % 4]}">${p.emoji}</div>
          <div class="flash-name">${p.name}</div>
          <div class="flash-price">¥<span>${p.price}</span></div>
          <div class="flash-original">¥${p.originalPrice}</div>
          <div class="progress flash-progress"><div class="progress-bar bg-danger" style="width:${sold}%"></div></div>
          <div class="flash-sold">${sold}% sold</div>
        </div>
      </div>`;
  }).join('');
}

// ── Announcements ────────────────────────────────────────
async function loadAnnouncements() {
  const list = document.getElementById('announcements-list');
  try {
    const items = await API.getAnnouncements();
    if (!items.length) {
      list.innerHTML = '<li class="text-muted small">No announcements yet.</li>';
      return;
    }
    list.innerHTML = items.slice(0, 5).map(a => `
      <li title="${escapeAttr(a.content || a.title)}">
        <a href="#" onclick="showAnnouncement(${a.id});return false;">${escapeHtml(a.title)}</a>
      </li>`).join('');
    window._annCache = items;
  } catch {
    list.innerHTML = '<li class="text-muted small">Could not load announcements.</li>';
  }
}

function showAnnouncement(id) {
  const a = (window._annCache || []).find(x => x.id === id);
  if (!a) return;
  toast(`${a.title}\n${a.content || ''}`, 'info');
}

// ── Top-bar / sidebar links ──────────────────────────────
function goToOrders(e) {
  e.preventDefault();
  const s = Auth.getSession();
  if (!s) { window.location.href = '/login.html'; return; }
  if (s.role === 'buyer')  window.location.href = '/pages/buyer/orders.html';
  else if (s.role === 'seller') window.location.href = '/pages/seller/dashboard.html';
  else window.location.href = '/pages/admin/dashboard.html';
}

function showHelp(e) {
  e.preventDefault();
  toast('📞 Customer Service: support@shophub.com · Hotline: +86 400-100-2026', 'info');
}

function showInfo(kind, e) {
  e.preventDefault();
  const messages = {
    about:   'ShopHub is a Spring 2026 student e-commerce project featuring sellers, buyers and admin tools — built with Flask, SQLite and Bootstrap.',
    terms:   'By using ShopHub you agree to fair-use, no resale of accounts, and respect for other users. Full terms available on request.',
    privacy: 'ShopHub stores only the data needed to run the marketplace: account info, orders and wallet balance. Passwords are hashed.',
  };
  toast(messages[kind] || 'Info unavailable.', 'info');
}

// ── Countdown ────────────────────────────────────────────
function updateCountdown() {
  const now = new Date(), end = new Date();
  end.setHours(23, 59, 59, 0);
  let diff = Math.max(0, Math.floor((end - now) / 1000));
  const h = document.getElementById('hours');
  const m = document.getElementById('minutes');
  const sec = document.getElementById('seconds');
  if (!h) return;
  h.textContent   = String(Math.floor(diff / 3600)).padStart(2, '0');
  m.textContent   = String(Math.floor((diff % 3600) / 60)).padStart(2, '0');
  sec.textContent = String(diff % 60).padStart(2, '0');
}

// ── Helpers ──────────────────────────────────────────────
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}
function escapeAttr(s) { return escapeHtml(s).replace(/\n/g, ' '); }

// ── Init ─────────────────────────────────────────────────
(async function init() {
  const s = Auth.getSession();

  if (s) {
    document.getElementById('topbar-left').innerHTML =
      `<span>Hello, <strong>${s.username}</strong>
       <span class="sh-role-badge sh-role-${s.role}" style="font-size:10px">${s.role}</span></span>`;

    if (s.role === 'buyer') {
      document.getElementById('nav-cart').style.display   = '';
      document.getElementById('nav-orders').style.display = '';
      // Sync count from server in case it changed elsewhere
      API.getCartCount().then(cnt => {
        const sess = Auth.getSession();
        if (sess) { sess.cartCount = cnt; localStorage.setItem(Auth.KEY, JSON.stringify(sess)); }
        const badge = document.getElementById('header-cart-count');
        if (badge && cnt > 0) { badge.textContent = cnt; badge.style.display = ''; }
      }).catch(() => {});
    }

    const dashLink = document.getElementById('nav-dashboard');
    dashLink.style.display = '';
    dashLink.href = ROLE_HOME[s.role] || '/';
    dashLink.textContent = s.role === 'admin'  ? 'Admin Panel'
                         : s.role === 'seller' ? 'Seller Hub'
                         :                       'My Account';

    document.getElementById('sidebar-user-box').style.display     = 'none';
    document.getElementById('sidebar-loggedin-box').style.display = '';
    document.getElementById('sidebar-welcome').textContent        = `Welcome, ${s.username}!`;

    const ROLE_LINKS = {
      buyer:  `<a href="/pages/buyer/account.html"    class="btn btn-sh btn-sm">My Account</a>
               <a href="/pages/buyer/orders.html"     class="btn btn-outline-secondary btn-sm">My Orders</a>`,
      seller: `<a href="/pages/seller/dashboard.html" class="btn btn-sh btn-sm">Seller Hub</a>
               <a href="/pages/seller/products.html"  class="btn btn-outline-secondary btn-sm">Products</a>`,
      admin:  `<a href="/pages/admin/dashboard.html"  class="btn btn-sh btn-sm">Admin Panel</a>
               <a href="/pages/admin/users.html"      class="btn btn-outline-secondary btn-sm">Users</a>`,
    };
    document.getElementById('sidebar-role-links').innerHTML = ROLE_LINKS[s.role] || '';
  }

  try {
    allProducts = await API.getProducts();
  } catch {
    allProducts = [];
  }

  filterProducts();
  renderFlashSale();
  loadAnnouncements();
  updateCountdown();
  setInterval(updateCountdown, 1000);
})();
