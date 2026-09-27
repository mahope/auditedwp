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
egen vært, og mønstrene dækker dem. `cdn.matomo.cloud` og `cdn.cookiebot.com`
er målt i denne iteration og dækkes af `matomo` hhv. `cookiebot` — de to mønstre
er brede nok til at ramme **enhver** sti på de to værter, så ingen rettelse
er nødvendig. `quantcast[_-]?choice` var **død som skrevet**; den er fjernet i
1.3.25, se "Fejl 8" nedenfor.

## Fejl 7 — to af de mest almindelige annonce-tags var usynlige (rettet i 1.3.24)

- **Målt før rettelsen, i alle tre produkter.** Elleve installationer kørt
  gennem motoren i repoet, den publicerede npm-motor og pluginen. **otte** gav
  fund. To gav `Third-party trackers: 0 found` — altså en grøn række på en side
  der kører en annonce-tracker, den modsatte fejlretning af opgave 57 og den
  dyre af de to. Den tredje af de elleve gav et fund i de to JS-motorer men
  ikke i pluginen, fordi pluginens `cookies`-række er et WordPress-tilstandstjek;
  dens consent-signaturer læses af `check_trackers()`, som opgave 57s port
  allerede vidste.

### Fejl 7a — Googles egen Google tag

- **Kilde, ikke formodet:** `https://www.googletagservices.com/tag/js/gpt.js`
  svarer **200 fra Googles egen vært**, hentet 2026-09-27. Det er den officielle
  afløser for `googleadservices.com/pagead/conversion.js`, som den gamle mønsterstreg
  kendte, og den ligger på en **tredje** vært: hverken `googleadservices\.com`
  (remarketing) eller `googlesyndication` (AdSense) matcher `googletagservices`.
  Google Docs-siderne (`developers.google.com/tag-platform/tag-manager/web`,
  `support.google.com/tagmanager/answer/6103696`) er JS-renderede og gav ingen
  tekst til dette miljø, så **beviset er en 200 fra leverandørens vært plus en
  dødsbetjent reference i Googles egen kode** — ikke et læst snippet. Det er
  skrevet her, fordi opgave 61 krævede *kilde-registreret* fixture, og forskellen
  er ærlig: stien er bekræftet, snippetet er ikke gengivet her.
- **Rettelsen** føjer `googletagservices\.com\/tag\/js\/gpt\.js` til
  **Google Ads remarketing**, ikke til DoubleClick/AdSense. Det er Googles eget
  annoncebibliotek; AdSense's er `adsbygoogle.js` på `googlesyndication`, og
  de to skal ikke slås sammen i én etiket.
- **Ingen ny bred regel:** kun `googletagservices`, fordi værtens navn ikke er et
  ord der kan stå i prosa — og containeren læser alligevel kun kode, så en
  regel der skrev hele `google` ville ramme enhver Google-knap.

### Fejl 7b — TikToks nuværende pixel-sti

- **Kilde:** TikToks egen hjælpe-side
  (`ads.tiktok.com/help/article/get-started-pixel`, "Set up and Verify Pixel",
  hentet 2026-09-27) beder kunden "Install the base code onto your website".
  Stien er `analytics.tiktok.com/i18n/pixel/<id>.js`; TikToks vært svarer selv
  i dag med **404 på et opdigtet pixel-id**, altså at stien serveres og kun
  id'et er forkert.
- **Målt før rettelsen:** 0 fund i alle tre produkter. Det gamle mønster kendte
  kun den **ældre** `static.tiktok.com/js/` og det indlejrede `ttq.`-kald, så
  den almindeligste pixel-opsætning i dag var usynlig.
- **Rettelsen matcher vært og sti, ikke navnet:** `analytics\.tiktok\.com\/`.
  TikTok indlejres også på `www.tiktok.com/embed/…`, og en butik der har lagt
  **én** TikTok-video ind i sin lookbook har ikke installeret en pixel. Derfor er
  den negative fixture en del af rettelsen, ikke en bivirkning af den: R1 kræver
  nul fund på den, og mutationen der skriver hele `tiktok\.com` gør porten rød
  på præcis den fixture. Samme fejlretning som Pinterests billed-CDN.

## Fejl 8 — en samtykkeplatform der aldrig kunne findes (fjernet i 1.3.25)

- **Målt først, i alle tre produkter.** `quantcast[_-]?choice` kan ikke matche
  `quantcast.mgr.consensu.org/choice/…/quantcast.js`, fordi der står et **punktum
  og en skråstreg** mellem de to ord, og mønstret tillader kun bindestreg,
  understreg eller intet. En fixture med den sti gav
  `No consent banner detected` — altså præcis det samme svar som på en side der
  **ikke** har nogen samtykkeplatform, på en side der spørger hvert besøgende.
  Det er den dyre fejlretning: et falsk *fund* kan ses i rapporten, et fund der
  mangler kan det ikke.

- **Dokumentationen kunne læses tre gange og tre gange fejlede.** `curl` mod
  `https://docs.quantcast.com/docs/` gav `000` på 0,02 s, `webfetch` gav
  *Transport error*, og `defuddle` gav `getaddrinfo ENOTFOUND
  docs.quantcast.com` — DNS slår fejl, så det er ikke en blokade men en vært der
  ikke løser fra byggemiljøet. `web.archive.org` har **ingen** snapshot af
  `docs.quantcast.com` og **ingen** af `quantcast.mgr.consensu.org`.
  Kvantcasts eget hjælpecenter findes derimod, og er nået via
  `https://quantcast.us.document360.io/v1/en` → `https://help.quantcast.com/v1/en`
  — men dets maskinlæsbare indeks (`llms.txt`, 60 039 bytes) indeholder **ingen**
  dokumentation om CMP'en. Den leverandøren kan læse, findes altså ikke.

- **Derfor fjernet, ikke rettet.** At skrive `quantcast\.mgr\.consensu\.org` ville
  være en påstand om en sti, ingen i dette repo har læst hos leverandøren — og
  det er præcis den fejl, der fik den oprindelige markør ind. En død markør i
  tabellen er værre end ingen: R2-porten ville få et fixture der så ud som
  dækning, og en læser af tabellen ville tro at platformen bliver fundet.
  Markøren er derfor fjernet fra **alle tre** tabeller i 1.3.25.

