# DECISION — 25. august 2026 — Fokus: EUComply (data-drevet)

## Beslutning: B (byg) — men konsolider til ÉT produkt

**Vælg det produkt der HAR data.** EUComply har 28 scanninger. Regex Tester har 0. Data er ikke smuk, men det er det eneste signal vi har — og signalet siger EUComply.

## Hvorfor EUComply vinder på de fem pengekriterier

| Kriterie | EUComply Pro ($79/yr) | Regex Tester ($2/mo) |
|----------|----------------------|---------------------|
| Hvor hurtigt betaler første kunde? | ⏳ LS key = 1 dag forsinket. Når den kommer: <5 min | ⏳ Samme LS key-blokering |
| Hvor stort beløb? | **$79/yr** — én Pro-sale dækker 4 Regex-år | $2/mo = $19/yr |
| Hvor mange kunder realistisk? | 28 scanninger = 28 leads. 1% konvertering = $79 | 0 brugere. Skal starte fra 0 |
| Tilbagevendende indtægt? | $79/yr abonnement | $19/yr abonnement |
| Leveringsomkostning? | Worker = ~0 kr (Cloudflare gratis) | ~0 kr (statisk HTML) |

EUComply vinder på **beløb pr. kunde** og **eksisterende traction**. 28 mennesker har allerede brugt værktøjet. Det er 28 gange flere end Regex.

## Hvad det betyder i praksis

1. **Stop Regex content production** — lad de 4 sider stå, men brug ikke flere iterationer på nye guides
2. **Fokusér al byggetid på EUComply** — gør landingssiden klar til at konvertere når LS kommer
3. **Forbered preorder/notify-mekanisme** — så når LS key kommer, kan vi sende én besked til 28 scanning-brugere

## Hvad kan slå det ihjel

- LS key kommer aldrig — så har vi intet. Men det er sandt for ALLE produkter
- Compliance-markedet kræver tillid — $79/yr er et større commitment end $2/mo
- 28 scanninger er små tal — 0 konverteringer ville være et signal om at produktet ikke matcher markedet

## Hvorfor valgt frem for alternativer

| Alternativ | Hvorfor ikke |
|------------|-------------|
| Regex Tester | 0 brugere, lavere beløb, commodity-marked |
| QuickFormat ($9) | 0 brugere, én gang betaling, ingen tilbagevendende indtægt |
| DevNotify (CWS) | Blokeret på CWS credentials (samme BW) |
| Nyt produkt | Alle kræver LS key til betaling — ingen fordel |

## Domæne

Foreløbigt: **auditedwp.pages.dev** (fungerer). Foreslået domæne: **eucomplypro.com** (allerede tilføjet til Pages iflg. memory). Kør på Pages-adressen indtil videre.

## Universality

✅ Bekræftet — alle produkter er platform-uafhængige. Ingen refaktoring nødvendig.