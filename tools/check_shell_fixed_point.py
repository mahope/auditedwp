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
tager det frosne træ, fjerner **én** artikelsides `art-meta` og kræver at R1 så
præcis den bevægelse den er lavet til at se — den situation de 33 legacy-sider
kom ind i. R2 kræver desuden, som opgave 110 lærte, at mutationen *faktisk*
ændrede en side — `.replace()` giver ingen fejl, den giver siden uændret
tilbage, og så er casen død uden at se ud som død.

Iteration 112 fandt her en fejl, porten ikke havde. Opgave 111 lagde
`frozen = SHELL_TIME.search(content)` ind i `article_meta()` for at genbruge
datoen skalen selv skrev. Det virker ikke: `content` er `html` **efter**
`SHELL_FENCE.sub("", html)`, så den `art-meta` der skulle læses, var allerede
riveret væk, og søgningen ramte aldrig sit mål. R1 var grøn på papiret og
`GATE GRØN` stod i planen — fordi porten dengang kun blev kørt lokalt med et
system-`python3` der var for gammel til at starte (`TypeError` på `str | None`),
så resultatet var fra et træ, der var kørt mange gange i forvejen. Først CI,
på en frisk udtjekning af HEAD, sagde `FEJL tools/check_shell_fixed_point.py`
med 99 bevægelige sider, og sitet holdt op med at deploye. R1 var altså ikke
død, den var aldrig kørt.

**Og R1 kørte en kæde, der ikke er den der kører.** Den sagde
`R1 OK — 230 sider, 0 ændret af én kørsel af den rigtige kæde`, men
`run_shell()` kørte `catalogue()` og `process()` og **ikke** `build_sitemap()`
eller `build_search_index()` — de to filer `main()` skriver *efter* sidernes
`process()`. De er ikke HTML, så løkken over `page_paths()` rørte dem aldrig.

Målt på den rigtige kommando (`tools/apply_shell.py`, uden `--dry-run`, altså
ikke R1): **148 `lastmod` i `site/sitemap.xml` flyttede sig**, mens porten stod
grøn. Ingen gik tilbage — alle 148 gik fremad, fordi de sider var redigeret
siden sidste gang sitemapet blev skrevet. Det skyldtes ikke en fejl i
`git_dates()`: `cdab45c` rummede en ægte sætningsfejl i `site/badge/index.html`
("it **unlocks**" → "it **gets**"), så `2026-09-28` for `/badge/` er sand.

Så det var ikke porten, der lå, men **det træ den målte**: R1 krævede et fast
punkt for 230 HTML-sider og sagde intet om de to filer, der beskriver dem. R1
måler nu hele `main()`s skriveflade, og R3 dømmer den modsatte retning med en
mutation R2 ikke kan lave: en `lastmod` der er forkert, **uden** at nogen side
røres. Bevis på at casen ikke er død: den gamle kæde ser mutationen som
`INGEN bevægelse`, den nye fanger den.

Selftest: tre negative cases. R3 er den der lukkede det hulle denne port
havde, og den fandt 148 forældte `lastmod` i det committede sitemap.

Krav: Python 3.10+. Det er ikke en bivirkning — `apply_shell.py` bruger
`str | None` i annoteringer, og på en ældre fortolkning dør den TypeError
ved indlæsningen, syv rammer under denne fils navn. `pyreq.require(__file__)`
står derfor i toppen, så en gammel `python3` siger *kravet* frem for at
efterlade en fejl der ligner en produktrelateret. Se `tools/pyreq.py`.
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import shutil
import pyreq
import sys
import tempfile

pyreq.require(__file__)

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
    found.extend(run_derivatives(shell, tree))
    return found


# De to afledte filer. `main()` skriver dem, og de er **ikke** HTML-sider, så
# løkken over `page_paths()` rør dem ikke. Det var hele hullet: R1 sagde
# "0 ændret af én kørsel af den rigtige kæde", og målt på den virkelige
# kommando (`tools/apply_shell.py`, ikke `--dry-run`) ændrede den 148
# `lastmod` i `sitemap.xml`. Se målingen i `IMPLEMENTATION_PLAN.md`.
DERIVEREDE = ("sitemap.xml", "search-index.json")


