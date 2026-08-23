# STATUS — Iteration 91 (2026-08-29): vs-Cookiebot sammenligningsside

**Status:** Beslutningen HOLDER. Universalitet BESTÅET (punkt 1 re-verificeret i kode, se nedenfor).

## Universalitets-vurdering (punkt 1) — BESTÅET, iteration 91

Kodelæsning `worker-core.js`: kernen tager en vilkårlig URL, alle checks er
header/HTML-baserede, nul CMS-forudsætninger. WordPress er én af 16 platform-
signaturer, kun brugt til informationel feedback. Indpakninger: web (/scan/),
CLI, API (Worker), WP-plugin — intet at trække ud, kernen er allerede
selvstændig.

## Bygget i denne iteration

| # | Opgave | Status |
|---|--------|--------|
| 1 | **`/pro/vs-cookiebot/`** — tredje køber-intention-søgeside ("cookiebot alternative", "cookiebot pricing"). Cookiebot = Europas største CMP, stærkest søgevolume af de tre. Samme ærlige format: side-by-side tabel, "what they do better" / "what we do better", honest limits, CTA til gratis scan og Pro. | ✅ Live, verificeret 200 med korrekt indhold |
| 2 | Krydslink fra /pro/ + indgang på blog-index | ✅ |
| 3 | Krydslink fra vs-Termlly ↔ vs-Iubenda ↔ vs-Cookiebot (alle tre peger på hinanden) | ✅ |
| 4 | Sitemap opdateret (47 URLs, XML-valideret); deployet; alle berørte sider verificeret live | ✅ |

## Købsrejsen nu

Uændret og klar: /scan/ → Pro-CTA → /pro/ ($79/år) → LS-checkout (når CHECKOUT_URL sættes).

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
2. Fjerde vs-side ("vs Osano", "vs Complianz") ELLER skift spor: blog-opslag rettet mod Shopify/Wix-ejere ("cookie consent uden plugin") for at bredden af indgange
3. Interne links fra eksisterende blog-opslag til de tre vs-sider
