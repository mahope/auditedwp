# Konkurrentpriser på vs/*-siderne

**Problem.** Otte sider under `site/vs/` skrev andres priser som rå fakta i en
sammenligningstabel. Der var ingen kilde, ingen dato, og ingen port der gjorde
det umuligt at skrive et nyt tal. Da siderne blev læst mod leverandørernes egne
prissider den 28. september 2026, var **syv af otte forkerte**.

## Fundene, målt mod leverandørens egen prisside

| Side | Vi skrev | Leverandøren viser (28/9) | Fejlen |
|---|---|---|---|
| termly | Free 1K pageviews, Pro $10/mo, Business $25/mo | Free $0 med **10.000** bannervisninger, **Starter** $10, **Pro+** $15 | Planerne "Pro" og "Business" findes ikke; gratis er 10× så stort som skrevet |
| complianz | Personal **€59**/år (1 site) | Personal **$59**/år, **€35**/år i EUR | Dollar-tallet stod som euro-pris |
| cookiebot | Essential **$9**/mo, Premium fra €30 | **Premium Lite €7**/mo … XLarge €90 | "Essential" findes ikke, og indgangen er €7 ikke €30 |
| iubenda | Essentials **~€27/år**, Plus €6.99/mo | Essentials **€4,99/md** pr. site (årligt) | ~10× for lavt, fordi månedsprisen var læst som årlig; "Plus" findes ikke |
| usercentrics | Pro ~**$34**, Business ~**$56**/mo | **€30** og **€50**/måned, ekskl. moms | Forkert valuta |
| enzuzo | ~$9–$49+/mo | $7 → $99/md, offentligt | Området var ikke forkert, men vagt |
| osano | "priser er ikke offentlige" | Free $0 og **Plus $199/md** er offentlige | Vi sagde "ikke offentligt" om noget der er det |
| onetrust | "typisk **$350+/mo**" | Ingen priser overhovedet; kun tilbud | Vi fremstillede et tal som fakta uden nogen kilde |

Det er ikke en kosmetisk fejl. Sammenligningssiden *er* produktet på de otte
URL'er: en læser der tjekker Termlys egen side og ser at "Pro" og "Business"
ikke findes, har grounds til at tro at resten også er opdigtet — inklusive
vores egen $79.

## Rettelsen: en kilde, og en port der dømmer mod den

`tools/competitor_facts.json` er nu den eneste kilde til hvad vi påstår om
andre. Hver konkurrent har sin prisside som `source`, en `checked`-dato, en
`currency_note` der siger hvad valuta siden viser, et `public_prices`-flag og
en liste af `claims` — de sætninger, siden faktisk viser.

Hver `vs/*`-side bærer nu:

- `data-competitor="<slug>"` på den celle og den pris-boks, der handler om
  konkurrenten, så porten ved præcis hvad den dømmer
- en `data-fact-source="<slug>"`-note under tabellen med kilden som link og
  `checked`-datoen som synlig tekst

`tools/check_competitor_facts.py` (trin 35 i gaten) har syv regler:

| Regel | Hvad den dømmer |
|---|---|
| R1 | Enhver `data-competitor` skal findes i JSON |
| R2 | Enhver optegnelse skal have en side — ingen forældede optegnelser |
| R3 | Siden skal vise `checked`-datoen, kildens navn og et link til kilden |
| R4 | `checked` må ikke være ældre end 180 dage, ellers er siden for gammel til at tale om andres priser |
| R5 | Alle `claims` skal stå i cellen |
| R6 | En konkurrent med `public_prices: false` må ikke have et valutatal nogen sted |
| R7 | Ethvert tal i konkurrentcellen skal kunne findes i en `claim` |

R1–R6 dømmer fortiden. **R7 dømmer næste diff** — den som ingen har skrevet
endnu. Det er den regel, der gør en ny pris umulig at smugle ind.

### R6 og vores egen pris

R6 så først vores egen `$79` og `$0` og erklærede OneTrust-siden for skyldig.
Det er en fejl i porten, ikke på siden: den skal dømme konkurrentens tal, ikke
vores. `mask_own_prices()` læser derfor *vores* pris-bokse fra siden og
maskerer de tal, før den skænder. Ingen pris er hardkodet i porten, så den
holder når Mahopes pris ændrer sig.

## Bevis

- `tools/check_competitor_facts.py` — grøn på 8 sider og 8 optegnelser
- selftest — grøn, 7 negative cases
- **Porten blev provokeret med de to fejl siderne faktisk havde**: `Business
  $25/mo` ind i termly-cellen fanges af R7, `Usually $350+/mo` ind i
  onetrust-boksen fanges af R6
- `tools/quality_gate.sh` — `GATE GRØN — alle 35 steps bestået`

## Hvad der bevidst ikke blev gjort

- **Ingen ny blok, ingen ny side, ingen nye links i navigationen.** Rettelsen er
  otte eksisterende sider der bliver sande, plus en port der holder dem sande.
- **Ingen plugin-version, ingen `update.json`, ingen ny zip, ingen
  Stripe-pris, ingen worker, ingen deploy** — intet af det rører salget.
- **Ingen planlagt pris-overvågning.** Det er en reel mangel: 180 dage er lang
  tid, og de fire sider vi rettede var skrevet før i år. En automatisk
  pris-overvåger er opført som næste opgave, ikke bygget her — den kræver en
  kørende service, og en agent må ikke oprette nye services.
- **Sibling-kørslen i `../hermes-passiv` kunne ikke køres i denne session**
  (adgang til mapper uden for workspace blev afvist). Repoets egen gate er
  evidensen, præcis som i iteration 104 og 105.
