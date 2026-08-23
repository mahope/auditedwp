# BUILD — korteste vej til første betalende kunde

Produkt: **AuditedWP** — white-label WordPress-drift med compliance-dokumentation,
wholesale til små/mellemstore webbureauer i EU/DACH.

## ✅ Allerede bygget (kan levere i dag)

| Lag | Status | Hvad |
|-----|--------|------|
| Landingsside EN | ✅ Live (Cloudflare Pages) | Priser, USP, margin-beregner |
| Landingsside DE | ✅ Live | DACH-markedet |
| Sample audit trail | ✅ Live | Preview af revisionsklar rapport |
| NIS2 vendor-clause template | ✅ Live | Gratis lead magnet |
| DPA-skabelon | ✅ Bygget | `site/deliverables/dpa-template.md` |
| NDA-clause-set | ✅ Bygget | `site/deliverables/nda-clause-set.md` |
| Change-log spec | ✅ Bygget | `site/deliverables/change-log-spec.md` |
| Kvartals-compliance-rapport | ✅ Bygget | `site/deliverables/` |
| Audit-trail-pipeline | ✅ Bygget, testet | `ops/auditlog.py` — stdlib Python, end-to-end |
| Margin-beregner | ✅ Live | Indbygget i landing page |
| robots.txt + sitemap.xml | ✅ Live | SEO-grundlag |
| Onboarding-manual | ✅ Bygget | `site/onboarding-manual.md` |

**Hvad der mangler for at lukke første kunde:**

```
Mads             ──→ Godkend outreach til 5 pilot-bureauer
Mads             ──→ Opret Stripe-konto (under hans navn)
Mads             ──→ Godkend DPA/NDA juridisk
Mads/Claude      ──→ Køb auditedwp.com (~70 DKK)
                 ──→ Sæt MX record så hello@auditedwp.com virker
                 ──→ Første salgssamtale → onboarding → Stripe Payment Link
```

## Den korteste vej — hvad jeg gør UDEN Mads

1. **Flyt til Cloudflare Pages** (allerede i gang) — sitet på pages.dev
2. **Skriv salgs-case til de 5 pilot-bureauer** — klar til når Mads siger ja
3. **Polér landingsside og sample audit trail**
4. **Forbered Stripe-integration** — Payment Link-opskrift, klar til at sende

## Salgs-case — hvem de 5 pilot-bureauer er

Målgruppe: 3-15 personers WordPress-bureau i Tyskland, Østrig, Schweiz eller
Norden med 10-40 WordPress-klienter.

Problemet: ejeren bruger 15-20 timer/uge på driftsopgaver der ikke skalerer.
Klienter begynder at stille NIS2/DORA-kompatibilitetsspørgsmål som ejeren ikke
kan besvare med dokumentation.

Løsningen: AuditedWP tager driften + compliance-dokumentationen. Bureauet
beholder klienten og marginen. Vi arbejder under NDA — slutkunden ved intet.

## Priser (usændret)

- Wholesale: €29/site/md (1-25) → €19/site/md (26+, 12 mdr.)
- Setup-fee: €290 pr. bureau (onboarding, DPA, white-label templates)
- Add-on: €99/kvartal/bureau for compliance-rapport

## Leverance-model (når første kunde er klar)

1. Mads modtager e-mail fra bureau → booker onboarding-samtale (20 min)
2. DPA/NDA signeres digitalt (PandaDoc el. lign. — gratis niveau)
3. Bureau giver site-adgang (SFTP/Admin) — 1-2 sites som pilot
4. Auditlog initialiseres: baseline backup + konfig-snapshot
5. Månedlig drift kører: patches, monitorering, logning
6. Månedsrapport genereres (auditlog.py → HTML → PDF) og sendes til bureau
7. Bureau videresender til klient med eget logo — klar til NIS2/DORA-revision