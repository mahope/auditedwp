#!/usr/bin/env python3
"""Convert deliverables/*.md into branded PDFs for Gumroad upload.
Zero external deps beyond reportlab + markdown (installed locally)."""
import os, re, glob
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Preformatted
import markdown

SRC = os.path.join(os.path.dirname(__file__), "deliverables")
OUT = os.path.join(os.path.dirname(__file__), "gumroad", "products")
os.makedirs(OUT, exist_ok=True)

INK = colors.HexColor("#1a2332")
ACC = colors.HexColor("#0b6e4f")
GREY = colors.HexColor("#5a6b63")

h1 = ParagraphStyle("h1", fontName="Times-Bold", fontSize=20, leading=25, textColor=ACC, spaceAfter=10)
h2 = ParagraphStyle("h2", fontName="Times-Bold", fontSize=14, leading=18, textColor=INK, spaceBefore=14, spaceAfter=6)
h3 = ParagraphStyle("h3", fontName="Times-Bold", fontSize=11.5, leading=15, textColor=INK, spaceBefore=10, spaceAfter=4)
body = ParagraphStyle("body", fontName="Times-Roman", fontSize=10.5, leading=15, textColor=INK, spaceAfter=5)
li = ParagraphStyle("li", parent=body, leftIndent=14, bulletIndent=4)
mono = ParagraphStyle("mono", fontName="Courier", fontSize=8.5, leading=11.5, textColor=INK, backColor=colors.HexColor("#f2f5f3"), borderPadding=6)
foot = ParagraphStyle("foot", parent=body, fontSize=8, textColor=GREY)

def md_to_html(md_text):
    html = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
    html = re.sub(r"<h1>", "<h1x>", html).replace("</h1>", "</h1x>")
    return html

def html_to_flowables(html):
    """Very small tag-walker: handles h1-h4, p, li, strong/em/code."""
    from xml.etree.ElementTree import fromstring
    root = fromstring(f"<root>{html}</root>")
    out = []
    def walk(el, style):
        for child in el:
            tag = child.tag.lower()
            if tag in ("h1x", "h2"):
                out.append(Paragraph(_t(child), h1 if tag == "h1x" else h2)); continue
            if tag == "h3":
                out.append(Paragraph(_t(child), h3)); continue
            if tag == "h4":
                out.append(Paragraph(_t(child), h3)); continue
            if tag == "hr":
                out.append(HRFlowable(width="100%", color=colors.HexColor("#dde5e1"), spaceBefore=8, spaceAfter=8)); continue
            if tag == "ul" or tag == "ol":
                for item in child:
                    if item.tag.lower() == "li":
                        out.append(Paragraph("&bull; " + _t(item), li))
                continue
            if tag == "pre":
                txt = "".join(child.itertext())
                out.append(Preformatted(txt.strip(), mono)); continue
            if tag == "p":
                out.append(Paragraph(_t(child), body)); continue
            walk(child, style)
    walk(root, body)
    return out

def _t(el):
    """Recursively serialize an HTML element to reportlab paragraph markup."""
    def rec(e):
        out = []
        t = e.text or ""
        t = t.replace("&", "&amp;")
        if e.tag.lower() in ("strong", "b"): t = f"<b>{t}</b>"
        elif e.tag.lower() in ("em", "i"): t = f"<i>{t}</i>"
        elif e.tag.lower() == "code": t = f"<font face='Courier' size='9' backColor='#eef2ef'>{t}</font>"
        out.append(t)
        for c in e:
            out.append(rec(c))
            tail = c.tail or ""
            tail = tail.replace("&", "&amp;")
            out.append(tail)
        return "".join(out)
    return rec(el).replace("<b></b>", "").replace("<i></i>", "")

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Times-Roman", 8)
    canvas.setFillColor(GREY)
    canvas.drawString(20*mm, 12*mm, "ComplianceDocs - template, not legal advice")
    canvas.drawRightString(A4[0]-20*mm, 12*mm, f"Page {doc.page}")
    canvas.restoreState()

for md_path in sorted(glob.glob(os.path.join(SRC, "*.md"))):
    name = os.path.splitext(os.path.basename(md_path))[0]
    if name == "README":
        continue
    text = open(md_path, encoding="utf-8").read()
    # Standard-14 fonts lack these glyphs; use ASCII-safe equivalents
    for bad, good in {"\u2192": "->", "\u2265": ">=", "\u2264": "<=", "\u2014": " - ",
                      "\u00b7": "-", "\u2190": "<-", "\u20ac": "EUR "}.items():
        text = text.replace(bad, good)
    html = md_to_html(text)
    doc = SimpleDocTemplate(os.path.join(OUT, name + ".pdf"), pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm, topMargin=18*mm, bottomMargin=20*mm,
                            title=name.replace("-", " ").title(), author="ComplianceDocs (Mahope)")
    story = [Spacer(1, 2)]
    story += html_to_flowables(html)
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#dde5e1")))
    story.append(Paragraph("ComplianceDocs &middot; v1.0 &middot; Professional template with guidance comments - not legal advice.", foot))
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print("built", name + ".pdf")
