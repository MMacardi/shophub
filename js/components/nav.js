'use strict';
// ── ShopHub ── nav.js ────────────────────────────────────

function injectNav(navLinks) {
  const s  = Auth.getSession();
  const el = document.getElementById('sh-nav');
  if (!el || !s) return;

  const isB = s.role === 'buyer';
  const cnt = isB ? cartCount() : 0;
  const cart = isB
    ? `<a href="/pages/buyer/cart.html" class="nav-link text-white me-1">
         🛒 Cart${cnt > 0 ? ` <span class="badge bg-warning text-dark">${cnt}</span>` : ''}
       </a>`
    : '';

  const links = (navLinks || []).map(l =>
    `<a href="${l.href}" class="nav-link text-white${l.active ? ' active-nav' : ''}">${l.label}</a>`
  ).join('');

  el.innerHTML =
    `<nav class="sh-topnav">
       <div class="container-fluid d-flex align-items-center gap-1">
         <a href="/" class="sh-brand me-3">ShopHub</a>
         <div class="d-flex gap-0 me-auto">${links}</div>
         ${cart}
         <span class="text-white small mx-3">
           <span class="sh-role-badge sh-role-${s.role}">${s.role}</span>
           ${s.username}
         </span>
         <button class="btn btn-sm btn-outline-light" onclick="Auth.logout()">Logout</button>
       </div>
     </nav>`;
}
