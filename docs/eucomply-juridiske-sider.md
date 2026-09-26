# Spec: den betalte `legal` skal kunne læse dansk, svensk og nederlandsk

Opgave 53, del 1. Skrevet 2026-09-26.

## Problemet, målt

`check_legal_pages()` i `plugin/eucomply.php` slår WordPress-sider op. Det den
slår op, var:

| Hvad | Sådan |
|---|---|
| Sti | `imprint`, `impressum` |
| Titel | `LIKE '%Imprint%'`, `LIKE '%Impressum%'` |
| Sti | `accessibility-statement`, `accessibility` |
| Titel | `LIKE '%Accessibility%'` |

Altså **kun engelsk og tysk**. Målingen før rettelsen, kørt gennem den rigtige
plugin med `tools/plugin_probe.php`:

```
dansk butik, siderne "Om os", "Handelsbetingelser" og "Privatlivspolitik"
  → "3 of 3 legal pages missing"
samme butik på engelsk
  → "Privacy, imprint and accessibility pages found"
```

Det er en **fejl i den betalte vare**: rapporten er det dokument et bureau sender
til sin kunde, og den siger til en dansk kunde, at kunden mangler tre sider,
kunden har lagt op. Samme fejlklasse som opgave 50 (den betalte `forms` svarede
svagere end den gratis scanner) og opgave 52 (`legal` som en score afhængig af
sprog) — her fejler det, fordi siden er skrevet på dansk.

Det er **ikke** det samme problem som de otte `LEGAL_PATTERNS` i de to
JS-motorer. Pluginen læser ikke markup'en; den læser WordPress' egen
sideoversigt. To fejl, to produkter, to målemetoder.

## Rettelsen

### 1. Stier

`imprint_paths` udvider de to engelske/tyske med de sideformer butikkerne bruger:

- DA: `om-os`, `om-oss`, `forretningsoplysninger`, `kontaktoplysninger`
- SV: `foretagsoplysningar`, `foretagsinformation`, `foretagsuppgifter`
- NL: `over-ons`, `colofon`, `bedrijfsgegevens`

`eaa_paths` får `tilgaengelighedserklaering`, `tillganglighetsredogorelse`,
`toegankelijkheidsverklaring` plus de to tyske.

### 2. Titler — **eksakt lighed, ikke LIKE**

Den nye `find_page_by_title()` slår op med `post_title = %s` og stopper ved det
første fund:

```sql
SELECT ID FROM wp_posts
WHERE post_title = %s AND post_type = 'page' AND post_status = 'publish'
LIMIT 1
```

Det er bevidst, og det er den del der er let at gøre forkert. Det danske
imprint-side hedder **"Om os"**. Et `LIKE '%Om os%'` ville også tælle siden
**"Om os i pressen"** — en pressoside — som den imprint rapporten fortælder
kunden at de har. Lighedstegnet er derfor `=`.

De ældre engelske og tyske `LIKE`-opslag er **bevaret uændret**, fordi
"Imprint" og "Impressum" optræder i længere titler ("Imprint / Impressum"), og
den løsning var rigtig, da den blev skrevet. `find_page_by_title()` køres
*før* dem, så den præcise søgning altid vinder.

### 3. Hvad der bevidst ikke er lavet

- **Ikke oversættelse af advarslerne.** `warnings[]` siger "Required in DE, AT,
  CH under Telemediengesetz (TMG)". Det er sandt for en dansk kunde, men
  opgaven her var at finde siderne, ikke at omskrive love. Det er en reel
  mangel, se nedenfor.
- **Ikke nye dokumenttyper.** Tjekket skal finde de tre, det efter spørger til.
- **Ikke ændret i de to JS-motorer.** Det er del 2, målt i
  `docs/eucomply-privatlivsprog.md`.

## Målemetoden: porten trin 22

`tools/check_legal_pages_langs.php` — samme butik, tre dokumenter, fire sprog.
Fem regler:

| Regel | Hvad den fanger |
|---|---|
| R1 | En DA/SV/NL-butik med alle tre dokumenter må ikke blive fortalt at de mangler. |
| R2 | De fire sprog skal give **samme dom**. |
| R3 | Hver af de to opslagsveje (WordPress-sti, sidetitel) skal finde siden **alene**. |
| R4 | En butik uden nogen af dem skal stadig fejle. |
| R5 | "Om os i pressen" må ikke tælles som imprint. |

R3 er der, fordi ellers er R1 opfyldt af den anden vej: en mutation der fjerner
stierne er usynlig, når titlerne stadig virker. Derfor har hver fixture en
`via`-værdi — `paths`, `titles`, `both` — der isolerer én opslagsvej.

Selftesten muterer **repoets egen pluginfil** fire gange, kørt gennem den samme
probe med `EUCOMPLY_PLUGIN_FILE` peget på en kopi:

| Mutation | Forventer |
|---|---|
| M1 — de nye sidespor forsvinder | `paths`-fixture bliver rød |
| M2 — titel-opslaget bliver `LIKE '%Om os%'` | R5 bliver grøn af mutationen |
| M3 — `find_page_by_title()` løkken køres ikke | `titles`-fixture bliver rød |
| M4 — de nye sprognavn forsvinder | `titles`-fixture bliver rød |

## To fejl fundet i min egen måle

Begge lå i **porten og proben**, ikke i pluginen, og begge blev fundet fordi
selftesten får lov til at fejle.

1. **`prepare()` gemte operatoren.** `$wpdb->prepare()` returnerede
   `'PREPARED(Om os)'`, så `get_var()` ikke kunne se om SQL'en var `=` eller
   `LIKE` — den skulle gætte, og gætningen var *altid* `=`. Følgen: de ældre
   `LIKE '%Imprint%'`-opslag holdt op at finde *Imprint*, og den engelske
   `titles`-fixture blev rød **uden at nogen fejl var indført**. Rettelsen er,
   at `prepare()` lægger operatoren i den streng den returnerer. Samme
   familie som opgave 30/32/41 fund 1: en stub der læser en mindre mængde end
   den, den skal dække.
2. **`0 !== strpos( $needle, '%' )` er altid sandt.** En streng uden
   procenttegn returnerer `false` fra `strpos`, og `0 !== false` er sandt, så
   min første operator-afledning læste *alle* lighedskrav som `LIKE`. Fundet af
   M2, som forventede en mutation der gør R5 grøn, og som forblev rød.

## Hvad der er blocking

- Advarselsteksten nævner kun tysk lov. Det er ikke en fejl, men det er heller
  ikke ærligt for en dansk kunde, der får den i mailen. Se `❓ Til Mads`.
- De otte øvrige `LEGAL_PATTERNS` i `shared/scan-engine.js` og
  `eucomply-scanner/engine/index.js` er del 2 af opgave 53.
