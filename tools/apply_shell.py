#!/usr/bin/env python3
"""Inject the shared EUComply shell (header, footer, site.css, site.js) into every
HTML page under site/, strip legacy shell CSS/markup, map legacy colours to the
design tokens, fill in SEO head tags and JSON-LD, clean up hype, and rebuild
sitemap.xml.  Idempotent: safe to run repeatedly.

    python tools/apply_shell.py            # apply to all pages
    python tools/apply_shell.py --dry-run  # report only
"""
import colorsys
import datetime as dt
import html as htmlmod
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
PARTIALS = SITE / "_partials"
ORIGIN = "https://eucomplypro.com"
LANGS = ["en", "da", "de", "fr"]
DRY = "--dry-run" in sys.argv
TODAY = dt.date.today().isoformat()
AUTHOR = {"@type": "Person", "name": "Mads Holst Jensen", "url": "https://mahoje.dk"}
ORG = {"@type": "Organization", "name": "EUComply", "url": ORIGIN + "/",
       "logo": {"@type": "ImageObject", "url": ORIGIN + "/icon-512.png"},
       "founder": AUTHOR}

I18N = {
    "en": dict(nav_label="Main", menu_label="Menu", nav_scan="Scan", nav_guide="Guide", nav_checklists="Checklists",
               nav_pricing="Pricing", nav_blog="Blog", built_by="Built by",
               maker_desc="developer and technical partner, Odense, Denmark.",
               source_on_github="Scanner source on GitHub",
               privacy_note="This site sets no cookies and loads no trackers or external fonts.",
               legal_note="Everything here is technical guidance, not legal advice.",
               col_site="On this site", col_sisters="Also by mahoje.dk", fine_calc="GDPR fine calculator",
               privacy="Privacy", terms="Terms",
               pro_status="Pro launches when checkout is live; the free scanner is complete.",
               checklist_link="compliance checklist",
               gen_title="This generator has been taken down",
               ),
    "da": dict(nav_label="Hovedmenu", menu_label="Menu", nav_scan="Scan", nav_guide="Guide", nav_checklists="Tjeklister",
               nav_pricing="Priser", nav_blog="Blog", built_by="Udviklet af",
               maker_desc="udvikler og teknisk partner, Odense.",
               source_on_github="Scannerens kildekode på GitHub",
               privacy_note="Sitet sætter ingen cookies og indlæser hverken trackere eller eksterne skrifttyper.",
               legal_note="Alt her er teknisk vejledning, ikke juridisk rådgivning.",
               col_site="På dette site", col_sisters="Også fra mahoje.dk", fine_calc="GDPR-bødeberegner",
               privacy="Privatliv", terms="Vilkår",
               pro_status="Pro åbner, når betaling er koblet på; den gratis scanner er færdig.",
               checklist_link="compliance-tjekliste",
               gen_title="Denne generator er taget ned",
               ),
    "de": dict(nav_label="Hauptmenü", menu_label="Menü", nav_scan="Scan", nav_guide="Leitfaden", nav_checklists="Checklisten",
               nav_pricing="Preise", nav_blog="Blog", built_by="Entwickelt von",
               maker_desc="Entwickler und technischer Partner, Odense, Dänemark.",
               source_on_github="Quellcode des Scanners auf GitHub",
               privacy_note="Diese Website setzt keine Cookies und lädt weder Tracker noch externe Schriften.",
               legal_note="Alles hier ist technische Orientierung, keine Rechtsberatung.",
               col_site="Auf dieser Website", col_sisters="Ebenfalls von mahoje.dk", fine_calc="DSGVO-Bußgeldrechner",
               privacy="Datenschutz", terms="Nutzungsbedingungen",
               pro_status="Pro startet, sobald die Bezahlung angebunden ist; der kostenlose Scanner ist fertig.",
               checklist_link="Compliance-Checkliste",
               gen_title="Dieser Generator wurde abgeschaltet",
               ),
    "fr": dict(nav_label="Menu principal", menu_label="Menu", nav_scan="Scanner", nav_guide="Guide", nav_checklists="Check-lists",
               nav_pricing="Tarifs", nav_blog="Blog", built_by="Développé par",
               maker_desc="développeur et partenaire technique, Odense, Danemark.",
               source_on_github="Code source du scanner sur GitHub",
               privacy_note="Ce site ne dépose aucun cookie et ne charge ni traceur ni police externe.",
               legal_note="Tout ce qui figure ici est une aide technique, pas un conseil juridique.",
               col_site="Sur ce site", col_sisters="Également par mahoje.dk", fine_calc="Calculateur d'amende RGPD",
               privacy="Confidentialité", terms="Conditions",
               pro_status="Pro sera disponible lorsque le paiement sera activé ; le scanner gratuit est complet.",
               checklist_link="check-list de conformité",
               gen_title="Ce générateur a été retiré",
               ),
}
I18N["es"] = I18N["en"]
LANG_LABEL = {"en": "EN", "da": "DA", "de": "DE", "fr": "FR", "es": "ES"}
OG_LOCALE = {"en": "en_GB", "da": "da_DK", "de": "de_DE", "fr": "fr_FR", "es": "es_ES"}

# Pages whose localised versions live under /<lang>/ when they exist.
CORE = {"", "scan/", "pricing/", "book/"}

