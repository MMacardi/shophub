'use strict';
// ── ShopHub ── pages/seller/products.js ─────────────────

const session  = Auth.requireRole('seller');
const modal    = new bootstrap.Modal(document.getElementById('productModal'));
const delModal = new bootstrap.Modal(document.getElementById('deleteModal'));
let pendingDeleteId = null;
let productsCache   = [];

injectNav([
  { href:'/pages/seller/dashboard.html', label:'Dashboard' },
  { href:'/pages/seller/products.html',  label:'Products',  active:true },
  { href:'/pages/seller/stats.html',     label:'Statistics' },
  { href:'/',                            label:'View Store' },
]);

// ── Render ───────────────────────────────────────────────
function renderProducts(products) {
  const tbody = document.getElementById('products-tbody');
  const empty = document.getElementById('products-empty');
  const wrap  = document.getElementById('products-table-wrap');

  if (!products.length) { empty.style.display = ''; wrap.style.display = 'none'; return; }
  empty.style.display = 'none'; wrap.style.display = '';

  tbody.innerHTML = products.map(p => {
    const cls  = p.stock === 0 ? 'stock-out' : p.stock <= 10 ? 'stock-low' : 'stock-ok';
    const text = p.stock === 0 ? 'Out of stock' : `${p.stock} in stock`;
    return `
      <tr>
        <td>
          <div class="d-flex align-items-center gap-2">
            <span style="font-size:24px">${p.emoji}</span>
            <div>
              <div class="fw-bold" style="font-size:13px">${p.name}</div>
              <div class="text-muted" style="font-size:11px">${p.description.substring(0,60)}${p.description.length>60?'…':''}</div>
            </div>
          </div>
        </td>
        <td><span class="badge bg-secondary">${p.category}</span></td>
        <td>
          <span class="fw-bold" style="color:var(--primary)">${fmt(p.price)}</span>
          ${p.originalPrice ? `<div class="text-muted" style="font-size:11px;text-decoration:line-through">${fmt(p.originalPrice)} <span class="discount-pill">−${p.discountPct}%</span></div>` : ''}
        </td>
        <td><span class="stock-badge ${cls}">${text}</span></td>
        <td>
          <button class="btn-icon"        title="Edit"   onclick="openModal(${p.id})"><i class="bi bi-pencil"></i></button>
          <button class="btn-icon danger" title="Delete" onclick="confirmDelete(${p.id})"><i class="bi bi-trash"></i></button>
        </td>
      </tr>`;
  }).join('');
}

// ── Modal helpers ────────────────────────────────────────
function autoEmoji() {
  const cat = document.getElementById('p-category').value;
  if (CAT_EMOJI[cat] && !document.getElementById('edit-id').value)
    document.getElementById('p-emoji').value = CAT_EMOJI[cat];
  updatePreview();
}

// ── Live preview inside the modal ─────────────────────────
function updatePreview() {
  const name  = document.getElementById('p-name').value.trim() || 'Product name';
  const emoji = document.getElementById('p-emoji').value.trim() || '📦';
  const cat   = document.getElementById('p-category').value || 'Category';
  const price = parseFloat(document.getElementById('p-price').value) || 0;
  const orig  = parseFloat(document.getElementById('p-original').value) || 0;
  const stock = parseInt(document.getElementById('p-stock').value) || 0;

  document.getElementById('pm-preview-emoji').textContent = emoji;
  document.getElementById('pm-preview-name').textContent  = name;
  document.getElementById('pm-preview-cat').textContent   = cat;
  document.getElementById('pm-preview-price').textContent = `¥${price.toFixed(2)}`;
  document.getElementById('pm-preview-orig').textContent  = orig > price ? `¥${orig.toFixed(2)}` : '';
  document.getElementById('pm-preview-stock').textContent = stock > 0 ? `Stock ${stock}` : 'Out of stock';

  const hint = document.getElementById('pm-discount-hint');
  if (orig > price && price > 0) {
    const pct = Math.round((orig - price) / orig * 100);
    hint.style.display = '';
    hint.textContent = `🏷️ ${pct}% discount — buyers will see a SALE badge`;
  } else {
    hint.style.display = 'none';
  }
}

