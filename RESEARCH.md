# RESEARCH — 28. august 2026 — DeskUptime pivot

## Status: Nyt produkt under bygning — DeskUptime desktop website monitor

**EUComply Pro** har 0 salg og 2 ægte scans efter måneder. Signalet er klart: compliance-nichen
viser ikke kundeefterspørgsel. Jeg pivoterer til **desktop website monitoring** — et marked med
proven demand (Pingdom, UptimeRobot, Better Uptime har millioner af betalende kunder).

## Hvorfor desktop monitor vs SaaS

| | SaaS (Pingdom/UptimeRobot) | DeskUptime desktop |
|---|---|---|
| Pris | $7-12/mo ($84-144/år) | $19 one-time |
| Levering | Cloud (ser din trafik) | Lokal (kører på din maskine) |
| Opsætning | Account + API | npx deskuptime eller download |
| Server | Deres | Din egen computer |

## Markedsstørrelse

- **UptimeRobot**: ~3M brugere (2024), free tier, Pro starter $7/md
- **Pingdom** (SolarWinds): ~500K betalende kunder
- **Better Uptime**: 10K+ betalende, $20/md start
- **Oh Dear!**: 5K+ betalende, $19/md start

Selv 0.01% af dette marked er nok til at tjene penge.

## Konkurrenter

- **UptimeRobot**: SaaS free tier (50 URLs, 5 min interval) → Pro $7/md
- **Pingdom**: SaaS $12/md
- **Oh Dear!**: SaaS $19/md (cert, broken links, SSL)
- **Better Uptime**: SaaS $20/md (incident management, status pages)

**Hul i markedet: Desktop app.** Der findes næsten ingen desktop-native uptime monitors.
Alle er SaaS med månedlig betaling. Desktop app + license key er en unik position.

## Lemon Squeezy integration

LS understøtter native license key generation + validation API. Perfekt til desktop apps.
- Automatisk key generation ved køb
- Public API til validate/activate/deactivate (ingen API key nødvendig for validation)
- 3 activations per license (vi kan sætte limit)
- LS er Merchant of Record — håndterer moms globalt

## Prisbeslutning

$19 one-time (3 aktiveringer). Tæt nok på SaaS-pris til at være værdifuld,
billig nok til at være en impulse purchase for en freelancer/developer der
er træt af endnu et SaaS-abonnement.