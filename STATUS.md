# STATUS — Iteration 132 (23. august, nat)

## 1. Universalitet (punkt 1) — vurderet igen

DevNotify-kernen (`providers.rs`) tager token+provider; GitHub/GitLab er
adapters, sitet er statisk HTML uden CMS. **Ikke bundet til én platform,
intet at trække ud.** GitLab-adapteren er i øvrigt nu også kommercialiseret:
ny guide-side målrettet GitLab-brugere.

## 2. Beslutningen revurderet under pengekriteriet — holder

Tjekket konkurrentbilledet live (GitHub API: Gitify stadig eneste reelle,
5.325 stjerner, gratis). Sitet gennemgået som fremmed: alle 10 URL'er svarer
200 med rigtigt indhold, checksums matcher DMG'erne, ingen døde links.
DECISION.md uændret.

## 3. Nyt denne iteration

- Ny guide: `/guides/gitlab-notifications-on-mac/` ("gitlab notifications mac"
  -retningen) med CTA. Nav + sitemap opdateret.
- Deployet og verificeret side for side.
- **Fejl fundet og rettet:** `./deploy.sh` uden argument udgiver mappen `site`
  (gammelt EUComply-projekt) — ikke `devnotify-site`. Korrekt kald er
  `./deploy.sh devnotify-site`. Sitet var kortvarigt EUComply-indhold;
  genudgivet og verificeret som DevNotify igen.

## 4. Blokeringer (én linje hver)

1. LS API-nøgle (Bitwarden unauthenticated) → checkout kan ikke åbnes.
2. Domæne getdevnotify.com venter på Registrar/Mads.

## 5. Traction

**0** betalende · **$0** revenue · **0** rigtige tilmeldinger.

## 6. Venter på Mads

1. LS-nøgle → LS-produkt via API + live checkout + ende-til-ende købstest.
2. Domæne via Cloudflare Registrar.
3. Ja/nej til Product Hunt- og Show HN-teksterne i `devnotify-site/LAUNCH.md`.

## 7. Næste iteration

Nøgle: LS-produkt + købstest.
Uden nøgle: næste long-tail-side eller sammenligningsside.
