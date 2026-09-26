# README — AuditedWP site

This directory is deployed to **Cloudflare Pages**.
Live URL: https://mahope.github.io/auditedwp
Custom domain (pending): auditedwp.com

## Structure

- `index.html` — landing page EN
- `de/index.html` — landing page DE (DACH market)
- `sample/index.html` — sample audit trail preview
- `template/index.html` — free NIS2 vendor-clause template
- `store/index.html` — compliance document store (Stripe, betalte skabeloner)
- Betalte skabeloner ligger i det private repo `mahope/paid-products` og leveres via Stripe.
- `onboarding-manual.md` — operational manual for first client

## Deploy

```sh
cd site
wrangler pages deploy . --project-name=auditedwp
```

Or use the deploy.sh script.