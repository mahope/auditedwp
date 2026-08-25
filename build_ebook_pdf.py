#!/usr/bin/env python3
"""Build 'The Practical Guide to EU Compliance 2026' PDF from book/manuscript.
Output: site/book/eu-website-compliance-guide-2026.pdf"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak
import markdown

ROOT = os.path.dirname(os.path.abspath(__file__))
MANU = os.path.join(ROOT, "book", "manuscript")
OUT_DIR = os.path.join(ROOT, "site", "book")
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "eu-website-compliance-guide-2026.pdf")

INK = colors.HexColor("#1a2332")
ACC = colors.HexColor("#0b6e4f")
GREY = colors.HexColor("#5a6b63")

h1 = ParagraphStyle("h1", fontName="Times-Bold", fontSize=22, leading=27, textColor=ACC, spaceAfter=12)
h2 = ParagraphStyle("h2", fontName="Times-Bold", fontSize=15, leading=19, textColor=INK, spaceBefore=16, spaceAfter=7)
h3 = ParagraphStyle("h3", fontName="Times-Bold", fontSize=12, leading=15.5, textColor=INK, spaceBefore=11, spaceAfter=5)
body = ParagraphStyle("body", fontName="Times-Roman", fontSize=10.8, leading=15.2, textColor=INK, spaceAfter=6)
li = ParagraphStyle("li", parent=body, leftIndent=14, bulletIndent=4)
quote = ParagraphStyle("quote", parent=body, leftIndent=18, textColor=GREY, fontStyle="italic")

def html_to_flowables(html):
    from xml.etree.ElementTree import fromstring
    root = fromstring(f"<root>{html}</root>")
    out = []
    def walk(el):
        for child in el:
            tag = child.tag.lower()
            if tag in ("h1", "h2", "h3", "h4"):
                style = {"h1": h1, "h2": h2, "h3": h3, "h4": h3}[tag]
                out.append(Paragraph(_inline(child), style))
            elif tag == "p":
                out.append(Paragraph(_inline(child), body))
            elif tag in ("ul", "ol"):
                for item in child:
                    if item.tag.lower() == "li":
                        out.append(Paragraph("&bull; " + _inline(item), li))
            elif tag == "blockquote":
                for p in child:
                    out.append(Paragraph(_inline(p), quote))
            elif tag == "hr":
                out.append(Spacer(1, 4))
                out.append(HRFlowable(width="100%", color=colors.HexColor("#dde5e1")))
            elif tag == "table":
                for row in child.iter():
                    if row.tag.lower() == "tr":
                        cells = [ _inline(c) for c in row if c.tag.lower() in ("td","th") ]
                        if cells:
                            out.append(Paragraph(" | ".join(cells), body))
                out.append(Spacer(1, 4))
            else:
                walk(child)
    walk(root)
    return out

def _inline(el):
    parts = []
    def rec(node):
        if node.text: parts.append(_esc(node.text))
        for c in node:
            t = c.tag.lower()
            inner = ""
            def gather(n):
                nonlocal inner
                if n.text: inner += _esc(n.text)
                for cc in n:
                    gather(cc)
                if n.tail: inner += _esc(n.tail)
            if t in ("strong","b"): inner = "<b>"; gather(c); inner += "</b>"
            elif t in ("em","i"): inner = "<i>"; gather(c); inner += "</i>"
            elif t == "code": inner = "<font face='Courier' size='9'>"; gather(c); inner += "</font>"
            elif t == "a": inner = ""; gather(c)  # strip links in print
            else: gather(c)
            parts.append(inner)
            if c.tail: parts.append(_esc(c.tail))
    rec(el)
    return "".join(parts)

def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Times-Roman", 8)
    canvas.setFillColor(GREY)
    canvas.drawString(20*mm, 14*mm, "The Practical Guide to EU Compliance 2026")
    canvas.drawRightString(A4[0]-20*mm, 14*mm, str(canvas.getPageNumber()))
    canvas.restoreState()

story = []
# Title page
story.append(Spacer(1, 70*mm))
story.append(Paragraph("The Practical Guide to<br/>EU Compliance 2026", ParagraphStyle("t", parent=h1, fontSize=28, leading=34)))
story.append(HRFlowable(width="40%", color=ACC))
story.append(Spacer(1, 8*mm))
story.append(Paragraph("What every website owner must know about GDPR, NIS2, DORA &amp; the EAA &mdash; in plain language.", body))
story.append(Spacer(1, 30*mm))
story.append(Paragraph("EUComply &middot; eucomplypro.com", ParagraphStyle("a", parent=body, textColor=GREY)))
story.append(PageBreak())

chapters = ["01-Intro.md","02-GDPR.md","03-NIS2.md","04-DORA.md","05-EAA.md",
            "06-Scan.md","07-Roadmap.md","08-Resources.md","09-Conclusion.md"]
for i, ch in enumerate(chapters):
    text = open(os.path.join(MANU, ch)).read()
    # demote file-level h1 markers like "# 01-Intro.md" duplicates
    lines = text.split("\n")
    if lines and lines[0].startswith("# ") and len(lines) > 1 and lines[1].startswith("#"):
        text = "\n".join(lines[1:])
    html = markdown.markdown(text, extensions=["tables", "fenced_code"])
    story.extend(html_to_flowables(html))
    if i < len(chapters) - 1:
        story.append(PageBreak())

doc = SimpleDocTemplate(OUT, pagesize=A4,
    leftMargin=22*mm, rightMargin=22*mm, topMargin=20*mm, bottomMargin=22*mm,
    title="The Practical Guide to EU Compliance 2026", author="EUComply")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("OK:", OUT, os.path.getsize(OUT), "bytes")
