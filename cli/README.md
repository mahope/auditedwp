# eucomply-scan-proxy (deprecated)

> **This directory is not the scanner, and it is not published.**
> `package.json` is marked `private`, so `npm publish` refuses it. It used to
> claim the name `eucomply-scanner` — the same name as the real scanner in
> `../eucomply-scanner/` — and two different programs cannot own one npm
> name. The real scanner won the name; this one kept the code.
> `tools/check_package_identity.py` now fails the build if that ever changes.
>
> This file forwards every scan to a hosted worker, so it only works while
> that worker is up and it inherits whatever that worker runs. **Use the real
> scanner instead** — it fetches the page itself, so there is no network hop,
> no rate limit and no dependency on our production:
>
> ```bash
> npx github:mahope/eucomply-scanner https://example.com
> ```
>
> See `../eucomply-scanner/README.md` for the documented install.

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
node eucomply.js example.com
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

This CLI wraps the free [EUComply](https://eucomplypro.com) public scan API.
Need editable WordPress DPA, NIS2/DORA and EAA starters plus an HTML report from the latest scan?
→ [EUComply Pro — $79/year per website](https://eucomplypro.com/pro/)

## License

MIT
