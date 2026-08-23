# STATUS — Iteration 130 (23. august, nat)

## 1. Universalitet (punkt 1) — bestået

DevNotify-kernen (`providers.rs`) tager token+provider; GitHub/GitLab er
adapters. Sitet er statisk HTML, ingen CMS-afhængighed. **Intet at trække ud.**

## 2. Nyt denne iteration

- Ny SEO-guide: `/guides/github-email-notifications-not-working/`
  ("github email notifications not working" — 6 reelle årsager: uverificeret
  mail, spam-markering, per-kanal settings, custom routing-mail, corporate
  filtre, push-forventning) med CTA. Linket i nav + sitemap.
- Deployet til Cloudflare Pages og verificeret: forside + ny guide + sitemap
  viser nyt indhold; alle 9 URL'er svarer korrekt (DMG'er inkluderet).
- Bemærkning: `deploy.sh` uden argument udgiver mappen `site` (EUComply) —
  DevNotify deployes med `./deploy.sh devnotify-site`. Rettet ikke i scriptet,
  bruger bare den korrekte form.

## 3. Blokeringer (én linje hver)

1. LS API-nøgle fra Bitwarden (session unauthenticated) → checkout live.
2. Domæne getdevnotify.com venter på Registrar/Mads.

## 4. Traction (worker-metrics, ikke egne tests)

**0** betalende · **$0** revenue · **0** rigtige tilmeldinger.

## 5. Venter på Mads

1. LS-nøgle (Bitwarden) → én kommandokæde sætter checkout live.
2. Cloudflare Registrar-adgang → domæne.
3. Ja/nej til Product Hunt- og Show HN-teksterne i `devnotify-site/LAUNCH.md`.

## 6. Næste iteration

1. Nøgle modtaget: LS-produkt via API + checkout-link på `/` + ende-til-ende
   købstest.
2. Uden nøgle: næste long-tail-side ("github notifications not working iphone"
   eller "turn off github email notifications") indtil checkout kan åbne.
