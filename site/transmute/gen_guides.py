#!/usr/bin/env python3
"""Generate Transmute SEO conversion guides from a shared template.

All CLI examples are verified against transmute/src/engine.js (see test/test.js).
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "guides")

HEADER = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🔁</text></svg>">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="article">
<style>
:root{{--ink:#101828;--muted:#4a5a6a;--line:#dde3ea;--bg:#fff;--soft:#f5f7fa;--accent:#7c3aed;--accent-dark:#6023d0;}}
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
pre{{background:#17122b;color:#e6e2f5;padding:16px;border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.6;margin:16px 0;font-family:'SF Mono','Fira Code','Consolas',monospace}}
pre .kw{{color:#b79bf5}}pre .str{{color:#a8d88a}}pre .cm{{color:#7d7699}}pre .nm{{color:#e6e2f5}}pre .prompt{{color:#7d7699}}
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
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title}",
  "description": "{desc}",
  "url": "https://auditedwp.pages.dev/transmute/guides/{slug}/",
  "author": {{"@type": "Organization", "name": "Mahope"}},
  "publisher": {{"@type": "Organization", "name": "Mahope"}}
}}
</script>
</head>
<body>

<header>
  <div class="wrap">
    <a href="/transmute/" class="logo">Trans<span>mute</span></a>
    <nav>
      <a href="/transmute/">Free Demo</a>
      <a href="/deskuptime/">DeskUptime</a>
      <a href="/tools/format/">Web Converter</a>
    </nav>
  </div>
</header>

<div class="wrap">

<h1>{h1}</h1>
<p class="meta">📅 September 2026 · {read} min read · <a href="/transmute/">Try it in your browser →</a></p>

{body}

<div class="cta-box">
  <h3>Pipelines like this — without writing a script</h3>
  <p>The Transmute CLI is free (<code>npx github:mahope/transmute</code>). The desktop app adds an interactive pipeline builder, live preview and batch processing — one-time $19, no subscription.</p>
  <a href="/transmute/" class="btn green">Try the live demo →</a>
  &nbsp;
  <a href="/transmute/#pricing" class="btn">See pricing</a>
</div>

<div class="cta-box" style="background:#fff">
  <p style="margin-bottom:8px"><strong>More guides:</strong> {related}</p>
</div>

</div>

<footer>
  <p><a href="/transmute/">Transmute</a> · <a href="/deskuptime/">DeskUptime</a> · <a href="/tools/format/">Free Web Converter</a> · <a href="/privacy/">Privacy</a> · <a href="/terms/">Terms</a></p>
  <p style="margin-top:8px">© 2026 Mahope. All transformations run locally on your machine.</p>
</footer>

</body>
</html>
"""

guides = {}

# ---------- xml-to-json ----------
guides["xml-to-json"] = dict(
    title="How to Convert XML to JSON (CLI, Python and Online Tools)",
    desc="Convert XML to JSON from the command line or in code. Free CLI examples you can paste today, plus Python and browser options.",
    h1="How to Convert XML to JSON",
    read=4,
    slug="xml-to-json",
    related='<a href="/transmute/guides/json-to-xml/">JSON to XML</a> · <a href="/transmute/guides/jq-alternative/">A simple jq alternative</a>',
    body="""
<p>Legacy APIs, RSS feeds, SOAP responses, Maven and .NET config files — XML is still everywhere, and almost every modern tool wants JSON. Here's how to convert it without hand-writing a parser.</p>

<h2 id="cli">Option 1: The Transmute CLI (free)</h2>
<p><code>transmute</code> parses XML records into JSON directly. Given this file (<code>users.xml</code>):</p>

<pre><span class="prompt">&lt;</span><span class="nm">data</span><span class="prompt">&gt;</span>
  <span class="prompt">&lt;</span><span class="nm">user</span><span class="prompt">&gt;&lt;</span><span class="nm">name</span><span class="prompt">&gt;</span>Alice<span class="prompt">&lt;/</span><span class="nm">name</span><span class="prompt">&gt;&lt;</span><span class="nm">age</span><span class="prompt">&gt;</span>32<span class="prompt">&lt;/</span><span class="nm">age</span><span class="prompt">&gt;&lt;/</span><span class="nm">user</span><span class="prompt">&gt;</span>
  <span class="prompt">&lt;</span><span class="nm">user</span><span class="prompt">&gt;&lt;</span><span class="nm">name</span><span class="prompt">&gt;</span>Bob<span class="prompt">&lt;/</span><span class="nm">name</span><span class="prompt">&gt;&lt;</span><span class="nm">age</span><span class="prompt">&gt;</span>25<span class="prompt">&lt;/</span><span class="nm">age</span><span class="prompt">&gt;&lt;/</span><span class="nm">user</span><span class="prompt">&gt;</span>
<span class="prompt">&lt;/</span><span class="nm">data</span><span class="prompt">&gt;</span></pre>

<p>run:</p>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute users.xml --format xml --pipe <span class="str">'[{"op":"head","n":10}]'</span> --output json
<span class="cm">[
  {
    "name": "Alice",
    "age": "32"
  },
  {
    "name": "Bob",
    "age": "25"
  }
]</span></pre>

<p>You can chain operations in the same pass — here filtering and reshaping before output:</p>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute users.xml --format xml \
    --pipe <span class="str">'[{"op":"filter","expr":"Number(item.age) > 26"},{"op":"pick","fields":["name"]}]'</span> \
    --output json
<span class="cm">[
  {
    "name": "Alice"
  }
]</span></pre>

<h2 id="python">Option 2: Python</h2>

<pre><span class="kw">import</span> xmltodict, json
<span class="kw">with open</span>(<span class="str">"users.xml"</span>) <span class="kw">as</span> f:
    data = xmltodict.parse(f.read())
print(json.dumps(data, indent=2))</pre>

<p><code>pip install xmltodict</code>. Solid, but it's another dependency to pin, and attributes get <code>@</code>-prefixed keys you often have to clean up afterwards.</p>

<h2 id="browser">Option 3: In your browser</h2>
<p>For a quick one-off, the <a href="/transmute/">live demo on the Transmute page</a> converts between formats entirely client-side — nothing is uploaded.</p>

<h2>Caveats worth knowing</h2>
<ul>
<li><strong>XML has no types.</strong> Everything arrives as strings; use a pipeline step like <code>Number(item.age)</code> when you need real numbers.</li>
<li><strong>Attributes vs elements.</strong> Converters differ on whether <code>&lt;user id="7"&gt;</code> becomes an <code>"id"</code> field. Check the output once before trusting it in bulk.</li>
<li><strong>Mixed content</strong> (text plus child elements in one node) doesn't map cleanly to JSON in any tool.</li>
</ul>
""")

