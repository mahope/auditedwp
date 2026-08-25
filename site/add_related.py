#!/usr/bin/env python3
"""Add topic-grouped 'Keep reading' related-links section to every blog post.
Ensures every post has internal backlinks (SEO). Idempotent: skips posts
already containing data-related."""
import re, pathlib, sys

BLOG = pathlib.Path(__file__).resolve().parent / "blog"

GROUPS = {
    "consent": [
        "eu-cookie-consent-guide-2026", "gdpr-cookie-banner-fines",
        "gdpr-cookie-fines-tracker", "google-analytics-gdpr-consent",
        "meta-pixel-gdpr-consent", "iab-tcf-compliance-guide",
        "cookiebot-alternative-2026", "server-side-vs-client-side-cookie-consent",
    ],
    "platform": [
        "shopify-gdpr-compliance-guide", "wix-gdpr-compliance-guide",
        "webflow-gdpr-compliance-guide", "squarespace-gdpr-compliance-guide",
        "website-compliance-scanner-comparison",
    ],
    "security": [
        "nis2-compliance-checklist-saas", "nis2-board-liability",
        "nis2-vendor-supply-chain-compliance", "dora-compliance-guide",
        "dora-for-ecommerce-2026", "dora-nis2-gdpr-differences",
        "hsts-preload-guide",
    ],
    "ecommerce": [
        "abmahnung-risk-ecommerce", "german-impressum-foreign-sellers",
        "eaa-compliance-ecommerce", "do-you-need-a-refund-policy",
        "european-accessibility-act-guide", "gdpr-compliance-for-agencies",
        "eu-compliance-checklist-2026",
    ],
}

def group_of(slug):
    for g, slugs in GROUPS.items():
        if slug in slugs:
            return g, slugs
    return None, []

def title_of(html):
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    t = m.group(1).strip() if m else ""
    # strip site suffix like " | EUComply"
    return re.split(r"\s*[|\u2013-]\s*EUComply", t)[0].strip()

def pick_related(slug):
    g, slugs = group_of(slug)
    pool = [s for s in slugs if s != slug] if slugs else []
    if len(pool) < 3:
        others = [s for gg, ss in GROUPS.items() for s in ss if s not in (slug,) and s not in pool]
        pool += others[: 3 - len(pool)]
    return pool[:3]

def titles_map():
    tm = {}
    for d in sorted(BLOG.iterdir()):
        f = d / "index.html"
        if d.is_dir() and f.exists():
            tm[d.name] = title_of(f.read_text(encoding="utf-8"))
    return tm

TM = titles_map()
SECTION = (
    '<nav class="keep-reading" aria-label="Related guides" data-related>'
    '<h2>Keep reading</h2><ul>{items}</ul></nav>'
)
ITEM = '<li><a href="/blog/{slug}/">{title}</a></li>'
CSS = ".keep-reading{margin-top:48px;padding-top:24px;border-top:1px solid rgba(148,163,184,.25)}\n.keep-reading h2{font-size:20px;margin-bottom:12px}\n.keep-reading ul{list-style:none;padding:0;margin:0;display:grid;gap:8px}\n.keep-reading a{color:#7dd3fc;text-decoration:none}\n.keep-reading a:hover{text-decoration:underline}"

changed = skipped = 0
for d in sorted(BLOG.iterdir()):
    if not d.is_dir():
        continue
    f = d / "index.html"
    if not f.exists():
        continue
    html = f.read_text(encoding="utf-8")
    if "data-related" in html:
        skipped += 1
        continue
    items = "".join(ITEM.format(slug=s, title=TM.get(s, s.replace("-", " ").title()))
                    for s in pick_related(d.name))
    section = SECTION.format(items=items)
    # insert before <footer> if present, else before </body>
    if "<footer>" in html:
        idx = html.find("<footer>")
        html = html[:idx] + section + "\n" + html[idx:]
    elif "</body>" in html:
        idx = html.rfind("</body>")
        html = html[:idx] + section + "\n" + html[idx:]
    else:
        print(f"WARN no anchor in {d.name}", file=sys.stderr)
        continue
    # ensure CSS once per file
    if ".keep-reading{" not in html:
        if "</style>" in html:
            html = html.replace("</style>", CSS + "\n</style>", 1)
        else:
            html = html.replace("</head>", f"<style>{CSS}</style>\n</head>", 1)
    f.write_text(html, encoding="utf-8")
    changed += 1

print(f"changed={changed} skipped={skipped}")