GENERATORS = ["impressum-generator", "privacy-policy-generator", "terms-of-service-generator",
              "refund-policy-generator", "cookie-policy-generator", "tools"]

SKIP_FILES = {"shared/live-check-widget.html"}

HEADER_TPL = (PARTIALS / "header.html").read_text(encoding="utf-8")
FOOTER_TPL = (PARTIALS / "footer.html").read_text(encoding="utf-8")

ICON_LINKS = """<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#0b6e4f">"""

JS_BOOT = '<script>document.documentElement.classList.add("js")</script>'


def asset_version(name: str) -> str:
    """Short content hash so a changed asset gets a new URL past the CDN cache."""
    import hashlib
    return hashlib.sha1((SITE / "assets" / name).read_bytes()).hexdigest()[:8]


CSS_V = asset_version("site.css")
JS_V = asset_version("site.js")

# ----------------------------------------------------------------- helpers

def rel_url(path: Path) -> str:
    """site/da/scan/index.html -> /da/scan/ ; site/404.html -> /404.html"""
    rel = path.relative_to(SITE).as_posix()
    if rel.endswith("index.html"):
        rel = rel[: -len("index.html")]
    return "/" + rel


def lang_of(url: str) -> str:
    m = re.match(r"^/(da|de|fr|es)/", url)
    return m.group(1) if m else "en"


def strip_lang(url: str) -> str:
    return re.sub(r"^/(da|de|fr|es)/", "/", url)


def alternates(url: str) -> dict:
    """Return {lang: url} for every existing language version of this page."""
    base = strip_lang(url)  # e.g. /scan/
    out = {}
    for lang in LANGS + ["es"]:
        cand = base if lang == "en" else "/" + lang + base
        fs = SITE / cand.lstrip("/")
        if cand.endswith("/"):
            fs = fs / "index.html"
        if fs.exists():
            out[lang] = cand
    return out


def core_path(lang: str, base: str) -> str:
    """Localised path for a core page if it exists, else the English one."""
    if lang != "en":
        cand = SITE / lang / base / "index.html" if base else SITE / lang / "index.html"
        if cand.exists():
            return f"/{lang}/{base}"
    return "/" + base


def render_shell(url: str, lang: str) -> tuple[str, str]:
    t = dict(I18N[lang])
    t["home"] = core_path(lang, "")
    t["p_scan"] = core_path(lang, "scan/")
    t["p_book"] = core_path(lang, "book/")
    t["p_pricing"] = core_path(lang, "pricing/")
    base = strip_lang(url)
    for key, pat in (("scan", "/scan/"), ("book", "/book/"), ("checklist", "/checklist/"),
                     ("pricing", "/pricing/"), ("blog", "/blog/")):
        t["cur_" + key] = ' aria-current="page"' if base == pat or (key == "blog" and base.startswith("/blog/")) else ""
    alts = alternates(url)
    if len(alts) >= 2:
        items = []
        for l in LANGS + ["es"]:
            if l not in alts:
                continue
            if l == lang:
                items.append(f'<li><span aria-current="true" lang="{l}">{LANG_LABEL[l]}</span></li>')
            else:
                items.append(f'<li><a href="{alts[l]}" hreflang="{l}" lang="{l}">{LANG_LABEL[l]}</a></li>')
        t["langswitch"] = '<ul class="sh-lang" aria-label="Language">' + "".join(items) + "</ul>"
    else:
        t["langswitch"] = ""
    header = HEADER_TPL
    footer = FOOTER_TPL
    for k, v in t.items():
        header = header.replace("{{" + k + "}}", v)
        footer = footer.replace("{{" + k + "}}", v)
    return header.strip(), footer.strip()


# ------------------------------------------------------------- git dates

