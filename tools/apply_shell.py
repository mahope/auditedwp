#!/usr/bin/env python3
"""Inject the shared EUComply shell into every HTML page under site/ and keep the
site consistent from page to page.  Idempotent: safe to run repeatedly.

    python tools/apply_shell.py            # apply to all pages
    python tools/apply_shell.py --dry-run  # report only

What one run does to a page
---------------------------
1. <html lang> is set from the path (/da/, /de/, /fr/, /es/ → else en) and the theme
   boot script (data-theme from localStorage) is placed in <head>.
2. <head> is normalised: title, description, canonical, hreflang, icons, Open Graph,
   Twitter, JSON-LD (WebSite/Organization/Article/FAQ/BreadcrumbList as appropriate),
   site.css and site.js with content-hash query strings.
3. Old shell markup is removed and the shared one inserted: skip link, family bar,
   header (brand, nav, search, language switcher with reserved slots, theme, menu),
   footer (four columns, localised), BugBottle script tag.
4. The page's own layout is neutralised so the shell's single `.container` is the only
   width on the page.  The rules (see filter_css / clean_style_attr):
     - selectors that are shell chrome (html, *, header, footer, nav, .logo, .brand, .nav,
       .site-header, .site-footer, .topbar, .navbar, .cta) are dropped;
     - `body` loses max-width/width/margin/padding (the old "body padding" hack);
     - wrapper selectors (.wrap, .container, .content, .page, .inner, main, article,
       .article, .post-body, .blog-header, .pg-legacy, section) lose max-width, width,
       margin and horizontal padding;
     - any rule that centres with `margin: 0 auto` loses that margin (content is left
       aligned inside the container); `text-align: center` is removed from hero/lede/h1
       rules so intros line up with the rest of the page;
     - custom properties on :root/html that site.css already defines are dropped, so a
       page cannot recolour the shell; remaining hard-coded colours are mapped to tokens;
     - `position: sticky; top: 0` becomes `top: var(--header-h)` so sticky bars sit
       under the sticky header;
     - inline style attributes lose max-width, width (except on img/svg/video/td/th/col/
       iframe/canvas), and `margin: … auto` centring.
5. The content is wrapped in `<main class="container layout-…" id="main">`:
     - layout-wide  : scanner, checkers, calculators, comparison tables, dashboards
                      (max-width --w-wide from 1480px up, identical to --w-page below);
     - layout-prose : articles, guides, checklists, legal text — a `.prose` column
                      (--w-prose) plus a sticky table of contents from h2/h3 on ≥1100px
                      and a <details> TOC above the text below that;
     - default      : everything else, full --w-page.
   Generated blocks are fenced with <!--shell:name-->…<!--/shell:name--> comments so a
   later run replaces rather than duplicates them.
6. Breadcrumbs (visible + BreadcrumbList JSON-LD) on every page but the home pages;
   article meta line (updated date from git, reading time, copy-link button) and
   newer/older links on articles; ids on every h2/h3; lazy images with dimensions;
   scrolling table wrappers with a sticky first column on comparison pages;
   aria-live on tool result containers.
7. Hype, emoji, social proof and dead checkout buttons are cleaned up (legacy pages).
8. /search/ pages (one per language), search-index.json and sitemap.xml are rebuilt.
"""
import colorsys
import datetime as dt
import html as htmlmod
import json
import re
import struct
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
YEAR = TODAY[:4]
AUTHOR = {"@type": "Person", "name": "Mads Holst Jensen", "url": "https://mahoje.dk"}
ORG = {"@type": "Organization", "name": "EUComply", "url": ORIGIN + "/",
       "logo": {"@type": "ImageObject", "url": ORIGIN + "/icon-512.png"},
       "founder": AUTHOR}
BUGBOTTLE_SRC = "https://cdn.jsdelivr.net/npm/bugbottle@0.5.0/dist/bugbottle.js"
BUGBOTTLE_ENDPOINT = "https://mahope.tools/api/bugreport"
ACCENT = "#0b6e4f"

I18N = {
    "en": dict(nav_label="Main", menu_label="Menu", nav_scan="Scan", nav_guide="Guide", nav_checklists="Checklists",
               nav_pricing="Pricing", nav_blog="Blog", built_by="Built by",
               maker_desc="developer and technical partner for small businesses, Odense, Denmark.",
               source_on_github="Scanner source on GitHub", releases="Releases and changelog",
               product_line="A free scanner for the EU compliance basics of any website, plus the guides to fix what it finds.",
               privacy_note="No cookies, no cross-site tracking, no external fonts.",
               legal_note="Everything here is technical guidance, not legal advice.",
               col_site="Site", col_family="Mahope tools", fam_all="All tools",
               privacy="Privacy", terms="Terms", security="Security", sitemap="Sitemap",
               report_bug="Report a bug", powered_by="Feedback powered by BugBottle",
               scanner_mit="Scanner and CLI are MIT licensed.",
               skip="Skip to content", search="Search", search_label="Search this site", theme_label="Switch theme",
               home="Home", contents="Contents", updated="Updated", published="Published", min_read="min read",
               newer="Newer", older="Older", share="Copy link",
               search_title="Search", search_desc="Search every page on EUComply: guides, checklists, tools and comparisons.",
               search_lede="Every page on this site, in all four languages. Type a word or two.",
               search_placeholder="e.g. cookie banner, NIS2, HSTS", search_button="Search",
               search_noscript="Search needs JavaScript. The sitemap lists every page.",
               nf_search="Or search the site", nf_placeholder="What are you looking for?",
               pro_status="The free scanner is complete and stays free.", support="Support the free scanner",
               checklist_link="compliance checklist",
               gen_title="This generator has been taken down",
               ),
    "da": dict(nav_label="Hovedmenu", menu_label="Menu", nav_scan="Scan", nav_guide="Guide", nav_checklists="Tjeklister",
               nav_pricing="Priser", nav_blog="Blog", built_by="Udviklet af",
               maker_desc="udvikler og teknisk partner for små virksomheder, Odense.",
               source_on_github="Scannerens kildekode på GitHub", releases="Udgivelser og changelog",
               product_line="En gratis scanner af de grundlæggende EU-krav til ethvert website, og guides til at rette det, den finder.",
               privacy_note="Ingen cookies, ingen sporing på tværs af sites, ingen eksterne skrifttyper.",
               legal_note="Alt her er teknisk vejledning, ikke juridisk rådgivning.",
               col_site="Sitet", col_family="Mahope tools", fam_all="Alle værktøjer",
               privacy="Privatliv", terms="Vilkår", security="Sikkerhed", sitemap="Sitemap",
               report_bug="Meld en fejl", powered_by="Feedback drevet af BugBottle",
               scanner_mit="Scanner og CLI er MIT-licenseret.",
               skip="Spring til indhold", search="Søg", search_label="Søg på sitet", theme_label="Skift tema",
               home="Forside", contents="Indhold", updated="Opdateret", published="Udgivet", min_read="min. læsning",
               newer="Nyere", older="Ældre", share="Kopiér link",
               search_title="Søg", search_desc="Søg i alle sider på EUComply: guides, tjeklister, værktøjer og sammenligninger.",
               search_lede="Alle sider på sitet, på alle fire sprog. Skriv et ord eller to.",
               search_placeholder="fx cookie-banner, NIS2, HSTS", search_button="Søg",
               search_noscript="Søgning kræver JavaScript. Sitemappet viser alle sider.",
               nf_search="Eller søg på sitet", nf_placeholder="Hvad leder du efter?",
               pro_status="Den gratis scanner er færdig og forbliver gratis.", support="Støt den gratis scanner",
               checklist_link="compliance-tjekliste",
               gen_title="Denne generator er taget ned",
               ),
    "de": dict(nav_label="Hauptmenü", menu_label="Menü", nav_scan="Scan", nav_guide="Leitfaden", nav_checklists="Checklisten",
               nav_pricing="Preise", nav_blog="Blog", built_by="Entwickelt von",
               maker_desc="Entwickler und technischer Partner für kleine Unternehmen, Odense, Dänemark.",
               source_on_github="Quellcode des Scanners auf GitHub", releases="Releases und Changelog",
               product_line="Ein kostenloser Scanner für die EU-Compliance-Grundlagen jeder Website, plus Leitfäden zum Beheben der Funde.",
               privacy_note="Keine Cookies, kein seitenübergreifendes Tracking, keine externen Schriften.",
               legal_note="Alles hier ist technische Orientierung, keine Rechtsberatung.",
               col_site="Website", col_family="Mahope tools", fam_all="Alle Werkzeuge",
               privacy="Datenschutz", terms="Nutzungsbedingungen", security="Sicherheit", sitemap="Sitemap",
               report_bug="Fehler melden", powered_by="Feedback mit BugBottle",
               scanner_mit="Scanner und CLI stehen unter MIT-Lizenz.",
               skip="Zum Inhalt springen", search="Suche", search_label="Website durchsuchen", theme_label="Thema wechseln",
               home="Start", contents="Inhalt", updated="Aktualisiert", published="Veröffentlicht", min_read="Min. Lesezeit",
               newer="Neuer", older="Älter", share="Link kopieren",
               search_title="Suche", search_desc="Alle Seiten auf EUComply durchsuchen: Leitfäden, Checklisten, Werkzeuge und Vergleiche.",
               search_lede="Jede Seite dieser Website, in allen vier Sprachen. Ein oder zwei Wörter genügen.",
               search_placeholder="z. B. Cookie-Banner, NIS2, HSTS", search_button="Suchen",
               search_noscript="Die Suche benötigt JavaScript. Die Sitemap listet jede Seite.",
               nf_search="Oder die Website durchsuchen", nf_placeholder="Wonach suchen Sie?",
               pro_status="Der kostenlose Scanner ist fertig und bleibt kostenlos.", support="Den kostenlosen Scanner unterstützen",
               checklist_link="Compliance-Checkliste",
               gen_title="Dieser Generator wurde abgeschaltet",
               ),
    "fr": dict(nav_label="Menu principal", menu_label="Menu", nav_scan="Scanner", nav_guide="Guide", nav_checklists="Check-lists",
               nav_pricing="Tarifs", nav_blog="Blog", built_by="Développé par",
               maker_desc="développeur et partenaire technique des petites entreprises, Odense, Danemark.",
               source_on_github="Code source du scanner sur GitHub", releases="Versions et changelog",
               product_line="Un scanner gratuit des bases de conformité européenne de tout site web, et les guides pour corriger ce qu'il trouve.",
               privacy_note="Aucun cookie, aucun pistage intersites, aucune police externe.",
               legal_note="Tout ce qui figure ici est une aide technique, pas un conseil juridique.",
               col_site="Site", col_family="Mahope tools", fam_all="Tous les outils",
               privacy="Confidentialité", terms="Conditions", security="Sécurité", sitemap="Plan du site",
               report_bug="Signaler un bug", powered_by="Retours propulsés par BugBottle",
               scanner_mit="Scanner et CLI sous licence MIT.",
               skip="Aller au contenu", search="Rechercher", search_label="Rechercher sur le site", theme_label="Changer de thème",
               home="Accueil", contents="Sommaire", updated="Mis à jour", published="Publié", min_read="min de lecture",
               newer="Plus récent", older="Plus ancien", share="Copier le lien",
               search_title="Recherche", search_desc="Rechercher dans toutes les pages d'EUComply : guides, check-lists, outils et comparatifs.",
               search_lede="Toutes les pages du site, dans les quatre langues. Tapez un mot ou deux.",
               search_placeholder="ex. bandeau cookies, NIS2, HSTS", search_button="Rechercher",
               search_noscript="La recherche nécessite JavaScript. Le plan du site liste chaque page.",
               nf_search="Ou rechercher sur le site", nf_placeholder="Que cherchez-vous ?",
               pro_status="Le scanner gratuit est complet et reste gratuit.", support="Soutenir le scanner gratuit",
               checklist_link="check-list de conformité",
               gen_title="Ce générateur a été retiré",
               ),
}
I18N["es"] = I18N["en"]
LANG_LABEL = {"en": "EN", "da": "DA", "de": "DE", "fr": "FR", "es": "ES"}
OG_LOCALE = {"en": "en_GB", "da": "da_DK", "de": "de_DE", "fr": "fr_FR", "es": "es_ES"}

