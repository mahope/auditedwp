#!/usr/bin/env python3
"""Layout-shift check: header and main must sit in the same box on every page.

    python tools/layout_check.py http://127.0.0.1:8765            # home + 10 random pages per language
    python tools/layout_check.py BASE --per-lang 10 --widths 360,768,1280 --seed 7
    python tools/layout_check.py BASE --all                        # every page (slow)

For each viewport width it records the bounding boxes of the family bar, the header and
main (left, width, top) plus the header's inner row.  All pages at one width must agree
within ±1px.  Prints a table per width and exits 1 on any deviation.
"""
import random
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
args = sys.argv[1:]
base = args[0].rstrip("/") if args and not args[0].startswith("--") else "http://127.0.0.1:8765"
per_lang = 10
widths = [360, 768, 1280]
seed = 1
if "--per-lang" in args:
    per_lang = int(args[args.index("--per-lang") + 1])
if "--widths" in args:
    widths = [int(x) for x in args[args.index("--widths") + 1].split(",")]
if "--seed" in args:
    seed = int(args[args.index("--seed") + 1])
everything = "--all" in args

pages = []
for p in sorted(SITE.rglob("index.html")):
    rel = p.relative_to(SITE).as_posix()
    if rel.startswith("_partials") or rel.startswith("shared/"):
        continue
    url = "/" + rel[: -len("index.html")]
    pages.append(url)
by_lang = {}
for u in pages:
    m = re.match(r"^/(da|de|fr|es)/", u)
    by_lang.setdefault(m.group(1) if m else "en", []).append(u)
random.seed(seed)
sample = []
for lang, urls in sorted(by_lang.items()):
    home = "/" if lang == "en" else f"/{lang}/"
    rest = [u for u in urls if u != home]
    sample += ([home] if home in urls else []) + (rest if everything else random.sample(rest, min(per_lang, len(rest))))
sample.append("/404.html")

JS = """() => {
  const box = (el) => { if (!el) return null; const r = el.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.width), Math.round(r.top), Math.round(r.height)]; };
  return { fam: box(document.querySelector('.fam')), header: box(document.querySelector('.sh')), row: box(document.querySelector('.sh .container')),
           main: box(document.querySelector('main')), footer: box(document.querySelector('.sf')), scrollW: document.documentElement.scrollWidth, innerW: window.innerWidth };
}"""

bad = 0
with sync_playwright() as p:
    b = p.chromium.launch()
    for w in widths:
        ctx = b.new_context(viewport={"width": w, "height": 900}, device_scale_factor=1, reduced_motion="reduce")
        pg = ctx.new_page()
        rows = []
        for u in sample:
            pg.goto(base + u, wait_until="load")
            pg.evaluate("window.scrollTo(0,0)")
            pg.wait_for_timeout(120)
            rows.append((u, pg.evaluate(JS)))
        ref = rows[0][1]
        print(f"\n== {w}px  reference {rows[0][0]}: fam {ref['fam']} header {ref['header']} row {ref['row']} main l/w {ref['main'][:2] if ref['main'] else None}")
        for u, r in rows:
            dev = []
            for key in ("fam", "header", "row"):
                if r[key] is None or ref[key] is None:
                    dev.append(f"{key} missing")
                elif any(abs(a - c) > 1 for a, c in zip(r[key], ref[key])):
                    dev.append(f"{key} {r[key]}")
            if r["main"] is None or ref["main"] is None:
                dev.append("main missing")
            elif any(abs(a - c) > 1 for a, c in zip(r["main"][:3], ref["main"][:3])):
                dev.append(f"main {r['main'][:3]}")
            if r["scrollW"] > r["innerW"]:
                dev.append(f"overflow {r['scrollW']}>{r['innerW']}")
            if dev:
                bad += 1
                print(f"  DEV {u}: " + "; ".join(dev))
        print(f"  {len(rows)} pages, {sum(1 for _, r in rows if r['main'])} with main, deviations so far: {bad}")
        ctx.close()
    b.close()
print(f"\npages sampled: {len(sample)} x {len(widths)} widths, deviations: {bad}")
sys.exit(1 if bad else 0)
