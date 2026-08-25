# DECISION — 26. august 2026 — DeskUptime: Desktop website monitor

## Beslutning: HOLDER under pengekriteriet.

## Hvad: DeskUptime — Desktop website monitor

| | |
|---|---|
| **Produkttype** | Tauri desktop app (macOS, Windows) + CLI (gratis) + web live-check (gratis) |
| **Målgruppe** | Webdevelopere, freelancere, små teams der overvåger websites |
| **Problem** | Uptime-monitorering SaaS koster $7-15/md ($84-180/år). En desktop app gør det samme uden løbende serveromkostninger |
| **Pris** | **$19 one-time** via LS license key (3 aktiveringer) |
| **Platform** | Salg via LS checkout. Distribution: GitHub Releases + npm (CLI) |
| **Indtjeningsmodel** | LS licensnøgle — $19 × ~92% (MoR) = ~$17,50/køb |
| **Status** | Desktop app BYGGET. Produktside LIVE med live-check widget. CLI virker. Domæne klar til køb (deskuptime.com). Venter på LS key for betaling. |

## Vurdering på de fem pengekriterier

| Kriterium | Vurdering |
|-----------|-----------|
| **Hurtig til betaling** | **Meget hurtig** — når LS key kommer: 10 min at oprette checkout-link og aktivere køb. Produkt og side er klar. |
| **Beløb pr kunde** | **$19** — impulse purchase for en freelancer. Lav friktion. |
| **Antal kunder** | Stort marked: UptimeRobot ~3M brugere, Pingdom ~500K betalende. Selv 0.01% = 300-500 kunder. |
| **Tilbagevendende** | **One-time.** Lavere LTV end SaaS, men lavere pris = lettere at sælge. Kræver nye kunder konstant. |
| **Leveringsomkostning** | **$0** — desktop app. Ingen servere, ingen cloud-infra. Cloudflare worker (live-check) er gratis tier. |

## Hvorfor valgt frem for alternativer (26. august — pengekriteriet)

| Alternativ | Vurdering |
|------------|-----------|
| **EUComply Pro ($79/yr)** | 0 salg efter måneder. Signal: compliance-nichen viser ikke kundeefterspørgsel. Aflivet. |
| **Chrome extension** | Kræver CWS API key → Bitwarden. Længere fra betaling end desktop. |
| **VS Code extension** | Kræver publisher account → Mads. Markedsplads-afhængig. |
| **KDP ebook ($9.99)** | 0 salg. Manuelt upload (ingen API). Kræver Mads hver gang. |
| **SaaS** | Kræver servere + drift + betalingsflow. Desktop er $0 at levere. |
| **Nyt produkt fra bunden** | DeskUptime er bygget og virker. At starte forfra forsinker betaling. |

## Hvad kan slå det ihjel

- **LS key kommer aldrig** — men alt andet er klar. Når den kommer, 10 min til checkout.
- **Ingen finder produktet** — 0 trafik. Løsning: SEO + blog-indhold (10+ artikler live).
- **Konkurrence fra gratis SaaS tiers** — differentierer via privacy, one-time price, desktop UX.
- **Desktop kræver at maskinen kører** — det er en reel begrænsning. Men til daglig "er alt OK?" er det nok for målgruppen.

## Domæne

Foreløbigt køb: **deskuptime.com** foreslået — verificeret ledigt 27/8-2026. ~$10/år via Cloudflare Registrar. Bygger videre på auditedwp.pages.dev/deskuptime/ indtil domænet sættes foran.