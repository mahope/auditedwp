#!/usr/bin/env python3
"""Gate for den erklærede Node-runtime.

Opgave 11 i IMPLEMENTATION_PLAN.md kræver, at runtime-kravet er *erklæret*:

  > Ny understøttet Node-major fremgår tydeligt i `engines` og `.nvmrc`.

En erklæring, ingen er holdt, er værdiløs. Repoet havde tre forskellige tal for
den samme runtime — `engines: ">=18"`, CI på `node-version: '20'` og en
maskine der kørte 22 — og ingen af dem kontrollerede de andre. Det er præcis
den fejltype, der dræbte jordemoderstudy 23. august: Next.js blev installeret,
men serveren byggede med Node 18, og fejlen viste sig først i produktion.

Derfor er der her tre ting, der skal være *én* ting:

  1. `engines.node` i begge pakker angiver en Node-major der ikke er EOL.
  2. `.nvmrc` i repo-roden angiver præcis samme major.
  3. Hver EUComply-workflow der sætter `node-version`, angiver samme major.

Reglen er bevidst stram — floor, .nvmrc og CI skal være *identiske* — fordi den
tester den version vi erklærer, i stedet for en nyere. En bruger på den
udelovede minimumversion skal kunne regne med at gaten dækker den.

Negativt testet: se `--selftest`. Scriptet skal kunne fejle, ellers er det ikke
en gate.

Brug:
    python3 tools/check_runtime.py            # hele kontrollen
    python3 tools/check_runtime.py --selftest # sæt fejl ind og kræv at de fanges
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Node-livscyklus, dato for end-of-life pr. major.
# Kilde: https://github.com/nodejs/Release/blob/main/schedule.json
# (hentet 2026-09-25). Holdes her bevidst som en dateret tabel i stedet for at
# hentes fra nettet, så gaten er deterministisk og kan køre uden forbindelse.
# Opdateres ved den næste runtime-commit — se `REQUIRED_FLOOR`-kommentaren.
NODE_MAJOR_EOL = {
    18: "2025-04-30",
    20: "2026-04-30",
    21: "2024-06-01",
    22: "2027-04-30",
    23: "2025-06-01",
    24: "2028-04-30",
    25: "2026-06-01",
}

# EUComply egger pakker. Begge går ud til brugere som henholdsvis npm-CLI og
# selvstændigt CLI, så de skal kræve den samme runtime.
EUCOMPLY_PACKAGES = ("eucomply-scanner/package.json", "cli/package.json")

# Workflows der hører til EUComply. `build-devnotify.yml` bygger et
# søskeprodukt og er bevidst holdt ude: opgave 11 siger, at DeskUptime- og
# DevNotify-opgraderinger ikke blandes ind i EUComply-commits, så de får deres
# egen diff med egen rollback. Fjern fra denne liste, når den er lavet.
WORKFLOW_EXCLUSIONS = {
    "build-devnotify.yml": "søskeprodukt, ikke EUComply-gaten",
}

# GitHub Actions skriver node-version på flere måder; vi vil have major'en.
NODE_VERSION_RE = re.compile(r"node-version:\s*['\"]?v?(\d+)")
ENGINE_FLOOR_RE = re.compile(r">=\s*(\d+)")


def eol_of(major: int) -> date:
    """EOL-datoen for en Node-major. Kaster ValueError for en ukendt major."""
    raw = NODE_MAJOR_EOL.get(major)
    if raw is None:
        raise ValueError(str(major))
    return date.fromisoformat(raw)


def read_floor(engines_node: str) -> int:
    """Udtræk den laveste understøttede major ud af en `engines`-streng."""
    match = ENGINE_FLOOR_RE.search(engines_node or "")
    return int(match.group(1)) if match else -1


def check_engines(root: Path, today: date) -> list[str]:
    """Begge pakker skal erklære en floor, og den må ikke være EOL."""
    findings = []
    for rel in EUCOMPLY_PACKAGES:
        path = root / rel
        if not path.is_file():
            findings.append(f"{rel}: pakken mangler — kan ikke erklære en runtime")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(f"{rel}: ugyldig JSON ({exc})")
            continue
        declared = (data.get("engines") or {}).get("node")
        if not declared:
            findings.append(f"{rel}: ingen engines.node — runtimekravet er ikke erklæret")
            continue
        floor = read_floor(declared)
        if floor < 0:
            findings.append(f'{rel}: engines.node="{declared}" er ikke en ">=N"-erklæring')
            continue
        try:
            eol = eol_of(floor)
        except ValueError:
            findings.append(
                f"{rel}: Node {floor} findes ikke i livscyklustabellen i dette script — "
                f"tilføj den med sin EOL-dato, eller brug en understøttet major"
            )
            continue
        if eol < today:
            findings.append(
                f"{rel}: erklærer Node >={floor}, men Node {floor} nåede EOL {eol} — "
                f"brug en understøttet major"
            )
    return findings


def check_nvmrc(root: Path, floor: int) -> list[str]:
    """.nvmrc skal findes og pege på samme major som engines."""
    path = root / ".nvmrc"
    if not path.is_file():
        return [".nvmrc mangler i repo-roden — runtimekravet er ikke erklæret for udviklere"]
    raw = path.read_text(encoding="utf-8").strip().lstrip("v")
    if not raw.isdigit():
        return [f".nvmrc indeholder {raw!r}, som ikke er en Node-major"]
    if int(raw) != floor:
        return [f".nvmrc siger Node {raw}, mens engines siger >={floor} — de skal være ens"]
    return []


def check_workflows(root: Path, floor: int) -> list[str]:
    """Ingen EUComply-workflow må bygge på en anden Node-version end den erklærede."""
    findings = []
    directory = root / ".github" / "workflows"
    if not directory.is_dir():
        return [".github/workflows mangler — CI's runtime kan ikke efterprøves"]
    seen = False
    for path in sorted(directory.glob("*.yml")) + sorted(directory.glob("*.yaml")):
        if path.name in WORKFLOW_EXCLUSIONS:
            continue
        text = path.read_text(encoding="utf-8")
        for major in NODE_VERSION_RE.findall(text):
            seen = True
            if int(major) != floor:
                findings.append(
                    f"{path.name}: sætter node-version {major}, mens engines siger >={floor}"
                )
    if not seen:
        findings.append(
            "ingen EUComply-workflow sætter node-version — CI ville bygge på "
            "runnernes default, som ikke er den erklærede runtime"
        )
    return findings


def check_running_node(floor: int) -> list[str]:
    """Gaten skal selv køre på den erklærede runtime, ellers er et grønt resultat svært."""
    major = _major_of_running_node()
    if major is None:
        return ["kan ikke læse den kørende Node-version — gaten kan ikke dokumentere hvilken runtime den testede"]
    if major < floor:
        return [
            f"gaten kører på Node {major}, men repoet erklærer >={floor} — "
            f"et grønt resultat på en ældre runtime beviser intet om den erklærede"
        ]
    return []


def _major_of_running_node():
    """Node-major for den node der faktisk kører gaten.

    Scriptet køres af `python3`, så Node-versionen skal spørges om i en
    subprocess. Kan ikke findes, returneres None, og kontrollen siger det
    ærligt i stedet for at gætte.
    """
    try:
        proc = subprocess.run(
            ["node", "--version"], capture_output=True, text=True, timeout=30
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    match = re.search(r"v?(\d+)", proc.stdout or "")
    return int(match.group(1)) if match else None


def check_dependencies(root: Path) -> list[str]:
    """Er der overhovedet noget at auditere? Uden lockfile kan `npm audit` ikke køre."""
    findings = []
    for rel in EUCOMPLY_PACKAGES:
        path = root / rel
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue  # allerede rapporteret i check_engines
        count = sum(
            len(data.get(field) or {})
            for field in ("dependencies", "devDependencies", "optionalDependencies")
        )
        if count and not (path.parent / "package-lock.json").is_file():
            findings.append(
                f"{rel}: erklærer {count} afhængigheder uden package-lock.json — "
                f"npm audit kan ikke køre, så afhængighederne er uauditeterede"
            )
    return findings


def run(root: Path, today: date | None = None) -> list[str]:
    """Kør alle kontroller mod en given repo-rod og samle fundene."""
    today = today or date.today()
    found: list[str] = []
    found.extend(check_engines(root, today))

    # floor til .nvmrc- og workflow-kontrollen er den højeste erklærede, så en
    # drift mellem de to pakker ikke kan skjules af at man bare læser den første.
    floors = [
        read_floor((json.loads((root / rel).read_text(encoding="utf-8")).get("engines") or {}).get("node", ""))
        for rel in EUCOMPLY_PACKAGES
        if (root / rel).is_file()
    ]
    floors = [f for f in floors if f > 0]
    if floors:
        floor = max(floors)
        found.extend(check_nvmrc(root, floor))
        found.extend(check_workflows(root, floor))
        found.extend(check_running_node(floor))
    found.extend(check_dependencies(root))
    return found


def selftest() -> int:
    """Gaten skal kunne fejle. Vi indplanter fejl og kræv at de fanges."""
    floor = 22
    today = date(2026, 9, 25)

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "repo"
        (base / ".github" / "workflows").mkdir(parents=True)
        (base / "eucomply-scanner").mkdir(parents=True)
        (base / "cli").mkdir(parents=True)

        def write_state(engines_floor=floor, nvmrc_major=str(floor), ci=str(floor),
                        drop_nvmrc=False, drop_engines=False, no_ci=False):
            for rel in EUCOMPLY_PACKAGES:
                path = base / rel
                data = json.loads(path.read_text(encoding="utf-8"))
                if drop_engines:
                    data.pop("engines", None)
                else:
                    data["engines"] = {"node": f">={engines_floor}"}
                path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            nvmrc = base / ".nvmrc"
            if drop_nvmrc:
                nvmrc.unlink(missing_ok=True)
            else:
                nvmrc.write_text(nvmrc_major + "\n", encoding="utf-8")
            wf = base / ".github" / "workflows" / "verify.yml"
            if no_ci:
                wf.unlink(missing_ok=True)
            else:
                wf.write_text(
                    "jobs:\n  gate:\n    steps:\n"
                    f"      - uses: actions/setup-node@v4\n        with:\n          node-version: '{ci}'\n",
                    encoding="utf-8",
                )

        # Frø: de to pakker skal findes, før write_state kan rette i dem.
        for rel in EUCOMPLY_PACKAGES:
            (base / rel).write_text(
                json.dumps({"name": Path(rel).parent.name, "engines": {"node": f">={floor}"}}, indent=2),
                encoding="utf-8",
            )

        write_state()
        clean = run(base, today)
        if clean:
            print("SELFTEST FEJLED: et minimalt rent repo giver fund:")
            for f in clean:
                print(f"  - {f}")
            return 1
        print("selftest: rent repo giver 0 fund")

        cases = [
            ("EOL-major i engines", "nåede EOL",
             lambda: write_state(engines_floor=20, nvmrc_major="20", ci="20")),
            (".nvmrc afviger fra engines", "skal være ens",
             lambda: write_state(nvmrc_major="24")),
            ("CI bygger på en anden version", "mens engines siger",
             lambda: write_state(ci="20")),
            ("manglende .nvmrc", ".nvmrc mangler",
             lambda: write_state(drop_nvmrc=True)),
            ("manglende engines.node", "runtimekravet er ikke erklæret",
             lambda: write_state(drop_engines=True)),
            ("ingen node-version i CI", "runnernes default",
             lambda: write_state(no_ci=True)),
        ]
        for label, needle, mutate in cases:
            mutate()
            hit = [f for f in run(base, today) if needle in f]
            if hit:
                print(f"selftest: {label} fanget")
            else:
                print(f"SELFTEST FEJLED: {label} blev ikke fanget")
                return 1
        write_state()

        # En major, der ikke står i livscyklustabellen, må kræve et blik fra et
        # menneske — ellers kan en ny runtime erklæres uden at nogen ved om den
        # er understøttet.
        (base / "eucomply-scanner" / "package.json").write_text(
            json.dumps({"engines": {"node": ">=99"}}, indent=2), encoding="utf-8"
        )
        if not [f for f in run(base, today) if "livscyklustabellen" in f]:
            print("SELFTEST FEJLED: ukendt Node-major blev ikke fanget")
            return 1
        print("selftest: ukendt Node-major kræver dokumentation fanget")

        # En afhængighed uden lockfile betyder en uauditeteret afhængighed.
        (base / "eucomply-scanner" / "package.json").write_text(
            json.dumps({"engines": {"node": ">=22"}, "dependencies": {"left-pad": "1.0.0"}}, indent=2),
            encoding="utf-8",
        )
        if not [f for f in run(base, today) if "uauditeterede" in f]:
            print("SELFTEST FEJLED: afhængighed uden lockfile blev ikke fanget")
            return 1
        print("selftest: afhængighed uden lockfile fanget")

    print(f"SELFTEST GRØN — alle {len(cases) + 2} negative cases fanges")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    found = run(ROOT)
    if found:
        print("RUNTIME-GATE RØD:")
        for f in found:
            print(f"  - {f}")
        print("\nRet dem i ÉN commit: engines + .nvmrc + CI skal vælge samme Node-major.")
        return 1
    print(
        "Runtime-gate grøn: engines, .nvmrc og CI angiver samme understøttede Node-major, "
        "gaten kører på den erklærede runtime, og der er ingen uauditeterede afhængigheder."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
