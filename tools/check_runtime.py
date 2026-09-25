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
# (hentet 2026-09-26). Holdes her bevidst som en dateret tabel i stedet for at
# hentes fra nettet, så gaten er deterministisk og kan køre uden forbindelse.
# Node 26 er den nyeste udgivne major: 26.0.0 kom 2026-05-05 og bliver LTS
# 2026-10-28. Det er *ikke* den samme oplysning som planens tidligere antagelse
# om at Node 26 "lander omkring oktober 2026" — den fandtes allerede i maj, så
# tabellen lå et halvt år forældet. Bliver en ny major udgivet, opdateres den her.
NODE_MAJOR_EOL = {
    18: "2025-04-30",
    20: "2026-04-30",
    21: "2024-06-01",
    22: "2027-04-30",
    23: "2025-06-01",
    24: "2028-04-30",
    25: "2026-06-01",
    26: "2029-04-30",
}

# Hvor tæt op EOL en advarsel erstatter et rødt resultat. 90 dage er nok til at
# hæve floor'en, opgradere gaten og få en grøn kørsel med — og langt nok til at
# gaten ikke larmer på en major, der lige er ved at blive EOL.
EOL_WARNING_DAYS = 90

# Minimumsmajor pr. GitHub-handling i EUComply-workflows, målt mod den major der
# kører på Node 24-native. Uden denne tabel kunne nogen skrive `checkout@v4`
# tilbage, og gaten ville sige grønt, fordi `node-version: '22'` stadig er
# korrekt — præcis de tre tal, der skilte sig, som opgave 11 fandt, nu i en
# anden egenskab.
#
# Kilde: GitHub API `/repos/<repo>/releases/latest`, hentet 2026-09-26:
#   actions/checkout         v7.0.1
#   actions/setup-node       v7.0.0
#   actions/setup-python     v7.0.0
#   actions/upload-artifact  v7.0.1
#   cloudflare/wrangler-action v4.1.3  (fastsat på patch, ikke major — se nedenfor)
#
# Samme livscyklus-mønster som `NODE_MAJOR_EOL`: en dateret tabel, der opdateres
# når den næste major udkommer. Uden den opdatering bliver gaten en dag rød på
# en handling, der finten kører — derfor er hver linje et *minimum* og ikke et
# krav om seneste version, så en patch- eller minor-opgradering aldrig kræver
# en kodeændring her.
#
# `wrangler-action` er bevidst fastsat på patch-tagget `v4.1.3` i stedet for
# `@v4`: 4.1.0 og 4.1.1 blev udgivet defekte og fejler i en workflow, så et
# flydende major-tag kan trække en ødelagt patch ind i selve deployet. Minimum
# major er derfor 4, og selve patchen frådes ikke af denne gate — den af CI.
ACTION_MIN_MAJOR = {
    "actions/checkout": 7,
    "actions/setup-node": 7,
    "actions/setup-python": 7,
    "actions/upload-artifact": 7,
    "cloudflare/wrangler-action": 4,
}

# Runner-imageet EUComply-jobs kører på. Fastsat, fordi GitHub har lagt en
# annotation på alle jobs om at `ubuntu-latest` migrerer til Ubuntu 26 den
# 19. oktober 2026 (set i CI 2026-09-25). Et flydende label kan så ændre den
# miljø, gaten er skrevet imod — `php -l`, node, `python3.13`, wrangler — uden at
# nogen rører repoet. Det er samme fejlklasse som en Node-major der glide: en
# værdi der står i koden, men ingen kontrollerer.
#
# Kravet er *præcist* dette image og ikke et minimum. En runner-image er ikke
# semver, så der findes ingen "seneste" at hæve til med; og når GitHub en dag
# fjerner ubuntu-24.04 skal skiftet ske i denne tabel og gives en grøn kørsel,
# ikke ske automatisk. En matrix som `${{ matrix.os }}` kan ikke efterprøves
# og er derfor et fund, ikke en undtagelse — `build-devnotify.yml`, som bruger
# en, ligger i WORKFLOW_EXCLUSIONS.
RUNNER_IMAGE = "ubuntu-24.04"
RUNNER_PINNED_AT = "2026-09-26"

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

