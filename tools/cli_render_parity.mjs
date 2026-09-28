#!/usr/bin/env node
/**
 * Mål om den PUBLICEREDE `bin` skriver præcis motorens egen rapport.
 *
 * Baggrund — målt 28/9 2026, ikke formodet
 * ----------------------------------------
 * Pakken havde **to renderere af den samme rapport**:
 *
 *   |                        | `cli/eucomply.js` (**bin**) | `engine/index.js`'s `main()` |
 *   |------------------------|-----------------------------|--------------------------------|
 *   | Score                  | `3/9 (33%)`                 | `3/6 of the checks that apply to this site (50%)` + `All 9 checks: 3/9 (33%)` |
 *   | Betingede rækker       | nævnt **ikke**              | `- not counted: tcf — …`      |
 *   | Råd                    | **0 `💡`-linjer**           | `💡` på 6 af 9 rækker          |
 *
 * `main()` kører kun når motorfilen selv er `argv[1]`, altså aldrig for en
 * bruger der har `npm install`et pakken. Hele den gratis scanner printer altså
 * det forudindtagede ni-tal og dropper både rådet og forklaringen på hvorfor tre
 * rækker ikke tæller, mens `/scan/` og `/pro/sample-report/` bruger den delte
 * tale. To sprog i én pakke, og det dårligere stod i det program folk kører.
 *
 * Rettelsen er `renderReport(report)` i motoren, som begge kalder. Denne gate
 * er den der gør den permanent — ellers kommer den anden renderer tilbage,
 * fordi der altid er en grund til at tilføje lidt i `bin`.
 *
 * Fire regler
 * -----------
 * **R1** `bin`'s stdout mod fixture'en skal være byte-identisk med
 * `renderReport(runScan(...))` på **samme** fixture. Kun `Duration: <heltal>ms`
 * må afvige: det er en måling af det kørende øjeblik, alt andet er deterministisk.
 *
 * **R2** `bin` må ikke selv formatere rapporten. Dom-ikonerne er *målt* undtaget:
 * `❌` står også i `bin`'s egen fejludskrift (`console.error('❌ Error:')`), så
 * et naivt "ingen ikoner" ville være rød på rigtig kode. Det der forbydes er
 * derfor **rapportens** felter — `report.score`, `report.checks`,
 * `report.platform`, `report.durationMs` — for de kan kun bruges til at
 * gengive rapporten.
 *
 * **R3** `'✅'` og `'⚠️'` må findes i **præcis én** fil i den publicerede kode
 * (`cli/` + `engine/`), og den fil skal eksportere `renderReport`. Det er den
 * regel der gør "to renderere" umuligt i stedet for rettet én gang.
 *
 * **R4** Udskriften skal indeholde det **delte** score og mindst én
 * `- not counted:`-linje. Uden denne regel kunne motoren engang miste den delte
 * tale, og så ville R1 være grøn af en grund den ikke måtte være grøn af — præcis
 * den fejlretning `check_score_split.py` holder sitet op mod.
 *
 * Kør:
 *   node tools/cli_render_parity.mjs
 *   node tools/cli_render_parity.mjs --selftest
 */

import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { installFixtureFetch } from "./cli_example_run.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const FIXTURE = path.join(ROOT, "tools", "fixtures", "webflow.com.json");
const RUNNER = path.join(ROOT, "tools", "cli_example_run.mjs");
const BIN = path.join(ROOT, "eucomply-scanner", "cli", "eucomply.js");
const ENGINE = path.join(ROOT, "eucomply-scanner", "engine", "index.js");

/** Den ene undtagelse: tallet i `Duration: <heltal>ms`. */
const DURATION_RE = /(Duration: )\d+(ms)/g;

/** Rapportens egne felter. De kan kun bruges til at gengive rapporten. */
const REPORT_FIELDS = ["report.score", "report.checks", "report.platform", "report.durationMs"];

/** Kun ikoner der *kun* bruges i rendererens domrækker. Målt, ikke antaget. */
const RENDERER_ONLY_ICONS = ["'✅'", "'⚠️'"];

function readFile(p) {
  return fs.readFileSync(p, "utf8");
}

/** Sæt den ene måling til en pladsholder, så to kørsler kan sammenlignes. */
export function normalise(text) {
  return text.replace(DURATION_RE, "$1<int>$2").replace(/\r\n/g, "\n");
}

