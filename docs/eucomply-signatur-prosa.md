# Signaturer: hvad der er **bevis**, og hvad der ikke er det

Opgave 57, 58 og 59. Plugin **1.3.20** (beholderen) og **1.3.21** (lækagerne).
Port: `tools/check_signature_prose.mjs` (trin 24 i `tools/quality_gate.sh`).

Denne side beskriver de fire signatur-tabeller, der er delt af tre produkter, og
de to spørgsmål, der altid stilles om dem:

1. **Måler de overhovedet noget?** En mangel i tabellen er usynlig i en diff.
2. **Finder de kun bevis?** En bred regel finder tekst, og tekst er ikke et
   værktøj der kører.

Sporet startede med en måling, ikke en læsning: opgave 57 kørte hver signatur mod
en prosa-fixture og fandt **48 falske fund** — 12 pr. sprog i fire sprog, i begge
JS-motorer og i pluginen. Opgave 59 kørte porten på det modsatte spørgsmål og
fandt **tre lækager**. Begge er fejl i den betalte rapport.

## De fire tabeller, og hvor de læser

| Tabel | Række | Hvad den spørger om | Hvor den læser |
|---|---|---|---|
| `TRACKER_SIGNATURES` | `trackers` | Hvilke marketing/analytics-sporinger læser siden? | kode og attributter |
| `CONSENT_SIGNATURES` | `cookies` | Står der en samtykkeplatform foran dem? | kode og attributter |
| `FORM_PLUGIN_SIGNATURES` | `forms` | Hvilke formular-plugins lever i markup'en? | kode og attributter |
| `DORA_SIGNATURES` | `dora` | Hvad skriver virksomheden om egen driftssikkerhed? | **hele siden** |

De tre første læser `codeAndAttributes(html)` — `visibleText` med script- og
style-blokke fjernet, plus de fundne attributter. Det er opgave 57s resultat, og
grunden er konkret: Contact Form 7 lever som `<div class="wpcf7">` **i markup'en**,
ikke som et script, og Klaro kommer som et `<link …klaro.css>`. En ren
scriptregel ville slettet den mest almindelige WordPress-formulardetektion.

`DORA_SIGNATURES` er det ene bevidste undtagelse, og den skal blive ligesådan:
markørerne er **påstande om virksomheden**, ikke om at kode kører. En virksomhed
der skriver "we have a business continuity plan" på sin sikkerhedsside har sagt
præcis det tjekket spørger om. Uden R4 i porten bliver undtagelsen usynlig, og en
senere agent "forenkler" den væk fordi den ser unødigt speciel ud.

## Fejl 1 — prosa var bevis (rettet i 1.3.20)

Målt: **48 falske fund**, 12 pr. sprog (DA/SV/NL/EN), i alle tre produkter.

```
<p>Vi bruger Matomo til statistik, og vores samtykkeplatform er Klaro.</p>
  → "Trackers found in page markup: Matomo / Piwik."     rød række
  → fix: "Install a CMP that blocks Google Analytics…"
```

Kunden fik en rød tracker-række og en instruks om at installere en samtykkeplatform
den allerede havde. Rettelsen var **beholderen, ikke ordene**: mønstrene er
uændrede, så alt der *rigtigt* blev fundet, bliver fundet.

Parret der gør det målbart er R1 mod R2, og det er pointen at de kan modsige
hinanden: R1 (prosa giver nul fund) kan ikke se forskellen på en for bred og en
for smal beholder — begge er grønne på prosa. Kun R2 (en rigtig side pr.
mekanisme) kan det. Selftestens mutation der kun læser kode uden attributter er
derfor skrevet til at kræve præcis det: **R1 grøn, R2 rød**.

## Fejl 2 — mellerummet i DORA-separatoren (rettet i 1.3.21)

`DORA_SIGNATURES` brugte `[_-]?` — bindestreg eller understreg, valgfri. Den
matcher **aldrig et mellemrum**, og den lange engelske form er skrevet med
mellemrum.

| Markør | Før | Efter |
|---|---|---|
| `business continuity plan` | ufandet | fundet |
| `incident response` | ufandet | fundet |
| `status page` | ufandet | fundet |

Målt før rettelsen på en side der nævner alle tre: **0 af 3 i alle tre
produkter**. Kun de enkeltstående tokens (DKIM, SPF, `failover`) kunne finde
noget, og de er ikke dem siden handler om. Rettelsen er `[ _-]?` i alle ni
signaturer, i begge motorer og i pluginen.

Dette er **tredje** forekomst af præcis denne fejlklasse: `terms` i opgave 52,
`sla` i opgave 55, `DORA_SIGNATURES` her. Den mønsterklasse, der gør et
flerords-mønster ubrugeligt, er separatoren — ikke sproget.

