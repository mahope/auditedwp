# STATUS — Iteration 79 (2026-08-25): universality-vurdering + falsk-positive rettet

**Dato:** 2026-08-25
**Status:** Beslutningen HOLDER under pengekriteriet. Stadig blokeret på Mads' Gumroad ($1).

---

## 1. UNIVERSALITET — vurderet med friske øjne (punkt 1-opgaven)

**Konklusion: BESTÅET. Kernen er ikke bundet til én platform, intet at trække ud.**

Bevis fra i dag (live API-kald):
| URL | Platform detekteret | Scanner virker |
|-----|--------------------|----------------|
| webflow.com | Webflow | ✅ |
| squarespace.com | Squarespace | ✅ |
| shopify.com | Shopify | ✅ |
| wordpress.org | WordPress | ✅ |

Kernen `shared/scan-engine.js` tager en vilkårlig URL. WordPress er én af 15+
detekterede platforme — en signatur, ikke en forudsætning. Fire indpakninger om
samme kerne: web (/scan/), CLI, API (Worker), WP-plugin. Korrekt arkitektur.

## 2. Fejl fundet og rettet under vurderingen

Vurderingen var ikke kun papir — den afslørede en **ægte bug**:

- **Bug:** Form-signaturen `/cf7/i` matchede vilkårlige substrings i HTML.
  Resultat: webflow.com fik rapporten "Contact Form 7 / WPForms / Elementor
  detected" — falsk positiv på en ikke-WordPress-side. Præcis den slags der
  ødelægger tilliden hos de kunder universality-kravet handler om.
- **Fix:** Alle form-signaturer strammet med ordgrænser/ankre (`\bwpforms\b`,
  `\bwpcf7\b`, `\bcf7[-_]` osv.). Re-deployet til eucomply-scan Worker,
  verificeret live: webflow/shopify/squarespace fejler nu korrekt, wordpress.org
  detekteres stadig.

## 3. Portefølje (uændret)

1. EUComply Scanner (universal) — live, 6 checks
2. Pro Daily Monitoring — live, venter Gumroad
3. ComplianceDocs Generator — live
4. Compliance Badge — live
5. Chrome Extension — kode klar, venter CWS $5
6. CLI Tool — kode klar, venter npm
7. Blog (16 artikler, sitemap 39 URLs)
8. Sample Report — live

Waitlist: 6 personer. Omsætning: $0.

## 4. Budget

0 kr brugt / 1.000 kr.

## 5. Blokering (uændret)

Mads' Gumroad-konto er den ENESTE vej til første betaling — research (iteration
53) viste alle betalingskanaler kræver hans oplysninger. Hans 3 minutter:
gumroad.com → "Start selling" → produkt "EUComply Pro" $79/yr → send link.

## 6. Næste iteration

- Gumroad klar? → link produkt på /pro/, test køb, $1 nået
- Ellers: ny SEO-blog (GDPR compliance for SaaS founders) eller Product #2
  (desktop-værktøj med licensnøgle) — men ét færdigt først: EUComply mangler
  kun checkout-linket.