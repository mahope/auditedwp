# STATUS — Iteration 94 (2026-08-29): købsrejse-gennemgang med friske øjne

**Status:** Beslutningen HOLDER. Universalitet re-verificeret i kildekode denne iteration:
kernen (`shared/scan-engine.js`, 415 linjer) tager vilkårlig URL — WordPress/Shopify/Wix osv.
er kun *detektions*-signaturer blandt 19 platforme, ingen afhængighed. Intet at trække ud.
Alle 4 vs-sider, dashboard og sample-report svarer 200 live.

## Ærlig vurdering af punkt 1 (universalitet)

BESTÅET igen, denne gang ved manuel gennemlæsning af `worker-scan/index.js` og
`shared/scan-engine.js`. WP-plugin'et er én indpakning; web, CLI, API, extension
og badge er de andre. Arkitekturen matcher Mads' model præcist.

## Fundet og RETTET i købsrejsen (friske-øjne-gennemgang)

1. ✅ **`/#pricing`-CTAs pegede på forsids-ankeret** fra /tools/, /cli/, /extension/
   og et blog-opslag — sendte køberklare besøgende tilbage til forsiden i stedet for
   den dedikerede salgsside. Alle 5 peger nu på `/pro/`.
2. ✅ **/check-eu-compliance/** (høj-intentions SEO-side): "See Pro" gik til dødt
   `/#pricing`-mønster → nu `/pro/`. Fik desuden links til sample-report + dashboard.
3. ✅ **Alle fire vs-sider** (vs-cookiebot/vs-termly/vs-osano/vs-iubenda) manglede
   "try before you buy"-dokumentation — tilføjet links til sample PDF-report og
   live dashboard under CTA-knapperne.
4. ✅ **Døde e-mail-løfter fjernet:** `hello@auditedwp.com` (adresse der ikke findes)
   var lovet på /template/, /de/ (2 steder) og via "contact form"-henvisning i
   privacy-politikken. /template/ og /de/ peger nu på gratis-scan; privacy teksten er
   ændret til at være korrekt om hvilke data vi faktisk processerer.
5. ✅ **Scanner prefill:** blog-links kan nu bruge `/scan/?url=domain.com` — feltet
   udfyldes og scannen kører automatisk. /blog/dora-compliance-guide/ brugte allerede
   det mønster uden at det virkede; nu virker det.
6. ✅ /sample/ footer linkede til "/" med forkert label — nu til /pro/dashboard/.

Alt deployet og verificeret live (curl på indhold, ikke kun statuskoder).

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
2. Nyt blog-opslag rettet mod Squarespace- eller Webflow-ejere ("GDPR compliance without a plugin")
3. Kør samme friske-øjne-gennemgang på mobil-layout af /pro/ og /scan/
