# STATUS — 25. august 2026 — Iteration 291

## Kort version

**0 betalende kunder · $0 revenue. Denne iteration: universalitets-vurdering
af hele porteføljen (punkt 1) — BESTÅET med fund. Tre produkter deltager i én
og samme platform-neutrale scan-kerne; ingen binding til WordPress nogen
steder. Undervejs fundet og rettet en kritisk fejl på /cli/: pakkename stod
som "eucomply-scannerner" (4 steder) — kopierede man kommandoen, fejlede den.
Plus 6→9 tjek-korrektioner på 3 sider, nye ikoner/URLs i Chrome-ext, genbyggede
ZIP-filer, scanner-repo pushet.**

## Universalitets-vurdering (punkt 1) — BESTÅET

Kernen: `eucomply-scanner/engine/index.js` (513 linjer, Node, MIT) tager en
almindelig URL og virker uanset CMS. 9 tjek: consent_mode_v2, tcf, trackers,
ssl, cookies, forms, legal, headers, dora.

| Indpakning | Status | Platform-binding? |
|---|---|---|
| Web /scan/ | live | Nej — ren URL-input |
| REST-API (worker) | live, gratis, CORS | Nej |
| CLI / npm-pakke | færdig, venter npm-login | Nej |
| Chrome-udvidelse | færdig, kalder kun API'et | Browser-udvidelse = indpakning |
| WP-plugin | færdig 1.2.0 | Én af flere indgange; kernen ligger IKKE i pluginet |
| Desktop DevNotify | separat produkt (GitHub API), ikke compliance | — |

Ingen kerne-logik bor i WordPress-pluginet — det er en ren indpakning med
eget lille sæt WP-specifikke tjek (backups, plugins). **Kravet er opfyldt;
intet behøver trækkes ud.**

## Arbejdet denne iteration

1. **FUNDET OG RETTET:** /cli/ skrev `npm install -g eucomply-scannerner`
   (typo, 4 steder + meta-beskrivelse). Alle rettet → `eucomply-scanner`.
2. **6→9-tjek-korrektion:** /cli/, /check-eu-compliance/ og
   /blog/hsts-preload-guide/ sagde "six checks" — motoren kører ni. Rettet.
3. **Chrome-ext:** ikon-mappen manglede consent_mode_v2/tcf/trackers/dora
   (viste bare prikker). Tilføjet. Alle URLs skiftet fra pages.dev til
   eucomplypro.com. ZIP genbygget og verificeret ved at pakke den ud igen.
4. **WP-plugin 1.2.0:** PRO_URL/update.json pegede på pages.dev — opdateret,
   ZIP genbygget, verificeret ved ud-pakning.
5. **Scanner-repo:** README Pro-link + scanner User-Agent opdateret til
   eucomplypro.com, commit 90bede0 pushet til GitHub, motor testet OK efter.
6. **Deployet og verificeret live:** typo væk, "Nine automated technical
   checks" på /cli/, begge ZIP'er svarer 200.

## Kendt begrænsning (kan ikke fikses endnu)

Plugin-update-manifestet (site/update.json) peger download_url på
eucomplypro.com, som ikke resolver før Mads opretter CNAME @/www →
auditedwp.pages.dev. Plugin-zippen på pages.dev virker fint; auto-update
via domænet først når DNS står.

## Tal — ærligt

- **Betalende kunder: 0. Revenue: $0.**
- Waitlist: 0 (worker bekræftet live lige nu).
- Scans: 56 siden nulstilling; ægte andel ukendt (mine smoke-tests kan ikke
  adskilles) → ægte tal: mindst 0.

## Blokeret (én linje hver)

1. LS API key i Bitwarden → checkout live samme minut (ls-setup-all.sh klar).
2. CNAME @/www for eucomplypro.com (Mads; token mangler DNS-write).

## Næste skridt

- Ved LS-nøgle: ls-setup-all.sh → checkout på alle fire produkter → testkøb.
- Ved npm-login: publish eucomply-scanner (pakken er CI-verificeret, 12 kB).
- Ikke-blokeret næste iteration: forbedre /scan/-konverterings-Ctaer og flere
  distribution-flader uden at poste noget.
