/**
 * Kan de juridiske mønstre læse dansk, svensk og nederlandsk?
 *
 *   node tools/check_legal_langs.mjs
 *   node tools/check_legal_langs.mjs --selftest   (beviser at den kan fejle)
 *
 * Opgave 52 målte `LEGAL_PATTERNS` i de to universelle motorer med 22 rigtige
 * footer-links: **0 af 22** blev fundet. Følgen er ikke en manglende etiket,
 * men en score: en dansk butik med privatlivspolitik, handelsbetingelser og
 * cookiepolitik i footeren fik `legal` = **én** juridisk side og dermed
 * *advarsel* og et tabt point — mens den **samme** side på engelsk eller tysk
 * bestod med to. Efter opgave 51 var privatlivsmønsteret sprogneutralt, så
 * privatliv blev talt; vilkår og cookiepolitik gjorde det ikke, og de er netop
 * de to dokumenter `legal` kræver to af.
 *
 * Denne port måler det, i stedet for at læse kode. Den kører `legal` i begge
 * motorer (`shared/scan-engine.js` og den publicerede `eucomply-scanner/`) på
 * de samme fixtures og håndhæver fire regler:
 *
 *   R1  Dækket, ikke antaget. For hvert (mønster, sprog) i portens egen
 *       dækningstabel skal portens **egen** sprogliste se stænglen i
 *       fixturet, og begge motorer skal tælle mønsteret med sit **navn** i det
 *       `detail` en kunde læser. En tabelrække uden fixture er rød: det er
 *       forskellen på "målt" og "påstået", og den er hele denne opgave.
 *   R2  De to motorer er samme produkt. Identisk `pass`, `warn`, `label` og
 *       `detail` på hver fixture — ellers er den ene kopi ældre.
 *   R3  Ingen nye falske fund. En dansk, svensk eller nederlandsk **sætning**
 *       uden et juridisk link er ikke en juridisk side, og en side med ét
 *       juridisk link bliver ved med at være en advarsel. R1 alene kan ikke se
 *       det her: enhver bredere regex består R1 og taber point på kunden.
 *   R4  Samme dom på samme indhold, uanset sprog. Den danske, svenske og
 *       nederlandske side skal give præcis samme `legal`-dom som den engelske
 *       side med præcis samme dokumenter. Det er den asymmetri, opgaven
 *       begynder med, målt som en regel og ikke som en anecdote.
 *
 * Selftesten muterer repoets egne filer: for hvert af de to mønstre fjernes de
 * nye sprog fra en kopi af hver motor, og porten skal blive rød på den fixture
 * der bærer sproget. Uden det er porten en påstand — samme fejlklasse som
 * opgave 45 fund 2 og opgave 50 fund 1.
 *
 * Hvad porten **ikke** dækker, og hvorfor: `LEGAL_PATTERNS` læses kun af de to
 * JS-motorer (målt: ingen forekomst i `plugin/eucomply.php`). Pluginens `legal`
 * er en anden mekanisme — den slår WordPress-sider op efter sti og titel, ikke
 * markup. Den har sit eget sproghul og er opgave 53.
 *
 * Ingen dependencies, intet netværk: `fetch` stubbes, målet er et IP-literal,
 * så `assertPublicTarget` ikke slår DNS op. Spec: `docs/eucomply-juridiske-sprog.md`.
 */

import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
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

/** Ét IP-literal: assertPublicTarget slår værter op i DNS, og porten skal ikke kræve netværk. */
const TARGET = "https://93.184.216.34/";

/*
 * Portens **egne** stængler, skrevet efter `docs/eucomply-juridiske-sprog.md` og
 * ikke kopieret fra nogen motor: en fejl i motorens liste må ikke gælde begge
 * veje, ellers kan R1 ikke se den. Kun de mønstre opgaven rettede står her —
 * en tabelrække uden fixture er rød, så den kan ikke vokse i det skjulte.
 */
