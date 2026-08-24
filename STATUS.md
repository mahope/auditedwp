# STATUS — Iteration 154 (24. august)

## 1. Blokering (én linje)

Bitwarden: CLI unauthenticated OG desktop-appen kan ikke åbne sit vindue
(spawner en TCC-tilladelsesdialog der kræver Mads' klik — set i systemlog).
→ LS-nøglen utilgængelig; venter på Mads.

## 2. Universalitetsvurdering (punkt 1) — genbekræftet

Kernen (`fetch_notifications`) tager en git-host-token (GitHub/GitLab) og er
platform-agnostisk; macOS-appen er én indpakning, sitet er statisk HTML.
Ingen overtrædelse af punkt 1.

## 3. Denne iteration — ny guide + intern linkning

- Ny høj-intentions guide:
  `guides/github-notifications-slack-too-noisy/` ("GitHub Notifications in
  Slack Are Too Noisy? 6 Ways to Fix It") — fanger søgninger fra folk der har
  prøvet Slack-integrationen og stadig mangler personlige alerts.
- Linket fra landingssiden (guides-sektion), fra de to relaterede guides
  (slack-github-notifications, turn-off-github-email-notifications) og tilføjet
  til sitemap.xml (nu 25 URLs).
- Deployet via staging-mappen og verificeret live: ny guide 200 med korrekt
  titel; backlinks fundet på landing + begge guides; sitemap opdateret;
  spotcheck af forsiden/download/terms/privacy = 200.

## 4. Traction (ærlige tal)

**2 besøg · 1 download · 0 tilmeldinger · $0 · 0 betalende kunder.**

## 5. Venter på Mads

1. Bitwarden-login (eller LS-nøglen lagt klar) → LS-produkt via API +
   checkout + købstest. OBS: desktop-appen viser intet vindue pga. en
   TCC-dialog der skal godkendes manuelt.
2. Domænekøb getdevnotify.com (forhåndsgodkendt — sig blot til).

## 6. Næste iteration

Ny sammenligningsside ("DevNotify vs GitHub mobile push"), eller opdatering af
vs/-siderne så de matcher nye søgeord.
