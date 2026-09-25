/**
 * Security regression tests for the EUComply workers.
 *
 *   node tools/test_worker_security.mjs
 *
 * Covers the two P0 classes found 2026-09-25:
 *   A. SSRF — the public scanner followed redirects without validating the
 *      target, so any public site could bounce a scan at 127.0.0.1 or the cloud
 *      metadata endpoint, and a hostile origin could put HTML in the HSTS header.
 *   B. Ownership — the monitoring beta let anyone read another site's history and
 *      silently re-point its alert email, because the only credential was the
 *      email on the record.
 *
 * No dependencies, no network: fetch and the KV bindings are stubbed.
 */

import assert from "node:assert/strict";

import {
  isPublicHostname, isPublicIPv4, isPublicIPv6, expandIPv6,
  normalizeUrl, assertPublicTarget, safeFetch, runScan, readCappedText,
} from "../shared/scan-engine.js";
import watch, { checkStates, previousEntry, diffChecks, applyScan } from "../worker-watch/index.js";

let passed = 0;
const failures = [];

async function test(name, fn) {
  try {
    await fn();
    passed++;
  } catch (e) {
    failures.push(`${name}: ${e && e.message}`);
  }
}

/* ------------------------------------------------------------------ stubs */

function stubFetch(routes) {
  const calls = [];
  const impl = async (input, init = {}) => {
    const url = typeof input === "string" ? input : input.url;
    calls.push({ url, init });
    const route = routes[url];
    if (!route) return new Response("no route", { status: 404 });
    if (typeof route === "function") return route(url, init);
    return route;
  };
  const saved = globalThis.fetch;
  globalThis.fetch = impl;
  return { calls, restore: () => { globalThis.fetch = saved; } };
}

const html = (body = "<html><body>hello</body></html>") =>
  new Response(body, { status: 200, headers: { "Content-Type": "text/html" } });

/** In-memory Cloudflare KV. */
function kv() {
  const map = new Map();
  return {
    map,
    async get(k) { return map.has(k) ? map.get(k) : null; },
    async put(k, v) { map.set(k, v); },
    async delete(k) { map.delete(k); },
    async list({ prefix = "" } = {}) {
      return { keys: [...map.keys()].filter(k => k.startsWith(prefix)).map(name => ({ name })), list_complete: true };
    },
  };
}

const watchEnv = () => ({ WATCH: kv(), RATE: kv() });
const post = (path, body, ip = "203.0.113.9") =>
  watch.fetch(new Request("https://watch.test" + path, {
    method: "POST",
    headers: { "Content-Type": "application/json", "cf-connecting-ip": ip },
    body: JSON.stringify(body),
  }), watchEnvFresh);

let watchEnvFresh;
const resetWatch = () => { watchEnvFresh = watchEnv(); return watchEnvFresh; };
const watchFetch = (path, body, ip = "203.0.113.9", env = watchEnvFresh) =>
  watch.fetch(new Request("https://watch.test" + path, {
    method: "POST",
    headers: { "Content-Type": "application/json", "cf-connecting-ip": ip },
    body: typeof body === "string" ? body : JSON.stringify(body),
  }), env);

/* ------------------------------------------------------- A. SSRF: literals */

await test("public IPv4 literals are allowed", () => {
  for (const ip of ["1.1.1.1", "8.8.8.8", "93.184.216.34", "172.32.0.1", "192.169.0.1", "100.63.255.255"]) {
    assert.equal(isPublicHostname(ip), true, ip);
  }
});

await test("private and reserved IPv4 literals are refused", () => {
  const bad = [
    "0.0.0.0", "0.1.2.3", "10.0.0.1", "10.255.255.254", "127.0.0.1", "127.1",
    "169.254.169.254", "172.16.0.1", "172.31.255.255", "192.168.1.1",
    "100.64.0.1", "100.127.255.255", "198.18.0.1", "198.19.255.255",
    "192.0.0.1", "192.0.2.1", "203.0.113.9", "224.0.0.1", "255.255.255.255",
    "999.1.1.1", "1.2.3",
  ];
  for (const ip of bad) assert.equal(isPublicHostname(ip), false, ip);
});

