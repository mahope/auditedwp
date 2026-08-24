#!/usr/bin/env python3
"""Switch all internal URLs from auditedwp.pages.dev to eucomplypro.com.

Rewrites .html, .xml (sitemap), .txt (robots), .json and .md files under site/.
Idempotent: running twice is a no-op. Use --revert to go back.
"""
import sys
from pathlib import Path

OLD = "auditedwp.pages.dev"
NEW = "eucomplypro.com"
ROOT = Path(__file__).resolve().parent.parent / "site"
EXTS = {".html", ".xml", ".txt", ".json", ".md"}

def main(revert=False):
    src, dst = (NEW, OLD) if revert else (OLD, NEW)
    changed = []
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in EXTS:
            continue
        text = p.read_text(encoding="utf-8")
        if src in text:
            p.write_text(text.replace(src, dst), encoding="utf-8")
            changed.append(str(p.relative_to(ROOT)))
    print(f"{'Reverted' if revert else 'Switched'} {src} -> {dst}: {len(changed)} files")
    for c in changed[:20]:
        print(" ", c)

if __name__ == "__main__":
    main(revert="--revert" in sys.argv)
