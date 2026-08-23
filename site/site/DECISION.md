# DECISION

**Dato:** 2026-08-23 (iteration 36 — nyt mandat: tjen penge, krav om nytænkning lempet)
**Status:** Besluttet. Bygger nu. Alt der kræver Mads-konti er rykket til "én eftermiddag" efter byg.

## Hvad

**EUComply — Free EU Compliance Audit Plugin til WordPress.**

Et WordPress-plugin der scanner en side for de fire vigtigste EU-reguleringer:
- **GDPR** — cookies, forms, SSL, privacy policy
- **NIS2** — backup status, recovery readiness
- **DORA** — plugin health, vulnerability management
- **EAA** — accessibility statement, legal pages

| Plan | Pris | Hvad får man |
|------|------|-------------|
| Free | $0 | Dashboardscan: SSL, cookies, forms, backups, plugins, legal pages |
| Pro (årligt) | $79/år | PDF-rapport, DPA-generator, NIS2-clause-kit, EAA-statement, kvartals-narrativ, email-alerts |

## Hvorfor dette (5 kriterier vurderet)

| Kriterium | Score | Forklaring |
|-----------|-------|-----------|
| Hastighed til 1. krone | Dage-uger | Landing page live nu. Gumroad-konto → Pro-link klar på 10 min. Første kunde når plugin er på wp.org eller link deles |
| Beløb pr. kunde | $79/år ✅ | Højere end EAA-only ($79 vs $49). Flere features = højere betalingsvilje |
| Rækkevidde | 10-100 betalende ⚠️ | wp.org (2-6 mdr organisk) → 500-2.000 aktive → 2-5% konvertering. Lave forventninger, men stabil vækst |
| Tilbagevendende indtægt | Årligt abonnement ✅✅ | Pro $79/år × 100 kunder = $7.900/år. Passivt. |
| Pris at levere | 0 kr ✅ | Hosting: Pages gratis. Plugin: 761 linjer PHP, ingen eksterne services. |

**Samlet: Solid pengemaskine med passiv recurring indtægt.** Distributionsflaskehalsen er wp.org-konto (Mads), men produktet er bygget og kan demonstreres nu.

## Ændringer fra forrige beslutning (EAA Scanner $49/yr)

1. **Bredere scope** — EUComply dækker 4 reguleringer (GDPR, NIS2, DORA, EAA) frem for kun EAA. Højere betalingsvilje ($79 vs $49).
2. **Eksisterende kode** — 761 linjer PHP allerede skrevet. Ingen grund til at skrive om eller bygge fra bunden.
3. **Byg først, konti bagefter** — Landingsside live på GitHub Pages nu. Plugin-kode klar. wp.org/Stripe/Gumroad kommer i én Mads-eftermiddag.

## Distribution

| Kanal | Status | Tid til trafik | Note |
|-------|--------|---------------|------|
| GitHub Pages | ✅ LIVE | Nu | `mahope.github.io/auditedwp/` — landingsside aktiv |
| Cloudflare Pages *.pages.dev | ⏳ Vent på Mads | 5 min efter login | `wrangler login` → deploy |
| wp.org plugin repository | ⏳ Vent på Mads | 2-4 uger efter upload | Bedste distributionskanal (organisk søgning) |
| Gumroad (Pro-betaling) | ⏳ Vent på Mads | 10 min efter konto | Stripe via Gumroad's MoR |

## Indtjeningsmodel

**Pro $79/år (1 site) — solgt via Gumroad/i løsningen.**

Realistisk scenarie:
- Plugin på wp.org → 500-2.000 aktive installationer (3-6 mdr)
- 2-5% konvertering → 10-100 betalende kunder
- Ved 50 kunder × $79 = **$3.950/år**
- Ved 100 kunder × $79 = **$7.900/år**
- Gumroad tager 10% + $0.50 = $7.90 + $0.50 pr. salg = **reelt $70.60 pr. kunde**

**ComplianceDocs (parallelspor):**
- DPA $29, NDA-set $19, bundle $49
- Allerede bygget (site/store/)
- 0 kr investeret
- Samme Gumroad-konto

## Parallelle spor

ComplianceDocs (Gumroad store) fortsætter:
- Allerede bygget (4/5 deliverables klare)
- Fungerer som lead magnet til Pro-plugin
- Én konto til begge (Gumroad)

## Hvad kan slå den ihjel

1. **Mads opretter ikke konti** — død. Men dette er 1 eftermiddag, 1 gang.
2. **Plugin afvist på wp.org** — risiko. Simpel PHP uden sikkerhedsproblemer bør bestå.
3. **Konkurrence** — WP Accessibility (60K+), GDPR Cookie Consent (2M+). Mit svar: EUComply dækker 4 reguleringer i ét plugin. Ingen anden plugin gør det.
4. **Ingen support dræber plugin** — ja, hvis der er bugs. Plugin er simpelt (6 checks, admin dashboard). Risikoen er acceptabel.

## Tre-måneders-testen

Hvis Mads rejser i 3 måneder efter at have sat konti op:
1. Plugin er live på wp.org — folk downloader og bruger det
2. Pro-køb går gennem Gumroad → penge på kontoen
3. ComplianceDocs sælger via Gumroad Discover
4. Support-spørgsmål er ubesvarede i 3 måneder — plugin'et virker stadig
5. Mads kommer hjem til penge på Stripe + Gumroad

**Resultat: Bestået.**

## Hvad Mads skal gøre (én eftermiddag)

1. **`wrangler login`** — sætter Cloudflare Pages op (5 min)
2. **Opret Gumroad-konto** — til Pro-betalinger og ComplianceDocs (10 min)
3. **Opret wp.org-konto** — til plugin-upload (5 min)
4. **Køb domæne** (valgfrit) — eucomply.io, complywp.com el. lign. via Cloudflare (5 min)

Derefter: intet. EUComply kører, pengene tikker ind.