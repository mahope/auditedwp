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

# GitHub Actions-inputnavne er case-insensitive, så det er mønstrene også.
# Kommentarer strippes før der matches, ellers kunne en kommentar med ordet
# "node-version" få en workflow til at se ud som om den erklærer en runtime.
NODE_VERSION_RE = re.compile(r"node-version:\s*['\"]?v?(\d+(?:\.\d+)?)", re.I)
NODE_VERSION_LINE_RE = re.compile(r"^\s*[-#]*\s*node-version\s*:", re.I | re.M)
SETUP_NODE_RE = re.compile(r"setup-node", re.I)
COMMENT_RE = re.compile(r"\s+#.*$", re.M)
ENGINE_FLOOR_RE = re.compile(r">=\s*(\d+)(?:\.(\d+))?")


def eol_of(major: int) -> date:
    """EOL-datoen for en Node-major. Kaster ValueError for en ukendt major."""
    raw = NODE_MAJOR_EOL.get(major)
    if raw is None:
        raise ValueError(str(major))
    return date.fromisoformat(raw)


def read_floor(declared):
    """Udtræk den laveste understøttede version ud af en `engines`-streng.

    Returnerer (major, minor|None) eller None, hvis strengen ikke er en
    `>=N`-erklæring. Minor medtages, fordi `>=22.11.0` ellers ville blive
    godtaget som `>=22`, selv om CI bygger på 22.0.0.
    """
    if not isinstance(declared, str):
        return None
    match = ENGINE_FLOOR_RE.search(declared)
    if not match:
        return None
    return int(match.group(1)), (int(match.group(2)) if match.group(2) else None)


def format_floor(floor) -> str:
    major, minor = floor
    return f">={major}" if minor is None else f">={major}.{minor}"


def load_packages(root: Path) -> tuple[list, list]:
    """Læs begge package.json én gang. Kaster aldrig — en fejl bliver et fund.

    Alt, der efterfølgende skal bruge tallene, får dem herfra, så gaten ikke
    læser den samme fil to gange med to forskellige fejlhåndteringer.
    """
    loaded, findings = [], []
    for rel in EUCOMPLY_PACKAGES:
        path = root / rel
        if not path.is_file():
            findings.append(f"{rel}: pakken mangler — kan ikke erklære en runtime")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
            findings.append(f"{rel}: kan ikke læses som JSON ({exc})")
            continue
        if not isinstance(data, dict):
            findings.append(f"{rel}: JSON'en er ikke et objekt")
            continue
        loaded.append((rel, data))
    return loaded, findings


def check_engines(packages: list, today: date) -> tuple[list, list]:
    """Begge pakker skal erklære den *samme* understøttede, ikke-EOL floor."""
    findings, floors = [], []
    for rel, data in packages:
        engines = data.get("engines")
        if not isinstance(engines, dict):
            findings.append(f"{rel}: ingen engines-objekt — runtimekravet er ikke erklæret")
            continue
        declared = engines.get("node")
        if not declared:
            findings.append(f"{rel}: ingen engines.node — runtimekravet er ikke erklæret")
            continue
        floor = read_floor(declared)
        if floor is None:
            findings.append(
                f'{rel}: engines.node="{declared}" er ikke en ">=N"-erklæring'
            )
            continue
        floors.append((rel, floor))
        try:
            eol = eol_of(floor[0])
        except ValueError:
            findings.append(
                f"{rel}: Node {floor[0]} findes ikke i NODE_MAJOR_EOL i dette script — "
                f"opdater tabellen med Node {floor[0]}'s EOL-dato fra "
                f"https://github.com/nodejs/Release/blob/main/schedule.json, eller brug "
                f"en understøttet major"
            )
            continue
        if eol <= today:
            findings.append(
                f"{rel}: erklærer Node {format_floor(floor)}, men Node {floor[0]} "
                f"nåede EOL {eol} — brug en understøttet major"
            )
    # De to pakker er to forskellige downloads, men én runtime. Uden denne
    # sammenligning kan den laveste erklærede major blive skjult af den højeste,
    # og en bruger af npm-pakken så køre en runtime, ingen testede.
    if len({floor for _, floor in floors}) > 1:
        detail = ", ".join(f"{rel} erklærer {format_floor(floor)}" for rel, floor in floors)
        findings.append(
            f"pakkerne erklærer forskellige runtimes: {detail} — de skal være ens"
        )
    return findings, floors


