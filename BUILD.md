# BUILD: Transmute — Desktop data transformer

## Korteste vej til første betalende kunde

Først: **LS key skal komme** før betaling kan aktiveres. Indtil da bygger jeg produktet
færdigt, så det kun mangler licensflippen.

## Iteration 1: Kernemotor + CLI (uge 1)

### 1.1 Datamotor
En Node.js-pakke (`transmute-engine`) der understøtter:

**Input formater:**
- JSON (pretty, minified, lines-array)
- CSV (med header-detection, delimiter detection)
- YAML
- XML
- Plain text

**Output formater:**
- JSON
- CSV
- YAML
- XML
- Plain text
- Table (CLI pretty-print)

**Transformationer (pipe-chain):**
- `filter` — behold/afvis rækker (JS expression, fx `.age > 18`)
- `map` — transformér hver række (JS expression, fx `{...item, fullName: item.first + ' ' + item.last}`)
- `pick` — vælg kun specificerede felter
- `omit` — fjern specificerede felter
- `sort` — sorter efter felt (asc/desc)
- `unique` — fjern dubletter efter felt
- `group` — gruppér efter felt
- `count` — tæl rækker/grupper
- `head` / `tail` — første/sidste N rækker

**Pipeline definition:** JSON array af transformationer:
```json
[
  { "op": "filter", "expr": "item.status === 'active'" },
  { "op": "pick", "fields": ["name", "email", "status"] },
  { "op": "sort", "by": "name", "dir": "asc" },
  { "op": "head", "n": 10 }
]
```

### 1.2 CLI
`npx transmute` eller global npm-package:
```bash
# Fil til fil
transmute input.json --pipe '[{"op":"filter","expr":"item.age > 18"}]' --output filtered.csv

# Pipe
cat data.json | transmute --pipe '[{"op":"head","n":5}]' --format yaml

# Interactive preview
transmute input.csv
# → Viser de første 20 rækker som tabel + prompt til transformation
```

### Teknologi
- Node.js (engine, CLI)
- npm-package (gratis at publicere)
- Ingen eksterne afhængigheder (kun Node.js stdlib + JSON/CSV/YAML parsers)

## Iteration 2: Desktop app (Tauri)

- GUI med pipeline-bygger (drag-and-drop transformations)
- Live preview (data ændrer sig mens du bygger)
- Historik (tidligere transformationer)
- Import/export af pipelines
- Licenskey-validering (klar til LS integration)

## Iteration 3: Landingsside + betaling

- Produktside på auditedwp.pages.dev/transmute/
- LS checkout-link (når key er tilgængelig)
- GitHub Releases til downloads
- npm-package til CLI

## Prissætning

- **CLI**: Gratis (npm package, open-source core)
- **Desktop app**: $19 one-time (3 aktiveringer)
- **Pro features**: Desktop-only (pipeline-bygger, batch, historik)
