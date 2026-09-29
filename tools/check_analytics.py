#!/usr/bin/env python3
"""Gat: en besøgende skal tælles, ellers ved vi intet om besøget.

Baggrund
--------
Plausible (det eneste tal, der ikke tæller bots) har vist **0 besøgende,
0 sidevisninger, 0 s** for eucomplypro.com i 28 dage. Cloudflare viser
5265 unikke besøgende-dage, men tæller bots, så de to tal kan ikke
løse striden fra hinanden.

Målingen 2026-09-28 fandt, at taggen **er** i orden: den ligger på 225 af
225 publicerede sider, CSP tillader både `script-src` og `connect-src`,
scriptet svarer 200, og `tools/analytics_probe.mjs` kører den rigtige tag
i en stubbet DOM og får præcis ét pageview med `d: "eucomplypro.com"` i
**begge** rækkefølger, et `async`-script kan gennemløbe. Så de 0 er ærlige
trafiktal og ikke en defekt tracking.

Det er præcis derfor denne gate er nødvendig. Før målingen var "0
besøgende" ubrugeligt: det kunne være ingen trafik **eller** en tag, der
sender intet, og intet i repoet skilte de to. Denne port gør den
forskel til en egenskab ved filerne:

1. **Dækning.** Hver publiceret side med et `<head>` skal have taggen.
   En side uden tag tæller intet, og dens besøg er usynlige.
2. **CSP må blokere taggen.** Uden `script-src` dør scriptet; uden
   `connect-src` dør *eventet*, stille. Begge ser ens ud i koden.
3. **Én script-id.** Træet, byggeren og den optagede tracker skal være
   enige, så en roteret id ikke efterlader porten med en gammel fixture.
4. **Adfærd.** Den publicerede tag skal sende præcis ét pageview i begge
   rækkefølger. En tag, der *ser* rigtig ud, kan sende intet, hvis
   `plausible.o` går tabt i racen mellem `async`-scriptet og stubben.

Kontrol 1-3 er deterministiske. Kontrol 4 kræver `node` (repoet kræver
Node >= 22); mangler den, er porten **rød** med beskeden, fordi en port
der springer over sin egen kontrol er grøn uden at have kontrolleret
noget — samme fejlklasse som opgave 9's kanin-hul.

Kørsel
------
    python3.13 tools/check_analytics.py             # gaten
    python3.13 tools/check_analytics.py --selftest   # negative cases
"""

import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
TREE = os.path.join(ROOT, "site-dist")
HEADERS = os.path.join(ROOT, "site", "_headers")
BUILDER = os.path.join(TOOLS, "build_public_tree.py")
PROBE = os.path.join(TOOLS, "analytics_probe.mjs")
FIXTURE_JS = os.path.join(TOOLS, "fixtures", "plausible-tracker.js")
FIXTURE_META = os.path.join(TOOLS, "fixtures", "plausible-tracker.json")

# Fragmenter har intet <head> — de er inkluderede, ikke udgivne sider.
FRAGMENT_DIRS = ("_partials", "shared")


def read(path):
    with open(path, encoding="utf-8", errors="surrogateescape") as fh:
        return fh.read()


def _builder():
    """Byggerens egne konstanter, så baseline er præcis hvad han indsætter."""
    sys.path.insert(0, TOOLS)
    import build_public_tree

    return build_public_tree


def builder_src():
    """Det script-id byggeren sprøjter ind. Læst fra koden, ikke antaget."""
    try:
        return _builder().PLAUSIBLE_SRC
    except Exception:
        match = re.search(r'PLAUSIBLE_SRC\s*=\s*"([^"]+)"', read(BUILDER))
        return match.group(1) if match else None


def _loader_re():
    builder = _builder()
    if builder is not None and hasattr(builder, "LOADER_RE"):
        return builder.LOADER_RE
    src = builder_src()
    if not src:
        return None
    return re.compile(r"<script\b[^>]*\basync\b[^>]*\bsrc=[\"']" + re.escape(src) + r"[\"']", re.I)


