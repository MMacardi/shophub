'use strict';
// ── ShopHub ── pages/register.js ────────────────────────

function selectRole(role) {
  document.getElementById('selected-role').value = role;
  document.getElementById('role-buyer').classList.toggle('selected',  role === 'buyer');
  document.getElementById('role-seller').classList.toggle('selected', role === 'seller');
  const shopField = document.getElementById('shopname-field');
  shopField.style.display = role === 'seller' ? '' : 'none';
  document.getElementById('shopname').required = role === 'seller';
  if (role !== 'seller') document.getElementById('shopname').value = '';
}

document.getElementById('register-form').addEventListener('submit', async function (e) {
  e.preventDefault();
  const btn    = this.querySelector('button[type=submit]');
  const errEl  = document.getElementById('error-msg');
  errEl.classList.add('d-none');

  const role     = document.getElementById('selected-role').value;
  const username = document.getElementById('username').value.trim();
  const email    = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  const confirm  = document.getElementById('confirm-password').value;
  const shopName = document.getElementById('shopname').value.trim();

  if (password !== confirm) {
    errEl.textContent = 'Passwords do not match.';
    errEl.classList.remove('d-none');
    return;
  }

  btn.disabled = true;
  const result = await Auth.register(username, email, password, role, shopName);
  btn.disabled = false;

  if (!result.ok) {
    errEl.textContent = result.msg;
    errEl.classList.remove('d-none');
    return;
  }
  window.location.href = ROLE_HOME[role] || '/';
});