/** Den publicerede `bin` kørt mod fixture'en — dens rigtige stdout, i en proces. */
export function runBin(fixture = FIXTURE) {
  const fixtureUrl = JSON.parse(readFile(fixture)).url;
  return execFileSync("node", [RUNNER, fixture, fixtureUrl], {
    cwd: ROOT,
    encoding: "utf8",
    maxBuffer: 8 * 1024 * 1024,
  }).replace(/\r\n/g, "\n").replace(/\n+$/, "");
}

/** Motorens egen renderer, i samme proces og mod samme optagelse. */
export async function runEngine(fixture = FIXTURE) {
  const { url } = JSON.parse(readFile(fixture));
  const stub = installFixtureFetch(JSON.parse(readFile(fixture)));
  try {
    const engine = await import(pathToFileURL(ENGINE).href);
    if (typeof engine.renderReport !== "function") {
      throw new Error("renderReport er ikke eksporteret fra motoren");
    }
    const report = await engine.runScan(url);
    return normalise(engine.renderReport(report));
  } finally {
    stub.restore();
  }
}

// ------------------------------------------------------------------- regler

/**
 * R1 og R4 på to strenge. Ren funktion, så selftesten kan mutere en
 * udskrift uden at køre motoren igen for hvert tilfælde.
 */
export function outputFindings(got, want) {
  const out = [];
  if (normalise(got).replace(/\n+$/, "") !== want.replace(/\n+$/, "")) {
    const g = normalise(got).replace(/\n+$/, "").split("\n");
    const w = want.replace(/\n+$/, "").split("\n");
    const i = next(
      (n) => (g[n] !== w[n]),
      Math.min(g.length, w.length),
    );
    out.push(
      `R1: bin's udskrift afviger fra motorens renderer i linje ${i + 1} — ` +
        `bin: ${g[i] ?? "<slutter>"} / motoren: ${w[i] ?? "<slutter>"}. ` +
        "En af de to renderer ikke længere motorens rapport.",
    );
  }
  if (!want.includes(" of the checks that apply to this site (")) {
    out.push(
      "R4: motorens rapport skal have det delte score — kun de checks der " +
        "gælder for sitet. Uden det er ni-tallet alene det forudindtagede tal.",
    );
  }
  if (!/^ {3}- not counted: /m.test(want)) {
    out.push(
      "R4: rapporten skal sige hvilke rækker der ikke tæller (`- not counted:`) — " +
        "ellers ved læseren ikke hvorfor scoren er lavere end antallet af rækker.",
    );
  }
  return out;
}

/** Første indeks hvor to lister afviger — så fundet peger på den linje, ikke på filen. */
function next(pred, from) {
  for (let n = from; n < from + 200; n++) if (pred(n)) return n;
  return from;
}

/** R2 og R3 på kilderne. Også ren, så selftesten kan mutere en kildekopi. */
export function sourceFindings(binSource, engineSource) {
  const out = [];
  for (const field of REPORT_FIELDS) {
    if (binSource.includes(field)) {
      out.push(
        `R2: cli/eucomply.js bruger ${field} — bin må ikke selv formatere ` +
          "rapporten. Lad motorens renderReport() skrive den.",
      );
    }
  }
  const files = { "cli/eucomply.js": binSource, "engine/index.js": engineSource };
  for (const icon of RENDERER_ONLY_ICONS) {
    const where = Object.entries(files)
      .filter(([, src]) => src.includes(icon))
      .map(([name]) => name);
    if (where.length !== 1) {
      out.push(
        `${icon} findes i ${where.length} filer (${where.join(", ") || "ingen"}) — ` +
          "dom-ikonerne må kun findes i den fil der eksporterer renderReport().",
      );
    }
  }
  if (!/export function renderReport|export const renderReport/.test(engineSource)) {
    out.push("R3: engine/index.js skal eksportere renderReport() — det er den ene renderer.");
  }
  return out;
}

// ------------------------------------------------------------------ måling

export async function measure() {
  const got = runBin();
  const want = await runEngine();
  return {
    got,
    want,
    findings: [
      ...outputFindings(got, want),
      ...sourceFindings(readFile(BIN), readFile(ENGINE)),
    ],
  };
}

// ---------------------------------------------------------------- selftest

