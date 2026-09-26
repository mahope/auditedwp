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
 *
 * R1 og R3 er de to retninger, porten skal kunne fejle i. R2 er den, opgaven
 * kræver målt på fixtures og ikke på kode.
 *
 * Ingen dependencies, intet netværk: fetch stubbes, og målet er et IP-literal,
 * så assertPublicTarget ikke slår DNS op. PHP'en svarer fra en fixture.
 * Specen for ændringen er `docs/eucomply-forms-paritet.md`.
 */

import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { runScan } from "../eucomply-scanner/engine/index.js";

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
/** Motorens `LEGAL_PATTERNS[0]`, som pluginen bruger uændret. */
const PRIVACY_LINK =
  /privacy|privacy[_-]?policy|datenschutz|gdpr|privacypolicy|data[_-]?protection/i;

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
    // Linket skrives som de mønstre, begge motorer læser, matcher: et dansk
    // "Privatlivspolitik" rammer ikke `privacy`, så en fixture på dansk ville
    // have testet et andet spørgsmål end det porten er skrevet til.
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

/** Kør den universelle motor mod den samme fixture. */
async function engineVerdict(fixture) {
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

/** Hvilke kilder fixturet faktisk viser. Porten læser fixturet, ikke pluginens svar. */
function evidence(fixture) {
  const html = fixture.html || "";
  return {
    pageForm: FORM_IN_PAGE.test(html) || FORM_WITH_EXTERNAL_ACTION.test(html),
    privacyLink: PRIVACY_LINK.test(html),
    installedFormPlugin: (fixture.active || []).some((f) => FORM_PLUGIN_FILES.includes(f)),
    privacyPageInWordPress: Boolean((fixture.options || {})["wp_page_for_privacy_policy"]),
  };
}

/*
 * De tre regler, som *kun* betinger. Porten og selftesten kalder de samme
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
for (const fixture of FIXTURES) {
  engineVerdicts.set(fixture.name, await engineVerdict(fixture));
}

for (const fixture of FIXTURES) {
  const ev = evidence(fixture);
  const engine = engineVerdicts.get(fixture.name);

  await test(`R1 aldrig svagere: ${fixture.name}`, () => {
    contractR1(pluginVerdict(fixture), engine);
  });
  await test(`R2 formular uden link fejler altid: ${fixture.name}`, () => {
    contractR2(pluginVerdict(fixture), ev);
  });
  await test(`R3 strengere kræver en kilde: ${fixture.name}`, () => {
    contractR3(pluginVerdict(fixture), engine, ev);
  });
}

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
  expectRed("R1", contractR1, { pass: true, label: "Mutationens svar" }, engineVerdicts.get(FIXTURES[0].name));

  // 2. R3: pluginen fejler uden en kilde, motoren består.
  expectRed("R3", contractR3, { pass: false, label: "Mutationens svar" }, engineVerdicts.get(FIXTURES[8].name), evidence(FIXTURES[8]));

  // 3. R2: en `<form>` uden privatlivslink må ikke bestå — heller ikke når
  //    WordPress siger, at der er en privatlivsside.
  expectRed("R2", contractR2, { pass: true, label: "Mutationens svar" }, evidence(FIXTURES[2]));

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
    } else {
      expectRed(name, contractR1, mutated, engineVerdicts.get(fixture.name));
    }
  };

  // 4. Mutationen i den retning opgaven handler om: formularen i markup'en holdt
  //    op med at tælle. Det er præcis 1.3.15-adfærden, og porten skal blive rød
  //    på den fixture opgaven beskriver.
  mutate(
    "mutation: formularmarkup ignoreres",
    "$page_form      = (bool) ( $has_local_form || $has_remote_form );",
    "$page_form      = false; // mutation: en formular er kun et plugin",
    FIXTURES[0],
    contractR1,
    true
  );

  // 5. Mutationen i den anden retning: en fejl uden forudsigelse om der
  //    overhovedet er en formular. R1 er grøn på den, så kun R3 kan se den.
  mutate(
    "mutation: fejl uden kilde",
    "if ( ! $privacy_link && ! $privacy_page ) {",
    "if ( ! $privacy_link ) { // mutation: mangler privatliv, alt er en fejl",
    FIXTURES[4],
    contractR3,
    false
  );

  if (caught.length !== 5) {
    failures.push(`selftest: forventede 5 negative cases fanget, fangede ${caught.length}`);
  } else {
    passed += 5;
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