def git_dates() -> dict:
    """{relpath: (first_commit_date, last_commit_date)} for files under site/."""
    out = {}
    try:
        log = subprocess.run(["git", "log", "--format=@%cs", "--name-only", "--", "site"],
                             cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    except Exception:
        return out
    cur = None
    for line in log.splitlines():
        if line.startswith("@"):
            cur = line[1:]
        elif line.strip() and cur:
            rel = line.strip()
            if rel.startswith("site/"):
                rel = rel[5:]
            first, last = out.get(rel, (cur, cur))
            out[rel] = (cur, last)  # log is newest-first: keep last, overwrite first
    return out


GIT_DATES = git_dates()


# ---------------------------------------------------------------- CSS filter

SHELL_SEL = re.compile(
    r"^(html|\*|header|footer|nav|\.logo|\.brand|\.nav|\.site-header|\.site-footer|\.topbar|\.navbar|\.cta)(\b|$)",
    re.I,
)


def split_rules(css: str):
    """Yield (selector, body) for top-level rules; handles one level of nesting."""
    i, n = 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0:
            break
        sel = css[i:j].strip()
        depth, k = 1, j + 1
        while k < n and depth:
            if css[k] == "{":
                depth += 1
            elif css[k] == "}":
                depth -= 1
            k += 1
        body = css[j + 1 : k - 1]
        yield sel, body
        i = k


def filter_css(css: str) -> str:
    """Drop shell rules (header/nav/footer/*/html) and move body layout to .pg-legacy."""
    out = []
    legacy_layout = []
    for sel, body in split_rules(css):
        if sel.startswith("@media") or sel.startswith("@supports"):
            inner = filter_css(body)
            if inner.strip():
                out.append(f"{sel}{{{inner}}}")
            continue
        if sel.startswith("@"):
            out.append(f"{sel}{{{body}}}")
            continue
        parts = [p.strip() for p in sel.split(",")]
        keep = [p for p in parts if not SHELL_SEL.match(p) and not re.match(r"^body\s*>?\s*(header|nav|footer)", p)]
        body_parts = [p for p in parts if p == "body"]
        if body_parts:
            decls = [d.strip() for d in body.split(";") if d.strip()]
            move = [d for d in decls if re.match(r"(max-width|width|margin|padding)\s*:", d)]
            stay = [d for d in decls if d not in move]
            if move:
                legacy_layout.extend(move)
            if stay:
                out.append("body{" + ";".join(stay) + "}")
            keep = [p for p in keep if p != "body"]
            if not keep:
                continue
        if not keep:
            continue
        if keep != parts:
            out.append(",".join(keep) + "{" + body + "}")
        else:
            out.append(sel + "{" + body + "}")
    if legacy_layout:
        out.append(".pg-legacy{" + ";".join(legacy_layout) + "}")
    return "\n".join(out)


# ------------------------------------------------------- colour tokenising

NAMED = {"white": (255, 255, 255), "black": (0, 0, 0), "#fff": (255, 255, 255), "#000": (0, 0, 0)}


def _rgb(tok: str):
    t = tok.strip().lower()
    if t in ("white", "black"):
        return NAMED[t], 1.0
    if t.startswith("#"):
        h = t[1:]
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        if len(h) not in (6, 8):
            return None, None
        try:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        except ValueError:
            return None, None
        a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return (r, g, b), a
    m = re.match(r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)\s*)?\)", t)
    if m:
        r, g, b = (int(float(m.group(i))) for i in (1, 2, 3))
        a = float(m.group(4)) if m.group(4) else 1.0
        return (r, g, b), a
    return None, None


def token_for(colour: str) -> str | None:
    """Map a hard-coded colour to the nearest design token, or None to keep it."""
    rgb, a = _rgb(colour)
    if rgb is None:
        return None
    r, g, b = (c / 255 for c in rgb)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    hue = h * 360
    if a < 0.5:
        return "var(--line)" if l > 0.35 else "var(--soft)"
    if s < 0.18 or (l > 0.93):
        if l > 0.93:
            return "var(--panel)"
        if l > 0.82:
            return "var(--soft)"
        if l > 0.62:
            return "var(--line)"
        if l > 0.3:
            return "var(--muted)"
        return "var(--ink)"
    # saturated
    if l > 0.85:
        if 80 <= hue <= 170:
            return "var(--accent-soft)"
        if hue < 70 or hue > 330:
            return "var(--warn-soft)" if 20 < hue < 70 else "var(--fail-soft)"
        return "var(--accent-soft)"
    if 80 <= hue <= 170:
        return "var(--ok)"
    if 170 < hue <= 300:
        return "var(--accent-dark)" if l < 0.3 else "var(--accent)"
    if hue <= 18 or hue > 330:
        return "var(--fail)"
    if l < 0.6:
        return "var(--warn)"
    return "var(--warn)"


COLOUR_RE = re.compile(r"(?<![\w-])(#[0-9a-fA-F]{8}\b|#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3,4}\b|rgba?\([^)]*\)|\bwhite\b|\bblack\b)")


def tokenize_decls(decls: str) -> str:
    """Rewrite colours inside a run of CSS declarations. Skips url() payloads."""
    parts = re.split(r"(url\([^)]*\))", decls)
    for i in range(0, len(parts), 2):
        def rep(m):
            tok = token_for(m.group(1))
            return tok or m.group(1)
        parts[i] = COLOUR_RE.sub(rep, parts[i])
    return "".join(parts)


def tokenize_css(css: str) -> str:
    """Apply tokenize_decls to every declaration block, leaving selectors alone."""
    out, i, n = [], 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0:
            out.append(css[i:])
            break
        out.append(css[i : j + 1])
        depth, k = 1, j + 1
        while k < n and depth:
            if css[k] == "{":
                depth += 1
            elif css[k] == "}":
                depth -= 1
            k += 1
        body = css[j + 1 : k - 1]
        if "{" in body:
            out.append(tokenize_css(body))
        else:
            out.append(tokenize_decls(body))
        out.append("}")
        i = k
    return "".join(out)


def tokenize_style_attrs(html: str) -> str:
    return re.sub(r'style="([^"]*)"', lambda m: 'style="' + tokenize_decls(m.group(1)) + '"', html)


# ---------------------------------------------------------------- cleaners

EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF☀-⛿✅❌❎⭐⭕‼⁉ℹ⌚⌛"
    "⏩-⏺▶◀⤴⤵⬅-⬇〰〽㊗㊙➕-➗"
    "⬛⬜❗❣❤✨✳✴❄❇➡➰➿"
    "\U0001F1E6-\U0001F1FF]️?(?:‍[\U0001F000-\U0001FAFF]️?)*|️"
)

