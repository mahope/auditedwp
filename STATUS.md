# STATUS — Iteration 115 (23. august 2026, nat)

## 1. Universitets-vurdering (punkt 1) — bestået (bekræftet igen)

DevNotify er ikke platform-bundet: kernen er notifications-API → normaliseret
liste → menu bar UI + polling. GitHub er én adapter; GitLab/Linear/Jira kan
lægges ind uden kerne-ændring. Ingen udtrækning nødvendig.

## 2. Pengekriteriet (punkt A) — beslutningen holder

DevNotify scorer stadigt højest på de fem pengefaktorer: bygget færdig
(leveringsomkostning 0), $19 lifetime, timer til første kunde SO snart
LS-nøglen ligger i Bitwarden. Ingen af de gamle kasserede idéer slår den på
"hurtigste vej til betalende kunde", fordi de alle kræver ny udvikling FØR de
kan tage imod penge. DevNotify er det eneste produkt der allerede kan levere.

## 3. Bygget denne iteration: 3 nye SEO-indgange mellem søgning og købsside

Det største hul var kun ÉN indgang fra Google. Rettet:

| Ting | Verificeret |
|------|--------|
| /devnotify/best-github-notification-apps-macos/ — "best GitHub notification apps macOS"-siden, ærlig sammenligning af web inbox/email/Gitify/Slack/DevNotify + Article JSON-LD | ✅ 200 live |
| /devnotify/github-token-scopes-guide/ — "GitHub token scopes"-guide med HowTo JSON-LD (matcher et reelt søgebehov fra DevNotify-brugere) | ✅ 200 live |
| vs/gitify fik Article JSON-LD + kryds-links til begge nye sider | ✅ 200 live |
| "Guides" i nav + begge sitemaps opdateret (rod: 4 devnotify-URLs) | ✅ |
| Rod-deploy verificeret: alle URLs 200, DMG stadig 200 (4.45 MB) | ✅ |

Købsrejsen selv er urørt og komplet (pris, trial, FAQ, terms/privacy) — intet
at pudse før LS-checkout kan sættes på knappen.

## 4. Traction (ærligt)

**0** betalende kunder · **0** downloads · **$0** revenue. Ingen analytics på
DMG-downloads endnu.

## 5. Budget

Brugt: **0 kr**. getdevnotify.com forhåndsgodkendt (~90 DKK), venter på køb.

## 6. Venter på Mads (uændret — nævnes ikke igen før noget bevæger sig)

LS API-nøgle (Bitwarden) = ENESTE revenue-blokering. Domænekøb + ja til posts
ligger også klar.

## Næste iteration

1. LS-nøgle → opret produkt $19 via API → checkout-URL i buy-btn → remote
   licensvalidering i app'en → genudgiv.
2. Cloudflare Web Analytics på devnotify-siderne så download-tallet bliver
   målbart (gratis, ingen cookies).
3. Flere søgeindgange ("github notifications widget mac", "tauri menu bar app").
