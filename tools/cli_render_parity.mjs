#!/usr/bin/env node
/**
 * Mål om den PUBLICEREDE pakke kun har ÉN renderer af rapporten, og om alt
 * den viser, er den motorens egen udskrift.
 *
 * Baggrund — målt 28/9 2026, ikke formodet
 * -----------------------------------------
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
 * Da `bin` var rettet, lå **to gengivelser mere** af samme rapport i pakken, og
 * begge var håndskrevne:
 *
 *   | fil                        | hvad den påstod                          | målt                     |
 *   |----------------------------|------------------------------------------|--------------------------|
 *   | `examples/sample-output.txt` | `Score: 2/9 (22%)`, wordpress.org, **6 af 9 rækker**, 0 `💡` | aldrig motorens output   |
 *   | `examples/node.js`         | tredje renderer: `Score: n/m (…)` + kun etiketten pr. række | tredje sprog i samme pakke |
 *   | `README.md` "Example output" | `Score: 5/8 (62%)` for example.com, 5 domme | et tal motoren aldrig printer |
 *
 * Det er samme fejl som ovenfor, flyttet fra `site/cli/` ind i npm-pakken — og
 * ingen af dem var synlig, fordi der ikke var noget at sammenligne med. Derfor
 * er de nu **genereret** og **målt**.
 *
 * Otte regler
 * -----------
 * **R1** `bin`'s stdout mod fixture'en skal være byte-identisk med
 * `renderReport(runScan(...))` på **samme** fixture. Kun `Duration: <heltal>ms`
 * må afvige: det er en måling af det kørende øjeblik, alt andet er deterministisk.
 *
 * **R2** Ingen anden publiceret fil end motoren må bruge rapportens felter
 * (`report.score`, `report.checks`, `report.platform`, `report.durationMs`) —
 * de kan kun bruges til at gengive rapporten. Dom-ikonerne er *målt* undtaget:
 * `❌` står også i `bin`s egen fejludskrift (`console.error('❌ Error:')`), så
 * et naivt "ingen ikoner" ville være rød på rigtig kode.
 *
 * **R3** `'✅'` og `'⚠️'` må findes i **præcis én** fil i den publicerede kode, og
 * den skal eksportere `renderReport`. Det er den regel der gør to renderer
 * umulige i stedet for rettet én gang. R2 og R3 måles over **alle** `.js`-filer
 * under `cli/`, `engine/` og `examples/`, fordi de to eksempler netop var den
 * tredje og fjerde renderer.
 *
 * **R4** Udskriften skal indeholle det **delte** score og mindst én
 * `- not counted:`-linje. Uden denne regel kunne motoren engang miste den delte
 * tale, og så ville R1 være grøn af en grund den ikke måtte være grøn af.
 *
 * **R5** `examples/sample-output.txt` skal være `bin`'s **eigne** stdout mod
 * fixture'en, byte-identisk undtagen varigheden. Filen er det, en læser af
 * npm-siden kopierer for at se hvad de får — så den skal være den rigtige
 * udskrift, ikke en håndskrevet.
 *
 * **R6** Samme krav til README'ens "Example output": hver linje i blokken skal
 * findes **ordret** i `sample-output.txt` (varigheden normaliseret), og blokken
 * skal have mindst ét `Score:`-tal og mindst fem domme. Uden R6 kunne README
 * igen vise `Score: 5/8 (62%)`, et tal motoren aldrig printer.
 *
 * **R7** README'en skal dokumentere den delte tale. Den skal nævne
 * `pct_applicable`, `applicable_total`, `passed_applicable` og `conditional` —
 * ellers peger den på det forudindtagede ni-tal som om det var det eneste tal.
 *
 * **R8** README'en skal dokumentere `renderReport()`. Det er den funktion
 * eksemplet i `examples/node.js` kalder, så en læser der vil skrive sit eget
 * program skal kunne finde den.
 *
 * Kør:
 *   node tools/cli_render_parity.mjs
 *   node tools/cli_render_parity.mjs --selftest
 *   node tools/cli_render_parity.mjs --write    # regenerér eksempelfilen
 */

