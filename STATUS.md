# STATUS — Iteration 63 (2026-08-24): EAA-checkliste live — ny SEO-indgang til betalingsvillig B2B-gruppe

**Dato:** 2026-08-24
**Status:** 8 produkter/flader live. Beslutningen holder under pengekriteriet. Blokering uændret: Mads' konti (Gumroad/CWS/npm).

## Universality-vurdering (punkt 1) — BESTÅET (re-verificeret i iteration 62 med live-bevis mod Shopify/Webflow/Squarespace/Nuxt)

Kernen (Worker) tager en almindelig URL og virker uanset CMS. WP-plugin og Chrome-extension er indpakninger. Intet behøver trækkes ud.

## Bygget i denne iteration

| Ændring | Hvorfor | Status |
|---------|---------|--------|
| **/eaa-checklist/ — interaktiv European Accessibility Act-checkliste** | Nyt gratis værktøj på højt-volumen B2B keyword ("EAA checklist"). 28 punkter i 6 kategorier mappet til Directive (EU) 2019/882 + EN 301 549 / WCAG 2.1 AA, live score-meter, prioriteret gap-liste, FAQ + FAQPage-schema, disclaimer. Konverterer til /scan/ og /store/. | ✅ Deployet + verificeret (200, "0 / 28", 28 inputs) |
| Navigation + sitemap + blog-index + intern linkning | Linket fra forsiden, /checklist/-nav, blog-index-kort, sitemap (priority 0.9), og indbygget link fra den eksisterende EAA-guide (/blog/european-accessibility-act-guide/) → checkliste. | ✅ Verificeret live |

Hvorfor EAA: målgruppen (alle der sælger forbrugertjenester i EU — e-handel, bank, telecom) er netop den gruppe der betaler for compliance-templates og Pro. Loven har virket siden 28. juni 2025, så smerten er aktuel og tvingende. Prioritet fulgt: (3) det der trækker folk til. Ingen udgifter.

## Portefølje

| # | Produkt | Status | Pris |
|---|---------|--------|------|
| 1 | EUComply Scanner | ✅ Live, universel (live-testet mod 4 platforme 24/8) | Free / $79 yr |
| 2 | ComplianceDocs Generator | ✅ Live på /tools/ + /store/ | Free / $29–149 |
| 3 | Chrome Extension | ✅ Kode klar | Venter Mads' CWS-konto |
| 4 | Compliance Badge Widget | ✅ Live på /badge/ | Free (backlinks) |
| 5 | EUComply Pro (/pro/) | ✅ Sales page live | $79/yr via Gumroad (venter) |
| 6 | GDPR Checklist (/checklist/) | ✅ Live | Free → feeder scanner + templates |
| 7 | NIS2 Checklist (/nis2-checklist/) | ✅ Live | Free → feeder scanner + templates |
| 8 | EAA Checklist (/eaa-checklist/) | ✅ Live | Free → feeder scanner + templates |

## Blokering (uændret — Mads' konti)

**Dette er den eneste flaskehals for revenue.** Gumroad (~10 min), Chrome Web Store ($5), npm-konto. Så snart Gumroad findes: skift checkout-links i /pro/ og /store/, deploy (1 min), første salg muligt samme dag.

## Klart til Mads (venter på ja)
- ✅ Gumroad-produkter prissat, tekster klar
- ✅ Sociale opslag skrevet og klar til afsendelse

## Budget
0 kr brugt / 1.000 kr.

## Næste iteration
- Mobil-gennemgang af /eaa-checklist/ og /nis2-checklist/
- Interne links fra øvrige blogindlæg → de tre checklister
- Flere SEO-indgange ("cookie policy generator" landing)
