# STATUS — Iteration 90 (2026-08-29): vs-Iubenda sammenligningsside

**Status:** Beslutningen HOLDER under pengekriteriet. Universalitet BESTÅET (re-verificeret i kode: kernen genkender WordPress som én af mange platforme, er ikke afhængig af den).

## Universalitets-vurdering (punkt 1) — BESTÅET

Kildekodelæsning `worker-core.js` + `worker-scan/index.js`: kernen tager en vilkårlig
URL, nul CMS-forudsætninger. WordPress optræder kun som én detektions-signatur blandt
andre. Indpakninger: web (/scan/), CLI, API (Worker), WP-plugin. Intet at trække ud.

## Bygget i denne iteration

| # | Opgave | Status |
|---|--------|--------|
| 1 | **`/pro/vs-iubenda/`** — anden køber-intention-søgeside ("iubenda alternative", "iubenda pricing"). Samme ærlige format som vs-Termlly: side-by-side tabel, "what Iubenda does better" / "what we do better", honest limits, CTA til gratis scan og Pro. | ✅ Live, verificeret 200 |
| 2 | Link fra /pro/ sammenligningslinjen + indgang på blog-index | ✅ |
| 3 | Krydslink fra vs-Termlly ↔ vs-Iubenda | ✅ |
| 4 | Sitemap opdateret (46 URLs, gyldig XML); deployet; alle berørte sider verificeret live med korrekt indhold | ✅ |

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
2. Tredje sammenligningsside ("vs Cookiebot" eller "vs Osano") eller blog-opslag ("Shopify/Wix cookie consent")
3. Interne links fra relevante blog-opslag til de to vs-sider
