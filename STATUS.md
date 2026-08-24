# STATUS — Iteration 149 (24. august)

## 1. Blokering (én linje)

Bitwarden unauthenticated → LS-nøglen utilgængelig; venter på Mads.

## 2. Universalitet (punkt 1) — vurdering

**Bestået.** Kernen i DevNotify (`devnotify/src-tauri/src/providers.rs`) er
platform-uafhængig: `fetch_notifications(provider, token)` — GitHub og GitLab er
adapters ovenpå samme kerne. macOS-appen er én indpakning; en Windows/Linux-build,
CLI eller browser-udvidelse ville genbruge kernen uændret. Sitet er statisk HTML.
Ingen kodeændring nødvendig — vurderingen står ved magt fra iteration 148.

## 3. Denne iteration (kvalitetsgennemgang af sitet)

Gik alle guides/vs-sider igennem med friske øjne. Fandt ét reelt problem:

- **Windows-guiden solgte en Mac-app.** "GitHub Notifications on Windows"
  anbefalede DevNotify som løsning uden at nævne at den kun findes til macOS.
  En Windows-besøgende der klikker "Get DevNotify" bliver skuffet — det er
  direkte konverteringstab og dårlig tro. Rettet: CTA'en hedder nu
  "Get DevNotify for Mac", teksten nævner eksplicit macOS-only og anbefaler
  Gitify til Windows-brugere.
- Deployet via staging-mappe og verificeret live: ny CTA-tekst på guiden,
  landing + download + vs/gitify + privacy/terms alle 200.

## 4. Traction (ærlige tal)

**2 besøg · 1 download · 0 tilmeldinger · $0 · 0 betalende kunder.**

## 5. Venter på Mads

1. Bitwarden-login (eller LS-nøglen lagt klar) → LS-produkt via API + checkout + købstest.
2. Domænekøb getdevnotify.com (forhåndsgodkendt — sig blot til).

## 6. Næste iteration

Ny guide fra høj-intentions søgeord; fortsat indholdsmotor mens LS-nøglen udestår.