import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { installFixtureFetch } from "./cli_example_run.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const PKG = path.join(ROOT, "eucomply-scanner");
const FIXTURE = path.join(ROOT, "tools", "fixtures", "webflow.com.json");
const RUNNER = path.join(ROOT, "tools", "cli_example_run.mjs");
const BIN = path.join(PKG, "cli", "eucomply.js");
const ENGINE = path.join(PKG, "engine", "index.js");
const SAMPLE = path.join(PKG, "examples", "sample-output.txt");
const README = path.join(PKG, "README.md");

/** Mapperne hver publiceret fil må ligge i — R2/R3 måles over dem alle. */
const PUBLISHED_DIRS = ["cli", "engine", "examples"];

/** Den ene måling der ikke er deterministisk. */
const DURATION_RE = /(Duration: )\d+(ms)/g;

/** Rapportens egne felter. De kan kun bruges til at gengive rapporten. */
const REPORT_FIELDS = ["report.score", "report.checks", "report.platform", "report.durationMs"];

/** Kun ikoner der *kun* bruges i rendererens domrækker. Målt, ikke antaget. */
const RENDERER_ONLY_ICONS = ["'✅'", "'⚠️'"];

/** README-blokken skal have mindst så mange domme, ellers er den en tom skal. */
const README_MIN_VERDICTS = 5;

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

