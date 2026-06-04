'use strict';
// ── ShopHub ── pages/login.js ────────────────────────────

(function redirectIfLoggedIn() {
  const s = Auth.getSession();
  if (s) window.location.href = ROLE_HOME[s.role] || '/';
})();

function fillDemo(username, password) {
  document.getElementById('username').value = username;
  document.getElementById('password').value = password;
}

document.getElementById('login-form').addEventListener('submit', async function (e) {
  e.preventDefault();
  const btn      = this.querySelector('button[type=submit]');
  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value;

  btn.disabled = true;
  const result = await Auth.login(username, password);
  btn.disabled = false;

  if (!result.ok) {
    const el = document.getElementById('error-msg');
    el.textContent = result.msg;
    el.classList.remove('d-none');
    return;
  }
  window.location.href = ROLE_HOME[result.user.role] || '/';
});
