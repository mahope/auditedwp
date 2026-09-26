#!/usr/bin/env python3
"""Gate for the købsvej: kun kontraktfikserede links, én købsknap pr. salgside,
korrekte canonicals, symmetriske lokaler og ingen løfter uden dækning.

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

import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

CANONICAL_ORIGIN = "https://eucomplypro.com"

# Kilde: business-kontrakten 24/9-2026. Ingen nye produkter, priser eller links
# oprettes; en side der linker noget uden for denne liste er en fejl, fordi den
# peger på en checkout der ikke findes.
PRO_CHECKOUT = "https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03"
TEMPLATE_CHECKOUTS = {
    "https://buy.stripe.com/bJe7sK8aT4My7dk7czbMQ05",  # eucomply-dpa
    "https://buy.stripe.com/4gM4gydvd92OapwgN9bMQ06",  # eucomply-nis2-clauses
    "https://buy.stripe.com/3cI7sK2Qz3IugNUgN9bMQ08",  # eucomply-eaa-statement
    "https://buy.stripe.com/aFafZg1Mv92OdBI8gDbMQ07",  # eucomply-nda-clauses
    "https://buy.stripe.com/00wdR8bn5a6S0OWeF1bMQ09",  # eucomply-report-kit
    "https://buy.stripe.com/eVqaEW0Iren855c68vbMQ0a",  # eucomply-template-bundle
}
DONATION = "https://donate.stripe.com/7sYeVcbn50wieFM8gDbMQ0c"
ALLOWED_CHECKOUTS = TEMPLATE_CHECKOUTS | {PRO_CHECKOUT, DONATION}

# Søskeprodukter på samne domæne. Hver har sit eget Stripeprodukt og sit eget
# repo, så deres checkout-links er ikke vores at begrænse her. Se spørgsmål 11.
# De findes både i topniveau og under de lokaliserede træer.
SIBLING_ROOTS = ("devnotify", "deskuptime", "transmute")

# Fragmenter der indgår i andre sider. De er ikke sider og har ingen canonical.
FRAGMENT_PREFIXES = ("_partials/", "shared/")

# Salgssider der SKAL have prissiden. Listen er kontraktet, ikke en søgning:
# en ny salgsside skal skrives her, ellers giver den ingen beskyttelse.
PRO_SALES_PAGES = (
    "index.html",
    "pro/index.html",
    "da/index.html",
    "da/pro/index.html",
    "de/index.html",
    "de/pro/index.html",
    "fr/index.html",
    "fr/pro/index.html",
    "checklist/index.html",
    "badge/index.html",
    "check-eu-compliance/index.html",
    "cookie-banner-check/index.html",
    "consent-mode-v2-check/index.html",
    "gdpr-compliance-check/index.html",
    "gdpr-scanner-free/index.html",
    "cli/index.html",
    "how-it-works/index.html",
    "compare/index.html",
    # Den gratis scanner er tragten: den side hvor læseren lige har set sine
    # egne fejl. Da den ikke stod her, havde den 0 købsankere i alle fire sprog,
    # og gaten var grøn. Se opgave 19.
    "scan/index.html",
    "da/scan/index.html",
    "de/scan/index.html",
    "fr/scan/index.html",
    # Pro-overfladen. `/plugin/` er den ENESTE side hvor Pro betales kan
    # leveres — dokumentgenereringen ligger i pluginen — og den havde 0
    # købsankere, kun donationen. Se opgave 21.
    "plugin/index.html",
    "pro/sample-report/index.html",
    "gdpr-fine-calculator/index.html",
)

# Sider hvis emne *er* et betalt skabelonprodukt. De skal sælge det produkt,
# ikke Pro: en EAA-checkliste der sælger en WordPress-licens er forkerte
# koordinater. Hver side skal have præcis én købsanker til sit eget produkt.
TEMPLATE_CTA_PAGES = {
    "eaa-checklist/index.html": "https://buy.stripe.com/3cI7sK2Qz3IugNUgN9bMQ08",
    "nis2-checklist/index.html": "https://buy.stripe.com/4gM4gydvd92OapwgN9bMQ06",
}

# Sider der med vilje ikke sælger. Udelad her, fordi gaten ellers ville kræve
# en købsknap på en side der skal holde sig til at fortælle sandheden.
NO_SALES_PAGES = {
    "404.html",
    "pro/thank-you/index.html",   # efter køb
    "terms/index.html",            # juridisk
    "privacy/index.html",          # juridisk
    "sample/index.html",           # arkiveret koncept, ikke et produkt
    "refund-policy-generator/index.html",  # nedlagt side
}

# Lokaliserede købssider der skal findes i alle tre sprog. Ens symmetri er
# acceptkriterium 1: en dansk læser må ikke miste en købsknap, en tysk har.
LOCALE_SALES_PATHS = ("index.html", "pro/index.html", "pricing/index.html")
LOCALES = ("da", "de", "fr")

# Købsrejsens sider: de steder, hvor et løfte om gratis prøveperiode, konto eller
# refund faktisk skader, fordi det står ved købsknappen. Blogindlæg og guides er
# redaktionelt indhold om andres forpligtelser — "a 14-day money-back guarantee
# converts better" i en artikel er rådgivning til læseren, ikke et løfte fra os,
# og en gate der rammer den ville gørede artiklen om emnet umulig at skrive.
PURCHASE_JOURNEY_PAGES = set(PRO_SALES_PAGES) | {
    f"{loc}/{rel}" for loc in LOCALES for rel in LOCALE_SALES_PATHS
} | {
    "terms/index.html",
    "pro/thank-you/index.html",
    "store/index.html",
    "template/index.html",
    "book/index.html",
}

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
CANONICAL_RE = re.compile(r'<link[^>]+rel="canonical"[^>]*>', re.I)
HREF_RE = re.compile(r'href="([^"]+)"')


def eucocomply_pages() -> list[Path]:
    """Alle EUComply-sider: site/** undtagen søskeprodukter og fragmenter."""
    pages = []
    for path in sorted(SITE.rglob("*.html")):
        rel = path.relative_to(SITE).as_posix()
        if rel in NO_SALES_PAGES:
            continue
        if rel.startswith(FRAGMENT_PREFIXES):
            continue
        parts = rel.split("/")
        if any(part in SIBLING_ROOTS for part in parts[:-1]):
            continue
        pages.append(path)
    return pages


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


def check_sales_cta() -> list[str]:
    """Hver afgrenset salgsside skal have prissiden — og kun den."""
    findings = []
    for rel in PRO_SALES_PAGES + tuple(TEMPLATE_CTA_PAGES):
        checkout = TEMPLATE_CTA_PAGES.get(rel, PRO_CHECKOUT)
        path = SITE / rel
        if not path.is_file():
            findings.append(f"{rel}: forventet salgsside mangler")
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


def check_forbidden_claims() -> list[str]:
    """Købsrejsens sider må ikke love noget, ingen kode dækker.

    Kun købsrejsen, ikke hele sitet: se kommentaren på PURCHASE_JOURNEY_PAGES.
    """
    findings = []
    for rel in sorted(PURCHASE_JOURNEY_PAGES):
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
    """Kør alle kontroller mod en given site-rod og samle fundene."""
    global SITE
    SITE = root / "site"
    found: list[str] = []
    for check in (
        check_checkout_contract,
        check_sales_cta,
        check_locale_parity,
        check_canonicals,
        check_dead_internal_hrefs,
        check_forbidden_claims,
    ):
        found.extend(check())
    return found


def _minimal_page(rel: str) -> str:
    """En minimal, helt korrekt salgsside for den givne sti."""
    tail = "" if rel == "index.html" else rel.replace("index.html", "")
    checkout = TEMPLATE_CTA_PAGES.get(rel)
    if checkout:
        label = "Buy the template — $39"
    else:
        checkout, label = PRO_CHECKOUT, "Buy Pro — 79 USD per website per year"
    return (
        f'<html><head><link rel="canonical" href="{CANONICAL_ORIGIN}/{tail}"></head>'
        f'<body><a class="btn" href="{checkout}">{label}</a>'
        "</body></html>"
    )


def selftest() -> int:
    """Gaten skal kunne fejle. Vi indplanter fejl og kræver at de fanges."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "repo"
        (base / "site").mkdir(parents=True)
        required = {f"{loc}/{rel}" for loc in LOCALES for rel in LOCALE_SALES_PATHS}
        required.update(PRO_SALES_PAGES)
        required.update(TEMPLATE_CTA_PAGES)
        required.update(NO_SALES_PAGES)
        for rel in sorted(required):
            path = base / "site" / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(_minimal_page(rel), encoding="utf-8")

        clean = run(base)
        if clean:
            print("SELFTEST FEJLED: et minimalt rent træ giver fund:")
            for f in clean:
                print(f"  - {f}")
            return 1
        print(f"selftest: rent træ ({len(required)} sider) giver 0 fund")

        def expect(label: str, needle: str, mutate, rel: str = "pro/index.html") -> bool:
            target = base / "site" / rel
            original = target.read_text(encoding="utf-8")
            target.write_text(mutate(original), encoding="utf-8")
            hit = [f for f in run(base) if needle in f]
            target.write_text(original, encoding="utf-8")
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

    print(f"SELFTEST GRØN — alle {len(cases) + 1} negative cases fanges")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    found = run(ROOT)
    if found:
        print("CTA-GATE RØD:")
        for f in found:
            print(f"  - {f}")
        print(f"\n{len(found)} fund. Ret dem, eller skriv bevidst om i contract-kommentaren.")
        return 1
    print("CTA-gate grøn: kun kontraktfikserede checkout-links, én købsknap pr. salgsside, "
          "korrekte canonicals, symmetriske lokaler, 0 døde interne referencer, 0 uunderstøttede løfter.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
