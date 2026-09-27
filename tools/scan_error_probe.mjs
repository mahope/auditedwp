/**
 * Adfærdskontrol for scannerens fejlvej — bruges af `tools/check_scan_errors.py`
 * (trin 28 i `tools/quality_gate.sh`).
 *
 * Hvorfor en måling og ikke en søgning: reglen skal være sand for den kode der
 * faktisk udgives, og det kan en regex ikke bevise. Her tages derfor den
 * `apiError`-funktion og den `T`-tabel, som **siden selv** indeholder, og de
 * køres i en `vm` med de **rigtige** svar fra den **udgivne** worker.
 *
 * De fire tilfælde er ikke opfundet. De er hentet fra
 * `eucomply-scan.mahope-eeb.workers.dev` 2026-09-28:
 *
 *   200  et site der svarer
 *   400  en adresse der ikke er en webadresse → `{"error":"Please provide …"}`
 *   429  elleve scanninger i samme minut       → `{"error":"Rate limit reached…"}`
 *   502  et domæne der ikke findes             → `{"error":"Scan failed: The site
 *        responded with HTTP 530 — a compliance scan needs a reachable page."}`
 *
 * Den sidste er hele fundet: en ny besøgende, der skriver et domæne med en
 * tastefejl, fik motorens egen sætning med et HTTP-statusnummer i. Før
 * rettelsen stod den i `errEl.textContent`.
 *
 * Klammerne i udtrækket tælles, så en streng med `}` ikke afbryder funktionen —
 * samme fejlklasse som opgave 65 del 1, hvor en blokke sluttede ved det første
 * `\n]`.
 *
 * Brug:
 *     node tools/scan_error_probe.mjs <side.html> <svar.json>
 *
 * Svarene læses fra en fil, så selftesten kan give porten svar den aldrig ser
 * live — en port der kun kan grønne på rigtige data kan heller aldrig rødme på
 * en mutation.
 */

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import vm from 'node:vm';

/** Sådan ser en rå fejl fra en Cloudflare-kant ud: HTML, ikke JSON. */
export const EDGE_HTML = '<html><head><title>520</title></head><body>Web server is returning an unknown error</body></html>';

/** Rød hvis en besøgende kan se noget af dette. */
const FORBIDDEN = [
  { re: /\bHTTP\s+\d{3}\b/, why: 'et råt HTTP-statusnummer' },
  { re: /Scan failed:/i, why: 'motorens interne præfiks' },
  { re: /Unexpected token|SyntaxError|TypeError|ReferenceError|is not a function|\bundefined\b|\bnull\b/i, why: 'en JavaScript- eller JSON-fejl fra browseren' },
  { re: /\b(curl|node|python|worker|WORKER|env\.|at Object|at Module)\b/i, why: 'en implementationsdetalje' },
  { re: /<|>|&/, why: 'markup i et felt der kun skal have tekst' },
];

function extract(src, header) {
  const start = src.indexOf(header);
  if (start < 0) return null;
  if (header.startsWith('var T =')) {
    const end = src.indexOf('};', start);
    return end < 0 ? null : src.slice(start, end + 2);
  }
  let depth = 0;
  let i = src.indexOf('{', start);
  if (i < 0) return null;
  let inStr = null;
  for (; i < src.length; i++) {
    const ch = src[i];
    if (inStr) {
      if (ch === '\\') { i++; continue; }
      if (ch === inStr) inStr = null;
      continue;
    }
    if (ch === '"' || ch === "'" || ch === '`') { inStr = ch; continue; }
    if (ch === '{') depth++;
    else if (ch === '}') { depth--; if (depth === 0) return src.slice(start, i + 1); }
  }
  return null;
}

