#!/usr/bin/env node
/**
 * Gate: den gratis scan-API er solgt uden en dør ind i den.
 *
 *     node tools/check_api_docs.mjs
 *     node tools/check_api_docs.mjs --selftest
 *
 * Baggrund, målt 28/9. `/vs/termly/` lovede i sin sammenligningstabel
 * **"API access: Free API + CLI"** for den gratis udgave — og den eneste
 * dokumentation af overfladen var tre filer i en npm-pakke, som ingen
 * læser først går og finder. En udvikler der gætter de URLs en
 * dokumenteret API plejer at have, fik 404 på alle tre:
 *
 *     /api/          findes ikke
 *     /docs/         findes ikke
 *     /developers/   findes ikke
 *
 * Det er samme fejlklasse som missionens første opgave: **vi sælger en
 * overflade uden en dør ind til den.** Og der er en målt fare ved at lade
 * den ligge: API'et virker faktisk. Fire endepunkter svarer 200 i dag, så
 * en læser der finder vejen hjem alene får et virkende svar om en
 * eksisterende, gratis tjeneste — og en læser der ikke gør, tror
 * opgaven enten er uafsluttet eller dyr.
 *
 * Derfor er dette en port, ikke en rapport. Fire regler, alle målbare mod
 * **repoets egne filer** — ingen af dem ringer til den udgivne worker, så
 * porten dør ikke i CI af et netværkshicik:
 *
 *   R1  Et endepunkt, `/api/` dokumenterer, skal være implementeret i
 *       `worker-scan/index.js`. En dokumenteret overflade der ikke
 *       findes er præcis den fejl, porten blev skrevet for — og den er
 *       dyrere for læseren, fordi den ser ud som om tjenesten er dyr.
 *   R2  En side der **lover API-adgang** skal linke til `/api/`. R2 er
 *       den regel, der gør døren permanent: en ny sammenligningsside der
 *       skriver "Free API" uden link er rød, så det kan ikke ske igen.
 *   R3  Workerens rute-grene skal være **nåelige**. Målt: `path` er
 *       normaliseret med `|| "/"`, så `path === ""` aldrig er sandt, og
 *       den service-info-gren var død kode. Live `GET /` svarer derfor
 *       404, selv om kilden indeholder en egen informationsgren for den.
 *   R4  `/api/` skal stå i `build_public_tree.py`s `PUBLIC_DIRS`. En
 *       dokumentationsside der ikke publiceres, er en dør ind til et
 *       rum uden vægge.
 *
 * R1 læser endepunkterne fra `data-endpoint`-markører i `<main>`, ikke ved
 * at gætte på prosa. Samme greb som `data-product` i `check_cta.py`:
 * markøren er erklæret, læsbar på ét sted og kan ikke glemmes ved en
 * omskrivning. Kun `<main>` læses — sidefoden indeholder BugBottles egen
 * `data-endpoint="https://mahope.tools/api/bugreport"`, som er et helt
 * andet API og ikke en rute i vores worker. Samme skelnen som
 * `check_store_ready.py` gør mellem header/footer og købsvej.
 *
 * Selftesten bygger et grønt fixture-træ og bryder så **én** regel ad
 * gangen. Den grønne case skal være rød, når den brydes — ellers kan
 * porten være grøn af en grund den aldrig har efterprøvet, hvilket er
 * præcis den fejl de foregående opgaver her måtte opdage i sig selv.
 */
