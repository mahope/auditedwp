# STATUS — Iteration 146 (24. august)

## 1. Blokering (én linje)

Bitwarden er ikke logget ind (ikke blot låst) — LS-nøglen kan ikke hentes, og jeg
har ikke login til at låse det op. Venter på Mads.

## 2. Universalitet (punkt 1) — vurdering

**Bestået.** DevNotify-kernen (`devnotify/src-tauri/src/providers.rs`) er
platform-uafhængig: `fetch_notifications(provider, token)` med GitHub/GitLab som
adapters. Sitet er statisk HTML. Intet at trække ud — GitLab-siden er allerede en
anden indgang til samme kerne.

## 3. Denne iteration

- **Købsrejse gennemgået med friske øjne.** Fundet og rettet:
  - vs-siderne Gitify/Octobox manglede krydslinks til de andre sammenligninger.
  - Octobox-CTA var inkonsistent (manglede pris + købsknap) — ensrettet.
  - GitHub Desktop-siden var ikke linket fra nogen side (kun sitemap) → linket fra
    alle andre vs-sider + guides-siden footer.
  - Ny side: **vs/chrome-extension/** — "github notifications chrome extension"-
    søgeord (største gratis alternativ). Ærlig vinkel: udvidelsen er fin hvis
    Chrome altid er åben; native app virker uden browser.
  - Guides-oversigten fik browser extensions som punkt 5 (DevNotify nu 6).
- Sitemap 23 URLs. Deployet via staging-mappe med korrekt `/devnotify/`-præfiks.
  Verificeret live: titler på 5 sider, krydslinks på nye side, DMG 0.2.0 (begge
  arch) downloader med fuld størrelse.

## 4. Traction (ærlige tal)

**2 besøg · 1 download · 0 tilmeldinger · $0 · 0 betalende kunder.**

## 5. Venter på Mads

1. Bitwarden-login (eller LS-nøglen lagt klar) → LS-produkt via API + checkout + købstest.
2. Domænekøb getdevnotify.com (forhåndsgodkendt — sig blot til).

## 6. Næste iteration

Ny guide fra høj-intentions søgeord; fortsat indholdsmotor mens LS-nøglen udestår.
