// Creates a Stripe Checkout session for the shop basket.
//
// Setup (one-off, free): in Netlify → Site configuration → Environment
// variables, add STRIPE_SECRET_KEY (sk_test_... while testing, sk_live_...
// when you go live). Until it is set, the shop falls back to "order by email".
//
// Prices are always read from data/products.json here on the server, never
// from the browser, so nobody can edit the price in their basket.

const catalogue = require('../../data/products.json');

const json = (statusCode, body) => ({
  statusCode,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
});

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') return json(405, { error: 'Method not allowed' });

  const key = process.env.STRIPE_SECRET_KEY;
  if (!key) return json(503, { error: 'not_configured' });

  let items;
  try {
    items = JSON.parse(event.body || '{}').items;
  } catch {
    return json(400, { error: 'Invalid request' });
  }
  if (!Array.isArray(items) || items.length === 0) return json(400, { error: 'Basket is empty' });

  const byId = new Map(catalogue.products.map(p => [p.id, p]));
  const params = new URLSearchParams();
  let subtotal = 0;
  let line = 0;

  for (const item of items.slice(0, 50)) {
    const product = byId.get(String(item.id));
    const qty = Math.floor(Number(item.qty));
    if (!product || !(qty >= 1 && qty <= 20)) return json(400, { error: 'Invalid basket item' });
    if (product.stock <= 0) return json(409, { error: `${product.name} is out of stock` });
    if (qty > product.stock) return json(409, { error: `Only ${product.stock} of ${product.name} left` });

    subtotal += product.price * qty;
    params.append(`line_items[${line}][quantity]`, String(qty));
    params.append(`line_items[${line}][price_data][currency]`, catalogue.currency.toLowerCase());
    params.append(`line_items[${line}][price_data][unit_amount]`, String(product.price));
    params.append(`line_items[${line}][price_data][product_data][name]`, product.name);
    params.append(`line_items[${line}][price_data][product_data][metadata][sku]`, product.id);
    line += 1;
  }

  const { standard, freeOver } = catalogue.shipping;
  const shippingCost = subtotal >= freeOver ? 0 : standard;
  params.append('shipping_options[0][shipping_rate_data][type]', 'fixed_amount');
  params.append('shipping_options[0][shipping_rate_data][display_name]', shippingCost ? 'UK Standard Delivery' : 'Free UK Delivery');
  params.append('shipping_options[0][shipping_rate_data][fixed_amount][amount]', String(shippingCost));
  params.append('shipping_options[0][shipping_rate_data][fixed_amount][currency]', catalogue.currency.toLowerCase());
  params.append('shipping_address_collection[allowed_countries][0]', 'GB');
  params.append('phone_number_collection[enabled]', 'true');
  params.append('mode', 'payment');

  const origin = process.env.URL || `https://${event.headers.host}`;
  params.append('success_url', `${origin}/order-complete.html?paid=1&session_id={CHECKOUT_SESSION_ID}`);
  params.append('cancel_url', `${origin}/shop.html?basket=open`);

  const res = await fetch('https://api.stripe.com/v1/checkout/sessions', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${key}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: params.toString(),
  });
  const data = await res.json();
  if (!res.ok) {
    console.error('Stripe error', data.error);
    return json(502, { error: 'Payment provider error, please try again' });
  }
  return json(200, { url: data.url });
};
