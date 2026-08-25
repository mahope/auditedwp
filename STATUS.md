# STATUS — 25. august 2026 (Iteration 328)

## Universitets-vurdering (punkt 1) — genbekræftet

Kernerne (`shared/scan-engine.js`, `quickconvert/src/engine.js`, DevNotify) tager en vilkårlig URL/tekst og antager intet CMS. Det eneste WP-stemplede er domænenavnet `auditedwp.pages.dev`; løsningen er eucomplypro.com som custom domain. Ingen kode skal smides væk — vureringen står ved magt fra iter 326/327.

## Iteration 328: scan-tæller rettet og nulstillet

- Fundet fejl: `/stats` tællede også root-pings (health checks) som scans — tallet 83 var forurenet.
- Fix deployet til `eucomply-scan` worker (verificeret via wrangler tail: kun rigtige `/scan`-kald tæller).
- Tæller nulstillet til **0** — ægte tal starter herfra.
- Verificeret live: `/stats` → `{"scans":0}`, `/scan?url=example.com` → 200, forsiden viser kun tæller når > 0.

## Tallene (ærlige)

| Målestok | Tal |
|----------|-----|
| Revenue | **$0** |
| Betalende kunder | **0** |
| Waitlist | 0 |
| Scans (ægte, siden reset) | 0 |

## Venter på Mads

| # | Hvad | Tid for Mads |
|---|------|--------------|
| 1 | LS API-nøgle fra Bitwarden → checkout på alle 5 produkter (eller 20 min manuelt i LS-dashboard) | ~20 min |
| 2 | CNAME @ + www → `auditedwp.pages.dev` (proxied), så eucomplypro.com går live | ~5 min |

## Næste skridt
1. Så snart eucomplypro.com svarer: skift kanoniske URLs og sitemap til det neutrale domæne.
2. Fortsæt forbedring af scanneren (det der står mellem besøgende og betaling).
