#!/usr/bin/env python3
"""Saml den offentlige deploy-tre fra site/ ud fra en positivliste.

    python3 tools/build_public_tree.py                 # site/ -> site-dist/
    python3 tools/build_public_tree.py --out /tmp/pub --quiet

Kilde-træet i site/ er fuldt af interne ting — strategidokumenter, budget,
driftsscripts, forskningsnoter og et par af søskeprodukter. Cloudflare Pages
uploader hele mappeindholdet, så alt i site/ er offentligt tilgængeligt.
Derfor kopierer dette script kun det, der er godkendt som offentligt, og
lader resten blive i repoet.

Exit code 1 hvis en godkendt sti mangler i kilden, så en slettet side ikke
kan forsvinde lydløst ud af det publicerede træ.
"""
import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

# Topniveau-filer der er en del af det publicerede websted.
PUBLIC_FILES = (
    "_headers",
    "_redirects",
    "404.html",
    "apple-touch-icon.png",
    "favicon.ico",
    "favicon.svg",
    "humans.txt",
    "icon-192.png",
    "icon-512.png",
    "icon-512-maskable.png",
    "index.html",
    "llms-full.txt",
    "llms.txt",
    "robots.txt",
    "search-index.json",
    "site.webmanifest",
    "sitemap.xml",
    "update.json",
)

# Topniveau-mapper der er en del af det publicerede websted.
PUBLIC_DIRS = (
    ".well-known",
    "_partials",
    "assets",
    "badge",
    "blog",
    "book",
    "check-eu-compliance",
    "checklist",
    "cli",
    "cmp-comparison",
    "compare",
    "consent-mode-v2-check",
    "cookie-banner-check",
    "cookie-policy-generator",
    "da",
    "de",
    "deskuptime",
    "devnotify",
    "downloads",
    "eaa-checklist",
    "es",
    "extension",
    "fr",
    "gdpr-compliance-check",
    "gdpr-fine-calculator",
    "gdpr-scanner-free",
    "guides",
    "how-it-works",
    "images",
    "impressum-generator",
    "nis2-checklist",
    "plugin",
    "privacy",
    "privacy-policy-generator",
    "pricing",
    "pro",
    "regex",
    "refund-policy-generator",
    "sample",
    "scan",
    "search",
    "shared",
    "store",
    "template",
    "terms",
    "terms-of-service-generator",
    "tools",
    "transmute",
    "vs",
)

# Stier der skal overleve uændret. Hvis en af dem mangler i kilden, stopper
# scriptet, så en tabt side aldrig udgiver stilt.
REQUIRED = (
    "index.html",
    "pro/index.html",
    "pricing/index.html",
    "da/pricing/index.html",
    "de/pricing/index.html",
    "fr/pricing/index.html",
    "da/pro/index.html",
    "de/pro/index.html",
    "fr/pro/index.html",
    "scan/index.html",
    "plugin/index.html",
    "privacy/index.html",
    "assets/site.css",
    "assets/site.js",
    "sitemap.xml",
    "robots.txt",
    "_headers",
    "_redirects",
)

# Også inde i en godkendt mappe er der interne filer. Navnene her er nævnt
# eksplicit, så det er læsbart hvad der er holdt ude.
INTERNAL_SUFFIXES = (".md", ".sh", ".py", ".toml", ".log", ".bak", ".env")
INTERNAL_NAMES = (".DS_Store", ".gitignore", ".gitattributes", "thumbs.db")
INTERNAL_PARTS = (
    "POSTS",
    "ops",
    "deliverables",
    "gumroad",
    "__pycache__",
    "node_modules",
    ".deploy-staging",
)


def is_internal(path: Path, root: Path):
    relative = path.relative_to(root)
    for part in relative.parts[:-1]:
        if part in INTERNAL_PARTS or part.startswith(".env"):
            return f"intern mappe ({part})"
    name = path.name
    if name in INTERNAL_NAMES:
        return "intern filnavn"
    if name.startswith(".env"):
        return "miljøfil"
    lowered = name.lower()
    for suffix in INTERNAL_SUFFIXES:
        if lowered.endswith(suffix):
            return f"intern endelse ({suffix})"
    return None


def collect(source: Path) -> tuple[list[Path], list[tuple[Path, str]]]:
    keep: list[Path] = []
    drop: list[tuple[Path, str]] = []
    for name in PUBLIC_FILES:
        path = source / name
        if path.is_file():
            keep.append(path)
    for name in PUBLIC_DIRS:
        base = source / name
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_symlink():
                drop.append((path, "symlink"))
            elif path.is_file():
                reason = is_internal(path, source)
                (drop.append((path, reason)) if reason else keep.append(path))
    return keep, drop


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", default=str(SITE))
    parser.add_argument("--out", default=str(ROOT / "site-dist"))
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    source = Path(args.site).resolve()
    target = Path(args.out).resolve()

    if not source.is_dir():
        print(f"FEJL: kildemappe findes ikke: {source}")
        return 1

    keep, drop = collect(source)
    relative = {path.relative_to(source).as_posix() for path in keep}

    missing = [path for path in REQUIRED if path not in relative]
    if missing:
        for path in missing:
            print(f"FEJL: godkendt sti mangler i kilden: {path}")
        return 1

    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)

    for path in keep:
        destination = target / path.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)

    if args.quiet:
        print(f"{len(keep)} offentlige filer -> {target}")
        return 0

    known = set(PUBLIC_FILES) | set(PUBLIC_DIRS)
    unknown = sorted(
        entry.name
        for entry in source.iterdir()
        if entry.name not in known and entry.name not in {".DS_Store", ".git", ".gitignore"}
    )

    print(f"Kilde:  {source}")
    print(f"Output: {target}")
    print(f"{len(keep)} filer kopieret, {len(drop)} interne udeladt")
    if unknown:
        print("  Ikke på listen, holdt ude — tilføj dem i PUBLIC_FILES/PUBLIC_DIRS hvis de er offentlige:")
        print(f"    {', '.join(unknown)}")
    grouped: dict[str, list[str]] = {}
    for path, reason in drop:
        grouped.setdefault(reason, []).append(path.relative_to(source).as_posix())
    for reason in sorted(grouped):
        names = grouped[reason]
        shown = ", ".join(sorted(names)[:6])
        more = f" (+{len(names) - 6} flere)" if len(names) > 6 else ""
        print(f"  holdt ude — {reason}: {shown}{more}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