- **Gaten holdt, først og fremmest fordi den tæller.** `MINDST.consent` stod på
  21 og blev rød med præcis den besked, der er værd at få:
  *"signatur-tabellen for «consent» gav 20 navne, forventede mindst 21 — en tabel
  der ikke kan parses gør porten grøn uden at den har noget at se på"*. Den blev
  sænket til 20 **med begrundelse i koden**, så den næste agent kan se at 20 er
  et valg: den døde markør kan ikke komme tilbage ved at sænke tallet igen, for
  den ville give 21.

### Hvad der stadig ikke er dækket, og hvorfor det er en opgave

Der findes **ingen** regel i porten, der kan se en markør der er død *uden* at
gulvet `MINDST` rammer den. En agent kan derfor tilføje en ny, død markør i dag,
hvis den samtidig hæver et tal, og ingen af de 24 steps vil sige det. R5 skal
lukke det: **hver signatur-række skal have en installationstest, porten erklærer,
som mønstret kan finde** — en rigtig URL eller et rigtig markup-fragment, aldrig
produktnavnet alene, fordi `quantcast_choice` ville tilfredsstille
`quantcast[_-]?choice` og skjule præcis den fejl R5 skal finde. Rækker, der ikke
kan give en troværdig installationstest, skal **fjernes** indtil de kan det.
Rækkefølgen er `consent` først (20 rækker), så `trackers` (12), `forms` (5) og
`dora` (9).



## Fejl 9 — en række, der hedder *Analytify/CAOS*, matchede `analytics-cat` (opgave 64)

**Målt før rettelsen:** `<script src="https://shop.example/wp-content/plugins/analytify/analytify.js">`
gennem motoren i repoet, den publicerede npm-motor og pluginen →
`No consent banner detected`, `Third-party trackers: 0 found`. Samme svar som en
side uden samtykkeplatform. Mønstret var `analytics[_-]?cat`, som kræver
`analytics-cat`, `analytics_cat` eller `analyticscat`.

**Beviset er ikke et netværkskald, og det er pointen med R5.** Rækkens *navn* er
`Analytify/CAOS` — og det navn kan ikke matches af sit eget mønster, fordi det
rimmer `/`. En regel der tester et mønster mod **sit eget navn** kan aldrig se
denne klasse fejl; opgave 63 fund 2 målte det og fandt den forkert på den første
af 23 rækker (`static\.hotjar\.com` matcher fint navnet `Hotjar`).

**R5** (`contractR5` i `tools/check_signature_prose.mjs`) gør hver række af
`CONSENT_SIGNATURES` målebar mod en **installationstest**: en rigtig URL eller et
rigtigt markup-fragment i `DAEKNING`, markeret med hvor den kommer fra. Rød
ved (a) manglende streng, (b) mønstre der ikke matcher sin egen streng i nogen
af de tre kopier, (c) en streng der peger på en række der ikke findes. En streng
skal rumme `//`, `.`, `=` eller `<`, så en streng skrevet efter mønstret navn
ikke kan bestå.

**Rettelse:** `analytify|caos` i alle tre kopier. Analytifs plugin-sti rummer
`analytify`; CAOS (Cookie Assistant for Osano) hedder *caos* — og Osano dækkes
allerede af `osano` i rækken ovenfor, så det er ikke ny dækning.

**Hvad R5 *ikke* havde dækket da denne fejl blev skrevet, skrevet ned fordi
porten ellers læses som om den gjorde det:** den iteration dækkede
`consent`-tabellen. `trackers` (12) kom i opgave 65 del 1, og `forms` (5) og `dora`
(9) i del 2 — hvor `forms` gav to døde rækker, se **Fejl 10** nedenfor.

**Bevisstyrken.** 8 strenge er verificeret i WordPress' eget plugin-katalog
(200), 2 på leverandørens egen vært (200), og 10 er markeret `formodnet` — de
står i ❓-afsnittet med målingen der viser hvorfor de ikke er bevis.

## Fejl 10 — to betalingsplatforme i `forms` var døde rækker (opgave 65 del 2)

R5 blev udvidet til de to sidste tabeller, og den **fandt to rækker der aldrig
kunne finde noget** — begge i `FORM_PLUGIN_SIGNATURES`, begge i begge motorer.

**Målt før rettelsen, 2026-09-27.** Fire rigtige Shopify-butikkers kurv- og
betalingssider (6 sider, hentet og gennemgået for det tekniske udsnit motoren
læser — scripts og attributter):

| Butik / side | `shopify[_-]?checkout` (gammelt) | `shopify-accelerated-checkout` (målt) |
|---|---|---|
| allbirds.com `/cart` | nej | ja |
| allbirds.com `/checkouts/cn/en-us` | nej | ja |
| deathwishcoffee.com `/cart` | nej | ja |
| kith.com `/cart` | nej | ja |
| tentree.com `/cart` | nej | ja |
| tentree.com `/checkouts/cn/en-us` | nej | ja |

**6 af 6 sider: 0 fund med det gamle mønster, 6 fund med det målte.** Mønstret
kræver at `shopify` og `checkout` står **ved siden af hinanden**; en rigtig
Shopify-side siger `shopify-accelerated-checkout`. Det er præcis opgave 63s
fejlklasse — en markør skrevet mod en adresse leverandøren ikke leverer.

**Stripe var død på samme måde, og det er den pinligere af de to.** Mønstret var
`stripe[_-]?checkout|stripe[_-]?payment|[_-]?stripe[_-]?form`, og **alle** de
former Stripe faktisk leverer, matcher det ikke:

