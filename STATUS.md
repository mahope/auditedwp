# STATUS — Iteration 153 (24. august)

## 1. Blokering (én linje)

Bitwarden unauthenticated → LS-nøglen utilgængelig; venter på Mads.

## 2. Universalitetsvurdering (punkt 1) — bestået

- **Kernen** (`fetch_notifications` i Tauri-appen) tager en GitHub/GitLab token
  og returnerer notifikationer — ingen platform-assumption ud over git-hosting.
- **Sitet/landingssiden** er almindelige statiske HTML-sider på Cloudflare Pages.
- **Guides-indholdet** handler om GitHub-notifikationsproblemer generelt, ikke
  om et WordPress-produkt. GitLab-guide findes allerede som bevis på bredde.
- Konklusion: DevNotify er IKKE bundet til én platform i strid med punkt 1.
  macOS-appen er ÉN indpakning; kernen kan senere pakkes som CLI, browser-
  extension eller Windows/Linux-build uden omskrivning.

## 3. Denne iteration — landingssiden linker nu til alle guides

Før: landingssiden havde 0 links til de 12 guides → intet link-equity nåede dem.
Nu: ny "Free guides"-sektion med 11 guide-links grupperet i Fixes / Noise /
Alternatives & Platforms. Undervejs fanget og rettet ét link til en side der
ikke findes (github-notifications-not-working → bruger not-showing-guiden).
Deployet via staging; **alle 11 links verificeret 200 live**.

## 4. Traction (ærlige tal)

**2 besøg · 1 download · 0 tilmeldinger · $0 · 0 betalende kunder.**

## 5. Venter på Mads

1. Bitwarden-login (eller LS-nøglen lagt klar) → LS-produkt via API + checkout + købstest.
2. Domænekøb getdevnotify.com (forhåndsgodkendt — sig blot til).

## 6. Næste iteration

Ny høj-intentions guide; overvej "DevNotify vs Octobox" indholdsopdatering
så sammenligningssiderne matcher de nye søgeord.
