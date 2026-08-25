// EUComply Watch — daily compliance monitoring (Pro feature).
// Universal: works on any URL, any CMS. No platform dependencies.
//
// Imports the shared scan engine so daily scans use the same logic.
//
// API:
//   POST /register  { url, email }        -> register a site for daily scans
//   GET  /status?url=example.com     -> latest result + 30-day history
//   POST /unregister { url, email }     -> remove a site (email must match)
//   GET  /health
// Cron: daily 06:00 UTC — re-scans every registered site, stores history,
//       emails alerts on score drops (via Resend if ALERT_KEY is set).

import { runScan, normalizeUrl, json, CORS } from '../shared/scan-engine.js';

const todayKey = () => new Date().toISOString().slice(0, 10);
const MAX_HISTORY_DAYS = 30;
const MAX_SITES = 200;
const validEmail = (e) => typeof e === "string" && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e);

async function sendAlert(env, to, subject, text) {
  if (!env.ALERT_KEY) return false;
  try {
    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: `Bearer ${env.ALERT_KEY}`, "Content-Type": "application/json" },
      body: JSON.stringify({ from: env.ALERT_FROM || "EUComply <alerts@eucomply.app>", to, subject, text }),
    });
    return r.ok;
  } catch { return false; }
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return new Response(null, { headers: CORS });
    const path = new URL(request.url).pathname.replace(/\/+$/, "");

    if (request.method === "GET" && (path === "" || path === "/health")) {
      const count = parseInt((await env.WATCH.get("meta:sitecount")) || "0", 10);
      return json({ service: "eucomply-watch", version: "1.0.0", sites: count, endpoints: ["POST /register {url,email}", "GET /status?url=...", "POST /unregister {url,email}"] });
    }

    if (request.method === "POST" && path === "/register") {
      let body;
      try { body = await request.json(); } catch { return json({ error: "Invalid JSON body" }, 400); }
      const url = normalizeUrl(body.url);
      const email = (body.email || "").trim().toLowerCase();
      if (!url) return json({ error: "Provide a valid public URL." }, 400);
      if (!validEmail(email)) return json({ error: "Provide a valid email address." }, 400);
      const count = parseInt((await env.WATCH.get("meta:sitecount")) || "0", 10);
      if (count >= MAX_SITES) return json({ error: "Monitor is at capacity. Contact support." }, 503);

      const key = `site:${url}`;
      const existing = JSON.parse((await env.WATCH.get(key)) || "null");
      const rec = existing || { url, created: new Date().toISOString(), history: [], lastScore: null };
      rec.email = email;
      rec.updated = new Date().toISOString();
      await env.WATCH.put(key, JSON.stringify(rec));
      if (!existing) await env.WATCH.put("meta:sitecount", String(count + 1));

      // Run the first scan immediately via the shared engine.
      try {
        const scan = await runScan(url);
        rec.lastScore = scan.score.pct;
        rec.lastScan = scan.scannedAt;
        // Same-day dedupe: replace any existing entry for today (cron may also
        // have run) so the first scan never creates two history entries.
        const entry = { date: todayKey(), score: scan.score.pct, passed: scan.score.passed, total: scan.score.total };
        rec.history = [...rec.history.filter(h => h.date !== entry.date), entry].slice(-MAX_HISTORY_DAYS);
        await env.WATCH.put(key, JSON.stringify(rec));
        return json({ ok: true, message: `Site registered. First scan complete — score ${scan.score.pct}%.`, score: scan.score, history: rec.history });
      } catch (e) {
        return json({ ok: true, message: "Site registered. First scheduled scan will run within 24h.", error: String(e.message || e) });
      }
    }

    if (request.method === "GET" && path === "/status") {
      const url = normalizeUrl(new URL(request.url).searchParams.get("url"));
      if (!url) return json({ error: "Provide ?url=example.com" }, 400);
      const raw = await env.WATCH.get(`site:${url}`);
      if (!raw) return json({ error: "Site not registered yet. Use POST /register {url, email} to start monitoring." }, 404);
      const rec = JSON.parse(raw);
      return json({
        url: rec.url,
        registeredSince: rec.created,
        lastScan: rec.lastScan,
        currentScore: rec.lastScore,
        history: rec.history,
        days: rec.history.length,
        disclaimer: "Automated technical checks only — not legal advice.",
      });
    }

    if (request.method === "POST" && path === "/unregister") {
      // Self-serve opt-out: email must match so only the owner can remove a site.
      let body;
      try { body = await request.json(); } catch { return json({ error: "Invalid JSON body" }, 400); }
      const url = normalizeUrl(body.url);
      const email = (body.email || "").trim().toLowerCase();
      if (!url) return json({ error: "Provide a valid public URL." }, 400);
      const raw = await env.WATCH.get(`site:${url}`);
      if (!raw) return json({ error: "That site is not registered for monitoring." }, 404);
      const rec = JSON.parse(raw);
      if (!validEmail(email) || rec.email !== email) {
        return json({ error: "Email does not match the address this site was registered with." }, 403);
      }
      await env.WATCH.delete(`site:${url}`);
      const count = parseInt((await env.WATCH.get("meta:sitecount")) || "0", 10);
      if (count > 0) await env.WATCH.put("meta:sitecount", String(count - 1));
      return json({ ok: true, message: `${url} has been removed from daily monitoring.` });
    }

    return json({ error: "Not found" }, 404);
  },

  async scheduled(event, env, ctx) {
    // Enumerate registered sites via KV list.
    let cursor, sites = [];
    do {
      const page = await env.WATCH.list({ prefix: "site:", cursor });
      sites.push(...page.keys.map(k => k.name));
      cursor = page.list_complete ? undefined : page.cursor;
    } while (cursor);

    for (const key of sites) {
      ctx.waitUntil((async () => {
        const rec = JSON.parse((await env.WATCH.get(key)) || "null");
        if (!rec) return;
        let scan;
        try { scan = await runScan(rec.url); } catch { return; }
        const prev = rec.lastScore;
        const entry = { date: todayKey(), score: scan.score.pct, passed: scan.score.passed, total: scan.score.total };
        rec.history = [...rec.history.filter(h => h.date !== entry.date), entry].slice(-MAX_HISTORY_DAYS);
        rec.lastScore = scan.score.pct;
        rec.lastScan = scan.scannedAt;
        await env.WATCH.put(key, JSON.stringify(rec));
        if (prev !== null && scan.score.pct < prev) {
          await sendAlert(env, rec.email,
            `EUComply alert: your compliance score dropped (${prev}% → ${scan.score.pct}%)`,
            `Your site ${rec.url} scored ${scan.score.pct}% in today's compliance check (previous: ${prev}%).\n\nView history: https://auditedwp.pages.dev/pro/\n\nAutomated technical checks only — not legal advice.`);
        }
      })());
    }
  },
};