def check_nvmrc(root: Path, floor: tuple) -> list[str]:
    """.nvmrc skal findes og dække præcis den erklærede floor."""
    path = root / ".nvmrc"
    if not path.is_file():
        return [".nvmrc mangler i repo-roden — runtimekravet er ikke erklæret for udviklere"]
    raw = path.read_text(encoding="utf-8", errors="replace").strip().lstrip("v")
    major, minor = floor
    want = str(major) if minor is None else f"{major}.{minor}"
    if raw != want:
        return [
            f".nvmrc angiver {raw!r}, mens engines angiver {format_floor(floor)} — "
            f"skriv {want!r} (en ren major/minor, så nvm og gaten er enige)"
        ]
    return []


def _workflow_files(root: Path) -> list:
    """Alle EUComply-workflows og composite actions, minus undtagelserne."""
    paths = []
    workflows = root / ".github" / "workflows"
    if workflows.is_dir():
        paths += sorted(workflows.glob("*.yml")) + sorted(workflows.glob("*.yaml"))
    # Composite actions sætter også node-version, og de lå tidligere uden for
    # gaten, fordi de ikke ligger i .github/workflows.
    actions = root / ".github" / "actions"
    if actions.is_dir():
        for sub in sorted(actions.iterdir()):
            if sub.is_dir():
                paths += sorted(sub.glob("action.yml")) + sorted(sub.glob("action.yaml"))
    return [p for p in paths if p.name not in WORKFLOW_EXCLUSIONS]


def check_workflows(root: Path, floor: tuple) -> list[str]:
    """Ingen EUComply-workflow må bygge på en anden Node-version end den erklærede."""
    findings = []
    files = _workflow_files(root)
    if not files:
        return [".github/workflows mangler — CI's runtime kan ikke efterprøves"]
    major, minor = floor
    want = str(major) if minor is None else f"{major}.{minor}"
    declared_anywhere = False
    for path in files:
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        text = COMMENT_RE.sub("", text)
        values = NODE_VERSION_RE.findall(text)
        has_line = bool(NODE_VERSION_LINE_RE.search(text))
        if not has_line:
            if SETUP_NODE_RE.search(text):
                findings.append(
                    f"{rel}: bruger setup-node uden en læsbar node-version (fx 'lts/*') — "
                    f"skriv node-version: '{want}', ellers bygger CI på noget andet end "
                    f"det erklærede"
                )
            continue
        if not values:
            findings.append(
                f"{rel}: sætter node-version, men værdien kan ikke læses som en major "
                f"(fx 'lts/*') — gaten kan da ikke bekræfte hvilken runtime der bygges"
            )
            continue
        for value in values:
            declared_anywhere = True
            if value != want:
                findings.append(
                    f"{rel}: sætter node-version {value}, mens engines angiver "
                    f"{format_floor(floor)}"
                )
    if not declared_anywhere:
        findings.append(
            "ingen EUComply-workflow sætter en læsbar node-version — CI ville bygge på "
            "runnernes default, som ikke er den erklærede runtime"
        )
    return findings