# Pages whose localised versions live under /<lang>/ when they exist.
CORE = {"", "scan/", "pricing/", "pro/", "book/", "search/"}

GENERATORS = ["impressum-generator", "privacy-policy-generator", "terms-of-service-generator",
              "refund-policy-generator", "cookie-policy-generator", "tools"]

SKIP_FILES = {"shared/live-check-widget.html"}

# Pages whose content duplicates another page: canonical points there, and they stay out of the sitemap.
CANONICAL_OVERRIDES = {}

# Hand-written titles where the automatic shortening would cut a sentence in half.
TITLE_OVERRIDES = {
    "/": "EUComply — free EU compliance scan for websites",
    "/da/": "EUComply — gratis compliance-scan af websites",
    "/de/": "EUComply — kostenloser Compliance-Scan für Websites",
    "/fr/": "EUComply — scan de conformité gratuit pour sites web",
    "/fr/scan/": "Scanner un site web : lacunes de conformité européenne",
    "/pro/": "EUComply Pro — WordPress compliance document tools",
    "/da/pro/": "EUComply Pro — dokumentværktøjer til WordPress",
    "/de/pro/": "EUComply Pro — Dokumentwerkzeuge für WordPress",
    "/fr/pro/": "EUComply Pro — outils documentaires WordPress",
    "/blog/dora-for-ecommerce-2026/": "DORA for E-Commerce: Does It Apply to Online Stores?",
    "/blog/hsts-preload-guide/": "HSTS Preload Guide 2026: Enable HSTS the Right Way",
    "/blog/meta-pixel-gdpr-consent/": "Meta Pixel and GDPR: When the Pixel Is Illegal in the EU",
    "/cli/": "eucomply-scanner — EU Compliance Scanner CLI",
    "/consent-mode-v2-check/": "Consent Mode v2 Check — Are Your Signals Correct?",
    "/de/deskuptime/": "DeskUptime — Websites vom Schreibtisch überwachen, ohne Abo",
    "/es/deskuptime/": "DeskUptime — Monitoriza tus sitios web sin suscripción",
    "/fr/deskuptime/": "DeskUptime — Surveillance de sites web sans abonnement",
    "/de/was-ist-ein-impressum/": "Was ist ein Impressum? Pflicht, Inhalte, Abmahnungsrisiko",
    "/deskuptime/change-monitor/": "Website Change Monitor — Free Content-Change Check",
    "/devnotify/github-notification-sounds-macos/": "Custom Sounds and Quiet Hours for GitHub Notifications",
    "/devnotify/guides/github-emails-after-unsubscribing/": "Still Getting GitHub Emails After Unsubscribing?",
    "/devnotify/guides/github-watch-vs-star/": "GitHub Watch vs Star: What Each Does to Notifications",
    "/devnotify/vs/gitify/": "DevNotify vs Gitify — Which GitHub Notification App?",
    "/devnotify/vs/chrome-extension/": "GitHub Notifications: Chrome Extension vs Menu Bar App",
    "/devnotify/vs/github-mobile-push/": "GitHub Notifications: Phone vs Mac Menu Bar",
    "/guides/": "All Guides — EU Compliance, Conversion and GitHub",
    "/regex/": "Regex Tester — Test and Debug Regular Expressions",
    "/regex/examples/": "Regex Examples — 20 Practical Patterns",
    "/vs/osano/": "EUComply vs Osano (2026): Scanner vs Consent Platform",
}

STOPWORDS = {"a", "an", "and", "or", "the", "in", "on", "to", "for", "of", "with", "vs", "your", "is",
             "after", "should", "at", "by", "from", "that", "this", "it", "as", "into", "und", "et", "für", "ohne"}

# Layouts. Wide pages get --w-wide from 1480px up; prose pages get the article column + TOC.
WIDE = re.compile(r"^/(scan/|compare/|cmp-comparison/|regex/|vs/|pro/(dashboard|sample-report)/|gdpr-fine-calculator/"
                  r"|[a-z0-9-]*-check/|gdpr-scanner-free/|check-eu-compliance/|deskuptime/(vs/|[a-z0-9-]*-(checker|monitor)/))")
PROSE_PAGES = {"/checklist/", "/nis2-checklist/", "/eaa-checklist/", "/privacy/", "/terms/",
               "/devnotify/privacy/", "/devnotify/terms/", "/how-it-works/"}
ARTICLE_GROUPS = ("/blog/", "/guides/", "/devnotify/guides/", "/transmute/guides/")

# Breadcrumb labels for path segments that have no index page of their own (or a long one).
SEG_LABELS = {
    "blog": {"en": "Blog", "da": "Blog", "de": "Blog", "fr": "Blog"},
    "guides": {"en": "Guides", "da": "Guides", "de": "Leitfäden", "fr": "Guides"},
    "vs": {"en": "Comparisons", "da": "Sammenligninger", "de": "Vergleiche", "fr": "Comparatifs"},
    "pro": {"en": "Pro", "da": "Pro", "de": "Pro", "fr": "Pro"}, "store": {"en": "Templates"}, "deskuptime": {"en": "DeskUptime"},
    "devnotify": {"en": "DevNotify"}, "transmute": {"en": "Transmute"}, "regex": {"en": "Regex"},
    "checklist": {"en": "Checklists", "da": "Tjeklister", "de": "Checklisten", "fr": "Check-lists"},
    "tools": {"en": "Tools"}, "book": {"en": "Guide", "da": "Guide", "de": "Leitfaden", "fr": "Guide"},
    "scan": {"en": "Scan", "fr": "Scanner"}, "pricing": {"en": "Pricing", "da": "Priser", "de": "Preise", "fr": "Tarifs"},
    "search": {"en": "Search", "da": "Søg", "de": "Suche", "fr": "Recherche"},
    # `/api/` er det tredje topsegment uden egen etiket. Uden denne faldt
    # brødkrummen tilbage til `<h1>`-teksten, og `<h1>` har `<code>API</code>`
    # indeni: etiketten blev "The EU compliance scan API " med et afsluttende
    # mellemrum, fordi koden er fjernet men pladsen efter den er blevet stående.
    # Samme fejl stod i alle fire sprog, kun på fire måder — spejlingerne fik
    # deres etiket fra den oversatte `<h1>`, originalen fra en håndskrevet
    # breadcrumb der sagde "Free scan API" og ikke længere passede med titlen.
    # "API" er produktets navn og ens i alle sprog, som `CLI`.
    "api": {"en": "API", "da": "API", "de": "API", "fr": "API"},
}

