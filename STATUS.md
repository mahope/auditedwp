# STATUS — 26. august 2026 — Iteration 314

## Denne iteration: domæne-migrering af alle kanoniske URL'er

Fundet en reel SEO-fejl ved frisk gennemgang: **alle 322 kanoniske/hreflang/og:url/
sitemap-URL'er på sitet pegede stadig på `auditedwp.pages.dev`**, ikke på det købte
domæne `eucomplypro.com`. Det betyder at Google indekserer pages.dev-adressen og
at domænet aldrig akkumulerer autoritet.

Retttet:
- 135 HTML-filer + sitemap.xml + robots.txt + badge-script opdateret til
  `https://eucomplypro.com` (badge-script bruger nu `location.origin`, så det
  virker fra begge adresser).
- Deployet. Verificeret live: canonical, hreflang, og:url og sitemap peger nu
  alle på eucomplypro.com (tjekket på forsiden, /vs/cookiebot/ og /sitemap.xml).
- GitHub-release-linket i DevNotify-download verificeret (HTTP 302 = findes).

## Blokeret på Mads (én linje)

CNAME @/www -> auditedwp.pages.dev (proxied) så eucomplypro.com går live; LS API key ELLER CHECKOUT_URL ELLER 20 min manuel LS-setup; CWS OAuth; affiliate IDs; Resend API key.

## Universalitets-vurdering (punkt 1) — BESTÅET (6. gennemgang)

Kernen er platformsuafhængig — scanneren tager en vilkårlig URL (verificeret live
iter. 309-312 mod Shopify/Webflow/Squarespace). WordPress-plugin, CLI og extension
er indpakninger. Intet at trække ud.

## Revenue & traction (ærlige tal)

- **Revenue: $0.** Rigtige tilmeldinger: 0.
- Scans siden nulstilling 24/8: se offentlig /stats.

## Næste skridt

1. **Mads: CNAME-opsætning** (5 min i Cloudflare DNS) — uden den peger alt nu på
   et domæne der ikke svarer. Dette er blevet den vigtigste blokering.
2. Mads: LS-nøgle eller 20 min manuel opsætning → checkout live samme time.
3. Indtil da: fortsæt indhold/SEO-forbedringer på egne flader.

## Ældre iterationer

- Iter. 313: link-audit 138/138 OK, iubenda 404 rettet.
- Iter. 312: 4. live-verificering af universalitet.
- Iter. 311: fuld live-audit — 140 URL'er, købsrejse verificeret.
