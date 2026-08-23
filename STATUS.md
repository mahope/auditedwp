# STATUS — Iteration 85 (2026-08-27): IAB TCF check + blog post

**Dato:** 2026-08-27
**Status:** Beslutningen HOLDER. Universalitet RE-VERIFICERET (bestået). Ny IAB TCF check.

## 1. Universalitets-vurdering (punkt 1)

**BESTÅET.** 350 linjers kerne i `shared/scan-engine.js` tager en vilkårlig URL — nul CMS-forudsætninger. De 2 `wp-`-referencer er udelukkende **detektion** (genkender WP Consent API blandt 20+ CMP'er og WordPress blandt 20+ CMS'er). Fem indpakninger: Worker, WordPress-plugin, CLI, Chrome-extension, web-UI. Live-bevis på wordpress.org, shopify.com, squarespace.com, wix.com, cnn.com.

## 2. Bygget i denne iteration

| # | Opgave | Status |
|---|--------|--------|
| 1 | **IAB TCF check** i scannermotoren | ✅ 5 signaturer: __tcfapi, IABTCF cookies, gdprApplies, TC string, TCF version. Uafhængigt af platform (detekterer i HTML/JS). |
| 2 | **Worker deployeret** v2 med 8 checks | ✅ `eucomply-scan` v2 live — 8 checks, inkl. TCF på position 0a |
| 3 | **Forside opdateret** | ✅ "Six" → "Eight compliance checks, one URL", nyt IAB TCF card i grid3 |
| 4 | **Scan-side opdateret** | ✅ "Seven" → "Eight", nyt IAB TCF feat-card, 8 checks total |
| 5 | **Blog post: IAB TCF guide** | ✅ Ny guide: hvad TCF er, hvem har brug for det, tabel vs Consent Mode v2, check-liste, CTA til free scanner |
| 6 | **Blog index opdateret** | ✅ IAB TCF guide som nyeste post |
| 7 | **Sitemap opdateret** | ✅ Ny URL: /blog/iab-tcf-compliance-guide/, lastmod 2026-08-27 |
| 8 | **Deployeret og verificeret** | ✅ Alle sider 200, API virker, TCF check leverer korrekte resultater |

## 3. Købsrejsen nu

/scan/ → 8 checks (CMv2 + IAB TCF + 6 andre) + egen score → personlig Pro-CTA → /pro/ (pris på 5 sek.) → Buy → Gumroad (venter på Mads).

## 4. Blokering (uændret)

**Eneste blokering:** Mads' Gumroad-konto. GUMROAD_PRODUCT_URL i site/pro/index.html venter på link. Første betaling mulig **samme dag** linket indsættes.

## 5. Venter på Mads' ja

Gumroad-konto · betalte annoncer (klar) · kold mail-række til agencies (klar) · ProductHunt · LinkedIn/Reddit-opslag

## 6. Budget

0 kr brugt / 1.000 kr

## 7. Næste iteration

Prioriteret:
1. Flere blog-opslag (målret "iab tcf framework", "transparency consent framework check")
2. Flere nyttige scanner-checks (GDPR repræsentant detection, consent banner text quality)
3. Forbedr Pro-siden (klar til Gumroad-link)