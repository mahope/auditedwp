# BUILD.md — EUComply: korteste vej til første betalende kunde

Opdateret 26. august 2026. Produktet er **universelt** (URL ind, resultat ud — alle CMS).
WordPress-pluginet er kun én af flere indgange, ikke produktet.

```
TRIN   HVAD                          STATUS
─────  ────────────────────────────  ──────────────────────────
 1     Landingsside + gratis scan    ✅ LIVE (eucomplypro.com)
  2     Universal scan-Worker         ✅ LIVE (eucomply-scan, 9 checks)
  3     Pro-side med pris + FAQ       ✅ LIVE (/pro/, 79 USD pr. websted pr. år)
  4     Pro-dashboard-demo           ✅ LIVE (illustrativ, ikke kundelog)
 5     Monitoring-beta               ✅ ÅBEN, ikke Pro / ikke kobnet til køb
 6     Blog/SEO (17 artikler)        ✅ LIVE
 7     Checkout via Stripe           ✅ LIVE (betalingslinks, 24/9-26)
 8     Første betalende kunde        ⏳ Timer efter trin 7
```

## Købsrejsen (bygget og optimeret)

1. Besøgende lander på /scan/ (organisk søgning eller blog-link)
2. Scanner sit site → får sin egen score + fejl-liste
3. Resultat-CTA er **personlig**: nævner antal fundne problemer og hvad Pro gør ved netop dem
4. Klik til /pro/ → pris på 5 sekunder (79 USD pr. websted pr. år), kun nuværende WordPress-fordele og illustrativ dashboard-demo
5. "Buy Pro" → Stripe-betalingslink (statisk i siden) → licensnøgle fra Stripe og validering via mahope.tools

## Betaling og licens (24/9-26)

Tidligere Lemon Squeezy; nu Stripe. Købsknapperne er faste Stripe-betalingslinks
direkte i HTML'en (se `business/planer/2026-09-24-stripe-kontrakt.md`).
`tools/apply_shell.py` lader links til buy.stripe.com/donate.stripe.com stå.
WordPress-pluginet validerer nøgler mod `https://mahope.tools/api/license/`.

## Ikke bygget endnu (bevidst)

- Bulk/agency-prisning — version 2, når der er betalende kunder
- Flere sprog — version 2