const STEMS = {
  "Cookie policy": {
    // EN, uændret siden før opgave 52. Den er her, fordi tabellen også lover
    // engelsk dækning, og R1 genkender en tabelrække uden egen stængel.
    EN: "cookie[_-]?policy",
    DA: "cookiepolitik",
    SV: "kakpolicy",
    NL: "cookies?beleid",
  },
  "Terms & Conditions": {
    // EN var ikke et sprogproblem men et separationsproblem: motoren havde
    // `[_-]?`, som aldrig matcher et mellemrum, så "Terms of Service" og
    // "Terms & Conditions" var usynlige. Portens egen stængel har derfor
    // mellemrummet med.
    EN: "terms[ _-]?(?:of[ _-]?use|of[ _-]?services?|and[ _-]?conditions|&\s*(?:amp;)?\s*conditions|conditions)",
    DA: "handelsbetingelser|vilk[aå]?r[ _-]?(?:og[ _-]?)?(?:betingelser|for[ _-]?(?:brug|anvendelse|køb))",
    SV: "allm[aä]nna[ _-]?villkor",
    NL: "algemene[ _-]?(?:leverings)?voorwaarden",
  },
};

/** (mønster, sprog) → fixture. R1 kræver, at hver af disse findes. */
const COVERAGE = [
  ["Cookie policy", "DA", "dansk butiksfooter med privatliv, handelsbetingelser og cookiepolitik"],
  ["Cookie policy", "SV", "svensk butiksfooter med integritetsskydd, allmänna villkor och kakpolicy"],
  ["Cookie policy", "NL", "nederlandsk butiksfooter met drie juridische links"],
  ["Terms & Conditions", "DA", "dansk butiksfooter med privatliv, handelsbetingelser og cookiepolitik"],
  ["Terms & Conditions", "SV", "svensk butiksfooter med integritetsskydd, allmänna villkor och kakpolicy"],
  ["Terms & Conditions", "NL", "nederlandsk butiksfooter met drie juridische links"],
  // Beviset på R4: samme tre dokumenter på engelsk, som altid har bestået.
  ["Cookie policy", "EN", "engelsk butiksfooter med privacy, terms og cookie policy"],
  ["Terms & Conditions", "EN", "engelsk butiksfooter med privacy, terms og cookie policy"],
  ["Terms & Conditions", "EN", "engelsk side hvor kun linkteksten siger Terms of Service"],
  ["Terms & Conditions", "DA", "dansk side med Vilkaar for brug og privatliv"],
];

/** Sprog til det sprog navnet skriver. Kun til fejlbeskeder. */
const SPROG = { DA: "dansk", SV: "svensk", NL: "nederlandsk", EN: "engelsk" };