HYPE = [
    (re.compile(r"\bSupercharge[sd]?\b"), "Speed up"),
    (re.compile(r"\bsupercharge[sd]?\b"), "speed up"),
    (re.compile(r"\bSeamlessly\b"), "Easily"), (re.compile(r"\bseamlessly\b"), "easily"),
    (re.compile(r"\bSeamless\b"), "Simple"), (re.compile(r"\bseamless\b"), "simple"),
    (re.compile(r"\bElevate[sd]?\b"), "Improve"), (re.compile(r"\belevate[sd]?\b"), "improve"),
    (re.compile(r"\bUnlock(s|ed)?\b"), "Get"), (re.compile(r"\bunlock(s|ed)?\b"), "get"),
    (re.compile(r"\bGame-changing\b|\bgame-changing\b"), "useful"),
    (re.compile(r"\bCutting-edge\b|\bcutting-edge\b"), "current"),
]

SOCIAL_PROOF = re.compile(
    r"(Trusted by|Join \d[\d,.]*\+?|\d[\d,.]*\+ (websites|sites|users|developers|agencies|scans|companies)"
    r"|websites scanned so far|scanned so far|people on the (wait|launch) ?list|Waiting for payments)",
    re.I,
)

INNERMOST_TAGS = ("span", "p", "li", "small", "strong", "em", "div", "h1", "h2", "h3", "h4", "b")


def remove_element_around(html: str, pos: int) -> str | None:
    """Remove the innermost element (of INNERMOST_TAGS) containing text position pos."""
    start = html.rfind("<", 0, pos)
    tries = 0
    while start >= 0 and tries < 12:
        tries += 1
        m = re.match(r"<(%s)\b[^>]*>" % "|".join(INNERMOST_TAGS), html[start:], re.I)
        if m:
            tag = m.group(1).lower()
            depth = 0
            for mm in re.finditer(r"<(/?)%s\b[^>]*>" % tag, html[start:], re.I):
                if mm.group(1) == "":
                    depth += 1
                else:
                    depth -= 1
                if depth == 0:
                    end = start + mm.end()
                    if end > pos:
                        return html[:start] + html[end:]
                    break
        start = html.rfind("<", 0, start)
    return None


def strip_social_proof(html: str) -> str:
    for _ in range(40):
        m = SOCIAL_PROOF.search(html)
        if not m:
            break
        new = remove_element_around(html, m.start())
        if new is None:
            s = html.rfind(".", 0, m.start()) + 1
            e = html.find(".", m.end())
            e = len(html) if e < 0 else e + 1
            new = html[:s] + html[e:]
        html = new
    return html


def strip_waitlist_forms(html: str, lang: str) -> str:
    def repl(m):
        form = m.group(0)
        if "data-keep" in form[: form.find(">")]:
            return form
        if 'type="email"' in form or "type='email'" in form:
            return f'<p class="status">{I18N[lang]["pro_status"]}</p>'
        return form
    return re.sub(r"<form\b[^>]*>.*?</form>", repl, html, flags=re.S | re.I)


DEAD_BUY = re.compile(
    r"<(a|button)\b([^>]*)>((?:(?!</\1>).)*?)</\1>", re.S | re.I)
BUY_TEXT = re.compile(
    r"(buy|get pro|upgrade|checkout|reserve|pre-?order|purchase|notify me|waiting for payments"
    r"|start (daily|pro|monitoring)|subscribe|get the (book|bundle|guide)\s*[—–-]\s*\$|order now|add to cart"
    r"|start (free )?trial|get started with pro|choose pro|go pro)", re.I)


def neutralise_buy_buttons(html: str, lang: str) -> str:
    def repl(m):
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
        if "data-keep" in attrs:
            return m.group(0)
        text = re.sub(r"<[^>]+>", "", inner)
        href = re.search(r'href="([^"]*)"', attrs)
        href = href.group(1) if href else ""
        external_checkout = re.search(r"lemonsqueezy|gumroad|stripe|paddle|checkout", href, re.I)
        if "data-checkout" in attrs or external_checkout or (BUY_TEXT.search(text) and (
            href == "" or href.startswith("#") or href.startswith("javascript") or
            href.startswith("/pro") or href.startswith("/pricing") or "waitlist" in href or
            re.search(r"\$\d", text))):
            return f'<span class="status">{I18N[lang]["pro_status"]}</span>'
        return m.group(0)
    return DEAD_BUY.sub(repl, html)


def fix_generator_links(html: str, lang: str) -> str:
    pat = re.compile(r'(<a\b[^>]*href=")(/(?:%s)/[^"]*)("[^>]*>)(.*?)(</a>)' % "|".join(GENERATORS), re.S | re.I)

    def repl(m):
        text = m.group(4)
        if re.search(r"generator|generate|tools", text, re.I):
            text = I18N[lang]["checklist_link"]
        return m.group(1) + "/checklist/" + m.group(3) + text + m.group(5)
    return pat.sub(repl, html)


def product_ctas(html: str, url: str) -> str:
    if url.startswith(("/deskuptime/", "/de/deskuptime/", "/fr/deskuptime/", "/es/deskuptime/")):
        html = re.sub(r'href="(/deskuptime/#(pro|try|download|pricing)|/deskuptime/downloads/[^"]*|#download|#try|#pro'
                      r'|https://github\.com/mahope/deskuptime/releases[^"]*)"',
                      'href="https://deskuptime.com/"', html)
    if url.startswith("/transmute/"):
        html = re.sub(r'href="(/transmute/#(pricing|download|pro)|#download|#pricing'
                      r'|https://github\.com/mahope/transmute/releases[^"]*)"',
                      'href="https://transmute.run/"', html)
    return html