HEADER_TPL = (PARTIALS / "header.html").read_text(encoding="utf-8")
FOOTER_TPL = (PARTIALS / "footer.html").read_text(encoding="utf-8")
SITE_CSS = (SITE / "assets" / "site.css").read_text(encoding="utf-8")
SITE_TOKENS = set(re.findall(r"(--[a-z0-9-]+)\s*:", SITE_CSS.split("/* ---------- Base")[0]))

ICON_LINKS = """<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#0b6e4f">"""

# Runs before the stylesheet so a remembered theme never flashes. Also marks JS as available.
JS_BOOT = ('<script data-boot>(function(){var d=document.documentElement;d.classList.add("js");'
           'try{var t=localStorage.getItem("theme");if(t==="light"||t==="dark")d.setAttribute("data-theme",t)}catch(e){}})()</script>')
OLD_BOOT = '<script>document.documentElement.classList.add("js")</script>'

SHELL_FENCE = re.compile(r"\s*<!--shell:([a-z-]+)-->.*?<!--/shell:\1-->", re.S)


def fence(name: str, inner: str) -> str:
    return f"<!--shell:{name}-->{inner}<!--/shell:{name}-->"


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


def page_exists(url: str) -> bool:
    fs = SITE / url.lstrip("/")
    if url.endswith("/"):
        fs = fs / "index.html"
    return fs.exists()


def alternates(url: str) -> dict:
    """Return {lang: url} for every existing language version of this page."""
    base = strip_lang(url)
    out = {}
    for lang in LANGS + ["es"]:
        cand = base if lang == "en" else "/" + lang + base
        if page_exists(cand):
            out[lang] = cand
    return out


def core_path(lang: str, base: str) -> str:
    """Localised path for a core page if it exists, else the English one."""
    if lang != "en" and page_exists(f"/{lang}/{base}"):
        return f"/{lang}/{base}"
    return "/" + base


def lang_switch(url: str, lang: str) -> str:
    """Four fixed slots (plus ES when it exists) so the header never changes width."""
    alts = alternates(url)
    items = []
    for l in LANGS + (["es"] if "es" in alts else []):
        if l == lang:
            items.append(f'<li><span aria-current="true" lang="{l}">{LANG_LABEL[l]}</span></li>')
        elif l in alts:
            items.append(f'<li><a href="{alts[l]}" hreflang="{l}" lang="{l}">{LANG_LABEL[l]}</a></li>')
        else:
            items.append(f'<li class="is-off" aria-hidden="true"><span>{LANG_LABEL[l]}</span></li>')
    return '<ul class="sh-lang" aria-label="Language">' + "".join(items) + "</ul>"


def render_shell(url: str, lang: str) -> tuple[str, str]:
    t = dict(I18N[lang])
    t["home"] = core_path(lang, "")
    t["p_scan"] = core_path(lang, "scan/")
    t["p_book"] = core_path(lang, "book/")
    t["p_pricing"] = core_path(lang, "pricing/")
    t["p_search"] = core_path(lang, "search/")
    t["year"] = YEAR
    base = strip_lang(url)
    for key, pat in (("scan", "/scan/"), ("book", "/book/"), ("checklist", "/checklist/"),
                     ("pricing", "/pricing/"), ("blog", "/blog/")):
        cur = base == pat or (key == "blog" and base.startswith("/blog/")) or (key == "checklist" and base.endswith("-checklist/"))
        t["cur_" + key] = ' aria-current="page"' if cur else ""
    t["langswitch"] = lang_switch(url, lang)
    header, footer = HEADER_TPL, FOOTER_TPL
    for k, v in t.items():
        header = header.replace("{{" + k + "}}", v)
        footer = footer.replace("{{" + k + "}}", v)
    return header.strip(), footer.strip()


# ------------------------------------------------------------- git dates

# Hvor mange commits `git_dates()` går tilbage i tiden efter `last`. Det er en
# arbejdsgrænse, ikke en sandhedsgrænse: en side, der ikke løses inden for
# vinduet, har ikke haft en redaktionel ændring i vinduet, så den falder
# tilbage på sin oprettelsesdato.
GIT_SIDE_VINDUE = 40


def _blob_reader():
    """Én `git cat-file --batch` for alle blobs: én proces, hundredvis af læsninger.

    Binær, ikke tekst. `read(n)` skal tælle **byte** — på en tekststrøm tæller
    den tegn, så en side med ét dansk tegn ville forskyde resten af strømmen,
    og hver svigende læsning ville se ud som en redaktionel ændring.
    """
    return subprocess.Popen(["git", "cat-file", "--batch"], cwd=ROOT,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)


def _read_blobs(proc, specs):
    proc.stdin.write(b"".join(s.encode() + b"\n" for s in specs))
    proc.stdin.flush()
    out = {}
    for s in specs:
        head = proc.stdout.readline().split()
        if len(head) < 3 or head[1] != b"blob":
            out[s] = None  # rod-commit, tilføjet fil eller slettet sti
            continue
        out[s] = proc.stdout.read(int(head[2])).decode("utf-8", "replace")
        proc.stdout.read(1)  # git skriver én newline efter hvert objekt
    return out


def _nøgle(rå: str) -> str:
    """`site/blog/x/index.html` → `blog/x/index.html`, som `relative_to(SITE)` giver."""
    return rå[5:] if rå.startswith("site/") else rå


def _kræv_fuld_historie() -> None:
    """Svar på "hvornår?" kræver historien. En grund klon har ikke nogen.

    `actions/checkout` har `fetch-depth: 1` som standard, altså **én** commit.
    `git log` svarer da på intet for alle de sider, HEAD-committen ikke rører,
    og `git_dates()` ville stille give dem `TODAY` — 175 `lastmod` i det
    publicerede sitemap flyttet til i dag, i stilhed. Målt 28/9 (`7bd3f60`):
    CI `36485230317` blev rød på `R1 sitemap.xml: linje 22`, fordi den dybe
    lokale klon og CI's klon på én commit gav to forskellige svar på det
    samme spørgsmål; `git clone --depth 1` af HEAD reproducerede fejlen byte
    for byte.

    Derfor er svaret på en grund klon **ingen**, og det siger hvorfor. En gate
    der ikke kan måle, skal være rød og sige det — ikke grøn og tavs. En
    undtagelse i stedet for `{}` er nødvendig: `{}` betyder "ingen datoer
    kendt", hvilket også er sandt, men kalderen læser det som "ingen sider",
    og så får alle 230 sider `TODAY` lige så stille.
    """
    dyb = subprocess.run(["git", "rev-parse", "--is-shallow-repository"],
                         cwd=ROOT, capture_output=True, text=True)
    if dyb.stdout.strip() == "true":
        raise SystemExit(
            "FEJL: git-historien er grund (--depth 1). `git_dates()` kan ikke "
            "svare på hvornår en side blev redigeret, fordi historien ikke er "
            "med, og den svarer ikke `TODAY` i stedet. Checkout med fuld "
            "historie: actions/checkout@v7 med `fetch-depth: 0`."
        )