def check_running_node(floor: tuple, major) -> list[str]:
    """Gaten skal selv køre på den erklærede runtime, ellers er et grønt resultat svært.

    `major` indsprøttes, så selftesten kan prøve den uden at være afhængig af
    hvilken Node værten tilfældigvis har.
    """
    if major is None:
        return ["kan ikke læse den kørende Node-version — gaten kan ikke dokumentere hvilken runtime den testede"]
    if major < floor[0]:
        return [
            f"gaten kører på Node {major}, men repoet erklærer {format_floor(floor)} — "
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


def check_dependencies(packages: list) -> list[str]:
    """Er der overhovedet noget at auditere? Uden lockfile kan `npm audit` ikke køre."""
    findings = []
    for rel, data in packages:
        count = 0
        for field in ("dependencies", "devDependencies", "optionalDependencies"):
            block = data.get(field)
            if isinstance(block, dict):
                count += len(block)
        lock = (Path(rel).parent / "package-lock.json")
        if count and not lock.is_file():
            findings.append(
                f"{rel}: erklærer {count} afhængigheder uden package-lock.json — "
                f"npm audit kan ikke køre, så afhængighederne er uauditeterede"
            )
    return findings


def _fallback_floor(root: Path):
    """Den floor de andre kontroller sammenligner mod, når ingen pakke erklærer en.

    Uden denne springer `.nvmrc`- og workflow-kontrollen over, og en gate der
    stille kun afprøver 1 af 5 ting er værre end ingen gate. Læser .nvmrc,
    fordi den er den erklæring, der er nemmest at finde uden om JSON.
    """
    path = root / ".nvmrc"
    if not path.is_file():
        return None
    raw = path.read_text(encoding="utf-8", errors="replace").strip().lstrip("v")
    parts = raw.split(".")
    if not parts[0].isdigit():
        return None
    minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
    return int(parts[0]), minor


def run(root: Path, today: date | None = None, probe_node: bool = True) -> list[str]:
    """Kør alle kontroller mod en given repo-rod og samle fundene.

    `probe_node=False` slår kun værtsens Node-version fra, så selftesten er
    deterministisk uanset hvilken Node den bliver kørt på.
    """
    today = today or date.today()
    found: list[str] = []
    packages, load_findings = load_packages(root)
    found.extend(load_findings)
    engines_findings, floors = check_engines(packages, today)
    found.extend(engines_findings)

    declared = [floor for _, floor in floors]
    if declared:
        floor = declared[0]
    else:
        floor = _fallback_floor(root)
        if floor is None:
            found.append(
                "kan ikke fastslå nogen Node-floor — ingen pakke erklærer engines.node, "
                "og .nvmrc mangler eller er ulæselig"
            )
            floor = (0, None)
        else:
            found.append(
                f"bruger {format_floor(floor)} fra .nvmrc som sammenligningsgrundlag, "
                f"fordi ingen pakke erklærer en floor"
            )

    found.extend(check_nvmrc(root, floor))
    found.extend(check_workflows(root, floor))
    if probe_node:
        found.extend(check_running_node(floor, _major_of_running_node()))
    found.extend(check_dependencies(packages))
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
                        drop_nvmrc=False, drop_engines=False, no_ci=False,
                        second_floor=None, ci_comment_only=False, no_node_step=False):
            for rel in EUCOMPLY_PACKAGES:
                path = base / rel
                data = json.loads(path.read_text(encoding="utf-8"))
                if drop_engines:
                    data.pop("engines", None)
                else:
                    chosen = second_floor if (second_floor and rel == EUCOMPLY_PACKAGES[1]) else engines_floor
                    data["engines"] = {"node": f">={chosen}"}
                path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            nvmrc = base / ".nvmrc"
            if drop_nvmrc:
                nvmrc.unlink(missing_ok=True)
            else:
                nvmrc.write_text(nvmrc_major + "\n", encoding="utf-8")
            wf = base / ".github" / "workflows" / "verify.yml"
            if no_ci:
                wf.unlink(missing_ok=True)
            elif no_node_step:
                # Workflow'en findes, men setup-node-steget er væk. Den ser
                # stadig helt troværdig ud og bygger på runnernes default.
                wf.write_text(
                    "jobs:\n  gate:\n    steps:\n      - run: bash tools/quality_gate.sh\n",
                    encoding="utf-8",
                )
            elif ci_comment_only:
                # Kun setup-node og en kommentar der nævner node-version:
                # det så ud til at erklære en runtime uden at gøre det.
                wf.write_text(
                    "jobs:\n  gate:\n    steps:\n"
                    "      - uses: actions/setup-node@v4\n"
                    f"        # historisk node-version: {floor}\n",
                    encoding="utf-8",
                )
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
        clean = run(base, today, probe_node=False)
        if clean:
            print("SELFTEST FEJLED: et minimalt rent repo giver fund:")
            for f in clean:
                print(f"  - {f}")
            return 1
        print("selftest: rent repo giver 0 fund")

        cases = [
            ("EOL-major i engines", "nåede EOL",
             lambda: write_state(engines_floor=20, nvmrc_major="20", ci="20")),
            (".nvmrc afviger fra engines", "mens engines angiver",
             lambda: write_state(nvmrc_major="24")),
            ("CI bygger på en anden version", "mens engines angiver",
             lambda: write_state(ci="20")),
            ("manglende .nvmrc", ".nvmrc mangler",
             lambda: write_state(drop_nvmrc=True)),
            ("manglende engines.node", "runtimekravet er ikke erklæret",
             lambda: write_state(drop_engines=True)),
            ("workflow uden setup-node-steg", "runnernes default",
             lambda: write_state(no_node_step=True)),
            ("hele workflow-mappen væk", ".github/workflows mangler",
             lambda: write_state(no_ci=True)),
            # De tre herunder er de mutationer, en frisk review fandt som
            # falske grønne i den første udgave af denne gate. De står derfor
            # eksplicit, så en senere ændring ikke genindfører dem.
            ("pakkerne erklærer hver sin runtime", "forskellige runtimes",
             lambda: write_state(second_floor=24)),
            ("uoplæselig node-version som lts/*", "kan ikke læses som en major",
             lambda: write_state(ci="lts/*")),
            ("kommentar som eneste node-version", "uden en læsbar node-version",
             lambda: write_state(ci_comment_only=True)),
        ]
        for label, needle, mutate in cases:
            mutate()
            hit = [f for f in run(base, today, probe_node=False) if needle in f]
            if hit:
                print(f"selftest: {label} fanget")
            else:
                print(f"SELFTEST FEJLED: {label} blev ikke fanget")
                return 1
        write_state()

        # Værtenes Node-version skal ikke afgøre selftestens udfald, så den
        # prøves direkte med indsprøjtede værdier i stedet.
        if check_running_node((22, None), 20):
            print("selftest: for gammel kørende Node fanget")
        else:
            print("SELFTEST FEJLED: Node under flooren blev ikke fanget")
            return 1
        if check_running_node((22, None), None) == []:
            print("SELFTEST FEJLED: ulæselig Node-version blev ikke fanget")
            return 1
        print("selftest: ulæselig kørende Node fanget")

        # En major, der ikke står i livscyklustabellen, må kræve et blik fra et
        # menneske — ellers kan en ny runtime erklæres uden at nogen ved om den
        # er understøttet.
        (base / "eucomply-scanner" / "package.json").write_text(
            json.dumps({"engines": {"node": ">=99"}}, indent=2), encoding="utf-8"
        )
        if not [f for f in run(base, today, probe_node=False) if "NODE_MAJOR_EOL" in f]:
            print("SELFTEST FEJLED: ukendt Node-major blev ikke fanget")
            return 1
        print("selftest: ukendt Node-major kræver dokumentation fanget")

        # En afhængighed uden lockfile betyder en uauditeteret afhængighed.
        (base / "eucomply-scanner" / "package.json").write_text(
            json.dumps({"engines": {"node": ">=22"}, "dependencies": {"left-pad": "1.0.0"}}, indent=2),
            encoding="utf-8",
        )
        if not [f for f in run(base, today, probe_node=False) if "uauditeterede" in f]:
            print("SELFTEST FEJLED: afhængighed uden lockfile blev ikke fanget")
            return 1
        print("selftest: afhængighed uden lockfile fanget")

        # Ødelagt JSON må give et fund, ikke et traceback. En gate der
        # fejler med en stacktrace mister alle de andre fund.
        (base / "eucomply-scanner" / "package.json").write_text(
            '{ "engines": { "node": ">=22" }', encoding="utf-8"
        )
        broken = run(base, today, probe_node=False)
        if not [f for f in broken if "ikke læses som JSON" in f or "kan ikke læses" in f]:
            print("SELFTEST FEJLED: ødelagt JSON blev ikke fanget som fund")
            return 1
        print("selftest: ødelagt JSON fanget som fund, ikke som crash")

    extra = 4
    print(f"SELFTEST GRØN — alle {len(cases) + extra} negative cases fanges")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    found = run(ROOT)
    if found:
        print("RUNTIME-GATE RØD:")
        for f in found:
            print(f"  - {f}")
        print("\nRet dem i ÉN commit: engines + .nvmrc + CI skal vælge samme Node-version.")
        return 1
    print(
        "Runtime-gate grøn: begge pakker, .nvmrc og CI angiver samme understøttte "
        "Node-version, gaten kører på den erklærede runtime, og ingen afhængighed "
        "står uden lockfile."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