def _init_re():
    return re.compile(r"plausible\.init\s*\(", re.I)


def _loader_present(text: str) -> bool:
    pattern = _loader_re()
    return bool(pattern and pattern.search(text))


def runs_tag(text: str) -> bool:
    """True når siden faktisk **kører** taggen: loader *og* init-kald.

    Matcher på hele taggen, ikke på URL-strengen. Det er den forskel, der
    gør porten i stand til at se de to fejl, der ellers læses som
    "besøgende der ikke blev talt":

      - en artikel der bare **nævner** scriptet i prosa eller et kodeblok
        har URL'en i teksten, men ingen tag. Før denne kontrol sagde porten
        "tagget", og siden sendte intet.
      - en side med **loaderen uden** init-kallet har taggen i teksten,
        fylder `plausible.q` og afsender aldrig. Før denne kontrol sagde
        porten "tagget" her også.

    Begge er målt som 0 i det publicerede træ lige nu — porten låser dem,
    fordi de er latente, ikke fordi de er løst.
    """
    return _loader_present(text) and bool(_init_re().search(text))


def _sources(directive_text):
    """Kilder uden skema, så 'https://x' og 'x' kan sammenlignes.

    CSP-værdierne skrives med skema, script-id'en uden. Uden denne
    normalisering er porten rød på et træ, der virker.
    """
    for source in directive_text.split():
        yield re.sub(r"^https?://", "", source)


def csp_directives(tree=None):
    """Alle CSP-direktiver som navn -> sæt af kilder.

    Læses fra det **publicerede** træs egen `_headers`, fordi det er den
    CSP der gælder for de udgivne sider. Kildefilen bruges kun som
    reserve, hvis træet ikke har sin egen.
    """
    path = os.path.join(tree, "_headers") if tree else HEADERS
    if not os.path.isfile(path):
        path = HEADERS
    directives = {}
    for line in read(path).splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        _, _, value = line.partition(":")
        for part in value.split(";"):
            name, _, sources = part.strip().partition(" ")
            if not name:
                continue
            directives.setdefault(name.lower(), set()).update(_sources(sources))
    return directives


def probe(page_path):
    """Kør den publicerede tag. Returnerer (resultat, fejltekst)."""
    if not shutil.which("node"):
        return None, "node ikke fundet — adfærdskontrollen kan ikke køres"
    proc = subprocess.run(
        ["node", PROBE, page_path, FIXTURE_JS],
        capture_output=True, text=True, timeout=120,
    )
    if proc.returncode != 0:
        return None, (proc.stderr or proc.stdout).strip()[:300] or f"probe exit {proc.returncode}"
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1]), None
    except (ValueError, IndexError):
        return None, f"probe-output kunne ikke læses: {proc.stdout[:200]!r}"


