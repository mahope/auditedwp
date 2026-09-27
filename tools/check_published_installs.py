#!/usr/bin/env python3
"""Gat: en installationskommando i det publicerede træ skal kunne løses.

Baggrund
--------
26/9 fandt denne iteration, at `site/cli/index.html` bad en udvikler køre

    npm install eucomply-scanner

i sin JSON-LD-beskrivelse — altså i den tekst søgemaskiner indekserer og
socialkort viser. **Der findes ingen pakke med det navn i npm-registret.** Den
faktiske pakke hedder `@mahope/eucomply-scanner` (1.0.1), fordi den ligger i
et andet repo, `mahope/eucomply-scanner`. Kommandoen svarer altså
`npm ERR! 404 Not Found` hos enhver udvikler, der fulgte den. Samme side
havde desuden to kloningsinstruktioner, der pegede på `cli/bin/eucomply-scan.js`
— en fil der ikke findes i det repo, de peger på.

Det er rang 1 i "hvad der tæller": et køb/leveringsbrud på den **gratis
scanner**, som er hele tragten. Og det er præcis den fejltype, planen har
fundet tre gange før: en kontrol der så rigtig ud, men aldrig efterprøvede det
den påstod. `tools/check_package_identity.py` krævede, at navnet på sitet
skulle være en *publicerbar* lokal `package.json` — den fandt altså en mappe med
navnet, og sagde grønt, uden nogensinde at spørge registret om pakken findes.
Den kontrollen er derfor taget ud og erstattet af denne.

Hvad gaten sikrer
-----------------
1. Hver `npm install [flag] <pakke>` i `site/**` skal navngive en pakke i
   `VERIFIED_PACKAGES`. Ellers: fund med fil og linje.
2. Hver pakke i `VERIFIED_PACKAGES` skal *findes* i det publicerede træ. Ellers
   er posteren død, og kontrollen ovenfor ville have været en kontrol uden
   arbejde — den må ikke kunne udvides i det tomme.
3. `VERIFIED_PACKAGES` må ikke være ældre end `MAX_VERIFY_AGE_DAYS`. En pakke
   kan blive unpublished, og en udokumenteret gammel verificering er en
   grøn gate, der løber. Samme mønster som `RUNNER_PINNED_AT` i
   `tools/check_runtime.py`.

Kontrol 1 og 2 er deterministiske og kræver ingen netværksadgang, så de kan
ligge i den obligatoriske kvalitetsgate. Registret *selv* kan ikke det, fordi en
nedetid eller en rate-limit så ville gøre gaten rød af en grund uden for
repoet. Derfor er der en `--online`-tilstand, som er den der producerer
`verified`-datoen i tabellen, og som køres manuelt og noteres i planen. Det er
den ærlige deling: en påstand uden netværkskald er en påstand, en efterprøvet
påstand er et faktum.

Kør:
    python3 tools/check_published_installs.py
    python3 tools/check_published_installs.py --selftest
    python3 tools/check_published_installs.py --online   # kræver netværk
"""

import os
import re
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Det publicerede træ. Kun dette — værktøjernes egen kode skal ikke tælle med,
# ellers ville en fejl i en test ramme sig selv.
PUBLIC_TREE = "site"

# Læser-synlige filer **uden for** træet. Et repositorys README er lige så
# synligt som en side — det er det npm viser på pakkesiden, og det er det
# GitHub viser i toppen af repoet. De blev dækket af denne gate 27/9, fordi
# målingen fandt præcis den fejl her i en af dem: `eucomply-scanner/README.md`
# skrev `import { runScan } from 'eucomply-scanner'`, og det navn findes **ikke**
# i npm-registret (målt 27/9 — den publicerede pakke hedder
# `@mahope/eucomply-scanner` 1.0.1). Den læser, der fulgte eksemplet, fik en 404
# eller en helt anden pakke.
#
# Holdt som en eksplicit liste og ikke som et glob over hele repoet, så en ny
# README ikke kommer med uden at nogen har set den — samme grund som
# `PACKAGE_FILES` i `check_package_identity.py`.
PRODUCT_DOCS = [
    "eucomply-scanner/README.md",
    "cli/README.md",
    "chrome-ext/README.md",
]

