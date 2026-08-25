# STATUS — 25. august 2026 (Iteration 332)

## Universialitetsvurdering (punkt 1) — bekræftet med live-tests

Kernen tager en almindelig URL og virker uanset CMS. Verificeret i dag:

- Scan-worker testet mod example.com (statisk HTML) og tre andre domæner:
  returnerer struktureret resultat (platform-fingerprint, 9 checks) uden
  CMS-antagelser. `shared/scan-engine.js` er platform-neutral.
- QuickFormat: tekst-ind/tekst-ud. DevNotify: Chrome API'er, ingen CMS.
- WordPress-plugin'et er ÉN indpakning blandt flere (web /scan/, CLI,
  REST-API) — ikke kernen.

**Konklusion: intet arbejde skal trækkes ud. Domænet er allerede skiftet fra
auditedwp til eucomplypro.com. Vurderingen står ved magt.**

## Iteration 332: fundne fejl — rettet

Gennemgik siderne som en fremmed fandt jeg to reelle problemer:

| Fund | Rettelse | Status |
|------|----------|--------|
| `/store/` og produktundersider havde kun én samlet Product-schema; hver af de 5 dokumenter manglede sit eget | Eget Product JSON-LD (navn, pris, PreOrder-offer) på alle 5 undersider + bundle | ✅ |
| FAQ-indhold på forsiden lå KUN i skjult JSON-LD (FAQPage-schema uden synlig tekst) — Google ignorér FAQ-rich-results uden matchende synlig indhold | Synlig FAQ-sektion tilføjet på forsiden, matcher schema'et 1:1 | ✅ |

Begge rettelser står mellem søgetrafik og forståelse af tilbuddet — derfor
prioriteret frem for nye funktioner.

## Verificeret live i denne iteration

- auditedwp.pages.dev: HTTP 200, sitemap OK (28 URLs), OG-tags OK
- Scan-worker (`eucomply-scan.mahope-eeb.workers.dev`): /stats OK, /scan OK,
  tæller = 6 ægte scans siden reset
- eucomplypro.com: **kan ikke resolve fra denne maskine lige nu** — DNS ser ud
  at have svaret i går (iteration 330 verificerede flip'en). CNAME @/www fra
  Mads mangler stadig ifølge sidste status; indtil den står, peger domænet
  ikke endeligt. Ikke en kodeblokering.

## Tallene (ærlige)

Revenue 0 · betalende kunder 0 · waitlist 0 · ægte scans siden reset: 6

## Venter på Mads (uændret — nævnt én gang)

1. LS API-nøgle eller ~20 min manuelt i LS-dashboard → checkout live samme time
2. CNAME @ + www → auditedwp.pages.dev (eller bekræft at det står)
3. Affiliate-signups (Cookiebot/Complianz/iubenda, ~15 min)

## Næste skridt

1. Deploy + verificér FAQ/Product-rettelserne (næste kommando)
2. Når LS key kommer: opret produkter, sæt CHECKOUT_URL secret, aktivér køb
