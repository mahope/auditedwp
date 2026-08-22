# RESEARCH

Arbejdsmappe: hermes-ceo/ (skriveadgang bekræftet 23/8).

## Iteration 20 (2026-08-23): Sidste radarkørsel — 2 nye signaler, begge døde. Finalister: NUL. Fasens konklusion er endelig.

Metode: STATUS.md's plan for iter. 20 var "dybere grav i finalisterne der stadig står".
Verificering viste: der findes INGEN finalister tilbage — alle ~92 kandidater fra iter. 1-19
er døde ved dybdegrav, den sidste (EU white-label WP-drift) blev fuldt due diligence-gravet
i iter. 9. I stedet kørtes radaren (HN Algolia) én sidste gang for signaler EFTER iter. 19's
kørsel kl. 01:34. 20 hits; 2 var grave-værdige:

### R8: Convictional (YC W19, ~$49M USD raised) — DØD: PIVOT-FIASCO, INGEN BRUGERBASE
Lukker 27/8-2026. Vigtigt: IKKE et graveyard med levende efterspørgsel. Dropship-delen
(Modern Dropship: 3.000 kunder, $2M ARR, $83M GMV) blev solgt til konkurrenten **Carro**
i 2025 — markedet for dropship vendor-onboarding er besat (Carro + Rithum + 10 leverandør-
onboarding-platforme, atlassystems.com top-10 2026). Pivot 2.0 (Slack-alternativ til
AI-æraen) fejlede på distribution: store firmaer bygger selv, små vil have billigere
Slack-kloner, "sustainable distribution remains an unsolved problem" (founder-citat,
BetaKit 20/8). Founder returnerer <halvdelen af de $49M til investorer.
→ DØD: intet at arve; autopsien bekræfter tværtimod mønster 21 (nedenunder).

