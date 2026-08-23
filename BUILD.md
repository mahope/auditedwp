# BUILD.md — Korteste vej til $1

## Produkt: EUComply Pro

**Hvad:** Automatiseret EU-compliance-monitorering for enhver hjemmeside.
**Til hvem:** Website-ejere, agencies og SaaS-stiftere der sælger til EU.
**Pris:** $79/år pr. site.
**Status:** Bygget, live, universel. Alt virker — mangler kun betalingslink.

---

## Korteste vej til første betalende kunde

### Mads: 3 minutter

1. **Gå til https://gumroad.com → "Start selling"**
2. **Opret produkt:**
   - Title: "EUComply Pro — Automated EU Compliance Monitoring"
   - Price: $79/year (recurring)
   - License key: skip (Gumroad håndterer adgang selv)
   - URL slug: `eucomply-pro`
3. **Kopier produkt-URL** → send den til mig (fx https://eucomply.gumroad.com/l/eucomply-pro)
4. **Done — ingen bank info påkrævet** (Gumroad holder pengene indtil payout er sat)

### Jeg: 5 minutter efter link modtaget

1. Indsæt produkt-URL i `site/pro/index.html` — `GUMROAD_PRODUCT_URL`
2. Afkommentér Gumroad Overlay script
3. Afkommentér Gumroad-script i footer
4. Deploy
5. Verificer: Buy-knap → Gumroad checkout → ✅

**Herefter:** Første kunde kan betale SAMME dag.

---

## Funnel før checkout (allerede bygget)

| Stage | Side | Status |
|-------|------|--------|
| Opdagelse (SEO) | Blog (17 articles) | ✅ Live |
| Opdagelse (free tool) | /scan/ | ✅ Live |
| Opdagelse (free generator) | /tools/ | ✅ Live |
| Konvertering | /pro/ (sammenligning, features, FAQ) | ✅ Live |
| Tillid | Sample report (/pro/sample-report/) | ✅ Live |
| Lead capture | Waitlist (0 rigtige signups) | ✅ Live |
| **Betaling** | Gumroad checkout | ⏳ Mangler Mads' link |

---

## Prismodel

- **Free:** 6 compliance-checks på enhver URL — intet login
- **Pro ($79/år):** Daglig monitorering, PDF-rapporter, compliance badge (live score),
  DPA/NIS2/EAA-skabeloner ($216+ værdi), 30-dages historik, email alerts ved score-drop

B2B-pris på $79/år er et "impulse buy" for en website-ejer — lav nok til at
der ikke kræves godkendelse, høj nok til at det er en seriøs forretning.

---

## Distributionskanaler (når Gumroad er oppe)

1. **SEO** — 17 blog-opslag med high-intent keywords (fortsæt)
2. **Chrome Web Store** — kræver $5 engang + Mads' konto
3. **npm CLI** — kræver Mads' npm-konto
4. **WordPress plugin directory** — kræver WP.org review
5. **Direkte links** fra gratis scanner → Pro

---

## Forretningsmodel

- Revenue: $79/år pr. site
- COGS: 0 kr/md (Cloudflare gratis-tier)
- Margin: ~95% (Gumroad tager 10% + $0,50)
- Break-even: 2 kunder ($158) dækker evt. domæne ($10/år)
- Passiv drift: ingen server-management, ingen support-infrastruktur (FAQ + email)

---

## Risici

| Risiko | Impact | Mitigation |
|--------|--------|------------|
| Ingen kunder vil betale | Høj | Waitlist (6) viser interesse; lav pris; refund policy |
| Gumroad lukker konto | Mellem | Flyt til LemonSqueezy — samme model |
| SEO trafik kommer ikke | Lav | 17 artikler allerede; fortsæt produktion |
| Konkurrent kopierer | Lav | Compliance er billigt + universelt; pris $79 vs $100—600 |
| Mads glemmer at sætte Gumroad op | Høj | BUILD.md er eneste dokumentation; ryk for det |