await test("the WHATWG parser's normalisations cannot smuggle loopback", () => {
  // These all reach the fetch layer as 127.0.0.1.
  for (const raw of ["http://0x7f.0.0.1/", "http://127.1/", "http://0177.0.0.1/", "http://127.000.000.001/"]) {
    assert.equal(isPublicHostname(new URL(raw).hostname), false, raw);
  }
  assert.equal(normalizeUrl("http://127.1"), null);
  assert.equal(normalizeUrl("http://0x7f.0.0.1"), null);
});

await test("private IPv6 literals are refused", () => {
  const bad = [
    "::1", "::", "[::1]", "::ffff:127.0.0.1", "[::ffff:7f00:1]",
    "::ffff:169.254.169.254", "::ffff:10.0.0.1", "::10.0.0.1",
    "fc00::1", "fd12:3456::1", "fe80::1", "fe80::a00:1", "ff02::1",
    "2001:db8::1", "64:ff9b::7f00:1", "2002:7f00:0001::1", "100::1",
  ];
  for (const ip of bad) assert.equal(isPublicHostname(ip), false, ip);
});

await test("public IPv6 literals are allowed", () => {
  for (const ip of ["2606:4700:4700::1111", "2a00:1450:4001:80e::200e", "2001:4860:4860::8888"]) {
    assert.equal(isPublicHostname(ip), true, ip);
  }
});

await test("expandIPv6 understands :: compression and v4 tails", () => {
  assert.deepEqual(expandIPv6("::1"), [0, 0, 0, 0, 0, 0, 0, 1]);
  assert.deepEqual(expandIPv6("::"), [0, 0, 0, 0, 0, 0, 0, 0]);
  assert.deepEqual(expandIPv6("fe80::1"), [0xfe80, 0, 0, 0, 0, 0, 0, 1]);
  assert.deepEqual(expandIPv6("::ffff:127.0.0.1"), [0, 0, 0, 0, 0, 0xffff, 0x7f00, 1]);
  assert.equal(expandIPv6("not-an-ip"), null);
  assert.equal(expandIPv6("1:2:3:4:5:6:7:8:9"), null);
});

await test("isPublicIPv4 / isPublicIPv6 agree with isPublicHostname", () => {
  assert.equal(isPublicIPv4(127, 0, 0, 1), false);
  assert.equal(isPublicIPv4(169, 254, 169, 254), false);
  assert.equal(isPublicIPv4(93, 184, 216, 34), true);
  assert.equal(isPublicIPv6("::1"), false);
  assert.equal(isPublicIPv6("2606:4700:4700::1111"), true);
});

await test("private-resolving hostnames are refused", () => {
  for (const h of ["localhost", "LOCALHOST.", "api.localhost", "printer.local",
                   "db.internal", "metadata.google.internal", "instance-data",
                   "box.home.arpa", "nas.lan", "files.corp"]) {
    assert.equal(isPublicHostname(h), false, h);
  }
});

/* ----------------------------------------------- A. SSRF: redirect handling */

await test("a redirect into loopback is refused, not followed", async () => {
  const s = stubFetch({
    "https://evil.example/start": new Response(null, { status: 302, headers: { Location: "http://127.0.0.1/admin" } }),
    "http://127.0.0.1/admin": html("SHOULD NEVER BE FETCHED"),
  });
  try {
    await assert.rejects(() => safeFetch("https://evil.example/start"), /not a public website/);
    assert.equal(s.calls.filter(c => c.url.includes("127.0.0.1")).length, 0,
      "the private target was requested");
  } finally { s.restore(); }
});

await test("a redirect to the cloud metadata endpoint is refused", async () => {
  const s = stubFetch({
    "https://evil.example/meta": new Response(null, { status: 301, headers: { Location: "http://169.254.169.254/latest/meta-data/" } }),
    "http://169.254.169.254/latest/meta-data/": html("SHOULD NEVER BE FETCHED"),
  });
  try {
    await assert.rejects(() => safeFetch("https://evil.example/meta"), /not a public website/);
    assert.equal(s.calls.filter(c => c.url.includes("169.254")).length, 0);
  } finally { s.restore(); }
});

