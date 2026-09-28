#!/usr/bin/env python3
"""Én erklæring af den python repoets værktøjer kræver — med en læsbar fejl.

    python3 tools/pyreq.py           # hvad kræver vi, og hvad kører der nu?
    python3 tools/pyreq.py --check   # exit 1 hvis den kørende python er for gammel

Baggrunden er målt, og den er dyr. Opgave 111 (28/9) frosne skalens datoer og
skrev `R1 OK — 230 sider` i planen. R1 var aldrig kørt: porten var startet med
system-`python3`, som på macOS er 3.9, og døde med

    TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'

pegerende på `apply_shell.py:413` — en fil brugeren aldrig kaldte, med en
fejl der siger intet om python. Resultatet så ud til at være en måling af
træet. Det var det ikke: det var en måling af et træ, der var kørt i forvejen.
Først CI på en frisk udtjekning af HEAD fandt de 99 bevægelige sider, og
sitet holdt op med at deploye i over et døgn.

`quality_gate.sh` har allerede `pick_python` og dører hårdt, hvis ingen
python >= 3.10 findes. Det er gaten, der er beskyttet. Det er *værktøjet i
hånden* der ikke var: en agent eller et menneske, der kører porten direkte,
fik en TypeError syv rammer nede i en anden fil og ingen besked om årsagen.

Derfor to ting ad gangen:

  1. `require()` — kaldes i toppen af de værktøjer der indlæser andre moduler
     dynamisk. Den fanger den gamle fortolkning, før den dynamiske
     indlæsning når at evaluere annoteringer der kræver 3.10.
  2. `check_runtime.py` — holder `MIN_PYTHON` i overensstemmelse med den
     floor `pick_python` tester, så de to tal ikke kan glide fra hinanden.

Kravet er 3.10+, ikke "fordi annoteringer er pæne". `build_public_tree.py`
kalder `Path.write_text(newline=)`, og det argument kom først i 3.10.

Denne fil skal selv kunne *køre* på den python den afviser — ellers ville
fejlen om for gammel python dø af den fejl den skal forklare. Derfor er den
holdt i 3.9-læselig del af sproget.
"""
from __future__ import annotations

import pathlib
import sys

# Én tal. `check_runtime.py` sammenligner det med den floor `pick_python`
# tester i `quality_gate.sh`, så de to kan ikke glide fra hinanden i det
# skjulte: en værktøjflok der kræver 3.11 mens gaten binder 3.10 dør i
# porten med præcis den fejl denne fil findes på at fange.
MIN_PYTHON = (3, 10)

TOOLS = "tools/pyreq.py"


def short_version(info) -> str:
    """`sys.version_info` som "3.9.6" — det tal en fejl skal kunne læses af."""
    major, minor, micro = info[0], info[1], info[2]
    return f"{major}.{minor}.{micro}"


def requirement_text() -> str:
    """Kravet i en hel sætning, så det kan stå i en fejl og i en rapport."""
    return f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+"


def interpreter_problem(info) -> str | None:
    """Beskriv forskellen på `info` og kravet, eller None når den er dækket.

    Returneres som en korte, midtsætnings-egnet sætning, så den kan indgå i
    både `require()`s fejl og `--check`s rapport uden at gentage kravet.

    `info` er indsprøjt i stedet for læst fra `sys.version_info`, så
    selftesten kan prøve både en for gammel og en nyere fortolkning uden at
    den afhænger af, hvilken python selftesten selv bliver kørt på. Det er
    samme greb som `check_runtime.py` bruger på `check_running_node()`.
    """
    if info[: len(MIN_PYTHON)] >= MIN_PYTHON:
        return None
    return f"men den kører på {short_version(info)}"


def require(tool: str) -> None:
    """Stop med en besked der forklarer årsagen, hvis fortolkningen er for gammel.

    Kaldt i toppen af værktøjet, **før** det indlæser andre moduler. En
    `TypeError` på `str | None` er en fejl ved modul-exekvering, så en vag
    der står længere nede når aldrig at køre.
    """
    problem = interpreter_problem(sys.version_info)
    if problem is None:
        return
    name = pathlib.Path(tool).name
    raise SystemExit(
        f"{name} kræver {requirement_text()}, {problem}.\n"
        f"  Kør `bash tools/quality_gate.sh` — den binder en passende python én\n"
        f"  gang og bruger den i alle trin.\n"
        f"  Ellers: kald værktøjet med python{MIN_PYTHON[0]}.{MIN_PYTHON[1]} eller nyere,\n"
        f"  og se `python3 tools/pyreq.py` for kravet."
    )


def main() -> int:
    problem = interpreter_problem(sys.version_info)
    print(f"krav:  {requirement_text()}")
    print(f"kører: {short_version(sys.version_info)} ({sys.executable})")
    if problem is None:
        print("OK — den kørende python dækker kravet")
        return 0
    print(f"FEJL — {TOOLS} kræver {requirement_text()}, {problem}.")
    print("  Kør `bash tools/quality_gate.sh`, som binder en passende python.")
    return 1 if "--check" in sys.argv else 0


if __name__ == "__main__":
    raise SystemExit(main())
