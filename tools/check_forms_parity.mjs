/**
 * Kan pluginens `forms` og motorens `forms` være uenige om den samme side?
 *
 *   node tools/check_forms_parity.mjs
 *   node tools/check_forms_parity.mjs --selftest   (beviser at den kan fejle)
 *
 * Opgave 49 kørte alle elleve plugin-tjek og alle ni motortjek på de samme
 * fixtures. Den fandt, at den betalte vare svarer en **mindre streng** vurdering
 * end den gratis scanner om den *samme* hjemmeside: `check_forms()` læste kun
 * installerede plugins og `wp_page_for_privacy_policy`, mens motoren læser
 * markup'en. En side med en håndbygget formular og intet privatlivslink fik
 * "fejler" i den gratis scanner og "består" i den rapport et bureau betaler $79
 * for at sende sin kunde. Det er den modsatte retning af de otte fund i opgave
 * 44: der var tjekket dødt, her er det mindre end det, kunden køber.
 *
 * Denne port måler det, i stedet for at læse kode. Den kører `check_forms()`
 * gennem `tools/plugin_probe.php` og den universelle motor gennem `runScan()`
 * på de samme fixtures og håndhæver tre regler:
 *
 *   R1  Aldrig svagere. Pluginen består aldrig noget, motoren fejler på samme
 *       HTML. Det er den retning, opgave 50 handler om, og den er den, en
 *       kunde mærker.
 *   R2  Aldrig svagere, uden motoren. En `<form>` i markup'en uden
 *       privatlivslink giver aldrig et bestående `forms`, uanset hvad
 *       WordPress siger. Denne regel er skrevet uafhængigt af motoren, så den
 *       ikke kan arve en fejl fra den.
 *   R3  Strengere kun med en kilde. Pluginen må fejle noget motoren består, men
 *       kun når fixturet faktisk viser en kilde: formularmarkup på siden, eller
 *       et installeret form-plugin på et site uden privatlivsside. Uden denne
 *       regel er R1 nok — en plugin der fejler alt, består R1.
 *   R4  De to universelle motorer er samme produkt. `shared/scan-engine.js` og
 *       den publicerede `eucomply-scanner/` skal give **identisk** `forms`-dom
 *       på hver fixture. Uden denne regel kunne den ene kopier være ældre.
 *   R5  De to motorer læser privatlivslinket lige. På en side med en lukket
 *       `<form>` skal de være enige med portens **egen** sprogliste, begge
 *       veje: et link porten kan se består de, intet link fejler de. Det er
 *       regelen, der måler opgave 51 — en dansk privatlivsside var en fejl i
 *       alle tre motorer, fordi mønsteret kun kendte engelsk og tysk.
 *   R6  Samme dom på en side med formular, begge veje. R1 kan kun se den ene
 *       retning, fordi den springer over når pluginen fejler — så en mutation
 *       der *fjerner* en evne (de nye sprog, 1.3.15's formularmarkup) var
 *       usynlig for porten. Det er fundet, R6 er svaret på.
 *
 * R1 og R3 er de to retninger, porten skal kunne fejle i. R2, R4, R5 og R6 er
 * dem, opgaverne kræver målt på fixtures og ikke på kode.
 *
 * Ingen dependencies, intet netværk: fetch stubbes, og målet er et IP-literal,
 * så assertPublicTarget ikke slår DNS op. PHP'en svarer fra en fixture.
 * Specen for de to seneste ændringer er `docs/eucomply-forms-paritet.md` og
 * `docs/eucomply-privatlivsprog.md`.
 */

import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { runScan as runPublishedScan } from "../eucomply-scanner/engine/index.js";
import { runScan as runSharedScan } from "../shared/scan-engine.js";

const REPO = join(import.meta.dirname, "..");
const PROBE = join(REPO, "tools", "plugin_probe.php");
const PLUGIN = join(REPO, "plugin", "eucomply.php");

/** Ét IP-literal: assertPublicTarget slår værter op i DNS, og porten skal ikke kræve netværk. */
const TARGET = "https://93.184.216.34/";

