// Crowsons shop — header, menus, catalogue, product page, basket and checkout.
// Products and categories live in data/products.json.
// The basket is kept in the shopper's own browser.

(() => {
  const SHOP_NAME = 'Crowsons';
  const CONTACT_EMAIL = 'trade@crowsonsglobal.com';
  const BASKET_KEY = 'crowsons_basket_v1';
  const MAX_QTY = 20;
  const PRICE_BANDS = [1000, 2000, 3000]; // "Under £10 / £20 / £30", in pence

  const page = document.body.dataset.page || '';
  const params = new URLSearchParams(location.search);
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const money = (pence) => '£' + (pence / 100).toFixed(2);
  const pounds = (pence) => '£' + Math.round(pence / 100);
  const enc = encodeURIComponent;
  const productUrl = (p) => `product.html?id=${enc(p.id)}`;
  const listUrl = (o = {}) => {
    const u = new URLSearchParams();
    Object.entries(o).forEach(([k, v]) => { if (v !== undefined && v !== '' && v !== null) u.set(k, v); });
    const s = u.toString();
    return `products.html${s ? '?' + s : ''}`;
  };

  /* ---------- Icons ---------- */
  const svg = (paths, sw = 1.8) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
  const I = {
    basket: svg('<path d="M3 9h18l-2 11H5z"/><path d="M8 9l3-6M16 9l-3-6"/>'),
    search: svg('<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>', 2),
    menu: svg('<path d="M4 6h16M4 12h16M4 18h16"/>', 2),
    lock: svg('<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>', 2),
    prev: svg('<path d="M15 6l-6 6 6 6"/>', 2.2),
    next: svg('<path d="M9 6l6 6-6 6"/>', 2.2),
  };
  const CAT_ICONS = {
    'home-kitchen': '<path d="M4 11l8-7 8 7v9H4z"/><path d="M10 20v-6h4v6"/>',
    'health-beauty': '<path d="M12 3c3 4 6 7 6 10.5A6 6 0 0 1 6 13.5C6 10 9 7 12 3z"/>',
    'toys-games': '<rect x="4" y="4" width="7" height="7" rx="1"/><rect x="13" y="4" width="7" height="7" rx="1"/><rect x="4" y="13" width="7" height="7" rx="1"/><circle cx="16.5" cy="16.5" r="3.5"/>',
    'food-drink': '<path d="M5 8h12v6a5 5 0 0 1-5 5h-2a5 5 0 0 1-5-5z"/><path d="M17 10h1.5a2.5 2.5 0 0 1 0 5H17"/><path d="M8 3v2M11 3v2M14 3v2"/>',
    'tech': '<rect x="4" y="5" width="16" height="11" rx="1"/><path d="M2 19h20"/>',
    'pet-supplies': '<circle cx="7" cy="9" r="2"/><circle cx="17" cy="9" r="2"/><circle cx="10" cy="5.5" r="1.8"/><circle cx="14" cy="5.5" r="1.8"/><path d="M12 12c-3 0-5 3.5-5 5.5 0 1.5 1.5 2 2.5 2 1 0 1.5-.5 2.5-.5s1.5.5 2.5.5 2.5-.5 2.5-2c0-2-2-5.5-5-5.5z"/>',
  };
  // Shown until a product has a real photo ("image" in products.json).
  const imageHTML = (p) => p.image
    ? `<img src="${esc(p.image)}" alt="${esc(p.name)}" loading="lazy">`
    : `<div class="ph" role="img" aria-label="${esc(p.name)} (photo coming soon)">${svg(CAT_ICONS[p.category] || '', 1.2)}</div>`;

  /* ---------- Catalogue ---------- */
  let catalogue = null;
  const byId = (id) => catalogue.products.find(p => p.id === id);
  const cat = (id) => catalogue.categories.find(c => c.id === id);
  const catName = (id) => cat(id)?.name || '';
  const sub = (catId, subId) => cat(catId)?.subcategories?.find(s => s.id === subId);
  // Subcategories that currently have products (empty ones stay out of menus).
  const liveSubs = (c) => (c.subcategories || []).filter(s => catalogue.products.some(p => p.category === c.id && p.subcategory === s.id));
  const onSale = (p) => p.compareAt && p.compareAt > p.price;
  const pctOff = (p) => Math.round((1 - p.price / p.compareAt) * 100);
  const inStock = (p) => p.stock > 0;
  // In-stock products with photos, featured first: used for imagery on the home page.
  const showcase = (fn = () => true) => catalogue.products
    .filter(p => p.image && inStock(p) && fn(p))
    .sort((a, b) => (b.featured === true) - (a.featured === true));
  const hasOffers = () => catalogue.products.some(p => onSale(p) && inStock(p));

  /* ---------- Basket storage (memory fallback if storage is blocked) ---------- */
  let memoryBasket = {};
  const readBasket = () => {
    try { return JSON.parse(localStorage.getItem(BASKET_KEY)) || {}; } catch { return { ...memoryBasket }; }
  };
  const writeBasket = (b) => {
    memoryBasket = b;
    try { localStorage.setItem(BASKET_KEY, JSON.stringify(b)); } catch { /* memory only */ }
    updateHeaderBasket();
    if (page === 'basket') renderBasketPage();
  };
  const lines = () => Object.entries(readBasket())
    .map(([id, qty]) => ({ p: byId(id), qty }))
    .filter(l => l.p && l.qty > 0);
  const maxFor = (p) => Math.max(0, Math.min(MAX_QTY, p.stock));
  const addToBasket = (id, qty = 1) => {
    const p = byId(id);
    if (!p || !inStock(p)) return 0;
    const b = readBasket();
    const before = b[id] || 0;
    b[id] = Math.min(before + qty, maxFor(p));
    writeBasket(b);
    return b[id] - before;
  };
  const setQty = (id, qty) => {
    const b = readBasket();
    const p = byId(id);
    if (!p || qty <= 0) delete b[id];
    else b[id] = Math.min(qty, maxFor(p));
    writeBasket(b);
  };
  const totals = () => {
    const ls = lines();
    const subtotal = ls.reduce((s, l) => s + l.p.price * l.qty, 0);
    const { standard, freeOver } = catalogue.shipping;
    const delivery = subtotal === 0 || subtotal >= freeOver ? 0 : standard;
    return { subtotal, delivery, total: subtotal + delivery, count: ls.reduce((s, l) => s + l.qty, 0) };
  };

  /* ---------- Header ---------- */
  function renderHeader() {
    const header = document.getElementById('siteHeader');
    if (!header) return;
    const q = params.get('q') || '';
    const free = catalogue ? pounds(catalogue.shipping.freeOver) : '£30';
    const std = catalogue ? money(catalogue.shipping.standard) : '£3.99';

    header.innerHTML = `
      <div class="topbar"><div class="wrap">
        <a href="contact.html">Track my order</a>
        <a href="delivery-returns.html">Delivery &amp; returns</a>
        <a href="contact.html">Help &amp; contact</a>
      </div></div>
      <div class="masthead"><div class="wrap">
        <button type="button" class="menu-btn" id="menuBtn" aria-label="Open menu" aria-controls="drawer" aria-expanded="false">${I.menu}</button>
        <a href="index.html" class="brand" aria-label="${SHOP_NAME} home"><img src="assets/crow-mark.png" alt=""><span>${SHOP_NAME}</span></a>
        <form class="search" action="products.html" role="search">
          <label for="q" class="sr-only">Search for products</label>
          <input id="q" name="q" type="search" placeholder="Search for products or brands" value="${esc(q)}" autocomplete="off">
          <button type="submit" aria-label="Search">${I.search}</button>
        </form>
        <a href="basket.html" class="basket-btn" aria-label="Basket">
          ${I.basket}<span><small>My basket</small><b id="basketItems">0 items</b></span>
        </a>
      </div></div>
      <nav class="catbar" id="catbar" aria-label="Departments">${catalogue ? catbarHTML() : '<div style="height:56px"></div>'}</nav>
      <div class="promises"><ul class="wrap">
        <li><strong>Free UK delivery over ${free}</strong>On every order</li>
        <li><strong>Dispatched in 1&ndash;2 days</strong>From our UK base</li>
        <li><strong>Standard delivery ${std}</strong>Usually 2&ndash;4 working days</li>
        <li><strong>30-day returns</strong>On most items</li>
      </ul></div>`;

    document.getElementById('menuBtn').addEventListener('click', openDrawer);
    const bar = document.getElementById('catbar');
    // Close the dropdown after a click, until the pointer leaves the bar.
    bar.addEventListener('click', (e) => { if (e.target.closest('.mega a')) bar.classList.add('is-closed'); });
    bar.addEventListener('mouseleave', () => bar.classList.remove('is-closed'));
  }

  function currentNav() {
    if (page !== 'products') return '';
    if (params.get('offers') === '1' && !params.get('category')) return 'offers';
    if (params.get('max') && !params.get('category')) return 'price';
    return params.get('category') || '';
  }

  function catbarHTML() {
    const cur = currentNav();
    const megas = catalogue.categories.map(c => {
      const feat = catalogue.products.find(p => p.category === c.id && p.featured && inStock(p))
        || catalogue.products.find(p => p.category === c.id && inStock(p));
      return `
        <li class="catbar-item ${cur === c.id ? 'is-current' : ''}">
          <a href="${listUrl({ category: c.id })}">${esc(c.name)}</a>
          <div class="mega"><div class="wrap">
            <div>
              <h3>${esc(c.name)}</h3>
              <div class="mega-links">
                ${liveSubs(c).map(s => `<a href="${listUrl({ category: c.id, sub: s.id })}">${esc(s.name)}</a>`).join('')}
              </div>
              <a class="mega-all" href="${listUrl({ category: c.id })}">Shop all ${esc(c.name)}</a>
            </div>
            ${feat ? `
            <div class="mega-feature">
              <span>${onSale(feat) ? 'On offer' : 'Popular'}</span>
              <a href="${productUrl(feat)}">
                <div class="thumb">${imageHTML(feat)}</div>
                <p>${esc(feat.name)}<strong>${money(feat.price)}</strong></p>
              </a>
            </div>` : ''}
          </div></div>
        </li>`;
    }).join('');
    return `<ul class="wrap catbar-list">
      ${hasOffers() ? `<li class="catbar-item catbar-item--offer ${cur === 'offers' ? 'is-current' : ''}"><a href="${listUrl({ offers: 1 })}">Offers</a></li>` : ''}
      ${megas}
      <li class="catbar-item catbar-item--price ${cur === 'price' ? 'is-current' : ''}"><a href="${listUrl({ max: PRICE_BANDS[1] })}">Under ${pounds(PRICE_BANDS[1])}</a></li>
    </ul>`;
  }

  /* ---------- Mobile drawer ---------- */
  const drawer = document.createElement('div');
  drawer.className = 'drawer';
  drawer.id = 'drawer';
  function buildDrawer() {
    drawer.innerHTML = `
      <div class="drawer-scrim" data-close></div>
      <nav class="drawer-panel" aria-label="Menu">
        <div class="drawer-head"><span>Shop by department</span><button type="button" data-close aria-label="Close menu">&times;</button></div>
        ${hasOffers() ? `<a href="${listUrl({ offers: 1 })}" class="is-offer">Offers</a>` : ''}
        ${catalogue.categories.map(c => `
          <details>
            <summary>${esc(c.name)}</summary>
            <a href="${listUrl({ category: c.id })}"><strong>Shop all ${esc(c.name)}</strong></a>
            ${liveSubs(c).map(s => `<a href="${listUrl({ category: c.id, sub: s.id })}">${esc(s.name)}</a>`).join('')}
          </details>`).join('')}
        ${PRICE_BANDS.map(b => `<a href="${listUrl({ max: b })}">Under ${pounds(b)}</a>`).join('')}
        <a href="delivery-returns.html">Delivery &amp; returns</a>
        <a href="contact.html">Help &amp; contact</a>
      </nav>`;
  }
  function openDrawer() {
    if (!catalogue) return;
    drawer.classList.add('is-open');
    document.body.classList.add('no-scroll');
    document.getElementById('menuBtn')?.setAttribute('aria-expanded', 'true');
    drawer.querySelector('.drawer-head button').focus();
  }
  function closeDrawer() {
    drawer.classList.remove('is-open');
    document.body.classList.remove('no-scroll');
    document.getElementById('menuBtn')?.setAttribute('aria-expanded', 'false');
  }
  drawer.addEventListener('click', (e) => { if (e.target.closest('[data-close]')) closeDrawer(); });

  /* ---------- Footer ---------- */
  function renderFooter() {
    const footer = document.getElementById('siteFooter');
    if (!footer) return;
    const joined = params.get('subscribed') === '1';
    footer.innerHTML = `
      <footer class="footer">
        <section class="signup" aria-labelledby="signupTitle">
          <div class="wrap">
            <h2 id="signupTitle">Sign up for emails with our latest offers and new arrivals</h2>
            <p>For details on how we use your information, read our <a href="privacy.html">Privacy policy</a> and <a href="privacy.html#cookies">Cookie policy</a>.</p>
            ${joined ? '<p class="notice">Thanks, you\'re signed up. Look out for our next email.</p>' : `
            <form class="signup-form" name="newsletter" method="POST" action="${esc(location.pathname.split('/').pop() || 'index.html')}?subscribed=1#siteFooter" data-netlify="true" netlify-honeypot="bot-field">
              <input type="hidden" name="form-name" value="newsletter">
              <p hidden><label>Leave this empty <input name="bot-field"></label></p>
              <label for="signupEmail" class="sr-only">Email address</label>
              <input id="signupEmail" type="email" name="email" placeholder="Please enter your email" required autocomplete="email">
              <button type="submit" class="btn btn-primary">Sign up</button>
            </form>`}
          </div>
        </section>
        <div class="wrap footer-links">
          <div><h3>${SHOP_NAME}</h3><ul>
            <li><a href="about.html">About us</a></li>
            ${(catalogue?.categories || []).map(c => `<li><a href="${listUrl({ category: c.id })}">${esc(c.name)}</a></li>`).join('')}
            ${catalogue && hasOffers() ? `<li><a href="${listUrl({ offers: 1 })}">Offers</a></li>` : ''}
          </ul></div>
          <div><h3>Information</h3><ul>
            <li><a href="delivery-returns.html">Delivery</a></li>
            <li><a href="delivery-returns.html#returns">Returns &amp; refunds</a></li>
            <li><a href="terms.html">Terms of sale</a></li>
            <li><a href="privacy.html">Privacy policy</a></li>
            <li><a href="privacy.html#cookies">Cookie policy</a></li>
          </ul></div>
          <div><h3>Help &amp; advice</h3><ul>
            <li><a href="contact.html">Contact us</a></li>
            <li><a href="contact.html">Track my order</a></li>
            <li><a href="faq.html">FAQs</a></li>
            <li><a href="basket.html">Your basket</a></li>
          </ul></div>
          <div class="footer-pay">
            <h3>Ways to pay</h3>
            <div class="pay-methods"><span>VISA</span><span>Mastercard</span><span>Amex</span><span>Apple Pay</span><span>Google Pay</span></div>
            <p>Payments are processed securely by Stripe. We never see or store your card details.</p>
          </div>
        </div>
        <div class="footer-bottom">
          <div class="wrap">
            <div class="footer-bottom-row">
              <span>&copy; ${new Date().getFullYear()} Crowsons Global Ltd. All rights reserved.</span>
              <a href="index.html" class="brand"><img src="assets/crow-mark.png" alt=""><span>${SHOP_NAME}</span></a>
              <a href="#main" class="to-top">Back to top &uarr;</a>
            </div>
            <p class="legal">${SHOP_NAME} is a trading name of Crowsons Global Ltd, a company registered in England and Wales (company number 16709080). Registered in Peterborough, United Kingdom. Prices include VAT where applicable. Your statutory rights are not affected.</p>
          </div>
        </div>
      </footer>`;
  }

  function updateHeaderBasket() {
    if (!catalogue) return;
    const t = totals();
    const el = document.getElementById('basketItems');
    if (el) el.textContent = t.count ? `${t.count} item${t.count === 1 ? '' : 's'} · ${money(t.subtotal)}` : '0 items';
  }

  /* ---------- Product card ---------- */
  const wasHTML = (p) => onSale(p) ? `Was <s>${money(p.compareAt)}</s> &middot; save ${money(p.compareAt - p.price)}` : '';
  const card = (p) => {
    const out = !inStock(p);
    return `
      <article class="card">
        ${out ? '<span class="badge badge--dark">Out of stock</span>' : onSale(p) ? `<span class="badge">Save ${pctOff(p)}%</span>` : ''}
        <a href="${productUrl(p)}" class="card-media" tabindex="-1" aria-hidden="true">${imageHTML(p)}</a>
        <div class="card-body">
          <h3 class="card-title"><a href="${productUrl(p)}">${esc(p.name)}</a></h3>
          <span class="price ${onSale(p) ? 'is-offer' : ''}">${money(p.price)}</span>
          <span class="was">${wasHTML(p)}</span>
          <span class="stock-note">${!out && p.stock <= 5 ? `Only ${p.stock} left` : ''}</span>
          <button type="button" class="btn btn-primary btn-block" data-add="${esc(p.id)}" ${out ? 'disabled' : ''}>${out ? 'Out of stock' : 'Add to basket'}</button>
        </div>
      </article>`;
  };

  /* ---------- Added-to-basket popup ---------- */
  const popup = document.createElement('div');
  popup.className = 'added';
  popup.setAttribute('role', 'dialog');
  popup.setAttribute('aria-label', 'Added to basket');
  let popupTimer;
  function showAdded(p, added) {
    const t = totals();
    popup.innerHTML = `
      <div class="added-head">
        <span>${added > 0 ? 'Added to your basket' : 'You have the maximum of this item'}</span>
        <button type="button" class="added-close" aria-label="Close">&times;</button>
      </div>
      <div class="added-item">
        <div class="thumb">${imageHTML(p)}</div>
        <div>${esc(p.name)}<small>Basket: ${t.count} item${t.count === 1 ? '' : 's'} &middot; ${money(t.subtotal)}</small></div>
      </div>
      <div class="added-actions">
        <a href="basket.html" class="btn btn-outline">View basket</a>
        <button type="button" class="btn btn-primary" data-checkout>Checkout</button>
      </div>`;
    popup.classList.add('is-open');
    clearTimeout(popupTimer);
    popupTimer = setTimeout(() => popup.classList.remove('is-open'), 7000);
  }
  popup.addEventListener('mouseenter', () => clearTimeout(popupTimer));
  popup.addEventListener('click', (e) => { if (e.target.closest('.added-close')) popup.classList.remove('is-open'); });

  /* ---------- Global handlers ---------- */
  document.addEventListener('click', (e) => {
    const add = e.target.closest('[data-add]');
    if (add && !add.disabled) {
      const qtyInput = add.hasAttribute('data-use-qty') ? document.getElementById('pdpQty') : null;
      const qty = qtyInput ? Math.max(1, Number(qtyInput.value) || 1) : 1;
      const p = byId(add.dataset.add);
      const added = addToBasket(p.id, qty);
      if (add.hasAttribute('data-buy-now')) { location.href = 'basket.html'; return; }
      showAdded(p, added);
    }
    const checkoutBtn = e.target.closest('[data-checkout]');
    if (checkoutBtn) startCheckout(checkoutBtn);
  });
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    popup.classList.remove('is-open');
    closeDrawer();
    document.getElementById('catbar')?.classList.add('is-closed');
    document.activeElement?.blur?.();
  });

  /* ---------- Checkout ---------- */
  async function startCheckout(btn) {
    if (!lines().length) { location.href = 'basket.html'; return; }
    const msg = document.getElementById('checkoutMsg');
    const original = btn.innerHTML;
    btn.disabled = true;
    btn.textContent = 'Opening secure checkout…';
    try {
      const res = await fetch('/.netlify/functions/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items: lines().map(l => ({ id: l.p.id, qty: l.qty })) }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.url) { location.href = data.url; return; }
      if (!msg) { location.href = 'basket.html?checkout=1'; return; }
      // A basket problem (e.g. sold out) is shown as-is; anything else means
      // card payments aren't switched on yet, so offer ordering by email.
      if ((res.status === 400 || res.status === 409) && data.error) msg.textContent = data.error;
      else msg.innerHTML = emailFallback();
    } catch {
      if (!msg) { location.href = 'basket.html?checkout=1'; return; }
      msg.innerHTML = emailFallback();
    } finally {
      btn.disabled = false;
      btn.innerHTML = original;
    }
  }

  function emailFallback() {
    const t = totals();
    const body = [
      'Hi, I would like to order:', '',
      ...lines().map(l => `${l.qty} x ${l.p.name} (${l.p.id}) - ${money(l.p.price * l.qty)}`),
      '', `Subtotal: ${money(t.subtotal)}`, `Delivery: ${t.delivery ? money(t.delivery) : 'Free'}`, `Total: ${money(t.total)}`,
      '', 'Name:', 'Delivery address:', 'Phone:',
    ].join('\n');
    const href = `mailto:${CONTACT_EMAIL}?subject=${enc(`Order from ${SHOP_NAME}`)}&body=${enc(body)}`;
    return `Card payments are being switched on. For now, <a href="${href}">email us your order</a> and we'll reply with a secure payment link.`;
  }

  /* ---------- Home page ---------- */
  function initHome() {
    const offers = catalogue.products.filter(p => onSale(p) && inStock(p)).sort((a, b) => pctOff(b) - pctOff(a));
    const maxPct = offers.length ? pctOff(offers[0]) : 0;

    const strip = document.getElementById('promoStrip');
    const hero = document.getElementById('heroBanner');
    if (offers.length) {
      strip.innerHTML = `<div class="wrap">
        <strong>Winter deals</strong><span>Up to ${maxPct}% off selected lines</span>
        <a href="${listUrl({ offers: 1 })}" class="btn btn-white">Shop offers</a></div>`;
      hero.innerHTML = `
        <div class="hero-copy">
          <span class="tag">Now on</span>
          <h1>Winter deals <em>up to ${maxPct}% off</em></h1>
          <p>Savings across home, beauty, toys and pet essentials, while stocks last.</p>
          <div class="actions">
            <a href="${listUrl({ offers: 1 })}" class="btn btn-white btn-lg">Shop all offers</a>
            <a href="products.html" class="btn btn-lg" style="color:#fff;border-color:rgba(255,255,255,.5)">Browse everything</a>
          </div>
        </div>
        <div class="hero-deals">
          <h2>Top deals this week</h2>
          ${offers.slice(0, 3).map(p => `
            <a href="${productUrl(p)}" class="deal-row">
              <div class="thumb">${imageHTML(p)}</div>
              <p>${esc(p.name)}<br><small>${esc(catName(p.category))}</small></p>
              <span class="now">${money(p.price)}<s>${money(p.compareAt)}</s></span>
            </a>`).join('')}
        </div>`;
    } else {
      // No offers running: lead with delivery and best sellers instead.
      const picks = showcase();
      const lead = picks.find(p => p.category === 'home-kitchen') || picks[0];
      const others = picks.filter(p => p !== lead && p.category !== lead.category).slice(0, 2);
      strip.innerHTML = `<div class="wrap">
        <strong>Free UK delivery</strong><span>on orders over ${pounds(catalogue.shipping.freeOver)}</span>
        <a href="products.html" class="btn btn-white">Shop now</a></div>`;
      hero.innerHTML = `
        <div class="hero-copy">
          <span class="tag">${catalogue.products.filter(inStock).length} products in stock</span>
          <h1>Big brands, <em>sent from the UK</em></h1>
          <p>Lindt, Braun, Shark, Tefal, Garmin and more. Genuine stock, dispatched within 1&ndash;2 working days.</p>
          <div class="actions">
            <a href="products.html" class="btn btn-white btn-lg">Shop all products</a>
            <a href="${listUrl({ max: PRICE_BANDS[1] })}" class="btn btn-lg" style="color:#fff;border-color:rgba(255,255,255,.5)">Gifts under ${pounds(PRICE_BANDS[1])}</a>
          </div>
        </div>
        <div class="hero-spot">
          <a href="${productUrl(lead)}" class="spot-main">
            <img src="${esc(lead.image)}" alt="${esc(lead.name)}">
            <div class="spot-tag">
              <small>Best seller</small>
              <p>${esc(lead.name)}</p>
              <strong>${money(lead.price)}</strong>
            </div>
          </a>
          <div class="spot-row">
            ${others.map(p => `
              <a href="${productUrl(p)}" class="spot-mini">
                <img src="${esc(p.image)}" alt="${esc(p.name)}" loading="lazy">
                <p>${esc(p.name)}<strong>${money(p.price)}</strong></p>
              </a>`).join('')}
          </div>
        </div>`;
    }

    document.getElementById('catTiles').innerHTML = catalogue.categories.map(c => `
      <a href="${listUrl({ category: c.id })}" class="tile tile--${esc(c.id)}">
        <div class="tile-head">${esc(c.name)}<small>${liveSubs(c).slice(0, 3).map(s => esc(s.name)).join(' &middot; ')}</small></div>
        <div class="tile-body">
          ${c.image
            ? `<img class="tile-photo" src="${esc(c.image)}" alt="" loading="lazy">`
            : `<div class="tile-collage">${showcase(p => p.category === c.id).slice(0, 3).map((p, i) =>
                `<img class="c${i + 1}" src="${esc(p.image)}" alt="" loading="lazy">`).join('')}</div>`}
        </div>
        <span class="btn btn-white">Shop now</span>
      </a>`).join('');

    const brandStrip = document.getElementById('brands');
    if (brandStrip) {
      const counts = {};
      catalogue.products.filter(inStock).forEach(p => { if (p.brand) counts[p.brand] = (counts[p.brand] || 0) + 1; });
      brandStrip.innerHTML = Object.keys(counts).sort((a, b) => counts[b] - counts[a] || a.localeCompare(b)).slice(0, 18)
        .map(b => `<a href="${listUrl({ q: b })}">${esc(b)}</a>`).join('');
    }

    const trending = catalogue.products.filter(p => p.featured && inStock(p));
    document.getElementById('trending').innerHTML = (trending.length ? trending : catalogue.products).map(card).join('');
    initCarousel(document.querySelector('[data-carousel]'));

    const priceTiles = document.getElementById('priceTiles');
    priceTiles.innerHTML = PRICE_BANDS.map(b => `
      <a href="${listUrl({ max: b })}" class="price-tile"><small>Gifts &amp; essentials</small><strong>Under ${pounds(b)}</strong><span>Shop now</span></a>`).join('')
      + (hasOffers()
        ? `<a href="${listUrl({ offers: 1 })}" class="price-tile"><small>Limited time</small><strong>Offers</strong><span>Shop the deals</span></a>`
        : `<a href="${listUrl({ max: 5000 })}" class="price-tile"><small>Gifts &amp; essentials</small><strong>Under £50</strong><span>Shop now</span></a>`);

    const offersGrid = document.getElementById('offersGrid');
    if (offers.length) offersGrid.innerHTML = offers.slice(0, 4).map(card).join('');
    else document.getElementById('offersBlock').remove();
  }

  function initCarousel(root) {
    if (!root) return;
    const track = root.querySelector('.carousel-track');
    const prev = root.querySelector('.carousel-btn--prev');
    const next = root.querySelector('.carousel-btn--next');
    const step = () => track.clientWidth * 0.9;
    const update = () => {
      prev.disabled = track.scrollLeft < 8;
      next.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 8;
    };
    prev.addEventListener('click', () => track.scrollBy({ left: -step(), behavior: 'smooth' }));
    next.addEventListener('click', () => track.scrollBy({ left: step(), behavior: 'smooth' }));
    track.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    update();
  }

  /* ---------- Listing page ---------- */
  function initListing() {
    const grid = document.getElementById('grid');
    const sort = document.getElementById('sort');
    const stockOnly = document.getElementById('inStock');
    const offersOnly = document.getElementById('offersOnly');

    let category = params.get('category') || '';
    if (category && !cat(category)) category = '';
    let subId = params.get('sub') || '';
    if (subId && !sub(category, subId)) subId = '';
    const q = (params.get('q') || '').trim();
    const max = Number(params.get('max')) || 0;
    offersOnly.checked = params.get('offers') === '1';

    const subObj = subId ? sub(category, subId) : null;
    let heading = 'All products';
    if (q) heading = `Results for “${q}”`;
    else if (subObj) heading = subObj.name;
    else if (category) heading = catName(category);
    else if (offersOnly.checked) heading = 'Offers';
    else if (max) heading = `Under ${pounds(max)}`;
    document.getElementById('listTitle').textContent = heading;
    document.title = `${heading} | ${SHOP_NAME}`;

    const crumbs = [`<a href="index.html">Home</a>`];
    if (category) crumbs.push(subObj ? `<a href="${listUrl({ category })}">${esc(catName(category))}</a>` : `<span>${esc(catName(category))}</span>`);
    if (subObj) crumbs.push(`<span>${esc(subObj.name)}</span>`);
    if (!category) crumbs.push(`<span>${esc(heading)}</span>`);
    document.getElementById('crumbs').innerHTML = crumbs.join('<span>/</span>');

    // Sidebar: departments, with the current one's subcategories underneath
    const count = (fn) => catalogue.products.filter(fn).length;
    const keep = { q, max: max || '', offers: offersOnly.checked ? 1 : '' };
    document.getElementById('catList').innerHTML = [
      `<li><a href="${listUrl(keep)}" class="${!category ? 'is-active' : ''}">All departments <span>${catalogue.products.length}</span></a></li>`,
      ...catalogue.categories.map(c => `
        <li><a href="${listUrl({ ...keep, category: c.id })}" class="${category === c.id && !subId ? 'is-active' : ''}">${esc(c.name)} <span>${count(p => p.category === c.id)}</span></a>
        ${category === c.id ? `<ul class="sub">${liveSubs(c).map(s => {
          const n = count(p => p.category === c.id && p.subcategory === s.id);
          return `<li><a href="${listUrl({ ...keep, category: c.id, sub: s.id })}" class="${subId === s.id ? 'is-active' : ''}">${esc(s.name)} <span>${n}</span></a></li>`;
        }).join('')}</ul>` : ''}</li>`),
    ].join('');
    document.getElementById('priceList').innerHTML = [
      `<li><a href="${listUrl({ q, category, sub: subId, offers: keep.offers })}" class="${!max ? 'is-active' : ''}">Any price</a></li>`,
      ...PRICE_BANDS.map(b => `<li><a href="${listUrl({ q, category, sub: subId, offers: keep.offers, max: b })}" class="${max === b ? 'is-active' : ''}">Under ${pounds(b)}</a></li>`),
    ].join('');

    const render = () => {
      const words = q.toLowerCase().split(/\s+/).filter(Boolean);
      let list = catalogue.products.filter(p => {
        if (category && p.category !== category) return false;
        if (subId && p.subcategory !== subId) return false;
        if (max && p.price >= max) return false;
        if (stockOnly.checked && !inStock(p)) return false;
        if (offersOnly.checked && !onSale(p)) return false;
        const s = sub(p.category, p.subcategory);
        const hay = `${p.name} ${p.brand} ${p.description} ${catName(p.category)} ${s ? s.name : ''}`.toLowerCase();
        return words.every(w => hay.includes(w));
      });
      const by = sort.value;
      if (by === 'price-asc') list = [...list].sort((a, b) => a.price - b.price);
      else if (by === 'price-desc') list = [...list].sort((a, b) => b.price - a.price);
      else if (by === 'name') list = [...list].sort((a, b) => a.name.localeCompare(b.name));
      else if (by === 'saving') list = [...list].sort((a, b) => (onSale(b) ? pctOff(b) : 0) - (onSale(a) ? pctOff(a) : 0));
      else list = [...list].sort((a, b) => inStock(b) - inStock(a) || (b.featured === true) - (a.featured === true));
      document.getElementById('resultCount').textContent = `${list.length} product${list.length === 1 ? '' : 's'}`;
      grid.innerHTML = list.length ? list.map(card).join('') : `
        <div class="empty">
          <p>Nothing matches${q ? ` “${esc(q)}”` : ''} yet. Try another search or clear the filters.</p>
          <a href="products.html" class="btn btn-outline">See all products</a>
        </div>`;
    };
    [sort, stockOnly, offersOnly].forEach(el => el.addEventListener('change', render));
    document.getElementById('filtersToggle').addEventListener('click', (e) => {
      const open = document.getElementById('filters').classList.toggle('is-open');
      e.currentTarget.setAttribute('aria-expanded', String(open));
    });
    render();
  }

  /* ---------- Product page ---------- */
  function initProduct() {
    const root = document.getElementById('product');
    const p = byId(params.get('id') || '');
    if (!p) {
      root.innerHTML = `<div class="empty" style="margin:20px 0"><p>Sorry, we couldn't find that product. It may have sold out or been removed.</p><a href="products.html" class="btn btn-primary">Browse all products</a></div>`;
      document.getElementById('relatedBlock')?.remove();
      return;
    }
    document.title = `${p.name} | ${SHOP_NAME}`;
    const out = !inStock(p);
    const max = maxFor(p);
    const s = sub(p.category, p.subcategory);
    const stockText = out ? 'Out of stock' : p.stock <= 5 ? `Low stock: only ${p.stock} left` : 'In stock';
    const { standard, freeOver } = catalogue.shipping;

    root.innerHTML = `
      <nav class="crumbs" aria-label="Breadcrumb">
        <a href="index.html">Home</a><span>/</span>
        <a href="${listUrl({ category: p.category })}">${esc(catName(p.category))}</a>
        ${s ? `<span>/</span><a href="${listUrl({ category: p.category, sub: s.id })}">${esc(s.name)}</a>` : ''}
      </nav>
      <div class="pdp">
        <div>
          <div class="pdp-media">
            ${onSale(p) && !out ? `<span class="badge">Save ${pctOff(p)}%</span>` : ''}
            ${imageHTML(p)}
          </div>
          ${p.images?.length > 1 ? `
          <div class="pdp-thumbs" role="group" aria-label="More photos">
            ${p.images.map((src, i) => `
              <button type="button" class="${i === 0 ? 'is-active' : ''}" data-photo="${esc(src)}" aria-label="Photo ${i + 1} of ${p.images.length}">
                <img src="${esc(src)}" alt="" loading="lazy">
              </button>`).join('')}
          </div>` : ''}
        </div>
        <div>
          ${p.brand ? `<a class="pdp-brand" href="${listUrl({ q: p.brand })}">${esc(p.brand)}</a>` : ''}
          <h1>${esc(p.name)}</h1>
          <p class="pdp-code">Product code: ${esc(p.id.toUpperCase())}</p>
          <div class="price ${onSale(p) ? 'is-offer' : ''}">${money(p.price)}</div>
          ${onSale(p) ? `<p class="was">Was <s>${money(p.compareAt)}</s><span class="pdp-save">Save ${money(p.compareAt - p.price)}</span></p>` : ''}
          <p class="pdp-stock ${out ? 'is-out' : p.stock <= 5 ? 'is-low' : ''}">${stockText}</p>
          <div class="buy-box">
            <div class="buy-row">
              <div class="stepper" data-stepper>
                <button type="button" data-step="-1" aria-label="Decrease quantity" ${out ? 'disabled' : ''}>&minus;</button>
                <input type="number" id="pdpQty" value="1" min="1" max="${max}" aria-label="Quantity" ${out ? 'disabled' : ''}>
                <button type="button" data-step="1" aria-label="Increase quantity" ${out ? 'disabled' : ''}>+</button>
              </div>
              <button type="button" class="btn btn-primary btn-lg" data-add="${esc(p.id)}" data-use-qty ${out ? 'disabled' : ''}>${I.basket} ${out ? 'Out of stock' : 'Add to basket'}</button>
            </div>
            ${out ? '' : `<button type="button" class="btn btn-outline btn-block" data-add="${esc(p.id)}" data-use-qty data-buy-now>Buy now</button>`}
          </div>
          <div class="assure">
            <p><strong>UK delivery ${money(standard)}, free over ${money(freeOver)}</strong>Dispatched within 1&ndash;2 working days.</p>
            <p><strong>30-day returns</strong>Changed your mind? See <a href="delivery-returns.html">delivery &amp; returns</a>.</p>
            <p><strong>Secure checkout</strong>Pay by card, Apple Pay or Google Pay through Stripe.</p>
          </div>
        </div>
      </div>
      <section class="details">
        <h2>Product details</h2>
        <p>${esc(p.description)}</p>
        ${p.bullets?.length ? `<ul>${p.bullets.map(b => `<li>${esc(b)}</li>`).join('')}</ul>` : ''}
      </section>`;

    root.querySelector('.pdp-thumbs')?.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-photo]');
      if (!btn) return;
      root.querySelector('.pdp-media img').src = btn.dataset.photo;
      root.querySelectorAll('.pdp-thumbs button').forEach(t => t.classList.toggle('is-active', t === btn));
    });

    const qty = document.getElementById('pdpQty');
    root.querySelector('[data-stepper]')?.addEventListener('click', (e) => {
      const step = e.target.closest('[data-step]');
      if (step) qty.value = Math.min(max, Math.max(1, (Number(qty.value) || 1) + Number(step.dataset.step)));
    });
    qty?.addEventListener('change', () => { qty.value = Math.min(max, Math.max(1, Math.floor(Number(qty.value)) || 1)); });

    const related = catalogue.products.filter(r => r.category === p.category && r.id !== p.id && inStock(r)).slice(0, 4);
    if (related.length) document.getElementById('related').innerHTML = related.map(card).join('');
    else document.getElementById('relatedBlock')?.remove();
  }

  /* ---------- Basket page ---------- */
  function renderBasketPage() {
    const root = document.getElementById('basketRoot');
    if (!root) return;
    const ls = lines();
    if (!ls.length) {
      root.innerHTML = `
        <div class="empty" style="margin-bottom:60px">
          <p style="font-size:18px;color:var(--ink)"><strong>Your basket is empty</strong></p>
          <p>There's free UK delivery on orders over ${money(catalogue.shipping.freeOver)}.</p>
          <a href="products.html" class="btn btn-primary">Start shopping</a>
        </div>`;
      return;
    }
    const t = totals();
    const { freeOver } = catalogue.shipping;
    const pct = Math.min(100, Math.round((t.subtotal / freeOver) * 100));
    const keepMsg = document.getElementById('checkoutMsg')?.innerHTML || '';
    root.innerHTML = `
      <div class="basket-page">
        <div>
          <div class="basket-lines">
            ${ls.map(({ p, qty }) => `
              <div class="line">
                <a href="${productUrl(p)}" class="thumb">${imageHTML(p)}</a>
                <div>
                  <a href="${productUrl(p)}" class="line-name">${esc(p.name)}</a>
                  <p class="line-meta">${money(p.price)} each${p.stock <= 5 ? ` &middot; only ${p.stock} left` : ''}</p>
                  <div class="line-actions">
                    <div class="stepper stepper--sm" data-line="${esc(p.id)}">
                      <button type="button" data-step="-1" aria-label="Decrease quantity of ${esc(p.name)}">&minus;</button>
                      <input type="number" value="${qty}" min="1" max="${maxFor(p)}" aria-label="Quantity of ${esc(p.name)}">
                      <button type="button" data-step="1" aria-label="Increase quantity of ${esc(p.name)}" ${qty >= maxFor(p) ? 'disabled' : ''}>+</button>
                    </div>
                    <button type="button" class="link-btn" data-remove="${esc(p.id)}">Remove</button>
                  </div>
                </div>
                <span class="line-total">${money(p.price * qty)}</span>
              </div>`).join('')}
          </div>
          <a href="products.html" class="continue">&larr; Continue shopping</a>
        </div>
        <aside class="summary" aria-label="Order summary">
          <h2>Order summary</h2>
          <div class="free-bar ${t.delivery ? '' : 'is-free'}">
            ${t.delivery ? `Spend ${money(freeOver - t.subtotal)} more for free UK delivery` : 'Your order qualifies for free UK delivery'}
            <div class="bar"><i style="width:${pct}%"></i></div>
          </div>
          <dl>
            <div><dt>Items (${t.count})</dt><dd>${money(t.subtotal)}</dd></div>
            <div><dt>UK delivery</dt><dd>${t.delivery ? money(t.delivery) : 'Free'}</dd></div>
            <div class="is-total"><dt>Total</dt><dd>${money(t.total)}</dd></div>
          </dl>
          <button type="button" class="btn btn-primary btn-lg btn-block" data-checkout>${I.lock} Proceed to checkout</button>
          <p class="checkout-msg" id="checkoutMsg" role="status">${keepMsg}</p>
          <p class="secure">Secure payment by Stripe. We never see your card details.</p>
          <div class="pay-methods" aria-label="Accepted payment methods"><span>VISA</span><span>Mastercard</span><span>Amex</span><span>Apple Pay</span><span>Google Pay</span></div>
        </aside>
      </div>`;
  }

  function initBasket() {
    const root = document.getElementById('basketRoot');
    root.addEventListener('click', (e) => {
      const rm = e.target.closest('[data-remove]');
      if (rm) return setQty(rm.dataset.remove, 0);
      const step = e.target.closest('[data-step]');
      const st = e.target.closest('[data-line]');
      if (step && st) setQty(st.dataset.line, (readBasket()[st.dataset.line] || 0) + Number(step.dataset.step));
    });
    root.addEventListener('change', (e) => {
      const st = e.target.closest('[data-line]');
      if (st && e.target.matches('input')) setQty(st.dataset.line, Math.floor(Number(e.target.value)) || 0);
    });
    renderBasketPage();
    if (params.get('checkout') === '1') {
      const msg = document.getElementById('checkoutMsg');
      if (msg) msg.innerHTML = emailFallback();
    }
  }

  /* ---------- Boot ---------- */
  renderHeader();
  renderFooter();
  document.body.append(popup, drawer);

  if (page === 'complete') {
    try { localStorage.removeItem(BASKET_KEY); } catch { /* ignore */ }
    memoryBasket = {};
  }
  if (page === 'contact' && params.get('sent') === '1') {
    document.getElementById('contactSent')?.removeAttribute('hidden');
  }

  fetch('data/products.json', { cache: 'no-cache' })
    .then(r => r.json())
    .then(data => {
      data.products = data.products.filter(p => !p.hidden);
      catalogue = data;
      renderHeader();
      renderFooter();
      buildDrawer();
      updateHeaderBasket();
      if (page === 'home') initHome();
      if (page === 'products') initListing();
      if (page === 'product') initProduct();
      if (page === 'basket') initBasket();
    })
    .catch(() => {
      const main = document.querySelector('main');
      if (main) main.insertAdjacentHTML('afterbegin', '<div class="wrap"><p class="empty" style="margin:24px 0">Sorry, the shop could not load. Please refresh the page.</p></div>');
    });
})();
