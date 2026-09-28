# Én renderer i hele npm-pakken (28. september 2026)

Fortsættelse af `docs/eucomply-cli-egen-renderering.md`. Den målte `bin` mod
motorens `main()`. Denne måler **resten af den publicerede kode** — de to
eksempler og README'en.

## Fundet

Efter at `bin` var rettet, lå der **to gengivelser mere af samme rapport** i
pakken. Begge var håndskrevne, og ingen af dem var synlig, fordi der ikke var
noget at sammenligne med:

| fil | hvad den påstod | målt |
|-----|-----------------|------|
| `examples/sample-output.txt` | `Score: 2/9 (22%)` for **wordpress.org**, **seks af ni** rækker, 0 `💡`-råd, ingen betingede rækker | aldrig nogen kørsel af motorens output |
| `examples/node.js` | **tredje renderer**: `Score: n/m (p %)` + ét dom pr. række uden `detail`, uden `fix`, uden disclaimér | et fjerde sprog i samme pakke |
| `README.md` "Example output" | `Score: 5/8 (62%)` for example.com, fem domme, kun én rigtig | **et tal motoren aldrig printer** — hverken ni-tallet (3/9) eller det delte (3/6) |

README'en havde også to **dokumentationsfejl i samme klasse**:

- `score` var dokumenteret som `{ passed, total, pct }` — altså kun det
  forudindtagede ni-tal. `pct_applicable`, `applicable_total`,
  `passed_applicable` og `conditional` findes i objektet, men var ikke nævnt,
  så en læser der ville vise en kunde et tal, ville bruge det forudindtagede.
- `renderReport()` var ikke dokumenteret, selv om `examples/node.js` er den
  fil der skal kalde den.
- `--timeout` virkede, men stod ikke i README's CLI-usage.

## Rettelsen

1. **`examples/node.js`** kalder `renderReport(report)` — samme funktion som
   `bin` og `main()`. Den har ingen egen formatting tilbage.
2. **`examples/sample-output.txt`** er **genereret**: `bin`'s egen stdout mod
   `tools/fixtures/webflow.com.json`. Den er derfor 47 linjer med ni domme, tre
   `- not counted:`-linjer og seks `💡`-råd, byte-identisk med det en bruger
   får. Skrives med `node tools/cli_render_parity.mjs --write`.
3. **README** har et uddrag, hvor **hver linje findes ordret** i
   `sample-output.txt`, og en pointer til filen for resten. Den klistrer ikke
   hele rapporten ind igen — det ville være en fjerde kopi af den samme tekst.
   `score`-tabellen dokumenterer begge tal med en forklaring på, hvornår man
   bruger hvilket. `renderReport()` får sit eget afsnit, og `--timeout` står i
   CLI-usage.

Versionen er hævet til **1.1.0** i `package.json` og i CLI'ens hjælpetekst, så
den publicerede pakke kan få det samme nummer, når Mads frigiver den. Vi må
ikke publisere selv.

## Porten — otte regler i `tools/cli_render_parity.mjs` (trin 32)

R1–R4 er uændrede (se `docs/eucomply-cli-egen-renderering.md`). De nye:

- **R5** — `examples/sample-output.txt` skal være `bin`'s egen stdout mod
  fixture'en, byte-identisk undtagen `Duration: <heltal>ms`. Fanger den
  håndskrevne wordpress.org-fil.
- **R6** — hver linje i README'ens "Example output"-blok skal findes ordret i
  `sample-output.txt` (varigheden normaliseret), og blokken skal have mindst
  ét `Score:`-tal og mindst **fem** domme. Fanger både det opdigtede `5/8
  (62%)` og en blok der bliver slanket til ingenting.
- **R7** — README skal dokumentere `pct_applicable`, `applicable_total`,
  `passed_applicable` og `conditional`. Fanger dokumentationen der kun peger på
  ni-tallet.
- **R8** — README skal dokumentere `renderReport(`.

**R2 og R3 er udvidet fra to filer til alle `.js`-filer under `cli/`, `engine/`
og `examples/`.** Det er den udvidelse, der gør fundene permanente: en tredje
renderer i `examples/` fanges nu af præcis den regel, der fangede `bin`'s. En
fjerde renderer et andet sted i pakken fanges også.

### Én målt undtagelse i R2

R2 måler **kode**, ikke kommentarer: en docstring må gerne nævne
`report.score.pct` for at forklare hvilket tal en læser skal bruge, og det gør
`examples/node.js`. Uden den skelnen ville porten være rød på den kode, der
forklarer reglen. Dom-ikonerne er fortsat målt undtaget for `❌`, fordi den
står i `bin`s egen `console.error('❌ Error:')`.

### Selftesten

12 negative cases (6 før), alle fanget — heraf fire der er dagens fund:
`examples/node.js` med sin egen rendering, den håndskrevne `sample-output.txt`,
README med `5/8 (62%)`, og README der kun dokumenterer ni-tallet. Den grønne
case er repoets egen pakke, så porten er grøn af design og ikke rød af en fejl
den ikke kan se.

## Hvad der *ikke* ændres

- Motorens domme, betingelser, signaturtabeller og SSRF-guard røres ikke.
- `bin`'s adfærd er uændret; kun hjælpetekstens versionslinje følger
  `package.json`.
- `shared/scan-engine.js` (worker-kopien) røres ikke. Den har ingen CLI og ingen
  eksempler, så den har ingen anden renderer at glide fra.
- Ingen `site/**`-fil røres, så intet publiceres af denne diff.

## Det vi ikke kan rette herfra

npm-pakken `@mahope/eucomply-scanner@1.0.1` er publiceret fra den gamle kode og
kan ikke rettes af os (vi må ikke publisere). `tools/check_published_engine.mjs`
**måler** derfor den publicerede kode og **rapporterer** afvigelser, præcis som
det gør med SSRF-guarden: en afvigelse vi ikke må rette er en rapport og ikke
et fund, ellers låser porten hvert merge og dermed hele sitets deploy. Indtil
Mads publicerer 1.1.0 har `npx`-brugere den svagere rapport.
