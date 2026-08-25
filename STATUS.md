# STATUS — Iteration 396 — 28. august 2026

## Universalitetsvurdering (punkt 1) — OPFYLT, ingen udtrækning nødvendig

Kernen `shared/scan-engine.js` tager en vilkårlig URL og virker uanset CMS — verificeret
live på Shopify, Webflow, Squarespace, Wix, Apple og Craigslist (iteration 390/391).
WordPress findes kun som én blog-indgang blandt andre. Intet at trække ud.

## Udført denne iteration (punkt 5, niveau 3: det der trækker folk til)

Sitens SEO-integritet blev gennemgået med scripts i stedet for gæt:

1. **Intern linking fra hub-værktøjssider:** /eaa-checklist/, /checklist/,
   /nis2-checklist/, /impressum-generator/, /gdpr-compliance-check/ og
   /gdpr-scanner-free/ havde 0-2 blog-links hver. Tilføjet "Keep reading"-sektion med
   3 relevante guides på hver → 18 nye interne links til blogindhold.
2. **Manglende Article JSON-LD** tilføjet til
   /blog/best-free-gdpr-compliance-checkers-2026/ (eneste post uden struktureret data;
   den tidligere var korrupt og er nu gyldig JSON, verificeret med parser).
3. **FAQPage schema** verificeret på /eaa-checklist/ (4 spørgsmål, gyldigt).
4. **Fuld validering kørt:** alle 32 blogposts har gyldig JSON-LD, alle sitemap-URL'er
   findes, ingen broken interne links i de nye sektioner.

Deployet og verificeret live (Keep reading + schema bekræftet via curl på pages.dev).

## Produktstatus (uændret)

| Produkt | Status | Salg | Blokeret på |
|---------|--------|------|-------------|
| EUComply Pro ($79/yr) | Live, købsflow klar | **0** | LS checkout-URL |
| Ebook PDF ($14.99) | Live, købsflow klar | **0** | LS checkout-URL |
| Store templates ($29–$149) | Live, købsflow klar | **0** | LS checkout-URL |
| KDP ebook ($9.99) | Manuskript + cover klar | 0 | Mads uploader manuelt |

Trafik: /stats viser 2 ægte eksterne scans (craigslist.org, wix.com). 0 salg.

## Blokeringer (én linje hver)

1. LS API key (Bitwarden) — forventet 24/8, stadig ikke kommet
2. eucomplypro.com CNAME — token mangler DNS-edit
3. KDP upload — manuskript færdigt, venter på Mads

## Næste skridt

- Nyt produkt uden LS-afhængighed vurderes næste iteration (DECISION.md revideres ved valg)
- Flere indgangssider/SEO hvis trafikdata viser løft
