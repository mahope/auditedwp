#!/usr/bin/env node
/**
 * Mål SSRF-guarden i den PUBLICEREDE npm-motor mod motoren i dette repo.
 *
 * Baggrund
 * ---------
 * `site/cli/` fortæller brugere at installere `@mahope/eucomply-scanner`, og
 * `eucomply-scanner/README.md` anbefaler `npx github:mahope/eucomply-scanner`.
 * Begge peger på **repoet `mahope/eucomply-scanner`**, som også er det npm blev
 * publiceret fra. Den publicerede 1.0.1 er fra før hærdningen i `28795c3`:
 * den afviser IP-literaler, men har ingen DNS-opløsning og ingen
 * per-hop-validering af redirects (`fetch(..., { redirect: "follow" })`).
 *
 * Målt 2026-09-26: den publicerede motor VED at lade `http://localtest.me`
 * (DNS -> 127.0.0.1) slippe igennem og starte en hentning; motoren her i repoet
 * nægter samme adresse med "resolves to a private address".
 *
 * Denne kontrol findholder den anden retning. Den publicerede motor kan ikke
 * rettes herfra — vi må ikke publisere — så en afvigelse er en RAPPORT, ikke
 * et fund, af samme grund som `unsold_products()` (opgave 37) og `KNOWN_LAG`
 * (opgave 38): en permanent rød gate ville låse hvert merge og dermed hele
 * sitets deploy, præcis skaden opgave 35 lavede.
 *
 * Det der KAN håndhæves, er den anden side: motoren her i repoet må aldrig
 * miste en egenskab, fordi den så ligner den publicerede. Derfor fejler denne
 * gate rødt, hvis en af de otte prøver opfører sig anderledes end i dag.
 *
 * Kør:
 *   node tools/check_published_engine.mjs
 *   node tools/check_published_engine.mjs --selftest
 *   node tools/check_published_engine.mjs --offline
 */

import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PKG = '@mahope/eucomply-scanner';
const LOCAL_ENGINE = path.join(ROOT, 'eucomply-scanner', 'engine', 'index.js');

/** Den version, målingen blev taget mod. Ændres den, skal forventningen følge. */
export const MEASURED_VERSION = '1.0.1';

/**
 * Otte prøver på denEgenskab der adskiller motorerne: kan en adresse, der
 * peger på et privat netværk, slippe igennem?
 *
 * `host` = det den kaldende browser/CLI skriver i adresselinjen.
 * `expect` = hvad motoren i repoet SKAL gøre: 'refuse' eller 'allow'.
 * `needsNet` = prøven kræver at `host` faktisk kan slås op.
 */
export const PROBES = [
  { id: 'litteral-loopback',   host: 'http://127.0.0.1/',              expect: 'refuse' },
  { id: 'litteral-privat-10',   host: 'http://10.0.0.5/',               expect: 'refuse' },
  { id: 'litteral-link-local',  host: 'http://169.254.169.254/',       expect: 'refuse' },
  { id: 'litteral-privat-192',  host: 'http://192.168.1.1/',           expect: 'refuse' },
  { id: 'ipv6-loopback',        host: 'http://[::1]/',                  expect: 'refuse' },
  { id: 'ipv4-mapped-loopback', host: 'http://[::ffff:127.0.0.1]/',     expect: 'refuse' },
  { id: 'dns-til-privat',       host: 'http://localtest.me/',          expect: 'refuse', needsNet: true },
  { id: 'offentlig-adresse',    host: 'https://example.com/',          expect: 'allow',  needsNet: true },
];

/**
 * Hvad den publicerede 1.0.1 faktisk gjorde med de samme otte prøver, målt
 * 26/9 2026 ved at hente tarballen og kalde dens `normalizeUrl`.
 *
 * Seks af dem afvises, fordi 1.0.1 har en `isPublicHostname` der læser
 * IP-literaler. **DNS-opløsning og redirects mangler helt**, så
 * `localtest.me` (som peger på 127.0.0.1) slipper igennem — det er hele
 * afvigelsen.
 *
 * Denne tabel er ikke en forventning, den er en **optaget måling**. Gaten
 * sammenligner den med den live måling, så hverken en ny publicering eller en
 * uventet ændring kan glide forbi: lukker npm-hullet, siger kontrollen det.
 */
