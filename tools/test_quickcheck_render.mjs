// tools/test_quickcheck_render.mjs
//
// Kører quick-check-blokkenes renderer mod et fjendtligt workersvar.
//
// Hvorfor denne test findes: tools/check_dom_xss.py læser koden og kræver, at
// hver sink står i esc(). Det er et statisk krav, og et statisk krav kan være
// grønt, mens rendereren stadig skriver markup. Denne test lukker det hull ved
// at *udføre* hver blok og se, hvad der faktisk havner i .innerHTML.
//
// Beviset fra 26/9 står uændret: workeren spejler den indtastede adresse urørt
// tilbage i `url`. Her giver vi rendereren et svar, hvor HVERT felt er en
// payload, og kræver at ingen af dem optræder råt i den markup, der skrives.
//
// Hver sentinel er valgt, så dens escapede form (`&lt;img …`) kan skelnes fra
// den rå (`<img …`). Vi tester altså ikke "er der et `<`", men "kommer præcis
// dette felt igennem uændret".
//
// Denne test har selv været årsag til to falske grønne, begge fundet fordi den
// så grøn ud uden at have kørt noget:
//   1. DOM-stubbens addEventListener var en no-op, så submit-handleren aldrig
//      blev kaldt, og `writes` var tom. Testen meldte "ingen fil skrev markup".
//   2. Selv med handleren fundet skrev den ingen .innerHTML, fordi den greb
//      `du-form` — en stub, der altid findes — i stedet for den form, der
//      faktisk havde en handler.
// Derfor tæller en fil kun som grøn, hvis den både fandt en trigger OG
// producerede mindst én .innerHTML-skrivning.
//
// TO FAMILIER (opgave 17)
// -----------------------
// 1. `quickcheck` — de 28 sider der kalder deskuptime-quickcheck.
// 2. `scancard`   — de scanner-sider der renderer et scan-resultat som kort
//    (`card.innerHTML` med `pillText(c)`). Disse skrev `c.label` og `c.detail`
//    råt ind i .innerHTML, mens deres søskendesider på /scan/ allerede escapede.
//    Familien får sit eget workersvar med præcis de felter rendereren læser.

import { readFileSync, readdirSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join, relative } from 'node:path';
import vm from 'node:vm';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const WORKER = 'deskuptime-quickcheck';
const TEST_URL = 'https://example.com/';

// Hvert felt bærer sin egen genkendelige payload.
const PAYLOADS = {
  url: '<img src=x onerror=alert(1)>',
  statusText: '<script>alert(2)</script>',
  responseMs: '<b>fast</b>',
  finalUrl: '<svg onload=alert(3)>',
  error: '<object data=evil>',
  sha256: '<marquee>hash</marquee>',
  sslExpiresAt: '<blink>2027-01-01</blink>',
  sslError: '<hr>',
  headers: { server: '<iframe src=evil>' },
  status: 200,
  contentBytes: 1234,
  https: true,
  redirected: true,
  sslDaysRemaining: 30,
  // Værdier der bruges i catch-blokkenes err.message.
  __message: '<embed src=evil>',
};

// Widgetens EGNE tags. Alt andet i outputtet er et fund.
const ALLOWED_TAGS =
  /<\/?(strong|br|span|p|code|dl|dt|dd|table|thead|tbody|tr|th|td|a|em|sup|sub|hr)\b[^>]*>/g;

// scancard-familien bygger kun span/b/p (+ small fra insertAdjacentHTML).
const ALLOWED_TAGS_SCANCARD = /<\/?(span|b|p|small)\b[^>]*>/g;

// scancard: hvert felt scanner-rendereren læser bærer sin egen payload.
// `label: ''` medvirker med vilje, fordi rendereren skriver `c.label || k` —
// så både den tomme-label-gren og nøgle-gren bliver kørt.
const SCAN_PAYLOAD = {
  url: '<iframe src=evil>',
  platform: '<b>nginx</b>',
  score: { pct: 42, passed: 3, total: 9 },
  checks: {
    trackers: {
      pass: false, warn: false,
      label: '<script>alert(2)</script>',
      detail: '<svg onload=alert(3)>',
      fix: '<object data=evil>',
    },
    ssl: {
      pass: true, warn: true,
      label: '<img src=x onerror=alert(4)>',
      detail: '<marquee>detail</marquee>',
    },
    headers: { pass: false, warn: false, label: '', detail: '<hr>' },
  },
};

