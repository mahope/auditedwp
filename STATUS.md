# STATUS — Iteration 92 (2026-08-29): vs-Osano side + DECISION opdateret

**Status:** Beslutningen HOLDER under pengekriteriet (revurderet med pengelinsen — se DECISION.md, nu opdateret fra Gumroad til Lemon Squeezy).

## Universalitet (punkt 1) — BESTÅET (re-verificeret iteration 91)

Kernen (`worker-core.js`) tager en vilkårlig URL, nul CMS-forudsætninger.
Indpakninger: web (/scan/), CLI, API, WP-plugin. Intet at trække ud.

## Bygget i denne iteration

| # | Opgave | Status |
|---|--------|--------|
| 1 | **`/pro/vs-osano/`** — fjerde køber-intention-søgeside. Osano = stor US privacy-platform med CMP; søgevolume på "osano alternative/pricing" er reelt. Samme ærlige format: side-by-side tabel, "what they do better" / "what we do better", honest limits, CTA. | ✅ Live, 200, indhold verificeret |
| 2 | Krydslink fra alle tre andre vs-sider + pro/index + blog-index (post-card) | ✅ Verificeret live |
| 3 | Sitemap: 48 URLs, XML-valideret, deployet | ✅ |
| 4 | **DECISION.md opdateret** — Gumroad-referencer erstattet med Lemon Squeezy; penge-vurderingen bekræftet: 0 kr drift, $79/år/kunde, 25M+ marked, timer til betaling når LS-nøglen ligger klar | ✅ |

## Købsrejsen nu

/scan/ → Pro-CTA → /pro/ ($79/år) → LS-checkout (når CHECKOUT_URL sættes).
Fire vs-sider + blog trækker køber-intention-søgning ind.

## Blokering (én linje)

Lemon Squeezy API-nøgle mangler i Bitwarden; når den ligger der, opretter jeg produktet selv samme dag.

## Venter på Mads' ja

LS-nøgle · betalte annoncer (tekst klar) · kold mail-række til agencies · ProductHunt · LinkedIn/Reddit-opslag

## Budget

0 kr brugt / 1.000 kr

## Rigtige tal

Rigtige tilmeldinger: 0 · Rigtige scanninger af andre end os: 0.

## Næste iteration

1. LS-nøgle → opret produkt via API → test-køb → CHECKOUT_URL → første betaling mulig
2. Interne links fra eksisterende blog-opslag til de fire vs-sider (de linker stadig ikke tilbage)
3. Blog-opslag rettet mod Shopify/Wix-ejere ("cookie consent uden plugin") for bredere indgang
