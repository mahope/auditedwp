# Privatlivsmønsteret skal kunne læse dansk, svensk og nederlandsk

Spec skrevet **før** kodeændringen, fordi signaturerne er delt af tre motorer og
fire porte (opgave 51).

## Problemet, målt

`LEGAL_PATTERNS[0]` var `privacy|privacy[_-]?policy|datenschutz|gdpr|privacypolicy|data[_-]?protection`
i `shared/scan-engine.js`, i den publicerede kopi i `eucomply-scanner/engine/index.js`
og i `check_forms()`'s inline regex i `plugin/eucomply.php`. **Engelsk og tysk.
Ikke dansk.**

Det blev fundet af en fixture i opgave 50, som skrev et dansk
`<a href="/privatlivspolitik/">Privatlivspolitik</a>` og faldt igennem **alle tre**
motorer. En dansk WordPress-butik med en håndbygget kontaktformular og en
privatlivspolitik får derfor:

- `forms` **fejler** — *"Form(s) found, no privacy-policy link"*
- `legal` **tæller den ikke** som en juridisk side

Det er symmetrisk — alle tre produkter er enige om det forkerte svar — så ingen port
var rød, og derfor lå det der. Samme fejlklasse som opgave 28 fund 2
(manglende "Historie" i et mønster) og opgave 31 fund 1 (`hostet` kan ikke læse
`hostede`): et **vokabular**-hul, der gør en hel målgruppe usynlig.

## Beslutning

Privatlivsmønsteret bliver **sprogsneutralt**. Det matcher stadig *hvor som helst*
i markup'en — samme løsning som før, bare med flere sprog — fordi strengere at
kræve et `<a href>`-element ville være en adfærdsændring, der rammer alle eksisterende
kunder og alle eksisterende fixtures, og den er ikke målet her.

### Sprogene, og hvorfor præcis disse

| sprog | stængler | brugt på |
|---|---|---|
| engelsk | `privacy`, `data[_-]?protection` | uændret |
| tysk | `datenschutz` | uændret |
| **dansk** | `privatliv`, `persondata`, `databeskyttelse` | ny |
| **svensk** | `integritetsskydd`, `dataskydd`, `personuppgifter` | ny |
| **nederlandsk** | `persoonsgegevens`, `gegevensbescherming` | ny |
| fransk | `confidentialit` | ny |
| spansk | `privacidad`, `datos personales` | ny |

Hver stængel er et helt ord fra det sprog den hører til — aldrig et dansk eller
svensk *fragment*, der også er et engelsk eller tysk ord. Det er derfor
`privatliv` (`privatlivspolitik`, `privatlivserklæring`, `privatliv`) dækker hele
den danske familie med ét alternativ, mens `persoonsgegevens` ikke dækkes af
`privacy` (som det danske `persoonsgegevens` heller ikke gør — det er hollandsk,
ikke dansk).

`confidentialit` er bevidst skrevet uden accent: det matcher både
`confidentialité` og en ASCII-form, fordi en manglende accent på en kundes side
skal ikke slå et reelt privatlivslink fra. Det dækker den formulering franske
sider faktisk bruger på et link — *politique de confidentialité*. Den franske
prosætning *données personnelles* er **ikke** en stængel: accenten ville give
forskellige matchregler i JavaScript og i PCRE (sidstnævnte matcher bytes, ikke
tegn), og to motorer der læser forskelligt er hele den fejlklasse, denne
opgave lukker.

### Hvad der **ikke** er ændret

- `LEGAL_PATTERNS[1]`–`[17]` er uændrede. De har delvis samme mangel (se nedenfor),
  men de får ikke ændret i denne iteration: de påvirker kun `legal`, som ikke er
  delt mellem produkterne, og hver mangel skal måles på fixtures før den rettes.
- Intet nyt tjek, ingen ny etiket, ingen ny scorevægt. En side der før fejlede
  `forms` med et dansk privatlivslink består nu; det er hele rettelsen.
- `plugin/eucomply.php` bruger den samme mønstringssæt, fordi et tjek med samme
  navn skal betyde det samme i begge produkter (samme regel som opgave 50).

## De øvrige mønstre, målt

Undersøgt, som opgaven beder om. `LEGAL_PATTERNS` har atten mønstre; **otte** af
dem har ingen dansk, svensk eller nederlandsk stængel:

