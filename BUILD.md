# BUILD — Korteste vej til første betalende kunde

## Nuværende position

**DevNotify.** App bygget, site live (0,5+1 betaling). 63/63 URL'er 200. Downloads virker.
App har trial/license-aktivering. Blokeret på: betalingsopsætning.

## Valg: Fortsæt DevNotify, byg lille portefølje når betaling er åben

Fortsatte under kriteriet "tjener flest penge hurtigst". DevNotify kræver 0 kr i drift,
kan tage imod $19 per kunde time efter checkout er sat op.

## Den korteste vej — to muligheder

### A. Mads opretter checkout via LS web-dashboard (2 min, ingen API-nøgle)

Dette er hurtigst. Mads logger ind på **https://lemonsqueezy.com** (mads@mahope.dk),
opretter et produkt:

1. **Products → Create product**
   - Navn: `DevNotify License`
   - Slug: `devnotify-license`
   - Beskrivelse: `Lifetime license for DevNotify — GitHub notifications in your macOS menu bar. One payment, perpetual use including updates.`
   - Pris: **$19** (one-time, ingen abonnement)
   - Publiseret ja
2. **Kopier checkout-URL'en** — den ser ud som `https://devnotify.lemonsqueezy.com/checkout/buy/xxx`
3. **Send URL'en** til mig — så flipper jeg sitet på 30 sekunder med:
   ```bash
   python3 scripts/flip_checkout.py <URL>
   ./deploy.sh site
   ```
   Done. Site accepterer betalinger.

### B. Mads logger ind i Bitwarden → jeg gør resten

1. `bw login` eller `bw unlock`
2. Jeg henter LS API key → kører `./scripts/ls-setup.sh` → får checkout URL → flipper

Same result, 3 min mere.

## Efter checkout er live

| Trin | Hvad | Hvem |
|------|------|------|
| 1 | Testkøb $19 på LS-checkouten | Mig |
| 2 | Verificér at licens-nøgle udleveres / app unlocker | Mig |
| 3 | Domæne købes: **getdevnotify.com** | Mads via Cloudflare |
| 4 | Skriv "Lancering" i 1 relevant kanal (Reddit r/macapps; Hacker News "Show HN") | Mig (skriver, Mads godkender) |
| 5 | Fortsæt SEO: titler, guides | Mig |
| 6 | Overvej nyt produkt når 1. betaling er landet | Mig |

## Fremtidige produkter (når DevNotify betaler)

- **CLI-variant** (npm → brew) — gratis kerne, betalt pro ($9/md)
- **Windows build** — Tauri cross-compile, nyt marked
- **EUComply** — compliance tjek, universelt, $79/md
- **Simpelt digitalt produkt** på en markedsplads med indbygget betaling