def outside_code(html: str, fn):
    """Apply fn to the parts of html that are not inside <script>/<style>."""
    parts = re.split(r"(<(?:script|style)\b[^>]*>.*?</(?:script|style)>)", html, flags=re.S | re.I)
    for i in range(0, len(parts), 2):
        parts[i] = fn(parts[i])
    return "".join(parts)


def wrap_tables(html: str) -> str:
    """Give every <table> a horizontally scrolling wrapper (idempotent)."""
    def repl(m):
        start = m.start()
        before = html[max(0, start - 40) : start]
        if re.search(r'<div class="tbl">\s*$', before):
            return m.group(0)
        return '<div class="tbl">' + m.group(0) + "</div>"
    return re.sub(r"<table\b.*?</table>", repl, html, flags=re.S | re.I)


def add_missing_alt(html: str) -> str:
    return re.sub(r"<img\b(?![^>]*\balt=)([^>]*?)(/?)>", r'<img alt=""\1\2>', html, flags=re.I)


# ----------------------------------------------------------------- SEO head

BRAND_SUFFIX = re.compile(r"\s*[|—–-]\s*(EUComply|DevNotify|ComplianceDocs|Deskuptime|DeskUptime|Transmute)\s*$", re.I)


def text_of(fragment: str) -> str:
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", fragment, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = htmlmod.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def short_title(t: str, limit: int = 60) -> str:
    t = re.sub(r"\s+", " ", htmlmod.unescape(t)).strip()
    t = BRAND_SUFFIX.sub("", t)
    if len(t) <= limit:
        return t
    for sep in (" — ", " – ", " | ", ": ", " (", " - ", "? "):
        idx = t.rfind(sep, 0, limit + 1)
        if idx >= 25:
            cand = t[: idx + (1 if sep == "? " else 0)].strip()
            if len(cand) <= limit:
                return cand
    cut = t[: limit + 1]
    cut = cut[: cut.rfind(" ")] if " " in cut else cut[:limit]
    return cut.rstrip(" ,;:-–—")


def short_desc(d: str, limit: int = 155) -> str:
    d = re.sub(r"\s+", " ", htmlmod.unescape(d)).strip()
    if len(d) <= limit:
        return d
    idx = d.rfind(". ", 0, limit)
    if idx >= 70:
        return d[: idx + 1]
    cut = d[:limit]
    cut = cut[: cut.rfind(" ")]
    return cut.rstrip(" ,;:-–—") + "."


def attr_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def find_meta(head: str, attr: str, name: str) -> str | None:
    m = re.search(r'<meta\s+[^>]*%s="%s"[^>]*content="([^"]*)"' % (attr, re.escape(name)), head, re.I)
    if not m:
        m = re.search(r'<meta\s+[^>]*content="([^"]*)"[^>]*%s="%s"' % (attr, re.escape(name)), head, re.I)
    return htmlmod.unescape(m.group(1)) if m else None


def remove_meta(head: str, attr: str, name: str) -> str:
    return re.sub(r'\s*<meta\s+[^>]*%s="%s"[^>]*>' % (attr, re.escape(name)), "", head, flags=re.I)


def slug_for_og(url: str) -> str:
    s = url.strip("/")
    return (s.replace("/", "-") if s else "home")


def og_image_for(url: str, lang: str, current: str | None) -> str:
    """Pick the best existing OG image for this page."""
    if current and "eucomply-og.png" not in current and not current.startswith("/images/og/"):
        path = current.replace(ORIGIN, "")
        if path.startswith("/") and (SITE / path.lstrip("/")).exists():
            return ORIGIN + path
    cands = [f"/images/og/{slug_for_og(url)}.png",
             f"/images/og/{slug_for_og(strip_lang(url))}.png" if lang != "en" and slug_for_og(strip_lang(url)) != "home" else None,
             f"/images/og/{lang}.png", "/images/og/en.png", "/images/eucomply-og.png"]
    for c in cands:
        if c and (SITE / c.lstrip("/")).exists():
            return ORIGIN + c
    return ORIGIN + "/images/eucomply-og.png"


def site_name_for(url: str) -> str:
    base = strip_lang(url)
    if base.startswith("/devnotify/"):
        return "DevNotify"
    if base.startswith("/deskuptime/"):
        return "Deskuptime"
    if base.startswith("/transmute/"):
        return "Transmute"
    if base.startswith("/store/"):
        return "ComplianceDocs by EUComply"
    return "EUComply"


MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def find_date(body: str) -> str | None:
    m = re.search(r'<time[^>]*datetime="(\d{4}-\d{2}-\d{2})', body)
    if m:
        return m.group(1)
    meta = re.search(r'class="meta"[^>]*>(.*?)</', body, re.S)
    scope = meta.group(1) if meta else body[:6000]
    m = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", scope)
    if m:
        return m.group(1)
    m = re.search(r"\b([A-Z][a-z]{2,8})\.? (\d{1,2}), (20\d{2})\b", scope)
    if m and m.group(1)[:3].lower() in MONTHS:
        return f"{m.group(3)}-{MONTHS[m.group(1)[:3].lower()]:02d}-{int(m.group(2)):02d}"
    m = re.search(r"\b(\d{1,2})\.? ([A-Z][a-zé]{2,9}) (20\d{2})\b", scope)
    if m and m.group(2)[:3].lower() in MONTHS:
        return f"{m.group(3)}-{MONTHS[m.group(2)[:3].lower()]:02d}-{int(m.group(1)):02d}"
    return None


