# eucomply-scanner (CLI)

**CLI tool for EU compliance scanning of any website.** Works on WordPress, Shopify, Webflow, Next.js, Squarespace, Wix — any HTML stack.

Scans a URL and checks HTTPS security, cookie consent, privacy policy links, forms, security headers and legal pages against GDPR, NIS2, DORA and EAA requirements.

## Run it

```bash
# No install needed — run straight from GitHub:
npx github:mahope/eucomply-scanner example.com
```

Or clone and run locally:

```bash
git clone https://github.com/mahope/eucomply-scanner
cd eucomply-scanner/cli && npm install
node bin/eucomply-scan.js example.com
```

> An npm registry release (`npm install -g eucomply-scanner`) is planned — pending publish access. The GitHub command above always runs the latest version.

## Usage

```bash
# Single URL
npx github:mahope/eucomply-scanner example.com

# Multiple URLs
npx github:mahope/eucomply-scanner example.com shopify.com wordpress.org

# Pipe from stdin
echo "example.com" | npx github:mahope/eucomply-scanner

# JSON output (pipe to jq)
npx github:mahope/eucomply-scanner --json example.com | jq '.score'

# Quiet mode (no upsell banner)
npx github:mahope/eucomply-scanner --quiet example.com
```

Local clone shortcuts: `node bin/eucomply-scan.js` supports the same flags (`--json`, `--quiet`, multiple URLs, stdin).

## What it checks

| Check | What it looks for |
|-------|-------------------|
| 🔒 HTTPS + HSTS | TLS encryption and Strict-Transport-Security header |
| 🍪 Cookie consent | 15+ consent platforms (Cookiebot, OneTrust, CookieYes…) |
| 📋 Forms & privacy link | Form markup with visible privacy-policy link |
| 📄 Legal pages | Privacy Policy, Imprint, Terms, EAA statement |
| 🛡️ Security headers | CSP, X-Content-Type-Options, Referrer-Policy, X-Frame-Options |
| 🔍 Platform fingerprint | Detects CMS/stack (informational) |

## Exit codes

- `0` — all sites scored 50% or higher
- `1` — one or more sites failed (< 50%) or an error occurred

Useful for CI/CD pipelines: add a scan of your own site to your pre-deploy checks.

## API

This CLI wraps the free [EUComply](https://auditedwp.pages.dev) public scan API.
Need auditor-ready PDF reports, DPA generators, NIS2 vendor clause kits?
→ **Pro: $79/year** at https://auditedwp.pages.dev/#pricing

## License

MIT
