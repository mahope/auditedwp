#!/usr/bin/env python3
"""Smoke-test det byggede offentlige deploy-træ før det uploades.

    python3 tools/check_public_tree.py                  # site-dist/
    python3 tools/check_public_tree.py --tree site      # kilden, kun til sammenligning

Tjekker tre ting og fejler med exit 1 ved det første brud:

  1. Ingen interne eller betalte filer i træet — interne dokumenter,
     scripts, forskningsnoter, driftsfiler eller credentials.
  2. Alle offentlige nøglesider og assets findes.
  3. Enhver intern reference i HTML peger på en fil, der findes, så en
     udeladt fil ikke efterlader døde links.

Exit code er antallet af brud, som i øvrigt.
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Mønstre der aldrig må ligge i det publicerede træ.
FORBIDDEN_SUFFIXES = (".md", ".sh", ".py", ".toml", ".log", ".bak", ".pdf~", ".sql", ".key", ".pem")
FORBIDDEN_NAMES = (".env", ".gitignore", ".gitattributes", ".DS_Store", "id_rsa", "credentials")
FORBIDDEN_NAME_HINTS = ("secret", "credential", "password", "passwd", "apikey", "api-key", "-kv", "private")
FORBIDDEN_PARTS = (
    ".git",
    ".env",
    "POSTS",
    "ops",
    "deliverables",
    "gumroad",
    "__pycache__",
    "node_modules",
    ".deploy-staging",
    "paid",
    "secrets",
)

# Sider og assets der altid skal være med i en udgivelse.
REQUIRED = (
    "index.html",
    "404.html",
    "pro/index.html",
    "pricing/index.html",
    "da/pro/index.html",
    "da/pricing/index.html",
    "de/pro/index.html",
    "de/pricing/index.html",
    "fr/pro/index.html",
    "fr/pricing/index.html",
    "scan/index.html",
    "sample/index.html",
    "plugin/index.html",
    "privacy/index.html",
    "assets/site.css",
    "assets/site.js",
    "robots.txt",
    "sitemap.xml",
    "_headers",
    "_redirects",
)

# Dele af kilden der aldrig skal udgives, uanset indhold.
BLOCKED_SOURCE_TREES = ("POSTS", "ops", "deliverables", "gumroad")

SKIP_HTML = ("404.html", "shared/live-check-widget.html")
REF = re.compile(r'(?:href|src)="([^"]+)"')


def tree_files(tree: Path):
    for path in sorted(tree.rglob("*")):
        if path.is_symlink():
            yield path
        elif path.is_file():
            yield path


def forbidden_findings(tree: Path):
    findings = []
    for path in tree_files(tree):
        relative = path.relative_to(tree).as_posix()
        if path.is_symlink():
            findings.append(f"symlink i publiceret træ: {relative}")
            continue
        parts = relative.split("/")
        for part in parts[:-1]:
            if part in FORBIDDEN_PARTS or part.startswith(".env"):
                findings.append(f"intern mappe i publiceret træ: {relative}")
                break
        else:
            name = path.name
            if name in FORBIDDEN_NAMES or name.startswith(".env"):
                findings.append(f"intern/credential-fil i publiceret træ: {relative}")
                continue
            lowered = name.lower()
            for hint in FORBIDDEN_NAME_HINTS:
                if hint in lowered:
                    findings.append(f"filnavn ligner credentials ({hint}): {relative}")
                    break
            for suffix in FORBIDDEN_SUFFIXES:
                if lowered.endswith(suffix):
                    findings.append(f"intern endelse ({suffix}) i publiceret træ: {relative}")
                    break
    return findings


def required_findings(tree: Path):
    return [f"offentlig sti mangler i træet: {path}" for path in REQUIRED if not (tree / path).is_file()]


def _references(html: str):
    for raw in REF.findall(html):
        url = raw.strip()
        if not url or url.startswith(("#", "mailto:", "tel:", "javascript:", "data:", "//")):
            continue
        if re.match(r"^(https?:|ftp:)", url):
            continue
        if "{{" in url or "}}" in url or url.startswith("+") or "'" in url:
            continue
        path = url.split("#")[0].split("?")[0]
        if path:
            yield path


def link_findings(tree: Path):
    findings = []
    pages = [
        path
        for path in tree.rglob("*.html")
        if path.relative_to(tree).as_posix() not in SKIP_HTML
    ]
    for page in pages:
        relative = page.relative_to(tree).as_posix()
        html = page.read_text(encoding="utf-8", errors="replace")
        for url in _references(html):
            if url.startswith("/"):
                target = url.lstrip("/")
            else:
                target = (page.parent.relative_to(tree) / url).as_posix()
            target = str(Path(target)) if target else "index.html"
            if target.startswith("_partials/"):
                continue
            candidates = (tree / target, tree / target / "index.html")
            if not any(candidate.is_file() for candidate in candidates):
                findings.append(f"død intern reference i {relative}: {url}")
    return findings, len(pages)


def redirect_findings(tree: Path):
    findings = []
    redirects = tree / "_redirects"
    if not redirects.is_file():
        return findings
    for number, line in enumerate(redirects.read_text(encoding="utf-8").splitlines(), 1):
        parts = line.split()
        if len(parts) < 2 or parts[0].startswith("#"):
            continue
        target = parts[1].split("#")[0].split("?")[0]
        if not target.startswith("/") or target.endswith("/"):
            continue
        if not (tree / target.lstrip("/")).is_file():
            findings.append(f"død redirect i _redirects linje {number}: {parts[0]} -> {parts[1]}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tree", default=str(ROOT / "site-dist"))
    args = parser.parse_args()
    tree = Path(args.tree).resolve()

    if not tree.is_dir():
        print(f"FEJL: træet findes ikke: {tree} — kør tools/build_public_tree.py først")
        return 1

    findings = forbidden_findings(tree) + required_findings(tree)
    links, pages = link_findings(tree)
    findings.extend(links)
    findings.extend(redirect_findings(tree))

    files = sum(1 for path in tree_files(tree) if not path.is_symlink())
    print(f"Træ: {tree}")
    print(f"{files} filer, {pages} HTML-sider")

    for finding in dict.fromkeys(findings):
        print(f"FEJL {finding}")

    if findings:
        summary = Counter(re.sub(r"^død intern reference i \S+: ", "død intern reference", f) for f in findings)
        for reason, count in summary.most_common():
            print(f"  {count:4d}  {reason}")
        print(f"\n{len(set(findings))} fund — intet uploades")
        return 1

    print("0 interne eller betalte filer i træet")
    print("0 døde interne referencer")
    return 0


if __name__ == "__main__":
    sys.exit(min(main(), 125))