# ---------- json-to-xml ----------
guides["json-to-xml"] = dict(
    title="How to Convert JSON to XML (Command Line and Code)",
    desc="Turn JSON arrays into clean XML from the terminal. Free CLI, no dependencies, with filterable pipelines.",
    h1="How to Convert JSON to XML",
    read=4,
    slug="json-to-xml",
    related='<a href="/transmute/guides/xml-to-json/">XML to JSON</a> · <a href="/transmute/guides/json-to-csv-pipeline/">JSON to CSV pipelines</a>',
    body="""
<p>Some enterprise endpoints, older SOAP services and Java tooling still only accept XML. When your data lives in JSON, here's the shortest path across.</p>

<h2 id="cli">The Transmute CLI (free, zero dependencies)</h2>
<p>Given <code>users.json</code>:</p>

<pre><span class="cm">[
  { "name": "Alice", "age": 32 },
  { "name": "Bob",   "age": 20 }
]</span></pre>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute users.json --output xml --pipe <span class="str">'[{"op":"head","n":10}]'</span>
<span class="cm">&lt;?xml version="1.0" encoding="UTF-8"?&gt;
&lt;data&gt;
  &lt;item&gt;
    &lt;name&gt;Alice&lt;/name&gt;
    &lt;age&gt;32&lt;/age&gt;
  &lt;/item&gt;
  ...
&lt;/data&gt;</span></pre>

<p>Because parsing, transforming and serializing are separate steps, you can reshape before emitting XML:</p>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute users.json \
    --pipe <span class="str">'[{"op":"filter","expr":"item.age >= 21"},{"op":"sort","by":"name"}]'</span> \
    --output xml</pre>

<h2 id="python">Python equivalent</h2>

<pre><span class="kw">import</span> json
<span class="kw">from</span> dicttoxml <span class="kw">import</span> dicttoxml

data = json.load(<span class="kw">open</span>(<span class="str">"users.json"</span>))
print(dicttoxml(data).decode())</pre>

<p><code>pip install dicttoxml</code>. Works, but pulls in more of your dependency tree than most one-off jobs justify.</p>

<h2>Things that bite people</h2>
<ul>
<li><strong>Arrays of objects</strong> map naturally; a single bare object needs wrapping first (Transmute does this automatically).</li>
<li><strong>Special characters</strong> in values must be escaped (<code>&amp;</code>, <code>&lt;</code>). A serializer handles this; string concatenation does not.</li>
<li><strong>Nulls</strong>: decide whether they become empty elements or disappear — be consistent.</li>
</ul>
""")