/*
 * Portens egen læsning af markup'en, bevidst ikke importeret fra motoren: en
 * fejl i motorens `<form>`-regel må ikke gælde begge veje, og R2 skal kunne
 * fange en plugin der blindt stoler på motoren.
 */
const FORM_IN_PAGE = /<form[^>]*>[\s\S]*?<\/form>/i;
/** En formular der poster til en tjeneste uden for sitet, også uden lukket `</form>`. */
const FORM_WITH_EXTERNAL_ACTION = /<form[^>]*action\s*=\s*["'](?:[^"']+:)?\/\/[^"']*["']/i;
/**
 * Portens egen sprogliste for privatlivslinket, skrevet efter
 * `docs/eucomply-privatlivsprog.md` og **ikke** kopieret fra nogen motor: en
 * fejl i motorens liste må ikke gælde begge veje, ellers kan R5 ikke se den.
 * Den er bygget som en liste af stængler, så selftesten kan genopbygge den
 * gamle engelsk/tyske liste og se, at de nye sprog bærer R5 alene.
 */
const PRIVACY_STEMS = [
  // EN + DE, uændret siden før opgave 51.
  "privacy", "privacy[_-]?policy", "datenschutz", "gdpr", "privacypolicy", "data[_-]?protection",
  // DA
  "privatliv", "persondata", "databeskyttelse",
  // SV
  "integritetsskydd", "dataskydd", "personuppgifter",
  // NL
  "persoonsgegevens", "gegevensbescherming",
  // FR + ES
  "confidentialit", "privacidad", "datos personales",
];
const PRIVACY_LINK = new RegExp(PRIVACY_STEMS.join("|"), "i");
/** Den liste motorerne havde før opgave 51. Kun bruges i selftesten. */
const ENGLISH_ONLY_PRIVACY_LINK =
  /privacy|privacy[_-]?policy|datenschutz|gdpr|privacypolicy|data[_-]?protection/i;

/** Læser markup'en med portens egen liste, så R5 ikke arver motorens regex. */
function privacyLinkPresent(html, re = PRIVACY_LINK) {
  return re.test(html || "");
}

/** De installerede plugins, `check_forms()` genkender som formular-udbydere. */
const FORM_PLUGIN_FILES = [
  "contact-form-7/wp-contact-form-7.php",
  "wpforms-lite/wpforms.php",
  "wpforms/wpforms.php",
  "gravityforms/gravityforms.php",
  "elementor/elementor.php",
  "formidable/formidable.php",
  "fluentform/fluentform.php",
];

const PRIVACY_SITE = { wp_page_for_privacy_policy: 12 };

const FIXTURES = [
  {
    name: "håndbygget formular, intet privatlivslink",
    // Tilfældet opgave 50 handler om: et theme-formular er usynligt for
    // WordPress-tilstanden, så 1.3.15 bestod det her.
    html: '<html><body><main><h1>Kontakt</h1><form action="#" method="post">'
      + '<input name="email" type="email"><button>Send</button></form></main></body></html>',
    active: [],
    options: {},
  },
  {
    name: "håndbygget formular, privatlivslink på siden",
    // Linket skrives på engelsk, fordi det dækkede alle tre motorer før
    // opgave 51. Det danske er de fire fixtures nedenfor — de ville have været
    // umulige at skrive før den, fordi mønsteret ikke kendte ordet.
    html: '<html><body><form action="#"><input name="email"></form>'
      + '<footer><a href="/privacy/">Privacy Policy</a></footer></body></html>',
    active: [],
    options: {},
  },
  {
    name: "håndbygget formular, WordPress har en privatlivsside men siden linker den ikke",
    // R2 holder her: en privatlivsside i Settings er ikke den notice, der skal
    // stå ved indsamlingen, så dommen er fejl uanset WordPress-tilstanden.
    html: '<html><body><form action="#"><input name="name"></form></body></html>',
    active: [],
    options: PRIVACY_SITE,
  },
  {
    name: "formular der poster til en ekstern tjeneste",
    html: '<html><body><form action="https://formspree.io/f/abc" method="post">'
      + '<input name="email"></body></html>',
    active: [],
    options: {},
  },
  {
    name: "WPForms installeret, privatlivsside sat, ingen formular på forsiden",
    html: "<html><head><title>Butik</title></head><body><p>Velkommen</p></body></html>",
    active: ["wpforms-lite/wpforms.php", "complianz-gdpr/cmp-functions.php"],
    options: PRIVACY_SITE,
  },
  {
    name: "WPForms installeret, hverken privatlivsside eller link",
    html: "<html><head><title>Butik</title></head><body><p>Velkommen</p></body></html>",
    active: ["wpforms-lite/wpforms.php"],
    options: {},
  },
  {
    name: "Contact Form 7 nævnt i markup'en, ingen formular endnu",
    html: "<html><body><p>Vi bruger Contact Form 7 på kontaktsiden.</p></body></html>",
    active: [],
    options: {},
  },
  {
    name: "en side uden formularer overhovedet",
    html: "<html><body><h1>Om os</h1><p>Vi sælger kaffe.</p></body></html>",
    active: ["complianz-gdpr/cmp-functions.php", "updraftplus/updraftplus.php"],
    options: PRIVACY_SITE,
  },
  {
    name: "en side uden privatliv noget som helst",
    html: "<html><body><h1>Om os</h1><p>Vi sælger kaffe.</p></body></html>",
    active: [],
    options: {},
  },
  // Opgave 51. Alle fem var umulige at skrive før den: privatlivsmønsteret
  // kendte engelsk og tysk, så hver af dem fejlede `forms` i alle tre motorer
  // på en side der gjorde præcis det, tjekket beder om.
  {
    name: "dansk formular med dansk privatlivslink",
    html: '<html><body><h1>Kontakt</h1><form action="/kontakt/send" method="post">'
      + '<input name="email" type="email"><button>Send</button></form>'
      + '<footer><a href="/privatlivspolitik/">Privatlivspolitik</a></footer></body></html>',
    active: [],
    options: {},
  },
  {
    name: "svensk formular med svensk integritetsside",
    html: '<html><body><form action="/kontakt"><input name="epost"></form>'
      + '<footer><a href="/integritetsskydd/">Integritetsskydd</a></footer></body></html>',
    active: [],
    options: {},
  },
  {
    name: "nederlandsk formular med nederlandsk privacybeleid",
    // Skrevet *uden* `privacy` i linket. Den almindelige hollandske
    // formulering "Privacybeleid" rammer det gamle `privacy` og ville derfor
    // have været grøn uden rettelsen; "Persoonsgegevens" er den, der ikke er.
    html: '<html><body><form action="/contact"><input name="email"></form>'
      + '<footer><a href="/persoonsgegevens/">Persoonsgegevens</a></footer></body></html>',
    active: [],
    options: {},
  },
  {
    name: "dansk privatlivsord kun i linkteksten, ikke i href'en",
    // Beviset mod mutation M4: en "forbedring" der kun læser `href` må ikke
    // slå denne side, fordi privatlivsordet står i den tekst, brugeren ser.
    html: '<html><body><form action="/kontakt"><input name="navn"></form>'
      + '<footer><a href="/juridisk/">Privatlivspolitik</a></footer></body></html>',
    active: [],
    options: {},
  },
  {
    name: "dansk formular med kun danske vilkår, intet privatliv",
    // Beviset mod den modsatte fejl: de nye sprog må ikke blive "ethvert
    // dansk ord". Handelsbetingelser er vilkår, ikke en privatlivsnotice, så
    // alle tre motorer skal stadig fejle.
    html: '<html><body><form action="/kontakt"><input name="navn"></form>'
      + '<footer><a href="/handelsbetingelser/">Handelsbetingelser</a>'
      + '<a href="/om-os/">Om os</a></footer></body></html>',
    active: [],
    options: {},
  },
];

/** Kør pluginens `forms` på én fixture. Én check ad gangen, så hentningen kan tilskrives den. */
function pluginVerdict(fixture, pluginFile) {
  const dir = mkdtempSync(join(tmpdir(), "eucomply-forms-"));
  const file = join(dir, "fixture.json");
  writeFileSync(
    file,
    JSON.stringify({
      html: fixture.html || "",
      headers: fixture.headers || {},
      active: fixture.active || [],
      options: fixture.options || {},
      pages: { 12: { post_title: "Privatlivspolitik", post_status: "publish" } },
    })
  );
  const env = { ...process.env };
  if (pluginFile) env.EUCOMPLY_PLUGIN_FILE = pluginFile;
  const out = execFileSync("php", [PROBE, file, "forms"], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
    env,
  });
  const decoded = JSON.parse(out.trim().split("\n").pop());
  assert.ok(decoded.forms, "proben svarede ikke på forms");
  return decoded.forms;
}

