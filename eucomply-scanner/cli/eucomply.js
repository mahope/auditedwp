#!/usr/bin/env node
/**
 * eucomply-scanner — CLI for EUComply Universal Scan Engine
 *
 * Denne fil fortolker argumenterne og **intet andet**. Rapporten skrives af
 * `renderReport()` i motoren, som `engine/index.js`'s egen `main()` også
 * kalder. Filen havde engang sin egen, dårligere rendering: den printer det
 * forudindtagede ni-tal, dropper `- not counted:` for de betingede rækker og
 * dropper alle `💡`-råd, så to renderer i én pakke gav to forskellige sprog.
 * Se `docs/eucomply-cli-egen-renderering.md`.
 *
 * Usage:
 *   eucomply-scanner https://example.com
 *   eucomply-scanner --json https://example.com
 *   npx @mahope/eucomply-scanner https://example.com
 */

import { runScan, renderReport } from '../engine/index.js';

const args = process.argv.slice(2);
const url = args.find(a => !a.startsWith('--'));
const jsonOutput = args.includes('--json');

if (!url || args.includes('--help') || args.includes('-h')) {
  console.log(`
EUComply Scanner v1.0.0 — Universal website compliance checker

USAGE:
  eucomply-scanner [options] <url>

OPTIONS:
  --json           Output raw JSON (default: human-readable)
  --timeout <ms>   Request timeout (default: 12000)
  --help, -h       Show this help

EXAMPLES:
  eucomply-scanner https://example.com
  eucomply-scanner --json https://example.com
  npx @mahope/eucomply-scanner https://example.com

REPORT:
  Scans a public URL for GDPR, DSA, ePrivacy, cookie consent,
  security headers, and resilience compliance signals.
  Platform-independent — works on any CMS.
`);
  process.exit(url ? 0 : 1);
}

const timeout = (() => {
  const idx = args.indexOf('--timeout');
  return idx >= 0 ? parseInt(args[idx + 1], 10) : 12000;
})();

runScan(url, { timeout }).then(report => {
  if (jsonOutput) {
    console.log(JSON.stringify(report, null, 2));
  } else {
    console.log(renderReport(report));
  }
  process.exit(0);
}).catch(e => {
  console.error('❌ Error:', e.message);
  process.exit(1);
});