const FIXTURES = [
  {
    name: "dansk butiksfooter med privatliv, handelsbetingelser og cookiepolitik",
    // Det er denne side der fik *én* juridisk side og en advarsel, før de nye
    // sprog kom til. Alle tre links er præcis sådan en dansk sko skriver dem.
    html: '<html><body><main><h1>Vores sko</h1><p>Fri fragt over 499 kr.</p></main>'
      + '<footer><a href="/privatlivspolitik/">Privatlivspolitik</a>'
      + '<a href="/handelsbetingelser/">Handelsbetingelser</a>'
      + '<a href="/cookiepolitik/">Cookiepolitik</a></footer></body></html>',
  },
  {
    name: "svensk butiksfooter med integritetsskydd, allmänna villkor och kakpolicy",
    // `Allmänna villkor` står med accent i den tekst læseren ser, fordi det er
    // sådan svenske butikker skriver det. href'en er ASCII-formen, som er den
    // de fleste CMS'er genererer.
    html: '<html><body><main><h1>Våra skor</h1><p>Fri frakt över 499 kr.</p></main>'
      + '<footer><a href="/integritetsskydd/">Integritetsskydd</a>'
      + '<a href="/allmanna-villkor">Allmänna villkor</a>'
      + '<a href="/kakpolicy">Kakpolicy</a></footer></body></html>',
  },
  {
    name: "nederlandsk butiksfooter met drie juridische links",
    // `Cookiesbeleid` med pluralsformen, som er den almindelige i Nederland.
    html: '<html><body><main><h1>Onze schoenen</h1><p>Gratis verzending boven €49.</p></main>'
      + '<footer><a href="/persoonsgegevens/">Persoonsgegevens</a>'
      + '<a href="/algemene-voorwaarden/">Algemene voorwaarden</a>'
      + '<a href="/cookiesbeleid/">Cookiesbeleid</a></footer></body></html>',
  },
  {
    name: "engelsk butiksfooter med privacy, terms og cookie policy",
    html: '<html><body><main><h1>Our shoes</h1><p>Free shipping over 49 EUR.</p></main>'
      + '<footer><a href="/privacy/">Privacy Policy</a>'
      + '<a href="/terms/">Terms of Service</a>'
      + '<a href="/cookie-policy/">Cookie Policy</a></footer></body></html>',
  },
  {
    name: "engelsk side hvor kun linkteksten siger Terms of Service",
    // Separatoren var `[_-]?`, som matcher bindestreg og understreg men aldrig
    // et mellemrum. Den fandt altså "terms-of-service" og ingen af de former en
    // side skriver. Denne fixture er den fejl, målt.
    html: '<html><body><main><h1>Support</h1><p>Vi svarer inden for 24 timer.</p></main>'
      + '<footer><a href="/legal">Terms of Service</a>'
      + '<a href="/legal/privacy">Privacy Policy</a></footer></body></html>',
  },
  {
    name: "dansk side med Vilkaar for brug og privatliv",
    html: '<html><body><main><h1>Om os</h1><p>Familiebutik siden 1998.</p></main>'
      + '<footer><a href="/privatlivspolitik/">Privatlivspolitik</a>'
      + '<a href="/vilkaar-for-brug">Vilkår for brug</a></footer></body></html>',
  },
  {
    name: "dansk side med kun ét juridisk link",
    // R3: én link er stadig én. En bredere regex må ikke gøre advarsel til
    // bestået, for det er den vej fejlen kommer tilbage ad.
    html: '<html><body><main><h1>Om os</h1><p>Vi er en dansk familiebutik siden 1998.</p></main>'
      + '<footer><a href="/privatlivspolitik/">Privatlivspolitik</a></footer></body></html>',
  },
  {
    name: "dansk sætning med leveringsbetingelser, intet juridisk link",
    // R3, dansk: `betingelser` er her en del af et helt andet ord. Havde
    // rettelsen brugt stænglen `betingelser`, ville denne side være fundet som
    // en vilkårside — og det er præcis den falske fund porten skal se.
    html: '<html><body><main><p>Priserne er ekskl. moms, og alle vores '
      + 'leveringsbetingelser gælder for levering til Danmark.</p></main></body></html>',
  },
  {
    name: "svensk sætning med köpvillkoren, intet juridisk link",
    // R3, svensk: `villkor` indgår i to helt andre ord. Havde rettelsen brugt
    // stænglen `villkor`, ville denne side være fundet.
    html: '<html><body><main><p>Köpvillkoren och returvillkoren framgår av '
      + 'orderbekräftelsen du fick per mejl.</p></main></body></html>',
  },
  {
    name: "nederlandse zin met voorwaarden, geen juridische link",
    // R3, nederlandsk: `voorwaarden` uden `algemene` er ikke sidenavnet.
    html: '<html><body><main><p>Onze voorwaarden voor de gratis proefperiode '
      + 'zijn niet bindend en kun je op elk moment opzeggen.</p></main></body></html>',
  },
  {
    name: "dansk side uden nogen juridisk side",
    html: '<html><body><main><h1>Kontakt</h1><p>Ring til os på 12 34 56 78.</p></main></body></html>',
  },
];

/**
 * Hvilke mønstre en motor fandt. Læst ud af `detail` — den tekst kunden ser i
 * rapporten — fordi `LEGAL_PATTERNS` ikke er eksporteret, og fordi det er den
 * tekst, porten skal måle: et mønster der findes i koden, men ikke i
 * rapporten, er ikke fundet for kunden.
 */
function foundNames(verdict) {
  const m = /Found on page: (.+?)\.$/.exec(verdict.detail || "");
  if (!m) return [];
  return m[1].split(", ").map((s) => s.trim());
}

/** Kør én motor mod én fixture. */
async function engineVerdict(runScan, fixture) {
  const saved = globalThis.fetch;
  globalThis.fetch = async () =>
    new Response(fixture.html || "", {
      status: 200,
      headers: { "Content-Type": "text/html", ...(fixture.headers || {}) },
    });
  try {
    const scan = await runScan(TARGET);
    assert.ok(scan.checks.legal, "motoren kender ikke tjekket legal");
    return scan.checks.legal;
  } finally {
    globalThis.fetch = saved;
  }
}

/** Hent en fixture ved navn. Navne, ikke indeks — så en ny fixture i midten ikke flytter dem. */
function fx(name) {
  const found = FIXTURES.find((f) => f.name === name);
  assert.ok(found, `porten har ingen fixture ved navn «${name}»`);
  return found;
}

/** Sprog, hvis portens egen liste ser stænglen i fixturet. */
function portSees(pat, lang, fixture) {
  const stem = STEMS[pat] && STEMS[pat][lang];
  if (!stem) return false;
  return new RegExp(stem, "i").test(fixture.html || "");
}