await test("a redirect to a private IPv6 or hostname is refused", async () => {
  for (const loc of ["http://[::1]/", "http://[fe80::1]/", "http://localhost/", "http://db.internal/"]) {
    const s = stubFetch({ "https://evil.example/x": new Response(null, { status: 302, headers: { Location: loc } }) });
    try {
      await assert.rejects(() => safeFetch("https://evil.example/x"), /not a public website/);
    } finally { s.restore(); }
  }
});

await test("non-http(s) redirect targets are refused", async () => {
  for (const loc of ["file:///etc/passwd", "gopher://127.0.0.1:11211/", "data:text/html,<script>"]) {
    const s = stubFetch({ "https://evil.example/s": new Response(null, { status: 302, headers: { Location: loc } }) });
    try {
      await assert.rejects(() => safeFetch("https://evil.example/s"), /Only http and https/);
    } finally { s.restore(); }
  }
});

await test("a public redirect chain is followed and reported", async () => {
  const s = stubFetch({
    "https://a.example/": new Response(null, { status: 301, headers: { Location: "https://b.example/next" } }),
    "https://b.example/next": new Response(null, { status: 302, headers: { Location: "/final" } }),
    "https://b.example/final": html("<html>ok</html>"),
  });
  try {
    const out = await safeFetch("https://a.example/");
    assert.equal(out.url, "https://b.example/final");
    assert.equal(out.resp.status, 200);
    assert.equal(out.chain.length, 2);
    assert.equal(out.chain[1].from, "https://b.example/next");
    assert.ok(s.calls.length >= 3, "expected three requests in the chain");
    const hops = s.calls.filter(c => c.url.startsWith("https://a.example") || c.url.startsWith("https://b.example"));
    assert.equal(hops.length, 3);
    for (const c of hops) assert.equal(c.init.redirect, "manual", "a hop was followed by the runtime");
  } finally { s.restore(); }
});

await test("redirect loops are capped instead of hanging", async () => {
  const s = stubFetch({
    "https://loop.example/": new Response(null, { status: 302, headers: { Location: "https://loop.example/again" } }),
    "https://loop.example/again": new Response(null, { status: 302, headers: { Location: "https://loop.example/" } }),
  });
  try {
    await assert.rejects(() => safeFetch("https://loop.example/"), /redirected more than 5 times/);
  } finally { s.restore(); }
});

await test("runScan reports an SSRF block instead of a network error", async () => {
  const s = stubFetch({
    "https://evil.example/": new Response(null, { status: 302, headers: { Location: "http://10.0.0.5/" } }),
  });
  try {
    await assert.rejects(() => runScan("https://evil.example"), /not a public website/);
  } finally { s.restore(); }
});

/* --------------------------------------------- A. SSRF: hostile header text */

await test("a script payload in the HSTS header is neutralised", async () => {
  const s = stubFetch({
    "https://xss.example/": new Response("<html>hi</html>", {
      status: 200,
      headers: { "Content-Type": "text/html", "Strict-Transport-Security": 'max-age=1"><script>alert(1)</script>' },
    }),
  });
  try {
    const out = await runScan("https://xss.example");
    const detail = out.checks.ssl.detail;
    assert.ok(!/[<>]/.test(detail), "raw angle brackets survive in the HSTS detail: " + detail);
    assert.ok(!/alert\(1\)/.test(detail), "script payload survives in the HSTS detail: " + detail);
  } finally { s.restore(); }
});

await test("a real HSTS policy is still reported", async () => {
  const s = stubFetch({
    "https://ok.example/": new Response("<html>hi</html>", {
      status: 200,
      headers: { "Content-Type": "text/html", "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload" },
    }),
  });
  try {
    const out = await runScan("https://ok.example");
    assert.equal(out.checks.ssl.pass, true);
    assert.match(out.checks.ssl.detail, /max-age=31536000/);
  } finally { s.restore(); }
});

await test("the ssl check follows the final URL, not the requested one", async () => {
  const s = stubFetch({
    "https://downgrade.example/": new Response(null, { status: 301, headers: { Location: "http://downgrade.example/" } }),
    "http://downgrade.example/": html("<html>hi</html>"),
  });
  try {
    const out = await runScan("https://downgrade.example");
    assert.equal(out.checks.ssl.label, "Not HTTPS");
    assert.equal(out.checks.ssl.pass, false);
  } finally { s.restore(); }
});

