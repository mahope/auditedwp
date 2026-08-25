# STATUS — Iteration 394 — 27. august 2026

## Universalitetsvurdering (punkt 1): ✅ OPFYLDT — ingen udtrækning nødvendig

Kernen er `shared/scan-engine.js` (kør i eucomply-scan workeren). Den tager en
almindelig URL og laver 9 compliance-checks på den offentlige HTML — ingen
CMS-forudsætning, intet plugin, ingen serveradgang. Live-verificeret på
Shopify, Webflow, Squarespace, Wix, Apple, Craigslist. /stats viser 2 ægte
eksterne scans (craigslist.org, wix.com).

Indpakninger omkring kernen: WordPress-plugin, CLI, Chrome-udvidelse, /scan-
siden, blog-guiderne. Alle er valgfri indgange; kernen afhænger af ingen af dem.
**Konklusion: produktet er allerede universelt. Intet arbejde skal ombygges.**

## Hvad denne iteration gjorde (punkt 5: det der trækker folk til)

To store blog-indgange (`best-free-gdpr-compliance-checkers-2026`,
`nis2-compliance-checklist-2026`) manglede "Keep reading"-lænker til andre
guides — besøgende landede i en blindgyde i stedet for at blive på sitet.
Begge har nu en relaterede-guides-blok, deployet og verificeret live (200 +
indhold tjekket). Alle 32 blogposts har nu internt lænkearbejde.

## Produktstatus

| Produkt | Status | Rigtige salg | Blokeret på |
|---------|--------|--------------|-------------|
| EUComply Pro ($79/yr) | Live, købsknappen virker når checkout sættes | **0** | LS checkout-URL |
| eBook PDF ($14.99) | Live, samme mekanisme | **0** | LS checkout-URL |
| Store templates ($29–149) | Live, samme mekanisme | **0** | LS checkout-URL |
| KDP ebook ($9.99) | Manuskript + cover klar | 0 | Mads' manuelle upload |

## Venter på Mads (én linje hver)

1. LS API key (Bitwarden) ELLER 20 min manuelt i LS-dashboard → CHECKOUT_URLS
   på workeren, alt live på under 5 min
2. eucomplypro.com DNS svarer ikke (ingen A/CNAME endnu)
3. KDP-upload (~15 min; book/ er klar)

## Ærlig stilling

Alt bygget, alt verificeret, 0 salg. Én ting står mellem os og indtægt: en
Lemon Squeezy-checkout-URL.

## Næste skridt (mig)

1. Konverteringstest på /book/ og /store/ (punkt 5, niveau 1)
2. Flere SEO-indgangssider til scanneren
3. Nyt produkt uden compliance — først når checkout-flaskehalsen er tømt for løft
