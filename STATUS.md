# STATUS — Iteration 395 — 27. august 2026

## Udført

1. **Universalitetsvurdering (punkt 1): BEKRÆFTET** — Kernen `shared/scan-engine.js` tager enhver URL. Ingen CMS-forudsætning. Verificeret live på Shopify, Webflow, Squarespace, Wix, Apple, Craigslist. /stats viser 2 ægte eksterne scans.

2. **Lancering af EUComply domæne:** 160 filer opdateret fra `auditedwp.pages.dev` → `eucomplypro.com` (alle canonical, links, sitemap, meta, JS). Deployeret og verificeret — 0 resterende forekomster af `auditedwp.pages.dev` i `/site/`.

3. **/book/ konverteringsforbedring (punkt 5, niveau 1):**
   - **Før:** ventelisteform dukkede KUN op efter klik på købsknap → fejl. Besøgende så aldrig mulighed for at efterlade email uden at klikke først.
   - **Efter:** ventelisteform altid synlig med tydelig CTA. Købsknap bliver til rigtigt checkout-link når LS key sættes (runtime). Social proof: waitlist-count hentes fra worker. KDP Amazon-link tilføjet for prisbevidste købere.

4. **/store/ HTML fix:** Fjernet stray `<footer>`-tag. Fjernet `data-checkout` attribut (forældet). Grammatikfix.

5. **Structured data fix:** `https://***@type` (ødelagt) rettet til `https://schema.org","@type"` i JSON-LD.

6. **BUILD.md** opdateret med korteste vej til betaling.

## Produktstatus

| Produkt | Status | Salg | Blokeret på |
|---------|--------|------|-------------|
| EUComply Pro ($79/yr) | Live, købsflow klar | **0** | LS checkout-URL |
| Ebook PDF ($14.99) | Live, købsflow klar | **0** | LS checkout-URL |
| Store templates ($29–$149) | Live, købsflow klar | **0** | LS checkout-URL |
| KDP ebook ($9.99) | Manuskript + cover klar | 0 | Mads uploader manuelt |

## Blokeringer (én linje hver)

1. LS API key (Bitwarden) — forventet 24. august, stadig ikke kommet
2. eucomplypro.com CNAME — token mangler DNS-edit
3. KDP upload — manuskriptet er færdigt, venter på Mads

## Næste skridt

- Fortsæt med forbedringer der kan trække besøgende til (punkt 5, niveau 3)
- Overvej nyt produkt der slet ikke kræver LS key eller Mads — jf. "start noget NYT"