const SCAN_STRING_SENTINELS = [
  SCAN_PAYLOAD.url,
  SCAN_PAYLOAD.checks.trackers.label,
  SCAN_PAYLOAD.checks.trackers.detail,
  SCAN_PAYLOAD.checks.trackers.fix,
  SCAN_PAYLOAD.checks.ssl.label,
  SCAN_PAYLOAD.checks.ssl.detail,
  SCAN_PAYLOAD.checks.headers.detail,
];

const STRING_SENTINELS = [
  PAYLOADS.url,
  PAYLOADS.statusText,
  PAYLOADS.responseMs,
  PAYLOADS.finalUrl,
  PAYLOADS.error,
  PAYLOADS.sha256,
  PAYLOADS.sslExpiresAt,
  PAYLOADS.sslError,
  PAYLOADS.headers.server,
  PAYLOADS.__message,
];

// Browsernes serialisering af textContent som innerHTML. `'` escape-es også,
// fordi den regex-baserede escaper i scanner-siderne gør det, og `mustAppear`-
// assertionen ellers ville melde et felt "ikke frem" for en apostrof.
function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/** Minimal DOM. Elementer registrerer hver innerHTML-skrivning. */
function makeDom() {
  const writes = [];
  const textWrites = [];
  const els = new Map();
  const make = (id, isEscaper = false) => ({
    id,
    style: {},
    className: '',
    value: TEST_URL,
    _text: '',
    __submit: null,
    __handlers: {},
    set textContent(v) { textWrites.push({ id, text: String(v) }); this._text = String(v); },
    get textContent() { return this._text; },
    // VIGTIGT: for et element lavet af createElement() serialiserer browseren
    // textContent, når man læser innerHTML — det er sådan esc() overhovedet
    // escaper. Vores første udgave returnerede den rå streng, hvilket gjorde
    // esc() til en no-op og fik testen til at melde alle 28 filer for lækkende.
    // Vi ville så have "rettet" korrekt kode for at tilfredsstille en stub.
    get innerHTML() { return isEscaper ? escapeHtml(this._text) : this._text; },
    set innerHTML(v) { writes.push({ id, html: String(v) }); this._text = String(v); },
    addEventListener(type, fn) {
      if (typeof fn !== 'function') return;
      this.__handlers[type] = fn;
      if (type === 'submit') this.__submit = fn;
    },
    removeAttribute() {},
    setAttribute() {},
    getAttribute() { return null; },
    appendChild() {},
    focus() {},
    // scancard-familien kalder disse to. Uden dem ville rendereren kaste, og
    // testen ville rapportere "kan ikke dokumenteres som sikker" for en fejl i
    // stubben — altså en ny falske-grøn-fælde af præcis samme slags.
    insertAdjacentHTML(pos, html) { writes.push({ id, html: String(html) }); },
    scrollIntoView() {},
  });
  // scancard bygger procent-tallet med createTextNode. Uden denne metode
  // kaster rendereren — og scannerens egen try/catch **sluger fejlen og
  // viser den som en fejlmeddelelse**. Testen så derefter 1 skrivning, erklærede
  // filen grøn og havde testet nul tegn af selve kortet. Dette er den tredje
  // falske grøn i dette værktøj, og den er nu permanent umulig: se `textWrites`
  // og assertRendered().
  const document = {
    getElementById(id) {
      if (!els.has(id)) els.set(id, make(id));
      return els.get(id);
    },
    createElement() { return make('tmp', true); },
    createTextNode(v) { return { nodeValue: String(v) }; },
    querySelector() { return null; },
    querySelectorAll() { return []; },
    addEventListener() {},
    readyState: 'complete',
    body: make('body'),
  };
  return { writes, textWrites, document, els };
}

function newContext(document, fetchImpl) {
  const sandbox = {
    document, console, setTimeout, clearTimeout, URL, Date, Math, JSON,
    String, Number, Boolean, Array, Object, RegExp, Error, Promise,
    encodeURIComponent, decodeURIComponent, parseInt, parseFloat, isNaN,
    location: { href: 'https://eucomplypro.com/' },
    navigator: { userAgent: 'test' },
    fetch: fetchImpl,
  };
  sandbox.window = sandbox;
  sandbox.globalThis = sandbox;
  sandbox.self = sandbox;
  return vm.createContext(sandbox);
}

