# STATUS — Iteration 66 (2026-08-24): Universality re-vurdering + Terms of Service Generator live

**Dato:** 2026-08-24
**Status:** 11 produkter/flader live. Beslutningen holder under pengekriteriet. Blokering uændret: Mads' konti (Gumroad/CWS/npm).

## Universality-vurdering (punkt 1) — BESTÅET med live-bevis

Gennemgang af alle 10 eksisterende flader:

- **Kernen** (scan-Worker på Cloudflare) tager en almindelig URL og returnerer resultater — CMS-uafhængigt. Live-API-kald mod Shopify/Webflow/Nuxt-verificeret i iteration 62.
- **Alle generatorer** (privacy, cookies, compliance-docs, ny ToS) kører 100 % i browseren og tager kun tekstinput — intet CMS-afhængigt. Output er HTML der kan indsættes hvor som helst.
- **Checklisterne** (GDPR/NIS2/EAA) er platform-neutrale selv-vurderinger.
- WP-plugin (`plugin/`) og Chrome-extension (`chrome-ext/`) er indpakninger omkring kernen — aldrig selve produktet.

**Konklusion: intet behøver trækkes ud. Porteføljen opfylder allerede punkt 1.**

## Bygget i denne iteration

| Ændring | Hvorfor | Status |
|---------|---------|--------|
| **/terms-of-service-generator/ — interaktiv ToS-generator** | "Terms of service generator" har stor søgevolumen og købsintent → feeder $29–149 templates i /store/, /pro/ og scanneren. 7 spørgsmål (navn, URL, mail, site-type, lovvalg: DK/DE/NL/IE/UK/US, samt accounts/betaling/UGC/API) → 18-sektions ToS med acceptable use, betaling & fornyelse, refunder, UGC-licens, liability-cap, indemnity, termination, ændringsmekanisme, ODR-platform. EU-forbrugerret fair-clauses. Copy/download, FAQPage-schema, disclaimer. | ✅ Deployet; logik verificeret med Node DOM-shim (ecommerce+accounts+pay+UGC = 18 sektioner inkl. German law; tom form = minimal-tilstand korrekt) |
| Intern linkning | Nav på forsiden + privacy- + cookie-generatoren, kort på blog-index, krydslink fra /tools/-hubben. Sitemap opdateret (priority 0.9). | ✅ Verificeret live |
| Mobil-tjek af generatorer/checklister | Alle har media queries ved 600px, flydende felter, ingen faste bredder > 600px undtagen max-width-containere. Ingen rettelser nødvendige. | ✅ Gennemgået |

Prioritet (3): det der trækker folk til. Ingen udgifter.

## Portefølje

| # | Produkt | Status | Pris |
|---|---------|--------|------|
| 1 | EUComply Scanner | ✅ Live, universel | Free / $79 yr |
| 2 | ComplianceDocs Generator (/tools/) | ✅ Live | Free / $29–149 |
| 3 | Chrome Extension | ✅ Kode klar | Venter Mads' CWS-konto |
| 4 | Compliance Badge Widget | ✅ Live på /badge/ | Free (backlinks) |
| 5 | EUComply Pro (/pro/) | ✅ Sales page live | $79/yr via Gumroad (venter) |
| 6 | GDPR Checklist (/checklist/) | ✅ Live | Free → feeder scanner + templates |
| 7 | NIS2 Checklist (/nis2-checklist/) | ✅ Live | Free → feeder scanner + templates |
| 8 | EAA Checklist (/eaa-checklist/) | ✅ Live | Free → feeder scanner + templates |
| 9 | Cookie Policy Generator | ✅ Live | Free → feeder templates + scanner |
| 10 | Privacy Policy Generator | ✅ Live | Free → feeder templates + scanner |
| 11 | Terms of Service Generator | ✅ Live | Free → feeder templates + scanner |

## Blokering (uændret — Mads' konti)

**Eneste flaskehals for revenue.** Gumroad (~10 min), Chrome Web Store ($5), npm-konto. Så snart Gumroad findes: skift checkout-links i /pro/ og /store/, deploy, første salg samme dag.

## Klart til Mads (venter på ja)
- ✅ Gumroad-produkter prissat, tekster klar
- ✅ Sociale opslag skrevet og klar til afsendelse

## Budget
0 kr brugt / 1.000 kr.

## Næste iteration
- SEO-blogindlæg: "Terms of Service template" / "Do I need terms of service" → link til generatoren
- Flere SEO-indgange ("GDPR compliance checker", "refund policy generator")
- Interne links fra øvrige blogindlæg → ToS-generatoren