/** Kør én af de to universelle motorer mod den samme fixture. */
async function engineVerdict(runScan, fixture) {
  const saved = globalThis.fetch;
  globalThis.fetch = async () =>
    new Response(fixture.html || "", {
      status: 200,
      headers: { "Content-Type": "text/html", ...(fixture.headers || {}) },
    });
  try {
    const scan = await runScan(TARGET);
    assert.ok(scan.checks.forms, "motoren kender ikke tjekket forms");
    return scan.checks.forms;
  } finally {
    globalThis.fetch = saved;
  }
}

/** Hvilke kilder fixturet faktisk viser. Porten læser fixturet, ikke nogen motors svar. */
function evidence(fixture, privacyRe = PRIVACY_LINK) {
  const html = fixture.html || "";
  return {
    pageForm: FORM_IN_PAGE.test(html) || FORM_WITH_EXTERNAL_ACTION.test(html),
    privacyLink: privacyLinkPresent(html, privacyRe),
    installedFormPlugin: (fixture.active || []).some((f) => FORM_PLUGIN_FILES.includes(f)),
    privacyPageInWordPress: Boolean((fixture.options || {})["wp_page_for_privacy_policy"]),
    html,
  };
}

/*
 * De fem regler, som *kun* betinger. Porten og selftesten kalder de samme
 * funktioner, så en negativ case ikke kan blive grøn ved at forvente noget andet
 * end det porten kræver — den fejl fandt opgave 42 og 45 to gange i hver sin
 * port.
 */