# `uses:` må starte med `-` (step), `name:` (gennemgående kontekst) eller stå
# alene. Kommentarer er strippet før match, ellers kunne en kommenteret
# `uses:`-linje tælle som en rigtig handling — samme falske grøn som en
# kommentar med `node-version`.
USES_RE = re.compile(r"^[ \t]*(?:-\s+)?uses:[ \t]*(\S+)", re.M)
# Samme problem som `node-version`: en kommentar må ikke kunne stå for en
# indstilling. Derfor findes linjen først, og værdien læses kun på en rigtig
# `runs-on:`-linje.
RUNS_ON_RE = re.compile(r"^[ \t]*runs-on\s*:(.*)$", re.I | re.M)
# Job-strukturen: nøgle på to mellemrum, egenskaber på fire. Se _parse_jobs.
JOB_HEADER_RE = re.compile(r"^  ([A-Za-z0-9_.-]+):\s*(#.*)?$")
JOB_PROP_RE = re.compile(r"^    ([A-Za-z0-9_.-]+):\s*(.*)$")
# En tag som `v7` eller `v4.1.3`. Alt uden en forudgående major regnes som
# flydende (`main`, `stable`) og kan ikke efterprøves.
VERSION_REF_RE = re.compile(r"^v?(\d+)(?:\.\d+)*$")
SHA_REF_RE = re.compile(r"^[0-9a-f]{7,40}$", re.I)


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
            f"skriv {want!r}. nvm indlæser også 'lts/*' og patch-numre, men gaten skal "
            f"kunne regne med at den testede runtime er den erklærede"
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


def check_action_majors(root: Path) -> tuple[list, list]:
    """Ingen EUComply-handling må sidde på en major under det dokumenterede minimum.

    `node-version: '22'` siger intet om hvilken Node handlingerne selv kører på.
    Opgave 12 opgræderede dem til Node-24-native majors, men uden denne kontrol
    kunne `actions/checkout@v4` glide tilbage, og gaten ville være grøn.

    Returnerer (fund, advarsler): en handling på en commit-sha er gyldig kode,
    men dens major kan ikke læses, så den er en advarsel og ikke et rødt
    resultat.
    """
    findings, warnings = [], []
    files = _workflow_files(root)
    if not files:
        # check_workflows siger allerede "workflows mangler"; her ville et
        # andet fund blot forvirre.
        return findings, warnings
    seen = 0
    for path in files:
        rel = path.relative_to(root).as_posix()
        text = COMMENT_RE.sub("", path.read_text(encoding="utf-8", errors="replace"))
        for target in USES_RE.findall(text):
            if target.startswith("./") or target.startswith("docker://"):
                continue  # lokal composite action eller container — ingen Node-major
            seen += 1
            if "@" not in target:
                findings.append(
                    f"{rel}: uses: {target} uden @-reference — en flydende reference "
                    f"kan trække en ny, utestet version ind i gaten eller deployet"
                )
                continue
            name, _, ref = target.partition("@")
            key = name.strip().lower()
            if SHA_REF_RE.match(ref):
                warnings.append(
                    f"{rel}: {name} er fastsat på en commit-sha ({ref[:7]}), så "
                    f"minimumsmajoren kan ikke efterprøves automatisk — noter majoren i "
                    f"ACTION_MIN_MAJOR, eller brug en fast major/patch"
                )
                continue
            match = VERSION_REF_RE.match(ref)
            if not match:
                findings.append(
                    f"{rel}: {name}@{ref} er fastsat på en flydende reference, der ikke "
                    f"kan efterprøves — sæt en fast major eller patch (fx @v7)"
                )
                continue
            minimum = ACTION_MIN_MAJOR.get(key)
            if minimum is None:
                findings.append(
                    f"{rel}: {name} står ikke i ACTION_MIN_MAJOR — tilføj den med sin "
                    f"minimum-major og dato, ellers ved vi ikke hvilken Node den kræver"
                )
                continue
            major = int(match.group(1))
            if major < minimum:
                findings.append(
                    f"{rel}: {name}@{ref} er under minimumsmajor v{minimum} "
                    f"(sidst efterprøvet 2026-09-26 mod GitHub API) — opgradér til "
                    f"@v{minimum} eller nyere, ellers kører handlingen på en Node-20-major"
                )
    if not seen and not findings:
        findings.append(
            "ingen EUComply-workflow bruger en tredjepartshandling med en læsbar major — "
            "handlernes major kan da slet ikke efterprøves"
        )
    return findings, warnings


