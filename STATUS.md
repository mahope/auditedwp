# STATUS — 25. august 2026 — Iteration 277

## Kort version

**0 betalende kunder · $0 revenue · 0 rigtige brugere · Domæne-migration klar, venter kun på DNS**

## Universalitets-vurdering (punkt 1) — BESTÅET for 8. gang

Scanner-kernen (`eucomply-scanner/engine`) tager en vilkårlig URL og virker
uanset CMS. WordPress-plugin og Chrome-extension er indpakninger, ikke kernen.
Ingen udtrækning nødvendig. Vurderingen står — jeg bruger ikke flere
iterationer på at bekræfte den.

## Denne iteration: domæne-migrationen gjort klar

eucomplypro.com er stadig pending (ingen CNAME endnu). I stedet for at vente:

1. **142 filer migreret**: alle kanoniske links, sitemap.xml (122 URL'er),
   robots.txt, hreflang og interne links peger nu på `https://eucomplypro.com`.
2. **`scripts/switch_domain.py`** med `--revert` — idempotent, kan køres begge veje.
3. **Committed men IKKE deployed.** Grunden: indtil CNAME'en findes, ville
   kanoniske links pege på et domæne der svarer 000 — det broder sitet.
4. Verificeret: eucomplypro.com svarer i dag 000 (ikke live), pages.dev 200.

## Deploy-plan (når CNAME er sat)

1. `./deploy.sh` → sitet lever på begge adresser, kanoniske = eucomplypro.com.
2. Tjek: `curl -s https://eucomplypro.com/ | grep canonical`, spot-tjek 5 undersider,
   sitemap + robots.txt over 200.
3. Search Console-verificering + sitemap-submit (kræver Mads' konto).

## Blokeret (én linje hver)

- LS API key i Bitwarden → `ls-setup-all.sh` sætter checkout på alle 4 produkter.
- npm-login til publish af eucomply-scanner (pakken færdig, v1.0.0).
- CNAME @/www → auditedwp.pages.dev på eucomplypro.com — eller DNS-write på tokenet.

## Næste skridt

1. CNAME fra Mads → deploy migrationen samme time (plan ovenfor).
2. LS-nøglen → checkout live på /pro/, /devnotify/, /quickconvert/ + stores.
3. Efter lancering: gratis-scan → pro-konversion måles via worker-/stats.
