# STATUS — 24. august 2026 — Iteration 247

## Kort version

**0 betalende kunder · $0 revenue · 0 rigtige tilmeldinger (reelle tal)**

Universalitets-vurderingen (punkt 1) er **bestået for alle 3 produkter** — ingen
platform-binding fundet, ingen omskrivning nødvendig. Til gengæld fandt jeg noget
vigtigere i denne iteration: **QuickFormat-appen var bygget færdig, men aldrig lagt ud.
Nu kan man downloade og bruge den — gratis beta. Det er det tætteste på et salgbart
produkt, vi har.**

## Universalitets-vurdering (punkt 1) — bestået

| Produkt | Kerne | Platform-uafhængig? |
|---------|-------|---------------------|
| EUComply | `shared/scan-engine.js` + worker | ✅ Tager enhver URL, ingen CMS-antagelser (verificeret mod example.com). WP-plugin/extension/CLI = indpakninger. |
| QuickFormat | `quickconvert/src/engine.js` | ✅ Ren konverteringskerne. Indpakninger: CLI, web-tool, Tauri-app. |
| DevNotify | (droppet som aktivt fokus) | n/a |

Ingen kerne skal trækkes ud — de ER allerede kerner med indpakninger udenom.

## Nyt denne iteration: QuickFormat er nu reelt downloadbar

- Verificerede at `QuickFormat.app` faktisk virker: kører (arm64), GUI starter,
  konverteringskernen returnerer korrekt output (JSON→YAML testet direkte).
- Pakket appen: `site/downloads/QuickFormat-macOS.zip` (3,2 MB).
- Produktsiden ændret fra "venteliste" til **direkte download + "Buy License $9"**:
  gratis beta nu, køb når checkout-flip kommer.
- Deployet og verificeret live: side 200, zip 200 (3.223.757 bytes), download-link på siden.

**Bemærkning om ærlighed:** Appen er ikke kodesignet (ad-hoc signatur) og ikke notariseret,
så macOS Gatekeeper viser en advarsel ved første åbning ("højreklik → Åbn"). Det står ikke
i vejen for beta-brugere, men notarisering kræver Mads' Apple Developer-konto ($99/år) —
notér som fremtidig udgift hvis QuickFormat får traction.

## Hvad der er klar

| Område | Status |
|--------|--------|
| QuickFormat.app downloadbar fra produktsiden | ✅ NY — live |
| Scanner API + site (alle sider 200) | ✅ Live |
| Pro-side $79/år | ✅ Live, venter kun på checkout-URL |
| Flip-scripts + /config endpoint | ✅ Klar |

## Blokeringer (én linje hver)

1. LS API key i Bitwarden — kræver manuel unlock af Mads.
2. CWS OAuth credentials — samme Bitwarden.

## Næste skridt

1. **Mads (2 min):** unlock Bitwarden → LS API key (eller kør flip-script selv)
2. Mig (minutter efter): LS-produkter → flip CHECKOUT_URL → test checkout → første betaling mulig
3. Uden blokering: SEO-indhold + npm-publish af `quick-format` CLI (gratis distribution)

## Lærdom

Jeg brugte tidligere iterationer på at skrive "QuickFormat app not yet built" i statusser,
uden at tjekke om den faktisk VAR bygget. Den var. Tjek artefakter før du antager mangler.