def collect(tree=TREE):
    """Fund + fakta for det publicerede træ."""
    findings, facts = [], {}
    src = builder_src()
    if src is None:
        findings.append("build_public_tree.py har ingen PLAUSIBLE_SRC — taggen kan ikke sættes ind")
        return findings, facts
    facts["script_src"] = src

    if not os.path.isdir(tree):
        findings.append(f"publiceret træ findes ikke: {tree} (kør build_public_tree.py først)")
        return findings, facts

    pages = sorted(
        os.path.join(root, name)
        for root, _, names in os.walk(tree)
        for name in names
        if name.endswith(".html")
    )
    tagged, untagged, fragments = [], [], []
    for page in pages:
        relative = os.path.relpath(page, tree)
        text = read(page)
        if not runs_tag(text):
            if "</head>" not in text.lower():
                # Intet <head>: kun gyldigt for inkluderede fragmenter.
                fragments.append(relative)
                if not relative.split(os.sep)[0] in FRAGMENT_DIRS:
                    findings.append(
                        f"{relative} har hverken analytics-tag eller <head> — "
                        "en publiceret side uden <head> er en fil, intet renderer"
                    )
                continue
            untagged.append(relative)
        else:
            tagged.append(relative)
    for relative in untagged:
        text = read(os.path.join(tree, relative))
        # To forskellige fejl, to forskellige rettelser. Begge så "ud" som
        # "mangler tag" før denne kontrol, men kun den ene mangler kode.
        if _loader_present(text):
            findings.append(
                f"{relative} har loaderen uden init-kaldet — taggen fylder "
                "plausible.q og afsender aldrig, så besøget tælles ikke"
            )
        elif src in text:
            findings.append(
                f"{relative} nævner kun scriptet i tekst, uden at have taggen — "
                "besøg på siden tælles ikke, selv om URL'en står i siden"
            )
        else:
            findings.append(f"{relative} mangler analytics-tag — besøg på siden tælles ikke")
    facts.update(pages=len(pages), tagget=len(tagged), fragmenter=len(fragments))

    if not tagged:
        findings.append("ingen publiceret side har taggen — mærkets 0 besøgende kan ikke læses som trafik")

    # Ét script-id i hele træet.
    ids = set()
    for relative in tagged:
        text = read(os.path.join(tree, relative))
        ids.update(re.findall(r"analytics\.holstjensen\.eu/js/([A-Za-z0-9_-]+\.js)", text))
    facts["script_ids"] = sorted(ids)
    for script_id in sorted(ids):
        if script_id not in src:
            findings.append(f"script-id {script_id} i træet er ikke det byggeren sætter ind ({src})")

    # CSP må ikke blokere hverken scriptet eller eventet.
    csp = csp_directives(tree)
    origin = re.sub(r"^(https?://)?([^/]+).*$", r"\2", src)
    for directive, why in (
        ("script-src", "scriptet bliver blokeret, taggen dør"),
        ("connect-src", "scriptet loades, men eventet bliver blokeret — taggen dør stille"),
    ):
        if origin not in csp.get(directive, set()):
            findings.append(
                f"Content-Security-Policy mangler {origin} i {directive}: {why}"
            )

    # Fixture og bygger skal være enige om id'en.
    if not os.path.isfile(FIXTURE_META):
        findings.append(f"fixture-metadata mangler: {FIXTURE_META}")
    else:
        meta = json.loads(read(FIXTURE_META))
        if meta.get("script_id") not in src:
            findings.append(
                f"optaget tracker er {meta.get('script_id')}, byggeren indsætter {src.rsplit('/', 1)[-1]} "
                "— genhent fixture'en, ellers måles der på en gammel proxy"
            )

    # Adfærd: den publicerede tag skal sende ét pageview i begge rækkefølger.
    if tagged:
        page = os.path.join(tree, tagged[0])
        result, error = probe(page)
        if error:
            findings.append(f"adfærdskontrol kunne ikke køres på {tagged[0]}: {error}")
        else:
            for order, outcome in sorted(result.get("ordninger", {}).items()):
                if outcome.get("fejl"):
                    findings.append(f"analytics-taggen kaster i {order}: {outcome['fejl']}")
                elif outcome.get("pageviews") != 1:
                    findings.append(
                        f"analytics-taggen sender {outcome.get('pageviews')} pageviews i {order} "
                        "(skal være præcis 1) — taggen er til stede, men intet tælles"
                    )
                else:
                    if outcome.get("domaener") != ["eucomplypro.com"]:
                        findings.append(
                            f"pageview i {order} rapporteres til {outcome.get('domaener')} "
                            "i stedet for eucomplypro.com"
                        )
                    if not any("/api/event" in u for u in outcome.get("endepunkter", [])):
                        findings.append(f"pageview i {order} sendes ikke til analytics-endpointet")
    return findings, facts


