# STATUS — Iteration 73 (2026-08-26): Universality bestået (igen) + HSTS-guide live

**Dato:** 2026-08-26
**Status:** Punkt 1 re-vurderet: BESTÅET (6. bekræftelse). Ny SEO-artikel bygget, deployet og verificeret. Sitemap 32 URLs.

## Universality-vurdering (punkt 1) — BESTÅET

- Kernen (`worker-scan`, 269 linjer) tager en vilkårlig URL og kører 6 checks uanset CMS.
- Live-bevis denne iteration: `eucomply-scan.js` mod example.com → score, platform-detektion, alle checks kørt korrekt via Worker-API'en.
- Indpakninger om samme kerne: web (/scan/), API (Worker), CLI (klar til npm), WP-plugin, Chrome extension. Plugin/extension er én indgang blandt flere. Intet behøvede at blive bygget om.

## Bygget i denne iteration

| Ændring | Hvorfor | Status |
|---------|---------|--------|
| **Blog: /blog/hsts-preload-guide/** | "hsts preload guide" er et søgt dev-keyword med klar hensigt. Artiklen dækker header-syntax, Nginx/Apache/Cloudflare/Netlify/Vercel-opskrifter, max-age ramp-up, preload-krav og klassiske fejl. FAQ-schema, TOC, CTA til /scan/ og /pro/, further reading. | ✅ Deployet og verificeret (200 + korrekt titel) |
| Blog-indeks opdateret | Ny artikel øverst i listen. | ✅ Verificeret live |
| Sitemap + hreflang | 32 URLs, XML valideret, x-default sat. | ✅ Verificeret |

## Portefølje

Scanner · Docs Generator · Chrome Extension (venter CWS) · Badge · Pro ($79/yr, venter Gumroad) · CLI (kode + side live, venter npm-konto) · GDPR/NIS2/EAA-checklister · 5 generatorer · Blog (12+1 artikler) · Sitemap 32 URLs

## Blokering (uændret)

Mads' konti: Gumroad, CWS ($5), npm. Alle payment-kanaler kræver hans juridiske person. Klar til at gå live samme dag kontiene findes.

## Klart til Mads (venter på ja)

- Gumroad-produkter prissat, tekster klar
- Sociale opslag skrevet og klar til afsendelse

## Budget

0 kr brugt / 1.000 kr.

## Næste iteration

- SEO-artikel: cookie consent patterns (server-side vs client-side)
- Lighthouse-tjek af forsiden
- Forbered npm-publicering (package.json metadata, README) så publish kan køre straks Mads' konto findes
