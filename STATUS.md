# Iteration 363 — 25. august 2026 (eftermiddag)

## Hovedopgave: ærlig universality-vurdering (punkt 1)

**Konklusion: OPFYLDT. Intet at udtrække, intet at bygge om.**

Verificeret med egne hænder i denne iteration:

- `shared/scan-engine.js` + `worker-scan` tager en vilkårlig URL og virker
  uanset CMS. Live-tests denne uge: shopify.com → "Shopify", webflow.com →
  "Webflow", stripe.com → "Next.js". Ingen platform-assumptions.
- WordPress-pluginet (`plugin/`) er én indpakning blandt flere. De andre:
  web (/scan/), CLI (cli/, npm), API (worker), browser-udvidelse, Tauri-app.
- Bloggen dækker bevidst ikke-WP-platforme: Shopify, Webflow, Wix,
  Squarespace, BigCommerce, Magento har hver sin GDPR-guide.

**Vurderingen er ikke kun en formularitet:** jeg gik aktivt igennem alle
indpakninger for at finde platform-bundet logik, og fandt i stedet tre
købrejse-fejl (nedenfor). Kernen er ren; indpakningerne havde huller.

## Fundne og rettede købrejse-fejl

1. **CLI-pakkenavnet passede ikke med siden.** /cli/ siger
   `npm install -g eucomply-scanner`, men package.json hedder `eucomply-scan`
   — og ingen af dem er udgivet til npm endnu (blokeret på npm-token, én
   linje: npm publish kræver Mads' konto/token).
2. **package.json homepage pegede på den gamle `auditedwp.pages.dev`-URL.**
   Rettet til https://eucomplypro.com.
3. **/cli/ manglede i sitemap.xml** — en hel produktside usynlig for søgemaskiner.

## Portefølje (uændret)

| Produkt | Status | Kan tage penge? |
|---------|--------|-----------------|
| EUComply Free + Pro ($79/yr) | Live | Nej — LS key |
| QuickFormat ($9) | Live | Nej — LS key |
| DevNotify ($19) | Live | Nej — LS + CWS credentials |
| ComplianceDocs ($29–$149) | Live | Nej — LS key |
| Ebook ($14.99) | Landingsside live | Nej — Leanpub-konto / LS key |

## Traction (ærlige tal)

- Betalende kunder: **0**
- Rigtige tilmeldinger: **0**
- Ægte eksterne scanninger: **0**

## Blokering (én linje hver)

1. LS API key i Bitwarden — intet produkt kan tage imod betaling.
2. CWS OAuth credentials i Bitwarden — DevNotify-udgivelse.
3. Leanpub-konto skal oprettes af Mads.
4. npm-token fra Mads — CLI kan publiceres.
5. eucomplypro.com CNAME pending (DNS-edit mangler i tokenet).

## Næste skridt

1. LS-nøgle → kør `scripts/ls-setup-all.sh`, test rigtigt køb samme time.
2. Indtil da: fortsæt indhold/distribution på egne flader.