| mønster | dansk | svensk | nederlandsk |
|---|---|---|---|
| `Privacy / GDPR` | `privatliv`, `persondata`, `databeskyttelse` | `integritetsskydd`, `dataskydd`, `personuppgifter` | `persoonsgegevens`, `gegevensbescherming` |
| `Imprint / Legal notice` | `om-os` (ufuldstændig) | — | `colofon` |
| `Accessibility statement` | `tilgængelighedserklæring` | `tillgänglighetsredogörelse` | `toegankelijkheidsverklaring` |
| `Cookie policy` | `cookiepolitik` | `kakpolicy` | `cookiebeleid` |
| `Terms & Conditions` | `vilkår`, `betingelser` | `villkor` | `algemene voorwaarden` |
| `Legal / Imprint` | `juridisk information` | `juridisk information` | `juridische informatie` |
| `Returns / Refund policy` | `retur- og forbrugerrettigheder` | `retur- och ångerrätt` | `retourbeleid` |
| `Shipping policy` | `leveringsbetingelser` | `frakt- och leveransvillkor` | `verzendbeleid` |
| `Data processing agreement` | `databehandleraftale` | `personuppgiftsbiträdesavtal` | `verwerkersovereenkomst` |
| `Acceptable use / Fair use` | `acceptablebrug` (dansk stavning: `acceptabel brug`) | `rimlig användning` | `redelijk gebruik` |
| `Sub-processor list` | `underbehandler` | `biträdesförteckning` | `subverwerkers` |
| `Code of conduct` | `adfærdskodeks` | `uppförandekodex` | `gedragcode` |
| `SLA / Warranty` | `serviceniveau`, `garanti` | `servicenivå` | `servicelevelovereenkomst` |
| `Complaints procedure` | `klageprocedure` | `klagförfarande` | `klachtprocedure` |
| `Modern slavery statement` | `moderne slaveri-erklæring` | `modernt slaveri` | `moderne slavernij` |
| `Whistleblower / Hinweisgeber` | `whistleblower` (allerede) | `visselblåsare` | `klokkenluider` |
| `Environmental / Sustainability` | `bæredygtighedspolitik` | `hållbarhetspolicy` | `duurzaamheidsbeleid` |
| `DPO / Data protection officer` | `databeskyttelsesrådgiver` | `dataskyddsansvarig` | `functionaris voor gegevensbescherming` |
| `General contact address` | sprogneutralt (`info@`) | — | — |

Det er en reel, prioriteret mangel, og den er **ikke** løst i denne iteration. Den
er skrevet som opgave 52 med den målemetode, der lå under for opgave 51: hvert
mønster får sine egne fixtures, og et mønster må først regnes som rettet når
`legal` giver samme dom i alle tre motorer på en dansk, svensk og nederlandsk
side. Det er fire gange så stort som denne rettelse og det er ikke samme fejl —
her ramte den et tjek, der **fejlede en kunde**, der gjorde det rigtige.

## Hvordan det måles

`tools/check_forms_parity.mjs` (gate trin 20) får fire nye fixtures og to nye
regler:

- **R4** — de to universelle motorer (`shared/` og den publicerede
  `eucomply-scanner/`) giver **identisk** `forms`-dom på alle fixtures. Samme
  produkt, to kopier; en forskel er en fejl i den ene, uanset hvilken.
- **R5** — når der står en formular i markup'en, skal alle **tre** motorer være
  enige om, om der står et privatlivslink, og dommen følger portens **egen**
  sprogliste. Begge retninger: et privatlivslink porten kan se, alle motorer
  består; intet privatlivslink, alle motorer fejler. R2 dækkede kun den ene.

R5 er skrevet med portens egen læsning af markup'en, ikke med motorens regex, så
den kan ikke arve motorens fejl — samme regel som R2.

Selftesten muterer repoets egen fil i to nye retninger:

- **M3** fjerner de nye sprog fra `check_forms()`'s regex → den danske fixture
  skal blive rød i R1.
- **M4** gør regexen til en ren `href`-matcher → den fixture hvor privatlivsordet
  kun står i **linkteksten** skal blive rød i R1. Det er beviset på, at en
  "forbedring" der kun kigger på `href` ikke må slå den danske tekst.
