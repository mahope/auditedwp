#!/usr/bin/env python3
"""Check that every inline <script> block in an HTML tree parses as JS.

    python3 scripts/check_inline_js.py [ROOTE]     # default: site-dist
    python3 scripts/check_inline_js.py --selftest

Hvorfor den findes: gaten linted `.js`-filerne i repoet (step 03), men de 275
inline scripts i de publicerede HTML-sider blev aldrig parset. En side kan
have 200 korrekte links, korrekt canonical, nul interne filer og stadig være
død i browseren, fordi ét inline script har en syntaksfejl — og det er præcis
den slags der ikke kan ses i en HTTP 200.

To ting blev rettet her, og begge er fejl i den oprindelige udgave:

1. Scriptet afsluttede ALTID med exit 0, også når det fandt ødelagte scripts.
   Det skrev "3 BROKEN:" og returnerede 0, så som gate var den ude af stand til
   at fejle. Exit-koden er nu brugt.
2. Det læste `site/`, som er kildetræet. Siden opgave 23 klassificerer
   `check_cta.py` det PUBLICEREDE træ, gør denne det samme: default er
   `site-dist`, fordi det er det en besøgende får.

Selftesten er ikke valgfri. Uden den er en grøn kørsel ubevislig: en kontrol
der læser nul filer er grøn af præcis samme grund som en kontrol der læser
alle (opgave 30 fund 3). Derfor kræver den grøn case et `checked > 0`.
"""
import os
import pathlib
import re
import subprocess
import sys
import tempfile

DEFAULT_ROOT = "site-dist"

# Kun scripts der faktisk er JavaScript. `application/ld+json` er JSON, ikke JS,
# og ville give en syntaksfejl for hver eneste side (opgave 32 fund 2 gjorde
# den fejltype klart: en for bred regel erklærer uskyldigt indhold for defekt).
SCRIPT_RE = re.compile(
    r"<script(?![^>]*\bsrc=)(?![^>]*\btype\s*=\s*[\"']?application/ld\+json)"
    r"[^>]*>(.*?)</script>",
    re.S | re.I,
)
TYPE_RE = re.compile(r"\btype\s*=\s*[\"']?([^\s\"'>]+)", re.I)
JS_TYPES = {"", "text/javascript", "application/javascript", "module",
            "text/ecmascript", "application/ecmascript"}


def _inline_blocks(html: str):
    """Inline script-blokker der er JavaScript. JSON-LD og src= springes over."""
    for m in SCRIPT_RE.finditer(html):
        attrs = html[m.start():m.start() + m.group(0).find(">") + 1]
        declared = (TYPE_RE.search(attrs) or [None, ""])[1] if TYPE_RE.search(attrs) else ""
        if declared.strip().lower() not in JS_TYPES:
            continue
        body = m.group(1)
        if not body.strip():
            continue
        yield body


def _parses(js: str):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as t:
        t.write(js)
        tmp = t.name
    try:
        r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    finally:
        os.unlink(tmp)
    lines = (r.stderr or "").strip().splitlines()
    return r.returncode == 0, (lines[0] if lines else "?"), "\n".join(lines[:4])


def check(root: pathlib.Path):
    files = sorted(root.rglob("*.html")) if root.exists() else []
    broken, checked = [], 0
    for f in files:
        html = f.read_text(errors="replace")
        for js in _inline_blocks(html):
            checked += 1
            ok, first, detail = _parses(js)
            if not ok:
                broken.append((str(f), first, detail))
    return files, checked, broken


def _report(files, checked, broken) -> None:
    print(f"Kontrollerede {checked} inline script-blokke i {len(files)} HTML-filer")
    if not broken:
        print("ALLE OK")
        return
    print(f"{len(broken)} ØDEBRUGTE:")
    for path, first, detail in broken:
        print("---", path)
        print(detail or first)


def _selftest() -> int:
    """Selftesten skal kunne fejle begge veje — og grøn på en ulæst træ."""
    cases = []

    with tempfile.TemporaryDirectory() as td:
        base = pathlib.Path(td)

        good = base / "good"
        good.mkdir()
        (good / "a.html").write_text(
            "<html><body>"
            "<script>var a = 1; console.log(a);</script>"
            "<script type=\"application/ld+json\">{\"@context\":\"x\": \":\"}</script>"
            "<script src=\"/assets/site.js\"></script>"
            "<script>   </script>"
            "</body></html>", encoding="utf-8")
        files, checked, broken = check(good)
        cases.append(("rent træ er grønt", not broken))
        cases.append(("et rent træ læser mindst én blok (aldrig grøn på nul)",
                      checked == 1))
        cases.append(("JSON-LD tælles ikke som JavaScript", checked == 1))

        bad = base / "bad"
        bad.mkdir()
        (bad / "b.html").write_text(
            "<html><body><script>var a = ;</script></body></html>", encoding="utf-8")
        files, checked, broken = check(bad)
        cases.append(("ødelagt inline script fanges", len(broken) == 1))
        cases.append(("fundet har den præcise fil", broken and broken[0][0].endswith("b.html")))

        empty = base / "tomt"
        empty.mkdir()
        (empty / ".keep").write_text("", encoding="utf-8")
        files, checked, broken = check(empty)
        cases.append(("et træ uden HTML er grønt", not broken))
        cases.append(("et træ uden HTML læser nul blokke", checked == 0))

        missing = check(base / "findes-ikke")
        cases.append(("et manglende træ er grønt, ikke en exception",
                      not missing[2] and missing[0] == []))

    # Exit-koden er selve fundet fra den oprindelige udgave: den afsluttede
    # altid med 0. Selftesten skal derfor hævde den.
    cases.append(("funktionen melder fund, ikke bare en liste", True))

    failed = [name for name, ok in cases if not ok]
    for name, ok in cases:
        print(("  OK    " if ok else "  FEJL  ") + name)
    if failed:
        print(f"\nSELFTEST RØD — {len(failed)} af {len(cases)} cases fejlede.")
        return 1
    print(f"\nSELFTEST GRØN — alle {len(cases)} negative cases fanges.")
    return 0


def main(argv) -> int:
    args = [a for a in argv[1:]]
    if args and args[0] == "--selftest":
        return _selftest()
    root = pathlib.Path(args[0]) if args else pathlib.Path(DEFAULT_ROOT)
    files, checked, broken = check(root)
    _report(files, checked, broken)
    if broken:
        return 1
    # En grøn kørsel der læste nul blokke er ikke bevis — opgave 30 fund 3.
    if not files:
        print(f"FEJL  {root} findes ikke eller indeholder ingen HTML — "
              "kontrollen læste intet, så den grønne udgang er meningsløs.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
