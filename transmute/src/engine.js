#!/usr/bin/env node

/**
 * Transmute Engine — core data transformation pipeline
 *
 * Input → [Parse] → [Filter → Map → Pick → Sort → Unique → ...] → [Serialize] → Output
 *
 * All operations are pure functions that operate on arrays of objects.
 * The pipeline is a JSON array of operation descriptors.
 */

// ─── Format parsers / serializers ────────────────────────────────────────

const parsers = {
  json: (text) => {
    const data = JSON.parse(text);
    return Array.isArray(data) ? data : [data];
  },
  csv: (text) => {
    const lines = text.trim().split('\n');
    if (lines.length === 0) return [];
    const headers = parseCSVLine(lines[0]);
    const rows = [];
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      const values = parseCSVLine(line);
      const row = {};
      headers.forEach((h, idx) => { row[h] = idx < values.length ? values[idx] : ''; });
      rows.push(row);
    }
    return rows;
  },
  yaml: (text) => {
    // Simple YAML parser for basic structures (arrays of scalars/objects)
    const lines = text.split('\n');
    if (lines.length === 0) return [];
    
    // Try JSON.parse first (YAML is superset of JSON)
    try { return parsers.json(text); } catch {}
    
    // Detect if it's a YAML list
    const result = [];
    let current = null;
    let isList = false;
    
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      
      if (trimmed.startsWith('- ')) {
        isList = true;
        const val = trimmed.slice(2).trim();
        // Check if it's a key: value pair
        if (val.includes(': ')) {
          if (current) result.push(current);
          current = {};
          const [k, ...v] = val.split(': ');
          current[k.trim()] = v.join(': ').trim();
        } else {
          current = null;
          result.push(parseYAMLValue(val));
        }
      } else if (trimmed.includes(': ') && !trimmed.startsWith('- ')) {
        if (current && !isList) {
          const [k, ...v] = trimmed.split(': ');
          current[k.trim()] = parseYAMLValue(v.join(': ').trim());
        } else if (isList && current) {
          // continuation of previous object
          const [k, ...v] = trimmed.split(': ');
          current[k.trim()] = parseYAMLValue(v.join(': ').trim());
        }
      } else if (!trimmed.startsWith('-') && !trimmed.includes(':')) {
        // Scalar list item without dash — edge case
        if (trimmed) result.push(parseYAMLValue(trimmed));
      }
    }
    if (current) result.push(current);
    return result;
  },
  xml: (text) => {
    // Minimal XML to array-of-objects conversion
    const rows = [];
    // Find root element
    const rootMatch = text.match(/<(\w+)[^>]*>/);
    if (!rootMatch) return rows;
    const rootTag = rootMatch[1];
    
    // Extract all child elements
    const itemRegex = /<(\w+)[^>]*>([\s\S]*?)<\/\1>/g;
    let match;
    let items = [];
    while ((match = itemRegex.exec(text)) !== null) {
      if (match[1] === rootTag) continue; // skip root
      items.push({ tag: match[1], content: match[2] });
    }
    
    // If items have sub-items, make them rows
    if (items.length > 0) {
      // Group by tag — each tag is a row type
      const row = {};
      items.forEach(item => {
        // Check for nested tags
        const nested = [...item.content.matchAll(itemRegex)];
        if (nested.length > 0) {
          if (!row[item.tag]) row[item.tag] = [];
          const subRow = {};
          nested.forEach(([_, tag, content]) => {
            subRow[tag] = content.trim();
          });
          row[item.tag].push(subRow);
        } else {
          row[item.tag] = item.content.trim();
        }
      });
      rows.push(row);
    }
    
    return rows;
  }
};