def is_article(url: str, body: str) -> bool:
    base = strip_lang(url)
    if base in ("/blog/", "/guides/", "/devnotify/guides/", "/devnotify/", "/deskuptime/", "/transmute/", "/vs/"):
        return False
    if base.startswith(("/blog/", "/guides/", "/devnotify/guides/")):
        return True
    return bool(re.search(r'class="meta"[^>]*>[^<]*(min read|\d{4}-\d{2}-\d{2}|20\d{2})', body))


def existing_ld_types(html: str) -> set:
    types = set()
    for m in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S | re.I):
        types.update(re.findall(r'"@type"\s*:\s*"([^"]+)"', m.group(1)))
    return types


def faq_from_details(body: str) -> list:
    items = []
    for m in re.finditer(r"<details\b[^>]*>(.*?)</details>", body, re.S | re.I):
        inner = m.group(1)
        sm = re.search(r"<summary\b[^>]*>(.*?)</summary>", inner, re.S | re.I)
        if not sm:
            continue
        q = text_of(sm.group(1))
        a = text_of(inner[sm.end():])
        if len(q) > 8 and len(a) > 20:
            items.append({"@type": "Question", "name": q,
                          "acceptedAnswer": {"@type": "Answer", "text": a[:1200]}})
    return items


def ld_script(obj: dict) -> str:
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>"


def seo_head(html: str, url: str, lang: str, rel: str) -> str:
    """Normalise <head>: title, description, canonical, OG, Twitter, icons, JSON-LD."""
    hi = html.find("</head>")
    if hi < 0:
        return html
    head, rest = html[:hi], html[hi:]
    body = rest
    canonical = ORIGIN + url
    noindex = bool(re.search(r'name="robots"[^>]*noindex', head))

    tm = re.search(r"<title>(.*?)</title>", head, re.S)
    full_title = re.sub(r"\s+", " ", htmlmod.unescape(tm.group(1))).strip() if tm else ""
    title = short_title(full_title) if full_title else ""
    if not title:
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
        title = short_title(text_of(h1.group(1))) if h1 else "EUComply"
        full_title = title
    if tm:
        head = head[: tm.start()] + "<title>" + attr_escape(title) + "</title>" + head[tm.end():]
    else:
        head = re.sub(r"(<meta charset[^>]*>)", r"\1\n<title>" + attr_escape(title) + "</title>", head, count=1)

    desc = find_meta(head, "name", "description") or find_meta(head, "property", "og:description")
    if not desc:
        main = body[body.find("<main"):] if "<main" in body else body
        for pm in re.finditer(r"<p\b[^>]*>(.*?)</p>", main, re.S):
            t = text_of(pm.group(1))
            if len(t) >= 60:
                desc = t
                break
        desc = desc or title
    desc = short_desc(desc)
    head = remove_meta(head, "name", "description")
    head = re.sub(r"(<title>.*?</title>)", lambda m: m.group(1) + '\n<meta name="description" content="' + attr_escape(desc) + '">', head, count=1, flags=re.S)

    # canonical
    head = re.sub(r'\s*<link\s+rel="canonical"[^>]*>', "", head, flags=re.I)
    head = head.replace("</title>", "</title>", 1)
    head = re.sub(r'(<meta name="description"[^>]*>)', lambda m: m.group(1) + f'\n<link rel="canonical" href="{canonical}">', head, count=1)

    # icons (the old inline SVG data-URI icon contains ">" inside the attribute, so it goes first)
    head = re.sub(r'\s*<link\s+rel="icon"\s+href="data:image/svg\+xml,[^"]*"[^>]*>', "", head, flags=re.I)
    head = re.sub(r"\s*<(?:rect|text|path|circle|g)\b[^\n]*?</svg>\">", "", head)
    head = re.sub(r'\s*<link\s+rel="(icon|apple-touch-icon|manifest|shortcut icon)"[^>]*>', "", head, flags=re.I)
    head = remove_meta(head, "name", "theme-color")
    head = re.sub(r'(<link rel="canonical"[^>]*>)', lambda m: m.group(1) + "\n" + ICON_LINKS, head, count=1)

    # Open Graph / Twitter
    og_title = find_meta(head, "property", "og:title") or full_title
    og_desc = find_meta(head, "property", "og:description") or desc
    og_type = find_meta(head, "property", "og:type") or ("article" if is_article(url, body) else "website")
    og_img = og_image_for(url, lang, find_meta(head, "property", "og:image"))
    for p in ("og:title", "og:description", "og:type", "og:url", "og:image", "og:site_name", "og:locale",
              "og:image:width", "og:image:height", "og:image:alt"):
        head = remove_meta(head, "property", p)
    for p in ("twitter:card", "twitter:title", "twitter:description", "twitter:image", "twitter:site", "twitter:creator"):
        head = remove_meta(head, "name", p)
    og = [
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:site_name" content="{attr_escape(site_name_for(url))}">',
        f'<meta property="og:locale" content="{OG_LOCALE[lang]}">',
        f'<meta property="og:url" content="{canonical}">',
        f'<meta property="og:title" content="{attr_escape(og_title)}">',
        f'<meta property="og:description" content="{attr_escape(short_desc(og_desc, 200))}">',
        f'<meta property="og:image" content="{og_img}">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{attr_escape(og_title)}">',
        f'<meta name="twitter:description" content="{attr_escape(short_desc(og_desc, 200))}">',
        f'<meta name="twitter:image" content="{og_img}">',
    ]
    head = re.sub(r'(<meta name="theme-color"[^>]*>)', lambda m: m.group(1) + "\n" + "\n".join(og), head, count=1)

    # JSON-LD: strip ours from a previous run, then add what is missing
    head = re.sub(r'\s*<script type="application/ld\+json" data-shell>.*?</script>', "", head, flags=re.S)
    types = existing_ld_types(head + body)
    blocks = []
    base = strip_lang(url)
    web_page = {"@type": "WebPage", "@id": canonical, "url": canonical, "name": title, "description": desc,
                "inLanguage": lang, "isPartOf": {"@type": "WebSite", "@id": ORIGIN + "/#website"},
                "author": AUTHOR}
    if base == "/":
        if "WebSite" not in types:
            blocks.append({"@context": "https://schema.org", "@type": "WebSite", "@id": ORIGIN + "/#website",
                           "url": ORIGIN + "/", "name": "EUComply", "inLanguage": lang,
                           "description": desc, "author": AUTHOR, "publisher": {"@id": ORIGIN + "/#org"}})
        if "Organization" not in types:
            blocks.append({"@context": "https://schema.org", "@id": ORIGIN + "/#org", **ORG})
    elif base == "/scan/":
        if "SoftwareApplication" not in types:
            blocks.append({"@context": "https://schema.org", "@type": "SoftwareApplication", "name": "EUComply scanner",
                           "url": canonical, "applicationCategory": "SecurityApplication", "operatingSystem": "Web",
                           "description": desc, "inLanguage": lang, "isAccessibleForFree": True,
                           "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"},
                           "author": AUTHOR, "publisher": ORG})
    elif is_article(url, body):
        if "Article" not in types and "BlogPosting" not in types and "TechArticle" not in types:
            first, last = GIT_DATES.get(rel, (TODAY, TODAY))
            published = find_date(body) or first
            modified = max(last, published)
            h1 = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
            blocks.append({"@context": "https://schema.org", "@type": "Article",
                           "headline": (text_of(h1.group(1)) if h1 else full_title)[:110],
                           "description": desc, "url": canonical, "mainEntityOfPage": canonical,
                           "inLanguage": lang, "image": og_img,
                           "datePublished": published, "dateModified": modified,
                           "author": AUTHOR, "publisher": ORG})
    if "WebPage" not in types and base not in ("/",) and not blocks:
        blocks.append({"@context": "https://schema.org", **web_page})
    if "FAQPage" not in types:
        faq = faq_from_details(body)
        if len(faq) >= 2:
            blocks.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": faq})
    if blocks:
        scripts = "\n".join(ld_script(b).replace('<script type="application/ld+json">', '<script type="application/ld+json" data-shell>', 1) for b in blocks)
        head = head.rstrip() + "\n" + scripts + "\n"
    if noindex:
        head = re.sub(r'\s*<meta\s+property="og:[^>]*>|\s*<meta\s+name="twitter:[^>]*>', "", head)
    return head + rest


