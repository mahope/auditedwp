#!/usr/bin/env python3
"""Mål den rigtige rapport — den alle besøgende får — mod motoren i repoet.

## Hvilket problem den her løser

Den gratis scanner er tragten, og `worker-scan` er det eneste endpoint alle
besøgende rammer. Alt indholdet i `shared/scan-engine.js` bliver til et
**resultat kunden læser og en rettelse de tror på** — ikke til en
implementationsdetalje. Derfor er det den dyreste fejlklasse i hele repoet,
når den er i motoren.

Målt 2026-09-27 22:35 UTC, tre offentlige sider, arbejderens egen User-Agent:

| mål | live worker | motoren i repoet |
|---|---|---|
| `github.com` | `Consent platform: TarteAuCitron / Klaro / Osano / CookieConsent` (pass) | `No consent banner detected` (warn) |
| `dr.dk` | `Consent platform: Cookiebot / OneTrust / Usercentrics / ConsentManager` (pass) | `Consent platform: Cookiebot` (pass) |
| `shopify.com` | `No consent banner detected` (warn) | `No consent banner detected` (warn) |

**Fundet: den live worker kører `027fc40` før den.** Rækkerne blev skrevet om
til én leverandør pr. række i `027fc40` (plugin 1.3.36), og den gamle kode
findes stadig i repoets historie som **navn** i stedet for som mønster:

    { re: /tarteaucitron|klaro|osano|cookieconsent/i, name: "TarteAuCitron / Klaro / Osano / CookieConsent" }

Den har *fire* leverandøre i én række, så `consentMatches[0]` er hele
navnet. Kunden får at vide den kører fire samtykkeplatforme, hvoraf der er
én — og på `github.com`, hvor den korrekte svar er "ingen", får den at vide
den kører fire. Det er **pass på en række, der skal være warn**, altså en
grøn dom på en side uden samtykkeplatform.

Målt i `github.com`s egen markup (576 275 B, samme UA som arbejderen bruger):
`cookieconsent` 1 forekomst, `tarteaucitron` 0, `klaro` 0, `osano` 0.

## Hvorfor dette ikke var dækket

Der er tre gates, der alle læser **repoet**: `check_signature_prose.mjs`
(mønstre mod navne), `check_published_engine.mjs` (publiceret npm-motor mod
motoren her) og `check_production_drift.py` (site-filer mod produktion).
Ingen af dem læser **den rapport en besøgende faktisk får**. R5-reglen
(R11) forbyder flere leverandøre i én række — men den tester *mønsteret i
koden*, ikke *den udgivne motor*, så den er grøn mens den dyre fejl er live
for hver besøgende.

## Hvad den her gate kan og ikke kan håndhæve

Rettelsen er ikke mere kode: `worker-scan/` skal deployes, og det kan en
agent ikke (`wrangler whoami` svarer "You are not authenticated", spørgsmål
9). Så en afvigelse mellem live og repo er en **RAPPORT**, ikke et fund —
samme stilling som `KNOWN_LAG` (opgave 38) og `unsold_products()`
(opgave 37): en permanent rød gate ville låse hvert merge og dermed hele
sitets deploy, præcis skaden opgave 35 lavede.

Det der KAN håndhæves, er den anden side, og den er den vigtige:

1. **Aftalen skal være målbar.** Uden en forventning kan en afvigelse ikke
   skelnes fra en fejl, og porten ville grønne en regression der *ligner*
   den kendte drift. Derfor ligger forventningen i `tools/funnel_drift.json`
   med den målte værdi, den målte tid og de prøver den blev taget med.
2. **Uden en undtagelse skal den være rød.** En ny afvigelse, der ikke står
   i filen, er et fund — ellers forsvinder den næste fejl i det samme
   mørke som denne.
3. **Undtagelsen skal kunne lukkes.** Når workeren er deployet, skal aftalen
   blive den *fælles* etiket, og selftesten bekræfter at den kan det, så den
   ikke kan blive stående som en løgn.

Kør:
    python3 tools/check_live_funnel.py
    python3 tools/check_live_funnel.py --selftest
    python3 tools/check_live_funnel.py --offline   # spring live-kaldet over
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN_URL = "https://eucomply-scan.mahope-eeb.workers.dev/scan?url="
ENGINE = os.path.join(ROOT, "shared", "scan-engine.js")
AGREEMENT = os.path.join(ROOT, "tools", "funnel_drift.json")
TIMEOUT = 25

# Samme UA som shared/scan-engine.js bruger, så målingen rammer den samme
# markup som den udgivne motor gør. En måling med en anden UA ville måle en
# anden side, og en gate der måler en anden side er ikke en gate.
UA = "Mozilla/5.0 (compatible; EUComplyScan/1.0; +https://auditedwp.pages.dev)"

NODE_BIN = "node"

# De rækker hvis etiket kunden læser. Vi måler ikke hele rapporten: en
# etiket der er formuleret forskelligt uden at være fejl er et
# drift-spørgsmål, ikke et fund (samme stilling som opgave 37/38 og som
# `check_verdict_labels.mjs` tager til formuleringer).
CHECKS = ("cookies",)


def _node():
    """Find node. Gateen kalder den, så mangler den skal siges højt."""
    from shutil import which
    found = which(NODE_BIN)
    if not found:
        raise RuntimeError("node ikke fundet på PATH")
    return found


def fetch(url):
    """GET med arbejderens egen UA. Returnér (status, krop, fejl)."""
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status, response.read().decode("utf-8", "replace"), None
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace"), None
    except Exception as exc:  # noqa: BLE001 - netværk skal give en note, ikke en fejl
        return None, "", str(exc)


def labels_from_report(body):
    """{check: label} fra en rapport-JSON. Tom dict hvis svaret ikke er en rapport."""
    try:
        report = json.loads(body)
    except (TypeError, ValueError):
        return {}
    checks = report.get("checks")
    if not isinstance(checks, dict):
        return {}
    out = {}
    for name in CHECKS:
        row = checks.get(name)
        if isinstance(row, dict) and isinstance(row.get("label"), str):
            out[name] = row["label"]
    return out


def run_local_engine(target, node_bin):
    """Kør motoren i repoet på samme mål og returnér {check: label}."""
    code = (
        "import(process.argv[1]).then(async m => {"
        "  const r = await m.runScan(process.argv[2]);"
        "  const out = {};"
        "  for (const k of process.argv[3].split(',')) {"
        "    if (r.checks && r.checks[k] && typeof r.checks[k].label === 'string')"
        "      out[k] = r.checks[k].label;"
        "  }"
        "  process.stdout.write(JSON.stringify(out));"
        "}).catch(e => { process.stderr.write(String(e && e.message || e)); process.exit(3); });"
    )
    import subprocess
    proc = subprocess.run(
        [node_bin, "--input-type=module", "-e", code,
         ENGINE, target, ",".join(CHECKS)],
        capture_output=True, text=True, timeout=TIMEOUT + 15, cwd=ROOT,
    )
    if proc.returncode != 0:
        raise RuntimeError("motoren i repoet fejlede: %s" % (proc.stderr.strip() or proc.returncode))
    return json.loads(proc.stdout or "{}")


def compare(case, live_labels, repo_labels):
    """Sammenlign ét måls to etiketter. Returnér (fund, noter).

    Ren funktion, så selftesten kan ramme **sammenligningen** med syntetiske
    etiketter. Det er den eneste måde at bevise at porten kan blive rød på
    en afvigelse den ikke kender, uden at være afhængig af et netværk der
    en dag ikke svarer.
    """
    findings, notes = [], []
    case_id = case.get("id", "?")
    target = case.get("target", "?")
    drift = case.get("drift") or {}

    for check, live_label in sorted(live_labels.items()):
        repo_label = repo_labels.get(check)
        if repo_label is None:
            notes.append("%s/%s: motoren i repoet gav ingen etiket — ikke målt" % (target, check))
            continue
        if live_label == repo_label:
            continue
        known = drift.get(check)
        if isinstance(known, dict) and known.get("live") == live_label:
            notes.append(
                "%s/%s AFDVIGER og er registreret: live %r, repo %r (målt %s, %s)"
                % (target, check, live_label, repo_label,
                   known.get("measured", "?"), known.get("because", "uden forklaring"))
            )
        else:
            findings.append(
                "%s/%s afviger UDEN at være registreret: live %r, repo %r. "
                "En ny afvigelse er et fund, ikke drift."
                % (target, check, live_label, repo_label)
            )
    return findings, notes


def collect(live=True):
    """Mål live mod repo. Returnér (fund, noter, facts)."""
    findings, notes, facts = [], [], {}

    try:
        agreement = json.load(open(AGREEMENT, encoding="utf-8"))
    except (OSError, ValueError) as exc:
        findings.append(
            "%s kunne ikke læses (%s). Uden aftalen kan en afvigelse ikke skelnes "
            "fra en fejl, så porten ville grønne en regression." % (AGREEMENT, exc)
        )
        return findings, notes, facts

    expected = {c["id"]: c for c in agreement.get("cases", []) if isinstance(c, dict)}
    if not expected:
        findings.append(
            "%s indeholder ingen cases. Aftalen skal måle hvilke(r) række(r) der "
            "er fundet at afvige, ellers er porten tom." % AGREEMENT
        )
        return findings, notes, facts

    if not live:
        notes.append("offline: live-kaldet er sprunget over, kun filen er læst")
        for case_id, case in expected.items():
            if not isinstance(case.get("target"), str) or not case["target"]:
                findings.append("case %s mangler 'target' i aftalen" % case_id)
        return findings, notes, {"cases": len(expected), "measured": 0}

    try:
        node_bin = _node()
    except RuntimeError as exc:
        notes.append("node mangler: %s — live-målingen er sprunget over" % exc)
        return findings, notes, {"cases": len(expected), "measured": 0}

    measured = 0
    for case_id, case in expected.items():
        target = case.get("target")
        if not isinstance(target, str) or not target:
            findings.append("case %s mangler 'target' i aftalen" % case_id)
            continue

        status, body, error = fetch(SCAN_URL + urllib.parse.quote(target, safe=""))
        if error or status != 200:
            notes.append("%s: live svarede %s (%s) — ikke målt" % (target, status, error or "ingen rapport"))
            continue

        live_labels = labels_from_report(body)
        if not live_labels:
            notes.append("%s: live svarede uden læselig rapport — ikke målt" % target)
            continue

        try:
            repo_labels = run_local_engine(target, node_bin)
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            notes.append("%s: motoren i repoet kunne ikke køres (%s) — ikke målt" % (target, exc))
            continue

        measured += 1
        case_findings, case_notes = compare(case, live_labels, repo_labels)
        findings.extend(case_findings)
        notes.extend(case_notes)

    facts["cases"] = len(expected)
    facts["measured"] = measured
    return findings, notes, facts


def _expect_red(name, mutate, must_mention, extra):
    """Kør porten på en mutation af repoets egne filer og kræv RØD.

    Vendt sandheden, ikke en lokal variabel: en tidligere `_expect_red` i
    check_asset_delivery.py satte `ok = False` på en lokal kopi, så kalderen
    troede alle cases var grønne, og selftesten printede GRØN mens seks af
    dem fejlede. Derfor returnerer den her altid sandhed, og kalderen summerer
    selv.
    """
    files = {}
    for rel, new_text in mutate.items():
        path = os.path.join(ROOT, rel)
        with open(path, encoding="utf-8") as fh:
            files[rel] = fh.read()
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new_text)
    try:
        findings, _notes, _facts = collect(live=False)
        findings = findings + extra()
    finally:
        for rel, old_text in files.items():
            with open(os.path.join(ROOT, rel), "w", encoding="utf-8") as fh:
                fh.write(old_text)

    if not findings:
        return (name, False, "%s blev GRØN — mutationen blev ikke fanget" % name)
    if must_mention and not any(must_mention in f for f in findings):
        return (name, False, "%s blev rød med en anden besked end forventet: %s" % (name, findings[0]))
    return (name, True, "%s fanget: %s" % (name, findings[0]))


def _selftest():
    """Negative cases. Alle muterer repoets egne filer og kræver rød."""
    cases = []
    with open(AGREEMENT, encoding="utf-8") as fh:
        good = fh.read()
    engine = open(ENGINE, encoding="utf-8").read()

    # 1. Grøn baseline: aftalen er gyldig. Uden denne er de øvrige cases
    #    meningsløse, fordi de alle ville være røde af den samme grund.
    findings, _n, _f = collect(live=False)
    cases.append(("baseline: en gyldig aftale er grøn", not findings, str(findings[:1])))

    # 2. Aftalen ugyldig JSON -> rød. Uden den er porten tom. (`"{}"` er
    #    gyldig JSON og giver derfor case 3's besked, ikke denne — mutationen
    #    skal ramme den fejl den egentlig vil provokere.)
    cases.append(_expect_red(
        "aftalen beskadiget",
        {os.path.relpath(AGREEMENT, ROOT): "{ ikke json"},
        "kunne ikke læses",
        lambda: [],
    ))

    # 3. Aftalen uden cases -> rød. En aftale uden cases måler ingenting.
    cases.append(_expect_red(
        "aftalen uden cases",
        {os.path.relpath(AGREEMENT, ROOT): json.dumps({"version": 1, "cases": []}, indent=2)},
        "indeholder ingen cases",
        lambda: [],
    ))

    # 4. Den afvigelse der AVGER porten: en live-etiket der ikke står i
    #    aftalen. Det er den eneste fejl der betyder noget, så den skal kunne
    #    faae porten redt. Sammenligningen kaldes med de RIGTIGE labels fra
    #    aftalen og en live-etiket der ikke er der — ikke en stub, der
    #    altid svarer sandt.
    known_case = json.loads(good)["cases"][0]
    _f, _n = compare(known_case,
                     {"cookies": "Consent platform: Noget Helt Andet"},
                     {"cookies": "No consent banner detected"})
    cases.append((
        "uregistreret afvigelse er rød",
        bool(_f) and "UDEN at være registreret" in _f[0],
        str(_f[:1]),
    ))

    # 5. Samme case med den REGISTREREDE live-etiket: samme kode skal give en
    #    note, ikke et fund. Uden denne kunne en agent gøre porten grøn ved
    #    at slette aftalen, og så ville den dyre fejl være usynlig igen.
    _f2, n2 = compare(known_case,
                      {"cookies": known_case["drift"]["cookies"]["live"]},
                      {"cookies": "No consent banner detected"})
    cases.append((
        "registreret afvigelse er en note, ikke et fund",
        not _f2 and any("AFDVIGER og er registreret" in x for x in n2),
        "fund=%s noter=%s" % (_f2[:1], n2[:1]),
    ))

    # 6. Ens etiketter giver hverken fund eller note — ellers ville porten
    #    være rød for en worker der gør det rigtige.
    _f3, n3 = compare(known_case,
                      {"cookies": "No consent banner detected"},
                      {"cookies": "No consent banner detected"})
    cases.append((
        "ens etiketter giver hverken fund eller note",
        not _f3 and not n3,
        "fund=%s noter=%s" % (_f3[:1], n3[:1]),
    ))

    # 7. En case uden 'target' -> rød.
    cases.append(_expect_red(
        "case uden target",
        {os.path.relpath(AGREEMENT, ROOT): good.replace('"target": "github.com"', '"targt": "github.com"')},
        "mangler 'target'",
        lambda: [],
    ))

    ok = True
    for name, passed, detail in cases:
        print("   %s  %s%s" % ("OK  " if passed else "FEJL", name, "" if passed else "  — " + str(detail)))
        if not passed:
            ok = False
    return ok


def main(argv):
    if "--selftest" in argv:
        return 0 if _selftest() else 1

    offline = "--offline" in argv
    findings, notes, facts = collect(live=not offline)
    for n in notes:
        print("   NOTE  %s" % n)
    for f in findings:
        print("   FUND  %s" % f)

    if findings:
        print("FUNNEL-GATE RØD — %d fund" % len(findings))
        return 1
    print("FUNNEL-GATE GRØN — %d cases i aftalen, %d målt live, ingen uregistreret afvigelse"
          % (facts.get("cases", 0), facts.get("measured", 0)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