# ---------- jq-alternative ----------
guides["jq-alternative"] = dict(
    title="A Simpler jq Alternative: Filter JSON Without Learning jq Syntax",
    desc="jq is powerful but has a notoriously steep syntax. Filter, sort and reshape JSON with readable pipeline steps instead.",
    h1="Filtering JSON Without Learning jq Syntax",
    read=5,
    slug="jq-alternative",
    related='<a href="/transmute/guides/xml-to-json/">XML to JSON</a> · <a href="/transmute/guides/json-to-csv-pipeline/">JSON to CSV pipelines</a>',
    body="""
<p><code>jq</code> is brilliant once you know it — and famously opaque if you don't. Getting "the names of users over 25, sorted by age" shouldn't require memorizing <code>.[] | select(.age &gt; 25) | .name</code>.</p>

<h2>The same query as named steps</h2>
<p>With the free Transmute CLI, a transformation is a list of steps with plain names:</p>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute users.json --pipe <span class="str">'[
  {"op":"filter","expr":"item.age > 25"},
  {"op":"sort","by":"age"},
  {"op":"pick","fields":["name","age"]}
]'</span></pre>

<p>Each step does one obvious thing:</p>

<div class="table-wrap">
<table>
<thead><tr><th>Step</th><th>What it does</th></tr></thead>
<tbody>
<tr><td><code>filter</code></td><td>Keep rows where an expression is true (<code>item.age > 25</code>)</td></tr>
<tr><td><code>map</code></td><td>Transform each row (<code>item.price * 1.25</code>)</td></tr>
<tr><td><code>sort</code></td><td>Order by a key, ascending or descending</td></tr>
<tr><td><code>unique</code></td><td>Deduplicate by a key (or whole rows)</td></tr>
<tr><td><code>group</code></td><td>Group rows by a key, with counts</td></tr>
<tr><td><code>pick</code> / <code>omit</code></td><td>Select or drop fields</td></tr>
<tr><td><code>rename</code></td><td>Rename columns via a mapping</td></tr>
<tr><td><code>head</code> / <code>tail</code></td><td>First/last N rows</td></tr>
<tr><td><code>count</code></td><td>Row count</td></tr>
</tbody>
</table>
</div>

<h2>When jq is still the right answer</h2>
<ul>
<li>You already know jq well — switching has no upside for you.</li>
<li>Deeply recursive transformations over arbitrary tree shapes.</li>
<li>You're inside a constrained environment where adding any tool is off-limits anyway (then neither helps).</li>
</ul>

<blockquote><p>Honest take: if your queries fit in the table above, named steps are easier to write, easier to read six months later, and easier to explain to a teammate. If they don't, learn jq properly — it pays off.</p></blockquote>

<h2>Chaining formats too</h2>
<p>Steps compose freely with format conversion, so CSV in → filtered YAML out is one command, not three tools glued together in shell:</p>

<pre><span class="prompt">$</span> <span class="kw">cat</span> events.csv | <span class="kw">npx</span> github:mahope/transmute --pipe <span class="str">'[{"op":"unique","by":"user"},{"op":"head","n":10}]'</span> --output yaml</pre>
""")

# ---------- json-to-csv-pipeline ----------
guides["json-to-csv-pipeline"] = dict(
    title="JSON to CSV With Filters: Clean Spreadsheets From API Data",
    desc="Export exactly the rows and columns you want to Excel-friendly CSV. Pick fields, filter, sort and dedupe in one command.",
    h1="JSON to CSV, Minus the Spreadsheet Cleanup",
    read=4,
    slug="json-to-csv-pipeline",
    related='<a href="/transmute/guides/xml-to-json/">XML to JSON</a> · <a href="/transmute/guides/jq-alternative/">A simpler jq alternative</a>',
    body="""
<p>Dumping an API response straight into Excel always ends the same way: hundreds of irrelevant columns, duplicate rows, and half an hour of manual cleanup. Do the shaping <em>before</em> the CSV exists.</p>

<h2>One command, shaped output</h2>
<p>Take a raw export like <code>orders.json</code> and keep only what the spreadsheet actually needs:</p>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute orders.json --pipe <span class="str">'[
  {"op":"filter","expr":"item.status === \"shipped\""},
  {"op":"pick","fields":["id","customer","total"]},
  {"op":"sort","by":"total","dir":"desc"}
]'</span> --output csv
<span class="nm">id,customer,total
1039,Cara Vind,2199.99
1042,Alice Hansen,1299</span></pre>

<p>What each step removed from the cleanup session:</p>
<ul>
<li><strong><code>filter</code></strong> — no more hiding cancelled orders in Excel filters</li>
<li><strong><code>pick</code></strong> — the sheet gets exactly the columns you chose, in order</li>
<li><strong><code>sort</code></strong> — highest value first, before anyone opens it</li>
</ul>

<h2>Deduplicating before import</h2>
<p>Re-running exports tends to duplicate rows. Dedupe by a business key on the way through:</p>

<pre><span class="prompt">$</span> <span class="kw">cat</span> customers.json | <span class="kw">npx</span> github:mahope/transmute --pipe <span class="str">'[{"op":"unique","by":"email"}]'</span> --output csv</pre>

<h2>Nested data</h2>
<p>CSV is flat. Flatten nested objects deliberately with <code>map</code> rather than hoping a generic flattener guesses right:</p>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute users.json --pipe <span class="str">'[
  {"op":"map","expr":"({ name: item.name, city: item.address.city })"}
]'</span> --output csv</pre>

<h2>No Node installed?</h2>
<p>The same transformations run in the browser on the <a href="/transmute/">Transmute demo page</a> — paste JSON, click through the pipeline, copy the CSV out. Nothing leaves your machine.</p>
""")

