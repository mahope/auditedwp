#!/usr/bin/env python3
"""Gate: rådet i rapporten skal være læsbar prosa, ikke markup.

Baggrund
--------
Målt 28/9 i den **serverede** `eucomply-1.3.38.zip` (og i begge JS-motorer):
`fix`-feltet i `forms`-tjekket indeholdt en hel `<a href="/privacy/">Privacy
Policy</a>` inde i en data-streng:

    Add a link to your privacy policy next to the form
    (e.g. <a href="/privacy/">Privacy Policy</a>), and assign …

Renderingen er **korrekt** — `plugin/eucomply.php` gør `esc_html( $r['fix'] )` —
og det er netop derfor markup'en *når kunden som kildekode*: i den rapport et
bureau sender videre under eget navn, og i mailen ved et check der skifter til
`fail`. Det er den eneste linje i hele rapporten, der ikke kan bruges.

Ingen af gaterens 29 steps så den, fordi de alle læser *kode-struktur*
(signaturer, claims, links, redirects) og ikke *rådets tekst*. Det er samme
fejlklasse som opgave 9's kanin-hul: en port der springer sin egen kontrol
over er grøn uden at have kontrolleret noget.

Sådan afgør porten
------------------
Der er **én** fejl, ikke en klasse — målt over alle `fix`/`detail`/`label`-
strenge i de to JS-motorer, pluginen og `shared/sample-report.json`. Fire
krav, der alle skal være opfyldt for at porten er grøn:

1. **Ingen markup i brugerrettet data.** Hver udtrukket streng skal være fri for
   `<\s*/?\s*(a|strong|em|br|code|p|span|div|ul|ol|li|h[1-6]|script|img|table)\b`.
   Tællingen sker på **værdien** (hele strengliteralet, også når det står på
   næste linje) — ikke på den linje feltet tildeles. Min egen målescript fandt
   først 0 i motorerne, fordi det søgte på tildelingslinjen; det er den
   fejlklasse planen har skrevet otte gange ned.
2. **Renderingskode er ikke data.** En linje der *escaper* (`esc_html(`,
   `htmlspecialchars(`, `esc(`, `wp_kses(`, `nl2br(`) eller skriver til
   `innerHTML` er kode, ikke en streng kunden læser, og springes over. Ellers
   er porten rød på korrekt kode.
3. **De to JS-motorer skal være ens** om strengen, så rettelsen ikke kan komme
   tilbage i den ene — samme paritetskrav som `test_engine_parity.mjs`.
4. **Tællingerne hænger sammen.** `data-strenge` må ikke være 0. "0 fund" der
   betyder "0 kontrolleret" er præcis den vished porten skal fjerne, så tallet
   skrives ud hver kørsel.

Kørsel
------
    python3 tools/check_advice_strings.py             # gaten
    python3 tools/check_advice_strings.py --selftest   # negative cases
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent

# De tre motorer + det delte datasæt. Rækkefølgen er den rækkefølge porten
# læser dem i, og den bruges også i selftestens rapport.
JS_ENGINES = ("shared/scan-engine.js", "eucomply-scanner/engine/index.js")
PHP_PLUGIN = "plugin/eucomply.php"
SAMPLE_DATA = "shared/sample-report.json"

SOURCES = JS_ENGINES + (PHP_PLUGIN, SAMPLE_DATA)

# Felterne der havner i rapporten som tekst kunden læser.
FIELDS = ("fix", "detail", "label")

# Markup der ikke må stå i en data-streng. Listen er bredere end den ene fejl
# vi målte, fordi kravet er egenskaben og ikke fundet: `<strong>` i et råd er
# samme fejl som `<a href>` i et råd, kun mindre synlig.
MARKUP_RE = re.compile(
    r"<\s*/?\s*(a|strong|em|b|i|br|code|pre|p|span|div|ul|ol|li|h[1-6]"
    r"|script|img|table|tr|td|small|sup|sub)\b",
    re.IGNORECASE,
)

# Renderingskode: ikke data. Hoppes over med vilje, fordi escapingkoden er
# korrekt — det er *værdien* der var forkert, ikke koden der renderer den.
RENDER_RE = re.compile(
    r"esc_html|htmlspecialchars|esc_attr|wp_kses|wp_strip_all_tags|nl2br|innerHTML|"
    r"strip_tags|sanitize",
    re.IGNORECASE,
)

# JS: `fix: '…'`, `fix:\n  '…'`  og  `checks.forms.fix =\n  '…'`
JS_FIELD_RE = re.compile(
    r"(?:\b(?P<field>fix|detail|label)\s*:\s*|\.\s*(?P<field2>fix|detail|label)\s*=\s*)",
)

# PHP: `$results['fix'] = …;`  (venstre side grupperes, så højre side er hele
# det udtryk der tildeles — altså også en konkatenation eller en ternary.)
PHP_FIELD_RE = re.compile(
    r"\$[A-Za-z_]\w*\s*\[\s*['\"](?P<field>fix|detail|label)['\"]\s*\]\s*=\s*"
)

# Ethvert bogstav-literal i et udtryk: '…', "…" og `…`.
LITERAL_RE = re.compile(
    r"'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\"|`((?:[^`\\]|\\.)*)`", re.S
)

OPENERS, CLOSERS = "([{", ")]}"


def _statement(text: str, start: int) -> str:
    """Udtrykket der tildeles ved `start`, med klammer og strenge balanceret.

    Uden denne ville porten læse kun det første literal i
    `detail: a ? '…' : '…'`, og en `<strong>` i den anden arm ville være
    usynlig — samme fejlklasse som at læse tildelingslinjen i stedet for
    værdien. Vi læser derfor hele sætningen og dømmer hvert literal i den.
    """
    depth = 0
    i = start
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in "\"'`":
            i = _skip_string(text, i)
            continue
        if ch in OPENERS:
            depth += 1
        elif ch in CLOSERS:
            if depth == 0:
                break
            depth -= 1
        elif depth == 0 and ch in ",;":
            break
        i += 1
    return text[start:i]


def _skip_string(text: str, i: int) -> int:
    """Indeks efter den streng der starter ved `i`."""
    quote = text[i]
    n = len(text)
    i += 1
    while i < n:
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == quote:
            return i + 1
        i += 1
    return n


def _is_rendering(statement: str) -> bool:
    """Er værdien selv escapest, så den ikke er data?

    Vi dømmer kun **udtrykkets hoved** — alt før det første bogstav-literal.
    Ellers kunne et råd der siger "strip tags from user input" blive
    sprunget over som om det var kode, og så ville porten være grøn ved at
    springe sin egen kontrol over.
    """
    head = statement
    first = re.search(r"['\"`]", statement)
    if first:
        head = statement[:first.start()]
    return bool(RENDER_RE.search(head))


def read(rel: str, findings: List[str]) -> str:
    path = ROOT / rel
    if not path.exists():
        findings.append(f"{rel}: filen findes ikke")
        return ""
    return path.read_text(encoding="utf-8")


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _skip_window(assigned: str) -> bool:
    """Spring renderingskode over.

    Se `_is_rendering`: det er udtrykkets hoved, ikke hele sætningen, der
    afgør om værdien er kode.
    """
    return _is_rendering(assigned)


def collect_strings(text: str, rel: str) -> List[Tuple[str, str, int]]:
    """(felt, værdi, linje) for hver brugerrettet streng i én kilde."""
    found: List[Tuple[str, str, int]] = []

    if rel.endswith(".json"):
        data = json.loads(text)
        for check_row in data.get("checks", []):
            if not isinstance(check_row, dict):
                continue
            for field in FIELDS:
                value = check_row.get(field)
                if isinstance(value, str):
                    found.append((field, value, 0))
        return found

    pattern = PHP_FIELD_RE if rel.endswith(".php") else JS_FIELD_RE
    for match in pattern.finditer(text):
        field = match.group("field") or match.group("field2")
        if field not in FIELDS:
            continue
        statement = _statement(text, match.end())
        if _is_rendering(statement):
            continue
        line_no = _line_of(text, match.start())
        for literal in LITERAL_RE.finditer(statement):
            value = next(group for group in literal.groups() if group is not None)
            if value.strip():
                found.append((field, value, line_no))
    return found


def forms_fix(rel: str) -> str:
    """Værdien af `forms.fix` i én motor, til paritetskravet."""
    text = read(rel, [])
    match = re.search(r"checks\.forms\.fix\s*=\s*([`'\"])(.*?)\1", text, re.DOTALL)
    if not match:
        block = re.search(r"forms\s*:\s*\{.*?\n {2}\}", text, re.DOTALL)
        if block:
            inner = re.search(r"\bfix\s*:\s*([`'\"])(.*?)\1", block.group(0), re.DOTALL)
            if inner:
                return inner.group(2)
        return ""
    return match.group(2)


def check() -> Tuple[List[str], Dict[str, int]]:
    findings: List[str] = []
    counts: Dict[str, int] = {}

    for rel in SOURCES:
        text = read(rel, findings)
        if not text:
            continue
        try:
            strings = collect_strings(text, rel)
        except (json.JSONDecodeError, re.error) as error:
            findings.append(f"{rel}: kunne ikke læses: {error}")
            continue
        counts[rel] = len(strings)
        for field, value, line_no in strings:
            if MARKUP_RE.search(value):
                where = f":{line_no}" if line_no else ""
                snippet = " ".join(value.split())[:120]
                findings.append(
                    f"{rel}{where}: {field}-strengen indeholder markup — "
                    f"den læses som kode, ikke som tekst: {snippet}"
                )

    # Krav 3: de to JS-motorer skal være ens om strengen.
    a, b = (forms_fix(rel) for rel in JS_ENGINES)
    if not a or not b:
        findings.append(
            "paritet: forms.fix kunne ikke findes i begge motorer "
            f"({JS_ENGINES[0]}={a!r}, {JS_ENGINES[1]}={b!r})"
        )
    elif a != b:
        findings.append(f"paritet: de to motorers forms.fix er forskellige:\n  {a}\n  {b}")

    # Krav 4: 0 fund må ikke kunne betyde 0 kontrolleret.
    for rel, count in counts.items():
        if count == 0:
            findings.append(f"{rel}: 0 brugerrettet strenge læst — porten har intet at dømme")

    return findings, counts


def selftest() -> int:
    """Negative cases: bevis at porten kan fejle, før den bruges som bevis."""
    print("Selftest for tools/check_advice_strings.py")
    passed = failed = 0
    real_root = globals()["ROOT"]

    def run(files: Dict[str, str], name: str, expect_red: bool) -> None:
        nonlocal passed, failed
        scratch = Path("/tmp/eucomply-advice-strings-selftest")
        if scratch.exists():
            import shutil
            shutil.rmtree(scratch, ignore_errors=True)
        for rel, body in files.items():
            path = scratch / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        globals()["ROOT"] = scratch
        try:
            findings, counts = check()
        finally:
            globals()["ROOT"] = real_root
        red = bool(findings)
        if red == expect_red:
            passed += 1
            print(f"  OK   {name} — {'rød som forventet' if red else 'grøn som forventet'}")
        else:
            failed += 1
            print(f"  FEJL {name} — {'RØD' if red else 'GRØN'} men forventet "
                  f"{'rød' if expect_red else 'grøn'}")
            for entry in findings:
                print(f"        {entry}")
        if scratch.exists():
            import shutil
            shutil.rmtree(scratch, ignore_errors=True)

    clean_js = (
        "export function scan(html) {\n"
        "  return {\n"
        "    forms: {\n"
        "      fix:\n"
        "        'Add a link to your privacy policy next to each form submit button.',\n"
        "      detail: 'Form markup found.',\n"
        "      label: 'Forms',\n"
        "    },\n"
        "  };\n"
        "}\n"
    )
    clean_php = (
        "<?php\n"
        "$results['label']  = 'Forms';\n"
        "$results['detail'] = 'Form markup found.';\n"
        "$results['fix']    = 'Add a link to your privacy policy next to the form.';\n"
    )

    def both(js: str = clean_js, php: str = clean_php) -> Dict[str, str]:
        return {JS_ENGINES[0]: js, JS_ENGINES[1]: js, PHP_PLUGIN: php,
                SAMPLE_DATA: json.dumps({"checks": [
                    {"key": "forms", "detail": "Form markup found."}]})}

    run(both(), "rent datasæt i alle fire kilder", False)

    marked = clean_js.replace(
        "next to each form submit button.'",
        "next to each form submit button (e.g. <a href=\"/privacy/\">Privacy</a>).'")
    run(both(js=marked), "markup i en JS-fix-streng", True)

    run(both(php=clean_php.replace(
        "next to the form.'", "next to the form (e.g. <a href=\"/p/\">P</a>).'")),
        "markup i pluginens fix", True)

    # Markup i den **anden** arm af en ternary: den fejlklasse der opstod, fordi
    # min første målescript kun læste det første literal efter kolon.
    run(both(js=clean_js.replace(
        "      detail: 'Form markup found.',\n",
        "      detail: html ? 'None.' : 'Found <strong>one</strong> form.',\n")),
        "markup i den anden arm af en ternary", True)

    # Markup i en konkatenation, kun i det andet stykke.
    run(both(php=clean_php.replace(
        "$results['fix']    = 'Add a link to your privacy policy next to the form.';",
        "$results['fix']    = 'Add a link' . ( $x ? ' <a href=\"/p/\">P</a>' : '' ) . ' next to the form.';")),
        "markup i en konkatenations anden arm", True)

    run({**both(), SAMPLE_DATA: json.dumps({"checks": [
        {"key": "forms", "detail": "Found <strong>one</strong> form."}]})},
        "markup i sample-datasættet", True)

    run(both(js=clean_js.replace("next to each form submit button.",
                                 "next to the submit button"), php=clean_php) | {
            JS_ENGINES[1]: clean_js},
        "de to motorer skal være ens", True)

    # Renderingskode er ikke data: en korrekt escaperet linje må ikke være rød.
    run(both(php="<?php\nforeach ($r as $row) {\n"
                 "  echo '<p class=\"fix\">' . esc_html( $r['fix'] ) . '</p>';\n"
                 "}\n"
                 "$results['fix'] = 'Add a link to your privacy policy.';\n"
                 "$results['detail'] = 'Form found.'; $results['label'] = 'Forms';\n"),
        "renderingslinje med esc_html er ikke data", False)

    # 0 læste strenge må være rødt, ellers "0 fund" betyder "0 kontrolleret".
    run({**both(), SAMPLE_DATA: json.dumps({"checks": []})},
        "et datasæt uden strenge er rødt, ikke grønt", True)

    total = passed + failed
    if failed:
        print(f"SELFTEST RØD — {failed} af {total} negative cases slipper")
        return 1
    print(f"SELFTEST GRØN — alle {total} negative cases fanges")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Port: rådet i rapporten må ikke være markup")
    parser.add_argument("--selftest", action="store_true",
                        help="kør selftesten: bevis at porten kan fejle")
    args = parser.parse_args()
    if args.selftest:
        return selftest()

    findings, counts = check()
    total = sum(counts.values())
    detail = ", ".join(f"{rel}: {count}" for rel, count in counts.items())
    print(f"data-strenge: {total} læst ({detail})")

    for entry in findings:
        print(f"  FUND {entry}")

    if findings:
        print(f"FEJL {len(findings)} fund — rådet skal være prosa, det bliver escapet")
        return 1
    print("OK    intet råd i nogen motor indeholder markup")
    return 0


if __name__ == "__main__":
    sys.exit(main())
