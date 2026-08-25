# Iteration 365 — 25. august 2026 (nat)

## Opgave: Ærlig universality-vurdering af det eksisterende

**Konklusion: Punkt 1 (universelt) er OPFYLDT og nu BEVIST med tests — ikke kun vurderet.**

### Vurderingen

Arkitekturen er allerede kerne + indpakninger, som mandatet kræver:

- **Kernen:** `shared/scan-engine.js` (448 linjer). Tager en almindelig URL,
  kender intet om WordPress som forudsætning. Platform-detektering er ÉN
  check blandt 20+ (Shopify, Wix, Squarespace, Webflow, Next.js, Nuxt, Drupal,
  Joomla, Craft, TYPO3, Umbraco, Ghost, BigCommerce, Magento, PrestaShop,
  OpenCart m.fl.). De juridiske checks (GDPR, TCF, Consent Mode v2, EAA,
  NIS2, DORA-signaturer) er CMS-agnostiske — de læser HTML, ikke database.
- **Indpakninger (én af flere hver):** web-fladen /scan/, CLI
  (`eucomply-scanner/cli/`), API-endpoint på workeren, Chrome-extension.

### Ny bevisførelse (denne iteration — rigtige kald mod live worker)

| Test-URL | Detekteret platform | Score |
|----------|--------------------|-------|
| shopify.com | Shopify | (fuldt svar, 9 checks) |
| webflow.com | Webflow | 44% |
| stripe.com | Next.js | 67% |
| squarespace.com | Squarespace | 33% |

Ingen af dem er WordPress — alle scannes korrekt og universelt.
WordPress-signaturerne i motoren er desuden bevidst snævert anchored
(kun tekniske artefakter som `/wp-content/`, aldrig tekstnævnelser), så de
ikke false-positive på andre platforms marketingtekster.

**Handling: Ingen refaktorering nødvendig. Intet arbejde smides væk — det
opfylder allerede kravet.**

## Portefølje (uændret)

| Produkt | Status | Kan tage penge? |
|---------|--------|-----------------|
| EUComply Free + Pro ($79/yr) | Live | Nej — LS key |
| QuickFormat ($9) | Live | Nej — LS key |
| DevNotify ($19) | Live | Nej — LS + CWS credentials |
| ComplianceDocs ($29–$149) | Live | Nej — LS key |
| Ebook ($14.99) | FAQ tilføjet iter. 364 | Nej — Leanpub-konto / LS key |

## Traction (ærlige tal)

- Betalende kunder: **0**
- Rigtige tilmeldinger: **0**
- Ægte eksterne scanninger: **0**

## Blokering (én linje hver)

1. LS API key i Bitwarden — intet produkt kan tage imod betaling.
2. CWS OAuth credentials i Bitwarden — DevNotify-udgivelse.
3. Leanpub-konto skal oprettes af Mads (eller LS key kommer).
4. npm-token fra Mads — CLI kan publiceres.
5. eucomplypro.com resolver ikke (DNS-edit mangler i tokenet).

## Næste skridt (i prioritetsorden)

1. LS-nøgle → kør `scripts/ls-setup-all.sh`, test rigtigt køb samme time.
2. Indtil da: fortsat forbedring mellem besøgende og betaling + indhold.
