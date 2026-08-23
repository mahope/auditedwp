/**
 * EUComply Universal Scan — Cloudflare Worker (indpakning om shared engine)
 *
 * Importerer kernen fra shared/scan-engine.js. Tilføjer web-facing
 * endpoint med rate limiting, CORS, og usage stats.
 */

import { runScan, normalizeUrl, json, CORS } from '../shared/scan-engine.js';

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS });
    }

    const path = new URL(request.url).pathname.replace(/\/+$/, "");
    const ip = request.headers.get("cf-connecting-ip") || "unknown";

    // Simple usage stats (optional KV).
    if (env?.RATE && path === "") {
      // fire-and-forget counter
      env.RATE.put("stats:scans", String(parseInt((await env.RATE.get("stats:scans")) || "0", 10) + 1), { expirationTtl: undefined }).catch(() => {});
    }

    if (request.method === "GET" && (path === "" || path === "/health")) {
      return json({ service: "eucomply-universal-scan", version: "1.0.0", usage: "GET /scan?url=example.com" });
    }

    if (path !== "" && path !== "/scan") {
      return json({ error: "Not found. Use GET /scan?url=example.com" }, 404);
    }

    let raw = new URL(request.url).searchParams.get("url");
    if (!raw && request.method === "POST") {
      try { raw = (await request.json())?.url; } catch { /* ignore */ }
    }

    const url = normalizeUrl(raw);
    if (!url) {
      return json({ error: "Please provide a valid public http(s) URL, e.g. ?url=example.com" }, 400);
    }

    // Inline rate-limit:
    try {
      if (env?.RATE) {
        const now = Date.now();
        const key = `ratelimit:${ip}`;
        const raw = await env.RATE.get(key);
        const win = raw ? JSON.parse(raw) : { start: now, n: 0 };
        if (now - win.start > 60_000) { win.start = now; win.n = 0; }
        win.n++;
        if (win.n > 10) return json({ error: "Rate limit reached. Try again in a few minutes." }, 429);
        await env.RATE.put(key, JSON.stringify(win), { expirationTtl: 120 });
      }
    } catch { /* fail open if KV unavailable */ }

    try {
      return json(await runScan(url));
    } catch (e) {
      return json({ error: "Scan failed: " + String(e && e.message || e) }, 502);
    }
  },
};