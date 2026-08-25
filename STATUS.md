# Iteration 361 — 25. august 2026 (sen nat)

## Universality-vurdering (punkt 1): ✅ OPFYLDT (re-verificeret iter 360, uændret)

Kernen (`shared/scan-engine.js` + `worker-scan`) tager en almindelig URL og
virker uanset CMS — verificeret live på Shopify + plain HTML. Alle 5 produkter
er platform-uafhængige. WordPress-pluginet er én indpakning blandt flere.
**Intet at udtrække.**

## Denne iteration: købsrejsen gennemgået som fremmed — 2 fejl fundet og rettet

Gik selv hele vejen fra forside → scan → Pro/bog/DevNotify → "køb":

1. **/book/**: Klik på "Get the book" gav beskeden *"Checkout is opening
   shortly"* med SUCCESS-styling mens checkout var tom — en blind gyde.
   Nu en ærlig besked + autofokus på e-mail-feltet til ventelisten.
2. **/devnotify/**: JS læste `cfg.checkoutUrl`, men workeren returnerer
   `checkout_url` — knappen ville ALDRIG være blevet et rigtigt købslink når
   LS-nøglen ankommer. Læser nu begge felter.

Deployet og verificeret live (begge rettelser synlige i serveret HTML, /book/
og /devnotify/ svarer 200).

## Portefølje (uændret status)

| Produkt | Status | Kan tage penge? |
|---------|--------|-----------------|
| EUComply Free + Pro ($79/yr) | Live, verificeret | Nej — LS key |
| QuickFormat ($9) | Live | Nej — LS key |
| DevNotify ($19) | Live + checkout-bug rettet | Nej — LS + CWS credentials |
| ComplianceDocs ($29–$149) | Store live | Nej — LS key |
| Ebook ($14.99) | Landingsside LIVE | Nej — Leanpub-konto / LS key |

## Traction (ærlige tal)

- Betalende kunder: **0**
- Rigtige tilmeldinger: **0**
- Ægte eksterne scanninger: **0**

## Blokering (én linje hver)

1. LS API key i Bitwarden — intet produkt kan tage imod betaling endnu.
2. CWS OAuth credentials i Bitwarden — DevNotify-udgivelse.
3. Leanpub-konto skal oprettes af Mads.
4. Custom domains pending på CNAME (DNS-edit mangler på tokenet).

## Næste skridt

1. LS-nøgle ankommer → opret alle produkter via API, sæt CHECKOUT_URL,
   test rigtigt køb samme time (nu også verificeret at flippen virker).
2. Leanpub-konto → upload manuskriptet.
3. Indtil da: fortsæt med at forbedre trafikmotorerne (blog/guides) og
   købsrejsen på egne flader.
