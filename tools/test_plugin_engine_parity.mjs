/**
 * Paritet mellem pluginens forside-tjek og den universelle motor.
 *
 *   node tools/test_plugin_engine_parity.mjs
 *   node tools/test_plugin_engine_parity.mjs --selftest   (beviser at den kan fejle)
 *
 * Opgave 43 porterede fem tjek fra `eucomply-scanner/engine/index.js` ind i
 * pluginen, så en WordPress-kunde får de samme ni URL-tjek som den gratis
 * scanner. Porten blev efterprøvet med `php -l` og med kilde/zip-pariteten — og
 * begge læser *koden*. Ingen af dem kørte et eneste tjek.
 *
 * Det er ikke en teoretisk fare. Første gang denne test kørte, fandt den en P0 i
 * pluginens egen kode: signatur-tabellen er positionsindekseret, `[navn, regex]`,
 * mens `matched_signatures()` læste `$sig['re']` og `$sig['name']`. Begge var
 * `null`, så `preg_match(null, …)` kørte med et tomt mønster, og de fire
 * signatur-baserede tjek — `consent_mode_v2`, `tcf`, `trackers`, `dora` — kunne
 * ikke finde noget på noget site. Pluginen sagde "No third-party trackers
 * detected" på en side med Google Analytics og Meta Pixel i markup'en, i en
 * rapport en betalende kunde sender videre til sin egen kunde.
 *
 * Derfor læser denne test ikke kode. Den kører begge motorer på de samme
 * fixtures og kræver samme dom. En forskel i regex-dialekt, i tærsklen eller i
 * en signatur, der bliver tilføjet i den ene motor og ikke i den anden, er rød
 * samme dag — i stedet for næste gang en kunde spørger hvorfor de to produkter
 * er uenige om deres egen hjemmeside.
 *
 * Ingen dependencies, intet netværk: fetch stubbes og målet er et IP-literal,
 * så assertPublicTarget ikke slår DNS op. PHP'en svarer fra en fixture gennem
 * `tools/plugin_probe.php`.
 */

import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { runScan } from "../eucomply-scanner/engine/index.js";

/** De fem tjek opgave 43 portede, med de nøgler run_checks() skriver. */
const SHARED = ["consent_mode_v2", "tcf", "trackers", "headers", "dora"];

/** Ét IP-literal: assertPublicTarget slår værter op i DNS, og gaten skal ikke kræve netværk. */
const TARGET = "https://93.184.216.34/";

const SECURE = {
  "content-security-policy": "default-src 'self'",
  "x-content-type-options": "nosniff",
  "referrer-policy": "strict-origin-when-cross-origin",
  "x-frame-options": "SAMEORIGIN",
};

/** Consent Mode v2 med alle seks signaturer. */
const CMV2_FULL = `
  <body class="google_consent_mode">
  <script>gtag('consent', 'default', { ad_storage: 'denied', analytics_storage: 'denied' });
  gtag('consent','update', { ad_storage: 'granted' });
  window.dataLayer = window.dataLayer || [];
  gtag('js', new Date()); gtag('config', 'G-1', { consent_mode: 'granted' });
  <script src="https://www.googletagmanager.com/gtm.js?id=GTM-1" async></script>
  <script src="https://www.googleadservices.com/pagead/conversion.js" async></script>
  </body>`;

const TCF_FULL = `
  <script>window.__tcfapi('addEventListener', 2);</script>
  <script>gdprApplies = true; tcfapi_v2 = "2.2"; IABConsent_String = "CPabc"; IABTCF_Session = "x";</script>`;

const DORA_FULL = `
  <p>SPF record, DKIM signing and a DMARC policy are published for this domain.
  Our incident response plan and business continuity documentation are public.</p>`;

const FIXTURES = [
  {
    name: "en side uden consent, trackere eller DORA-tekst",
    html: "<html><head><title>Shop</title></head><body><p>Velkommen</p></body></html>",
    headers: {},
  },
  {
    name: "en butik der har alt: consent mode, TCF, CMP og alle headere",
    html: `<html><head><title>Shop</title></head>${CMV2_FULL}${TCF_FULL}
      <script src="https://cdn.cookiebot.com/uc.js" async></script>${DORA_FULL}</body>`,
    headers: SECURE,
  },
  {
    name: "trackere uden consent-platform",
    html: `<html><body><script src="https://www.googletagmanager.com/gtm.js?id=GTM-1"></script>
      <script>fbq('init', '123')</script><script src="https://static.hotjar.com/x.js"></script></body></html>`,
    headers: SECURE,
  },
  {
    name: "ét signal i hver gruppe: advarsel, ikke bestået",
    html: `<html><body class="google_consent_mode"><script>window.__tcfapi('addEventListener', 2);</script>
      <p>Vi har en incident response plan.</p></body></html>`,
    headers: { "x-content-type-options": "nosniff" },
  },
  {
    name: "alle headere undtagen ét",
    html: "<html><body><p>Ingen trackere, ingen consent, ingen DORA-tekst</p></body></html>",
    headers: { ...SECURE, "referrer-policy": "" },
  },
  {
    name: "en side der ikke kan læses",
    // Kun PHP'en kan svare på denne: motoren har ingen tilsvarende sti, så den
    // håndhæves i PHP-casen nedenfor og ikke i paritetssammenligningen.
    phpOnly: true,
    html: "",
    error: "cURL error 28: Operation timed out after 10001 milliseconds",
  },
];