def run_derivatives(shell, tree: pathlib.Path) -> list[str]:
    """Skalens to afledte filer skal også være et fast punkt.

    De skrives af `main()` efter sidernes `process()`, og de læser *alle*
    siderne — så de arver præcis den bevægelighed porten så småt undgik at se.
    De måles derfor på samme måde som siderne: byte før, byte efter.
    """
    found: list[str] = []
    for navn in DERIVEREDE:
        sti = tree / navn
        if not sti.exists():
            found.append(f"R1 {navn}: mangler i træet — kæden skriver den, så den skal findes")
            continue
        before = sti.read_bytes()
        _kør_afledt(shell, navn)
        after = sti.read_bytes()
        if before != after:
            found.append(f"R1 {navn}: {_first_delta(before.decode('utf-8', 'replace'), after.decode('utf-8', 'replace'))}")
    return found


def _kør_afledt(shell, navn: str) -> None:
    if navn == "sitemap.xml":
        shell.build_sitemap()
    else:
        shell.build_search_index()


def _first_delta(a: str, b: str) -> str:
    la, lb = a.splitlines(), b.splitlines()
    for i, (x, y) in enumerate(zip(la, lb)):
        if x != y:
            return f"linje {i + 1} — {x.strip()[:70]} → {y.strip()[:70]}"
    return f"{len(la)} → {len(lb)} linjer"


def _short(s: str) -> str:
    return s.replace("\n", " ")


def tree_findings() -> list[str]:
    """R1: det committede træ skal være et fast punkt for den rigtige kæde."""
    shell = load_shell()
    with tempfile.TemporaryDirectory() as tmp:
        tree = pathlib.Path(tmp) / "site"
        shutil.copytree(SITE, tree)
        found = run_shell(shell, tree)
    if not found:
        pages = len(page_paths(SITE))
        print(f"R1 OK — {pages} sider + {len(DERIVEREDE)} afledte filer, 0 ændret "
              f"af én kørsel af den rigtige kæde")
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
    found.extend(afledt_selftest())
    return found


def afledt_selftest() -> list[str]:
    """R3: en forældet `sitemap.xml` skal fanges — det var det hele hullet.

    R2 fjerner en `art-meta`, som `process()` genskriver i **samme** kørsel. Den
    bevæger derfor også `build_sitemap()`, så den er en svag mutation af R3.

    R3 gør det modsatte: den skriver en `lastmod` der er **forkert**, uden at
    røre nogen side. `process()` har intet at sige om den, så kun
    `build_sitemap()` kan fange den — og før denne rettelse blev den slet ikke
    kaldt. Det er præcis den fejl, der lå i træet: 148 `lastmod` der pegede på
    den dag siden sidst blev redigeret, mens `R1 OK — 230 sider` stod i loggen.

    Som R2 må mutationen kunne lyve, hvis den var død, så den måles to gange:
    at filen faktisk blev skrevet, og at porten faktisk så den.
    """
    found: list[str] = []
    shell = load_shell()
    with tempfile.TemporaryDirectory() as tmp:
        tree = pathlib.Path(tmp) / "site"
        shutil.copytree(SITE, tree)
        sti = tree / "sitemap.xml"
        original = sti.read_text(encoding="utf-8")
        forkeret = original.replace("<lastmod>", "<lastmod>1999-01-01<!--", 1)
        if forkeret == original:
            return ["R3: mutationen ændrede intet i sitemapet — den er et "
                    "stilhedende no-op, så casen kan ikke lyve om R1"]
        sti.write_text(forkeret, encoding="utf-8")
        if sti.read_text(encoding="utf-8") != forkeret:
            return ["R3: sitemapet blev ikke skrevet, så mutationen døde på vejen"]
        moved = run_shell(shell, tree)
        if not any(m.startswith("R1 sitemap.xml") for m in moved):
            found.append("R3: en forældet lastmod i sitemap.xml blev ikke faget — "
                         "porten ser kun sider, ikke de afledte filer")
        else:
            print("R3 OK — en forældet lastmod i sitemap.xml så R1 fange den "
                  f"({len(moved)} linjer)")
            print("     " + _short(next(m for m in moved if m.startswith("R1 sitemap.xml"))))
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
