# STATUS — Iteration 159 (24. august)

## 1. Blokering (én linje)

LS-nøglen utilgængelig via CLI (Bitwarden session unauthenticated) → venter på Mads.

## 2. Universalitetsvurdering (punkt 1) — bestået (3. gang bekræftet)

Kernen i `devnotify/src-tauri/src/providers.rs` er platform-agnostisk
(normaliseret `NotificationItem`, provider-enum med adapters). macOS-appen er
én indpakning; sitet er statisk HTML. Intet at trække ud.

## 3. Penge-linsen — beslutningen holder

DevNotify: første kunde timer efter LS-nøglen ($19 one-time), bevist
betalingsvilje (Gitify 5.3k stjerner), ~0 kr. leveringsomkostning.
DECISION.md uændret.

## 4. Denne iteration — ny guide: GitHub-notifikationer i Teams

- Ny side `guides/github-notifications-microsoft-teams/` (høj
  søge-intention, stort hul i eksisterende guide-dækning: Slack var dækket,
  Teams var ikke).
- Tilføjet til sitemap (nu 28 URLs) og til "Keep reading" på tre relaterede
  guider (Slack, Discord, miss-PR-review).
- Deployet via staging-mappe (iteration 143-pitfall undgået) og verificeret:
  alle tre sider svarer 200 med korrekte titler, cross-link fundet på live
  side.

## 5. Traction (ærlige tal)

**2 besøg · 1 download · 0 tilmeldinger · $0 · 0 betalende kunder.**

## 6. Venter på Mads

1. **Log ind i Bitwarden-desktopappen én gang** (eller læg LS-nøglen et sted
   jeg kan læse). Derefter: produkt + checkout via API samme hour —
   `ls-setup.sh` → `ls-flip.sh <url>` → deploy → test-køb.
2. Domænekøb getdevnotify.com (forhåndsgodkendt — sig blot til).

## 7. Næste iteration

Ny guide ("GitHub notification badge not showing on app icon") eller
forbedring af download-sidens CTA.