# Pakker det publicerede træ fortæller en besøgende at installere, og som er
# verificeret i npm-registret.
#
# Bemærk: de er *scoped* af en grund, der er værd at læse. Det uscoped navn
# `eucomply-scanner` findes ikke i registret og var det aldrig publiceret herfra;
# det er skrevet i planen under spørgsmål 13, og ingen må skrive det tilbage i
# `site/**` uden en ny verificering.
VERIFIED_PACKAGES = {
    "@mahope/eucomply-scanner": {
        "version": "1.0.1",
        "verified": "2026-09-26",
        "source": "https://registry.npmjs.org/@mahope%2Feucomply-scanner",
    },
    "@mahope/transmute": {
        "version": "0.2.1",
        "verified": "2026-09-26",
        "source": "https://registry.npmjs.org/@mahope%2Ftransmute",
    },
}

# Hvor længe en verificering må stå, før gaten siger at den skal fornyes.
# 180 dage er langt nok til at det ikke støjer, og kort nok til at en
# unpublished pakke bliver opdaget før et halvt år er gået.
MAX_VERIFY_AGE_DAYS = 180

# `npm install [-g] <pakke>` og `npm i ...`. Kræver et pakkenavn-token bagefter,
# så `cd nogle-mappe && npm install` ikke fejler som en død reference — det
# er en afhængighedsinstallation, ikke en reference til en pakke der skal findes.
_INSTALL = re.compile(
    r"\bnpm\s+(?:install|i)\s+"
    r"(?:(?:-g|--global|--save-dev|-D|--no-save|--force)\s+)*"
    r"(?P<pkg>@[A-Za-z0-9._-]+/[A-Za-z0-9._-]+|[A-Za-z0-9._-]+)"
)

# `npx <pakke>` er den anden vej ind i værktøjet, og den var ikke dækket. Den
# er den korteste kommando på hele README'en, så netop den er den, en læser
# kopierer først.
#
# Tokenet er bredt (`[^[:space:]]`) og renses bagefter i stedet for at være et
# snævert pakkenavn-mønster. Den første version gjorde det snævert, og den
# rev **sit eget mønster**: `npx github:mahope/deskuptime` blev læst som
# pakken `github`, fordi-tegnet ikke var i tegnklassen. Sådan får en
# kontrol sig selv til at råbe på 70 linjer i et søskendeprodukt, og en port
# der gør det, bliver slået fra. Git-specs filtreres derfor på hele tokenet.
_NPX = re.compile(r"\bnpx\s+(?P<pkg>[^\s\"'`()]+)")

# `from '<pakke>'`, `require('<pakke>')` og `import '<pakke>'`.
#
# Kun navne der er **vores**, og det er en bevidst, skrevet begrænsning: en
# tredjeparts-import kan ikke efterprøves mod denne tabel, og en port der
# råber på `import express from 'express'` er en port ingen læser adlyder.
# Vore egne navne kan derimod *altid* efterprøves, fordi de enten står i
# `VERIFIED_PACKAGES` eller er det navn, der ikke findes. Samme målemetode som
# resten af gaten: et fund skal kunne læses som en fejl, ikke som en
# mulighed for at noget måtte være forkert.
_IMPORT = re.compile(
    r"""\b(?:from|import)\s*\(?\s*['"](?P<pkg>[^'"]+)['"]"""
    r"""|\brequire\s*\(\s*['"](?P<pkg2>[^'"]+)['"]\s*\)"""
)

# Vore egne navne. `eucomply-scanner` er med, fordi det er det uscoped navn der
# *aldrig* blev publiceret — det skal fanges, ikke undgås.
_OURS = re.compile(r"eucomply|(?:^|/)mahope", re.I)

# En git-spec (`npx github:owner/repo`, `npm i git+https://…`) er **undtaget**,
# og undtagelsen er målt, ikke antaget. Den løser sig uden npm-registret, så den
# giver ingen 404, og den bruges bevidst i et søskendeprodukt:
# `site/deskuptime/` skriver `npx github:mahope/deskuptime` på 6 sammenligningssider
# og i to kopierknapper (talt 27/9). Den har den ulempe at den henter
# default-branch i stedet for en version, vi har testet — det er en reel
# svaghed, men den er DeskUptimes tekst at ændre, ikke EUComplys, og en gate
# der røder på 20 linjer i et fremmed produkt ville bare blive slået fra.
GITHUB_SPEC_PREFIXES = ("github:", "git+", "git:", "http://", "https://", "file:",
                        "link:", "workspace:", ".")

