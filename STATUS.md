# STATUS — Iteration 156 (24. august)

## 1. Blokering (én linje)

LS-nøglen utilgængelig (Bitwarden CLI unauthenticated) → venter på Mads.

## 2. Universalitetsvurdering (punkt 1) — bestået, ingen ændring

Kernen i `devnotify/src-tauri/src/providers.rs` er platform-agnostisk
(normaliseret `NotificationItem`, provider-enum med adapters — nye hosts uden
UI-ændringer). macOS-appen er én indpakning; sitet er statisk HTML. Intet at
trække ud.

## 3. Penge-linsen — beslutningen holder

DevNotify: første kunde timer efter LS-nøglen ($19 one-time), bevist
betalingsvilje (Gitify 5.3k stjerner), ~0 kr. leveringsomkostning.
DECISION.md uændret.

## 4. Denne iteration — ny guide "GitHub Notifications in Discord"

- Ny side `guides/github-notifications-discord/`: 3 metoder (webhook, bot,
  lokal menu bar app) sammenlignet i en ærlig tabel — fanger søgninger efter
  Discord-integration, som vi ikke dækkede.
- Linket fra landingssiden (nu 13 guide-links), sitemap.xml (nu 27 URLs) og
  keep-reading på 3 relaterede guides (slack, slack-too-noisy,
  miss-pr-review).
- Deployet via staging og verificeret live: ny side 200 med korrekt titel,
  sitemap viser 27 URLs, interne links bekræftet på live-siderne.

## 5. Traction (ærlige tal)

**2 besøg · 1 download · 0 tilmeldinger · $0 · 0 betalende kunder.**

## 6. Venter på Mads

1. Bitwarden-login (eller LS-nøglen lagt klar) → LS-produkt via API +
   checkout + købstest.
2. Domænekøb getdevnotify.com (forhåndsgodkendt — sig blot til).

## 7. Næste iteration

Ny guide med høj søge-intention (fx GitHub + Teams/email-digest), eller
forbedring af landingssidens CTA over foldet.
