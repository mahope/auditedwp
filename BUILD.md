# BUILD — ComplianceDocs (digital-produkt-butik)

Produkt: færdige EU-compliance-dokument-skabeloner solgt som downloads.
Se DECISION.md (iter. 32, pivot) for fuld begrundelse.

## ✅ Færdigt og bygget

| Hvad | Status | Sted |
|------|--------|------|
| Butiksside med 5 produkter + bundle | ✅ Bygget, valideret | `site/store/index.html` |
| Produkterne selv (leverancefilerne) | ✅ Bygget | `site/deliverables/` — DPA, NDA-clause-set, change-log-spec, monthly report, quarterly narrative |
| NIS2 vendor-clause (produkt + SEO-side) | ✅ Live | https://mahope.github.io/auditedwp/template/ |
| Sample audit trail (social proof) | ✅ Live | https://mahope.github.io/auditedwp/sample/ |
| Gammel AuditedWP landing (EN/DE) | Fortsætter som trafikkilde | https://mahope.github.io/auditedwp/ |

Butikssiden er endnu ikke deployet til Pages — sker ved næste push af `site/`.

## Nul-indsats-arkitektur (hvordan det passer på sig selv)

1. Statisk side → ingen server der kan gå ned.
2. Checkout via merchant-of-record (Lemon Squeezy/Paddle/Gumroad) → de håndterer
   kortbetaling, moms, kvitteringer OG refusioner. Ingen support-samtaler.
3. Fil-levering sker automatisk fra platformen efter betaling.
4. Fejlsituationer: side nede = statisk hosting (ubetydelig risiko); checkout
   nede = knappen virker ikke, intet tabes; refusion = platformens self-service.

## ⏳ Mangler (én engangsopgave kræver Mads)

1. **Store-konto** (Lemon Squeezy anbefalet; Gumroad fallback): skal oprettes
   under Mads' navn/bank. ÉN gang. Herefter: indsæt produkt-links i
   `site/store/index.html` (markeret med `.buy`-knapper) — klar.
2. Domæne complidocs.com (~70 DKK, forhåndsgodkendt) — kosmetisk, ikke blokerende.
3. Flere dokumenter (EAA-statement, AI Act-disclosure) — valgfri vækst, kan
   bygges løbende uden deadlinetryk.

## Priser

$29 (NDA) · $39 (EAA) · $49 (NIS2/DORA clauses) · $59 (DPA) · $69 (report kit)
· Bundle $149.
