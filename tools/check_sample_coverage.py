#!/usr/bin/env python3
"""Gate: prøverapporten skal dække præcis de checks motoren kører.

    python3 tools/check_sample_coverage.py
    python3 tools/check_sample_coverage.py --selftest

Kæden, og hvor den kan knække:

    shared/scan-engine.js  →  shared/sample-report.json  →  HTML + PDF

Hvert led er en håndhævet regel, så fejlen kan lokaliseres i stedet for at
kunstige. Konkret fund bag gaten: `/pro/sample-report/` viste **7** rækker og
skrev selv `5/7`, "Two items need attention" og "2 Issues found", mens motoren
kører **9** tjek. Den dækkede altså 5 af 9, og de tre den manglede —
Google Consent Mode v2, IAB TCF og third-party trackers — er præcis dem, der
fejler på en rigtig butik. En køber der lige har kørt den gratis scanner så ni
resultater og lander så på en Pro-prøve med syv, oplever den betalte rapport som
*mindre* end den gratis. Det er den modsatte fejlretning af de forrige
opgaver, og her mister vi penge ved at underlove.

Derfor er tallene heller ikke længere håndlavede. Scoren, antallet af beståede,
antallet af fund, datoerne, rapport-id'et og historiklængden står ikke i
HTML'en og ikke i PDF-scriptet — de er afledt af datasættet, og de to
artefakter skrives af samme kode, så de kan ikke komme i uoverensstemmelse.
"""
import datetime as dt
import json
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import build_sample_report as builder  # noqa: E402

PAGE = builder.PAGE
PUBLISHED = os.path.join(ROOT, "site-dist", "pro", "sample-report", "index.html")
PDF = builder.PDF
DATA = builder.DATA

ROW = re.compile(r'data-check="([^"]+)"')
ICON = re.compile(r'<span class="icon (pass|warn|fail)">')
CIRCLE = re.compile(r'<div class="score-circle (?:pass|warn|fail)">(\d+)%</div>')
PASSED = re.compile(r'<span class="value">(\d+)/(\d+)</span>\s*<span class="label">Checks passed</span>')
ISSUES = re.compile(r'<span class="value">(\d+)</span>\s*<span class="label">Items needing attention</span>')
DAYS = re.compile(r'<span class="value">(\d+)</span>\s*<span class="label">Days of history</span>')
BARS = re.compile(r'title="([A-Z][a-z]{2} \d+): (\d+)%"')


def page_findings(keys, summary):
    """Læs den PUBLICEREDE side og kræv at den siger det datasættet siger."""
    findings = []
    if not os.path.exists(PAGE):
        return ["site/pro/sample-report/index.html mangler"]
    with open(PAGE, encoding="utf-8") as handle:
        page = handle.read()
    if builder.START not in page or builder.END not in page:
        return ["site/pro/sample-report/index.html mangler de genererede markører"]
    head, rest = page.split(builder.START, 1)
    block, _ = rest.split(builder.END, 1)
    listed = ROW.findall(block)
    for key in keys:
        if key not in listed:
            findings.append(f"prøverapporten viser ikke tjekket '{key}'")
    for key in listed:
        if key not in keys:
            findings.append(f"prøverapporten viser '{key}', som motoren ikke kører")
    if len(listed) != len(set(listed)):
        findings.append("prøverapporten har en dublet-række")
    icons = ICON.findall(block)
    if len(icons) != len(keys):
        findings.append(f"prøverapporten har {len(icons)} statusser til {len(keys)} tjek")
    circle = CIRCLE.search(block)
    if not circle or int(circle.group(1)) != summary["score"]:
        found = circle.group(1) if circle else "ingen"
        findings.append(f"scoren i cirklen er '{found}', datasættet siger {summary['score']}")
    passed = PASSED.search(block)
    if not passed or (int(passed.group(1)), int(passed.group(2))) != (summary["passed"], summary["total"]):
        found = f"{passed.group(1)}/{passed.group(2)}" if passed else "ingen"
        findings.append(f"'checks passed' er '{found}', datasættet siger {summary['passed']}/{summary['total']}")
    issues = ISSUES.search(block)
    if not issues or int(issues.group(1)) != summary["issues"]:
        found = issues.group(1) if issues else "ingen"
        findings.append(f"'items needing attention' er '{found}', datasættet siger {summary['issues']}")
    days = DAYS.search(block)
    rows = builder.history_rows(json.loads(open(DATA, encoding="utf-8").read()), summary["score"])
    if not days or int(days.group(1)) != len(rows):
        found = days.group(1) if days else "ingen"
        findings.append(f"'days of history' er '{found}', historikken har {len(rows)} dage")
    bars = BARS.findall(block)
    if len(bars) != len(rows):
        findings.append(f"historikken har {len(bars)} bjærker til {len(rows)} dage")
    for (label, value), row in zip(bars, rows):
        if label != row["label"] or int(value) != row["value"]:
            findings.append(f"historie-bjærken '{label}: {value}%' passer ikke til datasættets '{row['label']}: {row['value']}%'")
    return findings


