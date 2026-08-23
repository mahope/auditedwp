# DECISION

**Dato:** 2026-08-23 (iteration 33)
**Status:** Besluttet. Byggefase.

## Hvad

**ComplianceDocs** — B2B EU-compliance-dokument-skabeloner som digitale downloads, solgt via Gumroad (Merchant of Record). Ingen menneskelig indgriben efter opsætning.

## Tre-måneders-testen — HVORFOR denne idé

Mads rejser væk i 3 måneder uden internet. Hvad sker der?

1. Gumroad hoster produkterne, håndterer checkout, betaling, global moms/VAT/skat
2. Filer leveres automatisk til køber efter betaling
3. Pengene akkumuleres på Gumroad-kontoen
4. Nul supportbehov (dokumenter er self-contained)
5. Gumroad Discover sender organisk trafik
6. Egen side på Cloudflare Pages (gratis) kører og tiltrækker SEO-trafik

**Resultat:** Mads kommer hjem til penge på kontoen. Nul arbejde imens.

## Indtjeningsmodel

| Produkt | Pris |
|---|---|
| GDPR Data Processing Agreement (Art. 28) | $59 |
| NIS2/DORA Vendor Clause Set | $49 |
| Mutual NDA Clause Set | $29 |
| EAA Accessibility Statement Template | $39 |
| Client Compliance Report Kit | $69 |
| **Complete Bundle** (alle 5) | **$149** |

Gumroad tager 10% + $0,50 pr. salg. Jeg beholder ~$52,50 på et $59-salg.

**Realistisk scenarie:** 8-15 salg/måned efter 3-6 måneders SEO-modning = $400-1.200/md brutto.

## Hvem køber

- **Freelance-konsulenter** der har brug for en DPA til deres SaaS-kunde I MORGEN
- **Små webbureauer** (3-15 ansatte) der mangler NIS2-klausuler til deres driftskontrakter
- **SaaS-founders** der ikke har et juridisk budget og googler "DPA template GDPR"
- **Selvstændige** der skal have en EAA-accessibility-statement på deres site før deadline

Alle søger på Google/Gumroad efter præcis det her. Produkterne er self-explanatory.

## Hvorfor Gumroad (og ikke Lemon Squeezy/eget site)

| Faktor | Gumroad (valgt) | Lemon Squeezy | Eget site (Stripe) |
|---|---|---|---|
| Opsætning | Minutter | Timer | Dage+ |
| Discovery | ✅ Discover-marketplace giver organisk trafik | ❌ Ingen marketplace | ❌ Skal selv drive trafik |
| MoR | ✅ Global tax/VAT | ✅ Global tax/VAT | ❌ Skal selv |
| Fee | 10% + $0,50 | 5% + $0,50 | 2.9% + $0,30 |
| Payout | Ugentligt | Net 30 | Dagligt |

Gumroad vinder på **Discovery** — det er den eneste af de tre der kan sende betalende kunder uden at jeg gør noget. Det er afgørende for tre-måneders-testen.

## Status på byggeri — ALLEREDE FÆRDIGT

### Eksisterende deliverables (kan sælges I DAG)

| Produkt | Fil | Status |
|---|---|---|
| DPA Template | `site/deliverables/dpa-template.md` | ✅ Skrevet, 369 ord |
| NDA Clause Set | `site/deliverables/nda-clause-set.md` | ✅ Skrevet, 190 ord |
| Client Report Kit | `site/deliverables/monthly-report-template.md` + `quarterly-narrative-template.md` + `change-log-spec.md` | ✅ Alle skrevet |
| NIS2/DORA Clause Set | `site/template/index.html` (lead magnet) | ✅ Skal ekstraheres til .md |
| EAA Statement | Skal skrives | ❌ Mangler |

### Store page
- `site/store/index.html` — komplet butiksside med alle 5 produkter + bundle — ✅ bygget

### Hvad skal bygges NU
1. **EAA Accessibility Statement Template** — skrive dokumentet (~300 ord)
2. **NIS2 ekstraktion** — konvertere HTML lead magnet til salgsklar .md
3. **Poler eksisterende deliverables** — gøre dem klar til betalende kunder (PDF-output, frontmatter)
4. **Oprette Gumroad-konto** — MADS SKAL GODKENDE (konto i hans navn)

## Hvad kan slå den ihjel

1. **Mads siger nej til Gumroad-konto** — uden konto, ingen checkout. Død.
2. **Gumroad afviser account** — usandsynligt (selvstændige sælger uden firma), men muligt.
3. **Ingen trafik** — realistisk risiko. Gumroad Discover er ikke garanteret. SEO tager 3-6 måneder.
4. **Konkurrence fra gratis skabeloner** — GDPR.eu og DocuSign tilbyder gratis DPA-skabeloner. Modgift: mine er mere specifikke (agency-fokus, NIS2, EAA) og med kommentarer/vejledning.
5. **Trust på ny butik** — ingen reviews, ingen sociale beviser. Modgift: pengene-tilbage-garanti, sample-preview.

## Hvorfor denne frem for alternativerne

| Idé | Bedømmelse |
|---|---|
| WP security scan | Overfyldt marked ($9.99-499), byggetid uger, support-behov |
| Compliance API | Småt ubevist marked, uger at bygge data |
| Notion templates | $9-29 pris, mere konkurrence, skal bygges fra bunden |
| **ComplianceDocs** | ✅ Allerede bygget, 0 kr, 0 drift, passer testen |

## Domæne

ComplianceDocs. Forslag:
1. **compliancedocs.gumroad.com** — Gumroad subdomain (gratis, instant)
2. **compliancedocs.com** — ~$10/år via Cloudflare (forhåndsgodkendt)
3. **compliance.templates** — hvis ledigt

Indtil videre: Gumroad URL er nok. Ekstra domæne kan købes senere.

## Præcis hvad der sker uden menneskelig indgriben (3-måneders-testen)

1. Kunde finder ComplianceDocs via Gumroad Discover, Google-søgning, eller direkte link
2. Kunde klikker "Buy" → Gumroad checkout
3. Gumroad håndterer betaling, global moms/VAT, fraud detection
4. Efter betaling: Gumroad sender download-link automatisk
5. Kunde downloader .md/.pdf-fil(er), udfylder med egne detaljer
6. Kunde kan kontakte Gumroad support (ikke mig) med tekniske spørgsmål
7. Penge akkumuleres på Gumroad-kontoen
8. Mads logger ind ved hjemkomst → overfører til bank

**Alt dette kører uden at nogen rører noget som helst.**