def git_dates() -> dict:
    """{relpath: (første commit-dato, sidste redaktionelle dato)} for `site/`.

    Den **anden** dato er den der betyder noget. Den bliver `dateModified` i
    JSON-LD og `lastmod` i sitemapet, så den skal svare til det sidste en
    **redaktør** rørte — ikke det sidste en skalkørsel genererede.

    Før blev "er det en skalkørsel?" svaret med ét tal: rørte committen 60+
    filer, var den bulk. Det er målt, og det er **forkert i begge retninger**.
    `cdab45c` rørte 51 filer og blev dermed frikendt, så 36 sider fik
    `lastmod: 2026-09-28` i sitemapet uden at en redaktør have rørt dem — og
    samme commit rummede en ægte sætningsfejl i `site/plugin/index.html`.
    Omvendt blev alle 234 filer i `fba1971` frikendt, også den side der virkelig
    var skrevet om. Ét tal kan ikke se det, fordi **ét commit kan være begge
    dele på én gang**: en skalkørsel der samtidig rettede en sætning.

    Det kan måles i stedet. Skalens output ligger indhegnet i
    `<!--shell:…-->`-blokke, så er to revisioner ens **uden** blokke pr.
    definition en mekanisk ændring. Ellers har en redaktør rørt siden. Begge
    udfald peger samme vej, i den sikre retning: en tilføjet fil har ingen
    forælder og tælles som redaktionel (en ny side *er* nyt indhold), og en
    skalkørsel der ændrer noget uden for blokkene — en `aria-label` i
    headeren, et nyt stylesheet-link — tælles også som redaktionel. Porten kan
    altså aldrig markere en side som ændret, når den ikke er; den kan
    under-angive, og det er den fejl der koster en ekstra genindhentning.

    `GIT_SIDE_VINDUE` sætter grænsen på arbejdet. De 268 commits der rører
    `site/` er ikke alle værd at læse to blobs af for hver af 232 filer. Løses
    en side ikke inden for vinduet, har den ikke haft en redaktionel ændring
    derinde, så den får sin oprettelsesdato — præcis som den gamle bulk-regel
    gjorde, og ærligt: siden er ikke ændret siden den blev lagt ind.
    """
    _kræv_fuld_historie()
    oprettet, sidst = {}, {}
    try:
        log = subprocess.run(["git", "log", "--format=@%H %cs %P", "--name-only", "--", "site"],
                             cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    except Exception:
        return {}
    commits, cur = [], None
    for line in log.splitlines():
        if line.startswith("@"):
            if cur:
                commits.append(cur)
            p = line[1:].split()
            cur = {"sha": p[0], "dato": p[1], "forældre": p[2:], "filer": []}
        elif line.strip() and cur:
            cur["filer"].append(line.strip())  # repo-sti, `site/…` — nøglen tages senere
    if cur:
        commits.append(cur)
    for c in commits:  # nyeste først
        for rå in c["filer"]:
            rel = rå[5:] if rå.startswith("site/") else rå
            oprettet[rel] = c["dato"]  # overskrives af ældre commits → oprettelsesdato

    uløst = set(oprettet)
    proc = None
    try:
        for c in commits[:GIT_SIDE_VINDUE]:
            kandidater = [r for r in c["filer"] if _nøgle(r) in uløst]
            if not kandidater:
                continue
            if not c["forældre"]:
                uløst.difference_update(_nøgle(r) for r in kandidater)  # rod-commit
                for rel in (_nøgle(r) for r in kandidater):
                    sidst[rel] = c["dato"]
                continue
            if proc is None:
                proc = _blob_reader()
            forælder = c["forældre"][0]
            blobs = _read_blobs(proc, [f"{forælder}:{r}" for r in kandidater]
                                     + [f"{c['sha']}:{r}" for r in kandidater])
            for r in kandidater:
                rel = _nøgle(r)
                før, nu = blobs.get(f"{forælder}:{r}"), blobs.get(f"{c['sha']}:{r}")
                if før is not None and nu is not None and \
                        SHELL_FENCE.sub("", før) == SHELL_FENCE.sub("", nu):
                    continue  # mekanisk: kig længere tilbage
                uløst.discard(rel)
                sidst[rel] = c["dato"]
    finally:
        if proc:
            proc.stdin.close()
            proc.wait()
    for rel in uløst:  # vinduet slap: uændret siden den blev lagt ind
        sidst[rel] = oprettet[rel]
    return {k: (oprettet[k], sidst[k]) for k in oprettet}


GIT_DATES = git_dates()


# ---------------------------------------------------------------- CSS filter

SHELL_SEL = re.compile(
    r"^(html|\*|header|footer|nav|\.logo|\.brand|\.nav|\.site-header|\.site-footer|\.topbar|\.navbar|\.cta)(\b|$)",
    re.I,
)
WRAPPER_SEL = re.compile(
    r"^(body|\.wrap|\.container|\.content|\.page|\.inner|main|article|\.article|\.post-body|\.blog-header|\.pg-legacy|section|\.section)(\b|$)",
    re.I,
)
WIDTH_DECL = re.compile(r"^(max-width|width|min-width)\s*:", re.I)
SIDE_DECL = re.compile(r"^(margin|padding)-(left|right|inline)\s*:", re.I)
BOX_DECL = re.compile(r"^(margin|padding)\s*:\s*([^;]+)$", re.I)
CENTER_DECL = re.compile(r"^margin(-inline)?\s*:[^;]*\bauto\b", re.I)


def vertical_only(decl: str) -> str | None:
    """`margin: 32px auto` -> `margin:32px 0`; `padding: 0 20px` -> dropped; keeps vertical spacing."""
    m = BOX_DECL.match(decl)
    if not m:
        return decl
    prop, vals = m.group(1).lower(), m.group(2).split()
    if "!important" in vals:
        vals.remove("!important")
    top, bottom = (vals[0], vals[0]) if len(vals) < 3 else (vals[0], vals[2])
    if top in ("0", "0px") and bottom in ("0", "0px"):
        return None
    return f"{prop}:{top} 0 {bottom} 0"


def neutralise_layout(decls: list) -> list:
    out = []
    for d in decls:
        if WIDTH_DECL.match(d) or SIDE_DECL.match(d):
            continue
        d = vertical_only(d)
        if d:
            out.append(d)
    return out
ALIGN_SEL = re.compile(r"(hero|\.sub\b|\.lede|\.intro|^h1\b|\.title|\.head\b|\.header\b|\.top\b)", re.I)


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
    """Drop shell rules, neutralise page-own widths and centring, keep everything else."""
    out = []
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
        if not keep:
            continue
        decls = [d.strip() for d in body.split(";") if d.strip()]
        if any(re.match(r"^(:root|html)\b", p) for p in keep):
            decls = [d for d in decls if not (d.startswith("--") and d.split(":")[0].strip() in SITE_TOKENS)]
        keep = [re.sub(r"(?<![.\w-])main\b", "[data-legacy-main]", p) for p in keep]
        if any(WRAPPER_SEL.match(p) for p in keep) or any(WRAPPER_SEL.match(p) for p in parts):
            decls = neutralise_layout(decls)
        decls = [vertical_only(d) if CENTER_DECL.match(d) else d for d in decls]
        decls = [d for d in decls if d]
        if any(ALIGN_SEL.search(p) for p in keep):
            decls = [d for d in decls if not re.match(r"^text-align\s*:\s*center", d, re.I)]
        if any(re.match(r"^position\s*:\s*sticky", d, re.I) for d in decls):
            decls = [re.sub(r"^top\s*:\s*0(px)?$", "top:var(--header-h)", d, flags=re.I) for d in decls]
        if not decls:
            continue
        out.append(",".join(keep) + "{" + ";".join(decls) + "}")
    return "\n".join(out)


# ------------------------------------------------------- colour tokenising

NAMED = {"white": (255, 255, 255), "black": (0, 0, 0)}


def _rgb(tok: str):
    t = tok.strip().lower()
    if t in NAMED:
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
    return "var(--warn)"


COLOUR_RE = re.compile(r"(?<![\w-])(#[0-9a-fA-F]{8}\b|#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3,4}\b|rgba?\([^)]*\)|\bwhite\b|\bblack\b)")


def tokenize_decls(decls: str) -> str:
    """Rewrite colours inside a run of CSS declarations. Skips url() payloads."""
    parts = re.split(r"(url\([^)]*\))", decls)
    for i in range(0, len(parts), 2):
        parts[i] = COLOUR_RE.sub(lambda m: token_for(m.group(1)) or m.group(1), parts[i])
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
        out.append(tokenize_css(body) if "{" in body else tokenize_decls(body))
        out.append("}")
        i = k
    return "".join(out)


SIZED_TAGS = ("img", "svg", "video", "td", "th", "col", "iframe", "canvas", "i", "span", "input", "select", "textarea", "progress", "meter")


def clean_style_attr(tag: str, style: str) -> str:
    """Inline styles: no page-own widths or centring on block elements; colours to tokens."""
    decls = [d.strip() for d in style.split(";") if d.strip()]
    if tag.lower() not in SIZED_TAGS:
        decls = [d for d in decls if not WIDTH_DECL.match(d)]
    decls = [vertical_only(d) if CENTER_DECL.match(d) else d for d in decls]
    return tokenize_decls(";".join(d for d in decls if d))


STYLE_ATTR = re.compile(r'<([a-zA-Z][a-zA-Z0-9]*)((?:[^>"]|"[^"]*")*?)\s+style="([^"]*)"')


def clean_style_attrs(html: str) -> str:
    def repl(m):
        new = clean_style_attr(m.group(1), m.group(3))
        return f'<{m.group(1)}{m.group(2)} style="{new}"' if new else f"<{m.group(1)}{m.group(2)}"
    return STYLE_ATTR.sub(repl, html)


# ---------------------------------------------------------------- cleaners

EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF☀-⛿✅❌❎⭐⭕‼⁉ℹ⌚⌛"
    "⏩-⏺▶◀⤴⤵⬅-⬇〰〽㊗㊙➕-➗"
    "⬛⬜❗❣❤✨✳✴❄❇➡➰➿"
    "\U0001F1E6-\U0001F1FF]️?(?:‍[\U0001F000-\U0001FAFF]️?)*|️"
)

def hype_verb(base: str, by_suffix: dict[str, str]) -> tuple[re.Pattern, object]:
    """A hype verb whose replacement keeps the inflection of the word it replaces.

    `unlocks` -> `gets`, not `get`. The table this replaces had one form per verb,
    so every third-person sentence came out ungrammatical: "It unlocks the
    starters" became "It get the starters" on the three pages the cleaner still
    reaches. `by_suffix` is keyed by the matched suffix, "" for the base form, and
    the case of the replacement follows the case of `base`.
    """
    alts = "|".join(re.escape(s) for s in by_suffix if s)
    pat = re.compile(r"\b%s(%s)?\b" % (base, alts))
    upper = base[:1].isupper()
    return pat, lambda m, _f=by_suffix, _u=upper: _cased(_f[m.group(1) or ""], _u)


