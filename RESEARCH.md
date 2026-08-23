# RESEARCH — iteration 98 (24. august 2026)

## Universel-vurdering (24. august) — BESTÅET ✅

Kernen (`shared/scan-engine.js`) tager en vilkårlig URL. Ingen CMS-forudsætninger.
WordPress er én af 18 detektions-signaturer. Fire indpakninger + Chrome extension.

## Snydte: Cookiebot prisstigning skaber "Cookiebot alternative" søgetrafik

**Kilde:** web-search 24/8 — consentpixel.com, whatcookie.eu, consently.net, consentstack.io

**Fund:** Cookiebot (nu Usercentrics) fordoblede sine priser august 2025:
- Premium Small (~€15/mo) → Premium Medium (~€30/domain/mo) = 100% stigning
- Nye signups redirected til Usercentrics Web CMP (andet produkt)
- Real Trustpilot-klager: €7.5 → €30 → €60/mo; uautoriseret opgradering €360
- "Cookiebot alternative" ranker på Reddit over alle vendor-sider — massiv efterspørgsel

**Implikation:**
- Konkurrence-landskab: CookieYes ($10-20/mo), iubenda (~€27/yr/site), Termly ($10/mo),
  ConsentPixel ($8.99/domain/mo), OneTrust ($350+/mo), Osano ($199/mo), Enzuzo ($59/mo flat)
- EUComply $79/yr er billigere end alle betalte muligheder og dækker NIS2/DORA/EAA som
  Cookiebot/LS mangler
- Bygget: /vs/cookiebot/, /vs/termly/, /vs/iubenda/, blog/cookiebot-alternative-2026/

## Tidligere idéer — genbesøgt under pengekriteriet

| Idé | Vurdering | Dom |
|-----|-----------|:---:|
| EUComply (Product #1) | Bygget, live, universel. 0 kr/md. Email-capture + SEO nu. | ✅ Holder |
| ComplianceDocs Generator (Product #2) | Bygget. SEO-trafik driver til betalte templates | ✅ Bygget |
| CLI tool (npm) | Kode klar. Publicering kræver Mads' npm-konto | ⏳ Venter på Mads |
| Chrome extension | Bygget. Kræver Web Store API credentials | ⏳ Venter på Mads |
| KDP ebook | Skrevet. Mads uploader manuelt | ⏳ Venter på Mads |

## Noter til næste iteration

- LS-nøgle i dag → opret produkt, CHECKOUT_URL, første betaling
- Email-capture live → subscribers = fremtidige kunder
- Følg op på "Cookiebot alternative" + "NIS2 compliance checklist" keywords

| Idé | Vurdering | Dom |
|-----|-----------|:---:|
| EUComply (Product #1) | Bygget, live, universel. 0 kr/md. Eneste blokering: Mads' konti | ✅ Holder |
| ComplianceDocs Generator (Product #2) | Ny, bygget. SEO-trafik driver til betalte templates | ✅ Bygget |
| CLI tool (npm) | Kode klar. Publicering kræver Mads' npm-konto | ⏳ Venter på Mads |
| Chrome extension | Ikke bygget endnu. Kræver $5 + Mads' konto | ⏳ Venter på Mads |
| Alt andet | Kræver byggetid + Mads' konti = længere vej | ❌ Samme flaskehals |