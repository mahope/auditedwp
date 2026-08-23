# STATUS — Iteration 88 (2026-08-29): Købsrejse + trafik-arbejde (ikke blokeret)

**Dato:** 2026-08-29
**Status:** Beslutningen HOLDER under pengekriteriet. Universalitet BESTÅET (vurderet igen).

## Universalitets-vurdering (punkt 1) — BESTÅET igen

Kernen tager en vilkårlig URL, nul CMS-forudsætninger. `wp-`-referencer er kun
detektion blandt 20+ platforme. Fire indpakninger om samme kerne: web (/scan/),
CLI, API (Worker), WP-plugin — pluginet er én indpakning, ikke produktet.
Intet at trække ud, intet at bygge om.

## Bygget i denne iteration

| # | Opgave | Status |
|---|--------|--------|
| 1 | Gennemgået /scan/ som fremmed: fix-vejen fra fejl til Pro ER tydelig (personlig CTA med brugerens eget antal fejl + "keep them fixed"-vinkel). Ingen ændring nødvendig. | ✅ |
| 2 | Ret ødelagt LS-overlay-aktiveringslinje i /pro/ (`assets.Lemon Squeezy.com` → korrekt `assets.lemonsqueezy.com/js/lemon.js`) | ✅ |
| 3 | Nyt blog-opslag: **Meta Pixel & GDPR** (`/blog/meta-pixel-gdpr-consent/`) — højt kommercielt søgeord, direkte CTA til scanner og Pro | ✅ |
| 4 | Blog-index + sitemap opdateret; deployet; alle berørte sider verificeret 200 live | ✅ |
| 5 | Fuld link-tjek: alle 19 blog-URL'er + hele sitemap = 200 | ✅ |

## Købsrejsen nu

/scan/ → 9 checks → personlig Pro-CTA → /pro/ ($79/år) → Buy → LS-checkout
(når CHECKOUT_URL sættes). Alt klar undtagen én ting: Lemon Squeezy-nøglen.

## Blokering (én linje)

Lemon Squeezy API-nøgle mangler i Bitwarden (ventes 24/8); når den ligger der, opretter jeg produktet selv samme dag.

## Venter på Mads' ja

LS-nøgle · betalte annoncer (tekst klar) · kold mail-række til agencies (klar) · ProductHunt · LinkedIn/Reddit-opslag

## Budget

0 kr brugt / 1.000 kr

## Rigtige tal

Rigtige tilmeldinger: 0 · Rigtige scanninger af andre end os: 0.

## Næste iteration

1. LS-nøgle → opret produkt via API → test-køb → indsæt CHECKOUT_URL → første betaling mulig
2. Blog-opslag #3: "Shopify/Wix cookie consent" eller "HSTS preload" — vælg efter søgevolumen
3. Overvej en sammenligningsside mod et konkret konkurrent-navn (søgbar køber-intention)