import { readFileSync, existsSync, readdirSync, statSync, mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { join, relative } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";

const ROOT = fileURLToPath(new URL("..", import.meta.url));
const WORKER = join(ROOT, "worker-scan", "index.js");
const PUBLIC_TREE = join(ROOT, "tools", "build_public_tree.py");
const SITE = join(ROOT, "site");

// R2: de formuleringer, der sælger API-adgang. Holdt til den konkrete
// løfteform, der stod i tabellen — ikke til ordet "api", der også står i
// "eucomplypro.com/api/". En regel der ramte navnet ville være rød på
// den side, der er lavet for at fjerne fejlen.
const API_CLAIM = /(free\s+api|api\s+access|api-adgang|api\s+zugang)/gi;
const DOC_PAGE = "/api/";

// Sider der ikke skal linke til dokumentationen. `/api/` er selv
// dokumentationen, så den ville kræve et link til sig selv. Skrevet som
// én linje med sin begrundelse, så undtagelsen ikke ligner en vilkårlig
// smutvej: en ny undtagelse skal kunne argumenteres.
const SELF = new Set(["api/index.html"]);

// Søskeprodukter er deres egne sider med deres egne API'er og egne
// Stripeprodukter, så deres løfter er ikke vores at dømme her.
const SIBLINGS = new Set(["devnotify", "deskuptime", "transmute", "_partials", "shared"]);

const MAIN = /<main\b[^>]*>[\s\S]*?<\/main>/i;
const MARKER = /data-endpoint="([^"]+)"/gi;
const HREF = /href="([^"]+)"/gi;

function read(path) {
  try {
    return readFileSync(path, "utf8");
  } catch {
    return null;
  }
}

function walk(dir, out = []) {
  if (!existsSync(dir)) return out;
  for (const name of readdirSync(dir).sort()) {
    const full = join(dir, name);
    if (statSync(full).isDirectory()) {
      if (SIBLINGS.has(name)) continue;
      walk(full, out);
    } else if (name.endsWith(".html")) {
      out.push(full);
    }
  }
  return out;
}

function mainOf(html) {
  const found = MAIN.exec(html || "");
  return found ? found[0] : html || "";
}

/** R3: kan `path` aldrig være den tomme streng, givet normaliseringen? */
export function deadPathBranch(workerSource) {
  const assignment = /const\s+path\s*=\s*reqUrl\.pathname\.replace\([^)]*\)\s*\|\|\s*"([^"]*)"/.exec(
    workerSource,
  );
  if (!assignment) return null; // normaliseringen er ikke denne form — porten må tie
  const fallback = assignment[1];
  const hasEmptyTest = /path\s*===\s*""/.test(workerSource);
  if (fallback === "" || !hasEmptyTest) return null;
  return fallback;
}

/** R1: ruterne workeren faktisk implementerer. */
export function implementedRoutes(workerSource) {
  const routes = new Set();
  for (const m of workerSource.matchAll(/path\s*===\s*"(\/[^"]*)"/g)) routes.add(m[1]);
  // Faldgrenen: `path !== "" && path !== "/scan"` lader alt andet gå til
  // 404, så den rute der står i betingelsen er en af dem der serveres.
  const guard = /path\s*!==\s*""\s*&&\s*path\s*!==\s*"(\/[^"]*)"/.exec(workerSource);
  if (guard) routes.add(guard[1]);
  return routes;
}

