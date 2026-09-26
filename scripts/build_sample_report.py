#!/usr/bin/env python3
"""Build the illustrative Pro sample report: the HTML block and the sample PDF.

    python3 scripts/build_sample_report.py            # skriv begge artefakter
    python3 scripts/build_sample_report.py --check    # skriv intet, exit 1 hvis
                                                     # de committede er forældede

ÉN datasæt, to artefakter. `shared/sample-report.json` beskriver de ni tjek, og
hverken scoren, antallet af beståede, antallet af fund, datoerne eller
historiklængden står noget sted — de er afledt. Det er hele pointen: den gamle
opslagstilling havde tal i HTML'en OG tal i PDF-scriptet, og de to var kun enige
fordi nogen havde husket at rette begge.

De ni `key`-værdier er motorens egne. De læses ud af `shared/scan-engine.js` og
`eucomply-scanner/engine/index.js` — de to kopier, som `tools/test_engine_parity.mjs`
allerede holder sammen — og datasættet må ikke afvige fra dem. En rapport der
viser syv af ni tjek får en køber til at tro at den betalte rapport er mindre
end den gratis scanner, han lige har kørt.
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import sys
from xml.sax.saxutils import escape as xml_escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "shared", "sample-report.json")
ENGINES = (
    os.path.join(ROOT, "shared", "scan-engine.js"),
    os.path.join(ROOT, "eucomply-scanner", "engine", "index.js"),
)
PAGE = os.path.join(ROOT, "site", "pro", "sample-report", "index.html")
PDF = os.path.join(ROOT, "site", "downloads", "eucomply-sample-report.pdf")

START = "<!--sample:report-->"
END = "<!--/sample:report-->"

# `checks.<key> = {` er den måde motoren bygger sit resultatobjekt på. Der er
# ingen navngiven eksport af nøglerne, så det er kilden, der læses — fra BEGGE
# motorer, så en tjek kun findes i den ene, og det derfor er en fejl.
CHECK_KEY = re.compile(r"^\s*checks\.([A-Za-z0-9_]+)\s*=\s*\{", re.M)
STATUSES = ("pass", "warn", "fail")
MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")
WORDS = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five",
         6: "Six", 7: "Seven", 8: "Eight", 9: "Nine"}


def engine_keys(path):
    """De check-nøgler en motor bygger, i den rækkefølge den bygger dem i."""
    with open(path, encoding="utf-8") as handle:
        source = handle.read()
    return CHECK_KEY.findall(source)


def engine_check_keys():
    """Nøglerne fra alle motorer — eller en fejl hvis de er uenige."""
    per_engine = []
    for path in ENGINES:
        if not os.path.exists(path):
            raise SystemExit(f"motor mangler: {os.path.relpath(path, ROOT)}")
        per_engine.append((path, engine_keys(path)))
    first_path, first = per_engine[0]
    for path, keys in per_engine[1:]:
        if keys != first:
            raise SystemExit(
                "motorerne er uenige om hvilke tjek de kører:\n"
                f"  {os.path.relpath(first_path, ROOT)}: {', '.join(first)}\n"
                f"  {os.path.relpath(path, ROOT)}: {', '.join(keys)}"
            )
    if not first:
        raise SystemExit("ingen check-nøgler fundet i motorerne")
    return first


def load_data():
    with open(DATA, encoding="utf-8") as handle:
        return json.load(handle)


def coverage_findings(data):
    """Uoverensstemmelser mellem datasættet og motoren. Tom liste = dækket."""
    findings = []
    try:
        keys = engine_check_keys()
    except SystemExit as error:
        return [str(error)]
    listed = [entry.get("key") for entry in data.get("checks", [])]
    for key in keys:
        if key not in listed:
            findings.append(f"motoren kører tjekket '{key}', prøverapporten viser det ikke")
    for key in listed:
        if key not in keys:
            findings.append(f"prøverapporten viser tjekket '{key}', motoren kører det ikke")
    seen = [key for key in listed if listed.count(key) > 1]
    for key in dict.fromkeys(seen):
        findings.append(f"tjekket '{key}' står mere end én gang i prøverapporten")
    for entry in data.get("checks", []):
        if entry.get("status") not in STATUSES:
            findings.append(f"tjekket '{entry.get('key')}' har status '{entry.get('status')}'")
        for field in ("title", "detail"):
            if not str(entry.get(field, "")).strip():
                findings.append(f"tjekket '{entry.get('key')}' mangler {field}")
    return findings


def summarize(data):
    """Alle tal i rapporten, afledt af de ni tjek og af historikken."""
    checks = data["checks"]
    total = len(checks)
    passed = sum(1 for entry in checks if entry["status"] == "pass")
    issues = total - passed
    score = round(100 * passed / total) if total else 0
    failed = sum(1 for entry in checks if entry["status"] == "fail")
    if issues == 0:
        headline = "Every automated check passed. No items need attention."
        badge = "Pass — no issues found"
    else:
        word = WORDS.get(issues, str(issues))
        noun = "item" if issues == 1 else "items"
        headline = f"{word} {noun.lower()} need{'s' if issues == 1 else ''} attention — see findings below."
        badge = "Attention needed" if failed else "Pass — minor issues found"
    return {
        "total": total,
        "passed": passed,
        "issues": issues,
        "failed": failed,
        "score": score,
        "headline": headline,
        "badge": badge,
        "circle": "fail" if failed else ("warn" if issues else "pass"),
    }


def generated_stamp(data):
    meta = data["meta"]
    day = dt.date.fromisoformat(meta["generated_iso"])
    report_id = "EUC-{0}-{1}-{2}".format(
        day.strftime("%Y"), day.strftime("%m%d"), meta["generated_time"].replace(":", "")
    )
    shown = "{0} {1}, {2} – {3} UTC".format(
        MONTHS[day.month - 1], day.day, day.year, meta["generated_time"]
    )
    return day, shown, report_id


def history_rows(data, score):
    """Historie-bjærkerne: dato, højde og farve afledt af listens tal."""
    values = data["history"]
    if not values:
        return []
    last = dt.date.fromisoformat(data["meta"]["generated_iso"])
    rows = []
    for offset, value in enumerate(values):
        day = last - dt.timedelta(days=len(values) - 1 - offset)
        band = "ok" if value >= score else ("warn" if value >= score - 10 else "fail")
        rows.append({
            "date": day,
            "label": "{0} {1}".format(MONTHS[day.month - 1][:3], day.day),
            "value": value,
            "height": 8 + round(16 * value / 100),
            "band": band,
        })
    return rows


def dip_note(rows):
    """Den laveste sammenhængende periode under dagens score — eller intet."""
    dips, current = [], []
    for row in rows:
        if row["band"] == "ok":
            if current:
                dips.append(current)
                current = []
        else:
            current.append(row)
    if current:
        dips.append(current)
    if not dips:
        return None
    worst = min(dips, key=lambda group: min(row["value"] for row in group))
    span = worst[0]["label"] if len(worst) == 1 else "{0}–{1}".format(worst[0]["label"], worst[-1]["label"])
    return "{0}: illustrative score change in this static sample; no monitoring event occurred.".format(span)


def recommended_fixes(data):
    """Fund med en 'fix' — i den rækkefølge tjekket står i."""
    return [entry for entry in data["checks"] if entry.get("fix")]


def report_block(data):
    """Hele den genererede del af HTML-siden, som et indhold afgrænset af markører."""
    summary = summarize(data)
    day, stamp, report_id = generated_stamp(data)
    rows = history_rows(data, summary["score"])
    fixes = recommended_fixes(data)
    out = []
    add = out.append
    add("")
    add('<div class="report-header">')
    add('  <h1>Illustrative EU compliance report</h1>')
    add('  <p style="font-size:13px;color:var(--muted);background:var(--panel);border:1px solid var(--accent);'
        'border-radius:8px;padding:8px 12px;margin:8px 0">Static concept sample, generated {0}. {1}</p>'.format(
            html.escape(stamp), html.escape(data["disclaimer"])))
    add('  <p style="margin:10px 0 2px"><a href="/downloads/eucomply-sample-report.pdf" download '
        'style="display:inline-block;background:var(--accent);color:var(--panel);text-decoration:none;'
        'font-weight:700;font-size:14px;padding:10px 22px;border-radius:8px">Download the static sample PDF</a></p>')
    add('  <div class="meta">')
    add('    <strong>URL:</strong> {0}<br>'.format(html.escape(data["meta"]["url"])))
    add('    <strong>Generated:</strong> {0}<br>'.format(html.escape(stamp)))
    add('    <strong>Platform detected:</strong> {0}<br>'.format(html.escape(data["meta"]["platform"])))
    add('    <strong>Report ID:</strong> {0}<br>'.format(html.escape(report_id)))
    add('    <strong>Checks in this report:</strong> {0} — the same {1} the scanner runs'.format(
        summary["total"], "check" if summary["total"] == 1 else "checks"))
    add('  </div>')
    add('</div>')
    add("")
    add('<div class="score-section">')
    add('  <div class="score-circle {0}">{1}%</div>'.format(summary["circle"], summary["score"]))
    add('  <div class="score-details">')
    add('    <h2>Overall EU Compliance Score</h2>')
    add('    <p>{0}</p>'.format(html.escape(summary["headline"])))
    add('    <div class="status"> {0}</div>'.format(html.escape(summary["badge"])))
    add('  </div>')
    add('</div>')
    add("")
    add('<div class="section">')
    add('  <h3>Score Summary</h3>')
    add('  <div class="summary-grid">')
    add('    <div class="summary-item">')
    add('      <span class="value">{0}%</span>'.format(summary["score"]))
    add('      <span class="label">Overall score</span>')
    add('    </div>')
    add('    <div class="summary-item">')
    add('      <span class="value">{0}/{1}</span>'.format(summary["passed"], summary["total"]))
    add('      <span class="label">Checks passed</span>')
    add('    </div>')
    add('    <div class="summary-item">')
    add('      <span class="value">{0}</span>'.format(summary["issues"]))
    add('      <span class="label">Items needing attention</span>')
    add('    </div>')
    add('    <div class="summary-item">')
    add('      <span class="value">{0}</span>'.format(len(rows)))
    add('      <span class="label">Days of history</span>')
    add('    </div>')
    add('  </div>')
    add('</div>')
    add("")
    add('<div class="section">')
    add('  <h3>Detailed Check Results</h3>')
    add('  <ul class="check-list">')
    for entry in data["checks"]:
        status = entry["status"]
        icon = {"pass": "✓", "warn": "!", "fail": "✕"}[status]
        add('    <li data-check="{0}"><span class="icon {1}">{2}</span>'.format(
            html.escape(entry["key"]), status, icon))
        add('      <span class="label">{0}</span>'.format(html.escape(entry["title"], quote=False)))
        add('      <span class="detail">{0}'.format(html.escape(entry["detail"], quote=False)))
        if entry.get("fix"):
            add('        <span class="fix">→ {0}</span>'.format(html.escape(entry["fix"], quote=False)))
        add('      </span>')
        add('    </li>')
    add('  </ul>')
    add('  <p style="font-size:12px;color:var(--muted);margin-top:10px">This is the same set of checks the '
        'free scanner runs on every site, so nothing here is held back for Pro.</p>')
    add('</div>')
    add("")
    if fixes:
        add('<div class="section">')
        add('  <h3>Recommended Fixes (priority order)</h3>')
        add('  <ol style="font-size:14px;padding-left:20px">')
        for position, entry in enumerate(fixes, start=1):
            last = "margin-bottom:6px" if position == len(fixes) else "margin-bottom:10px"
            add('    <li style="{0}"><strong>{1}</strong> — {2}</li>'.format(
                last, html.escape(entry["title"], quote=False), html.escape(entry["fix"], quote=False)))
        add('  </ol>')
        add('</div>')
        add("")
    add('<div class="section">')
    add('  <h3>Illustrative {0}-day history</h3>'.format(len(rows)))
    add('  <p style="font-size:14px;color:var(--muted);margin-bottom:10px">Example score trend in this static sample:</p>')
    add('  <div style="background:var(--soft);border-radius:6px;padding:14px;font-size:13px;overflow-x:auto">')
    for row in rows:
        add('    <span style="display:inline-block;width:14px;height:{0}px;background:var(--{1});'
            'margin:0 1px;border-radius:2px" title="{2}: {3}%"></span>'.format(
                row["height"], row["band"], row["label"], row["value"]))
    add('    <br><span style="color:var(--muted);font-size:11px">{0}</span>'.format(
        " " * 15 + html.escape(rows[0]["label"])))
    add('  </div>')
    note = dip_note(rows)
    if note:
        add('  <p style="font-size:12px;color:var(--muted);margin-top:8px"><strong>{0}</strong></p>'.format(
            html.escape(note)))
    add('</div>')
    return "\n".join(out) + "\n"


def build_html(data):
    """Skriv den genererede blok ind i kildesiden mellem de to markører."""
    with open(PAGE, encoding="utf-8") as handle:
        page = handle.read()
    if START not in page or END not in page:
        raise SystemExit(f"{os.path.relpath(PAGE, ROOT)} mangler markørerne {START} / {END}")
    head, rest = page.split(START, 1)
    _, tail = rest.split(END, 1)
    block = report_block(data)
    updated = head + START + "\n" + block + END + tail
    if updated == page:
        return False
    with open(PAGE, "w", encoding="utf-8") as handle:
        handle.write(updated)
    return True


def build_pdf(data, path=PDF):
    """Skriv prøve-PDF'en. Samme datasæt, samme afledte tal, samme rækkefølge."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    summary = summarize(data)
    day, stamp, report_id = generated_stamp(data)
    rows = history_rows(data, summary["score"])
    fixes = recommended_fixes(data)
    ink = colors.HexColor("#0b1a2a")
    grey = colors.HexColor("#4a5a6a")
    soft = colors.HexColor("#f5f7fa")
    warn = colors.HexColor("#b85a0a")
    fail = colors.HexColor("#b3261e")
    good = colors.HexColor("#1a7a44")
    band = {"pass": ("✓ PASS", "#1a7a44"), "warn": ("⚠ WARN", "#b85a0a"), "fail": ("✕ FAIL", "#b3261e")}

    h1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=20, leading=25, textColor=ink)
    meta_style = ParagraphStyle("meta", fontName="Helvetica", fontSize=9, leading=14, textColor=grey)
    sec = ParagraphStyle("sec", fontName="Helvetica-Bold", fontSize=11, leading=15,
                         textColor=grey, spaceBefore=16, spaceAfter=8)
    body = ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=ink, spaceAfter=4)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    # invariant=1 gør filen byte-for-byte reproducerbar, så gaten kan
    # regenerere den og sammenligne — ellers ville "PDF'en er i sync" være en
    # påstand uden dækning.
    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm,
                            leftMargin=20 * mm, rightMargin=20 * mm, invariant=1,
                            title="EUComply Pro — Sample Compliance Audit Report", author="EUComply")
    story = [Paragraph("EU Compliance Audit Report", h1), Spacer(1, 2)]
    story.append(Paragraph(
        "<b>URL:</b> {0} &nbsp;·&nbsp; <b>Generated:</b> {1}<br/>"
        "<b>Platform detected:</b> {2} &nbsp;·&nbsp; <b>Report ID:</b> {3}<br/>"
        "<b>Checks in this report:</b> {4} — the same {5} the scanner runs".format(
            xml_escape(data["meta"]["url"]), xml_escape(stamp), xml_escape(data["meta"]["platform"]),
            xml_escape(report_id), summary["total"], "check" if summary["total"] == 1 else "checks"), meta_style))
    story.append(Spacer(1, 10))

    score_cell = ParagraphStyle("sc", fontName="Helvetica-Bold", alignment=1)
    score_tbl = Table([
        [Paragraph('<font size="22" color="#ffffff"><b>{0}%</b></font>'.format(summary["score"]), score_cell),
         Paragraph('<font size="12"><b>Overall EU Compliance Score</b></font><br/>'
                   '<font size="9" color="#4a5a6a">{0}</font>'.format(xml_escape(summary["headline"])), body)],
    ], colWidths=[38 * mm, 132 * mm])
    score_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), fail if summary["failed"] else good),
        ("BACKGROUND", (1, 0), (1, 0), soft),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(score_tbl)
    story.append(Paragraph(
        "CONCEPT SAMPLE — {0} The current Pro license generates an HTML report from the latest WordPress scan.".format(
            xml_escape(data["disclaimer"])),
        ParagraphStyle("note", parent=meta_style, textColor=warn, fontSize=8)))

    story.append(Paragraph("SCORE SUMMARY", sec))
    summary_tbl = Table([
        ["{0}%".format(summary["score"]),
         "{0}/{1}".format(summary["passed"], summary["total"]),
         "{0} {1}".format(summary["issues"], "item" if summary["issues"] == 1 else "items"),
         "{0} days".format(len(rows))],
        ["Overall score", "Checks passed", "Need attention", "Of history"],
    ], colWidths=[42.5 * mm] * 4)
    summary_tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, 0), 15),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("TEXTCOLOR", (0, 0), (-1, 0), ink),
        ("FONTSIZE", (0, 1), (-1, 1), 8), ("TEXTCOLOR", (0, 1), (-1, 1), grey),
        ("BACKGROUND", (0, 0), (-1, -1), soft),
        ("TOPPADDING", (0, 0), (-1, 0), 10), ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
    ]))
    story.append(summary_tbl)

    check_rows = []
    for entry in data["checks"]:
        label, colour = band[entry["status"]]
        detail = xml_escape(entry["detail"])
        if entry.get("fix"):
            detail += '<br/><font size="8.5" color="#0b6e4f">→ {0}</font>'.format(xml_escape(entry["fix"]))
        check_rows.append([
            Paragraph('<font color="{0}"><b>{1}</b></font>'.format(colour, xml_escape(label)), body),
            Paragraph("<b>{0}</b><br/><font size='8.5' color='#4a5a6a'>{1}</font>".format(
                xml_escape(entry["title"]), detail), body),
        ])
    check_tbl = Table(check_rows, colWidths=[24 * mm, 146 * mm])
    check_tbl.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, soft]),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor("#d0d8e0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(Paragraph("DETAILED CHECK RESULTS", sec))
    story.append(check_tbl)

    if fixes:
        story.append(Paragraph("RECOMMENDED FIXES", sec))
        for entry in fixes:
            story.append(Paragraph("• <b>{0}</b> — {1}".format(
                xml_escape(entry["title"]), xml_escape(entry["fix"])), body))

    story.append(Spacer(1, 14))
    story.append(Paragraph("ILLUSTRATIVE {0}-DAY SCORE HISTORY — CONCEPT ONLY".format(len(rows)), sec))
    third = max(1, -(-len(rows) // 3))
    cells = []
    for start in range(0, len(rows), third):
        group = rows[start:start + third]
        cells.append([row["value"] for row in group])
    while len(cells) < 3:
        cells.append([])
    while len(cells[0]) < third:
        for cell in cells:
            cell.append("")
    history_tbl = Table([
        ["Days 1–{0}".format(third), "Days {0}–{1}".format(third + 1, third * 2),
         "Days {0}–{1}".format(third * 2 + 1, len(rows))] if len(rows) > third else ["", "", ""],
        ["{0}%".format(value) if value != "" else "" for value in cells[0]],
        ["{0}%".format(value) if value != "" else "" for value in cells[1]],
        ["{0}%".format(value) if value != "" else "" for value in cells[2]],
    ], colWidths=[56.6 * mm] * 3)
    history_tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica"), ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("TEXTCOLOR", (0, 0), (-1, 0), grey),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica-Bold"), ("FONTSIZE", (0, 1), (-1, -1), 13),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("BACKGROUND", (0, 0), (-1, -1), soft),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
    ]))
    story.append(history_tbl)

    story.append(Spacer(1, 16))
    foot = ParagraphStyle("foot", parent=meta_style, fontSize=8, alignment=1)
    story.append(Paragraph(
        "EUComply Pro · eucomplypro.com/pro · Automated technical checks only — not legal advice.<br/>"
        "This is a sample with illustrative data. Scan your own domain free at eucomplypro.com/scan", foot))
    doc.build(story)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="skriv intet; exit 1 hvis de committede artefakter ikke matcher datasættet")
    args = parser.parse_args()
    data = load_data()
    findings = coverage_findings(data)
    if findings:
        for finding in findings:
            print("FEJL  " + finding)
        print("\n{0} prøverapport-fund".format(len(findings)))
        return 1
    if args.check:
        problems = []
        with open(PAGE, encoding="utf-8") as handle:
            page = handle.read()
        if START not in page or END not in page:
            problems.append(f"{os.path.relpath(PAGE, ROOT)} mangler markørerne")
        else:
            head, rest = page.split(START, 1)
            block, tail = rest.split(END, 1)
            if head + START + "\n" + report_block(data) + END + tail != page:
                problems.append(f"{os.path.relpath(PAGE, ROOT)} afviger fra shared/sample-report.json — kør scripts/build_sample_report.py")
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            fresh = build_pdf(data, os.path.join(folder, "sample.pdf"))
            with open(fresh, "rb") as a, open(PDF, "rb") as b:
                if a.read() != b.read():
                    problems.append("site/downloads/eucomply-sample-report.pdf afviger fra datasættet — kør scripts/build_sample_report.py")
        for problem in problems:
            print("FEJL  " + problem)
        if problems:
            print("\n{0} prøverapport-fund".format(len(problems)))
            return 1
        print("OK    prøverapportens HTML og PDF matcher shared/sample-report.json")
        return 0
    changed = build_html(data)
    build_pdf(data)
    print("skrev {0}{1}".format(os.path.relpath(PDF, ROOT), " og HTML-blokken" if changed else " (HTML uændret)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