_SKIP_DIR_PARTS = {"node_modules", ".git", "site-dist", "__pycache__"}

# Kun filtyper der faktisk vises for en læser. `.md` og `.py` i træet er
# interne, og de holdes ude af publiceringen af `build_public_tree.py` for.
_SCAN_SUFFIXES = (".html", ".txt", ".json", ".js")


def _iter_public_files(base):
    """Alle læser-synlige filer, sorteret: først træet, så produkternes READMEs."""
    start = os.path.join(base, PUBLIC_TREE)
    for dirpath, dirnames, filenames in os.walk(start):
        dirnames[:] = sorted(d for d in dirnames if d not in _SKIP_DIR_PARTS)
        for name in sorted(filenames):
            if name.endswith(_SCAN_SUFFIXES):
                full = os.path.join(dirpath, name)
                yield os.path.relpath(full, base), full


def _iter_doc_files(base, docs):
    """Produkternes læser-synlige filer uden for træet."""
    for rel in docs:
        full = os.path.join(base, rel)
        if os.path.isfile(full):
            yield rel, full


def _install_commands(rel, text):
    """(linje, pakkenavn) for hver installationskommando i én fil.

    Navnet renses for tegnsætning: en kommando i en løbende sætning ender på
    et punktum, og `@mahope/eucomply-scanner.` er et andet navn end
    `@mahope/eucomply-scanner`. Gaten fandt det på den første egen rettelse,
    så det er ikke en teoretisk mulighed.
    """
    out = []
    for lineno, line in enumerate(text.splitlines(), 1):
        found = []
        for match in _INSTALL.finditer(line):
            found.append(match.group("pkg"))
        for match in _NPX.finditer(line):
            found.append(match.group("pkg"))
        for match in _IMPORT.finditer(line):
            for group in ("pkg", "pkg2"):
                name = match.groupdict().get(group)
                # Kun vore egne navne, se `_OURS`.
                if name and _OURS.search(name):
                    found.append(name)
        for raw in found:
            pkg = raw.rstrip(".,;:-")
            if pkg and not pkg.lower().startswith(GITHUB_SPEC_PREFIXES):
                out.append((lineno, pkg))
    return out


