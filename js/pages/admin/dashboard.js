'use strict';
// ── ShopHub ── pages/admin/dashboard.js ─────────────────

Auth.requireRole('admin');

injectNav([
  { href:'/pages/admin/dashboard.html',     label:'Dashboard',       active:true },
  { href:'/pages/admin/users.html',         label:'User Management' },
  { href:'/pages/admin/announcements.html', label:'Announcements' },
  { href:'/',                               label:'View Store' },
]);

(async function init() {
  const [stats, users] = await Promise.all([
    API.getAdminStats(),
    API.getAdminUsers(),
  ]);

  document.getElementById('st-users').textContent    = stats.totalUsers    || 0;
  document.getElementById('st-sellers').textContent  = stats.sellers       || 0;
  document.getElementById('st-buyers').textContent   = stats.buyers        || 0;
  document.getElementById('st-products').textContent = stats.products      || 0;
  document.getElementById('st-orders').textContent   = stats.orders        || 0;
  document.getElementById('st-disabled').textContent = stats.disabled      || 0;

  const recent = users.slice(0, 8);
  document.getElementById('recent-users-tbody').innerHTML = recent.map(u => `
    <tr>
      <td class="fw-bold">${u.username}</td>
      <td><span class="badge-role-${u.role}">${u.role}</span></td>
      <td style="font-size:12px">${u.email}</td>
      <td><span class="${u.enabled ? 'badge-enabled' : 'badge-disabled'}">${u.enabled ? 'Active' : 'Disabled'}</span></td>
      <td style="font-size:12px">${fmtDate(u.createdAt)}</td>
    </tr>`).join('');
})();
