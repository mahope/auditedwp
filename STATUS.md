# STATUS — 3. september 2026 — Iteration 469

## Universality-vurdering (punkt 1) — BESTÅET

Kernen i `deskuptime/src/` tager en vilkårlig URL og laver HTTP-, SSL- og
indholds-tjek. Nul CMS-referencer (grep-verificeret iter 466). Desktop-app,
CLI, live-check-widget, GitHub Action og de nye gratis web-værktøjer er alle
indpakninger om den samme platform-uafhængige kerne. Intet at udtrække.

## Gjort i denne iteration — ny købsintentionsside: website change monitor

Målgruppe: changedetection.io/Visualping-publikummet — folk der betaler $9-30/md
for at få besked når en side ændrer sig. DeskUptime gør det samme for $19 én gang.

| Del | Status |
|-----|--------|
| Worker: nyt `/hash?url=` endpoint (SHA-256 af sidens HTML, CORS-åben) | Deployet + verificeret (stabil hash på 2 kald, /check upåvirket) |
| /deskuptime/change-monitor/ — gratis fingerprint-checker i browseren, "hvad overvåger man"-sektion, SaaS-sammenligningstabel, FAQ, JSON-LD (SoftwareApplication + FAQPage) | Deployet, 200 |
| Dedikeret 1200×630 og-billede (SVG→PNG, visuelt verificeret) | 200 image/png |
| Sitemap + hub-footer opdateret | Live |

Fejl undervejs (rettet): /hash ramte TDZ (const target deklareret senere) →
1101-fejl; flyttet deklarationen op. Deploy kræver eksplicit entry-point
(`wrangler deploy index.js`) pga. multi-env wrangler.toml.

## Næste skridt

1. LS API key → opret "DeskUptime Pro" i Lemon Squeezy, aktivér Buy Now-knap
   (BUILD.md trin 1–5 klar, ~10 min). Siden fanger trafikken indtil da.
2. deskuptime.com købes når checkout er aktiv (forhåndsgodkendt)
3. Flere købsintentionssider (næste kandidat: cron monitoring / status page alternativ)

## Venter på Mads (én linje hver)

1. LS API key i Bitwarden → checkout kan åbnes.

## Tal (ærlige)

Salg 0 · Waitlist 0 · Scans 2 (ægte) · Blogposts 53 · Live sider 190
