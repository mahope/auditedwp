/**
 * Tæller et juridisk dokument kun, når siden **linker** det?
 *
 *   node tools/check_legal_links.mjs
 *   node tools/check_legal_links.mjs --selftest   (beviser at den kan fejle)
 *
 * Opgave 56. `PRIVACY_LINK_SIGNATURE` og de sytten andre mønstre i
 * `LEGAL_PATTERNS` læste **hele HTML'en**. Målingen i denne iteration fandt
 * **22 falske fund på fire rene prosa-sider** — sider med en indledning og
 * nul links i foden:
 *
 *   DA  6   Imprint, Cookie policy, Shipping, DPA, Acceptable use, Environmental
 *   SV  8   Privacy, Imprint, Cookie, Returns, Shipping, DPA, Acceptable use, Env.
 *   NL  7   Imprint, Cookie, Returns, Shipping, DPA, Acceptable use, Env.
 *   EN  1   Privacy  (fra `gdpr` i "Read our GDPR documentation")
 *
 * Det er ikke en manglende etiket, det er en **falsk beståelse**: `legal`
 * kræver to dokumenter, så en side med seks af slags ord i en indledning fik
 * grønt med nul links. Og i `forms` var det værre — en formularside der
 * *beskriver* sin behandling ("vi behandler persondata i denne formular") fik
 * "privacy-policy link **detected**" og `pass = true`. Det er præcis det
 * tabte række-tal opgave 50handlede om, i modsat retning.
 *
 * Rettelsen er ikke en bredere eller smallere regex. Den er **beholderen**:
 * mønstrene prøves mod sidens `<a>`-elementer, åbnings-tagget med `href` og
 * den synlige tekst indeni. Ordene er uændrede, så opgave 51/52/54/55s sprog
 * dækning er bevaret — det er den afgørende prøve, R2.
 *
 * Fem kontrakter, alle egenskaber ved adfærden:
 *
 *   R1  **En sætning er ikke en juridisk side.** Mindst tre sprog, hvert med
 *       en prosa-fixture der bruger de juridiske ord i løbende tekst. Begge
 *       motorer skal finde **nul** dokumenter — ikke ét, nul.
 *   R2  **Ingen tabt dækning.** Den samme side som i R1, med præcis de samme
 *       dokumenter som **links**, skal stadig finde dem, i alle tre sprog. R1
 *       alene kan ikke se det: en for bred beskæring består R1 og tager
 *       point fra kunden, og det er den vej denne fejl kommer tilbage ad.
 *   R3  **De to motorer er samme produkt.** Identisk `pass`, `warn`, `label`
 *       og `detail` på hver fixture.
 *   R4  **Pluginen gør det samme.** Den har sit eget `html_links_privacy()`,
 *       fordi `legal` der slår WordPress-sider op i stedet for at læse markup.
 *       Kørt gennem `tools/plugin_probe.php` på de samme fixtures.
 *   R5  **`forms` følger samme regel.** En formular uden link fejler, en
 *       formular med link består, i alle tre produkter. Det er den række der
 *       lå og sagde "detected" på en side uden et link.
 *
 * Selftesten muterer **repoets egne filer**: hver af de to motorer og pluginen
 * får sin matcher til at læse hele HTML'en igen, og porten skal blive rød på
 * en prosa-fixture. Uden mutationer er porten en påstand — samme fejlklasse
 * som opgave 45 fund 2 og opgave 50 fund 1.
 *
 * Hvad porten **ikke** dækker: `find_page_by_title`-mekanismen fra opgave 53.
 * Den slår WordPress-sider op efter sti og titel og røres ikke her; dens egen
 * sprogtest er `tools/check_legal_pages_langs.php`.
 *
 * Spec: `docs/eucomply-juridiske-links.md`.
 */

import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

import { runScan as runPublishedScan } from "../eucomply-scanner/engine/index.js";
import { runScan as runSharedScan } from "../shared/scan-engine.js";