/** R1: aldrig svagere end den gratis scanner. */
function contractR1(plugin, engine) {
  if (!plugin.pass) return;
  assert.equal(
    Boolean(engine.pass),
    true,
    `pluginen består (${plugin.label}), motoren fejler (${engine.label}) på samme HTML`
  );
}

/** R2: formular i markup'en uden privatlivslink består aldrig, uanset WordPress. */
function contractR2(plugin, ev) {
  if (!ev.pageForm || ev.privacyLink) return;
  assert.equal(
    Boolean(plugin.pass),
    false,
    `pluginen består (${plugin.label}) på en side med formular og intet privatlivslink`
  );
}

/** R3: strengere end motoren kræver en kilde, porten kan se i fixturet. */
function contractR3(plugin, engine, ev) {
  if (plugin.pass) return;
  // Kun den ene retning er noget at forklare: fejler de to begge, er de enige.
  if (!engine.pass) return;
  const justified =
    ev.pageForm || (ev.installedFormPlugin && !ev.privacyLink && !ev.privacyPageInWordPress);
  assert.ok(
    justified,
    `pluginen fejler (${plugin.label}), motoren består (${engine.label}), og ` +
      `fixturet viser hverken formularmarkup (${ev.pageForm}) eller et form-plugin ` +
      `på et site uden privatlivsside (${ev.installedFormPlugin}) — altså en fejl ` +
      `uden kilde`
  );
}

