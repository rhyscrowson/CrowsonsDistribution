// Crowsons shop — header/footer, catalogue, product page, basket and checkout.
// Products live in data/products.json. The basket is kept in the shopper's browser.

(() => {
  const SHOP_NAME = 'Crowsons';
  const CONTACT_EMAIL = 'trade@crowsonsglobal.com';
  const BASKET_KEY = 'crowsons_basket_v1';
  const MAX_QTY = 20;

  const page = document.body.dataset.page || '';
  const params = new URLSearchParams(location.search);
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const money = (pence) => '£' + (pence / 100).toFixed(2);
  const productUrl = (p) => `product.html?id=${encodeURIComponent(p.id)}`;

  /* ---------- Icons ---------- */
  const svg = (paths, extra = '') => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" ${extra}>${paths}</svg>`;
  const I = {
    bag: svg('<path d="M5 8h14l-1.2 11.2a1 1 0 0 1-1 .8H7.2a1 1 0 0 1-1-.8z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/>'),
    search: svg('<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>'),
    check: svg('<path d="M20 6L9 17l-5-5"/>'),
    truck: svg('<path d="M3 6h11v10H3z"/><path d="M14 9h4l3 3v4h-7"/><circle cx="7" cy="17.5" r="1.8"/><circle cx="17.5" cy="17.5" r="1.8"/>'),
    box: svg('<path d="M21 8l-9-5-9 5 9 5 9-5z"/><path d="M3 8v8l9 5 9-5V8"/><path d="M12 13v8"/>'),
    back: svg('<path d="M9 14l-5-5 5-5"/><path d="M4 9h11a5 5 0 0 1 0 10h-3"/>'),
    lock: svg('<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>'),
    shield: svg('<path d="M12 3l8 3v6c0 4.5-3.4 8.2-8 9-4.6-.8-8-4.5-8-9V6z"/><path d="M9 12l2 2 4-4"/>'),
    arrow: svg('<path d="M5 12h14M13 6l6 6-6 6"/>'),
  };
  const CAT_ICONS = {
    'home-kitchen': '<path d="M4 11l8-7 8 7v9H4z"/><path d="M10 20v-6h4v6"/>',
    'health-beauty': '<path d="M12 3c3 4 6 7 6 10.5A6 6 0 0 1 6 13.5C6 10 9 7 12 3z"/>',
    'toys-games': '<rect x="4" y="4" width="7" height="7" rx="1"/><rect x="13" y="4" width="7" height="7" rx="1"/><rect x="4" y="13" width="7" height="7" rx="1"/><circle cx="16.5" cy="16.5" r="3.5"/>',
    'pet-supplies': '<circle cx="7" cy="9" r="2"/><circle cx="17" cy="9" r="2"/><circle cx="10" cy="5.5" r="1.8"/><circle cx="14" cy="5.5" r="1.8"/><path d="M12 12c-3 0-5 3.5-5 5.5 0 1.5 1.5 2 2.5 2 1 0 1.5-.5 2.5-.5s1.5.5 2.5.5 2.5-.5 2.5-2c0-2-2-5.5-5-5.5z"/>',
  };
  const placeholder = (cat, label) =>
    `<div class="ph" data-cat="${esc(cat)}" role="img" aria-label="${esc(label)}">${svg(CAT_ICONS[cat] || '', 'stroke-width="1.3"')}</div>`;
  const imageHTML = (p) => p.image
    ? `<img src="${esc(p.image)}" alt="${esc(p.name)}" loading="lazy">`
    : placeholder(p.category, p.name);

  /* ---------- Catalogue ---------- */
  let catalogue = null;
  const byId = (id) => catalogue.products.find(p => p.id === id);
  const catName = (id) => (catalogue.categories.find(c => c.id === id) || {}).name || '';
  const onSale = (p) => p.compareAt && p.compareAt > p.price;

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
    if (!p || p.stock <= 0) return 0;
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
    const subtotal = lines().reduce((s, l) => s + l.p.price * l.qty, 0);
    const { standard, freeOver } = catalogue.shipping;
    const delivery = subtotal === 0 || subtotal >= freeOver ? 0 : standard;
    return { subtotal, delivery, total: subtotal + delivery, count: lines().reduce((s, l) => s + l.qty, 0) };
  };

  /* ---------- Header + footer ---------- */
  function renderChrome() {
    const header = document.getElementById('siteHeader');
    const free = catalogue ? money(catalogue.shipping.freeOver) : '£30';
    if (header) {
      const q = params.get('q') || '';
      header.innerHTML = `
        <div class="announce">Free UK delivery on orders over ${free} &middot; Dispatched in 1&ndash;2 working days &middot; 30-day returns</div>
        <div class="masthead">
          <div class="wrap masthead-row">
            <a href="index.html" class="brand" aria-label="${SHOP_NAME} home"><img src="assets/crow-mark.png" alt=""><span>${SHOP_NAME}</span></a>
            <form class="search" action="products.html" role="search">
              <label for="q" class="sr-only">Search products</label>
              <input id="q" name="q" type="search" placeholder="Search for products" value="${esc(q)}" autocomplete="off">
              <button type="submit" aria-label="Search">${I.search}</button>
            </form>
            <nav class="masthead-links" aria-label="Account">
              <a href="contact.html" class="help-link">Help</a>
              <a href="basket.html" class="basket-link" aria-label="Basket">
                <span class="basket-icon">${I.bag}<span class="basket-count is-empty" id="basketCount">0</span></span>
                <span class="basket-total" id="basketTotal">£0.00</span>
              </a>
            </nav>
          </div>
        </div>
        <nav class="catnav" aria-label="Categories"><div class="wrap" id="catnav"></div></nav>`;
    }
    const footer = document.getElementById('siteFooter');
    if (footer) {
      footer.innerHTML = `
        <footer class="footer">
          <div class="wrap">
            <div class="footer-top">
              <div>
                <a href="index.html" class="brand"><img src="assets/crow-mark.png" alt=""><span>${SHOP_NAME}</span></a>
                <p>Everyday essentials for home, family and pets, sent out from our base in Peterborough.</p>
              </div>
              <div><h3>Shop</h3><ul id="footerCats"><li><a href="products.html">All products</a></li></ul></div>
              <div><h3>Help</h3><ul>
                <li><a href="contact.html">Contact us</a></li>
                <li><a href="delivery-returns.html">Delivery &amp; returns</a></li>
                <li><a href="basket.html">Your basket</a></li>
              </ul></div>
              <div><h3>Legal</h3><ul>
                <li><a href="terms.html">Terms of sale</a></li>
                <li><a href="privacy.html">Privacy policy</a></li>
              </ul></div>
            </div>
            <div class="footer-bottom">
              <span>&copy; ${new Date().getFullYear()} Crowsons Global Ltd</span>
              <span>Company No. 16709080 &middot; Registered in England and Wales</span>
            </div>
          </div>
        </footer>`;
    }
  }

  function renderCatNav() {
    const nav = document.getElementById('catnav');
    const current = page === 'products' ? (params.get('offers') ? 'offers' : params.get('category') || (params.get('q') ? '' : 'all')) : '';
    if (nav) {
      nav.innerHTML = [
        `<a href="products.html" class="${current === 'all' ? 'is-active' : ''}">All products</a>`,
        ...catalogue.categories.map(c => `<a href="products.html?category=${encodeURIComponent(c.id)}" class="${current === c.id ? 'is-active' : ''}">${esc(c.name)}</a>`),
        `<a href="products.html?offers=1" class="is-offers ${current === 'offers' ? 'is-active' : ''}">Offers</a>`,
      ].join('');
    }
    const fc = document.getElementById('footerCats');
    if (fc) fc.innerHTML += catalogue.categories.map(c => `<li><a href="products.html?category=${encodeURIComponent(c.id)}">${esc(c.name)}</a></li>`).join('');
  }

  function updateHeaderBasket() {
    if (!catalogue) return;
    const t = totals();
    const c = document.getElementById('basketCount');
    const tot = document.getElementById('basketTotal');
    if (c) { c.textContent = t.count; c.classList.toggle('is-empty', t.count === 0); }
    if (tot) tot.textContent = money(t.subtotal);
  }

  /* ---------- Product card ---------- */
  const priceHTML = (p) => `<span class="price ${onSale(p) ? 'is-sale' : ''}">${money(p.price)}${onSale(p) ? `<s>${money(p.compareAt)}</s>` : ''}</span>`;
  const card = (p) => {
    const out = p.stock <= 0;
    return `
      <article class="card">
        <a href="${productUrl(p)}" class="card-media" tabindex="-1" aria-hidden="true">
          ${imageHTML(p)}
          ${out ? '<span class="badge badge--dark">Sold out</span>' : onSale(p) ? `<span class="badge">Save ${Math.round((1 - p.price / p.compareAt) * 100)}%</span>` : ''}
        </a>
        <div class="card-body">
          <span class="card-cat">${esc(catName(p.category))}</span>
          <h3 class="card-title"><a href="${productUrl(p)}">${esc(p.name)}</a></h3>
          ${priceHTML(p)}
          <span class="stock-note">${!out && p.stock <= 5 ? `Only ${p.stock} left` : ''}</span>
          <button type="button" class="btn btn-primary btn-block" data-add="${esc(p.id)}" ${out ? 'disabled' : ''}>${out ? 'Sold out' : 'Add to basket'}</button>
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
        <span>${I.check} ${added > 0 ? 'Added to your basket' : 'Already at the maximum in your basket'}</span>
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
  popup.addEventListener('click', (e) => {
    if (e.target.closest('.added-close')) popup.classList.remove('is-open');
  });

  /* ---------- Global click handling ---------- */
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
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') popup.classList.remove('is-open'); });

  /* ---------- Checkout ---------- */
  async function startCheckout(btn) {
    if (!lines().length) { location.href = 'basket.html'; return; }
    // Messages show on the basket page; from the popup we go there first if needed.
    let msg = document.getElementById('checkoutMsg');
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
    const href = `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent('Order from the Crowsons shop')}&body=${encodeURIComponent(body)}`;
    return `Card payments are being switched on. For now, <a href="${href}">email us your order</a> and we'll reply with a secure payment link.`;
  }

  /* ---------- Home page ---------- */
  function initHome() {
    const tiles = document.getElementById('heroTiles');
    if (tiles) tiles.innerHTML = catalogue.categories.map(c => `
      <a href="products.html?category=${encodeURIComponent(c.id)}" class="hero-tile ph" data-cat="${esc(c.id)}">
        ${svg(CAT_ICONS[c.id] || '', 'stroke-width="1.2"')}
        <strong>${esc(c.name)}</strong><span>Shop now &rarr;</span>
      </a>`).join('');

    const cats = document.getElementById('catGrid');
    if (cats) cats.innerHTML = catalogue.categories.map(c => {
      const n = catalogue.products.filter(p => p.category === c.id).length;
      return `
        <a href="products.html?category=${encodeURIComponent(c.id)}" class="cat-card">
          ${placeholder(c.id, c.name)}
          <div><h3>${esc(c.name)}</h3><p>${esc(c.blurb || `${n} products`)}</p></div>
        </a>`;
    }).join('');

    const featured = catalogue.products.filter(p => p.featured && p.stock > 0);
    const best = document.getElementById('bestSellers');
    if (best) best.innerHTML = (featured.length ? featured : catalogue.products).slice(0, 8).map(card).join('');

    const offers = catalogue.products.filter(p => onSale(p) && p.stock > 0);
    const offerGrid = document.getElementById('offersGrid');
    if (offerGrid) {
      if (offers.length) offerGrid.innerHTML = offers.slice(0, 4).map(card).join('');
      else document.getElementById('offersSection')?.remove();
    }
  }

  /* ---------- Listing page ---------- */
  function initListing() {
    const grid = document.getElementById('grid');
    const title = document.getElementById('listTitle');
    const sub = document.getElementById('listSub');
    const crumb = document.getElementById('listCrumb');
    const count = document.getElementById('resultCount');
    const sort = document.getElementById('sort');
    const inStock = document.getElementById('inStock');
    const offersOnly = document.getElementById('offersOnly');
    const catList = document.getElementById('catList');

    let category = params.get('category') || 'all';
    if (category !== 'all' && !catalogue.categories.some(c => c.id === category)) category = 'all';
    const q = (params.get('q') || '').trim();
    offersOnly.checked = params.get('offers') === '1';
    if (params.get('sort')) sort.value = params.get('sort');

    const heading = q ? `Results for “${q}”` : offersOnly.checked && category === 'all' ? 'Offers' : category === 'all' ? 'All products' : catName(category);
    title.textContent = heading;
    crumb.textContent = heading;
    document.title = `${heading} | ${SHOP_NAME}`;
    sub.textContent = category !== 'all' ? (catalogue.categories.find(c => c.id === category).blurb || '') : '';

    const link = (cat) => {
      const u = new URLSearchParams();
      if (cat !== 'all') u.set('category', cat);
      if (q) u.set('q', q);
      return `products.html${u.toString() ? '?' + u : ''}`;
    };
    const countIn = (cat) => catalogue.products.filter(p => cat === 'all' || p.category === cat).length;
    catList.innerHTML = [{ id: 'all', name: 'All products' }, ...catalogue.categories]
      .map(c => `<li><a href="${link(c.id)}" class="${c.id === category ? 'is-active' : ''}">${esc(c.name)} <span>${countIn(c.id)}</span></a></li>`).join('');

    const render = () => {
      const words = q.toLowerCase().split(/\s+/).filter(Boolean);
      let list = catalogue.products.filter(p => {
        if (category !== 'all' && p.category !== category) return false;
        if (inStock.checked && p.stock <= 0) return false;
        if (offersOnly.checked && !onSale(p)) return false;
        const hay = `${p.name} ${p.brand} ${p.description} ${catName(p.category)}`.toLowerCase();
        return words.every(w => hay.includes(w));
      });
      const s = sort.value;
      if (s === 'price-asc') list = [...list].sort((a, b) => a.price - b.price);
      if (s === 'price-desc') list = [...list].sort((a, b) => b.price - a.price);
      if (s === 'name') list = [...list].sort((a, b) => a.name.localeCompare(b.name));
      if (s === 'featured') list = [...list].sort((a, b) => (b.stock > 0) - (a.stock > 0) || (b.featured === true) - (a.featured === true));
      count.textContent = `${list.length} product${list.length === 1 ? '' : 's'}`;
      grid.innerHTML = list.length ? list.map(card).join('') : `
        <div class="empty">
          <p>No products match${q ? ` “${esc(q)}”` : ''}. Try a different search or clear the filters.</p>
          <a href="products.html" class="btn btn-outline">See all products</a>
        </div>`;
    };
    [sort, inStock, offersOnly].forEach(el => el.addEventListener('change', render));
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
      root.innerHTML = `<div class="empty" style="margin:40px 0"><p>Sorry, we couldn't find that product. It may have sold out or been removed.</p><a href="products.html" class="btn btn-primary">Browse all products</a></div>`;
      return;
    }
    document.title = `${p.name} | ${SHOP_NAME}`;
    const out = p.stock <= 0;
    const max = maxFor(p);
    const stockText = out ? 'Sold out' : p.stock <= 5 ? `Low stock: only ${p.stock} left` : 'In stock, ready to dispatch';
    root.innerHTML = `
      <nav class="crumbs pdp-crumbs" aria-label="Breadcrumb">
        <a href="index.html">Home</a><span>/</span>
        <a href="products.html?category=${encodeURIComponent(p.category)}">${esc(catName(p.category))}</a><span>/</span>
        <span>${esc(p.name)}</span>
      </nav>
      <div class="pdp">
        <div class="pdp-media">${imageHTML(p)}${onSale(p) && !out ? `<span class="badge">Save ${Math.round((1 - p.price / p.compareAt) * 100)}%</span>` : ''}</div>
        <div>
          ${p.brand ? `<span class="pdp-brand">${esc(p.brand)}</span>` : ''}
          <h1>${esc(p.name)}</h1>
          <div>${priceHTML(p)}${onSale(p) ? `<span class="pdp-save">You save ${money(p.compareAt - p.price)}</span>` : ''}</div>
          <p class="pdp-stock ${out ? 'is-out' : p.stock <= 5 ? 'is-low' : ''}">${stockText}</p>
          <div class="buy-box">
            <div class="buy-row">
              <div class="stepper" data-stepper>
                <button type="button" data-step="-1" aria-label="Decrease quantity" ${out ? 'disabled' : ''}>&minus;</button>
                <input type="number" id="pdpQty" value="1" min="1" max="${max}" aria-label="Quantity" ${out ? 'disabled' : ''}>
                <button type="button" data-step="1" aria-label="Increase quantity" ${out ? 'disabled' : ''}>+</button>
              </div>
              <button type="button" class="btn btn-primary btn-lg" data-add="${esc(p.id)}" data-use-qty ${out ? 'disabled' : ''}>${I.bag} ${out ? 'Sold out' : 'Add to basket'}</button>
            </div>
            ${out ? '' : `<button type="button" class="btn btn-outline btn-block" data-add="${esc(p.id)}" data-use-qty data-buy-now>Buy now</button>`}
          </div>
          <ul class="assure">
            <li>${I.truck}<span>${money(catalogue.shipping.standard)} UK delivery, <strong>free over ${money(catalogue.shipping.freeOver)}</strong>. Dispatched in 1&ndash;2 working days.</span></li>
            <li>${I.back}<span>30-day returns. <a href="delivery-returns.html">Delivery &amp; returns</a></span></li>
            <li>${I.lock}<span>Secure checkout powered by Stripe</span></li>
          </ul>
          <div class="pdp-details">
            <h2>Product details</h2>
            <p>${esc(p.description)}</p>
            ${p.bullets?.length ? `<ul>${p.bullets.map(b => `<li>${esc(b)}</li>`).join('')}</ul>` : ''}
          </div>
        </div>
      </div>`;

    const qty = document.getElementById('pdpQty');
    root.querySelector('[data-stepper]')?.addEventListener('click', (e) => {
      const step = e.target.closest('[data-step]');
      if (!step) return;
      qty.value = Math.min(max, Math.max(1, (Number(qty.value) || 1) + Number(step.dataset.step)));
    });
    qty?.addEventListener('change', () => { qty.value = Math.min(max, Math.max(1, Math.floor(Number(qty.value)) || 1)); });

    const related = catalogue.products.filter(r => r.category === p.category && r.id !== p.id).slice(0, 4);
    const relGrid = document.getElementById('related');
    if (related.length && relGrid) relGrid.innerHTML = related.map(card).join('');
    else document.getElementById('relatedSection')?.remove();
  }

  /* ---------- Basket page ---------- */
  function renderBasketPage() {
    const root = document.getElementById('basketRoot');
    if (!root) return;
    const ls = lines();
    if (!ls.length) {
      root.innerHTML = `
        <div class="empty" style="margin:32px 0 72px">
          <p style="font-size:17px;color:var(--ink)"><strong>Your basket is empty</strong></p>
          <p>Have a look around: there's free UK delivery on orders over ${money(catalogue.shipping.freeOver)}.</p>
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
                <a href="${productUrl(p)}" class="line-thumb">${imageHTML(p)}</a>
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
            ${t.delivery ? `You're ${money(freeOver - t.subtotal)} away from free UK delivery` : 'Your order qualifies for free UK delivery'}
            <div class="bar"><i style="width:${pct}%"></i></div>
          </div>
          <dl>
            <div><dt>Subtotal (${t.count} item${t.count === 1 ? '' : 's'})</dt><dd>${money(t.subtotal)}</dd></div>
            <div><dt>UK delivery</dt><dd>${t.delivery ? money(t.delivery) : 'Free'}</dd></div>
            <div class="is-total"><dt>Total</dt><dd>${money(t.total)}</dd></div>
          </dl>
          <button type="button" class="btn btn-primary btn-lg btn-block" data-checkout>${I.lock} Proceed to checkout</button>
          <p class="checkout-msg" id="checkoutMsg" role="status">${keepMsg}</p>
          <p class="secure">${I.shield} Secure payment by Stripe. We never see your card details.</p>
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
  renderChrome();
  document.body.appendChild(popup);

  if (page === 'complete') {
    try { localStorage.removeItem(BASKET_KEY); } catch { /* ignore */ }
    memoryBasket = {};
  }

  // Contact form: show a thank-you after Netlify Forms redirects back.
  if (page === 'contact' && params.get('sent') === '1') {
    document.getElementById('contactSent')?.removeAttribute('hidden');
  }

  fetch('data/products.json', { cache: 'no-cache' })
    .then(r => r.json())
    .then(data => {
      catalogue = data;
      renderChrome();
      renderCatNav();
      updateHeaderBasket();
      if (page === 'home') initHome();
      if (page === 'products') initListing();
      if (page === 'product') initProduct();
      if (page === 'basket') initBasket();
    })
    .catch(() => {
      const main = document.querySelector('main');
      if (main) main.insertAdjacentHTML('afterbegin', '<div class="wrap"><p class="empty" style="margin:32px 0">Sorry, the shop could not load. Please refresh the page.</p></div>');
    });
})();