# ---------- csv-to-json ----------
guides["csv-to-json"] = dict(
    title="How to Convert CSV to JSON (Command Line, Python, Excel)",
    desc="Convert CSV to JSON from the terminal with correct types and no Excel mangling. Free CLI examples, Python snippet and browser option.",
    h1="How to Convert CSV to JSON",
    read=4,
    slug="csv-to-json",
    related='<a href="/transmute/guides/json-to-csv-pipeline/">JSON to CSV pipelines</a> · <a href="/transmute/guides/yaml-to-json/">YAML to JSON</a>',
    body="""
<p>Every developer has done this: export a spreadsheet, then fight it into JSON for an import script or a mock API. Here's the shortest path — with the type problems solved up front.</p>

<h2 id="cli">Option 1: The Transmute CLI (free)</h2>
<p>Given <code>people.csv</code>:</p>

<pre><span class="cm">name,age,city
Alice,32,Aarhus
Bob,25,Odense</span></pre>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute people.csv --output json
<span class="cm">[
  { "name": "Alice", "age": 32, "city": "Aarhus" },
  { "name": "Bob",   "age": 25, "city": "Odense" }
]</span></pre>

<p>You can reshape on the way through — filter, sort, rename columns — in the same command:</p>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute people.csv \
    --pipe <span class="str">'[{"op":"filter","expr":"item.age > 26"},{"op":"sort","by":"age","dir":"desc"}]'</span> \
    --output json
<span class="cm">[
  { "name": "Alice", "age": 32, "city": "Aarhus" }
]</span></pre>

<h2 id="python">Option 2: Python</h2>

<pre><span class="kw">import</span> csv, json
<span class="kw">with open</span>(<span class="str">"people.csv"</span>, newline=<span class="str">""</span>) <span class="kw">as</span> f:
    data = list(csv.DictReader(f))
print(json.dumps(data, indent=2))</pre>

<p>Zero dependencies — but every value arrives as a string. You'll write your own conversion loop for numbers.</p>

<h2 id="excel">Option 3: Excel / Sheets</h2>
<p>"Save As → CSV" gets you out of the spreadsheet, not into JSON. Third-party add-ons do exist, but for anything you'll run more than once a CLI beats clicking through dialogs.</p>

<h2>The types problem (all tools have it)</h2>
<ul>
<li>CSV has no types. Everything is text; converters must guess whether <code>32</code> is a number.</li>
<li>Check one row of output before bulk-converting: are IDs still strings? Leading zeros intact?</li>
<li>Dates stay strings everywhere — decide your format before importing downstream.</li>
</ul>
""")

# ---------- yaml-to-json ----------
guides["yaml-to-json"] = dict(
   title="How to Convert YAML to JSON (CLI and Code, No Online Upload)",
   desc="Convert YAML config files to JSON from the terminal. Free CLI with zero dependencies, Python snippet, and why pasting configs into web tools is risky.",
   h1="How to Convert YAML to JSON",
   read=4,
   slug="yaml-to-json",
   related='<a href="/transmute/guides/csv-to-json/">CSV to JSON</a> · <a href="/transmute/guides/jq-alternative/">A simpler jq alternative</a>',
   body="""
<p>Kubernetes manifests, GitHub Actions workflows, docker-compose files, CI configs — YAML owns configuration. But almost every programming language's tooling wants JSON. Here's the bridge.</p>

<h2 id="cli">Option 1: The Transmute CLI (free)</h2>
<p>Given <code>users.yaml</code>:</p>

<pre><span class="cm">users:
 - name: Alice
   age: 32
 - name: Bob
   age: 25</span></pre>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute users.yaml --format yaml --output json
<span class="cm">[
 { "name": "Alice", "age": 32 },
 { "name": "Bob",   "age": 25 }
]</span></pre>

<p>Filtering works in the same pass — here keeping only users over 26:</p>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute users.yaml --format yaml \
   --pipe <span class="str">'[{"op":"filter","expr":"item.age > 26"}]'</span> \
   --output csv
<span class="cm">name,age
Alice,32</span></pre>

<h2 id="python">Option 2: Python</h2>

<pre><span class="kw">import</span> yaml, json
data = yaml.safe_load(<span class="kw">open</span>(<span class="str">"config.yaml"</span>))
print(json.dumps(data, indent=2))</pre>

<p><code>pip install pyyaml</code>. Use <code>safe_load</code>, never <code>load</code> — the unsafe variant can execute arbitrary code embedded in the file.</p>

<h2 id="why-not-web">Why not paste it into an online converter?</h2>
<blockquote><p>YAML files are usually <em>configuration with secrets in them</em>: API keys, database URLs, tokens. Uploading them to a random website is a leak waiting to happen. A CLI that runs locally has nowhere to send your data.</p></blockquote>

<h2>Gotchas</h2>
<ul>
<li><strong>The Norway problem:</strong> YAML reads the unquoted two-letter country code <code>no</code> as boolean false. Quote such values in the source.</li>
<li><strong>Anchors and aliases</strong> (<code>&amp;</code>/<code>*</code>) disappear after conversion — you get the resolved copy, which is usually what you want anyway.</li>
<li><strong>Multi-document files</strong> (<code>---</code> separated) need per-document handling; most simple converters take only the first.</li>
</ul>
""")