| Rigtig Stripe-markør | Matchet før |
|---|---|
| `<form action="https://checkout.stripe.com/c/pay/cs_test_…">` | nej — "checkout" står først |
| `<script src="https://js.stripe.com/v3/">` | nej |
| `<div id="payment-element" data-stripe-key="pk_test_…">` | nej |
| `Stripe("pk_live_…")` | nej |
| `https://buy.stripe.com/6oU4gy76PgvgdBIdAXbMQ00` (vores eget betalingslink) | nej |

Det eneste der matchede var en `.php`-sti under `wp-content/plugins/
woocommerce-gateway-stripe/`, som aldrig serveres i en sides markup.

**Rettelse:** begge mønstre får de **målte** former som nye alternativer, og de
gamle bliver stående, fordi de koster intet og et specialt tema kan godt bruge
dem. `shopify[_-]?(accelerated[_-]?)?checkout` og
`js\.stripe\.com\/v[0-9]|data-stripe-(key|publishable)`. Bevis på en rigtig
kurvside: gammelt mønster **nej**, nyt mønster **ja**.

**To ting der er ærligt mindre end de ser ud til, skrevet ned fordi R5 ellers ville
læses som om dækningen var fuldstændig:**

1. `shopify-accelerated-checkout` er butikkens **accelerated-wallet-knap**, ikke
   selve betalingssiden. Den var på alle seks sider, men en butik der har slået den
   fra fanges ikke. Rækken dækker altså de Shopify-butikker der har den slået
   til — en delmængde, målt og skrevet ned, ikke antaget.
2. `js.stripe.com/v3` beviser at Strikes JavaScript er indlæst, ikke at en
   betalingsformular vises. Det er samme opgave som rækken har i forvejen: dommen
   kræver formular-markup i de samme bytes (se pluginens kommentar ved `forms`),
   så en side der kun indlæser Stripe-JS får et navn, ingen dom.

**Ingen `plugin/**`-fil rørt.** `forms`-tabellen i pluginen har to rækker — de to
her findes kun i motorerne — så der er ingen plugin-version, ingen ny zip og
ingen publiceret overflade. Rettelsen er **kode, ikke live**: motorerne deployes
af `worker-scan`, og den kan ikke deployes fra en agent (spørgsmål 9). Den
publicerede npm-CLI får den ved næste udgivelse, som Mads gør.

**Hvad `dora` krævede, og hvorfor den fik sin egen regel.** `dora` er den ene
tabel hvor installationstesten **er** prosa: de ni rækker er påstande om
virksomheden (SPF, DKIM, DMARC, MX, failover, incident response, BCP, status
page), og det eneste sted en sådan påstand står er virksomhedens egen side. R4
kræver endda at `dora` *kun* læser prosa. Så den fik regel **(e)**: mindst seks ord
og mindst to ord uden for rækkens eget navn, i stedet for kravet om `//`, `.`, `=`
eller `<`. Uden den ville `"Status page / uptime monitoring."` være **grøn** — den
har et punktum, og den er en genindskrivning af det vi led efter. Målt før
rettelsen: ingen af de ni dora-rækker var døde; de ni mønster matcher deres
egen sætning, i alle tre kopier. **R5 dækker nu alle 46 rækker.**

## Fejl 11 — tolv consent-rækker hvilede på en antagelse, og én af dem var død (opgave 66, rettet i 1.3.27)

Opgave 65 gjorde R5 i stand til at måle alle 46 rækker mod hver sin
installationstest. Opgave 66 spørger den spørgsmål, R5 ikke kan stille for sig
selv: **hvor kommer strengen fra?**

**Målt før rettelsen.** 12 af de 20 consent-rækker stod markeret `formodnet` —
antagelse, intet læst, intet svaret. En antagelse kan være lige så død som
Quantcast, og R5 kan ikke se forskellen, fordi den tester mønstret mod **min egen
streng**.

**Fundet: `Axeptio` var død for sin egen normale installation.** Leverandørens SDK
blev hentet direkte (715 445 bytes, 2026-09-27) og læst. Den sætter
`window.axeptio` — men den **indlæses** som

```
<script src="https://static.axept.io/sdk.js"></script>
```

og den adresse rummer **ikke** ordet `axeptio` (kun `axept.io`). Mønstret
`/axeptio/i` kan altså ikke finde script-tag'en; det kan kun finde det indlejrede
`axeptio('init', …)`-kald, som er den **valgfrie** form. Målt før rettelsen gav
`<script src="https://static.axept.io/sdk.js"></script>` gennem alle tre produkter
`No consent banner detected` — samme svar som en side uden samtykkeplatform.
Den gamle streng `axeptio.cdn.app/axeptio.js` svarer **000** (DNS fejler): den var
skrevet fra hukommelsen og aldrig læst.

Rettet til `axeptio|axept\.io` i alle tre kopier. Det indlejrede kald matcher
stadig, så ingen installation mister sit fund.

### De andelle elleve: otte læst, tre stadig antagelser

Alle tolv blev ført gennem leverandørens **egne** kilder — WordPress' offentlige
katalog (`api.wordpress.org/plugins/info/1.0/<slug>.json`) og leverandørens egen
kode, hentet som zip og læst. Fire af de antagede stier pegede på **filer der ikke
findes**:

| Række | Streng før rettelsen | Målt | Efter rettelsen |
|---|---|---|---|
| `Axeptio` | `axeptio.cdn.app/axeptio.js` | 000, DNS fejler | `static.axept.io/sdk.js`, **vaert 200** + læst i SDK'en |
| `CookieHub` | `app.cookiehub.com/bundle/…` | 000 | wp.org `cookiehub` (200) → `cookiehub/includes/js/dcchub-test.js` |
| `Analytify/CAOS` | `plugins/analytify/analytify.js` | 404 i kataloget | wp.org slug er **`wp-analytify`**, ikke `analytify` |
| `PixelYourSite` | `plugins/pixel-your-site/assets/js/pys.js` | 404 | wp.org slug er **`pixelyoursite`** (ingen bindestreger) |
| `OptinMonster` | `plugins/optinmonster/assets/js/optinmonster.js` | 200 på slugen, stien findes ikke | wp.org 200 (2.17.1) → `optinmonster/assets/dist/js/global.min.js` |
| `CookieYes` | `cdn-cookieyes.com/client_data/…/script.js` | 403 på opdigtet id; værtet er nævnt i leverandørens egen kode | wp.org `cookie-law-info` (200, 1 000 000 installs) |
| `iubenda` | `<div class="iubenda-cb-banner" …>` | — | wp.org `iubenda-cookie-law-solution` (200k) + `cdn.iubenda.com/iubenda.js` **vaert 200** |