export function collect({ site = SITE, worker = WORKER, treeScript = PUBLIC_TREE } = {}) {
  const findings = [];
  const source = read(worker);
  if (source === null) {
    findings.push("worker-scan/index.js: kan ikke læses — R1 og R3 kan da ikke efterprøves");
    return findings;
  }

  // R3 — døde rute-grene.
  const fallback = deadPathBranch(source);
  if (fallback !== null) {
    findings.push(
      `worker-scan/index.js: path er normaliseret med || "${fallback}", så ` +
        `path === "" er aldrig sandt. Grenen er død kode, og GET / svarer 404 ` +
        `selv om kilden skriver en informationsgren for den.`,
    );
  }

  // R1 — dokumenterede endepunkter skal implementeres.
  const routes = implementedRoutes(source);
  if (routes.size === 0) {
    findings.push(
      "worker-scan/index.js: ingen ruter fundet — R1 ville være grøn uden at have kontrolleret noget",
    );
  }
  const page = read(join(site, "api", "index.html"));
  if (page === null) {
    findings.push("site/api/index.html: mangler — API'et sælges uden dokumentation");
  } else {
    const scope = mainOf(page);
    const documented = [...scope.matchAll(MARKER)].map((m) => m[1]);
    if (documented.length === 0) {
      findings.push(
        "site/api/index.html: ingen data-endpoint-markører i <main> — R1 kan da " +
          "ingenlunde vide hvilken overflade siden lover",
      );
    }
    for (const endpoint of documented) {
      if (!routes.has(endpoint)) {
        findings.push(
          `site/api/index.html: dokumenterer ${endpoint}, som worker-scan/index.js ` +
            "ikke implementerer. En læser får 404, og den ser ud som om " +
            "dokumentationen er forældet.",
        );
      }
    }
  }

  // R4 — dokumentationssiden skal publiceres.
  const tree = read(treeScript);
  if (tree === null) {
    findings.push("tools/build_public_tree.py: kan ikke læses — R4 kan da ikke efterprøves");
  } else {
    const dirs = /PUBLIC_DIRS\s*=\s*\(([\s\S]*?)\)/.exec(tree);
    const listed = dirs ? [...dirs[1].matchAll(/"([^"]+)"/g)].map((m) => m[1]) : [];
    if (!listed.includes("api")) {
      findings.push(
        'tools/build_public_tree.py: "api" mangler i PUBLIC_DIRS — /api/ er en ' +
          "dokumentationsside, der aldrig ville blive uploadet",
      );
    }
  }

  // R2 — en side der sælger API-adgang skal have døren med.
  for (const file of walk(site)) {
    const rel = relative(site, file);
    if (SELF.has(rel)) continue;
    const html = read(file);
    if (html === null) continue;
    const scope = mainOf(html);
    const claims = [...new Set([...scope.matchAll(API_CLAIM)].map((m) => m[0].toLowerCase()))];
    if (claims.length === 0) continue;
    const links = [...scope.matchAll(HREF)].map((m) => m[1].split("?")[0].split("#")[0]);
    const hasDoor = links.some((href) => href === DOC_PAGE || href === DOC_PAGE.replace(/\/+$/, ""));
    if (!hasDoor) {
      findings.push(
        `${rel}: lover API-adgang (${claims.join(", ")}) men linker ikke til ` +
          `${DOC_PAGE}. En solgt overflade uden dør ind til den er det, R2 findes for.`,
      );
    }
  }

  return findings;
}

// --------------------------------------------------------------------------
// Selftest: et grønt fixture-træ, hvor hver case bryder præcis én regel.
// --------------------------------------------------------------------------

const WORKER_FIXTURE = `export default {
  async fetch(request, env) {
    const reqUrl = new URL(request.url);
    const path = reqUrl.pathname.replace(/\\/+$/, "");
    if (request.method === "POST" && path === "/subscribe") { return new Response(""); }
    if (request.method === "GET" && path === "/config") { return new Response(""); }
    if (request.method === "GET" && path === "/stats") { return new Response(""); }
    if (request.method === "GET" && path === "") { return new Response("info"); }
    if (path !== "" && path !== "/scan") { return new Response("nf", { status: 404 }); }
    return new Response("scan");
  },
};
`;

const PAGE_FIXTURE = `<!doctype html><html><body>
<main id="main">
  <h1>API</h1>
  <section data-endpoint="/scan"></section>
  <h3 data-endpoint="/stats"></h3>
  <h3 data-endpoint="/subscribe"></h3>
  <h3 data-endpoint="/config"></h3>
  <a href="/api/">Docs</a>
</main>
<footer><span data-endpoint="https://mahope.tools/api/bugreport"></span></footer>
</body></html>`;

const CLAIMING_PAGE = `<!doctype html><html><body><main>
  <table><tr><td>API access</td><td>Free API + CLI</td></tr></table>
  <a href="/pricing/">Pricing</a>
</main></body></html>`;

const LINKED_CLAIM_PAGE = CLAIMING_PAGE.replace('<a href="/pricing/">', '<a href="/api/">Docs</a><a href="/pricing/">');

