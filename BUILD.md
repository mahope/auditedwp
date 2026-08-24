# BUILD — Korteste vej til første betalende kunde

Opdateret: 24. august 2026 (mandat-revision)

## Blokering

**Bitwarden er låst (unauthenticated).** Indeholder LS API key — uden den kan intet produkt tage imod betaling.

Indtil blokeringen er løst, arbejder jeg på:
- Bygge trafik (SEO-indhold, guides)
- Gøre alt klar til at flippe sekundet LS key kommer
- Bygge nye produkter der ikke kræver gateway

## Når LS key kommer — tidslinje (minutter, ikke dage)

```
Minute 0:  bw unlock → ls API key
           curl -s LS_API create product "EUComply Pro $79/yr"
           curl -s LS_API create checkout link
           
Minute 5:  ./scripts/eucomply-flip.sh <checkout-url>
           curl -s verify: /config returnerer checkoutUrl
           
Minute 10: curl -s LS_API create product "QuickFormat $9 once"
           curl -s LS_API create checkout link
           ./scripts/quickformat-flip.sh <checkout-url>
           
Minute 15: Test checkout med eget kort
           Første rigtige kunde?
           
Minute 20: npm login → npm publish quick-format
           Chrome Web Store → publish DevNotify extension
```

## Prissætning (klar)

| Produkt | Pris | Model | LS klar? |
|---------|------|-------|----------|
| EUComply Pro | $79/år | Recurring (abonnement) | ❌ venter på key |
| QuickFormat | $9 once | One-time | ❌ venter på key |

## Distribution der er klar til at blive skudt af

| Kanal | Produkt | Status | Kræver |
|-------|---------|--------|--------|
| Produktside (CLOUDFLARE) | Alle | ✅ Live | LS key |
| CLI (npm) | QuickFormat | ✅ Code klar | npm login |
| Chrome Web Store | DevNotify | ❌ Blokeret | CWS credentials (Bitwarden) |
| Mac App Store | QuickFormat | ❌ Ikke bygget | $99/år, Mads godkendelse |