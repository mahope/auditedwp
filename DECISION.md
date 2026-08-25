# DECISION — 28. august 2026 — DeskUptime: Desktop website monitor

## Ærlig revurdering

Efter 399 iterationer i compliance-nichen: **0 salg, 2 ægte scans.** Signalet er klart.
Mads' nye mandat er krystalklart: "Tjen så mange penge som muligt, så hurtigt som muligt."
og "Et beboet marked med bevist betalingsvilje slår et tomt marked."

Jeg pivoterer til et marked med PROVEN DEMAND.

## Hvad: DeskUptime — Desktop website monitor

| | |
|---|---|
| **Produkttype** | Tauri desktop app (Mac + Windows) |
| **Målgruppe** | Webdevelopere, freelancere, små teams der vil overvåge websites |
| **Problem** | Uptime-monitorering SaaS koster $10-50/md. En desktop app gør det samme uden løbende serveromkostninger — én gang betalt |
| **Pris** | **$19 one-time** via LS license key (3 aktiveringer) |
| **Platform** | salg via LS checkout (klar når key kommer) |
| **Indtjeningsmodel** | LS licensnøgle — $19 × 70% = ~$13/køb. Billigere end 2 md SaaS |
| **Bygge nu** | Gratis version på GitHub + distribuer via npm/Homebrew. Pro via LS key |

## Hvorfor det her produkt vinder

Alle 5 kriterier:

| Kriterie | Vurdering |
|---|---|
| **Hvor hurtigt betaling?** | **Samme dag LS-key kommer.** LS har licenskey API. Jeg opretter produkt, variante, og checkout-link på 10 min. |
| **Hvor stort beløb?** | $19 one-time. Compared: UptimeRobot Pro = $7/md ($84/yr). Pingdom = $12/md ($144/yr). Desktop app er 3-7x billigere over 2 år. |
| **Hvor mange kunder?** | MILLIONER bruger SaaS uptime tools. Desktop = differentiering for prisbevidste udviklere. |
| **Tilbagevendende indtægt?** | One-time, men nye features kan sælges som v2 opgraderinger. Og hver kunde anbefaler til kolleger. |
| **Leveringsomkostning?** | **$0.** Tauri app, gratis hosting på GitHub, LS betaler sig selv. |

## Hvorfor valgt frem for alternativer

| Alternativ | Hvorfor ikke |
|---|---|
| **CLI tool (html→md)** | Gratis alternativer er gode nok — Turndown, Pandoc. Svært at overbevise om betaling. |
| **CodeCanyon tool** | Kræver author account → Mads. Samme blocker. |
| **KDP ebook (compliance)** | Stadig god idé, men kræver Mads' manuelle upload. |
| **Nu EUComply Pro** | 0 salg. 2 scans på måneder. Signalet er at markedet ikke er der. |
| **VS Code extension** | Kræver publisher account → Mads. |
| **SaaS (betalingsvæg)** | Kræver LS key — som jeg ikke har. Desktop app kan bygges og distribueres gratis NU. |

## Hvad kan slå det ihjel

- LS key kommer aldrig — men jeg bygger nu OG distribuerer gratis version (ingen betalingsvæg)
- Desktop app markedet er smalt — men SaaS-monitorering er et MASSIVT marked, selv en lille % er nok
- Nogen laver allerede en gratis desktop uptime checker — tjekkes under bygning
- Tauri bundling er kompleks på Windows — kræver testing

## Domæne

Ikke nødvendigt. Distribueres via:
- GitHub (gratis CLI/desktop app)
- npm (CLI-only)
- LS checkout link (betalt version)
- Produktside på auditedwp.pages.dev/deskuptime/

## Byggeplan (BUILD.md)

1. Byg Tauri desktop app: URL monitorering, ping, SSL tjek, notifikationer
2. Byg kernelogik i JS/TS (platformuafhængig)
3. Tauri wrapper + system notifications
4. Gratis version: 3 URLs, basic checks
5. GitHub release med binaries
6. Når LS key kommer: opret produkt + license key variant, byg unlock-flow
7. Produktside med priser, features, download