export const MEASURED_PUBLISHED = {
  'litteral-loopback': 'refuse',
  'litteral-privat-10': 'refuse',
  'litteral-link-local': 'refuse',
  'litteral-privat-192': 'refuse',
  'ipv6-loopback': 'refuse',
  'ipv4-mapped-loopback': 'refuse',
  'dns-til-privat': 'allow',
  'offentlig-adresse': 'allow',
};

/**
 * Kører én motor mod alle otte prøver og returnerer {id: 'refuse'|'allow'|'error'}.
 *
 * Hvilken funktion der kaldes, er ikke valgfrit — det er fundet i denne
 * iteration. Motoren i repoet deler guarden i to: `normalizeUrl` læser kun
 * IP-literaler, mens DNS-opløsningen ligger i `assertPublicTarget`, som
 * `safeFetch` kalder ved hvert redirect-hop. Den publicerede 1.0.1 har **kun**
 * `normalizeUrl`.
 *
 * En gate der blindt kaldte `normalizeUrl` på begge ville derfor have fundet
 * **nul** afvigelse — fordi repo-motoren "taber" prøven samme sted. Det er en
 * grøn af en fejl, i en kontrol hvis hele formål er at måle afvigelsen. Derfor
 * kaldes den funktion, motoren faktisk bruger, og det siges eksplicit i
 * udskriften hvilken det var.
 */
async function probeEngine(engineUrl) {
  const mod = await import(engineUrl);
  if (typeof mod.normalizeUrl !== 'function') throw new Error('normalizeUrl mangler i motoren');
  // `assertPublicTarget` er den ærlige indgang, når den findes: den løser DNS
  // og afviser et navn der peger på et privat netværk.
  const useTarget = typeof mod.assertPublicTarget === 'function';
  const out = {};
  for (const p of PROBES) {
    try {
      if (useTarget) {
        await mod.assertPublicTarget(p.host);
        out[p.id] = 'allow';
      } else {
        out[p.id] = mod.normalizeUrl(p.host) === null ? 'refuse' : 'allow';
      }
    } catch (e) {
      // Kaster den i en fejl uden at svare, er det en afvisning, ikke et
      // målefejl. Ellers ville en motor med en hård fejl ved fejl læse som
      // "afviser alt" og være grøn af en fejl.
      out[p.id] = /private|public website|Only http|redirected more than/i.test(String(e?.message || e)) ? 'refuse' : 'error';
    }
  }
  return { results: out, guard: useTarget ? 'assertPublicTarget' : 'normalizeUrl (kun IP-literaler)' };
}

function hentTarball(cacheDir) {
  const require = createRequire(import.meta.url);
  // Bevæg os uden for repoet: npm-laget skal ikke se vores node_modules.
  const url = `https://registry.npmjs.org/${encodeURIComponent(PKG)}`;
  const raw = execFileSync('curl', ['-sL', url], { maxBuffer: 32 * 1024 * 1024, encoding: 'utf8' });
  const meta = JSON.parse(raw);
  if (!meta.versions?.[MEASURED_VERSION]) {
    throw new Error(`${PKG}@${MEASURED_VERSION} findes ikke i registret (nuværende: ${Object.keys(meta.versions || {}).join(', ') || 'ingen'})`);
  }
  const tgz = meta.versions[MEASURED_VERSION].dist.tarball;
  const file = path.join(cacheDir, `${MEASURED_VERSION}.tgz`);
  execFileSync('curl', ['-sL', '-o', file, tgz]);
  execFileSync('tar', ['xzf', file], { cwd: cacheDir });
  const engine = path.join(cacheDir, 'package', 'engine', 'index.js');
  if (!fs.existsSync(engine)) throw new Error('tarballen har ingen engine/index.js');
  void require;
  return { engine, published: meta.versions[MEASURED_VERSION] };
}

export async function measure({ offline = false } = {}) {
  const local = await probeEngine(pathToFileURL(LOCAL_ENGINE).href);
  const report = { local: local.results, localGuard: local.guard, published: null, publishedGuard: null, publishedMeta: null, note: null };
  if (offline) {
    report.note = 'offline: den publicerede motor blev ikke hentet';
    return report;
  }
  const cacheDir = fs.mkdtempSync(path.join(os.tmpdir(), 'eucomply-engine-'));
  try {
    const { engine, published } = hentTarball(cacheDir);
    const pub = await probeEngine(pathToFileURL(engine).href);
    report.published = pub.results;
    report.publishedGuard = pub.guard;
    report.publishedMeta = published;
  } finally {
    fs.rmSync(cacheDir, { recursive: true, force: true });
  }
  return report;
}

