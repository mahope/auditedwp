# Juridiske sider skal kunne læses på dansk, svensk og nederlandsk

Spec for opgave 52, skrevet før den fulde rettelse. Målingen er gjort først, og
den viste to forskellige fejl — ikke én.

## Fejl 1: `legal` var en score, ikke en etiket

22 rigtige footer-links (otte dokumenttyper × dansk, svensk, nederlandsk) kørt
gennem `LEGAL_PATTERNS` i `shared/scan-engine.js`: **0 af 22 fundet**. Følgen
er ikke en manglende beskrivelse, men et **tabt point**. En dansk butik med
privatlivspolitik, handelsbetingelser og cookiepolitik i footeren:

| sprog | juridiske sider fundet | `legal` |
|---|---|---|
| dansk | 1 | *advarsel*, tabt point |
| svensk | 1 | *advarsel*, tabt point |
| nederlandsk | 1 | *advarsel*, tabt point |
| engelsk | 2 | **bestået** |
| tysk | 2 | **bestået** |

Den samme butik får et **anden scorenummer** alt efter hvilket sprog den skriver
på. Efter opgave 51 var privatlivsmønsteret sprogneutralt, så privatliv blev
talt; vilkår og cookiepolitik gjorde det ikke — og de er netop de to dokumenter
`legal` kræver to af (`uniqueLegal.length >= 2`).

## Fejl 2: `terms` havde en fejl, der var større end sprog

Separatoren var `[_-]?`: bindestreg **eller** understreg, valgfri. Den matcher
aldrig et **mellemrum**. Målt:

| fundet | ikke fundet |
|---|---|
| `terms-of-service` | `Terms of Service` |
| `terms_of_service` | `Terms & Conditions` |
| | `Terms and Conditions` |
| | `Terms of Use` |
| | `Allmänna villkor` |
| | `Algemene Voorwaarden` |

Så det engelske mønster ramte præcis de to former, ingen skriver, og de to
nederlandske/svenske sidenavne med mellemrum. Dette er en fejl, der ikke kræver
at man kan sproget for at se den.

## Beslutning

Ret `Cookie policy` og `Terms & Conditions` først, som opgaven siger. Hvert
mønster rettes på sin egen måling, og resten af de syv er opgave 53.

### De nye stængler

| mønster | DA | SV | NL |
|---|---|---|---|
| `Cookie policy` | `cookiepolitik` | `kakpolicy` | `cookies?beleid` |
| `Terms & Conditions` | `handelsbetingelser`, `vilk[aå]?r for brug` | `allm[aä]nna villkor`, `anv[äa]ndningsvillkor` | `algemene voorwaarden` |

Separatoren i `terms` er rettet fra `[_-]?` til `[ _-]?`, som tillader
mellemrummet.

### Hvad der bevidst **ikke** kom med

Porten har fixtures på præcis de tre fejltagelser, og de holdt:

- **ikke** `betingelser` — den danske sætning *"alle vores leveringsbetingelser
  gælder"* er et helt andet ord, ikke en vilkårside.
- **ikke** `villkor` — *"Köpvillkoren och returvillkoren framgår av
  orderbekräftelsen"* er prosa, ikke et link. `returvillkor` blev lagt ind i en
  tidligere udformning og fjernet igen, fordi porten fangede den.
- **ikke** `voorwaarden` — *"Onze voorwaarden voor de gratis proefperiode"* er
  prosa.
- **ikke** `vilka` — det er et almindeligt ord i dansk og svensk (*"se hvilke
  produkter vi har"*), ikke en vilkårside.

### Accenter

`allm[aä]nna` og `vilk[aå]?r` har en tegn-klasse med accenten. Det er tilladt
her og kun her: `LEGAL_PATTERNS` læses **kun** af de to JS-motorer (målt: ingen
forekomst i `plugin/eucomply.php`), og begge er JavaScript, så de læser ens.
Hvis linjen nogensinde kopieres til PHP, skal den accenterede alternativ
fjernes først — ellers matcher JavaScript og PCRE den samme linje forskelligt,
fordi sidstnævnte matcher bytes og ikke tegn. Det er præcis den fejlklasse
opgave 51 måtte, og den blev fjernet dér; den skal ikke genindføres her.

Pluginens `legal` er en **anden** mekanisme: den slår WordPress-sider op efter
sti og titel (`imprint`, `impressum`, `Accessibility%`), ikke markup, og den har
sit eget sproghul. Den er opgave 53 og ikke en del af denne rettelse.

## Hvordan det måles

`tools/check_legal_langs.mjs` (gate trin 21) kører `legal` i **begge** motorer
på elleve fixtures og håndhæver fire regler:

- **R1 — dækket, ikke antaget.** For hvert (mønster, sprog) i portens egen
  dækningstabel skal portens *egne* stængel se fixturet, og begge motorer skal
  tælle mønsteret med sit navn i det `detail` kunden læser. En tabelrække uden
  fixture er rød. Mønsternes navne læses ud af `detail`, fordi
  `LEGAL_PATTERNS` ikke er eksporteret — og fordi det er den tekst, porten skal
  måle.
- **R2 — de to motorer er samme produkt.** Identisk `pass` og `detail`.
- **R3 — ingen nye falske fund.** De tre sætnings-fixtures skal give nul juridiske
  sider, og siden med ét link skal stadig være en advarsel. R1 alene kan ikke se
  det: enhver bredere regex består R1 og taber point på kunden.
- **R4 — samme dom, samme dokumenter.** Dansk, svensk og nederlandsk footer med
  de samme tre juridiske dokumenter skal give præcis samme `legal`-dom som den
  engelske. Det er asymmetrien fra målingen, som en regel.

Selftesten har otte negative cases og **fire mutationer mod repoets egne
filer**: for hvert af de to mønstre fjernes de nye sprog fra en kopi af hver
motor, og porten skal blive rød på den fixture der bærer sproget. Mutationerne
er skrevet mod den lange linje, så de fejler med *"fandt ikke den linje den
erstatter"* den dag et nyt sprog kommer til, frem for at stå grønne på en
mutation de ikke længere rammer.

## Fund i min egen diff

Fire, og ingen af dem blev fundet ved at læse koden:

1. **`returvillkor` var for bred.** Den blev lagt ind, ramte prosaformen
   "returvillkoren", og den negative fixture gjorde den rød. Fjernet igen.
2. **`vilka(?:r|år)` er ikke `vilkår`.** Det danske ord er v-i-l-k-**å**-r;
   der *er* intet "vilka" i det. Stænglen var død, og R1 sagde det.
3. **`vilk[aå]?r` var en anden død stængel.** Efter rettelsen i punkt 2 skrev
   portens egen liste stadig ikke "Vilkår for brug", fordi den havde samme
   fejl. R1 igen.
4. **R2 sammenlignede `undefined` med `undefined`.** `verdicts` er
   `[hvem, dom]`-par, og `const [a, b] = verdicts` gav tupler, så `a.pass` var
   `undefined` på begge sider. Reglen var grøn for enhver afvigelse mellem
   motorerne — altså var den ingen regel. Selftestens R2-case fandt den.

De tre første er samme fejlklasse som opgave 42 fund 2: en stængel skrevet efter
det forventede ord i stedet for efter det ord, der står i koden. Den fjerde er
opgave 30 fund 1, 32 fund 1 og 41 fund 1 for fjerde gang: en kontrol, der læser
en mindre mængde end den skal dække.
