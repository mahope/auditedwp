# STATUS — 24. august 2026 — Iteration 223

## Universalitets-vurdering (punkt 1) — BESTÅET

Kernen `shared/scan-engine.js` er CMS-uafhængig — tager enhver URL, ingen
CMS-antagelser (shopify/webflow/squarespace/example beviest i it. 219).
WP-plugin, CLI og browser-ext er indpakninger. **Ingen udtrækning nødvendig.**

## Pengekriteriet — beslutningen HOLDER

EUComply Pro ($79/år recurring) primært. Pro-siden verificeret korrekt i
flip-tilstand: waitlist vises nu, skifter automatisk til checkout når
CHECKOUT_URL-secret sættes.

## Gjort i denne iteration

Prioritet 3 (distribution/SEO): fuld intern-linking-audit af alle 27 blogposts.

**Før:** 8 posts havde nul eller én intern backlink fra andre posts; 6 var
helt forældreløse (cookiebot-alternative, dora-for-ecommerce,
gdpr-compliance-for-agencies, hsts-preload-guide, iab-tcf-compliance-guide,
server-side-vs-client-side).

1. Nyt emnegrupperet "Keep reading"-modul (3 relaterede guides) i alle 27
   posts — konsolideret script `site/add_related.py` (idempotent).
2. 12 yderligere håndplukkede links så **alle 27 posts nu har mindst ét
   internt indgående link** — nul forældreløse (script-verificeret).
3. Link-validering: alle /blog/-hrefs peger på eksisterende sider.
4. Deployet; alle 27 undersider returnerer 200 med keep-reading live.

## Traction (ærlige tal)

**0 paying customers · $0 revenue · 0 real subscribers · 1 scanning**

## Blokering (én linje)

LS API-nøglen ligger endnu ikke i Bitwarden (bw status: unauthenticated).

## Venter på Mads

1. LS API-nøgle → `./scripts/eucomply-flip.sh <url>` (Pro $79/år) + store-flip.
2. Domæne eucomply.com (~$12, forhåndsgodkendt) når betaling er live.

## Næste skridt

Med LS-nøglen: sandbox-testkøb → flip Pro-checkout og 6 butikssider samme time.
Uden: ny side rettet mod "is my cookie banner compliant"-søgninger, eller
sitemeta/robots-tjek + hreflang-gennemgang af de tyske sider (/de/).
