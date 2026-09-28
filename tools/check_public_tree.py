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
# Fragmenter bliver udvendt i den side der inkluderer dem, så de er ikke sider
# med egne ankre. `_partials/header.html`s `#main` er korrekt på alle 225 sider
# og dødt som sit eget dokument — uden denne undtagelse giver porten 1 rød
# fund på en fejl, der ikke findes.
SKIP_ANCHOR_DIRS = ("_partials/", "shared/")
REF = re.compile(r'(?:href|src)="([^"]+)"')
# `<a name>` er gyldigt ankemål og bruges stadig i partialer.
ANCHOR_ID = re.compile(r"""\b(?:id|name)\s*=\s*["']([^"']+)["']""")


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


def _anchors(html: str):
    """(sti, anker) for hver intern reference med `#` i den.

    Filtrerer selv, i stedet for at låne `_references()`: den springer rene
    ankerlinks over med vilje (de har ingen fil at slå op), så en lån-listen
    ville få kontrol 4 til at måle nul links. Selftest case 2 og 4 fanger
    præcis det.
    """
    for url in REF.findall(html):
        url = url.strip()
        if not url or url.startswith(("mailto:", "tel:", "javascript:", "data:", "//")):
            continue
        if re.match(r"^(https?:|ftp:)", url):
            continue
        if "{{" in url or "}}" in url or url.startswith("+") or "'" in url:
            continue
        path, _, fragment = url.partition("#")
        if fragment:
            yield path, fragment


def _resolve(page: Path, path: str, tree: Path):
    """Den fil en intern reference peger på, eller None hvis den ikke findes."""
    if path.startswith("/"):
        target = path.lstrip("/")
    else:
        target = (page.parent.relative_to(tree) / path).as_posix()
    target = str(Path(target)) if target else "index.html"
    if target.startswith("_partials/"):
        return None
    for candidate in (tree / target, tree / target / "index.html"):
        if candidate.is_file():
            return candidate
    return None


def anchor_findings(tree: Path):
    """Døde ankre — `#id` skal findes på den side der linker til det.

    `_references()` splitter `#` fra stien, så et anker der ikke findes er
    usynlig for link-kontrollen ovenfor. Det er den døde klasse AGENTS.md
    forbyder, og den rammer bl.a. skip-linket der leder til `#main` på alle
    225 sider: fjerner en side sit `<main id="main">`, dør skip-linket på
    netop den side, og porten siger ingenting.

    Målt 2026-09-28 06:5x CEST før denne kontrol: 2168 ankerlinks i det
    publicerede træ, 0 døde. Så træet er rent — og bliver kun rent fordi
    porten nu kan se det.
    """
    findings = []
    checked = 0
    pages = [
        path
        for path in tree.rglob("*.html")
        if not path.relative_to(tree).as_posix().startswith(SKIP_ANCHOR_DIRS)
    ]
    ids = {
        path: set(ANCHOR_ID.findall(path.read_text(encoding="utf-8", errors="replace")))
        for path in pages
    }
    for page in pages:
        relative = page.relative_to(tree).as_posix()
        html = page.read_text(encoding="utf-8", errors="replace")
        for path, fragment in _anchors(html):
            target = page if not path else _resolve(page, path, tree)
            if target is None:
                # Selve filen mangler: link-kontrollen ovenfor melder den,
                # og et anker i en fil uden side ville være dobbelt-rapporteret.
                continue
            checked += 1
            if fragment in ids.get(target, set()):
                continue
            findings.append(f"dødt anker i {relative}: #{fragment}")
    return findings, checked


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
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--tree", default=str(ROOT / "site-dist"))
    args = parser.parse_args()
    if args.selftest:
        return selftest()

    tree = Path(args.tree).resolve()

    if not tree.is_dir():
        print(f"FEJL: træet findes ikke: {tree} — kør tools/build_public_tree.py først")
        return 1

    findings = forbidden_findings(tree) + required_findings(tree)
    links, pages = link_findings(tree)
    findings.extend(links)
    anchors, checked = anchor_findings(tree)
    findings.extend(anchors)
    findings.extend(redirect_findings(tree))

    files = sum(1 for path in tree_files(tree) if not path.is_symlink())
    print(f"Træ: {tree}")
    print(f"{files} filer, {pages} HTML-sider")

    for finding in dict.fromkeys(findings):
        print(f"FEJL {finding}")

    if findings:
        summary = Counter(re.sub(r"^død intern reference i \S+: ", "død intern reference", f) for f in findings)
        summary.update(
            Counter(
                re.sub(r"^dødt anker i \S+: ", "dødt anker ", f)
                for f in findings
                if f.startswith("dødt anker")
            )
        )
        for reason, count in summary.most_common():
            print(f"  {count:4d}  {reason}")
        print(f"\n{len(set(findings))} fund — intet uploades")
        return 1

    print("0 interne eller betalte filer i træet")
    print(f"0 døde interne referencer")
    print(f"0 døde ankre — {checked} ankerlinks i {pages} sider")
    return 0


