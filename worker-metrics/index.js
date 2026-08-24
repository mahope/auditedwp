// DevNotify metrics — privacy-friendly download + visit counter.
// No cookies, no personal data. Counts only.
//
// Endpoints:
//   POST /event  {type:"download"|"visit", path}  -> increments counters
//   GET  /stats  -> {downloads, visits, byPath}
//   GET  /health

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", ...CORS },
  });
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return new Response(null, { headers: CORS });
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "");

    if (request.method === "GET" && (path === "" || path === "/health")) {
      return json({ service: "devnotify-metrics", ok: true });
    }

    if (request.method === "GET" && path === "/stats") {
      const [dl, visits, subs] = await Promise.all([
        env.METRICS.get("stats:downloads"),
        env.METRICS.get("stats:visits"),
        env.METRICS.get("stats:subscribers"),
      ]);
      return json({
        downloads: parseInt(dl || "0", 10),
        visits: parseInt(visits || "0", 10),
        subscribers: parseInt(subs || "0", 10),
      });
    }

    if (request.method === "POST" && path === "/event") {
      let body;
      try { body = await request.json(); } catch { return json({ error: "bad json" }, 400); }
      const type = body.type === "visit" ? "visit" : body.type === "download" ? "download" : null;
      if (!type) return json({ error: "type must be 'download' or 'visit'" }, 400);

      // naive per-IP dedupe: one count per IP+type per hour
      const ip = request.headers.get("CF-Connecting-IP") || "unknown";
      const hourKey = `dedupe:${type}:${ip}:${new Date().toISOString().slice(0, 13)}`;
      const seen = await env.METRICS.get(hourKey);
      if (seen) return json({ counted: false });

      await env.METRICS.put(hourKey, "1", { expirationTtl: 3700 });
      const key = "stats:" + (type === "download" ? "downloads" : "visits");
      const cur = parseInt((await env.METRICS.get(key)) || "0", 10);
      await env.METRICS.put(key, String(cur + 1));
      return json({ counted: true });
    }

    if (request.method === "GET" && path === "/config") {
      // Public runtime config. Set CHECKOUT_URL secret via:
      //   wrangler secret put CHECKOUT_URL --name devnotify-metrics
      // The buy section detects a non-empty checkoutUrl at runtime and
      // switches from waitlist to live Lemon Squeezy checkout — no deploy needed.
      return json({
        service: "devnotify-metrics",
        checkoutUrl: (env?.CHECKOUT_URL || "").trim(),
      });
    }

    if (request.method === "POST" && path === "/subscribe") {
      // Notify-me list for launch. Rejects test/example addresses so we
      // never count our own smoke tests as real signups (AGENTS.md rule).
      let body;
      try { body = await request.json(); } catch { return json({ error: "bad json" }, 400); }
      const email = String(body.email || "").trim().toLowerCase();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) return json({ error: "invalid email" }, 400);
      const [name, domain] = email.split("@");
      const badLocal = /^(test|testing|asdf|foo|bar|demo|example|smoke|fake|noreply|no-reply)/.test(name);
      const badDomain = /(^|\.)(example|test|invalid|localhost|example\.com|mailinator\.com|10minutemail\.com|guerrillamail\.com)$/.test(domain) || domain === "example.com";
      if (badLocal || badDomain) return json({ error: "test address rejected" }, 422);
      const ip = request.headers.get("CF-Connecting-IP") || "unknown";
      const hourKey = `subdedupe:${ip}:${new Date().toISOString().slice(0, 13)}`;
      if (await env.METRICS.get(hourKey)) return json({ counted: false });
      await env.METRICS.put(hourKey, "1", { expirationTtl: 3700 });
      const key = `subscriber:${email}`;
      const exists = await env.METRICS.get(key);
      if (!exists) {
        await env.METRICS.put(key, JSON.stringify({
          email,
          at: new Date().toISOString(),
          ua: request.headers.get("User-Agent") || "",
        }));
        const cur = parseInt((await env.METRICS.get("stats:subscribers")) || "0", 10);
        await env.METRICS.put("stats:subscribers", String(cur + 1));
      }
      return json({ counted: true, message: "You're on the list. We'll email you when checkout is live." });
    }

    if (request.method === "GET" && path === "/stats") {
      const [dl, visits, subs] = await Promise.all([
        env.METRICS.get("stats:downloads"),
        env.METRICS.get("stats:visits"),
        env.METRICS.get("stats:subscribers"),
      ]);
      return json({
        downloads: parseInt(dl || "0", 10),
        visits: parseInt(visits || "0", 10),
        subscribers: parseInt(subs || "0", 10),
      });
    }

    return json({ error: "not found" }, 404);
  },
};
