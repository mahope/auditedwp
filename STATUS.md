# STATUS

## 2026-08-23 — Pivot tilbage til AuditedWP (iteration 33)

### Beslutning
ComplianceDocs dumpede på fire af fem penge-kriterier (ingen tilbagevendende indtægt,
SEO-afhængig, lille beløb pr. kunde). **AuditedWP vinder tilbage** på månedlig MRR,
højere beløb pr. kunde, og at produktet allerede er bygget og live. Nul-indsats-testen
er fjernet fra mandatet — manuelt arbejde er OK når målet er penge.

### Hvad er gjort i denne iteration
- **DECISION.md** — omskrevet med penge-begrundelse. ComplianceDocs kasseret, AuditedWP tilbage.
- **BUILD.md** — opdateret med korteste vej til første betalende kunde.
- **BUDGET.md** — complidocs.com fjernet, auditedwp.com tilbage.
- **Cloudflare Pages setup** — wrangler installeret (v4.125.0), wrangler.toml oprettet,
  alle canonical/hreflang URL'er opdateret til `auditedwp.pages.dev`, sitemap/robots
  opdateret, deploy.sh omskrevet til Cloudflare Pages.

### Hvad jeg IKKE har kunnet gøre selv
- **Cloudflare Pages deploy** — kræver `wrangler login` (Mads' Cloudflare OAuth).
  Sitet er stadig live på GitHub Pages: https://mahope.github.io/auditedwp/
  Når Mads kører `wrangler login` én gang, er deploy bare `sh site/deploy.sh`.

### Næste skridt — blokeret på Mads
1. **Stripe-konto** — under hvis navn? Skal oprettes før checkout virker.
2. **Udadvendt henvendelse** — 5 pilot-bureauer fra offentlige lister. Har jeg brug for ja?
3. **Domæne auditedwp.com (~70 DKK)** — forhåndsgodkendt; købes via Cloudflare.
4. **Cloudflare Pages deploy** — `wrangler login` én gang, så deployer jeg.
5. **Juridisk review** af DPA/NDA før første underskrift.

### Budget
0 kr brugt. Domæne ~70 DKK planlagt (forhåndsgodkendt).