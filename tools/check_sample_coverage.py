#!/usr/bin/env python3
"""Gate: prøverapporten skal dække præcis de checks motoren kører.

    python3 tools/check_sample_coverage.py
    python3 tools/check_sample_coverage.py --selftest

Kæden, og hvor den kan knække:

    shared/scan-engine.js  →  shared/sample-report.json  →  HTML + PDF

Hvert led er en håndhævet regel, så fejlen kan lokaliseres i stedet for at
kunstige. Konkret fund bag gaten: den gamle `/pro/sample-report/` viste **7** rækker og
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

PDF'en efterprøves på **indhold**, ikke på bytes, og det er ikke en
småting: `reportlab` bruges til at GENERERE PDF'en, men CI har ingen
pip-afhængigheder, så en gate der kræver reportlab for at læse sit eget
artefakt døde med en traceback og gjorde `main` rød på `deploy-site` 26/9.
Indholdet læses derfor med standardbiblioteket (`builder.pdf_text`), hvilket
også gør resultatet uafhængigt af reportlab-versionen. Byte-sammenligningen
med en regenereret PDF kører stadig, men kun hvor reportlab findes, og siger
det tydeligt når den springes over. Selftesten kører gaten i en subprocess hvor
importen er blokeret, så "den kan køre i CI" er en egenskab der efterprøves
og ikke en antagelse.

Vendt 22/11-2026 (salget lukket, EUComply frosset som gratis open source).
`/pro/sample-report/` er slettet og redirectet, så alle regler der kun handlede
om HTML-siden er slettet med den: rækkerne, cirklen, "checks passed", den delte
tale, historikbjælkerne, det publicerede træ og sammenligningen med builderens
blok. Det der er tilbage er kæden motor → datasæt → PDF, for PDF'en
(`site/downloads/eucomply-sample-report.pdf`) er stadig publiceret som et
eksempel på hvad den gratis scanner viser.

Ny regel, mærket `[salg]`: PDF'ens tekst må ikke sælge. Den må hverken henvise
til de slettede sider (`eucomplypro.com/pro`, `/pricing`, `/store`), vise en pris
eller et betalingslink, eller nævne Pro uden at sige at det ikke sælges længere.
Reglerne er `tools/no_sales.py`'s, så de dømmer det samme som resten af gaten.
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

sys.path.insert(0, os.path.join(ROOT, "tools"))

import build_sample_report as builder  # noqa: E402
import no_sales  # noqa: E402

PDF = builder.PDF
DATA = builder.DATA

BANDS = re.compile(r"\b(PASS|WARN|FAIL)\b")
BAND_WORD = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}

# PDF'en skriver adresser uden `https://`, så no_sales' linkregex rammer dem ikke.
PDF_CLOSED_LINK = re.compile(
    r"eucomplypro\.com/(?:(?:da|de|fr|es)/)?(?:pricing|pro|store|vs)\b", re.I)
SALES_TAG = "[salg]"

# Ting der IKKE skal være fund, men skal siges. `reportlab` bruges kun til at
# GENERERE PDF'en; gaten læser den committede med stdlib, så den kører overalt.
NOTICES = []


def reportlab_missing():
    try:
        import reportlab  # noqa: F401
    except ImportError:
        return True
    return False


def pdf_findings(data, summary, sales=True):
    """Den PDF købere henter skal sige præcis det datasættet siger.

    Indhold, ikke bytes. Det er den kontrol der kan køre i CI: byte-sammenligning
    afhænger af reportlab-versionen, og to maskiner med hver sin version ville
    give en rød, der intet siger om produktet. Alt hvad der er afledt — scoren,
    beståede/total, fund, dage, prosaen, rapport-id'et, datoen, de ni titler og
    statusserne i rækkefølge — skal kunne *læses* i den fil der ligger i træet.
    """
    if not os.path.exists(PDF):
        return ["site/downloads/eucomply-sample-report.pdf mangler"]
    try:
        text = builder.pdf_text(PDF)
    except (ValueError, OSError) as error:
        # Ulæselig er et FUND, ikke et spring. En kontrol der ikke kan læse
        # sit artefakt må ikke blive grøn ved at tie om det.
        return ["site/downloads/eucomply-sample-report.pdf kunne ikke læses: {0}".format(error)]
    if not text.strip():
        return ["site/downloads/eucomply-sample-report.pdf indeholder ingen tekst"]

    findings = pdf_sales_findings(text) if sales else []
    _, stamp, report_id = builder.generated_stamp(data)
    rows = builder.history_rows(data, summary["score"])
    noun = "item" if summary["issues"] == 1 else "items"
    # reportlab bryder en lang linje i én `(…)`-streng pr. visuel linje, så et
    # 150-tegns fix-embleme står i PDF'en som fire strenge med linjeskift
    # imellem. Uden denne sammenligning ville de to længste fund se ud til at
    # mangle i en PDF der faktisk indeholder dem — en grå mine, fordi
    # "Rapporten mangler en anbefaling" er aldrig den besked man vil sende.
    flat = re.sub(r"\s+", " ", text)

    def need(needle, label):
        if re.sub(r"\s+", " ", needle) not in flat:
            findings.append("PDF'en viser ikke {0} ('{1}')".format(label, needle))

    need("{0} — the same checks the scanner runs".format(summary["total"]), "hvor mange tjek rapporten har")
    need("{0}%".format(summary["score"]), "scoren")
    need("{0}/{1}".format(summary["passed"], summary["total"]), "beståede/total")
    need("{0} {1}".format(summary["issues"], noun), "antallet af fund")
    need("{0} days".format(len(rows)), "historiklængden")
    need(summary["headline"], "prosaen over scoren")
    need(report_id, "rapport-id'et")
    need(stamp, "datoen rapporten blev genereret")
    need(data["disclaimer"], "disclaimeren")
    for entry in data["checks"]:
        need(entry["title"], "tjekket '{0}'".format(entry["key"]))
    for entry in builder.recommended_fixes(data):
        need(entry["fix"], "fixen for '{0}'".format(entry["key"]))
    bands = BANDS.findall(text)
    expected = [BAND_WORD[entry["status"]] for entry in data["checks"]]
    if bands != expected:
        findings.append("PDF'ens statusser er {0}, datasættet siger {1}".format(bands, expected))
    return findings


def pdf_sales_findings(text, label="site/downloads/eucomply-sample-report.pdf"):
    """PDF'en er et gratis eksempel; den må ikke sælge noget eller pege på en købsvej."""
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]
    flat = " ".join(lines)
    findings = []
    for link in sorted({match.group(0) for match in PDF_CLOSED_LINK.finditer(flat)}):
        findings.append("{0} {1}: henviser til den lukkede side {2}".format(SALES_TAG, label, link))
    for link in no_sales.checkout_links(flat):
        findings.append("{0} {1}: betalingslink {2}".format(SALES_TAG, label, link))
    findings.extend("{0} {1}".format(SALES_TAG, finding) for finding in no_sales.price_findings(label, lines))
    findings.extend("{0} {1}".format(SALES_TAG, finding) for finding in no_sales.pro_findings(label, lines))
    return findings


