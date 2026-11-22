#!/usr/bin/env python3
"""Port: en side der nævner en konkurrents pris skal vise hvornår og hvorfra.

Vi skriver om andres priser, og tallet tilhører en anden og kan være forkert i
morgen. Fire af otte konkurrentsider havde en forkert påstand da de blev læst mod
leverandørens egen prisside 28/9 (Termly "Pro $10/mo", Complianz "Personal EUR
59/år", Cookiebot "Essential $9/mo", Osano "priser er ikke offentlige", ...).
`tools/competitor_facts.json` er den eneste kilde til hvad vi påstår om andres
priser: hver konkurrent har en kilde (leverandørens egen prisside), en
`checked`-dato og om priserne overhovedet er offentlige.

Før 22/11-2026 dømte gaten de otte `vs/*`-sider celle for celle (R1-R7: hver
`data-competitor`-celle mod JSON, hvert tal mod en optegnelse, ingen valutatal for
en konkurrent uden offentlige priser). Siderne er slettet (salget er lukket, og
de var salgssider), og de regler handlede kun om dem, så de er slettet med dem.

Konkurrentpriserne på `/compare/` og `/cmp-comparison/` er det der er tilbage,
og de stod aldrig under cellereglerne: ingen `data-competitor`-markering. Gaten
kræver derfor det der kan kræves af en sammenligningsside uden markering:

  C1  En side der nævner en konkurrents pris (navn og valutatal i samme afsnit,
      punkt eller tabelrække) skal vise `as_of`-datoen fra JSON (ISO-format),
      så en læser kan se hvor gammelt tallet er.
  C2  Den skal linke mindst to af de kilder (leverandørens prisside) JSON
      kender, så tallet kan efterprøves.
  C3  `as_of` og hver `checked` må ikke være ældre end `stale_after_days`, ellers
      er optegnelsen for gammel til at tale om andres priser. Genlæs kilden.
  C4  Hver kilde i JSON er en https-adresse, og hver konkurrent har dato og kilde.

Tal der ikke er en konkurrents pris (hvad en audit koster) kræver intet. Selvtesten
beviser at hver regel kan gøre en fixture-side rød, og at en ren side er grøn.

Kør:
    python3 tools/check_competitor_facts.py
    python3 tools/check_competitor_facts.py --selftest
"""
import json
import pathlib
import re
import sys
import tempfile
from datetime import date, datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import no_sales  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
FACTS = ROOT / "tools" / "competitor_facts.json"
PAGES = ("compare/index.html", "cmp-comparison/index.html")
CURRENCY = re.compile(r"[$€£]\s?\d")
MIN_SOURCES = 2


def visible(html):
    body = re.search(r"<main[^>]*>(.*?)</main>", html, re.S)
    scope = body.group(1) if body else html
    scope = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", scope, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", scope)).strip()


def fact_findings(facts, today):
    """C3 og C4: optegnelserne selv."""
    findings = []
    stale_after = int(facts.get("stale_after_days", 180))
    dated = [("as_of", facts.get("as_of"))] + [
        (f"{slug}.checked", fact.get("checked")) for slug, fact in facts.get("competitors", {}).items()
    ]
    for label, value in dated:
        try:
            age = (today - datetime.strptime(value, "%Y-%m-%d").date()).days
        except (TypeError, ValueError):
            findings.append(f"C3 competitor_facts.json: {label}={value!r} er ikke en ISO-dato")
            continue
        if age > stale_after:
            findings.append(f"C3 competitor_facts.json: {label} er {age} dage gammel (grænsen er {stale_after}) — genlæs kilden")
    for slug, fact in facts.get("competitors", {}).items():
        source = str(fact.get("source", ""))
        if not source.startswith("https://") or not fact.get("checked"):
            findings.append(f"C4 competitor_facts.json: {slug} mangler en https-kilde eller en checked-dato")
    return findings


ROW = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.I | re.S)


