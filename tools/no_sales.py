#!/usr/bin/env python3
"""Fælles definition af "intet købsspor" på eucomplypro.com.

Ejeren besluttede 22/11-2026 at fryse EUComply som gratis open source. Pro,
skabelonerne og e-bog-bundlet sælges ikke længere, og Stripe-linkene er
deaktiveret. Før den dag dømte portene i `tools/` at en købsvej FANDTES: ét
Stripe-link pr. salgsside, en pris der matchede kontrakten, en knap der kunne
trykkes. Fra den dag er sandheden den modsatte, og portene skal være
spejlbilledet: de skal være RØDE hvis et købsspor dukker op igen, og de må ikke
kræve et.

Dette modul er den ene definition af et købsspor. `check_cta.py`,
`check_pro_claims.py`, `check_buy_path.py`, `check_store_ready.py` og
`check_public_tree.py` bruger den, så de ikke kan blive uenige om hvad "lukket"
betyder. En definition pr. gate var præcis hvordan de gamle porte endte med
fire ordforråd for samme ting.

Et træ er lukket når:

  1. Ingen fil rummer et betalingslink (`buy.stripe.com`, `checkout.stripe.com`,
     Lemon Squeezy, Gumroad, Paddle). Donationslinket og Page Profile Pro-linket
     er undtaget, fordi de ikke er en del af EUComply (se ALLOWED_PAYMENT_LINKS).
  2. Ingen tekst, metabeskrivelse eller JSON-LD nævner en pris for Pro, en
     skabelon eller e-bog-bundlet (PRICE_NUMBERS i en valuta).
  3. Intet linker til de lukkede stier (`/pricing/`, `/pro/`, `/store/`, `/vs/`,
     også med sprogpræfiks) hverken i navigation, footer, brødtekst, sitemap,
     canonical eller `llms*.txt`.
  4. Al JSON-LD `offers` har price 0.
  5. Ingen knap eller link beder en læser købe ("Buy", "Køb", "Kaufen",
     "Acheter", "Upgrade to Pro").
  6. "Pro" nævnes kun som noget der ikke længere sælges eller som eksisterende
     licenser der stadig virker, og aldrig i en sætning der sælger det.
  7. De lukkede sider findes ikke, og hver sti har en 301 i `_redirects` til en
     side der findes.
  8. Forsiden på alle fire sprog har `id="frozen-notice"`, og den engelske
     siger `frozen as free open source`.
  9. README nævner "frozen" og "2026-11-22", og LICENSE er MIT 2026 Mahope.

Selvtesten sætter hver af de ni ind i et ellers rent fixture-træ og kræver rød,
og kræver at det rene træ er grønt. En port der ikke kan blive rød er ikke en
port.

Brug:
    python3 tools/no_sales.py --selftest
    python3 tools/no_sales.py [træ ...]      # standard: site/ og site-dist/
"""

from __future__ import annotations

import html
import json
import re
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
CLOSED_ON = "2026-11-22"
LOCALES = ("da", "de", "fr")
SITE_LOCALES = ("da", "de", "fr", "es")

# ---------------------------------------------------------------------------
# 1. Betalingslinks
# ---------------------------------------------------------------------------
DONATION_LINK = "https://donate.stripe.com/7sYeVcbn50wieFM8gDbMQ0c"
# Page Profile Pro er et andet produkt i et andet repo, og er ikke omfattet af
# frysningen (ejerens beslutning 22/11-2026). Linket må derfor stå, hvor det
# står; porten dømmer ikke et produkt den ikke ejer.
PAGE_PROFILE_PRO_ID = "9B6eVcgHp7YK69ggN9bMQ04"
ALLOWED_PAYMENT_IDS = frozenset({"7sYeVcbn50wieFM8gDbMQ0c", PAGE_PROFILE_PRO_ID})
ALLOWED_PAYMENT_LINKS = frozenset({
    DONATION_LINK, f"https://buy.stripe.com/{PAGE_PROFILE_PRO_ID}",
})

CHECKOUT_RE = re.compile(
    r"(?:https?://)?(?:"
    r"(?P<stripe>(?:buy|checkout|donate)\.stripe\.com)/(?P<id>[A-Za-z0-9_/-]+)"
    r"|[a-z0-9-]+\.lemonsqueezy\.com/[A-Za-z0-9_/-]*"
    r"|(?:[a-z0-9-]+\.)?gumroad\.com/l/[A-Za-z0-9_-]+"
    r"|(?:buy|checkout|pay)\.paddle\.com/[A-Za-z0-9_/-]*"
    r")",
    re.I,
)


def checkout_links(text: str) -> List[str]:
    """Betalingslinks i en tekst, undtagen de to der må blive."""
    found: List[str] = []
    for match in CHECKOUT_RE.finditer(text):
        if match.group("stripe"):
            identifier = match.group("id").split("/")[0]
            if identifier in ALLOWED_PAYMENT_IDS:
                continue
        found.append(match.group(0).rstrip(".,;)"))
    return found