def _parse_jobs(text: str) -> list:
    """Læs job-strukturen uden et YAML-bibliotek.

    Returnerer [(navn, bruger_genbrugt_workflow, [runs-on-værdier])] for hvert
    job under `jobs:`.

    Der parses bevidst ikke med PyYAML: gaten skal køre på den `python3` den
    har ved hånde, og CI's billede må ikke afgøre om gaten virker. GitHub-
    workflows er desuden maskinskrevet i én fast stil — job-nøgle på to mellemrum,
    egenskaber på fire — så en målrettet linjescanning er nok og uden afhængighed.

    Kan en fil ikke læses strukturelt, returneres en tom liste, og kaldstedet
    siger det som en advarsel i stedet for at springe filen over i stilhed.
    """
    jobs: list = []
    in_jobs = False
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not in_jobs:
            # `jobs:` skal stå i kolonne 0. Alt andet på kolonne 0 afslutter
            # jobs-blokken, hvilket også gør at `on:` ikke kan forveksles med
            # et job — det er præcis det `check_workflows` først fejlede på.
            if re.match(r"^jobs\s*:\s*$", line):
                in_jobs = True
            continue
        if not line.startswith(" "):
            in_jobs = False  # en ny topniveau-nøgle efter jobs
            continue
        header = JOB_HEADER_RE.match(line)
        if header:
            jobs.append([header.group(1), False, []])
            continue
        prop = JOB_PROP_RE.match(line)
        if prop and jobs:
            key, raw = prop.group(1), prop.group(2).strip()
            if key == "uses":
                jobs[-1][1] = True
            elif key == "runs-on":
                jobs[-1][2].append(raw)
    return jobs