/*
 * De fire regler, som *kun* betinger. Porten og selftesten kalder de samme
 * funktioner, så en negativ case ikke kan blive grøn ved at forvente noget andet
 * end det porten kræver — den fejl fandt opgave 42, 45 og 50.
 */

/** R1: dækket, ikke antaget — hvert (mønster, sprog) skal findes i begge motorer. */
function contractR1(verdicts, fixture) {
  for (const [pat, lang, fixtureName] of COVERAGE) {
    if (fixtureName !== fixture.name) continue;
    assert.ok(
      portSees(pat, lang, fixture),
      `portens egen liste kan ikke se ${SPROG[lang] || lang}-formen af «${pat}» i «${fixture.name}»`
    );
    for (const [hvem, v] of verdicts) {
      assert.ok(
        foundNames(v).includes(pat),
        `${hvem} finder ikke «${pat}» på en ${SPROG[lang] || lang} side ` +
          `(rapporten siger: "${v.detail}")`
      );
    }
  }
}

/** R2: de to motorer er samme produkt og skal svare identisk. */
function contractR2(verdicts) {
  // `verdicts` er [hvem, dom]-par, så dommen er indeks 1. Destrukturerer man
  // kun det ydre par, sammenligner man `undefined` med `undefined` — og regelen
  // er grøn for enhver afvigelse. Det gjorde den i første udformning, og
  // selftesten fandt det.
  const [, a] = verdicts[0];
  const [, b] = verdicts[1];
  assert.equal(
    Boolean(b.pass),
    Boolean(a.pass),
    `de to motorer er uenige om dommen: «${a.label}» mod «${b.label}»`
  );
  assert.equal(b.detail, a.detail, `samme dom, to forskellige rapporter: «${a.detail}» mod «${b.detail}»`);
}

/** R3: en sætning er ikke en juridisk side, og ét link er stadig ét link. */
function contractR3(verdicts, fixture) {
  const forventetLinks = fixture.name === "dansk side med kun ét juridisk link" ? 1 : 0;
  for (const [hvem, v] of verdicts) {
    if (forventetLinks === 0) {
      assert.equal(
        Boolean(v.pass),
        false,
        `${hvem} består (${v.label}) på «${fixture.name}» — der er intet juridisk link på siden`
      );
      assert.equal(
        foundNames(v).length,
        0,
        `${hvem} tæller ${foundNames(v).join(", ")} på «${fixture.name}» — en sætning er ikke en juridisk side`
      );
    } else {
      assert.equal(
        Boolean(v.warn),
        true,
        `${hvem} svarer ${v.label} på en side med ét juridisk link — advarslen forsvandt`
      );
      assert.equal(
        Boolean(v.pass),
        false,
        `${hvem} består (${v.label}) på en side med kun ét juridisk link`
      );
    }
  }
}

/**
 * R1s anden halvdel: en dækningstabelrække uden egen stængel eller uden egen
 * fixture er rød. Det er forskellen på "målt" og "påstået", og det er hele denne
 * opgave. Porten **og** selftesten kalder den her, så en negativ case ikke kan
 * blive grøn ved at forvente noget andet end det porten kræver — den fejl fandt
 * opgave 42, 45 og 50.
 */
function contractCoverage(table, stems, fixtures) {
  for (const [pat, lang, fixtureName] of table) {
    const langs = stems[pat] || {};
    assert.ok(
      Object.prototype.hasOwnProperty.call(langs, lang),
      `dækningstabellen lover «${pat}» på ${SPROG[lang] || lang}, men porten har ingen stængel til den`
    );
    assert.ok(
      fixtures.some((f) => f.name === fixtureName),
      `dækningstabellen lover «${pat}» på ${SPROG[lang] || lang}, men der er ingen fixture ved navn «${fixtureName}» — ` +
        `et mønster uden fixture er påstået, ikke målt`
    );
  }
}