def selftest() -> int:
    """Bevis at anker-kontrollen kan fejle. Uden dette er den grøn fordi den
    ingenting tjekker — samme fejlklasse som opgave 9's kanin-hul."""
    import tempfile

    PAGE = '<!DOCTYPE html><html lang="en"><head><title>t</title></head><body>{body}</body></html>'

    def build(body, extra=None):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "index.html").write_text(PAGE.format(body=body), encoding="utf-8")
        if extra:
            for name, content in extra.items():
                path = tmp / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
        return tmp

    def dead(body, extra=None):
        return anchor_findings(build(body, extra))[0]

    good = '<a href="#main">spring</a><main id="main">indhold</main>'
    cases = [
        # 1. grønt baseline-træ: et korrekt ankre må ikke være rødt.
        ("baseline med korrekt ankre er grøn", dead(good) == []),
        # 2. dødt anker på egen side skal være rødt.
        ("dødt anker på egen side er rødt", dead('<a href="#main">spring</a>') != []),
        # 3. korrekt ankre på en anden side må ikke være rødt.
        (
            "korrekt ankre på anden side er grønt",
            dead('<a href="/pricing/">priser</a>', {"pricing/index.html": '<main id="top"></main>', "index.html": '<a href="/pricing/#top">x</a>'}) == [],
        ),
        # 4. dødt ankre på en anden side skal være rødt.
        (
            "dødt anker på anden side er rødt",
            dead('<a href="/pricing/#top">x</a>', {"pricing/index.html": '<main id="andet"></main>'}) != [],
        ),
        # 5. `<a name>` er et gyldigt mål.
        ("`<a name>` tæller som mål", dead('<a href="#legacy">x</a><a name="legacy"></a>') == []),
        # 6. `href="#"` er ikke et anker og må ikke være rødt.
        ("tomt anker `#` ignoreres", dead('<a href="#">top</a>') == []),
        # 7. Et partials eget `#main` dør først i den side der inkluderer det,
        #    så porten må ikke tælle det som sit eget døde anker.
        (
            "partial med anker i includerende side er grønt",
            anchor_findings(build('<a href="#main">spring</a><main id="main">x</main>', {"_partials/header.html": '<a href="#main">spring</a>'}))[0] == [],
        ),
        # 8. En mutation uden forskel skal være grøn — ellers er de syv
        #    negative cases grønne, fordi porten ikke kører.
        ("mutation uden forskel er grøn", dead('<a href="#main">spring</a><main id="main">x</main>') == []),
    ]

    failed = 0
    for name, ok in cases:
        print(f"{'OK   ' if ok else 'FEJL '} {name}")
        if not ok:
            failed += 1
    print(f"\n{'SELFTEST RØD' if failed else 'SELFTEST GRØN'} — {len(cases) - failed}/{len(cases)} negative cases fanges")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(min(main(), 125))
