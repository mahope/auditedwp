#!/usr/bin/env node
// Kør den analytics-tag, der faktisk ligger i den publicerede side, i en
// stubbet DOM, og fortæl om der sendes et pageview-event.
//
// Det her findes, fordi taggen *ser* rigtig ud og alligevel kan sende
// intet: Plausible-proxy-scriptet definerer selv sit endpoint og sit
// domæne og kalder sig kun op, hvis `plausible.o` findes. Det `o` sættes
// af inline-stubben, og om det overlever afhænger af om det eksterne
// `async`-script nåede at køre før eller efter stubben. Begge rækkefølger
// er mulige i en rigtig browser, så begge må give præcis ét pageview.
//
// Uden denne måling er en tag, der sender intet, identisk med en side
// ingen besøger — og det er umuligt at skelne de to fra en rapport, der
// siger 0 besøgende.
//
// Kørsel:
//   node tools/analytics_probe.mjs <side.html> <tracker.js>
//
// Printer én JSON-linje paa stdout. Fejler hvis siden ikke har nogen
// analytics-tag — den skal findes, ikke antages.

import { readFileSync } from "node:fs";
import vm from "node:vm";

const [pagePath, scriptPath] = process.argv.slice(2);
if (!pagePath || !scriptPath) {
  process.stderr.write("brug: analytics_probe.mjs <side.html> <tracker.js>\n");
  process.exit(2);
}

const html = readFileSync(pagePath, "utf8");
const external = html.match(
  /<script\b[^>]*\bsrc="(https:\/\/analytics\.[^"]+)"[^>]*><\/script>/i
);
if (!external) {
  process.stdout.write(JSON.stringify({ fejl: "ingen analytics-tag i siden", src: null }) + "\n");
  process.exit(3);
}
const src = external[1];
const inline = [...html.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/gi)]
  .map((m) => m[1])
  .filter((code) => /\bplausible\b/.test(code));

const tracker = readFileSync(scriptPath, "utf8");

// Kør taggen i en DOM-stub. `fetch` registrerer events i stedet for at
// sende dem, så der er ingen skrivning mod nogen tjeneste.
function run(order) {
  const events = [];
  const document_ = {
    visibilityState: "visible",
    referrer: "",
    cookie: "",
    documentElement: { className: "", style: {}, clientWidth: 1920, clientHeight: 1080, scrollHeight: 3000 },
    head: {},
    body: {},
    addEventListener() {},
    querySelectorAll: () => [],
    querySelector: () => null,
  };
  const sandbox = {
    document: document_,
    location: {
      href: "https://eucomplypro.com/", pathname: "/", search: "", hash: "",
      hostname: "eucomplypro.com", protocol: "https:", host: "eucomplypro.com",
    },
    history: { pushState() {} },
    navigator: { userAgent: "Mozilla/5.0 (Macintosh) Chrome/140" },
    screen: { width: 1920, height: 1080 },
    innerWidth: 1920,
    innerHeight: 1080,
    addEventListener() {},
    removeEventListener() {},
    setTimeout: () => 1,
    clearTimeout() {},
    setInterval: () => 0,
    clearInterval() {},
    fetch: (url, options) => {
      events.push({ url, body: options && options.body });
      return Promise.resolve({ ok: true, status: 202 });
    },
    console: { warn() {}, log() {}, error() {} },
  };
  sandbox.window = sandbox;
  sandbox.self = sandbox;
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  const steps = order === "script-first" ? [tracker, ...inline] : [...inline, tracker];
  for (const code of steps) {
    try {
      vm.runInContext(code, sandbox, { filename: "analytics.js" });
    } catch (error) {
      return { fejl: error.message, events: [] };
    }
  }
  return { fejl: null, events };
}

const parse = (body) => {
  try {
    return JSON.parse(body);
  } catch {
    return {};
  }
};

const result = { src, inline: inline.length, ordninger: {} };
for (const order of ["inline-first", "script-first"]) {
  const r = run(order);
  const pageviews = r.events.filter((e) => parse(e.body).n === "pageview");
  result.ordninger[order] = {
    fejl: r.fejl,
    events: r.events.length,
    pageviews: pageviews.length,
    domaener: [...new Set(pageviews.map((e) => parse(e.body).d).filter(Boolean))],
    endepunkter: [...new Set(pageviews.map((e) => e.url))],
  };
}
process.stdout.write(JSON.stringify(result) + "\n");