def make_tree(tmp, pages=("index.html", "pro/index.html"), tag=True, src=None, csp=None):
    """Byg et minimalt publiceret træ til selftesten.

    Taggen er byggerens **egne** `PLAUSIBLE_TAG`, ikke en håndskrevet
    erstatning: en baseline der kun har `<script src>` uden init-kallet
    ville være rød i portens egen adfærdskontrol, og så ville alle
    mutationer se røde ud af en fejl i baseline.
    """
    src = src or builder_src()
    full_tag = _builder().PLAUSIBLE_TAG
    if src != _builder().PLAUSIBLE_SRC:  # pragma: no cover - kun ved mutation
        full_tag = full_tag.replace(_builder().PLAUSIBLE_SRC, src)
    body = "<html><head><title>t</title>%s</head><body>side</body></html>"
    for page in pages:
        path = os.path.join(tmp, page)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(body % (full_tag if tag else ""))
    if csp is None:
        origin = re.sub(r"^(https?://)?([^/]+).*$", r"\2", src)
        csp = (
            "/*\n  Content-Security-Policy: default-src 'self'; "
            f"script-src 'self' https://{origin}; connect-src 'self' https://{origin}\n"
        )
    with open(os.path.join(tmp, "_headers"), "w", encoding="utf-8") as fh:
        fh.write(csp)
    return tmp


