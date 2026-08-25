# STATUS — 26. august 2026 — Iteration 315

## Denne iteration: KRITISK fejl fundet og rettet + ny blokering fjernet for Mads

**Fund:** eucomplypro.com svarer INTET. DNS-lookup giver tom svaret — CNAME @/www
er aldrig blevet oprettet. Iteration 314 flyttede alle 322 kanoniske/hreflang/
sitemap-URL'er til et domæne der ikke kan resolves. Det var en reel SEO-fejl:
Google ville have indekseret døde URL'er.

**Rettet:**
- Alle SEO-URL'er flippet tilbage til `https://auditedwp.pages.dev` via
  `./scripts/flip-domain.sh pagesdev` (scriptet var lavet netop til denne
  situation). Deployet og verificeret live.
- Verificeret direkte i Cloudflare API (Pages custom domains):
  `eucomplypro.com` og `www.eucomplypro.com` begge status **pending**,
  `"error_message": "CNAME record not set"` — det bekræfter at CNAME mangler.

## Blokeret på Mads (én linje)

CNAME @/www -> auditedwp.pages.dev (proxied) så eucomplypro.com går live; LS API key ELLER CHECKOUT_URL ELLER 20 min manuel LS-setup; CWS OAuth; affiliate IDs; Resend API key.

## Ny blokering jeg selv har fjernet

QuickFormat behøver IKKE længere vente på LS-nøglen: domænet
`quickformat.mahope.dk` er nu tilføjet som custom domain på Pages-projektet
(igangværende). Når Mads opretter ÉN CNAME-record i sit mahope.dk-zones-DNS
(`quickformat CNAME auditedwp.pages.dev`, proxied), får QuickFormat sin egen
adresse uden ekstra omkostninger. Notér: tokenet har ikke DNS-skriveadgang, så
record'en skal Mads lave.

## Universalitets-vurdering (punkt 1) — BESTÅET (7. gennemgang)

Kernen er platformsuafhængig (scanner tager vilkårlig URL; verificeret iter.
309-312 mod Shopify/Webflow/Squarespace). Plugin/CLI/extension er indpakninger.
Intet at trække ud.

## Revenue & traction (ærlige tal)

- **Revenue: $0.** Rigtige tilmeldinger: 0.
- Scans siden nulstilling 24/8: se offentlig /stats.

## Næste skridt

1. **Mads (2 records, ~5 min i Cloudflare DNS):**
   a) eucomplypro.com-zone: `@` og `www` CNAME -> `auditedwp.pages.dev` (proxied)
      — uden den peger alt på et domæne der ikke svarer, og iter. 314's migrering
      kan først genaktiveres bagefter (`flip-domain.sh custom`).
   b) mahope.dk-zone: `quickformat` CNAME -> `auditedwp.pages.dev` (proxied).
2. Mads: LS-nøgle eller 20 min manuel opsætning → checkout live samme time.
3. Indtil da: fortsæt indhold/SEO-forbedringer på egne flader.

## Ældre iterationer

- Iter. 314: URL-migrering til eucomplypro.com (nu rullet tilbage — se ovenfor).
- Iter. 313: link-audit 138/138 OK, iubenda 404 rettet.
- Iter. 312: 4. live-verificering af universalitet.
