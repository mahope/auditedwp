# DECISION

Dato: 2026-08-23. Taget i oneshot-mode (ingen investor tilgængelig) under mandatets
bestemmelse: CEO'en beslutter hvad der bygges. Metode: Vej 2 fra STATUS.md —
acceptér konkurrence, vind på positionering og leverance i et beboet marked med
BEVIST betalingsvilje. Kriteriet "<2 konkurrenter" er bevidst droppet efter 22
iterationer viste det er umuligt at opfylde med web-research (mønster 1-24,
RESEARCH.md).

## Hvad

**Compliance-dokumenteret WordPress-drift (maintenance & security ops) solgt
white-label til små/mellemstore webbureauer i EU/DACH — med audit-spor.**

Ikke endnu et care-plan-abonnement. Kerneproduktet er DOKUMENTATIONSLAGET:
- Fuld ændringshistorik pr. site (opdateringer, backups, patches) som kunder kan
  fremvise ved revision, forsikring, DORA Art. 28-leverandøraftaler, NIS2-
  leverandørkæde-krav og EAA-dokumentationskrav.
- Kvartalsvis "compliance-fortælling" pr. klient bureauet kan videresælge.
- EU-hosting, EU-jurisdiktion, AVV/DPA som standard.
- Driftslaget leveres med AI-agent-automatisering (monitoring, patching, staging-
  tests) — én person + agenter erstatter det, der før krævede et hold.

## Til hvem

Køberen: ejeren af et 5-30-personers webbureau i EU (især DACH, NL, Nordics) der
(1) allerede sælger care-plans videre eller vil begynde, (2) møder kundeforespørgsler
om GDPR/NIS2/EAA-dokumentation de ikke kan besvare, (3) ikke vil bygge eget driftsteam.
Brugeren: bureauets tech lead. Beslutningstager: ejer/direktør — nås direkte, ingen
procurement.

## Hvorfor nu

1. Betalingsvilje er bevist 22 gange over: wholesale $39-100+/site/md → retail
   $100-300/site/md, margin 40-65%, tusindvis af bureauer (RESEARCH.md iter. 8-9).
2. NIS2 (leverandørkæde-ansvar), DORA Art. 28/30 og EAA skaber fra 2026-2027 et NYT
   dokumentationskrav i leverandøraftaler — de eksisterende white-label-aktører
   (TREJKA, WP Supra, fixed.net m.fl.) sælger DRIFT, ikke revisionstroværdige
   audit-spor. Det er den revne der åbner lige nu.
3. AI-agenter har netop flyttet omkostningsstrukturen: drift-ops kan leveres af én
   person. Det var ikke muligt for 2 år siden — derfor er revnen ikke allerede fyldt.

## Indtjeningsmodel

- Wholesale-pr. site: €29/site/md (0-25 sites) → €19 (26+) med 12-mdr. aftale.
  Break-even ved ~15 sites (~€350/md dækker værktøj + hosting). Mål år 1: 40 sites =
  ~€800-1.000/md netto.
- Setup-fee €290 pr. bureau (onboarding, DPA, dokumentationsskabeloner).
- Senere: kvartals-compliance-rapport som add-on €99/kvartal/bureau.
- Betaling forud månedligt, Stripe, engelsk/tysk checkout. Ingen enterprise-salg.

## Hvad der kan slå den ihjel (min hårdeste kritik — ubesvaret risiko)

1. **"X med Y"-kritikken:** drift + dokumentation er ikke radikal nytenkning. Svaret:
   mandatets fire krav er konfliktende i et marked hvor alle huller lukker på 6 md;
   dette er det bedste kompromis mellem nytænkning (dokumentationslaget er reelt nyt)
   og bevist indtjening.
2. **TREJKA/WP Supra kopierer på 3 md:** reel risiko. Modgift: dokumentationslaget er
   datamoat (ændringshistorik akkumuleres pr. klient over tid) + tysk sprog/jurisdiktion.
3. **SLA/leverance som enmandsvirksomhed:** jeg sælger BEVIDST ikke 24/7 — kun
   next-business-day-gendannelse og månedlig vedligeholdelsesvindue. Hvis en klient
   kræver 24/7, er det et nej. Skala-begrænsningen er accepteret: dette er en
   bootstrapped micro-business, ikke en VC-historie.
4. **Distribution via tillid:** CAC ukendt. Modgift: produktet er white-label = ét
   bureau-kunde-forhold dækker 5-20 slut sites; DACH-bureauer findes findelige via
   offentlige lister; indgang via gratis EAA/NIS2-dokumentations-skabeloner (content).
5. **Mads' eksisterende bureau kunne se det som konkurrence:** NEJ — det ER hans
   positionering (research-radar, aug 2026) pakket som selvstændig international
   forretning. Synergien er tilsigtet.

## Hvorfor den slog de næstbedste

- **EAA-audit-software til bureauer (iter. 2-3):** dræbt af mikrofritagelse +
  commodity-scanning ($0,10/URL) + Skiplink $249/md. Dokumentationslaget her sælger
  til dem der IKKE er fritaget og til drift — ikke scanning.
- **Productized services i construction/HOA/dental (iter. 4-6):** beviste penge, men
  USA-domænekrav (licenser, HIPAA, statslig lovgivning) jeg ikke kan løfte fra DK.
  WP-drift er jurisdiktionen jeg ER ekspert i (EU/GDPR), og hvor EU-positionering er
  en moat frem for en hindring.

## Domænenavne (prioriteret — forhåndsgodkendt køb via Cloudflare)

1. **wpscript.eu** — kort, "scripted/audited WP", .eu signalerer jurisdiktion.
   (Alternativ hvis optaget: wpscript.de for DACH.)
2. **auditedwp.com** — kerne-differentieringen i navnet; .com for internationalt.
3. **sovereignwp.eu** — datasuverænitet-positionering; stærk i DACH.
4. **eucareops.com** — bredere (kan rumme udvidelse udover WP).
5. **trustlayerwp.com** — fallback; længere, men siger dokumentations-løftet.

Anbefaling: **auditedwp.com** (positioneringen ER produktet). Estimeret pris ~$10/år
fra BUDGET.md's ramme.

## Første 30 dage (efter domænekøb)

1. Landingsside (Cloudflare Pages): pitch, wholesale-priser, DPA-skabelon download
   mod e-mail.
2. Byg pilot-infrastruktur på egne test-sites: monitoring + patch-pipeline +
   ændrings-log (bevis for dokumentationslaget).
3. 3 pilot-bureauer søges via offentlige bureau-lister — MEN kun efter Mads' ja til
   udadvendt henvendelse (grænse: ingen mails/opslag i hans navn uden godkendelse).
