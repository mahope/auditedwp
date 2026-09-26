#!/usr/bin/env python3
"""Hold the DORA page-signal check honest about what it is.

Why this gate exists (iteration 45, finding, not guesswork):

The free scanner's ninth check is a **static page-text marker count**, not a
DORA assessment. `eucomply-scanner/engine/index.js` says so in its own result
text ("This is not a DORA assessment."). Four published surfaces said the
opposite:

  1. All four homepages: "For financial-sector and ICT-provider sites … Skipped
     silently for everyone else." The code has no such branch — the check runs
     on every site and sets a boolean `pass`, so it costs every ordinary site a
     point of a nine-check score.
  2. `/scan/`: "Other sites get an informational note only." Same inversion.
  3. Eight comparison tables and the badge page sold "DORA resilience signals"
     as regulation coverage, and two of them carried a row literally titled
     "DORA coverage (2025+): ICT risk management, failover, BCDR signals" with
     the competitor marked "Not covered".
  4. `/blog/dora-compliance-guide/` published a table of what the check looks
     for. It listed six categories, **four of which the code cannot detect**
     (DORA-framework mentions, ICT risk management, supply-chain risk,
     resilience testing), and **none** of the seven markers the code actually
     counts (SPF, DKIM, DMARC, MX, CDN failover, status page, multi-server).

Nothing in the repo could see that: the claim gates match plugin feature
*names*, and a marker table is neither a name nor a count.

What is enforced here, and why each rule is falsifiable:

  R1  The marker table the guide publishes **is** the engine's marker table —
      same number of rows, and every row's own description is matched by at
      least one signature when fed through the signatures themselves. This is
      the rule that failed before the fix: 6 of 6 rows were undetectable.
  R2  The engine's disclaimer must still exist. It is the sentence every
      published limitation rests on, so its disappearance must be loud.
  R3  No published page may claim the check is scoped, skipped or informational
      for non-financial sites — the code cannot do that (R4), so the claim is
      always false.
  R4  The check must actually be scored for every site: the `dora` block in the
      engine sets a boolean `pass`. Without it, R3's reason ("it is scored, so
      it always costs a point") would be wrong and the honest fix would be the
      opposite one.

Exit 1 on any finding. `--selftest` proves the rules can fail.
"""

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENGINE = ROOT / "eucomply-scanner" / "engine" / "index.js"
GUIDE = ROOT / "site" / "blog" / "dora-compliance-guide" / "index.html"

# The engine's own sentence. Published limitations quote the same idea; if this
# string ever goes away the wording needs revisiting, so it is a hard rule.
DISCLAIMER = "This is not a DORA assessment"

# Claim patterns: (regex, human message). Each says the code cannot do this.
SCOPE_CLAIMS = [
    (r"skipped silently for everyone else", "claims the check is skipped for non-financial sites"),
    (r"springes stille over for alle andre", "påstår tjekket springes over for ikke-finansielle sites"),
    (r"stillschweigend übersprungen", "behauptet, die Prüfung werde übersprungen"),
    (r"ignoré silencieusement pour tous les autres", "affirme que le contrôle est ignoré"),
    (r"other sites get an informational note", "claims other sites only get an informational note"),
    (r"for financial-sector sites\b", "scopes the check to financial-sector sites"),
    (r"for financial-sector and ICT-provider sites", "scopes the check to financial and ICT sites"),
    (r"DORA operational-resilience wording for financial-sector sites", "scopes the marker check to financial-sector sites"),
]

# R5 blev forsøgt og fjernet med vilje, og det er en beslutning der skal
# læses: en bred "DORA + kapabilitetsord"-regel gav 102 fund, hvoraf langt de
# fleste var redaktionel tekst og artikeltitler ("DORA Compliance: What
# Financial Websites Need to Know", "dora-compliance-guide/" i et rel=prev-tag).
# Den negatør-vindue, der skulle skelne en afvisning fra et løfte, kan ikke se en
# afvisning der står *efter* matchet ("DORA page-signal markers (not an
# assessment)"). En port med 102 fund, hvoraf de 90 er sande, er en port ingen
# læser — og opgave 32 fandt for præcis den fejl i en bred regex. Den udvidede
# påstandsdækning er bevidst ikke lavet her; den kræver en side-for-side
# beslutning om hver af de fire-regulations-sætninger, ikke et mønster.

def published_files(tree):
    root = ROOT / tree
    if not root.is_dir():
        raise SystemExit(f"FEJL: det publicerede træ {tree} findes ikke")
    out = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix in (".html", ".txt", ".json", ".md"):
            out.append(p)
    return out


