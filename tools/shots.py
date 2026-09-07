#!/usr/bin/env python3
"""Take responsive screenshots and check for horizontal overflow and the mobile menu.

    python tools/shots.py http://127.0.0.1:8765 /scan/ /blog/ ...     # base url + paths
    python tools/shots.py --out DIR --widths 360,768,1280 BASE PATHS...
Writes DIR/<slug>-<width>.png and prints overflow/menu results.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

args = [a for a in sys.argv[1:]]
out = Path("shots")
widths = [360, 768, 1280]
if "--out" in args:
    i = args.index("--out"); out = Path(args[i + 1]); del args[i : i + 2]
if "--widths" in args:
    i = args.index("--widths"); widths = [int(x) for x in args[i + 1].split(",")]; del args[i : i + 2]
full = "--full" in args
if full:
    args.remove("--full")
dark = "--dark" in args
if dark:
    args.remove("--dark")
base, paths = args[0].rstrip("/"), args[1:]
out.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch()
    problems = 0
    for path in paths:
        slug = (path.strip("/").replace("/", "-") or "home") + ("-dark" if dark else "")
        for w in widths:
            ctx = b.new_context(viewport={"width": w, "height": 800}, device_scale_factor=1,
                                color_scheme="dark" if dark else "light")
            pg = ctx.new_page()
            errors = []
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.goto(base + path, wait_until="load")
            pg.wait_for_timeout(600)
            sw = pg.evaluate("Math.max(document.documentElement.scrollWidth, document.body.scrollWidth)")
            iw = pg.evaluate("window.innerWidth")
            res = f"{path} @{w}: scrollWidth {sw}/{iw}"
            if sw > iw:
                problems += 1
                wide = pg.evaluate("""() => { const out=[]; for (const el of document.querySelectorAll('body *')) { const r=el.getBoundingClientRect(); if (r.right > window.innerWidth + 1 && r.width > 0) out.push(el.tagName.toLowerCase()+(el.className&&typeof el.className==='string'?'.'+el.className.split(' ').join('.'):'')+' '+Math.round(r.right)); if (out.length>6) break; } return out; }""")
                res += " OVERFLOW " + "; ".join(wide)
            if w <= 760:
                btn = pg.query_selector(".sh-toggle")
                if btn and btn.is_visible():
                    btn.click(); pg.wait_for_timeout(250)
                    open_ok = pg.evaluate("document.querySelector('.sh-toggle').getAttribute('aria-expanded')==='true' && getComputedStyle(document.getElementById('sh-menu')).display!=='none'")
                    pg.screenshot(path=str(out / f"{slug}-{w}-menu.png"))
                    pg.keyboard.press("Escape"); pg.wait_for_timeout(150)
                    closed_ok = pg.evaluate("document.querySelector('.sh-toggle').getAttribute('aria-expanded')==='false'")
                    res += f" menu open={open_ok} esc-close={closed_ok}"
                    if not (open_ok and closed_ok):
                        problems += 1
                else:
                    res += " NO-TOGGLE"; problems += 1
            pg.screenshot(path=str(out / f"{slug}-{w}.png"), full_page=full)
            if errors:
                res += " JSERR " + " | ".join(errors)[:200]
            print(res)
            ctx.close()
    b.close()
print(f"problems: {problems}")
sys.exit(1 if problems else 0)
