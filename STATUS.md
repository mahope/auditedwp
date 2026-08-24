# STATUS — Iteration 151 (24. august)

## 1. Blokering (én linje)

Bitwarden unauthenticated → LS-nøglen utilgængelig; venter på Mads.

## 2. Universalitet (punkt 1) — vurdering

**Bestået, ingen kodeændring nødvendig.** Kernen (`devnotify/src-tauri/src/providers.rs`)
er `fetch_notifications(provider, token)` — platform-uafhængig. GitHub og GitLab er
adapters; Windows/Linux-build, CLI eller browser-udvidelse ville genbruge kernen.
Sitet er statisk HTML. macOS-appen er én indpakning blandt flere.

## 3. Beslutningen revurderet (pengekriteriet)

DevNotify holder stadig: bygget, udgivet, $19-licensmodel, landingsside sælger,
trial + licensvalidering færdigbygget i appen. Eneste manglende led er checkout-linket
(LS-nøglen). Ingen anden kandidat slår "timer til første betaling".

## 4. Denne iteration — fuld QA af den side der står mellem besøgende og betaling

Gennemgik alle 21 sider som en fremmed:

- **Fundet og rettet:** 10 sider linkede logo/home til `/devnotify/index.html`
  (308-redirect). Alle rettet til `/devnotify/`. Verificeret: alle 25 interne links
  svarer 200 live, inkl. begge DMG-filer (200).
- **Fundet (bevidst beholdt):** guides til Windows-brugere anbefaler allerede Gitify
  med disklaimer — korrekt og ærligt, ingen ændring.
- **Metrics-worker fix:** `/stats` returnerede ikke `subscribers`-feltet (deployet
  version var ældre end koden). Rettet og deployet → `{"downloads":1,"visits":2,"subscribers":0}`.
  Tallet er nu målbart igen.

## 5. Traction (ærlige tal, fra workeren direkte)

**2 besøg · 1 download · 0 tilmeldinger · $0 · 0 betalende kunder.**

## 6. Venter på Mads

1. Bitwarden-login (eller LS-nøglen lagt klar) → LS-produkt via API + checkout + købstest.
2. Domænekøb getdevnotify.com (forhåndsgodkendt — sig blot til).

## 7. Næste iteration

Ny guide fra høj-intentions søgeord; indholdsmotor fortsætter mens LS-nøglen udestår.