Mønstrene for de tre sidste var i forvejen brede nok til at ramme de rigtige
stier, så de fund var ikke døde rækker — men **strengene var fiktion**, og en
fiktiv streng er præcis det R5 ikke kan se.

**Tre bliver `formodnet`**, fordi de ikke findes i WordPress' offentlige katalog
under det navn tabellen bruger, og deres egen vært svarer `000` eller `404`:
`CookieScript`, `CEE/PL consent plugin` (slug `shoper`), `Borlabs / CookieNinja`
og `Moove GDPR` (slug `moove-gdpr-cookie-consent`) samt `WebToffee GDPR`. De står
under ❓ og tæller **ikke** som dækning.

> En metodefejl undervejs, skrevet ned fordi den er let at gentage: en 404 fra
> WordPress' info-API er **ikke** i sig selv bevis på at et plugin ikke findes. Den
> er det kun når *begge* svar er der — API'en **og** pluginsiden, som WordPress
> sender videre til sin søgning for en slug den ikke kender. Sluggen
> `moove-gdpr-cookie-consent` gav 404 i begge, mens en opdigtet slug gav præcis
> samme to svar, så kontrol-sluggen var nødvendig.

### Ratchetten, så det ikke kan ske igen

R5 har nu **regel (f)**: højst `HOEJST_FORMODNET = 12` `formodnet`-strenge i alt.
Tallet er et **loft, ikke et mål**, og det er bevidst ikke sat ned til de fem
der står tilbage — en agent der rydder videre skal kunne sænke det, og en der
glemmer det kan ikke hæve det. To selftest-cases beviser begge veje: grøn ved
præcis tolv, rød ved tretten. Den nye række i casen står **i signatur-tabellen**,
så regel (c) ikke fyrer først og casen er rød af den rigtige grund.

## Fejl 12 — de fem sidste antagelser: fire væk, én læst (opgave 67, rettet i 1.3.28)

Opgave 66 efterlod fem `formodnet`-strenge og et loft på tolv. Opgave 67 gjorde
opgaven færdig, så der står **nul** antagelser tilbage.

**Målt før rettelsen, 2026-09-27.** De fire slug'e tabellen brugte er ikke i
WordPress' eget katalog. Ikke bare 404 i info-API'en — de **301'er til en
søgeside**, som er wp.orgs egen måde at sige at slug'en ikke findes:

| slug | `info/1.0/<slug>.json` | `wordpress.org/plugins/<slug>/` |
|---|---|---|
| `shoper` (CEE/PL) | 404 | 301 → `/plugins/search/shoper/` |
| `borlabs-cookie` | 404 | 301 → søgeside |
| `moove-gdpr-cookie-consent` | 404 | 301 → søgeside |
| `webtoffee-gdpr-cookie-consent` | 404 | 301 → søgeside |
| `cookiehub` *(kontrol)* | **200** | 200 |
| `wp-consent-api` *(kontrol)* | **200** | 200 |
| `contact-form-7` *(kontrol)* | **200** | 200 |
| `complianz-gdpr` *(kontrol)* | **200** | 200 |

Kontrol-slugene er derfor ikke til pynt: de gør målingen i stand til at skelne
mellem *denne slug findes ikke* og *mit katalog-kald virker ikke*, som var
 metodefejlen i opgave 66. CookieScripts egne værter svarer desuden 000 herfra
(`cookiescript.com`, `app.cookiescript.com`, `cdn.cookiescript.com`), og
`app.cookiescript.com` peger på 192.64.119.254 — et parkeringsområde, ikke et CDN.

**Hvad der blev gjort.** `CookieScript`, `CEE/PL consent plugin`, `Moove GDPR` og
`WebToffee GDPR` er væk fra `CONSENT_SIGNATURES` i alle tre motorer, og deres
strenge er væk fra `DAEKNING`. Det er samme skæbne som Quantcast fik i 1.3.25,
og af samme grund: en række der ikke kan finde den platform den navngiver er
ikke dækning. Den er en grøn linje i en rapport kunden betaler for.

**Borlabs blev læst, ikke fjernet.** Leverandørens eget repo
`Borlabs/Borlabs-Cookie-GTM-Variable-Template` indeholder `template.tpl` (8 205
bytes), der kalder `callInWindow('BorlabsCookie.checkCookieConsent', …)` og
`callInWindow('BorlabsCookie.Consents.hasConsent', …)`, og som henviser til
`borlabs.io/kb/google-tag-manager/`. Den dokumenterede installation er altså den
**globale `BorlabsCookie`**, ikke et filnavn. Den gamle streng hed
`…/borlabs-cookie/borlabs-cookie.js` — et filnavn jeg havde gættet. Rækken
beholdes, og den nye streng finder en side uanset hvilket asset Borlabs enqueue'r,
hvilket den gamle ikke gjorde.

**Ratchetten.** `HOEJST_FORMODNET` går fra **12 til 0**. Loftet var 12, fordi det
var antallet før de tolv blev læst; en agent der rydder videre skulle kunne sænke
det. Nu er der ingen antagelser, så reglen er ikke længere et tal men opgave 63s
krav: *en installationstest skal være læst, ellers er den ingen*. Den første
antagelse giver rødt, og selftesten beviser begge veje (`nul antagelser` grøn,
`en installationstest der kun er formodet` rød). Den nye række i casen står stadig
**i** signatur-tabellen, så regel (c) ikke fyrer først.

