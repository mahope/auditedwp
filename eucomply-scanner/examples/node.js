#!/usr/bin/env node
/**
 * Scan a website as a library, and print exactly what the CLI prints.
 *
 *   node examples/node.js https://example.com
 *
 * The report is written by the engine's `renderReport()` — the same function
 * the `eucomply-scanner` CLI and the engine's own `main()` call. Do **not**
 * format the report here. This file used to be a third renderer of its own: it
 * printed `Score: 2/9 (22%)` and the bare check label, so a library user, the
 * CLI user and `/scan/` each got a different report out of one package. See
 * `docs/npm-pakken-egne-renderinger.md`.
 *
 * For a script, read `report.score.pct_applicable` (only the checks that apply
 * to the site) rather than `report.score.pct` (all nine). Both exist, and
 * `report.score.conditional` lists the ones that were left out and why.
 */

import { runScan, renderReport } from '../engine/index.js';

const target = process.argv[2] || 'https://example.com';

try {
  const report = await runScan(target);
  console.log(renderReport(report));
} catch (e) {
  console.error('❌ Error:', e.message);
  process.exit(1);
}