await test("an oversized body is truncated at the cap", async () => {
  const big = "x".repeat(3_000_000);
  const text = await readCappedText(new Response(big), 1000);
  assert.equal(text.length, 1000);
});

/* ------------------------------------------- B. monitoring beta: ownership */

await test("register returns an owner token and stores it", async () => {
  const env = resetWatch();
  const s = stubFetch({ "https://shop.example/": html("<html><a href='/privacy'>privacy</a></html>") });
  try {
    const r = await watchFetch("/register", { url: "shop.example", email: "owner@shop.example" }, "198.51.100.7", env);
    const d = await r.json();
    assert.equal(r.status, 200);
    assert.match(d.ownerToken, /^[a-f0-9]{48}$/);
    const rec = JSON.parse(env.WATCH.map.get("site:https://shop.example"));
    assert.equal(rec.ownerToken, d.ownerToken);
    assert.equal(rec.email, "owner@shop.example");
    // The email must never leave the worker.
    assert.ok(!JSON.stringify(d).includes("owner@shop.example"), "email leaked in the response");
  } finally { s.restore(); }
});

await test("status requires the owner token", async () => {
  const env = resetWatch();
  const s = stubFetch({ "https://shop.example/": html("<html>x</html>") });
  try {
    const reg = await (await watchFetch("/register", { url: "shop.example", email: "owner@shop.example" }, "198.51.100.7", env)).json();

    const noTok = await watchFetch("/status", { url: "shop.example" }, "198.51.100.8", env);
    assert.equal(noTok.status, 403);

    const wrong = await watchFetch("/status", { url: "shop.example", ownerToken: "f".repeat(48) }, "198.51.100.8", env);
    assert.equal(wrong.status, 403);

    const good = await watchFetch("/status", { url: "shop.example", ownerToken: reg.ownerToken }, "198.51.100.8", env);
    assert.equal(good.status, 200);
    const d = await good.json();
    assert.equal(d.url, "https://shop.example");
    assert.ok(!("email" in d), "status response leaks the owner email");
    assert.ok(!("ownerToken" in d), "status response echoes the owner token");
  } finally { s.restore(); }
});

await test("the old public GET /status route is gone", async () => {
  const env = resetWatch();
  const s = stubFetch({ "https://shop.example/": html("<html>x</html>") });
  try {
    await watchFetch("/register", { url: "shop.example", email: "owner@shop.example" }, "198.51.100.7", env);
    const r = await watch.fetch(new Request("https://watch.test/status?url=shop.example",
      { headers: { "cf-connecting-ip": "198.51.100.9" } }), env);
    assert.equal(r.status, 404);
  } finally { s.restore(); }
});

await test("a stranger cannot re-point the alert email", async () => {
  const env = resetWatch();
  const s = stubFetch({ "https://shop.example/": html("<html>x</html>") });
  try {
    const reg = await (await watchFetch("/register", { url: "shop.example", email: "owner@shop.example" }, "198.51.100.7", env)).json();
    const hijack = await watchFetch("/register", { url: "shop.example", email: "attacker@evil.example" }, "198.51.100.8", env);
    assert.equal(hijack.status, 409);
    const rec = JSON.parse(env.WATCH.map.get("site:https://shop.example"));
    assert.equal(rec.email, "owner@shop.example", "alert email was hijacked");
    assert.equal(rec.ownerToken, reg.ownerToken, "owner token was rotated by a stranger");

    // Same address, no token: still no silent success.
    const same = await watchFetch("/register", { url: "shop.example", email: "owner@shop.example" }, "198.51.100.8", env);
    assert.equal(same.status, 409);

    // The real owner can change it, and the token survives.
    const mine = await watchFetch("/register", { url: "shop.example", email: "new@shop.example", ownerToken: reg.ownerToken }, "198.51.100.7", env);
    assert.equal(mine.status, 200);
    const rec2 = JSON.parse(env.WATCH.map.get("site:https://shop.example"));
    assert.equal(rec2.email, "new@shop.example");
    assert.equal(rec2.ownerToken, reg.ownerToken, "owner must not have to re-claim on an email change");
  } finally { s.restore(); }
});