// TO svarsvarianter. Kun med `error` ville successtien aldrig blive
// renderet — `if(d.error){…;return;}` kortslutter den — og så ville vi
// have testet en fejlmeddelelse og troet vi havde testet hele blokken.
const OK_PAYLOAD = (() => { const p = { ...PAYLOADS }; delete p.error; return p; })();
const ERR_PAYLOAD = (() => {
  const p = { ...PAYLOADS };
  p.status = 0; p.redirected = false;
  return p;
})();

const fetchFor = (payload) => async () => ({
  ok: true,
  status: 200,
  json: async () => JSON.parse(JSON.stringify(payload)),
});

const hostileFetch = fetchFor(ERR_PAYLOAD);

/** Find den trigger der faktisk findes i denne fil. */
function findTrigger(ctx, document) {
  // 1. Formular-submit: find den form der faktisk har en handler.
  for (const id of ['du-form', 'live-check-form', 'check-form', 'purl-form', 'scan-form']) {
    const el = document.getElementById(id);
    if (el && el.__submit) return { kind: 'submit', run: () => el.__submit({ preventDefault() {} }) };
  }
  // 2. Globalt udsatte værktøjsfunktioner (bulk-tjek, hash, responstid, ssl).
  for (const name of ['doBulk', 'doHash', 'doCheck', 'doSslCheck']) {
    if (typeof ctx[name] === 'function') {
      return { kind: 'global:' + name, run: () => ctx[name]() };
    }
  }
  // 3. Et input-felt med en keydown-handler på Enter.
  for (const id of ['urls', 'purl', 'url', 'du-url', 'live-url']) {
    const el = document.getElementById(id);
    if (el && el.__handlers && el.__handlers.keydown) {
      return {
        kind: 'keydown:' + id,
        run: () => el.__handlers.keydown({ key: 'Enter', preventDefault() {} }),
      };
    }
  }
  return null;
}

// En familie er (navn, markør i kilden). Markøren skal være noget, kun denne
// families sider har — ellers ville filkredsen vokse på en måde, ingen har
// efterprøvet, hvilket er præcis den falske grøn opgave 14 dokumenterede.
// `mustAppearEscaped` er den Positive assertion: felterne skal være i outputtet
// — escapede. Uden den kan en render, der dør halvvejs, se grøn ud, fordi der
// så blot er mindre markup at finde fejl i. Det var netop det, der skete med
// scancard-familien, da createTextNode manglede i stubben.
//
// quickcheck-familien har KUN den negative assertion. De 28 renderere er
// heterogene — nogle skriver fejlgrenen, nogle succespadden, nogle kun
// textContent — så der findes ingen ærlig fællesmængde af felter, der *skal*
// dukke op i alle 28. Vi opfinder ikke en, for så ville vi teste en
// fabrikation. Det står her, så næste læser ikke tror, at dækningen er større.
const FAMILIES = [
  { name: 'quickcheck', marker: WORKER, payload: null, allowed: ALLOWED_TAGS, sentinels: STRING_SENTINELS, mustAppearEscaped: [] },
  {
    name: 'scancard', marker: 'pillText(c)', payload: SCAN_PAYLOAD,
    allowed: ALLOWED_TAGS_SCANCARD, sentinels: SCAN_STRING_SENTINELS,
    // Alle ni renderer skriver c.label og c.detail for hvert tjek i rækkefølge,
    // så hvert af disse felter SKAL kunne ses — escapede — i outputtet.
    mustAppearEscaped: [
      SCAN_PAYLOAD.checks.trackers.label, SCAN_PAYLOAD.checks.trackers.detail,
      SCAN_PAYLOAD.checks.ssl.label, SCAN_PAYLOAD.checks.ssl.detail,
      SCAN_PAYLOAD.checks.headers.detail,
    ],
  },
];

function familyFiles(marker) {
  const out = [];
  const walk = (dir) => {
    for (const e of readdirSync(dir)) {
      const p = join(dir, e);
      if (statSync(p).isDirectory()) walk(p);
      else if (e.endsWith('.html') && readFileSync(p, 'utf8').includes(marker)) out.push(p);
    }
  };
  walk(join(ROOT, 'site'));
  return out.sort();
}