/** Den del der MÅ være rød: motoren i repoet imod sine otte forventninger. */
export function localFindings(local) {
  const out = [];
  for (const p of PROBES) {
    if (local[p.id] !== p.expect) {
      out.push(`motoren i repoet: ${p.id} burde være ${p.expect}, er ${local[p.id]} (${p.host})`);
    }
  }
  return out;
}

/** Den del der KUN rapporteres: afvigelsen i den publicerede motor. */
export function publishedGap(published) {
  if (!published) return [];
  return PROBES.filter((p) => p.expect === 'refuse' && published[p.id] !== 'refuse')
    .map((p) => `${p.id} (${p.host}) — publiceret: ${published[p.id]}, forventet: refuse`);
}

export async function selftest() {
  let fails = 0;
  const cases = [];

  // 1. Rene målinger -> ingen fund, ingen afvigelse.
  cases.push(['rene målinger på begge motorer -> 0 fund og 0 afvigelse', () => {
    const good = Object.fromEntries(PROBES.map((p) => [p.id, p.expect]));
    return localFindings(good).length === 0 && publishedGap(good).length === 0;
  }]);

  // 2. REPO-motoren mister en egenskab -> RØD. Det er den håndhævede retning.
  for (const p of PROBES) {
    const broken = Object.fromEntries(PROBES.map((x) => [x.id, x.expect]));
    broken[p.id] = p.expect === 'refuse' ? 'allow' : 'refuse';
    cases.push([`repo-motoren taber ${p.id} -> fund med præcis den prøve`, () => {
      const f = localFindings(broken);
      return f.length === 1 && f[0].includes(p.id);
    }]);
  }

  // 3. PUBLICERET motor taber en egenskab -> rapporteret, ikke rød.
  cases.push(['publiceret motor taber dns-til-privat -> rapporteret, ikke fund', () => {
    const pub = Object.fromEntries(PROBES.map((x) => [x.id, 'refuse']));
    pub['offentlig-adresse'] = 'allow';
    pub['dns-til-privat'] = 'allow';
    const f = localFindings(pub);
    return f.length === 1 && publishedGap(pub).length === 1;
  }]);

  // 4. At guarden låser scanneren må også være rødt: 'offentlig-adresse' er
  //    lige så håndhævet som 'refuse'-proberne, fordi en for stram guard
  //    dræber det gratis værktøj (samme fejlretning som opgave 38).
  cases.push(['repo-motoren afviser en offentlig adresse -> fund (guarden har lukket scanneren)', () =>
    localFindings({ ...Object.fromEntries(PROBES.map((x) => [x.id, 'refuse'])), 'offentlig-adresse': 'refuse' }).length === 1]);

  // 5. Målingen skal læse alle otte prøver, ellers er en grøn kørsel meningsløs.
  cases.push(['alle otte prøver læses på begge motorer', () =>
    PROBES.length === 8 && Object.keys(MEASURED_PUBLISHED).length === 8]);

  // 6. Den publicerede måling skal være pinet til den version den blev taget mod.
  cases.push(['den publicerede måling er pinet til 1.0.1', () => MEASURED_VERSION === '1.0.1']);

  // 7. En motor der kaster en målefejl (ikke en afvisning) må hverken være
  //    grøn som 'afviser' for alt eller rød som et målefejl uden forklaring.
  cases.push(['et målefejl (ikke en afvisning) tælles hverken som refuse eller allow', () => {
    // Gengiver guardens klassificering af en fejl, der ikke er en afvisning.
    const classify = (msg) => /private|public website|Only http|redirected more than/i.test(String(msg)) ? 'refuse' : 'error';
    return classify('ECONNRESET') === 'error' && classify('That domain resolves to a private address') === 'refuse';
  }]);

  // 8. Den optagede måling skal dække præcis de samme prøver som PROBES,
  //    ellers sammenligner gaten ubesvarede nøgler med 'undefined' og er grøn.
  cases.push(['den optagede måling dækker præcis de otte prøver', () => {
    const a = PROBES.map((p) => p.id).sort().join(',');
    const b = Object.keys(MEASURED_PUBLISHED).sort().join(',');
    return a === b && Object.values(MEASURED_PUBLISHED).every((v) => v === 'refuse' || v === 'allow');
  }]);

  for (const [name, fn] of cases) {
    let ok = false;
    try { ok = await fn(); } catch (e) { ok = false; void e; }
    if (ok) console.log(`  OK    ${name}`);
    else { console.log(`  FANGET ${name}`); fails++; }
  }
  console.log(fails ? `\nSELFTEST RØD — ${fails} af ${cases.length} cases fejlede.` : `\nSELFTEST GRØN — alle ${cases.length} negative cases fanges.`);
  return fails;
}

