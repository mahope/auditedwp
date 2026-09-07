#!/usr/bin/env python3
"""Insert an ebook CTA box before the keep-reading nav (or </body>) on all
blog guide pages, so every guide cross-sells the $14.99 ebook."""
import glob, re, os

CTA = '''
<aside class="book-cta" style="margin:32px 0;padding:20px 22px;border:1px solid #d0d8e0;border-left:4px solid #2868d0;border-radius:10px;background:#f8faff">
  <strong style="font-size:16px">📖 The Practical Guide to EU Compliance 2026</strong>
  <p style="margin:8px 0;font-size:14px;color:#4a5a6a">Everything in this guide — plus GDPR, NIS2, DORA and EAA checklists, templates and a 90-day action plan — in one 24-page handbook. Instant PDF download.</p>
  <p style="margin:0"><a href="/book/" style="color:#2868d0;font-weight:600;text-decoration:none">Get the ebook — $14.99 →</a></p>
</aside>
'''

count = 0
for path in sorted(glob.glob('/Users/madsholstjensen/hermes-ceo/site/blog/*/index.html')):
    with open(path) as f:
        html = f.read()
    if 'book-cta' in html:
        continue  # idempotent
    marker = '<nav class="keep-reading"'
    if marker in html:
        html = html.replace(marker, CTA + '\n' + marker, 1)
    else:
        html = html.replace('</body>', CTA + '\n</body>', 1)
    with open(path, 'w') as f:
        f.write(html)
    count += 1

print(f"Inserted book CTA into {count} blog pages")
