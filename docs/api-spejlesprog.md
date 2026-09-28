# /api/ på fire sprog — tre spejlinger, én kilde

**Opgave 108, 2026-09-28.** `/api/` blev indekserbar i opgave 107. Denne
iteration målte, hvad der så skete med sproget — og svaret var: intet.

## Målingen først

191 indekserbare stier i det publicerede træ. **7** af dem fandtes på mere end
ét sprog (`/`, `/pricing/`, `/pro/`, `/book/`, `/scan/`, `/search/` …). Og 45
indekserbare sider — **alle med en købsknap** — fandtes kun på engelsk:
`/api/`, `/cli/`, `/plugin/`, `/store/*`, `/pro/vs-*`, `/vs/*`,
`/gdpr-fine-calculator/`, `/nis2-checklist/`.

Sprogvælgeren i headeren var ikke en fejl: `lang_switch()` i
`tools/apply_shell.py:319` skriver DA/DE/FR som `is-off`, fordi
`page_exists()` er sandt for `/da/api/` osv. Det er altså ikke en mangel i
skallen — det er en reelt fraværende overflade, der oveni ser ud som et valg.

`/api/` var det første valg, fordi det er den eneste side der sælger en
gratis tjeneste til udviklere: den har fire dokumenterede endepunkter, to
kodeeksempler og én købsknap til Pro, og den var den eneste af de 45.

## Hvorfor ikke tre håndskrevne sider

Opgave 106 målte otte `vs/*`-sider mod leverandørernes egne prissider: **syv af
otte var forkerte**, fordi de var skrevet i hånden og holdt i live. Tre
håndskrevne spejlinger af den bedste udviklerflade er tre billeder af den samme
løgn. Derfor er `site/api/index.html` den ene kilde, og spejlingerne er
genereret:

```
python3 tools/build_api_locales.py             # skriv spejlingerne + kør shellen
python3 tools/build_api_locales.py --check     # mål mod de committede filer
python3 tools/build_api_locales.py --list      # de sætninger der mangler en sætning
```

Kæden er: `render(locale)` tager originalens `<main>`, oversætter prosaen,
skriver `<title>` og meta-description, og **kører `apply_shell.process()` på
kun de tre nye filer** — så header, footer, breadcrumb, TOC, hreflang,
canonical, `og:locale` og JSON-LD skrives på det rigtige sprog af den ene
kilde, der allerede gør det for 226 andre sider. Sitemap og søgeindeks
genbygges i samme kørsel: 210 → **213** `<loc>`.

## Hvad der aldrig røres

`<pre>` (curl, Python, JSON), inline `<code>` (feltnavne, endepunkter,
HTTP-metoder) og de tal, der ikke er prosa. En tysk `curl`-kommando må ikke
blive tysk, og `score`/`passed`/`warn` skal kunne kopieres lige ud af siden.
`KEEP` i værktøjet er den eksplicitte liste over de identiske strenge — HTTP-
metoder, JSON-felter, endepunktstier, `CLI`, `Ctrl K` — så intet er beskyttet
ved en forglemt regel.

## Porten: to regler, to retninger

- **R1** (byte-identitet): `expected_files()` kopierer hele `site/` til en
  midlertidig mappe, skriver de tre filer fra `render()` og kører
  `apply_shell` på dem — og så sammenligner den filerne med de committede,
  tegn for tegn. Det er nødvendigt, fordi `apply_shell` selv afkorter
  meta-descriptionen ved en punktumgrænse og skriver `<style>`-blokken: en
  sammenligning af rå `render()`-output mod filerne ville være rød hele tiden,
  altså en port der ikke kan være grøn.
- **R2** (modsat retning): ingen engelsk sætning fra originalen må stå
  tilbage i en spejling. En nøgle hvis oversættelse er sig selv (`parameter`
  er også dansk) er ikke en mangel.

Selftesten muterer **repoets egne filer**, ikke fixtures: en uoversat sætning i
originalen, en håndskrevet rettelse i `site/da/api/index.html` (gendannet
bagefter), kodeeksemplerne skal stå tegn for tegn, og dækning i alle tre sprog.

## Baseline og hvad der kan måles

Plausible 28 d før denne iteration: **1 besøger**, bounce 100 %, kun Direct.
Det er ikke et målepunkt. Det målbare er indekserbare sprogindgange: **7 → 11**
spejlede stier (nu `/api/` ×3 mere), og tre nye `<loc>` i sitemap.xml.
Søgemaskinerne kan først tælle det; repoet har ingen Search Console-adgang.

Uden dette er `/da/api/` død kode: ingen indgang, ingen href fra EN-siden
ud over sprogvælgeren, intet i søgeindekset før denne kørsel.
