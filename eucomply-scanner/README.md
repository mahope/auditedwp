# EUComply Scanner

> **Universal website compliance scanner** — GDPR, DSA, ePrivacy, cookie consent, security headers, and resilience checks. Platform-independent: works on **any URL, any CMS**.

```bash
npx @mahope/eucomply-scanner https://example.com
```

## Why this exists

Most compliance scanners are tied to WordPress or require installing a plugin on your server. EUComply Scanner works from the **outside** — it fetches your page as a visitor would and analyzes the HTML + HTTP headers. No installation, no server access, no CMS dependency.

**Use it for:**
- Quick compliance health checks on any website
- Pre-acquisition due diligence
- Monitoring competitor compliance
- CI/CD pipeline compliance gates
- GDPR/DSA/ePrivacy audit preparation

> **Need WordPress document tools?** EUComply Pro provides editable DPA, NIS2/DORA and EAA starters plus an HTML report from the latest WordPress scan for $79/year per website. Hosted monitoring and runtime PDF reports are not included today.
> [EUComply Pro →](https://eucomplypro.com/pro/)

## Quick start

### Via npx (no install)

```bash
npx @mahope/eucomply-scanner https://example.com
```

### Install globally

```bash
npm install -g @mahope/eucomply-scanner
eucomply-scanner https://example.com
```

The package is published on npm as **`@mahope/eucomply-scanner`**. The unscoped
name `eucomply-scanner` has never been published, so `npm install
eucomply-scanner` fails with a 404 — use the scoped name above.


### As a library

```js
import { runScan, renderReport } from '@mahope/eucomply-scanner';

const report = await runScan('https://example.com');
console.log(renderReport(report));           // exactly what the CLI prints
console.log(`Not counted: ${report.score.conditional.join(', ') || 'none'}`);
```

`report.score.pct` is all nine checks. For a number to show a customer, use
`report.score.pct_applicable` — the checks that apply to the site. See
[API](#api).

## What it checks

| Check | Description | Why it matters |
|-------|-------------|----------------|
| **Consent Mode v2** | Google Consent Mode v2 implementation | Required since March 2024 for EEA ad personalization |
| **IAB TCF** | Transparency & Consent Framework | Required for programmatic ads in the EEA |
| **Trackers** | Third-party trackers vs consent signals | GDPR Art. 6 — consent before non-essential tracking |
| **SSL/HSTS** | HTTPS + Strict-Transport-Security | Security baseline; HSTS prevents downgrade attacks |
| **Cookies** | Cookie consent platform detection | ePrivacy Directive — consent for non-essential cookies |
| **Forms** | Form markup + privacy policy link | GDPR Art. 13 — privacy notice at point of data collection |
| **Legal** | Privacy policy, imprint, terms, etc. links | GDPR, DSA, EAA — required legal pages |
| **Security headers** | CSP, X-Content-Type-Options, Referrer-Policy | OWASP security best practices |
| **DORA-related page markers** | Static page-text references to failover, incident response and continuity | Informational only; no DNS lookup or DORA assessment |
| **Platform** | CMS/platform fingerprint (informational) | Know what you're dealing with |

## CLI usage

```bash
# Basic scan (human-readable output)
eucomply-scanner https://example.com

# JSON output for scripting
eucomply-scanner --json https://example.com

# Shorter or longer request timeout (default 12000 ms)
eucomply-scanner --timeout 25000 https://example.com
```

### Example output

The **full, real output** is in
[`examples/sample-output.txt`](examples/sample-output.txt). It is generated —
not written by hand — from a recorded capture of `https://webflow.com`
(510 616 B, sha256 `21462fbb…`, recorded 2026-09-28) by the same
`renderReport()` the CLI writes, so it cannot drift from what the tool
actually prints. An excerpt, with every line verbatim from that file:

```
$ eucomply-scanner https://webflow.com

🔍 EUComply Scan Report for https://webflow.com/
   Platform: Webflow  |  Duration: 64ms
   Score: 3/6 of the checks that apply to this site (50%)

   All 9 checks: 3/9 (33%)

 ❌ 1 tracker(s) with NO consent platform
    Trackers found in page markup: Google Analytics / GTM. No consent management platform was found — these trackers likely fire before consent.
    💡 EU ePrivacy rules and GDPR Art. 6 require consent BEFORE loading non-essential trackers. Install a CMP that blocks Google Analytics/Meta Pixel etc. until the visitor consents.

 ⚠️ No consent banner detected
    No known cookie-consent platform found in the HTML. If you set any non-essential cookies, EU ePrivacy rules require prior consent.
    💡 Add a consent management platform (e.g. one of the open-source options: Klaro, Tarteaucitron).

 ✅ HTTPS + HSTS OK
    HSTS: max-age=31536000

 ✅ 3 legal pages linked
    Found on page: Privacy / GDPR, Cookie policy, Terms & Conditions.

 ⚠️ 1 security header missing
    Missing: X-Content-Type-Options: nosniff missing
    💡 Add security headers. See https://securityheaders.com for guidance on each.
```

Two numbers, because they must not be read as one. **`3/6 (50%)`** counts only
the checks that apply to this site; the three that do not are printed as
`- not counted:` with the reason, not hidden. **`3/9 (33%)`** is all nine
checks, including the three that do not apply — it is the lower, historical
number, and it is the one to quote when comparing against an older version.

## API

### `runScan(url)`

Scans a public URL and returns a compliance report. The built-in request timeout is 12 seconds.

**Parameters:**
- `url` (string, required) — The URL to scan. Scheme defaults to `https://` if omitted.
- `timeout` (number, optional) — Request timeout in milliseconds, default `12000`.

**Returns:** A promise resolving to a report object with:
- `url` — The final URL (after redirects)
- `scannedAt` — ISO timestamp
- `durationMs` — Scan duration in milliseconds
- `platform` — Detected CMS/platform (or "Unknown")
- `checks` — Object with individual check results (each: `{ pass, warn, label, detail, fix?, applies?, condition? }`)
- `score` — see below
- `disclaimer` — Legal disclaimer

**`score` has two numbers, on purpose** — they must not be read as one:

| Field | Meaning |
|-------|---------|
| `passed` / `total` / `pct` | All checks the engine ran, including those that do not apply to this site. `pct` is the number earlier versions printed on their own. |
| `passed_applicable` / `applicable_total` / `pct_applicable` | Only the checks that apply to this site. **Use this one for a compliance number.** |
| `conditional` | Keys of the checks that were left out, so you can say which ones and why. |
| `conditional_applied` | Keys of the conditional checks that *did* apply. |

A conditional check is skipped when it cannot be judged from a public page —
IAB TCF only matters if the site runs programmatic ads, Consent Mode v2 only
if it runs Google Ads, DORA only for financial entities. A site with six
applicable checks and three of them passing scores `pct_applicable: 50`, not
`pct: 33`.

### `renderReport(report)`

Formats a report exactly as the CLI does, and returns the string. This is the
only renderer in the package: `bin`, the engine's own `main()` and
`examples/node.js` all call it. Use it instead of writing your own formatter —
see `docs/npm-pakken-egne-renderinger.md` for what happens when a second one
appears.

```js
import { runScan, renderReport } from '@mahope/eucomply-scanner';

const report = await runScan('https://example.com');
console.log(renderReport(report));
```

### `normalizeUrl(raw)`

Validates and normalizes a URL string. Returns `null` for private/internal/local addresses.

## REST API (free)

A public REST API is available at:

```
GET https://eucomply-scan.mahope-eeb.workers.dev/scan?url=https://example.com
GET https://eucomply-scan.mahope-eeb.workers.dev/stats
```

CORS-enabled for browser use. Rate-limited to 10 requests/minute/IP.

## Pro version

The current Pro license is for the WordPress plugin and adds:
- **Editable HTML starters** for a DPA, NIS2/DORA vendor clauses and an EAA statement
- **HTML report** generated from the latest WordPress scan
- **Agency or business name** used in generated documents

Hosted daily monitoring, runtime PDF reports, multi-site management and priority support are not included today.

**[EUComply Pro — $79/year per website](https://eucomplypro.com/pro/)**

## License

MIT — use it freely in your projects, CI/CD pipelines, and tools.