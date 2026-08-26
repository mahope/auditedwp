// DeskUptime Security Headers Checker — fetches a URL and reports security-relevant response headers.
// Same engine approach as quickcheck/redirect-trace: plain HTTP, no CMS assumptions.

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

const CHECKED = [
  'strict-transport-security',
  'content-security-policy',
  'x-content-type-options',
  'x-frame-options',
  'referrer-policy',
  'permissions-policy',
  'cross-origin-opener-policy',
  'x-xss-protection',
];

export default {
  async fetch(request) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS });
    }
    const url = new URL(request.url);
    const target = url.searchParams.get('url');

    if (!target) return new Response(
      JSON.stringify({ error: 'Missing ?url= parameter. Usage: /headers?url=https://example.com' }),
      { status: 400, headers: { ...CORS, 'Content-Type': 'application/json' } });
    if (!/^https?:\/\//i.test(target)) return new Response(
      JSON.stringify({ error: 'URL must start with http:// or https://' }),
      { status: 400, headers: { ...CORS, 'Content-Type': 'application/json' } });

    try {
      const started = Date.now();
      const resp = await fetch(target, {
        redirect: 'follow',
        headers: { 'User-Agent': 'Mozilla/5.0 (compatible; DeskuptimeHeaders/1.0)' },
      });
      const headers = {};
      for (const name of CHECKED) {
        const v = resp.headers.get(name);
        if (v !== null) headers[name] = v;
      }
      const present = Object.keys(headers).filter(h => h !== 'x-xss-protection');
      return new Response(JSON.stringify({
        url: resp.url || target,
        checkedAt: new Date().toISOString(),
        responseMs: Date.now() - started,
        finalStatus: resp.status,
        https: (resp.url || target).startsWith('https://'),
        headers,
        score: present.length,
        maxScore: 7,
        grade: present.length >= 6 ? 'A' : present.length >= 4 ? 'B'
             : present.length >= 2 ? 'C' : present.length >= 1 ? 'D' : 'F',
      }, null, 2), { headers: { ...CORS, 'Content-Type': 'application/json' } });
    } catch (e) {
      return new Response(JSON.stringify({ url: target, error: e.message }, null, 2),
        { status: 502, headers: { ...CORS, 'Content-Type': 'application/json' } });
    }
  },
};