def run_checks(verify_bytes=True, sales=True):
    """`verify_bytes=False` er den sti CI går ad, hvor reportlab mangler.

    Selftesten bruger den med vilje: ellers ville de negative cases for
    PDF-ens *indhold* blive fanget af byte-sammenligningen, fordi en udvikler-
    maskine tilfældigvis har reportlab, og så ville de cases være grønne af en
    fejl. Det er præcis det fund denne iteration lukker.
    """
    del NOTICES[:]
    findings = []
    data = builder.load_data()
    findings.extend(builder.coverage_findings(data))
    summary = builder.summarize(data)
    # Indholdschecket kører ALTID, med eller uden reportlab. Det er den
    # invariant CI kan holde, og det er den der fanger "datasættet blev ændret
    # men PDF'en ikke regenereret".
    findings.extend(pdf_findings(data, summary, sales=sales))
    # Byte-sammenligningen er en ekstra, kun hvor reportlab findes. Uden
    # `invariant=1` ville hver kørsel give et andet fil-id, og så ville den være
    # grøn af en fejl; og den afhænger af reportlab-versionen, så to maskiner
    # ville give forskellige svar om det samme produkt.
    if not verify_bytes or reportlab_missing():
        NOTICES.append("PDF-teksten er læst og efterprøvet; byte-sammenligning med en "
                       "regenereret PDF er sprunget over, fordi reportlab ikke er installeret")
    else:
        with tempfile.TemporaryDirectory() as folder:
            fresh = builder.build_pdf(data, os.path.join(folder, "sample.pdf"))
            with open(fresh, "rb") as new, open(PDF, "rb") as committed:
                if new.read() != committed.read():
                    findings.append("site/downloads/eucomply-sample-report.pdf afviger fra datasættet")
    return findings


