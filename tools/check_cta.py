#!/usr/bin/env python3
"""Gate for et lukket salg: intet købsspor i træet, og de lukkede sider er væk.

Siden 22/11-2026 er EUComply frosset som gratis open source. EUComply Pro,
skabelonerne og e-bog-bundlet sælges ikke længere, og Stripe-linkene er
deaktiveret. Denne gate var før den dag "gate for købsvejen": den krævede
præcis én købsanker til et kontraktfikseret Stripe-link på hver salgsside, en
pris der matchede `tools/stripe_products.json`, og at hver side var klassificeret
som pro, template, own, nosale, content eller free. Hver af de regler er nu
vendt, fordi de krævede det der er lukket.

Hvad gaten kræver nu:

  1. INTET KØBSSPOR. Ingen betalingslinks, priser, links til `/pricing/`,
     `/pro/`, `/store/` eller `/vs/`, JSON-LD offers over 0, købsknapper eller
     Pro-salgssprog. Definitionen bor i `tools/no_sales.py`, som alle porte
     deler. Den dømmer BÅDE kilde-træet (`site/`) og det der uploades
     (`site-dist/`), fordi en side kan ligge i det ene uden det andet.
  2. LUKKEDE SIDER ER VÆK, og hver sti har en 301 i `_redirects` til en side der
     findes (`pricing`, `pro/*`, `store/*`, `vs/*`, de tre sprog).
  3. FORSIDERNE har `id="frozen-notice"`, og den engelske siger "frozen as free
     open source". README nævner "frozen" og 2026-11-22, LICENSE er MIT 2026
     Mahope.
  4. DET PUBLICEREDE TRÆ er samme generation som kilden: en side i `site/` der
     ikke er publiceret kan ikke dømmes mod det en besøgende ser, og omvendt.
     (Det var den gamle gates fund 22, og det gælder stadig.)
  5. STRUKTUR: hver side har præcis én absolut canonical til sin egen sti, og
     ingen intern href peger på en side eller et asset der ikke findes.

Det der er SLETTET og hvorfor: PAGE_RULES-klassifikationen (pro/template/own/
nosale/content/free), kontrolleren af kontraktpriser, `data-product`-markeringerne,
sprogsymmetrien mellem tre prissider og "uunderstøttede løfter ved købsknappen".
De handlede alle om at en købsvej findes og er sand, og der er ingen købsvej.
Kontrollen mod døde "coming soon"-knapper og deaktiverede betalingsknapper er
slettet af samme grund: den er et særtilfælde af købsknapper, og `no_sales`
dømmer alle købsknapper.

Negativt testet: se `--selftest`. Scriptet skal kunne fejle, ellers er det ikke
en gate.

Brug:
    python3 tools/check_cta.py            # hele kontrollen
    python3 tools/check_cta.py --selftest # sæt fejl ind og kræv at de fanges
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent))
import no_sales  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

# Det træ, der faktisk uploades, og dermed det en besøgende kan se.
# `build_public_tree.py` samler det ud fra en POSITIVLISTE, så en side kan ligge
# i `site/` uden nogensinde at blive vist. Se `check_publish_alignment`.
PUBLISHED = ROOT / "site-dist"

CANONICAL_ORIGIN = "https://eucomplypro.com"

# Søskeprodukter på samme domæne. De har hver deres repo og hjemmeside og
# canonical på deres eget domæne, så strukturkontrollerne (canonical, døde
# referencer) gælder ikke dem. Købsspor-kontrollen gælder dem stadig.
SIBLING_ROOTS = ("devnotify", "deskuptime", "transmute")

# Fragmenter der indgår i andre sider. De er ikke sider og har ingen canonical.
FRAGMENT_PREFIXES = ("_partials/", "shared/")

# Sider der er undtaget fra strukturkontrollerne (canonical, døde referencer).
STRUCTURE_EXEMPT = frozenset({
    "404.html",
    "terms/index.html",
    "privacy/index.html",
    "sample/index.html",
    "refund-policy-generator/index.html",
})

CANONICAL_RE = re.compile(r'<link[^>]+rel="canonical"[^>]*>', re.I)
HREF_RE = re.compile(r'href="([^"]+)"')


def all_pages(base: Path) -> List[Path]:
    """Hele EUComply-træet: undtagen søskeprodukter og fragmenter."""
    pages = []
    for path in sorted(base.rglob("*.html")):
        rel = path.relative_to(base).as_posix()
        if rel.startswith(FRAGMENT_PREFIXES):
            continue
        parts = rel.split("/")
        if any(part in SIBLING_ROOTS for part in parts[:-1]):
            continue
        pages.append(path)
    return pages


def structure_pages(base: Path) -> List[Path]:
    return [p for p in all_pages(base) if p.relative_to(base).as_posix() not in STRUCTURE_EXEMPT]


def check_no_sales(site: Path, published: Path) -> List[str]:
    """Intet købsspor i kilden og i det der uploades.

    Kilden dømmes først. Det publicerede træ dømmes bagefter, og kun fund der
    ikke allerede står under kilden tæller igen, så en side der er rød begge
    steder ikke bliver talt dobbelt.
    """
    source = no_sales.scan_tree(site)
    findings = [f"site/{f}" for f in source]
    if published.is_dir():
        seen = set(source)
        findings.extend(f"site-dist/{f}" for f in no_sales.scan_tree(published) if f not in seen)
    return findings


def check_repo_files(root: Path) -> List[str]:
    return no_sales.repo_file_findings(root)


def check_publish_alignment(site: Path, published: Path) -> List[str]:
    """Det publicerede træ og kilde-træet skal være det samme sæt sider.

    `build_public_tree.py` samler sitet ud fra en positivliste. En side i kilden
    der ikke er på listen bliver aldrig set af nogen besøgende, så en gate der
    dømmer kilden dømmer noget andet end det der er live. Og et træ der mangler
    helt gør de øvrige kontroller vakuære, så det er et fund og ikke en advarsel.
    """
    if not published.is_dir():
        return [
            f"det publicerede træ {published.name}/ findes ikke — gaten kan da ikke "
            "dømme det der uploades. Kør `python3 tools/build_public_tree.py` først."
        ]
    source = {p.relative_to(site).as_posix() for p in all_pages(site)}
    live = {p.relative_to(published).as_posix() for p in all_pages(published)}
    findings: List[str] = []
    for rel in sorted(source - live):
        findings.append(
            f"{rel}: findes i site/ men er ikke i det publicerede træ — ingen besøgende "
            "kan nå den. Tilføj mappen til PUBLIC_DIRS i build_public_tree.py, eller slet siden."
        )
    for rel in sorted(live - source):
        findings.append(f"{rel}: publiceret men findes ikke i site/ — træerne er ikke samme generation. Genbyg site-dist/.")
    return findings


def check_canonicals(site: Path) -> List[str]:
    """Canonical skal være absolut og præcis sidens egen sti."""
    findings = []
    for path in structure_pages(site):
        rel = path.relative_to(site).as_posix()
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


def check_dead_internal_hrefs(site: Path) -> List[str]:
    """Ingen intern href må pege på en side eller et asset, der ikke findes."""
    findings = []
    for path in structure_pages(site):
        rel = path.relative_to(site).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for href in HREF_RE.findall(text):
            if not href.startswith("/") or href.startswith("//") or "#" in href:
                continue
            target = href.split("?")[0].rstrip("/")
            if target in ("", "/"):
                continue
            disk = site / target.lstrip("/")
            if disk.is_dir():
                disk = disk / "index.html"
            if disk.exists() or (site / (target.lstrip("/") + ".html")).exists() or (site / target.lstrip("/")).exists():
                continue
            if target.rsplit("/", 1)[-1].startswith("."):
                continue
            findings.append(f"{rel}: død intern reference {href}")
    return findings


def run(root: Path) -> List[str]:
    """Kør alle kontroller mod en given repo-rod og samle fundene."""
    site, published = root / "site", root / "site-dist"
    found: List[str] = []
    found.extend(check_publish_alignment(site, published))
    found.extend(check_no_sales(site, published))
    found.extend(check_repo_files(root))
    found.extend(check_canonicals(site))
    found.extend(check_dead_internal_hrefs(site))
    return found


# ---------------------------------------------------------------------------
# Selvtest: et rent fixture-træ er grønt, og hver regel kan gøre det rødt.
# ---------------------------------------------------------------------------
def _page(rel: str, body: str = "<p>Free scan.</p>", notice: str = "") -> str:
    tail = "" if rel == "index.html" else rel.replace("index.html", "")
    return (
        f'<!doctype html><html><head><link rel="canonical" href="{CANONICAL_ORIGIN}/{tail}">'
        f"</head><body>{notice}<main>{body}</main></body></html>"
    )


def _build_fixture(root: Path) -> None:
    """Et lille, helt korrekt træ: site/ og dets publicerede kopi site-dist/."""
    site = root / "site"
    no_sales._fixture(site)
    (site / "scan" / "index.html").write_text(_page("scan/index.html"), encoding="utf-8")
    for rel in ("index.html", "da/index.html", "de/index.html", "fr/index.html"):
        text = (site / rel).read_text(encoding="utf-8")
        tail = "" if rel == "index.html" else rel.replace("index.html", "")
        text = text.replace("<head>", f'<head><link rel="canonical" href="{CANONICAL_ORIGIN}/{tail}">', 1) \
            if "canonical" not in text else text
        (site / rel).write_text(text, encoding="utf-8")
    (root / "README.md").write_text("> Frozen as of 2026-11-22.\n", encoding="utf-8")
    (root / "LICENSE").write_text("MIT License\n\nCopyright (c) 2026 Mahope\n", encoding="utf-8")
    shutil.copytree(site, root / "site-dist")


def _selftest() -> int:
    failures: List[str] = []
    count = 0

    def fresh() -> Path:
        directory = Path(tempfile.mkdtemp(prefix="check-cta-"))
        _build_fixture(directory)
        return directory

    def edit(root: Path, rel: str, text: str, *, both: bool = True) -> None:
        for tree in (("site", "site-dist") if both else ("site",)):
            path = root / tree / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    def expect_red(name: str, root: Path, needle: str) -> None:
        nonlocal count
        count += 1
        found = run(root)
        if not any(needle in item for item in found):
            failures.append(f"{name}: forventede et fund med {needle!r}, fik {found[:3]}")

    # 1. Baseline: uden den er resten meningsløst.
    count += 1
    baseline = run(fresh())
    if baseline:
        failures.append(f"baseline: det rene træ skulle være grønt, fik {baseline[:3]}")

    # 2-6. Købsspor, i begge træer.
    root = fresh()
    edit(root, "scan/index.html", _page("scan/index.html", '<a href="https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03">x</a>'))
    expect_red("betalingslink", root, "betalingslink")

    root = fresh()
    edit(root, "scan/index.html", _page("scan/index.html", "<p>Pro costs $79 a year.</p>"))
    expect_red("pris", root, "pris")

    root = fresh()
    edit(root, "scan/index.html", _page("scan/index.html", '<a href="/pricing/">Pricing</a>'))
    expect_red("link til /pricing/", root, "lukkede side")

    root = fresh()
    edit(root, "scan/index.html", _page("scan/index.html", '<a class="btn" href="/scan/">Buy Pro</a>'))
    expect_red("købsknap", root, "købsknap")

    root = fresh()
    ld = '<script type="application/ld+json">{"@type":"Product","offers":{"@type":"Offer","price":"79"}}</script>'
    edit(root, "scan/index.html", _page("scan/index.html", ld))
    expect_red("JSON-LD offers med pris", root, "JSON-LD offers")

    # 7. Kun det publicerede træ har fejlen: den dømmes alligevel.
    root = fresh()
    edit(root, "scan/index.html", _page("scan/index.html", "<p>Pro costs $79 a year.</p>"), both=False)
    shutil.copy(root / "site" / "scan" / "index.html", root / "site" / "scan" / "ren.bak")
    (root / "site-dist" / "scan" / "index.html").write_text(
        _page("scan/index.html", '<a href="https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03">x</a>'), encoding="utf-8")
    (root / "site" / "scan" / "index.html").write_text(_page("scan/index.html"), encoding="utf-8")
    expect_red("fejl kun i det publicerede træ", root, "site-dist/scan/index.html")

    # 8-9. Lukkede sider og redirects.
    root = fresh()
    edit(root, "pricing/index.html", _page("pricing/index.html"))
    expect_red("den lukkede side findes igen", root, "findes stadig")

    root = fresh()
    edit(root, "_redirects", "/pricing/ /scan/ 301\n")
    expect_red("redirects mangler", root, "har ingen 301")

    # 10-11. Forsidens frys-note, README, LICENSE.
    root = fresh()
    edit(root, "index.html", _page("index.html"))
    expect_red("forside uden frozen-notice", root, "frozen-notice")

    root = fresh()
    (root / "README.md").write_text("# EUComply\n", encoding="utf-8")
    expect_red("README uden frys-linje", root, "README.md")

    root = fresh()
    (root / "LICENSE").unlink()
    expect_red("LICENSE mangler", root, "LICENSE")

    # 12-14. Struktur og publicering.
    root = fresh()
    edit(root, "scan/index.html", "<html><head></head><body><main><p>Free scan.</p></main></body></html>")
    expect_red("canonical mangler", root, "mangler canonical")

    root = fresh()
    edit(root, "scan/index.html", _page("scan/index.html", '<a href="/findes-ikke/">x</a>'))
    expect_red("død intern href", root, "død intern reference")

    root = fresh()
    (root / "site" / "extra").mkdir()
    (root / "site" / "extra" / "index.html").write_text(_page("extra/index.html"), encoding="utf-8")
    expect_red("side i kilden men ikke publiceret", root, "ikke i det publicerede træ")

    root = fresh()
    shutil.rmtree(root / "site-dist")
    expect_red("publiceret træ mangler", root, "findes ikke")

    # 15. Søskeprodukter: egen canonical og egne links, men betalingslinks dømmes.
    root = fresh()
    edit(root, "deskuptime/index.html", "<html><body><main><p>DeskUptime.</p></main></body></html>")
    count += 1
    found = run(root)
    if any("deskuptime" in item and "canonical" in item for item in found):
        failures.append("sibling: et søskendeprodukt skal ikke have EUComplys canonical-krav")
    edit(root, "deskuptime/index.html", "<main><a href=\"https://buy.stripe.com/7sY9AS9eX3Iu418fJ5bMQ01\">Buy</a></main>")
    expect_red("DeskUptime-betalingslink", root, "betalingslink")

    for failure in failures:
        print(f"SELFTEST FEJL: {failure}")
    print(f"SELFTEST {'GRØN' if not failures else 'RØD'} — {count - len(failures)}/{count} cases "
          "(rent træ grønt, hvert købsspor og hver strukturfejl rød)")
    return 0 if not failures else 1


def main(argv: List[str]) -> int:
    if "--selftest" in argv:
        return _selftest()
    findings = run(ROOT)
    for finding in findings:
        print(f"FUND  {finding}")
    if findings:
        print(f"\n{len(findings)} fund — salget er lukket 22/11-2026, og træet skal være det også")
        return 1
    print("intet købsspor; lukkede sider er væk og redirectet; forsiderne er frosset; canonicals og interne links holder")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
