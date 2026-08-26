#!/usr/bin/env python3
"""Extract inline <script> blocks (no src) from every HTML file and check they parse as JS."""
import re, subprocess, sys, json, tempfile, os, pathlib

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'site')
files = sorted(root.rglob('*.html'))
broken = []
checked = 0
for f in files:
    html = f.read_text(errors='replace')
    # inline scripts only
    for m in re.finditer(r'<script(?![^>]*\bsrc=)(?![^>]*ld\+json)[^>]*>(.*?)</script>', html, re.S | re.I):
        js = m.group(1)
        if not js.strip():
            continue
        checked += 1
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t:
            t.write(js); tmp = t.name
        r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
        os.unlink(tmp)
        if r.returncode != 0:
            first = r.stderr.strip().splitlines()
            broken.append((str(f), first[0] if first else '?', '\n'.join(first[:4])))

print(f"Checked {checked} inline script blocks in {len(files)} HTML files")
if not broken:
    print("ALL OK")
else:
    print(f"{len(broken)} BROKEN:")
    for b in broken:
        print('---', b[0])
        print(b[2])
