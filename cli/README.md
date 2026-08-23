# eucomply-scan

**CLI tool for EU compliance scanning of any website.** Works on WordPress, Shopify, Webflow, Next.js, Squarespace, Wix — any HTML stack.

Scans a URL and checks HTTPS security, cookie consent, privacy policy links, forms, security headers and legal pages against GDPR, NIS2, DORA and EAA requirements.

```
npx eucomply-scan example.com
```

## Install

```bash
npm install -g eucomply-scan
# or run directly:
npx eucomply-scan example.com
```

## Usage

```bash
# Single URL
eucomply example.com

# Multiple URLs
eucomply example.com shopify.com wordpress.org

# Pipe from stdin
echo "example.com" | eucomply

# JSON output (pipe to jq)
eucomply --json example.com | jq '.score'

# Quiet mode (no upsell banner)
eucomply --quiet example.com
```

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

Useful for CI/CD pipelines: add `eucomply your-site.com` to your pre-deploy checks.

## API

This CLI wraps the free [EUComply](https://auditedwp.pages.dev) public API.  
Need auditor-ready PDF reports, DPA generators, NIS2 vendor clause kits?  
→ **Pro: $79/year** at https://auditedwp.pages.dev/#pricing

## License

MIT