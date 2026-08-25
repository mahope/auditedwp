# Iteration 369 — 25. august 2026

## Punkt 1: Universality — vurdering med BEVIS

Kodegennemgang af `worker-core.js` bekræfter: kernen tager en vilkårlig URL og
kører header/HTML-tjek. "WordPress" optræder kun som ÉN fingerprint-signatur
blandt 8+ platforme — aldrig som antagelse.

**Live-verifikation (25/8, eucomply-scan worker):**

| Test-URL | Platform | Resultat |
|----------|----------|----------|
| shopify.com | Shopify | ✅ Scannet, korrekt fingerprint |
| webflow.com | Webflow | ✅ Scannet, korrekt fingerprint |
| apple.com | Unknown | ✅ Scannet uden CMS-antagelse |

**Konklusion:** Ingen refaktorering nødvendig. WordPress-pluginet er én
indpakning blandt flere (web /scan/, CLI, API). Kravet er OPFYLDT og bevist.

---

## Valg i denne iteration: A) Revurdering

**Ærlig vurdering:** Min nuværende beslutning ("distribution nu, betaling når LS kommer") er en taktisk holding-pattern, IKKE en indtjeningsstrategi. Den tjener ikke penge. Under Mads' regel "blokeret = start noget nyt" må jeg acceptere realiteten.

### Den hårde sandhed

| Forsøg | Resultat | Blokering |
|--------|----------|-----------|
| LS opsætning (5 produkter) | 0 kr | LS API key i Bitwarden (1+ dag) |
| Leanpub ebook | 0 kr | Mads skal oprette konto |
| DevNotify Chrome extension | 0 kr | CWS OAuth i Bitwarden |
| Domæne (eucomplypro.com) | 0 besøgende | CNAME DNS-edit mangler |
| npm publish | 0 downloads | npm-konto + email-verifikation |
| **TOTAL indtægt** | **0 kr** | **Mads er den eneste flaskehals** |

**"Blokeret = start noget nyt"-testen:** Jeg har gentaget den samme blokering ("LS key mangler") i 3+ iterationer. Det er præcis det, Mads siger man ikke skal. Jeg stopper med at gentage det.

### Hvad jeg gør i stedet

Jeg accepterer at **indtægt kræver Mads** og fokuserer på det eneste jeg kan gøre: **bygge distribution, så vi har kunder sekundet LS-nøglen ankommer.**

**Prioriteret plan:**

| # | Handling | Effekt | Tidsforbrug | Afhængighed |
|---|----------|--------|-------------|-------------|
| 1 | **npm publish quick-format CLI** | Installerbare downloads, brand | 10 min | npm-konto (Mads) |
| 2 | **npm publish eucomply-scanner CLI** | Devs kører scan fra terminal | 10 min | npm-konto (Mads) |
| 3 | **Forbedr web tools SEO** | Mere organisk trafik | Resten | — |
| 4 | **ls-setup-all.sh** | Ét klik → 5 produkter tager penge | ✅ KLAR | LS key |
| 5 | **Homebrew tap** | `brew install quick-format` | 15 min | GitHub + npm |

**Når LS key ankommer:** kør `./scripts/ls-setup-all.sh` → 5 produkter tager betaling samme dag.

---

## Blokeringer (ÉN linje hver, ikke gentaget)

1. LS API key i Bitwarden — 5 produkter kan ikke tage penge
2. npm-konto (email-verifikation) — CLI'erne kan ikke publiceres
3. CWS OAuth i Bitwarden — DevNotify kan ikke udgives
4. DNS-edit mangler i token — eucomplypro.com CNAME kan ikke aktiveres
5. Leanpub-konto — ebook kan ikke publiceres

---

## Traction (ærlige tal)

| Måling | Værdi | Kilde |
|--------|-------|-------|
| Betalende kunder | **0** | — |
| Rigtige tilmeldinger | **1** (venteliste) | KV-by_time (testdomæner afvist) |
| Ægte scanninger | **0** | scan-tæller (egne tests ekskl.) |
| npm downloads | **0** | Ikke publiceret endnu |
| Web tools besøgende | ??? | Kan ikke måles uden analytics |

---

## Næste skridt

1. Universality: ✅ AFSLUTTET med live-bevis (iteration 369)
2. Forbedr web tools (SEO, landingssider) mens vi venter på nøgler
3. Når LS key ankommer: kør ls-setup-all.sh → 5 produkter tager penge
4. Når npm-konto findes: publish quick-format + eucomply-scanner