## Fejl 3 — GTM's egen noscript-fallback (rettet i 1.3.21)

```html
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-…"></iframe></noscript>
```

Det er det snippet Googles egen dokumentation beder **alle** GTM-sites
installere. Signaturen matchede kun container-scriptet (`googletagmanager.com/gtm.js`),
så en side hvis eneste GTA-bevis er fallbacken fik `Third-party trackers: 0 found`
— en grøn række på en side der sender et pixel.

Det er **ikke** en regression fra opgave 57: mønsteret har aldrig matchet den,
fordi `ns.html` ikke stod i nogen tabel. Det er derfor en *lækage* og ikke en
falsk beståelse fra beskæringen — og derfor er den målt på sin egen fixture
(`GTM's ns.html-fallback`) frem for at falde ud af R1.

De to øvrige noscript-fixtures i porten — GA's `google-analytics.com/collect`
og Hotjars `static.hotjar.com` — var fundet i alle tre produkter hele tiden. Det
er beviset på at kodebeholderen ikke var problemet: mønsteret var det.

## Fejl 4 — motoren navngiver ikke platformen (rettet i 1.3.21)

Samme dom, to rapporter, om det *samme* website:

```
pluginen: "… A consent platform was also detected (TarteAuCitron / Klaro / …)."
motoren:  "… A consent platform was also detected."
```

Den betalte vare var den mere informative. Motoren læser nu
`CONSENT_SIGNATURES` i tabellens rækkefølge og skriver samme navn som pluginen,
og fordi de to JS-motorer læste den samme liste på to steder (en i
`trackers`-reglen, en i `cookies`-reglen) ligger læsningen nu ét sted — to
steder der læser det samme er præcis hvad der gør at to rækker kan komme til at
svare forskelligt.

Det her lå i portens R3 som en **undtagelse med vilje**: holdet sammenlignede
`sætningen` og ikke hele detaljen, fordi forskellen var reel. Da motoren blev
rettet, forsvand undtagelsen, og R3 sammenligner nu hele `trackers`-detaljen
byte-identisk på tværs af alle tre produkter.

## Fejl 5 — GA4's eget indlæsscript (rettet i 1.3.22)

Den dyreste lækage i de fire tabeller, og den eneste der gav en **grøn** række
på en side med en tracker.

GA4 indlæses med ét eksternt script:

```html
<script async src="https://www.googletagmanager.com/gtag/js?id=G-ABC123"></script>
```

Det gamle mønster var
`google-analytics\.com|googletagmanager\.com\/(?:gtm\.js|ns\.html)|gtag\(` — altså
matchede det kun det **indlejrede** `gtag(`-kald. Når konfigurationen ligger i
en aparte fil, som den gør i den almindeligste opsætning, står der **intet**
`gtag(` i markup'en, og siden fik:

```
Third-party trackers: 0 found
No third-party marketing/analytics trackers found in the served HTML.
```

Målt før rettelsen, i alle tre produkter, på præcis den installation ovenfor.
Samme måling på de otte andre markører i tabellen: syv fundet, og kun GA4's
`gtag/js` ikke. Hullet var altså den ene mekanisme, ikke hele mønstret.

**Hvorfor den er dyrere end de 48 falske fund fra 1.3.20.** Et falsk fund står i
rapporten og kan bemærkes. Et tracker der *ikke* rapporteres kan ingen læse sig
til: kunden får en grøn række og ingen grund til at sætte samtykke ind, på en
side der sender et pixel ved hvert besøg. Det er den modsatte fejlretning af
fejl 1, og den er den værre af de to for en kunde.

**Rettelsen matcher filstien, ikke id-præfikset.** Googles **Ads**-tags indlæses
fra samme URL med `AW-` i stedet for `G-`:

```html
<script async src="https://www.googletagmanager.com/gtag/js?id=AW-9876543"></script>
```

Der er derfor to fixtures og ikke én. En "rettelse" der skriver
`gtag\/js\?id=G-` ville få den første til at bestå og den anden til at fejle, så
parret kan skelne de to. Det er den mutation, der fanges med vilje.

Consent Mode v2 kommer fra **samme URL** — den indlæses også fra `gtag/js`, og
dets særlige `gtag('consent', 'default', …)`-kald var allerede dækket af det
gamle `gtag(`. Derfor er der to fixtures og ikke tre: den anden mekanisme i
opgavens scope viste sig at være den samme filsti, ikke en ny markør.

### Hvad den *ikke* var

GA4's klassiske `collect`-pixel og GTM's container-script var fundet begge, før
og efter. Det er derfor opgaven blev skrevet som én markør og én rettelse: målt
først, rettet bagefter. En bred `googletagmanager`-regel ville have ramt prosa
med "vi bruger Google Analytics" — den fejlretning opgave 57 gjorde, og R1 i
porten forhindrer den.

