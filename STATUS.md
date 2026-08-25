# STATUS — Iteration 387 — 26. august 2026

## Universality-vurdering (punkt 1): ✅ OPFYLT — intet ombygningsarbejde

Kernen er scan-workeren (`eucomply-scan.mahope-eeb.workers.dev`). Den tager en
almindelig URL og virker uanset CMS. Verificeret i denne iteration:

- Ingen WordPress-specifik logik i kernen; platform-fingerprint er kun en detektion
- Indpakninger omkring samme kerne: web-scanner (/scan), CLI (npx github:),
  browser-extension, watch/dashboard worker
- Konklusion: kernen ER universel. Det vi har bygget beholdes som indpakninger.

## Beslutningen under pengekriteriet: STÅR VED MAGT

Revurderet mod de fem pengekriterier (første betaling, beløb, reach,
tilbageværende, leveringsomkostning). EUComply Pro $79/yr vinder stadig:
højeste beløb pr. kunde, tilbagevendende, ~0 kr drift. Alle andre produktidéer
er blokeret på samme Lemon Squeezy-nøgle, så ingen fordel ved at skifte.

## Ærlige tal (0 er 0)

| Måling | Værdi |
|--------|-------|
| Betalende kunder | **0** |
| Ægte eksterne scanninger | **0** |
| Google-indekserede sider | ~0 (IndexNow genindsendt) |
| Waitlist (test-adresser frasorteret) | 0 |

## Hvad blev gjort i denne iteration

| # | Opgave | Status |
|---|--------|--------|
| 1 | Universality-vurdering af kernen | ✅ OPFYLT |
| 2 | Gennemgang af købsrejsen /pro/ + /pricing/ + scan→upsell-tragt | ✅ Fundet stærk |
| 3 | Fejl fundet og rettet: pricing sagde "7-day scan history", /pro/ lover 30 dage → rettet til "30-day scan history & change log" | ✅ Deployet og verificeret live |
| 4 | IndexNow genindsendt: alle 152 URLs til api.indexnow.org + Bing (begge HTTP 200) | ✅ |
| 5 | Link-check af kerne-sider (/ , /pro/, /scan/, /pricing/, sample-report, PDF, dashboard, vs-sider, store, privacy, terms, extension, how-it-works) | ✅ Alle 200 |
| 6 | robots.txt + sitemap verificeret (152 URLs, key-file 200) | ✅ |

## Prioritering fremad (efter Mads' rækkefølge)

Punkt 1-2 (besøgende→betaling + produkt) er gennemgået og solide.
Flaskehallet er punkt 3: TRAFIK. 0 ægte scanninger = ingen når siden.

1. Få indeksering igennem (IndexNow nu genindsendt — overvåg næste uger)
2. Mere guide-indhold med søgevolume (GDPR/NIS2/EAA per platform)
3. Når LS-key lander: `bash scripts/ls-setup-all.sh` → checkout < 5 min

## Blokeringer (én linje hver)

1. LS API key i Bitwarden → blokerer checkout for ALLE produkter
2. eucomplypro.com CNAME: mangler DNS-edit i Cloudflare-tokenet
3. npm-udgivelse: mangler write-token (npx github: fallback virker)
4. Chrome CWS udgivelse: mangler credentials
