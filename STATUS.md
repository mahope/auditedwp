# STATUS — Iteration 205 (24. august)

## 1. Universalitets-vurdering (punkt 1) — BESTÅET (uændret)

DevNotify er en Tauri desktop-app der tager et GitHub-token — ingen
CMS-afhængighed. Kernen ER produktet. Intet at trække ud.

## 2. Blokerings-check denne iteration (nye fund, ikke gentagelser)

| Hvad | Fund |
|------|------|
| Bitwarden | Stadig `unauthenticated`; nøglen i Keychain er tom — kan ikke hentes programmatisk |
| Domæne **køb** via API | Tokenet mangler registrar-skrive-rettigheder (`Insufficient registrar permissions. Required: #domain:list`) |
| Zone-oprettelse | Samme token mangler også `zone.create` |

Konsekvens: både checkout og domæne kræver Mads' handling. Se §6.

## 3. Gjort i denne iteration (forbedring af købsrejsen)

| Hvad | Status |
|------|--------|
| Alle 48 undersiders header-nav fik **Guides** + **Buy — $19** links (36 ens + 10 custom navs normaliseret) — hver side fører nu mod betaling | ✅ |
| 2 forældreløse SEO-sider (`gitify-alternative`, `octobox-alternative`) var ikke linket fra guide-indeks — rettet (intern linkvægt tabt) | ✅ |
| Fuldt internt link-tjek over alle 51 HTML-filer: **0 broken links** | ✅ |
| Deployet til auditedwp.pages.dev og verificeret live (nav-links + nye sider svarer med indhold) | ✅ |

## 4. Traction (ærlige tal)

**0 betalende kunder · $0 · tilmeldinger: 0**

## 5. Venter på Mads (én linje hver)

1. Lemon Squeezy: opret produkt manuelt i web-UI (2 min, spec i BUILD.md) eller gør Bitwarden tilgængelig → jeg flipper checkout straks.
2. Domæne getdevnotify.com (~$10): køb i Cloudflare dashboard ELLER giv API-tokenet `#domain:list` + registrar-write rettigheder, så køber jeg det selv.
3. Lanceringstekster klar i `site/devnotify/LAUNCH.md` (Product Hunt / Show HN) — venter på ja.

## 6. Næste skridt

1. Checkout-URL modtaget → `python3 scripts/flip_checkout.py <URL>` → deploy → testkøb
2. Domæne kobles på Pages-projektet
3. Produkt #2 startes, hvis blokeringerne stadig står ved næste iteration
