# STATUS — 2. september 2026 — Iteration 440

## 1. Universality-vurdering (iterationsopgaven): KERNEN ER ALLEREDE UNIVERSEL ✅

Gennemgang af DeskUptime mod punkt 1:

- **Kernen** (`deskuptime/src/engine.js` + `checkers/`) tager en almindelig
  URL og kører HTTP-checks. Nul CMS-antagelser — kommentaren i filen siger
  det selv: "Universal kernel: can run standalone (Node.js), as CLI, or
  integrated into a Tauri desktop app."
- Verificeret i praksis: CLI-testene rammer vilkårlige domæner
  (`example.com`, osv.), og web-widgeten på `/deskuptime/` tager enhver URL.
- **Indpakninger omkring kernen** (som mandatet foreskriver):
  1. CLI (gratis, curl-install) — platform-uafhængig
  2. Tauri desktop-app (macOS/Windows) — ÉN indpakning blandt flere
  3. Web live-check widget + GitHub Actions-guide — flere indgange
- Ingen WordPress-plugin, ingen platform-binding nogen steder.
  Landingssiden og JSON-LD FAQ'en siger eksplicit "works with any website".

**Konklusion: Intet at trække ud. Strukturen er allerede kerne + indpakninger.
Der bygges videre på den samme kerne.**

## 2. Købsrejsen: downloads-siden fik direkte download-links ✅

Forrige iteration efterlod kun et link til releases-taget (to klik til fil).
Nu peger downloads-siden direkte på alle fire v0.2.1-assets:

- macOS Apple Silicon (.zip), macOS Intel (.zip)
- Windows installer (.exe) + MSI

Alle fire URLs verificeret med `curl -sIL` → HTTP 200 før deploy.

## Ærlige tal

| Metrik | Værdi |
|--------|-------|
| Salg | **0** |
| Waitlist | **0** |
| Scans (reelle, testdomæner ekskl.) | **2** (craigslist.org, wix.com — ikke min trafik) |

## Blokering (1 linje)
LS API key ligger i Bitwarden som er låst.

## Næste skridt
1. LS key → `wrangler secret put CHECKOUT_URLS_JSON` med
   `{"deskuptime":"<checkout-url>"}` → Buy-knappen går live uden ny deploy.
2. Domæne deskuptime.com (~$10/år, forhåndsgodkendt).
3. Forbedring af produktet: release v0.2.2 så Windows-filnavne matcher
   versionsnummeret (i dag hedder .exe/.msi "0.1.0").

## Venter på Mads
- Lås Bitwarden op én gang så LS key kan hentes.
- Køb af deskuptime.com — sig bare til.
