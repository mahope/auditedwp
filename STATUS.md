# STATUS — Iteration 113 (23. august 2026, nat)

## 1. Universitets-vurdering (punkt 1) — DEVNOTIFY

DevNotify er IKKE platform-bundet i den forstand AGENTS.md mener. Kernen er
notifications-API → normaliseret liste → menu bar UI + polling. GitHub-integrationen
er én adapter; GitLab/Linear/Jira kan lægges ind uden ændring af kernen.
**Konklusion: bestået — ingen udtrækning nødvendig.** (Verificeret iter. 111.)

## 2. Færdigt denne iteration: synligheds-hul lukket (mellem besøgende og betaling)

Fandt og rettede et reelt problem: rodsidens sitemap.xml (den eneste robots.txt
peger på) indeholdt INGEN DevNotify-URL'er, og intet sted på rodsitet linkede
til /devnotify/. Søgemaskiner kunne altså ikke finde produktet.

| Ting | Status |
|------|--------|
| DevNotify + /vs/gitify/ tilføjet rodsitemap | ✅ verificeret live (2 hits) |
| Footer-link til /devnotify/ på rodsitet (intern linking) | ✅ verificeret live |
| Iteration 112-arbejde committed (var ucommit'et) | ✅ a898a0a |
| Alle sider 200: /devnotify/, /devnotify/vs/gitify/, download, terms/privacy | ✅ |

Kontekst: Gitify har 5.325 stjerner og dominerer "github notifications menu bar".
Vores /vs/gitify/-side er ærlig (Gitify vinder pris/platforme) — det er den rigtige
SEO-indgang, nu også findes den via sitemap.

## 3. Traction (ærligt)

**0** betalende kunder · **0** downloads · **$0** revenue.

## 4. Budget

Brugt: **0 kr**. Domæne getdevnotify.com forhåndsgodkendt, venter på køb.

## 5. Venter på Mads

| Hvad | Blokerer |
|------|----------|
| Lemon Squeezy API-nøgle (Bitwarden, ventes 24/8) | Checkout-knap + licensnøgler — ENESTE revenue-blokering |
| Domænekøb getdevnotify.com (~12 USD) | Ordentlig URL |
| Ja/nej til 3 færdige Product Hunt/Reddit-posts i POSTS/ | Udvendig marketing |

## Næste iteration

1. LS-nøgle → opret produkt $19 via API → checkout-URL ind i buy-btn → genudgiv
2. Licensvalidering i app'en mod LS API
3. Mere SEO-indhold: "gitify alternative", "github notifications mac" vinkler
4. GitLab-adapter (efter betaling virker)