/**
 * R6: på en side med en **lukket** `<form>` og ingen installerede
 * form-plugins skal pluginen og motoren svare identisk, begge veje. R1 kan kun
 * se den ene retning — den springer over, når pluginen fejler — så en
 * mutation der **fjerner** en evne (de nye sprog, 1.3.15's formularmarkup) er
 * usynlig for den. Det er den mutation, opgave 51 handler om.
 *
 * Samme afgrænsning som R5: en ekstern formular uden lukket `</form>`, og et
 * site med et installeret form-plugin, er de steder hvor pluginen med vilje
 * svarer strengere. R3 holder dem på plads.
 */
function contractR6(plugin, engine, ev) {
  if (!FORM_IN_PAGE.test(ev.html || "")) return;
  if (ev.installedFormPlugin) return;
  assert.equal(
    Boolean(plugin.pass),
    Boolean(engine.pass),
    `pluginen ${plugin.pass ? "består" : "fejler"} (${plugin.label}), motoren ` +
      `${engine.pass ? "består" : "fejler"} (${engine.label}) — samme side, samme kilder`
  );
}

/** R4: de to universelle motorer er samme produkt og skal svare identisk. */
function contractR4(shared, published) {
  assert.equal(
    Boolean(published.pass),
    Boolean(shared.pass),
    `de to motorer er uenige om dommen: delt "${shared.label}" mod publiceret "${published.label}"`
  );
  assert.equal(
    published.label,
    shared.label,
    `samme dom, to forskellige etiketter: delt "${shared.label}" mod publiceret "${published.label}"`
  );
}

/**
 * R5: privatlivslinket læses ens, begge veje.
 *
 * Udløseren er en **lukket** `<form> … </form>`, fordi det er den eneste
 * formular de to universelle motorer tæller. Den formular der poster til en
 * ekstern tjeneste uden lukket `</form>` er ikke med, og det er ikke en
 * forglemmelse: pluginen er der bevidst strengere end motoren
 * (`docs/eucomply-forms-paritet.md`), og R1/R3 holder den forskel på plads.
 * En regel der krævede de tre motorer enige på den slags fixture ville være
 * rød af design — opgave 50 lavede den forskel med vilje.
 *
 * Pluginens negative retning dækkes af R2, og dens positive af den direkte
 * sprogtest nedenfor. Tilsammen med R1 og R4 dækker de alle tre motorer.
 */
