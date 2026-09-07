/**
 * EUComply Checkout Widget — dynamic checkout links from worker config.
 * 
 * Reads the Lemon Squeezy checkout URL from the scan worker's /config endpoint.
 * When CHECKOUT_URL is set (env var), buy buttons redirect to the real checkout.
 * When empty, they show a "coming soon" state.
 * 
 * Usage: add data-checkout-* attributes to buttons:
 *   data-checkout="pro" — links to the Pro checkout
 *   data-checkout="store/dpa" — links to a specific product
 * 
 * The fallback (no checkout URL) shows a waitlist or preorder message.
 */

(function() {
  'use strict';

  const CONFIG_URL = 'https://eucomply-scan.mahope-eeb.workers.dev/config';
  const CHECKOUT_URLS = {
    'pro':           null,  // populated from config
    'store/dpa':     null,
    'store/nis2':    null,
    'store/nda':     null,
    'store/eaa':     null,
    'store/report':  null,
    'store/bundle':  null,
  };

  let configLoaded = false;

  function loadConfig() {
    if (configLoaded) return Promise.resolve();
    return fetch(CONFIG_URL)
      .then(r => r.json())
      .then(config => {
        configLoaded = true;
        const base = (config.checkoutUrl || '').trim();
        if (base) {
          // Map product keys to actual checkout URLs
          // Base is expected to be the Pro checkout URL
          CHECKOUT_URLS['pro'] = base;
          // For individual products, append /variants/xxx
          // (These will be set when products are created in LS)
          CHECKOUT_URLS['store/dpa'] = base.replace(/\/checkouts\/[^/]+/, '/checkouts/dpa');
          CHECKOUT_URLS['store/nis2'] = base.replace(/\/checkouts\/[^/]+/, '/checkouts/nis2-clauses');
          CHECKOUT_URLS['store/nda'] = base.replace(/\/checkouts\/[^/]+/, '/checkouts/nda');
          CHECKOUT_URLS['store/eaa'] = base.replace(/\/checkouts\/[^/]+/, '/checkouts/eaa-statement');
          CHECKOUT_URLS['store/report'] = base.replace(/\/checkouts\/[^/]+/, '/checkouts/report-kit');
          CHECKOUT_URLS['store/bundle'] = base.replace(/\/checkouts\/[^/]+/, '/checkouts/compliance-bundle');
        }
        updateButtons();
      })
      .catch(() => {
        // Config unavailable — keep buttons as-is (waitlist preorder)
        configLoaded = true;
        updateButtons();
      });
  }

  function updateButtons() {
    const buttons = document.querySelectorAll('[data-checkout]');
    buttons.forEach(btn => {
      const key = btn.getAttribute('data-checkout');
      const url = CHECKOUT_URLS[key];
      if (url) {
        btn.href = url;
        btn.target = '_blank';
        btn.rel = 'noopener noreferrer';
        btn.classList.remove('checkout-waiting');
        btn.classList.add('checkout-ready');
        // Restore original text if it was changed
        const original = btn.getAttribute('data-checkout-label');
        if (original) btn.textContent = original;
      } else {
        // No checkout URL yet — keep as preorder/waitlist
        btn.classList.add('checkout-waiting');
        btn.classList.remove('checkout-ready');
        if (!btn.getAttribute('data-checkout-original-href')) {
          btn.setAttribute('data-checkout-original-href', btn.href);
        }
      }
    });
  }

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadConfig);
  } else {
    loadConfig();
  }

  // Expose for debugging
  window.__checkout = { CHECKOUT_URLS, loadConfig };
})();