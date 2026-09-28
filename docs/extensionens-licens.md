# Extensionens licens: en påstand skal have en tekst bag sig

Målt 28/9, rettet i iteration 105. Grund: `/extension/` lovede en licens i
ren tekst, og den pakke læseren rent faktisk henter, indeholdt ingen.

## Fundet

Sådan lå det, målt og ikke læst:

| hvor | påstand | målt |
|---|---|---|
| `/extension/`, kortet "No tracking" | "Open source." | 0 licenstekster i pakken |
| `chrome-ext/` | — | ingen `LICENSE` |
| `site/assets/eucomply-extension-1.0.2.zip` | — | 9 medlemmer, **ingen** af dem `LICENSE` |
| repoet `mahope/auditedwp` | offentligt | `licenseInfo: null` — ingen root-LICENSE |

"Open source" er ikke en beskrivelse af en fil, det er en vilkårsklasse: den
forbinder en hensigt om at give rettigheder. Uden `LICENSE` i pakken har den
person, der unzipper zip'en, ingen rettigheder at gøre brug af — kun en
forsamling filer uden vilkår. Det er den eneste mangel i køen der er ren
juridisk risiko, alt andet er kosmetik.

Footeren på 203 sider siger "Scanner and CLI are MIT licensed." Den påstand
er sand: `eucomply-scanner/LICENSE` og `cli/LICENSE` findes, og begge er
byte-gode MIT-tekster. De blev ikke rørt, for de er korrekte. Det var kun
extensionen, der lå uden.

## Rettelsen

**1. `chrome-ext/LICENSE`** er byte-identisk med `eucomply-scanner/LICENSE`
(sha256 `306bcab8db4f…`), så der er én licenstekst i huset, ikke tre
variationer. Den ligger i kilden **og** i zip'en, fordi zip'en er den fil
læseren henter.

**2. `/extension/` siger "MIT licensed", ikke "open source".** Licensens navn
er en kendsgerning, læseren kan slå op. "Open source" er en hensigtserklæring,
og den er ikke efterprøvbar. Sætningen siger desuden, hvor teksten er, så
læseren ikke skal lede.

**3. Extensionen er 1.0.3.** Ikke fordi adfærden ændrede sig — den gør ikke —
men fordi pakken ændrer indhold, og en pakke med et uændret versionsnummer er
den måde, en læser pådrager sig to forskellige ting med samme navn. 1.0.2 →
1.0.3 er en ren filudgivelse.

**4. `tools/build_extension_zip.py` gør pakken reproducerbar.** Den var
genbygget i hånden to gange (1.0.1 → 1.0.2 var den anden), og en zip ingen kan
bygge igen er en zip der driver lydløst. Medlemmerne er sorteret, tidsstemplet
er fast (1980-01-01), og versionen fra `manifest.json` er filnavnet — så
arkivet, download-linket og manifestet ikke kan komme i strid. To builds af
samme kilde giver samme sha256, hvilket er målt:

```
a3a94d9fa120ef32542e70dd10f8e297fc739ebf319f73e1f1e197fa360a5a8e  eucomply-extension-1.0.3.zip  (×2)
```

Scriptet nægter desuden at bygge en pakke uden `LICENSE`, så den mangel ikke
kan genindføres ved at køre det.

## Porten: R11 og trin 34

`tools/check_store_ready.py` fik **R11**, som dømmer de tre sider af samme
mangel hver for sig, fordi de kan fejle uafhængigt:

1. `chrome-ext/LICENSE` skal findes **og** indeholde
   `Permission is hereby granted` — en fil med navnet LICENSE, der ikke er en
   licenstekst, er stadig en mangel.
2. Den publicerede zip skal indeholde `LICENSE` **og** en licenstekst. Det er
   den fil læseren henter, så det er den, der skal give rettighederne.
3. Sidens licenspåstand skal **navngive** en licens. Ordene "open source",
   "open-source", "opensource", "free software" og "source available" uden et
   navn blandt MIT/Apache/BSD/GPL/MPL/Unlicense er røde.

Selftesten gik fra **18** til **22** negative cases. De fire nye er dagens
fund: ingen LICENSE i kilden, ingen LICENSE i zip'en, en LICENSE der ikke er
en licenstekst, og en side der siger "Open source" uden at nævne hvilken
licens.

Trin 34 i gaten kører `build_extension_zip.py --check` og `--selftest`.
`--check` fejler på den gamle 1.0.2-pakke, hvilket er acceptkriteriet: porten
skulle kunne se den mangel, før den var rettet.

## Hvad der bevidst ikke blev rørt

- **Footeren på 203 sider.** "Scanner and CLI are MIT licensed" er sandt for
  scanneren og CLI'en, og begge har licenstekster. At skrive "Scanner, CLI and
  extension" på alle 203 ville være 203 filer i en diff om én licensfil.
- **Root-LICENSE i repoet.** `mahope/auditedwp` er offentligt uden
  licenstekst i roden, og det er en reel mangel — men en root-LICENSE ville
  dække *alt* i træet, inklusive `deliverables/` og `gumroad/`, hvor der ligger
  betalt indhold der skal flyttes til et privat repo. Det er Mads' beslutning,
  ikke en konsekvens af denne opgave. Skrevet i planen under `❓ Til Mads`.
- **Chrome Web Store.** Ikke udgivet, ingen upload, ingen publicering. Alle
  EUComply-jobs er fastsat på `ubuntu-24.04` og der må vi ikke røre releases.
