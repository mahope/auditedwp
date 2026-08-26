# STATUS — 3. september 2026 — Iteration 468

## Universality-vurdering (punkt 1) — BESTÅET (genbekræftet iter 466 med grep af al kernekilde)

Kernen i `deskuptime/src/` tager en vilkårlig URL og laver HTTP-, SSL- og
indholds-tjek. Nul CMS-referencer. Desktop-app, CLI, live-check-widget og
GitHub Action er indpakninger om den samme platform-uafhængige kerne.
Intet at udtrække, intet at bygge om.

## Gjort i denne iteration — ny købsintentionsside: domain expiry monitor

| Side | Indhold |
|------|---------|
| /deskuptime/domain-expiry-monitor/ | Gratis RDAP-baseret domæneudløbs-checker (virker i browseren, CORS verificeret), "hvorfor domæner stadig går tabt"-sektion, sammenligningstabel, FAQ, JSON-LD (SoftwareApplication + FAQPage), dedikeret 1200×630 og-billede |

Sitemap + hub-side opdateret. Deployet og verificeret: side 200, og-PNG 200
image/png, sitemap-entry og footer-link live. Committed + pushed.

RDAP valgt frem for WHOIS fordi det er en officiel, CORS-åben JSON-API —
ingen server, ingen scraping. TLD'er uden RDAP får en ærlig fejlbesked.

## Næste skridt

1. LS API key → opret "DeskUptime Pro" i Lemon Squeezy, aktivér Buy Now-knap
   (BUILD.md trin 1–5 klar, ~10 min)
2. deskuptime.com købes når checkout er aktiv (forhåndsgodkendt)
3. Flere købsintentions-sider

## Venter på Mads (én linje hver)

1. LS API key i Bitwarden → checkout kan åbnes.

## Tal (ærlige)

Salg 0 · Waitlist 0 · Scans 2 (ægte) · Blogposts 53 · Live sider 189
