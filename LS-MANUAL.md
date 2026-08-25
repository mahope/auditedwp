# LS Manual Setup — 20 min for Mads (25. august 2026)

Du har ALLEREDE en Lemon Squeezy-konto: `mads@mahope.dk`.
Bitwarden-nøglen er kun til automatisering. Den her bruger vi manuelt — 20 min, så er vi i gang.

## 1. Log ind

Gå til https://app.lemonsqueezy.com — log ind med din email.

## 2. Opret 6 produkter (Products → New product)

Brug EXACT disse indstillinger for hvert produkt. Kopiér beskrivelserne nedenfor.

### Produkt 1: GDPR Data Processing Agreement
| Felt | Værdi |
|------|-------|
| Title | "GDPR Data Processing Agreement (Art. 28) — Editable Template" |
| Price | **$59 one-time** |
| File upload | `gumroad/products/dpa-template.pdf` |
| Description | "An editable GDPR Data Processing Agreement template compliant with Article 28 of the GDPR. Covers data categories, processing purposes, sub-processor authorization, data breach notification, and deletion upon termination. Includes both controller-to-processor and processor-to-sub-processor versions. Microsoft Word format (.docx) — edit and sign immediately." |
| Variant name | "Single License" |

### Produkt 2: NIS2 / DORA Vendor Clause Set
| Felt | Værdi |
|------|-------|
| Title | "NIS2 / DORA Vendor Clause Set — 12 Ready-to-Use Clauses" |
| Price | **$49 one-time** |
| File upload | `gumroad/products/nis2-vendor-clauses.pdf` |
| Description | "12 ready-to-use vendor contract clauses that address NIS2 Article 21 (incident response, supply chain security) and DORA Article 5-7 (ICT risk management, resilience testing, third-party oversight). Use directly in MSAs and service agreements. Includes compliance matrix cross-referencing each clause to the relevant article." |
| Variant name | "Single License" |

### Produkt 3: Mutual NDA Clause Set
| Felt | Værdi |
|------|-------|
| Title | "Mutual NDA Clause Set — 6 Standard Variations" |
| Price | **$29 one-time** |
| File upload | `gumroad/products/nda-clause-set.pdf` |
| Description | "6 standard mutual NDA variations: one-way, mutual, multi-party, with data processing addendum, with non-solicit, and short-form. Each clause includes guidance on when to use it and common negotiation points. Word format — paste into your agreement template." |
| Variant name | "Single License" |

### Produkt 4: EAA Accessibility Statement Template
| Felt | Værdi |
|------|-------|
| Title | "EAA Accessibility Statement Template — Compliant with EN 301 549" |
| Price | **$39 one-time** |
| File upload | `gumroad/products/eaa-statement-template.pdf` |
| Description | "European Accessibility Act (EAA) compliant accessibility statement template. Meets EN 301 549 requirements and the Web Accessibility Directive (EU) 2016/2102. Fill in your organization's details, assessment methodology, and contact information. Includes WCAG 2.2 conformance report template." |
| Variant name | "Single License" |

### Produkt 5: Client Compliance Report Kit
| Felt | Værdi |
|------|-------|
| Title | "Client Compliance Report Kit — 3 Preparatory Templates" |
| Price | **$69 one-time** |
| File upload | `gumroad/products/reportkit.zip` |
| Description | "3 preparatory templates for compliance consulting engagements: (1) Compliance Assessment Questionnaire — 45+ questions covering GDPR, NIS2, DORA, EAA; (2) Remediation Roadmap — phased plan template with timeline, owner, and evidence fields; (3) Final Compliance Report — auditor-ready template with executive summary, findings table, and risk scoring methodology. All in Word format." |
| Variant name | "Single License" |

### Produkt 6: The Complete Bundle
| Felt | Værdi |
|------|-------|
| Title | "The Complete Compliance Bundle — All 5 Templates + 12 Months Updates" |
| Price | **$149 one-time** |
| File upload | Ingenting (dette er et bundle) |
| Description | "All 5 compliance templates (DPA, NIS2 Vendor Clauses, NDA Set, EAA Statement, Report Kit) plus 12 months of updates. Save $37 compared to buying individually. When regulation updates (e.g., NIS2 implementing acts, DORA amendments), you get the updated versions automatically." |
| Variant name | "Bundle License" |

## 3. Efter oprettelse

For hvert produkt: klik **Publish** → kopiér **Checkout URL** (direct link, ikke embed-kode).

Send mig disse 6 checkout-URL'er. Enten:
- I en Bitwarden-sikker note kaldet "LS checkout URLs"
- Eller i en besked

**Jeg gør herefter:**
1. Sætter URL'erne ind på `site/store/index.html` (erstatter waitlist-bannere)
2. Deployer
3. Kører sandbox-køb (kort 4242 4242 4242 4242, enhver dato, enhver CVC)
4. Verificerer at leveringsmailen indeholder PDF'en
5. Rapporterer status: **første betaling mulig**

## Prissætning (hvorfor disse priser)

| Produkt | Pris | Rationale |
|---------|------|-----------|
| DPA Template | $59 | Engangskøb. Kommerciel kontrakt — virksomheder betaler. |
| NIS2 Clauses | $49 | Nichemarked, høj værdi. NIS2 er nyt (2024). |
| NDA Set | $29 | Standardvare, billigere for at trække købere ind. |
| EAA Statement | $39 | Lovkrav fra 2025. Timing er perfekt. |
| Report Kit | $69 | 3 filer, højest værdi af enkeltprodukterne. |
| Bundle (-$37) | $149 | Spar 20% — lokker til upsell. |

## OBS: Ingen momshåndtering!

LS er Merchant of Record — de håndterer EU-moms og US sales tax automatisk.
Vi behøver INTET gøre. Priserne er før moms/skat; LS lægger det på ved checkout.
Sådan skal det være. Brug ALDRIG Stripe direkte.

## Efter første betaling

- Rapportér indtægten her
- Overvej om vi skal køre sandbox-køb på Pro ($79/år, abonnement) via LS dashboard
- Fjern manuel opsætning — overvej Bitwarden unlock for fuld API-automatisering