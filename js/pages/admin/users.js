'use strict';
// ── ShopHub ── pages/admin/users.js ─────────────────────

Auth.requireRole('admin');

injectNav([
  { href:'/pages/admin/dashboard.html',     label:'Dashboard' },
  { href:'/pages/admin/users.html',         label:'User Management', active:true },
  { href:'/pages/admin/announcements.html', label:'Announcements' },
  { href:'/',                               label:'View Store' },
]);

const resetModal  = new bootstrap.Modal(document.getElementById('resetModal'));
const toggleModal = new bootstrap.Modal(document.getElementById('toggleModal'));
let activeFilter    = '';
let pendingResetId  = null;
let pendingToggleId = null;
let usersCache      = [];

// ── Filter ───────────────────────────────────────────────
function setFilter(f) {
  activeFilter = f;
  ['all','seller','buyer','active','disabled'].forEach(k =>
    document.getElementById(`filter-${k}`).classList.toggle('active', k === (f || 'all'))
  );
  renderUsers();
}

// ── Render ───────────────────────────────────────────────
function renderUsers() {
  const search = document.getElementById('search-user').value.toLowerCase();
  let users = usersCache;

  if (activeFilter === 'seller')   users = users.filter(u => u.role === 'seller');
  if (activeFilter === 'buyer')    users = users.filter(u => u.role === 'buyer');
  if (activeFilter === 'active')   users = users.filter(u => u.enabled);
  if (activeFilter === 'disabled') users = users.filter(u => !u.enabled);
  if (search) users = users.filter(u =>
    u.username.toLowerCase().includes(search) || u.email.toLowerCase().includes(search));

  const tbody = document.getElementById('users-tbody');
  const empty = document.getElementById('users-empty');
  document.getElementById('user-count').textContent = `${users.length} user${users.length !== 1 ? 's' : ''}`;

  if (!users.length) { tbody.innerHTML = ''; empty.style.display = ''; return; }
  empty.style.display = 'none';

  tbody.innerHTML = users.map(u => `
    <tr>
      <td class="fw-bold">${u.username}</td>
      <td><span class="badge-role-${u.role}">${u.role}</span></td>
      <td style="font-size:12px">${u.email}</td>
      <td style="font-size:12px;color:#999">${u.shopName || '—'}</td>
      <td><span class="${u.enabled ? 'badge-enabled' : 'badge-disabled'}">${u.enabled ? 'Active' : 'Disabled'}</span></td>
      <td style="font-size:12px">${fmtDate(u.createdAt)}</td>
      <td>
        <button class="btn btn-sm ${u.enabled ? 'btn-outline-danger' : 'btn-outline-success'} me-1"
          style="font-size:11px;padding:3px 8px" onclick="confirmToggle(${u.id})">
          <i class="bi bi-${u.enabled ? 'slash-circle' : 'check-circle'} me-1"></i>${u.enabled ? 'Disable' : 'Enable'}
        </button>
        <button class="btn btn-sm btn-outline-warning" style="font-size:11px;padding:3px 8px"
          onclick="confirmReset(${u.id})">
          <i class="bi bi-key me-1"></i>Reset Pwd
        </button>
      </td>
    </tr>`).join('');
}

// ── Toggle ───────────────────────────────────────────────
function confirmToggle(id) {
  pendingToggleId = id;
  const u         = usersCache.find(x => x.id === id);
  const willDisable = u.enabled;
  document.getElementById('toggle-modal-title').textContent = willDisable ? 'Disable Account' : 'Enable Account';
  document.getElementById('toggle-modal-body').innerHTML =
    `${willDisable ? 'Disable' : 'Enable'} account for <strong>${u.username}</strong>?` +
    (willDisable ? '<div class="mt-1 text-muted small">User will not be able to log in while disabled.</div>' : '');
  const btn = document.getElementById('confirm-toggle-btn');
  btn.textContent = willDisable ? 'Disable' : 'Enable';
  btn.className = `btn btn-sm ${willDisable ? 'btn-danger' : 'btn-success'}`;
  toggleModal.show();
}

document.getElementById('confirm-toggle-btn').addEventListener('click', async function () {
  if (!pendingToggleId) return;
  try {
    const data = await API.toggleUser(pendingToggleId);
    toast(`"${data.username}" ${data.enabled ? 'enabled' : 'disabled'}.`, data.enabled ? 'success' : 'warning');
    await loadUsers();
  } catch (err) {
    toast(err.message || 'Failed to update user.', 'error');
  }
  toggleModal.hide();
  pendingToggleId = null;
});

// ── Reset password ────────────────────────────────────────
function confirmReset(id) {
  pendingResetId = id;
  const u = usersCache.find(x => x.id === id);
  document.getElementById('reset-username').textContent = u.username;
  resetModal.show();
}

document.getElementById('confirm-reset-btn').addEventListener('click', async function () {
  if (!pendingResetId) return;
  try {
    const data = await API.resetUserPassword(pendingResetId);
    toast(`Password for "${data.username}" reset to: 123456`, 'info');
  } catch (err) {
    toast(err.message || 'Failed to reset password.', 'error');
  }
  resetModal.hide();
  pendingResetId = null;
});

// ── Search live ──────────────────────────────────────────
document.getElementById('search-user').addEventListener('input', renderUsers);

async function loadUsers() {
  usersCache = await API.getAdminUsers();
  renderUsers();
}

loadUsers();
