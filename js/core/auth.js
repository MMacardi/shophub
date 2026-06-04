'use strict';
// ── ShopHub ── auth.js ───────────────────────────────────

const Auth = {
  KEY: 'sh_session',

  async login(username, password) {
    try {
      const data = await API.login(username, password);
      if (!data) return { ok: false, msg: 'Login failed.' };
      const session = { token: data.token, ...data.user, cartCount: 0 };
      localStorage.setItem(this.KEY, JSON.stringify(session));
      return { ok: true, user: data.user };
    } catch (err) {
      return { ok: false, msg: err.message || 'Invalid username or password.' };
    }
  },

  async register(username, email, password, role, shopName) {
    try {
      const data = await API.register(username, email, password, role, shopName);
      if (!data) return { ok: false, msg: 'Registration failed.' };
      const session = { token: data.token, ...data.user, cartCount: 0 };
      localStorage.setItem(this.KEY, JSON.stringify(session));
      return { ok: true, user: data.user };
    } catch (err) {
      return { ok: false, msg: err.message || 'Registration failed.' };
    }
  },

  logout() {
    localStorage.removeItem(this.KEY);
    window.location.href = '/login.html';
  },

  getSession() {
    try { return JSON.parse(localStorage.getItem(this.KEY)); }
    catch { return null; }
  },

  isLoggedIn() { return !!this.getSession(); },

  requireRole(...roles) {
    const s = this.getSession();
    if (!s || !roles.includes(s.role)) {
      window.location.href = '/login.html';
      return null;
    }
    return s;
  },
};