/** Kør pluginens fem tjek mod én fixture. */
function phpVerdicts(fixture) {
  const dir = mkdtempSync(join(tmpdir(), "eucomply-parity-"));
  const file = join(dir, "fixture.json");
  writeFileSync(
    file,
    JSON.stringify({ html: fixture.html || "", headers: fixture.headers || {}, error: fixture.error || "" })
  );
  const out = execFileSync("php", [join(import.meta.dirname, "plugin_probe.php"), file], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });
  return JSON.parse(out.trim().split("\n").pop());
}

/** Kør den universelle motor mod den samme fixture. */
async function engineVerdicts(fixture) {
  const saved = globalThis.fetch;
  globalThis.fetch = async () =>
    new Response(fixture.html || "", {
      status: 200,
      headers: { "Content-Type": "text/html", ...(fixture.headers || {}) },
    });
  try {
    return await runScan(TARGET);
  } finally {
    globalThis.fetch = saved;
  }
}

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

const fixtureParity = FIXTURES.filter((f) => !f.phpOnly);
const readable = FIXTURES.filter((f) => !f.error);

for (const fixture of fixtureParity) {
  await test(`samme dom: ${fixture.name}`, async () => {
    const php = phpVerdicts(fixture);
    const js = await engineVerdicts(fixture);
    for (const key of SHARED) {
      assert.ok(js.checks[key], `motoren kender ikke tjekket ${key}`);
      assert.equal(
        Boolean(php[key].pass),
        Boolean(js.checks[key].pass),
        `${key}: pluginen pass=${php[key].pass}, motoren pass=${js.checks[key].pass}`
      );
      assert.equal(
        Boolean(php[key].warn),
        Boolean(js.checks[key].warn),
        `${key}: pluginen warn=${php[key].warn}, motoren warn=${js.checks[key].warn}`
      );
    }
  });
}

await test("hver læsbar fixture giver de samme fund, ikke kun det samme dom", async () => {
  // Pass og warn kan være lige nok til at skjule en forsvunden signatur: to
  // fejlsynlige tjek kan begge være grønne. Fundene skal også være ens.
  const signalled = fixtureParity.filter((f) => f !== fixtureParity[0]);
  assert.ok(signalled.length >= 3, "fixtures skal dække fund, advarsel og fejl");
  let fixturesWithHits = 0;
  for (const fixture of signalled) {
    const php = phpVerdicts(fixture);
    const js = await engineVerdicts(fixture);
    const phpHit = /signals: ([^.]*)\./.exec(php.dora.detail || "") || /markup: ([^.]*)\./.exec(php.trackers.detail || "");
    const jsHit = /signals: ([^.]*)\./.exec(js.checks.dora.detail || "") || /markup: ([^.]*)\./.exec(js.checks.trackers.detail || "");
    const phpNames = phpHit ? phpHit[1].split(", ").length : 0;
    const jsNames = jsHit ? jsHit[1].split(", ").length : 0;
    assert.equal(phpNames, jsNames, `${fixture.name}: ${phpNames} fund i pluginen, ${jsNames} i motoren`);
    if (phpNames > 0) fixturesWithHits++;
  }
  assert.ok(fixturesWithHits >= 2, `kun ${fixturesWithHits} fixture(s) fandt noget — fundene prøves ikke af`);
});

await test("en forside der ikke kan læses er aldrig et bestået tjek", () => {
  const php = phpVerdicts(FIXTURES.find((f) => f.error));
  for (const key of SHARED) {
    assert.equal(Boolean(php[key].pass), false, `${key} blev bestået på en side der ikke kunne læses`);
    assert.equal(Boolean(php[key].warn), true, `${key} er hverken bestået eller advarsel på en ulæselig forside`);
  }
});

await test("de fem tjek henter forsiden én gang", () => {
  const php = phpVerdicts(FIXTURES[0]);
  assert.equal(php._fetches, 1, `forsiden blev hentet ${php._fetches} gange for fem tjek`);
});

await test("en ulæselig forside heller ikke hentes fem gange", () => {
  const php = phpVerdicts(FIXTURES.find((f) => f.error));
  assert.equal(php._fetches, 1, `forsiden blev hentet ${php._fetches} gange på en fejlet hentning`);
});

if (process.argv.includes("--selftest")) {
  // Beviser at porten kan fejle. Mutationen er lavet i hukommelsen: den
  // forventer, at PHP og motoren kan komme ud af takt på hver deres måde.
  const fixture = FIXTURES[1];
  const js = await engineVerdicts(fixture);
  const fake = { ...js.checks.dora, pass: !js.checks.dora.pass };
  const caught = [];
  try {
    assert.equal(Boolean(js.checks.dora.pass), Boolean(fake.pass), "dora: pluginen pass, motoren ikke");
  } catch {
    caught.push("dora");
  }
  const missing = { ...js.checks };
  delete missing.tcf;
  try {
    for (const key of SHARED) assert.ok(missing[key], `motoren kender ikke tjekket ${key}`);
  } catch {
    caught.push("nøgle");
  }
  if (caught.length !== 2) {
    failures.push(`selftest: forventede 2 negative cases fanget, fangede ${caught.length}`);
  } else {
    passed += 2;
  }
  void fixture;
}

if (failures.length) {
  for (const f of failures) console.error(`FAIL  ${f}`);
  console.error(`${failures.length} PLUGIN/MOTOR-PARITET FEJL`);
  process.exit(1);
}
console.log(
  `${passed} plugin/motor-paritetstest bestået — ${readable.length} læsbare fixtures, samme dom i begge motorer`
);
