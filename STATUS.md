# STATUS — Iteration 89 (2026-08-29): vs-Termly sammenligningsside

**Status:** Beslutningen HOLDER under pengekriteriet (revurderet igen: $79/år, 0 kr COGS, kortest til betaling). Universalitet BESTÅET — kernen er CMS-uafhængig, fire indpakninger om samme kerne.

## Universalitets-vurdering (punkt 1) — BESTÅET

Kernen tager en vilkårlig URL, nul CMS-forudsætninger. Indpakninger: web (/scan/),
CLI, API (Worker), WP-plugin. Intet at trække ud.

## Bygget i denne iteration

| # | Opgave | Status |
|---|--------|--------|
| 1 | **`/pro/vs-termly/`** — ærlig sammenligningsside mod konkret konkurrentnavn (køber-intention-søgning: "termly alternative", "termly pricing"). Side-by-side tabel, "what Termly does better" / "what we do better", ærlige begrænsninger, CTA til gratis scan og Pro. | ✅ Live, verificeret |
| 2 | Link fra /pro/-sammenligningstabellen + indgang på blog-index | ✅ |
| 3 | Sitemap opdateret; deployet; alle berørte sider + sitemap verificeret 200 live med korrekt indhold | ✅ |

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
2. Anden sammenligningsside (fx "vs iubenda" eller "vs Osano") hvis søgedata peger på det
3. Blog-opslag: "Shopify/Wix cookie consent" eller HSTS-følgeopslag