/** R4: samme dokumenter, samme dom — uanset hvilket sprog siden står på. */
function contractR4(verdicts) {
  const dansk = verdicts["dansk butiksfooter med privatliv, handelsbetingelser og cookiepolitik"];
  const svensk = verdicts["svensk butiksfooter med integritetsskydd, allmänna villkor och kakpolicy"];
  const nederlandsk = verdicts["nederlandsk butiksfooter met drie juridische links"];
  const engelsk = verdicts["engelsk butiksfooter med privacy, terms og cookie policy"];
  for (const [sprog, v] of Object.entries({ dansk, svensk, nederlandsk })) {
    assert.equal(
      Boolean(v.pass),
      Boolean(engelsk.pass),
      `en ${sprog} butik med de samme tre juridiske dokumenter får «${v.label}», ` +
        `mens den engelske får «${engelsk.label}» — scoren afhænger af sprog`
    );
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

const verdicts = new Map();
for (const fixture of FIXTURES) {
  const per = [];
  for (const [hvem, , runScan] of ENGINES) per.push([hvem, await engineVerdict(runScan, fixture)]);
  verdicts.set(fixture.name, per);
}

for (const fixture of FIXTURES) {
  const vs = verdicts.get(fixture.name);
  await test(`R1 dækket, ikke antaget: ${fixture.name}`, () => contractR1(vs, fixture));
  await test(`R2 de to motorer er ens: ${fixture.name}`, () => contractR2(vs));
  if (
    fixture.name === "dansk side med kun ét juridisk link" ||
    !foundNames(vs[0][1]).length
  ) {
    await test(`R3 ingen falske fund: ${fixture.name}`, () => contractR3(vs, fixture));
  }
}

await test("R1: hver (mønster, sprog) i tabellen har en stængel og en fixture", () => {
  contractCoverage(COVERAGE, STEMS, FIXTURES);
});

await test("R4: samme tre juridiske dokumenter giver samme dom på fire sprog", () => {
  contractR4(Object.fromEntries(verdicts));
});

if (process.argv.includes("--selftest")) {
  const caught = [];
  /** Forventer at kontrakten bliver rød på dette input, og tæller det. */
  const expectRed = (name, contract, ...args) => {
    try {
      contract(...args);
      failures.push(`selftest: ${name} gav en grøn port — den kan ikke se den fejl`);
    } catch {
      caught.push(name);
    }
  };

  // 1. R1: motoren finder ikke den danske cookiepolitik.
  expectRed("R1 (motor finder ikke)", contractR1, [
    ["motoren i repoet", { pass: true, label: "3 legal pages linked", detail: "Found on page: Privacy / GDPR, Terms & Conditions." }],
  ], fx("dansk butiksfooter med privatliv, handelsbetingelser og cookiepolitik"));

  // 2. R1: portens egen liste kan ikke se stænglen, selv om motoren kan. Det er
  //    den retning, der gør tabellen ubrugelig frem for at motoren er rød.
  expectRed("R1 (portens egen liste)", contractR1, [
    ["motoren i repoet", { pass: true, label: "3 legal pages linked", detail: "Found on page: Privacy / GDPR, Cookie policy, Terms & Conditions." }],
  ], { name: "dansk butiksfooter med privatliv, handelsbetingelser og cookiepolitik", html: "<p>ingen juridisk side</p>" });

  // 3. R2: de to motorer svarer forskelligt.
  expectRed("R2", contractR2, [
    ["motoren i repoet", { pass: true, label: "3 legal pages linked", detail: "Found on page: a, b, c." }],
    ["den publicerede motor", { pass: false, label: "1 legal page linked", detail: "Found on page: a." }],
  ]);

  // 4. R3: en sætning blev talt som en juridisk side.
  expectRed("R3 (falsk fund)", contractR3, [
    ["motoren i repoet", { pass: true, warn: false, label: "2 legal pages linked", detail: "Found on page: Terms & Conditions, Cookie policy." }],
  ], fx("svensk sætning med köpvillkoren, intet juridisk link"));

  // 5. R3: ét link blev bestået.
  expectRed("R3 (ét link bestået)", contractR3, [
    ["motoren i repoet", { pass: true, warn: false, label: "1 legal page linked", detail: "Found on page: Privacy / GDPR." }],
  ], fx("dansk side med kun ét juridisk link"));

  // 6. R4: den danske side advarser, den engelske består.
  expectRed("R4", contractR4, {
    "dansk butiksfooter med privatliv, handelsbetingelser og cookiepolitik": { pass: false, label: "1 legal page linked" },
    "svensk butiksfooter med integritetsskydd, allmänna villkor och kakpolicy": { pass: true, label: "3 legal pages linked" },
    "nederlandsk butiksfooter met drie juridische links": { pass: true, label: "3 legal pages linked" },
    "engelsk butiksfooter med privacy, terms og cookie policy": { pass: true, label: "3 legal pages linked" },
  });

  /*
   * Mutationer mod repoets egne filer. For hvert mønster fjernes de nye sprog fra
   * en kopi af hver motor, og porten skal blive rød på den fixture der bærer
   * sproget. Skrevet mod den lange linje, så de fejler med "fandt ikke den linje
   * den erstatter" den dag et nyt sprog kommer til, i stedet for at lade porten
   * stå grøn på en mutation den ikke længere rammer.
   */
  const MUTATIONS = [
    {
      name: "cookie: de nye sprog forsvinder",
      before: "cookie[_-]?preferences|cookiepolitik|cookies?beleid|kakpolicy",
      after: "cookie[_-]?preferences",
      fixture: "dansk butiksfooter med privatliv, handelsbetingelser og cookiepolitik",
      pattern: "Cookie policy",
    },
    {
      name: "terms: de nye sprog forsvinder",
      before: "terms[ _-]?(?:of[ _-]?use|of[ _-]?services?|and[ _-]?conditions|&\\s*(?:amp;)?\\s*conditions|conditions)|handelsbetingelser|vilk[aå]?r[ _-]?(?:og[ _-]?)?(?:betingelser|for[ _-]?(?:brug|anvendelse|køb))|allm[aä]nna[ _-]?villkor|anv[äa]ndningsvillkor|algemene[ _-]?(?:leverings)?voorwaarden",
      after: "terms[ _-]?(?:of[ _-]?use|of[ _-]?services?|and[ _-]?conditions|&\\s*(?:amp;)?\\s*conditions|conditions)",
      fixture: "svensk butiksfooter med integritetsskydd, allmänna villkor och kakpolicy",
      pattern: "Terms & Conditions",
    },
  ];

  for (const m of MUTATIONS) {
    for (const [hvem, file, ] of ENGINES) {
      const source = readFileSync(file, "utf8");
      if (!source.includes(m.before)) {
        failures.push(
          `selftest: mutationen «${m.name}» i ${hvem} fandt ikke den linje den erstatter — ` +
            `porten kan ikke længere bevise at den ser den fejl`
        );
        continue;
      }
      const dir = mkdtempSync(join(tmpdir(), "eucomply-legal-mutant-"));
      const mutant = join(dir, file.endsWith("index.js") ? "index.js" : "scan-engine.js");
      writeFileSync(mutant, source.replace(m.before, m.after));
      const mutated = await engineVerdict((await import(pathToFileURL(mutant).href)).runScan, fx(m.fixture));
      try {
        assert.ok(
          foundNames(mutated).includes(m.pattern),
          `mutationen «${m.name}» i ${hvem} fandt stadig «${m.pattern}» (${mutated.detail})`
        );
        failures.push(
          `selftest: mutationen «${m.name}» i ${hvem} gav stadig «${m.pattern}» — ` +
            `porten kan ikke se den fejl den blev skrevet til at se`
        );
      } catch {
        caught.push(`${m.name} (${hvem})`);
      }
      // Og den mutation skal gøre R1 rød, ikke blot ved at miste et navn.
      const anden = [hvem, mutated];
      const [første] = ENGINES;
      const par = verdicts.get(m.fixture).map(([h, v]) => (h === første[0] ? anden : [h, v]));
      expectRed(`${m.name} (${hvem}) i R1`, contractR1, par, fx(m.fixture));
    }
  }

  // 7. En (mønster, sprog)-række i tabellen uden fixture er rød. Den kalder
  //    portens egen kontrakt med den fixture fjernet, så den ikke kan være grøn
  //    ved at kræve noget andet end det porten kræver.
  const mistet = FIXTURES.filter((f) => f.name !== COVERAGE[0][2]);
  expectRed("R1 (tabellen kræver en fixture)", contractCoverage, COVERAGE, STEMS, mistet);

  // 8. Samme regel for en stængel, portens egen liste ikke har.
  expectRed("R1 (tabellen kræver en stængel)", contractCoverage,
    [...COVERAGE, ["Shipping policy", "DA", "dansk side med kun ét juridisk link"]],
    STEMS, FIXTURES);

  const forventet = 6 + MUTATIONS.length * 4 + 2;
  if (caught.length !== forventet) {
    failures.push(`selftest: forventede ${forventet} negative cases fanget, fangede ${caught.length}`);
  } else {
    passed += forventet;
  }
}

if (failures.length) {
  for (const f of failures) console.error(`FAIL  ${f}`);
  console.error(`${failures.length} JURIDISK-SPROG FEJL`);
  process.exit(1);
}
console.log(
  `${passed} juridisk-sprogtest bestået — ${FIXTURES.length} fixtures, ${COVERAGE.length} (mønster, sprog) dækket`
);
