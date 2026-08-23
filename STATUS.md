# STATUS — Iteration 111 (26. august 2026)

## 1. Universitets-vurdering (punkt 1) — DEVNOTIFY

DevNotify er IKKE platform-bundet på den måde AGENTS.md mener. Det er en desktop-app
mod GitHub REST API — der er intet CMS-afhængigt. Kernen er: notifications-API →
normaliseret liste → menu bar UI + polling. GitHub-integrationen er én adapter;
senere kan GitLab/Linear/Jira adapters lægges ind uden ændring af kernen.
**Konklusion: bestået — ingen udtrækning nødvendig.**

## 2. Færdigt denne iteration: DevNotify landingsside + download — LIVE

| Ting | Status |
|------|--------|
| Landingsside (hvad/hvem/pris/køb) | ✅ https://auditedwp.pages.dev/devnotify/ |
| DMG-build (4,2 MB) via hdiutil | ✅ verificeret byte-identisk online |
| Download-knap → rigtig fil | ✅ 200, 4.421.222 bytes, hash matcher |
| Terms + Privacy | ✅ live |
| Sitemap + _headers (rigtig content-type på .dmg) | ✅ |
| Rodsitet (EUComply) gendannet efter fejldeploy | ✅ |

Fejl jeg fandt og rettede: `wrangler pages deploy <mappe>` uploader mappe-indholdet
på roden — første deploys lå derfor på /index.html i stedet for /devnotify/, og
/devnotify/* faldt tilbage til forsiden (SPA-fallback). Løsning: publish/-mappe med
devnotify/-undermappe.

## 3. Traction (ærligt)

**0** betalende kunder · **0** downloads · **$0** revenue.

## 4. Budget

| Post | Beløb |
|------|-------|
| Brugt | **0 kr** |
| Domæne (getdevnotify.com ~12 USD) | Forhåndsgodkendt, venter på køb |
| Tilbage | ~910 kr |

## 5. Venter på Mads

| Hvad | Blokerer |
|------|----------|
| Lemon Squeezy API-nøgle (Bitwarden) | Checkout-knap + licensnøgler — ENESTE blokering for revenue |
| Domænekøb getdevnotify.com | Ordentlig URL (forhåndsgodkendt) |
| Ja/nej til 3 færdige Product Hunt/Reddit-posts i POSTS/ | Udvendig marketing |

## Næste iteration

1. LS-nøgle → opret produkt $19 via API → indsæt checkout-URL i index.html → genudgiv
2. Licensvalidering i app'en mod LS API
3. GitLab-adapter til kernen (bredden, efter betaling virker)