# ---------- json-to-yaml ----------
guides["json-to-yaml"] = dict(
    title="How to Convert JSON to YAML (CLI, Python, No Upload)",
    desc="Convert JSON to clean YAML from the terminal. Free CLI with zero dependencies, a Python one-liner, and how to avoid indentation mistakes.",
    h1="How to Convert JSON to YAML",
    read=4,
    slug="json-to-yaml",
    related='<a href="/transmute/guides/yaml-to-json/">YAML to JSON</a> · <a href="/transmute/guides/jq-alternative/">A simpler jq alternative</a>',
    body="""
<p>JSON is what machines want; YAML is what humans read. When an API response or config export needs to become something a person can review — in docs, PRs, or runbooks — here's the shortest path.</p>

<h2 id="cli">Option 1: The Transmute CLI (free)</h2>
<p>Given <code>users.json</code>:</p>

<pre><span class="cm">[
  { "name": "Alice", "age": 32 },
  { "name": "Bob",   "age": 25 }
]</span></pre>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute users.json --output yaml
<span class="cm">- name: Alice
  age: 32
- name: Bob
  age: 25</span></pre>

<p>You can reshape before emitting — filter rows and drop fields in the same command:</p>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute users.json \
    --pipe <span class="str">'[{"op":"filter","expr":"item.age > 26"},{"op":"omit","fields":["email"]}]'</span> \
    --output yaml
<span class="cm">- name: Alice
  age: 32</span></pre>

<h2 id="python">Option 2: Python</h2>

<pre><span class="kw">import</span> json, yaml
data = json.load(<span class="kw">open</span>(<span class="str">"users.json"</span>))
print(yaml.safe_dump(data, sort_keys=<span class="str">False</span>))</pre>

<p><code>pip install pyyaml</code>. Use <code>safe_dump</code>, never <code>dump</code>. Pass <code>sort_keys=False</code> unless you enjoy your field order being shuffled alphabetically.</p>

<h2>Gotchas when going JSON → YAML</h2>
<ul>
<li><strong>Indentation is syntax.</strong> Hand-converting invites invisible errors; a serializer gets column alignment right every time.</li>
<li><strong>Strings that look like other things.</strong> A value like <code>"no"</code>, <code>"on"</code> or <code>"3.10"</code> must be quoted in YAML or it changes type on load.</li>
<li><strong>Empty values:</strong> JSON <code>null</code>, empty string and empty array all serialize differently — check which convention your target expects.</li>
</ul>
""")

# ---------- csv-to-xml ----------
guides["csv-to-xml"] = dict(
    title="How to Convert CSV to XML (Command Line and Python)",
    desc="Turn spreadsheet exports into well-formed XML from the terminal. Free CLI examples with filtering built in, plus a Python snippet.",
    h1="How to Convert CSV to XML",
    read=4,
    slug="csv-to-xml",
    related='<a href="/transmute/guides/json-to-xml/">JSON to XML</a> · <a href="/transmute/guides/csv-to-json/">CSV to JSON</a>',
    body="""
<p>Legacy import formats, .NET config, enterprise feeds — plenty of systems still ask for XML when your data starts life as a spreadsheet export. Here's the conversion without hand-building tags.</p>

<h2 id="cli">Option 1: The Transmute CLI (free)</h2>
<p>Given <code>people.csv</code>:</p>

<pre><span class="cm">name,age,city
Alice,32,Aarhus
Bob,25,Odense</span></pre>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute people.csv --output xml
<span class="cm">&lt;?xml version="1.0" encoding="UTF-8"?&gt;
&lt;data&gt;
  &lt;item&gt;
    &lt;name&gt;Alice&lt;/name&gt;
    &lt;age&gt;32&lt;/age&gt;
    &lt;city&gt;Aarhus&lt;/city&gt;
  &lt;/item&gt;
  ...
&lt;/data&gt;</span></pre>

<p>Because transformation happens before serialization, you can filter and reshape on the way through:</p>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute people.csv \
    --pipe <span class="str">'[{"op":"filter","expr":"item.age > 26"}]'</span> \
    --output xml
<span class="cm">&lt;?xml version="1.0" encoding="UTF-8"?&gt;
&lt;data&gt;
  &lt;item&gt;
    &lt;name&gt;Alice&lt;/name&gt;
    &lt;age&gt;32&lt;/age&gt;
    &lt;city&gt;Aarhus&lt;/city&gt;
  &lt;/item&gt;
&lt;/data&gt;</span></pre>

<h2 id="python">Option 2: Python</h2>

<pre><span class="kw">import</span> csv
<span class="kw">from</span> xml.etree.ElementTree <span class="kw">import</span> Element, tostring

root = Element(<span class="str">"data"</span>)
<span class="kw">for</span> row <span class="kw">in</span> csv.DictReader(<span class="kw">open</span>(<span class="str">"people.csv"</span>, newline=<span class="str">""</span>)):
    item = Element(<span class="str">"item"</span>)
    <span class="kw">for</span> k, v <span class="kw">in</span> row.items():
        child = Element(k)
        child.text = v
        item.append(child)
    root.append(item)
print(tostring(root, encoding=<span class="str">"unicode"</span>))</pre>

<p>Standard library only — but note it does <em>not</em> escape invalid tag names. A header like <code>first name</code> (with a space) produces broken XML unless you sanitize keys yourself.</p>

<h2>Things that bite people</h2>
<ul>
<li><strong>Tag naming.</strong> Column headers become element names: no spaces, can't start with a digit. Rename columns first (<code>{"op":"rename",...}</code>) if needed.</li>
<li><strong>Escaping.</strong> Values containing <code>&amp;</code> or <code>&lt;</code> must be escaped — always use a serializer.</li>
<li><strong>Types.</strong> CSV has no types, so everything arrives as text in the XML too. Decide downstream whether <code>&lt;age&gt;32&lt;/age&gt;</code> needs casting.</li>
</ul>
""")

