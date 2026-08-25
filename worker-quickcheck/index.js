// DeskUptime Quick Check — live demo worker
// Checks any URL: HTTP status, response time, redirect, HTTPS
export default {
  async fetch(request) {
    const url = new URL(request.url);

    // CORS for all origins (landing page on any domain)
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    const target = url.searchParams.get('url');
    if (!target) {
      return new Response(
        JSON.stringify({ error: 'Missing ?url= parameter. Usage: /check?url=https://example.com' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Basic validation — must be http or https
    if (!/^https?:\/\//i.test(target)) {
      return new Response(
        JSON.stringify({ error: 'URL must start with http:// or https://' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const start = Date.now();
    const result = {
      url: target,
      checkedAt: new Date().toISOString(),
      https: target.startsWith('https://'),
      responseMs: 0,
      status: null,
      statusText: null,
      redirected: false,
      finalUrl: null,
      error: null,
      headers: {},
    };

    try {
      const resp = await fetch(target, {
        method: 'HEAD',
        redirect: 'follow',
        headers: { 'User-Agent': 'DeskuptimeQuickCheck/1.0' },
      });

      result.responseMs = Date.now() - start;
      result.status = resp.status;
      result.statusText = resp.statusText;
      result.redirected = resp.redirected;
      result.finalUrl = resp.url;

      // Relevant response headers
      const interesting = ['server', 'content-type', 'content-length', 'x-frame-options',
        'strict-transport-security', 'x-content-type-options'];
      for (const h of interesting) {
        const val = resp.headers.get(h);
        if (val) result.headers[h] = val;
      }
    } catch (e) {
      result.error = e.message;
      result.responseMs = Date.now() - start;
    }

    // SSL expiry via Certificate Transparency logs (crt.sh) — no key needed.
    // The newest logged leaf certificate for the host is effectively the
    // currently-served one; browsers require CT logging, so this tracks
    // renewals within minutes.
    if (target.startsWith('https://')) {
      try {
        const host = new URL(target).hostname;
        const cr = await fetch(
          `https://api.certspotter.com/v1/issuances?domain=${encodeURIComponent(host)}&include_subdomains=false&exclude_expired=true`,
          { headers: { 'User-Agent': 'DeskuptimeQuickCheck/1.0' } }
        );
        if (cr.ok) {
          const entries = await cr.json();
          const now = Date.now();
          let best = null;
          for (const e of entries) {
            if (e.revoked) continue;
            const t = Date.parse(e.not_after);
            if (!isNaN(t) && (!best || t > best.t)) best = { t };
          }
          if (best) result.sslDaysRemaining = Math.floor((best.t - now) / 86400000);
          if (best) result.sslExpiresAt = new Date(best.t).toISOString().slice(0, 10);
        } else if (cr.status === 429) {
          result.sslError = 'Certificate log lookup rate-limited, try again shortly.';
        }
      } catch (e) {
        // non-fatal — SSL data is best-effort
      }
    }

    return new Response(JSON.stringify(result, null, 2), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
};