# DECISION

Dato: 2026-08-23 (iteration 32 — pivot efter Mads' nul-indsats-krav).

## Nul-indsats-testen (det afgørende krav)

Mads rejser væk i 3 måneder uden internet → forretningen skal stadig tjene penge
ved hans hjemkomst. Alt der kræver kundesupport, manuel levering, løbende
beslutninger, salg eller uendelig indholdsproduktion er kasseret.

## Hvad

**ComplianceDocs — butik for færdige, advokatinspirerede B2B-compliance-dokumenter
til EU-regulering (EAA, NIS2, DORA, GDPR), solgt som digitale downloads.**

- Køberen: webbureau-ejer, SaaS-stifter eller selvstændig konsulent i EU/DACH der
  skal bruge en DPA, NDA-clause, vendor-audit-clause eller dokumentations-skabelon
  I MORGEN — og ikke vil betale en advokat €500-2.000.
- Produktet er filen: markdown/PDF, leveret automatisk efter betaling.
- Portefølje (bygget, i `site/deliverables/`): DPA-skabelon, NDA-clause-set,
  NIS2 vendor-clause, change-log-spec, kvartals-compliance-rapport-skabelon.
  Flere følger: EAA-tilgængelighedserklæring, DORA-leverandøraftale-clause,
  AI Act-disclosure-tekst — hver bygget én gang, solgt uendeligt.

## Hvorfor nu

EAA trådte i kraft juni 2025 (håndhævelse fra juni 2025), NIS2 og DORA ruller
ud i 2026 — tusindvis af små virksomheder får dokumentationskrav de ikke kan
opfyldte uden rådgivning. Advokater sælger samme dokumenter for €500-2.000;
Termly/iubenda beviser betalingsviljen i software-laget. Fil-laget mellem
"gratis blog-indhold" og "advokat på €500/time" er tyndt beboet på
$29-149-niveauet.

## Indtjeningsmodel

- Pris: $29-79 pr. dokument (bundles $99-149). Checkout + merchant-of-record
  via Lemon Squeezy eller Paddle (de står for moms/faktura — nul administration).
- Automatisk levering: fil/e-mail efter betaling. NUL manuel trin.
- Mål: 10 salg/md = ~$500-800. Skalerer uden ekstra indsats.

## PRAECIS hvad der sker UDEN menneskelig indgriben

1. Kunde finder sitet organisk (SEO/indhold bygget på forhånd, statisk hosting).
2. Læser salgsside + fuld sample-preview, klikker køb.
3. Betaler via Lemon Squeezy/Paddle checkout — MoR håndterer kort, moms, kvittering.
4. Modtager dokumentet automatisk (download-link + e-mail, leveret af platformen).
5. Pengene udbetales til kontoen månedligt.
6. Hvis siden går ned: Cloudflare Pages statisk hosting — ingen server der kan
   gå ned; hvis checkout-platformen fejler, viser siden en fejl og intet tabes.

**Hvad der ville kræve menneskelig indgriben (og derfor IKKE sker):**
- Tilpassede dokumenter på forespørgsel → NEJ, sælges ikke.
- Refusion: pengene-tilbage-garanti uden spørgsmål, håndteret af MoR's
  refund-flow — ingen samtale nødvendig.
- Nye dokumenter ved ny lovgivning → VALGFRI vækst, ikke drift. Gamle produkter
  står selv og sælger videre uden vedligeholdelse.
- Support: dokumenterne er self-contained; support-volume forventet <1 time/md.
  Hvis den vokser, er svaret en FAQ-side, ikke flere timer.

**Eneste engangsopgave:** Lemon Squeezy/Paddle-konto under Mads' navn skal
oprettes og godkendes én gang (kræver hans identitet/bank — kan ikke gøres af mig).

## Hvad kan slå den ihjel (min hårdeste kritik)

1. **Ingen trafik = ingen salg.** Største risiko. Modgift: statisk SEO-site med
   gratis mini-versioner af dokumenterne som lead-magnets; indholdet rangerer på
   2026-reguleringssøgetermer der er NYE og derfor ikke fuldt swarmet. Hvis
   trafikken aldrig kommer, tjener det 0 — men det koster også ~0 at stå, og
   testen er opfyldt: det kræver ikke Mads.
2. **"Det er bare skabeloner."** Ja — og det er pointen. Kedeligt er fint.
3. **Juridisk risiko:** dokumenterne sælges som "templates, not legal advice" med
   tydelig disclaimer — standard i branchen.
4. **MoR-afvisning af konto.** Fallback: Gumroad (ingen godkningsmur, højere gebyr).

## Hvorfor den slog de næstbedste

- **AuditedWP drift (forrige beslutning):** bevist marked, men FEJLER
  nul-indsats-testen — drift er per definition manuel leverance og support.
- **EAA-audit-SaaS:** kræver drift, SLA, support; swarmet af Skiplink.
- **Generisk skabelon-butik (Gumroad):** power-law kommodity uden distribution.
  Compliance-vertikalen har pris-tolerance og smerte som generiske skabeloner mangler.

## Domæne

auditedwp.com er forkert navn nu. Nye kandidater (forhåndsgodkendt, Cloudflare):
1. **complidocs.com** — kort, siger hvad det er.
2. **eudocs.shop** — jurisdiktion + butik.
3. **compliancefiles.com** — bogstaveligt.
Anbefaling: complidocs.com hvis ledig; ellers eudocs.shop. ~$10/år. Sitet kan
fortsætte på pages.dev indtil videre — ingen blokering.

## Første 30 dage

1. Byg produktsider for 5 dokumenter med fuld sample-preview + disclaimer.
2. Sæt checkout op (Lemon Squeezy — kræver Mads én gang).
3. SEO-sider: "NIS2 vendor clause template", "EAA accessibility statement
   template" osv. + gratis mini-versioner som lead-magnet.
4. Bundle-side: hele porteføljen $149.