## Porten: fire kontrakter, fjorten mutationer

`node tools/check_signature_prose.mjs [--selftest]` — 30 tests, 27 negative cases,
**fjorten mutationer mod repoets egne filer**.

| Kontrakt | Krav |
|---|---|
| R1 | prosa giver **nul** fund i alle tre produkter, fire sprog |
| R2 | en rigtig side pr. mekanisme giver sit fund, i alle tre |
| R3 | samme fund, samme etikette, samme detalje i alle tre |
| R4 | `dora` læser prosa, også den lange engelsk form |

Fund-listen læses **af porten selv**: navnene parses ud af produkternes egne
signatur-tabeller, så en ny signatur dækkes automatisk, og en tabel der ikke kan
parses gør porten rød frem for grøn (`MINDST`: 12/21/2/9). Samme
"dækkede-ikke-antaget"-regel som trin 21.

### Hvad porten ikke kan se

Den måler at portens egne fixtures er fundet — ikke at signatur-tabellerne er
**fuldstændige**. En markør der mangler helt i en tabel kan ingen fixture finde,
fordi porten læser navnene og ikke formernes rækkevidde. Det er præcis fejl 3
og fejl 5 forklaret, og derfor er mutationerne der fjerner dækningen igen lige
så vigtige som fixtures: de binder tabellen til et krav om dækning.

**Og den ser kun de produkter den kører.** R3 sammenligner de tre, men en
mutation i det ene produkt er målt i det ene. Derfor er der skrevet **én
mutation pr. kopi**: `shared/scan-engine.js`,
`eucomply-scanner/engine/index.js` og `plugin/eucomply.php` har hver sin egen
lang linje, og en rettelse der kun rammer to af dem er en lækage der ikke kan ses
i en diff.

### Mutationerne

| # | Mutation | Kontrakt skal blive |
|---|---|---|
| 1–3 | hvert produkt læser hele HTML'en igen | R1 rød |
| 4 | motoren læser kun kode og taber attributterne | R1 **grøn**, R2 rød |
| 5 | motoren taber GTM's `ns.html` | R2 rød |
| 6–8 | `gtag/js` taber (motor, npm-motor, plugin) | R2 rød |
| 9–10 | `gtag/js` bindes til id-præfikset `G-` (motor, plugin) | R2 rød |
| 11–13 | DORA-separatoren taber mellerummet (motor, npm-motor, plugin) | R4 rød |
| 14 | motoren holder op med at navngive platformen | R3 rød |

Alle er skrevet mod den **lange** linje, så de fejler højt med "fandt ikke den
linje den erstatter" den dag et nyt kald eller et nyt alternativ indsættes,
frem for at stå grønne på en mutation de ikke længere rammer (samme
selvbeskyttelse som opgave 29 og 51). Det er ikke en teoretisk beskyttelse: da
`gtag/js` kom til, brød mutation 5 med præcis den besked, fordi den skrev den
gamle linje, og den blev skrevet om i stedet for at slettes.

## Fejl fundet i min egen port

Fire, alle fordi porten blev skrevet frem for at læst:

1. `const [a, b, c] = domme` i R3 giver **[hvem, dom]-parene**, ikke dommene, så
   `.label` læses på `undefined` og R3 var grøn for enhver afvigelse mellem
   motorerne. Præcis fælden opgave 52 fund 4 dokumenterede — lavet igen i en ny fil.
2. Samme fælde i R1, hvor `const [, , php] = domme` gav paret, så pluginens
   consent-regel var grøn uden at se noget.
3. R2 for Klaro var grøn for den **forkerte** grund: signatur-listen blev valgt
   efter den række fundet *står i* (`trackers`) i stedet for efter den liste
   navnet *kommer fra* (`consent`), så pluginen "fandt" ikke Klaro — og porten
   sagde alligevel ja.
4. `dora`-fixturet med "business continuity plan" fandt **intet** i nogen af de
   tre produkter. Det var ikke en fejl i porten: det var en lækage i den
   betalte DORA-række, målt, og den er fejl 2 ovenfor.

Den fjerde er hele pointen med at køre en port mod rigtige fixtures: fundet lå i
produktkoden, opdaget af værktøjet, og ikke i nogen af de 23 forrige steps — de
måler at en rigtig side stadig findes, ikke at **prosa ikke tæller** og ikke at
**mellemrum matcher**.

## Femte fejl i porten: den kunne ikke skrive en plugin-mutation overhovedet

