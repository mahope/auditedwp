# Iteration 351 — 25. august 2026

## Universality-vurdering (punkt 1): OPFYLDT

Kernen (`shared/scan-engine.js`) tager en vilkårlig URL og virker uanset
CMS. Verificeret live i tidligere iterationer: Shopify, Next.js,
Squarespace, WordPress. WordPress-signaturer er kun informationel
fingerprinting. Web, CLI og Worker-API er indpakninger omkring kernen.
**Ingen udtrækning nødvendig.** QuickFormat og DevNotify er
platform-uafhængige desktop-apps fra start.

## Hvad blev gjort i denne iteration (købsrejsen = prioritet 1)

Fremmed-gennemgang af alle salgssider fandt to tillidshuller mellem
besøgende og betaling:

1. **ComplianceDocs-produktsiderne (5 stk.) havde hverken refusions-
   garanti eller FAQ.** For et ukendt mærke er det det største argument
   imod at købe. Tilføjet en "Buy with confidence"-sektion på alle 5:
   14 dages money-back, levering, MoR/betaling, licens, ikke-juridisk
   rådgivning. Deployet og verificeret live.
2. **14-dages money-back nævnt på /pro/ og /store/ oversigtssiden**
   (var der fra før på pro; butiksforsiden fik garantinoten).

Mindre: QuickFormat-H1 manglede punktum.

Bemærkning: `site/AGENTS.md` siger at domænet er **eucomplypro.com**,
men det resolver ikke endnu (DNS pending) — alt verificeret via
auditedwp.pages.dev. Siderne peger allerede internt på eucomplypro.com,
så de er klar når CNAME'et går igennem.

## Portefølje-status (uændret)

| Produkt | Status | Kan tage penge? |
|---------|--------|----------------|
| EUComply Free | Live | Nej (gratis) |
| EUComply Pro ($79/yr) | Live, klar | **Nej — mangler LS key** |
| QuickFormat ($9) | App + side live | **Nej — mangler LS key** |
| DevNotify ($19) | Side live, extension pakket | **Nej — LS + CWS credentials** |
| ComplianceDocs ($29–$149) | Store live | **Nej — mangler LS key** |

## Traction (ærlige tal)

- 0 betalende kunder, 0 rigtige tilmeldinger.
- Ægte eksterne scanninger efter nulstilling: 0.

## Venter på Mads (én linje hver)

1. LS API key i Bitwarden (eller manuel opsætning ~20 min, LS-MANUAL.md).
2. DNS CNAME @/www → auditedwp.pages.dev + eucomplypro.com (token mangler DNS-edit).

## Næste skridt

1. LS key → opret produkter via API → sandbox-køb → første betaling.
2. Imens: næste iteration gennemgår /pro/vs-* sammenligningssiderne og
   /scan/-fladen som en fremmed.
