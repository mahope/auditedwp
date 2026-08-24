# STATUS — Iteration 147 (24. august)

## 1. Blokering (én linje)

Bitwarden unauthenticated → LS-nøglen utilgængelig; venter på Mads.

## 2. Universalitet (punkt 1) — vurdering

**Bestået, verificeret denne iteration.** DevNotify-kernen
(`devnotify/src-tauri/src/providers.rs`) er platform-uafhængig:
`fetch_notifications(provider, token)` — GitHub og GitLab er adapters ovenpå
samme kerne. Ingen kode at trække ud; sitet er statisk HTML. En fremtidig
Windows/Linux-build eller CLI ville genbruge kernen uændret.

## 3. Denne iteration

- **Fundet og rettet en reel fejl i købsrejsen:** alle 22 sider linkede til
  `privacy.html`/`terms.html`, som Cloudflare 308-redirectede til extensionless.
  Omdøbt filerne til `privacy`/`terms` og rettet samtlige links → direkte 200,
  ingen redirect-tab for besøgende tæt på køb.
- Gen-deployet via staging-mappe (korrekt `/devnotify/`-præfiks) og verificeret:
  `/devnotify/`, `/devnotify/download/`, `/devnotify/privacy`, `/devnotify/terms`
  samt vs-/guide-sider svarer 200 med korrekt indhold.

## 4. Traction (ærlige tal)

**2 besøg · 1 download · 0 tilmeldinger · $0 · 0 betalende kunder.**

## 5. Venter på Mads

1. Bitwarden-login (eller LS-nøglen lagt klar) → LS-produkt via API + checkout + købstest.
2. Domænekøb getdevnotify.com (forhåndsgodkendt — sig blot til).

## 6. Næste iteration

Ny guide fra høj-intentions søgeord; fortsat indholdsmotor mens LS-nøglen udestår.
