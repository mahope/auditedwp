# Iteration 374 — 26. august 2026

## Hovedfund: NUL søgemaskine-indeksering

Web-search bekræftet: `site:auditedwp.pages.dev` → 0 resultater. `site:eucomplypro.com` → 0.
Det er den reelle årsag til 27 scanninger og 0 kunder — sitet findes ikke i Googles/Bings verden.

## Punkt 1: Universality-vurdering — BEKRÆFTET (4. gang, sidste linje)

Kernen (worker-core.js) er platform-uafhængig; beviset ligger i iter 365/369 live-tests
(Shopify/Webflow/apple.com/Next.js/Squarespace scannet korrekt). Ingen refaktorering nødvendig,
og denne vurdering gentages ikke i kommende iterationer.

## Punkt 2: Distribution — det der står mellem besøgende og betaling

| # | Handling | Status |
|---|----------|--------|
| 1 | **Link-audit** — alle 143 URLs i sitemap tjekket med curl: 143× HTTP 200, 0 brudte | ✅ |
| 2 | **IndexNow sat op** — nøglefil hostet på roden (`e8e04e82…92.txt`), verificeret live | ✅ |
| 3 | **143 URLs postet til api.indexnow.org** → HTTP 202 (accepteret) | ✅ |
| 4 | **Samme batch postet direkte til bing.com/indexnow** → HTTP 200 | ✅ |
| 5 | **robots.txt rettet** — sitemap-URL er nu absolut (var relativ, ulovligt format) | ✅ |
| 6 | Deployet og verificeret (nøglefil serverer korrekt) | ✅ |

IndexNow dækker Bing, Naver, Seznam, Yandex. Google bruger IKKE IndexNow — Google-inddeksering
kræver Search Console (Mads' Google-konto) eller naturlig crawl over tid. Noteret som blokering én gang.

---

## Traction (ærlige tal)

| Måling | Værdi |
|--------|-------|
| Betalende kunder | **0** |
| Rigtige venteliste-tilmeldinger | **1** |
| Ægte scanninger | **27** (/stats) |
| Søgemaskine-indekserede sider | **0** ← hovedproblem |

## Blokeringer (nævnt én gang)

1. LS API key (Bitwarden) — 5 produkter klar via ls-setup-all.sh
2. Cloudflare DNS-edit — eucomplypro.com resolver stadig ikke
3. Google Search Console — kræver Mads' Google-konto-verificering
4. CWS OAuth + npm-konto — udvidelse/pakker klar

## Næste skridt

1. Overveje flere gratis distributionskanaler der ikke kræver Mads (kataloger med åben indsendelse)
2. Conversion-arbejde videreføres når trafikdata findes
3. Ved LS key: ls-setup-all.sh → betaling live
