#!/usr/bin/env python3
"""Gate for the købsvej: kun kontraktfikserede links, én købsknap pr. salgside,
korrekte canonicals, symmetriske lokaler og ingen løfter uden dækning.

Klassifikationen gælder det PUBLICEREDE træ (`site-dist/`), ikke kilde-træet.
Se afsnittet om PUBLISHED nedenfor — det er hele opgave 23.

Opgaver 10 i IMPLEMENTATION_PLAN.md har tre acceptkriterier, der alle var
papirlove indtil dette script:

  1. EN/DA/DE/FR har ingen 404, død knap eller fejl canonical.
  2. Én CTA pr. side fører til det kontraktfikserede Stripe-link.
  3. Baseline metrics kan skelne egne testbrugere fra reelle kunder.

Kriterium 1 og 2 er prøvbare og bliver prøvet her. Kriterium 3 er bevidst ikke
et script: repoet har ingen trafikmåling (se `Baseline` i IMPLEMENTATION_PLAN.md),
så tallet er 0, indtil en tællende worker er deployet. Et script der således
"beviser" 0 ville være en løgn i stedet for et bevis.

Negativt testet: se `--selftest`. Scriptet skal kunne fejle, ellers er det ikke
en gate.

Brug:
    python3 tools/check_cta.py            # hele kontrollen
    python3 tools/check_cta.py --selftest # sæt fejl ind og kræv at de fanges
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

# Det træ, der faktisk uploades, og dermed det en besøgende kan se.
#
# Opgave 22 gjorde klassifikationen afledt, men den kørte på `site/`. Det er den
# forkerte mappe at klassificere: `build_public_tree.py` samler sitet ud fra en
# POSITIVLISTE, så en side kan ligge i `site/` og være dækket af en regel med
# præcis én købsanker, uden at nogen besøgende nogensinde ser den. Gaten var
# grøn på en beskyttelse af en side, der ikke findes — samme fejltype som de tre
# foregående opgaver fandt, bare et lag længere nede.
#
# Indholdet i de to træer er identiske, fordi publiceringen er en kopi. Derfor
# skal INGEN indholdskontrol køre to gange: claims, canonicals, døde referencer
# og checkout-kontrakt giver samme svar på begge. Det der KAN afvige er hvilke
# sider der findes, og det er præcis her købsgaten lå det forkerte sted — så det
# er her den nye kontrol `check_publish_alignment` bor.
PUBLISHED = ROOT / "site-dist"

CANONICAL_ORIGIN = "https://eucomplypro.com"

# Kilde: business-kontrakten 24/9-2026, kopieret maskinlæsbart i
# `tools/stripe_products.json`. Ingen nye produkter, priser eller links oprettes;
# en side der linker noget uden for denne liste er en fejl, fordi den peger på en
# checkout der ikke findes.
#
# Opgave 37: før dette var tillidslisten her **håndskrevet** — otte links, seks af
# dem skabeloner — altså en delmængde af kontraktens tretten. Det gav tre huller,
# alle fundet ved at måle træet i hånden: (1) `eu-compliance-ebook-bundle` er et
# EUComply-produkt i kontrakten, men det stod i ingen konstant, så en side der
# lagde det **ærlige** link ind ville være rød som "ikke i kontrakten"; (2) de fire
# søskeprodukter stod slet ikke, så intet i repoet vidste hvilke produkter der
# overhovedet var; (3) ingen pris stod nogen steds maskinlæsbart, så en knap der
# lovede en anden pris end Stripe tog var umulig at opdage. Nu er listen **afledt**
# af datasættet, og det samme datasæt bruges til at tjekke priser og til at
# rapportere produkter uden side.
CONTRACT_PATH = ROOT / "tools" / "stripe_products.json"
CONTRACT = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
PRODUCTS: tuple[dict, ...] = tuple(CONTRACT["products"])
PRODUCT_BY_URL: dict[str, dict] = {p["url"]: p for p in PRODUCTS}
if len(PRODUCT_BY_URL) != len(PRODUCTS):
    raise SystemExit(f"FEJL {CONTRACT_PATH.name}: to produkter deler samme payment link")


def _product(url: str) -> dict | None:
    return PRODUCT_BY_URL.get(url)


def price_of(url: str) -> int | None:
    """Kontraktprisen i USD, eller None for donation og ukendte links."""
    product = _product(url)
    return product["price_usd"] if product else None


def label_of(url: str) -> str:
    product = _product(url)
    return product["label"] if product else url


PRO_CHECKOUT = next(p["url"] for p in PRODUCTS if p["product_key"] == "eucomply-pro")
DONATION = next(p["url"] for p in PRODUCTS if p["product_key"] == "support-mahope-oss")
# Sorteret, fordi to steder i gaten bruger "et eksempel på et skabelonprodukt",
# og en Python-set rækker ikke rækkefølger stabilt mellem processer.
TEMPLATE_CHECKOUT_LIST: tuple[str, ...] = tuple(
    sorted(p["url"] for p in PRODUCTS if p["template"]))
TEMPLATE_CHECKOUTS = frozenset(TEMPLATE_CHECKOUT_LIST)
ALLOWED_CHECKOUTS = frozenset(PRODUCT_BY_URL)

# Søskeprodukter på samne domæne. Hver har sit eget Stripeprodukt og sit eget
# repo, så deres checkout-links er ikke vores at begrænse her. Se spørgsmål 11.
# De findes både i topniveau og under de lokaliserede træer.
SIBLING_ROOTS = ("devnotify", "deskuptime", "transmute")

# Fragmenter der indgår i andre sider. De er ikke sider og har ingen canonical.
FRAGMENT_PREFIXES = ("_partials/", "shared/")

# ---------------------------------------------------------------------------
# Sideklassifikationen er AFLEDT, ikke håndskrevet.
# ---------------------------------------------------------------------------
# Før denne regel var `PRO_SALES_PAGES` en håndskrevet liste af 31 stier, og
# `check_sales_cta` kørte kun den. En ny side stod altså *uden for* gaten uden
# at nogen vidste det — præcis fejlen de to foregående opgaver fandt ved at måle
# træet i hånden. Nu er hver publiceret side klassificeret af en deklarativ
# regel, og en side ingen regel matcher er et fund, ikke en stilhed.
#
# Arter:
#   pro       — salgsside: præcis én købsanker til kontraktlinket
#   template  — skabelonside: præcis én købsanker til sit eget produkt
#   own       — butiksside: sælger sit eget produkt, dækket af checkout-kontrakten
#   nosale    — med vilje uden køb (juridisk, efter køb, gratis indhold)
#   content   — redaktionelt indhold om emnet, ikke et tilbud fra os
#   free      — frit værktøj, der skal blive frit
#
# REGEL: et mønster må kun bruges hvor familien virkelig er ens. Et
# blanket-`**`-mønster ville gøre den nye gate ligeså stum som den gamle, så
# hver regel bærer sin egen begrundelse og et eksempel på en side den dækker.



LOCALES = ("da", "de", "fr")


def _glob_to_re(pattern: str) -> re.Pattern[str]:
    """Glob -> regex hvor `*` KRYDSER IKKE `/`.

    fnmatch's `*` matcher også skråstreger, så `blog/*/index.html` ville dække
    `blog/a/b/index.html` med. Det er præcis den slags stum dækning, denne regel
    skal fjerne, så skillet tegnes selv.
    """
    return re.compile("".join("[^/]*" if ch == "*" else re.escape(ch)
                              for ch in pattern) + r"\Z")


class Rule:
    """Én klassifikationsregel: mønstre, art, begrundelse og et eksempel.

    `example` er en konkret sti mønstrene dækker. Den bruges to steder:
    selftesten bygger sit fixture-træ af den, så en regel der matcher ingenting
    aldrig kan være død, og den gør reglen læsbar uden glob-syntaks.
    """

    __slots__ = ("kind", "patterns", "reason", "example", "checkout", "_regexes")

    def __init__(self, kind: str, patterns: tuple[str, ...], reason: str,
                 example: str, checkout: str = "") -> None:
        self.kind = kind
        self.patterns = patterns
        self.reason = reason
        self.example = example
        # Kun skabelonsider har et eget produkt; pro-siders checkout er den
        # kontraktfikserede, fordi de alle sælger det samme.
        self.checkout = checkout
        self._regexes = tuple(_glob_to_re(p) for p in patterns)

    def matches(self, rel: str) -> bool:
        return any(rx.match(rel) for rx in self._regexes)

    def label(self) -> str:
        head = self.patterns[0] if len(self.patterns) == 1 else f"{len(self.patterns)} mønstre"
        return f"{self.kind}: {head} — {self.reason}"


def _loc(pattern: str) -> tuple[str, ...]:
    """Udbred en side til alle tre sprog: 'pro/index.html' -> da/de/fr."""
    return tuple(f"{loc}/{pattern}" for loc in LOCALES)


PAGE_RULES: tuple[Rule, ...] = (
    # --- pro: salgssider, præcis én købsanker til kontraktlinket ------------
    Rule("pro", ("index.html",) + _loc("index.html"),
         "forsiden i alle fire sprog: her begynder købsrejsen", "index.html"),
    Rule("pro", ("pro/index.html",) + _loc("pro/index.html"),
         "Pro-siden i alle fire sprog", "pro/index.html"),
    Rule("pro", ("pricing/index.html",) + _loc("pricing/index.html"),
         "prissiden i alle fire sprog", "pricing/index.html"),
    Rule("pro", ("scan/index.html",) + _loc("scan/index.html"),
         "den gratis scanner er tragten: læseren har lige set sine egne fejl",
         "scan/index.html"),
    Rule("pro", ("plugin/index.html",),
         "Pro leveres kun i pluginen, så dette er den eneste side hvor et køb kan "
         "følges igennem til levering", "plugin/index.html"),
    Rule("pro", ("pro/sample-report/index.html",),
         "eksempelrapporten er en Pro-overflade", "pro/sample-report/index.html"),
    Rule("pro", ("pro/vs-*/index.html",),
         "Pro-sammenligninger: læseren står i selve valget mellem os og en "
         "konkurrent", "pro/vs-cookiebot/index.html"),
    Rule("pro", ("vs/*/index.html",),
         "CMP-sammenligningerne sælger vores værktøj som alternativ til "
         "konkurrentens, og har allerede hver præcis én købsanker",
         "vs/cookiebot/index.html"),
    Rule("pro", ("checklist/index.html", "badge/index.html", "cli/index.html",
                 "compare/index.html", "how-it-works/index.html",
                 "check-eu-compliance/index.html", "gdpr-fine-calculator/index.html",
                 "gdpr-scanner-free/index.html", "gdpr-compliance-check/index.html",
                 "cookie-banner-check/index.html", "consent-mode-v2-check/index.html")
         + _loc("cookie-banner-check/index.html"),
         "frie værktøjer med dokumenteret købsintents; den tyske udgave af "
         "cookie-banner-check lå uden for den håndskrevne liste",
         "checklist/index.html"),

    # --- skabelonsider: de sælger deres eget produkt, ikke Pro --------------
    # En EAA-checkliste der sælger en WordPress-licens er forkerte
    # koordinater, så hver side skal have præcis ÉN købsanker til sit eget
    # produkt. Checkoutet står i reglen, så der er én kilde til sandheden.
    Rule("template", ("eaa-checklist/index.html",),
         "sider emnet ER EAA-statementet, så den sælger det — ikke Pro",
         "eaa-checklist/index.html",
         "https://buy.stripe.com/3cI7sK2Qz3IugNUgN9bMQ08"),
    Rule("template", ("nis2-checklist/index.html",),
         "sider emnet ER NIS2/DORA-klausulpakken, så den sælger den — ikke Pro",
         "nis2-checklist/index.html",
         "https://buy.stripe.com/4gM4gydvd92OapwgN9bMQ06"),

    # --- butikken: hver side sælger sit eget skabelonprodukt ----------------
    Rule("own", ("store/index.html",),
         "butiksoversigten sælger hele kataloget", "store/index.html"),
    Rule("own", ("store/*/index.html",),
         "butiksside med sit eget produkt; checkout-linket dækkes af "
         "check_checkout_contract", "store/dpa/index.html"),

    # --- med vilje uden køb -------------------------------------------------
    Rule("nosale", ("404.html",),
         "fejlsiden skal ikke sælge", "404.html"),
    Rule("nosale", ("pro/thank-you/index.html",),
         "kvitteringssiden kommer efter et køb", "pro/thank-you/index.html"),
    Rule("nosale", ("terms/index.html", "privacy/index.html"),
         "juridisk tekst skal fortælle sandheden, ikke sælge", "terms/index.html"),
    Rule("nosale", ("sample/index.html",),
         "arkiveret koncept, ikke et produkt", "sample/index.html"),
    Rule("nosale", ("refund-policy-generator/index.html",),
         "nedlagt side, ingen købsrejse", "refund-policy-generator/index.html"),
    Rule("nosale", ("extension/index.html",),
         "gratis Chrome-udvidelse: et Pro-tilbud dér ville være emnefremmedt",
         "extension/index.html"),
    Rule("nosale", ("cmp-comparison/index.html",),
         "affiliate-sammenligning af CMP-leverandører: emnet er deres værktøj, "
         "ikke vores", "cmp-comparison/index.html"),
    Rule("nosale", ("search/index.html",) + _loc("search/index.html"),
         "søgning er et værktøj, ikke en købsside", "search/index.html"),
    Rule("nosale", ("book/index.html",) + _loc("book/index.html"),
         "gratis PDF-guide i alle fire sprog", "book/index.html"),
    Rule("nosale", ("template/index.html",),
         "gratis NIS2/DORA-checkliste, ikke det betalte produkt", "template/index.html"),
    Rule("nosale", ("pro/dashboard/index.html",),
         "konceptdemo for en roadmap-funktion. En købsknap ville læses som om "
         "dashboardet er en del af Pro i dag, og det dækker ingen kode — så "
         "købsvejen går videre til sample-report, der er en ægte Pro-overflade",
         "pro/dashboard/index.html"),

    # --- redaktionelt indhold ----------------------------------------------
    Rule("content", ("blog/*/index.html", "blog/index.html"),
         "artikler er rådgivning til læseren om andres forpligtelser, ikke "
         "løfter fra os; derfor er de også undtaget fra claims-gaten",
         "blog/dora-for-ecommerce-2026/index.html"),
    Rule("content", ("de/dsgvo-cookie-banner-bussgelder/index.html",
                     "de/was-ist-ein-impressum/index.html"),
         "lokaliserede artikler, skrevet eksplicit fordi de er undtagelse fra "
         "reglen ovenfor: en ny tysk artikel skal klassificeres med vilje",
         "de/was-ist-ein-impressum/index.html"),

    # --- frie værktøjer -----------------------------------------------------
    Rule("free", ("guides/*/index.html", "guides/index.html",
                  "regex/*/index.html", "regex/index.html"),
         "frie referenceværktøjer uden salg", "regex/index.html"),
    Rule("free", ("tools/index.html",),
         "frit værktøjsoversigt", "tools/index.html"),
    Rule("free", ("*-generator/index.html",),
         "gratis generatorer: de skal blive gratis for at være nyttige",
         "impressum-generator/index.html"),
)

# Sider undtaget fra strukturkontrollerne (canonical, døde referencer). Det er
# ikke det samme som at være uklassificeret: de står stadig i PAGE_RULES, så
# de kan ikke forsvinde fra kontrakten ved et uopdaget skred.
STRUCTURE_EXEMPT = frozenset({
    "404.html",
    "pro/thank-you/index.html",
    "terms/index.html",
    "privacy/index.html",
    "sample/index.html",
    "refund-policy-generator/index.html",
})


# Sider der sælger deres eget skabelonprodukt. Afledt af PAGE_RULES, så en
# skabelonside der tilføjes uden checkout ikke kan få en tom gate-kontrakt.
TEMPLATE_CTA_PAGES: dict[str, str] = {
    rel: rule.checkout
    for rule in PAGE_RULES if rule.kind == "template"
    for rel in rule.patterns
}


def classify(rel: str) -> "Rule | None":
    """Første regel der matcher siden. None betyder uklassificeret."""
    for rule in PAGE_RULES:
        if rule.matches(rel):
            return rule
    return None


def classify_tree(base: Path | None = None) -> tuple[dict[str, list[str]], list[str]]:
    """Klassificér et træ → (sider pr. art, uklassificerede)."""
    groups: dict[str, list[str]] = {}
    unknown: list[str] = []
    for path in all_eucocomply_pages(base):
        rel = path.relative_to(base or SITE).as_posix()
        rule = classify(rel)
        if rule is None:
            unknown.append(rel)
        else:
            groups.setdefault(rule.kind, []).append(rel)
    return groups, unknown


# Afledt, ikke skrevet: alle pro-sider i et træ. Før denne ændring var det en
# liste på 31 stier, og de 15 øvrige pro-sider i træet var usynlige for gaten —
# de havde tilfældigvis alle én købsanker, hvilket ingen vidste.
def pro_sales_pages(base: Path | None = None) -> tuple[str, ...]:
    """Alle pro-sider i et træ, fundet ved klassifikation."""
    root = base or SITE
    return tuple(
        rel
        for path in all_eucocomply_pages(root)
        if (rel := path.relative_to(root).as_posix())
        and (rule := classify(rel))
        and rule.kind == "pro"
    )


def purchase_journey_pages() -> set[str]:
    """Købsrejsens sider for det aktuelle træ. Se kommentaren på konstanten."""
    return set(pro_sales_pages()) | {
        f"{loc}/{rel}" for loc in LOCALES for rel in LOCALE_SALES_PATHS
    } | {
        "terms/index.html",
        "pro/thank-you/index.html",
        "store/index.html",
        "template/index.html",
        "book/index.html",
    }

# Lokaliserede købssider der skal findes i alle tre sprog. Ens symmetri er
# acceptkriterium 1: en dansk læser må ikke miste en købsknap, en tysk har.
LOCALE_SALES_PATHS = ("index.html", "pro/index.html", "pricing/index.html")

# Købsrejsens sider: de steder, hvor et løfte om gratis prøveperiode, konto eller
# refund faktisk skader, fordi det står ved købsknappen. Blogindlæg og guides er
# redaktionelt indhold om andres forpligtelser — "a 14-day money-back guarantee
# converts better" i en artikel er rådgivning til læseren, ikke et løfte fra os,
# og en gate der rammer den ville gørede artiklen om emnet umulig at skrive.
# Sætten er afledt af klassifikationen: se purchase_journey_pages().

# Løfter købsrejsen ikke kan holde, fordi intet i repoet dækker dem. Stripe er
# ikke Merchant of Record, og der er hverken gratis prøveperiode eller konto.
FORBIDDEN_CLAIMS = (
    (re.compile(r"\bfree trial\b|\bgratis\s+pr[øo]ve(?:periode)?\b|\btestperiode\b|\bkostenlos.{0,12}test\b", re.I),
     "gratis prøveperiode"),
    (re.compile(r"\b14[- ]day\b.{0,25}\btrial\b|\b14\s+dage\b.{0,25}\bpr[øo]ve\b", re.I),
     "14 dages prøveperiode"),
    (re.compile(r"\bcancel anytime\b|\bcancel\s+whenever\b|\bsay no to cancel", re.I),
     "cancel anytime"),
    (re.compile(r"\bno credit card (required|needed)\b|\bingen kortoplysninger\b", re.I),
     "no credit card required"),
    (re.compile(
        r"\b(?:we|i)\s+(?:will\s+|shall\s+)?refund(?:s|ed)?\b"
        r"|\brefund(?:s|ed)?\s+(?:you|your\s+purchase|the\s+purchase)\b"
        r"|\b\d+\s*(?:days?|dage|tage|jours)\s+(?:money[\s-]back|refund|garanti)\b"
        r"|\b(?:money|garanti)[\s-]?back\s+guarantee\b"
        r"|\btrygghedsgaranti\b|\bgarantie\s+de\s+remboursement\b|\bGeld\s+zur\s+ück\s+garantie\b",
        re.I),
     "refund-løfte vi ikke kan dokumentere"),
    (re.compile(r"\b(?:create|open)\s+an?\s+account\b|\bopret\s+(?:en\s+)?(?:konto|profil)\b|\bstarten? (?:gratis )?konto\b", re.I),
     "konto-oprettelse"),
)

STRIPE_RE = re.compile(r"https://(?:buy|donate)\.stripe\.com/[A-Za-z0-9]+")
# Belob der staar med valuta-tegn foran eller bagved, saa bade "$59" og "19 $"
# laeses. Kun USD: "$" og "USD" er de to former kontrakten og knapperne bruger.
USD_AMOUNT_RE = re.compile(r"(?:\$\s*([0-9][0-9,]*)|([0-9][0-9,]*)\s*(?:USD|US\$|\$))", re.I)
CANONICAL_RE = re.compile(r'<link[^>]+rel="canonical"[^>]*>', re.I)
HREF_RE = re.compile(r'href="([^"]+)"')


def all_eucocomply_pages(base: Path | None = None) -> list[Path]:
    """Hele EUComply-træet: undtagen søskeprodukter og fragmenter.

    Uden struktur-undtagelsen, så selv en side der er fri for canonical-
    kontrollen stadig skal klassificeres. Ellers så en død regel ud som død
    bare fordi dens side er undtaget fra et andet tjek — præcis den stumhed
    opgave 22 fjerner.

    `base` vælger hvilket træ: `site/` (kilden) eller `site-dist/` (det der
    publiceres). Klasseforskel: eksistens, ikke indhold.
    """
    root = base or SITE
    pages = []
    for path in sorted(root.rglob("*.html")):
        rel = path.relative_to(root).as_posix()
        if rel.startswith(FRAGMENT_PREFIXES):
            continue
        parts = rel.split("/")
        if any(part in SIBLING_ROOTS for part in parts[:-1]):
            continue
        pages.append(path)
    return pages


def eucocomply_pages() -> list[Path]:
    """EUComply-sider med strukturkrav (canonical, døde interne referencer)."""
    return [
        path for path in all_eucocomply_pages()
        if path.relative_to(SITE).as_posix() not in STRUCTURE_EXEMPT
    ]


def check_checkout_contract() -> list[str]:
    """Ingen EUComply-side må pege på en checkout uden for kontrakten.

    Søskeprodukterne springes over med vilje: hver har sit eget Stripeprodukt
    og sit eget repo, så deres links er ikke vores at begrænse her.
    """
    findings = []
    for path in eucocomply_pages():
        text = path.read_text(encoding="utf-8", errors="replace")
        for link in set(STRIPE_RE.findall(text)):
            if link not in ALLOWED_CHECKOUTS:
                rel = path.relative_to(SITE).as_posix()
                findings.append(f"{rel}: Stripe-link ikke i kontrakten: {link}")
    return findings


def check_price_claims() -> list[str]:
    """En købsknap skal love den pris kontrakten siger.

    Opgave 37. `check_checkout_contract` svarer på "pegede den på et rigtigt
    produkt?", men ikke på "lovede den det rigtige?" — og det er det sidste en
    køber kan lide sig for. To fejl lå i det samme klik: en knap der siger
    "$29" på et produkt der koster $59, og en knap der er flyttet til et andet
    produkts link, så man betaler $29 for noget der står som $59. Begge er
    uskyldige at rette på den rigtige side (Stripedata, ikke markup) og begge er
    umulige at opdage uden et datasæt at sammenligne imod — derfor dette.

    KUN beløb i selve købsankeren tjekkes. Ikke `class="price"`: den bruges også
    på sammenligningssider til at citere konkurrenters priser ($350+/mo,
    €179/year, "Gratis"), så en sådan regel ville være rød på ærlige sider.
    KUN USD-beløb: kontrakten viser også DKK og EUR, og omregningen af dem er
    Stripes, ikke vores — at gætte på den ville give røde fund uden sandhed.
    """
    findings: list[str] = []
    for path in eucocomply_pages():
        rel = path.relative_to(SITE).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(
            r'<a\b[^>]*href="(https://(?:buy|donate)\.stripe\.com/[^"]+)"[^>]*>(.*?)</a>',
            text, re.S):
            url, inner = match.group(1), match.group(2)
            contract_price = price_of(url)
            if contract_price is None:
                continue
            label = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", inner)).strip()
            for amount in sorted({int(n) for n in [a or b for a, b in USD_AMOUNT_RE.findall(label)]}):
                if amount != contract_price:
                    findings.append(
                        f"{rel}: købsknappen lover {amount} USD for "
                        f"{label_of(url)}, som koster {contract_price} USD i "
                        f"kontrakten: \"{label}\"")
    return findings


def unsold_products(base: Path | None = None) -> list[tuple[str, str]]:
    """Kontraktprodukter til EUComply-domænet uden én eneste side.

    **Rapport, ikke fund.** Et produkt uden side tjener 0 kroner, så det er
    præcis den slags der bliver glemt — men en permanent rød gate ville stoppe
    hvert merge og dermed hele sitets deploy (opgave 35). Derfor står det her som
    en linje på hver kørsel, så det ikke kan blive glemt uden at nogen ser det.

    Målt 26/9 (opgave 37): `eu-compliance-ebook-bundle` ($29) har nul forekomster
    i det publicerede træ. Det er et live Stripeprodukt uden salgsside, og der
    står intet i repoet om hvad køberen modtager — så der er ingen side at skrive
    uden at opfinde løftet. Se spørgsmål 20 i planen.
    """
    root = base or PUBLISHED
    corpus: list[str] = []
    for path in all_eucocomply_pages(root):
        corpus.append(path.read_text(encoding="utf-8", errors="replace"))
    blob = "\n".join(corpus)
    return [
        (p["product_key"], p["label"])
        for p in PRODUCTS
        if p["scope"] == "eucomply" and p["url"] not in blob
    ]


def check_classification() -> list[str]:
    """Ingen publiceret side må være uklassificeret.

    Det er hele pointen med opgave 22: før denne kontrol var gaten lige så stum
    for en ny side som den altid havde været — den kørte kun på en håndskrevet
    liste. Nu er en side, ingen regel matcher, et fund, fordi den ellers ville
    stå uden købsgate helt i stilhed.
    """
    findings: list[str] = []
    groups, unknown = classify_tree()
    for rel in unknown:
        findings.append(
            f"{rel}: uklassificeret — ingen regel i PAGE_RULES matcher. Skriv "
            "siden i en eksisterende regel, eller tilføj en ny regel med "
            "begrundelse; ellers står den uden købsgates."
        )
    # En regel der matcher ingen side er død kontrakt: den ligner en
    # beskyttelse, men beskytter intet. Selftestens fixture bygges af hver
    # regels `example`, så den dør aldrig af sig selv.
    seen = {classify(rel) for group in groups.values() for rel in group}
    for rule in PAGE_RULES:
        if rule not in seen:
            findings.append(f"død regel — matcher ingen publiceret side: {rule.label()}")
    return findings


def check_sales_cta() -> list[str]:
    """Hver afgrenset salgsside skal have prissiden — og kun den.

    Rækken kommer fra klassifikationen, ikke fra en liste: en ny pro-side er
    dækket i samme sekund den findes i træet.

    Kører på det PUBLICEREDE træ. Det er ikke en småting: "forventet salgsside
    mangler" er en eksistenspåstand, og det er præcis den påstand, der var
    forkert — en pro-side i `site/` uden en publiceret udgave er en købsside,
    ingen besøgende kan nå.
    """
    findings = []
    for rel in pro_sales_pages(PUBLISHED) + tuple(TEMPLATE_CTA_PAGES):
        checkout = TEMPLATE_CTA_PAGES.get(rel, PRO_CHECKOUT)
        path = PUBLISHED / rel
        if not path.is_file():
            findings.append(f"{rel}: forventet salgsside mangler i det publicerede træ")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if checkout not in text:
            findings.append(f"{rel}: mangler det kontraktfikserede Pro-link ({checkout})")
            continue
        # Én købsknap: to knapper til samme checkout er færdig-følelse, ikke
        # valg, og de gør det umuligt at måle hvilken der virker.
        buy_anchors = len(re.findall(r'<a[^>]+href="' + re.escape(checkout) + r'"', text))
        if buy_anchors != 1:
            findings.append(f"{rel}: forventer præcis 1 købsanker til Pro-linket, fandt {buy_anchors}")
    return findings


def check_publish_alignment() -> list[str]:
    """Det publicerede træ og kilde-træet skal være det samme for EUComply.

    Opgave 22 gjorde klassifikationen afledt, så en ny side ikke kan undslippe.
    Men den klassificerede `site/`, og det er ikke det træ, en besøgende ser:
    `build_public_tree.py` samler sitet ud fra en positivliste. Siden da kunne
    en salgsside ligge i kilden, være dækket af en regel med præcis én
    købsanker, og alligevel aldrig blive publiceret — og ingen død regel ville
    fortelle det, fordi siden findes i det træ gaten kiggede på.

    Fire fund, fordi de fire ting der kan gå galt er fire forskellige:

      1. Det publicerede træ mangler. Uden det er kontrol 2 og 3 vakuære, så
         det er et fund og ikke en advarsel — ellers ville gaven være grøn på
         en egenskab den aldrig har efterprøvet.
      2. En side i kilden er ikke publiceret. Den mest alvorlige: den ligner
         beskyttet og ingen kan nå den.
      3. En publiceret side findes ikke i kilden. Umuligt for en kopi, så et
         fund betyder at de to træer ikke er samme generation.
      4. En publiceret side er uklassificeret, eller en regel er død *i det
         publicerede træ*. Det er den egenskab, der gør resten meningsfulde:
         også det en besøgende kan se skal være klassificeret.
    """
    if not PUBLISHED.is_dir():
        return [
            f"det publicerede træ {PUBLISHED.name}/ findes ikke — klassifikationen "
            "kan da ikke efterprøves mod det, der uploades. Kør "
            "`python3 tools/build_public_tree.py` først."
        ]

    source = {p.relative_to(SITE).as_posix() for p in all_eucocomply_pages(SITE)}
    live = {p.relative_to(PUBLISHED).as_posix() for p in all_eucocomply_pages(PUBLISHED)}

    findings: list[str] = []
    for rel in sorted(source - live):
        findings.append(
            f"{rel}: findes i site/ men er ikke i det publicerede træ — "
            "siden er dækket af en regel, men ingen besøgende kan nå den. "
            "Tilføj mappen til PUBLIC_DIRS/PUBLIC_FILES i build_public_tree.py, "
            "eller skriv den bevidst ud som intern undtagelse."
        )
    for rel in sorted(live - source):
        findings.append(
            f"{rel}: publiceret men findes ikke i site/ — de to træer er ikke "
            "samme generation. Genbyg site-dist/."
        )

    groups, unknown = classify_tree(PUBLISHED)
    for rel in unknown:
        findings.append(
            f"{rel}: publiceret men uklassificeret — ingen regel i PAGE_RULES "
            "matcher. Skriv siden i en eksisterende regel, eller tilføj en ny "
            "regel med begrundelse; ellers står den uden købsgates."
        )
    seen = {classify(rel) for group in groups.values() for rel in group}
    for rule in PAGE_RULES:
        if rule not in seen:
            findings.append(
                f"død regel i det publicerede træ — matcher ingen publiceret "
                f"side: {rule.label()}"
            )
    return findings


def check_locale_parity() -> list[str]:
    """De tre sprog skal have præcis de samme købssider."""
    findings = []
    for rel in LOCALE_SALES_PATHS:
        for locale in LOCALES:
            path = SITE / locale / rel
            key = f"{locale}/{rel}"
            if not path.is_file():
                findings.append(f"{key}: lokaliseret købsside mangler (EN har den)")
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if rel == "pricing/index.html":
                if PRO_CHECKOUT not in text:
                    findings.append(f"{key}: mangler det kontraktfikserede Pro-link")
            else:
                if "79 USD" not in text and "79\u20ac" not in text and "79 kr" not in text:
                    findings.append(f"{key}: nævner ikke Pro-prisen (79)")
    return findings


def check_canonicals() -> list[str]:
    """Canonical skal være absolut og præcis sidens egen sti."""
    findings = []
    for path in eucocomply_pages():
        rel = path.relative_to(SITE).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        tags = CANONICAL_RE.findall(text)
        if not tags:
            findings.append(f"{rel}: mangler canonical")
            continue
        if len(tags) > 1:
            findings.append(f"{rel}: {len(tags)} canonical-tags (skal være 1)")
        url = (re.search(r'href="([^"]+)"', tags[0]) or [None, ""])[1]
        tail = "" if rel == "index.html" else rel.replace("index.html", "")
        want = CANONICAL_ORIGIN + "/" + tail
        if url.rstrip("/") != want.rstrip("/"):
            findings.append(f"{rel}: canonical er {url}, forventet {want}")
    return findings


def check_dead_internal_hrefs() -> list[str]:
    """Ingen intern href må pege på en side eller et asset, der ikke findes."""
    findings = []
    for path in eucocomply_pages():
        rel = path.relative_to(SITE).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for href in HREF_RE.findall(text):
            if not href.startswith("/") or href.startswith("//"):
                continue
            if "#" in href:
                continue
            target = href.split("?")[0].rstrip("/")
            if target in ("", "/"):
                continue
            # /assets/x.css?v=1 -> /assets/x.css
            disk = SITE / target.lstrip("/")
            if disk.is_dir():
                disk = disk / "index.html"
            if disk.exists():
                continue
            if (SITE / (target.lstrip("/") + ".html")).exists():
                continue
            if (SITE / target.lstrip("/")).exists():
                continue
            # Layoutskabeloner og locale-assets må gerne komme fra partials.
            if target.rsplit("/", 1)[-1].startswith("."):
                continue
            findings.append(f"{rel}: død intern reference {href}")
    return findings


# Et køb, der ikke kan gennemføres. Regex-siden havde en disabled-knap med
# "Payment opening soon" og en statuslinje om at checkout "will be available
# once payment processing is configured" — altså en pris og en knap, men ingen
# vej at betale.MISSIONENS regel er eksplicit: ingen tekster om at checkout
# kommer. Mønstret kræver derfor begge dele i SAMME kontrolelement: et købsord
# (buy/køb/kaufen/acheter/checkout/betal) og en "snart"-markør. En artikel der
# skriver at en kundes side var "coming soon" er redaktionelt indhold og
# rammes ikke, fordi den ikke er en kontrol.
UNBUYABLE_CTA = re.compile(
    r"<(?:button|span|a)\b[^>]*\bclass=\"[^\"]*\bbtn\b[^\"]*\"[^>]*>(?:(?!</(?:button|span|a)>).)*?"
    r"\b(?:buy|checkout|pay|rent|køb|købs|kauf|bezahlen|acheter|achat|pagar|betal|betalning)\w*"
    r"(?:(?!</(?:button|span|a)>).)*?"
    r"\b(?:soon|coming|opening|available|kommt|kommende|underwegs|bientôt|prochain|próxim|kommer)\w*"
    r"(?:(?!</(?:button|span|a)>).)*?</(?:button|span|a)>"
    r"|<(?:button|span|a)\b[^>]*\bclass=\"[^\"]*\bbtn\b[^\"]*\"[^>]*>(?:(?!</(?:button|span|a)>).)*?"
    r"\b(?:soon|coming|opening|underwegs|bientôt|prochain)\w*"
    r"(?:(?!</(?:button|span|a)>).)*?"
    r"\b(?:buy|checkout|pay|rent|køb|kauf|bezahlen|acheter|achat|pagar|betal)\w*"
    r"(?:(?!</(?:button|span|a)>).)*?</(?:button|span|a)>",
    re.I | re.S,
)
# Samme fejl i en anden form: en disabled-knap ved siden af en pris. Ordene
# "coming soon" mangler, men knappen kan stadig ikke betales, og det er den
# egentlige fejl — ikke formuleringen af den.
#
# Attributten skal være whitespace-afgrænset. Første udgave brugte `\bdisabled\b`,
# som også matcher inde i en href: DevNotify's indholdsfortegnelpe har 46 links
# med `#1-web-notifications-are-disabled-in-your-github-settings`, og gatten
# erklærede en artikel om *netop* det emne som et rødt fund. Fundet ved
# mutation mod repoets egen fil, ikke ved at læse koden.
DISABLED_PAY_CTL = re.compile(
    r"<(?:button|span|a)\b[^>]*?\sdisabled(?=[\s/>])[^>]*>", re.I
)


def check_unbuyable_cta() -> list[str]:
    """Ingen side må vise en købsknap, der ikke kan gennemføres.

    Hele EUComply-træet, ikke kun købsrejsen: de to fejl denne kontrol
    fandt sad på søskeprodukterne `/transmute/` og `/regex/`, som ligger i
    deploy-træet og linkedes fra bloggen, men ikke i købsrejsens sæt.

    Derfor læses det PUBLICEREDE træ og ikke EUComply-sættet. Det var den
    første mutation, der slap forbi: `site/transmute/` er et søskeproduct,
    så `eucocomply_pages()` beskæftiger sig aldrig med den — og netop der
    lå den skjulte checkout. Fejlen skal kunne sidde hvor som helst i det,
    der publiceres. `_partials/` og `shared/` er inkluderede fragmenter, ikke
    sider, så de springes over.
    """
    findings = []
    if not PUBLISHED.is_dir():
        return findings
    for path in sorted(PUBLISHED.rglob("*.html")):
        rel = path.relative_to(PUBLISHED).as_posix()
        if rel.startswith(FRAGMENT_PREFIXES):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if UNBUYABLE_CTA.search(text):
            findings.append(f"{rel}: købsknap der ikke kan gennemføres (krøver 'coming soon')")
        if DISABLED_PAY_CTL.search(text):
            findings.append(f"{rel}: deaktiveret betalingsknap (kan ikke gennemføres)")
    return findings


def check_forbidden_claims() -> list[str]:
    """Købsrejsens sider må ikke love noget, ingen kode dækker.

    Kun købsrejsen, ikke hele sitet: se kommentaren på PURCHASE_JOURNEY_PAGES.
    """
    findings = []
    for rel in sorted(purchase_journey_pages()):
        path = SITE / rel
        if not path.is_file():
            continue
        # kun synlig tekst: JSON-LD og scripts er ikke løfter til læseren
        text = path.read_text(encoding="utf-8", errors="replace")
        text = re.sub(r"<script.*?</script>", " ", text, flags=re.S | re.I)
        text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        for pattern, label in FORBIDDEN_CLAIMS:
            if pattern.search(text):
                findings.append(f"{rel}: uunderstøttet løfte ({label})")
    return findings


def run(root: Path) -> list[str]:
    """Kør alle kontroller mod en given repo-rod og samle fundene."""
    global SITE, PUBLISHED
    SITE = root / "site"
    PUBLISHED = root / "site-dist"
    found: list[str] = []
    for check in (
        # Først aligneringen: den forteller om de to træer overhovedet er det
        # samme, og de øvrige eksistens- og klassifikationskontroller er kun
        # meningsfulde når de er det.
        check_publish_alignment,
        check_classification,
        check_checkout_contract,
        check_price_claims,
        check_sales_cta,
        check_locale_parity,
        check_canonicals,
        check_dead_internal_hrefs,
        check_forbidden_claims,
        check_unbuyable_cta,
    ):
        found.extend(check())
    return found


def _minimal_page(rel: str) -> str:
    """En minimal, helt korrekt side for den givne sti.

    Købsankeren følger sidens *art*, ikke en håndskrevet undtagelse: en
    butiksside får sit eget produkt, en artikelside ingen. Det var netop
    fejlen opgave 21s selftest fangede, da fixture'en hardcoded Pro-linket og
    de to skabelonsider så ville være testet som om de solgte Pro.
    """
    tail = "" if rel == "index.html" else rel.replace("index.html", "")
    rule = classify(rel)
    kind = rule.kind if rule else "pro"
    body = ""
    if kind == "pro":
        checkout = PRO_CHECKOUT
        body = f'<a class="btn" href="{checkout}">Buy Pro — {price_of(checkout)} USD per website per year</a>'
    elif kind == "template":
        checkout = TEMPLATE_CTA_PAGES[rel]
        body = f'<a class="btn" href="{checkout}">Buy the template — ${price_of(checkout)}</a>'
    elif kind == "own":
        checkout = TEMPLATE_CHECKOUT_LIST[0]
        body = f'<a class="btn" href="{checkout}">Buy this document — ${price_of(checkout)}</a>'
    return (
        f'<html><head><link rel="canonical" href="{CANONICAL_ORIGIN}/{tail}"></head>'
        f"<body>{body}</body></html>"
    )


def publish(base: Path) -> None:
    """Spejl `build_public_tree.py`: site/ -> site-dist/.

    Selftesten skal have BEGGE træer, ellers ville aligneringskontrollen være
    vakuær: den ville enten finde intet at sammenligne, eller finde alt for meget
    i en fixture der aldrig ligner den virkelige publicering, som er en kopi.
    """
    target = base / "site-dist"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(base / "site", target)


def selftest() -> int:
    """Gaten skal kunne fejle. Vi indplanter fejl og kræv at de fanges."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "repo"
        (base / "site").mkdir(parents=True)
        # Fixture-træet bygges af reglerne — ikke af en håndskrevet liste. Hvert
        # mønster uden `*` bidrager med sig selv, så de lokaliserede sider
        # (da/de/fr scan, pro, pricing, book, search) er med og hver især kan
        # testes. Mønstre med `*` bidrager med regelens `example`. Så dækker
        # selftesten præcis den klassifikation, der ligger i træet, og en regel
        # kan ikke dø uden at selftesten bliver rød.
        required = {rule.example for rule in PAGE_RULES}
        required.update(
            pattern for rule in PAGE_RULES for pattern in rule.patterns
            if "*" not in pattern
        )
        for rel in sorted(required):
            path = base / "site" / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(_minimal_page(rel), encoding="utf-8")
        publish(base)

        clean = run(base)
        if clean:
            print("SELFTEST FEJLED: et minimalt rent træ giver fund:")
            for f in clean:
                print(f"  - {f}")
            return 1
        print(f"selftest: rent træ ({len(required)} sider, kilde + publiceret) "
              "giver 0 fund")

        def expect(label: str, needle: str, mutate, rel: str = "pro/index.html") -> bool:
            # Begge træer muteres. `check_sales_cta` læser det publicerede,
            # resten læser kilden, så en mutation i kun det ene træ ville teste
            # den halve gade — præcis den falske grøn, den her skal fange.
            originals = {}
            for root in (base / "site", base / "site-dist"):
                target = root / rel
                originals[root] = target.read_text(encoding="utf-8")
                target.write_text(mutate(originals[root]), encoding="utf-8")
            hit = [f for f in run(base) if needle in f]
            for root, text in originals.items():
                (root / rel).write_text(text, encoding="utf-8")
            if hit:
                print(f"selftest: {label} fanget")
                return True
            print(f"SELFTEST FEJLED: {label} blev ikke fanget")
            return False

        cases = [
            ("død intern reference", "findes-ikke",
             lambda t: t.replace("</body>", '<a href="/findes-ikke/">x</a></body>')),
            ("udokumenteret checkout-link", "ikke i kontrakten",
             lambda t: t.replace(PRO_CHECKOUT, "https://buy.stripe.com/0000ophaegtViLink000000000")),
            ("to købsankere på én side", "købsanker",
             lambda t: t.replace("</body>", f'<a class="btn" href="{PRO_CHECKOUT}">Buy Pro</a></body>')),
            ("forkert canonical", "canonical er",
             lambda t: t.replace(f'{CANONICAL_ORIGIN}/pro/', f"{CANONICAL_ORIGIN}/pricing/")),
            ("uunderstøttet løfte", "uunderstøttet løfte",
             lambda t: t.replace("</body>", "<p>No credit card required.</p></body>")),
            ("manglende købsknap", "mangler det kontraktfikserede Pro-link",
             lambda t: t.replace(PRO_CHECKOUT, "/pricing/")),
            # Scanneren er den nye salgsside. Uden denne case kunne de fire nye
            # stier stå i listen uden at være dækket, og en slåfe sti i listen
            # ville se grøn ud præcis som da scanneren manglede helt.
            ("scanner uden købsknap", "mangler det kontraktfikserede Pro-link",
             lambda t: t.replace(PRO_CHECKOUT, "/pricing/"), "scan/index.html"),
            ("fransk scanner uden købsknap", "mangler det kontraktfikserede Pro-link",
             lambda t: t.replace(PRO_CHECKOUT, "/pricing/"), "fr/scan/index.html"),
            # Skabelonsiden skal sælge sit eget produkt. Hvis denne case
            # mangler, kunne de to checklister stå i kontrakten uden at være
            # dækket — præcis som da scanneren manglede helt.
            ("EAA-checkliste uden sit produkt", "mangler det kontraktfikserede Pro-link",
             lambda t: t.replace("3cI7sK2Qz3IugNUgN9bMQ08", "/store/"),
             "eaa-checklist/index.html"),
            ("NIS2-checkliste uden sit produkt", "mangler det kontraktfikserede Pro-link",
             lambda t: t.replace("4gM4gydvd92OapwgN9bMQ06", "/store/"),
             "nis2-checklist/index.html"),
            # Opgave 32: en købsknap, der ikke kan gennemføres. Uden disse to
            # cases kunne `check_unbuyable_cta` være grøn af den forkerte grund —
            # mutation M2 mod repoets egen `/transmute/` slap først forbi, fordi
            # kontrollen læste EUComply-sættet, der slet ikke rummer søskeproduktet.
            ("købsknap der kræver 'coming soon'", "købsknap der ikke kan gennemføres",
             lambda t: t.replace("</body>",
                                 '<span class="btn">Buy — $19 (coming soon)</span></body>')),
             ("deaktiveret betalingsknap", "deaktiveret betalingsknap",
              lambda t: t.replace("</body>",
                                  '<button class="btn" disabled>Buy — $19</button></body>')),
             # Opgave 37: det beløb købsknappen lover. Uden disse cases kunne
             # `check_price_claims` være grøn af den forkerte grund — en knap der
             # siger en anden pris end kontrakten er præcis det køberen mærker
             # først, og ingen anden kontrol i gaten kan se det.
             ("forkert pris i købsknappen", "lover",
              lambda t: t.replace(f"${price_of(TEMPLATE_CHECKOUT_LIST[0])}", "$9"),
              "store/dpa/index.html"),
             # Beløb skrevet BAGVED tegnet. Den danske og tyske skabelon skriver
             # "19 $", så kun beløb med tegn foran ville være grøn på et forkert
             # beløb i netop den form. (At den rigtige værdi i den form IKKE er
             # et fund, er prøvet af det rene fixture-træ ovenfor.)
             ("beløb skrevet bagved tegnet", "lover",
              lambda t: t.replace(f"${price_of(TEMPLATE_CHECKOUT_LIST[0])}", "9 $"),
              "store/dpa/index.html"),
             # Forkert produkt i stedet for forkert pris: knappen siger $69, men
             # href'en er et $29-produkt. Kunden betaler for den billige.
             ("knap med et andet produkts link", "lover",
              lambda t: t.replace(TEMPLATE_CHECKOUT_LIST[0],
                                  "https://buy.stripe.com/aFafZg1Mv92OdBI8gDbMQ07"),
              "store/dpa/index.html"),
             ("pris i pro-knappen", "lover",
              lambda t: t.replace(f"{price_of(PRO_CHECKOUT)} USD", "29 USD"),
              "pricing/index.html"),
        ]
        for label, needle, mutate, *target_rel in cases:
            if not expect(label, needle, mutate, *(target_rel or ["pro/index.html"])):
                return 1

        # en manglende lokal købsside
        victim = base / "site" / "fr" / "pricing" / "index.html"
        victim.unlink()
        if not [f for f in run(base) if "lokaliseret købsside mangler" in f]:
            print("SELFTEST FEJLED: manglende fransk købsside blev ikke fanget")
            return 1
        print("selftest: manglende lokal købsside fanget")
        blocks = 1

        # Opgave 22, del 1: en ny side skal vælge sin art, ellers er den et fund.
        # Uden denne case ville den afledte klassifikation være lige så stum som
        # den håndskrevne liste var — siden ville bare ligge uden for alle
        # mønstre uden at nogen lægger mærke til det. Skrives i begge træer, så
        # denne case tester klassifikationen og ikke aligneringen ved siden af.
        stray = base / "site" / "ny-vaerktoej" / "index.html"
        stray.parent.mkdir(parents=True, exist_ok=True)
        stray.write_text(
            f'<html><head><link rel="canonical" '
            f'href="{CANONICAL_ORIGIN}/ny-vaerktoej/"></head>'
            f'<body><a class="btn" href="{PRO_CHECKOUT}">Buy Pro</a></body></html>',
            encoding="utf-8",
        )
        publish(base)
        if not [f for f in run(base) if "uklassificeret" in f]:
            print("SELFTEST FEJLED: uklassificeret side blev ikke fanget")
            return 1
        print("selftest: uklassificeret side fanget")
        stray.unlink()
        publish(base)
        blocks += 1

        # Opgave 22, del 2: en ny pro-side fanges af et mønster, ikke af en
        # liste. `pro/vs-acme/` står i ingen konstant nogen skrev ved hånd, så
        # denne case er beviset på at dækningen er afledt.
        derived = base / "site" / "pro" / "vs-acme" / "index.html"
        derived.parent.mkdir(parents=True, exist_ok=True)
        derived.write_text(
            f'<html><head><link rel="canonical" '
            f'href="{CANONICAL_ORIGIN}/pro/vs-acme/"></head>'
            "<body>En ny Pro-sammenligning uden købsknap.</body></html>",
            encoding="utf-8",
        )
        publish(base)
        if not [f for f in run(base) if "mangler det kontraktfikserede Pro-link" in f]:
            print("SELFTEST FEJLED: ny pro-side uden købsknap blev ikke fanget")
            return 1
        print("selftest: ny pro-side uden købsknap fanget (kun et mønster dækkede den)")
        derived.unlink()
        publish(base)
        blocks += 1

        # En regel der matcher ingen side ligner en beskyttelse men beskytter
        # intet. Den skal findes, ellers kan en død regel blive stående for evig.
        # `store/*/index.html` dør ved at fjerme dens eneste side; `store/`
        # selv overlever i den anden regel, så fundet skyldes den døde mønstregel
        # og ikke bare et manglende træ.
        (base / "site" / "store" / "dpa" / "index.html").unlink()
        if not [f for f in run(base) if "død regel" in f]:
            print("SELFTEST FEJLED: død regel blev ikke fanget")
            return 1
        print("selftest: død regel fanget")
        # Siden sættes tilbage, så de fire cases nedenfor kun tester det
        # publicerede træ og ikke arver denne mutation.
        (base / "site" / "store" / "dpa" / "index.html").write_text(
            _minimal_page("store/dpa/index.html"), encoding="utf-8")
        publish(base)
        blocks += 1

        # ------------------------------------------------------------------
        # Opgave 23: de fire fejl, der kun kan ske i det PUBLICEREDE træ.
        #
        # Før denne iteration klassificerede gaten `site/`. Det lyder som en
        # detalje, men det er hele opgaven: en side kunne være dækket af en regel
        # med præcis én købsanker i det træ gaten kiggede på, og alligevel aldrig
        # blive publiceret — fordi `build_public_tree.py` samler sitet ud fra en
        # positivliste. Uden de fire nederste cases ville den nye kontrol være en
        # påstand om at den dækker det, præcis som de tre foregående opgaver.
        # ------------------------------------------------------------------

        # 1. En salgsside der ikke er publiceret. Det er det alvorligste fund:
        #    siden ligner beskyttet, og ingen besøgende kan nå den.
        (base / "site-dist" / "checklist" / "index.html").unlink()
        if not [f for f in run(base) if "ikke i det publicerede træ" in f]:
            print("SELFTEST FEJLED: upubliceret salgsside blev ikke fanget")
            return 1
        print("selftest: salgsside i kilden men ikke publiceret fanget")
        publish(base)
        blocks += 1

        # 2. Samme fejl, set fra den anden side: en regel der er død for det
        #    publicerede træ, men levende i kilden. Før denne kontrol ville
        #    `check_classification` have sagt "alt i orden" om `store/*/`.
        (base / "site-dist" / "store" / "dpa" / "index.html").unlink()
        if not [f for f in run(base) if "død regel i det publicerede træ" in f]:
            print("SELFTEST FEJLED: død regel i det publicerede træ blev ikke fanget")
            return 1
        print("selftest: død regel i det publicerede træ fanget")
        publish(base)
        blocks += 1

        # 3. En side der er publiceret uden at være klassificeret. Kun det
        #    publicerede træ skal klassificeres — det er det, en besøgende ser.
        lone = base / "site-dist" / "ny-vaerktoej" / "index.html"
        lone.parent.mkdir(parents=True, exist_ok=True)
        lone.write_text(
            f'<html><head><link rel="canonical" '
            f'href="{CANONICAL_ORIGIN}/ny-vaerktoej/"></head>'
            f"<body><a class=\"btn\" href=\"{PRO_CHECKOUT}\">Buy Pro</a></body></html>",
            encoding="utf-8",
        )
        if not [f for f in run(base) if "publiceret men uklassificeret" in f]:
            print("SELFTEST FEJLED: publiceret men uklassificeret side blev ikke fanget")
            return 1
        print("selftest: publiceret men uklassificeret side fanget")
        lone.unlink()
        blocks += 1

        # 4. Intet publiceret træ. Uden dette fund ville kontrol 1-3 være
        #    vakuære, og gaten grøn på en egenskab den aldrig har prøvet.
        shutil.rmtree(base / "site-dist")
        if not [f for f in run(base) if "kan da ikke efterprøves" in f]:
            print("SELFTEST FEJLED: manglende publiceret træ blev ikke fanget")
            return 1
        print("selftest: manglende publiceret træ fanget")
        blocks += 1

        # ------------------------------------------------------------------
        # Opgave 37: rapporten over produkter uden side, i begge retninger.
        # ------------------------------------------------------------------
        publish(base)
        baseline = run(base)
        orphan = next((p for p in PRODUCTS if p["product_key"] == "eu-compliance-ebook-bundle"), None)
        if orphan is None:
            print("SELFTEST FEJLED: e-bog-bundlen står ikke i stripe_products.json")
            return 1
        listed = [key for key, _ in unsold_products(base / "site-dist")]
        if orphan["product_key"] not in listed:
            print("SELFTEST FEJLED: et produkt uden side blev ikke rapporteret — "
                  "rapporten er vakuær")
            return 1
        print(f"selftest: produkt uden side rapporteret ({orphan['product_key']})")
        blocks += 1

        # Den anden retning: en side med det **ærlige** link skal give nul fund
        # og fjerne produktet fra rapporten. Før denne opgave var det umuligt:
        # tillidslisten var en delmængde af kontrakten, så præcis dette link blev
        # rødt som "ikke i kontrakten" — kontrakten forbyder salget af et
        # produkt den selv opfører.
        blog = base / "site" / "blog" / "dora-for-ecommerce-2026" / "index.html"
        original_blog = blog.read_text(encoding="utf-8")
        blog.write_text(
            original_blog.replace(
                "</body>",
                f'<a class="btn" href="{orphan["url"]}">Buy the bundle — '
                f'${orphan["price_usd"]}</a></body>'),
            encoding="utf-8")
        publish(base)
        # Ikke "nul fund": en tidligere case har slettet den franske prisside, så
        # dens fund er med i baseline. Kravet er at mutationen ikke tilføjer
        # noget — det er den egenskab der testes, ikke træets tilstand.
        after = run(base)
        if after != baseline:
            print("SELFTEST FEJLED: en side med et kontraktprodukt-link ændrede fundene:")
            for f in after:
                if f not in baseline:
                    print(f"  + {f}")
            for f in baseline:
                if f not in after:
                    print(f"  - {f}")
            return 1
        if orphan["product_key"] in [key for key, _ in unsold_products(base / "site-dist")]:
            print("SELFTEST FEJLED: produktet stod stadig i rapporten med en side")
            return 1
        print("selftest: samme link på en side er lovligt og fjerner fundet")
        blocks += 1
        blog.write_text(original_blog, encoding="utf-8")
        publish(base)

    print(f"SELFTEST GRØN — alle {len(cases) + blocks} negative cases fanges")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    found = run(ROOT)
    if found:
        print("CTA-GATE RØD:")
        for f in found:
            print(f"  - {f}")
        print(f"\n{len(found)} fund. Ret dem, eller skriv bevidst om i PAGE_RULES.")
        return 1
    groups, _ = classify_tree(PUBLISHED)
    counts = " ".join(f"{len(v)} {k}" for k, v in sorted(groups.items()))
    print(f"CTA-gate grøn: {counts} — klassificeret i det publicerede træ, som "
          "er identisk med kilden. Kun kontraktfikserede checkout-links, "
          "købsknapper til kontraktprisen, én købsknap pr. salgsside, korrekte "
          "canonicals, symmetriske lokaler, 0 døde interne referencer, 0 "
          "uunderstøttede løfter.")
    unsold = unsold_products()
    if unsold:
        print("RAPPORT: kontraktprodukt uden side (tjener 0 kr, se spørgsmål 20 "
              "i planen — ikke et fund, fordi det ville stoppe deploy):")
        for key, label in unsold:
            print(f"  - {key} — {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
