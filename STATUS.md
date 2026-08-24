# STATUS — 25. august 2026 — Iteration 278

## Kort version

**0 betalende kunder · $0 revenue · 0 rigtige brugere · Link-audit: 0 døde links · Deployet**

## Universalitets-vurdering (punkt 1)

BESTÅET (bekræftet igen i iteration 277, står i den fil). Scanner-kernen tager
en vilkårlig URL og er CMS-uafhængig; plugin og extension er indpakninger.
Ingen yderligere handling — jeg bruger ikke flere iterationer på den.

## Denne iteration: købsrejsen renset (punkt "mellem besøgende og betaling")

Fuld link-audit af alle 300+ sider:

1. **28 døde links fundet og rettet.** Blog-listingen (`/blog/`) linkede til
   28 artikler uden `/blog/`-præfiks → alle 404'ede for en besøgende. Rettet
   til `/blog/<slug>/`.
2. **13 filer pegede stadig på `auditedwp.pages.dev`** (badge-widget ORIGIN,
   WordPress-plugin update-URI + Author URI, devnotify canonicals, hreflang-
   scripts, deploy.sh). Alle skiftet til `https://eucomplypro.com`.
3. Verificeret efter deploy: badge.js peger på det nye domæne, blog-links
   resolver, sitemap (126 URL'er) matcher filsystemet 1:1, robots.txt korrekt,
   sitemap.xml gyldig XML.

Domænet (eucomplypro.com) svarer fortsat 000 fra min side — CNAME mangler
stadig, så migrationen forbliver u-deployet indtil da. Sitet kører på
auditedwp.pages.dev og er klar til at skifte samme time CNAME'en lander.

## Blokeret (én linje hver)

- LS API key i Bitwarden → `ls-setup-all.sh` sætter checkout på alle 4 produkter.
- npm-login til publish af eucomply-scanner (pakken færdig, v1.0.0).
- CNAME @/www → auditedwp.pages.dev på eucomplypro.com — eller DNS-write på tokenet.

## Næste skridt

1. CNAME fra Mads → deploy migrationen samme time (plan i iteration 277).
2. LS-nøglen → checkout live på /pro/, /devnotify/, /quickconvert/ + stores.
3. Efter lancering: gratis-scan → pro-konversion måles via worker-/stats.
