'use strict';
// ── ShopHub ── constants.js ──────────────────────────────

const CATEGORIES = ['Electronics','Fashion','Home','Beauty','Sports','Food','Toys','Other'];

const CAT_BG = {
  Electronics:'bg-electronics', Fashion:'bg-fashion', Home:'bg-home',
  Beauty:'bg-beauty',           Sports:'bg-sports',   Food:'bg-food',
  Toys:'bg-toys',               Other:'bg-other',
};

const CAT_EMOJI = {
  Electronics:'📱', Fashion:'👗', Home:'🏠', Beauty:'💄',
  Sports:'⚽',      Food:'🍎',    Toys:'🎮', Other:'📦',
};

// Where each role lands after login / when accessing the wrong page
const ROLE_HOME = {
  admin:  '/pages/admin/dashboard.html',
  seller: '/pages/seller/dashboard.html',
  buyer:  '/pages/buyer/account.html',
};