const REPO = join(import.meta.dirname, "..");
const ENGINES = [
  ["motoren i repoet", join(REPO, "shared", "scan-engine.js"), runSharedScan],
  ["den publicerede motor", join(REPO, "eucomply-scanner", "engine", "index.js"), runPublishedScan],
];
const PLUGIN = join(REPO, "plugin", "eucomply.php");
const PROBE = join(REPO, "tools", "plugin_probe.php");

/** Ét IP-literal: assertPublicTarget slår værter op i DNS, og porten skal ikke kræve netværk. */
const TARGET = "https://93.184.216.34/";

/** Samme tre sprog som opgave 52-55, plus engelsk fordi fejlen ikke var et sprogproblem. */
const SPROG = { DA: "dansk", SV: "svensk", NL: "nederlandsk", EN: "engelsk" };

/**
 * Fixtures. R1 og R2 er **par**: hver prosa-fixture har en tvilling der har de
 * præcis samme dokumenter som links. Uden parret kan en for bred beskæring
 * bestå R1 og tage point fra kunden, og det er den vej fejlen kommer tilbage ad.
 */
const PROSA = {
  DA: "Vores virksomhedsoplysninger, cookiepolitik, retur- og forbrugerrettigheder, "
    + "fragt og levering, databehandleraftale, acceptabel brug og bæredygtighedspolitik "
    + "er alle opdateret i år, og vi behandler persondata i denne formular.",
  SV: "Våra bolagsuppgifter, kakpolicy, retur och ångerrätt, frakt och leverans, "
    + "biträdesavtal för personuppgifter, rimlig användning och hållbarhetspolicy är alla "
    + "uppdaterade i år, och vi behandlar personuppgifter i den här formuläret.",
  NL: "Onze bedrijfsgegevens, cookiesbeleid, retourbeleid, verzendbeleid, "
    + "verwerkersovereenkomst, redelijk gebruik en duurzaamheidsbeleid zijn dit jaar "
    + "bijgewerkt, en we verwerken persoonsgegevens in dit formulier.",
  // Beviset på at fejlen ikke var et sprogproblem: `gdpr` matcher engelsk prosa
  // lige såvel som dansk `persondata`, så en bredere sprogliste ville ikke have
  // løst den — kun beholderen gør det.
  EN: "Our data protection, cookie policy, refund policy, shipping policy, acceptable "
    + "use and privacy documentation were all updated this year. Read our GDPR "
    + "documentation before you publish.",
};

/** De samme dokumenter som links, i hvert sprog. R2 påstår de stadig findes. */
const LINKS = {
  DA: [["https://da.example/om-os/", "Om os"], ["https://da.example/privatlivspolitik/", "Privatlivspolitik"],
    ["https://da.example/handelsbetingelser/", "Handelsbetingelser"], ["https://da.example/cookiepolitik/", "Cookiepolitik"],
    ["https://da.example/fragt-og-levering/", "Fragt og levering"]],
  SV: [["https://sv.example/om-oss/", "Om oss"], ["https://sv.example/integritetsskydd/", "Integritetsskydd"],
    ["https://sv.example/allmanna-villkor", "Allmänna villkor"], ["https://sv.example/kakpolicy", "Kakpolicy"],
    ["https://sv.example/frakt-och-leverans/", "Frakt och leverans"]],
  NL: [["https://nl.example/colofon/", "Colofon"], ["https://nl.example/persoonsgegevens/", "Persoonsgegevens"],
    ["https://nl.example/algemene-voorwaarden/", "Algemene voorwaarden"], ["https://nl.example/cookiesbeleid/", "Cookiesbeleid"],
    ["https://nl.example/verzendbeleid/", "Verzendbeleid"]],
  EN: [["https://en.example/imprint/", "Imprint"], ["https://en.example/privacy/", "Privacy Policy"],
    ["https://en.example/terms/", "Terms of Service"], ["https://en.example/cookie-policy/", "Cookie Policy"]],
};

/**
 * Alle fire dokumenter hver sprogs fixture linker. R2 påstår de stadig findes.
 *
 * Listen er de fire `LEGAL_PATTERNS` der er i opgave 51-55s kerne, **ikke**
 * alle atten: en R2 der krævede alle atten ville kræve en fixture med atten
 * links i hvert sprog, og den ville være så lang at den læse som en påstand
 * frem for en måling. Fire er nok til at bevise at rettelsen ikke har taget
 * dækning, fordi de dækker alle fire *mekanismer*: ord i href'en, ord i
 * linkteksten, accenter i begge og et mønster uden skilletegn.
 */
