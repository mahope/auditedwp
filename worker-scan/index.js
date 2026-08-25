/**
 * EUComply Universal Scan — Cloudflare Worker (indpakning om shared engine)
 *
 * Importerer kernen fra shared/scan-engine.js. Tilføjer web-facing
 * endpoint med rate limiting, CORS, og usage stats.
 */

import { runScan, normalizeUrl, json, CORS } from '../shared/scan-engine.js';

const SIMPLE_EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS });
    }

    const reqUrl = new URL(request.url);
    const path = reqUrl.pathname.replace(/\/+$/, "") || "/";

    // POST /subscribe — email capture from scan results
    if (request.method === "POST" && path === "/subscribe") {
      try {
        const body = await request.json();
        const email = (body.email || "").trim().toLowerCase();
        if (!SIMPLE_EMAIL_RE.test(email)) {
          return json({ error: "Valid email required." }, 400);
        }
        // Reject test/disposable addresses so our own smoke tests never pollute real numbers
        const domain = email.split("@")[1];
        const badDomain = /(^|\.)(example|test|invalid|localhost|mailinator|10minutemail|guerrillamail)\.(com|org|net|info)$/.test(domain) || domain === "example.com";
        if (badDomain) {
          return json({ error: "Test address rejected." }, 422);
        }
        // Store subscriber
        const sub = {
          email,
          url: body.url || "",
          score: body.score ?? null,
          source: body.source || "scan-page",
          timestamp: new Date().toISOString(),
        };
        // Simple hash for KV key
        const key = `sub:${Array.from(new TextEncoder().encode(email)).map(b => b.toString(16)).join("")}`;
        await env.SUBSCRIBERS.put(key, JSON.stringify(sub));
        return json({ ok: true, message: "You're subscribed — we'll send compliance tips and updates." });
      } catch (e) {
        return json({ error: "Invalid request: " + (e.message || e) }, 400);
      }
    }

    // GET /config — public runtime config (checkout URL sættes via secret/vars,
    // så en ny Lemon Squeezy-checkout kan aktiveres uden ny deploy).
    // CHECKOUT_URLS er en kommasepareret liste på formen  key:url,key:url
    // (fx "ebook:https://xxx.lemonsqueezy.com/buy/abc,pro:...").
    if (request.method === "GET" && path === "/config") {
      const urls = {};
      for (const pair of (env?.CHECKOUT_URLS || "").split(",")) {
        const idx = pair.indexOf(":");
        if (idx > 0) {
          const key = pair.slice(0, idx).trim();
          const val = pair.slice(idx + 1).trim();
          if (/^https:\/\//.test(val)) urls[key] = val;
        }
      }
      return json({
        checkoutUrl: (env?.CHECKOUT_URL || "").trim(),
        checkout_urls: urls,
        launchPricing: true,
      });
    }

    // GET /stats — public scan counter (transparency / social proof)
    // Domains used in our own smoke tests and homepage example buttons are
    // EXCLUDED so the public number reflects real external usage only.
    if (request.method === "GET" && path === "/stats") {
      const TEST_HOSTS = new Set([
        "example.com", "www.example.com",
        "wordpress.org", "shopify.com", "www.shopify.com", "webflow.com", "www.webflow.com",
        "www.apple.com", "wordpress.com", "www.squarespace.com", "vercel.com",
        "stripe.com", "www.stripe.com", "www.allbirds.com",
        // typo variants seen from automated tests
        "www.shopify.com.com", "www.webflow.com.com", "www.stripe.com.com",
      ]);
      let scans = null;
      let domains = [];
      try {
        const raw = await env?.RATE?.get("stats:domains");
        const map = raw ? JSON.parse(raw) : {};
        const entries = Object.entries(map).filter(([h]) => !TEST_HOSTS.has(h));
        scans = entries.reduce((sum, [, n]) => sum + n, 0);
        domains = entries
          .map(([host, n]) => ({ host, scans: n }))
          .sort((a, b) => b.scans - a.scans)
          .slice(0, 20);
      } catch { /* ignore */ }
      return json({ scans: Number.isFinite(scans) ? scans : null, domains });
    }

    const ip = request.headers.get("cf-connecting-ip") || "unknown";

    // Simple usage stats
    if (request.method === "GET" && path === "") {
      if (env?.RATE) {
        env.RATE.put("stats:scans", String(parseInt((await env.RATE.get("stats:scans")) || "0", 10) + 1), { expirationTtl: undefined }).catch(() => {});
      }
      return json({ service: "eucomply-universal-scan", version: "1.0.0", usage: "GET /scan?url=example.com | POST /subscribe" });
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

    // Count real scans (not root pings) + per-domain tally so our own
    // smoke tests are visible and separable from real external traffic
    if (env?.RATE) {
      env.RATE.put("stats:scans", String(parseInt((await env.RATE.get("stats:scans")) || "0", 10) + 1)).catch(() => {});
      try {
        const host = new URL(url).host;
        const map = JSON.parse((await env.RATE.get("stats:domains")) || "{}");
        map[host] = (map[host] || 0) + 1;
        await env.RATE.put("stats:domains", JSON.stringify(map));
      } catch { /* non-fatal */ }
    }

    try {
      return json(await runScan(url));
    } catch (e) {
      return json({ error: "Scan failed: " + String(e && e.message || e) }, 502);
    }
  },
};