/** Byg en `apiError` ud fra sidens egen kode. */
export function compile(src) {
  const fn = extract(src, 'function apiError(');
  if (!fn) return { error: 'siden mangler function apiError(' };
  // Ikke alle siderne har en `T`-tabel — nogle skriver beskederne direkte i
  // funktionen. Så springes sammenligningen med `T.network`, og det er
  // stadig sidens egen kode der afgør teksten.
  const t = extract(src, 'var T =') || '';
  const ctx = vm.createContext({});
  try {
    vm.runInContext(`${t}\n${fn}\nthis._apiError = apiError;`, ctx, { timeout: 1000 });
  } catch (e) {
    return { error: `sidens egen kode kunne ikke evalueres: ${e.message}` };
  }
  return { apiError: ctx._apiError, T: ctx.T || null };
}

export function verdictFor(apiError, status, body) {
  let d = null;
  try { d = JSON.parse(body); } catch { d = null; }
  return apiError(status, d);
}

/** Kør siden gennem porten. Returnerer en liste med fund, tom når den er grøn. */
export function check(page, responses) {
  const findings = [];
  const src = readFileSync(page, 'utf8');
  const c = compile(src);
  if (c.error) return [`${page}: ${c.error}`];

  // 1. Hvert svar skal give en besked, og ingen må afsløre internals.
  for (const r of responses) {
    const text = verdictFor(c.apiError, r.status, r.body);
    if (typeof text !== 'string' || !text.trim()) {
      findings.push(`${page}: status ${r.status} gav ingen besked (${JSON.stringify(text)})`);
      continue;
    }
    for (const f of FORBIDDEN) {
      if (f.re.test(text)) findings.push(`${page}: status ${r.status} viste ${f.why}: ${JSON.stringify(text)}`);
    }
    if (c.T && text === c.T.network) {
      findings.push(`${page}: status ${r.status} faldt tilbage til netværksfejlen, som er til for en worker der svarede: ${JSON.stringify(text)}`);
    }
  }

  // 2. En kantfejl er HTML, så `.json()` kaster. Porten skal stadig give en
  //    besked, og den må ikke være browserens egen undtagelsestekst.
  for (const status of [429, 502, 503, 520, 522, 524]) {
    const text = verdictFor(c.apiError, status, EDGE_HTML);
    if (c.T && text === c.T.network) {
      findings.push(`${page}: en Cloudflare-kantfejl (${status}) giver kun netværksfejlen, som lyder som om serveren nede: ${JSON.stringify(text)}`);
    }
    for (const f of FORBIDDEN) {
      if (typeof text === 'string' && f.re.test(text)) findings.push(`${page}: kantfejl ${status} viste ${f.why}: ${JSON.stringify(text)}`);
    }
  }

  // 3. De tre kendte tilfælde skal være tre forskellige sætninger.
  const known = [400, 429, 502].map((s) => {
    const hit = responses.find((r) => r.status === s);
    return hit ? verdictFor(c.apiError, s, hit.body) : null;
  });
  if (new Set(known).size !== known.length) {
    findings.push(`${page}: 400, 429 og 502 gav ikke hver sin besked: ${JSON.stringify(known)}`);
  }

  // 4. Uopnåeligt domæne er det første en ny besøgende skriver, så beskeden
  //    skal pege på næste skridt — ellers er den en blindgade.
  const unreachable = verdictFor(c.apiError, 502, JSON.stringify({ error: 'Scan failed: The site responded with HTTP 530' }));
  if (!/https:\/\/$|example\.com|spelling|stavemåde/i.test(unreachable)) {
    findings.push(`${page}: beskeden for et uopnåeligt domæne peger ikke på næste skridt: ${JSON.stringify(unreachable)}`);
  }
  return findings;
}

const args = process.argv.slice(2).filter((a) => a !== '--selftest');
if (args.length < 2) {
  console.error('brug: node tools/scan_error_probe.mjs <side.html> <svar.json>');
  process.exit(2);
}
const findings = check(resolve(args[0]), JSON.parse(readFileSync(resolve(args[1]), 'utf8')));
for (const f of findings) console.log(`  FEJL ${f}`);
process.exit(findings.length ? 1 : 0);