def _cased(word: str, upper: bool) -> str:
    """`Get` when the source word started upper case, `get` when it did not."""
    return word[:1].upper() + word[1:] if upper else word


HYPE = [
    hype_verb("Supercharge", {"": "speed up", "s": "speeds up", "d": "sped up"}),
    hype_verb("supercharge", {"": "speed up", "s": "speeds up", "d": "sped up"}),
    (re.compile(r"\bSeamlessly\b"), "Easily"), (re.compile(r"\bseamlessly\b"), "easily"),
    (re.compile(r"\bSeamless\b"), "Simple"), (re.compile(r"\bseamless\b"), "simple"),
    hype_verb("Elevate", {"": "improve", "s": "improves", "d": "improved"}),
    hype_verb("elevate", {"": "improve", "s": "improves", "d": "improved"}),
    hype_verb("Unlock", {"": "get", "s": "gets", "ed": "got"}),
    hype_verb("unlock", {"": "get", "s": "gets", "ed": "got"}),
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
                depth += 1 if mm.group(1) == "" else -1
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


LIVE_CHECKOUT = ("https://buy.stripe.com/", "https://donate.stripe.com/")
DEAD_BUY = re.compile(r"<(a|button)\b([^>]*)>((?:(?!</\1>).)*?)</\1>", re.S | re.I)
BUY_TEXT = re.compile(
    r"(buy|get pro|upgrade|checkout|reserve|pre-?order|purchase|notify me|waiting for payments"
    r"|start (daily|pro|monitoring)|subscribe|get the (book|bundle|guide)\s*[—–-]\s*\$|order now|add to cart"
    r"|start (free )?trial|get started with pro|choose pro|go pro)", re.I)


def neutralise_buy_buttons(html: str, lang: str) -> str:
    def repl(m):
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
        if "data-keep" in attrs or "sf-bug" in attrs or "sh-" in attrs:
            return m.group(0)
        text = re.sub(r"<[^>]+>", "", inner)
        href = re.search(r'href="([^"]*)"', attrs)
        href = href.group(1) if href else ""
        # Live Stripe payment and donation links are real buttons, never dead ones.
        if href.startswith(LIVE_CHECKOUT):
            return m.group(0)
        external_checkout = re.search(r"stripe|paddle|checkout", href, re.I)
        # Only short, button-like elements: a post card or a comparison card whose text
        # happens to mention a price is content, and a TOC link to "#start-monitoring"
        # is navigation.  Both were wiped by an earlier, looser version of this rule.
        if re.search(r"<(h\d|p|div|ul|ol|li|section|article)\b", inner, re.I) or len(text.strip()) > 48:
            return m.group(0)
        if href.startswith("#") and "btn" not in attrs:
            return m.group(0)
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
    """Apply fn to the parts of html that are not inside <script>/<style>/<pre>/<code>.

    `<pre>` og `<code>` blev beskyttet i iteration 110, og de skulle have været
    det hele vejen. Målt over hele træet (230 sider, 1081 kodeblokke) ændrede
    skallen **én** blok, og den var rigtig: emoji-renseren slettede 🔍 fra
    `/cli/`s genererede eksempel på den **egentlige** scanner-output. Det er den
    fejlklasse, der gør et dokumenteret eksempel til løgnen — samme som
    `check_dom_xss.py` så i quick-check-widgeten. Renserne skal ændre prosa, og
    et `<pre>` er ikke prosa.

    Navnet passede aldrig helt; nu gør det.
    """
    parts = re.split(r"(<(?:script|style|pre|code)\b[^>]*>.*?</(?:script|style|pre|code)\s*>)", html,
                     flags=re.S | re.I)
    for i in range(0, len(parts), 2):
        parts[i] = fn(parts[i])
    return "".join(parts)


def wrap_tables(html: str, sticky_col: bool = False) -> str:
    """Give every <table> a horizontally scrolling wrapper (idempotent)."""
    cls = "tbl sticky-col" if sticky_col else "tbl"
    html = re.sub(r'<div class="tbl(?: sticky-col)?">\s*(<table\b.*?</table>)\s*</div>', r"\1", html, flags=re.S | re.I)
    return re.sub(r"<table\b.*?</table>", lambda m: f'<div class="{cls}">' + m.group(0) + "</div>", html, flags=re.S | re.I)


def add_missing_alt(html: str) -> str:
    return re.sub(r"<img\b(?![^>]*\balt=)([^>]*?)(/?)>", r'<img alt=""\1\2>', html, flags=re.I)


def image_size(src: str):
    """(width, height) for a local PNG/JPEG/SVG, else None."""
    if not src.startswith("/") or src.startswith("//"):
        return None
    p = SITE / src.split("?")[0].lstrip("/")
    if not p.exists():
        return None
    try:
        data = p.read_bytes()
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            w, h = struct.unpack(">II", data[16:24])
            return w, h
        if data[:2] == b"\xff\xd8":
            i = 2
            while i < len(data):
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                if marker in (0xC0, 0xC1, 0xC2):
                    h, w = struct.unpack(">HH", data[i + 5 : i + 9])
                    return w, h
                i += 2 + struct.unpack(">H", data[i + 2 : i + 4])[0]
        if p.suffix == ".svg":
            head = data[:2000].decode("utf-8", "replace")
            m = re.search(r'viewBox="[\d.\s-]*?([\d.]+)\s+([\d.]+)"', head)
            if m:
                return int(float(m.group(1))), int(float(m.group(2)))
    except Exception:
        return None
    return None


def lazy_images(html: str) -> str:
    def repl(m):
        tag = m.group(0)
        closer = "/>" if tag.endswith("/>") else ">"
        inner = tag[: -len(closer)].rstrip()
        add = ""
        if "loading=" not in inner:
            add += ' loading="lazy"'
        if "decoding=" not in inner:
            add += ' decoding="async"'
        if "width=" not in inner or "height=" not in inner:
            src = re.search(r'src="([^"]+)"', inner)
            size = image_size(src.group(1)) if src else None
            if size:
                inner = re.sub(r'\s(width|height)="[^"]*"', "", inner)
                add += f' width="{size[0]}" height="{size[1]}"'
        return inner + add + closer
    return re.sub(r"<img\b[^>]*>", repl, html, flags=re.I)


def aria_live_results(html: str) -> str:
    """Tool result containers announce themselves to screen readers."""
    return re.sub(r'<(div|section|ul|ol|output)\b((?![^>]*aria-live)[^>]*\bid="(results?|output|out|verdict|report)"[^>]*)>',
                  r'<\1\2 aria-live="polite">', html, flags=re.I)


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
    words = cut.rstrip(" ,;:-–—").split(" ")
    while len(words) > 3 and words[-1].lower().strip("?:,") in STOPWORDS:
        words.pop()
    return " ".join(words).rstrip(" ,;:-–—")


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
    return s.replace("/", "-") if s else "home"


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
MONTHS.update({"mai": 5, "okt": 10, "dez": 12, "mär": 3, "jui": 6, "aoû": 8, "déc": 12, "fév": 2, "avr": 4})


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
    m = re.search(r"\b(\d{1,2})\.? ([A-Za-zéû]{3,9}) (20\d{2})\b", scope)
    if m and m.group(2)[:3].lower() in MONTHS:
        return f"{m.group(3)}-{MONTHS[m.group(2)[:3].lower()]:02d}-{int(m.group(1)):02d}"
    return None


def is_article(url: str, body: str) -> bool:
    base = strip_lang(url)
    if base in ("/blog/", "/guides/", "/devnotify/guides/", "/devnotify/", "/deskuptime/", "/transmute/", "/vs/"):
        return False
    if base.startswith(ARTICLE_GROUPS):
        return True
    return bool(re.search(r'class="meta"[^>]*>[^<]*(min read|Min\. Lesezeit|min\. læsning|min de lecture|\d{4}-\d{2}-\d{2}|20\d{2})', body))


def layout_for(url: str, body: str) -> str:
    base = strip_lang(url)
    if WIDE.match(base):
        return "wide"
    if base in PROSE_PAGES or is_article(url, body):
        return "prose"
    return "default"


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


def ld_script(obj: dict, marker: str = "data-shell") -> str:
    return f'<script type="application/ld+json" {marker}>' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>"


def seo_head(html: str, url: str, lang: str, rel: str) -> str:
    """Normalise <head>: title, description, canonical, OG, Twitter, icons, JSON-LD."""
    hi = html.find("</head>")
    if hi < 0:
        return html
    head, rest = html[:hi], html[hi:]
    body = rest
    canonical = ORIGIN + CANONICAL_OVERRIDES.get(url, url)
    noindex = bool(re.search(r'name="robots"[^>]*noindex', head))

    tm = re.search(r"<title>(.*?)</title>", head, re.S)
    full_title = re.sub(r"\s+", " ", htmlmod.unescape(tm.group(1))).strip() if tm else ""
    title = TITLE_OVERRIDES.get(url) or (short_title(full_title) if full_title else "")
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

    head = re.sub(r'\s*<link\s+rel="canonical"[^>]*>', "", head, flags=re.I)
    head = re.sub(r'(<meta name="description"[^>]*>)', lambda m: m.group(1) + f'\n<link rel="canonical" href="{canonical}">', head, count=1)

    head = re.sub(r'\s*<link\s+rel="icon"\s+href="data:image/svg\+xml,[^"]*"[^>]*>', "", head, flags=re.I)
    head = re.sub(r"\s*<(?:rect|text|path|circle|g)\b[^\n]*?</svg>\">", "", head)
    head = re.sub(r'\s*<link\s+rel="(icon|apple-touch-icon|manifest|shortcut icon)"[^>]*>', "", head, flags=re.I)
    head = remove_meta(head, "name", "theme-color")
    head = re.sub(r'(<link rel="canonical"[^>]*>)', lambda m: m.group(1) + "\n" + ICON_LINKS, head, count=1)

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

    # Skalens egen JSON-LD river væk med det samme, så dens datoer læses
    # lige før. Uden dem skrev hver kørling dagens `dateModified`, fordi
    # `find_date(body)` læser den `art-meta` skalen lige har skrevet, og
    # `datePublished` så faldt sammen med `dateModified`.
    frozen_ld = shell_dates(head + body)
    head = re.sub(r'\s*<script type="application/ld\+json" data-shell(-crumbs)?>.*?</script>', "", head, flags=re.S)
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
                           "description": desc, "author": AUTHOR, "publisher": {"@id": ORIGIN + "/#org"},
                           "potentialAction": {"@type": "SearchAction",
                                               "target": {"@type": "EntryPoint", "urlTemplate": ORIGIN + core_path(lang, "search/") + "?q={search_term_string}"},
                                               "query-input": "required name=search_term_string"}})
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
            published = frozen_ld.get("datePublished") or find_date(body) or first
            modified = frozen_ld.get("dateModified") or max(last, published)
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
        head = head.rstrip() + "\n" + "\n".join(ld_script(b) for b in blocks) + "\n"
    if noindex:
        head = re.sub(r'\s*<meta\s+property="og:[^>]*>|\s*<meta\s+name="twitter:[^>]*>', "", head)
    return head + rest


