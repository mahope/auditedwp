# BUILD.md — Iteration 395 — 27. august 2026

## Korteste vej til første betalende kunde

| Produkt | Blokeret på | Hvad mangler |
|---------|-------------|--------------|
| EUComply Pro ($79/yr) | LS checkout-URL | Mads frigør LS key → `wrangler secret put CHECKOUT_URL` |
| Ebook PDF ($14.99) | LS checkout-URL | Samme — LS key, en worker-variabel |
| KDP ebook ($9.99) | Mads uploader manuelt | 15 min i KDP dashboard |
| Store templates ($29–$149) | LS checkout-URL | Samme — LS key |

## Hvad er bygget (klar, venter på betaling)

| Område | Status |
|--------|--------|
| EUComply scanner (universel) | ✅ Live — 9 checks, enhver URL |
| /pro/ (salgs-side) | ✅ Pris, features, demo, FAQ |
| /book/ (salgs-side) | ✅ Ventelisteform altid synlig, social proof, KDP-link |
| /store/ (salgs-side) | ✅ 5 produkter, bundle, venteliste |
| 32 blogguides | ✅ Alle med intern linking |
| KDP-manuskript | ✅ 8.945 ord, cover klar |
| EUComply domæne | ✅ eucomplypro.com købt, CNAME stadig blokeret |

## Præcis hvad der skal til for at åbne betaling

1. **Mads:** LS API key → `lemon.js` på /pro/, /book/, /store/ + CHECKOUT_URL på worker
2. **Eller Mads:** Upload KDP manuscript (15 min)
3. Ingen kodeændring på nogen af siderne — de læser checkout URL runtime fra worker /config

## Hvad bygges i ventetiden

- Flere SEO-indgangssider til scanneren (data viser hvad der rangerer)
- /book/ konverteringstests
- Nyt produkt der ikke kræver LS key (under overvejelse)