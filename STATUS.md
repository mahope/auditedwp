# STATUS — Iteration 74 (2026-08-27): Universality bestået (7. gang) + cookie-consent arkitektur-guide live

**Dato:** 2026-08-27
**Status:** Punkt 1 re-vurderet med frisk live-bevis: BESTÅET. Ny SEO-artikel bygget, deployet og verificeret. Sitemap 33 URLs.

## Universality-vurdering (punkt 1) — BESTÅET, ærligt

- Frisk live-bevis denne iteration: Worker-API'en scannet **shopify.com** og **webflow.com**
  (begge non-WP). Korrekt platform-detektion ("Shopify", "Webflow"), alle 6 checks kørt,
  HSTS/cookies/forms/legal/headers resultater returneret på under 1 sekund.
- Kernen tager en vilkårlig URL; WordPress er kun én detektions-signatur blandt andre.
- Indpakninger om samme kerne: web (/scan/), API (Worker), CLI (klar til npm), WP-plugin,
  Chrome extension. Pluginet er én indgang blandt flere — korrekt arkitektur.
- **Intet behøvede at blive trukket ud eller bygget om.**

## Bygget i denne iteration

| Ændring | Hvorfor | Status |
|---------|---------|--------|
| **Blog: /blog/server-side-vs-client-side-cookie-consent/** | Planlagt i iteration 73. Dækker søgeintentions-keywords ("server side cookie consent", "client side consent GDPR"). Indhold: begge mønstre forklaret, hvad loven kræver, sammenligningstabel, kode-opskrifter (Cloudflare Workers + Nginx), cache-fælder, hybrid-mønster, valgtabel. FAQ-schema, TOC, CTA til /scan/ og /pro/, further reading. | ✅ Deployet og verificeret (200 + titel + schema + CTAs) |
| Blog-indeks opdateret | Ny artikel øverst. | ✅ Verificeret live |
| Sitemap | 33 URLs, XML valideret. | ✅ Verificeret |

## Kvalitetstjek (egen gennemgang)

- Alle 8 interne links på artiklen → HTTP 200 verificeret
- FAQ-schema + canonical + hreflang x-default på plads
- Mobil-safe (samme responsive CSS som øvrige artikler), ingen eksterne tunge filer

## Portefølje

Scanner · Docs Generator · Chrome Extension (venter CWS) · Badge · Pro ($79/yr, venter Gumroad) · CLI (kode + side live, venter npm-konto) · GDPR/NIS2/EAA-checklister · 5 generatorer · Blog (13 artikler) · Sitemap 33 URLs

## Blokering (uændret)

Mads' konti: Gumroad, CWS ($5), npm. Alle payment-kanaler kræver hans juridiske person.
Klar til at gå live samme dag kontiene findes.

## Klart til Mads (venter på ja)

- Gumroad-produkter prissat, tekster klar
- Sociale opslag skrevet og klar til afsendelse

## Budget

0 kr brugt / 1.000 kr.

## Næste iteration

- Lighthouse-tjek af forsiden (planlagt siden it. 73)
- Forbered npm-publicering fuldt ud (package.json metadata, README, CI-check) så publish kan køre straks Mads' konto findes
- SEO-artikel: NIS2 board liability / ansvar for ledelsen (høj B2B-intention)