async function runFile(file, fam) {
  const html = readFileSync(file, 'utf8');
  const blocks = [...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)]
    .map((m) => m[1])
    .filter((b) => b.includes(fam.marker));
  if (blocks.length === 0) return { error: `ingen ${fam.name}-blok` };

  // scancard har ingen fejlgren at køre; dens rendereres to gennemløb er det
  // samme svar, så vi kører den én gang. quickcheck køres stadig i to, fordi
  // `if(d.error){…;return;}` ellers aldrig ville nå succespadden.
  const rounds = fam.payload
    ? [['scansvar', fam.payload]]
    : [['fejlsvar', ERR_PAYLOAD], ['succes', OK_PAYLOAD]];

  const writes = [];
  const textWrites = [];
  let trigger = null;

  for (const [label, payload] of rounds) {
    const dom = makeDom();
    const ctx = newContext(dom.document, fetchFor(payload));
    for (const code of blocks) {
      try {
        vm.runInContext(code, ctx, { timeout: 5000, filename: file });
      } catch (e) {
        return { error: `scriptfejl under indlæsning (${label}) — ${e.message}` };
      }
    }
    const t = findTrigger(ctx, dom.document);
    if (!t) {
      return { error: 'ingen trigger fundet (ingen submit-handler, ingen global funktion, ingen Enter-handler)' };
    }
    trigger = trigger ? trigger + '+' + t.kind : t.kind;
    try {
      await t.run();
    } catch (e) {
      // En fejl under rendering er ikke et bevis på sikkerhed.
      return { error: `triggeren ${t.kind} kastede i ${label}-svaret — ${e.message}` };
    }
    writes.push(...dom.writes);
    for (const t of dom.textWrites) textWrites.push(t);
  }
  return { writes, textWrites, trigger, innerHtmlInSource: /\.innerHTML\s*=/.test(html) };
}

function problemsIn(all, sentinels, allowed, mustAppearEscaped = []) {
  const problems = [];
  for (const p of sentinels) {
    if (all.includes(p)) problems.push(`payload kom igennem råt: ${p}`);
  }
  for (const p of mustAppearEscaped) {
    if (!all.includes(escapeHtml(p))) {
      problems.push(`feltet kom slet ikke frem (heller ikke escaped) — renderen døde: ${p}`);
    }
  }
  const stray = all.replace(allowed, '').match(/<[a-zA-Z/!][^>]*>/);
  if (stray) problems.push(`uventet rå tag: ${stray[0].slice(0, 80)}`);
  return problems;
}

// Renderer scannerens egen catch-klar, og så fanger vi den hellere.
//
// Forskellen på "siden håndterede et fejlsvar" og "renderen døde" er, om
// teksten indeholder en af payloads. Fejlgrenen skriver `d.error` — altså
// payload'en — og det er den tilsigtede vej. En renderer, der dør, skriver derimod
// en ren netværksfejl uden payload. Første version af denne detektor matchede
// begge og erklærede `response-time-monitor` rød, fordi den *med vilje* viser
// fejlsvaret. En gate, der røber på det rigtige, er lige så ubrugelig som en
// der ikke kan fejle.
const ABORT_TEXT = /Network error|Could not reach|Scan failed|Check failed/i;
function abortedRender(textWrites, sentinels) {
  return textWrites.find(
    (t) => ABORT_TEXT.test(t.text) && !sentinels.some((p) => t.text.includes(p))
  );
}