/** Alle publicerede JS-filer, som `{ "cli/eucomply.js": kildekode }`. */
export function publishedSources() {
  const out = {};
  for (const dir of PUBLISHED_DIRS) {
    const base = path.join(PKG, dir);
    for (const name of fs.readdirSync(base).sort()) {
      if (name.endsWith(".js")) out[`${dir}/${name}`] = readFile(path.join(base, name));
    }
  }
  return out;
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

/** Første afvigende linje, eller -1 hvis ingen linje afviger (kun længden gør). */
function firstDiff(a, b) {
  for (let n = 0; n < Math.max(a.length, b.length); n++) {
    if (a[n] !== b[n]) return n;
  }
  return -1;
}

/** R5: filen skal være `bin`'s egen udskrift, kun varigheden må afvige. */
export function sampleFindings(sample, want) {
  const got = normalise(sample).replace(/\n+$/, "");
  const engine = normalise(want).replace(/\n+$/, "");
  if (got === engine) return [];
  const g = got.split("\n");
  const w = engine.split("\n");
  const at = firstDiff(g, w);
  return [
    `R5: examples/sample-output.txt afviger fra bin's egen udskrift i linje ${at + 1} — ` +
      `${at < 0 ? `linjetallene er ${g.length} mod ${w.length}` : `filen: ${g[at] ?? "<slutter>"} / bin: ${w[at] ?? "<slutter>"}`}. ` +
      "Kør `node tools/cli_render_parity.mjs --write`. Filen er det en læser af " +
      "npm-siden kopierer, så den skal være den rigtige udskrift.",
  ];
}

/** R2 og R3 på kilderne. Også ren, så selftesten kan mutere en kildekopi. */
export function sourceFindings(files) {
  const out = [];
  const engine = files["engine/index.js"] || "";
  // Kun **kode** tæller. En docstring må gerne *nævne* `report.score.pct` for at
  // forklare hvilket tal en læser skal bruge — det er præcis det
  // `examples/node.js` gør, og det er ikke en renderer. Uden den skelnen ville
  // porten være rød på den kode, der forklarer reglen.
  const code = (src) =>
    src
      .replace(/\/\*[\s\S]*?\*\//g, " ")
      .replace(/^[ \t]*\/\/.*$/gm, " ")
      .replace(/\/\/[^\n]*/g, " ");
  for (const [name, src] of Object.entries(files)) {
    if (name === "engine/index.js") continue;
    const body = code(src);
    for (const field of REPORT_FIELDS) {
      if (body.includes(field)) {
        out.push(
          `R2: ${name} bruger ${field} — ingen anden fil end motoren må formatere ` +
            "rapporten. Lad renderReport() skrive den.",
        );
      }
    }
  }
  for (const icon of RENDERER_ONLY_ICONS) {
    const where = Object.entries(files)
      .filter(([, src]) => code(src).includes(icon))
      .map(([name]) => name);
    if (where.length !== 1) {
      out.push(
        `${icon} findes i ${where.length} filer (${where.join(", ") || "ingen"}) — ` +
          "dom-ikonerne må kun findes i den fil der eksporterer renderReport().",
      );
    }
  }
  if (!/export function renderReport|export const renderReport/.test(engine)) {
    out.push("R3: engine/index.js skal eksportere renderReport() — det er den ene renderer.");
  }
  return out;
}

/** Blokken under README'ens "### Example output" — de ```-klammede linjer. */
export function readmeBlock(readme) {
  const m = readme.match(/###\s+Example output[\s\S]*?```\n([\s\S]*?)```/);
  return m ? m[1].replace(/\n+$/, "") : null;
}

/** R6, R7 og R8 på README'en. Ren, så selftesten kan mutere en tekst. */
export function readmeFindings(readme, sample) {
  const out = [];
  const block = readmeBlock(readme);
  if (block === null) {
    return [
      "R6: README.md har ingen kodeblok under `### Example output` — eksemplet kan " +
        "så ikke efterprøves mod motorens egen udskrift",
    ];
  }
  // R6: hver linje skal findes ordret i den genererede fil. Varigheden er
  // normaliseret, fordi den er den ene måling af det kørende øjeblik.
  const have = new Set(normalise(sample).replace(/\n+$/, "").split("\n"));
  const lines = block.split("\n");
  for (const [n, line] of lines.entries()) {
    const norm = normalise(line);
    // Tomme linjer og kommandolinjen er ikke rapportens udskrift.
    if (norm.trim() === "" || norm.startsWith("$ ")) continue;
    if (!have.has(norm)) {
      out.push(
        `R6: README'ens Example output afviger fra examples/sample-output.txt i ` +
          `linje ${n + 1}: ${norm.trim()}`,
      );
      break;
    }
  }
  const verdicts = lines.filter((l) => /^ (?:✅|⚠️|❌) /.test(l)).length;
  if (verdicts < README_MIN_VERDICTS) {
    out.push(
      `R6: README'ens Example output viser ${verdicts} domme — den skal vise mindst ` +
        `${README_MIN_VERDICTS}, ellers er den et eksempel på et eksempel.`,
    );
  }
  if (!lines.some((l) => /Score:.*\d+\/\d+/.test(l))) {
    out.push(
      "R6: README'ens Example output skal vise et score-tal fra den rigtige " +
        "udskrift, ellers læseren ikke hvad de får.",
    );
  }
  // R7: den delte tale skal være dokumenteret, ellers peger README på det
  // forudindtagede ni-tal som om det var det eneste tal.
  for (const field of ["pct_applicable", "applicable_total", "passed_applicable", "conditional"]) {
    if (!readme.includes(field)) {
      out.push(
        `R7: README.md skal dokumentere score.${field} — rapporten har to tal, og ` +
          "uden den anden peger dokumentationen kun på det forudindtagede ni-tal.",
      );
    }
  }
  // R8: den funktion eksemplet kalder skal kunne findes.
  if (!/renderReport\s*\(/.test(readme)) {
    out.push(
      "R8: README.md skal dokumentere renderReport(report) — det er den funktion " +
        "eksemplet i examples/node.js kalder, og den eneste renderer i pakken.",
    );
  }
  return out;
}

// ------------------------------------------------------------------ måling

export async function measure() {
  const got = runBin();
  const want = await runEngine();
  const files = publishedSources();
  const sample = readFile(SAMPLE);
  const readme = readFile(README);
  return {
    got,
    want,
    sample,
    readme,
    findings: [
      ...outputFindings(got, want),
      ...sourceFindings(files),
      ...sampleFindings(sample, got),
      ...readmeFindings(readme, sample),
    ],
  };
}

// ---------------------------------------------------------------- selftest

export async function selftest() {
  const want = await runEngine();
  const good = runBin();
  const files = publishedSources();
  const sample = good;
  const readme = readFile(README);
  const cases = [];
  // `green` = casen skal være fund-fri. Uden den markering ville selftesten
  // være rød på præcis den kørsel, der skal være grøn — en port der kun kan
  // finde fejl, men ikke bekræfte det rigtige, er halvtestet.
  const push = (name, findings, green = false) => cases.push([name, findings, green]);

  push("repoets egen pakke -> 0 fund", [
    ...outputFindings(good, want),
    ...sourceFindings(files),
    ...sampleFindings(sample, good),
    ...readmeFindings(readme, sample),
  ], true);

  // 1. Den fejl der lå i `main` før iteration 102: den rå ni-tal-score, ingen
  //    not-counted, ingen råd. Den skal fanges, og den skal fanges af R1.
  const rawNine = good
    .replace(/ of the checks that apply to this site \(\d+%\)/, "")
    .replace(/^ {3}- not counted: .*\n/gm, "")
    .replace(/^ {3}All \d+ checks: /gm, "   Score:    ")
    .replace(/^ {4}💡 .*\n/gm, "");
  push("bin der printer det rå ni-tal uden råd (iteration 102s fejl) -> R1", outputFindings(rawNine, want));
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
  const binWithRenderer = { ...files, "cli/eucomply.js": `${files["cli/eucomply.js"]}\nconsole.log(\`   Score:    \${report.score.pct}%\`);` };
  push("bin med sin egen rendering (iteration 102s fejl) -> R2 + R3", sourceFindings(binWithRenderer));
  if (!sourceFindings(binWithRenderer).some((f) => f.startsWith("R2:"))) {
    console.log("  FEJL    en bin der selv renderer fanges ikke af R2");
  }

  // 4. Det er den mutation der bragte den TREDJE renderer ind i pakken:
  //    `examples/node.js` formaterede selv rapporten. R2 og R3 måles nu over
  //    alle publicerede filer, så den fanges samme sted som bin's.
  const exampleRenderer = {
    ...files,
    "examples/node.js": `${files["examples/node.js"]}\nfor (const c of Object.values(report.checks)) console.log(\`  \${c.pass ? '✅' : '❌'} \${c.label}\`);`,
  };
  push("eksempel med sin egen rendering (iteration 103s fejl) -> R2 + R3", sourceFindings(exampleRenderer));
  if (!sourceFindings(exampleRenderer).some((f) => f.startsWith("R2:"))) {
    console.log("  FEJL    et eksempel der selv renderer fanges ikke af R2");
  }

  // 5. R3 alene: ikonerne i to filer, uden at nogen af dem rører rapportens felter.
  const binWithIcon = { ...files, "cli/eucomply.js": `${files["cli/eucomply.js"]}\nconst x = check.pass ? '✅' : '⚠️';\n` };
  push("renderer-ikon i to filer -> R3", sourceFindings(binWithIcon));

  // 6. R3: motoren holdt op med at **eksportere** rendereren, men har den stadig
  //    — så dom-ikonerne ligger i præcis én fil, og det er alene
  //    eksport-reglen der skal fange det.
  const unexported = { ...files, "engine/index.js": files["engine/index.js"].replace("export function renderReport", "function renderReport") };
  const unexportedFindings = sourceFindings(unexported);
  push("motoren eksporterer ikke renderReport -> R3", unexportedFindings);
  if (!unexportedFindings.some((f) => f.includes("skal eksportere renderReport"))) {
    console.log("  FEJL    en motor der ikke eksporterer renderReport fanges ikke af R3");
  }

  // 7. R5: den håndskrevne `examples/sample-output.txt` fra før denne
  //    iteration — wordpress.org, `Score: 2/9 (22%)`, seks af ni rækker.
  const handSample = [
    "",
    "🔍 EUComply Scan Report",
    "   URL:      https://wordpress.org/",
    "   Platform: WordPress 7.2-alpha-63343",
    "   Duration: 877ms",
    "   Score:    2/9 (22%)",
    "",
    " ❌ No Google Consent Mode v2 detected",
    " ❌ No IAB TCF detected",
    " ❌ 1 tracker(s) with NO consent platform",
    " ✅ HTTPS + HSTS OK",
    " ⚠️ No consent banner detected",
    " ✅ Form(s) found, no consent link",
  ].join("\n");
  push("den håndskrevne sample-output.txt (dagens fejl) -> R5", sampleFindings(handSample, good));
  if (!sampleFindings(handSample, good).some((f) => f.startsWith("R5:"))) {
    console.log("  FEJL    den håndskrevne sample-output fanges ikke af R5");
  }

  // 8. R6: README'ens opdigtede `Score: 5/8 (62%)` — et tal motoren aldrig
  //    printer, fordi det hverken er ni-tallet eller det delte.
  const fiveOfEight = readme.replace(/^   Score: .*$/m, "   Score:    5/8 (62%)");
  push("README med det opdigtede 5/8 (62%) (dagens fejl) -> R6", readmeFindings(fiveOfEight, sample));
  if (!readmeFindings(fiveOfEight, sample).some((f) => f.startsWith("R6:"))) {
    console.log("  FEJL    README'ens opdigtede score fanges ikke af R6");
  }

  // 9. R6: en blok der kun viser ét domme og intet score-tal — den skal være
  //    rød, ellers kunne eksemplet slankes til ingenting uden at nogen mærker
  //    det. Blokken er fundet med `readmeBlock`, så mutationen ikke kan ramme en
  //    anden kodeblok i README'en.
  const thin = readme.replace(
    /### Example output[\s\S]*?```\n[\s\S]*?```/,
    () => "### Example output\n\n```\n ❌ 1 tracker(s) with NO consent platform\n```",
  );
  const thinFindings = readmeFindings(thin, sample);
  push("README uden scorelinje og med ét domme -> R6", thinFindings);
  if (!thinFindings.some((f) => f.startsWith("R6:"))) {
    console.log("  FEJL    en udslanket README-blok fanges ikke af R6");
  }

  // 10. R7: en README der kun dokumenterer det forudindtagede ni-tal — præcis
  //     den fejl, planen havde noteret som fundet.
  const oldApi = readme
    .replace(/pct_applicable/g, "pct")
    .replace(/applicable_total/g, "total")
    .replace(/passed_applicable/g, "passed")
    .replace(/conditional/g, "checks");
  push("README der kun dokumenterer ni-tallet -> R7", readmeFindings(oldApi, sample));
  if (!readmeFindings(oldApi, sample).some((f) => f.startsWith("R7:"))) {
    console.log("  FEJL    en README uden den delte tale fanges ikke af R7");
  }

  // 11. R8: en README der ikke nævner renderReport.
  push("README uden renderReport -> R8", readmeFindings(readme.replace(/renderReport\s*\(/g, "printReport("), sample));

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

  if (process.argv.includes("--write")) {
    const out = runBin() + "\n";
    fs.writeFileSync(SAMPLE, out, "utf8");
    console.log(`skrev ${path.relative(ROOT, SAMPLE)} (${out.split("\n").length - 1} linjer) fra bin mod ${path.basename(FIXTURE)}`);
    return 0;
  }

  const { got, sample, findings } = await measure();
  const g = got.split("\n");
  const s = sample.replace(/\n+$/, "").split("\n");
  const block = readmeBlock(readFile(README)) ?? "";
  console.log(`Publiceret pakke mod motorens renderer, samme fixture (${path.basename(FIXTURE)}):`);
  console.log(`  bin:            ${g.length} linjer, ${g.filter((l) => /^ (?:✅|⚠️|❌) /.test(l)).length} domme, ${g.filter((l) => l.includes("💡")).length} råd`);
  console.log(`  sample-output:  ${s.length} linjer, ${s.filter((l) => /^ (?:✅|⚠️|❌) /.test(l)).length} domme`);
  console.log(`  README-blok:    ${block.split("\n").filter((l) => l.trim() && !l.startsWith("$ ")).length} linjer hentet fra sample-output`);
  console.log(`  publiceret .js: ${Object.keys(publishedSources()).join(", ")}`);
  for (const f of findings) console.log(`  - ${f}`);
  if (findings.length) {
    console.log(`\nFEJL — ${findings.length} fund: pakken har mere end én renderer, eller noget den viser er ikke motorens rapport.`);
    return 1;
  }
  console.log(`\nOK    én renderer i hele pakken, og alt den viser er motorens egen udskrift.`);
  return 0;
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  process.exit(await main());
}