### R9: Open Science Framework (stopper nye uploads nov. 2026) — DØD: OFFICIEL EFTERFØLGER EKSISTERER
OSF lukker for nye fil-uploads pga. spam-misbrug og ulovlig privat-lager-brug
(cos.io/blog). Tusindvis af forskere skal flytte — men hullet er fyldt FØR begravelsen:
**ResearchBox** (datacolada.org/137) er allerede den officielt anbefalede destination
(8.970 forskere, AsPredicted-integration, Zenodo+Internet Archive-mirroring med DOI,
anti-spam-design bygget PRÆCIS mod OSF's problemer). Plus gratis generalister:
Zenodo, Dataverse, institutionelle repositories (MIT/MSK/Arizona-libguides).
→ DØD: samme mønster som TV Time — efterfølgeren var klar og markedsført inden
lukningen. Akademisk marked oveni = lav betalingsvilje.

### Nyt mønster (nu 20 iterationer)
21. Pivot-dødsfald (Convictional) er en NY graveyard-variant uden arv: når et VC-backet
    firma lukker fordi PMF ALDRIG blev fundet, er der ingen betalende brugerbase at
    arve — signalet er en advarsel, ikke en mulighed. Graveyard-screeningen skal
    skelne mellem (a) lukket med levende betalende efterspørgsel (arv — men altid
    swarmede, mønster 16) og (b) lukket uden PMF (ingen arv).

### ENDGILTIG FASE-KONKLUSION efter 20 iterationer (~92 kandidater, 14 metoder)
Alle finalister er gravet, dømt og dokumenteret. Alle live-signaler er swarmede inden
for dage (målt ned til "før shutdown-datoen"). Web-research kan bevise markeder, ikke
finde ubesatte. Der findes ikke flere iterationer der kan ændre dette resultat uden
ny input-type: primærdata (interviews), distributionskanal, eller en strategisk
beslutning fra Mads. Se STATUS.md.

## Iteration 1 (2026-08-22/23): 36 kandidater → 4 finalister + F5
Se git-history eller RESUMÉ nederst for den fulde tabel. Finalister: F1 chargeback-defense
(STR hosts), F2 EAA-audit for små webshops, F3 job-dokumentation/scope-creep,
F4 late-payment defense, F5 SMV compliance-radar.

## Iteration 2 (2026-08-23): Dybde-research af finalisterne — ALLE DØDE

### F1 Chargeback-defense for STR-hosts — DROP
- Airbnb er merchant of record og "absorberer alle chargeback-omkostninger, vi sender dem
  aldrig videre til hosts" (Airbnb Engineering, medium.com/airbnb-engineering). Det fjerner
  selve det økonomiske smertepunkt for langt de fleste platform-bookinger.
- Sept. 2025-politikrygte om øget host-ansvar er uverificeret selv af Airbnb-support
  (thehost.co) — for tyndt fundament til at bygge en virksomhed på.
- Konkurrenten Checkout Shield (checkout-shield.ezzon.nl) gør PRÆCIS evidence-dokumentation
  med GPS/tamper-evident proof til hosts. Hullerne er allerede fyldt.
- Win-rate-tal ("70% med stærk evidence") kommer kun fra content-marketing-sider uden kilder.
→ Død: problemet er mindre end antaget, og løst af eksisterende aktør.

### F3 Scope-creep/job-dokumentation — DROP
- Markedet er tættere end antaget: ScopeSnap, ProofOfService, Settled, Scopify (AI SoW,
  Gemini-drevet), WaffleInvoice. Medianpris for proposal-features $35/md (microgaps.com).
- Distribution til freelancers/håndværkere er dyr, betalingsvilje lav, og well-funded
  spillere kan overhale os. Ingen forsvarbar kant.

### F4 Late-payment chaser — DROP
- Chaser (UK, rapporterer 75% DSO-reduktion) og InvoiceSherpa er etablerede OG profitabele
  (microgaps.com/gaps/2026-02-17). Plutio inkluderer automated reminders i sit $19/md-produkt.
- Hele idéen er offentligt udstillet som færdig blueprint på MicroGaps — enhver indie hacker
  kan bygge den samme uge.
- Freelancers er notorisk dårlige software-kunder; pengene kan vi ikke rykke uden licens.

### F2 + F5 EAA/compliance for små EU-webshops — DROP I NUVÆRENDE FORM
Nye fund (23/8):
- **Mikrofritagelse:** Virksomheder <10 ansatte OG <€2M omsætning er FRI taget for EAA-services
  (accessible.org/counts-as-microenterprise-under-eaa; altaudit.com). Det skærer bunden —
  altså størstedelen — af det europæiske shop-marked væk som tvunget målgruppe.
- **Reel håndhævelse findes dog:** tyske claimant law firms sender cease-and-desist-breve til
  mindre shops (Freshfields, nov 2025); første franske sager nov 2025; hollandske audits 2026
  (gocreativeai.com EAACheck-listing). Smerten er reel — men hos de lidt større.
- **Prisanker kollapset i bunden:** EAACheck API $0,10/URL (axe-core/Lighthouse mod EN 301 549);
  accessiBe fra $490/år; UserWay $49/md; Shopify-app "Accessibility Manager Pro" $9,99-29,99/md
  (lancering feb 2026) med scans, rapporter og compliance-certifikater. Scanning er commodity.
- **I toppen:** manuelle audits koster $1.250-2.750 pr. digital asset (Accessible.org),
  $1.500-5.000 (DigitalA11Y); Siteimprove-mediankontrakt ~$28.000/år; enterprise-platforme
  high five figures (auditsu.com buyer's guide).
- **White-label til bureauer findes allerede som MENNESKESERVICE:** accessibilitychecker.org
  agency-program, testparty.ai partnerships, halfaccessible.com, accessiblepixels.com — alle
  leverer audits/remediation under bureauets brand. Software-værktøj til bureauernes egen
  workflow er derimod ikke tydeligt dækket — UTESTET hypotese, se STATUS.
→ Død som "billig scanner/dashboard til små shops": mikrofritagelse + $10/md-konkurrence +
  copybar axe-core = ingen forsvarbarhed. Frygt-salg til en fritaget gruppe konverterer ikke.

### F5 (SMV compliance-radar EAA+GDPR+NIS2) — DROP SOM OPRINDELIGT Tænkt
- GDPR-SMB-markedet har 256 listede værktøjer (krowdbase); OneTrust/TrustArc presser nedad;
  EAA-benet rammer mikrofritagelsen. Et "radar-dashboard" er feature, ikke produkt, og
  håndhævelsen varierer pr. land = fragmenteret salg.

## Mønster på tværs af fiaskoerne (vigtigere end de enkelte grave)
1. De 4 finalister solgte til folk LAVE penge (hosts, freelancers, mikro-shops) — betalings-
   vilje og -evne lav, CAC høj, churn høj. Alle overlevede ikke mødet med konkurrent-data.
2. Hvor regulering skaber reelle penge (Tyske C&D'er, franske sager), tjener BUREAUER og
   konsulenter på dem — ikke slutkunden. Audit-priserne ($1.250-2.750/asset) viser at der ER
   margin i leverance-laget, bare ikke i et $19/md-abonnement til shop-ejeren.
3. Alt der kan beskrives som "axe-core + rapport" er allerede commodity ($0,10/URL).
   Forsvarbarhed skal ligge i workflow, integration eller ansvar — ikke i scanningen.
4. MicroGaps udgiver færdige blueprints til disse idé-typer: hvis en idé kan opsummeres i ét
   blogindlæg, er den ikke værd at bygge alene.

## RESUMÉ iteration 1 (bevaret)
36 kandidater screenet; kilder: chargebacks911.com, eur-lex 2019/882, plutio.com,
handl.works, nis-2-templates.com m.fl. — fuld kandidattabel ligger i git-history af denne fil.

## Iteration 3 (2026-08-23): Bureau-hypotesen afkræftet + 3 nye kandidatklasser testet — ALLE DØDE

### H1: White-label audit-software til web/compliance-bureauer — AFKRÆFTET (hypotesen fra iter. 2)
Software-hullet var IKKE utestet. Det er fyldt, og mere end én gang:
- Skiplink.dev/for/agencies — $249/md Agency-plan, unlimited clients, white-label PDF, API/CLI,
  "agencies charge $1,250-2,750 per audit, automated part takes us 3 seconds".
- Accessiscan (piposlab) — white-label WCAG/VPAT til bureauer, "we run the engine, you own the client".
- Decareto — white-label platform, custom domains, API, €34/md for 5 sites.
- ADA Scanner Business-plan, adaguard.io (Duda-agenter), gitnux top-10-liste.
→ Død: mindst 5 dedikerede aktører, prispunkt $249/md, ingen differentieringsmulighed tilbage.

### K1: VSME/CSRD-kaskade til SMV-leverandører ("ét VSME-rapport svar til alle kunder") — DROP
- Markedet er allerede pakket: ExecutESG (gratis Basic / €49/md Pro), Greenly, Eevery, Ecobio,
  Sustainova (gratis), Dcycle, csr-tools (Word-skabelon fra €699). 7+ sammenligningsartikler.
- Omnibus I (feb 2026) skar direkte CSRD-omfang fra ~49.000 til ~1.000 virksomheder —
  kaskade-presset er politisk ustabilt fundament.
- Prisniveauet er kollapset i bunden (gratis-tiers). Ingen kant.

### K2: BFSG/Abmahnung-response-værktøj til tyske shops — DROP
- Abmahnung-bølgen er reel (€1.780 + €490 typisk krav, anden bølge med audit-rapporter),
  men responsen er allerede industrialiseret af tyske aktører: Eye-Able, accessibility-check.ai,
  sitecockpit, usableaccess, IT-Recht-Kanzlei m.fl. — gratis guides, betalte services.
- Samme problem som F2: mikrofritagelse + commodity-scanning + copybar axe-core.

### K3: CBAM nær-grænse-importører (30-50 t/år, "de-minimis watch") — DROP
- Konkurrenttæthed: CarbonAtlas (gratis Excel + platform, "400+ importers"), Import Safe-Pass,
  CarbonOps, SustainGRC, Bindu (€2.876/år, offentlig pris), Autocbam, Dubrink (€1.990/år),
  Digicust, IntegrityNext, osapiens, CBAMBOO — 10+ platforme dækker ALLEREDE de-minimis-
  tracking som feature ("threshold engine flags declarant status automatically").
- 50-t-grænsen fritager ~182.000 importører (~90%) — det resterende marked er lille, og
  alle platforme jager det. Prispresset: €0-480/år i bunden.
- CBAM udvides dog mod downstream (180 stål/aluminiums-produkter annonceret dec 2025) —
  det er en FREMtidig bølge, men CarbonChain m.fl. har allerede positioneret sig.

### K4: DORA Register of Information for små betalingsinstitutter — DROP
- 12+ platforme sammenlignes i 2026-købereguides (Vendorica €299/md, Legiscope €5-30k/år,
  DORApp, Venvera, Vanta, ComplyJet, 3rdRisk, OneTrust...). Gratis EBA-Excel-skabelon + 3-4
  gratis community-templates (RiskNow, Orbiq, Vendorica) betjener bunden.
- Kun ~40% af berørte firmaer havde indsendt RoI pr. 16/3-2026 (regreportingdesk) — smerten er
  reel, men markedet er allerede overbefolket, og EBA's xBRL-CSV-format kræver tung compliance-
  infrastruktur som enmandsvirksomhed ikke kan løfte troværdigt.

### K5 (bi-fund): EUDR SME-traders — DROP
- EUDRReady gør PRÆCIS "collect DDS refs, store 5 years" for €29-79/md med gratis tier.
  Coolset, osapiens, TechUltra dækker resten. Hullet er lukket før jeg nåede dertil.

## Mønster efter 3 iterationer (nu hårdt bekræftet)
1. ALLE EU-reguleringsbølger fra 2024-2026 (EAA, CSRD/VSME, CBAM, EUDR, DORA, BFSG) har
   allerede en tæt software-swoop: 5-12 konkurrenter pr. niche, flere med funding.
   Regulatorisk timing-alonen er IKKE en moat i 2026 — vinduet lukker på 6-12 mdr.
2. Hvor jeg graver, finder jeg altid (a) en gratis tier eller skabelon i bunden, (b) en
   VC-backet platform i midten, (c) enterprise i toppen. Compliance-SaaS er rødt hav på
   tværs af ALLE reguleringer jeg har testet.
3. Det jeg IKKE har testet: klasser hvor værdien ikke er "compliance-artefakt" — fx
   data-udtræk/integration-lag, vertikale workflows med operationel smerte (ikke regulatorisk),
   eller markeder hvor køberen tjener penge PÅ værktøjet (agenter som distributører).

## Næste iteration skal
Se STATUS.md — kort: drop hele "EU-compliance-software"-klassen som hovedspor; generér 15+
kandidater i (a) operationelle vertikaler uden regulatorisk driver, (b) tool-for-agencies
hvor agenten tjener på værktøjet, (c) data/integration-infrastruktur. Krav: bevist betalings-
vilje, <2 direkte konkurrenter, og en moat der ikke er "vi læser reglerne først".

## Iteration 4 (2026-08-23): Operationelle vertikaler + tool-for-agencies — 12 kandidater screenet, 0 finalister

### Screenet og dræbt i første grav (konkurrenttæthed)
1. **Dental insurance verification (software)** — 6+ platforme i 2026-købereguides alene:
   Zuub ($500/md solo), Savvy Agents Milo ($200/md, 300+ payers), Vyne Trellis, Pearl Precheck,
   DentalRobot ("automatiserer 93% af RCM-opgaver"), Medusind QuickVerify, PatientXpress,
   CareStack. (avized.com, savvyagents.ai, themolarreport.com, dentistdecoded.com, jul 2026)
2. **Dental verification outsourced service** — eAssist prissætter $11–12,50/verification ASAP;
   Outsource Strategies fra $3; DentalClaimSupport $6,50–8,25; offshore BPO'er (Flatworld,
   Staffingly) + remote staffing $375–500/uge. Fuldt besat på tværs af alle prispunkter.
3. **STR host permit/registration tracking** — Regulatr findes allerede med PRÆCIS denne pitch
   (EU 2024/1028-deadline 20/5 2026, Austin delister 1/7); Avalara MyLodgeTax dækker licenser
   + lodging tax og har OwnerRez-integration. (regulatr.info, avalara.com)
4. **HOA board meeting minutes AI** — BoardBreeze ($29,99–499/md), MinuteSmith (lavere pris,
   action-tracking), PerfectHOA, My Condo Space (Canada), HOACart.AI, Musely generisk værktøj.
   Plus menneskeservice: FirstMotion $59/møde, CondoVoter $185, OTR $190+. Markedet er
   mættet på under et år. (appboardbreeze.com, minutesmith.com, firstmotionservices.com)
5. **Lien waiver management** — Siteline top-13-liste; $400–800/md GC-planer. Besat.
6. **COI tracking** — 12 platforme testet og reviewet (myCOI, TrustLayer, Billy, CertFocus
   $6–8/vendor selvbetjening). Rødt hav. (scryai.com, vertikalrms.com)
7. **Carrier packet onboarding (freight brokers)** — Highway + MyCarrierPackets dominerer.
8. **Tip payout compliance** — Kickfin, TipHaus, Ferry, Gratuity Solutions (patenteret siden 2009).
9. **Equipment rental / driving school / marina / campground / swim school vertical SaaS** —
   hver niche har 3–6 etablerede platforme (Quipli, Dockwa/Molo, Zutobi, PayHOA m.fl.).
10. **Receipt chasing til bogholdere** — ReceiptNudge + Receipt Bot + hele TaxDome/Karbon-
    portalklassen dækker det.
11. **Chargeback representment** — Chargeflow, Chargebacks911, Riskified m.fl. (også F1-arv).
12. **Utility bill auditing** — Nectar, Utilified, TrueMeter ("AI agents audit every bill").

### Dybde-gravet og droppet med begrundelse
- **K6: Verifikations-infrastruktur (API/white-label) til dental billing companies.**
  Hypotesen var: software-aktørerne mangler human-QA-laget (Needletail nævner eksplicit
  "No human QA layer" som svaghed), så sælg QA-as-a-service oven på Zuubs API til de små
  billing-firmaer der videresælger verifikation til $6,50–12,50 stykket.
  → DROP: (a) Zuub tilbyder ALLEREDE selv white-label/embedded API (zuub.com/dental-insurance-
  eligibility-verification-api) — infrastruktur-laget er deres kerneforretning, ikke et hul;
  (b) min "moat" ville være et tyndt arbitrage-lag oven på en leverandør der kan gå direkte
  til kunden; (c) HIPAA/BAA som enmandsvirksomhed i EU over for amerikanske patientdata er
  en compliance-byrde jeg reelt ikke kan løfte troværdigt.
- **K7: Human-in-the-loop minutes-service til HOA management companies** (tool + service,
  $59–99/møde, distribueres via management-firmaernes egne kunder).
  → DROP: markedet allerede dobbeltbesat — både software (BoardBreeze/MinuteSmith/PerfectHOA)
  og menneskeservice (FirstMotion $59/møde med 24-t levering). Prisen er allerede sat af en
  konkurrent, og differentieringsmuligheden er væk. Lærte mønster fra iter. 3 gentager sig:
  enhver "AI + menneskelig QA"-idé i en synlig niche er allerede bygget.

### Mønstre (nu 4 iterationer)
5. Enhver vertikal med synlig smerte OG dokumenteret betalingsvilje har allerede 3–10 aktører.
   Det skyldtes at micro-SaaS-værktøjet (AI + skabeloner) er blevet så billigt at bygge, at
   første-mover-forspringet er 3-6 måneder. Jeg finder altid sporene EFTER swoop'en, fordi
   købereguides/content-marketing først indexerer 6-12 md efter lancering.
6. De steder hvor der stadig ER penge (audit-priser, per-meeting-priser, per-verification-priser),
   ligger de i SERVICE-leverance med ansvar/relations-moat — ikke i software-abonnementet. Men
   services kræver domæneautoritet (HIPAA, statslig lovgivning, branchekendskab) jeg ikke har
   på dage 1, og distributionen går gennem relationer, ikke søgning.
7. Det jeg systematisk IKKE har kunnet teste udefra: nicher hvor smerten er usynlig i
   søgningen (folk klager ikke offentligt), og moats der bygger på proprietær data-akkumulation
   over tid. Det kræver en anden researchmetode end web-søgning — fx interviews eller
   community-deltagelse over uger.

### Konklusion iteration 4
Ingen kandidat overlevede kriteriet "<2 direkte konkurrenter efter dybde-grav". Jeg skriver
ikke DECISION.md. Web-søgningsbaseret idé-generering ser ud til at have nået sit loft: den
finder kun markeder der allerede er synlige — og dem er der altid andre i.

## Næste iteration skal
Se STATUS.md.

## Iteration 5 (2026-08-23): Community-grav i 3 nicher (vej 1) — ALLE 3 MÆTTED

Metode: i stedet for bred screening, grav direkte i klager/tråde fra folk der BRUGER de
eksisterende værktøjer i de tre nicher hvor iter. 3-4 havde dokumenteret betalingsvilje.
Hypotesen var at finde usynlige smerter som købereguides endnu ikke har indexeret.

### N1: Dental front office / RCM — MÆTTET, også i appeals-nichen
Selve smerten er veldokumenteret og reel (r/dentist, r/Insurance: verifikation "takes hours",
holdtider 45 min–3 t, $25-118 pr. denial-rework iflg. MGMA). Men hvert lag er besat:
- **Appeals/narratives:** DentaPrism ($49/md AI Appeal Generator + 17+ templates),
  Omniscient Partners (gratis appeal-letter generator), Toothy AI (end-to-end AR med human QA),
  Staffingly (outsourced denial management, 2 ugers onboarding), Zentist, DentalRobot.
  (dentaprism.com/appeals, toothydocs.com, staffingly.com, aug 2026)
- Selv foji.io's kritiske indlæg ("most dental AI tools fall short — it's offshore arbitrage
  with a UI") konkluderer at svaret er FLERE full-service-udbydere, ikke et nyt værktøjshul.
→ Død: smerten er stor, men hele værdikæden fra template → AI-draft → human-in-the-loop →
full BPO er allerede leveret af mindst 6 aktører på alle prispunkter $0-$500+/md.

### N2: HOA management / selvstyrende boards — MÆTTET + DÅRLIG KØBER
Reddit r/HOA-tråde (aug 2026) bekræfter kaos: issues rapporteres via opkald/SMS/email/i forbifsåen,
"we reported this already"/"no one followed up", boards bruger Gmail-labels, Google Docs,
manila-mapper. MEN: svarene på trådene er altid det samme — PayHOA, HOA Start, HOA Life,
ManageCasa, CINC, Solume m.fl., hver med violation-tracking og intake-portaler. Og en tråd-
deltager markedsfører aktivt sit eget Lovable-prototypeprodukt (NeoHome) i kommentarerne —
selv hobby-byggere er i gang med netop denne idé.
→ Død: markedet er dobbeltmættet (software + management-selskaber), køberen er frivillige
ubetalte boards med lav betalingsvilje — samme fejl som F1/F4.

### N3: Construction pay applications (AIA G702/G703) for små subs — MÆTTET I BEGGE ENDER
Smerten er den mest dokumenterede hidtil: subs venter i gennemsnit 90 dage på betaling,
1/3 kommer for sent, $208 mia. tabt/år (Siteline/Levelset); håndudfyldte pay apps tager
2-5 timer stykket = 12-30 timer/md ved 6 projekter (projul.com); én afvist pay app kan
forsinke $80k+ i 60-90 dage. Excel er stadig normen blandt små subs (r/electrical,
r/ConstructionManagers).
Men markedet er lukket i begge ender:
- **Software:** Siteline (subs, ~$400-800/md), Trimble Pay (ex-Flashtract), GCPay ($3.999/år),
  Knowify, Buildertrend — OG Payapps.com som allerede dækker bunden med $49/md (1 kontrakt),
  $120 (3), $150 (5), pay-as-you-go $65/claim. Mit antagede "hul under Siteline" er fyldt.
- **Service:** PayAppUSA laver PRÆCIS productized-service-spillet — $300/pay app (SOV +
  G702/703 + submission + collection follow-up), $400 med fuld månedsbilling, $500 med
  client representation. Houston-baseret enmandsfirma på Squarespace.
  Silver Cloud Accounting går endnu dybere: vertikal niche (el/mekanisk subs i NoVa
  datacenter-korridoren), fixed monthly retainer, tiered controllership. (payappusa.com,
  silvercloudbooks.com, aug 2026)
→ Død: både software-bunden OG service-modellen er allerede bygget, inkl. af solo-
iværksættere. Enhver indgang jeg havde, har en konkurrent med forspring.

### Metode-konklusion efter iteration 5 (vigtigst)
Også community-grav via web-søgning rammer det samme loft: i det øjeblik en smerte er
synlig i Reddit/Facebook-tråde, er den også synlig for hundredevis af andre micro-SaaS-
byggere — og sporene viser at de handler på det (NeoHome-prototypen i HOA-tråden er
beviset). "Usynlige smerter" kan ikke findes med søgemaskine; de kræver samtaler.
Web-baseret research uanset form (screening ELLER community-grav) er udskiftningsteknik.

### Konklusion
Ingen DECISION.md. Ingen kandidat overlevede. Jeg vil IKKE sætte egne penge i nogen af
de tre, og jeg kan ikke forsvare nogen mod min egen kritik.

## Iteration 6 (2026-08-23): "Betalt humant arbejde pr. styk"-minedrift — 4 kandidater testet, ALLE DØDE

Ny metode-testet denne gang: i stedet for at lede efter klager (smerte-signal), led efter
HVOR folk faktisk betaler mennesker for tilbagevendende arbejde pr. enhed (betalings-signal).
Hypotesen: hvis mennesker bliver betalt $X pr. styk for noget tilbagevendende, findes der
et productizeringsspil — og måske er software-hullet der endnu. Resultat: signalet er
pålideligt, men hvert enkelt marked var allerede dækket i begge ender.

### P1: Permit expediting (byggelicenser, USA) — DØD: VC-backet + bootstrappede + software
Betalings-signalet var stærkt: $400-$15.000 pr. permit (permitcpr.com, permitsguide.com),
monthly contractor plans $5.000-7.500+/md (mcpeckgroup.com), flat fees $500-750/permit
(permitatl.com). Men markedet er fuldt struktureret:
- PermitFlow: $91M funding (Accel, Kleiner Perkins, YC), SaaS $350/md (ustechautomations.com).
- Pulley: $4.4M seed, CitySync mod 19.000 jurisdiction-portaler, ekspert-netværk.
- Permit Place: 20 år, bootstrappede, profitable, flat fee $4.000-7.000/TI, offentlig
  timeline-database over 642+ byer (deres egen moat: data akkumuleret siden 2006).
- 7+ tracking-platforme fra Jobber $49/md til enterprise $1.500/md (ustechautomations.com).
→ Moaten her er lokale relationer til building departments + jurisdiktionsdata over år.
  Ikke tilgængelig på dag 1 fra Danmark.

### P2: Restaurant invoice data entry — DØD: AI har allerede spist mellemleddet
Signalet: manuel indtastning koster $15-26/faktura, offshore BPO $1,50-4,00, AI <$1
(invoicedataextraction.com cost guide, apr 2026). Break-even ved 200 fakturarer/md.
AI-automatisering er allerede billigere end BPO ved næsten alle volumener, og mindst én
aktør (Invoice Data Extraction) sælger pay-as-you-go uden abonnement med gratis 50 sider/md.
→ Klassisk "menneske-arbejde der lige er blevet erstattet af commodity-AI". Intet hul.

### P3: Business license renewal / annual report filings — DØD: $9/md monitoring eksisterer
Signalet: virksomheder betaler formation-services $125-249/år for registered agent +
compliance-pakker; staternes gebyrer $0-800/år. Men:
- file.business gør PRÆCIS "monitor deadlines + alert + per-filing filing" fra $9/md/entity
  (Monitoring) / $29/md (Business OS med filing), SOC 2, state fees pass-through.
- CorpNet, Northwest, ZenBusiness, LegalZoom, Bizee har alle ongoing-compliance-tjenester.
- Gratis niveauer: read-only compliance-kalender hos file.business, gratis state lookups.
→ Bundprisen er sat ved $9/md af en dedikeret aktør. Ingen plads.

### P4 (screening): VA-opgave-markedet generelt — DØD SOM IDÉ-KLASSE
Managed VA-services $1.500-4.000/md (prialto.com, rosetalentsolutions.io $2.500/md nearshore).
Retainer-kategorierne på Upwork (content/SEO, ads mgmt, dev, support, dashboards) er alle
allerede produktiseret af hundredvis af bureauer (uphunt.io retainer-guide, blogarama top-19).
Enhver "productize den tilbagevendende VA-opgave"-idé lander i et felt af eksisterende
productized agencies.

### Metode-konklusion (iteration 6)
"Betalt humant arbejde pr. styk" er det stærkeste research-signal jeg har fundet — det
beviser betalingsvilje direkte i stedet for at inferere den fra klager. Men i alle fire
tilfælde var markedets struktur (VC-platform + bootstrappede services + commodity-software)
allerede komplet når man graver ét lag dybere. Signalet finder pengene; det finder ikke huller,
fordi hvor der er dokumenterede penge, er der også allerede konkurrenter.

### Samlet konklusion efter 6 iterationer (~52 kandidater screenet)
Ingen DECISION.md. Jeg kan ikke forsvare nogen kandidat mod min egen kritik. Alle fire
metoder (bred screening, dybde-grav i finalister, community-grav, betalings-signal-minedrift)
konvergerer mod samme resultat: alt der er findeligt med web-søgning er enten mættet eller
strukturelt utilgængeligt (relation-moats, licens-moats, kapital-moats).

## Iteration 7 (2026-08-23): De tre sidste utestede kandidatklasser — ALLE 3 DØDE

Sidste utestede klasser fra iter. 3's mønster-liste, testet for at lukke research-fasen
udtømmende: (a) teknologiskift-bølger uden compliance-artefakt, (b) AI-governance/tillid,
(c) "sælge skovle til vindere". Resultat: samme mønster hver gang.

### T1: IRS FIRE→IRIS-systemskift (31/12 2026) — DØD: HELE markedet har allerede swoopet
Signalet var stærkt: FIRE (1980'ere-platform) nedlægges permanent 31/12 2026; alle der
e-filer 10+ information returns SKIFTES til IRIS; ny IRIS-TCC tager op til 45 dage;
navnefelt-splitting og XML-format kræver data-audit; stater bruger stadig FIRE-format =
dobbelte workflows i overgangsperioden; første tvungne IRIS-sæson = jan-mar 2027.
Kilder: irs.gov, tabservice.com (jun 2026), 1099pro.com, boomtax.com, morado1099.com,
efilemyforms.com, blog.taxbandits.com (aug 2026).
Men konkurrentbilledet ved første grav:
- BoomTax: "if you use BoomTax, nothing changes — we handle the IRIS transition automatically".
- TaxBandits: tiered pricing $0,80-2,75/form + dedikeret CPA/tax-pro produktlinje.
- Tax1099 ($0,68-2,99/form), Avalara/Track1099 ($0,63-3,10), Yearli/Greatland,
  eFileMyForms, Morado, ftwilliam.com — 8+ aktører, alle IRIS-ready, alle med content
  marketing der allerede rangerer på "FIRE to IRIS transition".
→ Død: bølgen er reel, men indholdsmarkedet OG softwaremarkedet besatt før januar 2026.
En ny aktør i august 2026 er 4+ måneder før deadline mod virksomheder med 40 års
leverandørrelationer. Ingen kant.

### T2: California ADMT / AI-governance-compliance (deadline 1/1 2027) — DØD: overbefolket
Reglerne gælder kun virksomheder over CCPA-tærsklerne (~$25M omsætning eller store
persondatavolumener) — altså enterprise/mid-market, ikke SMV (mayerbrown.com, jan 2026;
cppa.ca.gov). Og markedet er allerede pakket på alle lag:
- ADMT.ai (forsikring af AI-agenters beslutninger), Causum/Mars (decision-time governance,
  PRNewswire feb 2026), Direktiv.ai (agent-inventory platform), VerifyWise (open-source
  CCPA/ADMT-modul), Risk Meridian (udtrykkeligt SMB-prissat AI-governance), Polyphemi
  (managed AI model inventory til finansielle institutioner).
→ Død: samme mønster som EAA/DORA/CBAM — regulatorisk bølge, 6+ dedikerede aktører inden
for 12 måneder, inkl. en der allerede jager SMB-segmentet. Compliance-SaaS-klassen forbliver
rødt hav på TVÆRS af alle jurisdiktioner jeg har testet (EU + US delstater).

### T3: "Sælge skovle til AI-bureauer" (tool-for-agencies) — DØD I SCREENING
Reddit/LinkedIn-grav (r/AI_Agents, r/automation, r/Entrepreneurs, aug 2026) viser at
AI-agency-markedet selv er i krise ("AI agencies are dying in 2026"; "simple automations
are dead") — køberne er tusindvis af lavkapitalede solopreneurs, ikke en solid købergruppe.
Og tool-laget er allerede bygget af dem der vandt platform-spillet: ClickUp Brain,
storyflow.so's top-12-agency-tools-guide indexerer markedet fuldt.
→ Død: distribution til et fragmenteret, lavbetalingsvilligt segment — samme fejl som
F1/F4/N2. Ingen grund til dybere grav.

### Samlet konklusion efter 7 iterationer (~55 kandidater)
Alle seks metoder konvergerer. De tre sidste klasser bekræfter det strukturelle fund:
enhver bølge med dokumenterede penge har en software-swoop inden for 6-12 måneder efter
at reglen/deadline er annonceret, og den er indexeret af content-marketing før jeg når
dertil. Web-research kan bevise markeder; den kan ikke finde ubesatte markeder.
Research-fasen er nu UDTØMMENDE på web-metoder. Videre fremdrift kræver primær data
(interviews) eller en strategisk beslutning fra Mads — se STATUS.md.

## Iteration 8 (2026-08-23): Mads' ordre om én iteration til — mit eget spor testet som FORRETNING (ikke kun positionering)

Ny vinkel: alt min research-radar (EU-datasuverænitet, driftpakker, sikkerhed, white-label)
har hidtil været behandlet som POSITIONERING for Mads' bureau. Denne iteration behandlede
den som selvstændige kandidater med konkurrent-grav.

### W1: White-label WordPress-drift/care-plans til bureauer — MÆTTET I KERNE-MARKEDET
Konkurrenter fundet ved første grav (alle med offentlige partner-programmer):
WP Buffs (20% white-label-rabat), SiteForza ($62/site wholesale vs $150-200 retail),
WP Care Pros (UK, margin-beregner på siden), Web Help Agency (NA/AU/UK), Seahawk Media,
E2M Solutions, ThriveWP, Icecube Digital, The White Label Agency,
wordpressmaintenanceservice.com ("plans from $39/month", 4-timers SLA), Bobcares.
Prisstrukturen er fuldt industrialiseret: wholesale $39-100+/site/md → agency sælger
$100-300/site/md, margin 40-65% (webhelpagency.com, belovdigital.agency, 2026-guides).
→ Kernen er et rødt hav af leverandører på alle prispunkter.

### W2: EU-datasuverænitet som forskel — REEL, MEN TYND REVNE
Positive fund: næsten ingen af de store white-label-udbydere positionerer sig på
EU-hosting/DSGVO-first. Kun fragmenterede EU-tilbud: Accentio (GDPR maintenance,
EU-servers), Maintenance-WP (FR), yarify.tech (GCP EU white-label hosting), Sitenyx
(platform, EU-hosting + audit-hash-chain), Templ (SE/DE datacentre). DACH-købere er
dokumenteret mest aggressive på AVV/DPA/Schrems II/EU-backups (thebrownbrick Berlin-guide);
DORA Art. 28/30 kræver kontrakt-klausuler om EU-datacenter og EU-supportpersonale
(wppoland.com DORA-artikel). Værktøjslaget har dog allerede en EU-vinder: WP Umbrella
(Frankrig, €1,99/site/md, eksplicit markedsført på "EU-only data processing") — software-
laget af EU-hullet er taget; tilbage er SERVICE-leverancen.

### Hvorfor jeg ALLIGEVEL IKKE skriver DECISION.md — min hårdeste kritik
1. Ikke nytænkende efter mandatets definition: "white-label WP-drift med EU-hosting" er
   præcis "X, men med Y". Moaten er placering og sprog — let kopieret af enhver EU-bureau.
2. Service-forretning der kræver leverancekapacitet (døgnvagt, opdateringer, hacketilbage-
   førsel). Som AI-enmandsvirksomhed kan jeg ikke levere 24/7-SLA troværdigt fra dag 1 —
   samme strukturelle problem som K6/HIPAA i iteration 4.
3. Distribution går gennem tillid og relationer til bureau-ejere, ikke søgning; uden Mads'
   netværk aktivt involveret er CAC ukendt og sandsynligvis høj.
4. Teknologien er commodity (WP Umbrella/MainWP); det der resterer at sælge er ansvar og
   arbejdstimer — jobs, ikke software-skala.
KONKLUSION: Den bedste kandidatklasse jeg har fundet på 8 iterationer, plausibel som
MADS' BUREAUS positionering (vej 2) — men ikke som selvstændig international forretning.
Jeg ville ikke sætte mine egne penge i den som produkt.

## Iteration 9 (2026-08-23): Sidste finalist gravet i bund — EU white-label WP-drift DØD som selvstændig forretning. Research-fasen afsluttet med konklusion.

Metode: fuld due diligence af den ene tilbageværende kandidatklasse fra iteration 8
("EU-jurisdiktions driftspartner for webbureauer") på de fire punkter der manglede:
konkurrenter på service-laget, reel markedsstørrelse, prissætning, kundetilgang.

### Ny fund 23/8-2026

**EU/GDPR-positionerede konkurrenter på service-laget (ikke bare software):**
- **TREJKA** (PL, familiefirma siden 2010, 400+ WP-sites) — fuldt white-label
  driftsprogram med wholesale pr. side: ~€25-35/side/md netto, EU-backup-cloud,
  NDA + skriftligt forbud mod at kontakte bureauets kunder, SLA for 15+ sider.
  Eksplicit margin-beregner på siden ("du fakturerer €399, vi koster €109").
  (trejka.com/en/for-agencies)
- **WP Supra** (CH/DE) — "one of the most comprehensive white-label WordPress
  maintenance programs in Europe", schweiziske servere, 300+ klienter,
  250k+ opdateringer/år; op til 1 års gratis drift i onboarding.
  (einpresswire.com aug 2026, wpsupra.com/de)
- **fixed.net** (DK/EU!) — white-label reseller med EU-hosting inkluderet,
  prisfaldende pr. site (£16-33/site/md ved 30 sites), 24/7, branded client area.
  Danskt rodfæstet konkurrent jeg ikke havde set i iter. 8. (fixed.net/eu)
- **Skynetix** (GR/EU) — 100% anonymt white-label med NDA'er, fixed wholesale-
  pakker (€470-1.699 engangs + årlig maintenance €120-350). (skynetix.eu)
- **CMS ADMINS** (München) — direkte DACH-slutkundemarked €63-131/md med
  staging-tests, 60-dages realtime backups, tysk support. (cms-admins.de)
- **Forge12** (DE) — fastpris WordPress-bureau med "GDPR-compliant, EU-hosted"
  som standardpositionering, Care ab €59/md. (forge12.com)
- **peaknetworks.at**, **managedserver.eu**, **040hosting.nl** — EU-reseller/
  agency-hosting med white-label + DPA som standardtilbud.
→ Konklusion: "ingen positionerer sig på EU" fra iter. 8 var forkert. Revnen er
ikke bare tynd — den er allerede beboet af mindst 6 europæiske aktører, hvoraf
én er dansk (fixed.net) og én polsk (TREJKA) sælger PRÆCIS modellen med
wholesale-priser offentligt.

**Pris-/margin-struktur bekræftet endnu engang:** wholesale $39-100+/site/md →
klientpris $100-300/site/md, margin 40-65% (wordpressmaintenanceservice.com,
wpflora.com $49-79 wholesale / $199 retail, fatlab $59-79/site). Ingen plads til
prisdifferentiering; EU-positionering giver ingen præmie — Accentio tager
$99-249/md for det samme som US-aktører.

**Markedsstørrelse:** intet nyt. Tusindvis af små bureauer, fragmenteret, lav
kontraktstørrelse, distribution via tillid/relationer. WP Umbrella alene har
5.000+ bureau-kunder og 80.000 sites (aug 2026) = værktøjslaget konsolideret.

### Min hårdeste kritik — finalen
1. Ikke nytænkende efter mandatets egen definition ("X, men med EU-servere").
2. Moaten er placering+sprog; nu bevist allerede kopieret af 6+ EU-aktører.
3. Service-SLA kræver leverancekapacitet (døgnvagt) enmandsvirksomhed ikke kan
   løfte troværdigt fra dag 1.
4. Distribution via relationer til bureau-ejere; CAC ukendt uden Mads' netværk.
5. Bedste tilfælde: lille stabil servicevirksomhed med dansk timepris og
   international konkurrence fra Polen/Tyrkiet/Indien på samme arbejde.
KONKLUSION: Jeg ville IKKE sætte egne penge i den som selvstændig international
forretning. Den forbliver relevant kun som positionering for Mads' eksisterende
bureau (STATUS vej 2).

### Endelig konklusion på research-fasen efter 9 iterationer (~60 kandidater)
Alle syv metoder (screening, dybde-grav, community-grav, betalings-signal,
tech-shift-bølger, eget spor, due diligence af finalisten) konvergerer:
- Synlige markeder er besat af 5-12 aktører inden 6-12 md efter signalet.
- Usynlige markeder kan ikke findes med web-søgning — kun med interviews.
- Web-research kan bevise at et marked findes; den kan ikke finde ubesatte.
Research-fasen er udtømmende afsluttet på tilgængelige metoder. Videre fremdrift
kræver Mads' valg mellem de tre veje i STATUS.md (interviews / acceptér
konkurrence som del af bureauet / moat-pivot med distributionsopbygning).

### Næste iteration skal
Ikke flere web-research-iterationer — fasen er lukket. Afventer Mads' beslutning.

## Iteration 10 (2026-08-23): Mads' ordre om endnu en iteration — jobopslags-minedrift (metode 8)

Ny metode: i stedet for klager eller betalte services, led i JOBSOPSLAG — hvor virksomheder
hyrer FOLK til tilbagevendende digitalt arbejde. Et opslags-signal er stærkere end et klage-
signal (nogen er villige til at betale en LØN, ikke et abonnement). Kandidater:

### J1: Amazon Seller Central case-management / catalog-fixes — MÆTTET I BEGGE ENDER
Signalet var det stærkeste hidtil: hele stillinger hyres ("Marketplace Listing Specialist",
"Ecommerce Operations Specialist" med flad filer, suppressions, case-opfølgning som kerne-
opgaver; virtustant.com, persona-talent, jobera.com aug 2026). Priserne er høje:
- Freelancer pr. ASIN: $20-108/ASIN (zinnhub), $149/ASIN (fecoms), bulk flat-file $150-400/projekt.
- Productized retainers: Parker-Lambert $500/md (1 request ad gangen!), $900/md;
  Seller Candy $797-2.500/md unlimited tasks; CentralDesk (ex-Amazonians) ticket-model.
- Full-service agencies $997-7.500/md (dotcomreps, supplykick).
- Reinstatement: ecommerceChris $1.500/ASIN, $4.000-5.000/account.
Men konkurrenttætheden er TOTAL: SellerPlex har PRÆCIS modellen inkl. "Backlog Cleanup"
som trin 2 i onboarding; ecombrainly gratis audit + 48t fix; Jarvio (AI account health);
SellerSonar/eComEngine (suppression-alerts); FlatFilePro ($19-99/md flat files); ReimburseOps
$19/md reimbursements. Hver micro-segment af arbejdet har en dedikeret aktør på alle
prispunkter fra $19/md til $5.000/md. → DØD: samme mønster igen — signalet fandt pengene,
men markedet var besat før jeg nåede dertil.

### J2: Multichannel listing/crosslisting software — DØD I SCREENING
Job-signalet findes også her (listings-specialists på tværs af Amazon/Etsy/Walmart/eBay),
men værktøjsmarkedet har 20+ aktører fra $4,99/md (OneCart) over Vendoo/List Perfectly/
Crosslist/Nembol/Sellbrite ($9-179/md) til ChannelAdvisor/Rithum enterprise. (getonecart,
resaleos, rglister købereguides 2026.) → Rødeste hav hidtil.

### J3: Etsy/eBay/Walmart seller support & reinstatement — DØD
Etsy-appeals: Fiverr-giggere fra få dollars + AMZ Sellers Attorney $1.500-2.300 attorney-led.
eBay: StarterX, spctek m.fl. Walmart: ingen dedikeret service-marked fundet — men heller
ikke dokumenteret betalingsvilje (kun generiske VA-bureauer). → Enten mættet eller intet marked.

### J4: Stripe/payout reconciliation for SMB — DØD
Smerten er reel og målt (4-6 timer/uge pr. entitet, finlens.app jun 2026; r/Bookkeeping-tråde).
Men Acodei $12/md, Synder $15-599/md, Finlens (gratis starter), Webgility, HubiFi $1k+/md —
hele spektret besat. → Samme mønster.

### J5: TikTok Shop ops for små brands — INGEN DOKUMENTERET BETALINGSVILJE I BUNDEN
Agency-markedet findes (Canopy, Darkroom, AmpliSell buyer's guide) men jager brands med
volume; små sælgere betjenes af generiske VA-bureauer (KavaBD, assistworld). Intet hul med
dokumenteret betaling. → Ikke bevisbar.

### Metode-konklusion (8 metoder nu testet)
Jobsignal-metoden bekræfter de 7 foregående: hvor virksomheder hyrer mennesker til repetitivt
digitalt arbejde, er der ALLEREDE et komplet økosystem af freelancere (Fiverr/ZinnHub $20+),
productized services ($500/md) og software ($12-99/md). Konkurrence-tætheden korrelerer
positivt med signal-styrken — det er netop dér andre byggere kigger.

## SAMLET KONKLUSION EFTER 10 ITERATIONER (~65 kandidater, 8 metoder)
Research-fasen er udtømmende lukket. Alle otte metoder konvergerer:
synlige markeder er besat; usynlige kræver interviews. Ingen DECISION.md — jeg kan ikke
forsvare nogen kandidat mod min egen kritik. Afventer Mads' valg mellem de tre veje i STATUS.md.


## Iteration 11 (2026-08-23): Metode 9-10 — mikro-opkøbssignaler + 1-stjerners-minedrift i vindere

Der stod ingen finalister tilbage efter iter. 10, så "dybere grav" udfyldtes med to nye metoder.

### M1: Acquire.com/Flippa-mikro-opkøbs-signaler — DATA, IKKE HULLER
615 live listings analyseret (bigideasdb.com State of SaaS Acquisitions 2026): median asking
$190K, gennemsnit 2.6x TTM revenue / 10.7x profit. ~50% af exits skyldes founder-attention,
ikke døde produkter. Konklusion: markedet for at KØBE bevisede micro-SaaS er flydende —
men alt der listes er per definition allerede bygget og jaget. Metoden beviser at exit-vejen
findes (vigtig for indtjeningsmodellen), men finder ingen ubesat niche. Nyttig som kendsgerning,
død som idé-generator.

### M2: 1-stjerners-anmeldelsesminedrift i etablerede vindere (ny metode) — ÉN REVNE FUNDET, ALLEREDE BEBOET
Hypotese: i stedet for et tomt marked, find revnen i vinderen i en vertical med dokumenteret
betalingsvilje (fra iter. 4-5: HOA, construction pay apps).

**Siteline (pay apps):** 3.3/5 rating (iconpolls); kendte svagheder er opaque pricing + årlig
binding — men bunden er allerede dækket af Payapps.com $49/md (iter. 5) og PayAppUSA-service.
Ingen ny revne.

**PayHOA (HOA-software, 573 anmeldelser):** ægte revne fundet — Florida-statutlaget.
HB 913 (2025)/HB 1021 (2024) kræver: records-request med 10-arbejdsdags-ur + $50/dag bøde,
statutlig website-of-record med versionering (25+ units, deadline jan 2026), 48t/14dags-notices
med affidavit, fining-committee-validering, milestone/SIRS-recordkeeping, director-certification
90-dages-ur. PayHOA dækker INGEN af delene (hoarocket.com teardown; hoaengineer.com origin-story).
Men revnen er allerede beboet af mindst 4 aktører:
- HOA Rocket (Revis-1 LLC) — dedikeret §718/HB913-compliance-software, live
- HOA Engine — board-president-bygget, live beta på Space Coast
- LEADR (leadrdesign.com) — compliance-infrastructure service til inspection firms/CAMs
- FloridaSIRS.org + condo.insure — SIRS-tool og unit-insurance-tracking
→ DØD SOM KANDIDAT: (a) 4+ aktører inde i revnen før mig; (b) markedet er ÉN amerikansk
delstat — strider direkte mod det internationale krav i mandatet; (c) jeg har ingen Florida-
domæneautoritet fra Danmark.

### Mønstre (nu 11 iterationer)
8. "Revnen-i-vinderen"-metoden virker teknisk (den fandt en ægte, veldokumenteret feature-gap),
men gapet i enhver synlig vertical er også synligt for de 4-10 andre byggere der læser samme
anmeldelser — og mindst én af dem bygger hurtigere end mig, ofte som insider (HOA Engine blev
bygget af selve board-presidenten). Domæneautoritet slår fjernarbejde hver gang i vertikaler
med jurisdiktions-specifik compliance.

## Iteration 12 (2026-08-23): Metode 11 — sproglig arbitrage (ikke-engelsk web)

Den ene metode der reelt ALDRIG var testet i 11 runder: al research har kun læst det
engelsksprogede web. Hypotese: bevist, betalende produkter i Japan/Tyskland/Korea/Frankrig
uden engelsk pendant ville være det eneste sted et ubesat marked kan gemme sig. Testet på
tre vinkler:

### S1: "Copy til Vesten"-minedrift (JP/KR → EN) — INGEN KONKRET HUL, STRUKTURELT PROBLEMATISK
Fund: Korea køber ikke SaaS (SI-dominans; koreanske SaaS-firmaer kan ikke sælge hjemme og
omvejen går via Japan — LINE WORKS #1 i Japan, #5 i Korea). Japan er "goldilocks zone in a
bad way": stort nok marked til at succesfulde founders aldrig behøver at internationalisere.
De få niches der findes (naver-scraper-API'er osv.) er allerede dækket af indie hackers på
RapidAPI. Konklusion: de fleste JP/KR-produkter uden vestlig pendant mangler den, fordi
modellen ikke transporterer (keiretsu/SI-salg, ringi-købskultur) — ikke fordi ingen har set dem.

### S2: Japan akiya/overseas-owner administration — DØD VED FØRSTE GRAV
Signalet var stærkt: 9 mio. tomme huse, 60% af udenlandske investorer bedømmer info-adgang
som "dårlig" (MLIT), og 2025-26-regler straffer aktivt fraværende ejere (管理不全空家-tab af
skattefordele op til 6x ejendomsskat; Kyoto tomgangsskat fra regnskabsår 2026; tvungen
納税管理人 tax representative + 国内連絡先 kontaktadresse; arveregistrering tvunget siden
4/2024). MEN konkurrentbilledet ved første grav:
- **Japan YES Property Management** — præcis modellen: tax rep + kontaktadresse +
  mailscanning/oversættelse + billpay, ¥66.000-154.000/år + setup ¥22.000, spot-services.
- **MailMate** — akiya/Airbnb-pakke ¥14.800-29.800/md + ¥66.000 setup, tax agent service,
  kundecases med Akiya Collective og AkiyaMart som PORTFOLIO-kunder.
- **AKIYA2.0** — fuld manage-linje, ¥85.000 sign-on + ¥15.000/md.
- **Property Management Kyoto** — offentlig prisguide for hele segmentet.
→ DØD: (a) mindst 4 aktører på alle prispunkter inden for samme niche; (b) moaten er FOLK
PÅ JORDEN I JAPAN — fysisk nøglehåndtering, post, kommunekontakt — umulig at levere
troværdigt fra Danmark; (c) sprog-moaten vender imod mig: kunderne vil have japansk-talende
på stedet.

### S3: Tysk marked (Fredy, Immopix m.fl.) — bekræfter kun mønstret
Tyske niches har allerede engelsk-eksportørende aktører (Immopix "now available in English",
Fredy open-source). Ingen ubesat importmulighed fundet.

### Mønster (nu 12 iterationer)
9. Sproglig arbitrage virker teknisk — den fandt et ægte, regulatorisk tvunget smertemarked
   (S2) på under én time. Men selv her var hullet fyldt: når smerten er lov-pålagt OG synlig
   for englæs-talende købere (alle guides rangerer på Google), swooper engelsktalende
   byggere det også. Den sidste "usynlige zone" er mindre end antaget, fordi selve
   efterspørgslen (engelsksprogede købere) skaber engelsksproget konkurrence.
10. Strukturel konklusion på tværs af ALLE 11 metoder: hver gang jeg finder dokumenteret
    betalingsvilje, finder jeg også 3-12 konkurrenter der nåede dertil før mig — og moaten
    hos vinderne er altid noget jeg ikke kan købe med arbejdstimer: domæneautoritet,
    fysisk nærvær, relationer, licens eller kapital.

### SAMLET KONKLUSION EFTER 12 ITERATIONER (~70 kandidater, 11 metoder)
Research-fasen er nu udtømmende inkl. ikke-engelsk web. Ingen kandidat overlevede min egen
hårdeste kritik. Der skrives ingen DECISION.md. Alle veje frem kræver input Mads skal give
(interviews via hans netværk, accept af konkurrence som del af bureauet, eller
distributionsopbygning først). Se STATUS.md.

## Iteration 13 (2026-08-23): Metode 12 — agent-economy (markeder hvor KØBEREN er en AI-agent)

Den sidste utestede klasse: det eneste sted hvor min egen natur (AI-agent) kunne være en
moat i stedet for et handicap. Testet på tre lag:

### A1: Betalt MCP-server / pay-per-call API (x402) — MARKEDET ER REELT MEN ~$23K/MD I ALT
Infrastrukturen er i produktion: x402 (Coinbase/Linux Foundation) ~$600M annualized volume,
AWS Bedrock-native maj 2026, Stripe-integration feb 2026. MEN målinger af den faktiske
betalende økonomi (agentatwork.xyz paged hele Bazaar-kataloget 13/8; philpher0x.dev uafhængig
replikation):
- Hele den opdagelige økonomi: ~$23.500-26.000/md på tværs af ~15.000 services.
- Top 1 endpoint (Bitrefill gavekort) = 60%; top 100 = 85%. Kun 27 services tjener >$50/md.
- Kategorier: rails/gift cards $16k, crypto-data $3k (424 aktører!), search/scraping $1,3k.
- NetIntel-operatørens egne data (101 endpoints): én transformation-endpoint = 42% af revenue;
  35 af 101 endpoints har ALDRIG været betalt for. Én enkelt køber bag toppen.
→ DØD SOM FORRETNING: selv at være top-30 endpoint ud af 15.000 giver < $500/md. Monetize-
platformene (MCPize 85% rev share, Apify 80%, MCP Marketplace) er infrastruktur-spillet og
er allerede bygget. "5% af 12.000 MCP-servers tjener noget."

### A2: Agent-payment-infrastruktur (facilitators, protokoller) — BESAT AF GIANTE
x402 = Coinbase; MPP = Stripe+Tempo; ACP = OpenAI/Stripe/Meta; AP2 = Google+100 partnere;
Visa TAP + Cloudflare. Alle fire lag (discovery, authorization, checkout, settlement) har
en platform-ejer. Ingen plads for enmandsvirksomhed.

### A3: "Agent-readiness"-audits til merchants — ALLEREDE BEBOET PÅ ALLE PRISPNKTER
Hullet lignede bedst: virksomheder skal gøres agent-læselige, og Cloudflare udgav officiel
"Agent Readiness score". Men:
- Gratis: pagechecks.com checker (MCP/WebMCP/x402/ACP), jwatte.com audit, Cloudflare Radar,
  openhermit.com 15-point checkliste.
- Solokonsulent: muratulusoy.de sælger PRÆCIS audits (16 signals, MCP/x402/ACP) allerede;
  digitalstrategyforce.com har enterprise-framework + 90-dages sprints; mudko sælger en
  $350 "website agent-readiness package" på selve x402 Bazaar.
- Readable.ai m.fl. bygger GEO/AI-visibility-produktlinjen oven på det.
→ DØD: samme mønster som EAA-audits (iter. 2-3) — commodity-scanning i bunden, konsulent-
service i midten besat, enterprise framework i toppen. Og købermarkedet (A1) viser at den
samlede agent-betalingsøkonomi stadig er mikroskopisk.

### Mønster (nu 13 iterationer)
11. Selv klassen hvor jeg strukturelt burde have fordel (agent-til-agent handel) er (a)
    målt for lille ($23k/md globalt på største facilitator) og (b) besat på alle fire
    infrastruktur-lag af Stripe/Coinbase/Google/OpenAI/Cloudflare/Visa. Leverance-laget
    ovenpå (audits, integration) følger præcis compliance-SaaS-mønsteret fra iter. 2-3.
12. ENDGILTIG STRUKTUREL KONKLUSION: Der findes pt. ingen synlig, betalende markeds-niche
    som en alenefounder uden kapital, licens, fysisk nærvær eller eksisterende distribution
    kan gå ind i med web-research som eneste redskab. Det er ikke en anke mod idé-generering
    — det er et målbarhed-resultat på tværs af 12 metoder og ~75 kandidater.

## Iteration 14 (2026-08-23): Metode 13 — retsdata-minedrift (PACER/domsignal)

Ny metode (valgt selv da ingen bruger var til rådighed ved afklaring): minedrift i
føderale retssager og domstolsstatistik — kilder hvor smerten er dokumenteret med PENGE
eller tab, men som micro-SaaS-byggere der kun læser Reddit/købereguides sjældent ser.
Fundet den stærkeste enkelt-smerte på alle 14 iterationer: **"Schedule A"-masselitigation**
mod marketplace-sælgere. Og alligevel: klassen dør på tre uafhængige grunde.

### Signalet (stærkere end alt hidtil)
- 4.211 trademark-sager filed i US district courts i 2025 (+25% / +848 sager vs 2024);
  stor del er Schedule A-masse-sager hvor ÉN klage navngiver 100-250+ sælgere via et
  bilag, under seal, og får ex parte TRO der fryser ALLE deres midler hos Amazon/eBay/
  Walmart/PayPal/Payoneer inden 24-72 timer. Mange opdager først at de er stævnet da
  kontoen fryser. (ipwatchdog.com apr 2026; columbialawreview.org "SAD Scheme";
  chicagoiplitigation.com)
- Konsekvensen ved passivitet er brutal: default judgment op til $2.000.000 willful;
  eksempel Lovitedo v. Schedule A Defendants: $141.219 dom mod én ikke-opdukkende
  Amazon-sælger, midlerne overført direkte fra frosset konto på 225 dage. (patsnap.com)
- Selv uskyldige rammes: i Collectanea-modsag beviste eBay at >halvdelen af 50 testede
  sælgere ALDRIG havde solgt en anklaget vare; 25 af 50 var verificerede US-virksomheder.
  Domstol opløste PI mod alle 252 defendarter for improper joinder. (chicagoiplitigation,
  mar 2026)

### Hvorfor klassen ALLIGEVEL er død — tre uafhængige drabsgrunde
1. **Preventiv-side besat:** Trohub (trohub.com) gør PRÆCIS hele hypotesen — AI-scanning
   af produktbilleder/listings mod USPTO/EUIPO design patents + trademarks + reverse-image
   copyright + LIVE TRO/Schedule A-database (10.000+ cases indexeret), bulk CSV-katalogscan,
   API + agent-integration, gratis trial, pay-per-scan eller abonnement, kinesisk+engelsk.
   Plus AZAlert ($79,97 lifetime brand-risk alerts), TrackMyOrders IP Catcher, SellerSprite,
   GleanMark/Sealvo (AI trademark clearance), TrademarkDashboard (£9,99/scan).
   Screening-laget er commodity før jeg nåede dertil.
2. **Responsiv-side kræver advokatlicens:** TRO-forsvar/fund-release er domineret af
   specialiserede law firms med dokumenterede resultater (AMZ Sellers Attorney: 75+ TRO'er,
   $5M+ frigjort, $3.000 flat; CJ Rosenbaum/Amazon Sellers Lawyer; Valley Summit Law;
   krepplaw). En ikke-advokat kan ikke lovligt levere selve værditilbuddet (UPL-problem),
   kun lead-gen — og lead-gen til advokater er i sig selv et mættet felt.
3. **Bølgen er politisk/juridisk på vej NED, ikke op:** NDIL-dommere har startet et
   systematisk opgør — improper joinder-dissolutioner (Kocoras mar 2026), skærpede
   bond-krav, "Dyson $1.000 per defendant"-normer (ericgoldman.org, årets udviklinger
   2025), Law.com "A Reckoning for Schedule A?", NYSBA reform-opfordringer, Second Circuit
   forbød email-service på Kina-defendarter dec 2025 (Hague Convention). Hele produktets
   marked (mængden af masse-navngivne sælgere) bliver aktivt regulatorisk formindsket.
   Ny variant af mønster 1: bølge-RETNING skal tjekkes — nogle bølger er på vej ned når
   web-research når frem.

Bonus: kernekøbergruppen er kinesiske cross-border-sælgere (Trohub er tosproet netop
derfor) — distribution går gennem kinesiske økosystemer (WeChat, seller-communities),
utilgængelig fra Danmark uden udadvendte handlinger i Mads' navn.

### Delsignaler tjekket undervejs (alle døde eller kommodity)
- UK civil justice stats (gov.uk Q1 2026): small claims ~37,6 uger til trial, 450k money
  claims/kvartal — volumen reelt, men claim-prep fyldt af no-win-no-fee + MCOL-flow;
  intet hul identificerbart uden primærdata.
- India NCH e-commerce complaints: 20 lakh/5 år, 79.818 non-delivery i 2025 — FORBRUGER-
  klager mod platformene, ikke en købersmerte man kan productisere internationalt.

## SAMLET KONKLUSION EFTER 14 ITERATIONER (~78 kandidater, 13 metoder)
Uændret: research-fasen er udtømmende på tilgængelige metoder. Ingen DECISION.md.
Afventer stadig Mads' valg mellem de tre veje (interviews / acceptér konkurrence /
moat-pivot) i STATUS.md.


## Iteration 15 (2026-08-23): Metode 14 — post-mortem/graveyard-minedrift ("død leverandør, levende efterspørgsel")

Ny metode: i stedet for at lede efter klager eller betalte services, led efter produkter der er
NEDLAGT med aktiv brugerbase — hvor efterspørgslen overlevede produktet. Hypotese: her er
betalingsviljen bevist af den døde leverandørs historik, og konkurrent-swoopen skulle teoretisk
kunne være langsommere end ved regulering-bølger. Resultat: hypotesen fejlede på alle fem test-
tilfælde — graveyard-huller er de HØJESTE signaler af alle og derfor de hurtigst besatte.

### G1: GummySearch (Reddit-research, lukket nov 2025 — Reddit API-licens dræbte den)
135.000+ brugere mistede deres værktøj. Men gapet var fyldt inden for måneder:
RedReach, Reddily, ReddinBox (kommerciel API-klon), RedNudge ($7-19/md, offentlige endpoints),
Shadow Inbox ($49-249/md, intent-scoring), Insightios (done-for-you rapporter), Syften,
SparkToro som nærmeste store. Mindst 8 aktører kæmper om resterne.
→ DØD. Og selve kategorien bærer platform-risk (Reddit kan lukke alle efterfølgere samme måde).

### G2: Shopify Stocky (lukket 31/8 2026 — annonceret juni 2026)
Native PO/reorder-lag for POS-butikker. Community-tråd fra 15/6 viser mønsteret i mikroskop:
inden 31/7 — seks uger efter annonceringen — var mindst syv erstatnings-apps live eller i beta
(Prediko $49+, Stockful $19,99, Sensible Forecasting $29, Sumtracker, Fabrikatör, SKUSavvy,
Replenora gratis/-$29), PLUS mikro-byggere der disclosede sig selv i tråden (Replenora, InvoRescue,
FyreTrail, happy_helper's app, Stockporter-beta). Én tråd-deltager opsummerede det præcist:
"it is the loudest gap, so it is the one everybody is aiming at. The quieter gaps have less
competition" — men de stille gap han pegede på, havde HAN selv allerede bygget et produkt til.
→ DØD. Swarm-latency er nu ~6 uger fra annoncering til mættet bund.

### G3: InkFrog (eBay-listing-værktøj, Wix-ejet, lukket 1/6 2026)
Hele migrations-markedet besat ved deadline: Snap2List (AI-listings + InkFrog-kuponer),
3Dsellers, Salestio ($29-299/md), DashVue (UK VAT-niche!), Vooltist, MyListerHub — hver med
content-marketing der rangerer på "inkfrog alternative" INDEN shutdowndatoen.
→ DØD. Selv SEO-spillet omkring et graveyard er besat før begravelsen.

### G4: Chartable (podcast-attribution, Spotify-ejet, lukket dec 2024)
Ét år senere: "the dust is settled and the new landscape looks dramatically different"
(Podglomerate-webinar) — Podkite (gratis-$50/md), Podstatus ($5+/md), Podgagement ($9-19/md),
CoHost, Magellan ListenLinks, Linkfire. Panel-konklusion: "the measurement gap has largely
closed". SmartLinks-attribution er den eneste halvfærdige rest — men kræver podcast-ecosystem-
distribution jeg ikke har.
→ DØD. Selv det mest citerede "no direct replacement"-hul lukkede på under et år.

### G5: Coverfly + The Tracking Board + Done Deal Pro (screenwriting-ecosystem, Cast & Crew,
lukket aug-sep 2025). Det mest interessante graveyard: ScriptMatch har bygget PRÆCIS den
funktion alle migrations-guides kalder "the genuine gap nobody is talking about" — buyer
intelligence / "who's buying now" — og er live med leaderboard + database. StoryNotes,
betterdraft.io, Scrybe, Kinolime m.fl. har taget coverage/hosting-sliverne. FilmFreeway (samme
ejer!) tog contest-tracking. Contest-deadline-aggregatoren (MovieBytes, Scrybe, Creative
Screenwriting) findes stadig som gratis lister — men betalingsviljen for en $5-10/md tracker
er udemonstreret, og ISA/FilmFreeway dækker behovet gratis.
→ DØD som kandidat; bekræfter blot mønsteret endnu engang.

### Mønster (nu 15 iterationer)
13. Graveyard-metoden fandt de STÆRKESTE efterspørgsler hidtil (beviste brugerbaser, dokumenteret
    betaling) — og i samtlige fem tilfælde var swarmen komplet inden for 6-12 måneder, ofte
    før selve shutdowndagen. Årsagen er strukturel: et nedlagt produkt med levende efterspørgsel
    er det mest synlige mulighedssignal der findes — alle byggere læser de samme obituarer og
    migrations-guides. Signal-styrke og konkurrent-tæthed korrelerer perfekt, igen.
14. Metoden kan kun vindes af den der er FØRST til obituaren — dvs. har distribution/lyttepost
    i realtid. Min research er per definition bagefter: jeg læser det web der allerede er indexeret.
15. SAMLET ENDKONKLUSION EFTER 15 ITERATIONER (~85+ kandidater, 14 metoder): Alle 14 metoder —
    inkl. den sidste utestede — konvergerer mod samme målbarhedsresultat: synlige markeder er
    besat; usynlige kræver primærdata (interviews/netværk); moats hos vinderne er altid kapital,
    licens, fysisk nærvær, relationer eller eksisterende distribution. Web-research-fasen er nu
    bevist udtømmende på ALLE tilgængelige metoder. Ingen DECISION.md — jeg ville ikke sætte
    egne penge i nogen kandidat. Afventer Mads' valg mellem de tre veje i STATUS.md.

## Iteration 18 (2026-08-23): Radaren leverede 4 live graveyard-signaler via HN — ALLE 4 ALLEREDE SWATMEDE

Metode: Reddit var stadig 429-blokeret fra dette miljø, men Hacker News Algolia-API
(gratis, ingen nøgle) leverede ferske shutdown-signaler direkte. Fire kandidater gravet:

### R1: Flowise (AI workflow builder, EOL 31/8-2026) — SWATMET PÅ 33 DAGE
55k GitHub-stjerner, Workday-købt aug 2025, lukket 12 mdr senere ("coding agents gjorde
canvasen forældet" — samme uge deprecierede GitHub Spark af samme årsag). Swarm-status:
LLMGraph har en fuld migrations-landingpage rangerende på "Flowise alternative" INDEN EOL;
Langflow (OSS), gptme, FutureAGI-alternativeguides, stackone IT-migrationsguide. Mindst 5
aktører kæmper om brugerbasen, og kategorien dør strukturelt (hosted Langflow allerede
lukket af DataStax apr 2026). → DØD: kategorien er på vej ned, ikke op.

### R2: Relay.app (human-in-the-loop automation, founder tilbage til Google) — SWATMET PÅ ~3 UGER
Lukket annonceret 16/7; gratis konti slettet 15/8; betalende til 14/9. Ved søgning i dag:
Fleece AI, MESA, Sim, Lindy, Make (officiel migrationsguide) — 6+ alternativ-guides med
pristabeller og deadline-urgency, flere publiceret inden free-account-datoen.
→ DØD: komplet swarm inden selve shutdown-datoen, igen.

### R3: Productiv (SaaS management platform) — SWATMET PÅ 4 DAGE
Annonceret 2/8, sunnet 6/8, ALLE kundedata DESTRUKTERET (ingen migration mulig — kun
"rediscovery"). Ved 19/8: Torii (Gartner MQ Leader) har dedikerede landingpages
("Productiv destroyed your data"), SpendHound (gratis <1.000 ansatte), Zylo, Zluri,
1Password/Trelica, Flexera, CloudNuro, BetterCloud, Tropic — 9+ aktører med
konkurrencesider live inden for to uger. → DØD: SMP-markedet er enterprise-rødt hav.

### R4: TV Time (25M+ brugere, tracker-app) — SWATMET FØR SHUTDOWNDATOEN
JustWatch lancerede migrationsværktøj 9/7 — seks dage FØR shutdown 15/7. Trakt havde
indbygget importer ved lanceringen; Hobi er "official migration partner"; TrackShows,
Simkl, Moviebase, Serializd, Sofa Time, SeriesGuide, Showly, CinExplore OG nyopstartede
Zuki (waitlist) — 10+ destinationer. Consumer-tracker = lav betalingsvilje oveni.
→ DØD: det mest synlige graveyard nogensinde, fuldstændig besat før begravelsen.

### Nye mønstre (nu 18 iterationer)
16. Swarm-latensen er nu MÅLT nedefra gennem researchen: Stocky 6 uger → Relay ~3 uger →
    Productiv 4 dage → TV Time: migrationsværktøjet lanceret FØR shutdown-datoen. For
    produkter med kendt brugerbase er konkurrencen ikke længere "først efter obituaren" —
    den er samtidig med eller før dødsfaldet. En solo-bygger der opdager signalet via web
    kan aldrig vinde dette kapløb.
17. Migration-content selv er blevet et besat produktionsfelt (dedikerede domæner som
    llmgraph.ai/alternatives/flowise, reacham.app/demand-leaks bygget på forhånd).
    Selv SEO-laget omkring et graveyard er industrialiseret.
18. Bi-fund: SimpleClosure H1-2026-rapport (Business Wire 20/8): SaaS lukker hurtigere end
    nogensinde ("SaaSpocalypse") — signalforsyningen stiger, men det ændrer intet: hvert
    signal er besat hurtigere end nogen fjern-observatør kan reagere.

### Konklusion iteration 18
Radaren virker teknisk (HN-kanal løste Reddit-429-problemet), men alle fire live-signaler
var allerede swarmede ved første grav — tre af dem inden selve shutdown-datoen. Ingen
kandidat består kriteriet "<2 konkurrenter ved dybdegrav". Ingen DECISION.md.

### Næste iteration skal
Vej 3's logik holder kun hvis lytteposten er SAMTIDIG (cron dagligt + flere kanaler:
HN Algolia tilføjes til radar.py, GitHub archived-repos). Men den reelle konklusion står
fast: moat-pivot kan ikke levere en kandidat via fjern-observation; den kan kun give
indhold/distribution. Kræver fortsat Mads' ja/nej til kanal.

## Iteration 19 (2026-08-23): Radaren opgraderet (HN Algolia + GitHub archived) og kørt — 3 nye live-signaler, alle 3 døde ved første grav

Metode: STATUS.md's køreplan fra iter. 18 udført. `POSTS/radar.py` udvidet med to kanaler:
HN Algolia `search_by_date` (shutdown-stories, 7 dage) og GitHub Search API (`archived:true,
stars>=500, pushed sidste 14 dage`). Testkørsel: Reddit 429 stadig, IndieHackers timeout,
men HN + GitHub leverede 30 signaler. Tre var reelt grave-værdige:

### R5: InstantDB (YC S22 realtime BaaS, lukket ~20/8-2026) — SWATMET PÅ DAGE
HN-story 20/8 ("InstantDB Is Shutting Down", 10 point). Brugerbase: indie/SaaS-byggere,
dokumenteret popularitet (2026 BaaS-sammenligninger placerede den i top-7-kategorien).
Swarm-status ved første grav (søgning 23/8):
- RxDB har dedikeret "InstantDB Alternative"-landingsside LIVE (rxdb.info)
- Pylon har dedikeret "InstantDB alternative"-vs-side LIVE (pylonsync.com/vs/instantdb)
- Kategorien (realtime BaaS) er pakket: Supabase (42k★), Convex, PocketBase, Appwrite,
  Zero (2026-zeitgeist iflg. cssauthor.com top-26-guide)
→ DØD: migrations-markedet besat inden for få dage; kategoriledere står klar til at opsuge
brugerbasen; ingen differentieringsmulighed for en fjern-observatør.

### R6: Whoogle Search (11.595★ self-hosted Google-frontend, EOL jul 2026) — KATEGORI-DRAB
Ikke en shutdown-med-brugere-at-tage: Google blokerede systematisk alle no-JS User-Agents
indtil den sidste vej var lukket ("Google closed both doors; there's no third one to try").
Forks opfordres eksplicit (MIT). → DØD SOM FORRETNING: hele kategorien (scraping-fri
Google-frontends) er strukturelt ved at blive dræbt af platform-ejeren — enhver efterfølger
arver samme dødsdom. Bekræfter mønster 19 (nedenunder).

### R7: elevenlabs-mcp (1.534★ officiel MCP-server, arkiveret) — VENDOR-IN-HOUSE
Arkiveret fordi ElevenLabs selv overtog MCP-distributionen (SDK/changelog). Ingen tredje-
parts-forretningsmulighed; modsat retning — vendor-konsolidering.

Øvrige 27 GitHub-signaler: OSS-biblioteker/læringsmateriale/WICG-specs uden betalende
brugerbaser — ikke forretningskandidater (ingen betalingsvilje at arve).

### Nye mønstre (nu 19 iterationer)
19. To nye graveyard-varianter identificeret og begge ufrugtbare: (a) platform-drab hvor
    selve KATEGORIEN dør med produktet (Whoogle) — tjek altid HVORFOR noget lukker før
    efterspørgslen vurderes; (b) vendor-in-house-arkivering (elevenlabs-mcp) — tegn på
    konsolidering, ikke hul.
20. Radaren med HN+GitHub fungerer som lyttepost (signaller fanges samme dag), men
    iter. 18-19 bekræfter: også de FERSKESTE signaler er swarmede inden for dage.
    Latens-målingen strammes: TV Time (før shutdown) → Productiv 4 dage → InstantDB:
    konkurrencesider live < 1 uge. En daglig cron ville stadig være for sent.

### Konklusion iteration 19
Ingen kandidat består screeningen. Ingen DECISION.md. Radarens rolle reduceres til
indholdsleverance til vej 3 (essays), ikke idé-kilde.

### Næste iteration skal
Afventer fortsat Mads' valg (STATUS.md): kanal ja/nej, og valg mellem interviews /
acceptér konkurrence / moat-pivot. Web-research er nu bevist udtømmende i 19 iterationer
og ~90 kandidater inkl. realtids-signaler.

## Iteration 17 (2026-08-23): Vej 3-leverancer bygget — ingen ny kandidat-grav nødvendig
Alle finalister var allerede døde og dokumenteret (iter. 1-16); denne iteration udførte
den køreplan STATUS.md (iter. 16) definerede: indhold + lyttepost.

**Leveret:**
1. 5 færdige engelsksprogede essays i POSTS/ — alle trukket direkte af iter. 1-15's data
   (hovedautopsien, graveyard-autopsien, Stocky 6-ugers-swarm, regulering-scoreboard,
   signal-styrke-korrelation). Klar til Mads' godkendelse; intet offentliggjort.
2. POSTS/radar.py — gratis lyttepost (RSS: r/SaaS, r/EntrepreneurRideAlong, IndieHackers),
   dedupe via radar_seen.json, output RADAR.md med de 4 screeningskriterier.
   Testet med rigtige kald: mekanikken virker; Reddit gav HTTP 429 ved tætte gentagelser
   og IndieHackers timeout → anbefaling: daglig cron-kørsel, ikke timevis. Nul nye
   shutdown-signaler i testvinduet.

**Ingen DECISION.md:** stadig ingen idé der består de 4 kriterier. Vej 3 er distributions-
opbygning FØR valg af produkt — DECISION.md skrives når radaren finder et live-signal
der består screeningen, eller interviews giver primærdata.

**Næste iteration:** afhænger af Mads' ja/nej til kanal + konto (se STATUS.md).


## Iteration 21 (2026-08-23): Metode 15 — "tidlig bølge"-hypotesen (regler vedtaget nu, deadline 2027-28) — TESTET OG AFKRÆFTET DØD

STATUS.md's plan ("dybere grav i finalister") var igen umulig: der står NUL finalister.
I stedet testede jeg den eneste strukturelle luke mine egne mønstre tillader: mønster 1
siger swoop sker 6-12 mdr EFTER signal. Alle hidtidige bølger var allerede 12+ mdr gamle
ved første grav. Hypotese: bølger vedtaget I ÅR med deadline 2027-28 skulle teoretisk være
før-swoop. Kilder: HN Algolia (radar, 7 dage) + web-search pr. bølge.

### Radar (HN, sidste 7 dage): ingen nye grave-værdige graveyard-signaler
InstantDB-duplikat, macOS hdiutil-deprecation (OS-leverandør-ejet), Tesla Solar Roof
(hardware), Columbia House (fysisk detail). Intet arveligt.

### T1: Cyber Resilience Act (CRA) — DØD: FULDT SWATMET 15 MDR FØR DEADLINE
Deadline for full application: 11/12-2027; Art. 14-rapportering starter 11/9-2026 (om 3 uger).
Fund: Venvera-købereguide "6 Best CRA Compliance Software" (jul 2026); Attestra AI
(EU-co-funded, modul 1 live NU til sept-deadline); OpenComplAI (OSS CRA/AI Act checks i
CI/CD, Show HN 14/8); Determinate Secure Packages; ENISA SMV-survey → EU-finansierede
GRATIS værktøjer (OSCRAT, OCCTET) målrettet netop mikrovirksomheder.
→ Død: alle tre lag (enterprise, SME, gratis) besat FØR den første rapporteringsfrist.

### T2: Digital Product Passport / ESPR / Battery Reg — DØD: 6+ PLATFORME, GRATIS-TIER LIVE
Battery-passports obligatoriske 18/2-2027; tekstiler 2027-29. Fund: Traceable.digital
(fra €15/passport, AI-extraction, EC "Good Practice"-udvalgt); dpp.gs (Sensoneo,
EU-regulator-IT i 9 lande); SigmaTag (€349/md tier); Tracelia (tekstil-SME);
OriginPass (6 md gratis mod LOI, Q4 2026-launch); DPP Agent (validator + white-label).
Plus: EU DPP Registry LIVE siden 20/7-2026, harmoniserede standarder (EN 18216-23)
publiceret juni 2026 — økosystemet er færdigt før markedet åbner.
→ Død: samme tredelte besættelse; SME-bunden koster allerede €15/styk.

### T3: PPWR (emballage) — DØD: REGLEN GÆLDER ALLEREDE (12/8-2026) OG MARKEDET ER PAKKET
Repax (DoC-generering), PAQR, Packgine, Dcycle, Ecoveritas + "8 best tools"-guide.
→ Død: DoC-artefaktet er allerede et produkt.

### T4: EU AI Act high-risk (dec 2027/aug 2028) — DØD + POLITISK USTABIL
Compliance-platform-markedet "growing" (€10-30k/år enterprise; gratis checker:
artificialintelligenceact.eu). Og afgørende: Regulation (EU) 2026/1744 ("Digital Omnibus",
i kraft 27/7-2026) flyttede lige high-risk-deadlinesne 12-24 md ud — samme politiske
ustabilitet som CSRD/Omnibus I (iter. 3). En forretning bygget på disse datoer kan blive
omstødt ved trilogue.

### T5: Forced Labour Regulation (14/12-2027) — DØD I SCREENING
Assent (AI-native forced labor due diligence, enterprise), TrusTrace (FLR-løsning live),
Single Portal + risk database bygget af Kommissionen selv.
→ Død uden dybere grav.

### Bi-fund: EAA EFTER deadlinen (13 måneder inde) — INGEN NY ÅBNING
Enforcement er fortsat stille i de fleste medlemslande (web60.ie, irsk status ét år efter);
Carrefour-dommen (daglige bøder trods 71% compliance) viser at håndhævelse rammer STORE
aktører først. Mikrofritagelsen (<10 ansatte + <€2M) står uændret. Ingen ny indgang for
iter. 2's døde finalister.

### Mønster (nu 21 iterationer)
22. "Tidlig bølge"-hypotesen er AFKRÆFTET som død: selv regler vedtaget i 2024 med
    deadline 2027-28 er fuldt swarmede 12-18 mdr før deadline, på ALLE tre lag (enterprise-
    platform, SME-prispoint, EU-finansieret gratisværktøj). Swoop'en starter ikke ved
    signalets offentliggørelse — den starter ved vedtagelsen, ofte før. Web-research kan
    derfor STRUKTURELT ikke nå nogen regulatorisk bølge i tide: inden en regel er synlig
    nok til at jeg kan finde den, er dens tooling-market allerede beboet.
23. Konsekvens: den eneste resterende kilde til ubesatte markeder er information der IKKE
    er offentlig endnu — altså primærdata via interviews/netværk. Dette er nu bevist, ikke
    formodet, på tværs af 15 metoder.

### Konklusion iteration 21
Ingen kandidat består screeningen (<2 konkurrenter ved dybdegrav). Ingen DECISION.md —
der er intet at forsvare. Budget: 0 kr brugt.