**Hvad det koster kunden.** `consent` går fra 20 til 16 rækker, og en side med
CookieScript, Shoper, Moove eller WebToffee får i dag **færre** fund end før.
Changelog'en siger det samme, fordi det er sandt: en plattform der tabes er
bedre end en grøn linje der aldrig kunne findes. Mønstrene for de fire var
desuden rettet mod **mappe-navne**, så de ville have fundet en installation
hvis filen hed noget andet — de var ikke døde, de var ubeviste. Det er grunden
til at de ikke kommer tilbage i denne version: de kan tilbage, når nogen har
læst leverandørens egen kode.

**Resultat i porten:** `42 af 46 rækker med installationstest` (42 står i
tabellen, 46 er det samlede antal rækker i de fire tabeller efter de fire
fjernelser), `52 af 52` negative cases uændret, `GATE GRØN — alle 24 steps`.

## Fejl 13 — et mønstalternativ fandt en leverandør, rapporten ikke navngiver (opgave 71, rettet i 1.3.31)

**Fejlen.** `FORM_PLUGIN_SIGNATURES`' række *Contact Form 7 / WPForms /
Formidable / Gravity / Fluent / Elementor* indeholdt alternativet
`ninja[_-]?forms`. Ninja Forms stod **ikke** i rækkens navn. En side der
indlæser Ninja Forms' egne scripts fik derfor dommen *"Contact Form 7 / WPForms
/ Formidable / Gravity / Fluent / Elementor detected"* — et grønt fund på seks
leverandører, hvor den installerte er den syvende, og ingen af de seks kan
findes i sidens markup.

Det er præcis opgave 70s fejl, som den samme måling havde fjernet fra
mønstret: `cognito[_-]?forms` og `\bformsort\b` lå i rækken *Typeform /
Formspree* på samme måde. **De var ikke de eneste.** Opgave 70 fjernede to
markører, den fandt ved at læse koden — og den regel, der skulle have fortalt at
der var flere, manglede stadig.

**Hvorfor ingen port så den.** R5 (regel b) læser hvert mønster og tester det
mod rækkens **egen installationstest**. `ninja[_-]?forms` matcher ingen af dem,
og det er netop ikke et problem for R5: den spørger "kan mønstret finde det, det
er skrevet til", og det kan den. Den spørger aldrig "**nævner** mønstret den
leverandør, det er skrevet til". Regel (g) fra opgave 69 går den modsatte vej — den tæller navne og kræver
en streng pr. navngiven leverandør — så de to regler er blinde for hver især
og porten er blind for fejlen mellem dem.

**Rettelsen.** Leverandøren får sit navn og sin streng. `ninja-forms` svarer
**200** i WordPress' eget katalog (2026-09-27), og `wp-content/plugins/ninja-forms/`
er den sti pluginen enqueuer sine assets fra. Rækken hedder nu *Contact Form 7 /
WPForms / Formidable / Gravity / Fluent / **Ninja** / Elementor* i alle tre
kopier. Intet er indsnævret: hvert mønster der matchede noget, matcher stadig
det, og rækken afgør om en side beder om samtykke — en falsk grøn række dér er
dyrere end en rød.

**Den nye regel (i), så den ikke kommer tilbage.** `contractAlternativer` i
`tools/check_signature_prose.mjs` læser hvert `|`-adskilt alternativ i alle fire
tabeller i alle tre kopier og spørger, om det kan spores til en leverandør
rækken navngiver. Tre veje, i den rækkefølge de skal bruges:

1. **navnet** — alternativet rummer et navneord fra en leverandør i samme række
   (`cookiebot` i *Cookiebot / OneTrust / …*). Parentensens indhold tæller med,
   fordi det i `dora` er en **beskrivelse af samme markør**: *MX (Mail exchange)*
   finder `mail[ _-]?exchange`, og uden parentesens indhold ville det være et fund
   på *Mail exchange* i en række der kun hedder *MX*.
2. **installationstesten** — alternativet står bogstaveligt i en af rækkens
   strenge. Strengene er målte installationer af de **navngivne** leverandører,
   så `otSDKStub` (OneTrusts egen stub) og `s.pinimg.com/ct` (Pinterests egen
   loader) er sporet uden en note.
3. **`ALIASSER`** — en note, fordi 1 og 2 ikke kan se en **forkortelse**:
   `wpcf7` er ikke *Contact Form 7* med mellemrum væk. Noten skal pege på en
   leverandør der står i navnet, og begrundelsen skal være en måling.

**Fejl i min egen regel, fundet mens jeg skrev den.** Tre ting var forkert i
første udkast, og alle tre ville have givet **flere** røde end de fortjente —
altså en port agenten lærer at ignorere:

- **Tegnklasser i normaliseringen.** `js\.stripe\.com\/v[0-9]` blev til
  `jsstripecomv09`, som ikke findes i installationstestens `js.stripe.com/v3` —
  så porten ville have meldt en fejl på en markør der *er* målt. `[...]` er
  valg, ikke navne, og er nu fjernet før normalisering. Målt: de fire
  `forms`-huller faldt fra ni til syv.
- **To-bogstavs navne.** `MX` er to tegn, og tærsklen var tre, så *MX (Mail
  exchange)* tabte alle tre af sine egne alternativer. Tærsklen er nu to.
- **Parentes læst efter de var fjernet.** `navneKandidater` kaldte
  `leverandoerer()`, som fjerner parentesen — altså fjernede den præcis den
  beskrivelse, parentesen rummer. Parenteserne læses nu på den **rå** streng.
  Målt: dora faldt fra syv til fire.

Et fjerde sted, der ikke var en fejl men et valg: attributtet `data-stripe-(key|publishable)`
er **ét** alternativ med to veje, og kun den indre `data-stripe-key` står i
strengen. Tilskrivningen prøver derfor alle fragmenter af et alternativ, ikke
kun helheden — ellers ville porten melde en fejl der ikke er der.

**Målingen.** 86 forskellige alternativer på tværs af alle tre kopier.
**27 kan ikke spores** — consent 5, trackers 11, forms 7, dora 4 — og de er
opgjort pr. række i opgave 72 med den måling, der lukker hver. Ratchetten står
**pr. tabel** (`HOEJST_UTILREGNET`), ikke samlet: et samlet tal ville give
consent-tabellen tilladelse til trackers' huller, fordi hver test kun dømmer sin
egen. Loftet må kun synke.

