#!/usr/bin/env python3
"""Generate the favicon set for eucomplypro.com: favicon.svg, favicon.ico,
apple-touch-icon.png, icon-192.png, icon-512.png and site.webmanifest.
A rounded square in the accent colour with a lined "EU" mark, matching the
inline brand mark in site/_partials/header.html.

    python tools/make_icons.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
ACCENT = (11, 110, 79)
PAPER = (247, 248, 246)

SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
<rect width="32" height="32" rx="7" fill="#0b6e4f"/>
<path d="M9 11h7M9 16h6M9 21h7M20 11v7a3 3 0 0 0 6 0v-7" fill="none" stroke="#f7f8f6" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


def render(size: int, padding: float = 0.0) -> Image.Image:
    """Draw the mark at `size` px with optional padding ratio (for maskable icons)."""
    s = 8  # supersample
    n = size * s
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = int(n * padding)
    box = n - 2 * pad
    unit = box / 32
    r = 7 * unit
    d.rounded_rectangle([pad, pad, pad + box, pad + box], radius=r, fill=ACCENT)
    w = 2.6 * unit

    def P(x, y):
        return (pad + x * unit, pad + y * unit)

    def line(a, b):
        d.line([P(*a), P(*b)], fill=PAPER, width=int(w))
        for pt in (a, b):
            x, y = P(*pt)
            d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=PAPER)

    line((9, 11), (16, 11))
    line((9, 16), (15, 16))
    line((9, 21), (16, 21))
    # U: two stems and a half circle
    import math
    arc = [P(23 + 3 * math.cos(math.radians(a)), 18 + 3 * math.sin(math.radians(a))) for a in range(180, -1, -10)]
    pts = [P(20, 11)] + arc + [P(26, 11)]
    d.line(pts, fill=PAPER, width=int(w), joint="curve")
    for pt in (P(20, 11), P(26, 11)):
        d.ellipse([pt[0] - w / 2, pt[1] - w / 2, pt[0] + w / 2, pt[1] + w / 2], fill=PAPER)
    return img.resize((size, size), Image.LANCZOS)


def main():
    (SITE / "favicon.svg").write_text(SVG, encoding="utf-8")
    render(180, 0.0).save(SITE / "apple-touch-icon.png")
    render(192, 0.0).save(SITE / "icon-192.png")
    render(512, 0.0).save(SITE / "icon-512.png")
    render(512, 0.1).save(SITE / "icon-512-maskable.png")
    ico = render(32)
    ico.save(SITE / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    (SITE / "site.webmanifest").write_text(
        '{\n  "name": "EUComply",\n  "short_name": "EUComply",\n'
        '  "description": "Free compliance scan for websites with visitors in the EU.",\n'
        '  "start_url": "/",\n  "display": "browser",\n  "background_color": "#f7f8f6",\n  "theme_color": "#0b6e4f",\n'
        '  "icons": [\n'
        '    {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},\n'
        '    {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},\n'
        '    {"src": "/icon-512-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}\n'
        '  ]\n}\n', encoding="utf-8")
    print("icons written")


if __name__ == "__main__":
    main()
