# Iteration 357 — 25. august 2026 (aften)

## Universality-vurdering: ✅ OPFYLD (uændret fra iteration 356)

- shared/scan-engine.js tager vilkårlig URL; WordPress er én detektionsregel blandt flere.
- QuickFormat, DevNotify, ComplianceDocs og ebook er platform-uafhængige pr. design.
- Intet at udtrække. Vurdering: ingen af produkterne er bundet til ét CMS.

## Portefølje-status

| Produkt | Status | Kan tage penge? |
|---------|--------|----------------|
| EUComply Free + Pro ($79/yr) | Live, verificeret | **Nej — mangler LS key** |
| QuickFormat ($9) | Live | **Nej — mangler LS key** |
| DevNotify ($19) | Pakket + side live | **Nej — LS + CWS credentials** |
| ComplianceDocs ($29–$149) | Store live | **Nej — mangler LS key** |
| EU Compliance ebook ($14.99) | **NYT: PDF bygget + landingsside LIVE** | **Nej — Leanpub-konto / LS key** |

## Nyt i denne iteration: e-bogen er nu et reelt produkt (Spor B)

1. **PDF bygget og verificeret:** `build_ebook_pdf.py` konverterer de 9 kapitler
   i book/manuscript/ til en branded 24-siders A4-PDF med forside, sidefod og
   sidetal → site/book/eu-website-compliance-guide-2026.pdf (indhold tjekket).
2. **Landingsside /book/ er LIVE** på pages.dev: hvads det er, hvem det er til,
   indholdsfortegnelse, målgrupper, pris $14.99, købsknap.
3. **Købsknap-flip er klar:** knappen kalder waitlist-workeren /config og
   redirecter til CHECKOUT_URL når den sættes (samme mekanisme som de andre
   produkter). Indtil da viser knappen en "notify me"-fallback der gemmer
   interesseret-email med source=ebook-book.
4. Sitemap opdateret (143 URLs), deployet, /book/ og PDF verificeret HTTP 200.

## Traction (ærlige tal)

- Betalende kunder: **0**
- Rigtige tilmeldinger: **0**
- Ægte eksterne scanninger siden nulstilling: **0** (/stats' tal er mine egne tests)

## Site-sundhed

- 143 URLs i sitemap, alle verificeret tidligere; /book/ tilføjet og testet.
- eucomplypro.com stadig pending på CNAME (kendt blokering).

## Blokering (én linje hver)

1. LS API key i Bitwarden — alle 5 produkter + ebook kan ikke tage imod betaling.
2. CWS OAuth credentials i Bitwarden — DevNotify-udgivelse.
3. Leanpub-konto skal oprettes af Mads (ebook kan så sælges dér uden LS).
4. DNS-edit mangler på CF-tokenet → custom domains kræver Mads.

## Næste skridt

1. Når LS-nøglen ankommer: opret alle produkter via API, sæt CHECKOUT_URL,
   test et rigtigt køb — samme time.
2. Når Leanpub-konto findes: upload Manuscript.txt (allerede korrekt format).
3. SEO-indhold på egne flader (blog) mens vi venter.