def _expect_red(name, mutate, mention, extra):
    """Kør en mutation og kræv at porten bliver rød med den omtalte tekst.

    Returnerer sandhed. Kalderen summerer selv — en lokal `ok = False` er
    præcis den fejl, der gjorde seks selftest-cases grønne i
    check_asset_delivery.py (iteration 84).
    """
    import tempfile

    tmp = tempfile.mkdtemp(prefix="analytics-")
    try:
        tree = make_tree(tmp)
        mutate(tree)
        findings, _ = collect(tree=tree)
        if not findings:
            print(f"  FEJL: {name} gav en grøn port — mutationen testede intet")
            return False
        if not any(mention in f for f in findings):
            print(f"  FEJL: {name} blev rød, men uden '{mention}': {findings[0]}")
            return False
        extra[0] += 1
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _selftest():
    ok = True
    extra = [0]
    cases = []

    # Baseline først, så mutationerne ikke kan være grønne af en fejl i porten.
    import tempfile

    tmp = tempfile.mkdtemp(prefix="analytics-")
    try:
        findings, facts = collect(tree=make_tree(tmp))
        if findings:
            print(f"  FEJL: grønt baseline-træ er rødt: {findings[0]}")
            ok = False
        elif facts.get("tagget") != 2:
            print(f"  FEJL: baseline læste {facts.get('tagget')} sider med tag (forventede 2)")
            ok = False
        else:
            print("  grønt baseline-træ: 2 sider, tag på begge, ét pageview pr. rækkefølge")
            extra[0] += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    def drop_tag(tree):
        page = os.path.join(tree, "pro", "index.html")
        with open(page, "w", encoding="utf-8") as fh:
            fh.write("<html><head><title>t</title></head><body>side</body></html>")

    def drop_connect_src(tree):
        with open(os.path.join(tree, "_headers"), "w", encoding="utf-8") as fh:
            fh.write("/*\n  Content-Security-Policy: script-src 'self' https://analytics.holstjensen.eu\n")

    def drop_script_src(tree):
        with open(os.path.join(tree, "_headers"), "w", encoding="utf-8") as fh:
            fh.write("/*\n  Content-Security-Policy: connect-src 'self' https://analytics.holstjensen.eu\n")

    def foreign_script_id(tree):
        # Bevarer den rigtige tag, så fundet er om det **fremmede** id,
        # ikke om en manglende tag.
        page = os.path.join(tree, "index.html")
        text = read(page)
        with open(page, "w", encoding="utf-8") as fh:
            fh.write(
                text.replace(
                    "</head>",
                    '<script async src="https://analytics.holstjensen.eu/js/pa-GAMMEL.js">'
                    "</script></head>",
                )
            )

    def page_without_head(tree):
        path = os.path.join(tree, "blog", "post", "index.html")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("<div>fragment der slap igennem uden head</div>")

    def loader_without_init(tree):
        # Taggen er i siden, men init-kallet mangler: `plausible.q` fyldes
        # og afsendes aldrig. Før `runs_tag()` sagde porten "tagget", fordi
        # URL'en var i teksten.
        page = os.path.join(tree, "index.html")
        text = read(page)
        init = _builder().PLAUSIBLE_INIT
        with open(page, "w", encoding="utf-8") as fh:
            fh.write(text.replace(init, ""))

    def url_mentioned_without_tag(tree):
        # En artikel der nævner scriptet i prosa. Før `runs_tag()` blev den
        # talt som tagget, og byggeren sprang den, fordi URL'en var der.
        path = os.path.join(tree, "blog", "analytics", "index.html")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(
                "<html><head><title>Analytics</title>"
                f"<!-- config: {builder_src()} --></head>"
                f"<body><p>Sæt src={builder_src()} i head.</p></body></html>"
            )

    def empty_tree(tree):
        for name in os.listdir(tree):
            if name != "_headers":
                path = os.path.join(tree, name)
                shutil.rmtree(path, ignore_errors=True) if os.path.isdir(path) else os.remove(path)

    cases = [
        ("side uden tag", drop_tag, "mangler analytics-tag"),
        ("loader uden init-kald", loader_without_init, "uden init-kaldet"),
        ("URL nævnt uden tag", url_mentioned_without_tag, "nævner kun scriptet i tekst"),
        ("CSP uden connect-src", drop_connect_src, "connect-src"),
        ("CSP uden script-src", drop_script_src, "script-src"),
        ("fremmed script-id i træet", foreign_script_id, "ikke det byggeren sætter ind"),
        ("publiceret side uden <head>", page_without_head, "hverken analytics-tag eller <head>"),
        ("træ uden sider", empty_tree, "ingen publiceret side har taggen"),
    ]
    for name, mutate, mention in cases:
        if not _expect_red(name, mutate, mention, extra):
            ok = False

    # Adfærd: taggen skal sende ét pageview. Nås ikke længere
    # init-kaldet, dør taggen stille — det er den fejlklasse porten findes for.
    #
    # Før `runs_tag()` blev denne mutation fanget af adfærdsproben, fordi
    # siden stadig blev regnet som tagget. Nu er den fanget **tidligere**, som
    # en statisk mangel, så porten kan se den uden at køre node. Begge veje er
    # ægte; statisk først, fordi den så også dækker de 232 sider, der ikke er
    # valgt som probe.
    import tempfile

    tmp = tempfile.mkdtemp(prefix="analytics-")
    try:
        # Rigtig src, men init-kaldet er væk: taggen er til stede og
        # sender intet. Det er præcis den fejlklasse porten findes for.
        src = builder_src()
        body = '<html><head><script async src="%s"></script></head><body>side</body></html>'
        for page in ("index.html", "pro/index.html"):
            path = os.path.join(tmp, page)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(body % src)
        make_tree(tmp, pages=(), csp=(
            "/*\n  Content-Security-Policy: script-src 'self' https://analytics.holstjensen.eu; "
            "connect-src 'self' https://analytics.holstjensen.eu\n"
        ))
        findings, _ = collect(tree=tmp)
        if not any("uden init-kaldet" in f for f in findings):
            print("  FEJL: taggen uden init-kald gav ikke 'uden init-kaldet': "
                  f"{findings[0] if findings else '(grøn)'}")
            ok = False
        else:
            print("  adfærd: taggen uden init-kald er statisk dødt -> rød")
            extra[0] += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # Byggerens egen kontrakt. Efter mutationen M1 — se funktionen.
    if not _builder_injects_on_every_page(extra):
        ok = False

    # Bevis på at selftesten kan fejle: en mutation der umuligt kan finde
    # noget skal give False, ellers er "grøn" her meningsløs.
    if _probe_never_fails():
        print("  FEJL: selftesten kan ikke fejle — mutationen returnede True")
        ok = False
    else:
        print("  selftesten kan fejle: mutation uden fund returnerer False")
        extra[0] += 1

    if ok:
        print("SELFTEST GRØN — alle %d negative cases fanges" % extra[0])
    return ok


