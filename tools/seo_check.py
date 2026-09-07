#!/usr/bin/env python3
"""Scan site/ (or live URLs) for SEO basics and report what is missing.

    python tools/seo_check.py                 # every page under site/
    python tools/seo_check.py --url https://eucomplypro.com/ https://eucomplypro.com/da/
    python tools/seo_check.py --verbose       # list every finding, not just the summary

Exit code is the number of pages with findings (capped at 125).
"""
import html as htmlmod
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
ORIGIN = "https://eucomplypro.com"
SKIP = {"shared/live-check-widget.html", "404.html"}
GENERATORS = ("impressum-generator", "privacy-policy-generator", "terms-of-service-generator",
              "refund-policy-generator", "cookie-policy-generator", "tools")
VERBOSE = "--verbose" in sys.argv


def meta(head, attr, name):
    m = re.search(r'<meta\s+[^>]*%s="%s"[^>]*content="([^"]*)"' % (attr, re.escape(name)), head, re.I)
    return htmlmod.unescape(m.group(1)) if m else None


def _head_ok(target: str) -> bool:
    try:
        req = urllib.request.Request(target, method="HEAD", headers={"User-Agent": "seo_check/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except Exception:
        return False


def check(html: str, url: str, all_pages: dict | None = None) -> list:
    f = []
    hi = html.find("</head>")
    head, body = (html[:hi], html[hi:]) if hi > 0 else (html, html)
    if "�" in html or "Ã©" in html or "â€" in html:
        f.append("mojibake")
    m = re.search(r"<html\b[^>]*\blang=\"([^\"]+)\"", html)
    if not m:
        f.append("no html lang")
    if 'name="viewport"' not in head:
        f.append("no viewport")
    t = re.search(r"<title>(.*?)</title>", head, re.S)
    title = re.sub(r"\s+", " ", htmlmod.unescape(t.group(1))).strip() if t else ""
    if not title:
        f.append("no title")
    elif len(title) > 60:
        f.append(f"title {len(title)} chars")
    d = meta(head, "name", "description")
    if not d:
        f.append("no description")
    elif len(d) > 160:
        f.append(f"description {len(d)} chars")
    elif len(d) < 50:
        f.append("description short")
    c = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', head)
    if not c:
        f.append("no canonical")
    elif not c.group(1).startswith(ORIGIN):
        f.append("canonical off-domain")
    elif url and c.group(1) != url:
        # A page may deliberately point at the page it duplicates, as long as that page exists.
        target = c.group(1)
        exists = target in all_pages if all_pages is not None else _head_ok(target)
        if not exists:
            f.append(f"canonical differs: {target}")
    noindex = bool(re.search(r'name="robots"[^>]*noindex', head))
    if not noindex:
        for p in ("og:title", "og:description", "og:url", "og:image", "og:type"):
            if not meta(head, "property", p):
                f.append(f"no {p}")
        img = meta(head, "property", "og:image")
        if img and not img.startswith("https://"):
            f.append("og:image not absolute")
        if not meta(head, "name", "twitter:card"):
            f.append("no twitter:card")
        if 'application/ld+json' not in html:
            f.append("no JSON-LD")
    h1 = re.findall(r"<h1\b", body)
    if len(h1) != 1:
        f.append(f"{len(h1)} h1")
    for im in re.findall(r"<img\b[^>]*>", body):
        if not re.search(r'\balt=', im):
            f.append("img without alt")
            break
    # hreflang reciprocity
    hl = re.findall(r'<link\s+rel="alternate"\s+hreflang="([^"]+)"\s+href="([^"]+)"', head)
    langs = {l: h for l, h in hl}
    if hl:
        if "x-default" not in langs:
            f.append("hreflang without x-default")
        if url and url not in langs.values():
            f.append("hreflang lacks self")
        if all_pages is not None:
            for l, h in hl:
                if l == "x-default":
                    continue
                other = all_pages.get(h)
                if other is None:
                    f.append(f"hreflang target missing: {h}")
                elif url and url not in other:
                    f.append(f"hreflang not reciprocal: {h}")
    if 'rel="icon"' not in head:
        f.append("no favicon link")
    return f


def local_pages():
    pages = {}
    for p in sorted(SITE.rglob("*.html")):
        rel = p.relative_to(SITE).as_posix()
        if rel in SKIP or rel.startswith("_partials/") or rel.split("/")[0] in GENERATORS:
            continue
        if not rel.endswith("index.html"):
            continue
        url = ORIGIN + "/" + rel[: -len("index.html")]
        pages[url] = p.read_text(encoding="utf-8")
    return pages


def main():
    if "--url" in sys.argv:
        urls = [a for a in sys.argv[sys.argv.index("--url") + 1 :] if a.startswith("http")]
        pages = {}
        for u in urls:
            req = urllib.request.Request(u, headers={"User-Agent": "seo_check/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                pages[u] = r.read().decode("utf-8", "replace")
        hreflang_index = None
    else:
        pages = local_pages()
        hreflang_index = {u: set(re.findall(r'hreflang="[^"]+"\s+href="([^"]+)"', h[: h.find("</head>")])) for u, h in pages.items()}
    bad = 0
    summary = Counter()
    for u, h in pages.items():
        findings = check(h, u, hreflang_index)
        if findings:
            bad += 1
            summary.update(re.sub(r" \d+ chars", " too long", x) for x in findings)
            if VERBOSE or len(pages) <= 12:
                print(u.replace(ORIGIN, "") or "/", "->", "; ".join(findings))
    print(f"\n{len(pages)} pages checked, {bad} with findings")
    for k, v in summary.most_common():
        print(f"  {v:4d}  {k}")
    sys.exit(min(bad, 125))


if __name__ == "__main__":
    main()