Selftestens PHP-gren læste `if (forventer === "R1") … else …`, og `else` kørte
**R4**. En `forventer: "R2"`-mutation i `plugin/eucomply.php` blev derfor målt
med DORA-kontrakten, som ingen tracker-mutation kan gøre rød — den ville have
stået grøn, og porten ville have hævdet at pluginen er dækket.

Det er samme fejlklasse som punkt 1 og 2, og det er derfor den lå ubemærket:
pluginen er **tredje kopi** af hver signatur, og opgave 59 skrev en mutation for
`ns.html` i `shared/scan-engine.js` og ingenting for de to andre — ikke fordi den
glemte pluginen, men fordi porten ikke kunne udtrykke det. Grenen måler nu R2 på
pluginen, og mutation 8 og 10 er begge skrevet mod `plugin/eucomply.php`.


## Fejl 6 — Pinterests dokumenterede stier (rettet i 1.3.23)

Opgave 61 skrev, at Pinterest-mønsteret `cdn\.pinterest\.com.*pin.*js|pintrk\(`
ramte `assets.pinterest.com/js/pinit.js` via `pintrk(`-grenen, men **ikke**
Pinterests basistag. Det viste sig at være værre end et delvist fund.

**Kilde.** `https://help.pinterest.com/business/article/install-the-base-code`
("Install the base code"), hentet 2026-09-27. Den dokumenterede basistag er:

```html
<script>!function(e){if(e.pintrk){return;}var n=e.pintrk=function(){…n.version="3.0";
…t.src=e;…}}("https://s.pinimg.com/ct/core.js");
pintrk('load', 'YOUR_TAG_ID');
pintrk('page');</script>
<noscript><img … src="https://ct.pinterest.com/v3/?tid=YOUR_TAG_ID&event=init&noscript=1" /></noscript>
```

**Målt før rettelsen** (fixture mod motoren i repoet, den publicerede
npm-motor og pluginen): `s.pinimg.com/ct/core.js` alene → `Third-party trackers:
0 found` i alle tre. `ct.pinterest.com/v3/?tid=…&noscript=1` alene → **0 fund** i
alle tre. Hele basistaget → 1 fund i alle tre, **kun** fordi den indlejrede
`pintrk(` findes i markup'en.

Det er altså ikke en mangel i en alternativ sti: **hele den dokumenterede
installation var usynlig, så længe de indlejrede scripts var indlejrede.** Og
de bliver det — det er præcis hvad samtykke-værktøjer gør, når de flytter
scripts ud af en bundle, og det er hvad en `script-src`-CSP gør når den
tillader domænet men ikke inline. Samme fejlretning som opgave 60: en grøn
række på en side der sender et pixel. `cdn.pinterest.com.*pin.*js` matcher
forresten **intet** i Pinterests nuværende dokumentation.

**Rettelsen matcher stien, ikke værten:** `s\.pinimg\.com\/ct\/` og
`ct\.pinterest\.com\/v3\/`, begge læst direkte af dokumentationen. Ikke
`pinimg\.com`, fordi Pinterests **billed**-CDN ligger på samme vært — en butik
med tre opslagsbilleder har intet tag at slette. Den negative fixture
`i.pinimg.com` er derfor målt på samme måde som R1s prosa: en bred regel på
værten skal gøre porten rød. Det gør den (mutation 5).

### Fejl fundet i porten undervejs

Selftestens R1-gren læste altid `PROSA_FIXTURES[0]` — den danske prosa — uanset
hvilken fixture mutationen var skrevet til. Den negative billed-fixture gjorde
mutationen grøn ved at aldrig blive kørt, og porten ville have skrevet
"mutationen fanges" fordi den ikke var målt. R1-grenen læser nu
`m.fixture` med `prosa` som fallback. Samme fejlklasse som opgave 59 fund 1.

### Hvad der stadig ikke er verificeret

De elleve øvrige tracker-markører er **kun** kontrolleret mod leverandørernes
værter, ikke mod deres dokumentation: `snap.licdn.com` (LinkedIn,
`insight.min.js` svarer 200), `sc-static.net` (Snap, `scevent.min.js` 200) og
`connect.facebook.net` (Meta, `fbevents.js` 200) er bekræftet på leverandørens
egen vært, og mønstrene dækker dem. `static.tiktok.com`, `googlesyndication.com`,
`cdn.matomo.cloud`, `cdn.cookiebot.com` og `quantcast.mgr.consensu.org` kunne
**ikke** bekræftes i denne iteration — de skal have hver sin kilde-registrerede
fixture, før en rettelse skrives, og det er opgave 62. `quantcast[_-]?choice`
ser især ud til at skulle være `quantcast\.[^"']*choice` for at ramme
`quantcast.mgr.consensu.org/choice/…`, men det er **formodet**, ikke målt, og
en død markør er værre end ingen.
