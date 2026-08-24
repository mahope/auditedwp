# STATUS — Iteration 148 (24. august)

## 1. Blokering (én linje)

Bitwarden unauthenticated → LS-nøglen utilgængelig; venter på Mads.

## 2. Universalitet (punkt 1) — vurdering

**Bestået (genbedomt denne iteration, ingen kodeændring nødvendig).**
DevNotify-kernen (`devnotify/src-tauri/src/providers.rs`) er platform-uafhængig:
`fetch_notifications(provider, token)` — GitHub og GitLab er adapters ovenpå
samme kerne. Sitet er statisk HTML. En Windows/Linux-build eller CLI ville
genbruge kernen uændret. Produktet er altså IKKE bundet til én platform —
macOS-appen er én indpakning af flere mulige.

## 3. Denne iteration (konvertering tæt på købet)

- **Landingssiden:** "Buy"-sektionen havde KUN en notify-mig-knap — en besøgende
  der var klar til at prøve produktet havde ingen vej til download. Tilføjet
  "Download free trial"-knap + "Free 7-day trial · no card required"-note.
- **Downloadsiden:** besøgende der downloader var færdige efter DMG'erne.
  Tilføjet licens-blok ("Using it past the 7-day trial? $19 once…") med link
  til #buy — den side hvor trial-udløb er mest nærværende.
- Deployet via staging-mappe og verificeret live: `/devnotify/` viser begge
  CTA'er, `/devnotify/download/` viser licens-blokken, vs-/guide-sider 200.

## 4. Traction (ærlige tal)

**2 besøg · 1 download · 0 tilmeldinger · $0 · 0 betalende kunder.**

## 5. Venter på Mads

1. Bitwarden-login (eller LS-nøglen lagt klar) → LS-produkt via API + checkout + købstest.
2. Domænekøb getdevnotify.com (forhåndsgodkendt — sig blot til).

## 6. Næste iteration

Ny guide fra høj-intentions søgeord; fortsat indholdsmotor mens LS-nøglen udestår.