function contractR5(shared, published, ev) {
  if (!FORM_IN_PAGE.test(ev.html || "")) return;
  const forventet = Boolean(ev.privacyLink);
  for (const [hvem, v] of [["motoren i repoet", shared], ["den publicerede motor", published]]) {
    assert.equal(
      Boolean(v.pass),
      forventet,
      `${hvem} ${v.pass ? "består" : "fejler"} (${v.label}), men portens egen sprogliste ` +
        `${forventet ? "kan se" : "kan ikke se"} et privatlivslink på en side med formular`
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

const engineVerdicts = new Map();
const sharedVerdicts = new Map();
for (const fixture of FIXTURES) {
  engineVerdicts.set(fixture.name, await engineVerdict(runPublishedScan, fixture));
  sharedVerdicts.set(fixture.name, await engineVerdict(runSharedScan, fixture));
}

/** Hent en fixture ved navn. Selftesten brugte indeks, og en ny fixture i midten
 *  ville have flyttet dem uden at nogen kunne se det. */
function fx(name) {
  const found = FIXTURES.find((f) => f.name === name);
  assert.ok(found, `porten har ingen fixture ved navn «${name}»`);
  return found;
}

for (const fixture of FIXTURES) {
  const ev = evidence(fixture);
  const engine = engineVerdicts.get(fixture.name);
  const shared = sharedVerdicts.get(fixture.name);

  await test(`R1 aldrig svagere: ${fixture.name}`, () => {
    contractR1(pluginVerdict(fixture), engine);
  });
  await test(`R2 formular uden link fejler altid: ${fixture.name}`, () => {
    contractR2(pluginVerdict(fixture), ev);
  });
  await test(`R3 strengere kræver en kilde: ${fixture.name}`, () => {
    contractR3(pluginVerdict(fixture), engine, ev);
  });
  await test(`R4 de to motorer er ens: ${fixture.name}`, () => {
    contractR4(shared, engine);
  });
  await test(`R5 privatlivslinket læses ens: ${fixture.name}`, () => {
    contractR5(shared, engine, ev);
  });
  await test(`R6 samme domme på en side med formular: ${fixture.name}`, () => {
    contractR6(pluginVerdict(fixture), engine, ev);
  });
}

await test("et privatlivslink i dansk, svensk og nederlandsk består i alle tre motorer", () => {
  const sprog = [
    "dansk formular med dansk privatlivslink",
    "svensk formular med svensk integritetsside",
    "nederlandsk formular med nederlandsk privacybeleid",
    "dansk privatlivsord kun i linkteksten, ikke i href'en",
  ];
  for (const navn of sprog) {
    const f = fx(navn);
    assert.ok(evidence(f).privacyLink, `portens egen liste kan ikke se privatlivslinket i «${navn}»`);
    const domme = [
      ["pluginen", pluginVerdict(f)],
      ["motoren i repoet", sharedVerdicts.get(navn)],
      ["den publicerede motor", engineVerdicts.get(navn)],
    ];
    for (const [hvem, v] of domme) {
      assert.equal(Boolean(v.pass), true, `${hvem} fejler (${v.label}) på «${navn}»`);
    }
  }
});

await test("danske vilkår uden privatliv fejler stadig i alle tre motorer", () => {
  const f = fx("dansk formular med kun danske vilkår, intet privatliv");
  assert.equal(evidence(f).privacyLink, false, "portens liste læser Handelsbetingelser som privatliv");
  for (const [hvem, v] of [
    ["pluginen", pluginVerdict(f)],
    ["motoren i repoet", sharedVerdicts.get(f.name)],
    ["den publicerede motor", engineVerdicts.get(f.name)],
  ]) {
    assert.equal(Boolean(v.pass), false, `${hvem} består (${v.label}) på en side uden privatlivsnotice`);
  }
});

await test("formularer i markup'en fører til begge domme i pluginen", () => {
  const withForm = FIXTURES.filter((f) => evidence(f).pageForm);
  assert.ok(withForm.length >= 2, "porten skal have fixtures med formularmarkup");
  const verdicts = withForm.map((f) => pluginVerdict(f));
  assert.ok(
    verdicts.some((v) => v.pass) && verdicts.some((v) => !v.pass),
    "alle fixtures med formularmarkup fik samme dom — formtjekket svarer ens altid"
  );
});

await test("en ulæselig forside er aldrig et bestående forms", () => {
  const dir = mkdtempSync(join(tmpdir(), "eucomply-forms-"));
  const file = join(dir, "fixture.json");
  writeFileSync(
    file,
    JSON.stringify({
      error: "cURL error 28: Operation timed out",
      active: ["wpforms-lite/wpforms.php"],
    })
  );
  const out = JSON.parse(
    execFileSync("php", [PROBE, file, "forms"], { encoding: "utf8" }).trim().split("\n").pop()
  );
  assert.equal(Boolean(out.forms.pass), false, "en ulæselig forside blev bestået");
  assert.equal(Boolean(out.forms.warn), true, "en ulæselig forside er hverken bestået eller advarsel");
  assert.match(out.forms.label, /could not read/, `etiketten siger ikke at tjekket ikke kørte: ${out.forms.label}`);
});

if (process.argv.includes("--selftest")) {
  // Beviser at porten kan fejle i begge retninger, og at den kan fejle på en
  // fejl i repoets egen fil. Uden dette er porten en påstand.
  const caught = [];
  /** Forventer at kontrakten bliver rød på dette par domme, og tæller det. */
  const expectRed = (name, contract, ...args) => {
    try {
      contract(...args);
      failures.push(`selftest: ${name} gav en grøn port — den kan ikke se den fejl`);
    } catch {
      caught.push(name);
    }
  };

  // 1. R1: pluginen består, motoren fejler.
  expectRed(
    "R1",
    contractR1,
    { pass: true, label: "Mutationens svar" },
    engineVerdicts.get(fx("håndbygget formular, intet privatlivslink").name)
  );

  // 2. R3: pluginen fejler uden en kilde, motoren består.
  const udenKilde = fx("en side uden privatliv noget som helst");
  expectRed(
    "R3",
    contractR3,
    { pass: false, label: "Mutationens svar" },
    engineVerdicts.get(udenKilde.name),
    evidence(udenKilde)
  );

  // 3. R2: en `<form>` uden privatlivslink må ikke bestå — heller ikke når
  //    WordPress siger, at der er en privatlivsside.
  expectRed(
    "R2",
    contractR2,
    { pass: true, label: "Mutationens svar" },
    evidence(fx("håndbygget formular, WordPress har en privatlivsside men siden linker den ikke"))
  );

  // 4. R4: de to universelle motorer må ikke svare forskelligt.
  expectRed(
    "R4",
    contractR4,
    { pass: true, label: "Mutationens svar" },
    { pass: false, label: "Den anden kopi" }
  );

  // 5. R5: alle tre motorer skal være enige med portens egen sprogliste. Denne
  //    case er portens modsvar på sig selv: en motor der består, mens porten
  //    ikke kan se noget privatlivslink, er den fejl R5 er skrevet til at se.
  const dansk = fx("dansk formular med dansk privatlivslink");
  const lukketForm = { pageForm: true, html: "<form></form>" };
  expectRed(
    "R5 (motor for læs)",
    contractR5,
    { pass: true, label: "Mutationens svar" },
    { pass: true, label: "Mutationens svar" },
    { pageForm: true, privacyLink: false, ...lukketForm }
  );
  // Og den anden retning: portens liste ser et link, en motor gør det ikke.
  expectRed(
    "R5 (motor ser ikke)",
    contractR5,
    { pass: true, label: "Mutationens svar" },
    { pass: false, label: "Mutationens svar" },
    { pageForm: true, privacyLink: true, ...lukketForm }
  );
  // Og beviset på portens egen liste: med den gamle engelsk/tyske liste er den
  // danske fixture et site uden privatlivslink, og R5 bliver rød, fordi
  // begge motorer består den.
  expectRed(
    "R5 (portens liste uden de nye sprog)",
    contractR5,
    { pass: true, label: "Mutationens svar" },
    { pass: true, label: "Mutationens svar" },
    evidence(dansk, ENGLISH_ONLY_PRIVACY_LINK)
  );

  // 6. R6: de to produkter svarer forskelligt på samme side — den retning R1
  //    ikke kan se, fordi den springer over når pluginen fejler.
  expectRed(
    "R6",
    contractR6,
    { pass: false, label: "Mutationens svar" },
    { pass: true, label: "Mutationens svar" },
    evidence(fx("dansk formular med dansk privatlivslink"))
  );

  /**
   * En mutation mod repoets egen fil: skriv en ændret kopi af
   * `plugin/eucomply.php`, kør portens egen regel på den, og kræv at den bliver
   * rød. Er den grøn, er porten ikke i stand til at se den fejl, den blev
   * skrevet til at se — og så er fundet ovenfor værdeløst.
   */
  const mutate = (name, before, after, fixture, contract, expectPass) => {
    const source = readFileSync(PLUGIN, "utf8");
    if (!source.includes(before)) {
      failures.push(
        `selftest: mutationen «${name}» fandt ikke den linje den erstatter i ` +
          `check_forms() — porten kan ikke længere bevise at den ser den fejl`
      );
      return;
    }
    const dir = mkdtempSync(join(tmpdir(), "eucomply-forms-mutant-"));
    const mutant = join(dir, "eucomply.php");
    writeFileSync(mutant, source.replace(before, after));
    const mutated = pluginVerdict(fixture, mutant);
    try {
      assert.equal(
        Boolean(mutated.pass),
        expectPass,
        `mutationen «${name}» gav ${mutated.label} i stedet for ${expectPass ? "bestået" : "fejl"}`
      );
    } catch (e) {
      failures.push(`selftest: ${e.message}`);
      return;
    }
    if (contract === contractR3) {
      expectRed(name, contractR3, mutated, engineVerdicts.get(fixture.name), evidence(fixture));
    } else if (contract === contractR6) {
      expectRed(name, contractR6, mutated, engineVerdicts.get(fixture.name), evidence(fixture));
    } else {
      expectRed(name, contractR1, mutated, engineVerdicts.get(fixture.name));
    }
  };

  // 6. Mutationen i den retning opgave 50 handler om: formularen i markup'en
  //    holdt op med at tælle. Det er præcis 1.3.15-adfærden, og porten skal
  //    blive rød på den fixture opgaven beskriver.
  mutate(
    "mutation: formularmarkup ignoreres",
    "$page_form      = (bool) ( $has_local_form || $has_remote_form );",
    "$page_form      = false; // mutation: en formular er kun et plugin",
    fx("håndbygget formular, intet privatlivslink"),
    contractR6,
    true
  );

  // 7. Mutationen i den anden retning: en fejl uden forudsigelse om der
  //    overhovedet er en formular. R1 er grøn på den, så kun R3 kan se den.
  mutate(
    "mutation: fejl uden kilde",
    "if ( ! $privacy_link && ! $privacy_page ) {",
    "if ( ! $privacy_link ) { // mutation: mangler privatliv, alt er en fejl",
    fx("WPForms installeret, privatlivsside sat, ingen formular på forsiden"),
    contractR3,
    false
  );

  /*
   * De to mutationer i opgave 51. Begge rører privatlivsmønsteret i
   * `check_forms()`, og begge er skrevet mod den lange linje, så de fejler med
   * "fandt ikke den linje den erstatter" den dag et nyt sprog kommer til i stedet
   * for at lade porten stå grøn på en mutation den ikke længere rammer.
   */
  const PRIVACY_LINE =
    "preg_match( '~privacy|privacy[_-]?policy|datenschutz|gdpr|privacypolicy|data[_-]?protection"
    + "|privatliv|persondata|databeskyttelse|integritetsskydd|dataskydd|personuppgifter"
    + "|persoonsgegevens|gegevensbescherming|confidentialit|privacidad|datos personales~i', $html )";

  // 8. Sprogene forsvinder — det er præcis fejlen opgave 51 retter, i pluginen.
  mutate(
    "mutation: de nye sprog forsvinder",
    PRIVACY_LINE,
    "preg_match( '~privacy|privacy[_-]?policy|datenschutz|gdpr|privacypolicy|data[_-]?protection~i', $html )",
    fx("dansk formular med dansk privatlivslink"),
    contractR6,
    false
  );

  // 9. En "forbedring" der kun læser `href`. Den må ikke slå den side hvor
  //    privatlivsordet kun står i den tekst, brugeren ser.
  mutate(
    "mutation: kun href",
    PRIVACY_LINE,
    String.raw`preg_match( '~href\s*=\s*["\'][^"\']*(?:privacy|privatliv|persondata)[^"\']*["\']~i', $html )`,
    fx("dansk privatlivsord kun i linkteksten, ikke i href'en"),
    contractR6,
    false
  );

  const forventet = 12;
  if (caught.length !== forventet) {
    failures.push(`selftest: forventede ${forventet} negative cases fanget, fangede ${caught.length}`);
  } else {
    passed += forventet;
  }
}

if (failures.length) {
  for (const f of failures) console.error(`FAIL  ${f}`);
  console.error(`${failures.length} FORMS-PARITET FEJL`);
  process.exit(1);
}
console.log(
  `${passed} forms-paritetstest bestået — ${FIXTURES.length} fixtures, aldrig svagere end den gratis scanner`
);
