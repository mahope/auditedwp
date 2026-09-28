#!/usr/bin/env python3
"""Port: en indekserbar side skal sta i sitemap.xml — ellers er den usynlig.

    python3 tools/check_sitemap.py
    python3 tools/check_sitemap.py --selftest

Malt 28/9. `site/sitemap.xml` havde 209 `<loc>`, og det publicerede trae
havde 223 sider. De 14 der manglede saa ikke alle ud som en fejl — 13 af dem
er `noindex` og skal *da* ikke i sitemap: `/search/`, de tre locale-søgninger,
`/pro/dashboard/`, `/pro/thank-you/`, `/tools/` og de fem generator-sider.
Men **en** af dem var ikke noindex:

    /api/    ingen robots-meta overhovedet, altsaa indekserbar, publiceret
             (den ligger i build_public_tree.py's PUBLIC_DIRS), fuld
             dokumentation med fire `data-endpoint`, to `<pre>` med
             færdig kode, JSON-eksempel og en købsknap — og den laa ikke i
             sitemap.xml.

Det er den dør, hele API-argumentationen hænger paa. `check_api_docs.mjs`
sørger for at *siden* findes og at den publiceres; ingen port spurgte nogen
sindes om den er *meldt til nogen*. Den har heller ingen `hreflang`, saa den
kan heller ikke findes via en dansk, tysk eller fransk søgning.

Saa porten dømmer symmetrien, fordi begge retninger er fejl:

  R1  En publiceret side der er indekserbar (ingen `noindex`) skal have en
      `<loc>` i sitemap.xml. R1 er den der fangede `/api/`.
  R2  En `<loc>` skal være en side der faktisk findes i det publicerede
      trae. En sitemap-peger paa en død adresse, og den dør stille.
  R3  En `<loc>` skal være præcis sidens egen `rel=canonical`. Samme side
      under to adresser i sitemap'en er to sider for søgemaskinen, og den
      ene uden `<lastmod>`-værdi.
  R4  En `noindex`-side må **ikke** sta i sitemap.xml. Ellers beder vi om at
      blive indekseret og forbyder det i samme linje, og de 13 korrekte
      undtagelser bliver umulige at skelne fra de nye fejl.

R1-R4 loeser intet op i sig selv. De gør fundet permanent, saa den næste
indekserbare side der kommer op ikke kan forsvinde i samme stilhed igen.

Sidernes liste laeses fra `build_public_tree.py`s egen PUBLIC_DIRS, saa
porten ikke har en kopi af den sande liste — ellers kunne de to glide fra
hinanden, og en forældet kopi ville faar porten til at dømme sider der ikke
engang udgives.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
SITEMAP = SITE / "sitemap.xml"
ORIGIN = "https://eucomplypro.com"

ROBOTS = re.compile(r'<meta\s+name="robots"\s+content="([^"]*)"', re.I)
CANONICAL = re.compile(r'<link\s+rel="canonical"\s+href="([^"]+)"', re.I)
LOC = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>")


def public_dirs():
    """Spejl `build_public_tree.py`: den ene liste over det der publiceres."""
    source = (ROOT / "tools" / "build_public_tree.py").read_text()
    block = re.search(r"PUBLIC_DIRS = \(([^)]*)\)", source, re.S)
    if not block:
        raise SystemExit("FEJL: PUBLIC_DIRS kunne ikke læses fra build_public_tree.py")
    return set(re.findall(r'"([^"]+)"', block.group(1)))


def robots_of(html):
    m = ROBOTS.search(html.split("</head>", 1)[0])
    return m.group(1).lower() if m else ""


def url_for(rel):
    return ORIGIN + "/" if rel == "." else f"{ORIGIN}/{rel}/"


def collect_pages():
    """{url: (rel, indexable, canonical)} for hver publiceret side."""
    allowed = public_dirs()
    pages = {}
    for index in SITE.rglob("index.html"):
        rel = index.parent.relative_to(SITE).as_posix()
        if rel != "." and rel.split("/", 1)[0] not in allowed:
            continue
        head = index.read_text(errors="replace").split("</head>", 1)[0]
        canonical = CANONICAL.search(head)
        pages[url_for(rel)] = (rel, "noindex" not in robots_of(head), canonical.group(1) if canonical else "")
    return pages


def findings(pages, sitemap_text):
    locs = LOC.findall(sitemap_text)
    listed = set(locs)
    f = []
    for url, (rel, indexable, _) in sorted(pages.items()):
        # R1 — indekserbar, publiceret, men aldrig meldt.
        if indexable and url not in listed:
            f.append(f"R1 {rel}/ er indekserbar men staar ikke i sitemap.xml")
    known = set(pages)
    for url in locs:
        # R2 — sitemap peger paa noget der ikke findes.
        if url not in known:
            f.append(f"R2 sitemap.xml har en <loc> uden side: {url}")
            continue
        # R3 — samme side under en anden adresse end dens egen canonical.
        canonical = pages[url][2]
        if canonical and canonical != url:
            f.append(f"R3 sitemap.xml siger {url}, men sidens canonical er {canonical}")
        # R4 — vi beder om indeksering og forbyder den i samme linje.
        if not pages[url][1]:
            f.append(f"R4 {pages[url][0]}/ er noindex men staar i sitemap.xml")
    return f


def selftest():
    """Bevis at porten kan fejle. Fire muteringer mod de virkelige filer."""
    pages = collect_pages()
    real = SITEMAP.read_text()
    cases = []

    def case(name, mutate_pages=None, mutate_sitemap=None):
        p = dict(pages)
        s = real
        if mutate_pages:
            p = mutate_pages(p)
        if mutate_sitemap:
            s = mutate_sitemap(s)
        found = findings(p, s)
        cases.append((name, found))

    # R1: fjern /api/ igen -> porten skal sige det.
    api = url_for("api")
    case("R1 indekserbar side fjernet fra sitemap",
         mutate_sitemap=lambda s: s.replace(f"<loc>{api}</loc>", "<loc>https://eucomplypro.com/cli/</loc>"))
    # R1b: en helt ny indekserbar side, som aldrig har været i sitemap.
    case("R1 ny indekserbar side aldrig meldt",
         mutate_pages=lambda p: {**p, f"{ORIGIN}/ny-side/": ("ny-side", True, f"{ORIGIN}/ny-side/")})
    # R2: en <loc> uden side.
    case("R2 <loc> uden side",
         mutate_sitemap=lambda s: s.replace("</urlset>", f"  <url><loc>{ORIGIN}/findes-ikke/</loc></url>\n</urlset>"))
    # R3: en <loc> der ikke er sidens egen canonical.
    case("R3 <loc> uden trailing slash",
         mutate_sitemap=lambda s: s.replace(f"<loc>{api}</loc>", f"<loc>{ORIGIN}/api</loc>"))
    # R4: en noindex-side i sitemap.
    case("R4 noindex-side i sitemap",
         mutate_sitemap=lambda s: s.replace("</urlset>", f"  <url><loc>{ORIGIN}/search/</loc></url>\n</urlset>"))

    passed = 0
    for name, found in cases:
        if found:
            passed += 1
        else:
            print(f"SELFTEST FEJLT: {name} blev ikke fanget")
    print(f"SELFTEST {'GRØN' if passed == len(cases) else 'RØD'} — {passed}/{len(cases)} negative cases fanges")
    return 0 if passed == len(cases) else 1


def main():
    pages = collect_pages()
    f = findings(pages, SITEMAP.read_text())
    indexable = sum(1 for _, (_, ix, _) in pages.items() if ix)
    print(f"publicerede sider: {len(pages)} — {indexable} indekserbare, sitemap-loc: {len(LOC.findall(SITEMAP.read_text()))}")
    if not f:
        print("SITEMAP GRØN — hver indekserbar side er meldt, og hver <loc> er en virkelig side.")
        return 0
    for line in f:
        print(f"FEJL {line}")
    return 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main())