await test("a stranger cannot unregister somebody else's site", async () => {
  const env = resetWatch();
  const s = stubFetch({ "https://shop.example/": html("<html>x</html>") });
  try {
    const reg = await (await watchFetch("/register", { url: "shop.example", email: "owner@shop.example" }, "198.51.100.7", env)).json();
    const bad = await watchFetch("/unregister", { url: "shop.example", email: "attacker@evil.example" }, "198.51.100.8", env);
    assert.equal(bad.status, 403);
    assert.ok(env.WATCH.map.has("site:https://shop.example"), "site was deleted by a stranger");
    const badTok = await watchFetch("/unregister", { url: "shop.example", ownerToken: "a".repeat(48) }, "198.51.100.8", env);
    assert.equal(badTok.status, 403);
    assert.ok(env.WATCH.map.has("site:https://shop.example"));

    const good = await watchFetch("/unregister", { url: "shop.example", ownerToken: reg.ownerToken }, "198.51.100.7", env);
    assert.equal(good.status, 200);
    assert.ok(!env.WATCH.map.has("site:https://shop.example"), "owner could not delete their own record");
    assert.equal(env.WATCH.map.get("meta:sitecount"), "0", "site counter not decremented");
  } finally { s.restore(); }
});

await test("a legacy beta record can be claimed once with its address", async () => {
  const env = resetWatch();
  const s = stubFetch({ "https://legacy.example/": html("<html>x</html>") });
  try {
    await env.WATCH.put("site:https://legacy.example", JSON.stringify({
      url: "https://legacy.example", email: "old@legacy.example", created: "2026-08-01T00:00:00.000Z",
      history: [{ date: "2026-08-01", score: 50 }], lastScore: 50,
    }));
    const stranger = await watchFetch("/status", { url: "legacy.example", email: "nope@evil.example" }, "198.51.100.8", env);
    assert.equal(stranger.status, 403);
    const owner = await watchFetch("/status", { url: "legacy.example", email: "old@legacy.example" }, "198.51.100.8", env);
    assert.equal(owner.status, 200);
    const d = await owner.json();
    assert.equal(d.currentScore, 50, "existing beta data was lost when claiming");
    const rec = JSON.parse(env.WATCH.map.get("site:https://legacy.example"));
    assert.match(rec.ownerToken, /^[a-f0-9]{48}$/);
  } finally { s.restore(); }
});

await test("repeated writes from one IP are rate limited", async () => {
  const env = resetWatch();
  const s = stubFetch({ "https://a.example/": html("<html>x</html>"), "https://b.example/": html("<html>x</html>") });
  try {
    const codes = [];
    for (let n = 0; n < 9; n++) {
      const host = n % 2 ? "b.example" : "a.example";
      const r = await watchFetch("/register", { url: host, email: `o${n}@shop.example` }, "198.51.100.20", env);
      codes.push(r.status);
    }
    assert.ok(codes.includes(429), "no 429 after 9 writes from one IP: " + codes.join(","));
    // A different IP is unaffected.
    const other = await watchFetch("/register", { url: "c.example", email: "o@shop.example" }, "198.51.100.21", env);
    assert.notEqual(other.status, 429);
  } finally { s.restore(); }
});

await test("register and unregister validate their input", async () => {
  const env = resetWatch();
  const s = stubFetch({});
  try {
    assert.equal((await watchFetch("/register", { url: "http://127.0.0.1/", email: "a@b.co" }, "198.51.100.30", env)).status, 400);
    assert.equal((await watchFetch("/register", { url: "shop.example", email: "nope" }, "198.51.100.30", env)).status, 400);
    assert.equal((await watchFetch("/unregister", { url: "shop.example", email: "a@b.co" }, "198.51.100.30", env)).status, 404);
  } finally { s.restore(); }
});

/* ------------------------------------------- C. per-check history & alerting */

const GOOD_PAGE = `<!doctype html><html><head><meta name="generator" content="WordPress">
<meta name="robots" content="index"><link rel="privacy-policy" href="/privacy-policy/">
<title>Shop</title></head><body><nav><a href="/privacy-policy/">Privacy Policy</a>
<a href="/terms-and-conditions/">Terms</a></nav><form action="/contact/"><input name="email"></form>
<!-- IAB TCF consent platform, Consent Mode v2 --></body></html>`;

