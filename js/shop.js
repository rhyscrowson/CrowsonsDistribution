// Crowsons Global — shop: catalogue, product page and basket.
// Products live in data/products.json. Basket is kept in this browser only.

(() => {
  const ORDER_EMAIL = 'trade@crowsonsglobal.com';
  const BASKET_KEY = 'cg_basket_v1';
  const MAX_QTY = 20;

  /* ---------- Helpers ---------- */
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const money = (pence) => '£' + (pence / 100).toFixed(2);
  const params = new URLSearchParams(location.search);

  const ICONS = {
    'home-kitchen': '<path d="M4 11l8-7 8 7v9H4z"/><path d="M10 20v-6h4v6"/>',
    'health-beauty': '<path d="M12 3c3 4 6 7 6 10.5A6 6 0 0 1 6 13.5C6 10 9 7 12 3z"/>',
    'toys-games': '<rect x="4" y="4" width="7" height="7" rx="1"/><rect x="13" y="4" width="7" height="7" rx="1"/><rect x="4" y="13" width="7" height="7" rx="1"/><circle cx="16.5" cy="16.5" r="3.5"/>',
    'pet-supplies': '<circle cx="7" cy="9" r="2"/><circle cx="17" cy="9" r="2"/><circle cx="10" cy="5.5" r="1.8"/><circle cx="14" cy="5.5" r="1.8"/><path d="M12 12c-3 0-5 3.5-5 5.5 0 1.5 1.5 2 2.5 2 1 0 1.5-.5 2.5-.5s1.5.5 2.5.5 2.5-.5 2.5-2c0-2-2-5.5-5-5.5z"/>',
  };

  const imageHTML = (p, cls = '') => p.image
    ? `<img src="${esc(p.image)}" alt="${esc(p.name)}" class="${cls}" loading="lazy">`
    : `<div class="shop-placeholder ${cls}" data-cat="${esc(p.category)}" role="img" aria-label="${esc(p.name)}">
         <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round">${ICONS[p.category] || ''}</svg>
       </div>`;

  /* ---------- Basket storage (falls back to memory if storage is blocked) ---------- */
  let memoryBasket = {};
  const readBasket = () => {
    try { return JSON.parse(localStorage.getItem(BASKET_KEY)) || {}; } catch { return memoryBasket; }
  };
  const writeBasket = (b) => {
    memoryBasket = b;
    try { localStorage.setItem(BASKET_KEY, JSON.stringify(b)); } catch { /* memory only */ }
    renderBasket();
  };

  let catalogue = null;
  const productById = (id) => catalogue.products.find(p => p.id === id);
  const categoryName = (id) => (catalogue.categories.find(c => c.id === id) || {}).name || '';

  const addToBasket = (id, qty = 1) => {
    const p = productById(id);
    if (!p || p.stock <= 0) return;
    const b = readBasket();
    b[id] = Math.min((b[id] || 0) + qty, Math.min(MAX_QTY, p.stock));
    writeBasket(b);
    openBasket();
  };

  const setQty = (id, qty) => {
    const b = readBasket();
    if (qty <= 0) delete b[id];
    else b[id] = Math.min(qty, MAX_QTY, productById(id)?.stock ?? MAX_QTY);
    writeBasket(b);
  };

  const basketLines = () => {
    const b = readBasket();
    return Object.entries(b)
      .map(([id, qty]) => ({ product: productById(id), qty }))
      .filter(l => l.product && l.qty > 0);
  };

  const totals = () => {
    const subtotal = basketLines().reduce((s, l) => s + l.product.price * l.qty, 0);
    const { standard, freeOver } = catalogue.shipping;
    const shipping = subtotal === 0 || subtotal >= freeOver ? 0 : standard;
    return { subtotal, shipping, total: subtotal + shipping };
  };

  /* ---------- Basket UI ---------- */
  const basketBtn = document.createElement('button');
  basketBtn.className = 'basket-btn';
  basketBtn.type = 'button';
  basketBtn.setAttribute('aria-label', 'Open basket');
  basketBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 8h14l-1.2 11.2a1 1 0 0 1-1 .8H7.2a1 1 0 0 1-1-.8z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/></svg><span class="basket-count" id="basketCount">0</span>`;

  const drawer = document.createElement('aside');
  drawer.className = 'basket';
  drawer.id = 'basket';
  drawer.setAttribute('aria-label', 'Basket');
  drawer.setAttribute('aria-hidden', 'true');
  drawer.innerHTML = `
    <div class="basket-scrim" data-close></div>
    <div class="basket-panel" role="dialog" aria-modal="true" aria-labelledby="basketTitle">
      <div class="basket-head">
        <h2 id="basketTitle">Your basket</h2>
        <button type="button" class="basket-close" data-close aria-label="Close basket">&times;</button>
      </div>
      <div class="basket-lines" id="basketLines"></div>
      <div class="basket-foot" id="basketFoot"></div>
    </div>`;

  const openBasket = () => {
    drawer.classList.add('is-open');
    drawer.setAttribute('aria-hidden', 'false');
    document.body.classList.add('no-scroll');
    drawer.querySelector('.basket-close').focus();
  };
  const closeBasket = () => {
    drawer.classList.remove('is-open');
    drawer.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('no-scroll');
  };

  function renderBasket() {
    if (!catalogue) return;
    const lines = basketLines();
    const count = lines.reduce((s, l) => s + l.qty, 0);
    const countEl = document.getElementById('basketCount');
    if (countEl) {
      countEl.textContent = count;
      countEl.classList.toggle('is-empty', count === 0);
    }

    const linesEl = document.getElementById('basketLines');
    const footEl = document.getElementById('basketFoot');
    if (!lines.length) {
      linesEl.innerHTML = `<p class="basket-empty">Your basket is empty.</p>`;
      footEl.innerHTML = `<a href="shop.html" class="btn btn-ghost basket-full">Browse the shop</a>`;
      return;
    }

    linesEl.innerHTML = lines.map(({ product: p, qty }) => `
      <div class="basket-line">
        <a href="product.html?id=${encodeURIComponent(p.id)}" class="basket-thumb">${imageHTML(p)}</a>
        <div class="basket-info">
          <a href="product.html?id=${encodeURIComponent(p.id)}" class="basket-name">${esc(p.name)}</a>
          <span class="basket-price">${money(p.price)}</span>
          <div class="qty" data-id="${esc(p.id)}">
            <button type="button" data-step="-1" aria-label="Decrease quantity">&minus;</button>
            <span>${qty}</span>
            <button type="button" data-step="1" aria-label="Increase quantity">+</button>
            <button type="button" class="basket-remove" data-remove>Remove</button>
          </div>
        </div>
        <span class="basket-line-total">${money(p.price * qty)}</span>
      </div>`).join('');

    const t = totals();
    const { freeOver } = catalogue.shipping;
    const nudge = t.shipping > 0
      ? `<p class="basket-nudge">Add ${money(freeOver - t.subtotal)} more for free UK delivery.</p>`
      : `<p class="basket-nudge is-free">You've got free UK delivery.</p>`;

    footEl.innerHTML = `
      ${nudge}
      <dl class="basket-totals">
        <div><dt>Subtotal</dt><dd>${money(t.subtotal)}</dd></div>
        <div><dt>Delivery</dt><dd>${t.shipping ? money(t.shipping) : 'Free'}</dd></div>
        <div class="is-total"><dt>Total</dt><dd>${money(t.total)}</dd></div>
      </dl>
      <button type="button" class="btn btn-primary basket-full" id="checkoutBtn">
        Checkout securely
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
      </button>
      <p class="basket-msg" id="basketMsg" role="status"></p>
      <p class="basket-secure">Payments handled by Stripe. We never see your card details.</p>`;
  }

  drawer.addEventListener('click', (e) => {
    if (e.target.closest('[data-close]')) return closeBasket();
    const qtyEl = e.target.closest('.qty');
    if (qtyEl) {
      const id = qtyEl.dataset.id;
      const current = readBasket()[id] || 0;
      if (e.target.closest('[data-remove]')) return setQty(id, 0);
      const step = e.target.closest('[data-step]');
      if (step) return setQty(id, current + Number(step.dataset.step));
    }
    if (e.target.closest('#checkoutBtn')) checkout();
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && drawer.classList.contains('is-open')) closeBasket(); });
  basketBtn.addEventListener('click', openBasket);

  /* ---------- Checkout ---------- */
  async function checkout() {
    const btn = document.getElementById('checkoutBtn');
    const msg = document.getElementById('basketMsg');
    const items = basketLines().map(l => ({ id: l.product.id, qty: l.qty }));
    btn.disabled = true;
    msg.textContent = 'Taking you to secure checkout…';
    try {
      const res = await fetch('/.netlify/functions/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.url) { location.href = data.url; return; }
      // A basket problem (e.g. sold out) is shown as-is; anything else means
      // card checkout isn't live yet, so offer ordering by email instead.
      if ((res.status === 400 || res.status === 409) && data.error) msg.textContent = data.error;
      else emailFallback(msg);
    } catch {
      emailFallback(msg);
    } finally {
      btn.disabled = false;
    }
  }

  // Used until Stripe is connected: lets the customer send the order by email.
  function emailFallback(msg) {
    const t = totals();
    const body = [
      'Hi, I would like to order:', '',
      ...basketLines().map(l => `${l.qty} x ${l.product.name} (${l.product.id}) – ${money(l.product.price * l.qty)}`),
      '', `Subtotal: ${money(t.subtotal)}`, `Delivery: ${t.shipping ? money(t.shipping) : 'Free'}`, `Total: ${money(t.total)}`,
      '', 'Name:', 'Delivery address:', 'Phone:',
    ].join('\n');
    const href = `mailto:${ORDER_EMAIL}?subject=${encodeURIComponent('Shop order')}&body=${encodeURIComponent(body)}`;
    msg.innerHTML = `Card checkout is being set up. <a href="${href}">Email your order</a> and we'll send a secure payment link.`;
  }

  /* ---------- Product card ---------- */
  const cardHTML = (p) => {
    const out = p.stock <= 0;
    const sale = p.compareAt && p.compareAt > p.price;
    return `
      <article class="product-card">
        <a href="product.html?id=${encodeURIComponent(p.id)}" class="product-media">
          ${imageHTML(p)}
          ${sale ? `<span class="product-badge">Save ${Math.round((1 - p.price / p.compareAt) * 100)}%</span>` : ''}
          ${out ? `<span class="product-badge is-out">Out of stock</span>` : ''}
        </a>
        <div class="product-body">
          <span class="product-cat">${esc(categoryName(p.category))}</span>
          <h3><a href="product.html?id=${encodeURIComponent(p.id)}">${esc(p.name)}</a></h3>
          <div class="product-foot">
            <span class="product-price">${money(p.price)}${sale ? ` <s>${money(p.compareAt)}</s>` : ''}</span>
            <button type="button" class="btn btn-primary btn-sm" data-add="${esc(p.id)}" ${out ? 'disabled' : ''}>${out ? 'Sold out' : 'Add'}</button>
          </div>
        </div>
      </article>`;
  };

  document.addEventListener('click', (e) => {
    const add = e.target.closest('[data-add]');
    if (add && !add.disabled) {
      const qtyInput = document.getElementById('pdpQty');
      addToBasket(add.dataset.add, add.hasAttribute('data-use-qty') && qtyInput ? Math.max(1, Number(qtyInput.value) || 1) : 1);
    }
  });

  /* ---------- Shop listing ---------- */
  function initListing(root) {
    const chips = document.getElementById('shopChips');
    const search = document.getElementById('shopSearch');
    const sort = document.getElementById('shopSort');
    const countEl = document.getElementById('shopCount');
    let active = params.get('category') || 'all';
    if (active !== 'all' && !catalogue.categories.some(c => c.id === active)) active = 'all';

    chips.innerHTML = [{ id: 'all', name: 'All products' }, ...catalogue.categories]
      .map(c => `<button type="button" class="chip" data-cat="${esc(c.id)}">${esc(c.name)}</button>`).join('');

    const render = () => {
      chips.querySelectorAll('.chip').forEach(ch => ch.classList.toggle('is-active', ch.dataset.cat === active));
      const q = search.value.trim().toLowerCase();
      let list = catalogue.products.filter(p =>
        (active === 'all' || p.category === active) &&
        (!q || `${p.name} ${p.brand} ${p.description}`.toLowerCase().includes(q)));
      if (sort.value === 'price-asc') list = [...list].sort((a, b) => a.price - b.price);
      if (sort.value === 'price-desc') list = [...list].sort((a, b) => b.price - a.price);
      if (sort.value === 'name') list = [...list].sort((a, b) => a.name.localeCompare(b.name));
      countEl.textContent = `${list.length} product${list.length === 1 ? '' : 's'}`;
      root.innerHTML = list.length ? list.map(cardHTML).join('') : `<p class="shop-empty">No products match that search.</p>`;
    };

    chips.addEventListener('click', (e) => {
      const ch = e.target.closest('.chip');
      if (!ch) return;
      active = ch.dataset.cat;
      const url = new URL(location.href);
      if (active === 'all') url.searchParams.delete('category'); else url.searchParams.set('category', active);
      history.replaceState(null, '', url);
      render();
    });
    search.addEventListener('input', render);
    sort.addEventListener('change', render);
    render();
  }

  /* ---------- Product detail ---------- */
  function initProduct(root) {
    const p = productById(params.get('id') || '');
    if (!p) {
      root.innerHTML = `<div class="pdp-missing"><h1>Product not found</h1><p>It may have sold out or moved.</p><a href="shop.html" class="btn btn-primary">Back to the shop</a></div>`;
      return;
    }
    document.title = `${p.name} | Crowsons Global Shop`;
    const out = p.stock <= 0;
    const sale = p.compareAt && p.compareAt > p.price;
    const max = Math.min(MAX_QTY, p.stock);
    root.innerHTML = `
      <nav class="pdp-crumbs" aria-label="Breadcrumb">
        <a href="shop.html">Shop</a> <span>/</span>
        <a href="shop.html?category=${encodeURIComponent(p.category)}">${esc(categoryName(p.category))}</a>
      </nav>
      <div class="pdp">
        <div class="pdp-media">${imageHTML(p)}</div>
        <div class="pdp-info">
          ${p.brand ? `<span class="product-cat">${esc(p.brand)}</span>` : ''}
          <h1>${esc(p.name)}</h1>
          <p class="pdp-price">${money(p.price)}${sale ? ` <s>${money(p.compareAt)}</s>` : ''}</p>
          <p class="pdp-stock ${out ? 'is-out' : p.stock <= 5 ? 'is-low' : ''}">
            ${out ? 'Out of stock' : p.stock <= 5 ? `Only ${p.stock} left` : 'In stock, dispatched from the UK'}
          </p>
          <p class="pdp-desc">${esc(p.description)}</p>
          ${p.bullets?.length ? `<ul class="pdp-bullets">${p.bullets.map(b => `<li>${esc(b)}</li>`).join('')}</ul>` : ''}
          <div class="pdp-buy">
            <label class="pdp-qty">Qty
              <input type="number" id="pdpQty" min="1" max="${max}" value="1" ${out ? 'disabled' : ''}>
            </label>
            <button type="button" class="btn btn-primary" data-add="${esc(p.id)}" data-use-qty ${out ? 'disabled' : ''}>
              ${out ? 'Sold out' : 'Add to basket'}
            </button>
          </div>
          <ul class="pdp-assure">
            <li>Free UK delivery over ${money(catalogue.shipping.freeOver)}</li>
            <li>30-day returns. <a href="shipping-returns.html">Delivery &amp; returns</a></li>
            <li>Genuine stock from authorised suppliers</li>
          </ul>
        </div>
      </div>`;
  }

  /* ---------- Boot ---------- */
  document.addEventListener('DOMContentLoaded', async () => {
    const actions = document.querySelector('.nav-actions');
    if (actions) actions.prepend(basketBtn);
    document.body.appendChild(drawer);

    if (params.get('paid') === '1') {
      try { localStorage.removeItem(BASKET_KEY); } catch { /* ignore */ }
      memoryBasket = {};
    }

    try {
      const res = await fetch('data/products.json', { cache: 'no-cache' });
      catalogue = await res.json();
    } catch {
      const grid = document.getElementById('shopGrid');
      if (grid) grid.innerHTML = `<p class="shop-empty">The shop couldn't load. Please refresh the page.</p>`;
      return;
    }

    renderBasket();
    const grid = document.getElementById('shopGrid');
    const pdp = document.getElementById('productView');
    if (grid) initListing(grid);
    if (pdp) initProduct(pdp);
    if (params.get('basket') === 'open') openBasket();
  });
})();
