# STATUS — 25. august 2026 — Iteration 289

## Kort version

**0 betalende kunder · $0 revenue. Denne iteration: universalitets-punkt 1
ikke bare vurderet, men TESTET — kernen scannet live mod Shopify, Webflow,
Squarespace og Next.js, alle fingerprintet korrekt. Desuden fuld
worker-URL-audit af hele sitet: alle 27 API-referencer er live (200).**

## Universalitets-vurdering (punkt 1) — BESTÅET, nu empirisk

Tidligere iterationer har påstået det; denne gang beviste jeg det ved at køre
`eucomply-scanner/cli/eucomply.js` direkte mod fire ikke-WordPress-sites:

| Site | Fingerprintet som | Resultat |
|------|-------------------|----------|
| shopify.com | Shopify | ✅ korrekt |
| webflow.com | Webflow | ✅ korrekt |
| squarespace.com | Squarespace | ✅ korrekt |
| stripe.com | Next.js | ✅ korrekt |

Kernen laver 9 checks uden CMS-formodninger: ingen wp-json-afhængigheder,
intet install-krav. WordPress er ÉN post i fingerprint-checken ved siden af
Shopify/Wix/Elementor — detektion, ikke binding. Pakket platform-neutralt ud
som: (1) web-app, (2) open source npm/CLI, (3) offentlig REST-API.
WordPress-pluginet er én indpakning blandt flere. **Ingen ændring nødvendig.**

## Arbejdet denne iteration

1. **Empirisk kernetest** (ovenfor) — første gang universalitets-kravet er
   bevist med faktiske scans i stedet for en påstand i STATUS.md.
2. **Worker-URL-audit:** grep over hele site/-mappen fandt 27 referencer til
   workers.dev-endpoints på tværs af 17 filer. Alle fire hosts testet live:
   eucomply-scan, waitlist-eucomply, eucomply-watch, devnotify-metrics —
   alle svarer 200. Ingen døde endpoints (i modsætning til sidste iterations
   GitHub-fund).
3. **Launch-tekster verificeret:** API-curl-eksemplet i LAUNCH-EUCOMPLY.md
   peger på den rigtige, virkende URL (200 + gyldig JSON) — fejlen fra
   iteration 288 er ikke gentaget i lanceringsmaterialet.
4. **Købsrejsen tjekket:** /pro henter checkout runtime fra workerens
   /config endpoint (`{"checkoutUrl":"","launchPricing":true}`). Så snart
   CHECKOUT_URL sættes som secret på workeren, går checkout live uden ny
   deploy. Infrastrukturen er klar; der mangler kun LS-nøglen.

## Tal — ærligt

- **Betalende kunder: 0. Revenue: $0.** Scan-tæller: 53 siden nulstilling
  (inkluderer mine egne smoke-tests; ægte brugere kan ikke adskilles endnu —
  tallet er "ukendt, mindst 0").

## Blokeret (én linje hver)

1. LS API key i Bitwarden → opret produkter + checkout_urls samme minut.
2. CNAME @/www for eucomplypro.com mangler DNS-write-adgang (curl giver
   pt. ingen respons på domænet).

## Næste skridt

- Ved LS-nøgle: produkter via skrive-API, testkøb, CHECKOUT_URL-secret sat →
  checkout live uden deploy.
- Ved Mads' ja: lanceringstekster postes (LAUNCH-EUCOMPLY.md er færdig og
  verificeret).
- Ikke-blokeret arbejde videreføres: distribution-forberedelse (dev.to/
  hashnode-artikler ligger klar uden at poste), forbedringer af scan-flow.