async function main() {
  const argv = process.argv.slice(2);
  if (argv.includes('--selftest')) return (await selftest()) ? 1 : 0;

  const offline = argv.includes('--offline');
  let report;
  try {
    report = await measure({ offline });
  } catch (e) {
    console.error(`FEJL: den publicerede motor kunne ikke hentes: ${e.message}`);
    console.error('Det er INGEN måling. En grøn udskrift uden måling er ikke bevis — kør igen med netværk.');
    return 1;
  }

  const findings = localFindings(report.local);
  console.log(`Motor i repoet: ${PROBES.length} prøver, målt gennem ${report.localGuard}`);
  for (const p of PROBES) console.log(`  ${report.local[p.id] === p.expect ? 'ok     ' : 'FEJL   '} ${p.id.padEnd(20)} ${report.local[p.id].padEnd(7)} ${p.host}`);

  const gap = publishedGap(report.published);
  if (report.note) {
    console.log(`\nPubliceret motor: ikke målt (${report.note})`);
  } else {
    const v = report.publishedMeta?.version;
    console.log(`\nPubliceret motor: ${PKG}@${v} — ${PROBES.length} prøver, målt gennem ${report.publishedGuard}`);
    for (const p of PROBES) {
      const want = p.expect === 'refuse' ? 'afviser' : 'slipper ';
      const got = report.published[p.id];
      const mark = got === p.expect ? 'ok     ' : (p.expect === 'refuse' ? 'SLIPPER ' : 'NÆGTET ');
      void want;
      console.log(`  ${mark} ${p.id.padEnd(20)} ${got.padEnd(7)} ${p.host}${got === p.expect ? '' : `   <- forventet ${p.expect}`}`);
    }

    // Den live måling skal være den optagede. Det er den egenskab der gør
    // tabellen værd at vedligeholde: en ny publicering, eller en tomme der
    // pludselig slipper mere igennem, kan ikke læse som "uændret".
    const drift = PROBES.filter((p) => report.published[p.id] !== MEASURED_PUBLISHED[p.id])
      .map((p) => `${p.id}: målt ${report.published[p.id]}, optaget ${MEASURED_PUBLISHED[p.id]}`);
    if (drift.length) {
      console.log(`\nFEJL — den publicerede motor opfører sig anderledes end optaget ${MEASURED_VERSION}:`);
      for (const d of drift) console.log(`  - ${d}`);
      console.log('  Opdatér MEASURED_PUBLISHED, når det er undersøgt hvorfor — eller lad publicér 1.1.0 med motoren fra dette repo.');
      return 1;
    }
    console.log(`\nOK    live-målingen er identisk med den optagede måling for ${PKG}@${MEASURED_VERSION}.`);

    if (gap.length === 0) {
      console.log(`OK    ingen afvigelse: den publicerede motor afviser alle private prøver.`);
    } else {
      console.log(`\nRAPPORT — den publicerede motor slipper ${gap.length} privat prøve${gap.length === 1 ? '' : 'r'} igennem:`);
      for (const g of gap) console.log(`  - ${g}`);
      console.log('  Vi må ikke publisere, så dette er ikke et fund. publicér 1.1.0 med motoren fra dette repo (spørgsmål 17),');
      console.log('  eller lad @mahope/eucomply-scanner pege på et repo med den hærdede motor. Indtil da skal /cli/ være ærlig om det.');
    }
  }

  if (findings.length) {
    console.log('\nFEJL — motoren i repoet har mistet en egenskab:');
    for (const f of findings) console.log(`  - ${f}`);
    return 1;
  }
  console.log(`\nOK    motoren i repoet afviser alle private prøver og slipper den offentlige adresse igennem.`);
  return 0;
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) {
  process.exit(await main());
}
