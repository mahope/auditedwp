#!/usr/bin/env python3
"""Inject the shared EUComply shell (header, footer, site.css) into every HTML
page under site/, strip legacy shell CSS/markup, clean up hype, and rebuild
sitemap.xml.  Idempotent: safe to run repeatedly.

    python tools/apply_shell.py            # apply to all pages
    python tools/apply_shell.py --dry-run  # report only
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
PARTIALS = SITE / "_partials"
ORIGIN = "https://eucomplypro.com"
LANGS = ["en", "da", "de", "fr"]
DRY = "--dry-run" in sys.argv

I18N = {
    "en": dict(nav_label="Main", nav_scan="Scan", nav_guide="Guide", nav_checklists="Checklists",
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
    "da": dict(nav_label="Hovedmenu", nav_scan="Scan", nav_guide="Guide", nav_checklists="Tjeklister",
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
    "de": dict(nav_label="Hauptmenü", nav_scan="Scan", nav_guide="Leitfaden", nav_checklists="Checklisten",
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
    "fr": dict(nav_label="Menu principal", nav_scan="Scanner", nav_guide="Guide", nav_checklists="Check-lists",
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

# Pages whose localised versions live under /<lang>/ when they exist.
CORE = {"", "scan/", "pricing/", "book/"}

GENERATORS = ["impressum-generator", "privacy-policy-generator", "terms-of-service-generator",
              "refund-policy-generator", "cookie-policy-generator", "tools"]

SKIP_FILES = {"shared/live-check-widget.html"}

HEADER_TPL = (PARTIALS / "header.html").read_text(encoding="utf-8")
FOOTER_TPL = (PARTIALS / "footer.html").read_text(encoding="utf-8")

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


# ---------------------------------------------------------------- CSS filter

SHELL_SEL = re.compile(
    r"^(html|\*|header|footer|nav|\.logo|\.brand|\.nav|\.site-header|\.site-footer|\.topbar|\.navbar|\.cta)(\b|$)",
    re.I,
)


def split_rules(css: str):
    """Yield (selector, body, is_at_block) for top-level rules; handles one level of nesting."""
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
    # walk back to the nearest opening tag whose matching close comes after pos
    start = html.rfind("<", 0, pos)
    tries = 0
    while start >= 0 and tries < 12:
        tries += 1
        m = re.match(r"<(%s)\b[^>]*>" % "|".join(INNERMOST_TAGS), html[start:], re.I)
        if m:
            tag = m.group(1).lower()
            close = re.compile(r"</%s\s*>" % tag, re.I)
            # find matching close accounting for nesting of the same tag
            depth, i = 0, start
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
            # fall back: delete the sentence
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
    native = 'data-dark-ok' in html[:400]  # pages written for the new shell

    # --- head: stylesheet, beacon, hreflang
    html = re.sub(r"\s*<link[^>]+/assets/site\.css[^>]*>", "", html)
    html = re.sub(r"\s*<script[^>]*cloudflareinsights[^>]*></script>", "", html, flags=re.I)
    html = re.sub(r"\s*<script[^>]*/assets/checkout\.js[^>]*></script>", "", html, flags=re.I)
    html = re.sub(r'\s*<link[^>]+rel="alternate"[^>]+hreflang=[^>]*>', "", html)
    alts = alternates(url)
    if len(alts) >= 2 and "noindex" not in html[:3000]:
        tags = "".join(f'\n<link rel="alternate" hreflang="{l}" href="{ORIGIN}{u}">' for l, u in alts.items())
        tags += f'\n<link rel="alternate" hreflang="x-default" href="{ORIGIN}{alts.get("en", url)}">'
        html = re.sub(r'(<link rel="canonical"[^>]*>)', lambda m: m.group(1) + tags, html, count=1) \
            if 'rel="canonical"' in html else html.replace("</head>", tags + "\n</head>", 1)
    html = html.replace("</head>", '<link rel="stylesheet" href="/assets/site.css">\n</head>', 1)

    # --- inline CSS: drop legacy shell rules (not for pages authored for the shell)
    if not native:
        def css_repl(m):
            return m.group(1) + filter_css(m.group(2)) + m.group(3)
        html = re.sub(r"(<style\b[^>]*>)(.*?)(</style>)", css_repl, html, flags=re.S | re.I)

    # --- body: remove old header/footer, insert shell
    header, footer = render_shell(url, lang)
    html = re.sub(r"<header\b[^>]*>.*?</header>\s*", "", html, count=1, flags=re.S | re.I)
    # article-style breadcrumb nav right after <body>
    html = re.sub(r"(<body\b[^>]*>)\s*<nav\b[^>]*>(?:(?!</nav>).)*?(?:← ?EUComply|&larr;|EUComply)(?:(?!</nav>).)*?</nav>\s*",
                  r"\1\n", html, count=1, flags=re.S | re.I)
    # last footer
    footers = list(re.finditer(r"<footer\b[^>]*>.*?</footer>\s*", html, flags=re.S | re.I))
    if footers:
        f = footers[-1]
        html = html[: f.start()] + html[f.end():]
    html = re.sub(r'<div class="pg-legacy">\n?', "", html, count=1)
    html = html.replace("</div><!--/pg-legacy-->", "", 1)
    if native:
        html = re.sub(r"(<body\b[^>]*>)", lambda m: m.group(1) + "\n" + header + "\n", html, count=1)
        html = html.replace("</body>", footer + "\n</body>", 1)
    else:
        html = re.sub(r"(<body\b[^>]*>)", lambda m: m.group(1) + "\n" + header + '\n<div class="pg-legacy">\n', html, count=1)
        html = html.replace("</body>", "</div><!--/pg-legacy-->\n" + footer + "\n</body>", 1)

    # --- cross-cutting clean-up
    html = html.replace("auditedwp.pages.dev", "eucomplypro.com")
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
        # tidy leftovers such as "<h3> HTTPS" after emoji removal
        html = re.sub(r"(<(h[1-6]|p|li|span|strong|b|td|th|a)\b[^>]*>)\s+(?=\S)", r"\1", html)
    elif native:
        html = fix_generator_links(html, lang)

    if html != orig and not DRY:
        path.write_text(html, encoding="utf-8")
    return html != orig


# ------------------------------------------------------------------ sitemap

def build_sitemap():
    urls = []
    for p in sorted(SITE.rglob("*.html")):
        rel = p.relative_to(SITE).as_posix()
        if rel in SKIP_FILES or rel.startswith("_partials/") or rel == "404.html":
            continue
        if rel.split("/")[0] in GENERATORS:
            continue
        head = p.read_text(encoding="utf-8")[:4000]
        if re.search(r'name="robots"[^>]*noindex', head):
            continue
        if not rel.endswith("index.html"):
            # loose files like devnotify/privacy.html duplicate their /privacy/ folder
            continue
        urls.append(rel_url(p))
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for u in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{ORIGIN}{u}</loc>")
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
