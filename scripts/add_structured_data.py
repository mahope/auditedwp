#!/usr/bin/env python3
"""Add JSON-LD structured data to pages missing it. Idempotent."""
import os, re, html

ROOT = "site"

def meta_of(fp):
    src = open(fp, encoding="utf-8").read()
    def m(p):
        r = re.search(p, src)
        return html.unescape(r.group(1)).strip() if r else ""
    title = m(r"<title>(.*?)</title>")
    if not title:
        t = re.search(r'property="og:title" content="(.*?)"', src)
        title = html.unescape(t.group(1)) if t else ""
    desc = m(r'<meta name="description" content="(.*?)"')
    if not desc:
        d = re.search(r'property="og:description" content="(.*?)"', src)
        desc = html.unescape(d.group(1)) if d else ""
    return src, title.replace(" | EUComply", "").strip(), desc.strip()

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# path suffix -> (schema type, extra fields builder)
def app_fields(path):
    return {
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
    }

ARTICLE = re.compile(r"(^site/(blog|guides|devnotify)/|^site/pro/vs-|cmp-comparison)")
APP = re.compile(r"^site/$|^site/(scan|cli|plugin|extension|badge|quickconvert|check-eu-compliance|tools|tools/format)(/|$)")

import json as _j

def json_dumps(o):
    return _j.dumps(o, indent=2, ensure_ascii=False)

added = []

for dirpath, dirs, files in os.walk(ROOT):
    for f in files:
        if not f.endswith(".html"):
            continue
        fp = os.path.join(dirpath, f)
        rel = fp[:-len(".html")] if fp.endswith("/index.html") else fp[:-5]
        src, title, desc = meta_of(fp)
        if not title or "ld+json" in src:
            continue
        url = "https://eucomplypro.com/" + (rel[len("site"):] and rel[len("site")+1:] + "/" or "")
        url = url.rstrip("/") or "https://eucomplypro.com/"
        if APP.search(rel):
            obj = {"@context": "https://schema.org", "@type": "WebApplication",
                   "name": title, "description": desc, "url": url}
            obj.update(app_fields(rel))
        elif ARTICLE.search(rel):
            obj = {"@context": "https://schema.org", "@type": "Article",
                   "headline": title, "description": desc,
                   "url": url, "author": {"@type": "Organization", "name": "EUComply"},
                   "publisher": {"@type": "Organization", "name": "EUComply"}}
        else:
            continue  # utility pages: skip
        snippet = '<script type="application/ld+json">\n' + \
            json_dumps(obj) + '\n</script>\n'
        # insert before </head>
        new = src.replace("</head>", snippet + "</head>", 1)
        open(fp, "w", encoding="utf-8").write(new)
        added.append(rel)

import json as _j
def json_dumps(o):
    return _j.dumps(o, indent=2, ensure_ascii=False)

print(f"Added ld+json to {len(added)} pages")
for a in sorted(added):
    print(" ", a)