const ALLE_DOKUMENTER = [
  "Privacy / GDPR", "Imprint / Legal notice", "Cookie policy", "Terms & Conditions",
];

function side({ prosa = null, links = null, form = false } = {}) {
  const indhold = [];
  if (prosa) indhold.push(`<h1>Om os</h1><p>${prosa}</p>`);
  if (form) indhold.push('<form action="/kontakt" method="post"><input name="email" type="email"></form>');
  if (links) indhold.push(`<footer>${links.map(([href, t]) => `<a href="${href}">${t}</a>`).join("")}</footer>`);
  return `<html><body><main>${indhold.join("")}</main></body></html>`;
}

const FIXTURES = [];
for (const lang of Object.keys(PROSA)) {
  FIXTURES.push({ lang, kind: "prosa", form: false, html: side({ prosa: PROSA[lang] }) });
  FIXTURES.push({ lang, kind: "links", form: false, html: side({ links: LINKS[lang] }) });
  // R5: samme par med en formular, fordi det er `forms` der lå.
  FIXTURES.push({ lang, kind: "prosa+formular", form: true, html: side({ prosa: PROSA[lang], form: true }) });
  FIXTURES.push({ lang, kind: "links+formular", form: true, html: side({ links: LINKS[lang], form: true }) });
}

// ── Kør en motor mod én fixture ──────────────────────────────────────────────

async function engineVerdict(runScan, fixture) {
  const saved = globalThis.fetch;
  globalThis.fetch = async () =>
    new Response(fixture.html || "", { status: 200, headers: { "Content-Type": "text/html" } });
  try {
    const scan = await runScan(TARGET);
    assert.ok(scan.checks.legal, "motoren kender ikke tjekket legal");
    assert.ok(scan.checks.forms, "motoren kender ikke tjekket forms");
    return scan.checks;
  } finally {
    globalThis.fetch = saved;
  }
}

/** Hvilke juridiske dokumenter dommen tæller. Læst ud af `detail` — den tekst kunden læser. */
function foundNames(verdict) {
  const m = /Found on page: (.+?)\.$/.exec((verdict && verdict.detail) || "");
  if (!m) return [];
  return m[1].split(", ").map((s) => s.trim());
}

/**
 * Dommen for ét tjek pr. motor.
 *
 * `verdicts` er [hvem, checks]-par, og **`checks` er ikke `checks.legal`**. En
 * port der læser `.detail` på hele objektet ser `undefined`, og en påstand om
 * nul fund på prosa bliver grøn af den grund. Det gjorde den i denne fil's
 * første udformning, og R1 fangede det ikke — R1 krævede nul fund, og
 * `undefined` gav nul fund. R2 fandt det, fordi den kræver fund.
 */
function legalVerdicts(verdicts) {
  return verdicts.map(([hvem, checks]) => {
    assert.ok(checks.legal, `${hvem} kender ikke tjekket legal`);
    return [hvem, checks.legal];
  });
}

