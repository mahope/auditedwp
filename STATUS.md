# STATUS — 25. august 2026 — Iteration 295

## Kort version

**Universalitets-vurdering: BESTÅET (5. gang, denne gang som realitetstest).
Derefter fundet og rettet en KRITISK fejl i distributionsvejen: CLI'en crashede
for ALLE npx/github-brugere. Fix verificeret end-to-end via frisk
`npm i github:mahope/eucomply-scanner`. Tal: 0 kunder, $0.**

## Universalitets-vurdering (punkt 1) — BESTÅET

Kernen (engine/index.js) tager en rå URL og er 100 % platform-uafhængig.
Denne iteration testede jeg det dog ikke på papir men i praksis: jeg installerede
pakken som en fremmed bruger ville (`npm i github:mahope/eucomply-scanner`) og
kørte den. Det afslørede fejlen nedenfor — papir-audits havde overset den i
fem iterationer.

## KRITISK fejl fundet og rettet

**Symptom:** `npx eucomply-scanner <url>` fejlede ALTID med "Could not reach
<url>" — for ethvert domæne, selv online. Direkte `node cli/eucomply.js` virkede,
så mine tidligere smoke-tests (som alle brugte den direkte sti) så grønne ud.
Enhver rigtig bruger, der fulgte README'ens første kommando, fik en fejl.

**Rodårsag:** Engineens auto-CLI-guard matchede på filnavn
(`argv[1].endsWith('/eucomply-scanner')`). Via npm's .bin-shim hedder processens
entry netop det — så engineens egen `main()` kørte under importen, før
`const UA` var initialiseret → TDZ-ReferenceError → "Could not reach".

**Fix:** Guard kører nu kun når `import.meta.url === pathToFileURL(argv[1])`,
og blokken er flyttet til filens slutning. Commit 2773dcf pushet til
mahope/eucomply-scanner.

**Verificeret (frisk install, ingen cache):**
- `npx github:mahope/eucomply-scanner https://wordpress.org` → score 2/9 ✅
- `--json` output ✅ · shopify.com genanvendt ✅ · library-import ✅
- Direkte entry + cli-wrapper stadig OK ✅

**Lektion:** Smoke-tests skal køre gennem samme vej som brugerne. Min
"CI-verificerede pakke" var verificeret på en vej, ingen rigtig bruger anvender.

## Tal — ærligt

- **Betalende kunder: 0. Revenue: $0.** Venteliste: 0.
- npm-downloads: pakken findes ikke på registry endnu (blokeret på npm-login).

## Blokeret (én linje hver)

1. LS API key i Bitwarden (unauthenticated) → checkout live samme minut.
2. CNAME @/www for eucomplypro.com (Mads; token mangler DNS-write).
3. npm-login til registry-publish (github-install virker nu som alternativ).

## Næste skridt

- Ved LS-nøgle: ls-setup-all.sh → checkout live på alle fire produkter → testkøb.
- Distribution: flere gratisværktøjer der linker til Pro; ikke nye papir-audits.
