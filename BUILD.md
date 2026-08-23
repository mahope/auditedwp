# BUILD — korteste vej til første betalende kunde

Produkt: **AuditedWP** — white-label WordPress-drift med compliance-dokumentation,
wholesale til små/mellemstore webbureauer i EU/DACH.
Se DECISION.md for fuld begrundelse.

## ✅ Færdigt og live

| Hvad | Status | URL |
|------|--------|-----|
| Landingsside EN | ✅ Live | https://mahope.github.io/auditedwp/ |
| Landingsside DE (DACH) | ✅ Live | https://mahope.github.io/auditedwp/de/ |
| Sample audit trail | ✅ Live | https://mahope.github.io/auditedwp/sample/ |
| NIS2 vendor-clause template | ✅ Live | https://mahope.github.io/auditedwp/template/ |
| DPA-skabelon + NDA + white-label rapporter | ✅ Bygget | `site/deliverables/` |
| Interaktiv margin-beregner | ✅ Live | Indbygget i EN + DE landing pages |
| robots.txt + sitemap.xml | ✅ Live | SEO-klar fra dag 1 |
| Onboarding-manual | ✅ Bygget | `site/onboarding-manual.md` |
| Deploy script (GitHub Pages) | ✅ Testet | `cd site && sh deploy.sh` |

## ⏳ Mangler (kræver Mads)

1. **Stripe-konto** — hvem opretter? Under hvilket navn? Skal tilføjes som CTA.
2. **Udadvendt henvendelse** — 5 pilot-bureauer (kun efter Mads' ja).
3. **Domæne auditedwp.com** (~70 DKK, forhåndsgodkendt) — sættes som custom domain.
4. **Juridisk review** af DPA/NDA før første underskrift.

## Priser (uændret fra DECISION.md)

- Wholesale: €29/site/md (0-25 sites) → €19/site/md (26+, 12 mdr.)
- Setup-fee: €290 pr. bureau
- Add-on: kvartals-compliance-rapport €99/kvartal/bureau

## Hvordan første kunde ser ud

1. Kunde finder sitet (organisk / direkte link / Mads' netværk)
2. Klikker "Start onboarding → email hello@auditedwp.com"
3. Mail lander hos Mads (når domæne + MX opsat)
4. Onboarding-samtale → Stripe Payment Link → oprettelse
5. Leverance: concierge-style (MainWP/WP Umbrella på test-site først, manuel drift)

## Hvad jeg IKKE bygger nu

Ingen kunde-dashboard, ingen billing-infrastruktur, ingen automatiserings-pipeline
før mindst ét bureau har betalt. Software-byggeri starter ved smertetærsklen.

## Deploy

```sh
cd site
git add -A
git commit -m "..."
git push origin main
# ~30s build på GitHub Pages → live
```

Alternativt: `sh site/deploy.sh` (gør det samme + commit-besked med dato).