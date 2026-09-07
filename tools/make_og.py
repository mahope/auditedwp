#!/usr/bin/env python3
"""Generate 1200x630 Open Graph images into site/images/og/ for the site, each
language front page and the main pages. Text is read from each page's <h1> and
meta description, so the images stay in sync with the copy.

    python tools/make_og.py
"""
import html as htmlmod
import re
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
OUT = SITE / "images" / "og"
W, H = 1200, 630
PAPER = (247, 248, 246)
INK = (22, 33, 28)
MUTED = (91, 102, 96)
LINE = (214, 219, 214)
ACCENT = (11, 110, 79)

PAGES = ["/", "/da/", "/de/", "/fr/",
         "/scan/", "/da/scan/", "/de/scan/", "/fr/scan/",
         "/pricing/", "/da/pricing/", "/de/pricing/", "/fr/pricing/",
         "/book/", "/da/book/", "/de/book/", "/fr/book/",
         "/checklist/", "/nis2-checklist/", "/eaa-checklist/", "/gdpr-fine-calculator/",
         "/blog/", "/pro/", "/store/", "/deskuptime/", "/transmute/", "/badge/",
         "/cookie-banner-check/", "/gdpr-compliance-check/", "/consent-mode-v2-check/",
         "/check-eu-compliance/", "/how-it-works/", "/compare/", "/cmp-comparison/", "/extension/", "/cli/", "/plugin/"]

FONT_DIRS = [Path("C:/Windows/Fonts"), Path("/usr/share/fonts"), Path("/System/Library/Fonts")]


def font(bold: bool, size: int) -> ImageFont.FreeTypeFont:
    names = ["segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"] if bold else ["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"]
    for d in FONT_DIRS:
        for n in names:
            p = d / n
            if p.exists():
                return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def text_of(fragment: str) -> str:
    t = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", htmlmod.unescape(t)).strip()


def page_text(url: str):
    p = SITE / url.lstrip("/") / "index.html"
    if not p.exists():
        return None
    h = p.read_text(encoding="utf-8")
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
    d = re.search(r'name="description" content="([^"]*)"', h)
    title = text_of(h1.group(1)) if h1 else text_of(re.search(r"<title>(.*?)</title>", h, re.S).group(1))
    desc = htmlmod.unescape(d.group(1)) if d else ""
    return title, desc


def wrap(draw, text, fnt, max_w, max_lines):
    words, lines, cur = text.split(), [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if draw.textlength(cand, font=fnt) <= max_w:
            cur = cand
        else:
            lines.append(cur)
            cur = w
            if len(lines) == max_lines:
                break
    if len(lines) < max_lines and cur:
        lines.append(cur)
    if len(lines) == max_lines and len(" ".join(lines)) < len(text):
        last = lines[-1]
        while draw.textlength(last + "…", font=fnt) > max_w and " " in last:
            last = last[: last.rfind(" ")]
        lines[-1] = last + "…"
    return lines


def mark(draw, x, y, size):
    unit = size / 32
    draw.rounded_rectangle([x, y, x + size, y + size], radius=7 * unit, fill=ACCENT)
    w = int(2.6 * unit)

    def P(px, py):
        return (x + px * unit, y + py * unit)

    def line(a, b):
        draw.line([P(*a), P(*b)], fill=PAPER, width=w)
        for pt in (a, b):
            cx, cy = P(*pt)
            draw.ellipse([cx - w / 2, cy - w / 2, cx + w / 2, cy + w / 2], fill=PAPER)

    line((9, 11), (16, 11)); line((9, 16), (15, 16)); line((9, 21), (16, 21))
    import math
    arc = [P(23 + 3 * math.cos(math.radians(a)), 18 + 3 * math.sin(math.radians(a))) for a in range(180, -1, -10)]
    pts = [P(20, 11)] + arc + [P(26, 11)]
    draw.line(pts, fill=PAPER, width=w, joint="curve")
    for pt in (P(20, 11), P(26, 11)):
        draw.ellipse([pt[0] - w / 2, pt[1] - w / 2, pt[0] + w / 2, pt[1] + w / 2], fill=PAPER)


def render(title: str, desc: str, brand: str) -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    mark(d, 80, 72, 56)
    d.text((152, 76), brand, font=font(True, 34), fill=INK)
    size = 64
    fnt = font(True, size)
    lines = wrap(d, title, fnt, W - 160, 3)
    while len(lines) == 3 and lines[-1].endswith("…") and size > 44:
        size -= 4
        fnt = font(True, size)
        lines = wrap(d, title, fnt, W - 160, 3)
    y = 190
    for ln in lines:
        d.text((80, y), ln, font=fnt, fill=INK)
        y += int(size * 1.18)
    if desc:
        f2 = font(False, 28)
        y += 18
        for ln in wrap(d, desc, f2, W - 160, 2):
            d.text((80, y), ln, font=f2, fill=MUTED)
            y += 40
    d.line([(80, H - 92), (W - 80, H - 92)], fill=LINE, width=2)
    d.text((80, H - 72), "eucomplypro.com", font=font(False, 26), fill=MUTED)
    tag = "Mads Holst Jensen · mahoje.dk"
    f3 = font(False, 26)
    d.text((W - 80 - d.textlength(tag, font=f3), H - 72), tag, font=f3, fill=MUTED)
    return img


def slug(url: str) -> str:
    s = url.strip("/")
    return s.replace("/", "-") if s else "home"


def brand_for(url: str) -> str:
    base = re.sub(r"^/(da|de|fr|es)/", "/", url)
    for k, v in (("/deskuptime/", "Deskuptime"), ("/transmute/", "Transmute"), ("/store/", "ComplianceDocs")):
        if base.startswith(k):
            return v
    return "EUComply"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    n = 0
    for url in PAGES:
        t = page_text(url)
        if not t:
            continue
        title, desc = t
        img = render(title, desc, brand_for(url))
        img.save(OUT / f"{slug(url)}.png", optimize=True)
        n += 1
    for lang in ("da", "de", "fr"):
        src = OUT / f"{lang}.png"
        if not src.exists():
            shutil.copy(OUT / "home.png", src)
    shutil.copy(OUT / "home.png", OUT / "en.png")
    shutil.copy(OUT / "home.png", SITE / "images" / "eucomply-og.png")
    print(f"og images: {n}")


if __name__ == "__main__":
    main()
