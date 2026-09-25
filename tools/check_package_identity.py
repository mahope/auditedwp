#!/usr/bin/env python3
"""Gat: ingen to pakker i repoet må påstå samme npm-navn.

Baggrund
--------
Dette repo har to mapper med en `package.json`. `eucomply-scanner/` er den
ægte motor, der scanner siden lokalt. `cli/` var en tynd proxy, der viderede
hvert scan til den hosted worker — og den erklærede *samme* npm-navn,
`eucomply-scanner`, i samme version. To forskellige programmer med samme
identitet kan ikke begge publiceres, og hvilken en bruger får ved
`npm install eucomply-scanner` afhænger af, hvem der trykker publish først.

Sitet fortæller brugerne at installere `eucomply-scanner`
(`site/cli/index.html`), så det navn skal høre til den pakke, der er
testet og som har de rettede guards. Det er derfor `eucomply-scanner/`,
der har ret til navnet, og `cli/` der har mistet det.

Identitetskollisionen alene er ikke nok at finde: den skal være umulig at
føre tilbage. Derfor er den her en permanent del af kvalitetsgaten, ikke en
engangsnotering i planen.

Kør:
    python3 tools/check_package_identity.py
    python3 tools/check_package_identity.py --selftest
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Pakker der skal findes. Holdt eksplicit frem for at globbe hele træet, så
# en ny mappe med en package.json ikke kan overtage et navn ved et tilfælde,
# og så en fejlplaceret package.json ikke kan få gaten til at se ingenting.
PACKAGE_FILES = [
    "eucomply-scanner/package.json",
    "cli/package.json",
]

# Mapper der ikke er vores kode og derfor ikke må give fund.
SKIP_DIR_PARTS = {"node_modules", ".git", "site-dist", "__pycache__"}

# Navnet sitet beder brugeren installere. Denne pakke skal være publicerbar
# og have et unikt navn, ellers peger dokumentationen på et vildledende
# sted. Se site/cli/index.html.
DOCUMENTED_PACKAGE = "eucomply-scanner"


def _load(rel):
    """Returnér (data, fejltekst) for en package.json."""
    path = os.path.join(ROOT, rel)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh), None
    except FileNotFoundError:
        return None, "%s mangler" % rel
    except json.JSONDecodeError as exc:
        # Ødelagt JSON må give et fund og ikke et traceback: ellers ville en
        # comma-fejl se ud som at gaten crashede, og resultatet ville være
        # ufortolkeligt.
        return None, "%s er ikke gyldig JSON: %s" % (rel, exc)


def _bin_names(data):
    b = data.get("bin")
    if isinstance(b, str):
        return [os.path.basename(b)]
    if isinstance(b, dict):
        return sorted(b)
    return []


def collect(base=None, extra=None, documented=None):
    """Find alle fund.

    `extra` er en liste af (rel, data) som lægges oven på de rigtige pakker,
    og `documented` kan overskrives. Det er sådan selftesten kan udtrykke
    "den dokumenterede pakke mangler" uden at røre disken.
    """
    base = base or ROOT
    documented = documented or DOCUMENTED_PACKAGE
    findings = []
    loaded = []

    for rel in PACKAGE_FILES:
        relpath = rel if base == ROOT else os.path.join(base, rel)
        try:
            with open(relpath, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError) as exc:
            findings.append("%s: kunne ikke læses som JSON (%s)" % (rel, exc))
            continue
        if not isinstance(data, dict):
            findings.append("%s: JSON'en er ikke et objekt" % rel)
            continue
        loaded.append((rel, data))

    for rel, data in extra or []:
        if not isinstance(data, dict):
            findings.append("%s: kunne ikke læses som JSON" % rel)
            continue
        loaded.append((rel, data))

    # 1. Et navn må kun bruges én gang i repoet.
    by_name = {}
    for rel, data in loaded:
        name = data.get("name")
        if not name:
            findings.append("%s: erklærer intet 'name'" % rel)
            continue
        by_name.setdefault(name, []).append(rel)

    for name, rels in sorted(by_name.items()):
        if len(rels) > 1:
            findings.append(
                "npm-navnet '%s' er erklæret af %d pakker: %s. Kun én kan "
                "ege det navn, og en bruger ved `npm install %s` får kun "
                "den der er publiceret."
                % (name, len(rels), ", ".join(sorted(rels)), name)
            )

    # 2. Den dokumenterede pakke skal findes, være publicerbar og have et
    #    unikt navn — ellers peger site/cli/index.html på det forkerte sted.
    documented_pkgs = [(rel, d) for rel, d in loaded if d.get("name") == documented]
    if not documented_pkgs:
        findings.append(
            "Ingen pakke erklærer navnet '%s', som sitet beder brugeren "
            "installere (site/cli/index.html)." % documented
        )
    else:
        rel, data = documented_pkgs[0]
        if data.get("private") is True:
            findings.append(
                "%s er sat til private, men sitet beder brugerne installere "
                "'%s'." % (rel, documented)
            )
        if len(documented_pkgs) > 1:
            findings.append(
                "'%s' er erklæret af %d pakker — se identitetskollisionen ovenfor."
                % (documented, len(documented_pkgs))
            )

    # 3. En pakke med bin-navne skal have et navn, så `npx <navn>` er
    #    entydigt. Uden det er der ingen måde at se hvad bin'en installerer.
    for rel, data in loaded:
        bins = _bin_names(data)
        if bins and not data.get("name"):
            findings.append("%s: har bin-navne %s uden et pakke-navn" % (rel, ", ".join(bins)))

    return findings


def run(base=None):
    findings = collect(base)
    if findings:
        print("PAKKE-IDENTITET RØD — %d fund:" % len(findings))
        for f in findings:
            print("  FEJL  %s" % f)
        return findings
    print(
        "Pakke-identitet grøn: hver pakke har sit eget npm-navn, og "
        "'%s' — den sitet fortæller brugerne at installere — er den "
        "publicerbare motor." % DOCUMENTED_PACKAGE
    )
    return []


def _fixture(name, version="1.0.0", private=None, **rest):
    d = {"name": name, "version": version}
    if private is not None:
        d["private"] = private
    d.update(rest)
    return d


def selftest():
    """Bevis at gaten kan fejle. Uden dette er et grønt resultat ubevis."""
    cases = []

    def expect_red(label, extra, **kw):
        f = collect(extra=extra, **kw)
        cases.append((label, bool(f)))

    def expect_green(label, extra, **kw):
        f = collect(extra=extra, **kw)
        cases.append((label, not f))

    # Ren udgangspunkt: de to rigtige pakker, ingen kollision.
    expect_green("det virkelige repo er grønt", [])

    # Den kollision der fandtes: to pakker, samme navn.
    expect_red(
        "to pakker med samme npm-navn",
        [("cli/package.json", _fixture("eucomply-scanner"))],
    )

    # Samme navn men den ene privat, så den ikke kan publiceres.
    expect_red(
        "samme navn hvor den ene er privat",
        [("legacy/package.json", _fixture("eucomply-scanner", private=True))],
    )

    # Den dokumenterede pakke forsvinder.
    expect_red("den dokumenterede pakke mangler", [], documented="eucomply-fandtes-ikke")

    # Den dokumenterede pakke er privat, så sitet peger på noget der ikke
    # kan installeres.
    expect_red(
        "den dokumenterede pakke er privat",
        [("x/package.json", _fixture("eucomply-scanner", private=True))],
    )

    # Bin-navne uden pakke-navn: umuligt at se hvad npx vil installere.
    expect_red(
        "bin-navne uden pakke-navn",
        [("x/package.json", {"version": "1.0.0", "bin": {"eucomply": "b.js"}})],
    )

    # Ødelagt JSON må give et fund, ikke et traceback.
    expect_red("uoplæselig package.json", [("x/package.json", None)])
    expect_red("package.json der ikke er et objekt", [("x/package.json", ["eucomply-scanner"])])

    # Bin som streng (npm tillader begge former) skal stadig tælle.
    expect_green(
        "bin som streng er gyldigt",
        [("x/package.json", _fixture("x-tool", bin="bin/x.js"))],
    )

    # To forskellige navne er fint — det er kollisionen, der er fejlen.
    expect_green(
        "to forskellige navne er ikke en kollision",
        [("x/package.json", _fixture("andet-værktøj"))],
    )

    bad = [label for label, ok in cases if not ok]
    for label, ok in cases:
        print("  %s  %s" % ("ok  " if ok else "FANG IKKE", label))
    if bad:
        print("SELFTEST RØD — %d af %d cases blev ikke fanget" % (len(bad), len(cases)))
        return 1
    print("SELFTEST GRØN — alle %d negative cases fanges" % len(cases))
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(1 if run() else 0)