// Same shop after a bad deploy: legal pages gone, trackers shipping before
// consent, and the HSTS header gone. `legal` and `trackers` become hard fails,
// `ssl` becomes a warning — three different states from one page.
const BROKEN_PAGE = `<!doctype html><html><head><meta name="generator" content="WordPress">
<meta name="robots" content="index"><title>Shop</title>
<script src="https://www.google-analytics.com/analytics.js"></script>
<script src="https://connect.facebook.net/en_US/fbevents.js"></script></head>
<body><form action="/contact/"><input name="email"></form></body></html>`;

const HSTS = { "Strict-Transport-Security": "max-age=31536000; includeSubDomains" };

/** Run the real engine against a stubbed origin, so the fixtures stay honest. */
async function scanOf(page, { headers = HSTS } = {}) {
  const s = stubFetch({ "https://watch.example/": new Response(page, { status: 200, headers: { "Content-Type": "text/html", ...headers } }) });
  try { return await runScan("https://watch.example/"); } finally { s.restore(); }
}

/** Drive the real cron handler and wait for the work it hands to waitUntil. */
async function runCron(env) {
  const pending = [];
  await watch.scheduled({ cron: "0 6 * * *" }, env, { waitUntil: (p) => pending.push(p) });
  await Promise.all(pending);
}

const recFor = (over = {}) => ({ url: "https://watch.example", email: "owner@shop.example", history: [], lastScore: null, ...over });
const day = (n) => `2026-09-${String(n).padStart(2, "0")}`;
const iso = (n) => new Date(Date.UTC(2026, 0, 1) + n * 86_400_000).toISOString().slice(0, 10);

await test("per-check state is tri-state, not the summary score", async () => {
  const good = await scanOf(GOOD_PAGE);
  const broken = await scanOf(BROKEN_PAGE, { headers: {} });
  const goodStates = checkStates(good);
  const badStates = checkStates(broken);
  assert.equal(goodStates.legal, "pass", "fixture no longer passes the legal check");
  assert.equal(badStates.legal, "fail", "a missing legal page is a hard fail, not a warning");
  assert.equal(badStates.ssl, "warn", "https without HSTS is a warning, not a fail");
  assert.ok(Object.values(badStates).filter(s => s === "warn").length >= 1);
  // The score is unchanged by this work: a warning still counts as a miss.
  assert.equal(broken.score.total, good.score.total);
  assert.ok(broken.score.passed < good.score.passed, "the broken page should score worse");
  assert.ok(!Object.values(badStates).includes(undefined), "every scored check needs a state");
});

await test("previousEntry picks the last day that is not today", () => {
  const h = [{ date: "2026-09-20" }, { date: "2026-09-21" }, { date: "2026-09-22" }];
  assert.equal(previousEntry(h, "2026-09-22").date, "2026-09-21");
  assert.equal(previousEntry(h, "2026-09-23").date, "2026-09-22");
  assert.equal(previousEntry([{ date: "2026-09-22" }], "2026-09-22"), null);
  assert.equal(previousEntry(undefined, "2026-09-22"), null);
});

await test("diffChecks reports movement only, never a repeat", () => {
  const prev = { legal: "pass", ssl: "warn", trackers: "pass" };
  assert.deepEqual(diffChecks(prev, { ...prev }), [], "identical states must be silent");
  assert.deepEqual(diffChecks(prev, { legal: "fail", ssl: "warn", trackers: "pass" }).map(c => [c.key, c.from, c.to]), [["legal", "pass", "fail"]]);
  assert.deepEqual(diffChecks(prev, { legal: "pass", ssl: "fail", trackers: "pass" }).map(c => c.to), ["fail"]);
  assert.deepEqual(diffChecks({}, { legal: "fail" }).map(c => c.from), ["new"]);
  assert.deepEqual(diffChecks(prev, { legal: "pass", ssl: "warn" }), [], "a check that vanished is not a regression");
});

