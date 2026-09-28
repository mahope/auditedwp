# Skalen skal lade kodeblokke være i fred

**28. september 2026.** Én fælles hjælpefunktion, én publiceret sandhed, én ny
port med tre regler.

## Fundet

`tools/apply_shell.py` har `outside_code(html, fn)`, som anvender en renser på
den del af en side der **ikke** er kode:

```python
re.split(r"(<(?:script|style)\b[^>]*>.*?</(?:script|style)>)", html, ...)
```

`<pre>` og `<code>` stod ikke i listen. Renserne — emoji, HYPE-ord,
social-proof, venteliste-formularer, købsknap-neutralisering, generator-links og
CTA-indsats — måtte altså skrive i en kodeblok.

Planen fra i går målte dette som **"en landmine uden tændt snore"**, fordi der var
0 HYPE-ord i en kodeblok. Det var en måling af ét mønster, ikke af kæden, og det
er samme forveksling som iteration 109 gjorde med `/api/`: ét eksempel blev
taget for en måling af træet.

Kæden kørt på hele træet — **230 sider, 1081 kodeblokke** — ændrede **én**:

```
site/cli/index.html
$ eucomply-scanner https://webflow.com

🔍 EUComply Scan Report for https://webflow.com
```

Det er **emoji-renseren**, ikke HYPE-tabellen. Og det er den værste slags fejl,
fordi blokken ikke er håndskrevet: `/cli/`s eksempel er genereret fra den
rigtige scanner-output (`tools/capture_cli_fixture.py`), så `🔍` er en egenskab
ved `eucomply-scanner`. Renseren ville have fjernet den, og siden ville have
vist et eksempel på et værktøj, der ikke findes.

Det er samme fejlklasse som `check_dom_xss.py` så i quick-check-widgeten: en
rens der kører på markup, den ikke forstår, og resultatet er ikke en skrivefejl
men en **dokumenteret sandhed der bliver til en pænere løgn**.

## Rettelsen

`<pre>` og `<code>` er nu beskyttet i `outside_code()`. Det er den ene linje, der
løser det hele, fordi alle syv rensere går gennem samme hjælpefunktion.

Navnet passede aldrig helt; nu gør det.

De øvrige fire kald (`wrap_tables`, `add_missing_alt`, `lazy_images`,
`aria_live_results`) rører heller ikke kode, hvilket er rigtigt: en `<table>`
eller et `<img>` inde i en `<pre>` er escaped tekst, ikke markup. Attribut-rens
er ikke berørt, fordi attributterne ligger på taggen og ikke i indholdet.

## Porten: `tools/check_code_blocks.py`

| Regel | Hvad den dømmer |
|---|---|
| **R1** | Hver `<pre>`/`<code>`-blok i alle 230 sider skal komme tilbage **byte for byte**, når den rigtige `process()` kører på siden. Porten kalder skalen selv på en midlertidig kopi, så den måler den kæde der faktisk kører. |
| **R2** | Med den gamle script/style-only `outside_code` genskabt skal R1 finde **præcis den blok**, der lå i træet. Uden R2 er R1 vacuously sand: 1081 blokke, nul fejl, intet udsagn om hvorfor. |
| **R3** | Inline `<code>` i løbende tekst måles hver for sig, fordi en helsides-kørling ellers ville slå den ud i mellem en `<p>` og sit `<code>`. |

Selftesten har **6 negative cases**, og to af dem er mutationer mod repoets egne
filer — ikke fixtures. Den vigtigste af de to dømmer **begge retninger** for det
samme indhold:

- HYPE-ord indeni en kodeblok i `/cli/` **med** beskyttelsen væk → fund.
- Det **samme** indhold med beskyttelsen på → intet fund.

Uden den anden ville den første bare bevise, at porten kan tælle.

## Målt

| | Før | Efter |
|---|---|---|
| Sider læst | 230 | 230 |
| Kodeblokke læst | 1081 | 1081 |
| Blokke ændret af skallen | **1** | 0 |
| Negative cases | — | 6 af 6 |

## Hvad der ikke er gjort

`/cli/` er **ikke** kørt gennem skallen i denne iteration. Det er den næste
kandidat, og det er nu sikkert: porten måler præcis den egenskab, først skal den
have. Men det er en anden opgave, og en side ad gangen er den regel, der har
holdt i 110 iterationer.
