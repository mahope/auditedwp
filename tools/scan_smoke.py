#!/usr/bin/env python3
"""Submit a scan on the live /scan/ page and confirm results render under the CSP.

    python tools/scan_smoke.py [base_url] [target]
"""
import sys

from playwright.sync_api import sync_playwright

base = sys.argv[1] if len(sys.argv) > 1 else "https://eucomplypro.com"
target = sys.argv[2] if len(sys.argv) > 2 else "wordpress.org"
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 390, "height": 844})
    console = []
    pg.on("console", lambda m: console.append(f"{m.type}: {m.text}"))
    pg.on("pageerror", lambda e: console.append(f"pageerror: {e}"))
    pg.goto(base + "/scan/?url=" + target, wait_until="load")
    try:
        pg.wait_for_selector(".rcard", timeout=45000)
        cards = pg.locator(".rcard").count()
        score = pg.locator(".score .num").first.inner_text() if pg.locator(".score .num").count() else "-"
        print(f"scan ok: {cards} result cards, score {score}")
        pg.screenshot(path="scan-result.png", full_page=False)
        rc = 0
    except Exception as e:
        print("scan FAILED:", e)
        rc = 1
    csp = [c for c in console if "Content Security Policy" in c or "Refused to" in c]
    print("csp violations:", len(csp))
    for c in csp[:5]:
        print("  ", c[:200])
    for c in console:
        if c.startswith("pageerror"):
            print("  ", c[:200])
    b.close()
    sys.exit(rc or (1 if csp else 0))
