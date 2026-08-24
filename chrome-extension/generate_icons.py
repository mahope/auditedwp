"""Generate DevNotify Chrome extension icons — simple colored bell-style icon."""
from PIL import Image, ImageDraw
import os, math

SIZES = [16, 48, 128]
COLOR = (59, 130, 246)  # Blue-500
ACCENT = (34, 197, 94)   # Green-500 (for the dot)
OUT_DIR = os.path.join(os.path.dirname(__file__), 'icons')

def make_icon(size):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    r = int(size * 0.42)

    # Bell body
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=COLOR + (255,))

    # Notification dot (green circle top-right)
    dot_r = max(3, int(size * 0.14))
    dot_cx = cx + int(size * 0.22)
    dot_cy = cy - int(size * 0.22)
    draw.ellipse([dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r], fill=ACCENT + (255,))

    # Save
    path = os.path.join(OUT_DIR, f'icon-{size}.png')
    img.save(path, 'PNG')
    print(f"  {path}  ({size}x{size})")

if __name__ == '__main__':
    for s in SIZES:
        make_icon(s)
    print("Done — 3 icons created")