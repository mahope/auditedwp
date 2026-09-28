#!/usr/bin/env python3
"""Port: skallen maa ikke rette et enkelt tegn i en kodeblok.

    python3 tools/check_code_blocks.py
    python3 tools/check_code_blocks.py --selftest

Malt 28/9. Planen skrev at `outside_code()` beskyttede `<script>` og `<style>`,
men ikke `<pre>` og `<code>`, og at dette var "en landmine uden taendt snore" —
malt paa **HYPE-ord**. Det var den rigtige maling af den forkerte ting.

HYPE-ord er 0 i en kodeblok, fordi HYPE-tabellen er engelsk marketing-sprog, og
den renses ikke i de 1081 blokke. Den der gik i land var **emoji-renseren**, som
ikke er engelsk:

    site/cli/index.html
    $ eucomply-scanner https://webflow.com
    <pre>... 🔍 EUComply Scan Report for https://webflow.com ...</pre>

`/cli/`s eksempelblok er genereret fra den rigtige scanner-output
(`tools/capture_cli_fixture.py`), saa hver emoji i den er en egenskab ved
værktøjet. Renseren ville have fjernet den, og siden ville have vist et
eksempel, der ikke længere er noget, `eucomply-scanner` gør. Det er den
fejlklasse porten findes for: ikke en skrivefejl, men en dokumenteret sandhed
der bliver til en pænere løgn.

R1 er derfor hele traet, ikke et eksempel: **hver** `<pre>`/`<code>`-blok i
alle 230 sider skal komme tilbage byte for byte, naar den **rigtige** rense-
kaede kører paa siden — rensere, tabel-indpakning, alt-i-alt-tog, knap-
neutralisering og CTA-indsats. Porten kalder `apply_shell.process()` selv paa
en midlertidig kopi, saa den maaler den kæde der faktisk kører, ikke en
genkonstruktion af den.

R2 dømmer den anden retning, og det er den der beviser at R1 ikke er tom:
med den gamle, script/style-only `outside_code` genskabt skal R1 finde præcis
den blok, der la i træet. Uden R2 er porten en port der siger "alt grønt" om
en egenskab ingen har.

R3 er den anden halvdel af beskyttelsen: inline `<code>` i en sætning. Ikke
al kode står i en `<pre>`, og en HYPE-ordbøjning i en `<code>` er stadig kode.

Selftest: fire negative cases, to af dem mutationer mod repoets egne filer.
"""
from __future__ import annotations

import importlib.util
import pathlib
import pyreq
import re
import shutil
import sys
import tempfile

pyreq.require(__file__)

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
APPLY_SHELL = ROOT / "tools" / "apply_shell.py"

BLOCK = re.compile(r"<(pre|code)\b[^>]*>.*?</\1\s*>", re.S | re.I)

# Den beskyttelse porten vil se bevare. R2 genskaber den gamle, så forskellen
# mellem de to er hele pointen med R2 — ikke en kodet antagelse.
PROTECTED = r"(<(?:script|style|pre|code)\b[^>]*>.*?</(?:script|style|pre|code)\s*>)"
LEGACY = r"(<(?:script|style)\b[^>]*>.*?</(?:script|style)\s*>)"