# ---------- add-computed-fields ----------
guides["add-computed-fields"] = dict(
    title="How to Add Computed Fields to JSON or CSV (Without Writing a Script)",
    desc="Add derived columns like totals, tax or full names to any JSON or CSV file from the terminal. Free CLI, verified examples.",
    h1="How to Add Computed Fields to JSON or CSV",
    read=4,
    slug="add-computed-fields",
    related='<a href="/transmute/guides/jq-alternative/">A simpler jq alternative</a> · <a href="/transmute/guides/json-to-csv-pipeline/">JSON to CSV pipelines</a>',
    body="""
<p>You have an order list and need a <code>total</code> column. Or user records where you want a lowercase <code>username</code>. The usual answers are a throwaway Python script or a spreadsheet round-trip. There's a shorter path.</p>

<h2 id="cli">The Transmute CLI (free)</h2>
<p>The <code>add</code> operation computes new fields from existing ones. Given <code>orders.json</code>:</p>

<pre><span class="cm">[
  { "name": "Alice", "price": 10, "qty": 2 },
  { "name": "Bob",   "price": 5,  "qty": 4 }
]</span></pre>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute orders.json \\\n    --pipe <span class="str">'[{"op":"add","fields":{"total":"item.price * item.qty"}}]'</span> \\\n    --output json
<span class="cm">[
 {
  "name": "Alice",
  "price": 10,
  "qty": 2,
  "total": 20
 },
 {
  "name": "Bob",
  "price": 5,
  "qty": 4,
  "total": 20
 }
]</span></pre>

<p><code>add</code> works on CSV input too — the types are coerced first, so arithmetic just works:</p>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute orders.csv \\\n    --pipe <span class="str">'[{"op":"add","fields":{"total":"item.price * item.qty"}}]'</span> -o csv</pre>

<p>Combine with the other pipeline steps — here adding a field and filtering in one pass:</p>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute orders.json \\\n    --pipe <span class="str">'[{"op":"add","fields":{"total":"item.price * item.qty"}},{"op":"filter","expr":"item.total >= 20"}]'</span> \\\n    --output json</pre>

<h2 id="alternatives">The alternatives</h2>
<ul>
<li><strong>jq:</strong> <code>jq '. + {total: (.price * .qty)}'</code> works, but jq's syntax is its own language — great once learned, easy to forget between uses.</li>
<li><strong>Python:</strong> a dict comprehension per row plus file I/O. Fine for a one-off, but it's a script you'll never commit and rewrite next month.</li>
<li><strong>Spreadsheet:</strong> import, formula, export — and hope the number formatting survives the trip.</li>
</ul>

<h2>Gotchas</h2>
<ul>
<li><strong>CSV types are inferred.</strong> <code>"007"</code> stays a string on purpose (IDs, zip codes); <code>"7"</code> becomes a number. Check edge-case rows once.</li>
<li><strong>A failing expression yields <code>null</code></strong> instead of crashing the whole run — handy for messy data, but scan for nulls afterwards (<code>{"op":"filter","expr":"item.total === null"}</code>).</li>
</ul>
""")