# ------------------------------------------------------------ page catalogue

PAGES: dict[str, dict] = {}   # url -> {title, h1, desc, lang, date, rel}


def catalogue():
    """Titles, dates and descriptions of every page, for breadcrumbs, prev/next and search."""
    for p in sorted(SITE.rglob("*.html")):
        rel = p.relative_to(SITE).as_posix()
        if rel in SKIP_FILES or rel.startswith("_partials/") or rel == "404.html":
            continue
        html = p.read_text(encoding="utf-8")
        url = rel_url(p)
        tm = re.search(r"<title>(.*?)</title>", html, re.S)
        title = TITLE_OVERRIDES.get(url) or (short_title(tm.group(1)) if tm else "")
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
        h1t = text_of(h1.group(1)) if h1 else title
        body = html[html.find("</head>"):]
        first, last = GIT_DATES.get(rel, (TODAY, TODAY))
        PAGES[url] = {"title": title or h1t, "h1": h1t or title, "lang": lang_of(url), "rel": rel,
                      "desc": find_meta(html, "name", "description") or "",
                      "date": find_date(body) or first, "updated": max(last, find_date(body) or first),
                      "noindex": bool(re.search(r'name="robots"[^>]*noindex', html[:4000])),
                      "article": is_article(url, body)}


def crumb_label(seg: str, lang: str, url: str) -> str:
    if seg in SEG_LABELS:
        return SEG_LABELS[seg].get(lang) or SEG_LABELS[seg]["en"]
    if url in PAGES:
        return short_title(PAGES[url]["h1"], 40)
    return seg.replace("-", " ").capitalize()


def breadcrumbs(url: str, lang: str, page_title: str) -> tuple[str, dict | None]:
    base_home = core_path(lang, "")
    if url == base_home or url == "/404.html":
        return "", None
    parts = url.strip("/").split("/")
    if lang != "en" and parts and parts[0] == lang:
        parts = parts[1:]
    t = I18N[lang]
    items = [(t["home"], base_home)]
    prefix = "/" + lang + "/" if lang != "en" else "/"
    for i, seg in enumerate(parts[:-1]):
        u = prefix + "/".join(parts[: i + 1]) + "/"
        alt = "/" + "/".join(parts[: i + 1]) + "/"   # localised sections may only exist in English
        target = u if page_exists(u) else (alt if page_exists(alt) else None)
        items.append((crumb_label(seg, lang, target or u), target))
    last = parts[-1] if parts else ""
    if last in SEG_LABELS and len(parts) == 1:
        items.append((crumb_label(last, lang, url), None))
    else:
        items.append((short_title(page_title, 70).rstrip(".!"), None))
    lis = []
    for i, (label, href) in enumerate(items):
        if href and i < len(items) - 1:
            lis.append(f'<li><a href="{href}">{attr_escape(label)}</a></li>')
        elif i == len(items) - 1:
            lis.append(f'<li><span aria-current="page">{attr_escape(label)}</span></li>')
        else:
            lis.append(f"<li><span>{attr_escape(label)}</span></li>")
    nav = f'<nav class="crumbs" aria-label="Breadcrumb"><ol>{"".join(lis)}</ol></nav>'
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": label,
         **({"item": ORIGIN + href} if href else ({"item": ORIGIN + url} if i == len(items) - 1 else {}))}
        for i, (label, href) in enumerate(items)]}
    return nav, ld


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower().replace("æ", "ae").replace("ø", "o").replace("å", "a")
               .replace("ä", "a").replace("ö", "o").replace("ü", "u").replace("ß", "ss")
               .replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a").replace("ç", "c")).strip("-")
    return s[:60].rstrip("-") or "section"


def heading_ids(html: str) -> tuple[str, list]:
    """Ensure every h2/h3 has an id; return (html, [(level, id, text)])."""
    seen, toc = set(), []
    for m in re.finditer(r'\bid="([^"]+)"', html):
        seen.add(m.group(1))

    def repl(m):
        level, attrs, inner = m.group(1), m.group(2), m.group(3)
        text = text_of(inner)
        if not text or re.match(r"^(keep reading|further reading|related|contents|table of contents|læs også|weiterlesen|lire aussi)", text, re.I):
            return m.group(0)
        idm = re.search(r'\bid="([^"]+)"', attrs)
        if idm:
            hid = idm.group(1)
        else:
            hid = base = slugify(text)
            n = 2
            while hid in seen:
                hid = f"{base}-{n}"
                n += 1
            seen.add(hid)
            attrs = attrs + f' id="{hid}"'
        toc.append((int(level), hid, text))
        return f"<h{level}{attrs}>{inner}</h{level}>"
    html = re.sub(r"<h([23])\b([^>]*)>(.*?)</h\1>", repl, html, flags=re.S | re.I)
    return html, toc


def toc_markup(toc: list, lang: str) -> tuple[str, str]:
    if len(toc) < 3:
        return "", ""
    items = "".join(f'<li class="lvl{lvl}"><a href="#{hid}">{attr_escape(short_title(text, 70))}</a></li>' for lvl, hid, text in toc)
    label = I18N[lang]["contents"]
    side = f'<aside class="toc-side" aria-label="{label}"><h2>{label}</h2><ol>{items}</ol></aside>'
    details = f'<details class="toc-details"><summary>{label}</summary><ol>{items}</ol></details>'
    return side, details


def article_group(url: str) -> str | None:
    base = strip_lang(url)
    for g in ARTICLE_GROUPS:
        if base.startswith(g) and base != g:
            return (url[: len(url) - len(base) + len(g)])
    return None


def prev_next(url: str, lang: str) -> str:
    g = article_group(url)
    if not g:
        return ""
    sib = sorted([(u, p) for u, p in PAGES.items() if u.startswith(g) and u != g and p["article"] and not p["noindex"]
                  and u.count("/") == g.count("/") + 1], key=lambda x: (x[1]["date"], x[0]), reverse=True)
    urls = [u for u, _ in sib]
    if url not in urls:
        return ""
    i = urls.index(url)
    t = I18N[lang]
    out = []
    if i > 0:
        u = urls[i - 1]
        out.append(f'<a class="prev" href="{u}" rel="prev"><small>{t["newer"]}</small><b>{attr_escape(short_title(PAGES[u]["h1"], 80))}</b></a>')
    if i + 1 < len(urls):
        u = urls[i + 1]
        out.append(f'<a class="next" href="{u}" rel="next"><small>{t["older"]}</small><b>{attr_escape(short_title(PAGES[u]["h1"], 80))}</b></a>')
    return f'<nav class="pn" aria-label="{t["newer"]} / {t["older"]}">{"".join(out)}</nav>' if out else ""


SHELL_TIME = re.compile(r'<time datetime="(\d{4}-\d{2}-\d{2})"[^>]*>([A-Za-z]+) \1</time>')

# Kun skalens **egne** markerede blokke tæller. En `art-meta` eller et
# `data-shell`-JSON-LD som en redaktør har skrevet i hånden, er ikke skalens
# hukommelse, og den skal derfor ikke låse sin egen dato fast.
SHELL_META_BLOCK = re.compile(r'<!--shell:meta-->(.*?)<!--/shell:meta-->', re.S)
SHELL_LD_BLOCK = re.compile(
    r'<script type="application/ld\+json" data-shell>(.*?)</script>', re.S)