/** Kør pluginen på én fixture gennem proben, dens ene sandhed om hvad WordPress gør. */
function pluginVerdict(fixture) {
  const dir = mkdtempSync(join(tmpdir(), "eucomply-links-"));
  const file = join(dir, "fixture.json");
  try {
    writeFileSync(file, JSON.stringify({ html: fixture.html }));
    const out = execFileSync("php", [PROBE, file, "forms"], { encoding: "utf8", stdio: ["ignore", "pipe", "inherit"] });
    const parsed = JSON.parse(out);
    return parsed.forms;
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

// ── Kontrakterne. Porten OG selftesten kalder disse, så en negativ case ikke
// kan blive grøn ved at forvente noget andet end det porten kræver.

/** R1: en sætning er ikke en juridisk side. Nul, ikke "færre". */
function contractR1(verdicts, fixture) {
  for (const [hvem, v] of verdicts) {
    const fundne = foundNames(v);
    assert.equal(
      fundne.length,
      0,
      `${hvem} tæller ${fundne.join(", ")} på «${fixture.kind}» i ${SPROG[fixture.lang]} prosa — ` +
        `en sætning i løbende tekst er ikke et link`
    );
    assert.equal(
      Boolean(v.pass),
      false,
      `${hvem} består (${v.label}) på «${fixture.kind}» i ${SPROG[fixture.lang]} prosa`
    );
  }
}

/** R2: de samme dokumenter som links er stadig fundet. Ingen tabt dækning. */
function contractR2(verdicts, fixture) {
  for (const [hvem, v] of verdicts) {
    const fundne = foundNames(v);
    for (const dokument of ALLE_DOKUMENTER) {
      assert.ok(
        fundne.includes(dokument),
        `${hvem} finder ikke «${dokument}» på en ${SPROG[fixture.lang]} side der linker det ` +
          `(rapporten siger: "${v.detail}") — rettelsen har taget dækning fra kunden`
      );
    }
    assert.equal(
      Boolean(v.pass),
      true,
      `${hvem} består ikke (${v.label}) på en ${SPROG[fixture.lang]} side med fire juridiske links`
    );
  }
}

/** R3: de to motorer er samme produkt. */
function contractR3(verdicts) {
  // `verdicts` er [hvem, dom]-par, så dommen er indeks 1. Destrukturerer man kun
  // det ydre par, sammenligner man `undefined` med `undefined` — og regelen er
  // grøn for enhver afvigelse. Det gjorde den i opgave 52.
  const [, a] = verdicts[0];
  const [, b] = verdicts[1];
  assert.equal(Boolean(b.pass), Boolean(a.pass), `de to motorer er uenige: «${a.label}» mod «${b.label}»`);
  assert.equal(b.detail, a.detail, `samme dom, to rapporter: «${a.detail}» mod «${b.detail}»`);
}

/**
 * R4: pluginen gør det samme som motorerne på det samme input.
 *
 * Kun på **formular**-fixtures, og det er ikke en bekvemmelighed: pluginens
 * `forms` går tidligt tilbage med *"Nothing for this check to review"* på en
 * side uden formular, fordi der så intet er at se på. At kræve en fejl derfra
 * ville være at kræve en fejl, pluginen med rette ikke giver. Den del af dens
 * dom, der kan sammenlignes med motorerne, er privatlivslinjen — og den læses
 * på en side med en formular.
 */
function contractR4(verdicts, fixture, plugin) {
  if (!fixture.form) {
    assert.equal(
      /Nothing for this check to review/i.test(plugin.label || ""),
      true,
      `pluginen svarer «${plugin.label}» på «${fixture.kind}» i ${SPROG[fixture.lang]} — ` +
        `siden har ingen formular, så der skal intet se på`
    );
    return;
  }
  const [, motor] = verdicts[0];
  if (fixture.kind.startsWith("prosa")) {
    assert.equal(
      Boolean(plugin.pass),
      false,
      `pluginen består (${plugin.label}) på en ${SPROG[fixture.lang]} formular der kun beskriver sin behandling`
    );
  } else {
    assert.equal(
      Boolean(plugin.pass),
      true,
      `pluginen består ikke (${plugin.label}) på en ${SPROG[fixture.lang]} formular med privatlivslink ved siden af`
    );
  }
  // Og den skal være enige med motoren om privatlivslinjen, fordi det er den
  // del af dommen de to produkter har til fælles.
  const motorHarLink = Boolean(motor.forms.pass);
  const pluginHarLink = /privacy-policy link found/i.test(plugin.label || "");
  assert.equal(
    pluginHarLink,
    motorHarLink,
    `pluginen og motoren er uenige om privatlivslinket på «${fixture.kind}» i ${SPROG[fixture.lang]}: ` +
      `«${plugin.label}» mod «${motor.forms.label}»`
  );
}

/** R5: `forms` følger samme regel. Den række lå og sagde "detected" på prosa. */
function contractR5(verdicts, fixture, plugin) {
  for (const [hvem, checks] of verdicts) {
    assert.ok(checks.forms, `${hvem} kender ikke tjekket forms`);
    const forms = checks.forms;
    if (!fixture.form) continue;
    if (fixture.kind.startsWith("prosa")) {
      assert.equal(
        Boolean(forms.pass),
        false,
        `${hvem} består (${forms.label}) på en formular der kun beskriver sin behandling`
      );
    } else {
      assert.equal(
        Boolean(forms.pass),
        true,
        `${hvem} består ikke (${forms.label}) på en formular med et privatlivslink ved siden af`
      );
    }
  }
  if (fixture.form && fixture.kind.startsWith("prosa")) {
    assert.equal(
      Boolean(plugin.pass),
      false,
      `pluginen består (${plugin.label}) på en formular der kun beskriver sin behandling`
    );
  }
}

// ── Kør porten ───────────────────────────────────────────────────────────────

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

for (const fixture of FIXTURES) {
  const vs = [];
  for (const [hvem, , runScan] of ENGINES) vs.push([hvem, await engineVerdict(runScan, fixture)]);
  fixture.verdicts = vs;
  fixture.plugin = pluginVerdict(fixture);

  const navn = `${fixture.kind} (${SPROG[fixture.lang]})`;
  const legalVs = legalVerdicts(vs);
  if (fixture.kind.startsWith("prosa")) {
    await test(`R1 en sætning er ikke et juridisk link: ${navn}`, () => contractR1(legalVs, fixture));
  } else {
    await test(`R2 intet dæknings tab: ${navn}`, () => contractR2(legalVs, fixture));
  }
  await test(`R3 de to motorer er ens: ${navn}`, () => contractR3(legalVs));
  await test(`R4 pluginen gør det samme: ${navn}`, () => contractR4(vs, fixture, fixture.plugin));
  if (fixture.form) {
    await test(`R5 forms følger samme regel: ${navn}`, () => contractR5(vs, fixture, fixture.plugin));
  }
}

console.log(
  `${passed} juridisk-linktest bestået — ${FIXTURES.length} fixtures i ${Object.keys(PROSA).length} sprog, ` +
    `${Object.keys(PROSA).length - 1} prosa-sprog målt, 3 produkter`
);

if (failures.length) {
  for (const f of failures) console.error(`FEJL  ${f}`);
  process.exit(1);
}

// ── Selftest: bevis at porten kan fejle ──────────────────────────────────────

if (process.argv.includes("--selftest")) {
  const caught = [];
  const expectRed = (name, contract, ...args) => {
    try {
      contract(...args);
      failures.push(`selftest: ${name} gav en grøn port — den kan ikke se den fejl`);
    } catch {
      caught.push(name);
    }
  };

  const prosa = FIXTURES.find((f) => f.kind === "prosa" && f.lang === "NL");
  const links = FIXTURES.find((f) => f.kind === "links" && f.lang === "NL");

  // 1. R1: en motor tæller prosa igen — præcis fejlen denne opgave retter.
  expectRed("R1 (prosa fundet igen)", contractR1, [
    ["motoren i repoet", { pass: true, label: "8 legal pages linked", detail: "Found on page: Privacy / GDPR, Imprint / Legal notice, Cookie policy, Terms & Conditions." }],
  ], prosa);

  // 2. R1: fund på prosa, men dommen siger "No legal pages linked". R1 skal
  //    kunne se det — ellers ville en værre motor glide igennem.
  expectRed("R1 (etiket modsiger fundet)", contractR1, [
    ["motoren i repoet", { pass: false, label: "No legal pages linked", detail: "Found on page: Privacy / GDPR." }],
  ], prosa);

  // 3. R2: rettelsen har taget dækning — rettelsen skal kunne ses.
  expectRed("R2 (dækning tabt)", contractR2, [
    ["motoren i repoet", { pass: false, label: "2 legal pages linked", detail: "Found on page: Imprint / Legal notice, Cookie policy." }],
  ], links);

  // 4. R3: motorerne er uenige.
  expectRed("R3", contractR3, [
    ["motoren i repoet", { pass: true, label: "4 legal pages linked", detail: "Found on page: a, b." }],
    ["den publicerede motor", { pass: false, label: "0 legal pages linked", detail: "No standard legal page links found in the page HTML." }],
  ]);

  // 5. R4: pluginen består igen på en formular uden link. Det er den mutation,
  //    der lå i pluginens egen fil før denne rettelse.
  expectRed("R4 (pluginen består på prosa)", contractR4, [
    ["motoren i repoet", { legal: { pass: false, detail: "No standard legal page links found in the page HTML." }, forms: { pass: false, label: "Form(s) found, no privacy-policy link" } }],
  ], FIXTURES.find((f) => f.kind === "prosa+formular" && f.lang === "NL"),
    { pass: true, label: "Form(s) on the page, privacy-policy link found" });

  // 6. R4: pluginen **og** motoren er uenige om privatlivslinket.
  expectRed("R4 (produkter uenige)", contractR4, [
    ["motoren i repoet", { legal: { pass: true, detail: "Found on page: a, b." }, forms: { pass: false, label: "Form(s) found, no privacy-policy link" } }],
  ], FIXTURES.find((f) => f.kind === "links+formular" && f.lang === "NL"),
    { pass: true, label: "Form(s) on the page, privacy-policy link found" });

  // 7. R4: pluginen afviser at se på en side uden formular. Den skal sige det,
  //    for det er dens egen ærlige svar — en port der krævede andet ville være
  //    rød af design, og en port der er rød af design læses ikke.
  expectRed("R4 (pluginen ser på en side uden formular)", contractR4, [
    ["motoren i repoet", { legal: { pass: false, detail: "" }, forms: { pass: true, label: "Page has neither form markup nor a form plugin" } }],
  ], FIXTURES.find((f) => f.kind === "prosa" && f.lang === "DA"),
    { pass: false, label: "Form(s) on the page, no privacy-policy link" });

  // 8. R5: `forms` består igen på en formular uden link.
  expectRed("R5 (forms består på prosa)", contractR5, [
    ["motoren i repoet", { forms: { pass: true, label: "Form(s) found, privacy-policy link detected" } }],
  ], FIXTURES.find((f) => f.kind === "prosa+formular" && f.lang === "SV"), { pass: true, label: "x" });

  /*
   * Mutationer mod repoets egne filer. Hver gør matcherens beholder til at læse
   * hele HTML'en igen — den uændrede fejl — og porten skal blive rød på en
   * prosa-fixture. Skrevet mod de lange linjer, så de fejler med "fandt ikke den
   * linje den erstatter" den dag koden ændrer form, i stedet for at lade porten
   * stå grøn på en mutation den ikke længere rammer.
   *
   * Hver mutation rører **begge** steder i hver motor: `linkedLegalNames()`
   * driver `legal` (de 22 falske fund), og `linksLegal()` driver `forms` (den
   * række der lå og sagde "detected"). En mutation der kun rammer den ene, så
   * den anden vei grøn, ville være en mutation der beviser halvt. Det var fejlen
   * i denne fils første udformning: den muterede `linksLegal` og krævede R1,
   * som handler om `legal` — to forskellige funktioner, så porten var grøn af
   * den forkerte grund.
   */
  const MUTATIONER = [
    {
      navn: "motoren i repoet læser hele HTML'en igen",
      fil: join(REPO, "shared", "scan-engine.js"),
      foer: [
        { for: "return linkAnchors(html).some((a) => sig.re.test(a));", efter: "return sig.re.test(html);" },
        { for: "if (anchors.some((a) => sig.re.test(a))) names.push(sig.name);", efter: "if (sig.re.test(html)) names.push(sig.name);" },
      ],
    },
    {
      navn: "den publicerede motor læser hele HTML'en igen",
      fil: join(REPO, "eucomply-scanner", "engine", "index.js"),
      foer: [
        { for: "return linkAnchors(html).some((a) => sig.re.test(a));", efter: "return sig.re.test(html);" },
        { for: "if (anchors.some((a) => sig.re.test(a))) names.push(sig.name);", efter: "if (sig.re.test(html)) names.push(sig.name);" },
      ],
    },
    {
      navn: "pluginen læser hele HTML'en igen",
      fil: PLUGIN,
      foer: [
        {
          // Mutationen sætter **hele siden** ind som det ene "anchor", fordi
          // en prosa-side slet ikke har et `<a>`: en mutation der kun sat
          // `$anchor = $html` inde i løkken, sprang over en side uden links
          // og porten blev grøn af den forkerte grund. Det er mutationen der
          // skal genskabe **1.3.18's** kodevej, og den kodevej læser siden
          // uden at kigge på links.
          for: "if ( '' === $html || ! preg_match_all( '~<a\\b[^>]*>(?:(?!</a>)[\\s\\S])*~i', $html, $m ) ) {",
          efter: "if ( '' === $html ) {\n            return false;\n        }\n        $m = array( array( $html ) ); // mutation: læs hele siden\n        if ( false ) {",
        },
      ],
    },
  ];

  const prosaForm = FIXTURES.find((f) => f.kind === "prosa+formular" && f.lang === "NL");
  const prosaLinks = FIXTURES.find((f) => f.kind === "links" && f.lang === "NL");

  for (const m of MUTATIONER) {
    const original = readFileSync(m.fil, "utf8");
    let mutant = original;
    for (const { for: fra, efter } of m.foer) {
      if (!mutant.includes(fra)) {
        failures.push(`selftest: mutationen «${m.navn}» fandt ikke den linje den erstatter i ${m.fil}: ${fra}`);
        mutant = null;
        break;
      }
      mutant = mutant.replace(fra, efter);
    }
    if (mutant === null) continue;
    writeFileSync(m.fil, mutant);
    let rød = false;
    let grund = "";
    try {
      if (m.fil.endsWith(".php")) {
        try {
          contractR4([["x", { legal: { detail: "" }, forms: { pass: false, label: "Form(s) found, no privacy-policy link" } }]],
            prosaForm, pluginVerdict(prosaForm));
        } catch (e) {
          rød = true;
          grund = e.message;
        }
      } else {
        // Query-strengen på importen, fordi ESM cache'r modulerne pr. URL.
        const importPath = `${pathToFileURL(m.fil).href}?mut=${encodeURIComponent(m.navn)}`;
        const mutantScan = (await import(importPath)).runScan;
        const dom = await (async () => {
          const saved = globalThis.fetch;
          globalThis.fetch = async () => new Response(prosaForm.html, { status: 200, headers: { "Content-Type": "text/html" } });
          try {
            return (await mutantScan(TARGET)).checks;
          } finally {
            globalThis.fetch = saved;
          }
        })();
        try {
          contractR1(legalVerdicts([["mutationen", dom]]), prosaForm);
        } catch (e) {
          rød = true;
          grund = e.message;
        }
        // Og `forms` vejen, som læses af `linksLegal()` og ikke af
        // `linkedLegalNames()`. Den skal også blive rød.
        try {
          contractR5([["mutationen", dom]], prosaForm, { pass: true, label: "mutation" });
        } catch (e2) {
          if (!rød) grund = e2.message;
          rød = true;
        }
        // Og ingen tabt dækning: R2 skal fortsat være grøn på link-fixturet,
        // så mutationen ikke bare slår alt fra og gør porten grøn af en anden
        // grund.
        const dom2 = await (async () => {
          const saved = globalThis.fetch;
          globalThis.fetch = async () => new Response(prosaLinks.html, { status: 200, headers: { "Content-Type": "text/html" } });
          try {
            return (await mutantScan(TARGET)).checks;
          } finally {
            globalThis.fetch = saved;
          }
        })();
        contractR2(legalVerdicts([["mutationen", dom2]]), prosaLinks);
      }
    } finally {
      writeFileSync(m.fil, original);
    }
    if (rød) caught.push(`mutation: ${m.navn}`);
    else failures.push(`selftest: mutationen «${m.navn}» gav en grøn port — ${grund || "mutationen gav ingen fejl"}`);
  }

  if (failures.length) {
    for (const f of failures) console.error(`FEJL  ${f}`);
    process.exit(1);
  }
  console.log(`SELFTEST GRØN — alle negative cases fanges (${caught.length} af ${caught.length})`);
  for (const c of caught) console.log(`  fanget: ${c}`);
}
