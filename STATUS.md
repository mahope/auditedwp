# STATUS — Iteration 140 (24. august)

## 1. Universalitet (punkt 1) — vurderet

DevNotify-kernen (`providers.rs`) er platform-uafhængig: token ind,
notifications ud. GitHub og GitLab er adapters; sitet er statisk HTML.
**Ikke bundet til én platform — intet at trække ud.** Verificeret igen.

## 2. Gjort denne iteration

- Ny guide: **github-desktop-notifications-mac** ("GitHub Desktop Notifications
  on Mac: Every Option That Works") — høj-intentionssøgning, sammenligner web-inbox,
  email, Gitify, DevNotify + DIY-script. Interne links til download, token-scopes
  og GitLab-guide. Live: 200 + korrekt titel.
- Sitemaps opdateret (rod: 18 URLs; devnotify: 8 URLs). Nav-link på forsiden.
- Deploy verificeret live (forside, ny guide, download-side, DMG svarer 200).

## 3. Blokeringer (én linje hver)

1. LS API-nøgle: Bitwarden `unauthenticated` → checkout kan ikke åbnes endnu.
2. Domæne getdevnotify.com: ikke købt via Cloudflare Registrar endnu.

## 4. Traction (ærlige tal)

**0** betalende · **$0** revenue · **0** rigtige tilmeldinger.

## 5. Venter på Mads

1. LS-nøgle i Bitwarden → LS-produkt via API + live checkout + købstest.
2. Domænekøb getdevnotify.com.

## 6. Næste iteration

LS-nøglen kommer: checkout før alt. Ellers ny guide ("github notifications
slack integration" eller "gitlab desktop app alternative").