def shell_dates(html: str) -> dict[str, str]:
    """Datoerne skalen selv skrev i sidste kørling, kun fra dens egne blokke.

    Det er den eneste kilde, der er et fast punkt. `GIT_DATES` er ikke: sidste
    skalkørsel-commit er større end portens bulk-tærskel på 60 filer, så git
    mente siden var redaktionelt opdateret i går, og næste kørling skrev dagens
    dato. Datoen er så læst tilbage fra `art-meta` som sidens *publicerings*
    dato, hvilket gjorde `datePublished` til `dateModified` og fik `prev_next()`
    til at sortere kæden om. Se `check_shell_fixed_point.py`.
    """
    out: dict[str, str] = {}
    block = SHELL_META_BLOCK.search(html)
    if block:
        m = SHELL_TIME.search(block.group(1))
        if m:
            out["art"], out["label"] = m.group(1), m.group(2)
    ld = SHELL_LD_BLOCK.search(html)
    if ld:
        for key in ("datePublished", "dateModified"):
            m = re.search(rf'"{key}"\s*:\s*"(\d{{4}}-\d{{2}}-\d{{2}})"', ld.group(1))
            if m:
                out[key] = m.group(1)
    return out


def article_meta(url: str, lang: str, rel: str, content: str,
                 frozen: dict | None = None) -> str:
    """Artiklens dato-linje. Den skal være et **fast punkt**, ikke en afledning.

    Datoen blev hver kørsel genberegnet som `max(git-seneste-commit, publiceret)`.
    Det er selvkørende: skalen skriver `Updated <git-dato>` ind i `art-meta`, og
    næste kørsel læser **sit eget output** tilbage som sidens dato (`find_date`
    tager det første `<time>` i body). Den nye dato flytter siden i
    `prev_next()`'s sortering, så hele bloggens forrige/næste-kæde skrev sig om,
    og de nye sider fik nye datoer — 33 sider i første kørsel, 39 i den næste, og
    først i tredje standsede det. Hver ny commit der rørte `site/` startede
    kæden forfra.

    En dato skalen selv har skrevet, genbruges derfor uændret. En mekanisk
    gen-rendring er ikke en redaktionel opdatering, så den må heller ikke flytte
    datoen: det ville mærke artikler som "Updated" uden at en redaktør har rørt
    dem. Kun sider uden en skrevet dato får en, og da fra siden selv eller git.
    """
    t = I18N[lang]
    words = len(text_of(content).split())
    minutes = max(1, round(words / 220))
    if frozen and frozen.get("art"):
        date, label = frozen["art"], frozen["label"]
    else:
        first, last = GIT_DATES.get(rel, (TODAY, TODAY))
        published = find_date(content) or first
        date = max(last, published)
        label = t["updated"] if date != published else t["published"]
    return (f'<p class="art-meta"><time datetime="{date}">{label} {date}</time><span>{minutes} {t["min_read"]}</span>'
            f'<button type="button" class="btn-ghost btn-sm share" data-copy-link>{t["share"]}</button></p>')


# ----------------------------------------------------------------- per page

def process(path: Path) -> bool:
    rel = path.relative_to(SITE).as_posix()
    if rel in SKIP_FILES or rel.startswith("_partials/"):
        return False
    url = rel_url(path)
    lang = lang_of(url)
    html = path.read_text(encoding="utf-8")
    orig = html
    # Læs **før** `SHELL_FENCE` river skalens egen blokke væk. Det var her
    # opgave 111 satte læsningen, og da var den dødfød: `content` nederst i
    # `process()` er `SHELL_FENCE.sub("", html)`, så den `art-meta` der skulle
    # fryse datoen, var væk 30 linjer ovenfor. R1 målte 99 bevægelige sider.
    frozen = shell_dates(html)
    is_devnotify = "/devnotify/" in url
    native = "pg-legacy" not in html and "data-dark-ok" in html[:400]  # pages written for the new shell

    # --- <html>: language and theme boot
    def html_tag(m):
        attrs = re.sub(r'\s*lang="[^"]*"', "", m.group(1))
        attrs = re.sub(r"\s*data-dark-ok\b", "", attrs)
        return f'<html lang="{lang}" data-dark-ok{attrs}>'
    html = re.sub(r"<html\b([^>]*)>", html_tag, html, count=1)

    # --- head: stylesheet, scripts, hreflang
    html = re.sub(r"\s*<link[^>]+/assets/site\.css[^>]*>", "", html)
    html = re.sub(r"\s*<script[^>]*/assets/site\.js[^>]*></script>", "", html)
    html = re.sub(r"\s*<script data-boot>.*?</script>", "", html, flags=re.S)
    html = html.replace("\n" + OLD_BOOT, "").replace(OLD_BOOT, "")
    html = re.sub(r"\s*<script[^>]*cloudflareinsights[^>]*></script>", "", html, flags=re.I)
    html = re.sub(r"\s*<script[^>]*/assets/checkout\.js[^>]*></script>", "", html, flags=re.I)
    html = re.sub(r"\s*<script[^>]*bugbottle[^>]*></script>", "", html, flags=re.I)
    html = re.sub(r'\s*<link[^>]+rel="alternate"[^>]+hreflang=[^>]*>', "", html)
    html = re.sub(r'\s*<link rel="preload" href="/assets/site\.css[^>]*>', "", html)
    html = seo_head(html, url, lang, rel)
    alts = alternates(url)
    if len(alts) >= 2 and "noindex" not in html[:3000]:
        tags = "".join(f'\n<link rel="alternate" hreflang="{l}" href="{ORIGIN}{u}">' for l, u in alts.items())
        tags += f'\n<link rel="alternate" hreflang="x-default" href="{ORIGIN}{alts.get("en", url)}">'
        html = re.sub(r'(<link rel="canonical"[^>]*>)', lambda m: m.group(1) + tags, html, count=1)
    html = html.replace("</head>", f'<link rel="stylesheet" href="/assets/site.css?v={CSS_V}">\n'
                        + JS_BOOT + f'\n<script src="/assets/site.js?v={JS_V}" defer></script>\n</head>', 1)

    # --- inline CSS: drop legacy shell rules, page-own widths, and map colours (not for native pages)
    if not native:
        html = re.sub(r"(<style\b[^>]*>)(.*?)(</style>)", lambda m: m.group(1) + tokenize_css(filter_css(m.group(2))) + m.group(3), html, flags=re.S | re.I)
        html = outside_code(html, clean_style_attrs)

    # --- body: remove old shell and generated blocks, insert the shared shell
    header, footer = render_shell(url, lang)
    html = re.sub(r'\s*<a class="skip"[^>]*>.*?</a>', "", html, count=1, flags=re.S)
    html = re.sub(r'\s*<nav class="fam"[^>]*>.*?</nav>', "", html, count=1, flags=re.S)
    html = re.sub(r"<header\b[^>]*>.*?</header>\s*", "", html, count=1, flags=re.S | re.I)
    html = re.sub(r"(<body\b[^>]*>)\s*<nav\b[^>]*>(?:(?!</nav>).)*?(?:← ?EUComply|&larr;|EUComply)(?:(?!</nav>).)*?</nav>\s*",
                  r"\1\n", html, count=1, flags=re.S | re.I)
    footers = list(re.finditer(r"<footer\b[^>]*>.*?</footer>\s*", html, flags=re.S | re.I))
    if footers:
        f = footers[-1]
        html = html[: f.start()] + html[f.end():]
    html = SHELL_FENCE.sub("", html)
    html = re.sub(r'<div class="pg-legacy">\n?', "", html, count=1)
    html = re.sub(r"\s*</div><!--/pg-legacy-->", "", html, count=1)
    if not native:
        had_shell_main = re.search(r"<main\b[^>]*data-shell[^>]*>\s*", html)
        if had_shell_main:
            html = html[: had_shell_main.start()] + html[had_shell_main.end():]
            last_main = html.rfind("</main>")
            if last_main >= 0:
                html = html[:last_main] + html[last_main + len("</main>"):]
        # the page's own <main> becomes a div: the shell owns <main>
        html = re.sub(r"<main\b", "<div data-legacy-main", html, flags=re.I)
        html = re.sub(r"</main>", "</div>", html, flags=re.I)
    html = re.sub(r"(<body\b[^>]*>)\s*", r"\1\n", html, count=1)
    html = re.sub(r"\s*</body>", "\n</body>", html, count=1)

    # --- layout, breadcrumbs and article furniture
    bi = html.find("<body")
    body_html = html[bi:]
    layout = layout_for(url, body_html)
    main_cls = "container" + {"wide": " layout-wide", "prose": " layout-prose"}.get(layout, "")
    title_for_crumb = PAGES.get(url, {}).get("h1") or PAGES.get(url, {}).get("title") or "EUComply"
    crumbs, crumb_ld = breadcrumbs(url, lang, title_for_crumb)
    html = re.sub(r'\s*<script type="application/ld\+json" data-shell-crumbs>.*?</script>', "", html, flags=re.S)
    if crumb_ld and "BreadcrumbList" not in existing_ld_types(html):
        html = html.replace("</head>", ld_script(crumb_ld, "data-shell-crumbs") + "\n</head>", 1)
    crumbs_block = ("\n" + fence("crumbs", crumbs)) if crumbs else ""

    if native:
        html = re.sub(r"<main\b[^>]*>", f'<main class="{main_cls}" id="main">' + crumbs_block, html, count=1)
        html = re.sub(r"(<body\b[^>]*>)", lambda m: m.group(1) + "\n" + header + "\n", html, count=1)
        html = html.replace("</body>", footer + "\n</body>", 1)
    else:
        m_body = re.search(r"<body\b[^>]*>\n", html)
        m_end = html.rfind("</body>")
        content = html[m_body.end():m_end]
        before = ""
        after = ""
        if layout == "prose":
            content, toc = heading_ids(content)
            side, details = toc_markup(toc, lang)
            art = article_meta(url, lang, rel, content, frozen) if is_article(url, content) else ""
            if art:
                h1_end = content.lower().find("</h1>")
                window_end = h1_end + 1500 if h1_end >= 0 else 3000
                head_part, tail_part = content[:window_end], content[window_end:]
                head_part = re.sub(r'\s*<(p|div)\b[^>]*class="meta"[^>]*>(?:(?!</\1>).)*?</\1>', "", head_part, count=1, flags=re.S | re.I)
                content = head_part + tail_part
                content = re.sub(r"(</h1>)", lambda m: m.group(1) + "\n" + fence("meta", art), content, count=1, flags=re.I)
            pn = prev_next(url, lang) if art else ""
            before = fence("grid", '<div class="prose-grid"><div class="prose">' + details) + "\n"
            after = (("\n" + fence("pn", pn)) if pn else "") + "\n" + fence("grid-end", "</div>" + side + "</div>")
        html = (html[: m_body.end()] + header + f'\n<main class="{main_cls}" id="main" data-shell>' + crumbs_block + "\n"
                + before + '<div class="pg-legacy">\n' + content.strip("\n") + "\n</div><!--/pg-legacy-->" + after
                + "\n</main>\n" + footer + "\n" + html[m_end:])

    # --- BugBottle on every page, right before </body>
    bb = (f'<script src="{BUGBOTTLE_SRC}" data-endpoint="{BUGBOTTLE_ENDPOINT}" data-locale="{lang}" '
          f'data-primary="{ACCENT}" data-brand="EUComply" data-position="bottom-right" data-scrub defer></script>')
    html = html.replace("\n</body>", "\n" + bb + "\n</body>", 1)

    # --- cross-cutting clean-up
    html = html.replace("auditedwp.pages.dev", "eucomplypro.com")
    sticky_col = strip_lang(url).startswith(("/vs/", "/compare/", "/cmp-comparison/", "/deskuptime/vs/", "/devnotify/vs/", "/pro/vs-"))
    html = outside_code(html, lambda s: wrap_tables(s, sticky_col))
    html = outside_code(html, add_missing_alt)
    html = outside_code(html, lazy_images)
    html = outside_code(html, aria_live_results)
    if not is_devnotify and not native:
        def clean(txt):
            # Emoji'en markeres, det dobbelte mellemrum den efterlod renses, og
            # først så fjernes markøren. Det skal ske i den rækkefølge: renses
            # alle "  " på én gang, ødelægger den indrykning af markupket — to
            # mellemrum foran `<div>` er ikke et dobbelt mellemrum i løbende
            # tekst, det er en ny linje. Kun mellemrum umiddelbart efter en
            # fjernet emoji må renses, og det er de markeren gør mulige.
            txt = re.sub(EMOJI.pattern, "\x00", txt)
            txt = re.sub(r"\x00 +", "\x00", txt)
            txt = txt.replace("\x00", "")
            for pat, rep in HYPE:
                txt = pat.sub(rep, txt)
            return txt.replace("AuditedWP", "EUComply")
        html = outside_code(html, clean)
        html = outside_code(html, strip_social_proof)
        html = strip_waitlist_forms(html, lang)
        html = neutralise_buy_buttons(html, lang)
        html = fix_generator_links(html, lang)
        html = product_ctas(html, url)
        # Proscerydende mellemrum efter en tag fjernes, fordi legacy-siderne
        # har `<p>\n  tekst`. Elementer med `style=` springes over: en inline
        # span med vilkårligt forholdsrum er sat med vilje for at aligninge i
        # en celle, og det er præcis sådan prøverapportens datoer er sat op.
        html = re.sub(r'(<(h[1-6]|p|li|span|strong|b|td|th|a)\b(?:(?!style=)[^>])*>)\s+(?=\S)', r"\1", html)
    elif native:
        html = fix_generator_links(html, lang)

    if html != orig and not DRY:
        path.write_text(html, encoding="utf-8")
    return html != orig


