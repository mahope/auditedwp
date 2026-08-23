# STATUS — Iteration 87 (2026-08-23, aften): Lemon Squeezy-overgang + konsistens

**Dato:** 2026-08-23
**Status:** Beslutningen HOLDER under pengekriteriet. Universalitet BESTÅET.

## 1. Universalitets-vurdering (punkt 1) — BESTÅET

Kernen `shared/scan-engine.js` tager en vilkårlig URL, nul CMS-forudsætninger.
`wp-`-referencer er udelukkende detektion blandt 20+ platforme. WordPress-pluginet
og CLI'en er indpakninger omkring kernen — ikke produktet. Ingen ændring nødvendig;
verificeret igen i denne iteration.

## 2. Bygget i denne iteration

| # | Opgave | Status |
|---|--------|--------|
| 1 | Alle Gumroad-referencer på sitet skiftet til **Lemon Squeezy** (forside, pro, store, terms, privacy, cli) — verificeret via curl efter deploy | ✅ |
| 2 | WordPress-pluginets licensvalidering omkodet fra Gumroad API til **Lemon Squeezy License API** (`/v1/licenses/activate`, instance-håndtering, 404 = ugyldig nøgle) | ✅ |
| 3 | Konsistensrettelser: "6 checks" → "9 checks" på /pro/ og /cli/ (motoren har 9) | ✅ |
| 4 | BUILD.md omskrevet: korteste vej til første betaling via LS API-nøglen i Bitwarden — jeg opretter produktet selv | ✅ |
| 5 | Deployet og indholdsverificeret på alle berørte sider | ✅ |

## 3. Købsrejsen nu

/scan/ → **9 checks** → Pro-CTA → /pro/ ($79/år) → Buy → Lemon Squeezy checkout.
Alt klar undtagen én ting: `CHECKOUT_URL` i site/pro/index.html.

## 4. Blokering (én linje)

Lemon Squeezy API-nøgle mangler i Bitwarden; når den ligger der, opretter jeg produktet selv samme dag.

## 5. Venter på Mads' ja

LS-nøgle · betalte annoncer (tekst klar) · kold mail-række til agencies (klar) · ProductHunt · LinkedIn/Reddit-opslag

## 6. Budget

0 kr brugt / 1.000 kr

## 7. Rigtige tal

Rigtige tilmeldinger: 0 · Rigtige scanninger af andre end os: 0 (ikke verificeret adskilt).

## 8. Næste iteration

1. LS-nøgle → opret produkt via API → test-køb → indsæt CHECKOUT_URL → første betaling mulig
2. Blog-opslag målrettet "meta pixel gdpr" / "facebook pixel consent"
3. Gennemgå /scan/-resultatsiden som fremmed: er fix-vejen fra fejl til Pro tydelig nok?
