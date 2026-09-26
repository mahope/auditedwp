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
//   POST /badge     { url, ownerToken, enabled } -> opt in/out of the public badge
//   GET  /badge/{site_id}.json                  -> public, no key: score + time only
//   GET  /health
// Cron: daily 06:00 UTC — re-scans every registered beta site, stores per-check
//       history, and emails one alert per new regression (via Resend if
//       ALERT_KEY is set). Identical scans are silent.
//
// Named exports below are the pure history/alert logic. They are exported so the
// regression tests can exercise them without a network or a KV binding.

import { runScan, normalizeUrl, json, CORS } from '../shared/scan-engine.js';

const todayKey = () => new Date().toISOString().slice(0, 10);
// Retention is the entry cap, not a KV expiration: an expirationTtl on the site
// record would delete the registration itself, and the daily cron write resets
// it anyway, so it could never expire an actively monitored site.
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

async function rateLimited(env, ip, max = RATE_MAX, ns = "watchrl") {
  if (!env.RATE || !ip || ip === "unknown") return false;
  try {
    const key = `${ns}:${ip}`;
    const now = Date.now();
    const raw = await env.RATE.get(key);
    const win = raw ? JSON.parse(raw) : { start: now, n: 0 };
    if (now - win.start > RATE_WINDOW_MS) { win.start = now; win.n = 0; }
    win.n++;
    if (win.n > max) return true;
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

/* ------------------------------------------------------- history & alerting */

const WORDS = { pass: "passing", warn: "warning", fail: "failing", new: "new (no earlier snapshot)" };

/**
 * Per-check state for one scan, as a small tri-state map.
 *
 * Tri-state on purpose: the summary score counts a warning as a miss (decision
 * in task 3b), but "HTTPS without HSTS" is a different problem from a consent
 * banner that disappeared. A single score cannot tell an agency which check
 * regressed, so history keeps the three states apart and the summary score
 * stays exactly what it always was.
 */
export function checkStates(scan) {
  const out = {};
  for (const [key, c] of Object.entries(scan?.checks || {})) {
    if (typeof c?.pass !== "boolean") continue;
    out[key] = c.pass ? "pass" : c.warn ? "warn" : "fail";
  }
  return out;
}

/** The most recent stored day that is not `date`, i.e. the baseline to diff against. */
export function previousEntry(history, date) {
  for (let i = (history || []).length - 1; i >= 0; i--) {
    const h = history[i];
    if (h && h.date !== date) return h;
  }
  return null;
}

/**
 * What changed between two per-check snapshots.
 *
 * A check that is still broken is not news on day two, and repeating it is
 * exactly the alert spam this replaces — so identical states never appear here.
 * A check missing from the older snapshot is reported as `new` rather than as a
 * regression against a guess.
 */
export function diffChecks(prev, next) {
  const out = [];
  for (const [key, to] of Object.entries(next || {})) {
    const from = prev?.[key];
    if (from === to) continue;
    out.push({ key, from: from || "new", to });
  }
  return out;
}

/**
 * One mail per scan that changed something, listing each new regression with its
 * check name, the status it had before, the time it was seen, and what to do
 * about it. Returns null when there is nothing to say, so identical daily scans
 * send nothing at all.
 *
 * `prevScore` is the baseline's score, not the record's current one — the caller
 * has already stored today's number by the time it gets here.
 */
export function buildAlert(site, changes, scan, prevScore) {
  const regressions = changes.filter(c => c.to !== "pass" && c.from !== "fail");
  const recovered = changes.filter(c => c.to === "pass");
  const scoreDropped = typeof prevScore === "number" && scan.score.pct < prevScore;
  if (!regressions.length && !scoreDropped) return null;

  const stamp = scan.scannedAt || new Date().toISOString();
  const subject = regressions.length
    ? `EUComply: ${regressions.length} new ${regressions.length === 1 ? "issue" : "issues"} on ${site.url}`
    : `EUComply: score dropped on ${site.url} (${prevScore}% → ${scan.score.pct}%)`;

  const lines = regressions.map((c, i) => {
    const check = scan.checks?.[c.key] || {};
    const name = check.label || c.key;
    return [
      `${i + 1}. ${name} (${c.key}) — ${WORDS[c.from] || c.from} → ${WORDS[c.to] || c.to}`,
      `   Seen: ${stamp}`,
      check.detail ? `   Found: ${check.detail}` : null,
      check.fix ? `   Fix: ${check.fix}` : `   Re-run the scan for the full detail: https://eucomplypro.com/scan/`,
    ].filter(Boolean).join("\n");
  });

  const tail = [];
  if (recovered.length) tail.push(`Recovered: ${recovered.map(c => (scan.checks?.[c.key]?.label || c.key)).join(", ")}.`);
  if (scoreDropped) tail.push(`Score: ${scan.score.pct}% (previous ${prevScore}%).`);
  tail.push("Run a new scan: https://eucomplypro.com/scan/");
  tail.push("Automated technical checks only — not legal advice.");

  return { subject, text: `${lines.join("\n\n")}\n\n${tail.join("\n")}`, regressions, recovered };
}

/**
 * Fold one scan into a site record: store the day's snapshot, keep 30 days, and
 * decide whether this day deserves an alert.
 *
 * The date is a parameter rather than a direct `new Date()` so the regression
 * tests can walk 100 consecutive days without a fake clock. Both the cron job
 * and the first scan at registration go through here, so they cannot drift apart.
 *
 * Returns the updated record plus the alert to send, or null when the day is
 * silent — including the first day of a record that predates per-check history,
 * where there is no baseline to compare against yet.
 */
export function applyScan(rec, scan, date = todayKey()) {
  const history = rec.history || [];
  // A retried run on the same date must measure against what today already
  // stored, not against yesterday: comparing to yesterday again would re-send
  // the identical "4 new issues" mail on every retry.
  const prevEntry = history.find(h => h && h.date === date) || previousEntry(history, date);
  const prevChecks = prevEntry?.checks || null;
  const entry = { date, score: scan.score.pct, passed: scan.score.passed, total: scan.score.total, checks: checkStates(scan) };
  const record = {
    ...rec,
    history: [...history.filter(h => h && h.date !== date), entry].slice(-MAX_HISTORY_DAYS),
    lastScore: scan.score.pct,
    lastScan: scan.scannedAt,
    lastChecks: entry.checks,
  };
  if (!prevChecks) {
    // A record that predates per-check history has no baseline to diff against,
    // and reporting every already-broken check as "new" would mail every beta user
    // a burst of false alarms on deploy day. The old score-only alert is still
    // honest, so that one day keeps the score drop it always had.
    const legacyDrop = typeof prevEntry?.score === "number" && scan.score.pct < prevEntry.score;
    return { record, entry, alert: legacyDrop ? buildAlert(record, [], scan, prevEntry.score) : null };
  }
  return { record, entry, alert: buildAlert(record, diffChecks(prevChecks, entry.checks), scan, prevEntry.score) };
}

/* ------------------------------------------------------------------ badge */

const SITE_ID_BYTES = 16;
const BADGE_RATE_MAX = 60;
const VERIFY_BASE = "https://eucomplypro.com/verify/";

const validSiteId = (s) => typeof s === "string" && /^[a-f0-9]{32}$/.test(s);

function newSiteId() {
  const b = new Uint8Array(SITE_ID_BYTES);
  crypto.getRandomValues(b);
  return Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("");
}

const badgeKey = (id) => `badge:${id}`;

/**
 * The public badge payload, and nothing else.
 *
 * This is the only shape a stranger can read about a monitored site, so it is
 * built by picking fields rather than by deleting fields: a future field added
 * to the record cannot leak by default. In particular it never carries the full
 * URL (only the host — no path, no query, no credentials), the alert address,
 * the owner token, the history, or any check label/detail/fix text.
 *
 * Returns null when the badge may not be served at all, so a disabled badge and
 * an unknown id are answered identically and the endpoint reveals neither
 * whether a site is monitored nor whether it is a customer.
 */
export function publicBadge(rec, siteId) {
  if (!rec || rec.badge?.enabled !== true) return null;
  if (rec.badge.siteId !== siteId) return null;

  let host = "";
  try { host = new URL(rec.url).hostname.toLowerCase(); } catch { return null; }
  if (!host) return null;

  const entry = (rec.history || []).filter(Boolean).slice(-1)[0] || null;
  const pct = Number.isFinite(rec.lastScore) ? rec.lastScore : null;
  const passed = Number.isFinite(entry?.passed) ? entry.passed : null;
  const total = Number.isFinite(entry?.total) ? entry.total : null;

  // Only the three states checkStates() can produce. A record is data in KV, so
  // a value that is not one of them is dropped rather than passed on to a widget
  // that renders it into somebody else's page.
  const checks = {};
  for (const [k, v] of Object.entries(rec.lastChecks || {})) {
    if (typeof k === "string" && /^[a-z0-9_]{1,24}$/.test(k) && (v === "pass" || v === "warn" || v === "fail")) checks[k] = v;
  }

  return {
    site_id: siteId,
    host,
    score: { passed, total, pct },
    last_scan_at: typeof rec.lastScan === "string" ? rec.lastScan : null,
    checks,
    disclaimer: "Automated technical checks only — not legal advice.",
    verify_url: `${VERIFY_BASE}${siteId}/`,
  };
}

/**
 * Badge responses are never cached.
 *
 * The score is a claim about a specific moment, so a cached 200 would let a
 * badge keep showing a stale score as if it were current — and would keep
 * serving a site whose badge was switched off or whose site was deleted.
 */
function badgeJson(data, status = 200, extra = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      ...CORS,
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
      ...extra,
    },
  });
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return new Response(null, { headers: CORS });
    const path = new URL(request.url).pathname.replace(/\/+$/, "");
    const ip = request.headers.get("cf-connecting-ip") || "unknown";

    if (request.method === "GET" && (path === "" || path === "/health")) {
      const count = parseInt((await env.WATCH.get("meta:sitecount")) || "0", 10);
      return json({ service: "eucomply-watch", version: "1.3.0", sites: count, endpoints: ["POST /register {url,email}", "POST /status {url,ownerToken}", "POST /unregister {url,ownerToken}", "POST /badge {url,ownerToken,enabled}", "GET /badge/{site_id}.json"] });
    }

    // Public badge read. Deliberately before the write rate limit and on its own
    // namespace: a badge is fetched on every page view, so the 5-per-minute
    // write budget would blank a busy visitor's badge within seconds.
    const badgeRead = path.match(/^\/badge\/([^/]+)\.json$/);
    if (request.method === "GET" && badgeRead) {
      const siteId = String(badgeRead[1] || "").trim().toLowerCase();
      // A malformed id and an unknown id get the same answer, so the response
      // never tells a prober which shape of id is valid.
      const notFound = () => badgeJson({ error: "badge_disabled", message: "No public badge for that id." }, 404);
      if (!validSiteId(siteId)) return notFound();
      if (await rateLimited(env, ip, BADGE_RATE_MAX, "badgerl")) {
        return badgeJson({ error: "rate_limited" }, 429, { "Retry-After": "60" });
      }
      const indexed = JSON.parse((await env.WATCH.get(badgeKey(siteId))) || "null");
      if (!indexed?.url) return notFound();
      // The index is a pointer, never a copy: a copy would freeze the score at
      // opt-in time, because the daily cron rewrites `site:` and not this key.
      const rec = JSON.parse((await env.WATCH.get(`site:${indexed.url}`)) || "null");
      const payload = publicBadge(rec, siteId);
      if (!payload) return notFound();
      return badgeJson(payload);
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
        const { record } = applyScan(rec, scan);
        await env.WATCH.put(key, JSON.stringify(record));
        return json({ ok: true, ownerToken, message: `Site registered. First scan complete — score ${scan.score.pct}%.`, score: scan.score, history: record.history });
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
        // Per-check states are part of the stored history, so the owner can see
        // which check moved — never the alert address, the owner token, or
        // anything belonging to another site.
        checks: rec.lastChecks || null,
        // The owner sees their own badge state; nobody else can, because the
        // public id only resolves while it is enabled.
        badge: rec.badge?.enabled
          ? { enabled: true, site_id: rec.badge.siteId, verify_url: `${VERIFY_BASE}${rec.badge.siteId}/` }
          : { enabled: false },
        disclaimer: "Automated technical checks only — not legal advice.",
      });
    }

    // POST /badge — opt in or out of the public badge. The owner token is the
    // only credential, because publishing a site's score to the world is a
    // bigger decision than changing an alert address.
    if (request.method === "POST" && path === "/badge") {
      let body;
      try { body = await request.json(); } catch { return json({ error: "Invalid JSON body" }, 400); }
      const url = normalizeUrl(body.url);
      const token = String(body.ownerToken || "").trim().toLowerCase();
      if (!url) return json({ error: "Provide the URL you registered." }, 400);
      const key = `site:${url}`;
      const raw = await env.WATCH.get(key);
      if (!raw) return json({ error: "Site not registered yet. Use POST /register {url, email} to start monitoring." }, 404);
      const rec = JSON.parse(raw);
      if (!rec.ownerToken || !tokenMatches(token, rec.ownerToken)) {
        return json({ error: "Wrong owner token for this site." }, 403);
      }

      if (body.enabled === false) {
        // Turning it off must stop the public id immediately and destroy the
        // index entry, so a badge URL that is already embedded — or cached in
        // someone's HTML — stops resolving on the next load. The id itself is
        // kept on the record so switching it back on does not break a snippet
        // the customer has already published.
        const old = rec.badge?.siteId;
        rec.badge = validSiteId(old) ? { enabled: false, siteId: old } : null;
        rec.updated = new Date().toISOString();
        await env.WATCH.put(key, JSON.stringify(rec));
        if (validSiteId(old)) await env.WATCH.delete(badgeKey(old));
        return json({ ok: true, site_id: null, message: "Public badge switched off. The embed will show no score." });
      }

      // Re-enabling keeps the same id, so switching the badge off and on again
      // does not silently break the snippet the customer already published.
      const siteId = validSiteId(rec.badge?.siteId) ? rec.badge.siteId : newSiteId();
      rec.badge = { enabled: true, siteId, enabledAt: rec.badge?.enabledAt || new Date().toISOString() };
      rec.updated = new Date().toISOString();
      await env.WATCH.put(key, JSON.stringify(rec));
      // The index holds the url, not a copy of the record, so it can never go
      // stale relative to the site it points at.
      await env.WATCH.put(badgeKey(siteId), JSON.stringify({ url: rec.url }));
      return json({
        ok: true,
        site_id: siteId,
        host: new URL(rec.url).hostname,
        verify_url: `${VERIFY_BASE}${siteId}/`,
        message: "Public badge switched on. The score comes from the daily scan, never from a value a visitor sends.",
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
      const badgeId = rec.badge?.siteId;
      await env.WATCH.delete(`site:${url}`);
      // Deleting the site has to take the public id with it, or a badge for a
      // removed site would keep resolving from the index alone.
      if (validSiteId(badgeId)) await env.WATCH.delete(badgeKey(badgeId));
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
        const { record, alert } = applyScan(rec, scan);
        await env.WATCH.put(key, JSON.stringify(record));
        if (alert) await sendAlert(env, rec.email, alert.subject, alert.text);
      })());
    }
  },
};