def names_a_price(html, facts):
    """Står en konkurrents navn og et valutatal i samme afsnit, punkt eller tabelrække?

    Det er det der gør et tal til "en andens pris". `/compare/` har også tal der
    ikke er det (hvad en audit koster), og dem skal siden ikke kilde.
    """
    names = [re.compile(r"\b" + re.escape(fact["name"]) + r"\b", re.I)
             for fact in facts.get("competitors", {}).values() if fact.get("name")]
    units = list(no_sales.parse_blocks(html).blocks)
    units += [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", row)) for row in ROW.findall(html)]
    return any(CURRENCY.search(unit) and any(name.search(unit) for name in names) for unit in units)


def page_findings(rel, html, facts):
    """C1 og C2: en side med en konkurrents pris viser dato og kilde."""
    text = visible(html)
    if not names_a_price(html, facts):
        return []
    findings = []
    as_of = facts.get("as_of", "")
    if as_of not in text:
        findings.append(f"C1 {rel}: siden nævner priser, men viser ikke datoen {as_of} de er læst fra leverandørernes egne sider")
    linked = sum(1 for fact in facts.get("competitors", {}).values() if fact.get("source") and fact["source"] in html)
    if linked < MIN_SOURCES:
        findings.append(f"C2 {rel}: siden nævner priser, men linker kun {linked} af leverandørernes prissider (kræver {MIN_SOURCES})")
    return findings


def run(root, facts, today):
    findings = fact_findings(facts, today)
    pages = [root / rel for rel in PAGES if (root / rel).is_file()]
    for path in pages:
        findings.extend(page_findings(path.relative_to(root).as_posix(),
                                      path.read_text(encoding="utf-8", errors="replace"), facts))
    return findings, len(pages)


def main():
    if not FACTS.exists():
        print(f"FEJL: {FACTS} mangler")
        return 1
    facts = json.loads(FACTS.read_text(encoding="utf-8"))
    findings, pages = run(ROOT / "site", facts, date.today())
    if findings:
        print(f"KONKURRENTFAKTA: {len(findings)} fund")
        for finding in findings:
            print(f"  {finding}")
        return 1
    print(f"KONKURRENTFAKTA OK — {pages} sammenligningssider, {len(facts['competitors'])} optegnelser, datoen og kilderne står på siderne")
    return 0


def selftest():
    """Hver regel skal kunne gøre en side rød, og en ren side skal være grøn."""
    facts = json.loads(FACTS.read_text(encoding="utf-8"))
    sources = [fact["source"] for fact in facts["competitors"].values()]
    as_of = facts["as_of"]
    today = date.today()
    cases = 0
    failures = []

    def page(price="€59/yr", with_date=True, linked=2):
        links = "".join(f'<a href="{src}">pris</a>' for src in sources[:linked])
        note = f"Prices read from vendors' own pages {as_of}." if with_date else "Prices read from vendors' own pages."
        return f"<html><body><main><p>Cookiebot {price}</p><p>{note} {links}</p></main></body></html>"

    def expect(name, html, needle, when=today, changed=None):
        nonlocal cases
        cases += 1
        use = changed if changed is not None else facts
        directory = pathlib.Path(tempfile.mkdtemp(prefix="competitor-"))
        (directory / "compare").mkdir()
        (directory / "compare" / "index.html").write_text(html, encoding="utf-8")
        findings, _pages = run(directory, use, when)
        if needle is None:
            if findings:
                failures.append(f"{name}: skulle være grøn, fik {findings[:2]}")
        elif not any(needle in finding for finding in findings):
            failures.append(f"{name}: forventede {needle!r}, fik {findings[:2]}")

    expect("en ren side er grøn", page(), None)
    expect("C1 siden viser ikke datoen", page(with_date=False), "C1")
    expect("C2 siden linker ingen kilder", page(linked=0), "C2")
    expect("C2 siden linker for få kilder", page(linked=1), "C2")
    expect("en side uden valutatal kræver intet", page(price="free", with_date=False, linked=0), None)
    expect("et valutatal der ikke er en konkurrents pris kræver intet",
           "<html><body><main><p>A manual audit costs $500 per site.</p></main></body></html>", None)
    expect("en konkurrentpris i en tabelrække kræver dato og kilde",
           "<html><body><main><table><tr><td>Cookiebot</td><td>$10/mo</td></tr></table></main></body></html>", "C1")
    expect("C3 en gammel optegnelse", page(), "C3", when=date(2030, 1, 1))
    broken = json.loads(json.dumps(facts))
    broken["as_of"] = "ikke en dato"
    expect("C3 en dato der ikke er en dato", page(), "C3", changed=broken)
    broken = json.loads(json.dumps(facts))
    first = next(iter(broken["competitors"]))
    broken["competitors"][first]["source"] = "http://example.com"
    expect("C4 en kilde uden https", page(), "C4", changed=broken)

    for failure in failures:
        print(f"SELFTEST FEJLT: {failure}")
    print(f"SELFTEST {'GRØN' if not failures else 'RØD'} — {cases - len(failures)}/{cases} cases")
    return 0 if not failures else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main())
