# RESEARCH — Iteration 110 (26. august 2026)

## Ny retning: Desktop app (Tauri) i stedet for web SaaS

**Beslutning:** EUComply er blokeret på Mads' konti i 100+ iterationer med $0 revenue.
Under nye rammer (23/8): skriv blokering som én linje, start nyt produkt.

**Kilde:** Research på solo developer revenue patterns (26/8)
- Lunar: $7K/mo, macOS app, $23 lifetime license, solo dev
- 35 micro SaaS portfolio: $77K/mo, solo dev, simple tools
- VS Code extensions: $6.8K/mo fra 3 niche extensions
- Mønster: niche problem, lokal-først, low overhead, lifetime eller lav subscription

**Valgt:** DevNotify — GitHub notifications i macOS menu bar

## Hvorfor desktop app

1. **Færrest blokeringer:** Kun LS-nøgle (vs. VS Code konto + LS)
2. **Ingen hosting-omkostning:** Kører på brugers maskine
3. **Stærk USP:** 100% lokal, ingen cloud. GitHub har dårlig native macOS klient
4. **Bevis:** Lunar ($7K/mo) beviste at $19-23 macOS apps virker for solo devs

## Konkurrenter

| Værktøj | Pris | Kommentar |
|---------|------|-----------|
| GitHub web UI | Gratis | Langsom, kræver browser |
| GitHub Mobile app | Gratis | Mobil-only, ikke menu bar |
| Gitify (OSS) | Gratis | Electron, eksisterer men clunky |
| Octobox | $29/mo | Web-baseret, enterprise-fokuseret |
| **DevNotify** | **$19 lifetime** | Native macOS, menu bar, 100% lokal |

## Prisanalyse

Lunar: $23 lifetime, $7K/mo → ~300 salg/md
DevNotify mål: $19 lifetime, mål 50-100 salg første måned = $950-1,900

## Næste research-spørgsmål (når LS-nøgle kommer)
- Hvordan bundter man license key validation i Tauri?
- Hvordan notarizer man en macOS app uden Apple Dev account?
## Opdatering 23/8 (iteration 127): konkurrenttjek under penge-linsen

- Gitify (github.com/gitify-app/gitify): 5.325 stjerner, gratis, Electron,
  macOS/Win/Linux, GitHub-only. Verificeret via GitHub API.
- Læsning: markedet er beboet og der er download-aktivitet → bevist efterspørgsel.
  Gitify's eksistens gør DevNotify MERE troværdig som forretningsidé, ikke mindre.
- DevNotify's differentiering: native Tauri (mindre RAM end Electron),
  GitLab-adapter indbygget, $19 lifetime med remote licensvalidering.
- Konklusion: DECISION.md holder. Ingen ændring.
