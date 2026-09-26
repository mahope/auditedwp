/**
 * Étiketten skal have samme polaritet som dommen — i alle tre motorer.
 *
 *   node tools/check_verdict_labels.mjs
 *   node tools/check_verdict_labels.mjs --selftest   (beviser at den kan fejle)
 *
 * Baggrund. Opgave 45b fandt to checks, der skrev "Legal pages checked" på en
 * **rød** række. Opgave 48 fandt den spejlede fejl: en **grøn** række hvis
 * etiket *beskriver en mangel* ("No third-party trackers detected" på en side
 * uden trackere), altså en række der læses som et fund, selv om den er grøn.
 * Begge fejl lå i en betalt vare eller dens tragt, og ingen port dækkede
 * nogen af dem.
 *
 * Derfor er der her ÉN port for alle tre motorer — `shared/scan-engine.js`
 * (sitet), `eucomply-scanner/engine/index.js` (npm-pakken) og pluginens
 * `run_checks()` — frem for en port pr. motor. De tre er samme produkt i tre
 * indpakninger, så en regel der kun gælder den ene er en regel, der glider.
 *
 * Polaritet betyder her præcis tre statusser, fordi det er dem kunden ser:
 *
 *   ✓ pass  (pass=1, warn=0)  → må ikke begynde med en mangel
 *   ⚠ warn  (pass=1, warn=1)  → må gerne sige begge dele; det er hele pointen
 *   ✗ fail  (pass=0)          → må ikke begynde med en succes
 *
 * Advarselsrækken er bevidst **fri**. "HTTPS OK, no HSTS" begynder med en
 * succes og indeholder en mangel, og det er korrekt: den siger præcis det, der
 * er sandt. En port der greb den ville have tvunget os til at slå en sand
 * advarsel fra, så advarselsrækker er undtaget med vilje og skriftligt.
 *
 * Hvad der *ikke* er portet, og hvorfor: forskelle i formulering mellem de to
 * JS-motorer er ikke røde. Den npm-udgivne på markedet er 1.0.1 og en måned
 * bagen (se `tools/check_published_engine.mjs` og spørgsmål 13/17), så en
 * formulering mellem dem er et **drift-rapportspørgsmål**, ikke en fejl i
 * dette repo — samme stilling som opgave 37/38 tog til en rød port på et
 * publiceret produkt.
 *
 * Kilder: ingen af dem. `fetch` stubbes, målet er et IP-literal så
 * assertPublicTarget ikke slår DNS op, og pluginen svarer fra en fixture
 * gennem `tools/plugin_probe.php` — samme to kilder som
 * `tools/test_plugin_engine_parity.mjs`, og pluginens fixtures læses fra
 * `tools/test_plugin_checks.php --dump`, så der er ét sæt fixtures for
 * pluginen og ikke to.
 */

import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { dirname, join } from "node:path";

import { runScan as runScanShared } from "../shared/scan-engine.js";
import { runScan as runScanNpm } from "../eucomply-scanner/engine/index.js";

const HERE = dirname(new URL(import.meta.url).pathname);

/** Ét IP-literal: assertPublicTarget slår værter op i DNS, og gaten skal ikke kræve netværk. */
const TARGET_HTTPS = "https://93.184.216.34/";
const TARGET_HTTP = "http://93.184.216.34/";

/** De ni tjek motoren skriver. Rækkefølgen er koden, ikke os. */
const ENGINE_KEYS = [
  "consent_mode_v2",
  "tcf",
  "trackers",
  "ssl",
  "cookies",
  "forms",
  "legal",
  "headers",
  "dora",
];

