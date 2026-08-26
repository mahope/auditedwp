# STATUS — 3. september 2026 — Iteration 452

## Universality-vurdering (punkt 1) — BESTÅET (re-verificeret iter 451)

DeskUptime-kernen (`src/engine.js`) tager en almindelig URL og virker uanset
CMS. WP-pluginet er ÉN indpakning blandt fem (CLI, desktop, web, GH Action,
WP). Ingen kerneudtrækning nødvendig. Beslutningen holder under penge-
kriteriet: produktet er bygget, $0 leveringsomkostning, $19 impulse-pris.

## Gjort i denne iteration: "vs Better Stack"-indgang (SEO → besøgende)

Better Stack var den sidste store konkurrent uden dedikeret vs-side.
Priser verificeret mod betterstack.com/pricing: $29/responder/md,
$21–25 pr 50 monitors, gratis tier 10 monitors/3-min.

| Artefakt | URL | Status |
|----------|-----|--------|
| Sammenligningsside | `/deskuptime/vs/better-stack/` | Live, 200 ✅ |
| Blogpost (opdateret) | `/blog/better-stack-alternative-2026/` | Live, 200 ✅ |
| vs-hub kort | `/deskuptime/vs/` | Peger nu på vs-siden, korrekt pris ($29/responder, ikke $13) ✅ |
| Bloghub | `/blog/index.html` | Post var allerede listet ✅ |
| Sitemap | `/sitemap.xml` | +2 URLs ✅ |
| Kryds-links | 4 eksisterende vs-sider + Oh Dear-side | "vs Better Stack"-link tilføjet ✅ |

Siden er ærlig om hvad Better Stack gør bedre (on-call, telefonisk eskalering,
statussider, globale tjek når maskinen sover).

## Ærlige tal

| Metrik | Værdi |
|--------|-------|
| Salg | **0** (checkout ikke åbnet endnu) |
| Scans (reelle, worker /stats) | 2 |
| Waitlist | **0** |

## Blokering (1 linje)

LS API key utilgængelig; deskuptime.com ikke købt endnu.

## Næste skridt

1. LS key tilgængelig → BUILD.md trin 1-5 (~10 min) → Buy Now live.
2. Domæne deskuptime.com købes + CNAME.
3. Launch-kit (LAUNCH.md) står klar til Mads' ja.

## Venter på Mads

- Lås Bitwarden op → LS key.
- Køb deskuptime.com (~$10/år, forhåndsgodkendt).
