# STATUS — Iteration 86 (2026-08-28): Tracker-check + GA/GDPR-guide

**Dato:** 2026-08-28
**Status:** Beslutningen HOLDER. Universalitet BESTÅET (re-verificeret).

## 1. Universalitets-vurdering (punkt 1)

**BESTÅET.** Kernen `shared/scan-engine.js` tager en vilkårlig URL — nul CMS-forudsætninger. De få `wp-`-referencer er udelukkende detektion (genkender WP blandt 20+ platforme). Nye checks bygges også platformsneutralt: tracker-checken kører på ren HTML/JS-signaturgenkendelse.

## 2. Bygget i denne iteration

| # | Opgave | Status |
|---|--------|--------|
| 1 | **Ny check: Trackers uden consent** i motoren | ✅ 12 signaturer (GA/GTM, Meta Pixel, TikTok, Hotjar, Clarity, LinkedIn, Snap, Pinterest, DoubleClick m.fl.). Fail hvis trackere findes uden CMP — den klassiske GDPR-fælde. |
| 2 | **Worker deployet** — nu 9 checks | ✅ Live på eucomply-scan.workers.dev, testet på cnn.com (finder korrekt DoubleClick) |
| 3 | **Forside** "Nine compliance checks" + nyt kort (DORA-kort-mangel på forsiden rettet indirekte via scan-siden) | ✅ |
| 4 | **Scan-side** opdateret til 9 checks med nyt feat-kort | ✅ |
| 5 | **Blog: Google Analytics & GDPR-guide** (~900 ord) — søgeord omkring "google analytics gdpr", consent-first-reglen, bødetabel, fix-trin, FAQ, CTA til scanner | ✅ |
| 6 | Blog-index + sitemap (43 URLs) | ✅ |
| 7 | Deployet og verificeret | ✅ Alle sider 200, nyt indhold bekræftet |

## 3. Købsrejsen nu

/scan/ → **9 checks** → personlig Pro-CTA → /pro/ ($79/år) → Buy → Lemon Squeezy (venter på API-nøgle).

## 4. Blokering (én linje)

Lemon Squeezy API-nøgle mangler i Bitwarden; GUMROAD_PRODUCT_URL i site/pro/index.html venter på link — første betaling mulig samme dag linket indsættes.

## 5. Venter på Mads' ja

Lemon Squeezy-nøgle · betalte annoncer (klar) · kold mail-række til agencies (klar) · ProductHunt · LinkedIn/Reddit-opslag

## 6. Budget

0 kr brugt / 1.000 kr

## 7. Rigtige tal

Rigtige tilmeldinger: 0 · Rigtige scanninger af andre end os: ikke målt adskilt — rapporteres kun som 0 indtil verificeret.

## 8. Næste iteration

1. Forbedr /pro/ salgsside mod Lemon Squeezy-link
2. Blog-opslag målrettet "meta pixel gdpr" / "facebook pixel consent"
3. Consent banner text quality-check (banner findes, men "notify only"-konfiguration)