const SECURE = {
  "content-security-policy": "default-src 'self'",
  "x-content-type-options": "nosniff",
  "referrer-policy": "strict-origin-when-cross-origin",
  "x-frame-options": "SAMEORIGIN",
  "strict-transport-security": "max-age=31536000",
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
  <p>SPF-record, DKIM signing, DMARC-record, incident-response plan, business-continuity and a status-page are published.</p>`;

const LEGAL_LINKS = `
  <a href="/privacy">Privacy</a><a href="/imprint">Imprint</a><a href="/accessibility">Accessibility</a>`;

/**
 * Fixtures der hver især danner en fejlklasse. De er skrevet *efter*
 * signaturerne, ikke efter forventningen: de fire af ni DORA-markører kræver en
 * bindestreg eller underscore i løbet (se opgave 45), så "SPF record" med et
 * mellemrum matcher ikke `spf[_-]?record`.
 */
const FIXTURES = [
  {
    name: "en side hvor alt er i orden",
    target: TARGET_HTTPS,
    html: `<html><head><title>Shop</title></head>${CMV2_FULL}${TCF_FULL}
      <script src="https://cdn.cookiebot.com/uc.js" async></script>${DORA_FULL}
      ${LEGAL_LINKS}</body>`,
    headers: SECURE,
  },
  {
    name: "en side der hverken har consent, trackere, DORA eller headere",
    target: TARGET_HTTPS,
    html: "<html><head><title>Shop</title></head><body><p>Velkommen</p></body></html>",
    headers: {},
  },
  {
    name: "trackere uden consent-platform",
    target: TARGET_HTTPS,
    html: `<html><body><script src="https://www.googletagmanager.com/gtm.js?id=GTM-1"></script>
      <script>fbq('init', '123')</script><script src="https://static.hotjar.com/x.js"></script></body></html>`,
    headers: SECURE,
  },
  {
    name: "ét signal i hver gruppe: advarsel, ikke bestået",
    target: TARGET_HTTPS,
    html: `<html><body class="google_consent_mode"><script>window.__tcfapi('addEventListener', 2);</script>
      <p>Vi har en incident response plan.</p>${LEGAL_LINKS}</body>`,
    headers: { "x-content-type-options": "nosniff" },
  },
  {
    name: "en side over http",
    target: TARGET_HTTP,
    html: `<html><body>${LEGAL_LINKS}</body></html>`,
    headers: SECURE,
  },
  {
    name: "en form uden privatlivslink",
    target: TARGET_HTTPS,
    html: '<html><body><form action="/kontakt"><input name="navn"></form></body></html>',
    headers: SECURE,
  },
  {
    name: "en form med privatlivslink",
    target: TARGET_HTTPS,
    html: '<html><body><a href="/privacy">Privacy</a><form action="/kontakt"><input name="navn"></form></body></html>',
    headers: SECURE,
  },
];

/** Kør én motor mod én fixture med fetch stubbet. */
async function engineVerdicts(runScan, fixture) {
  const saved = globalThis.fetch;
  let finalUrl = fixture.target;
  globalThis.fetch = async (input) => {
    // Redirects følges manuelt i safeFetch(), så svaret skal kunne læses to
    // gange: en gang af læseren og en gang af runScan selv.
    const body = fixture.html || "";
    return new Response(body, {
      status: 200,
      headers: { "Content-Type": "text/html", ...(fixture.headers || {}) },
    });
  };
  try {
    return await runScan(fixture.target);
  } finally {
    globalThis.fetch = saved;
    void finalUrl;
  }
}

/** Læs pluginens måling fra dens egen harness, så fixtures ikke findes to steder. */
function pluginObservations() {
  const raw = execFileSync(
    "php",
    [join(HERE, "test_plugin_checks.php"), "--dump"],
    { encoding: "utf8", stdio: ["ignore", "pipe", "inherit"], maxBuffer: 8 * 1024 * 1024 }
  );
  const parsed = JSON.parse(raw.trim().split("\n").pop());
  assert.ok(Array.isArray(parsed.observations) && parsed.observations.length > 0, "plugin-dumpen er tom");
  return parsed;
}

// ── Reglerne ──────────────────────────────────────────────────────────────────

/**
 * Mangelord i en etiket på en grøn række — **hele** etiketten, ikke kun
 * begyndelsen.
 *
 * Begyndelsen var for lidt, og det viste en mutation mod repoets egen fil:
 * den genskabte opgave 48s døde beståelses-sti i `forms`, så en grøn række fik
 * etiketten *"Form(s) found, **no** privacy-policy link"* —negationen lå i
 * sætningens anden halvdel, og porten var grøn. Det er præcis den fejlklasse
 * porten findes til, så den skal kunne se den.
 *
 * Derfor er reglen: en grøn række må **ikke** indeholde et mangelord. Det er
 * strammere end det lyder, og det er med vilje — en etiket uden mangelord kan
 * ikke være polaritets-ambigu, så ingen fremtidig forgrening kan stikke den
 * forkerede sætning ind i den. De to grønne etiketter, det kostede, er skrevet
 * om til den positive form ("neither … nor", "Nothing for this check to
 * review") i stedet for slået fra som undtagelse.
 *
 * `detail` er **ikke** med i denne regel, og det er ikke en forglemelse:
 * DORA's grønne række siger "This is not a DORA assessment" i detaljen, og det
 * er en forbeholdssætning om tjekket — ikke et fund på sitet. At slette den
 * ville være præcis den fejl opgave 45 rettede på fire hovedsider. Etiketten er
 * dommens plads; detaljen er forklaringen, og den skal kunne sige hvad der ikke
 * blev fundet.
 */
const DEFICIENCY = /\b(no|not|without|missing|absent|lacks?|failed|unable|cannot|unconfigured|unset)\b/i;

/**
 * Succesord i **begyndelsen** af en etiket på en rød række. Spejlen af 45b.
 */
const SUCCESS_LEAD = /^(ok|all|pass(ed)?|clean|present|active|detected|verified|checked|reviewed|compliant|secure|enabled|up to date|found)\b/i;

/**
 * Og *midt i* en rød række: et ord om en handling, der er udført. Det er ikke
 * en vilkårlig stramning — det er præcis det opgave 45b fandt, da "Legal pages
 * checked" stod på en rød række, og det er dets egne tre ord. "Alt udført" i en
 * sætning, der dømmer en række fejlet, er en påstand om noget der skete, og det
 * skete ikke.
 *
 * Kun disse tre, og ikke "found"/"detected": en kvalificeret sætning som
 * "Form plugins found, no Privacy Policy page" er sand på begge dele, og den
 * skal kunne stå. Det er forskellen på en ubetinget positiv dom og en
 * opregning — samme forskel som DEFICIENCY kun læser i begyndelsen.
 */
const SUCCESS_MID = /\b(checked|reviewed|verified)\b/i;

/** Etiketten, så den kan læses: emoji, ikoner og mellemrum er ikke dommen. */
function bare(text) {
  return String(text || "")
    .replace(/^[\s\p{Extended_Pictographic}·•\-–—:>]+/u, "")
    .trim();
}

/** Dommen i den række, kunden ser. */
export function statusOf(observation) {
  if (!observation.pass) return "fail";
  return observation.warn ? "warn" : "pass";
}

/**
 * Fundene for én motor. Ét datasæt, så selftesten og porten ikke kan have hver
 * sin fortolkning af "mangler".
 */
export function findings(observations) {
  const out = [];
  const labels = new Map();
  // Én observation pr. fixture pr. check, så den samme fejl tælles en gang pr.
  // motor-tjek-par og ikke en gang pr. fixture. Uden det er en port der *kan*
  // fejle, men hvis output er 15 linjer om én skrivefejl — altså umulig at læse
  // på den måde, den skal bruges.
  const seen = new Set();
  const push = (o, finding) => {
    const id = [o.engine, o.key, finding.status, finding.label, finding.rule].join("|");
    if (seen.has(id)) return;
    seen.add(id);
    out.push({ engine: o.engine, key: o.key, ...finding });
  };
  for (const o of observations) {
    const status = statusOf(o);
    const label = bare(o.label);
    if (!label) {
      push(o, { status, label: o.label, rule: "tom-etiket", text: "rækken har ingen etiket" });
      continue;
    }
    if (status === "pass" && DEFICIENCY.test(label)) {
      push(o, {
        status,
        label: o.label,
        rule: "gron-række-begynder-med-mangel",
        text: `bestået uden advarsel, men etiketten begynder med "${label.split(/\s+/)[0]}"`,
      });
    }
    if (status === "fail" && (SUCCESS_LEAD.test(label) || SUCCESS_MID.test(label))) {
      push(o, {
        status,
        label: o.label,
        rule: "rod-række-begynder-med-succes",
        text: SUCCESS_LEAD.test(label)
          ? `fejlet, men etiketten begynder med "${label.split(/\s+/)[0]}"`
          : "fejlet, men etiketten påstår at noget blev tjekket/gennemgået/verificeret",
      });
    }
    const perKey = labels.get(o.key) || new Set();
    perKey.add(label);
    labels.set(o.key, perKey);
  }
  // Samme sætning på begge domme er opgave 45b i dens anden form: rækken kan
  // ikke læses uden at vide hvilken kolonne man kigger i.
  //
  // Én fund pr. motor, ikke ét pr. nøgle: den første motor der udløser regelen
  // må ikke æde de andres, ellers svarer porten "1 fund" om en fejl der ligger i
  // to filer — og en læser der retter den ene tror den anden er grøn.
  for (const [key] of labels) {
    const seenHere = new Set();
    for (const engine of new Set(observations.map((o) => o.engine))) {
      const pass = new Set(
        observations.filter((o) => o.engine === engine && o.key === key && statusOf(o) === "pass").map((o) => bare(o.label))
      );
      const fail = new Set(
        observations.filter((o) => o.engine === engine && o.key === key && statusOf(o) === "fail").map((o) => bare(o.label))
      );
      for (const shared of pass) {
        if (!fail.has(shared)) continue;
        const id = [engine, key, shared].join("|");
        if (seenHere.has(id)) continue;
        seenHere.add(id);
        const sample = observations.find((o) => o.engine === engine && o.key === key && bare(o.label) === shared) || {};
        push(sample, {
          status: "delt",
          label: shared,
          rule: "samme-etiket-på-begge-domme",
          text: "står på en bestået og på en fejlende række",
        });
      }
    }
  }
  return out;
}

// ─--selftest: bevis at porten kan fejle ───────────────────────────────────────

async function selftest() {
  let passed = 0;
  const failures = [];
  const t = async (name, fn) => {
    try {
      await fn();
      passed++;
    } catch (e) {
      failures.push(`${name}: ${e && e.message}`);
    }
  };

  const O = (label, pass, warn = false, key = "ssl") => ({ key, label, pass, warn });

  await t("en grøn række der begynder med No er rød", () => {
    assert.equal(findings([O("No third-party trackers detected", true, false, "trackers")]).length, 1);
  });
  await t("en grøn række der begynder med Not er rød", () => {
    assert.equal(findings([O("Not HTTPS", true, false)]).length, 1);
  });
  await t("en grøn række der begynder med 'All' er grøn", () => {
    assert.equal(findings([O("All common security headers present", true, false, "headers")]).length, 0);
  });
  await t("en rød række der begynder med 'All' er rød", () => {
    assert.equal(findings([O("All up to date", false, false, "plugins")]).length, 1);
  });
  await t("en rød række der begynder med 'Detected' er rød", () => {
    assert.equal(findings([O("Detected 6 DORA page signals", false, false, "dora")]).length, 1);
  });
  await t("'checked' midt i en rød række er rød — det er 45b's fejl", () => {
    assert.equal(findings([O("Legal pages checked", false, false, "legal")]).length, 1);
  });
  await t("en kvalificeret rød række må opregne hvad den fandt", () => {
    assert.equal(findings([O("Form plugins found, no Privacy Policy page", false, false, "forms")]).length, 0);
  });
  await t("'reviewed' og 'verified' midt i en rød række er også røde", () => {
    assert.equal(findings([O("Forms reviewed", false, false, "forms")]).length, 1);
    assert.equal(findings([O("Consent state verified", false, false, "cookies")]).length, 1);
  });
  await t("en advarselsrække må sige begge dele", () => {
    assert.equal(findings([O("HTTPS OK, no HSTS", true, true)]).length, 0);
  });
  await t("forbehold i detaljen er ikke et fund — porten læser kun etiketten", () => {
    // DORA's grønne række siger "This is not a DORA assessment" i DETAILJEN.
    // Det er en forbeholdssætning om tjekket, ikke et fund på sitet, og en
    // regel der greb den ville have tvunget os til at slette en disclaimer.
    const withDetail = {
      key: "dora",
      label: "DORA-related page signals: 6 found",
      pass: true,
      warn: false,
      detail: "Page-text markers found: SPF record, DKIM. This is not a DORA assessment.",
    };
    assert.equal(findings([withDetail]).length, 0);
  });
  await t("et mangelord midt i en grøn etiket ER et fund — det er 48's fejl", () => {
    const mutation = { key: "forms", label: "Form(s) found, no privacy-policy link", pass: true, warn: false };
    assert.equal(findings([mutation]).length, 1);
  });
  await t("samme etiket på begge domme er rød", () => {
    const both = [O("Legal pages checked", true), O("Legal pages checked", false)];
    assert.equal(findings(both).filter((f) => f.rule === "samme-etiket-på-begge-domme").length, 1);
  });
  await t("en tom etiket er rød — en række uden tekst er ikke et dom", () => {
    assert.equal(findings([O("", true)]).length, 1);
  });
  await t("et ikon foran etiketten skjul ikke dommen", () => {
    assert.equal(findings([O("🔒 No backup plugin", true, false, "backups")]).length, 1);
  });
  await t("dommen følger pass/warn, ikke ordet i etiketten", () => {
    assert.equal(statusOf({ pass: true, warn: true }), "warn");
    assert.equal(statusOf({ pass: true, warn: false }), "pass");
    assert.equal(statusOf({ pass: false, warn: true }), "fail");
  });

  // Målingen skal se alle ni motortjek og alle elleve plugin-tjek, ellers er en
  // grøn udgang betydningsløs.
  await t("målingen dækker de ni motortjek", async () => {
    const seen = new Set();
    for (const fixture of FIXTURES) {
      const res = await engineVerdicts(runScanShared, fixture);
      for (const key of ENGINE_KEYS) if (res.checks[key]) seen.add(key);
    }
    assert.equal(seen.size, 9, `kun ${seen.size}/9: ${[...seen].join(", ")}`);
  });
  await t("målingen ser elleve plugin-tjek", () => {
    assert.equal(pluginObservations().keys.length, 11);
  });

  if (failures.length) {
    console.error(`SELFTEST RØD — ${failures.length} af ${passed + failures.length} cases fejlede`);
    for (const f of failures) console.error(`  ${f}`);
    process.exit(1);
  }
  console.log(`SELFTEST GRØN — alle ${passed} negative cases fanges`);
}

// ── Kørslen ───────────────────────────────────────────────────────────────────

if (process.argv.includes("--selftest")) {
  await selftest();
  process.exit(0);
}

const all = [];
for (const [name, runScan] of [
  ["shared/scan-engine.js", runScanShared],
  ["eucomply-scanner/engine/index.js", runScanNpm],
]) {
  let seen = 0;
  for (const fixture of FIXTURES) {
    const res = await engineVerdicts(runScan, fixture);
    for (const key of ENGINE_KEYS) {
      const c = res.checks[key];
      if (!c) continue;
      seen++;
      all.push({
        engine: name,
        fixture: fixture.name,
        key,
        label: c.label,
        pass: Boolean(c.pass),
        warn: Boolean(c.warn),
      });
    }
  }
  console.log(`OK    ${name}: ${seen} domme over ${FIXTURES.length} fixtures`);
  if (seen < ENGINE_KEYS.length) {
    console.error(`FEJL  ${name} gav kun ${seen} domme for ${ENGINE_KEYS.length} tjek — porten så ikke alt`);
    process.exit(1);
  }
}

const plugin = pluginObservations();
for (const o of plugin.observations) {
  all.push({ engine: "plugin/eucomply.php", fixture: o.fixture, key: o.key, label: o.label, pass: o.pass, warn: o.warn });
}
console.log(`OK    plugin/eucomply.php: ${plugin.observations.length} domme over ${plugin.keys.length} tjek`);

const found = findings(all);
if (found.length) {
  console.error(`\n${found.length} fund: en etiket har ikke samme polaritet som sit dom\n`);
  for (const f of found) {
    console.error(`  ${f.engine}  ${f.key}  [${f.status}]  "${f.label}"`);
    console.error(`      ${f.rule}: ${f.text}`);
  }
  process.exit(1);
}
console.log(`OK    ${all.length} domme i tre motorer: ingen etiket modsiger sit eget dom`);