export async function selftest() {
  const want = await runEngine();
  const good = runBin();
  const cases = [];
  // `green` = casen skal være fund-fri. Uden den markering ville selftesten
  // være rød på præcis den kørsel, der skal være grøn — en port der kun kan
  // finde fejl, men ikke bekræfte det rigtige, er halvtestet.
  const push = (name, findings, green = false) => cases.push([name, findings, green]);

  push("repoets egen bin mod motorens renderer -> 0 fund", [
    ...outputFindings(good, want),
    ...sourceFindings(readFile(BIN), readFile(ENGINE)),
  ], true);

  // 1. Den fejl der lå i `main` før denne iteration: den rå ni-tal-score, ingen
  //    not-counted, ingen råd. Den skal fanges, og den skal fanges af R1.
  const rawNine = good
    .replace(/ of the checks that apply to this site \(\d+%\)/, "")
    .replace(/^ {3}- not counted: .*\n/gm, "")
    .replace(/^ {3}All \d+ checks: /gm, "   Score:    ")
    .replace(/^ {4}💡 .*\n/gm, "");
  push("bin der printer det rå ni-tal uden råd (dagens fejl) -> R1", outputFindings(rawNine, want));
  if (!outputFindings(rawNine, want).some((f) => f.startsWith("R1:"))) {
    console.log("  FEJL    den rå ni-tal-udskrift fanges ikke af R1");
  }

  // 2. R4 skal være rød, selv når de to udskrifter er ens — en motor der engang
  //    mister den delte tale ville ellers være grøn af en grund den ikke måtte.
  const noSplit = want
    .replace(/^ {3}Score: .*$/m, "   Score:    3/9 (33%)")
    .replace(/^ {3}- not counted: .*$/gm, "");
  push("en rapport uden delt score og uden not-counted -> R4", outputFindings(noSplit, noSplit));

  // 3. R2: en `bin` der selv renderer. Det er den mutation der bragte den anden
  //    renderer ind i pakken.
  const binWithRenderer = `${readFile(BIN)}\nconsole.log(\`   Score:    \${report.score.pct}%\`);`;
  push("bin med sin egen rendering (dagens fejl) -> R2 + R3", sourceFindings(binWithRenderer, readFile(ENGINE)));
  if (!sourceFindings(binWithRenderer, readFile(ENGINE)).some((f) => f.startsWith("R2:"))) {
    console.log("  FEJL    en bin der selv renderer fanges ikke af R2");
  }

  // 4. R3 alene: ikonerne i to filer, uden at nogen af dem rører rapportens felter.
  const binWithIcon = `${readFile(BIN)}\nconst x = check.pass ? '✅' : '⚠️';\n`;
  push("renderer-ikon i to filer -> R3", sourceFindings(binWithIcon, readFile(ENGINE)));

  // 5. R3: motoren holdt op med at eksportere rendereren.
  push("motoren eksporterer ikke renderReport -> R3", sourceFindings(readFile(BIN), "export function runScan(){}"));

  let fails = 0;
  for (const [name, findings, green] of cases) {
    if (green) {
      if (findings.length === 0) console.log(`  fanget  ${name}`);
      else {
        console.log(`  FEJL    ${name}: ${findings[0]}`);
        fails++;
      }
      continue;
    }
    if (findings.length === 0) {
      console.log(`  FEJL    ${name}: forventede fund, fik 0`);
      fails++;
    } else {
      console.log(`  fanget  ${name}: ${findings[0].slice(0, 90)}…`);
    }
  }
  console.log(fails ? `\nSELFTEST RØD — ${fails} af ${cases.length} cases fejlede.` : `\nSELFTEST GRØN — alle ${cases.length} negative cases fanges.`);
  return fails;
}

// --------------------------------------------------------------------- main

async function main() {
  if (process.argv.includes("--selftest")) return (await selftest()) ? 1 : 0;

  const { got, want, findings } = await measure();
  const g = got.split("\n");
  console.log(`Publiceret bin mod motorens renderer, samme fixture (${FIXTURE.split("/").pop()}):`);
  console.log(`  bin:    ${g.length} linjer, ${g.filter((l) => /^ (?:✅|⚠️|❌) /.test(l)).length} domme, ${g.filter((l) => l.includes("💡")).length} råd`);
  console.log(`  motoren: ${want.split("\n").length} linjer efter normalisering af varigheden`);
  for (const f of findings) console.log(`  - ${f}`);
  if (findings.length) {
    console.log(`\nFEJL — ${findings.length} fund: bin's rapport er ikke motorens rapport.`);
    return 1;
  }
  console.log(`\nOK    bin skriver præcis motorens egen rapport — delt score, not-counted og råd med i.`);
  return 0;
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  process.exit(await main());
}
