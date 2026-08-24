# STATUS — Iteration 200 (24. august, nat)

## 1. Universalitets-vurdering (punkt 1) — bekræftet

**DevNotify BESTÅR stadig.** Tauri desktop-app, tager en GitHub token, virker
uafhængigt af CMS/platform/server. Kernen ER produktet — intet at trække ud.
(Vurderingen står i DECISION.md fra iteration 197 og er uændret.)

## 2. Gjort i denne iteration

Fundet og rettet reelle problemer under en systematisk gennemgang af alle 42 sider:

| Hvad | Status |
|------|--------|
| **Ny guides-hub `/devnotify/guides/`** — 31 guider + 4 deep dives, kategoriseret (fixes / noise / routing / platforms), auto-genereret af `scripts/gen_guides_hub.py` | ✅ Live |
| **Root-sitemap var brudt:** kun 6 af ~49 DevNotify-URL'er var listet — Google kunne ikke se 87 % af indholdet. Flettet alle 43 DevNotify-URL'er ind → nu 106 URLs total | ✅ Live |
| Duplikeret `id="guides"` på forsiden (ugyldig HTML, ankre ramte forkert) fjernet | ✅ Live |
| Nav-link "Guides" pegede på én artikel — peger nu på hub'en; hub linket fra forsiden og downloadsiden | ✅ Live |
| Verificeret: alle 106 sitemap-URLs svarer 200. Ingen orphans, ingen døde links | ✅ |
| **Sync-fix:** iteration 199's garanti-tekster (money-back på forsiden + refund-FAQ + schema) lå i `devnotify-site/` men var aldrig blevet kopieret til `site/` — de er nu LIVE | ✅ Live |

Bemærkning: der findes to træer (`site/devnotify/` = det live, `devnotify-site/` =
arbejdskopi). Denne iteration rettede i `site/devnotify/`. Næste iteration bør
gøre `devnotify-site/` til den eneste kilde (eller et symlink), så fejlen ikke
gentager sig.

## 3. Traction (ærlige tal)

**0 betalende kunder · $0 · tilmeldinger: 0**

## 4. Venter på Mads (én linje)

Bitwarden-login eller 2-minutters LS checkout-setup → DevNotify kan tage imod $19.

## 5. Næste skridt

1. Gør `devnotify-site/` til den eneste kilde for sitet (fjern dobbelt-træet)
2. Når checkout er åben: `python3 scripts/flip_checkout.py <URL>` → deploy → testkøb
3. Domæne getdevnotify.com (forhåndsgodkendt)
4. Lanceringstekster klar i `devnotify-site/LAUNCH.md` (venter på ja til Reddit/HN)