// ---------------------------------------------------------------- selftest
async function selftest() {
  const mk = (body) =>
    `
(function(){
  function esc(s){var d=document.createElement('div');d.textContent=String(s==null?'':s);return d.innerHTML;}
  var f=document.getElementById('du-form');
  f.addEventListener('submit',async function(e){
    var res=document.getElementById('du-result');
    var api='https://deskuptime-quickcheck.mahope-eeb.workers.dev/?url='+encodeURIComponent('x');
    var r=await fetch(api);
    var d=await r.json();
${body}
  });
})();
`;
  const cases = [
    {
      name: 'alle felter escaped (skal være sikker)',
      body: "    res.innerHTML='<strong>'+esc(d.status)+' '+esc(d.statusText)+'</strong> '+esc(d.responseMs)+'ms';",
      expectSafe: true,
    },
    {
      name: 'ÉN esc() fjernet (skal lække)',
      body: "    res.innerHTML='<strong>'+esc(d.status)+' '+d.statusText+'</strong>';",
      expectSafe: false,
    },
    {
      name: 'esc() helt fjernet (skal lække)',
      body: "    res.innerHTML='<strong>'+d.status+' '+d.statusText+'</strong>';",
      expectSafe: false,
    },
    {
      name: 'd.error lækker uden esc() (skal lække)',
      body: "    res.innerHTML='E '+d.error;",
      expectSafe: false,
    },
  ];
  // scancard-familien har sin egen minimalrenderer, så selftestens negative
  // cases ikke kan afhænge af, at repoets filer er korrekte — de skal kunne
  // fejle, også hvis alle 5 sider bliver ødelagt.
  const cardMk = (body) =>
    `
(function(){
  var API = 'https://eucomply-scan.mahope-eeb.workers.dev';
  var form = document.getElementById('scan-form');
  var input = document.getElementById('url');
  var errEl = document.getElementById('err');
  var btn = document.getElementById('btn');
  var results = document.getElementById('results');
  var cardsEl = document.getElementById('cards');
  // Den regex-baserede escaper — samme form som de fem scanner-sider bruger,
  // så selftesten prøver den escaper der faktisk er i drift.
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (m) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
    });
  }
  function pillText(){ return 'Pass'; }
  form.addEventListener('submit', async function(e){
    var r = await fetch(API + '/scan?url=x');
    var d = await r.json();
    var c = d.checks.trackers;
    var k = 'trackers';
    var card = document.createElement('div');
${body}
    cardsEl.appendChild(card);
  });
})();
`;
  const cardCases = [
    {
      name: 'scancard: begge felter escaped (skal være sikker)',
      body: "    card.innerHTML = '<b>' + esc(c.label || k) + '</b>' + '<p>' + esc(c.detail || '') + '</p>';",
      expectSafe: true,
    },
    {
      name: 'scancard: esc() kun omkring label (skal lække via detail)',
      body: "    card.innerHTML = '<b>' + esc(c.label || k) + '</b>' + '<p>' + (c.detail || '') + '</p>';",
      expectSafe: false,
    },
    {
      name: 'scancard: esc() fjernet helt (skal lække)',
      body: "    card.innerHTML = '<b>' + (c.label || k) + '</b>' + '<p>' + (c.detail || '') + '</p>';",
      expectSafe: false,
    },
  ];

  let bad = 0;
  for (const c of cardCases) {
    const { writes, document } = makeDom();
    const ctx = newContext(document, fetchFor(SCAN_PAYLOAD));
    try {
      vm.runInContext(cardMk(c.body), ctx, { timeout: 5000 });
    } catch (e) {
      console.log(`  FEJL  ${c.name}: scriptfejl — ${e.message}`);
      bad++;
      continue;
    }
    const trigger = findTrigger(ctx, document);
    if (!trigger) {
      console.log(`  FEJL  ${c.name}: ingen trigger — testen kan ikke fange noget`);
      bad++;
      continue;
    }
    await trigger.run();
    const all = writes.map((w) => w.html).join('\n');
    if (!all) {
      console.log(`  FEJL  ${c.name}: ingen .innerHTML skrevet`);
      bad++;
      continue;
    }
    const problems = problemsIn(all, SCAN_STRING_SENTINELS, ALLOWED_TAGS_SCANCARD,
      ['<script>alert(2)</script>', '<svg onload=alert(3)>']);
    const safe = problems.length === 0;
    const ok = safe === c.expectSafe;
    if (!ok) bad++;
    console.log(
      `  ${ok ? 'OK  ' : 'FEJL'}  ${c.name}: ` +
      (safe ? 'ingen markup lækket' : 'lækket — ' + problems[0])
    );
  }
  for (const c of cases) {
    const { writes, document } = makeDom();
    const ctx = newContext(document, hostileFetch);
    try {
      vm.runInContext(mk(c.body), ctx, { timeout: 5000 });
    } catch (e) {
      console.log(`  FEJL  ${c.name}: scriptfejl — ${e.message}`);
      bad++;
      continue;
    }
    const trigger = findTrigger(ctx, document);
    if (!trigger) {
      console.log(`  FEJL  ${c.name}: ingen trigger — testen kan ikke fange noget`);
      bad++;
      continue;
    }
    await trigger.run();
    const all = writes.map((w) => w.html).join('\n');
    if (!all) {
      console.log(`  FEJL  ${c.name}: ingen .innerHTML skrevet`);
      bad++;
      continue;
    }
    const problems = problemsIn(all, STRING_SENTINELS, ALLOWED_TAGS);
    const safe = problems.length === 0;
    const ok = safe === c.expectSafe;
    if (!ok) bad++;
    console.log(
      `  ${ok ? 'OK  ' : 'FEJL'}  ${c.name}: ` +
      (safe ? 'ingen markup lækket' : 'lækket — ' + problems[0])
    );
  }
  if (bad) {
    console.log(`\nRENDER-SELFTEST RØD — ${bad} case(s) gav forkert svar`);
    return 1;
  }
  const negatives = cardCases.filter((c) => !c.expectSafe).length + cases.filter((c) => !c.expectSafe).length;
  const positives = cardCases.filter((c) => c.expectSafe).length + cases.filter((c) => c.expectSafe).length;
  console.log(`\nRENDER-SELFTEST GRØN — ${negatives} negative og ${positives} positive cases opfører sig korrekt`);
  return 0;
}