def check_runner_pins(root: Path) -> tuple[list, list]:
    """Hvert EUComply-job skal køre på det fastsatte runner-image.

    `node-version: '22'` siger intet om hvilket OS-billede jobbet kører på, og
    `ubuntu-latest` siger intet om hvilken version af det billede, CI får om tre
    måneder. Uden denne kontrol kan pin'en glide tilbage til `ubuntu-latest` og
    ingen ser det, før et billede har ændret sig under fødderne på gaten.

    Kontrollen er pr. job og ikke pr. fil. Det er den eneste måde, den dækker
    det billede, mutationen første gang afslørede: `deploy-site.yml` har tre
    jobs, hvor `verify` er et genbrugt workflow-kald uden `runs-on`, og de to
    andre har hver sin. En pr. fil-kontrol er grøn, så snart ÉN job har en pin,
    så fjernes `runs-on` fra det tredje job, og gaten siger alligevel grønt.

    Et job uden `runs-on` er kun gyldigt, hvis det kalder et genbrugt workflow
    (`uses:` under jobs) — så vælger den kaldte workflow sit eget billede.

    Returnerer (fund, advarsler): en fil, hvis job-struktur ikke kan læses, er
    en advarsel. Den springes ikke stift over, men den må heller ikke gøre gaten
    rød på en syntaks, gaten ikke kan parse.
    """
    findings: list[str] = []
    warnings: list[str] = []
    files = _workflow_files(root)
    if not files:
        # check_workflows siger allerede "workflows mangler".
        return findings, warnings
    for path in files:
        rel = path.relative_to(root).as_posix()
        text = COMMENT_RE.sub("", path.read_text(encoding="utf-8", errors="replace"))
        jobs = _parse_jobs(text)
        if not jobs:
            warnings.append(
                f"{rel}: job-strukturen kunne ikke læses, så runs-on er ikke "
                f"efterprøvet job for job — tjek at job står på to mellemrum under "
                f"`jobs:`"
            )
            # Falder tilbage på rå linjer, så vi ikke ender med at have set
            # slet intet. En pin, der findes, efterprøves stadig.
            jobs = [["", False, [v.strip().strip("'\"") for v in RUNS_ON_RE.findall(text)]]]
            if not RUNS_ON_RE.findall(text):
                findings.append(
                    f"{rel}: ingen runs-on at efterprøve — jobbet kører på et billede "
                    f"gaten ikke ved noget om. Sæt runs-on: {RUNNER_IMAGE}"
                )
        for name, reusable, values in jobs:
            where = f"{rel}: job '{name}'" if name else rel
            if reusable:
                continue  # billedet vælges af den kaldte workflow
            if not values:
                findings.append(
                    f"{where} har ingen runs-on — jobbet kører på et billede gaten ikke "
                    f"ved noget om. Sæt runs-on: {RUNNER_IMAGE}"
                )
                continue
            for value in values:
                if not value:
                    findings.append(
                        f"{where}: runs-on uden værdi — gaten kan ikke se hvilket "
                        f"billede jobbet kører på. Sæt runs-on: {RUNNER_IMAGE}"
                    )
                elif "${{" in value:
                    findings.append(
                        f"{where}: runs-on: {value} er et udtryk, gaten ikke kan "
                        f"efterprøve — brug runs-on: {RUNNER_IMAGE}, eller dokumentér "
                        f"billedet her"
                    )
                elif value == "ubuntu-latest":
                    findings.append(
                        f"{where}: runs-on: ubuntu-latest er et flydende label — GitHub "
                        f"migrerer det til Ubuntu 26 den 19. oktober 2026, så billedet "
                        f"kan ændre sig uden at nogen rører repoet. Sæt runs-on: "
                        f"{RUNNER_IMAGE} (fastsat {RUNNER_PINNED_AT})"
                    )
                elif value != RUNNER_IMAGE:
                    findings.append(
                        f"{where}: runs-on: {value} er ikke det fastsatte image "
                        f"{RUNNER_IMAGE} (fastsat {RUNNER_PINNED_AT}) — brug "
                        f"{RUNNER_IMAGE}, eller opdatér RUNNER_IMAGE i denne gate og få "
                        f"en grøn kørsel på det nye billede"
                    )
    return findings, warnings


def check_eol_soon(packages: list, today: date) -> list[str]:
    """Advarsel — ikke rødt resultat — når den erklærede floor er tæt på EOL.

    Gaten bliver rød 1. maj 2027 for floor 22, fordi Node 22 så er EOL. Det er
    rigtigt, men et overraskende rødt resultat en måned inden er dyrere end en
    advarsel: der er tid til at hæve floor'en og få en grøn kørsel med.
    """
    warnings = []
    for rel, data in packages:
        floor = read_floor(data.get("engines", {}).get("node") if isinstance(data.get("engines"), dict) else None)
        if floor is None:
            continue
        try:
            eol = eol_of(floor[0])
        except ValueError:
            continue  # allerede et rødt fund i check_engines
        days = (eol - today).days
        if 0 <= days <= EOL_WARNING_DAYS:
            warnings.append(
                f"{rel}: Node {floor[0]} er EOL om {days} dage ({eol}) — hæv floor'en "
                f"til en understøttet major inden da, ellers bliver gaten rød uden varsel"
            )
    return warnings


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
    """Kør alle kontroller mod en given repo-rod og returnér kun de røde fund.

    Bevares som tynt lag, så eksisterende kaldsteder og selftesten beholder deres
    betydning: en streng liste er et rødt resultat.
    """
    return collect(root, today, probe_node)[0]