# ---------- join-two-files ----------
guides["join-two-files"] = dict(
    title="How to Join Two JSON or CSV Files by a Shared Key (CLI)",
    desc="Merge two data files on a common key — like SQL JOIN, but from the terminal. Free CLI with hash-join pipelines.",
    h1="How to Join Two Files by a Shared Key",
    read=5,
    slug="join-two-files",
    related='<a href="/transmute/guides/add-computed-fields/">Adding computed fields</a> · <a href="/transmute/guides/json-to-csv-pipeline/">JSON to CSV pipelines</a>',
    body="""
<p>Orders in one file, customers in another. Inventory counts in one export, product names in another. Merging them usually means opening Python or loading both into SQLite. Here's the one-command version.</p>

<h2 id="cli">The Transmute CLI (free)</h2>
<p>The <code>join</code> operation merges a second row set into your data on a shared key — like a left SQL join. Given <code>cart.json</code>:</p>

<pre><span class="cm">[
  { "sku": "A1", "qty": 2 },
  { "sku": "B2", "qty": 1 }
]</span></pre>

<p>and warehouse stock arriving inline (or from a second file via shell substitution):</p>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute cart.json \\\n    --pipe <span class="str">'[{"op":"join","on":"sku","keep":"left","prefix":"stock_","with":[{"sku":"A1","warehouse":"EU","stock":42},{"sku":"B2","warehouse":"US","stock":7}]}]'</span> \\\n    --output json
<span class="cm">[
 {
  "sku": "A1",
  "qty": 2,
  "stock_warehouse": "EU",
  "stock_stock": 42
 },
 {
  "sku": "B2",
  "qty": 1,
  "stock_warehouse": "US",
  "stock_stock": 7
 }
]</span></pre>

<p>What the options mean:</p>
<div class="table-wrap">
<table>
<tr><th>Option</th><th>Effect</th></tr>
<tr><td><code>on</code></td><td>The shared key. Matching is string-compared, so <code>"A1"</code> matches <code>A1</code>.</td></tr>
<tr><td><code>keep:"left"</code></td><td>Rows without a match are kept (SQL LEFT JOIN). Default drops them (INNER JOIN).</td></tr>
<tr><td><code>prefix</code></td><td>Joined fields get this prefix so they can't collide with existing column names.</td></tr>
<tr><td><code>with</code></td><td>The rows to merge in. Pass a bigger dataset via shell substitution: <code>--pipe "[{\\"op\\":\\"join\\",\\"on\\":\\"id\\",\\"with\\":$(cat stock.json)}]"</code></td></tr>
</table>
</div>

<p>Chain it like anything else — enrich, then filter and count in one pass:</p>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute cart.json \\\n    --pipe <span class="str">'[{"op":"join","on":"sku","keep":"left","with":[...]},{"op":"filter","expr":"item.stock_stock > 0"},{"op":"count"}]'</span> \\\n    --output json</pre>

<h2 id="sql">Compared to the alternatives</h2>
<ul>
<li><strong>SQLite:</strong> <code>sqlite3 :memory: '.import cart.csv c' ...</code> is powerful but it's five steps of schema wrangling for what is conceptually one lookup.</li>
<li><strong>Python/pandas:</strong> <code>df.merge()</code> is the right tool at scale; for files under a few MB, startup cost exceeds the whole job.</li>
<li><strong>jq:</strong> possible with <code>--slurpfile</code>, but the expression syntax for joins is famously hard to get right from memory.</li>
</ul>

<h2>Gotchas</h2>
<ul>
<li><strong>Duplicate keys in the right side:</strong> only the last row per key wins — dedupe first if that matters.</li>
<li><strong>Type coercion:</strong> numeric-looking keys in CSV become numbers on the left but matching is by string, so joins still line up.</li>
</ul>
""")

