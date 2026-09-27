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
