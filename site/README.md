# AuditedWP — GitHub Pages deployment

Static site in this folder. Deploy:

```sh
cd site
sh deploy.sh
```

Live URL: https://mahope.github.io/auditedwp/

- No build step, no backend. Pure static HTML/CSS.
- Checkout = email CTA → onboarding call → Stripe (see BUILD.md).
- When the domain auditedwp.com is bought, it can be set via GitHub Pages custom domain.

## Pages

| URL | Content |
|-----|---------|
| `/` | EN landing page |
| `/de/` | DE landing page (DACH market) |
| `/sample/` | Sample audit trail |
| `/template/` | Free NIS2/DORA vendor-clause template |
| `/deliverables/` | DPA, NDA, report templates (onboarding docs) |