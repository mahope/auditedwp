/**
 * QuickFormat — Universal Format Conversion Engine
 *
 * Platform-independent core: takes text input, detects format,
 * converts between JSON, YAML, CSV, TOML, and XML.
 *
 * Can be wrapped as:
 *   - CLI (bin/quick-format.js)
 *   - Web tool (site/tools/format/index.html)
 *   - Desktop app (Tauri wrapper)
 *   - VS Code extension
 *   - API endpoint
 *
 * Usage:
 *   import { detect, convert, format, validate } from './src/engine.js'
 */

import * as jsyaml from 'js-yaml'
import * as tomlLib from 'toml'
import { parse as csvParse } from 'csv-parse/sync'
import { stringify as csvStringify } from 'csv-stringify/sync'
import { XMLParser, XMLBuilder } from 'fast-xml-parser'

// --- Format detection ---

const FORMAT_PATTERNS = {
  json: [
    { test: (s) => /^\s*[{[]/.test(s) && /[}\]]\s*$/.test(s), weight: 10 },
    { test: (s) => /^\s*"[\w_]+"\s*:/.test(s), weight: 5 },
  ],
  yaml: [
    { test: (s) => /^\s*[\w_-]+:\s+.+/m.test(s) && !/^\s*[{[]/.test(s), weight: 8 },
    { test: (s) => /^\s*---\s*$/.test(s.split('\n')[0]), weight: 15 },
    { test: (s) => /: \|2?$|: >-?$|^  - /.test(s), weight: 5 },
  ],
  toml: [
    { test: (s) => /^\s*\[[\w.]+\]\s*$/.test(s.split('\n')[0]?.trim()), weight: 12 },
    { test: (s) => /^\s*[\w_-]+\s*=\s*["']/.test(s), weight: 5 },
    { test: (s) => /=\s*(true|false|\d+\.?\d*)\s*$/.test(s.split('\n')[0]), weight: 3 },
  ],
  csv: [
    { test: (s) => s.includes(',') && /^[\w\s-]+(,[\w\s-]+)*$/.test(s.trim().split('\n')[0]), weight: 6 },
    { test: (s) => /^[\w\s]+,[\w\s]+/.test(s.trim()) && s.split('\n').length > 1, weight: 4 },
  ],
  xml: [
    { test: (s) => /^\s*<[\w?]/.test(s.trim()), weight: 12 },
    { test: (s) => /<[\w-]+>.*<\/[\w-]+>/.test(s), weight: 6 },
    { test: (s) => /<\?xml\s/.test(s), weight: 15 },
  ],
}

/**
 * Detect the format of input text.
 * @param {string} text - Raw input
 * @returns {string|null} - 'json', 'yaml', 'csv', 'toml', 'xml', or null
 */
export function detect(text) {
  if (!text || typeof text !== 'string') return null
  const trimmed = text.trim()
  if (!trimmed) return null

  let scores = {}
  for (const [fmt, patterns] of Object.entries(FORMAT_PATTERNS)) {
    scores[fmt] = patterns.reduce((sum, p) => sum + (p.test(trimmed) ? p.weight : 0), 0)
  }

  // Try parse as tiebreaker
  for (const fmt of ['json', 'yaml', 'toml', 'xml', 'csv']) {
    try {
      parseInput(trimmed, fmt)
      scores[fmt] += 20 // bonus for successful parse
    } catch {}
  }

  const best = Object.entries(scores).sort((a, b) => b[1] - a[1])[0]
  return best && best[1] > 0 ? best[0] : null
}

/**
 * Detect format quickly (no full parse). Use for UI hinting.
 */
export function detectQuick(text) {
  if (!text || typeof text !== 'string') return null
  const trimmed = text.trim()
  if (!trimmed) return null

  if (/^\s*[{[]/.test(trimmed) && /[}\]]\s*$/.test(trimmed)) return 'json'
  if (/^\s*[\w_-]+:\s+.+/m.test(trimmed) && !/^\s*[{[]/.test(trimmed)) return 'yaml'
  if (/^\s*\[[\w.]+\]\s*$/.test(trimmed.split('\n')[0]?.trim())) return 'toml'
  if (/^\s*</.test(trimmed)) return 'xml'
  if (trimmed.includes(',') && /^[\w\s-]+(,[\w\s-]+)*$/.test(trimmed.split('\n')[0])) return 'csv'

  return null
}

// --- Parsing ---

function parseInput(text, format) {
  switch (format) {
    case 'json': return JSON.parse(text)
    case 'yaml': return jsyaml.load(text)
    case 'toml': return tomlLib.parse(text)
    case 'xml': {
      const parser = new XMLParser({ ignoreAttributes: false, attributeNamePrefix: '@_' })
      return parser.parse(text)
    }
    case 'csv': {
      const records = csvParse(text, { columns: true, skip_empty_lines: true, trim: true })
      return records
    }
    default: throw new Error(`Unsupported format: ${format}`)
  }
}

function stringifyOutput(data, format, pretty = true) {
  switch (format) {
    case 'json': return pretty ? JSON.stringify(data, null, 2) : JSON.stringify(data)
    case 'yaml': return jsyaml.dump(data, { indent: 2, lineWidth: -1, noRefs: true, sortKeys: false })
    case 'toml': return tomlify(data)
    case 'xml': {
      const builder = new XMLBuilder({ format: pretty, ignoreAttributes: false, attributeNamePrefix: '@_', suppressEmptyNode: true })
      return builder.build({ root: data })
    }
    case 'csv': {
      if (!Array.isArray(data)) data = [data]
      return csvStringify(data, { header: true })
    }
    default: throw new Error(`Unsupported format: ${format}`)
  }
}

// Simple TOML stringifier (enough for common cases)
function tomlify(obj, prefix = '') {
  let result = ''
  for (const [key, value] of Object.entries(obj)) {
    if (value === null || value === undefined) continue
    const fullKey = prefix ? `${prefix}.${key}` : key
    if (Array.isArray(value)) {
      if (value.length > 0 && typeof value[0] === 'object') {
        value.forEach(item => {
          result += `[[${fullKey}]]\n`
          result += tomlify(item, fullKey)
        })
      } else {
        result += `${key} = [${value.map(v => formatTomlValue(v)).join(', ')}]\n`
      }
    } else if (typeof value === 'object') {
      result += `[${fullKey}]\n`
      result += tomlify(value, fullKey)
    } else {
      result += `${key} = ${formatTomlValue(value)}\n`
    }
  }
  return result
}

function formatTomlValue(v) {
  if (typeof v === 'string') return `"${v.replace(/"/g, '\\"')}"`
  if (typeof v === 'boolean') return v ? 'true' : 'false'
  if (v instanceof Date) return v.toISOString()
  return String(v)
}

// --- Core operations ---

/**
 * Convert from one format to another.
 * @param {string} input - Raw input text
 * @param {string} from - Source format ('auto' | 'json' | 'yaml' | 'csv' | 'toml' | 'xml')
 * @param {string} to - Target format
 * @param {object} [options] - { pretty: true }
 * @returns {{ success: boolean, data?: string, error?: string, detected?: string
 */
export function convert(input, from, to, options = {}) {
  try {
    const pretty = options.pretty !== false
    const sourceFormat = from === 'auto' ? detect(input) : from
    if (!sourceFormat) throw new Error(`Could not detect source format`)

    const data = parseInput(input.trim(), sourceFormat)
    const output = stringifyOutput(data, to, pretty)

    return { success: true, data: output, detected: sourceFormat !== from ? sourceFormat : undefined }
  } catch (e) {
    return { success: false, error: e.message }
  }
}

/**
 * Validate format correctness.
 * @param {string} input - Raw input
 * @param {string} format - Format to validate against
 * @returns {{ valid: boolean, error?: string }}
 */
export function validate(input, format) {
  try {
    parseInput(input.trim(), format)
    return { valid: true }
  } catch (e) {
    return { valid: false, error: e.message }
  }
}

/**
 * Format (pretty-print or minify) text in its own format.
 * @param {string} input - Raw input
 * @param {string} format - Format
 * @param {boolean} pretty - true for pretty, false for minified
 * @returns { success: boolean, data?: string, error?: string }}
 */
export function formatText(input, format, pretty = true) {
  return convert(input, format, format, { pretty })
}

export default { detect, detectQuick, convert, validate, format: formatText }