def collect(root: Path, today: date | None = None, probe_node: bool = True) -> tuple[list, list]:
    """Kør alle kontroller og adskil fund fra advarsler.

    `probe_node=False` slår kun værtsens Node-version fra, så selftesten er
    deterministisk uanset hvilken Node den bliver kørt på.

    Advarsler er fund, der er ærlige uden at være fejl: de skal kunne læses uden
    at gaten bliver rød, ellers ender de med at blive slået fra.
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
    runner_findings, runner_warnings = check_runner_pins(root)
    found.extend(runner_findings)
    action_findings, action_warnings = check_action_majors(root)
    found.extend(action_findings)
    if probe_node:
        found.extend(check_running_node(floor, _major_of_running_node()))
    found.extend(check_dependencies(packages))
    return found, action_warnings + runner_warnings + check_eol_soon(packages, today)


def selftest() -> int:
    """Gaten skal kunne fejle. Vi indplanter fejl og kræv at de fanges."""
    floor = 22
    today = date(2026, 9, 26)
    # Den major, handlingerne i de rene fixtures skal sidde på. Sættes den
    # lavere, er det ikke længere et rent repo, og selftesten ville gråne over
    # sit eget fund.
    clean_action = f"actions/setup-node@v{ACTION_MIN_MAJOR['actions/setup-node']}"

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "repo"
        (base / ".github" / "workflows").mkdir(parents=True)
        (base / "eucomply-scanner").mkdir(parents=True)
        (base / "cli").mkdir(parents=True)

        def write_state(engines_floor=floor, nvmrc_major=str(floor), ci=str(floor),
                        drop_nvmrc=False, drop_engines=False, no_ci=False,
                        second_floor=None, ci_comment_only=False, no_node_step=False,
                        extra_uses=None, action_ref=None, runner=RUNNER_IMAGE,
                        drop_runs_on=False, runner_comment_only=False):
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
            # Runner-pinnen skrives i alle grene, så en mutation af node-version
            # eller handlinger ikke også udløser et runner-fund. Ellers ville
            # nålen i hver case ramme den forkerte besked.
            if drop_runs_on:
                pin = ""
            elif runner_comment_only:
                pin = f"    # runs-on: {runner}\n"
            else:
                pin = f"    runs-on: {runner}\n"
            # Fixture'en har to jobs, ligesom repoets rigtige workflows: et
            # genbrugt workflow-kald uden runs-on og et job med pin. En fixture
            # med kun ét job skjulte en falsk grøn, hvor det andet job kunne
            # miste sin pin uden at nogen så det — præcis fejlen mutationen
            # mod repoets egne workflows afdøde.
            reusable_job = "  verify:\n    name: kvalitetsgate\n    uses: ./.github/workflows/verify.yml\n"
            if no_ci:
                wf.unlink(missing_ok=True)
            elif no_node_step:
                # Workflow'en findes, men setup-node-steget er væk. Den ser
                # stadig helt troværdig ud og bygger på runnernes default.
                wf.write_text(
                    "jobs:\n" + reusable_job + "  gate:\n" + pin + "    steps:\n"
                    "      - run: bash tools/quality_gate.sh\n",
                    encoding="utf-8",
                )
            elif ci_comment_only:
                # Kun setup-node og en kommentar der nævner node-version:
                # det så ud til at erklære en runtime uden at gøre det.
                wf.write_text(
                    "jobs:\n" + reusable_job + "  gate:\n" + pin + "    steps:\n"
                    f"      - uses: {clean_action}\n"
                    f"        # historisk node-version: {floor}\n",
                    encoding="utf-8",
                )
            else:
                uses = action_ref or clean_action
                extra = f"      - uses: {extra_uses}\n" if extra_uses else ""
                wf.write_text(
                    "jobs:\n" + reusable_job + "  gate:\n" + pin + "    steps:\n"
                    f"      - uses: {uses}\n        with:\n          node-version: '{ci}'\n"
                    + extra,
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
            # Opgave 13: `node-version: '22'` siger intet om hvilken Node
            # handlingerne selv kører på, så en Node-20-major må fanges her.
            ("handling under sit minimumsmajor", "under minimumsmajor",
             lambda: write_state(action_ref="actions/checkout@v4")),
            ("udokumenteret handling", "står ikke i ACTION_MIN_MAJOR",
             lambda: write_state(extra_uses="acme/build-action@v1")),
            ("flydende action-reference", "flydende reference, der ikke kan efterprøves",
             lambda: write_state(action_ref="actions/setup-node@main")),
            ("action-reference uden @", "uden @-reference",
             lambda: write_state(action_ref="actions/setup-node")),
            ("ingen handling at efterprøve", "slet ikke efterprøves",
             lambda: write_state(no_node_step=True)),
            # Opgave 14: `ubuntu-latest` er et flydende label, og GitHub har
            # dateret migreringen til Ubuntu 26. Uden disse fem cases kunne
            # pin'en glide tilbage, og gaten ville være grøn.
            ("flydende runner-label", "flydende label",
             lambda: write_state(runner="ubuntu-latest")),
            ("forkert fastsat runner-image", "er ikke det fastsatte image",
             lambda: write_state(runner="ubuntu-22.04")),
            ("runner som ikke kan efterprøves", "udtryk, gaten ikke kan efterprøve",
             lambda: write_state(runner="${{ matrix.os }}")),
            ("manglende runs-on i jobbet", "har ingen runs-on",
             lambda: write_state(drop_runs_on=True)),
            ("kommenteret runs-on tæller ikke", "har ingen runs-on",
             lambda: write_state(drop_runs_on=True, runner_comment_only=True)),
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

        # Tælleren tæller sig selv, så en ny kontrol ikke kan komme ind uden at
        # antallet af dækkede fund bliver ved at være sandt.
        extra = 0

        # Værtenes Node-version skal ikke afgøre selftestens udfald, så den
        # prøves direkte med indsprøjtede værdier i stedet.
        if check_running_node((22, None), 20):
            print("selftest: for gammel kørende Node fanget")
            extra += 1
        else:
            print("SELFTEST FEJLED: Node under flooren blev ikke fanget")
            return 1
        if check_running_node((22, None), None) == []:
            print("SELFTEST FEJLED: ulæselig Node-version blev ikke fanget")
            return 1
        print("selftest: ulæselig kørende Node fanget")
        extra += 1

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
        extra += 1

        # En afhængighed uden lockfile betyder en uauditeteret afhængighed.
        (base / "eucomply-scanner" / "package.json").write_text(
            json.dumps({"engines": {"node": ">=22"}, "dependencies": {"left-pad": "1.0.0"}}, indent=2),
            encoding="utf-8",
        )
        if not [f for f in run(base, today, probe_node=False) if "uauditeterede" in f]:
            print("SELFTEST FEJLED: afhængighed uden lockfile blev ikke fanget")
            return 1
        print("selftest: afhængighed uden lockfile fanget")
        extra += 1

        # En floor tæt på EOL skal give en advarsel, ikke et rødt resultat. Sådan
        # fanges det: 2027-02-28 ligger 61 dage før Node 22's EOL 2027-04-30.
        write_state()
        near, near_warnings = collect(base, date(2027, 2, 28), probe_node=False)
        if not any("er EOL om" in w for w in near_warnings):
            print("SELFTEST FEJLED: en major tæt på EOL gav ingen advarsel")
            return 1
        if [f for f in near if "nåede EOL" in f]:
            print("SELFTEST FEJLED: en major tæt på EOL gav et rødt resultat")
            return 1
        print("selftest: major tæt på EOL advarer uden at være rød")
        extra += 1

        # ...og en floor langt fra EOL skal ikke advare om noget, ellers er
        # advarslen støj, og en støjende gate bliver slået fra.
        _, far_warnings = collect(base, today, probe_node=False)
        if far_warnings:
            print("SELFTEST FEJLED: en understøttet floor advarede alligevel:", far_warnings)
            return 1
        print("selftest: understøttet floor giver ingen advarsel")
        extra += 1

        # En handling på en commit-sha er gyldig kode, men majoren kan ikke
        # læses. Det skal siges, uden at gaten bliver rød. Den plantede
        # afhængighed ovenfor fjernes først, så den eneste mutation der er aktiv
        # er den, der testes her.
        for rel in EUCOMPLY_PACKAGES:
            (base / rel).write_text(
                json.dumps({"engines": {"node": f">={floor}"}}, indent=2), encoding="utf-8"
            )
        write_state(action_ref="actions/setup-node@" + "a1b2c3d" + "0" * 33)
        sha_found, sha_warnings = collect(base, today, probe_node=False)
        if not any("commit-sha" in w for w in sha_warnings) or sha_found:
            print("SELFTEST FEJLED: sha-fastsat handling blev ikke advaret om alene")
            return 1
        print("selftest: sha-fastsat handling advaret om, ikke rødt")
        extra += 1

        # Ødelagt JSON må give et fund, ikke et traceback. En gate der
        # fejler med en stacktrace mister alle de andre fund. Den står sidst,
        # fordi den med vilje efterlader en fil, der ikke kan læses.
        (base / "eucomply-scanner" / "package.json").write_text(
            '{ "engines": { "node": ">=22" }', encoding="utf-8"
        )
        broken = run(base, today, probe_node=False)
        if not [f for f in broken if "ikke læses som JSON" in f or "kan ikke læses" in f]:
            print("SELFTEST FEJLED: ødelagt JSON blev ikke fanget som fund")
            return 1
        print("selftest: ødelagt JSON fanget som fund, ikke som crash")
        extra += 1

    print(f"SELFTEST GRØN — alle {len(cases) + extra} negative cases fanges")
    return 0


def dependency_total(packages: list) -> int:
    """Hvor mange afhængigheder der overhovedet er at auditere.

    Begge EUComply-pakker er dependency-free i dag, så udsagnet "ingen
    afhængighed står uden lockfile" er sandt uden at være prøvet. Summen siger
    det i grøn-beskeden, så et grønt resultat ikke lader som om der blev auditet
    noget, der ikke findes — og bliver sandt, den dag en afhængighed tilføjes.
    """
    total = 0
    for _, data in packages:
        for field in ("dependencies", "devDependencies", "optionalDependencies"):
            block = data.get(field)
            if isinstance(block, dict):
                total += len(block)
    return total


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    found, warnings = collect(ROOT)
    if warnings:
        print("RUNTIME-ADVARSLER (gaten er grøn, men dette bør ses):")
        for w in warnings:
            print(f"  ! {w}")
    if found:
        print("RUNTIME-GATE RØD:")
        for f in found:
            print(f"  - {f}")
        print("\nRet dem i ÉN commit: engines + .nvmrc + CI skal vælge samme Node-version.")
        return 1
    packages, _ = load_packages(ROOT)
    print(
        "Runtime-gate grøn: begge pakker, .nvmrc og CI angiver samme understøttte "
        "Node-version, gaten kører på den erklærede runtime, alle EUComply-jobs er "
        f"fastsat på {RUNNER_IMAGE}, ingen handling sidder under sit dokumenterede "
        f"minimum, og {dependency_total(packages)} afhængigheder står uden lockfile."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
