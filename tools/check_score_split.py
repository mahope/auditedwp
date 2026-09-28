#!/usr/bin/env python3
"""Port: tallet i et skanneresultat skal sige, hvad det tæller.

Fire af de ni rækker i `runScan()` gælder kun for bestemte sites: en
cookie-række på et site der ikke sætter cookies, en TCF-række på et site uden
programmatisk annoncering, en Consent-Mode-række på et site uden Google Ads og
en DORA-række, en offentlig sidescan overhovedet ikke kan afgøre. Før dette var
alle ni talt med, så et site der gjorde alt andet rigtigt scorede 56 % (5 af 9)
— og båndet blev grønt ved 80.

Porten læser **listen fra motoren** og kræver at hver publiceret side bruger
den, så en ny betinget række i motoren uden en sideændring giver rød. Den må
ikke tro på sidens egen liste: den skal bare have nøglerne.

Kontroller:
  1. Motoren har en `CONDITIONAL_CHECKS`-tabel med en helt sætning pr. nøgle.
  2. Hver nøgle findes i `runScan()`, og hver række får både `applies` og
     `condition` sat — også de der *gælder*, ellers kan siden ikke fortælle
     hvorfor de tæller med.
  3. `score` har både det gamle (`pct`, `total`) og det nye (`pct_applicable`,
     `applicable_total`, `conditional`).
  4. `dora.applies` er fast `false` — en offentlig scan kan ikke afgøre, om
     driftsselskabet er en finansiel enhed. Det er det eneste sted hvor porten
     håndhæver en enkelt række, fordi det er det eneste dom.
  5. Hver publiceret resultatside læser `pct_applicable` **og** nævner nøglerne
     fra motoren — ikke sin egen liste.
  6. Ingen side må selv finde på listen: et nøglesæt i en side skal være
     præcis motorens.
"""
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(ROOT, "shared", "scan-engine.js")
ENGINE_NPM = os.path.join(ROOT, "eucomply-scanner", "engine", "index.js")

# Sider der viser et scoretal. Fundet ved at søge på `score`-brug, og porten
# kræver at hver af dem bruger det nye tal — en side der scorer uden at sige
# hvad tæller, er præcis fejlen.
RESULT_PAGES = [
    "site/scan/index.html",
    "site/da/scan/index.html",
    "site/de/scan/index.html",
    "site/fr/scan/index.html",
    "site/cookie-banner-check/index.html",
    "site/de/cookie-banner-check/index.html",
    "site/consent-mode-v2-check/index.html",
    "site/gdpr-compliance-check/index.html",
    "site/gdpr-scanner-free/index.html",
]


def engine_keys():
    """Nøglerne fra motoren — den eneste sandhed, porten og siderne deler."""
    out = subprocess.run(
        ["node", "-e",
         "import('./shared/scan-engine.js').then(m => console.log(JSON.stringify(m.CONDITIONAL_CHECKS)))"],
        cwd=ROOT, capture_output=True, text=True)
    if out.returncode != 0:
        return None, out.stderr.strip()
    return json.loads(out.stdout.strip()), None


def read(path):
    with io.open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return fh.read()


def check(engine_src, npm_src, keys, pages):
    findings = []

    # 1 + 4: tabellen og den ene håndhævede række
    for label, src in (("shared/scan-engine.js", engine_src), ("eucomply-scanner/engine/index.js", npm_src)):
        for k, why in keys.items():
            if len(why) < 30 or not why.endswith("."):
                findings.append("%s: CONDITIONAL_CHECKS['%s'] er ikke en hel sætning: %r" % (label, k, why))
            if "checks.%s.applies" % k not in src and "checks['%s'].applies" % k not in src:
                findings.append("%s: rækken '%s' får aldrig 'applies'" % (label, k))
        if "checks.dora.applies = false;" not in src:
            findings.append("%s: dora skal være fast betinget — en offentlig scan kan ikke afgøre om "
                            "driftsselskabet er en finansiel enhed" % label)
        if "checks[key].condition = CONDITIONAL_CHECKS[key];" not in src:
            findings.append("%s: rækkerne får ikke 'condition' — uden den kan siden ikke vise grunden" % label)
        for field in ("applicable_total: applicable.length", "passed_applicable: passedApplicable",
                      "pct_applicable: applicable.length", "conditional: CONDITIONAL_CHECK_KEYS.filter("):
            if field not in src:
                findings.append("%s: score mangler '%s'" % (label, field))
        if "pct:" not in src:
            findings.append("%s: det gamle tal (pct) er væk — det er tallet kunder har set, det skal blive"
                            % label)

    # 1b: de to motorer skal have præcis samme nøgler. Ellers får npm-CLI'en og
    # workeren to forskellige betingelser for det samme website, og det er præcis
    # den inkonsistens hele porten findes for.
    for label, src in (("shared/scan-engine.js", engine_src), ("eucomply-scanner/engine/index.js", npm_src)):
        table = re.search(r"CONDITIONAL_CHECKS = \{(.*?)\n\};", src, re.S)
        if not table:
            findings.append("%s: CONDITIONAL_CHECKS-tabellen er væk" % label)
            continue
        own = set(re.findall(r"^\s{2}(\w+):", table.group(1), re.M))
        if own != set(keys):
            findings.append("%s: tabellen har nøglerne %s, den delte motor har %s"
                            % (label, sorted(own), sorted(keys)))

    # 5 + 6: siderne. Læses fra den overgivne tabel, ikke fra disk — ellers ville
    # selftestens mutationer blive overskrevet af de rigtige filer, og porten
    # ville være grøn fordi den læste noget andet end det den testede.
    for path in pages:
        src = pages[path]
        if "var pct = sp ? sp.pct_applicable : d.score.pct;" not in src:
            findings.append("%s: det viste tal kommer ikke fra de rækker der gælder for sitet" % path)
        if "+ notCountedSentence(sp)" not in src:
            findings.append("%s: nævner ikke ved siden af tallet hvilke rækker der ikke tæller med" % path)
        if "conditionLine" not in src or "c.applies === false" not in src:
            findings.append("%s: viser ikke betingelsen i selve rækken" % path)
        # Egen liste: en side må have præcis motorens nøgler, ikke et udvalg.
        for block in re.findall(r"COND_LABELS\s*=\s*\{[^}]*\}", src):
            side = set(re.findall(r"(\w+)\s*:", block))
            if side != set(keys):
                findings.append("%s: COND_LABELS har nøglerne %s, motoren har %s"
                                % (path, sorted(side), sorted(keys)))
    return findings