# ---------------------------------------------------------------------------
# 2. Priser
# ---------------------------------------------------------------------------
# Pro 79 (år) og 149 (lifetime), skabeloner 29/39/49/59/69/149, e-bog-bundle 29.
# 6.58 er 79/12, den månedlige omregning kontrakten brugte, og 14.99 var den
# gamle e-bogspris. Begge var en pris på siden og er det ikke længere.
PRICE_NUMBERS = ("149", "79", "69", "59", "49", "39", "29", "14.99", "6.58")
_NUM = "(?:" + "|".join(re.escape(n) for n in PRICE_NUMBERS) + ")"
_CUR_BEFORE = r"(?:US\$|\$|USD\s?|EUR\s?|€|DKK\s?|kr\.?\s?)"
_CUR_AFTER = r"(?:\s?(?:USD|US\$|\$|dollars?|EUR|€|DKK|kr\b\.?))"
PRICE_RE = re.compile(
    rf"(?<![\w.,/])(?:{_CUR_BEFORE}\s?{_NUM}(?![\d])(?![.,]\d)(?:[.,]00)?"
    rf"|{_NUM}(?:[.,]00)?{_CUR_AFTER}(?![\w]))",
    re.I,
)


def price_hits(text: str) -> List[str]:
    return [m.group(0).strip() for m in PRICE_RE.finditer(text)]


# ---------------------------------------------------------------------------
# 3. Lukkede stier
# ---------------------------------------------------------------------------
REMOVED_ROOTS = ("pricing", "pro", "store", "vs")
REMOVED_LINK_RE = re.compile(
    r"(?<![\w/.-])(?:https?://(?:www\.)?eucomplypro\.com)?"
    r"/(?:(?:" + "|".join(SITE_LOCALES) + r")/)?"
    r"(?:" + "|".join(REMOVED_ROOTS) + r")(?=[/?#\"'\s)<>\]]|$)",
    re.I,
)

# De sider der blev slettet, og som `_redirects` skal sende videre. Rod-stierne
# kræver en egen linje (med og uden skråstreg); undersiderne må dækkes af en
# splat-linje (`/pro/*`), som Cloudflare Pages forstår.
REMOVED_TOP = (
    "/pricing/", "/da/pricing/", "/de/pricing/", "/fr/pricing/",
    "/pro/", "/da/pro/", "/de/pro/", "/fr/pro/",
    "/store/", "/vs/",
)
REMOVED_SUB = (
    "/pro/dashboard/", "/pro/sample-report/", "/pro/thank-you/",
    "/pro/vs-cookiebot/", "/pro/vs-iubenda/", "/pro/vs-onetrust/",
    "/pro/vs-osano/", "/pro/vs-termly/",
    "/store/dpa/", "/store/eaa-statement/", "/store/nda-clauses/",
    "/store/nis2-clauses/", "/store/report-kit/",
    "/vs/complianz/", "/vs/cookiebot/", "/vs/enzuzo/", "/vs/iubenda/",
    "/vs/onetrust/", "/vs/osano/", "/vs/termly/", "/vs/usercentrics/",
)
REMOVED_OG_IMAGES = (
    "images/og/pricing.png", "images/og/da-pricing.png",
    "images/og/de-pricing.png", "images/og/fr-pricing.png",
    "images/og/store.png", "images/og/pro.png",
)


def removed_links(text: str) -> List[str]:
    return [m.group(0) for m in REMOVED_LINK_RE.finditer(text)]


# ---------------------------------------------------------------------------
# 4. JSON-LD offers
# ---------------------------------------------------------------------------
LDJSON_RE = re.compile(
    r"<script\b[^>]*\btype=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
    re.I | re.S,
)
PRICE_KEYS = ("price", "lowPrice", "highPrice")


def _is_zero(value: object) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return value == 0
    if isinstance(value, str):
        return value.strip() in ("0", "0.0", "0.00")
    return False