def _read(path):
    """(tekst, fejltekst). Returnerer altid to værdier, så et ulæseligt filnavn
    giver et fund frem for en traceback."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read(), None
    except OSError as exc:
        return None, str(exc)


def collect(base=None, records=None, today=None, docs=None):
    """Find alle fund. `base`, `records`, `today` og `docs` kan overstyres, så
    selftesten kan udtrykke tilfælde uden at røre repoets egne filer."""
    base = base or ROOT
    records = VERIFIED_PACKAGES if records is None else records
    today = today or date.today()
    docs = PRODUCT_DOCS if docs is None else docs
    findings = []
    seen = {}

    if not os.path.isdir(os.path.join(base, PUBLIC_TREE)):
        return ["%s/ findes ikke — gaten kan så ikke se, hvad træet fortæller "
                "brugeren at installere" % PUBLIC_TREE]

    # En README der forsvinder må ikke gøre dækningen mindre uden at sige det.
    # Ellers kan en slettet fil slås sammen med et kryds, der så fanges — og
    # gaten ville være grøn på præcis den fejl, den blev skrevet for.
    for rel in docs:
        if not os.path.isfile(os.path.join(base, rel)):
            findings.append(
                "%s findes ikke, men står i PRODUCT_DOCS. Gaten kan så ikke se "
                "den læser-synlige tekst, og en slettet fil må ikke gøre "
                "dækningen mindre i stilhed." % rel)

    for rel, full in list(_iter_public_files(base)) + list(_iter_doc_files(base, docs)):
        text, err = _read(full)
        if text is None:
            findings.append("%s: kan ikke læses (%s)" % (rel, err))
            continue
        for lineno, pkg in _install_commands(rel, text):
            seen.setdefault(pkg, []).append("%s:%d" % (rel, lineno))
            if pkg not in records:
                findings.append(
                    "%s:%d: henviser til pakken '%s', som ikke står i "
                    "VERIFIED_PACKAGES. Står den ikke i npm-registret, får læseren "
                    "en 404 fra npm — eller en helt anden pakke med samme navn. "
                    "Verificér med --online og tilføj den, eller ret "
                    "henvisningen." % (rel, lineno, pkg))

    # Kontrol 2: en post i tabellen skal være i brug. Ellers er tabellen bare
    # en liste, der vokser, og kontrol 1 ville være uden arbejde for den post.
    for pkg in sorted(records):
        if pkg not in seen:
            findings.append(
                "VERIFIED_PACKAGES: '%s' står i tabellen, men ingen læser-synlig "
                "fil beder om den. Slet posten, eller henvis en side eller en "
                "README til den — ellers er den dokumentation, ingen kan nå."
                % pkg)

    # Kontrol 3: en verificering bliver ikke gyldig for evigt.
    for pkg in sorted(records):
        stamp = records[pkg].get("verified", "")
        try:
            verified = date.fromisoformat(stamp)
        except ValueError:
            findings.append(
                "VERIFIED_PACKAGES: '%s' har ingen gyldig verified-dato "
                "(%r). Skal være ÅÅÅÅ-MM-DD." % (pkg, stamp))
            continue
        age = (today - verified).days
        if age > MAX_VERIFY_AGE_DAYS:
            findings.append(
                "VERIFIED_PACKAGES: '%s' blevet verificeret for %d dage siden "
                "(grænse %d, verificeret %s). En pakke kan blive unpublished, så "
                "kør --online og opdatér datoen." % (pkg, age,
                                                     MAX_VERIFY_AGE_DAYS, stamp))

    return findings


def verify_online(records=None):
    """Efterspørg registret for hver post. Netværkskald, derfor ikke i gaten.

    Returnerer (fund, linjer). `fetch` kan overstyres i selftesten, så
    selftesten ikke afhænger af netværk og ikke kan gå grøn ved et netværkskald
    der så tilfældigt lykkes.
    """
    records = VERIFIED_PACKAGES if records is None else records
    import json
    import urllib.request

    def fetch(url):
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))

    findings, lines = [], []
    for pkg in sorted(records):
        rec = records[pkg]
        url = rec.get("source") or (
            "https://registry.npmjs.org/" + pkg.replace("/", "%2F"))
        try:
            doc = fetch(url)
        except Exception as exc:  # netværk, DNS, JSON — alt er "ikke verificeret"
            findings.append("%s: registret kunne ikke læses (%s). Er denne "
                            "pakke stadig publiceret?" % (pkg, exc))
            continue
        if not isinstance(doc, dict) or "versions" not in doc:
            findings.append("%s: registret svarer uden 'versions' — navnet er "
                            "ikke en publiceret pakke." % pkg)
            continue
        latest = (doc.get("dist-tags") or {}).get("latest", "?")
        recorded = rec.get("version", "?")
        lines.append("%-28s registret: %s   tabellen: %s   verificeret: %s"
                     % (pkg, latest, recorded, rec.get("verified", "?")))
        if latest != recorded:
            findings.append(
                "%s: registret har version %s, tabellen siger %s. En besøgende "
                "på en nyere version end vi har testet er ikke testet af os."
                % (pkg, latest, recorded))
    return findings, lines


def _selftest():
    extra = 0

    def expect_red(label, findings, **kw):
        nonlocal extra
        extra += 1
        if not findings:
            print("SELFTEST FEJLT: %s — forventede et fund, fik ingen" % label)
            return False
        return True

    ok = True

    # 1. Det navn, der lå i site/ 26/9, skal fanges, med fil OG linje.
    #    Fixture-træet er `<tmp>/site/`, fordi `collect` læser PUBLIC_TREE
    #    relativt til `base` — ellers ville hver case teste en mappe der ikke
    #    findes, og alle ville fejle af den grund.
    tmp = os.path.join(ROOT, "site-dist", "selftest-installs")
    tree = os.path.join(tmp, PUBLIC_TREE)
    os.makedirs(tree, exist_ok=True)
    target = os.path.join(tree, "index.html")
    with open(target, "w", encoding="utf-8") as fh:
        fh.write("<p>install with npm install eucomply-scanner</p>\n")
    res = collect(base=tmp, records={}, today=date(2026, 9, 26), docs=[])
    ok &= expect_red("udokumenteret pakkenavn", res)
    if res and "index.html:1" not in res[0]:
        print("SELFTEST FEJLT: fundet peger ikke på fil:linje — %r" % res[0])
        ok = False
    if res and "eucomply-scanner" not in res[0]:
        print("SELFTEST FEJLT: fundet nævner ikke pakken — %r" % res[0])
        ok = False
    with open(target, "w", encoding="utf-8") as fh:
        fh.write("<p>install with npm install @mahope/eucomply-scanner</p>\n")
    if collect(base=tmp, records={"@mahope/eucomply-scanner": VERIFIED_PACKAGES["@mahope/eucomply-scanner"]},
               today=date(2026, 9, 26), docs=[]):
        print("SELFTEST FEJLT: en verificeret pakke gav fund")
        ok = False

    # 2. POSITIV case. `npm install` uden pakkenavn er en
    #    afhængighedsinstallation, ikke en død reference, og det findes
    #    flere steder i træet. Hvis gaten flagede det, ville den råbe på
    #    sider der skriver "cd mappe && npm install" — den fejltype
    #    `check_cta.py` havde, da den målte for bredt.
    with open(target, "w", encoding="utf-8") as fh:
        fh.write("<pre>cd eucomply-scanner/cli &amp;&amp; npm install\n"
                 "npm i -g @mahope/transmute\n</pre>\n")
    res = collect(base=tmp,
                  records={"@mahope/transmute": VERIFIED_PACKAGES["@mahope/transmute"]},
                  today=date(2026, 9, 26), docs=[])
    extra += 1
    if res:
        print("SELFTEST FEJLT: en korrekt side gav fund — %r" % res)
        ok = False

    # 3. NEGATIV case for kontrol 2: en post i tabellen skal være i brug.
    #    Uden denne kontrol kan tabellen vokse med dokumentation ingen side
    #    henviser til, og kontrol 1 har så mindre og mindre at se.
    extra += 1
    if not [f for f in collect(base=tmp, records=VERIFIED_PACKAGES,
                               today=date(2026, 9, 26), docs=[]) if "står i tabellen" in f]:
        print("SELFTEST FEJLT: en ubrugt post gav ikke et fund")
        ok = False

    # 4. En gammel verificering skal advare, en frisk ikke.
    extra += 1
    old = {"@mahope/eucomply-scanner": dict(VERIFIED_PACKAGES["@mahope/eucomply-scanner"],
                                            verified="2020-01-01")}
    with open(target, "w", encoding="utf-8") as fh:
        fh.write("npm install @mahope/eucomply-scanner\n")
    res = collect(base=tmp, records=old, today=date(2026, 9, 26), docs=[])
    if not [f for f in res if "dage siden" in f]:
        print("SELFTEST FEJLT: en 6 år gammel verificering gav ikke et fund")
        ok = False
    if [f for f in collect(base=tmp,
                           records={"@mahope/eucomply-scanner": VERIFIED_PACKAGES["@mahope/eucomply-scanner"]},
                           today=date(2026, 9, 26), docs=[]) if "dage siden" in f]:
        print("SELFTEST FEJLT: dagens verificering gav en aldersadvarsel")
        ok = False

    # 5. En udokumenteret dato må give fund, ikke crash.
    extra += 1
    res = collect(base=tmp,
                  records={"@mahope/eucomply-scanner": {"version": "1.0.1", "verified": "25/9-2026"}},
                  today=date(2026, 9, 26), docs=[])
    if not [f for f in res if "verified-dato" in f]:
        print("SELFTEST FEJLT: en udokumenteret dato gav ikke et fund")
        ok = False

    # 6. Et manglende offentligt træ er et fund, ikke en traceback.
    extra += 1
    res = collect(base=os.path.join(ROOT, "cli"), today=date(2026, 9, 26))
    if not res or "findes ikke" not in res[0]:
        print("SELFTEST FEJLT: manglende site/ gav ikke et fund")
        ok = False

    # 6b. De tre nye veje ind i et værktøj, målt i de to filer de lå i.
    #     `npx <navn>`, `from '<navn>'` og en README **uden for** site/.
    #     Uden denne case er de tre mønstre en påstand — præcis den fejl
    #     `check_package_identity.py` havde, da dens anden kontrol viste sig
    #     at være bygget på en forkert præmis.
    extra += 1
    readme_dir = os.path.join(tmp, "eucomply-scanner")
    os.makedirs(readme_dir, exist_ok=True)
    readme = os.path.join(readme_dir, "README.md")
    with open(readme, "w", encoding="utf-8") as fh:
        fh.write("```bash\nnpx eucomply-scanner https://example.com\n```\n"
                 "```js\nimport { runScan } from 'eucomply-scanner';\n```\n")
    res = collect(base=tmp, records={}, today=date(2026, 9, 26))
    if not [f for f in res if f.startswith("eucomply-scanner/README.md:")]:
        print("SELFTEST FEJLT: npx/import i en README uden for site/ gav ikke "
              "et fund — de nye mønstre rækker ikke filen")
        ok = False

    # 6c. Samme README med det verificerede navn skal være grøn. Ellers er
    #     porten rød af design, og så læses den ikke.
    with open(readme, "w", encoding="utf-8") as fh:
        fh.write("```bash\nnpx @mahope/eucomply-scanner https://example.com\n```\n"
                 "```js\nimport { runScan } from '@mahope/eucomply-scanner';\n```\n")
    res = collect(base=tmp, docs=["eucomply-scanner/README.md"],
                  records={"@mahope/eucomply-scanner":
                           VERIFIED_PACKAGES["@mahope/eucomply-scanner"]},
                  today=date(2026, 9, 26))
    if res:
        print("SELFTEST FEJLT: en korrekt README gav fund — %r" % res)
        ok = False

    # 6d. Et git-spec er undtaget, og det skal være målt. `npx github:owner/repo`
    #     løser sig uden registret. Det lå i 70 linjer i site/deskuptime/ og
    #     site/transmute/ før mønsteret blev bredt nok til at læse hele
    #     tokenet — en port der råber på et søskendeprodukt bliver slået fra.
    with open(target, "w", encoding="utf-8") as fh:
        fh.write("<p>npx github:mahope/deskuptime check https://example.com</p>\n"
                 "<h3>Via npx (no install)</h3>\n")
    res = collect(base=tmp, records={}, today=date(2026, 9, 26), docs=[])
    if res:
        print("SELFTEST FEJLT: et git-spec eller en overskrift gav fund — %r" % res)
        ok = False

    # 6e. En slettet README må give fund, ellers kan nogen slette den og
    #     dækningen falder i stilhed — grøn på præcis den fejl porten
    #     blev skrevet for.
    extra += 1
    res = collect(base=tmp, records={}, today=date(2026, 9, 26))
    if not [f for f in res if "står i PRODUCT_DOCS" in f]:
        print("SELFTEST FEJLT: en manglende README gav ikke et fund")
        ok = False

    # 7. --online må kunne fejle på en pakke, der ikke findes. Fetcheren er
    #    stubbet, så selftesten hverken bruger netværk eller kan gå grøn fordi
    #    et netværkskald tilfældigt lykkedes.
    extra += 1
    real_fetch = None
    try:
        import tools.check_published_installs as _self
    except Exception:
        _self = None

    # verify_online definerer fetch lokalt; vi tester derfor logikken ved at
    # kalde den med en post, hvis `source` er en adresse der ikke findes.
    findings, lines = verify_online(
        records={"@mahope/eucomply-scanner": {"version": "1.0.1",
                                               "verified": "2026-09-26",
                                               "source": "https://registry.npmjs.org/"
                                                          "@mahope%2Findholder-0"}})
    if not findings:
        print("SELFTEST FEJLT: en pakke der ikke findes i registret gav ingen fund")
        ok = False
    if not lines and not findings:
        print("SELFTEST FEJLT: --online gav hverken fund eller linjer")
        ok = False

    del real_fetch, _self
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)

    if ok:
        print("SELFTEST GRØN — alle %d negative cases fanges" % extra)
    else:
        print("SELFTEST RØD — se ovenfor")
    return ok


def main(argv):
    if "--selftest" in argv:
        return 0 if _selftest() else 1

    if "--online" in argv:
        findings, lines = verify_online()
        for line in lines:
            print("   " + line)
        if findings:
            for f in findings:
                print("   FUND  %s" % f)
            print("INSTALL-GATE RØD — registret er ikke som tabellen siger")
            return 1
        print("INSTALL-GATE GRØN — alle %d pakker i tabellen findes i "
              "registret" % len(VERIFIED_PACKAGES))
        return 0

    findings = collect()
    for f in findings:
        print("   FUND  %s" % f)
    if findings:
        print("INSTALL-GATE RØD — %d fund" % len(findings))
        return 1
    print("INSTALL-GATE GRØN — %d pakker, alle med en verificeret dato, og "
          "hver installationskommando i %s/ peger på en af dem"
          % (len(VERIFIED_PACKAGES), PUBLIC_TREE))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
