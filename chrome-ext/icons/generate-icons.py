"""Generate EUComply Chrome extension icons (16, 48, 128 px)."""
from PIL import Image, ImageDraw
import os

def make_icon(size):
    img = Image.new('RGBA', (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    
    # Fill circle as background
    cx = cy = size // 2
    r = size // 2 - max(1, size // 16)
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(40, 104, 208, 255))
    
    # White check mark - draw as two thick lines
    # V shape
    lw = max(2, size // 10)
    r2 = int(r * 0.55)
    
    # Left arm of V
    x1, y1 = cx - r2, cy
    xm, ym = cx - r2//3, cy + r2//2
    x2, y2 = cx + r2, cy - r2//2
    
    draw.line([(x1, y1), (xm, ym)], fill=(255,255,255,255), width=lw)
    draw.line([(xm, ym), (x2, y2)], fill=(255,255,255,255), width=lw)
    
    out_path = os.path.join(os.path.dirname(__file__), f'icon{size}.png')
    img.save(out_path, 'PNG')
    print(f"Saved {out_path} ({size}x{size})")

for s in (16, 48, 128):
    make_icon(s)