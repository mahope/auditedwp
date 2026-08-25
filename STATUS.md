# STATUS — 29. august 2026 — Iteration 287

## Kort version

**0 betalende kunder · $0 revenue · 0 rigtige brugere. Denne iteration:
universalitets-vurdering BESTÅET (6. gang) + fundet og rettet en rigtig fejl:
/pro/vs-onetrust/ fandtes ikke, men 3 blogindlæg og sitemap-tilstand pegede på
den — Cloudflare-fallbacken serverede /pro/-siden med HTTP 200, så fejlen var
usynlig i sidste iterations "verificering". Siden er bygget, deployet og
live-verificeret.**

## Universalitets-vurdering (punkt 1 fra Mads)

**BESTÅET.** Kernen `shared/scan-engine.js` tager en vilkårlig URL og laver 9
checks uden CMS-formodninger. WordPress nævnes kun som én post i den
informativt fingerprint-check (linje 108) sammen med Shopify/Wix m.fl.
Ingen wp-json-afhængigheder, ingen install-på-server-krav. WordPress-guides på
bloggen er indhold/distribution, ikke produktbundet. Ingen ændring nødvendig.

## Fundet og rettet denne iteration

1. **Blindt link / skjult 404:** /pro/vs-onetrust/ eksisterede ikke lokalt,
   selvom iter 286 byggede de fire andre pro/vs-sider. Tre blogindlæg
   (dora-compliance-guide, dora-nis2-gdpr-differences, dora-for-ecommerce-2026)
   linker til den; Cloudflare fallback serverede /pro/-siden med status 200,
   så curl-tjekket i iter 286 fangede det ikke.
2. Bygget site/pro/vs-onetrust/index.html i samme design/tone som de andre fire
   (ærlig sammenligning, pris-tabel, honest-limits-boks).
3. Tilføjet til sitemap.xml (nu 136 URLs) + OneTrust-kryds-link i alle fire
   eksisterende pro/vs-footere.
4. Deployet og verificeret live: ny side serverer rigtig title; alle 4 gamle
   sider linker nu til vs-onetrust; sitemap indeholder den.

Lærning noteret: HTTP 200-verificering er ikke nok — fallback-side kan maskere
manglende filer. Fremover: sammenlign titel/canonisk URL mod forventet side.

## Tal — ærligt

- **Betalende kunder: 0. Revenue: $0.** Waitlist-tæller: 0.

## Blokeret (én linje hver)

1. LS API key i Bitwarden → opret produkter + checkout_urls samme minut.
2. CNAME @/www → eucomplypro.com løser ikke offentligt endnu (DNS-write).

## Næste skridt

- Ved LS-nøgle: produkter via skrive-API, testkøb, checkout_urls.
- Ved Mads' ja: lanceringstekster postes (site/LAUNCH-EUCOMPLY.md).
- Næste ikke-blokerede arbejde: fuld link-audit af ALLE interne hrefs (samme
  fallback-fejl kan gemme sig andre steder), derefter ny distribution-kanal.
