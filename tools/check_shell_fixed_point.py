#!/usr/bin/env python3
"""Port: en kørsel af skalen skal være nok — træet skal være et fast punkt.

    python3 tools/check_shell_fixed_point.py
    python3 tools/check_shell_fixed_point.py --selftest

Målt 28/9. Opgave 107 og 110 skrev begge, at skallen var idempotent, og begge
gange med målet "anden kørling: 0 ændringer". Målt på den ene side de arbejdede
på, holdt det. Målt på **træet** holdt det ikke:

    fra HEAD:  kørsel 1 → 33 sider ændret, kørsel 2 → 39, kørsel 3 → 0

Årsagen er ikke tilfældig. `article_meta()` skrev `Updated <git-dato>` i
`art-meta`, og næste kørsel læste **sit eget output** tilbage som sidens dato —
`find_date()` tager det første `<time>` i body, og efter en kørsel er det skalens
eget. Den nye dato flyttede siden i `prev_next()`'s sortering, så hele bloggens
forrige/næste-kæde skrev sig om, og de sider den nåede fik nye datoer, som så
fandt nye naboer. Kæden standsede først i tredje kørsel, og hver senere commit
der rørte `site/` ville have startet den forfra.

R1 kræver derfor det, planen ellers hævdede: kør den **rigtige** `process()` over
en kopi af hele det committede træ, og kræv at **hver** fil kommer tilbage byte
for byte. Porten kalder `apply_shell.process()` selv, så den måler kæden der
faktisk kører — ikke en genkonstruktion.

R2 dømmer den anden retning, og det er den der beviser at R1 ikke er tom: den
genskaber den gamle selvkørende dato og kræver at R1 så præcis den fejl den er
lavet til at se. R2 kræver desuden, som opgave 110 lærte, at mutationen
*faktisk* ændrede en side — `.replace()` giver ingen fejl, den giver siden
uændret tilbage, og så er casen død uden at se ud som død.

Selftest: to negative cases.
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
APPLY_SHELL = ROOT / "tools" / "apply_shell.py"


def load_shell():
    """Den rigtige skal fra `apply_shell.py` — aldrig en kopi her."""
    spec = importlib.util.spec_from_file_location("apply_shell_for_fixed_point", APPLY_SHELL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def page_paths(tree: pathlib.Path) -> list[pathlib.Path]:
    return [p for p in sorted(tree.rglob("*.html")) if "_partials" not in p.parts]


def run_shell(shell, tree: pathlib.Path) -> list[str]:
    """Kør den rigtige kæde over hele træet og saml de sider der flytter sig."""
    shell.SITE = tree
    shell.PARTIALS = tree / "_partials"
    shell.catalogue()
    found: list[str] = []
    for path in page_paths(tree):
        before = path.read_bytes()
        shell.process(path)
        after = path.read_bytes()
        if before != after:
            delta = _first_delta(before.decode("utf-8", "replace"),
                                 after.decode("utf-8", "replace"))
            found.append(f"R1 {path.relative_to(tree).as_posix()}: {_short(delta)}")
    return found


def _first_delta(a: str, b: str) -> str:
    la, lb = a.splitlines(), b.splitlines()
    for i, (x, y) in enumerate(zip(la, lb)):
        if x != y:
            return f"linje {i + 1} — {x.strip()[:70]} → {y.strip()[:70]}"
    return f"{len(la)} → {len(lb)} linjer"


def _short(s: str) -> str:
    return s.replace("\n", " ")


def legacy_article_meta(shell):
    """Den selvkørende dato fra før opgave 111, til R2.

    Datoen blev hver kørsel genberegnet som `max(git-seneste-commit, publiceret)`
    i stedet for at genbruge den skalen selv havde skrevet. Det er præcis den
    kæde der gjorde træet bevægeligt, så R2 genskaber den — ikke en opfundet
    fejl, men den kode der var i filen.
    """
    def article_meta(url, lang, rel, content):
        t = shell.I18N[lang]
        minutes = max(1, round(len(shell.text_of(content).split()) / 220))
        first, last = shell.GIT_DATES.get(rel, (shell.TODAY, shell.TODAY))
        published = shell.find_date(content) or first
        updated = max(last, published)
        label = t["updated"] if updated != published else t["published"]
        return (f'<p class="art-meta"><time datetime="{updated}">{label} {updated}</time>'
                f'<span>{minutes} {t["min_read"]}</span>'
                f'<button type="button" class="btn-ghost btn-sm share" data-copy-link>'
                f'{t["share"]}</button></p>')
    return article_meta


def tree_findings() -> list[str]:
    """R1: det committede træ skal være et fast punkt for den rigtige kæde."""
    shell = load_shell()
    with tempfile.TemporaryDirectory() as tmp:
        tree = pathlib.Path(tmp) / "site"
        shutil.copytree(SITE, tree)
        found = run_shell(shell, tree)
    if not found:
        pages = len(page_paths(SITE))
        print(f"R1 OK — {pages} sider, 0 ændret af én kørsel af den rigtige kæde")
    return found


def selftest_findings() -> list[str]:
    """R2: R1 skal se bevægelse, når træet bevæger sig.

    En port der siger "alt grønt" om en egenskab ingen har, er dødsvægten i en
    kvalitetsgate. Derfor dømmer R2 den modsatte retning: tag det frosne træ,
    tag **én** artikelside og fjern dens `art-meta`. Det er præcis den
    situation de 33 legacy-sider kom ind i: en side uden skrevet dato får en
    tildelt, flytter i `prev_next()`-sorteringen og trækker sin naboers
    forrige/næste-links med sig. R1 skal finde præcis den bevægelse.

    Og mutationen skal kunne lyve hvis den er død, så den måles to gange: at
    siden faktisk blev ændret, og at træet faktisk flyttede sig. `.replace()`
    giver ingen fejl, den giver siden uændret tilbage — det erfund fra opgave
    110, hvor en case mutationen ikke rørte ved.
    """
    found: list[str] = []
    shell = load_shell()
    with tempfile.TemporaryDirectory() as tmp:
        tree = pathlib.Path(tmp) / "site"
        shutil.copytree(SITE, tree)
        page = _pick_article(tree)
        if page is None:
            return ["R2: ingen artikelside med en art-meta at fjerne"]
        before = page.read_text(encoding="utf-8")
        stripped = META_FENCE.sub("", before, count=1)
        if stripped == before:
            return ["R2: mutationen fjernede intet — den er et stilhedende no-op, "
                    "så casen kan ikke lyve om R1"]
        page.write_text(stripped, encoding="utf-8")
        after_write = page.read_text(encoding="utf-8")
        if after_write != stripped:
            return ["R2: siden blev ikke skrevet, så mutationen døde på vejen"]

        moved = run_shell(shell, tree)
        if not moved:
            found.append("R2: træet flyttede sig ikke, selv om en artikelside mistede "
                         "sin art-meta — porten kan ikke se bevægelse")
        else:
            print(f"R2 OK — uden art-meta på {page.name} så R1 {len(moved)} sider flytte sig")
            print("     " + _short(moved[0]))
    return found


META_FENCE = re.compile(r"\s*<!--shell:meta-->.*?<!--/shell:meta-->", re.S)


def _pick_article(tree: pathlib.Path):
    for p in page_paths(tree):
        if '<!--shell:meta-->' in p.read_text(encoding="utf-8", errors="replace"):
            return p
    return None


def main() -> int:
    findings = selftest_findings() if "--selftest" in sys.argv else tree_findings()
    for f in findings:
        print(f, file=sys.stderr)
    if findings:
        print(f"FUND — {len(findings)} linjer", file=sys.stderr)
        return 1
    print("PORT GRØN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
