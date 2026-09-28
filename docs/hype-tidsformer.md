# HYPE-renseren skal bevare bøjningen

**28. september 2026.** To filer, én publiceret sætning, én ny port med to regler.

## Fundet

`tools/apply_shell.py` har en `HYPE`-tabel, der fjerner markedsføringsord fra
prosaen, når en side går gennem skallen. Den havde **én erstatning pr. verbum**,
uanset hvilken form ordet havde:

```python
(re.compile(r"\bUnlock(s|ed)?\b"), "Get"),     # gruppen bruges aldrig
(re.compile(r"\bSupercharge[sd]?\b"), "Speed up"),
(re.compile(r"\bElevate[sd]?\b"), "Improve"),
```

Mønsterne optager altså tre bøjninger, og erstatningen er skrevet til den
første. Resultatet er ikke en typfejl, det er en sætning, der kun er synlig for
den der læser den:

| Kilde | Efter renseren |
|---|---|
| `It unlocks the editable HTML document starters` | `It get the editable…` |
| `…the free plugin, which unlocks editable starters` | `…which get editable…` |
| `Supercharges your scans` | `Speed up your scans` |
| `Elevated conversion rates` | `Improve conversion rates` |

## Hvor meget var det i praksis

Planen fra iteration 108 sagde, at kun `/api/` var ramt, fordi de øvrige sider er
`native` og derfor skipper renseren (`native = "pg-legacy" not in html and
"data-dark-ok" in html[:400]`). Det er rigtigt for de sider, der er skrevet i den
nye skal, og **ikke** for de 170 legacy-sider, som stadig går gennem renseren.

Målt 28/9 på hele træet:

- **19 prosaforekomster** af `unlocks`/`Unlock` i publiceret HTML, i 13 sider.
- **3 sider ville få en brudt sætning**, hvis skallen kørte i dag: `/api/`,
  `/checklist/` og `/plugin/` — alle med `It get …` eller `which get …`.
- **1 sider har fejlen i dag**: `site/deskuptime/thanks/index.html:89` skrev
  *"Run this once — it get unlimited URLs"*. Den er rettet i samme diff.

Planens måling var altså rigtig for sit eget eksempel og for siden af interesse
på det tidspunkt, men den dækkede ikke træet. Det er derfor fundet nu ligger i
en port frem for i en note.

## Rettelsen

`hype_verb(base, by_suffix)` bygger mønsteret og erstatningen sammen, så
erstatningen slår ordets bøjning:

```python
hype_verb("unlock", {"": "get", "s": "gets", "ed": "got"})
hype_verb("supercharge", {"": "speed up", "s": "speeds up", "d": "sped up"})
hype_verb("elevate", {"": "improve", "s": "improves", "d": "improved"})
```

Erstatningen er et callable, ikke en streng, og `by_suffix` er nøglet af den
faktiske endelse. store bogstaver følger kilden, som før.

## Porten — `tools/check_hype_tenses.py`

**R1 læser den rigtige tabel.** Værktøjet importerer `HYPE` fra
`tools/apply_shell.py` gennem `importlib` — aldrig en kopi. En forældet kopi er
genfejlen her: opgave 72, 64 og 65 var alle en tabel der blev læst to steder.
Porten beder om heleformen for hvert nyt verbum, så `EXPECT` i porten er den
opsummering, tabellen skal opfylde — ikke en beskrivelse af den.

- Rød hvis en bøjning ikke overlever: `unlocks` → `get` i stedet for `gets`.
- Rød hvis et mønster dækker færre endelser end porten kræver (mønsteret kender
  kun `s`, porten kræver `s` og `ed`).
- Rød hvis tabellen har et bøjet ord porten ikke kender, så et nyt verbum
  ikke kan komme ind uden at blive dømt.

**R2 måler resultatet.** Alle 230 sider læses, `<script>/<style>/<pre>/<code>`
og tags fjernes, og en tredjeperson (it, that, which, this, Pro, these …) efter
grundformen af en HYPE-erstatning er rød. Undtagelsen er de verber der gør
grundformen korrekt: *"what data does it get"* er rigtig engelsk og blev fundet
ved målingen, så porten læser ordet foran subjektet og springer over, når det
er `does`, `to`, `can`, `how` …

**Selftest: 5 negative cases**, alle dømmer begge veje — flad tabel, ukendt
bøjning, manglende endelse, brudt sætning injiceret i en rigtig side, og den
korrekte sætning som *ikke* må give en find.

## Hvad der ikke blev rørt

- `<pre>`-blokke er **ikke** beskyttet mod renseren: `outside_code()` splitter
  kun på `<script>` og `<style>`. Målt 28/9: **0** HYPE-ord i et `<pre>` eller
  `<code>`-blok, så det er en landmine uden tændt snore. Samme måling fandt at
  emoji-renseren griber `/cli/`'s genererede eksempelblok — det er grund til at
  `apply_shell.py` ikke køres frit, men gennem `build_cli_example.py --check`
  (gate trin 585). Ikke rettet her; det er en egen opgave.
- Ingen plugin-version, ingen ny zip, ingen Stripe-pris, ingen worker, ingen
  publiceret overflade ud over den ene rettede sætning på
  `/deskuptime/thanks/`.
