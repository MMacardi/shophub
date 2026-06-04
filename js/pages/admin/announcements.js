'use strict';
// ── ShopHub ── pages/admin/announcements.js ─────────────

Auth.requireRole('admin');

injectNav([
  { href:'/pages/admin/dashboard.html',     label:'Dashboard' },
  { href:'/pages/admin/users.html',         label:'User Management' },
  { href:'/pages/admin/announcements.html', label:'Announcements', active:true },
  { href:'/',                               label:'View Store' },
]);

const annModal = new bootstrap.Modal(document.getElementById('annModal'));
const delModal = new bootstrap.Modal(document.getElementById('delModal'));
let pendingDelId = null;

function openModal() {
  document.getElementById('a-title').value   = '';
  document.getElementById('a-content').value = '';
  annModal.show();
}

async function saveAnn() {
  const title   = document.getElementById('a-title').value.trim();
  const content = document.getElementById('a-content').value.trim();
  if (!title) { toast('Title is required.', 'error'); return; }
  try {
    await API.createAnnouncement(title, content);
    toast('Announcement published!');
    annModal.hide();
    await loadList();
  } catch (err) {
    toast(err.message || 'Failed to publish.', 'error');
  }
}

function confirmDelete(id) {
  pendingDelId = id;
  delModal.show();
}

document.getElementById('confirm-del-btn').addEventListener('click', async () => {
  if (!pendingDelId) return;
  try {
    await API.deleteAnnouncement(pendingDelId);
    toast('Announcement deleted.', 'info');
    await loadList();
  } catch (err) {
    toast(err.message || 'Failed to delete.', 'error');
  }
  delModal.hide();
  pendingDelId = null;
});

async function loadList() {
  const items = await API.getAnnouncements();
  const list  = document.getElementById('ann-list');
  const empty = document.getElementById('ann-empty');
  document.getElementById('ann-count').textContent =
    `${items.length} post${items.length !== 1 ? 's' : ''}`;

  if (!items.length) { list.innerHTML = ''; empty.style.display = ''; return; }
  empty.style.display = 'none';

  list.innerHTML = items.map(a => `
    <div class="ann-row d-flex justify-content-between align-items-start gap-3 py-3 border-bottom">
      <div class="flex-grow-1">
        <div class="fw-bold mb-1">${escapeHtml(a.title)}</div>
        ${a.content ? `<div class="text-muted small mb-1">${escapeHtml(a.content)}</div>` : ''}
        <div class="text-muted" style="font-size:11px">${fmtDateTime(a.createdAt)}</div>
      </div>
      <button class="btn btn-sm btn-outline-danger" onclick="confirmDelete(${a.id})">
        <i class="bi bi-trash"></i>
      </button>
    </div>
  `).join('');
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}

loadList();