De 27 er ikke alle fejl. Nogle er leverandørens **egen JS-funktion** — `fbq(`,
`hj(`, `snaptr(`, `ttq.`, `pintrk(` — som vejen 1 og 2 ikke kan se, fordi de er
forkortelser af navnet; de skal have en `ALIASSER`-note. Én er en fejl af
opgave 70s slags og ligger i samme række stadig: **`cookie[_-]?notice` i rækken
*Generic cookie consent banner*** er slug'en på *Cookie Notice Lite*, som er en
egen række i samme tabel. Og to af `forms` er hverken navn eller målt kode:
`caldera[_-]?forms` (Caldera Forms svarer **404** i WordPress' eget katalog under
`caldera-forms`, så intet kan læses herfra — samme som JustUno, Privy og Jotform
i opgave 70) og `wc_[_-]?checkout` (WooCommerces egen klasse hedder
`woocommerce-checkout`, jf. opgave 65 del 2).

**Resultat i porten:** `51 signatur-prosatest` (47 → 51, fire nye
regel-(i)-tests), `70 af 70` negative cases (63 → 70 — syv nye: opgave 70s
`cognito`/`formsort` genskabt i alle tre kopier skal give rød, fire grønne
beviser på at reglen ikke er rød af design, og to røde på en `ALIASSER`-note
til en leverandør uden for navnet og på en begrundelse uden måling),
`GATE GRØN — alle 24 steps`. Plugin **1.3.31**.

## Fejl 14 — elleve tracker-markører pegede på leverandører rapporten ikke kunne navngive (opgave 72 del 2)

Regel (i) blev skrevet i opgave 71 med 27 målte huller: mønstalternativer der
finder en platform, men hvor ingen kilde kunne tilskrive dem en leverandør, rækken
navngiver. Opgave 72 del 1 lukkede consent-tabellens fem. Del 2 er `trackers`
med elleve, og målingen delte dem i to klasser, som viste sig at kræve to
forskellige rettelser.

**Seks var værter eller funktioner i leverandørens egen kode — de blev læst, ikke
antaget.** Ratchetten går 11 → 5, og intet i porten blev slappet for at få den
til at synke.

To var **værter, rækken matchede men ingen installationstest dækkede**. Begge viste
sig at være præcis leverandørens egen adresse, så rigtigvis manglede
installationstesten og ikke mønstret:

- `ct.pinterest.com/v3/` står i Pinterests **egen installationsside**
  (`help.pinterest.com/business/article/install-the-base-code`, 200, 148 228
  bytes). Rækken havde kun `s.pinimg.com/ct/core.js`, så vejen 2 ikke kunne se
  den. Strengen er udvidet, ikke mønstret indsnævret.
- `www.googleadservices.com/pagead/conversion.js` **er** Googles eget
  konverteringsscript — målt 200, og filen definerer `google_conversion` 19
  gange. Rækken hed *Google Ads remarketing*, så det er præcis den kode. Også
  her udvidet strengen.

Fire var leverandørernes **egne globale funktioner**. De kan per definition ikke
findes i installationstesten, fordi strengen er et `<script src>`-tag, mens
funktionen defineres i det indlejrede kald der indlæser den — så de fik
`ALIASSER`-noter, hver med en måling i leverandørens egen kode:

| Alternativ | Række | Målt i leverandørens egen kode |
|---|---|---|
| `fbq(` | Meta (Facebook) Pixel | `connect.facebook.net/en_US/fbevents.js` (200, 424 690 B) rummer `fbq` **83** gange; Metas egen udviklerreference viser `fbq('track')` |
| `snaptr(` | Snapchat Pixel | `sc-static.net/scevent.min.js` (200, 59 319 B) rummer `snaptr` **5** gange |
| `pintrk(` | Pinterest Tag | leverandørens egen installationsside har `pintrk('load', 'YOUR_TAG_ID')` ved siden af `s.pinimg.com/ct/core.js` |
| `google_conversion` | Google Ads remarketing | `www.googleadservices.com/pagead/conversion.js` (200) definerer den **19** gange |

**Fem blev ikke lukket, og de fik ingen note.** Målingen, der kom ud af at prøve,
er skrevet ned her, fordi den er dyrere end de seks fund:

- `hj(` — `help.hotjar.com` svarer **403** på sit eget installations-artikel,
  `hotjar.com/docs/hotjar-tracking-code` er **404**, og hotjar.com's egen forside
  (200, 415 922 B) rummer **0** forekomster. Hotjar bruger sin egen sporing
  gennem et andet klient-id end den rækken vedligeholder.
- `_linkedin_partner_id` — LinkedIns hjælpeartikel er 200 men klient-renderet
  (52 261 B, 0 forekomster), og leverandørens eget script
  `snap.licdn.com/li.lms-analytics/insight.min.js` er kun **3 326 B**: en loader,
  ikke koden. Den har `partner_id`, ikke `_linkedin_partner_id`.
- `ttq.` — `ads.tiktok.com/help/article/get-started-pixel` er 200 men **1 542 739
  B uden ét `ttq.`**. Den eneste forekomst i TikToks næste artikel var en
  **fejlmatch**: pixel-id'et `5KXttq2qqWM6REORtjRf1s`, hvor `ttq` er to tegn i en
  tilfældig nøgle. Den slags match skal afvises, ikke tages til siglighed for.
- `static.tiktok.com` — **ingen DNS** (`dig +short` er tom).
- `cdn.pinterest.com.*pin.*js` — **ingen DNS**. Pinterests egen side bruger
  `s.pinimg.com`, som rækken allerede dækker.

De to døde værter er værd at beslutte om i næste iteration: en død
CDN-adresse i et mønster er dækning på papiret. De er **ikke** fjernet her, fordi
opgave 60 viste at en for snæver markør giver en **falsk grøn** — det dyreste fund
i tabellen — så beslutningen skal måles på rigtige sider, ikke gættes.