const serializers = {
  json: (data, pretty = true) => pretty ? JSON.stringify(data, null, 2) : JSON.stringify(data),
  csv: (data) => {
    if (data.length === 0) return '';
    const headers = Object.keys(data[0]);
    const lines = [headers.map(escapeCSV).join(',')];
    for (const row of data) {
      lines.push(headers.map(h => escapeCSV(String(row[h] ?? ''))).join(','));
    }
    return lines.join('\n');
  },
  yaml: (data) => {
    if (!Array.isArray(data)) data = [data];
    return data.map(item => {
      if (typeof item !== 'object' || item === null) return `- ${item}`;
      const keys = Object.keys(item);
      return keys.map((k, i) => {
        const prefix = i === 0 ? '- ' : '  ';
        return `${prefix}${k}: ${formatYAMLValue(item[k])}`;
      }).join('\n');
    }).join('\n');
  },
  xml: (data, rootName = 'data') => {
    if (!Array.isArray(data)) data = [data];
    let xml = `<?xml version="1.0" encoding="UTF-8"?>\n<${rootName}>\n`;
    for (const row of data) {
      if (typeof row !== 'object' || row === null) {
        xml += `  <item>${escapeXML(String(row))}</item>\n`;
      } else {
        xml += `  <item>\n`;
        for (const [key, val] of Object.entries(row)) {
          xml += `    <${key}>${escapeXML(String(val ?? ''))}</${key}>\n`;
        }
        xml += `  </item>\n`;
      }
    }
    xml += `</${rootName}>`;
    return xml;
  },
  table: (data) => {
    if (data.length === 0) return '(empty)';
    const headers = Object.keys(data[0]);
    // Calculate column widths
    const colWidths = headers.map(h => Math.max(
      h.length,
      ...data.map(row => String(row[h] ?? '').length)
    ));
    // Build separator
    const sep = '+-' + colWidths.map(w => '-'.repeat(w)).join('-+-') + '-+';
    // Header
    const header = '| ' + headers.map((h, i) => h.padEnd(colWidths[i])).join(' | ') + ' |';
    const headerSep = '+-' + colWidths.map(w => '-'.repeat(w)).join('-+-') + '-+';
    // Rows (first 20)
    const maxRows = 20;
    const rows = data.slice(0, maxRows).map(row =>
      '| ' + headers.map((h, i) => String(row[h] ?? '').padEnd(colWidths[i])).join(' | ') + ' |'
    );
    let output = [headerSep, header, headerSep, ...rows, headerSep];
    if (data.length > maxRows) {
      output.push(`... ${data.length - maxRows} more rows`);
    }
    output.push(`(${data.length} rows, ${headers.length} columns)`);
    return output.join('\n');
  }
};

// ─── Transformation operations ───────────────────────────────────────────

