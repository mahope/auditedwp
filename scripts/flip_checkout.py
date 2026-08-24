#!/usr/bin/env python3
"""flip_checkout.py — sæt Lemon Squeezy checkout-URL ind på alle DevNotify-sider i ét hug.

Brug:
    python3 scripts/flip_checkout.py https://devnotify.lemonsqueezy.com/buy/xxxx

Gør på hver .html-fil under devnotify-site/:
1. Erstatter buy-knappen (#buy-btn, notify-formular + dens JS) med et direkte
   <a>-link til checkout-URL'en (rel="noopener", target="_blank").
2. Erstatter tekstlinks "#buy"-henvisninger der siger "get notified" osv. —
   de peger allerede på #buy, så de skal ikke røres.
3. Skriver CHECKOUT_URL ind i en kommentar øverst i index.html så det er synligt.

Idempotent: kør den igen med en ny URL, og den opdaterer alle links.
"""
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "devnotify-site"

# JS-blokken fra "// Buy button reveals" til slutningen af if(buyBtn&&notifyForm)-blokken
JS_BLOCK = re.compile(
    r"// Buy button reveals.*?\nif\(buyBtn&&notifyForm\)\{\s*.*?\n\}\n",
    re.DOTALL,
)

# subscribe-IIFE: refererer til notifyForm som er fjernet — skal også væk
SUBSCRIBE_BLOCK = re.compile(
    r"\(function\(\)\{\n  const form=notifyForm;.*?\n\}\)\(\);\n?",
    re.DOTALL,
)

METRICS_LINE = re.compile(r"const METRICS_URL='[^']*';\n")

FORM_BLOCK = re.compile(
    r'\s*<form id="notify-form".*?</form>',
    re.DOTALL,
)

BTN_BLOCK = re.compile(
    r'<button class="btn btn-primary" id="buy-btn"[^>]*>.*?</button>',
)


def flip(url: str) -> int:
    assert url.startswith("https://"), "checkout URL skal være https"
    changed = 0
    for html in SITE.rglob("*.html"):
        text = html.read_text()
        orig = text
        # 1. buy-knap: flip eller opdater eksisterende checkout-URL
        if 'id="buy-btn"' in text:
            if BTN_BLOCK.search(text):
                text = BTN_BLOCK.sub(
                    f'<a class="btn btn-primary" id="buy-btn" href="{url}" '
                    f'target="_blank" rel="noopener" '
                    f'aria-label="Buy DevNotify license for $19">Buy license — $19</a>',
                    text,
                )
                # 2. fjern formularen
                text = FORM_BLOCK.sub("", text)
                # 3. fjern JS-blokke (buy-toggle + subscribe-IIFE).
                # NB: METRICS-linjen BLIVER — bruges af visit/download-tælleren.
                text = JS_BLOCK.sub("", text)
                text = SUBSCRIBE_BLOCK.sub("", text)
            else:
                # allerede flippet — opdater URL'en hvis den er ændret
                text = re.sub(
                    r'(id="buy-btn" href=")https://[^"]+(")',
                    rf"\g<1>{url}\g<2>",
                    text,
                )
        # aria-label opdateres også på uflippede sider der refererer til notify
        text = text.replace(
            'aria-label="Get notified when DevNotify checkout opens"',
            f'aria-label="Buy DevNotify license for $19" data-checkout="{url}"',
        )
        if text != orig:
            html.write_text(text)
            changed += 1
            print(f"  opdateret: {html.relative_to(SITE)}")
    print(f"\n{changed} filer opdateret. Deploy nu: cd .. && ./deploy.sh devnotify-site")
    return changed


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    flip(sys.argv[1])