function fixture({ worker = WORKER_FIXTURE, page = PAGE_FIXTURE, tree, vs = LINKED_CLAIM_PAGE } = {}) {
  const root = mkdtempSync(join(tmpdir(), "apidocs-"));
  mkdirSync(join(root, "site", "api"), { recursive: true });
  mkdirSync(join(root, "site", "vs", "termly"), { recursive: true });
  mkdirSync(join(root, "worker-scan"), { recursive: true });
  mkdirSync(join(root, "tools"), { recursive: true });
  writeFileSync(join(root, "worker-scan", "index.js"), worker, "utf8");
  writeFileSync(join(root, "site", "api", "index.html"), page, "utf8");
  writeFileSync(join(root, "site", "vs", "termly", "index.html"), vs, "utf8");
  writeFileSync(
    join(root, "tools", "build_public_tree.py"),
    tree ?? 'PUBLIC_DIRS = (\n    "api",\n    "assets",\n)\n',
    "utf8",
  );
  return {
    root,
    run: () => collect({ site: join(root, "site"), worker: join(root, "worker-scan", "index.js"), treeScript: join(root, "tools", "build_public_tree.py") }),
    cleanup: () => rmSync(root, { recursive: true, force: true }),
  };
}

function selftest() {
  const failures = [];
  const cases = [];

  const runCase = (label, marker, options) => {
    const f = fixture(options);
    const findings = f.run();
    f.cleanup();
    if (!findings.length) return `case ${label}: forventet rød, men porten var grøn`;
    if (!findings.some((x) => x.includes(marker))) return `case ${label}: rød, men intet fund nævner ${marker} — ${findings[0]}`;
    return null;
  };

  // Den grønne case skal være rød, når den brydes. Ellers er den grøn af en
  // grund den aldrig har efterprøvet.
  const green = fixture();
  const greenFindings = green.run();
  green.cleanup();
  if (greenFindings.length) cases.push(`rent fixture-træ: ${greenFindings[0]}`);

  // R1 — dokumenteret rute som workeren ikke implementerer.
  cases.push(runCase("dokumenteret rute findes ikke", "ikke implementerer", {
    page: PAGE_FIXTURE.replace('data-endpoint="/config"', 'data-endpoint="/history"'),
  }));
  // R1 — ingen markører, så R1 ingenlunde ved hvilken overflade siden lover.
  cases.push(runCase("ingen data-endpoint-markører", "ingen data-endpoint-markører", {
    page: "<!doctype html><html><body><main><h1>API</h1></main></body></html>",
  }));
  // R2 — en side der lover API-adgang uden dør.
  cases.push(runCase("API-løfte uden dør", "linker ikke til /api/", { vs: CLAIMING_PAGE }));
  // R3 — den døde rute-gren.
  cases.push(runCase("død rute-gren", "død kode", {
    worker: WORKER_FIXTURE.replace('.replace(/\\/+$/, "")', '.replace(/\\/+$/, "") || "/"'),
  }));
  // R4 — siden er ikke i PUBLIC_DIRS.
  cases.push(runCase("ikke i PUBLIC_DIRS", "mangler i PUBLIC_DIRS", {
    tree: 'PUBLIC_DIRS = (\n    "assets",\n)\n',
  }));

  const failed = cases.filter(Boolean);
  if (failed.length) {
    for (const f of failed) console.log("SELFTEST FEJLET:", f);
    return 1;
  }
  console.log(`SELFTEST GRØN — alle 5 negative cases fanges`);
  return 0;
}

const argv = process.argv.slice(2);
if (argv.includes("--selftest")) {
  process.exit(selftest());
}

const findings = collect();
if (findings.length) {
  for (const f of findings) console.log("FUND:", f);
  console.log(
    `\n${findings.length} fund — API'et sælges uden en dokumentationsside, ` +
      "eller dokumentationen lover en overflade der ikke findes.",
  );
  process.exit(1);
}
console.log(
  "API-dokumentation: alle dokumenterede endepunkter er implementeret i workeren, " +
    "ingen rute-gren er død, /api/ publiceres, og enhver side der lover API-adgang " +
    "har en dør ind til dokumentationen.",
);