**Selftesten** får case 31f, der tømmer `ALIASSER` uden at sænke ratchetten, så
porten skal blive rød på de seks noter den mister, og en grøn case der beviser at
de faktisk giver sporing. Uden case 31f ved næste agent ikke, om lukningen skyldes
noterne eller et tal — og det er præcis den fejl opgave 63 så ud som en grøn
linje. `51 signatur-prosatest`, `73 af 73` negative cases (var 70),
`64 installationstester` (62 → 64), `16 mønstalternativer` (22 → 16),
`GATE GRØN — alle 24 steps`. **Ingen `plugin/**`-fil rørt** — kun `tools/` og
`docs/`, så ingen ny version, ingen ny zip, ingen publiceret overflade.

## Fejl 15 — en platform, der er *lukket* i kataloget, så ud som død (opgave 75, rettet i 1.3.33)

`caldera[_-]?forms\b` lå i CF7-rækkens mønster siden længe, men **ikke i
navnet** — præcis opgave 71s Ninja, en række længere ned i samme liste. En
Caldera-side fik derfor *"Contact Form 7 / WPForms / Formidable / Gravity /
Fluent / Ninja / Elementor detected"*: et grønt fund på syv leverandører, hvor
kunden kører den ottende, og ingen af de syv kan findes på siden. Rækken er den
der afgør, om en side beder om samtykke, så en falsk grøn dér er dyrere end en
rød.

**Målingen er den interessante del, fordi den peger på en fejl type agenten
let gentager.** WordPress' egen info-API svarer på `caldera-forms`:

```json
{"error":"closed","closed":true,"closed_date":"2022-04-05",
 "reason":"author-request","reason_text":"Author Request",
 "description":"This plugin has been closed ... This closure is permanent."}
```

Det er **ikke** en død platform. Leverandørens eget repo `CalderaWP/caldera-forms`
er ikke arkiveret, sidste push 2024-06-11, 189 stjerner, og to linjer i dets kode
danner præcis den installation strengen skriver:

- `caldera-core.php:55` — `define('CFCORE_URL', plugin_dir_url(__FILE__));`, altså
  mappen `wp-content/plugins/caldera-forms/`
- `classes/render/assets.php:259` og `:315` — `self::make_url('caldera-forms-front')`,
  og `make_url()` bygger `$root_url . 'assets/build/js/' . $name . '.min.js'`
  (linje 637) med `$root_url = CFCORE_URL` (linje 573)

Strengen er derfor `…/wp-content/plugins/caldera-forms/assets/build/js/caldera-forms-front.min.js`
— **pluggens egen mappe**, målt i koden. Filen hedder det og er 152 489 B.

**Reglen for den næste agent, skrevet ned fordi den er billig at bryde:** *et
lukket wp.org-slug er ikke en død platform.* Opgave 70 fjernede Jotform, Privy
og JustUno fordi **alle** deres dokumenterede stier var 404/403/520 — platformen
kunne ikke læses nogen steder. Caldera kan læses i leverandørens eget repo, så
den fik navn og streng. Fjerner man en platform på katalog-svaret alene, gør man
opgave 70s fejl på en platform med 189 stjerner.

**Ratchetten går `forms` 2 → 1**, så 11 → **10** i alt. `51 signatur-prosatest`,
`66 installationstester` (65 → 66) for `52 navngivne leverandører` (51 → 52).
Ingen ny regel og ingen ny negativ case: rettelsen er en navngivelse plus en
målt streng, og portens regel (g) — én streng pr. navngiven leverandør — var
allerede rød, fordi navnet krævede den. Uden den streng ville porten være blevet
rød ved navnet alene, så rettelsen er ikke valgfri.

**To fund ved siden af, i en kundevej.** `site/_redirects` havde ingen linje for
`eucomply-1.3.29.zip` eller `eucomply-1.3.31.zip`, selv om begge pakker var fjernet
fra træet ved tidligere udgivelser: en installation på en af dem bad om sin egen
pakke og fik en 404. Begge har nu en linje, og `redirect_findings` i porten læser
den version, `sections.changelog` nævner som den foregående — som var **1.3.24**,
fordi `sections.changelog` var fire udgivelser bag `changelog`. Den er nu ajour,
så porten dømmer den version den erstatter.

## Fejl 16 — fire DORA-markører pegede på noget, rapporten ikke kunne navngive (opgave 72 del 4)

**Målt 2026-09-27.** `contractAlternativer` delte `dora`-tabellens fire
ubeviste alternativer i to helt forskellige klasser, og det er den anden
klasse der er den interessante:

- **Ét var sporbart ved læsning.** `security[ _-]?incident` lå i mønstret for
  *Incident response / SOC reporting* uden at ordet *security* findes i
  navnet, og vejen gennem installationstesterne havde ingen «security
  incident»-sætning at finde. Beviset er læst i **UK's egen** side om
  hændelsesstyring — ikke en marketing-side, men en myndighedsside om præcis
  den praksis rækken påstår at måle:
  `www.ncsc.gov.uk/collection/incident-management` svarer **200** (136 142
  bytes) og skriver «security incident» **3 gange**, herunder i løbende prosa
  om, hvilken teknologi et hændelsesresponsteam har brug for. Den sætning står
  nu som rækkens **anden** installationstest, så regel (e) dømmer den som prosa
  (mindst 6 ord, mindst 2 ord uden for rækkens navn) og regel (b) kræver at alle
  tre kopiers mønster kan finde den.
