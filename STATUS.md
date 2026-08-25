# Iteration 346 — 25. august 2026

## Universality-vurdering (punkt 1 i de nye rammer)

**Konklusion: kernen ER universel. Ingen udtrækning nødvendig.**

Fakta:
- Scanningskernen ligger allerede som en selvstændig, platformsuafhængig pakke
  i `eucomply-scanner/engine/` (MIT, npm-klar). Headeren siger det eksplicit:
  "takes any public URL … no platform assumptions".
- WordPress-detektion findes kun som **informationelt platform-fingerprint**
  (meta generator + stier), aldrig som en forudsætning. Kernen antager ingenting.
- **Live-verificeret lige nu (egne kørsler, ikke gamle noter):**

| Platform | Testside | Score |
|---|---|---|
| Shopify | shopify.com | 4/9 (44 %) |
| Squarespace | squarespace.com | 3/9 (33 %) |
| WordPress | wordpress.org | 2/9 (22 %) |

Samme kerne, samme checks, meningerløse resultater på alle tre. Det er tidligere
iterationer (344–345) også konkluderet på Next.js/Webflow-sider.

**Arkitekturen følger allerede mønsteret "kerne + indpakninger":**
kerne = `eucomply-scanner` (CLI + importbar engine)
indpakninger = web-UI på /scan/, worker-scan API, WordPress-plugin (kun én af
flere indgange).

Ingen kodeændringer krævet af punkt 1.

## Portefølje-status

5 produkter bygget og live: EUComply Free/Pro, QuickFormat, DevNotify,
ComplianceDocs (+ Chrome extension-pakke). Alle QA't. **Ingen kan tage imod
penge endnu** — alt venter på Lemon Squeezy-nøglen.

Traction (ærlige tal, ikke mine egne tests): 0 betalende kunder, 0 rigtige
tilmeldinger siden nulstilling 24/8.

## Venter på Mads (én linje hver, uændret)

1. LS API key i Bitwarden — eller manuel opsætning (~20 min), se LS-MANUAL.md.
2. DNS: CNAME `@` + `www` → auditedwp.pages.dev (proxied) — eller token med DNS-edit.

## Næste skridt

1. LS key modtaget → opret produkter via API → sandbox-køb → første betaling.
2. CNAME sat → domæner peger rigtigt inden for minutter.
3. Affiliate-IDs → /cmp-comparison/ (allerede bygget).
4. Imens: forbedre det der står mellem besøgende og betaling på egne flader —
   intet nyt produkt bygges oven på LS-blokeringen.
