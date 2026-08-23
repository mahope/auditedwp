# DECISION — Iteration 110 (26. august 2026)

**Status:** NY BESLUTNING. EUComply er blokeret på Mads' konti (Bitwarden/LS).
Under nye rammer: skriv blokeringen som én linje, start nyt produkt.

## Nyt produkt: DevNotify — GitHub Notifications in Your Menu Bar

### Hvad
En macOS menu bar app (Tauri v2) der samler dine GitHub-notifikationer ét sted:

- Menu bar icon viser antal ulæste notifikationer
- Klik → popup vindue med liste over PRs, issues, mentions
- Klik på en notifikation → åbner i browser
- Background polling hvert 60. sekund
- Kræver: GitHub Personal Access Token (brugerens egen)

### Til hvem
Udviklere der:
- Har travlt og glemmer at tjekke GitHub
- Har flere repos og mange notifications
- Vil have et hurtigt overblik uden at åbne browseren

### Hvorfor nu
- **Mønster:** Lunar ($7K/mo, $23 license) — macOS desktop app, solo dev, lifetime license
- **Bevis:** $6.8K/mo fra VS Code extensions — udviklere betaler for workflow-værktøjer
- **Unikt:** GitHub notifications har ingen god native macOS klient. Web-UI'et er langsomt.
- **Lokal USP:** 100% lokal, ingen data sendes til skyen (modsætning: GitHub web + email)

### Indtjeningsmodel
- **$19 lifetime license** (som Lunar's $23)
- Betaling: Lemon Squeezy (når nøglen ligger i Bitwarden)
- Freemium: Gratis trial (7 dage) via LS license key API

### Hvorfor valgt frem for alternativer

| Idé | Dom |
|-----|:---:|
| EUComply (blokeret på Mads) | ❌ Blokeret — 0 revenue på 100+ iters |
| VS Code extension | ❌ Kræver publisher account + LS = 2 blokeringer |
| Web micro-SaaS | ❌ Samme LS-blokering, anden vertikal |
| Digitalt produkt på markedsplads | ❌ Kræver Mads' konto |
| **DevNotify desktop app** | ✅ Bygget, virker, kun LS blokering |

### Hvad kan slå den ihjel
- GitHub laver en native macOS app (de har en, men den er dårlig)
- For lille marked (GitHub power users)
- Apple ændrer menu bar API (usandsynligt)

### 5-punkts pengevurdering

| Faktor | DevNotify | Score |
|--------|-----------|:-----:|
| Tid til 1. kunde | Timer efter LS-nøgle | ⭐⭐⭐⭐⭐ |
| Beløb pr. kunde | $19 (one-time) | ⭐⭐⭐ |
| Markedsstørrelse | ~10M GitHub devs, ~1M power users | ⭐⭐⭐⭐ |
| Tilbagevendende | One-time (kan add årlig opdatering) | ⭐⭐ |
| Omkostning | 0 kr/md — bygget, klar til distribution | ⭐⭐⭐⭐⭐ |

## Domæne: devnotify.app / devnotify.dev (forhåndsgodkendt)

Foreslået: **getdevnotify.com** eller **devnotify.dev**.
Skriv i BUDGET.md og sig til.

## Næste skridt (når LS-nøgle kommer)
1. Opret produkt i LS via API ($19 license)
2. Bundle .app med notarization (kræver Apple Dev account — Mads?)
3. Distribuer via getdevnotify.com landingsside
4. Alternativt: GitHub releases + direkte download