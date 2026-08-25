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

    return new Response(JSON.stringify(result, null, 2), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
};