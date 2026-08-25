#!/usr/bin/env python3
"""Generate SEO conversion guides from a shared template."""
import os

BASE = os.path.dirname(os.path.abspath(__file__))

HEADER = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🔧</text></svg>">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="article">
<style>
:root{{--ink:#0b1a2a;--muted:#4a5a6a;--line:#d0d8e0;--bg:#fff;--soft:#f5f7fa;--accent:#2868d0;--accent-dark:#1a4f9e;}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;color:var(--ink);background:var(--bg);line-height:1.7}}
.wrap{{max-width:760px;margin:0 auto;padding:0 20px}}
header{{border-bottom:1px solid var(--line);padding:14px 0}}
header .wrap{{display:flex;align-items:center;justify-content:space-between}}
.logo{{font-weight:800;font-size:18px;text-decoration:none;color:var(--ink)}}
.logo span{{color:var(--accent)}}
nav a{{color:var(--muted);text-decoration:none;margin-left:20px;font-size:14px}}
nav a:hover{{color:var(--accent)}}
h1{{font-size:34px;line-height:1.2;margin:40px 0 8px;letter-spacing:-.02em}}
.meta{{color:var(--muted);font-size:14px;margin-bottom:32px;display:flex;gap:16px;flex-wrap:wrap}}
h2{{font-size:24px;margin:36px 0 10px;letter-spacing:-.01em;padding-top:8px}}
h3{{font-size:18px;margin:24px 0 8px}}
p{{margin-bottom:16px}}
code{{background:var(--soft);padding:2px 6px;border-radius:4px;font-size:14px;font-family:'SF Mono','Fira Code','Consolas',monospace}}
pre{{background:#1a1f2e;color:#e4e8f0;padding:16px;border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.6;margin:16px 0;font-family:'SF Mono','Fira Code','Consolas',monospace}}
pre .kw{{color:#7eb8f0}}pre .str{{color:#a8d88a}}pre .cm{{color:#6a7a8a}}pre .nm{{color:#e4e8f0}}pre .prompt{{color:#6a7a8a}}
.table-wrap{{overflow-x:auto;margin:16px 0}}
table{{width:100%;border-collapse:collapse;font-size:14px}}
th,td{{padding:10px 14px;text-align:left;border-bottom:1px solid var(--line)}}
th{{background:var(--soft);font-size:12px;text-transform:uppercase;color:var(--muted);letter-spacing:.04em}}
blockquote{{border-left:3px solid var(--accent);padding:12px 16px;margin:16px 0;background:var(--soft);border-radius:0 6px 6px 0}}
blockquote p{{margin:0;color:var(--muted);font-size:14px}}
ul,ol{{margin:12px 0 16px;padding-left:24px}}
li{{margin-bottom:6px}}
.cta-box{{background:var(--soft);border:1px solid var(--line);border-radius:8px;padding:24px;text-align:center;margin:32px 0}}
.cta-box h3{{font-size:18px;margin-bottom:6px}}
.cta-box p{{font-size:14px;color:var(--muted);margin-bottom:16px}}
.btn{{display:inline-block;background:var(--accent);color:#fff;text-decoration:none;font-weight:600;padding:10px 22px;border-radius:6px;font-size:14px;transition:background .12s}}
.btn:hover{{background:var(--accent-dark)}}
.btn.green{{background:#1a7a44}}
footer{{text-align:center;padding:32px 0;color:var(--muted);font-size:13px;border-top:1px solid var(--line);margin-top:48px}}
footer a{{color:var(--accent);text-decoration:none}}
@media(max-width:600px){{h1{{font-size:26px}}h2{{font-size:20px}}}}
</style>
</head>
<body>

<header>
  <div class="wrap">
    <a href="/" class="logo">Quick<span>Format</span></a>
    <nav>
      <a href="/tools/format/">Free Converter</a>
      <a href="/quickconvert/">Desktop App</a>
      <a href="/guides/json-vs-yaml/">JSON vs YAML</a>
    </nav>
  </div>
</header>

<div class="wrap">

<h1>{h1}</h1>
<p class="meta">📅 August 24, 2026 · {read} min read · <a href="/tools/format/">Try the free converter →</a></p>

{body}

<div class="cta-box">
  <h3>Convert {pair} in one click</h3>
  <p>QuickFormat lives in your Mac menu bar. Paste, click, done — JSON, YAML, CSV, TOML and XML, offline.</p>
  <a href="/quickconvert/" class="btn green">Get QuickFormat for Mac — $9 →</a>
  &nbsp;
  <a href="/tools/format/" class="btn">Or use the free web converter</a>
</div>

</div>

<footer>
  <p><a href="/">EUComply Scanner</a> · <a href="/tools/format/">Free Format Converter</a> · <a href="/quickconvert/">QuickFormat for Mac</a> · <a href="/guides/json-vs-yaml/">JSON vs YAML Guide</a> · <a href="/privacy/">Privacy</a> · <a href="/terms/">Terms</a></p>
  <p style="margin-top:8px">© 2026 Mahope. All conversions run locally in your browser or on your machine.</p>
</footer>

</body>
</html>
"""

guides = {}

# ---------- yaml-to-json ----------
guides["yaml-to-json"] = dict(
    title="How to Convert YAML to JSON (3 Ways: CLI, Web, Desktop)",
    desc="Three reliable ways to convert YAML to JSON: yq and qf CLI commands, a free online converter, and a Mac menu bar app. With code examples.",
    h1="How to Convert YAML to JSON (3 Ways)",
    read=5, pair="YAML → JSON",
    body="""
<p>You have a Kubernetes manifest, a GitHub Actions workflow, or a Docker Compose file — and something downstream wants JSON. An API payload, a <code>jq</code> query, a JavaScript tool that only reads JSON.</p>

<p>Here are three ways to convert YAML to JSON, from one-liners to a daily-driver desktop app.</p>

<h2 id="cli">Method 1: CLI Tools (Fastest for Developers)</h2>

<h3>Using <code>qf</code> (QuickFormat CLI)</h3>
<p>The <code>qf</code> CLI detects the format automatically, so you never argue about flags:</p>

<pre><span class="prompt">$</span> <span class="kw">cat</span> config.yaml | <span class="kw">qf</span> --to json
<span class="nm">{"name"</span>: <span class="str">"test"</span>, <span class="nm">"replicas"</span>: 3}</pre>

<p>It handles multi-document files, nested structures and anchors correctly, and it's zero-dependency — no Python, no Ruby, nothing to install besides one binary.</p>

<h3>Using <code>yq</code></h3>
<p>If you already use <code>yq</code> (the Go version by mikefarah):</p>

<pre><span class="prompt">$</span> <span class="kw">yq</span> -o=json eval config.yaml</pre>

<p>Note the <code>-o=json</code> flag — without it you get YAML back out, which is easy to miss.</p>

<h3>Using Python</h3>

<pre><span class="prompt">$</span> <span class="kw">python3</span> -c <span class="str">"import yaml,json,sys;print(json.dumps(yaml.safe_load(sys.stdin)))"</span> &lt; config.yaml</pre>

<p>This requires PyYAML (<code>pip install pyyaml</code>). Watch out for <code>yaml.load()</code> without a Loader — it's a known security issue; always use <code>yaml.safe_load()</code>.</p>

<h2 id="web">Method 2: Free Online Converter</h2>
<p>For a one-off conversion, paste into the <a href="/tools/format/">free browser-based converter</a>. It runs entirely client-side — your data is never uploaded anywhere, so it's safe for configs containing hostnames or secrets you'd rather not send to a random site.</p>

<h2 id="desktop">Method 3: A Menu Bar App for Daily Use</h2>
<p>If you convert formats more than a few times a week, the <a href="/quickconvert/">QuickFormat desktop app</a> sits in your Mac menu bar: paste YAML, hit the shortcut, copy JSON out. No terminal, no browser tab hunting.</p>

<h2>Common Pitfalls</h2>
<ul>
<li><strong>Dates:</strong> YAML parses unquoted dates like <code>2026-08-24</code> into date objects; JSON has no date type. Most converters emit them as strings.</li>
<li><strong>Anchors and aliases:</strong> <code>&amp;base</code> / <code>*base</code> references are resolved before conversion — the output JSON will contain duplicated values instead of references.</li>
<li><strong>Multi-document files:</strong> a file with multiple <code>---</code> documents can't become a single JSON object. Tools either take the first document or wrap output in an array — check which yours does.</li>
</ul>

<h2>Which should you pick?</h2>
<ul>
<li><strong>One-off:</strong> free <a href="/tools/format/">web converter</a>.</li>
<li><strong>Scripts/CI:</strong> <a href="/quickconvert/">qf CLI</a> — pipe in, pipe out.</li>
<li><strong>Daily use:</strong> <a href="/quickconvert/">QuickFormat for Mac</a> — $9 one-time, offline.</li>
</ul>
""")

# ---------- json-to-csv ----------
guides["json-to-csv"] = dict(
    title="How to Convert JSON to CSV (4 Ways, Including Nested Arrays)",
    desc="Convert JSON to CSV with jq, qf, Python/pandas or a free online tool. Includes how to flatten nested arrays and objects correctly.",
    h1="How to Convert JSON to CSV (4 Ways)",
    read=6, pair="JSON → CSV",
    body="""
<p>Exporting API responses, database dumps or log data to open in Excel or Google Sheets always ends the same way: someone pastes JSON into a converter and gets mangled columns. Here's how to do it right.</p>

<h2 id="cli">Method 1: CLI (Best for Automation)</h2>

<h3>Using <code>qf</code> (QuickFormat CLI)</h3>

<pre><span class="prompt">$</span> <span class="kw">cat</span> users.json | <span class="kw">qf</span> --to csv
<span class="nm">id,name,email
1,Alice,alice@example.com
2,Bob,bob@example.com</span></pre>

<p><code>qf</code> takes an array of flat objects and produces proper headers automatically. Nested values are flattened with dot notation (<code>address.city</code> becomes a column named exactly that).</p>

<h3>Using <code>jq</code></h3>

<pre><span class="prompt">$</span> <span class="kw">jq</span> -r '(.[0] | keys_unsorted) as $cols | $cols, .[] | [.[$cols[]]] | @csv' users.json</pre>

<p>Powerful but famously unreadable — fine if you already know <code>jq</code>, otherwise skip it.</p>

<h2 id="python">Method 2: Python (pandas)</h2>

<pre><span class="kw">import</span> pandas <span class="kw">as</span> pd
df = pd.read_json(<span class="str">"users.json"</span>)
df.to_csv(<span class="str">"users.csv"</span>, index=<span class="kw">False</span>)</pre>

<p>pandas normalizes nested structures with <code>pd.json_normalize(data)</code> if you need flattening control. Heavyweight for small jobs, unbeatable for messy ones.</p>

<h2 id="web">Method 3: Free Online Converter</h2>
<p>The <a href="/tools/format/">browser-based converter</a> handles JSON → CSV entirely on your device — nothing is uploaded. Good when the data contains anything sensitive.</p>

<h2 id="excel">Method 4: Directly in Excel/Sheets</h2>
<p>Excel (365) and Google Sheets can import JSON via Power Query / IMPORTDATA respectively — but both choke silently on nested arrays. Flatten first, then import the CSV.</p>

<h2>Nested Arrays: The Hard Part</h2>
<blockquote><p><strong>Rule of thumb:</strong> CSV can only represent one table. If your JSON has arrays of objects inside rows, decide: flatten each array into a joined string, split into multiple CSVs, or repeat the parent row per child. There's no universally correct answer — pick what your spreadsheet needs.</p></blockquote>

<ul>
<li><strong>Automation:</strong> <a href="/quickconvert/">qf CLI</a> — deterministic, scriptable.</li>
<li><strong>One-off, sensitive data:</strong> <a href="/tools/format/">local web converter</a>.</li>
<li><strong>Messy/nested data at scale:</strong> pandas.</li>
<li><strong>Frequent conversions on a Mac:</strong> <a href="/quickconvert/">QuickFormat</a> — $9 once, lives in the menu bar.</li>
</ul>
""")

# ---------- csv-to-json ----------
guides["csv-to-json"] = dict(
    title="How to Convert CSV to JSON (CLI, Python and Online Tools)",
    desc="Turn CSV into clean JSON: type-correct numbers and booleans, nested columns via dot notation. CLI, Python and free online methods compared.",
    h1="How to Convert CSV to JSON",
    read=5, pair="CSV → JSON",
    body="""
<p>Spreadsheets are where product data lives and APIs are where it goes. Converting CSV to JSON sounds trivial until you hit types, empty cells and commas inside quoted fields.</p>

<h2 id="cli">Method 1: CLI</h2>

<h3>Using <code>qf</code> (QuickFormat CLI)</h3>

<pre><span class="prompt">$</span> <span class="kw">cat</span> users.csv | <span class="kw">qf</span> --to json
<span class="nm">[
  { "id": 1, "name": "Alice", "active": true },
  { "id": 2, "name": "Bob", "active": false }
]</span></pre>

<p><code>qf</code> converts values that look like numbers, booleans and nulls into their JSON types, and uses the header row as keys. Columns named with dot notation (<code>address.city</code>) become nested objects.</p>

<h3>Using <code>jq</code>+<code>mlr</code> alternatives</h3>
<p><code>jq</code> alone doesn't parse CSV. Miller (<code>mlr --csv put -j</code>) does if you have it installed; otherwise a tiny script is simpler than a new dependency.</p>

<h2 id="python">Method 2: Python (stdlib only)</h2>

<pre><span class="kw">import</span> csv, json
<span class="kw">with</span> open(<span class="str">"users.csv"</span>) <span class="kw">as</span> f:
    data = list(csv.DictReader(f))
print(json.dumps(data, indent=2))</pre>

<p>No dependencies — but everything comes out as strings. Add your own type coercion if the consumer cares about numbers vs strings.</p>

<h2 id="web">Method 3: Free Online Converter</h2>
<p>Paste CSV into the <a href="/tools/format/">browser converter</a> and copy JSON out. It runs locally in your browser — customer lists and pricing sheets never leave your machine.</p>

<h2>Gotchas</h2>
<ul>
<li><strong>Types:</strong> CSV has no types. Decide whether <code>"007"</code> stays a string or becomes <code>7</code> (it shouldn't become 7 — IDs with leading zeros are strings).</li>
<li><strong>BOM:</strong> Excel-exported CSVs often start with a UTF-8 BOM that shows up as garbage in the first key. Strip it.</li>
<li><strong>Quoted commas:</strong> any correct parser handles <code>"Smith, John"</code> — if your hand-rolled <code>split(",")</code> doesn't, stop hand-rolling.</li>
</ul>

<ul>
<li><strong>Scripts:</strong> <a href="/quickconvert/">qf CLI</a>.</li>
<li><strong>One-off:</strong> <a href="/tools/format/">web converter</a>.</li>
<li><strong>Every day:</strong> <a href="/quickconvert/">QuickFormat for Mac</a>, $9 one-time.</li>
</ul>
""")

# ---------- toml-vs-yaml ----------
guides["toml-vs-yaml"] = dict(
    title="TOML vs YAML: Which Config Format Should You Use in 2026?",
    desc="TOML vs YAML compared: readability, gotchas, tooling and where each wins. Plus how to convert between them instantly.",
    h1="TOML vs YAML: Which Config Format Should You Use?",
    read=6, pair="TOML ⇄ YAML",
    body="""
<p>Rust chose TOML. Kubernetes chose YAML. Python packaging chose TOML. Both formats are winning — just in different worlds. Here's an honest comparison and how to move between them.</p>

<h2>The short answer</h2>
<div class="table-wrap"><table>
<tr><th></th><th>TOML</th><th>YAML</th></tr>
<tr><td><strong>Spec size</strong></td><td>Small, unambiguous</td><td>Huge, surprising corners</td></tr>
<tr><td><strong>Deep nesting</strong></td><td>Gets verbose fast</td><td>Clean indentation</td></tr>
<tr><td><strong>Copy-paste safety</strong></td><td>High</td><td>Indentation errors are silent bugs</td></tr>
<tr><td><strong>Comments</strong></td><td>Yes</td><td>Yes</td></tr>
<tr><td><strong>Ecosystem home</strong></td><td>Rust, Python packaging, Cargo</td><td>Kubernetes, CI/CD, Ansible, Docker Compose</td></tr>
</table></div>

<h2>Where TOML wins</h2>
<ul>
<li><strong>No surprise semantics.</strong> In YAML, the <a href="https://www.bram.us/2022/01/11/the-norway-problem/" rel="nofollow">Norway problem</a> is famous: <code>no</code>, <code>off</code> and country codes silently become booleans in some parsers. TOML has none of that.</li>
<li><strong>Flat configs read beautifully.</strong> <code>pyproject.toml</code>, <code>Cargo.toml</code> — key/value pairs with sections are what most config actually is.</li>
</ul>

<h2>Where YAML wins</h2>
<ul>
<li><strong>Deeply nested structures.</strong> A Kubernetes Deployment is 60+ lines in YAML; in TOML it becomes a wall of repeated bracket-sections.</li>
<li><strong>Everyone in DevOps knows it.</strong> Network effect matters more than elegance.</li>
</ul>

<h2>Converting between them</h2>
<p>You rarely get to choose the format — you inherit it. When you need one in the shape of the other:</p>

<pre><span class="prompt">$</span> <span class="kw">cat</span> pyproject.toml | <span class="kw">qf</span> --to yaml
<span class="nm">project</span>:
  <span class="nm">name</span>: <span class="str">my-app</span>
  <span class="nm">version</span>: <span class="str">"2.0"</span></pre>

<p><code>qf</code> detects TOML vs YAML automatically, both directions. Or paste into the <a href="/tools/format/">free online converter</a> — it supports TOML ⇄ YAML ⇄ JSON ⇄ CSV ⇄ XML entirely in your browser.</p>

<h2>Recommendation</h2>
<ul>
<li><strong>New app config, shallow structure:</strong> TOML. Fewer foot-guns.</li>
<li><strong>Kubernetes-style manifests, deep nesting, ecosystem pressure:</strong> YAML. Fight the battle you're in.</li>
<li><strong>Need both?</strong> Keep sources in whichever, convert with <a href="/quickconvert/">qf</a> or the <a href="/tools/format/">web tool</a> when a consumer demands the other format.</li>
</ul>
""")

for slug, g in guides.items():
    d = os.path.join(BASE, slug)
    os.makedirs(d, exist_ok=True)
    html = HEADER.format(**g)
    with open(os.path.join(d, "index.html"), "w") as f:
        f.write(html)
    print("wrote", slug)

# add URLs to sitemap before </urlset>
sm_path = os.path.join(BASE, "..", "sitemap.xml")
with open(sm_path) as f:
    sm = f.read()
added = []
for slug in guides:
    url = f"https://eucomplypro.com/guides/{slug}/"
    if url not in sm:
        entry = f"<url><loc>{url}</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>"
        sm = sm.replace("</urlset>", entry + "</urlset>")
        added.append(slug)
with open(sm_path, "w") as f:
    f.write(sm)
print("sitemap added:", added)
