# STATUS — Iteration 160 (24. august)

## 1. Blokering (én linje)

LS-nøglen utilgængelig via CLI (Bitwarden session unauthenticated) → venter på Mads.

## 2. Universalitetsvurdering (punkt 1) — bestået, verificeret i dag

Kernen (`devnotify/src-tauri/src/providers.rs`) er platform-agnostisk:
normaliseret `NotificationItem` + provider-enum med adapters. GitHub er én
provider; GitLab kan tilføjes uden ændringer i kernen. macOS-appen er ÉN
indpakning; sitet er statisk HTML; license-validering taler med Lemon
Squeezy's standard License API. Ingen del af produktet forudsætter et bestemt
CMS eller en platform. Intet at trække ud.

## 3. Penge-linsen — beslutningen holder

Første kunde timer efter LS-nøglen ($19 one-time), bevist betalingsvilje
(Gitify 5,3k stjerner), ~0 kr/md i leveringsomkostning, produktet er bygget
og download-siden virker. DECISION.md uændret.

## 4. Denne iteration — fuld link-audit af live sitet + 2 fejl rettet

Gennemgik ALLE interne links og ALLE sitemap-URLs på det deployede site med
programmatisk tjek (statuskode + indholdsstørrelse):

- **Fund fejl 1:** `/devnotify/terms/` og `/devnotify/privacy/` (med slash)
  returnerede **404** — filerne ligger extensionless, men 2 guider og sitemap
  linkede med trailing slash. Rettet links + sitemap → deployet.
- Fund fejl 2: samme URLs i `sitemap.xml` pegede på `.html`-varianter der
  ikke findes. Rettet.
- **Verificeret efter deploy:** alle 31 unikke interne links 200 (inkl.
  begge .dmg-filer, >4 MB hver), alle 28 sitemap-URLs 200 med indhold.
- Købsrejsen gennemgået igen: landing → download → trial → buy-section.
  Alt teknisk virker; eneste manglende led er LS-checkout URL'en (blokeret,
  se pkt. 1). `ls-flip.sh` står klar til at sætte den ind på ét streng.

## 5. Traction (ærlige tal)

**2 besøg · 1 download · 0 tilmeldinger · $0 · 0 betalende kunder.**

## 6. Venter på Mads

1. **Log ind i Bitwarden-desktopappen én gang** (eller læg LS-nøglen et sted
   jeg kan læse). Derefter: produkt + checkout via API samme time —
   `ls-setup.sh` → `ls-flip.sh <url>` → deploy → test-køb.
2. Domænekøb getdevnotify.com (forhåndsgodkendt — sig blot til).

## 7. Næste iteration

Ny guide ("GitHub notification badge not showing on app icon") — høj
søge-intention, dækker endnu ikke.