# ----------------------------------------------------------------- per page

def process(path: Path) -> bool:
    rel = path.relative_to(SITE).as_posix()
    if rel in SKIP_FILES or rel.startswith("_partials/"):
        return False
    url = rel_url(path)
    lang = lang_of(url)
    html = path.read_text(encoding="utf-8")
    orig = html
    is_devnotify = "/devnotify/" in url
    native = "pg-legacy" not in html and "data-dark-ok" in html[:400]  # pages written for the new shell

    # --- <html>: language and dark-mode opt-in
    def html_tag(m):
        attrs = m.group(1)
        attrs = re.sub(r'\s*lang="[^"]*"', "", attrs)
        attrs = re.sub(r"\s*data-dark-ok\b", "", attrs)
        return f'<html lang="{lang}" data-dark-ok{attrs}>'
    html = re.sub(r"<html\b([^>]*)>", html_tag, html, count=1)

    # --- head: stylesheet, scripts, beacon, hreflang
    html = re.sub(r"\s*<link[^>]+/assets/site\.css[^>]*>", "", html)
    html = re.sub(r"\s*<script[^>]*/assets/site\.js[^>]*></script>", "", html)
    html = html.replace("\n" + JS_BOOT, "").replace(JS_BOOT, "")
    html = re.sub(r"\s*<script[^>]*cloudflareinsights[^>]*></script>", "", html, flags=re.I)
    html = re.sub(r"\s*<script[^>]*/assets/checkout\.js[^>]*></script>", "", html, flags=re.I)
    html = re.sub(r'\s*<link[^>]+rel="alternate"[^>]+hreflang=[^>]*>', "", html)
    html = seo_head(html, url, lang, rel)
    alts = alternates(url)
    if len(alts) >= 2 and "noindex" not in html[:3000]:
        tags = "".join(f'\n<link rel="alternate" hreflang="{l}" href="{ORIGIN}{u}">' for l, u in alts.items())
        tags += f'\n<link rel="alternate" hreflang="x-default" href="{ORIGIN}{alts.get("en", url)}">'
        html = re.sub(r'(<link rel="canonical"[^>]*>)', lambda m: m.group(1) + tags, html, count=1)
    html = html.replace("</head>", f'<link rel="stylesheet" href="/assets/site.css?v={CSS_V}">\n'
                        + JS_BOOT + f'\n<script src="/assets/site.js?v={JS_V}" defer></script>\n</head>', 1)

    # --- inline CSS: drop legacy shell rules and map colours (not for pages authored for the shell)
    if not native:
        def css_repl(m):
            return m.group(1) + tokenize_css(filter_css(m.group(2))) + m.group(3)
        html = re.sub(r"(<style\b[^>]*>)(.*?)(</style>)", css_repl, html, flags=re.S | re.I)
        html = outside_code(html, tokenize_style_attrs)

    # --- body: remove old header/footer, insert shell
    header, footer = render_shell(url, lang)
    html = re.sub(r"<header\b[^>]*>.*?</header>\s*", "", html, count=1, flags=re.S | re.I)
    html = re.sub(r"(<body\b[^>]*>)\s*<nav\b[^>]*>(?:(?!</nav>).)*?(?:← ?EUComply|&larr;|EUComply)(?:(?!</nav>).)*?</nav>\s*",
                  r"\1\n", html, count=1, flags=re.S | re.I)
    footers = list(re.finditer(r"<footer\b[^>]*>.*?</footer>\s*", html, flags=re.S | re.I))
    if footers:
        f = footers[-1]
        html = html[: f.start()] + html[f.end():]
    html = re.sub(r'<div class="pg-legacy">\n?', "", html, count=1)
    html = re.sub(r"\s*</div><!--/pg-legacy-->", "", html, count=1)
    html = re.sub(r"(<body\b[^>]*>)\s*", r"\1\n", html, count=1)
    html = re.sub(r"\s*</body>", "\n</body>", html, count=1)
    if native:
        html = re.sub(r"(<body\b[^>]*>)", lambda m: m.group(1) + "\n" + header + "\n", html, count=1)
        html = html.replace("</body>", footer + "\n</body>", 1)
    else:
        html = re.sub(r"(<body\b[^>]*>)", lambda m: m.group(1) + "\n" + header + '\n<div class="pg-legacy">\n', html, count=1)
        html = html.replace("</body>", "</div><!--/pg-legacy-->\n" + footer + "\n</body>", 1)

    # --- cross-cutting clean-up
    html = html.replace("auditedwp.pages.dev", "eucomplypro.com")
    html = outside_code(html, wrap_tables)
    html = outside_code(html, add_missing_alt)
    if not is_devnotify and not native:
        def clean(txt):
            txt = EMOJI.sub("", txt)
            for pat, rep in HYPE:
                txt = pat.sub(rep, txt)
            txt = txt.replace("AuditedWP", "EUComply")
            return txt
        html = outside_code(html, clean)
        html = outside_code(html, strip_social_proof)
        html = strip_waitlist_forms(html, lang)
        html = neutralise_buy_buttons(html, lang)
        html = fix_generator_links(html, lang)
        html = product_ctas(html, url)
        html = re.sub(r"(<(h[1-6]|p|li|span|strong|b|td|th|a)\b[^>]*>)\s+(?=\S)", r"\1", html)
    elif native:
        html = fix_generator_links(html, lang)

    if html != orig and not DRY:
        path.write_text(html, encoding="utf-8")
    return html != orig


