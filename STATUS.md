# STATUS — Iteration 116 (23. august 2026, aften)

## 1. Universitets-vurdering (punkt 1) — bestået

DevNotify er ikke platform-bundet: kernen er notifications-API → normaliseret
liste → menu bar UI + polling. GitHub er én adapter; GitLab/Linear/Jira kan
lægges ind uden kerne-ændring. Ingen udtrækning nødvendig.

## 2. Pengekriteriet — beslutningen holder stadig

DevNotify er det eneste produkt der allerede kan levere: bygget færdig,
$19 lifetime, leveringsomkostning 0. Ingen ny idé slår "timer til første
kunde når LS-nøglen kommer".

## 3. Bygget denne iteration: måling — downloads og besøg kan nu tælles

Tidligere stod der "Ingen analytics på DMG-downloads endnu". Rettet:

| Ting | Verificeret |
|------|--------|
| Ny Worker `devnotify-metrics` (KV-tæller, ingen cookies, IP-dedupe 1/time) deployeret til devnotify-metrics.mahope-eeb.workers.dev | ✅ /health, /event og /stats testet live |
| Landingsside sender nu visit-event + download-klik på alle .dmg-links | ✅ script live på auditedwp.pages.dev/devnotify/ |
| Privacy.html opdateret med ærlig beskrivelse af den anonyme tæller | ✅ 200 live |
| Feature-tekst rettet fra "no analytics" → "no tracking of your activity" (var ikke længere præcist) | ✅ |
| Testtællinger nulstillet — tallet starter ærligt på 0 | ✅ |

Bemærkning: Cloudflare Web Analytics kunne ikke aktiveres (API-tokenet har
ikke analytics-scope), så jeg byggede i stedet en egen 30-linjers Worker —
gratis, cookie-fri, og jeg styrer tallene selv.

## 4. Traction (ærligt)

**0** betalende kunder · **0** downloads · **0** besøg · **$0** revenue.
Målingen er nu på plads, så næste rapportering bygger på rigtige tal.

## 5. Budget

Brugt: **0 kr**. Workers + KV koster intet på gratis-niveauet.
getdevnotify.com forhåndsgodkendt (~90 DKK), venter på køb.

## 6. Venter på Mads (én linje, uændret)

LS API-nøgle (Bitwarden) = eneste revenue-blokering. Domæne + posts klar.

## Næste iteration

1. LS-nøgle → opret produkt $19 via API → checkout-URL i buy-btn → genudgiv.
2. Flere søgeindgange ("github notifications widget mac", "tauri menu bar app").
3. Overvej Intel-build for at udvide det købende marked.
