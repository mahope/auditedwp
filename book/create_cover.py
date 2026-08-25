"""Generate a professional book cover for KDP ebook."""
from PIL import Image, ImageDraw, ImageFont
import os

# KDP Kindle ebook cover: 6x9 inches (virtual) = 1600x2400 at ~267 DPI
WIDTH, HEIGHT = 1600, 2400

# Create image with gradient background
img = Image.new('RGB', (WIDTH, HEIGHT), color=(11, 26, 42))
draw = ImageDraw.Draw(img)

# Draw gradient overlay (bottom lighter)
for y in range(HEIGHT):
    factor = y / HEIGHT
    r = int(11 + factor * 30)
    g = int(26 + factor * 25)
    b = int(42 + factor * 20)
    draw.rectangle((0, y, WIDTH, y), fill=(r, g, b))

# Draw accent line (top)
accent_color = (40, 104, 208)  # #2868d0
draw.rectangle((0, 0, WIDTH, 8), fill=accent_color)

# Title text
title = "The Website\nCompliance\nHandbook 2026"

# Use a default font (PIL's built-in)
try:
    title_font = ImageFont.truetype("/Library/Fonts/Arial.ttf", 96)
except:
    title_font = ImageFont.load_default()

try:
    sub_font = ImageFont.truetype("/Library/Fonts/Arial.ttf", 36)
except:
    sub_font = ImageFont.load_default()

try:
    body_font = ImageFont.truetype("/Library/Fonts/Arial.ttf", 24)
except:
    body_font = ImageFont.load_default()

# Title positioning (centered, upper area)
title_y_start = 480
for line_text in title.split('\n'):
    # Get bbox
    bbox = draw.textbbox((0, 0), line_text, font=title_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (WIDTH - tw) // 2
    draw.text((x, title_y_start), line_text, fill=(255, 255, 255), font=title_font)
    title_y_start += th + 12

# Subtitle
subtitle = "GDPR, ePrivacy, NIS2 & Accessibility"
bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
sw = bbox[2] - bbox[0]
draw.text(((WIDTH - sw) // 2, title_y_start + 40), subtitle, fill=(160, 180, 200), font=sub_font)

# Subtitle 2
subtitle2 = "for European Small Business Owners"
bbox = draw.textbbox((0, 0), subtitle2, font=sub_font)
sw = bbox[2] - bbox[0]
draw.text(((WIDTH - sw) // 2, title_y_start + 90), subtitle2, fill=(160, 180, 200), font=sub_font)

# Bottom accent bar
draw.rectangle((0, HEIGHT-80, WIDTH, HEIGHT), fill=accent_color)

# Bottom text
bottom_text = "A Practical Guide to EU Website Compliance"
bbox = draw.textbbox((0, 0), bottom_text, font=body_font)
bw = bbox[2] - bbox[0]
draw.text(((WIDTH - bw) // 2, HEIGHT - 65), bottom_text, fill=(200, 210, 220), font=body_font)

# Save
output_path = "book/cover.png"
img.save(output_path)
print(f"Cover saved: {output_path}")
print(f"Dimensions: {WIDTH}x{HEIGHT}")

# Also create a smaller preview
img_thumb = img.resize((400, 600))
thumb_path = "book/cover-thumb.png"
img_thumb.save(thumb_path)
print(f"Thumbnail saved: {thumb_path}")