const operations = {
  filter: (data, params) => {
    const fn = compileExpression(params.expr);
    return data.filter((item, i) => fn(item, i));
  },
  map: (data, params) => {
    const fn = compileExpression(params.expr);
    return data.map((item, i) => fn(item, i));
  },
  pick: (data, params) => {
    const fields = Array.isArray(params.fields) ? params.fields : [params.fields];
    return data.map(item => {
      const picked = {};
      for (const f of fields) {
        if (f in item) picked[f] = item[f];
      }
      return picked;
    });
  },
  omit: (data, params) => {
    const fields = new Set(Array.isArray(params.fields) ? params.fields : [params.fields]);
    return data.map(item => {
      const omitted = {};
      for (const [k, v] of Object.entries(item)) {
        if (!fields.has(k)) omitted[k] = v;
      }
      return omitted;
    });
  },
  sort: (data, params) => {
    const by = params.by;
    const dir = params.dir === 'desc' ? -1 : 1;
    return [...data].sort((a, b) => {
      const va = a[by], vb = b[by];
      if (va === undefined) return 1;
      if (vb === undefined) return -1;
      if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * dir;
      return String(va).localeCompare(String(vb)) * dir;
    });
  },
  unique: (data, params) => {
    const by = params.by;
    const seen = new Set();
    return data.filter(item => {
      const key = by ? item[by] : JSON.stringify(item);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  },
  group: (data, params) => {
    const by = params.by;
    const groups = {};
    for (const item of data) {
      const key = item[by] ?? '(null)';
      if (!groups[key]) groups[key] = [];
      groups[key].push(item);
    }
    return Object.entries(groups).map(([key, items]) => ({
      key,
      count: items.length,
      items
    }));
  },
  count: (data) => {
    return [{ count: data.length }];
  },
  head: (data, params) => {
    const n = params.n ?? 10;
    return data.slice(0, n);
  },
  tail: (data, params) => {
    const n = params.n ?? 10;
    return data.slice(-n);
  },
  rename: (data, params) => {
    const mapping = params.mapping ?? {};
    return data.map(item => {
      const renamed = {};
      for (const [k, v] of Object.entries(item)) {
        renamed[mapping[k] ?? k] = v;
      }
      return renamed;
    });
  },
  flatten: (data, params) => {
    const field = params.field;
    const result = [];
    for (const item of data) {
      const arr = item[field];
      if (Array.isArray(arr)) {
        for (const sub of arr) {
          if (typeof sub === 'object' && sub !== null) {
            result.push({ ...item, [field]: undefined, ...sub });
          } else {
            result.push({ ...item, [field]: sub });
          }
        }
      } else {
        result.push(item);
      }
    }
    return result;
  }
};

// ─── Helpers ─────────────────────────────────────────────────────────────

function parseCSVLine(line) {
  const result = [];
  let current = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"') {
      if (inQuotes && i + 1 < line.length && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  result.push(current.trim());
  return result;
}

function escapeCSV(val) {
  if (val.includes(',') || val.includes('"') || val.includes('\n')) {
    return '"' + val.replace(/"/g, '""') + '"';
  }
  return val;
}

function parseYAMLValue(val) {
  if (val === 'true') return true;
  if (val === 'false') return false;
  if (val === 'null' || val === '~') return null;
  const num = Number(val);
  if (!isNaN(num) && val.trim() !== '') return num;
  return val;
}

function formatYAMLValue(val) {
  if (val === null || val === undefined) return 'null';
  if (typeof val === 'object') return JSON.stringify(val);
  return String(val);
}

function escapeXML(val) {
  return String(val)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

/**
 * Compile a safe JS expression for filter/map operations.
 * The expression receives `item` (current row) and `i` (index).
 * Returns a function or the default identity passthrough.
 */
function compileExpression(expr) {
  if (!expr || expr === 'item') return (item) => item;
  try {
    const fn = new Function('item', 'i', `"use strict"; return (${expr});`);
    return fn;
  } catch {
    return (item) => item;
  }
}

// ─── Main pipeline function ──────────────────────────────────────────────

/**
 * Run a transformation pipeline.
 *
 * @param {string} inputText - Raw input text
 * @param {string} inputFormat - 'json' | 'csv' | 'yaml' | 'xml'
 * @param {Array} pipeline - Array of { op, ...params }
 * @param {string} outputFormat - 'json' | 'csv' | 'yaml' | 'xml' | 'table'
 * @returns {object} { data, text, error }
 */
function run(inputText, inputFormat, pipeline = [], outputFormat = 'json') {
  try {
    // Parse
    if (!parsers[inputFormat]) return { error: `Unknown input format: ${inputFormat}` };
    let data = parsers[inputFormat](inputText);

    // Transform
    for (const step of pipeline) {
      if (!operations[step.op]) return { error: `Unknown operation: ${step.op}` };
      data = operations[step.op](data, step);
      if (!Array.isArray(data)) data = [data];
    }

    // Serialize
    if (!serializers[outputFormat]) return { error: `Unknown output format: ${outputFormat}` };
    const text = serializers[outputFormat](data);

    return { data, text };
  } catch (err) {
    return { error: err.message };
  }
}

module.exports = { run, parsers, serializers, operations, detectFormat };

/**
 * Detect format from filename or content.
 */
function detectFormat(filename, content) {
  if (filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const extMap = { json: 'json', csv: 'csv', yaml: 'yaml', yml: 'yaml', xml: 'xml' };
    if (extMap[ext]) return extMap[ext];
  }
  if (content) {
    const trimmed = content.trim();
    if (trimmed.startsWith('{') || trimmed.startsWith('[')) return 'json';
    if (trimmed.startsWith('<')) return 'xml';
    if (trimmed.startsWith('- ') || trimmed.startsWith('---')) return 'yaml';
    if (trimmed.includes('\n') && trimmed.includes(',')) {
      const firstLine = trimmed.split('\n')[0];
      if (firstLine.includes(',') && !firstLine.includes(': ')) return 'csv';
    }
  }
  return 'json'; // default
}
