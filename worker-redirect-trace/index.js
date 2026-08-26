// DeskUptime Redirect Chain Tracer — traces every hop from URL to final destination.
// Uses the same engine approach as quickcheck: plain HTTP, no CMS assumptions.

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export default {
  async fetch(request) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS });
    }
    const url = new URL(request.url);
    const target = url.searchParams.get('url');

    if (!target) return new Response(
      JSON.stringify({ error: 'Missing ?url= parameter. Usage: /trace?url=https://example.com' }),
      { status: 400, headers: { ...CORS, 'Content-Type': 'application/json' } });
    if (!/^https?:\/\//i.test(target)) return new Response(
      JSON.stringify({ error: 'URL must start with http:// or https://' }),
      { status: 400, headers: { ...CORS, 'Content-Type': 'application/json' } });

    const hops = [];
    let current = target;
    const started = Date.now();

    try {
      for (let i = 0; i < 10; i++) {
        const hopStart = Date.now();
        // Manual redirect following so each hop is visible
        const resp = await fetch(current, {
          redirect: 'manual',
          headers: { 'User-Agent': 'Mozilla/5.0 (compatible; DeskuptimeTrace/1.0)' },
        });
        const hop = {
          step: i + 1,
          url: current,
          status: resp.status,
          statusText: resp.statusText,
          responseMs: Date.now() - hopStart,
          https: current.startsWith('https://'),
        };
        const loc = resp.headers.get('location');
        if (loc && resp.status >= 300 && resp.status < 400) {
          try { hop.redirectTo = new URL(loc, current).href; } catch { hop.redirectTo = loc; }
        }
        hops.push(hop);

        if (!hop.redirectTo) break;
        current = hop.redirectTo;
      }
      if (hops.length === 10 && hops[hops.length - 1].redirectTo) {
        hops.push({ step: 11, note: 'Redirect limit reached (10 hops) — possible loop.' });
      }
    } catch (e) {
      hops.push({ url: current, error: e.message });
    }

    const last = [...hops].reverse().find(h => h.status);
    return new Response(JSON.stringify({
      url: target,
      tracedAt: new Date().toISOString(),
      totalMs: Date.now() - started,
      hopCount: hops.filter(h => h.step).length,
      finalUrl: last ? last.url : null,
      finalStatus: last ? last.status : null,
      allHttps: hops.every(h => h.https || h.error),
      hops,
    }, null, 2), { headers: { ...CORS, 'Content-Type': 'application/json' } });
  },
};
