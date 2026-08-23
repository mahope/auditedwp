# STATUS

## 2026-08-23 — Iteration 32: PIVOT efter nul-indsats-testen. Butik bygget.

### Hvad der skete
Mads' nye afgørende krav (3 måneder væk uden internet = stadig indtægt) fejlede
den gamle beslutning: **AuditedWP white-label drift ER manuel leverance og
support** — kasseret trods bevist marked og færdigt site. 0 kr tabt på sporet.

### Ny beslutning (DECISION.md, iter. 32)
**ComplianceDocs** — butik for færdige EU-compliance-dokument-skabeloner
(DPA, NDA-clauses, NIS2/DORA vendor-terms, EAA-statement) som digitale downloads.
Genbruger de fem deliverables der allerede var bygget til AuditedWP. Leverancen
er en fil; checkout + levering + refusion kører via merchant-of-record-platform.
Nul marginal-indsats. Kedeligt og bevidst.

### Bygget i denne iteration
- `site/store/index.html` — komplet butiksside: 5 produkter + $149-bundle,
  priser, disclaimer, sample-previews, checkout-pladsholdere klar til
  Lemon Squeezy-links. HTML valideret.
- BUDGET/BUILD/DECISION/RESEARCH opdateret.

### Næste skridt
1. Deploy `site/store/` til Pages (næste push).
2. Verificere complidocs.com ledig; køb via Cloudflare (forhåndsgodkendt).
3. **BLOKERET PÅ MADS (én gang):** opret store-konto i hans navn/bank — kan
   ikke gøres af mig. Gumroad-fallback hvis Lemon Squeezy afviser.
4. Indsæt checkout-links i butikssiden → forretningen kører selv.

### Blokeret / ærlige risici
- Uden Mads' engangs-oprettelse af store-konto er checkout lukket — siden står
  klar men tjener 0 indtil da. Alt andet (produkter, sider, tekst) er færdigt.
- Trafikrisiko: organisk SEO tager måneder; produktet koster ~0 at stå imens.

### Budget
0 kr brugt. Fast omkostning 0 kr/md indtil første salg (MoR tager % ved salg).
