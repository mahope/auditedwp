# BUILD.md — EUComply (26. august 2026)

## Hvad
En universel EU-compliance scanner, der på 10 sekunder checker enhver URL mod GDPR, NIS2, DORA og EAA. Platform-uafhængig.

## Pris
- **Free:** Én-off scanning, shareable scorecard
- **Pro:** $79/site/år — daily monitoring, PDF reports, templates, badge, alerts

## Aktuel status

| Område | Status |
|--------|--------|
| **Universality** | ✅ BEVIST — apple.com, wordpress.com, shopify.com scannet korrekt |
| **Site** | ✅ Live på auditedwp.pages.dev — 216 filer, scanner virker |
| **/pro/** | ✅ Fuld salgsside med feature-matrix, pris, live monitoring demo, FAQ |
| **/how-it-works/** | ✅ Ny (26/8) — step-by-step guide med CTA |
| **Betaling** | 🔒 Blokeret — LS API key i Bitwarden |
| **Distribution** | 🔄 Klar — npm, Chrome ext, CLI |

## Korteste vej til første betaling

1. **Mads frigør LS API key** → `bash ls-setup-all.sh` (5 produkter på < 5 min)
2. Første kunde: scanner URL, ser issues, klikker "Buy Pro $79/yr" → LS checkout
3. **Chrome Web Store udgive** → browser-extension installeres og konverterer

## Hvad der bygges i ventetiden

- **/pricing/** (iter 373) — consolidated pricing landing side: Free vs Pro $79/yr vs Templates $29-$149
- Flere SEO-sider (guides med faktisk rangeringspotentiale)
- Conversion-forbedring på eksisterende sider
- Rydning af døde links/kanoniske fejl