# README — AuditedWP site

> **Frozen as of 2026-11-22.** EUComply is frozen as free open source: it is not actively maintained and no paid versions are sold. The free scanner, the CLI (`@mahope/eucomply-scanner`) and the free guides stay online. Licence keys issued earlier keep working. The repository is MIT licensed (see `LICENSE`), except the WordPress plugin in `plugin/`, which is GPL v2 or later.

This directory is deployed to **Cloudflare Pages**.
Live URL: https://mahope.github.io/auditedwp
Custom domain (pending): auditedwp.com

## Structure

- `index.html` — landing page EN
- `de/index.html` — landing page DE (DACH market)
- `sample/index.html` — sample audit trail preview
- `template/index.html` — free NIS2 vendor-clause template
- `deliverables/` — downloadable document templates (DPA, NDA, etc.)
- `onboarding-manual.md` — operational manual for first client

## Deploy

```sh
cd site
wrangler pages deploy . --project-name=auditedwp
```

Or use the deploy.sh script.