# ------------------------------------------------------------- search pages

SEARCH_TPL = """<!DOCTYPE html>
<html lang="{lang}" data-dark-ok>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — EUComply</title>
<meta name="description" content="{desc}">
<meta name="robots" content="noindex,follow">
</head>
<body>
<main>
  <section class="pg-narrow hero srch">
    <h1>{title}</h1>
    <p class="lede">{lede}</p>
    <form class="srch-form" action="{action}" method="get" role="search">
      <input type="search" id="srch-q" name="q" placeholder="{placeholder}" aria-label="{label}" autocomplete="off" autofocus>
      <button class="btn" type="submit">{button}</button>
    </form>
    <p class="srch-status" id="srch-status" aria-live="polite"></p>
    <ul class="srch-list" id="srch-results"></ul>
    <noscript><p>{noscript} <a href="/sitemap.xml">sitemap.xml</a></p></noscript>
  </section>
</main>
</body>
</html>
"""


def ensure_search_pages():
    for lang in LANGS:
        t = I18N[lang]
        d = SITE / ("search" if lang == "en" else f"{lang}/search")
        d.mkdir(parents=True, exist_ok=True)
        page = SEARCH_TPL.format(lang=lang, title=t["search_title"], desc=attr_escape(t["search_desc"]), lede=t["search_lede"],
                                 action=("/search/" if lang == "en" else f"/{lang}/search/"), placeholder=attr_escape(t["search_placeholder"]),
                                 label=attr_escape(t["search_label"]), button=t["search_button"], noscript=t["search_noscript"])
        f = d / "index.html"
        # Rewrite from the template only when the shell has not been applied yet (keeps the run idempotent).
        if not f.exists() or "data-boot" not in f.read_text(encoding="utf-8"):
            f.write_text(page, encoding="utf-8")


# ------------------------------------------------------------- search index

def section_for(url: str) -> str:
    base = strip_lang(url).strip("/").split("/")
    seg = base[0] if base else ""
    if seg == "blog":
        return "blog"
    if seg == "guides":
        return "guides"
    if seg in ("checklist", "nis2-checklist", "eaa-checklist"):
        return "checklists"
    if seg in ("vs", "compare", "cmp-comparison"):
        return "compare"
    if seg in ("deskuptime", "devnotify", "transmute", "store", "pro"):
        return seg
    if seg in ("scan", "regex", "cli", "extension", "plugin", "badge", "gdpr-fine-calculator", "gdpr-scanner-free",
               "check-eu-compliance") or seg.endswith(("-check", "-checker")):
        return "tools"
    return "pages"


def build_search_index() -> int:
    items = []
    for p in sorted(SITE.rglob("*.html")):
        rel = p.relative_to(SITE).as_posix()
        if rel in SKIP_FILES or rel.startswith("_partials/") or rel == "404.html" or not rel.endswith("index.html"):
            continue
        if rel.split("/")[0] in GENERATORS or rel_url(p) in CANONICAL_OVERRIDES:
            continue
        html = p.read_text(encoding="utf-8")
        if re.search(r'name="robots"[^>]*noindex', html[:4000]):
            continue
        url = rel_url(p)
        mi = html.find("<main")
        main = html[mi: html.rfind("</main>")] if mi >= 0 else html
        main = SHELL_FENCE.sub(" ", main)
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", main, re.S)
        text = text_of(main[h1.end():] if h1 else main)
        tm = re.search(r"<title>(.*?)</title>", html, re.S)
        tags = [s for s in strip_lang(url).strip("/").split("/")[:-1] if s]
        items.append({"url": url, "title": htmlmod.unescape(tm.group(1)) if tm else text_of(h1.group(1)) if h1 else url,
                      "description": find_meta(html, "name", "description") or "",
                      "lang": lang_of(url), "section": section_for(url), "body": text[:400], "tags": tags})
    (SITE / "search-index.json").write_text(json.dumps(items, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return len(items)


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
        if not rel.endswith("index.html") or rel_url(p) in CANONICAL_OVERRIDES:
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
    if not DRY:
        ensure_search_pages()
    catalogue()
    changed = 0
    total = 0
    for p in sorted(SITE.rglob("*.html")):
        if "_partials" in p.parts:
            continue
        total += 1
        if process(p):
            changed += 1
    n = build_sitemap() if not DRY else 0
    s = build_search_index() if not DRY else 0
    print(f"pages: {total}, changed: {changed}, sitemap urls: {n}, search index: {s}")


if __name__ == "__main__":
    main()
