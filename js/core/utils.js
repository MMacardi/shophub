'use strict';
// ── ShopHub ── utils.js ──────────────────────────────────
// Pure helper functions — no side effects, no dependencies.

function fmt(n)         { return '¥' + Number(n).toFixed(2); }
function fmtDate(d)     { return new Date(d).toLocaleDateString('en-GB',  { day:'2-digit', month:'short', year:'numeric' }); }
function fmtDateTime(d) { return new Date(d).toLocaleString  ('en-GB',    { day:'2-digit', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit' }); }

function cartCount() {
  const s = Auth.getSession();
  return (s && s.role === 'buyer') ? (s.cartCount || 0) : 0;
}

function toast(msg, type = 'success') {
  let wrap = document.getElementById('_toasts');
  if (!wrap) {
    wrap = document.createElement('div');
    wrap.id = '_toasts';
    wrap.style.cssText = 'position:fixed;top:72px;right:16px;z-index:9999;display:flex;flex-direction:column;gap:8px;pointer-events:none;';
    document.body.appendChild(wrap);
  }
  const BG = { success:'#27ae60', error:'#e74c3c', warning:'#f39c12', info:'#3498db' };
  const el = document.createElement('div');
  el.style.cssText = `background:${BG[type]||BG.success};color:#fff;padding:10px 18px;border-radius:8px;font-size:13px;box-shadow:0 4px 16px rgba(0,0,0,.25);opacity:0;transition:opacity .3s;max-width:300px;`;
  el.textContent = msg;
  wrap.appendChild(el);
  requestAnimationFrame(() => el.style.opacity = '1');
  setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 320); }, 3200);
}