# ---------- json-to-sql ----------
guides["json-to-sql"] = dict(
    title="How to Convert JSON to SQL INSERT Statements (CLI, Python, No Upload)",
    desc="Turn JSON, CSV or YAML data into ready-to-run SQL INSERT statements from the terminal. Free CLI with filtering, correct escaping and custom table names.",
    h1="How to Convert JSON to SQL INSERT Statements",
    read=5,
    slug="json-to-sql",
    related='<a href="/transmute/guides/csv-to-json/">CSV to JSON</a> · <a href="/transmute/guides/join-two-files/">Joining two files by a key</a>',
    body="""
<p>You have a JSON export and need it in a database: seed data, a migration, test fixtures for staging. Pasting values by hand doesn't scale, and most online converters want you to upload data you'd rather keep local. Here's the terminal-first path.</p>

<h2 id="cli">Option 1: The Transmute CLI (free)</h2>
<p>Given <code>users.json</code>:</p>

<pre><span class="cm">[
  { "name": "Alice", "age": 32 },
  { "name": "Bob",   "age": 25 }
]</span></pre>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute users.json --output sql --table users
<span class="cm">-- Generated by Transmute
INSERT INTO "users" ("name", "age") VALUES
  ('Alice', 32),
  ('Bob', 25);</span></pre>

<p>The same works for <strong>CSV and YAML input</strong> — pick the format flag that matches your source:</p>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute people.csv --output sql --table people
<span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute config.yaml --format yaml --output sql</pre>

<h2 id="filter">Shaping rows before they hit the database</h2>
<p>Because transformation happens before serialization, you filter, sort and reshape in the same command. Only adults, names only:</p>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute users.json \
    --pipe <span class="str">'[{"op":"filter","expr":"item.age > 26"},{"op":"pick","fields":["name"]}]'</span> \
    --output sql --table adults
<span class="cm">-- Generated by Transmute
INSERT INTO "adults" ("name") VALUES
  ('Alice');</span></pre>

<p>This is where a converter beats a one-off script: the same pipeline that cleans the data also decides what gets inserted.</p>

<h2 id="escaping">Escaping and types (the part that breaks imports)</h2>
<ul>
<li><strong>Quotes are escaped correctly.</strong> <code>O'Brien</code> becomes <code>'O''Brien'</code> — the standard SQL doubling, valid in PostgreSQL, MySQL and SQLite. A string-concatenation approach produces broken statements on exactly this input.</li>
<li><strong>Numbers stay numbers.</strong> Numeric-looking strings are emitted unquoted so they insert as real numeric columns; everything else is quoted.</li>
<li><strong>Nulls are real NULLs.</strong> JSON <code>null</code>, missing fields and empty strings all become <code>NULL</code> — not the string <code>"null"</code>.</li>
<li><strong>Booleans become TRUE/FALSE</strong>, which PostgreSQL accepts natively; MySQL maps them to its TINYINT convention.</li>
</ul>

<pre><span class="prompt">$</span> <span class="kw">npx</span> github:mahope/transmute mixed.json --output sql
<span class="cm">-- Generated by Transmute
INSERT INTO "my_table" ("a") VALUES
  (1),
  (NULL);</span></pre>

<h2 id="python">Option 2: Python</h2>

<pre><span class="kw">import</span> json

rows = json.load(<span class="kw">open</span>(<span class="str">"users.json"</span>))
cols = list(rows[0])
<span class="kw">for</span> row <span class="kw">in</span> rows:
    vals = ", ".join(
        "NULL" <span class="kw">if</span> row.get(c) <span class="kw">is</span> <span class="kw">None</span>
        <span class="kw">else</span> str(row[c]) <span class="kw">if</span> isinstance(row.get(c), (int, float))
        <span class="kw">else</span> "'" + str(row[c]).replace("'", "''") + "'"
        <span class="kw">for</span> c <span class="kw">in</span> cols
    )
    print(f'INSERT INTO users ({", ".join(cols)}) VALUES ({vals});')</pre>

<p>Zero dependencies — but note what you're signing up for: column inference from the first row (later rows with extra keys silently drop data), manual type handling, and no batching. Fine for ten rows; error-prone for ten thousand.</p>

<h2 id="why-not-web">Why not paste it into an online converter?</h2>
<blockquote><p>Exports headed for a database often contain customer data, tokens or internal IDs. Uploading them to a random website to get SQL back means trusting a third party with exactly the data you were about to put somewhere permanent. A CLI that runs locally has nowhere to send it.</p></blockquote>

<h2 id="batching">Loading bigger files</h2>
<p>A few thousand INSERT lines load fine through any client (<code>psql -f seed.sql</code>). Past tens of thousands of rows, wrap the output in a single transaction so a failure rolls back cleanly instead of leaving half a table:</p>

<pre><span class="prompt">$</span> <span class="kw">{</span> echo <span class="str">'BEGIN;'</span>; <span class="kw">npx</span> github:mahope/transmute big.json --output sql; echo <span class="str">'COMMIT;'</span>; <span class="kw">}</span> &gt; seed.sql
<span class="prompt">$</span> psql mydb -f seed.sql</pre>

<h2>Gotchas</h2>
<ul>
<li><strong>Column set comes from the union of keys</strong> across rows — consistent records convert cleanly, ragged ones get NULLs where fields are missing.</li>
<li><strong>Dates stay strings</strong> — quote style is correct, but cast to your column type on load if the target isn't text.</li>
<li><strong>Reserved words as column names</strong> (<code>order</code>, <code>group</code>) are quoted with double quotes, which works in PostgreSQL/SQLite; MySQL needs ANSI_QUOTES mode or backticks.</li>
</ul>
""")

os.makedirs(OUT, exist_ok=True)
for slug, g in guides.items():
    d = os.path.join(OUT, slug)
    os.makedirs(d, exist_ok=True)
    html = HEADER.format(**g)
    with open(os.path.join(d, "index.html"), "w") as f:
        f.write(html)
    print("wrote", slug)

# add URLs to sitemap
sm_path = os.path.join(BASE, "..", "sitemap.xml")
with open(sm_path) as f:
    sm = f.read()
added = []
for slug in guides:
    url = f"https://auditedwp.pages.dev/transmute/guides/{slug}/"
    if url not in sm:
        entry = f"<url><loc>{url}</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>"
        sm = sm.replace("</urlset>", entry + "</urlset>")
        added.append(slug)
with open(sm_path, "w") as f:
    f.write(sm)
print("sitemap added:", added)

