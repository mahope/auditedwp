#!/usr/bin/env python3
"""Port: hver Article-JSON-LD skal have baade `datePublished` og `dateModified`.

    python3 tools/check_article_dates.py
    python3 tools/check_article_dates.py --selftest

Malt 29/9. Skalen skriver sin egen Article-blok med begge datoer, men 113 sider
har en **haandskrevet** blok der udelader dem. Saa sitemapets `lastmod` (fra git)
og JSON-LD fortalte to forskellige historier om samme side: 20 blog-indlaeg
stod med `datePublished` i august og `lastmod: 2026-09-27` i sitemapet, uden at
structured data sagde at siden var blevet roert. Google viser saa den aldre
dato i soegeresultatet.

Rettelsen var at lade skallen injicere de manglende datoer i de haandskrevne
blokke (`inject_article_dates()` i `apply_shell.py`). Porten goer den permanent:

  R1  Hver Article/BlogPosting/TechArticle-JSON-LD — haandskrevet eller
      skreven af skalen — skal have begge datoer, vaere gyldig JSON, og
      `dateModified` maa ikke ligge foer `datePublished`.
  R2  Naar en side har en `dateModified` i JSON-LD, skal sitemapets `lastmod`
      vaere den samme dato. `lastmod_for()` laeser foerst fra JSON-LD, saa de
      to ikke kan glide fra hinanden — med mindre noget andet end datoerne
      aendrer sig.
"""
import json
import pathlib
import pyreq
import re
import sys

pyreq.require(__file__)

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

ARTICLE_TYPES = ("Article", "BlogPosting", "TechArticle")
LD_BLOCK = re.compile(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.S | re.I)
PUB = re.compile(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})"')
MOD = re.compile(r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})"')


def article_blocks(html):
    """(er_artikel_blok, datoer) for hver JSON-LD-blok i en side."""
    for m in LD_BLOCK.finditer(html):
        blk = m.group(1)
        if not any(f'"@type": "{t}"' in blk or f'"@type":"{t}"' in blk for t in ARTICLE_TYPES):
            continue
        yield blk


def tree_findings(pages, lastmod):
    f = []
    for rel, html in pages.items():
        blocks = list(article_blocks(html))
        if not blocks:
            continue
        for blk in blocks:
            try:
                json.loads(blk)
            except ValueError as e:
                f.append(f"R1 {rel}: ugyldig JSON i Article-blokken — {e}")
                continue
            pub, mod = PUB.search(blk), MOD.search(blk)
            if not pub:
                f.append(f"R1 {rel}: Article-blokken har ingen datePublished")
            if not mod:
                f.append(f"R1 {rel}: Article-blokken har ingen dateModified")
            if pub and mod and mod.group(1) < pub.group(1):
                f.append(f"R1 {rel}: dateModified {mod.group(1)} ligger foer datePublished {pub.group(1)}")
        side_mod = MOD.search(html)
        path = "/" + rel[: -len("/index.html")] if rel.endswith("/index.html") else "/" + rel
        if side_mod and lastmod.get(path) and side_mod.group(1) != lastmod[path]:
            f.append(f"R2 {rel}: JSON-LD siger dateModified {side_mod.group(1)}, "
                     f"sitemapet siger lastmod {lastmod[path]}")
    return f


def pages():
    return {
        p.relative_to(SITE).as_posix(): p.read_text(encoding="utf-8", errors="replace")
        for p in sorted(SITE.rglob("*.html"))
        if "_partials" not in p.parts
    }


def sitemap_lastmod():
    import xml.etree.ElementTree as ET
    NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    out = {}
    for url in ET.parse(SITE / "sitemap.xml").getroot().findall(f"{NS}url"):
        loc = url.find(f"{NS}loc").text
        lm = url.find(f"{NS}lastmod")
        if lm is None:
            continue
        path = loc.replace("https://eucomplypro.com", "").rstrip("/") or "/"
        out[path] = lm.text
    return out


def selftest():
    """Bevis at porten kan fejle. Tre muteringer mod de rigtige filer."""
    real_pages = pages()
    real_lastmod = sitemap_lastmod()
    cases = []

    # Find en side med en komplet haandskrevet Article-blok at mutere.
    target = None
    for rel, html in real_pages.items():
        if any(MOD.search(b) and PUB.search(b) for b in article_blocks(html)):
            target = rel
            break
    if target is None:
        print("SELFTEST FEJLT: ingen side med komplet Article-blok at mutere")
        return 1

    def without_mod(html):
        return MOD.sub("", html, count=1)

    def mod_before_pub(html):
        return MOD.sub('"dateModified": "2020-01-01"', html, count=1)

    def wrong_sitemap(html):
        return html

    cases.append(("R1 dateModified fjernet", target, without_mod(real_pages[target]), real_lastmod))
    cases.append(("R1 dateModified foer datePublished", target, mod_before_pub(real_pages[target]), real_lastmod))

    # R2: saa sitemapet fra den samme side og ret lastmod.
    path = "/" + target[: -len("/index.html")] if target.endswith("/index.html") else "/" + target
    if path not in real_lastmod:
        print(f"SELFTEST FEJLT: {path} findes ikke i sitemapet")
        return 1
    wrong = dict(real_lastmod)
    wrong[path] = "2020-01-01"
    cases.append(("R2 sitemap lastmod passer ikke", target, real_pages[target], wrong))

    passed = 0
    for name, rel, html, lastmod in cases:
        p = dict(real_pages)
        p[rel] = html
        found = tree_findings(p, lastmod)
        if found:
            passed += 1
        else:
            print(f"SELFTEST FEJLT: {name} blev ikke fanget")
    print(f"SELFTEST {'GRØN' if passed == len(cases) else 'RØD'} — {passed}/{len(cases)} negative cases fanges")
    return 0 if passed == len(cases) else 1


def main():
    all_pages = pages()
    lastmod = sitemap_lastmod()
    f = tree_findings(all_pages, lastmod)
    n_blocks = sum(len(list(article_blocks(html))) for html in all_pages.values())
    print(f"ARTICLE-DATOER: {n_blocks} Article-blokke i {len(all_pages)} sider — {len(lastmod)} sitemap-poster laest")
    if not f:
        print("ARTICLE-DATOER GRØN — hver Article-blok har begge datoer, og sitemapet passer.")
        return 0
    for line in f:
        print(f"FEJL {line}")
    print(f"\n{len(f)} article-dato-fund")
    return 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main())