await test("identical scans are silent, and a repeat failure is not mailed twice", async () => {
  const good = await scanOf(GOOD_PAGE);
  const broken = await scanOf(BROKEN_PAGE, { headers: {} });
  const r1 = applyScan(recFor(), good, day(1));
  assert.equal(r1.alert, null, "the first day has no baseline to alert on");
  const r2 = applyScan(r1.record, good, day(2));
  assert.equal(r2.alert, null, "an identical daily scan sent an alert");
  const r3 = applyScan(r2.record, broken, day(3));
  assert.ok(r3.alert, "pass → fail did not produce an alert");
  const r4 = applyScan(r3.record, broken, day(4));
  assert.equal(r4.alert, null, "the same failure was mailed again on day two");
  const r5 = applyScan(r4.record, good, day(5));
  assert.equal(r5.alert, null, "a recovery-only day must stay silent, not invent news");
});

await test("one mail names the check, its old status, the time and the fix", async () => {
  const good = await scanOf(GOOD_PAGE);
  const broken = await scanOf(BROKEN_PAGE, { headers: {} });
  const base = applyScan(recFor(), good, day(1)).record;
  const { record, alert } = applyScan(base, broken, day(2));
  const keys = alert.regressions.map(r => r.key);
  // Dropping the legal pages also removes the privacy link the form check needs,
  // so this fixture legitimately reports four checks — the point is that none of
  // them is hidden and none of the unchanged ones is repeated.
  for (const key of ["legal", "trackers", "ssl"]) assert.ok(keys.includes(key), `${key} regressed but was not reported: ${keys.join(",")}`);
  assert.ok(!keys.includes("dora"), "an unchanged check was reported as a change");
  const legal = alert.regressions.find(r => r.key === "legal");
  assert.equal(legal.from, "pass");
  assert.equal(legal.to, "fail");
  assert.match(alert.subject, /watch\.example/);
  // Name, previous status, timestamp and a concrete action — the four things an
  // agency needs to act without opening a browser.
  assert.match(alert.text, /legal/i);
  assert.match(alert.text, /passing → failing/);
  assert.match(alert.text, new RegExp(broken.scannedAt));
  assert.match(alert.text, /Fix: /);
  assert.match(alert.text, new RegExp(`Score: ${broken.score.pct}% \\(previous ${good.score.pct}%\\)`));
  assert.ok(!/owner@shop\.example/.test(alert.text), "the mail body must not echo the address back");
  assert.equal(record.lastChecks.legal, "fail");
});

await test("a re-run of the same day is deduped, not double-counted", async () => {
  const good = await scanOf(GOOD_PAGE);
  const broken = await scanOf(BROKEN_PAGE, { headers: {} });
  const base = applyScan(recFor(), good, day(1)).record;
  const first = applyScan(base, broken, day(2));
  const again = applyScan(first.record, broken, day(2));
  assert.equal(again.record.history.filter(h => h.date === day(2)).length, 1);
  assert.equal(again.alert, null, "a retried cron run must not re-send the same alert");
});

await test("30 days are kept and older days are dropped", async () => {
  const good = await scanOf(GOOD_PAGE);
  let rec = recFor();
  for (let d = 1; d <= 35; d++) rec = applyScan(rec, good, day(d)).record;
  assert.equal(rec.history.length, 30, `expected 30 days, got ${rec.history.length}`);
  assert.equal(rec.history[0].date, day(6), "the oldest retained day is wrong");
  assert.equal(rec.history.at(-1).date, day(35));
  assert.ok(rec.history.every(h => h.checks && Object.keys(h.checks).length > 0), "an entry lost its per-check state");
  assert.ok(rec.history.every(h => h.date >= day(6)), "an expired day survived");
});

await test("50 and 100 consecutive daily scans stay bounded", async () => {
  const good = await scanOf(GOOD_PAGE);
  const broken = await scanOf(BROKEN_PAGE, { headers: {} });
  for (const total of [50, 100]) {
    let rec = recFor();
    for (let d = 1; d <= total; d++) rec = applyScan(rec, d % 2 ? good : broken, iso(d)).record;
    assert.equal(rec.history.length, 30, `${total} scans should still cap at 30 days`);
    const bytes = JSON.stringify(rec).length;
    assert.ok(bytes < 32_000, `${total} scans grew the record to ${bytes} bytes`);
    // The record has to survive a real KV round-trip, not just live in memory.
    const round = JSON.parse(JSON.stringify(rec));
    assert.equal(round.history.length, 30);
    assert.ok(round.lastChecks.legal, "per-check state lost in the round-trip");
  }
});