- **Tre var ikke sporbart, og de kræver alle tre en mønsterændring** — altså en
  ændring i `shared/scan-engine.js`, `eucomply-scanner/engine/index.js` **og**
  `plugin/eucomply.php`, som ikke kan gøres uden plugin-udgivelse. De blev derfor
  **målt** i stedet for lukket, og målingerne står i `HOEJST_UTILREGNET`:
  `bcp[ _-]?plan` er **død** («bcp plan» 0 gange på
  `en.wikipedia.org/wiki/Business_continuity_planning`, 200, 363 579 bytes, som
  skriver *BCP* 23 gange og *business continuity* 227 gange — samme klasse som
  `shopify[_-]?checkout` i opgave 65 del 2); `multi[ _-]?az[ _-]?dns` er den
  fulde form 0 gange på syv hentede sider, mens `multi-AZ` i prosa står 62
  gange på AWS' egen RDS-dokumentation, så rettelsen er at **udvide** til
  `multi[ _-]?az` (en ægte supermængde) og ikke at fjerne; `redundan` er kun
  bekræftet som *linktekst* («Design for redundancy», Microsofts egen
  resiliency-side, 200, 35 461 bytes) og **0 gange i prosa** på Postgresqls to
  HA-dokumenter og Hetzners forside, så valget er at navngive ordet i rækken
  (opgave 52) eller fjerne markøren.

**Ratchetten `dora` går 4 → 3**, så 10 → **9** i alt. `51 signatur-prosatest`,
`67 installationstester` (66 → 67), `76 negative selftest-cases` (75 → 76 — den
nye case 31i sletter NCSC-sætningen igen og kræver rødt, så beviset er
bærende og ikke en note der kan slettes), `GATE GRØN — alle 24 steps bestået`.
Ingen motor, ingen plugin, ingen ny version, ingen ny zip.

**Selftestens egen etiket blev rettet samtidig.** Den sagde «(i) (alle
alternative i dora-tabellen er sporet)» mens tre åbenbart stod i ratchetten.
Det er opgave 45bs fejlklasse — en grøn etiket der siger det modsatte af det
den måler — flyttet til selftestens egen tekst. Efter opgave 72 del 5 og 6 står
alle fire tabeller på 0, så etiketten siger nu at **alle** alternative i
`dora` er sporet, hvilket er sandt.

## Fejl 17 — en installationstest der var skrevet fra hukommelsen, og en markør der ikke findes (opgave 72 del 6)

**Fejlen.** Rækken *Stripe Checkout / Payment* havde **to** installationstester.
Den ene var `<div id="payment-element" data-stripe-key="pk_live_a1b2c3"></div>`, og
dens bevisstyrke lød «vaert 200 · payment-element læst i leverandørens egen v3-fil».
Attributten `data-stripe-key` forekommer **0 gange** i `js.stripe.com/v3/`. Den
blev altså skrevet fra hukommelsen, og **intet mønster i rækken matcher den** undtagen det
alternativ, der også var opdigtet.

Det er opgave 60s fejlklasse, som her gav sig selv: en **falsk grøn** måling i en
betalt vare. Alt efter var grønt — R5 fandt mønstret i installationstesten, og
regel (i) fandt en leverandør i rækkens navn — fordi porten læser det, den er
skrevet til, og den opførte sætning er præcis den slags streng der får begge dele
til at sige ja. Bevisstyrken var den eneste, der kunne have stoppet den, og den
lød som en måling.

**Målingen.** Alle fem kilder svarer 200:

| Kilde | Størrelse | `data-stripe-key` / `-publishable` |
|---|---|---|
| `checkout.stripe.com/checkout.js` | 90 238 B | 0 / 0 |
| `js.stripe.com/v3/` | 1 121 765 B | 0 / 0 |
| `docs.stripe.com/payments/accept-a-payment` | 1 711 358 B | 0 / 0 |
| `docs.stripe.com/js/custom_checkout/init` | 2 149 961 B | 0 / 0 |
| `docs.stripe.com/payments/checkout` | 489 398 B | 0 / 0 |

To ting ved de to script-filer er værd at sige, fordi de lukker spørgsmålet om
hvor markøren så kom fra. `js.stripe.com/v3/` indeholder to `data-stripe-` —
`data-stripe-backdrop-id`, som Stripe selv sætter på sin egen dialog, og intet
andet. Og `checkout.stripe.com/checkout.js` læser slet **ingen** data-attributter:
0 `dataset`, 2 `getAttribute`. Nøglen kommer altså fra købmandens egen markup,
ikke fra leverandørens fil — så attributten kan ikke dokumenteres i den, og ingen
fil fra leverandøren er det sted, den skal måles.

**Rettelsen, og hvorfor fjernelsen ikke taber noget.** `data-stripe-(key|
publishable)` er væk fra mønstret, og den opdigtede streng er væk fra porten. Den
taber intet målbart, fordi attributten kun betyder noget for Stripe.js — og
Stripe.js hentes fra `js.stripe.com/v3`, som er et alternativ der stadig står i
rækken og den eneste streng den har. Enhver side der har den attribut, indlæser
altså den fil, rækken allerede finder. Det er **ikke** samme sag som
`shopify[_-]?checkout` i opgave 65 del 2, hvor markøren var den eneste vej til en
hele familier af sider.

**Rækken hedder nu `Stripe`, ikke `Stripe Checkout / Payment`.** Regel (g) kræver
én installationstest pr. navngiven leverandør, og ` / ` gør *Stripe Checkout* og
*Payment* til to leverandører. Da den anden streng forsvandt, stod der én
leverandør og to navne der så ud som to firmaer. Et navn der tæller flere
leverandører end rækken dækker får en agent til at skrive en streng til en streng,
der allerede dækker alt.

**En fejl i selftesten, fundet fordi den blev skrevet.** Den negative case for
dette spørgsmål tog formen: sæt `data-stripe-(key|publishable)` tilbage i
mønstret og kræv rødt på regel (i). Den var **grøn**. Ikke fordi porten er gåt i
stykker, men fordi den bevidst ikke kan se denne fejl: `normalisér()` gør
alternativet til `datastripekeypublishable`, og vejen gennem navnet matcher, fordi
«stripe» er en del af det. Samme blindhed som `\b` i opgave 72 del 3 og
tegnklasserne i opgave 71 — porten læser et *fragment* af et alternativ som sit
eget navn. Den mutation der **kan** være rød er den ægte fejl, den opdigtede
streng: intet mønster matcher den, så regel (b) fanger den samme sekund den
skrives ind igen. Den er skrevet ind, og **79 af 79** negative cases fanges.
