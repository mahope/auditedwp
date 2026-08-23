# STATUS — Iteration 131 (23. august, nat)

## 1. Universalitet (punkt 1) — vurderet igen, bestået

DevNotify-kernen (`providers.rs`) tager token+provider; GitHub/GitLab er
adapters. Sitet er statisk HTML uden CMS. **Ikke bundet til én platform,
intet at trække ud.**

## 2. Nyt denne iteration

- Ny guide: `/guides/github-notifications-not-working-iphone/`
  ("github notifications not working iphone" — 5 reelle årsager: per-repo
  watch settings, global read-markering, iOS Focus/Scheduled Summary, forkert
  konto, Background App Refresh) med CTA.
- Deployet og verificeret: ny side 200, forside og sitemap indeholder den.
- Commit `e7895f9` pushed.

## 3. Blokeringer (én linje hver)

1. LS API-nøgle (Bitwarden unauthenticated) → checkout kan ikke åbnes.
2. Domæne getdevnotify.com venter på Registrar/Mads.

## 4. Traction

**0** betalende · **$0** revenue · **0** rigtige tilmeldinger.

## 5. Venter på Mads

1. LS-nøgle → checkout + ende-til-ende købstest (én kommandokæde klar).
2. Domæne via Cloudflare Registrar.
3. Ja/nej til Product Hunt- og Show HN-teksterne i `devnotify-site/LAUNCH.md`.

## 6. Næste iteration

Nøgle: LS-produkt via API + live checkout + købstest.
Uden nøgle: næste long-tail-side eller sammenligningsside indtil checkout
kan åbne.