if (process.argv.includes('--selftest')) {
  process.exit(await selftest());
}

// ------------------------------------------------------------------ kørslen
let failed = 0;
let tested = 0;
let textOnly = 0;
let total = 0;

for (const fam of FAMILIES) {
  const files = familyFiles(fam.marker);
  console.log(`\n${fam.name}: ${files.length} filer`);
  total += files.length;
  for (const f of files) {
    const rel = relative(ROOT, f);
    let res;
    try {
      res = await runFile(f, fam);
    } catch (e) {
      console.log(`FEJL  ${rel}: ${e.message}`);
      failed++;
      continue;
    }
    if (res.error) {
      console.log(`FEJL  ${rel}: ${res.error}`);
      failed++;
      continue;
    }
    if (!res.writes || res.writes.length === 0) {
      if (!res.innerHtmlInSource) {
        // Kilden skriver aldrig til .innerHTML — den bruger textContent, som
        // ikke kan skabe markup. Det er sikkert af konstruktion, ikke ved held.
        textOnly++;
        console.log(`OK    ${rel}: skriver kun textContent (ingen .innerHTML i kilden)`);
        continue;
      }
      console.log(`FEJL  ${rel}: ${res.trigger} kørte, men skrev ingen .innerHTML — ` +
        `der er altså intet testet, og filen må ikke tælles som grøn`);
      failed++;
      continue;
    }
    const aborted = abortedRender(res.textWrites || [], fam.sentinels);
    if (aborted) {
      failed++;
      console.log(`FEJL  ${rel} (${res.trigger}): renderen nåede sin egen catch og skrev ` +
        `"${aborted.text.slice(0, 60)}" — kortet blev altså aldrig bygget, og ` +
        `filen må ikke tælles som grøn`);
      continue;
    }
    const all = res.writes.map((w) => w.html).join('\n');
    const problems = problemsIn(all, fam.sentinels, fam.allowed, fam.mustAppearEscaped);
    if (problems.length) {
      failed++;
      console.log(`FEJL  ${rel} (${res.trigger})`);
      for (const p of problems) console.log(`        ${p}`);
    } else {
      tested++;
      console.log(`OK    ${rel} (${res.trigger}, ${res.writes.length} skrivninger)`);
    }
  }
}

console.log(`\nrendereringsveje kørt og grønne: ${tested}`);
console.log(`textContent-only filer: ${textOnly}`);
if (failed) {
  console.log(`\nRENDER-TEST RØD — ${failed} fil(er) kan ikke dokumenteres som sikre`);
  process.exit(1);
}
if (tested + textOnly !== total) {
  console.log(`\nRENDER-TEST RØD — kun ${tested + textOnly} af ${total} filer blev testet`);
  process.exit(1);
}
console.log(`\nRENDER-TEST GRØN — alle ${total} filers renderer skrev ingen markup fra et fjendtligt svar.`);