// ── AI Generate description ──────────────────────────────
async function aiGenerateDescription() {
  const name     = document.getElementById('p-name').value.trim();
  const category = document.getElementById('p-category').value;
  const hint     = document.getElementById('p-description').value.trim();
  const btn      = document.getElementById('ai-generate-btn');

  if (!name) { toast('Enter a product name first.', 'warning'); return; }
  if (!hint) { toast('Write a rough description first — AI will polish it.', 'warning'); return; }

  const original = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '⏳ Generating…';

  try {
    const s = Auth.getSession();
    const res = await fetch('/api/ai/generate-description', {
      method:  'POST',
      headers: {
        'Content-Type':  'application/json',
        'Authorization': 'Bearer ' + (s && s.token),
      },
      body: JSON.stringify({ name, category, hint }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || 'AI generation failed.');
    document.getElementById('p-description').value = data.description;
    toast('Description polished by AI ✨');
  } catch (err) {
    toast(err.message || 'AI generation failed.', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = original;
  }
}

// Wire up live-preview listeners (idempotent — only attaches once)
['p-name','p-emoji','p-category','p-price','p-original','p-stock'].forEach(id => {
  const el = document.getElementById(id);
  if (el && !el._previewWired) {
    el.addEventListener('input',  updatePreview);
    el.addEventListener('change', updatePreview);
    el._previewWired = true;
  }
});

function openModal(id) {
  document.getElementById('modal-title').textContent = id ? 'Edit Product' : 'Add New Product';
  document.getElementById('edit-id').value = id || '';

  if (id) {
    const p = productsCache.find(x => x.id === id);
    if (!p) return;
    document.getElementById('p-name').value        = p.name;
    document.getElementById('p-emoji').value       = p.emoji;
    document.getElementById('p-category').value    = p.category;
    document.getElementById('p-price').value       = p.price;
    document.getElementById('p-original').value    = p.originalPrice || '';
    document.getElementById('p-stock').value       = p.stock;
    document.getElementById('p-description').value = p.description;
  } else {
    ['p-name','p-emoji','p-price','p-original','p-stock','p-description'].forEach(id => {
      document.getElementById(id).value = '';
    });
    document.getElementById('p-category').value = '';
  }
  updatePreview();
  modal.show();
}

async function saveProduct() {
  const name     = document.getElementById('p-name').value.trim();
  const emoji    = document.getElementById('p-emoji').value.trim() || '📦';
  const category = document.getElementById('p-category').value;
  const price    = parseFloat(document.getElementById('p-price').value);
  const origRaw  = document.getElementById('p-original').value.trim();
  const original = origRaw ? parseFloat(origRaw) : null;
  const stock    = parseInt(document.getElementById('p-stock').value);
  const desc     = document.getElementById('p-description').value.trim();
  const editId   = parseInt(document.getElementById('edit-id').value) || 0;

  if (!name || !category || isNaN(price) || price <= 0 || isNaN(stock) || stock < 0) {
    toast('Please fill in all required fields correctly.', 'error');
    return;
  }
  if (original !== null && (isNaN(original) || original <= price)) {
    toast('Original price must be higher than sale price.', 'error');
    return;
  }

  const payload = { name, emoji, category, price, stock, description: desc, originalPrice: original };

  try {
    if (editId) {
      await API.updateProduct(editId, payload);
    } else {
      await API.createProduct(payload);
    }
    toast(editId ? 'Product updated!' : 'Product added!');
    modal.hide();
    await loadProducts();
  } catch (err) {
    toast(err.message || 'Failed to save product.', 'error');
  }
}

// ── Delete ───────────────────────────────────────────────
function confirmDelete(id) {
  pendingDeleteId = id;
  delModal.show();
}

document.getElementById('confirm-delete-btn').addEventListener('click', async function () {
  if (!pendingDeleteId) return;
  try {
    await API.deleteProduct(pendingDeleteId);
    delModal.hide();
    toast('Product deleted.', 'info');
    await loadProducts();
  } catch (err) {
    toast(err.message || 'Failed to delete product.', 'error');
  }
  pendingDeleteId = null;
});

// ── Load ─────────────────────────────────────────────────
async function loadProducts() {
  productsCache = await API.getMyProducts();
  renderProducts(productsCache);
}

loadProducts();