await test("a record with no per-check baseline does not report every failure as new", async () => {
  // Pre-deploy beta records have score-only history. On the first day after the
  // per-check deploy there is no baseline: mailing each already-broken check as
  // "new" would be a burst of false alarms on deploy day. The old score-only
  // alert is honest and stays, until tomorrow's snapshot makes the diff real.
  const legacy = { url: "https://watch.example", email: "owner@shop.example", history: [{ date: day(1), score: 100, passed: 9, total: 9 }], lastScore: 100 };
  const broken = await scanOf(BROKEN_PAGE, { headers: {} });
  const r1 = applyScan(legacy, broken, day(2));
  assert.ok(r1.alert, "a real score drop on the transition day should still be reported");
  assert.equal(r1.alert.regressions.length, 0, "checks without a baseline must not be reported as new");
  assert.match(r1.alert.subject, /score dropped on https:\/\/watch\.example \(100% → 0%\)/);
  assert.ok(!/no earlier snapshot/.test(r1.alert.text), "the transition mail leaks 'new' placeholders");
  assert.equal(r1.record.history.length, 2);
  assert.ok(r1.record.history.at(-1).checks.legal === "fail", "the first day should still be stored");
  // The next day has a real baseline, and day two of the same failure is silent.
  assert.equal(applyScan(r1.record, broken, day(3)).alert, null);
});

await test("the cron path stores history and mails through the real handler", async () => {
  const env = resetWatch();
  const mails = [];
  env.ALERT_KEY = "test-key";
  // Yesterday's snapshot is the good page, so today's cron run finds a real
  // regression rather than an unchanged site.
  const seeded = applyScan(
    { url: "https://watch.example", email: "owner@shop.example", history: [], lastScore: null },
    await scanOf(GOOD_PAGE),
    new Date(Date.now() - 86_400_000).toISOString().slice(0, 10),
  );
  await env.WATCH.put("site:https://watch.example", JSON.stringify(seeded.record));
  const s = stubFetch({
    "https://watch.example/": new Response(BROKEN_PAGE, { status: 200, headers: { "Content-Type": "text/html" } }),
    "https://api.resend.com/emails": (url, init) => { mails.push(JSON.parse(init.body)); return new Response("{}", { status: 200 }); },
  });
  try {
    await runCron(env);
    assert.equal(mails.length, 1, `expected exactly one mail, got ${mails.length}`);
    assert.equal(mails[0].to, "owner@shop.example");
    assert.match(mails[0].subject, /new issues? on https:\/\/watch\.example/);
    assert.match(mails[0].text, /legal/i);
    await runCron(env);
    assert.equal(mails.length, 1, "a second identical cron run sent another mail");

    const rec = JSON.parse(env.WATCH.map.get("site:https://watch.example"));
    assert.equal(rec.history.length, 2, "a same-day rerun added a second history entry");
    assert.ok(rec.lastChecks.legal === "fail", "cron did not store per-check state");
  } finally { s.restore(); }
});

await test("customer data never reaches the public surface", async () => {
  const env = resetWatch();
  const s = stubFetch({ "https://watch.example/": new Response(GOOD_PAGE, { status: 200, headers: { "Content-Type": "text/html", ...HSTS } }) });
  try {
    const reg = await (await watchFetch("/register", { url: "watch.example", email: "private@shop.example" }, "198.51.100.41", env)).json();
    await runCron(env);
    const status = await (await watchFetch("/status", { url: "watch.example", ownerToken: reg.ownerToken }, "198.51.100.41", env)).json();
    const dump = JSON.stringify(status);
    assert.ok(!dump.includes("private@shop.example"), "the alert address leaked into /status");
    assert.ok(!dump.includes(reg.ownerToken), "the owner token leaked into /status");
    const health = await (await watch.fetch(new Request("https://watch.test/health"), env)).json();
    assert.ok(!JSON.stringify(health).includes("watch.example"), "/health exposes monitored sites");
    assert.ok(status.checks && Object.keys(status.checks).length > 0, "the owner cannot see per-check state");
  } finally { s.restore(); }
});

/* ------------------------------------------------------------------ report */

console.log(`${passed} security checks passed`);
if (failures.length) {
  for (const f of failures) console.error("FAIL " + f);
  process.exit(1);
}
