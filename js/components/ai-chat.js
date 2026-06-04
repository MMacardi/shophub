'use strict';
// ── ShopHub ── ai-chat.js ────────────────────────────────
// Floating ShopBot chat widget. Talks to /api/ai/chat which proxies
// the user's running conversation to Aliyun DashScope with tool use.

(function () {
  const STORAGE_KEY = 'sh_ai_chat_history';
  const MAX_HISTORY = 30; // keep last N user/assistant/tool messages

  // ── DOM bootstrap ─────────────────────────────────────────
  function mount() {
    if (document.getElementById('ai-chat-root')) return;

    const root = document.createElement('div');
    root.id = 'ai-chat-root';
    root.innerHTML = `
      <button class="ai-fab" id="ai-fab" aria-label="Open ShopBot">
        <span class="ai-fab-icon">💬</span>
        <span class="ai-fab-label">ShopBot</span>
      </button>
      <div class="ai-panel" id="ai-panel" role="dialog" aria-label="ShopBot">
        <div class="ai-header">
          <div class="ai-header-title">
            <span class="ai-avatar">🤖</span>
            <div>
              <div class="ai-name">ShopBot</div>
              <div class="ai-sub">Your AI shopping assistant</div>
            </div>
          </div>
          <div class="ai-header-actions">
            <button class="ai-icon-btn" id="ai-reset" title="Start over">↻</button>
            <button class="ai-icon-btn" id="ai-close" title="Close">×</button>
          </div>
        </div>
        <div class="ai-messages" id="ai-messages"></div>
        <div class="ai-quick" id="ai-quick">
          <button class="ai-chip" data-msg="I'm looking for wireless earbuds under 150 yuan">Earbuds &lt; ¥150</button>
          <button class="ai-chip" data-msg="Recommend a winter coat for me">Winter coat</button>
          <button class="ai-chip" data-msg="What's in my cart?">View cart</button>
        </div>
        <form class="ai-input-row" id="ai-form">
          <input class="ai-input" id="ai-input" type="text" autocomplete="off"
                 placeholder="Tell ShopBot what you're looking for…" />
          <button class="ai-send" type="submit" id="ai-send">Send</button>
        </form>
      </div>
    `;
    document.body.appendChild(root);

    document.getElementById('ai-fab').addEventListener('click', togglePanel);
    document.getElementById('ai-close').addEventListener('click', closePanel);
    document.getElementById('ai-reset').addEventListener('click', resetConversation);
    document.getElementById('ai-form').addEventListener('submit', onSubmit);
    document.getElementById('ai-quick').addEventListener('click', (e) => {
      const t = e.target.closest('.ai-chip');
      if (!t) return;
      sendMessage(t.getAttribute('data-msg'));
    });

    renderHistory();
    if (loadHistory().length === 0) {
      appendMessage('assistant', greeting());
    }
  }

  function greeting() {
    const s = (typeof Auth !== 'undefined') && Auth.getSession();
    if (s && s.role === 'buyer') {
      return `Hi ${s.username}! I'm ShopBot. Tell me what you're shopping for — `
           + `I can recommend products, share reviews, add things to your cart and even check out for you.`;
    }
    if (s) {
      return `Hi! I can search the catalog and show product / seller reviews. `
           + `To add items to your cart or pay, please sign in as a buyer.`;
    }
    return `Hi! I'm ShopBot. I can recommend products and show reviews. `
         + `<a href="/login.html">Sign in</a> as a buyer to use the cart and checkout.`;
  }

  // ── State ────────────────────────────────────────────────
  function loadHistory() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || []; }
    catch { return []; }
  }
  function saveHistory(arr) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(arr.slice(-MAX_HISTORY)));
  }
  function resetConversation() {
    localStorage.removeItem(STORAGE_KEY);
    document.getElementById('ai-messages').innerHTML = '';
    appendMessage('assistant', greeting());
  }

  function togglePanel() {
    const p = document.getElementById('ai-panel');
    p.classList.toggle('open');
    if (p.classList.contains('open')) {
      setTimeout(() => document.getElementById('ai-input').focus(), 50);
    }
  }
  function closePanel() {
    document.getElementById('ai-panel').classList.remove('open');
  }

  // ── Render ───────────────────────────────────────────────
  function renderHistory() {
    const box = document.getElementById('ai-messages');
    box.innerHTML = '';
    for (const m of loadHistory()) {
      if (m.role === 'user' || m.role === 'assistant') {
        if (m.content && (typeof m.content === 'string') && m.content.trim()) {
          appendMessage(m.role, m.content, /*persist=*/false);
        }
      }
    }
  }

  function appendMessage(role, html, persist = true) {
    const box = document.getElementById('ai-messages');
    const div = document.createElement('div');
    div.className = 'ai-msg ai-msg-' + role;
    div.innerHTML = `
      <div class="ai-msg-bubble">${renderText(html)}</div>
    `;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;

    if (persist) {
      const h = loadHistory();
      h.push({ role, content: html });
      saveHistory(h);
    }
  }

  function appendTyping() {
    const box = document.getElementById('ai-messages');
    const div = document.createElement('div');
    div.id = 'ai-typing';
    div.className = 'ai-msg ai-msg-assistant';
    div.innerHTML = `<div class="ai-msg-bubble ai-typing"><span></span><span></span><span></span></div>`;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
  }
  function removeTyping() {
    const t = document.getElementById('ai-typing');
    if (t) t.remove();
  }

  // Light Markdown-ish: line breaks + **bold** + links.
  function renderText(s) {
    if (!s) return '';
    const escaped = String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    return escaped
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\[(.+?)\]\((https?:[^)\s]+|\/[^)\s]*)\)/g, '<a href="$2" target="_blank">$1</a>')
      .replace(/\n/g, '<br/>');
  }

  // ── Submit ───────────────────────────────────────────────
  function onSubmit(e) {
    e.preventDefault();
    const input = document.getElementById('ai-input');
    const text  = input.value.trim();
    if (!text) return;
    input.value = '';
    sendMessage(text);
  }

  async function sendMessage(text) {
    appendMessage('user', text);
    const sendBtn = document.getElementById('ai-send');
    sendBtn.disabled = true;
    appendTyping();

    try {
      const history = loadHistory()
        .filter(m => m.role === 'user' || m.role === 'assistant')
        .map(m => ({ role: m.role, content: m.content }));

      const session = (typeof Auth !== 'undefined') && Auth.getSession();
      const headers = { 'Content-Type': 'application/json' };
      if (session && session.token) headers['Authorization'] = 'Bearer ' + session.token;

      const res = await fetch('/api/ai/chat', {
        method: 'POST',
        headers,
        body: JSON.stringify({ messages: history }),
      });
      const data = await res.json().catch(() => ({}));
      removeTyping();

      if (!res.ok) {
        appendMessage('assistant', `⚠️ ${data.error || 'AI service is unavailable.'}`);
      } else {
        appendMessage('assistant', data.reply || '(no reply)');
        refreshCartCount();
        broadcastAISearchResults(data.messages || []);
      }
    } catch (err) {
      removeTyping();
      appendMessage('assistant', `⚠️ Network error: ${err.message}`);
    } finally {
      sendBtn.disabled = false;
      document.getElementById('ai-input').focus();
    }
  }

  // ── Broadcast AI search results so the host page can filter ──
  // Scans the returned messages for the LAST `search_products` tool result
  // and emits a window event with the product IDs + the user's last question.
  function broadcastAISearchResults(messages) {
    let lastSearch = null;
    for (const m of messages) {
      if (m.role !== 'tool' || m.name !== 'search_products') continue;
      try { lastSearch = JSON.parse(m.content || '{}'); } catch { /* skip */ }
    }
    if (!lastSearch || !Array.isArray(lastSearch.products)) return;
    const ids = lastSearch.products.map(p => p.id).filter(Boolean);
    if (!ids.length) return;

    // Find the user's most recent message for a nice chip label
    let lastUserMsg = '';
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === 'user' && typeof messages[i].content === 'string') {
        lastUserMsg = messages[i].content;
        break;
      }
    }
    window.dispatchEvent(new CustomEvent('ai-suggestion', {
      detail: { productIds: ids, query: lastUserMsg },
    }));
  }

  // ── Side-effect: keep header cart badge in sync ──────────
  async function refreshCartCount() {
    const session = (typeof Auth !== 'undefined') && Auth.getSession();
    if (!session || session.role !== 'buyer') return;
    try {
      const count = await API.getCartCount();
      const badge = document.getElementById('header-cart-count');
      if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? '' : 'none';
      }
      session.cartCount = count;
      localStorage.setItem(Auth.KEY, JSON.stringify(session));
    } catch { /* not signed in or no cart endpoint here */ }
  }

  // ── Boot ─────────────────────────────────────────────────
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }
})();
