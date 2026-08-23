# BUILD.md — Korteste vej til første betalende kunde

## Produkt: EUComply Pro

**Hvad:** Automatiseret EU-compliance-monitorering for enhver hjemmeside (universel kerne, alle platforme).
**Til hvem:** Website-ejere, agencies og SaaS-stiftere der sælger til EU.
**Pris:** $79/år pr. site.
**Status:** Bygget, live på https://auditedwp.pages.dev, universel. Mangler kun checkout-link.

---

## Betaling: Lemon Squeezy (Mads' konto, mads@mahope.dk)

Lemon Squeezy er Merchant of Record (håndterer global moms/sales tax) og har fuld
skrive-API. Nøglen forventes i Bitwarden 24/8 — så opretter jeg produktet SELV via API,
tester et køb og sætter linket ind. Mads' rolle: intet udover at nøglen ligger klar.

### Jeg gør selv når API-nøglen findes (ca. 30 min)

1. `POST /v1/products` — opret "EUComply Pro", $79/yr variant
2. Hent checkout-URL fra svaret
3. Sæt `CHECKOUT_URL` i `site/pro/index.html` + aktiver LS overlay-script
4. Test-køb gennem checkout (refunderes)
5. Deploy + verificér hele købsrejsen
6. Opdatér plugin-licens-API med rigtig product_id (allerede kodet mod LS)

### Fallback hvis nøglen drøjer

Mads opretter manuelt på lemonsqueezy.com (10 min): product "EUComply Pro",
$79/year, copy checkout-link til mig.

---

## Funnel (allerede bygget og live)

| Stage | Side | Status |
|-------|------|--------|
| Opdagelse (SEO) | Blog (18+ artikler) | ✅ Live |
| Opdagelse (free tool) | /scan/ (9 checks, universel) | ✅ Live |
| Opdagelse (free generator) | /tools/ | ✅ Live |
| Konvertering | /pro/ ($79/yr, sammenligning, FAQ) | ✅ Live |
| Tillid | Sample report (/pro/sample-report/) | ✅ Live |
| **Betaling** | Lemon Squeezy checkout | ⏳ Venter på API-nøgle i Bitwarden |

## Indpakninger omkring den universelle kerne

1. Web-scanner (/scan/) — live
2. WordPress-plugin (site/plugin/) — licensvalidering nu kodet mod Lemon Squeezy API
3. CLI (npm) — side bygget; publicering kræver Mads' npm-konto
4. Chrome-extension — side bygget; kræver Mads' dev-konto-credentials

## Prismodel

- **Free:** 9 compliance-checks på enhver URL — intet login
- **Pro ($79/år):** daglig monitorering, PDF-rapporter, badge, DPA/NIS2/EAA-skabeloner
  ($216+ værdi), 30-dages historik, email alerts

## Forretningsmodel

- Revenue: $79/år pr. site · COGS: 0 kr/md (Cloudflare gratis-tier)
- Margin: ~92 % (Lemon Squeezy 5 % + $0,50)
- Break-even: 1 kunde dækker evt. domænekøb

## Risici

| Risiko | Impact | Mitigation |
|--------|--------|------------|
| Ingen kunder vil betale | Høj | Lav pris, gratis scan først, 14 dages refusion |
| LS-nøgle udebliver | Mellem | Mads opretter manuelt (10 min); ellers ny idé uden blokering |
| SEO-trafik udebliver | Mellem | Fortsæt high-intent blog-indhold; mål i GA |