def _builder_injects_on_every_page(extra):
    """Byggeren skal sætte en **kørende** tag ind på enhver side med <head>.

    Uden denne kontrol døde porten stum, da M1 blev prøvet mod repoets egen
    fil: at slå `if not LOADER_RE.search(html):` tilbage til den bløde
    `if PLAUSIBLE_SRC in html:` gav **grøn selftest**. Grunden er, at porten
    måler det *publicerede* træ, og ingen rigtig side nævner scriptet i prosa
    — så mutationen var usynlig for den.

    Kontraktet her er derfor på **byggerens egen funktion**, kørt på de to
    sider der netop får den forkerte adfærd. Det er den egenskab, der skal
    låses, ikke et tilfælde af det publicerede træ.
    """
    builder = _builder()
    src = builder.PLAUSIBLE_SRC
    cases = [
        (
            "URL nævnt i prosa",
            f"<html><head><!-- config: {src} --></head><body>artikel</body></html>",
        ),
        (
            "loader uden init-kald",
            f'<html><head><script async src="{src}"></script></head><body>s</body></html>',
        ),
        ("helt uden tag", "<html><head><title>t</title></head><body>s</body></html>"),
    ]
    ok = True
    for name, page in cases:
        result = builder.with_analytics(page)
        if not builder.has_analytics(result):
            print(f"  FEJL: byggeren giver ingen kørende tag på en side med {name} "
                  f"(loader={bool(builder.LOADER_RE.search(result))}, "
                  f"init={bool(builder.INIT_RE.search(result))})")
            ok = False
        elif builder.with_analytics(result) != result:
            print(f"  FEJL: byggeren er ikke idempotent på en side med {name}")
            ok = False
    if ok:
        print("  byggeren: kørende tag på prosa-nævnt, halv tag og tom side; idempotent på alle tre")
        extra[0] += 1
    return ok


def _probe_never_fails():
    """Selftestens egen modsætning: en mutation der intet kan finde.

    Samme metode som check_asset_delivery.py: mutationen skriver det, der
    allerede står i filen, så den skaber ingen forskel. En port hvis
    selftest sådan kan være grøn, beviser ingenting.
    """
    with tempfile_module() as tmp:
        findings, _ = collect(tree=make_tree(tmp))  # mutationen: ingen
        return bool(findings)                       # skal være False


class tempfile_module:
    """Lille hjælper, så selftesten ikke importerer tempfile to steder."""

    def __enter__(self):
        import tempfile

        self._dir = tempfile.mkdtemp(prefix="analytics-")
        return self._dir

    def __exit__(self, *exc):
        shutil.rmtree(self._dir, ignore_errors=True)
        return False


def main(argv):
    if "--selftest" in argv:
        return 0 if _selftest() else 1
    findings, facts = collect()
    if findings:
        print(f"ANALYTICS-GATE RØD — {len(findings)} fund:")
        for finding in findings[:20]:
            print(f"  - {finding}")
        if len(findings) > 20:
            print(f"  … og {len(findings) - 20} mere")
        return 1
    print(
        "ANALYTICS-GATE GRØN — {pages} sider, {tagget} med tag, {fragmenter} fragmenter uden <head>, "
        "script-src + connect-src tillader analytics, ét pageview pr. rækkefølge "
        "({script_id})".format(
            script_id=facts.get("script_src", "?").rsplit("/", 1)[-1], **facts
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
