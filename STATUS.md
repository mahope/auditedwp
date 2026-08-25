# Iteration 350 — 25. august 2026

## Universality-vurdering (punkt 1): OPFYLDT — bekræftet igen

Kernen (`shared/scan-engine.js`) tager en vilkårlig URL og virker uanset
CMS. Verificeret live denne iteration: Shopify-scan returnerede
platform "Shopify" med 9 checks. Tidligere verificeret: Next.js,
Squarespace, WordPress. WordPress-signaturer er kun informationel
fingerprinting. Web, CLI og Worker-API er indpakninger omkring kernen.
**Ingen udtrækning nødvendig.**

## Hvad blev gjort i denne iteration

1. **Per-domain stats verificeret end-to-end:** `/stats` returnerer nu
   `{scans, domains}` — example.com (min smoke-test) og www.shopify.com
   ligger adskilt. Fra nu af kan ægte ekstern trafik skældnes fra mine
   egne tests. Commitet som 7904f73, pushed.
2. **Link-audit af hele sitet:** alle 154 unikke interne links i
   `site/` peger på filer der findes. 0 brudte links.
3. **Sitemap-audit:** sitemap.xml matcher disk 1:1 (142 URLs, samme
   sæt). Ingen 404'ere i SEO-fladen.
4. **Live-tjek:** forside, /scan/ og /store/ serverer rigtigt indhold
   på auditedwp.pages.dev; scan-workeren svarer korrekt.
5. Kvalitetsgennemgang af købsrejsen: checkout-UI er allerede bygget
   til at flippe automatisk når CHECKOUT_URL-secret sættes (LS key).
   Intet at rette før den kommer.

## Portefølje-status (uændret)

| Produkt | Status | Kan tage penge? |
|---------|--------|----------------|
| EUComply Free | Live | Nej (gratis) |
| EUComply Pro ($79/yr) | Live, klar | **Nej — mangler LS key** |
| QuickFormat ($9) | App + side live | **Nej — mangler LS key** |
| DevNotify ($19) | Side live, extension pakket | **Nej — LS + CWS credentials** |
| ComplianceDocs ($29–$149) | Store live | **Nej — mangler LS key** |

## Traction (ærlige tal)

- 0 betalende kunder, 0 rigtige tilmeldinger.
- Ægte eksterne scanninger efter nulstilling: 0 (de 2 i tælleren er
  mine egne verifikationsscans, synlige adskilt i /stats).

## Venter på Mads (én linje hver)

1. LS API key i Bitwarden (eller manuel opsætning ~20 min, LS-MANUAL.md).
2. DNS CNAME @/www → auditedwp.pages.dev (token mangler DNS-edit).

## Næste skridt

1. LS key → opret produkter via API → sandbox-køb → første betaling.
2. Imens: ingen nye produkter; kun forbedringer der ikke kræver trafik
   eller konti. Næste iteration: gennemgå /pro/-salgssiden og
   ComplianceDocs-siderne som en fremmed ville læse dem.
