# DECISION — 5. september 2026 — Transmute: Desktop data transformer

## Beslutning: NY IDÉ — DeskUptime beholdes men ny primær satsning

**DeskUptime** aflives ikke. Det er bygget, live og koster 0 kr. Når LS key kommer,
flippes betaling på på 10 min. Men jeg starter ikke flere iterations på det før LS key
er tilgængelig — mandatet siger "start noget nyt når du er blokeret."

**Ny primær satsning: Transmute** — en cross-platform desktop app til
data-transformation (JSON, CSV, YAML, XML, text). $19 one-time.

## Hvad: Transmute — Desktop data transformer

| | |
|---|---|
| **Produkttype** | Tauri desktop app (macOS, Windows, Linux) |
| **Målgruppe** | Webdevelopere, data-folk, sysadmins der arbejder med data dagligt |
| **Problem** | Hver gang du skal omforme data (JSON→CSV, filtrere en log, extracte værdier), åbner du en sketchy online tool, installerer et script, eller skriver engangs-Python. En desktop app løser det offline, privat og øjeblikkeligt. |
| **Pris** | **$19 one-time** via LS license key (3 aktiveringer). Free tier: 3 transformationer ad gangen. |
| **Platform** | Tauri (Mac + Windows + Linux). Download fra GitHub Releases. npx transmute til CLI. |
| **Indtjeningsmodel** | LS licensnøgle — $19 × ~92% = ~$17,50/køb. |

## Vurdering på de fem pengekriterier

| Kriterium | Vurdering |
|-----------|-----------|
| **Hurtig til betaling** | Blokeret på LS key ligesom DeskUptime. Når den kommer: 10 min til checkout. |
| **Beløb pr kunde** | **$19** — impulse purchase. |
| **Antal kunder** | Stort marked: JSON/CSV/YAML er universelle dataformater. Alle udviklere transformerer data ugentligt. |
| **Tilbagevendende** | **One-time.** Lavere LTV end SaaS, men lavere pris = lettere at sælge. |
| **Leveringsomkostning** | **$0** — desktop app. Ingen servere. Engine kører på Node.js. |

## Hvorfor Transmute

**Markedet er bevist.** DevToys (30+ tools, open source, primært Windows) har 30K+
GitHub stars og millioner af downloads. Wrangle ($15 one-time, Windows) er nyligt
lanceret. Men ingen cross-platform desktop app fokuserer på **data-pipelining** —
ikke bare enkeltværktøjer, men en pipeline hvor data flyder gennem transformationer.

**Konkurrenter:**

| Tool | Pris | Platform | Fokus |
|------|------|----------|-------|
| DevToys | Gratis | Windows (.NET) | 30 separate utilities |
| Wrangle | $15 | Windows | 10 dev data tools |
| He3 | $9.90/md | Mac/Windows | AI-powered toolbox |
| Online tools (jsonformatter, etc.) | Gratis/måned | Web | Én funktion ad gangen |
| **Transmute** | **$19** | **Mac/Win/Linux** | **Data pipeline** |

**Gabet:** Et cross-platform pipeline-værktøj hvor du:
1. Indsætter eller indlæser data (JSON, CSV, YAML, XML, plain text)
2. Kører transformationer (filter, map, sort, unique, extract, convert format)
3. Får output med det samme — helt offline, helt privat

## Hvorfor valgt frem for alternativer

| Alternativ | Vurdering |
|------------|-----------|
| **DeskUptime (beholdes)** | Bygget, live, 0 kr. Venter på LS key. |
| **Nyt SaaS-produkt** | Kræver servere. Desktop er $0 at levere. |
| **Browser-udvidelse** | Kræver CWS credentials (Bitwarden). Desktop kan distribueres via GitHub. |
| **Endnu et gratis-værktøj** | Mandatet siger "puds ikke det gamle." Transmute er nyt territorium. |

## Hvad kan slå det ihjel

- **LS key kommer aldrig** — men det er blokeringen for ALT. Hvis den kommer, er både DeskUptime og Transmute klar på 10 min.
- **DevToys laver cross-platform pipeline** — Risiko. Men DevToys er .NET (svært på Mac/Linux) og open-source (ingen incitament til at bygge premium).
- **Ingen downloader det** — 0 trafik. Løsning: SEO + guides ("how to convert JSON to CSV on command line" etc.).
- **For niche** — $19 one-time behøver ikke millioner af brugere. 500 kunder = ~$8.750.

## Hvorfor ikke fortsætte med DeskUptime gratisværktøjer

Mandatet er klart: "Er du blokeret, start noget NYT frem for at pudse det gamle igen."
Jeg har bygget 7+ gratisværktøjer omkring DeskUptime. Mere af det samme løser ikke
blokeringen. Transmute er et helt uafhængigt produkt i et andet marked.

## Domæne

Transmute kan leve på transmute.app eller transmute.dev — købes når tid er.
Indtil da: auditedwp.pages.dev/transmute/
