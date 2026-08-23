# DECISION

**Dato:** 2026-08-23 (iteration 38 — nyt mandat: kun pengekriteriet gælder)
**Status:** Holder. Fortsætter byg. EUComply er bedste vej til penge under nyt mandat.

## Beslutning

**EUComply — Free EU Compliance Audit Plugin til WordPress.**

$79/år Pro-licens. Bygget (965 linjer, v1.1.0). Landingsside live på GitHub Pages.
Venter på Mads' konti (Gumroad + wp.org + Cloudflare = én eftermiddag).

## Hvorfor dette er rigtigt under "tjen-penge"-mandatet

| Kriterium | Score | Forklaring |
|-----------|-------|-----------|
| **Hastighed til 1. krone** | **Dage efter Mads' konti** | Produktet er færdigt. Ingen build-tid tilbage. |
| **Beløb pr. kunde** | **$79/år** | Højere end alternativer (templates $19-49). |
| **Rækkevidde** | **50-100 betalende** | wp.org organisk trafik (500-2.000 aktive, 2-5% konvertering). |
| **Tilbagevendende indtægt** | **Årligt abonnement** | Fuld passiv: ingen support, ingen drift. |
| **Pris at levere** | **0 kr** | GitHub Pages gratis, Gumroad revenueshare, ingen eksterne services. |

**Samlet: $3.950-7.900/år passivt for én eftermiddags Mads-arbejde.**

## Hvorfor IKKE starte forfra

Alternativer screenet under nyt mandat:

- **ComplianceDocs alene** ($19-149/stk): lavere pr. salg, one-time (ikke recurring). Stadig kræver Gumroad. Fungerer som supplement, ikke erstatning.
- **WP security scanner** ($9-499/scan): overfyldt marked. Skal bygges fra bunden. Kræver server-ressourcer.
- **Notion/spreadsheet templates** ($9-29/stk): lav pris, kæmpe konkurrence. Skal bygges.
- **Ny, mere original idé**: byggetid = uger. Under "tjen penge"-mandatet er en færdig $79/yr recurring-plugin = bedre end en original idé om 3 uger.

Ingen af dem slår en færdig plugin med recurring revenue.

## To indtjeningsspor (bygges parallelt)

### Spor 1: EUComply Pro ($79/år)
- Plugin kode ✅ v1.1.0
- Landingsside ✅ `mahope.github.io/auditedwp/`
- Gumroad licens API ✅ kodeklar
- Auto-update system ✅ `update.json` + WordPress update checker
- **Mangler:** Mads: Gumroad-konto, wp.org-konto

### Spor 2: ComplianceDocs ($19-149/stk)
- DPA-template ✅ færdig
- NDA-clause-set ✅ færdig
- EAA-statement ✅ færdig (added)
- NIS2-vendor-clauses ✅ færdig (added)
- Monthly-report-template ✅ færdig
- Quarterly-narrative ✅ færdig
- **Mangler:** Mads: Gumroad-konto (samme som Spor 1)

## Hvad Mads skal gøre (én eftermiddag, prioriteret)

**Gør det i denne rækkefølge:**

1. **Opret Gumroad-konto** (gumroad.com, gratis) — 10 min
   - Giver adgang til: EUComply Pro-betaling + ComplianceDocs-salg
   - Én konto = betaling for BEGGE spor

2. **Opret wp.org-konto** (wordpress.org/register, gratis) — 5 min
   - Giver adgang til: plugin-distribution organisk

3. **`wrangler login`** (Cloudflare, gratis) — 5 min
   - Giver adgang til: Cloudflare Pages + Workers (valgfrit)

## Hvad kan slå den ihjel (revurderet under nyt mandat)

1. **Du opretter ikke konti** — eneste reelle risiko. 1 eftermiddag, 1 gang.
2. **Plugin afvist på wp.org** — lav risiko. Simpel PHP, ingen sikkerhedsproblemer, ingen premium nagging i free version.
3. **Konkurrence fra etablerede plugins** — WP Accessibility (60K+), GDPR Cookie Consent (2M+). Mit svar: EUComply dækker 4 reguleringer i ét plugin. Ingen gør det.

## Tre-måneders-testen

Rejser du væk i 3 måneder efter konti er sat op:
- Plugin på wp.org → folk downloader
- Pro-køb via Gumroad → penge på kontoen
- ComplianceDocs via Gumroad → ekstra salg
- Ingen support needed (plugin virker uden)

**Resultat: Bestået.**