#!/usr/bin/env python3
"""Mål afstanden mellem den kode der ligger i repoet og den der kører i produktion.

## Hvilket problem den her løser

`site/` bliver deployet ved hver merge til `main`. `worker-scan/` og
`worker-watch/` gør **ikke** — de uploades af et manuelt `wrangler deploy`
(spørgsmål 9 i planen). Det betyder at indholdet på `eucomplypro.com` og
indholdet i de to workers kan glide fra hinanden uden at nogen bliver
underrettet, og ingen eksisterende gate så det.

Det er ikke et hypotetisk problem. Da denne gate blev skrevet, svarede
`eucomply-watch` i produktion `1.0.0`, mens `worker-watch/index.js` erklærede
`1.3.0`. Forskellen på de to er ikke kosmetisk: 1.1.0-1.3.0-ændringerne er
per-check-historik, pass-til-fail-alarmer, SSRF-guarden og ejerskabstokens.
En `GET /status?url=…` uden token var altså stadig **live**, fordi rettelsen
ligger i repoet og ikke i Cloudflare. Planens egen produkttabel sagde
"produktionen kører 1.1.0" — den var fejl, og ingen kunne opdage den.

En fejlretning der er usynlig, bliver ikke rettet. Derfor må afstanden være
målbar i den samme gate der kører før hver merge.

## Hvad der er fatalt, og hvorfor

Fire ting er fejl. Resten er en rapporteret kendsgerning.

1. **Endpointet svarer ikke, eller svarer uden brugbar version.** Så er
   produktet nede for alle brugere, og det er missionens prioritet nr. 1.
2. **Live er lavere end den registrerede gulv-version.** Et rollback i
   Cloudflare, som ingen kan se, uden denne gate.
3. **Live er højere end den erklærede version i repoet.** Så kører produktion
   kode, der ikke findes her, og repoet er ikke længere kilden til sandheden.
   Den farligste variant heraf er en forkert servicenavn: den betyder at den
   uploade er en anden worker end den, der er læst.
4. **Repoet er foran produktion, og afstanden er ikke noteret.** Dette er
   det punkt, der gør gaten til en discipline frem for en rapport. Uden
   registreringen kan en drænet af en ny diff leve videre i en plan uden at
   nogen nogensinde skriver den ned, og næste iteration læser igen en
   produkttabel der er forældet.

En uregistreret forskud afstand er altså *fejl*, selv om den er forklaret og
forventet. Den skal skrives i `tools/production_drift.json` med en begrundelse,
så den er en synlig, gennemgået beslutning frem for en tilstand.

## Registreringen

`tools/production_drift.json` har to oplysninger pr. worker:

- `floor` — den version der senest er **set køre** i produktion. Den er et
  gulv, ikke et mål: produktion må gerne ligge lavere end den, hvis nogen
  ruller tilbage, og det skal gaten så opdage.
- `behind` — den afstand der er kendt og accepteret, med en begrundelse der
  ikke må være tom.

Begge skal opdateres i samme diff som den der ændrer dem, ellers fejler gaten.
At sænke `floor` kræver en begrundelse, fordi det fjerner netop den kontrol
der fanger et rollback.

## Brug

    python3 tools/check_production_drift.py            # mål mod produktion
    python3 tools/check_production_drift.py --offline  # spring netværket over
    python3 tools/check_production_drift.py --selftest # kræv at hver regel kan fejle

Selftesten sætter hver af de fire fejl ind i en kopi af de rigtige filer og
kræver at de fanges. En regel, der ikke kan fejle, er ikke en regel.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "tools" / "production_drift.json"

# Hver worker læses fra sin egen kildefil, så den erklærede version ikke kan
# glide ud af sync med den kode der faktisk er i repoet. Værdierne her er kun
# de to ting et filnavn ikke kan give: hvor koden ligger, og hvilken URL den
# er publiceret på.
WORKERS = (
    {
        "name": "eucomply-scan",
        "source": "worker-scan/index.js",
        "url": "https://eucomply-scan.mahope-eeb.workers.dev/",
        "service": "eucomply-universal-scan",
    },
    {
        "name": "eucomply-watch",
        "source": "worker-watch/index.js",
        "url": "https://eucomply-watch.mahope-eeb.workers.dev/",
        "service": "eucomply-watch",
    },
)

TIMEOUT = 20
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def parse_version(raw: object) -> tuple[int, int, int] | None:
    """Giv en tupel til sammenligning, eller None hvis teksten ikke er en version.

    Bevidst streng: `1.3`, `v1.3.0` og tomme strenge giver None, fordi en gate
    der gætter på en versionsform, holder op med at vide hvad den kontrollerer.
    """
    if not isinstance(raw, str) or not SEMVER.match(raw):
        return None
    major, minor, patch = raw.split(".")
    return (int(major), int(minor), int(patch))


def object_blocks(text: str) -> list[str]:
    """De Objects i `text` der er lukket med klammer, ikke klippet af et regex.

    Et regex som `\\{[^\\{\\}]*\\}` er ikke i stand til at læse denne linje fra
    `worker-watch/index.js`:

        return json({ service: "eucomply-watch", version: "1.3.0", sites: count,
                      endpoints: ["POST /status {url,ownerToken}", …] });

    fordi `endpoints`-arrayet indeholder sine egne klammer. Den første
    implementation af denne gate brugte et sådant regex, og det læste
    scan-workerens version og **ikke** watch-workerens — altså læste den den
    halve del af filerne den skulle dække og sagde grønt. Det er samme
    fejltype som fund 3 i opgave 28, hvor en kommentar holdt en slettet
    funktion alive. Derfor balanceres klammerne her.
    """
    blocks: list[str] = []
    depth = 0
    start = -1
    for index, char in enumerate(text):
        if char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start >= 0:
                    blocks.append(text[start : index + 1])
                    start = -1
    return blocks


def declared_version(source: Path, service: str) -> tuple[str | None, str | None]:
    """Find den version kilden erklærer for `service`.

    Læser `version:`-feltet i det objekt der også nævner servicen, så et
    versionsstrøg i en anden del af filen ikke kan stå for den her. Et objekt
    der nævner servicen med to versioner er tvetydigt og bliver None.
    """
    if not source.is_file():
        return None, f"kildekoden {source.name} findes ikke"
    text = source.read_text(encoding="utf-8", errors="replace")
    versions = set()
    for block in object_blocks(text):
        if f'"{service}"' not in block:
            continue
        found = re.search(r'version:\s*"([^"]+)"', block)
        if found:
            versions.add(found.group(1))
    if not versions:
        return None, f"{source.name} erklærer ingen version for {service}"
    if len(versions) > 1:
        return None, (
            f"{source.name} erklærer {len(versions)} versioner for {service} "
            f"({', '.join(sorted(versions))}) — hvilken der gælder er uklart"
        )
    return versions.pop(), None


def fetch_live(url: str) -> tuple[dict | None, str | None, int | None]:
    """Hent rod-endpointet. Returnér (payload, fejl, http_status).

    En 4xx er **ikke** det samme som "kunne ikke nås". Workeren svarede, den
    svarede bare uden et rod-endpoint — og det er en driftform, der kan
    registreres og lukkes, hvorimod en worker der ikke svarer overhovedet er
    en fejl. Skelnen er derfor eksplicit her frem for i kalderen.
    """
    request = urllib.request.Request(url, headers={"User-Agent": "eucomply-drift-gate/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read().decode("utf-8", errors="replace")
            status = response.status
    except urllib.error.HTTPError as exc:
        # Svar med en krop er stadig et svar: en 404 med en forklarende tekst
        # fortjener at blive læst, fordi netop den tekst er beviset på formen.
        try:
            raw = exc.read().decode("utf-8", errors="replace")
        except Exception:
            raw = ""
        try:
            return json.loads(raw), None, exc.code
        except json.JSONDecodeError:
            return None, f"svarer HTTP {exc.code} uden et JSON-objekt", exc.code
    except Exception as exc:  # netværk, DNS, timeout
        return None, f"kunne ikke nås ({exc.__class__.__name__})", None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None, "svaret er ikke JSON", status
    if not isinstance(payload, dict):
        return None, "svaret er et JSON-objekt uden felter", status
    return payload, None, status


def load_registry(path: Path) -> tuple[dict, str | None]:
    if not path.is_file():
        return {}, f"registreringen {path.name} findes ikke"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, f"{path.name} er ikke gyldig JSON ({exc})"
    if not isinstance(data, dict) or not isinstance(data.get("workers"), dict):
        return {}, f"{path.name} mangler et 'workers'-objekt"
    return data, None


def evaluate(
    root: Path,
    workers: tuple[dict, ...],
    registry: dict,
    live_payloads: dict[str, dict | None],
) -> tuple[list[str], list[str]]:
    """Ren logik, så selftesten kan drive den med vilkårlige data.

    Returnér (fejl, bemærkninger).
    """
    errors: list[str] = []
    notes: list[str] = []
    known = registry.get("workers", {})

    for worker in workers:
        name = worker["name"]
        service = worker["service"]
        source = root / worker["source"]

        version, why = declared_version(source, service)
        if version is None:
            errors.append(f"{name}: {why}")
            continue
        if parse_version(version) is None:
            errors.append(f"{name}: erklærer versionen {version!r}, som ikke er x.y.z")
            continue

        entry = known.get(name)
        if not isinstance(entry, dict):
            errors.append(f"{name}: mangler i {REGISTRY.name} — enhver afstand skal være noteret")
            continue
        floor = parse_version(entry.get("floor"))
        if floor is None:
            errors.append(f"{name}: {REGISTRY.name} har ingen gyldig floor-version for den")
            continue

        reachable, payload = live_payloads.get(name, (None, None))
        if not reachable:
            errors.append(f"{name}: produktion kunne ikke nås — se rådata ovenfor")
            continue

        live_raw = (payload or {}).get("version")
        if live_raw is None:
            # 1.0.0-udgaven af eucomply-scan har intet rod-endpoint, så det
            # er en rigtig driftsform, ikke en fejl i skrivefejlen. Den skal
            # kunne registreres, ellers kan den aldrig lukkes.
            behind = entry.get("behind")
            if isinstance(behind, dict) and behind.get("reason"):
                notes.append(
                    f"{name}: produktion svarer uden version. noteret: {behind['reason']}"
                )
            else:
                errors.append(
                    f"{name}: produktion svarer uden version, og hullet er ikke noteret i "
                    f"{REGISTRY.name}"
                )
            continue

        live = parse_version(live_raw)
        if live is None:
            errors.append(f"{name}: produktion svarer versionen {live_raw!r}, som ikke er x.y.z")
            continue

        live_service = (payload or {}).get("service")
        if live_service is not None and live_service != service:
            errors.append(
                f"{name}: produktion svarer service={live_service!r}, men koden her er {service!r} "
                "— der er en anden worker uploadet end den der læses"
            )
            continue

        if live < floor:
            errors.append(
                f"{name}: produktion kører {live_raw}, under den registrerede floor "
                f"{entry['floor']} — det er et rollback"
            )
            continue
        if live > parse_version(version):
            errors.append(
                f"{name}: produktion kører {live_raw}, men koden her erklærer kun {version} — "
                "produktion har kode der ikke findes i repoet"
            )
            continue
        if live < parse_version(version):
            behind = entry.get("behind")
            reason = behind.get("reason") if isinstance(behind, dict) else None
            if not (isinstance(reason, str) and reason.strip()):
                errors.append(
                    f"{name}: produktion kører {live_raw}, koden her erklærer {version} — "
                    f"afstanden er ikke noteret med en begrundelse i {REGISTRY.name}"
                )
                continue
            notes.append(
                f"{name}: produktion kører {live_raw}, koden her {version}. "
                f"noteret: {reason}"
            )
        else:
            notes.append(f"{name}: produktion kører {live_raw} — samme version som koden her.")

    return errors, notes


def report(live_payloads: dict, errors: list[str], notes: list[str]) -> int:
    for line in notes:
        print(f"  - {line}")
    for name, (reachable, payload) in live_payloads.items():
        if payload is None:
            print(f"  ! {name}: rådata kunne ikke læses")
        else:
            print(f"  · {name}: {json.dumps(payload, ensure_ascii=False)[:160]}")
    if errors:
        print("\nDRIFT-GATE RØD:")
        for line in errors:
            print(f"  - {line}")
        print(
            "\nDeployes en worker manuelt, så opdatér floor og behind i "
            "tools/production_drift.json i samme diff. Sænkes floor, skal begrundelsen med."
        )
        return 1
    print(
        "Drift-gate grøn: hver workers produktionsversion er målt, ingen kører en kode "
        "repoet ikke har, og enhver forskud afstand er noteret med en begrundelse."
    )
    return 0


def check(root: Path, workers: tuple[dict, ...], offline: bool) -> int:
    registry, why = load_registry(root / "tools" / "production_drift.json")
    if why:
        print(f"DRIFT-GATE RØD:\n  - {why}")
        return 1

    if offline:
        print("Drift-gate: springer produktionen over (--offline).")
        # Selv uden netværk skal deklarationen og registreringen være i orden.
        errors = []
        for worker in workers:
            version, reason = declared_version(root / worker["source"], worker["service"])
            if version is None:
                errors.append(f"{worker['name']}: {reason}")
            elif parse_version(version) is None:
                errors.append(f"{worker['name']}: erklærer versionen {version!r}, som ikke er x.y.z")
        if errors:
            print("DRIFT-GATE RØD:")
            for line in errors:
                print(f"  - {line}")
            return 1
        print(f"Drift-gate grøn offline: {len(workers)} workers erklærer en gyldig version.")
        return 0

    live_payloads: dict[str, tuple[bool, dict | None]] = {}
    for worker in workers:
        payload, why, status = fetch_live(worker["url"])
        if why:
            print(f"  ! {worker['name']} ({worker['url']}): {why}")
        live_payloads[worker["name"]] = (why is None, payload)

    errors, notes = evaluate(root, workers, registry, live_payloads)
    return report(live_payloads, errors, notes)


# ------------------------------------------------------------------ selftest

SELFTEST_DOC = """
Selftesten bygger et miniature-repo i en midlertidig mappe med de samme fire
filer som den rigtige gate læser, og kræver at hver af gagens fire fejl fanges
— og at den grønne kørsel forbliver grøn. Uden dette er der ingen evidens for,
at reglerne virker; en gate der ikke kan fejle er en kommentar.
"""


def build_fixture(root: Path, declared: dict[str, str], registry: dict, live: dict) -> Path:
    (root / "tools").mkdir(parents=True, exist_ok=True)
    (root / "worker-scan").mkdir(parents=True, exist_ok=True)
    (root / "worker-watch").mkdir(parents=True, exist_ok=True)
    for name, service in (("worker-scan", "eucomply-universal-scan"), ("worker-watch", "eucomply-watch")):
        key = "eucomply-scan" if "scan" in name else "eucomply-watch"
        version = declared[key]
        (root / name / "index.js").write_text(
            'function json(b, s) { return new Response(JSON.stringify(b)); }\n'
            "async fetch(request) {\n"
            '  const u = new URL(request.url);\n'
            '  if (u.pathname === "/") return json({ service: "%s", version: "%s" });\n'
            "  return json({});\n"
            "}\n" % (service, version),
            encoding="utf-8",
        )
    (root / "tools" / "production_drift.json").write_text(
        json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return root


def selftest() -> int:
    import tempfile

    print("Selftest: drift-gaten skal kunne fejle på fire måder.\n")
    registry = {
        "workers": {
            "eucomply-scan": {"floor": "1.0.0", "behind": {}},
            "eucomply-watch": {"floor": "1.0.0", "behind": {}},
        }
    }
    declared = {"eucomply-scan": "1.0.0", "eucomply-watch": "1.0.0"}
    live_ok = {
        "eucomply-scan": {"service": "eucomply-universal-scan", "version": "1.0.0"},
        "eucomply-watch": {"service": "eucomply-watch", "version": "1.0.0"},
    }
    behind_reason = {"floor": "1.0.0", "behind": {"reason": "worker-deploy venter paa svar 9"}}
    behind_accepted = {
        "workers": {
            "eucomply-scan": dict(behind_reason),
            "eucomply-watch": dict(behind_reason),
        }
    }

    cases = [
        (
            "den grønne kørsel fejler ikke",
            declared,
            registry,
            live_ok,
            0,
        ),
        (
            "regel 1: produktion svarer ikke",
            declared,
            registry,
            {**live_ok, "eucomply-watch": None},
            1,
        ),
        (
            "regel 1b: produktion svarer uden version, og hullet er ikke noteret",
            declared,
            registry,
            {**live_ok, "eucomply-watch": {"service": "eucomply-watch"}},
            1,
        ),
        (
            "regel 1c: produktion svarer uden version, men hullet er noteret",
            declared,
            behind_accepted,
            {**live_ok, "eucomply-watch": {"service": "eucomply-watch"}},
            0,
        ),
        (
            "regel 2: et rollback under floor",
            declared,
            {**registry, "workers": {**registry["workers"], "eucomply-watch": {"floor": "1.1.0", "behind": {}}}},
            live_ok,
            1,
        ),
        (
            "regel 3: produktion kører kode repoet ikke har",
            declared,
            registry,
            {**live_ok, "eucomply-watch": {"service": "eucomply-watch", "version": "2.0.0"}},
            1,
        ),
        (
            "regel 3b: en forkert worker er uploadet",
            declared,
            registry,
            {**live_ok, "eucomply-watch": {"service": "nogen-anden-worker", "version": "1.0.0"}},
            1,
        ),
        (
            "regel 4: uregistreret afstand mellem repo og produktion",
            {**declared, "eucomply-watch": "1.3.0"},
            registry,
            live_ok,
            1,
        ),
        (
            "regel 4b: samme afstand, men noteret med en begrundelse",
            {**declared, "eucomply-watch": "1.3.0"},
            behind_accepted,
            live_ok,
            0,
        ),
        (
            "regel 4c: en tom begrundelse er ikke en begrundelse",
            {**declared, "eucomply-watch": "1.3.0"},
            {**registry, "workers": {**registry["workers"], "eucomply-watch": {"floor": "1.0.0", "behind": {"reason": "   "}}}},
            live_ok,
            1,
        ),
        (
            "regel 5: en worker uden registrering",
            declared,
            {"workers": {"eucomply-scan": {"floor": "1.0.0", "behind": {}}}},
            live_ok,
            1,
        ),
        (
            "regel 6: kildekoden erklærer ingen version",
            {"eucomply-scan": "", "eucomply-watch": "1.0.0"},
            registry,
            live_ok,
            1,
        ),
        (
            "regel 7: to forskellige versioner for samme service",
            {"eucomply-scan": "1.0.0", "eucomply-watch": ""},
            registry,
            live_ok,
            1,
        ),
        (
            "en version der ikke er x.y.z",
            {**declared, "eucomply-watch": "1.3"},
            registry,
            live_ok,
            1,
        ),
    ]

    passed = 0
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        for index, (label, decl, reg, live, expected) in enumerate(cases):
            root = Path(tmp) / f"case{index}"
            build_fixture(root, decl, reg, live)
            wrapped = {k: (True, v) for k, v in live.items()}
            errors, _ = evaluate(root, WORKERS, reg, wrapped)
            got = 1 if errors else 0
            if got == expected:
                passed += 1
                print(f"  OK    {label}")
            else:
                failures.append(label)
                print(f"  FEJL  {label} — forventede exit {expected}, fik {got}")
                for line in errors[:3]:
                    print(f"          {line}")

    print()
    if failures:
        print(f"SELFTEST RØD — {len(failures)} af {len(cases)} cases fejlede:")
        for label in failures:
            print(f"  - {label}")
        return 1
    print(f"SELFTEST GRØN — alle {len(cases)} negative cases fanges.")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    offline = "--offline" in sys.argv
    return check(ROOT, WORKERS, offline)


if __name__ == "__main__":
    raise SystemExit(main())
