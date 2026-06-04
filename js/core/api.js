'use strict';
// ── ShopHub ── api.js ────────────────────────────────────
// Fetch-based client for the Flask backend.

const API = (() => {
  const BASE = '/api';

  async function req(path, options = {}) {
    const session = Auth.getSession();
    const headers = { 'Content-Type': 'application/json' };
    if (session && session.token) headers['Authorization'] = 'Bearer ' + session.token;
    Object.assign(headers, options.headers || {});

    const res = await fetch(BASE + path, { ...options, headers });

    if (res.status === 401) { Auth.logout(); return; }

    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || 'Request failed');
    return data;
  }

  function body(method, payload) {
    return { method, body: JSON.stringify(payload) };
  }

  // ── Auth ───────────────────────────────────────────────
  async function login(username, password) {
    return req('/auth/login', body('POST', { username, password }));
  }

  async function register(username, email, password, role, shopName) {
    return req('/auth/register', body('POST', { username, email, password, role, shopName }));
  }

  // ── Products ───────────────────────────────────────────
  async function getProducts(params = {}) {
    const qs = new URLSearchParams(params).toString();
    const data = await req('/products' + (qs ? '?' + qs : ''));
    return data ? data.products : [];
  }

  async function getMyProducts() {
    const data = await req('/products?seller=my');
    return data ? data.products : [];
  }

  async function createProduct(payload) {
    const data = await req('/products', body('POST', payload));
    return data ? data.product : null;
  }

  async function updateProduct(id, payload) {
    const data = await req(`/products/${id}`, body('PUT', payload));
    return data ? data.product : null;
  }

  async function deleteProduct(id) {
    return req(`/products/${id}`, { method: 'DELETE' });
  }

  // ── Cart ───────────────────────────────────────────────
  async function getCart() {
    const data = await req('/cart');
    return data || { cart: [], count: 0 };
  }

  async function getCartCount() {
    const data = await req('/cart/count');
    return data ? data.count : 0;
  }

  async function addToCart(productId, qty = 1) {
    const data = await req('/cart', body('POST', { productId, qty }));
    if (data) _updateCartCount(data.count);
    return data;
  }

  async function updateCartQty(productId, qty) {
    const data = await req(`/cart/${productId}`, body('PUT', { qty }));
    if (data) _updateCartCount(data.count);
    return data;
  }

  async function removeFromCart(productId) {
    const data = await req(`/cart/${productId}`, { method: 'DELETE' });
    if (data) _updateCartCount(data.count);
    return data;
  }

  function _updateCartCount(count) {
    const s = Auth.getSession();
    if (s) { s.cartCount = count; localStorage.setItem(Auth.KEY, JSON.stringify(s)); }
  }

  // ── Orders ─────────────────────────────────────────────
  async function getOrders() {
    const data = await req('/orders');
    return data ? data.orders : [];
  }

  async function checkout() {
    const data = await req('/orders', { method: 'POST' });
    if (data) _updateCartCount(0);
    return data ? data.order : null;
  }

  // ── Wallet ─────────────────────────────────────────────
  async function getWallet() {
    const data = await req('/wallet');
    return data ? data.balance : 0;
  }

  async function topupWallet(amount) {
    const data = await req('/wallet/topup', body('POST', { amount }));
    return data ? data.balance : 0;
  }

  // ── Admin ──────────────────────────────────────────────
  async function getAdminStats() {
    const data = await req('/admin/stats');
    return data || {};
  }

  async function getAdminUsers() {
    const data = await req('/admin/users');
    return data ? data.users : [];
  }

  async function toggleUser(uid) {
    return req(`/admin/users/${uid}/toggle`, { method: 'POST' });
  }

  async function resetUserPassword(uid) {
    return req(`/admin/users/${uid}/reset-password`, { method: 'POST' });
  }

  // ── Sellers ────────────────────────────────────────────
  async function getSeller(sid) {
    const data = await req(`/sellers/${sid}`);
    return data ? data.seller : null;
  }

  async function getSellerProducts(sid) {
    const data = await req(`/sellers/${sid}/products`);
    return data ? data.products : [];
  }

  async function getSellerReviews(sid) {
    const data = await req(`/sellers/${sid}/reviews`);
    return data ? data.reviews : [];
  }

  // ── Reviews ────────────────────────────────────────────
  async function getReviews(productId) {
    const data = await req(`/products/${productId}/reviews`);
    return data ? data.reviews : [];
  }

  async function createReview(productId, rating, comment) {
    const data = await req(`/products/${productId}/reviews`, body('POST', { rating, comment }));
    return data ? data.review : null;
  }

  async function deleteReview(productId, reviewId) {
    return req(`/products/${productId}/reviews/${reviewId}`, { method: 'DELETE' });
  }

  // ── Announcements ──────────────────────────────────────
  async function getAnnouncements() {
    const data = await req('/announcements');
    return data ? data.announcements : [];
  }

  async function createAnnouncement(title, content) {
    const data = await req('/announcements', body('POST', { title, content }));
    return data ? data.announcement : null;
  }

  async function deleteAnnouncement(id) {
    return req(`/announcements/${id}`, { method: 'DELETE' });
  }

  return {
    login, register,
    getProducts, getMyProducts, createProduct, updateProduct, deleteProduct,
    getCart, getCartCount, addToCart, updateCartQty, removeFromCart,
    getOrders, checkout,
    getWallet, topupWallet,
    getAdminStats, getAdminUsers, toggleUser, resetUserPassword,
    getAnnouncements, createAnnouncement, deleteAnnouncement,
    getReviews, createReview, deleteReview,
    getSeller, getSellerProducts, getSellerReviews,
  };
})();
