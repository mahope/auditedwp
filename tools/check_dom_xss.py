#!/usr/bin/env python3
"""tools/check_dom_xss.py — gate for DOM-XSS i quick-check-blokkene.

HVAD DENNE GATE DÆKKER (og ikke mere)
-------------------------------------
Den dækker **kun** de filer, der indeholder et `<script>`-blok, som taler med
`deskuptime-quickcheck.mahope-eeb.workers.dev`. Det er 28 filer i dag:
`site/shared/live-check-widget.html`, 16 `site/blog/*/index.html` og
`site/deskuptime/**/index.html`.

Den er bevidst **ikke** en global DOM-XSS-scanner. En bredere eftersøgning
26/9 fandt yderligere 104 fund i 21 andre filer (`site/regex/`,
`site/gdpr-scanner-free/` m.fl.). De er reelle, men de er opgave 17, og en
regel der favner 104 åbne fund kan ikke gå grøn. At fremstille denne gate som
global ville være den falske grøn, som opgave 14 dokumenterede i testværktøjet.

HVORFOR IKKE BARE LÆSE KODEN
----------------------------
Gaten læser ikke, om en værdi *ser* ud til at være escapet. Den kræver, at
hver sink er `esc(...)` eller `textContent`, og den afviser filer, der mangler
`esc`-definitionen selv. `tools/test_quickcheck_render.mjs` er den anden halvdel
og *kører* blokkenes renderer mod et fjendtligt svar — koden læses altså ikke
som bevis, den adfærd.

SELFTEST
--------
`--selftest` beviser at gaten kan fejle: den indbygger 12 mutanter, der hver
ligner en reel fejltagelse, og kræver at alle 12 fanges. Mutationerne kører
mod syntetiske eksempler, ikke mod repoets filer, så selftesten aldrig kan
fejle fordi repoet er rod.

Brug:
    python3 tools/check_dom_xss.py
    python3 tools/check_dom_xss.py --selftest
    python3 tools/check_dom_xss.py --list
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKER = "deskuptime-quickcheck"

# Dynamiciske værder, der kommer fra workeren eller fra brugerens eget input.
# Hver af dem skal modes gennem esc() (eller via textContent) i den blok, der
# renderer dem. Navnene matcher de faktiske felter i workerens JSON-svar.
SINKS = [
    "d.url",
    "d.status",
    "d.statusText",
    "d.responseMs",
    "d.finalUrl",
    "d.error",
    "err.message",
    "d.headers.server",
    "d.sha256",
    "d.sslExpiresAt",
    "d.sslError",
    "days",
    "ms",
    "url",
]

ESC_DEF = re.compile(
    r"function\s+esc\s*\(\s*\w+\s*\)\s*\{[^}]*"
    r"\.textContent\s*=\s*[^;]{0,80};"
    r"[^}]*return\s+\w+\.innerHTML",
    re.S,
)

# En rendererings-linje: en .innerHTML-tilskrivning. Kun den blok vi leder efter.
INNER_HTML = re.compile(r"\.innerHTML\s*=(?!=)", re.S)


def blocks(html: str) -> list[str]:
    """Alle <script>-blokke i dokumentet, der taler med quickcheck-workeren."""
    out = []
    for m in re.finditer(r"<script[^>]*>(.*?)</script>", html, re.S):
        body = m.group(1)
        if WORKER in body:
            out.append(body)
    return out


def inside_esc(before: str) -> bool:
    """Står vi stadig inde i et esc(...)-kald på dette sted?

    Vi hopper over hvert *fuldt* esc(...)-kald og returnerer True kun hvis
    vi løber ud af kaldet. Den naive version af denne tælling var
    `before.count("esc(") > before.count("esc)")` — men `esc)` findes aldrig i
    koden, så tællingen var altid "åben", og **hver** sink efter det første
    esc() på en linje blev springet over. Gaten sagde grøn på 28 filer, mens
    den ikke ville have fundet en eneste reel mangel. Det er præcis den falske
    grøn opgave 14 dokumenterede, fundet to gange i samme værktøj.
    """
    i = 0
    while i < len(before):
        if before.startswith("esc(", i):
            depth = 1
            j = i + 4
            while j < len(before) and depth:
                if before[j] == "(":
                    depth += 1
                elif before[j] == ")":
                    depth -= 1
                j += 1
            if depth:  # vi nåede slutningen af linjen inde i esc(...)
                return True
            i = j
        else:
            i += 1
    return False


def strip_esc_calls(s: str) -> str:
    """Erstat hvert fuldt esc(...)-kald med en pladsholder."""
    out, i = [], 0
    while i < len(s):
        if s.startswith("esc(", i):
            depth, j = 1, i + 4
            while j < len(s) and depth:
                if s[j] == "(":
                    depth += 1
                elif s[j] == ")":
                    depth -= 1
                j += 1
            if depth:
                return s[:i] + "\x00"  # uafsluttet esc( — spring resten
            out.append("\x01")
            i = j
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def strip_string_literals(s: str) -> str:
    """Erstat '…', "…" og `…` med en pladsholder.

    Uden dette matcher den korte streng 'ms<br>' sinken `ms` — det er tekst,
    ikke data, og en gate der råber op om sin egen markup er ubrugelig.
    """
    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c in "'\"":
            q, j = c, i + 1
            while j < n and s[j] != q:
                j += 2 if s[j] == "\\" else 1
            out.append("\x01")
            i = j + 1
        elif c == "`":
            j = i + 1
            while j < n and s[j] != "`":
                j += 2 if s[j] == "\\" else 1
            out.append("\x01")
            i = j + 1
        else:
            out.append(c)
            i += 1
    return "".join(out)


# En sink er en *interpolation*: den skal staa i en sammensaetning. Tegnene foer
# og efter afgoer det. `(d.redirected&&d.finalUrl?…` er en betingelse og kan ikke
# indsaette markup, saa den skal ikke findes.
#
# `&` og `|` maa med paa AFTER-siden, fordi `(d.headers.server || 'unknown')` er
# en hel parentesgruppe, der selv sættes ind i markup — dens operander er
# interpolationer. Betingelsen `(d.redirected&&d.finalUrl?…` rammes stadig ikke,
# fordi den afgores af `?` bag finalUrl.
BEFORE_OK = set("+(, \x01")
AFTER_OK = set("+,);:|& \x01")
# Kald som går forud: `(if(d.error)` er en betingelse, ikke en sink.
COND_CALL = re.compile(r"(if|while|switch|catch|typeof|return|for)\s*$")


def is_interpolation(rhs: str, start: int, end: int) -> bool:
    before = rhs[:start].rstrip()
    after = rhs[end:].lstrip()
    if COND_CALL.search(before + " "):
        return False
    b = before[-1] if before else "\x01"
    a = after[0] if after else "\x01"
    if b not in BEFORE_OK or a not in AFTER_OK:
        return False
    # `return d.error;` er en sink, `if (d.error)` er ikke — men vi vil heller
    # ikke fange `d.error` i en ren funktionskrop. Return-caset er dækket af
    # AFTER_OK via `;`.
    return True


def find_sinks_in_block(block: str) -> list[tuple[str, str]]:
    """Returnér (sink, kontekst) for hver brug af en sink i en innerHTML-linje.

    Vi ser kun på den fysiske linje, hvor .innerHTML tildeles, PLUS de linjer
    der bygger den streng med + over flere linjer. Det dækker blokkenes
    `res.innerHTML=\n  a + b + c;`-mønster uden at skulle parse JS.
    """
    hits: list[tuple[str, str]] = []
    lines = block.split("\n")
    for idx, line in enumerate(lines):
        assign = INNER_HTML.search(line)
        if not assign:
            continue
        # Saml den fulde tilskrivning: linjen plus de følgende, der afslutter
        # på ';' — altså hele det udtryk der sættes ind i innerHTML.
        expr = line
        j = idx + 1
        while ";" not in expr and j < len(lines) and j - idx < 12:
            expr += "\n" + lines[j]
            j += 1
        # KUN det der staar til hoejre for `=`. Alt foran er kontrolflow —
        # `if(d.error){…}` er en betingelse, ikke en sink, og ville ellers give
        # et fund for hver eneste fejlhåndtering. Det er den falske-fund-fejl
        # denne gate lærte under sin foerste korsel.
        rhs = strip_string_literals(strip_esc_calls(expr[assign.end():]))
        for sink in SINKS:
            for m in re.finditer(r"(?<![\w.])" + re.escape(sink) + r"(?![\w])", rhs):
                if not is_interpolation(rhs, m.start(), m.end()):
                    continue
                hits.append((sink, expr.strip()[:160]))
                break
    return hits


def check_file(path: Path) -> list[str]:
    """Returnér en liste af fund for én fil. Tom liste = grøn."""
    findings: list[str] = []
    html = path.read_text(encoding="utf-8")
    qc_blocks = blocks(html)
    if not qc_blocks:
        return findings

    # Renderer skriver til innerHTML i en quickcheck-blok, skal filen have esc?
    writes_html = any(INNER_HTML.search(b) for b in qc_blocks)
    if writes_html and not ESC_DEF.search(html):
        findings.append(
            f"{path}: quickcheck-blokken skriver til .innerHTML, men filen "
            f"har ingen esc()-definition. Uden den kan intet escapes."
        )
    return findings


def audit(paths: list[Path]) -> tuple[list[str], int, int]:
    findings: list[str] = []
    checked = 0
    sinks_total = 0
    for p in paths:
        html = p.read_text(encoding="utf-8")
        for block in blocks(html):
            checked += 1
            for sink, ctx in find_sinks_in_block(block):
                sinks_total += 1
                findings.append(
                    f"{p}: {sink} skrives ind i .innerHTML uden esc() — {ctx}"
                )
    for p in paths:
        findings.extend(check_file(p))
    return findings, checked, sinks_total


def quickcheck_files() -> list[Path]:
    return sorted(
        p for p in (ROOT / "site").rglob("*.html") if WORKER in p.read_text(
            encoding="utf-8", errors="replace")
    )


# ------------------------------------------------------------------ selftest
GOOD_A = """<script>
(function(){
  function esc(s){var d=document.createElement('div');d.textContent=String(s==null?'':s);return d.innerHTML;}
  var f=document.getElementById('du-form');
  res.innerHTML='x '+esc(url)+' y';
  res.innerHTML='z '+esc(d.status)+' '+esc(d.statusText)+' '+esc(d.responseMs);
  res.innerHTML='e '+esc(d.error);
  res.innerHTML='n '+esc(err.message);
  res.innerHTML='r '+esc(d.finalUrl);
  var api='https://deskuptime-quickcheck.mahope-eeb.workers.dev/?url='+encodeURIComponent(url);
})();
</script>"""

GOOD_B = """<script>
function esc(s){var d=document.createElement('div');d.textContent=String(s==null?'':s);return d.innerHTML;}
document.getElementById('live-check-form').addEventListener('submit', async function(e){
  dataDiv.innerHTML = 'E ' + esc(d.error);
  dataDiv.innerHTML =
    '<span class="lc-accent">' + esc(d.url) + '</span><br>' +
    '  S <span class="lc-ok">' + esc(d.status) + ' ' + esc(d.statusText) + '</span><br>' +
    '  R <span style="color:red">' + esc(d.responseMs) + 'ms</span><br>' +
    (d.redirected ? '  F ' + esc(d.finalUrl) + '<br>' : '') +
    '  S ' + esc(d.headers.server || 'unknown');
  var api='https://deskuptime-quickcheck.mahope-eeb.workers.dev/check?url='+u;
});
</script>"""


def mutants() -> list[tuple[str, str, bool]]:
    """(navn, kildekode, forventes_at_fange)."""
    return [
        ("d.statusText uden esc i family A", GOOD_A.replace("esc(d.statusText)", "d.statusText"), True),
        ("d.status uden esc i family A", GOOD_A.replace("esc(d.status)", "d.status"), True),
        ("d.responseMs uden esc i family A", GOOD_A.replace("esc(d.responseMs)", "d.responseMs"), True),
        ("d.error uden esc i family A", GOOD_A.replace("esc(d.error)", "d.error"), True),
        ("err.message uden esc i family A", GOOD_A.replace("esc(err.message)", "err.message"), True),
        ("d.finalUrl uden esc i family A", GOOD_A.replace("esc(d.finalUrl)", "d.finalUrl"), True),
        ("url-input uden esc", GOOD_A.replace("esc(url)", "url"), True),
        ("d.url uden esc i family B", GOOD_B.replace("esc(d.url)", "d.url"), True),
        ("d.statusText uden esc i family B", GOOD_B.replace("esc(d.statusText)", "d.statusText"), True),
        ("d.headers.server uden esc", GOOD_B.replace("esc(d.headers.server || 'unknown')",
                                                     "d.headers.server || 'unknown'"), True),
        ("esc()-definitionen fjernet fra family A",
         GOOD_A.replace("  function esc(s){var d=document.createElement('div');"
                        "d.textContent=String(s==null?'':s);return d.innerHTML;}\n", ""), True),
        ("esc()-definitionen fjernet fra family B",
         GOOD_B.replace("function esc(s){var d=document.createElement('div');"
                        "d.textContent=String(s==null?'':s);return d.innerHTML;}\n", ""), True),
        # Negativ kontrol: de to rene filer skal IKKE give fund.
        ("family A er grøn", GOOD_A, False),
        ("family B er grøn", GOOD_B, False),
        # textContent-only blok skal heller ikke give fund.
        ("textContent-blok uden innerHTML er grøn",
         "<script>\nvar api='https://deskuptime-quickcheck.mahope-eeb.workers.dev/';\n"
         "box.textContent='x '+d.sslError;\n</script>", False),
    ]


def run_selftest() -> int:
    import tempfile

    failures = []
    for name, src, should_fail in mutants():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "case.html"
            p.write_text(src, encoding="utf-8")
            found, nblocks, _ = audit([p])
        if nblocks == 0:
            print(f"  FEJL  selftest-fixture er ikke skannet ({name}) — "
                  f"audit() saa 0 blokke, saa mutanten er ikke beviset")
            failures.append((name, False, should_fail, ["fixture scannede 0 blokke"]))
            continue
        caught = bool(found)
        if caught != should_fail:
            failures.append((name, caught, should_fail, found))
        mark = "fanget" if should_fail else "rens"
        status = "OK  " if caught == should_fail else "FEJL"
        print(f"  {status}  {mark:6}  {name}")

    if failures:
        print(f"\nSELFTEST RØD — {len(failures)} negative cases ikke fanget korrekt")
        for name, caught, should, found in failures:
            print(f"  {name}: forventede fanget={should}, fik fanget={caught}")
            for f in found:
                print(f"    {f}")
        return 1
    n = sum(1 for _, _, s in mutants() if s)
    print(f"\nSELFTEST GRØN — alle {n} negative cases fanges")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        return run_selftest()
    if "--list" in args:
        for p in quickcheck_files():
            print(p.relative_to(ROOT))
        return 0
    if args:
        print(f"ukendt argument: {' '.join(args)}", file=sys.stderr)
        return 2

    files = quickcheck_files()
    if not files:
        print("FEJL  ingen quickcheck-filer fundet under site/ — "
              "har søgningen brudt? Gaten kan ikke bevise noget.", file=sys.stderr)
        return 1

    findings, checked, sinks = audit(files)
    print(f"quickcheck-filer: {len(files)}")
    print(f"quickcheck-scriptblokke: {checked}")
    print(f"escapede dynamiske vaerdier i .innerHTML: {sinks}")
    if findings:
        print(f"\n{len(findings)} fund:")
        for f in findings:
            print(f"  {f}")
        return 1
    print("\nDOM-XSS-gate gron for quickcheck-blokkene.")
    print("SCOPE: kun de filer der kalder deskuptime-quickcheck. "
          "Ikke en global DOM-XSS-scanner — se docstring.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
