#!/usr/bin/env node

/**
 * eucomply-scan — CLI wrapper for the EUComply universal compliance scanner.
 *
 * Usage:
 *   eucomply example.com
 *   eucomply example.com shopify.com wordpress.org
 *   echo "example.com" | eucomply          # reads from stdin
 *
 * Flags:
 *   --json          output raw JSON instead of formatted table
 *   --quiet         suppress upsell banner, only show scores
 *
 * API endpoint: https://eucomply-scan.mahope-eeb.workers.dev/scan?url=
 */

const API = 'https://eucomply-scan.mahope-eeb.workers.dev/scan';

// ─── helpers ────────────────────────────────────────────────────────

function bold(s)  { return `\x1b[1m${s}\x1b[22m`; }
function green(s) { return `\x1b[32m${s}\x1b[0m`; }
function yellow(s){ return `\x1b[33m${s}\x1b[0m`; }
function red(s)   { return `\x1b[31m${s}\x1b[0m`; }
function dim(s)   { return `\x1b[2m${s}\x1b[22m`; }
function cyan(s)  { return `\x1b[36m${s}\x1b[0m`; }

function pill(v) {
  if (v.warn && v.pass === false) return yellow('CHECK MANUALLY');
  if (v.warn) return yellow('WARNING');
  return v.pass ? green('PASS') : red('FAIL');
}

function icon(k) {
  return ({ssl:'🔒', cookies:'🍪', forms:'📋', legal:'📄', headers:'🛡️'})[k] || '•';
}

function scoreBadge(n) {
  if (n >= 80) return green(` ${n}% `);
  if (n >= 50) return yellow(` ${n}% `);
  return red(` ${n}% `);
}

// ─── scan one URL ────────────────────────────────────────────────────

async function scan(url) {
  const u = new URL(API);
  u.searchParams.set('url', url);
  const resp = await fetch(u.toString());
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.error || `HTTP ${resp.status}`);
  return data;
}

function renderOne(data, opts) {
  const u = new URL(data.url);
  console.log(bold(`\n╔══ ${green('EUComply Scan')} ═══ ${cyan(u.hostname)} ${dim(`(${data.durationMs}ms)`)}`));

  if (opts.json) {
    console.log(JSON.stringify(data, null, 2));
    return;
  }

  // Platform
  const plat = data.platform !== 'Unknown' ? `Platform: ${cyan(data.platform)}` : dim('Platform: Unknown');
  console.log(`║  Score: ${scoreBadge(data.score.pct)}  ${data.score.passed}/${data.score.total} checks  ·  ${plat}`);
  console.log(`║  ${dim(data.url)}`);

  // Individual checks
  for (const [key, c] of Object.entries(data.checks)) {
    const label = c.label || key;
    let detail = c.detail || '';
    const line = `║  ${icon(key)}  ${label.padEnd(35)} ${pill(c)}`;
    console.log(line);
    if (!opts.quiet && detail) {
      while (detail.length > 0) {
        const chunk = detail.slice(0, 72);
        console.log(`║  ${dim(chunk)}`);
        detail = detail.slice(72);
      }
    }
  }
  console.log(`╚${'═'.repeat(50)}`);

  // Upsell (unless --quiet)
  if (!opts.quiet) {
    console.log(dim('Need auditor-ready PDF reports, DPA docs, NIS2 clauses & EAA statements?'));
    console.log(dim('→ ') + cyan('https://auditedwp.pages.dev/#pricing') + dim('  ($79/yr)'));
    console.log();
  }

  return data.score;
}

// ─── main ────────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);
  const opts = { json: false, quiet: false };

  // Parse flags (must come before URLs)
  const urls = [];
  for (const a of args) {
    if (a === '--json')       opts.json = true;
    else if (a === '--quiet') opts.quiet = true;
    else if (a === '--help' || a === '-h') {
      console.log(`
Usage: eucomply <url> [url2 ...] [--json] [--quiet]

Scan any URL for EU compliance gaps (GDPR, NIS2, DORA, EAA).

Arguments:
  url           One or more URLs to scan (protocol optional, defaults to https://)

Options:
  --json        Output raw JSON instead of formatted table
  --quiet       Suppress upsell banner, show compact output
  --help, -h    Show this help

Examples:
  eucomply example.com
  eucomply example.com shopify.com wordpress.org
  echo "example.com" | eucomply
  eucomply --json example.com | jq '.score'

Exit code: 0 if all URLs have score >= 50, 1 otherwise.
`);
      process.exit(0);
    }
    else {
      let u = a.trim();
      if (!/^https?:\/\//i.test(u)) u = 'https://' + u;
      urls.push(u);
    }
  }

  // Read from stdin if no URLs on command line
  if (urls.length === 0 && !process.stdin.isTTY) {
    const chunks = [];
    for await (const chunk of process.stdin) chunks.push(chunk);
    const lines = Buffer.concat(chunks).toString('utf-8').trim().split('\n');
    for (const line of lines) {
      let u = line.trim();
      if (u && !/^https?:\/\//i.test(u)) u = 'https://' + u;
      if (u) urls.push(u);
    }
  }

  if (urls.length === 0) {
    console.error('Error: provide at least one URL or pipe URLs via stdin.');
    console.error('Usage: eucomply example.com');
    process.exit(1);
  }

  // Scan each URL sequentially (respects rate limit — 20/10min)
  let allPass = true;
  for (let i = 0; i < urls.length; i++) {
    if (i > 0 && !opts.json) console.log(dim('───'));
    try {
      const data = await scan(urls[i]);
      const score = renderOne(data, opts);
      if (score.pct < 50) allPass = false;
    } catch (err) {
      console.error(red('✖ Error:'), err.message);
      allPass = false;
    }
  }

  process.exit(allPass ? 0 : 1);
}

main();