def published_findings(keys):
    """Det publicerede træ skal have de samme rækker — ellers sælger vi en side, der ikke findes."""
    if not os.path.isdir(os.path.dirname(PUBLISHED)):
        return []  # endnu ikke bygget; step 04 i gaten bygger træet før step 05
    with open(PUBLISHED, encoding="utf-8") as handle:
        published = handle.read()
    listed = ROW.findall(published)
    if listed != keys:
        return ["site-dist/pro/sample-report/index.html viser {0} checks {1}, motoren kører {2}".format(
            len(listed), listed, keys)]
    return []


def run_checks():
    findings = []
    data = builder.load_data()
    keys = builder.engine_check_keys()
    findings.extend(builder.coverage_findings(data))
    if not findings:
        findings.extend(page_findings(keys, builder.summarize(data)))
    findings.extend(published_findings(keys))
    # Genérér i en midlertidig mappe og sammenlign byte for byte. Uden
    # `invariant=1` i reportlab ville hver kørsel give et andet fil-id, og så
    # ville denne kontrol være grøn af en fejl.
    with tempfile.TemporaryDirectory() as folder:
        fresh = builder.build_pdf(data, os.path.join(folder, "sample.pdf"))
        with open(fresh, "rb") as new, open(PDF, "rb") as committed:
            if new.read() != committed.read():
                findings.append("site/downloads/eucomply-sample-report.pdf afviger fra datasættet")
    expected = builder.report_block(data)
    with open(PAGE, encoding="utf-8") as handle:
        page = handle.read()
    if builder.START in page and builder.END in page:
        head, rest = page.split(builder.START, 1)
        block, tail = rest.split(builder.END, 1)
        if head + builder.START + "\n" + expected + builder.END + tail != page:
            findings.append("site/pro/sample-report/index.html afviger fra datasættet")
    return findings


