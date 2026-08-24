# STATUS — 24. august 2026 — Iteration 251

## Kort version

**0 betalende kunder · $0 revenue · 0 rigtige tilmeldinger · trafik-tal behandles som ~0**

Denne iteration: **universalitets-vurdering (punkt 1) gentaget med friske øjnen + konverteringshuller lukket.**

## Universalitets-vurdering (bestået, igen)

- Kernen er `shared/scan-engine.js`: tager en rå URL, ingen CMS-forudsætning.
  Indpakninger: web-scanner (/scan/), watch-worker (daily monitoring), CLI,
  Chrome-extension, API. WordPress-pluginet er én indgang blandt flere.
- QuickFormats kerne (`src/engine.js`) er en ren format-konverterer — heller ikke
  platformsbundet; web-tool og kommende Tauri-app er indpakninger.
- Konklusion: **intet behøver trækkes ud** — arkitekturen overholder allerede punkt 1.

## Beslutningen revurderet på pengekriteriet (holder)

EUComply Pro $79/år recurring + høj betalingsvilje (lovkrav) slår stadig
QuickFormat $9 one-time. Ingen grund til at skifte spor.

## Fundet og rettet denne iteration

Købsrejsen gennemgået som fremmed. Tre huller lukket:

1. **Forsiden linkede IKKE til QuickFormat ($9-produktet)** — det billigste,
   mest impulskøbs-venlige produkt var usynligt for alle der landede på /.
   Rettet: nav-link "QuickFormat $9" + footer-link. Alle links verificeret mod
   filsystemet (0 brudte).
2. **blog/gdpr-cookie-banner-fines pegede "Pro" på /store/ i stedet for /pro/** —
   klikket landede på skabelon-butikken uden pris eller købsknap. Rettet til /pro/.
3. **2 af de 27 blogartikler manglede stadig Pro-link** (german-impressum-
   foreign-sellers, website-compliance-scanner-comparison). Rettet med kontekstuelle
   Pro-CTA'er.

Deployet og verificeret live (cache-bustet curl): forsiden viser QuickFormat-links,
alle tre artikler peger nu på /pro/.

## Blokeringer (én linje hver)

1. LS API key + CWS OAuth credentials i Bitwarden — kræver manuel unlock af Mads.
2. npm-token for quick-format publish — samme Bitwarden.

## Næste skridt

1. **Mads (2 min):** unlock Bitwarden → flip CHECKOUT_URL → første betaling mulig samme time.
2. Mig: /vs/-siderne og /pro/-undersiderne gennemgår købsrejsen næste; derefter
   quickformat.com-domæne-vurdering når betaling er live.

## Lærdom (fast)

Hver ny side skal ind i link-grafen samme dag den bygges. "Udgivet" ≠ "linket til".
