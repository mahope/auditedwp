#!/usr/bin/env node
/**
 * quick-format — CLI for QuickFormat conversion engine
 *
 * Usage:
 *   echo '{"name":"test"}' | qf --to yaml
 *   qf --from json --to yaml < input.json
 *   qf --detect < unknown.txt
 *   qf --validate --from json < data.json
 *
 * Install: npm install -g quick-format
 * Run:     npx quick-format --help
 */

import { detect, convert, validate, formatText } from '../src/engine.js'

function help() {
  console.log(`
QuickFormat v1.0.0 — Universal format converter

USAGE:
  qf [options] < input

OPTIONS:
  --from <format>    Source format (default: auto-detect)
                     json | yaml | csv | toml | xml
  --to <format>      Target format (required for convert)
  --detect           Only detect the format, don't convert
  --validate         Validate format correctness
  --minify           Minify output (no pretty-printing)
  --help             Show this help

EXAMPLES:
  echo '{"a":1}' | qf --to yaml
  cat data.csv | qf --from csv --to json
  qf --detect < unknown.txt
`)
}

const args = process.argv.slice(2)
if (args.includes('--help')) { help(); process.exit(0) }

const fromIdx = args.indexOf('--from')
const toIdx = args.indexOf('--to')
const from = fromIdx >= 0 ? args[fromIdx + 1] : 'auto'
const to = toIdx >= 0 ? args[toIdx + 1] : null
const doDetect = args.includes('--detect')
const doValidate = args.includes('--validate')
const minify = args.includes('--minify')

let input = ''
process.stdin.on('data', chunk => input += chunk)
process.stdin.on('end', () => {
  input = input.trim()
  if (!input) { console.error('Error: No input provided'); process.exit(1) }

  if (doDetect) {
    const result = detect(input)
    console.log(result || 'unknown')
    process.exit(result ? 0 : 1)
  }

  if (doValidate) {
    const format = from === 'auto' ? detect(input) : from
    if (!format) { console.error('Error: Could not detect format'); process.exit(1) }
    const r = validate(input, format)
    if (r.valid) { console.log('✅ Valid'); process.exit(0) }
    else { console.error('❌ Invalid:', r.error); process.exit(1) }
  }

  if (!to) { console.error('Error: --to <format> is required (or use --detect/--validate)'); process.exit(1) }

  const r = convert(input, from, to, { pretty: !minify })
  if (r.success) {
    console.log(r.data)
    if (r.detected) console.error(`(detected: ${r.detected})`)
    process.exit(0)
  } else {
    console.error('❌ Error:', r.error)
    process.exit(1)
  }
})