def _prices_under(node: object) -> List[object]:
    found: List[object] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key in PRICE_KEYS:
                found.append(value)
            else:
                found.extend(_prices_under(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_prices_under(item))
    return found


def _offer_nodes(node: object) -> Iterable[dict]:
    if isinstance(node, dict):
        kinds = node.get("@type")
        kinds = kinds if isinstance(kinds, list) else [kinds]
        if any(k in ("Offer", "AggregateOffer") for k in kinds if isinstance(k, str)):
            yield node
        elif "offers" in node:
            offers = node["offers"]
            for offer in offers if isinstance(offers, list) else [offers]:
                if isinstance(offer, dict):
                    yield offer
        for value in node.values():
            if isinstance(value, (dict, list)):
                yield from _offer_nodes(value)
    elif isinstance(node, list):
        for item in node:
            yield from _offer_nodes(item)


def offers_findings(rel: str, text: str) -> List[str]:
    """Al JSON-LD `offers` skal have price 0, og et tilbud uden price er ikke bevist 0."""
    findings: List[str] = []
    for raw in LDJSON_RE.findall(text):
        try:
            data = json.loads(html.unescape(raw))
        except ValueError:
            continue  # ugyldig JSON-LD dømmes af en anden port
        seen = set()
        for offer in _offer_nodes(data):
            if id(offer) in seen:
                continue
            seen.add(id(offer))
            prices = _prices_under(offer)
            if not prices:
                findings.append(f"{rel}: JSON-LD offers uden price — kun price 0 kan stå, og her er intet bevist")
            for price in prices:
                if not _is_zero(price):
                    findings.append(f"{rel}: JSON-LD offers med price {price!r} — salget er lukket, kun price 0 må stå")
    return findings


# ---------------------------------------------------------------------------
# 5. Købsknapper
# ---------------------------------------------------------------------------
ANCHOR_RE = re.compile(r"<(a|button)\b([^>]*)>(.*?)</\1>", re.I | re.S)
HREF_ATTR_RE = re.compile(r"""\bhref\s*=\s*["']([^"']*)["']""", re.I)
BUY_TEXT_RE = re.compile(
    r"^\W*(?:buy|purchase|order|k[øo]b|kaufen|jetzt\s+kaufen|acheter|comprar)\b"
    r"|\b(?:upgrade|opgrader|upgraden|passer)\b.{0,20}\bPro\b"
    r"|^\W*(?:see|view|get|go|try|se|hent|vis|ansehen|voir)\s+(?:EUComply\s+)?Pro\b"
    r"|\bPro\s+(?:kaufen|ansehen|acheter|k[øo]b\w*)\b",
    re.I,
)


def _plain(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def buy_buttons(text: str) -> List[str]:
    found: List[str] = []
    for match in ANCHOR_RE.finditer(text):
        label = _plain(match.group(3))
        href = HREF_ATTR_RE.search(match.group(2))
        if href and any(href.group(1).startswith(link) for link in ALLOWED_PAYMENT_LINKS):
            continue
        if label and BUY_TEXT_RE.search(label):
            found.append(label[:60])
    return found


# ---------------------------------------------------------------------------
# 6. "Pro" kun som lukket
# ---------------------------------------------------------------------------
PRO_NAME_RE = re.compile(
    r"\bEUComply\s+Pro\b"
    r"|\bPro[\s-]+(?:licen[cs]es?|licens\w*|Lizenz\w*|plan|plugin|version|upgrade|abonnement)\b"
    r"|\b(?:licen[cs]e|licens|Lizenz)\s+Pro\b",
    re.I,
)
CLOSURE_RE = re.compile(
    r"no\s+longer\s+(?:sold|for\s+sale|offered|available)"
    r"|not\s+sold\s+(?:any\s?more|anymore)"
    r"|s[æe]lges\s+ikke\s+l[æe]ngere|ikke\s+l[æe]ngere\s+til\s+salg"
    r"|nicht\s+mehr\s+(?:verkauft|erh[äa]ltlich)|wird\s+nicht\s+mehr\s+verkauft"
    r"|n['’]est\s+plus\s+(?:vendu|commercialis[ée])|ne\s+se\s+vend\s+plus"
    r"|ya\s+no\s+se\s+vende"
    r"|existing\s+licen[cs]es?|eksisterende\s+licenser|bestehende\s+Lizenzen"
    r"|licences?\s+existantes?"
    r"|frozen\s+as\s+free\s+open\s+source|frosset|eingefroren|gel[ée]e?\b",
    re.I,
)
SELL_RE = re.compile(
    r"\b(?:buy|buying|purchase[sd]?|pricing|price[sd]?|costs?|upgrade[sd]?|unlock\w*|"
    r"per\s+(?:year|website|site)|a\s+year|annual\w*|subscri\w+|lifetime|one-time|checkout|"
    r"k[øo]b\w*|pris\w*|opgrad\w*|årlig\w*|abonnement\w*|kauf\w*|preis\w*|jahr\w*|"
    r"acheter|achat\w*|prix|tarif\w*|annuel\w*)\b|/\s*year|/\s*år",
    re.I,
)
_VOID = frozenset("area base br col embed hr img input link meta param source track wbr".split())
_SKIP = frozenset({"script", "style", "noscript", "template"})
_BLOCK = frozenset(
    "address article aside blockquote body dd details div dl dt fieldset figcaption figure "
    "footer form h1 h2 h3 h4 h5 h6 header hr li main nav ol p section summary table tbody "
    "td tfoot th thead tr ul button".split()
)


class _Collector(HTMLParser):
    """Samler synlige tekstblokke og teksten under hvert element med et id."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: List[str] = []
        self.ids: Dict[str, str] = {}
        self._buffer: List[str] = []
        self._skip = 0
        self._stack: List[Tuple[str, Optional[str]]] = []

    def _flush(self) -> None:
        text = re.sub(r"\s+", " ", "".join(self._buffer)).strip()
        if text:
            self.blocks.append(text)
        self._buffer = []

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP:
            self._skip += 1
            return
        if tag in _BLOCK:
            self._flush()
        if tag in _VOID:
            return
        self._stack.append((tag, dict(attrs).get("id")))
        element_id = dict(attrs).get("id")
        if element_id:
            self.ids.setdefault(element_id, "")

    def handle_endtag(self, tag):
        if tag in _SKIP:
            self._skip = max(0, self._skip - 1)
            return
        if tag in _BLOCK:
            self._flush()
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index][0] == tag:
                del self._stack[index:]
                break

    def handle_data(self, data):
        if self._skip:
            return
        self._buffer.append(data)
        for _tag, element_id in self._stack:
            if element_id:
                self.ids[element_id] = self.ids.get(element_id, "") + " " + data

    def close(self) -> None:
        super().close()
        self._flush()


def parse_blocks(text: str) -> _Collector:
    collector = _Collector()
    collector.feed(text)
    collector.close()
    return collector


def pro_findings(rel: str, blocks: List[str]) -> List[str]:
    """Pro må kun nævnes som lukket, og aldrig i en sætning der sælger det."""
    findings: List[str] = []
    names_pro = False
    for block in blocks:
        if not PRO_NAME_RE.search(block):
            continue
        names_pro = True
        if SELL_RE.search(block) and not CLOSURE_RE.search(block):
            findings.append(f"{rel}: sælger Pro ({SELL_RE.search(block).group(0)!r}) uden at sige at det ikke sælges længere: {block[:90]}")
    if names_pro and not any(CLOSURE_RE.search(block) for block in blocks):
        findings.append(f"{rel}: nævner Pro, men siger intet sted at det ikke sælges længere eller at eksisterende licenser virker")
    return findings


# ---------------------------------------------------------------------------
# Én fil
# ---------------------------------------------------------------------------
_NON_LD_SCRIPT_RE = re.compile(
    r"<script\b(?![^>]*application/ld\+json)[^>]*>.*?</script>|<style\b[^>]*>.*?</style>",
    re.I | re.S,
)


# DevNotify er et søskendeprodukt, der ikke er omfattet af frysningen: ejeren
# lukkede Clean Copy, DeskUptime og Transmute og lod DevNotify stå. Dets egen
# købsknap og JSON-LD-pris er derfor ikke et købsspor. Betalingslink og links til
# EUComplys lukkede stier dømmes stadig, for dem ejer DevNotify ikke.
OPEN_SIBLINGS = ("devnotify",)


def is_open_sibling(rel: str) -> bool:
    parts = rel.split("/")
    if parts and parts[0] in SITE_LOCALES:
        parts = parts[1:]
    return bool(parts) and parts[0] in OPEN_SIBLINGS


def scan_text(rel: str, text: str, kind: str) -> List[str]:
    """Dom én fils tekst. `kind` er html, text (llms, xml, json) eller js."""
    findings: List[str] = []
    for link in checkout_links(text):
        findings.append(f"{rel}: betalingslink {link} — salget er lukket")
    for link in sorted(set(removed_links(text))):
        findings.append(f"{rel}: link til den lukkede side {link}")
    if kind == "js" or is_open_sibling(rel):
        return findings
    priced = _NON_LD_SCRIPT_RE.sub(" ", text) if kind == "html" else text
    for hit in sorted(set(price_hits(priced))):
        findings.append(f"{rel}: pris {hit!r} — Pro, skabeloner og e-bog-bundle har ingen pris mere")
    if kind == "html":
        findings.extend(offers_findings(rel, text))
        for label in buy_buttons(text):
            findings.append(f"{rel}: købsknap {label!r}")
        findings.extend(pro_findings(rel, parse_blocks(text).blocks))
    elif kind == "text":
        lines = [line for line in text.splitlines() if line.strip()]
        if rel.endswith(".txt"):
            findings.extend(pro_findings(rel, lines))
    return findings


# ---------------------------------------------------------------------------
# Redirects og lukkede sider
# ---------------------------------------------------------------------------
def parse_redirects(text: str) -> List[Tuple[str, str, str]]:
    rules: List[Tuple[str, str, str]] = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 2 or parts[0].startswith("#"):
            continue
        rules.append((parts[0], parts[1], parts[2] if len(parts) > 2 else "302"))
    return rules


def _rule_for(path: str, rules: List[Tuple[str, str, str]]) -> Optional[Tuple[str, str, str]]:
    bare = path.rstrip("/")
    for source, target, status in rules:
        if source in (path, bare):
            return source, target, status
    for source, target, status in rules:
        if source.endswith("/*") and path.startswith(source[:-1]):
            return source, target, status
    return None


def _page_exists(base: Path, target: str) -> bool:
    clean = target.split("#")[0].split("?")[0]
    if not clean.startswith("/") or clean.startswith("//"):
        return False
    relative = clean.lstrip("/")
    if relative == "" or clean.endswith("/"):
        return (base / relative / "index.html").is_file()
    return (base / relative).is_file() or (base / relative / "index.html").is_file()


def removed_page_findings(base: Path) -> List[str]:
    """De lukkede sider er væk, og hver sti har en 301 til en side der findes."""
    findings: List[str] = []
    for path in REMOVED_TOP + REMOVED_SUB:
        if (base / path.strip("/") / "index.html").is_file():
            findings.append(f"{path.strip('/')}/index.html findes stadig — siden er lukket 22/11-2026 og skal være slettet")
    for image in REMOVED_OG_IMAGES:
        if (base / image).is_file():
            findings.append(f"{image} findes stadig — billedet hører til en lukket side")
    redirects = base / "_redirects"
    if not redirects.is_file():
        findings.append("_redirects mangler — de lukkede stier har ingen 301")
        return findings
    rules = parse_redirects(redirects.read_text(encoding="utf-8", errors="replace"))
    for path in REMOVED_TOP + REMOVED_SUB:
        rule = _rule_for(path, rules)
        if rule is None:
            findings.append(f"_redirects: {path} har ingen 301 — et gammelt link eller en søgemaskine får 404")
            continue
        source, target, status = rule
        if status != "301":
            findings.append(f"_redirects: {source} er {status}, ikke 301 — lukningen er permanent")
        elif removed_links(target):
            findings.append(f"_redirects: {source} peger på {target}, en anden lukket side")
        elif not _page_exists(base, target):
            findings.append(f"_redirects: {source} peger på {target}, som ikke findes")
    return findings


# ---------------------------------------------------------------------------
# Forsidens frys-note, README og LICENSE
# ---------------------------------------------------------------------------
FROZEN_PHRASE = "frozen as free open source"
HOME_PAGES = (("index.html", "en"),) + tuple((f"{loc}/index.html", loc) for loc in LOCALES)


def frozen_notice_findings(base: Path) -> List[str]:
    findings: List[str] = []
    for rel, language in HOME_PAGES:
        path = base / rel
        if not path.is_file():
            findings.append(f"{rel}: forsiden mangler")
            continue
        notice = parse_blocks(path.read_text(encoding="utf-8", errors="replace")).ids.get("frozen-notice")
        if notice is None:
            findings.append(f'{rel}: mangler elementet id="frozen-notice" — forsiden siger ikke at EUComply er frosset')
            continue
        text = re.sub(r"\s+", " ", notice).strip()
        if language == "en" and FROZEN_PHRASE not in text.lower():
            findings.append(f'{rel}: id="frozen-notice" siger ikke "{FROZEN_PHRASE}"')
        elif len(text) < 40:
            findings.append(f'{rel}: id="frozen-notice" er tomt eller for kort til at være en meddelelse')
    return findings


def repo_file_findings(root: Path) -> List[str]:
    findings: List[str] = []
    readme = root / "README.md"
    if not readme.is_file():
        findings.append("README.md mangler")
    else:
        text = readme.read_text(encoding="utf-8", errors="replace")
        if "frozen" not in text.lower():
            findings.append('README.md nævner ikke "frozen" — frys-linjen mangler øverst')
        if CLOSED_ON not in text:
            findings.append(f"README.md nævner ikke datoen {CLOSED_ON}")
    licence = root / "LICENSE"
    if not licence.is_file():
        findings.append("LICENSE mangler — gratis open source uden licens er ikke open source")
    else:
        text = licence.read_text(encoding="utf-8", errors="replace")
        if "MIT License" not in text:
            findings.append('LICENSE er ikke MIT ("MIT License" mangler)')
        if "2026 Mahope" not in text:
            findings.append('LICENSE nævner ikke "2026 Mahope"')
    return findings


# ---------------------------------------------------------------------------
# Et helt træ
# ---------------------------------------------------------------------------
SCANNED = {".html": "html", ".txt": "text", ".xml": "text", ".json": "text",
           ".svg": "text", ".webmanifest": "text", ".js": "js"}
# `_partials` er med: header og footer bærer navigationen, og et "Pricing"-link
# dér ender på hver eneste side.
INTERNAL_PARTS = frozenset({"POSTS", "ops", "deliverables", "gumroad", "__pycache__",
                            "node_modules", ".deploy-staging"})
# Kildekopier af pluginet. De er byte-identiske med plugin/ og må ikke ændres
# uden en plugin-udgivelse (versionsbump, zip, paritetskontrol), så de er
# undtaget med vilje. Alt andet i træet er ikke.
#
# `update.json` er undtaget af samme grund: den er byte-identisk med `update.json`
# i roden (paritet dømmes af check_pro_claims.artifact_findings), pluginets
# auto-opdatering læser den, og dens changelog er historik om hvad tidligere
# udgaver kostede. Ændres den, kræver det en plugin-udgivelse.
EXEMPT_FILES = frozenset({"plugin/eucomply.php", "plugin/readme.txt", "update.json"})


def tree_files(base: Path) -> List[Path]:
    files = []
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SCANNED:
            continue
        rel = path.relative_to(base)
        if rel.as_posix() in EXEMPT_FILES or INTERNAL_PARTS & set(rel.parts[:-1]):
            continue
        files.append(path)
    return files


def scan_tree(base: Path, *, label: str = "") -> List[str]:
    """Hele træet: indhold, lukkede sider, redirects og forsidernes frys-note."""
    prefix = f"{label}/" if label else ""
    findings: List[str] = []
    for path in tree_files(base):
        rel = path.relative_to(base).as_posix()
        if rel == "_redirects":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for finding in scan_text(rel, text, SCANNED[path.suffix.lower()]):
            findings.append(prefix + finding)
    for finding in removed_page_findings(base) + frozen_notice_findings(base):
        findings.append(prefix + finding)
    return findings


# ---------------------------------------------------------------------------
# Selvtest
# ---------------------------------------------------------------------------
NOTICE_EN = (
    "EUComply is frozen as free open source as of 22 November 2026. The free scanner "
    "and CLI (@mahope/eucomply-scanner) and the free guides and e-books stay; Pro is "
    "no longer sold; existing licences keep working."
)


def _home(language: str, extra: str = "", notice: Optional[str] = None) -> str:
    text = notice if notice is not None else (
        NOTICE_EN if language == "en" else f"EUComply er frosset ({language}) som gratis open source pr. 22/11-2026.")
    return (
        '<!doctype html><html><head><title>EUComply</title></head><body><main>'
        f'<div id="frozen-notice"><p>{text}</p></div>'
        f"<p>Free scanner.</p>{extra}</main></body></html>"
    )


def _fixture(root: Path) -> None:
    files = {
        "index.html": _home("en"),
        "da/index.html": _home("da"),
        "de/index.html": _home("de"),
        "fr/index.html": _home("fr"),
        "scan/index.html": "<html><body><main><h1>Scan</h1><p>Free scan.</p></main></body></html>",
        "llms.txt": "# EUComply\n- [Scan](/scan/)\nPro is no longer sold.\n",
        "sitemap.xml": "<urlset><url><loc>https://eucomplypro.com/scan/</loc></url></urlset>",
        "plugin/readme.txt": "Buy Pro: https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03 for $79\n",
        "assets/site.js": "const x = 1;\n",
    }
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    lines = [f"{p} /scan/ 301" for p in REMOVED_TOP + tuple(p.rstrip("/") for p in REMOVED_TOP)]
    lines += ["/pro/* /scan/ 301", "/store/* /scan/ 301", "/vs/* /scan/ 301"]
    (root / "_redirects").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (root / "README.md").write_text("> Frozen as of 2026-11-22.\n", encoding="utf-8")
    (root / "LICENSE").write_text("MIT License\n\nCopyright (c) 2026 Mahope\n", encoding="utf-8")


def selftest() -> int:
    failures: List[str] = []
    count = 0

    def fixture() -> Path:
        directory = Path(tempfile.mkdtemp(prefix="no-sales-"))
        _fixture(directory)
        return directory

    def findings_of(root: Path) -> List[str]:
        return scan_tree(root) + repo_file_findings(root)

    def put(root: Path, rel: str, text: str) -> None:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def expect(name: str, root: Path, needle: str) -> None:
        nonlocal count
        count += 1
        found = findings_of(root)
        if not any(needle in item for item in found):
            failures.append(f"{name}: forventede et fund med {needle!r}, fik {found[:3]}")

    def expect_green(name: str, root: Path) -> None:
        nonlocal count
        count += 1
        found = findings_of(root)
        if found:
            failures.append(f"{name}: skulle være grøn, fik {found[:3]}")

    expect_green("rent træ er grønt", fixture())

    root = fixture()
    put(root, "scan/index.html", '<main><p>Pay <a href="https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03">here</a>.</p></main>')
    expect("buy.stripe.com-link", root, "betalingslink")

    root = fixture()
    put(root, "scan/index.html", '<main><a href="https://buy.stripe.com/28E5kC3UDcf0btA2WjbMQ0f">x</a></main>')
    expect("lifetime-linket", root, "betalingslink")

    root = fixture()
    put(root, "scan/index.html", '<main><a href="https://buy.stripe.com/bJe7sK8aT4My7dk7czbMQ05">x</a></main>')
    expect("skabelon-linket", root, "betalingslink")

    root = fixture()
    put(root, "assets/site.js", "location = 'https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03';\n")
    expect("betalingslink i JavaScript", root, "betalingslink")

    root = fixture()
    put(root, "scan/index.html", f'<main><a href="{DONATION_LINK}">Support open source</a>'
        f'<a href="https://buy.stripe.com/{PAGE_PROFILE_PRO_ID}">Page Profile Pro</a></main>')
    expect_green("donation og Page Profile Pro må stå", root)

    for name, text, needle in (
        ("pris i dollar-tegn", "<p>$79 a year.</p>", "pris"),
        ("pris i USD", "<p>79 USD per website.</p>", "pris"),
        ("lifetime-pris", "<p>One payment of 149 USD.</p>", "pris"),
        ("skabelonpris", "<p>The DPA template costs $59.</p>", "pris"),
        ("e-bog-bundle-pris", "<p>The e-book bundle is $29.</p>", "pris"),
        ("pris i metabeskrivelse", '<meta name="description" content="Pro from $49 a year">', "pris"),
        ("pris i euro", "<p>Only €79.</p>", "pris"),
    ):
        root = fixture()
        put(root, "scan/index.html", f"<html><head></head><body><main>{text}</main></body></html>")
        expect(name, root, needle)

    root = fixture()
    put(root, "scan/index.html", "<main><p>Fines reach 4% of turnover or €20 million, 79 pages, $790.</p></main>")
    expect_green("tal uden for prislisten og uden valuta er ikke priser", root)

    for name, link in (
        ("link til /pricing/", '<a href="/pricing/">Pricing</a>'),
        ("link til /da/pro/", '<a href="/da/pro/">Pro</a>'),
        ("link til /store/dpa/", '<a href="/store/dpa/">DPA</a>'),
        ("link til /vs/termly/", '<a href="/vs/termly/">vs</a>'),
        ("absolut link til /pro/", '<a href="https://eucomplypro.com/pro/">Pro</a>'),
    ):
        root = fixture()
        put(root, "scan/index.html", f"<main>{link}</main>")
        expect(name, root, "lukkede side")

    root = fixture()
    put(root, "scan/index.html", '<main><a href="/deskuptime/pricing/x/">sibling</a><a href="/provider/">p</a></main>')
    expect_green("sibling-stier der bare indeholder pro/pricing er ikke lukkede stier", root)

    root = fixture()
    put(root, "llms.txt", "# EUComply\n- [Pricing](/pricing/)\n")
    expect("llms.txt linker /pricing/", root, "lukkede side")

    root = fixture()
    put(root, "sitemap.xml", "<urlset><url><loc>https://eucomplypro.com/pro/</loc></url></urlset>")
    expect("sitemap lister /pro/", root, "lukkede side")

    ld = '<script type="application/ld+json">{offers}</script>'
    root = fixture()
    put(root, "scan/index.html", "<main>" + ld.replace("{offers}", '{"@type":"Product","offers":{"@type":"Offer","price":"79","priceCurrency":"USD"}}') + "</main>")
    expect("offers med price 79", root, "price '79'")

    root = fixture()
    put(root, "scan/index.html", "<main>" + ld.replace("{offers}", '{"@type":"SoftwareApplication","offers":{"@type":"Offer","price":0,"priceCurrency":"USD"}}') + "</main>")
    expect_green("offers med price 0 er grøn", root)

    root = fixture()
    put(root, "scan/index.html", "<main>" + ld.replace("{offers}", '{"@type":"SoftwareApplication","offers":{"@type":"Offer","priceCurrency":"USD"}}') + "</main>")
    expect("offers uden price", root, "uden price")

    for name, button in (
        ("Buy-knap", '<a class="btn" href="/scan/">Buy Pro</a>'),
        ("Køb-knap", '<a class="btn" href="/scan/">Køb licens</a>'),
        ("Kaufen-knap", '<button>Jetzt kaufen</button>'),
        ("Acheter-knap", '<a href="/scan/">Acheter Pro</a>'),
        ("Upgrade-knap", '<a href="/scan/">Upgrade to Pro</a>'),
        ("See Pro-knap", '<a href="/scan/">See Pro</a>'),
    ):
        root = fixture()
        put(root, "scan/index.html", f"<main>{button}</main>")
        expect(name, root, "købsknap")

    root = fixture()
    put(root, "scan/index.html", "<main><p>Pro is no longer sold, and existing licences keep working.</p></main>")
    expect_green("Pro nævnt som lukket er grøn", root)

    root = fixture()
    put(root, "scan/index.html", "<main><p>EUComply Pro adds a daily scan.</p></main>")
    expect("Pro nævnt uden lukning", root, "nævner Pro")

    root = fixture()
    put(root, "scan/index.html", "<main><p>EUComply Pro, upgrade today.</p><p>Pro is no longer sold.</p></main>")
    expect("Pro der sælges i samme side som lukningen", root, "sælger Pro")

    root = fixture()
    put(root, "llms.txt", "# EUComply\nEUComply Pro is a paid upgrade.\n")
    expect("llms.txt sælger Pro", root, "sælger Pro")

    root = fixture()
    put(root, "pricing/index.html", "<main>old</main>")
    expect("lukket side findes stadig", root, "findes stadig")

    root = fixture()
    put(root, "pro/sample-report/index.html", "<main>old</main>")
    expect("lukket underside findes stadig", root, "findes stadig")

    root = fixture()
    put(root, "images/og/pricing.png", "x")
    expect("OG-billede for lukket side findes stadig", root, "images/og/pricing.png")

    root = fixture()
    (root / "_redirects").write_text("/pricing/ /scan/ 301\n", encoding="utf-8")
    expect("redirect mangler", root, "har ingen 301")

    root = fixture()
    text = (root / "_redirects").read_text().replace("/da/pro/ /scan/ 301", "/da/pro/ /scan/ 302")
    (root / "_redirects").write_text(text, encoding="utf-8")
    expect("redirect er 302", root, "ikke 301")

    root = fixture()
    text = (root / "_redirects").read_text().replace("/store/ /scan/ 301", "/store/ /findes-ikke/ 301")
    (root / "_redirects").write_text(text, encoding="utf-8")
    expect("redirect peger på en side der ikke findes", root, "som ikke findes")

    root = fixture()
    text = (root / "_redirects").read_text().replace("/store/ /scan/ 301", "/store/ /pricing/ 301")
    (root / "_redirects").write_text(text, encoding="utf-8")
    expect("redirect peger på en anden lukket side", root, "en anden lukket side")

    root = fixture()
    (root / "_redirects").unlink()
    expect("_redirects mangler", root, "_redirects mangler")

    root = fixture()
    put(root, "index.html", _home("en", notice=""))
    (root / "index.html").write_text(_home("en").replace('<div id="frozen-notice">', '<div id="andet">'), encoding="utf-8")
    expect("frozen-notice mangler på forsiden", root, 'mangler elementet id="frozen-notice"')

    root = fixture()
    put(root, "index.html", _home("en", notice="Welcome to EUComply, a compliance scanner for your site today."))
    expect("engelsk frozen-notice uden frasen", root, FROZEN_PHRASE)

    root = fixture()
    (root / "de" / "index.html").write_text(_home("de").replace('id="frozen-notice"', 'id="x"'), encoding="utf-8")
    expect("frozen-notice mangler på tysk forside", root, "de/index.html")

    root = fixture()
    (root / "README.md").write_text("# EUComply\n", encoding="utf-8")
    expect("README uden frys-linje", root, "frozen")

    root = fixture()
    (root / "README.md").write_text("> Frozen.\n", encoding="utf-8")
    expect("README uden datoen", root, CLOSED_ON)

    root = fixture()
    (root / "LICENSE").unlink()
    expect("LICENSE mangler", root, "LICENSE mangler")

    root = fixture()
    (root / "LICENSE").write_text("Apache License 2.0\n2026 Mahope\n", encoding="utf-8")
    expect("LICENSE er ikke MIT", root, "MIT")

    root = fixture()
    put(root, "devnotify/index.html",
        '<main><a class="btn" href="#buy">Buy license — $19</a>'
        + ld.replace("{offers}", '{"@type":"Product","offers":{"@type":"Offer","price":"19"}}') + "</main>")
    expect_green("DevNotify er ikke frosset og må sælge sin egen licens", root)

    root = fixture()
    put(root, "devnotify/index.html", '<main><a href="/pricing/">Pricing</a></main>')
    expect("DevNotify må ikke linke EUComplys lukkede sider", root, "lukkede side")

    root = fixture()
    put(root, "da/devnotify/index.html", '<main><a href="https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03">x</a></main>')
    expect("DevNotify med et EUComply-betalingslink", root, "betalingslink")

    root = fixture()
    put(root, "plugin/eucomply.php", "<?php define('EUCOMPLY_PRO_URL','https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03');")
    put(root, "plugin/readme.txt", "Buy Pro for $79 https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03\n")
    expect_green("pluginets kildekopier er undtaget", root)

    for failure in failures:
        print(f"SELFTEST FEJL: {failure}")
    print(f"SELFTEST {'GRØN' if not failures else 'RØD'} — {count - len(failures)}/{count} cases (rent træ grønt, hvert købsspor rødt)")
    return 0 if not failures else 1


def main(argv: List[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    trees = [Path(arg) for arg in argv if not arg.startswith("-")] or [ROOT / "site", ROOT / "site-dist"]
    findings: List[str] = []
    for tree in trees:
        if tree.is_dir():
            findings.extend(scan_tree(tree, label=tree.name))
    findings.extend(repo_file_findings(ROOT))
    for finding in findings:
        print(f"FUND  {finding}")
    print(f"{len(findings)} købsspor" if findings else "intet købsspor")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
