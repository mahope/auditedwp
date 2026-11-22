# README — AuditedWP site

> **Frozen as of 2026-11-22.** EUComply is frozen as free open source: not actively maintained, no paid versions sold. There is no store, pricing or Pro page any more.

This directory is deployed to **Cloudflare Pages**.
Live URL: https://mahope.github.io/auditedwp
Custom domain (pending): auditedwp.com

## Structure

- `index.html` — landing page EN
- `de/index.html` — landing page DE (DACH market)
- `sample/index.html` — sample audit trail preview
- `template/index.html` — free NIS2 vendor-clause template
- `onboarding-manual.md` — operational manual for first client

## Deploy

```sh
cd site
wrangler pages deploy . --project-name=auditedwp
```

Or use the deploy.sh script.