def self_test_cases():
    """Negative cases: hver eneste skal fange sin egen mutation."""
    failures = []

    def expect(findings, needle, name):
        if not any(needle in finding for finding in findings):
            failures.append(f"self-test {name}: {needle!r} blev ikke fundet, fandt {findings}")

    def expect_clean(findings, name):
        if findings:
            failures.append(f"self-test {name}: uventede fund {findings}")

    data = builder.load_data()
    keys = builder.engine_check_keys()

    # 1. Selftesten læser den rigtige motor, ikke en konstant.
    if keys != ["consent_mode_v2", "tcf", "trackers", "ssl", "cookies", "forms", "legal", "headers", "dora"]:
        failures.append(f"self-test engine: motoren kører {keys}")

    # 2. Ekstraktoren læser en fil, der ligger på disk — ellers er case 1 værdiløs.
    with tempfile.TemporaryDirectory() as folder:
        fixture = os.path.join(folder, "engine.js")
        with open(fixture, "w", encoding="utf-8") as handle:
            handle.write("  checks.alpha = {\n    pass: true,\n  };\n  checks.beta = { pass: true };\n")
        read = builder.engine_keys(fixture)
        if read != ["alpha", "beta"]:
            failures.append(f"self-test extract: fixture'en gav {read}")
        with open(fixture, "w", encoding="utf-8") as handle:
            handle.write("// checks.alpha = {} — en kommentar er ikke et tjek\nconst other = 1;\n")
        if builder.engine_keys(fixture):
            failures.append("self-test extract comment: et nøgleord i en kommentar blev læst som et tjek")

    # 3. Et tjek motoren kører, men prøverapporten mangler.
    trimmed = json.loads(json.dumps(data))
    trimmed["checks"] = [entry for entry in trimmed["checks"] if entry["key"] != "tcf"]
    expect(builder.coverage_findings(trimmed), "'tcf'", "missing check")

    # 4. Et tjek prøverapporten viser, men motoren ikke kører.
    extra = json.loads(json.dumps(data))
    extra["checks"].append({"key": "accessibility", "title": "Accessibility", "status": "pass", "detail": "x"})
    expect(builder.coverage_findings(extra), "'accessibility'", "extra check")

    # 5. Det samme tjek to gange.
    doubled = json.loads(json.dumps(data))
    doubled["checks"].append(json.loads(json.dumps(doubled["checks"][0])))
    expect(builder.coverage_findings(doubled), "mere end én gang", "duplicate check")

    # 6. En ugyldig status må ikke regnes som bestået.
    bad_status = json.loads(json.dumps(data))
    bad_status["checks"][0]["status"] = "maybe"
    expect(builder.coverage_findings(bad_status), "status 'maybe'", "bad status")

    # 7. Tallene er aflede: ændrer en status, ændrer scoren.
    worse = json.loads(json.dumps(data))
    worse["checks"][0]["status"] = "fail"
    before, after = builder.summarize(data), builder.summarize(worse)
    if (after["score"], after["passed"], after["issues"]) == (before["score"], before["passed"], before["issues"]):
        failures.append("self-test derived: scoren fulgte ikke statusændringen")
    if after["score"] != round(100 * after["passed"] / after["total"]):
        failures.append("self-test derived: scoren er ikke beståede/alle")
    if before["headline"] == after["headline"] and before["failed"] != after["failed"]:
        failures.append("self-test derived: prosaen fulgte ikke et nyt fund")

    # 8. Historiklængden er afledt, ikke en håndlavet "30 dage".
    short = json.loads(json.dumps(data))
    short["history"] = short["history"][:5]
    rows = builder.history_rows(short, builder.summarize(short)["score"])
    if len(rows) != 5:
        failures.append(f"self-test derived history: fem dage gav {len(rows)} rækker")
    elif [row["value"] for row in rows] != short["history"]:
        failures.append("self-test derived history: rækkerne følger ikke listen i datasættet")
    elif rows[-1]["date"] != dt.date.fromisoformat(short["meta"]["generated_iso"]):
        failures.append("self-test derived history: den sidste dag er ikke scannedatoen")
    if len(builder.history_rows(data, builder.summarize(data)["score"])) == 5:
        failures.append("self-test derived history: alle lister længden uafhængigt af data")

    # 9. En bjærke under dagens score giver en note, en perfekt historik gør ikke.
    if builder.dip_note(builder.history_rows(data, 100)) is None:
        failures.append("self-test dip: en historik under dagens score gav ingen note")
    if builder.dip_note(builder.history_rows(data, 40)) is not None:
        failures.append("self-test dip: en historik over dagens score fik en dip-note")

    # 10. Den rigtige kørsel er grøn, og mutationer mod repoets egne filer er røde.
    expect_clean(run_checks(), "clean run")
    with open(PAGE, encoding="utf-8", ) as handle:
        page = handle.read()
    mutated = page.replace('data-check="trackers"', 'data-check="tracker"', 1)
    if mutated == page:
        failures.append("self-test mutation: kunne ikke fjerne rækken fra siden")
    else:
        with open(PAGE, "w", encoding="utf-8") as handle:
            handle.write(mutated)
        try:
            expect(run_checks(), "tracker", "page row removed")
        finally:
            with open(PAGE, "w", encoding="utf-8") as handle:
                handle.write(page)
    with open(PDF, "rb") as handle:
        pdf = handle.read()
    with open(PDF, "wb") as handle:
        handle.write(pdf[:-40] + b"0" * 40)
    try:
        expect(run_checks(), "sample-report.pdf", "pdf changed")
    finally:
        with open(PDF, "wb") as handle:
            handle.write(pdf)
    if run_checks():
        failures.append("self-test revert: repoet er ikke grønt igen efter mutationerne")
    return failures


def main() -> int:
    if "--selftest" in sys.argv:
        failures = self_test_cases()
        for failure in failures:
            print(f"FEJL  self-test: {failure}")
        if failures:
            print(f"\nSELFTEST RØD — {len(failures)} fejl")
            return 1
        print("SELFTEST GRØN — alle negative cases fanges")
        return 0
    findings = run_checks()
    for finding in findings:
        print(f"ERROR {finding}")
    if findings:
        print(f"\n{len(findings)} prøverapport-fund")
        return 1
    print(f"OK: prøverapporten dækker de {len(builder.engine_check_keys())} checks motoren kører, "
          "og HTML + PDF følger datasættet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