def _block_reportlab(folder):
    """En mappe hvor `import reportlab` fejler — som i CI, der har ingen pip-afhængigheder."""
    package = os.path.join(folder, "reportlab")
    os.makedirs(package, exist_ok=True)
    with open(os.path.join(package, "__init__.py"), "w", encoding="utf-8") as handle:
        handle.write("raise ImportError('reportlab er ikke installeret (simuleret)')\n")


def _gate_subprocess(shim):
    env = dict(os.environ)
    if shim:
        env["PYTHONPATH"] = shim + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools", "check_sample_coverage.py")],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )


def _without_reportlab_cases():
    """Selftesten skal køre gaten i det miljø, den døde i.

    Fundet bag denne iteration: `check_sample_coverage.py` blev skrevet og
    deklareret grøn på en maskine med reportlab, og **aldrig kørt i CI** — hvor
    `from reportlab.lib import colors` kastede ModuleNotFoundError. Gaten døde
    med en traceback, `main` nåede aldrig `return 1`, og `deploy-site` blev rød
    på en merge der ellers var korrekt. En selftest der kun kører hvor
    afhængigheden findes, kan ikke fange præcis den fejl.

    Derfor køres her to rigtige subprocess-kørser med importen blokeret:
    rent repo skal være **grønt** (og sige at byte-sammenligningen blev sprunget
    over, så vi ved at den virkelig gik den vej), og et muteret datasæt skal være
    **rødt** — altså at PDF'en stadig efterprøves uden reportlab.
    """
    failures = []
    with open(DATA, encoding="utf-8") as handle:
        original_data = handle.read()
    with tempfile.TemporaryDirectory() as folder:
        _block_reportlab(folder)
        clean = _gate_subprocess(folder)
        # En `[salg]`-rest (PDF'en peger stadig på en lukket side) er en rigtig rød
        # i gaten, men den siger intet om om gaten kan køre uden reportlab. Alt
        # andet end den skal være grønt, og en traceback er aldrig tilladt.
        other = [line for line in clean.stdout.splitlines()
                 if line.startswith("ERROR ") and SALES_TAG not in line]
        if clean.returncode not in (0, 1) or other or "Traceback" in clean.stderr:
            failures.append("self-test uden reportlab: det rene repo gav exit {0}: {1}".format(
                clean.returncode, (clean.stdout + clean.stderr).strip()[-400:]))
        elif "sprunget over" not in clean.stdout:
            failures.append("self-test uden reportlab: rapportlab-blokeringen virkede ikke, "
                            "byte-sammenligningen kørte alligevel — så casen prøvede ingenting")

        stale = json.loads(original_data)
        stale["checks"][0]["status"] = "fail"
        with open(DATA, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(stale, ensure_ascii=False, indent=2))
        try:
            dirty = _gate_subprocess(folder)
        finally:
            with open(DATA, "w", encoding="utf-8") as handle:
                handle.write(original_data)
        if dirty.returncode == 0:
            failures.append("self-test uden reportlab: et datasæt der ikke matcher PDF'en "
                            "gav exit 0 — altså blev PDF'en slet ikke efterprøvet")
        elif "prøverapport-fund" not in dirty.stdout:
            failures.append("self-test uden reportlab: den røde kørsel skyldtes ikke prøverapporten: {0}".format(
                (dirty.stdout + dirty.stderr).strip()[-400:]))
    return failures


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

    # 10. Mutationer mod repoets egne filer er røde, og en kørsel uden dem er
    # grøn. `sales=False` fordi repoets PDF kan have en rest fra før frysningen
    # (en fodlinje der peger på /pro); den regel prøves for sig i punkt 12, og
    # her må en rest ikke gøre alle de andre cases røde.
    expect_clean(run_checks(sales=False), "clean run")
    # Samme kørsel uden byte-sammenligning: den skal være grøn, fordi den er
    # den sti CI går ad.
    expect_clean(run_checks(verify_bytes=False, sales=False), "clean run without reportlab")
    # 10b. Datasættet ændret, PDF'en ikke regenereret. Det er den mutation der
    # fanger "en ændret kunne ikke huske at bygge PDF'en", og den skal være rød
    # UDEN reportlab — ellers er CI's eneste PDF-kontrol en illusion.
    with open(DATA, encoding="utf-8") as handle:
        original_data = handle.read()
    stale = json.loads(original_data)
    stale["checks"][0]["status"] = "fail"
    with open(DATA, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(stale, ensure_ascii=False, indent=2))
    try:
        # Naalen er "PDF'en viser ikke" og ikke filnavnet: kun `pdf_findings`
        # siger det, så casen kan ikke blive grøn af HTML-kontrollen.
        expect(run_checks(verify_bytes=False, sales=False), "PDF'en viser ikke",
               "dataset changed, pdf not rebuilt (content path only)")
    finally:
        with open(DATA, "w", encoding="utf-8") as handle:
            handle.write(original_data)
    # 10c. En PDF der ikke kan læses er et fund, ikke et spring.
    with open(PDF, "rb") as handle:
        pdf = handle.read()
    with open(PDF, "wb") as handle:
        handle.write(pdf[: len(pdf) // 2])
    try:
        expect(run_checks(verify_bytes=False, sales=False), "kunne ikke læses",
               "pdf truncated (content path only)")
    finally:
        with open(PDF, "wb") as handle:
            handle.write(pdf)
    if run_checks(sales=False):
        failures.append("self-test revert: repoet er ikke grønt igen efter mutationerne")

    # 12. PDF'en må ikke sælge. Hver regel skal kunne gøre en tekst rød, og en
    # ren tekst skal være grøn, ellers er reglen grøn af en grund den ikke må.
    clean_text = ("EUComply scan report\nThis is a sample with illustrative data. "
                  "Scan your own domain free at eucomplypro.com/scan\n")
    expect_clean(pdf_sales_findings(clean_text), "sales clean pdf text")
    expect(pdf_sales_findings(clean_text + "EUComply Pro · eucomplypro.com/pro\n"),
           "lukkede side eucomplypro.com/pro", "sales pdf footer links /pro")
    expect(pdf_sales_findings(clean_text + "Pricing: eucomplypro.com/da/pricing\n"),
           "lukkede side", "sales pdf links /da/pricing")
    expect(pdf_sales_findings(clean_text + "EUComply Pro costs $79/year per site\n"),
           "pris '$79", "sales pdf price")
    expect(pdf_sales_findings(clean_text + "Buy: https://buy.stripe.com/abc123\n"),
           "betalingslink", "sales pdf checkout link")
    expect(pdf_sales_findings(clean_text + "The current Pro license generates an HTML report\n"),
           "nævner Pro", "sales pdf Pro without closure")
    expect_clean(pdf_sales_findings(clean_text + "EUComply Pro is no longer sold; existing licences keep working.\n"),
                 "sales pdf closed Pro is allowed")
    expect_clean(pdf_sales_findings(clean_text + "Support: https://donate.stripe.com/7sYeVcbn50wieFM8gDbMQ0c\n"),
                 "sales pdf donation link is allowed")

    # 11. Gaten skal køre i det miljø den døde i. Se _without_reportlab_cases.
    # Køres ALTID og uden betingelse: subprocessen blokerer importen selv, så
    # casen er meningsfuld både med og uden reportlab på maskininen. En tidligere
    # version gjorde "reportlab mangler" til en FEJL, hvilket gjorde gaten
    # kræve præcis den afhængighed den skulle tåle — den var grøn på min maskine
    # og rød i CI, altså præcis fejlen den skulle forhindre.
    failures.extend(_without_reportlab_cases())
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
    for notice in NOTICES:
        print(f"INFO  {notice}")
    for finding in findings:
        print(f"ERROR {finding}")
    if findings:
        print(f"\n{len(findings)} prøverapport-fund")
        return 1
    print(f"OK: prøverapporten dækker de {len(builder.engine_check_keys())} checks motoren kører, "
          "PDF'en følger datasættet og sælger ikke")
    return 0


if __name__ == "__main__":
    sys.exit(main())
