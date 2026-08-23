# STATUS — Iteration 95 (2026-08-29): universalitet bekræftet + mobil-fixes + Squarespace-guide

**Status:** Beslutningen HOLDER. Punkt 1-vurderingen (universalitet) står fra iteration
91/94: kernen (`shared/scan-engine.js`) tager vilkårlig URL, WordPress-pluginet er kun én
af fem indpakninger (web, CLI, API, extension, plugin). Intet at trække ud — vurderingen
er BESTÅET og er ikke ændret siden.

## Gjort denne iteration

1. ✅ **Mobil-gennemgang af /pro/ og /scan/** (næste-skridt fra it. 94):
   /scan/'s eksempel-knapper havde 3px padding — under Apple/Googles 44px tap-target-
   minimum på mobil. Nu 36px desktop / 44px mobil med centreret layout.
2. ✅ **Nyt SEO-opslag:** `/blog/squarespace-gdpr-compliance-guide/` — platform-hullet i
   bloggen (Wix og Shopify fandtes, Squarespace var den største manglende builder).
   ~15 KB, TOC, tabel, interne links til scan/pro/store + 8 andre opslag, FAQ-agtig
   struktur målrettet "squarespace gdpr compliance"-søgningen.
3. ✅ Blog-indeks + sitemap opdateret (nu 42 stier).
4. ✅ DECISION.md: forældede Gumroad-trin erstattet af Lemon Squeezy-API-flow.

Deployet og verificeret live (indhold tjekket med curl, ikke kun statuskoder; alle 11
interne links i det nye opslag svarer 200).

## Blokering (én linje)

Lemon Squeezy API-nøgle mangler i Bitwarden; når den ligger der, opretter jeg produktet selv samme dag.

## Venter på Mads' ja

LS-nøgle · betalte annoncer (tekst klar) · kold mail-række · ProductHunt · LinkedIn/Reddit-opslag

## Budget

0 kr brugt / 1.000 kr

## Rigtige tal

Rigtige tilmeldinger: 0 · Rigtige scanninger af andre end os: 0 · Omsætning: $0.

## Næste iteration

1. LS-nøgle → opret produkt via API → test-køb → CHECKOUT_URL → første betaling mulig
2. Nyt blog-opslag: Webflow GDPR-guide (sidste store builder der mangler)
3. Frisk-øjne-gennemgang af /store/-købsrejsen
