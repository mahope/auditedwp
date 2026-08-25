# Iteration 349 — 25. august 2026 (nat)

## Universality-vurdering: opfyldt (bekræftet igen)

Punkt 1 er opfyldt og verificeret live i it. 346–348: kernen
(`shared/scan-engine.js`) tager en vilkårlig URL og virker på Next.js,
Shopify, Squarespace og WordPress. WordPress-signaturer er kun
informationel fingerprinting. Ingen kerne skal trækkes ud — webfladen,
CLI'en og Worker-API'et ER allerede indpakninger omkring den.

## Hvad blev gjort i denne iteration

**Ærlig traction-måling:** `/stats` på scan-workeren holder nu en
per-domæne-tally (`stats:domains` i KV). Det betyder at vi fremover kan
se forskel på mine egne smoke-tests (fx stripe.com) og rigtige eksterne
scanninger — i stedet for ét tal der blander det hele.

- Deployet til `eucomply-scan.mahope-eeb.workers.dev` (ver. 4678b8a8).
- Verificeret live: scan + `/stats` returnerer `{scans, domains}`.
- Tæller nulstillet igen: `scans: 0, domains: []`. Ægte tal starter nu.

## Portefølje-status (uændret — alle klar, ingen kan tage penge endnu)

| Produkt | Status | Kan tage penge? |
|---------|--------|----------------|
| EUComply Free | Live | Nej (gratis) |
| EUComply Pro ($79/yr) | Live, klar | **Nej — mangler LS key** |
| QuickFormat ($9) | App + side live | **Nej — mangler LS key** |
| DevNotify ($19) | Side live, extension pakket | **Nej — LS + CWS credentials** |
| ComplianceDocs ($29–$149) | Store live | **Nej — mangler LS key** |

## Traction (ærlige tal)

- 0 betalende kunder, 0 rigtige tilmeldinger.
- Scan-tæller nulstillet 25/8 med ny domæneopdeling: ægte eksterne
  scanninger = 0 indtil videre. Næste rapport kan skælde egne tests fra.

## Venter på Mads (én linje hver)

1. LS API key i Bitwarden (eller manuel opsætning ~20 min, `LS-MANUAL.md`).
2. DNS CNAME @/www → auditedwp.pages.dev (token mangler DNS-edit).

## Næste skridt

1. LS key modtaget → opret produkter via API → sandbox-køb → første betaling.
2. Imens: forbedre siderne mellem besøgende og betaling; bruge den nye
   domæne-opdelte stats som ærlig social proof når tallet > 0.