def selftest():
    """Negative cases. Grønt baseline-træ først, så en mutation der ikke
    muterer ikke kan være grøn."""
    engine_src = read("shared/scan-engine.js")
    npm_src = read("eucomply-scanner/engine/index.js")
    keys = json.loads(subprocess.run(
        ["node", "-e",
         "import('./shared/scan-engine.js').then(m => console.log(JSON.stringify(m.CONDITIONAL_CHECKS)))"],
        cwd=ROOT, capture_output=True, text=True).stdout.strip())
    page = read("site/scan/index.html")
    pages = {p: read(p) for p in RESULT_PAGES}

    def baseline():
        return check(engine_src, npm_src, keys, pages)

    def mutate_engine(src, old, new):
        assert src.count(old) == 1, "mutationen rammer ikke præcis én gang: %r" % old
        return src.replace(old, new)

    def expect_red(name, eng=None, npm=None, page_mut=None):
        e = eng or engine_src
        n = npm or npm_src
        p = dict(pages)
        if page_mut:
            for path, old, new in page_mut:
                p[path] = mutate_engine(p[path], old, new)
        found = check(e, n, keys, p)
        if not found:
            print("  SELFTEST FEJLEDE: %s gav ingen fund" % name)
            return False
        return True

    ok = True
    if baseline():
        print("  SELFTEST FEJLEDE: baseline-træet er rødt, så mutationerne er værdiløse")
        ok = False
    cases = [
        ("dora tæller igen",
         (npm_src, "checks.dora.applies = false;", "checks.dora.applies = true;"), None),
        ("en betinget række mangler applies",
         (npm_src, "checks.tcf.applies = adSignals;", "/* fjernet */"), None),
        ("condition sættes ikke",
         (npm_src, "checks[key].condition = CONDITIONAL_CHECKS[key];", "/* fjernet */"), None),
        ("det nye tal er væk",
         (npm_src, "pct_applicable: applicable.length", "pct_x: applicable.length"), None),
        ("siden bruger det gamle tal",
         None, None, [("site/scan/index.html", "sp.pct_applicable", "d.score.pct")]),
        ("siden dropper betingelsen i rækken",
         None, None, [("site/de/scan/index.html", "c.applies === false && c.condition", "false")]),
        ("siden har sin egen liste",
         None, None, [("site/fr/scan/index.html", "dora: 'DORA'", "gdpr: 'GDPR'")]),
        ("en side scorer uden at nævne nævneren",
         None, None, [("site/gdpr-scanner-free/index.html", "+ notCountedSentence(sp);", ";")]),
        # Flere sider, så porten ikke kan være grøn fordi den kun kigger på én.
        ("npm-motoren mangler et nøgle i tabellen",
         None, (npm_src, "  dora: \"Not counted here", "  doraX: \"Not counted here"), None),
    ]
    for case in cases:
        name = case[0]
        eng_case, npm_case, page_case = (list(case[1:]) + [None, None, None])[:3]
        ok &= expect_red(name,
                         eng=mutate_engine(engine_src, *eng_case[1:]) if eng_case else None,
                         npm=mutate_engine(npm_src, *npm_case[1:]) if npm_case else None,
                         page_mut=page_case)
    if ok:
        print("  SELFTEST GRØN — alle %d negative cases fanges" % len(cases))
    return ok


def main():
    keys, err = engine_keys()
    if keys is None:
        print("FEJL: motoren kan ikke indlæses: %s" % err)
        return 1
    if "--selftest" in sys.argv:
        return 0 if selftest() else 1
    findings = check(read("shared/scan-engine.js"),
                     read("eucomply-scanner/engine/index.js"),
                     keys,
                     {p: read(p) for p in RESULT_PAGES})
    if findings:
        for f in findings:
            print("FEJL %s" % f)
        return 1
    print("OK: %d betingede rækker i motoren, %d resultatsider bruger dem" % (len(keys), len(RESULT_PAGES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
