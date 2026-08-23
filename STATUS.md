# STATUS — Iteration 62 (2026-08-24): Universality re-verificeret med live-bevis + NIS2-checkliste live

**Dato:** 2026-08-24
**Status:** 7 produkter/flader live. Beslutningen holder under pengekriteriet. Blokering uændret: Mads' konti (Gumroad/CWS/npm).

## Universality-vurdering (punkt 1) — RE-verificeret denne iteration

**✅ BESTÅET — intet behøver trækkes ud, intet er platform-bundet.**

Friske live-bevis (24/8): scan-API'en kaldt mod 4 ikke-WP-sider og identificerede platform + kørende alle 6 checks korrekt:

| Side | Platform detekteret | Checks |
|------|--------------------|--------|
| shopify.com | Shopify | 6/6 kørt (ssl/cookies/forms/legal/headers/resilience) |
| webflow.com | Webflow | 6/6 |
| squarespace.com | Squarespace | 6/6 |
| neal.fun | Nuxt | 6/6 |

Kernen (Cloudflare Worker) tager en almindelig URL og virker uanset CMS. WP-plugin, Chrome-extension osv. er indpakninger. Ingen refaktorering nødvendig.

## Bygget i denne iteration

| Ændring | Hvorfor | Status |
|---------|---------|--------|
| **/nis2-checklist/ — interaktiv NIS2-checkliste** | Nyt gratis værktøj på B2B-højt-volumen keyword ("nis2 compliance checklist"). 24 punkter i 6 kategorier mappet til Art. 21, live score-meter, prioriteret gap-liste, FAQ + FAQPage-schema, disclaimer. Konverterer til /scan/ og /store/. | ✅ Deployet + verificeret (200, "0 / 24", 24 items) |
| Navigation + sitemap + blog-index | Linket fra forsiden (/nis2-checklist/), /checklist/-nav, blog-index-kort, sitemap (priority 0.9). | ✅ Verificeret live |

Prioritet fulgt: (3) det der trækker folk til — NIS2-købere er netop den B2B-gruppe der betaler for templates og Pro. Ingen udgifter.

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

## Blokering (uændret — Mads' konti)

**Dette er den eneste flaskehals for revenue.** Gumroad (~10 min), Chrome Web Store ($5), npm-konto. Så snart Gumroad findes: skift checkout-links i /pro/ og /store/, deploy (1 min), første salg muligt samme dag.

## Klart til Mads (venter på ja)
- ✅ Gumroad-produkter prissat, tekster klar
- ✅ Sociale opslag skrevet og klar til afsendelse

## Budget
0 kr brugt / 1.000 kr.

## Næste iteration
- Flere SEO-indgange ("EAA checklist", "cookie policy generator" landing)
- Interne links fra blogindlæg → /nis2-checklist/
- Mobil-gennemgang af /nis2-checklist/
