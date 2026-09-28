#!/usr/bin/env node
/**
 * Kør den **rigtige** CLI mod en optaget fixture og print dens stdout.
 *
 *   node tools/cli_example_run.mjs tools/fixtures/webflow.com.json https://webflow.com
 *
 * Dette er det, /cli/'s eksempelblok er genereret fra. Ingen gengivelse af
 * motorens formatering her — hvis den ændrer sig, ændrer det publicerede
 * eksempel sig med, fordi det er det samme program der skriver det.
 *
 * To ting stubbes, og begge er *målt* frem for *antaget*:
 *
 *   1. `fetch` — svarer med den optagede krop og de optagede overskrifter.
 *      Et kald til en anden URL end fixture'ens er en hård fejl, så en
 *      fixture kan ikke i stilhed servere en anden side end den siger.
 *   2. `cloudflare-dns.com/dns-query` — motorens SSRF-guard slår værten op i
 *      DNS. Uden dette svare kalder optagelsen to tredjepartstjenester, og
 *      resultatet afhænger af dem. Vi svarer med en målt offentlig adresse for
 *      webflow.com (104.18.32.47), så kørslen er deterministisk og kan gå uden
 *      netværk.
 */

import { readFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import { resolve, dirname } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));

/** webflow.com's own A record, measured 2026-09-28. Public, so the guard passes. */
const PUBLIC_IP = "104.18.32.47";

function dnsAnswer(name) {
  return new Response(
    JSON.stringify({
      Status: 0,
      Answer: [{ name, type: 1, TTL: 60, data: PUBLIC_IP }],
    }),
    { status: 200, headers: { "Content-Type": "application/dns-json" } },
  );
}

export function installFixtureFetch(fixture) {
  const body = gunzipSync(Buffer.from(fixture.body_gz_b64, "base64"));
  // `new URL(x).toString()` normaliserer slashes, så "https://webflow.com" og
  // "https://webflow.com/" er det samme kald. Uden det ville motorens
  // normalisering give en stående fejl på en fixture der ellers er rigtig.
  const want = new URL(fixture.url).toString();
  let served = 0;
  const saved = globalThis.fetch;
  globalThis.fetch = async (input, init) => {
    const href = typeof input === "string" ? input : input?.url ?? String(input);
    if (href.startsWith("https://cloudflare-dns.com/dns-query")) {
      const name = new URL(href).searchParams.get("name") || "";
      return dnsAnswer(name);
    }
    if (new URL(href).toString() !== want) {
      throw new Error(
        `Fixture mismatch: engine asked for ${href}, fixture holds ${want}`,
      );
    }
    served++;
    return new Response(body, {
      status: fixture.status,
      headers: { "Content-Type": "text/html; charset=utf-8", ...fixture.headers },
    });
  };
  return {
    served: () => served,
    restore: () => { globalThis.fetch = saved; },
  };
}

async function main() {
  const [fixtureArg, urlArg] = process.argv.slice(2);
  if (!fixtureArg) {
    console.error("usage: cli_example_run.mjs <fixture.json> <url>");
    process.exit(2);
  }
  const fixture = JSON.parse(readFileSync(resolve(fixtureArg), "utf8"));
  const stub = installFixtureFetch(fixture);

  const cli = resolve(HERE, "../eucomply-scanner/cli/eucomply.js");
  process.argv = [process.argv[0], cli, urlArg || fixture.url];

  // CLI'en kalder selv `process.exit(0)` når rapporten er printet, så
  // "blev fixtureen serveret" efterprøves i exit-hook'en — det er det sidste
  // øjeblik hvor vi stadig kan sige noget, og det kan ikke forbigås ved at
  // motorens promise endnu ikke er færdig da importet vender.
  process.on("exit", (code) => {
    if (stub.served() === 0) {
      process.stderr.write(
        "fixture blev aldrig serveret — eksemplet kommer ikke fra motoren\n",
      );
      process.exitCode = code || 1;
    }
    stub.restore();
  });

  try {
    await import(pathToFileURL(cli).href);
  } catch (e) {
    console.error("CLI fejlede:", e && e.message);
    process.exit(1);
  }
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  await main();
}
