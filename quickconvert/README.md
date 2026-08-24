# Quick Format

> **Convert between JSON, YAML, CSV, TOML, and XML — from your terminal, browser, or menu bar. Works offline. Your data never leaves your machine.**

```bash
# Once installed
cat data.json | qf --to yaml
echo '{"hello":"world"}' | qf --to csv
```

## Features

- **5 formats:** JSON, YAML, CSV, TOML, XML — all supported in both directions
- **Auto-detect:** Pipe in any format, it figures out what it is
- **Offline:** No network calls. Your secrets stay on your machine.
- **Fast:** Sub-millisecond conversion. No server, no latency.
- **CLI + library:** Use it in your terminal or `import { convert } from 'quick-format'`

## Install

```bash
npm install -g quick-format
```

Or run without installing:

```bash
npx quick-format --to yaml < input.json
```

## Usage

### CLI

```bash
# Basic conversion — auto-detect input format
cat data.json | qf --to yaml

# Specify input format explicitly
qf --from csv --to toml < data.csv

# Read from file instead of stdin
qf --to json < config.yaml > config.json

# Validate
qf --validate < data.json
# → Valid JSON ✓

# Format/prettify
qf --format < minified.json
```

### As a library

```js
import { detect, convert, format, validate } from 'quick-format'

const source = '{"hello": "world"}'
const result = await convert(source, { from: 'json', to: 'yaml' })
// → "hello: world\n"
```

### Supported conversions

| From \\ To | JSON | YAML | CSV | TOML | XML |
|-----------|------|------|-----|------|-----|
| JSON | ✓ | ✓ | ✓ | ✓ | ✓ |
| YAML | ✓ | ✓ | ✓ | ✓ | ✓ |
| CSV | ✓ | ✓ | ✓ | ✓ | ✓ |
| TOML | ✓ | ✓ | ✓ | ✓ | ✓ |
| XML | ✓ | ✓ | ✓ | ✓ | ✓ |

All 25 combinations work out of the box.

## Desktop App (macOS)

Prefer a visual interface? **QuickFormat for Mac** lives in your menu bar:

- **Global shortcut** — select any text, press a key, get converted output
- **Drag & drop** — drop a file on the menu bar icon
- **Auto-paste** — result is automatically pasted where you need it
- **No browser needed** — always one click away

**[Buy QuickFormat for Mac — $9 one-time](https://auditedwp.pages.dev/quickconvert/)**

The CLI is free and open source. The desktop app is a one-time $9 purchase that supports development.

## Who is this for?

- **Developers** converting config files between YAML and JSON
- **Data analysts** transforming CSV exports to JSON for APIs
- **DevOps engineers** switching between TOML and YAML configs
- **API users** formatting JSON responses for readability
- **Anyone** who regularly works with structured data formats

## Why not use a web tool?

| | QuickFormat CLI | Web tools |
|---|---|---|
| Works offline | ✅ Yes | ❌ No |
| Data privacy | ✅ Stays on your machine | ❌ Uploaded to server |
| Speed | ✅ Sub-ms | ❌ Network latency |
| Scriptable | ✅ Pipe-friendly | ❌ Manual copy-paste |
| No ads | ✅ Clean | ❌ Ads and trackers |
| No rate limits | ✅ Unlimited | ❌ Often capped |

## License

MIT © QuickFormat

---

*CLI is free. [Desktop app is $9 one-time.](https://auditedwp.pages.dev/quickconvert/)*