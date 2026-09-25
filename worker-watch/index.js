// EUComply Watch — open daily monitoring beta (not a current Pro entitlement).
// Universal: works on any URL, any CMS. No platform dependencies.
//
// Imports the shared scan engine so daily scans use the same logic.
//
// Every registered site gets an unguessable owner token. Reading results and
// removing a site both require that token, so one visitor can no longer see or
// overwrite another visitor's registration (which would silently redirect their
// alert mail).
//
// API:
//   POST /register  { url, email }              -> { ok, ownerToken, ... }
//   POST /status    { url, ownerToken }         -> latest result + 30-day history
//   POST /unregister{ url, ownerToken|email }   -> remove a site
//   GET  /health
// Cron: daily 06:00 UTC — re-scans every registered beta site, stores history,
//       emails score-drop alerts (via Resend if ALERT_KEY is set).

import { runScan, normalizeUrl, json, CORS } from '../shared/scan-engine.js';

const todayKey = () => new Date().toISOString().slice(0, 10);
const MAX_HISTORY_DAYS = 30;
const MAX_SITES = 200;
const RATE_WINDOW_MS = 60_000;
const RATE_MAX = 5;
const TOKEN_BYTES = 24;
const validEmail = (e) => typeof e === "string" && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e);
const validToken = (t) => typeof t === "string" && /^[a-f0-9]{32,64}$/.test(t);

function newToken() {
  const b = new Uint8Array(TOKEN_BYTES);
  crypto.getRandomValues(b);
  return Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("");
}

/** Constant-time-ish comparison so a token cannot be probed byte by byte. */
function tokenMatches(a, b) {
  if (!validToken(a) || !validToken(b) || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

async function rateLimited(env, ip) {
  if (!env.RATE || !ip || ip === "unknown") return false;
  try {
    const key = `watchrl:${ip}`;
    const now = Date.now();
    const raw = await env.RATE.get(key);
    const win = raw ? JSON.parse(raw) : { start: now, n: 0 };
    if (now - win.start > RATE_WINDOW_MS) { win.start = now; win.n = 0; }
    win.n++;
    if (win.n > RATE_MAX) return true;
    await env.RATE.put(key, JSON.stringify(win), { expirationTtl: 120 });
  } catch { /* fail open if KV unavailable */ }
  return false;
}

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
    const ip = request.headers.get("cf-connecting-ip") || "unknown";

    if (request.method === "GET" && (path === "" || path === "/health")) {
      const count = parseInt((await env.WATCH.get("meta:sitecount")) || "0", 10);
      return json({ service: "eucomply-watch", version: "1.1.0", sites: count, endpoints: ["POST /register {url,email}", "POST /status {url,ownerToken}", "POST /unregister {url,ownerToken}"] });
    }

    if (await rateLimited(env, ip)) {
      return json({ error: "Too many requests. Try again in a minute." }, 429);
    }

    if (request.method === "POST" && path === "/register") {
      let body;
      try { body = await request.json(); } catch { return json({ error: "Invalid JSON body" }, 400); }
      const url = normalizeUrl(body.url);
      const email = (body.email || "").trim().toLowerCase();
      if (!url) return json({ error: "Provide a valid public URL." }, 400);
      if (!validEmail(email)) return json({ error: "Provide a valid email address." }, 400);

      const key = `site:${url}`;
      const existing = JSON.parse((await env.WATCH.get(key)) || "null");
      if (existing) {
        // Re-registering must not be able to take over, re-target or delete
        // somebody else's record. Only the holder of the owner token (or the
        // same address already on file) may change the alert address.
        const supplied = String(body.ownerToken || "").trim().toLowerCase();
        const owns = tokenMatches(supplied, existing.ownerToken);
        if (!owns && existing.email !== email) {
          return json({ error: "This site is already monitored. Use the owner token or the address it was registered with to change it." }, 409);
        }
        if (!owns && existing.email === email) {
          return json({ error: "This site is already monitored.", ownerTokenRequired: true }, 409);
        }
      }

      const count = parseInt((await env.WATCH.get("meta:sitecount")) || "0", 10);
      if (!existing && count >= MAX_SITES) return json({ error: "Monitor is at capacity. Contact support." }, 503);

      const ownerToken = existing ? existing.ownerToken : newToken();
      const rec = existing || { url, created: new Date().toISOString(), history: [], lastScore: null };
      rec.ownerToken = ownerToken;
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
        return json({ ok: true, ownerToken, message: `Site registered. First scan complete — score ${scan.score.pct}%.`, score: scan.score, history: rec.history });
      } catch (e) {
        return json({ ok: true, ownerToken, message: "Site registered. First scheduled scan will run within 24h.", error: String(e.message || e) });
      }
    }

    // POST /status — was public GET /status?url=... ; it now requires the owner
    // token so no one can read another site's history or guess who owns it.
    if (request.method === "POST" && path === "/status") {
      let body;
      try { body = await request.json(); } catch { return json({ error: "Invalid JSON body" }, 400); }
      const url = normalizeUrl(body.url);
      const token = String(body.ownerToken || "").trim().toLowerCase();
      if (!url) return json({ error: "Provide the URL you registered." }, 400);
      const raw = await env.WATCH.get(`site:${url}`);
      if (!raw) return json({ error: "Site not registered yet. Use POST /register {url, email} to start monitoring." }, 404);
      const rec = JSON.parse(raw);
      // Legacy beta records predate the owner token; the registering address is
      // the only credential they have, so accept that once and upgrade the record.
      if (!rec.ownerToken) {
        if (!validEmail(body.email) || rec.email !== String(body.email).trim().toLowerCase()) {
          return json({ error: "This record predates owner tokens. Send the email address it was registered with to claim it." }, 403);
        }
        rec.ownerToken = newToken();
        rec.updated = new Date().toISOString();
        await env.WATCH.put(`site:${url}`, JSON.stringify(rec));
      } else if (!tokenMatches(token, rec.ownerToken)) {
        return json({ error: "Wrong owner token for this site." }, 403);
      }
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
      // Self-serve opt-out: the owner token is the credential. The registering
      // address still works, so nobody is locked out of deleting their own data.
      let body;
      try { body = await request.json(); } catch { return json({ error: "Invalid JSON body" }, 400); }
      const url = normalizeUrl(body.url);
      const token = String(body.ownerToken || "").trim().toLowerCase();
      const email = (body.email || "").trim().toLowerCase();
      if (!url) return json({ error: "Provide a valid public URL." }, 400);
      const raw = await env.WATCH.get(`site:${url}`);
      if (!raw) return json({ error: "That site is not registered for monitoring." }, 404);
      const rec = JSON.parse(raw);
      const byToken = rec.ownerToken && tokenMatches(token, rec.ownerToken);
      const byEmail = validEmail(email) && rec.email === email;
      if (!byToken && !byEmail) {
        return json({ error: "That is not the owner token or address for this site." }, 403);
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
             `Your site ${rec.url} scored ${scan.score.pct}% in today's compliance check (previous: ${prev}%).\n\nRun a new scan: https://eucomplypro.com/scan/\n\nAutomated technical checks only — not legal advice.`);
        }
      })());
    }
  },
};