def engine_signatures(source):
    """Return [(name, pattern)] from the engine's DORA_SIGNATURES table."""
    block = re.search(r"const DORA_SIGNATURES = \[(.*?)\n\];", source, re.S)
    if not block:
        return None
    out = []
    for line in block.group(1).splitlines():
        m = re.match(r'\s*\{\s*re:\s*/(.*)/([a-z]*)\s*,\s*name:\s*"(.*?)"\s*\}', line)
        if m:
            out.append((m.group(3), re.compile(m.group(1), re.I if "i" in m.group(2) else 0)))
    return out


def engine_dora_block(source):
    m = re.search(r"checks\.dora = \{(.*?)\n  \};", source, re.S)
    return m.group(1) if m else None


def guide_marker_rows(html):
    """The (name, description) rows of the published 'what it looks for' table."""
    table = re.search(r"<h2 id=\"scan\">.*?</table>", html, re.S)
    if not table:
        return None
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", table.group(0), re.S):
        cells = re.findall(r"<td>(.*?)</td>", tr, re.S)
        if len(cells) == 2:
            rows.append((re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", cells[0])).strip(),
                         re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", cells[1])).strip()))
    return rows


def normalise(text):
    """Lowercase, drop the separators a signature may or may not use, collapse spaces.

    The engine matches "SPF-record" but not "SPF record", so a table that writes
    the spaced form documents a marker the code cannot find. Comparing with the
    separators removed would hide exactly that, so the *description* check in
    R1 uses the raw text; this normalisation is only for the name lookup.
    """
    return re.sub(r"\s+", " ", re.sub(r"[-_/]", " ", text.lower())).strip()


def strip_tags(text):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def findings(source, html, tree):
    out = []

    sigs = engine_signatures(source)
    if not sigs:
        out.append("motoren: DORA_SIGNATURES kunne ikke læses — porten ville være grøn af en fejl")
        return out

    # R2 — the disclaimer every published limitation rests on.
    if DISCLAIMER not in source:
        out.append(f"motoren: sætningen {DISCLAIMER!r} er væk — al publiceret afgrænsning skal skrives om")

    # R4 — the check is scored for every site, which is why no page may claim
    # it is scoped or informational.
    block = engine_dora_block(source)
    if block is None:
        out.append("motoren: checks.dora-blokken kunne ikke læses")
    elif not re.search(r"pass:\s*doraMatches\.length", block):
        out.append("motoren: dora-tjekket sætter ingen boolesk pass — det ville ikke koste alle sites et point")

    # R1 — the published marker table is the engine's marker table.
    rows = guide_marker_rows(html) if html else None
    if rows is None:
        out.append("guiden: markørtabellen kunne ikke læses — porten ville være grøn af en fejl")
    else:
        if len(rows) != len(sigs):
            out.append(
                f"guiden: tabellen dokumenterer {len(rows)} markører, motoren tæller {len(sigs)} "
                f"({', '.join(n for n, _ in sigs)})"
            )
        documented = normalise(" | ".join(f"{a} {b}" for a, b in rows))
        for name, _ in sigs:
            head = re.sub(r"\s*\(.*?\)\s*$", "", name).lower().split("(")[0].strip()
            token = normalise(head)[:12]
            if token and token not in documented:
                out.append(f"guiden: markøren {name!r} findes ikke i den publicerede tabel")
        for label, desc in rows:
            if not any(rx.search(desc) for _, rx in sigs):
                out.append(
                    f"guiden: rækken {label!r} kan ikke findes af nogen signatur — "
                    f"beskrivelsen {desc[:60]!r} er ikke noget motoren tæller"
                )

    # R3 — no scoping claim, in any language, anywhere in the published tree.
    for p in published_files(tree):
        rel = str(p.relative_to(ROOT))
        text = p.read_text(encoding="utf-8", errors="replace")
        for pat, msg in SCOPE_CLAIMS:
            for m in re.finditer(pat, text, re.IGNORECASE):
                out.append(f"{rel}: {msg} ({m.group(0)!r})")

    return out


def selftest():
    good_engine = (
        "const DORA_SIGNATURES = [\n"
        '  { re: /incident[_-]?response/i, name: "Incident response" },\n'
        '  { re: /spf[_-]?record/i, name: "SPF (Email sender auth)" },\n'
        "];\n"
        "  checks.dora = {\n    pass: doraMatches.length >= 2,\n"
        '    detail: "This is not a DORA assessment.",\n  };\n'
    )
    good_guide = (
        '<h2 id="scan">5. Free DORA page-signal check</h2><table>'
        "<tr><th>Signal</th><th>What it looks for</th></tr>"
        "<tr><td>Incident response</td><td>Text such as \"incident-response\"</td></tr>"
        "<tr><td>SPF (Email sender auth)</td><td>Text such as \"SPF-record\"</td></tr>"
        "</table>"
    )

    cases = []

    # 1. Ren kode + ren tabel + ingen publiceret træ = grøn.
    cases.append(("rent sæt er grønt", findings(good_engine, good_guide, "docs") == []))

    # 2. Den gamle guide: seks rækker motoren ikke kan finde = rød.
    old_guide = good_guide.replace(
        '<tr><td>SPF (Email sender auth)</td><td>Text such as "SPF-record"</td></tr>',
        '<tr><td>Resilience testing</td><td>Penetration testing, vulnerability scanning</td></tr>',
    ).replace(
        '<tr><td>Incident response</td><td>Text such as "incident-response"</td></tr>',
        '<tr><td>ICT risk management</td><td>Information security risk framework</td></tr>',
    )
    f2 = findings(good_engine, old_guide, "docs")
    # Rigtig nål: de to rækker er stadig to, så antallet kan ikke ændre sig —
    # det er navnene der forsvinder. (Første skrivning af denne case søgte på
    # tællingsbeskeden, som ikke kan komme her: samme fejlklasse som opgave 42.)
    cases.append(("udokumenterede markører fanges", any("findes ikke i den publicerede tabel" in x for x in f2)))
    cases.append(("helt tabt markørrække fanges", any("tabellen dokumenterer 1 markører" in x for x in findings(good_engine, good_guide.replace('<tr><td>SPF (Email sender auth)</td><td>Text such as "SPF-record"</td></tr>', ''), "docs"))))
    cases.append(("opdagede markører fanges", any("SPF (Email sender auth)'" in x for x in f2)))
    cases.append(("ulæselige rækker fanges", any("kan ikke findes af nogen signatur" in x for x in f2)))

    # 2b. Den rumsatte form ("incident response") kan signaturen ikke finde.
    #     Det er præcis den fejl denne iteration begik i sin egen tabel, så
    #     selftesten skal kunne fange den igen.
    spaced = good_guide.replace('incident-response', 'incident response')
    f2b = findings(good_engine, spaced, "docs")
    cases.append(("rumsatte markørformer fanges", any("kan ikke findes af nogen signatur" in x for x in f2b)))

    # 3. Uden disclaimer skal publiceret afgrænsning skrives om.
    f3 = findings(good_engine.replace(DISCLAIMER, "This is fine"), good_guide, "docs")
    cases.append(("manglende disclaimer fanges", any("er væk" in x for x in f3)))

    # 4. Tjekket der ikke scores: så må R3's begrundelse ikke gælde mere.
    unscored = good_engine.replace("pass: doraMatches.length >= 2,", "note: 'x',")
    f4 = findings(unscored, good_guide, "docs")
    cases.append(("u-scored check fanges", any("boolesk pass" in x for x in f4)))

    # 5. Et ulæseligt signatur-tabel skal være rødt, ikke grønt.
    f5 = findings("const X = 1;\n", good_guide, "docs")
    cases.append(("ulæselig motor er rød", any("kunne ikke læses" in x for x in f5)))

    failed = 0
    for name, ok in cases:
        print(f"{'OK   ' if ok else 'FEJL '} {name}")
        if not ok:
            failed += 1
    print(f"\n{'SELFTEST RØD' if failed else 'SELFTEST GRØN'} — {len(cases) - failed}/{len(cases)} negative cases fanges")
    return 1 if failed else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--tree", default="site")
    args = ap.parse_args()
    if args.selftest:
        return selftest()

    source = ENGINE.read_text(encoding="utf-8")
    html = GUIDE.read_text(encoding="utf-8")
    found = findings(source, html, args.tree)
    for f in found:
        print(f"FEJL  {f}")
    if found:
        print(f"\n{len(found)} fund — DORA-siden skal kun love det, motoren gør.")
        return 1
    sigs = engine_signatures(source)
    rows = guide_marker_rows(html)
    print(
        f"OK: DORA-tjekket er {len(sigs)} statiske markører, guidens tabel dokumenterer "
        f"{len(rows)} af dem, og ingen side afgrænser det til finanssektoren."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