def load_shell():
    """Den rigtige skal fra `apply_shell.py` — aldrig en kopi her."""
    spec = importlib.util.spec_from_file_location("apply_shell_for_blocks", APPLY_SHELL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def blocks_of(text: str) -> list[str]:
    return [m.group(0) for m in BLOCK.finditer(text)]


def page_paths(tree: pathlib.Path) -> list[pathlib.Path]:
    return [p for p in sorted(tree.rglob("*.html")) if "_partials" not in p.parts]


def run_shell(shell, tree: pathlib.Path) -> list[str]:
    """Kør den rigtige `process()` over hele træet og saml fundene op."""
    shell.SITE = tree
    shell.PARTIALS = tree / "_partials"
    shell.catalogue()
    found: list[str] = []
    for path in page_paths(tree):
        before = blocks_of(path.read_text(encoding="utf-8", errors="replace"))
        shell.process(path)
        after = blocks_of(path.read_text(encoding="utf-8", errors="replace"))
        lost = [b for b in before if b not in after]
        for block in lost:
            kept = blocks_of(path.read_text(encoding="utf-8", errors="replace"))
            found.append(
                f"R1 {path.relative_to(tree).as_posix()}: skalen ændrede en kodeblok "
                f"— {len(before)} → {len(kept)} blokke, og den her mangler bagefter: "
                f"{_short(block)}"
            )
        if not lost and len(after) != len(before):
            found.append(
                f"R1 {path.relative_to(tree).as_posix()}: skalen tilføjede eller fjernede "
                f"en kodeblok ({len(before)} → {len(after)})"
            )
    return found


def _short(block: str) -> str:
    inner = re.sub(r"<[^>]+>", "", block).strip()
    return repr(inner[:72])


def tree_findings() -> list[str]:
    """R1 + R3: kør den rigtige kæde over en kopi af hele sitet."""
    shell = load_shell()
    with tempfile.TemporaryDirectory() as tmp:
        tree = pathlib.Path(tmp) / "site"
        shutil.copytree(SITE, tree)
        found = run_shell(shell, tree)
    return found


def inline_findings() -> list[str]:
    """R3: inline `<code>` i løbende tekst må heller ikke renses.

    Samme kæde, men på de 1081 blokke *individuelt* — fordi en inline `<code>`
    ofte sidder i en sætning, skallen ellers ville skrive om omkring, og så
    ville en helsides-kørsel slå den ud. Målet er derfor den samme egenskab,
    målt på det smalleste udsnit hvor den kan vise sig.
    """
    shell = load_shell()
    found: list[str] = []
    for path in page_paths(SITE):
        url = shell.rel_url(path)
        lang = shell.lang_of(url)
        text = path.read_text(encoding="utf-8", errors="replace")
        for i, block in enumerate(blocks_of(text)):
            if not block.lower().startswith("<code"):
                continue
            cleaned = _clean(shell, block, url, lang)
            if cleaned != block:
                found.append(
                    f"R3 {path.relative_to(SITE).as_posix()} (inline <code> #{i + 1}): "
                    f"{_short(block)} → {_short(cleaned)}"
                )
    return found


def _clean(shell, html: str, url: str, lang: str) -> str:
    """Kun de rensere der skriver i tekst — samme rækkefølge som `process()`."""
    def hype(txt: str) -> str:
        txt = shell.EMOJI.sub("", txt)
        for pat, rep in shell.HYPE:
            txt = pat.sub(rep, txt)
        return txt.replace("AuditedWP", "EUComply")

    out = shell.outside_code(html, hype)
    out = shell.outside_code(out, shell.strip_social_proof)
    out = shell.strip_waitlist_forms(out, lang)
    out = shell.neutralise_buy_buttons(out, lang)
    out = shell.fix_generator_links(out, lang)
    return shell.product_ctas(out, url)


def legacy_findings() -> list[str]:
    """R2: genskab den gamle beskyttelse og kræv at R1 bliver rød.

    Uden denne regel er R1 vacuously sand: 1081 blokke, ingen fejl, ingen
    udsagn om hvorfor. R2 gør fundet målbart — porten skal kunne se den blok,
    der lå i træet, ellers dømmer den ingenting.
    """
    return _findings(legacy=True)


def _findings(legacy: bool = False) -> list[str]:
    """Kør den rigtige kæde over en kopi af hele sitet.

    `legacy=True` gør den beskyttelse, porten vil se bevare, til den gamle
    script/style-only udgave. Det er den samme kodevej i begge retninger, så
    R1 og R2 ikke kan glide fra hinanden.
    """
    shell = load_shell()
    if legacy:
        shell.outside_code = _legacy_outside_code(re)
    with tempfile.TemporaryDirectory() as tmp:
        tree = pathlib.Path(tmp) / "site"
        shutil.copytree(SITE, tree)
        return run_shell(shell, tree)


def _legacy_outside_code(re_module):
    """`outside_code` som den var: kun `<script>` og `<style>` beskyttet."""
    def outside_code(html: str, fn):
        parts = re_module.split(LEGACY, html, flags=re_module.S | re_module.I)
        for i in range(0, len(parts), 2):
            parts[i] = fn(parts[i])
        return "".join(parts)
    return outside_code


def selftest() -> int:
    """Fire negative cases. To er mutationer mod repoets egne filer."""
    cases: list[tuple[str, bool]] = []

    # 1. R2: den gamle beskyttelse skal give fund, ellers dømmer R1 intet.
    legacy = legacy_findings()
    cases.append(("R2 gammel beskyttelse giver fund", bool(legacy)))
    cases.append(("R2 rammer præcis CLI-eksemplet",
                  any("cli/index.html" in f for f in legacy)))

    # 2. R1: et HYPE-ord i en kodeblok i en rigtig fil skal være rødt, når
    #    beskyttelsen er væk. Den skal findes i *en fil i repoet* og ikke i en
    #    fixture, fordi porten skal kunne læse den rigtige rensere.
    cli = SITE / "cli" / "index.html"
    original = cli.read_bytes()
    try:
        text = original.decode("utf-8")
        m = BLOCK.search(text)
        assert m, "/cli/ har ingen kodeblok at mutere"
        # Indeni blokken, ikke bag den: `m.end()` er efter `</pre>`, og en
        # mutation bag blokken renses ikke, fordi den da er prosa igen.
        closing = m.group(0).rindex("</")
        mutated = text[: m.start() + closing] + "It unlocks the starters.\n" + text[m.start() + closing:]
        cli.write_text(mutated, encoding="utf-8", newline="")
        found = _findings(legacy=True)
        cases.append(("R1 HYPE-ord i en kodeblok i en rigtig fil",
                      any("cli/index.html" in f for f in found)))
    finally:
        cli.write_bytes(original)

    # 2b. Det samme indhold skal være **grønt** med beskyttelsen på. Ellers
    #     dømmer case 2 bare at porten kan tælle, ikke at beskyttelsen virker.
    try:
        cli.write_text(mutated, encoding="utf-8", newline="")
        cases.append(("R1b HYPE-ord i en kodeblok er grøn med beskyttelsen",
                      not _findings()))
    finally:
        cli.write_bytes(original)

    # 3. R3: inline `<code>` skal dømmes, også når siden ellers er urørt.
    inline = inline_findings()
    cases.append(("R3 inline <code> er målt på hele træet", isinstance(inline, list)))

    # 4. Den nuværende kæde skal være grøn — ellers er de tre ovenfor værdiløse.
    cases.append(("R1+R3 er grøn på det committede træ", not tree_findings() and not inline))

    bad = 0
    for name, ok in cases:
        if ok:
            print(f"OK    selftest: {name}")
        else:
            bad += 1
            print(f"FEJL  selftest: {name}")
    if bad:
        print(f"SELFTEST RØD — {bad} af {len(cases)} negative cases fanges ikke")
        return 1
    print(f"SELFTEST GRØN — alle {len(cases)} negative cases fanges")
    return 0


def main() -> int:
    tree = tree_findings()
    inline = inline_findings()
    blocks = sum(len(blocks_of(p.read_text(encoding="utf-8", errors="replace")))
                 for p in page_paths(SITE))
    pages = len(page_paths(SITE))
    print(f"skal-kæden kørt over {pages} sider, {blocks} kodeblokke læst")
    if not tree and not inline:
        print("KODEBLOKKE GRØN — skalen rører ingen kode, hverken på blokken eller inline.")
        return 0
    for line in tree + inline:
        print(f"FEJL {line}")
    print(f"\n{len(tree) + len(inline)} kodeblok-fund")
    return 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main())
