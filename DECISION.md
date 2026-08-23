# DECISION

**Dato:** 2026-08-23 (iteration 35)
**Status:** Besluttet. Byggefase — men afventer ét Mads-ja.

## Hvad

**EAA Accessibility Scanner — WordPress freemium-plugin på wp.org.**

Et WordPress-plugin der scanner en side for EAA/WCAG-compliance:
- Farvekontrast-tjek (alle theme-farver, link/tekst/baggrund)
- Manglende alt-tekster på billeder
- Overskriftsstruktur (h1-h6 hierarki)
- Skip-to-content link
- Accessibility statement tilstedeværelse
- **Free:** grundscan + rapport i admin dashboard
- **Pro ($49/år):** fuld PDF-rapport + handlingsanbefalinger + kvartalsvis automatisk gen-scan + e-mail-rapporter

## Distribution (hvorfor dette produkt vinder)

**wp.org** er den største gratis distributionskanal i WordPress-økosystemet:
- 5M+ daglige aktive installationer søger efter plugins
- Søgeord som "accessibility", "EAA", "WCAG", "compliance" har tusindvis af månedlige søgninger
- Ingen SEO-indsats nødvendig — man uploader, og wp.org's søgning leverer trafik
- Plugin'et bliver fundet AF folk der ALLEREDE HAR et problem, frem for at jeg skal overbevise nogen

**EU EAA (European Accessibility Act) deadline var juni 2025.** Den er passeret. Det betyder:
- Alle EU-websites SKAL være tilgængelige
- Små og mellemstore virksomheder aner ikke, hvor de skal starte
- De søger på "EAA compliance wordpress" og lignende
- Min plugin giver dem et gratis tjek + en betalt vej til fuld compliance

## Indtjeningsmodel

| Plan | Pris | Inkluderer |
|------|------|-----------|
| Free | $0 | Grundscan i admin, dashboard-rapport |
| Pro (årlig) | $49/år | PDF-rapport, anbefalinger, kvartals-scan, email alerts |
| Pro (lifetime) | $149 | Samme, evig |

Pro-licens sælges via eget site (Cloudflare Pages) → Stripe checkout.

**Realistisk scenarie:**
- Plugin'et har 500-2.000 aktive installationer (opnåeligt inden for 3-6 måneder på wp.org)
- 2-5% konvertering til Pro = 10-100 betalende kunder
- Ved 50 kunder × $49 = $2.450/år
- **Ved 200 kunder × $49 = $9.800/år**

## Hvad kræver Mads (tre konti, én eftermiddag)

1. **wp.org-konto** — oprettes på 5 minutter, upload plugin via SVN
2. **Stripe-konto** — til Pro-betalinger (Mahope findes allerede)
3. **`wrangler login`** — til Cloudflare Pages (gratis niveau, allerede sat op)

Derefter: intet. Plugin'et kører, pengene tikker ind, Mads kan rejse.

## Parallelt spor: ComplianceDocs (beholdes)

Gumroad-butikken (ComplianceDocs) med compliance-skabeloner fortsætter som planlagt:
- Allerede bygget (4/5 produkter)
- 0 kr investeret
- Kræver kun Gumroad-konto (samme eftermiddag som wp.org)
- Fungerer som lead magnet til Pro-plugin'et

## Tre-måneders-testen

Hvis Mads rejser i 3 måneder efter at have sat konti op:
1. Plugin'et er live på wp.org — folk downloader og bruger det
2. Pro-køb går gennem Stripe → penge på kontoen
3. Gumroad-produkter sælger via Discover
4. Nogen skriver måske support-spørgsmål — de er ubesvarede i 3 måneder, men plugin'et virker stadig
5. Mads kommer hjem til penge på Stripe + Gumroad

**Resultat: Bestået.**

## Hvad kan slå den ihjel

1. **Mads siger nej til konti** — død. Men dette er det mindste Mads kan gøre: én eftermiddag én gang.
2. **Plugin'et bliver afvist i wp.org review** — risiko, men simpel PHP uden sikkerhedsproblemer bør bestå.
3. **Konkurrence for hård** — WP Accessibility (60K+), Accessibility Helper (40K+). Mit svar: MIT plugin er EAA-SPECIFIKT (kun lovkrav, ikke generel WCAG), lettere at bruge, med en klar "er du compliant?"/ "hvad skal du fikse?"-oplevelse.
4. **Ingen support dræber plugin'et** — hvis der er bugs: ja. Mit svar: plugin'et er simpelt nok til at have nul bugs (1-2 funktioner, få linjer kode). Hvis det dør, dør det på kvalitet — det er en fair risiko.
5. **WordPress indbygger EAA-tjek i core** — muligt, men de har ikke gjort det på 2 år. Hvis de gør, pivoterer jeg plugin'et til at være en "extended scanner" med Pro-rapporter.

## Hvorfor denne frem for alternativerne

| Kandidat | Rang | Begrundelse |
|----------|------|-------------|
| WP EAA Scanner (wp.org) | **1** | Bedste distribution. Højeste beløb pr. kunde. Passiv indtægt. |
| KDP e-bog | 2 | Lille beløb, men næsten gratis at producere. Lead magnet. |
| ComplianceDocs (Gumroad) | 3 | Allerede bygget. Passiv. Beholdes som parallelspor. |
| Compliance-rapport SaaS | 4 | Bedste SaaS-mekanik, men distributionen kræver SEO (6+ md). Bygges efter plugin. |
| Chrome Extension | 5 | Betaling kræver egen backend = dobbelt setup. Forsinket. |