# BUILD.md — EUComply: korteste vej til første betalende kunde

Opdateret 26. august 2026. Produktet er **universelt** (URL ind, resultat ud — alle CMS).
WordPress-pluginet er kun én af flere indgange, ikke produktet.

```
TRIN   HVAD                          STATUS
─────  ────────────────────────────  ──────────────────────────
 1     Landingsside + gratis scan    ✅ LIVE (eucomplypro.com)
 2     Universal scan-Worker         ✅ LIVE (eucomply-scan, 7 checks)
 3     Pro-side med pris + FAQ       ✅ LIVE (/pro/, $79/år)
 4     Pro Dashboard                 ✅ LIVE (/pro/dashboard/)
 5     Daily monitoring Worker       ✅ LIVE (eucomply-watch)
 6     Blog/SEO (17 artikler)        ✅ LIVE
 7     Checkout via Lemon Squeezy      ❌ Venter på LS API-nøgle (Bitwarden)
 8     Første betalende kunde        ⏳ Timer efter trin 7
```

## Købsrejsen (bygget og optimeret)

1. Besøgende lander på /scan/ (organisk søgning eller blog-link)
2. Scanner sit site → får sin egen score + fejl-liste
3. Resultat-CTA er **personlig**: nævner antal fundne problemer og hvad Pro gør ved netop dem
4. Klik til /pro/ → pris på 5 sekunder ($79/yr), sammenligningstabel, live dashboard-demo
5. "Buy Pro" → Lemon Squeezy checkout (via CHECKOUT_URL secret på workeren)

## Når LS-nøglen ligger i Bitwarden

Pro-siden henter allerede checkout-URL'en fra workeren. Én handling:

```bash
wrangler secret put CHECKOUT_URL --name eucomply-scan   # = LS checkout-link
```

Knappen skifter automatisk fra waitlist-fallback til direkte checkout.
Samme dag kan første kunde betale. (Alternativt oprettes produktet selv via
LS write-API, når nøglen kan læses.)

## Ikke bygget endnu (bevidst)

- Licensvalidering mod Gumroad API — først når der findes en rigtig nøgle at teste med
- Bulk/agency-prisning — version 2, når der er betalende kunder
- Flere sprog — version 2
