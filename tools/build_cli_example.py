#!/usr/bin/env python3
"""Generér /cli/'s eksempeludskrift fra motoren — eller efterprøv den.

    python3 tools/build_cli_example.py            # skriv blokken i site/cli/
    python3 tools/build_cli_example.py --check    # skriv intet; exit 1 hvis
                                                  # den publicerede blok ikke er
                                                  # motorens egen udskrift
    python3 tools/build_cli_example.py --selftest # bevis at porten kan blive rød

Baggrunden er målt, ikke formodet. `/cli/` skrev *"Example output (real scan of
webflow.com)"* og viste seks rækker i et `║ ║ ╚═══╗`-felt. Den rigtige CLI
(find `eucomply-scanner/package.json` → `bin`) skriver **ni** rækker i et helt
andet format, og to af de seks domme var forkerede:

| publiceret dom                        | motorens dom                        |
|---------------------------------------|-------------------------------------|
| `No consent banner detected  CHECK MANUALLY` | `⚠️ No consent banner detected` |
| `No DORA / resilience disclosures     CHECK MANUALLY` | `❌ No DORA-related page signals detected` |
| *(mangler helt)*                      | `❌ 1 tracker(s) with NO consent platform` |

Den sidste er den alvorligste: en tracker uden samtykkeplatform er det
klassisk håndhævelsesmål, og den stod slet ikke på siden. Ingen port kunne se
det, fordi blokken var håndskrevet — der var ingen at sammenligne med.

Derfor er blokken nu **genereret**: `tools/cli_example_run.mjs` kører den
publicerede `bin` mod en optaget fixture, og denne fil skriver dens stdout
mellem to markører i `site/cli/index.html`. Der er ingen anden gengivelse af
motorens formatering i repoet, så de to kan ikke glide fra hinanden.

Én af tallene er ikke deterministisk: `Duration: 62ms` er en måling af det
kørende øjeblik. Derfor sammenligner `--check` alt andet byte for byte og
kræver af den afvigende linje, at den er `Duration: <heltal>ms`. Uden den
undantagelse ville porten være rød af en grund der ikke findes i koden.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tools" / "fixtures" / "webflow.com.json"
PAGE = ROOT / "site" / "cli" / "index.html"
RUNNER = ROOT / "tools" / "cli_example_run.mjs"

START = "<!--cli:example-->"
END = "<!--/cli:example-->"

# Den ene linje der må afvige, og kun fordi den er en måling af det kørende
# øjeblik. `DURATION_RE` bruges på både den publicerede og den friske blok, så
# der sammenlignes på den normaliserede form.
DURATION_RE = re.compile(r"^(   Duration: )\d+(ms)$")
DURATION_LINE_RE = re.compile(r"^   Duration: \d+ms$")

# Ni checks, ni domme. Den publicerede blok havde seks, og ingen port kendte
# forskel på "seks rækker" og "alle ni" — den tæller dem.
VERDICT_RE = re.compile(r"^ (?:✅|⚠️|❌) ", re.M)
CHECK_COUNT = 9

# `/cli/` siger andre steder hvad CLI'en skriver. Blokerne skal ikke bare være
# motorens output — de skal også *beskrive* den.
SENTENCE_RULES = (
    # (regex der skal findes i side-HTML'en, fordi CLI'en virkelig gør det)
    (re.compile(r"sub-second scans over a public API"),
     "CLI'en kalder én side — ikke en public API"),
    (re.compile(r"every check reports PASS, FAIL or CHECK MANUALLY"),
     "CLI'en skriver ✅/⚠️/❌ og dommens etiket, ikke PASS/FAIL/CHECK MANUALLY"),
)


def run_cli(fixture: Path = FIXTURE) -> str:
    """Den publicerede `bin`'s stdout mod fixture'en."""
    proc = subprocess.run(
        ["node", str(RUNNER), str(fixture), fixture_url(fixture)],
        cwd=ROOT, capture_output=True, text=True,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise SystemExit(
            f"CLI'en fejlede mod {fixture.name} (exit {proc.returncode}):\n{proc.stderr.strip()}"
        )
    return proc.stdout.rstrip("\n")


def fixture_url(fixture: Path = FIXTURE) -> str:
    import json

    return json.loads(fixture.read_text(encoding="utf-8"))["url"]


def normalise(block: str) -> str:
    """Erstat det éneste ikke-deterministiske tal, så blokke kan sammenlignes."""
    return "\n".join(
        DURATION_RE.sub(r"\1<ms>\2", line) for line in block.split("\n")
    )


def render_block(url: str, stdout: str) -> str:
    """Kommandolinjen + motorens egen udskrift, som publiceret HTML."""
    body = html.escape(stdout, quote=False)
    return f"$ eucomply-scanner {url}\n{body}"


def read_page() -> str:
    if not PAGE.exists():
        raise SystemExit(f"siden mangler: {PAGE.relative_to(ROOT)}")
    return PAGE.read_text(encoding="utf-8")


def find_block(page: str) -> str | None:
    """Blokken mellem markørerne, uden `<pre>`-kapslen.

    Markørerne står uden for `<pre>`, så det publicerede HTML er
    `…<!--cli:example--><pre>…</pre><!--/cli:example-->`. Kapslen er
    markup, ikke udskrift, så den sammenlignes ikke med motorens stdout.
    """
    if START not in page or END not in page:
        return None
    block = page.split(START, 1)[1].split(END, 1)[0].strip()
    if block.startswith("<pre>") and block.endswith("</pre>"):
        block = block[len("<pre>"):-len("</pre>")]
    return block


def expected_block() -> str:
    return render_block(fixture_url(), run_cli())


# ------------------------------------------------------------------- regler


def findings(page: str) -> list[str]:
    out: list[str] = []
    block = find_block(page)
    if block is None:
        return [
            f"{PAGE.relative_to(ROOT)} har ingen blok mellem {START} og {END} — "
            "eksemplet kan så ikke genereres fra motoren"
        ]
    want = expected_block()

    # R1: hele blokken er motorens egen udskrift, byte for byte, undtagen den
    # ene målte linje. Det er den regel der fanger den håndskrevne blok.
    got_norm, want_norm = normalise(block).strip(), normalise(want).strip()
    if got_norm != want_norm:
        got_lines, want_lines = got_norm.split("\n"), want_norm.split("\n")
        first = next(
            (i for i, (a, b) in enumerate(zip(got_lines, want_lines)) if a != b),
            min(len(got_lines), len(want_lines)),
        )
        out.append(
            f"R1: den publicerede blok afviger fra motorens udskrift i linje {first + 1} — "
            f"publiceret: {got_lines[first] if first < len(got_lines) else '<slutter>'} / "
            f"motoren: {want_lines[first] if first < len(want_lines) else '<slutter>'}. "
            "Kør `python3 tools/build_cli_example.py`."
        )

    # R2: den afvigende linje skal være den målte varighed, ellers er R1's
    # undtagelse en bagdør. Kræver formatet `   Duration: <heltal>ms`.
    duration_lines = [l for l in got_norm.split("\n") if l.startswith("   Duration:")]
    if len(duration_lines) != 1 or not DURATION_LINE_RE.match(
        duration_lines[0].replace("<ms>", "0")
    ):
        out.append(
            "R2: blokken skal have præcis én `   Duration: <heltal>ms`-linje, "
            f"fandt {len(duration_lines)}"
        )

    # R3: alle ni checks, som motoren kører. Den publicerede blok havde seks,
    # og det var ingen der spurgte hvorfor.
    count = len(VERDICT_RE.findall(html.unescape(block)))
    if count != CHECK_COUNT:
        out.append(
            f"R3: blokken viser {count} af motorens {CHECK_COUNT} domme "
            "(✅/⚠️/❌) — et eksempel der viser færre rækker end motoren kører "
            "er et eksempel, ingen har set"
        )

    # R4: kommandolinjen skal pege på den side der faktisk blev scannet.
    url = fixture_url()
    if not block.strip().startswith(f"$ eucomply-scanner {url}"):
        out.append(f"R4: blokken skal begynde med `$ eucomply-scanner {url}`")

    # R5: sider der beskriver CLI'en skal beskrive den CLI'en faktisk er.
    for pattern, why in SENTENCE_RULES:
        if pattern.search(page) and why:
            out.append(f"R5: siden siger {pattern.pattern!r} — {why}")

    return out


# ---------------------------------------------------------------- selftest


def selftest() -> int:
    """Bevis at porten kan blive rød — på mutationer af repoets egne filer."""
    cases: list[tuple[str, list, bool]] = []
    ok = True

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)

        # 1. den håndskrevne blok fra 2026-09-28: seks rækker i box-format, to
        #    forkerede domme og ingen tracker-advarsel. Den ligger mellem
        #    markørerne, så det er R1/R3/R4 der skal dømme den — ikke en
        #    klagemål om manglende markører.
        hand_body = (
            "$ eucomply-scanner https://webflow.com\n"
            " EUComply Scan Report — webflow.com\n"
            "║    HTTPS + HSTS OK                     PASS\n"
            "║    No consent banner detected          CHECK MANUALLY\n"
            "║    Forms present, privacy policy linked PASS\n"
            "║    Legal pages linked                  PASS\n"
            "║    3/4 security headers present        PASS\n"
            "║  •  No DORA / resilience disclosures     CHECK MANUALLY\n"
            "╚══════════════════════════════════════════════════"
        )
        hand_page = f"{START}\n<pre>{html.escape(hand_body)}</pre>\n{END}\n"
        hand_findings = findings(hand_page)
        hand_rules = {f[:2] for f in hand_findings}
        cases.append((
            "den håndskrevne blok fra /cli/ (dagens fejl)",
            hand_findings,
            True,
        ))
        # R4 kan ikke fange den: den håndskrevne blok startede med den rigtige
        # kommandolinje. Det er R1 (den er ikke motorens udskrift) og R3 (den
        # har seks domme, motoren har ni) der gør den rød — og de to er nok,
        # fordi en blok der så vel ud forfra, men viste en tredjedel færre
        # resultater, var præcis fejlen.
        missing = {"R1", "R3"} - hand_rules
        if missing:
            ok = False
            print(f"  FEJL    håndskrevet blok fanges ikke af {sorted(missing)}")
        else:
            print("  fanget  håndskrevet blok: både R1 og R3 fanger den")

        # 2. en blok der kun mangler én række — den skal være rød på R3 alene
        good = expected_block()
        trimmed = "\n".join(
            l for l in good.split("\n") if not l.startswith(" ❌ No DORA-related")
        )
        with (tmpdir / "short.html").open("w", encoding="utf-8") as fh:
            fh.write(f"{START}\n<pre>{html.escape(trimmed)}</pre>\n{END}\n")
        short_findings = findings((tmpdir / "short.html").read_text(encoding="utf-8"))
        cases.append((
            "eksempel uden DORA-rækken (8 af 9 domme)",
            [f for f in short_findings if f.startswith("R3:")],
            True,
        ))

        # 3. en blok der er motorens, men hvor den afvigende linje ikke er
        #    varighed — R2 skal fange at undtagelsen er vokset
        tampered = good.replace("Duration: ", "Time: ")
        with (tmpdir / "tampered.html").open("w", encoding="utf-8") as fh:
            fh.write(f"{START}\n<pre>{html.escape(tampered)}</pre>\n{END}\n")
        tamper_findings = findings((tmpdir / "tampered.html").read_text(encoding="utf-8"))
        cases.append((
            "varighedslinjen omdøbt (R2 vokser ikke)",
            [f for f in tamper_findings if f.startswith("R2:")],
            True,
        ))

        # 4. en blok der er motorens, men der peger på en anden URL
        wrong = good.replace("$ eucomply-scanner https://webflow.com", "$ eucomply-scanner https://example.com")
        with (tmpdir / "wrong.html").open("w", encoding="utf-8") as fh:
            fh.write(f"{START}\n<pre>{html.escape(wrong)}</pre>\n{END}\n")
        cases.append((
            "kommandolinjen peger på en anden side (R4)",
            [f for f in findings((tmpdir / "wrong.html").read_text(encoding="utf-8")) if f.startswith("R4:")],
            True,
        ))

    for name, got, want_findings in cases:
        if want_findings and got:
            print(f"  fanget  {name}: {len(got)} fund")
        elif not want_findings and not got:
            print(f"  fanget  {name}: 0 fund")
        else:
            ok = False
            print(f"  FEJL    {name}: forventede {'fund' if want_findings else 'ingen fund'}, fik {len(got)}")

    # 5. grøn case: den rigtige blok skal være grøn, ellers er porten rød af design
    clean = findings(read_page())
    if clean:
        ok = False
        print("  FEJL    repoets egen side: " + "; ".join(clean))
    else:
        print("  fanget  repoets egen side: 0 fund (porten er grøn, ikke rød af design)")

    print("SELFTEST GRØN — alle negative cases fanges" if ok else "SELFTEST RØD")
    return 0 if ok else 1


# --------------------------------------------------------------------- main


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="skriv intet, exit 1 hvis blokken er forældet")
    parser.add_argument("--selftest", action="store_true", help="bevis at porten kan blive rød")
    args = parser.parse_args()

    if args.selftest:
        return selftest()

    page = read_page()
    want = expected_block()

    if not args.check:
        if START not in page or END not in page:
            raise SystemExit(
                f"{PAGE.relative_to(ROOT)} mangler {START} … {END} — tilføj markørerne "
                "omkring <pre>-blokken med eksempeludskriften."
            )
        head, rest = page.split(START, 1)
        _, tail = rest.split(END, 1)
        new = head + START + "\n<pre>" + want + "</pre>\n" + END + tail
        PAGE.write_text(new, encoding="utf-8")
        print(f"skrev eksempelblokken i {PAGE.relative_to(ROOT)} ({len(want)} tegn)")
        return 0

    bad = findings(page)
    for f in bad:
        print(f"FEJL  {f}")
    if bad:
        print(f"FEJL  {len(bad)} fund i /cli/'s eksempel")
        return 1
    print("OK    /cli/'s eksempel er motorens egen udskrift, alle ni checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