# ------------------------------------------------------------------ sitemap

def lastmod_for(p: Path) -> str:
    rel = p.relative_to(SITE).as_posix()
    html = p.read_text(encoding="utf-8")
    m = re.search(r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})', html)
    if m:
        return m.group(1)
    first, last = GIT_DATES.get(rel, (TODAY, TODAY))
    return last


def build_sitemap():
    urls = []
    for p in sorted(SITE.rglob("*.html")):
        rel = p.relative_to(SITE).as_posix()
        if rel in SKIP_FILES or rel.startswith("_partials/") or rel == "404.html":
            continue
        if rel.split("/")[0] in GENERATORS:
            continue
        head = p.read_text(encoding="utf-8")[:6000]
        if re.search(r'name="robots"[^>]*noindex', head):
            continue
        if not rel.endswith("index.html"):
            continue
        urls.append((rel_url(p), lastmod_for(p)))
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for u, mod in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{ORIGIN}{u}</loc>")
        lines.append(f"    <lastmod>{mod}</lastmod>")
        alts = alternates(u)
        if len(alts) >= 2:
            for l, a in alts.items():
                lines.append(f'    <xhtml:link rel="alternate" hreflang="{l}" href="{ORIGIN}{a}"/>')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{ORIGIN}{alts.get("en", u)}"/>')
        lines.append("  </url>")
    lines.append("</urlset>\n")
    (SITE / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")
    return len(urls)


def main():
    changed = 0
    total = 0
    for p in sorted(SITE.rglob("*.html")):
        if "_partials" in p.parts:
            continue
        total += 1
        if process(p):
            changed += 1
    n = build_sitemap() if not DRY else 0
    print(f"pages: {total}, changed: {changed}, sitemap urls: {n}")


if __name__ == "__main__":
    main()
