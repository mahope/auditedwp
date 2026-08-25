#!/usr/bin/env python3
"""Build the downloadable sample EU compliance audit report PDF (site/downloads/)."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site", "downloads", "eucomply-sample-report.pdf")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

ACC = colors.HexColor("#2868d0")
INK = colors.HexColor("#0b1a2a")
GREY = colors.HexColor("#4a5a6a")
SOFT = colors.HexColor("#f5f7fa")
WARN = colors.HexColor("#b85a0a")

h1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=20, leading=25, textColor=INK)
meta = ParagraphStyle("meta", fontName="Helvetica", fontSize=9, leading=14, textColor=GREY)
sec = ParagraphStyle("sec", fontName="Helvetica-Bold", fontSize=11, leading=15,
                     textColor=GREY, spaceBefore=16, spaceAfter=8)
body = ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=INK, spaceAfter=4)

doc = SimpleDocTemplate(OUT, pagesize=A4, topMargin=18*mm, bottomMargin=18*mm,
                        leftMargin=20*mm, rightMargin=20*mm,
                        title="EUComply Pro — Sample Compliance Audit Report",
                        author="EUComply")

E = []
E.append(Paragraph("EU Compliance Audit Report", h1))
E.append(Spacer(1, 2))
E.append(Paragraph(
    "<b>URL:</b> https://shopify.com &nbsp;·&nbsp; <b>Generated:</b> January 15, 2026 – 06:02 UTC<br/>"
    "<b>Platform detected:</b> Shopify &nbsp;·&nbsp; <b>Report ID:</b> EUC-2026-0115-0602<br/>"
    "<b>Plan:</b> EUComply Pro — daily monitoring (scan #14 of 30-day history)", meta))
E.append(Spacer(1, 10))

# Score box
score_tbl = Table([
    [Paragraph('<font size="22" color="#ffffff"><b>71%</b></font>',
               ParagraphStyle("sc", fontName="Helvetica-Bold", alignment=1)),
     Paragraph('<font size="12"><b>Overall EU Compliance Score</b></font><br/>'
               '<font size="9" color="#4a5a6a">Your site passes most automated checks. '
               'Two items need attention — see findings below.</font><br/>'
               '<font size="8" color="#ffffff"> </font>', body)],
], colWidths=[38*mm, 132*mm])
score_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#1a7a44")),
    ("BACKGROUND", (1, 0), (1, 0), SOFT),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
]))
E.append(score_tbl)
E.append(Paragraph("SAMPLE REPORT — illustrative data. Your Pro reports show live results "
                   "for your own domain.", ParagraphStyle(
                       "note", parent=meta, textColor=WARN, fontSize=8)))

E.append(Paragraph("SCORE SUMMARY", sec))
sum_tbl = Table([
    ["71%", "5/7", "2 issues", "30 days"],
    ["Overall score", "Checks passed", "Found", "Of history"],
], colWidths=[42.5*mm]*4)
sum_tbl.setStyle(TableStyle([
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, 0), 15),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("TEXTCOLOR", (0, 0), (-1, 0), INK),
    ("FONTSIZE", (0, 1), (-1, 1), 8), ("TEXTCOLOR", (0, 1), (-1, 1), GREY),
    ("BACKGROUND", (0, 0), (-1, -1), SOFT),
    ("TOPPADDING", (0, 0), (-1, 0), 10), ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
]))
E.append(sum_tbl)

checks = [
    ("✓ PASS", "#1a7a44", "HTTPS / TLS",
     "TLS 1.3 active, valid certificate (Let's Encrypt), expires Mar 12, 2026."),
    ("⚠ WARN", WARN, "HSTS header",
     "HTTPS works but Strict-Transport-Security header is missing."),
    ("✓ PASS", "#1a7a44", "Cookie consent",
     "Consent banner detected (Shopify default consent platform)."),
    ("✓ PASS", "#1a7a44", "Forms and privacy link",
     "All forms reference the privacy policy (GDPR Art. 13)."),
    ("✓ PASS", "#1a7a44", "Privacy policy",
     "Linked from homepage footer; reachable in under one click."),
    ("⚠ WARN", WARN, "Security headers",
     "Content-Security-Policy missing; X-Frame-Options not set (NIS2 Art. 21 baseline)."),
    ("✓ PASS", "#1a7a44", "Accessibility statement",
     "EAA accessibility statement found at /accessibility."),
]
rows = [[Paragraph(f'<font color="{c}"><b>{s}</b></font>', body),
         Paragraph(f"<b>{t}</b><br/><font size='8.5' color='#4a5a6a'>{d}</font>", body)]
        for s, c, t, d in checks]
chk = Table(rows, colWidths=[24*mm, 146*mm])
chk.setStyle(TableStyle([
    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, SOFT]),
    ("LINEBELOW", (0, 0), (-1, -2), 0.4, colors.HexColor("#d0d8e0")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
]))
E.append(Paragraph("DETAILED CHECK RESULTS", sec))
E.append(chk)

E.append(Paragraph("RECOMMENDED FIXES", sec))
for f in [
    "Add <b>Strict-Transport-Security: max-age=31536000; includeSubDomains</b> as a response header. "
    "One line in your edge/server config; supports GDPR Art. 32 security-of-processing.",
    "Add <b>Content-Security-Policy</b> (report-only first) and <b>X-Frame-Options: DENY</b>. "
    "Closes the two most common OWASP baseline findings auditors check.",
]:
    E.append(Paragraph("• " + f, body))

E.append(Spacer(1, 14))
E.append(Paragraph("30-DAY SCORE HISTORY", sec))
hist = Table([["Day 1–10", "Day 11–20", "Day 21–30"],
              ["68%", "70%", "71%"]], colWidths=[56.6*mm]*3)
hist.setStyle(TableStyle([
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica"), ("FONTSIZE", (0, 0), (-1, 0), 8),
    ("TEXTCOLOR", (0, 0), (-1, 0), GREY),
    ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"), ("FONTSIZE", (0, 1), (-1, 1), 13),
    ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#1a7a44")),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("BACKGROUND", (0, 0), (-1, -1), SOFT),
    ("TOPPADDING", (0, 0), (-1, 0), 6),
]))
E.append(hist)

E.append(Spacer(1, 16))
foot = ParagraphStyle("foot", parent=meta, fontSize=8, alignment=1)
E.append(Paragraph(
    "EUComply Pro · eucomplypro.com/pro · Automated technical checks only — not legal advice.<br/>"
    "This is a sample with illustrative data. Scan your own domain free at eucomplypro.com/scan",
    foot))

doc.build(E)
print("wrote", OUT)
