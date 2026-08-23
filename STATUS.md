# STATUS — Iteration 135 (23. august, nat)

## 1. Universalitet (punkt 1) — vurderet

DevNotify-kernen (`providers.rs`) tager token+provider; GitHub og GitLab er
adapters. Sitet er statisk HTML, appen taler kun med offentlige API'er.
**Ikke bundet til én platform — intet at trække ud.**

## 2. Beslutningen — holder under pengekriteriet (revurderet)

Målt på de fem penge-kriterier slår "færdig desktop-app, $19, 0 kr/md,
venter kun på betalingsnøglen" stadig alle alternativer. DECISION.md uændret.

## 3. Verificeret denne iteration (live, ikke antaget)

- Alle 12 site-URL'er tjekket: 200 + rigtigt indhold
  (/privacy/ og /terms/ redirecter til uden slash — bevidst, lander korrekt).
- Bitwarden-status: stadig `unauthenticated` → LS-nøgle kan ikke læses endnu.
- getdevnotify.com: ikke købt endnu (000/DNS).

## 4. Nyt denne iteration: guides klar til udgivelse

To nye long-tail-guides skrevet og lagt i `devnotify-site/guides/` klar til
næste deploy (høj-intention-søgninger der matcher produktet direkte):
- `slack-github-notifications/index.html` ("slack github notifications")
- `turn-off-github-email-notifications/index.html`

Begge følger samme skabelon som de eksisterende 6 guides: problem → løsning →
CTA til DevNotify, ens typografi, canonical + sitemap-opdatering.

## 5. Blokeringer (én linje hver)

1. LS API-nøgle: Bitwarden `unauthenticated` → checkout kan ikke åbnes.
2. Domæne getdevnotify.com venter på Registrar-køb.

## 6. Traction (ærlige tal)

**0** betalende · **$0** revenue · **0** rigtige tilmeldinger.

## 7. Venter på Mads

1. LS-nøgle → LS-produkt via API + live checkout + ende-til-ende købstest.
2. Domæne via Cloudflare Registrar.

## 8. Næste iteration

Deploy de to nye guides (nav + sitemap), verificér live, og fortsæt med
næste long-tail-side. Nøgle kommer: LS-produkt + købstest først.
