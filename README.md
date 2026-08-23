# AuditedWP — Cloudflare Pages deployment

Static site in this folder. Deploy:

```
cd site
npx wrangler pages deploy . --project-name=auditedwp
```

- Free tier, `*.pages.dev` URL (auditedwp.pages.dev) until the domain
  auditedwp.com is bought via Cloudflare and attached.
- No build step, no backend. Checkout = Stripe Payment Links / email CTA
  (see BUILD.md step 2).
