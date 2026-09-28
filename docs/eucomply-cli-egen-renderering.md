# Én renderer i CLI-pakken (28. september 2026)

Målt 28/9 2026 mod `tools/fixtures/webflow.com.json` (optagelse af webflow.com,
510 616 B) og den publicerede `bin` (`eucomply-scanner/package.json` → `bin`).

## Fundet

Pakken indeholdt **to renderere af den samme rapport**:

| | `cli/eucomply.js` (**det folk kører**) | `engine/index.js`'s egen `main()` |
|---|---|---|
| Score | `Score: 3/9 (33%)` — det forudindtagede ni-tal | `3/6 of the checks that apply to this site (50%)` **og** `All 9 checks: 3/9 (33%)` |
| Betingede rækker | nævnt **ikke** | `- not counted: tcf — …` (én linje pr. række) |
| Råd | **0 `💡`-linjer** | `💡`-råd på 6 af 9 rækker |

`main()` kører kun når motorfilen selv er `argv[1]`, altså aldrig for en bruger
der har installeret pakken. Resultatet: **hele den gratis scanner printer det
rå ni-tal og dropper både rådet og forklaringen på hvorfor tre rækker ikke
tæller** — mens `/scan/`, `/pro/sample-report/` og rapporten i pluginen bruger
den delte tale. Samme motor, to sprog, og det dårligere sprog stod i det
program folk faktisk kører.

## Rettelsen

`engine/index.js` får én eksporteret funktion, `renderReport(report)`, som
returnerer den fulde tekst. `main()` kalder den, og `cli/eucomply.js` kalder
den samme funktion i stedet for at formatere selv. Der er ingen gengivelse af
motorens formatering andet sted i pakken.

Rækkefølgen i rapporten er motorens, uændret: overskrift med URL, platform +
varighed, det delte score (`… of the checks that apply to this site`), én
`- not counted:`-linje pr. betinget række, så ni-tallet til sidst, ni domme med
`detail` og `💡 fix`, og til sidst disclaimeren.

## Hvad der *ikke* ændres

- Motorens domme, betingelser, signaturtabeller og SSRF-guard røres ikke.
- `--json` er uændret: rå JSON er rå JSON, uanset renderer.
- `shared/scan-engine.js` (worker-kopien) røres ikke for denne del. Den har
  ingen CLI, så den har ingen anden renderer at glide fra.

## Målet

`tools/cli_render_parity.mjs` (ny, trin 32 i gaten):

- **R1** — `bin`'s stdout mod fixture'en skal være **byte-identisk** med
  `renderReport(runScan(...))` på samme fixture. Kun `Duration: <heltal>ms` må
  afvige, fordi det er en måling af det kørende øjeblik.
- **R2** — `cli/eucomply.js` må ikke selv formatere: nul dom-ikoner, nul
  `report.score`, nul `report.checks`. En renderer der kommer tilbage i `bin`
  gør porten rød.
- **R3** — dom-ikonerne må findes i **præcis én** fil i pakken, og den fil skal
  eksportere `renderReport`. Det er den regel der gør "to renderere" umuligt
  frem for rettet én gang.
- **R4** — udskriften skal indeholle det delte score og mindst én
  `- not counted:`-linje. Uden denne regel kunne motoren engang miste den delte
  tale, og så ville R1 være grøn af en grund den ikke måtte være grøn af.

`tools/build_cli_example.py` (trin 31) får R2 rettet, fordi den Undtagelse
`Duration:` lå i en linje for sig selv. Nu ligger varigheden i
`   Platform: …  |  Duration: …`, så undtagelsen skal være **cifrene i en
linje hvis øvrige indhold er låst** — ellers kunne R1's undtagelse flytte sig
til en linje med noget nyt i.

## Det vi ikke kan rette herfra

npm-pakken `@mahope/eucomply-scanner@1.0.1` er publiceret fra den gamle kode og
kan ikke rettes af os (vi må ikke publisere). `tools/check_published_engine.mjs`
**måler** derfor om den publicerede `bin` har sin egen renderer, og **rapporterer**
det, præcis som det gør med SSRF-guarden: en afvigelse vi ikke må rette, er en
rapport og ikke et fund, ellers låser porten hvert merge og dermed hele sitets
deploy. Indtil Mads publicerer 1.1.0 har `npx`-brugere den svagere rapport.
Det er derfor, rettelsen også gør `/cli/` ærlig om installationsvejen — ikke
fordi teksten skal være dårligere, men fordi to forskellige output på samme
motor er det værste af alt.
