# STATUS — 25. august 2026 — Iteration 286

## Kort version

**0 betalende kunder · $0 revenue · 0 rigtige brugere. Denne iteration: intern
linkning mellem indhold og købs-sider — 17 af 31 blogindlæg havde NUL links til
/pro/vs/-salgssiderne, og de 5 /vs/*-sider fik kun links fra én side hver.
Retttet: alle 31 blogindlæg linker nu til en relevant vs-side, deployet og
verificeret live.**

## Fundet og rettet denne iteration

1. **Internt link-hul (vigtigste fund):** 17 blogindlæg (alle DORA-, NIS2-, EAA-,
   Webflow/Squarespace/Magento/BigCommerce-guides m.fl.) havde ingen links til
   /pro/vs/* — læseren kunne ikke komme fra indholdet til salgssiden. Tilføjet
   en naturlig sammenlignings-paragraf med kontekstuel vs-side i hvert indlæg.
2. **Dækning nu:** vs-termly 20 links, vs-cookiebot 17, vs-osano 10,
   vs-iubenda 10, vs-onetrust 3 (fra blog + kryds-links).
3. Alle 8 /vs/*-sider havde allerede Pro-links — ok.
4. Deployet (207 filer) og curl-verificeret live på 5 stikprøver: pro/vs-links
   serveres i det udgivne HTML.

## Universalitets-vurdering

BESTÅET tidligere (iter 283–285): kernen `shared/scan-engine.js` er platform-
neutral. Ingen ny vurdering nødvendig denne iteration.

## Tal — ærligt

- **Betalende kunder: 0. Revenue: $0.** Waitlist-tæller: 0.

## Blokeret (én linje hver)

1. LS API key i Bitwarden → opret produkter + checkout_urls samme minut.
2. CNAME @/www → eucomplypro.com løser ikke offentligt endnu (DNS-write).
3. npm-login → publish af eucomply-scanner CLI.

## Næste skridt

- Ved LS-nøgle: produkter via skrive-API, testkøb, checkout_urls.
- Ved Mads' ja: lanceringstekster postes (site/LAUNCH-EUCOMPLY.md).
- Næste ikke-blokerede arbejde: overveje om vs-onetrust fortjener flere
  indgange (kun 3), ellers ny distribution-kanal der ikke kræver Mads.
