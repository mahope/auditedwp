# BUILD — korteste vej til første betalende kunde

Produkt: **AuditedWP** — white-label WordPress-drift med compliance-dokumentation,
wholesale til små/mellemstore webbureauer i EU/DACH.
(Se DECISION.md for fuld begrundelse. Beslutningen re-vurderet 23/8 under det nye
penge-mandat: holder — se STATUS.md.)

## Korteste vej til første euro

1. **Landingsside** (færdig): `site/index.html` + tysk version `site/de/index.html`
   (DACH = primærmarked). Statisk HTML/CSS, klar til Cloudflare Pages `*.pages.dev`.
   Sælger: hvad, til hvem, pris, hvordan man køber.
   Lead magnet: gratis DPA/NIS2-leverandørklausul-skabelon.
2. **Checkout**: Stripe Payment Links (gratis at oprette) — månedligt abonnement
   pr. tier + setup-fee. Ingen backend nødvendigt for de første kunder.
3. **Onboarding-manual**: `site/onboarding-manual.md` (færdig).
4. **Pilot-infrastruktur**: MainWP (self-hosted, gratis) eller WP Umbrella
   (€1,99/site/md) på egen test-site → ændrings-log + kvartalsrapport-skabelon
   som bevis for dokumentationslaget. Bygges når første pilot-bureau er tæt på.
5. **Udadvendt rekruttering**: KRÆVER stadig Mads' eksplicitte ja (grænse i
   AGENTS.md). Landingssiden kan dog konvertere organisk/SEO fra dag 1.

## Priser (som i DECISION.md)

- Wholesale: €29/site/md (0-25 sites) → €19/site/md (26+, 12 mdr.)
- Setup-fee: €290 pr. bureau (onboarding, DPA, dokumentationsskabeloner)
- Add-on senere: kvartals-compliance-rapport €99/kvartal/bureau

## Hvad jeg IKKE bygger nu

- Ingen kunde-dashboard, ingen billing-infrastruktur, ingen automatiserings-
  pipeline før mindst ét bureau har betalt. Alt leveres manuelt + eksisterende
  værktøj i starten (concierge-MVP). Software først når manuel leverance gør ondt.

## Blokeret på Mads

1. Domæne auditedwp.com via Cloudflare (~70 DKK, forhåndsgodkendt). Indtil da:
   `auditedwp.pages.dev`.
2. Ja/nej til udadvendt henvendelse til pilot-bureauer (mails i hans navn).
3. Under hvis navn oprettes Stripe-kontoen?

## Leverance-pakke (BYGGET 23/8, iter. 26)

`site/deliverables/` — alle løfter fra pristabellen findes som rigtige
dokumenter: DPA-skabelon, NDA-klausulsæt, white-label månedsrapport,
kvartals-compliance-fortælling, change-log-format-spec. Første betalende
bureau kan betjenes dag 1. Forbehold: juridisk review før første underskrift.

## Konverterings-tilføjelser (iter. 27-28)

- Interaktiv margin-beregner på landingssiden (`site/index.html`, #calc):
  to sliders → live omsætning/omkostning/margin. Ren klient-JS.
- Tysk landingsside `site/de/index.html` (DACH er primærmarkedet i
  DECISION.md) — fuld oversættelse af pitch, priser, FAQ, med hreflang-
  links og sprogvælger EN/DE i navigationen.
- `site/robots.txt` + `site/sitemap.xml` til organisk indeksering fra dag 1.
- Kanoniske URL'er + hreflang (en/de) på begge landingssider.

## Verificering (iter. 30)
- Alle 4 sider validerer rent (html-validate); JS syntakstjekket OK (node).
- DE-siden har NU margin-beregneren — den manglede faktisk trods notitsen
  herunder (rettet iter. 30; lærdom: byg-påstande verificeres før de skrives).

## Deploy (iter. 29)

`site/deploy.sh` — én kommando: `sh site/deploy.sh`
(kræver engangs `npx wrangler login`). Efter deploy er sitet live på
https://auditedwp.pages.dev med det samme.
