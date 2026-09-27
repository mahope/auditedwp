#!/usr/bin/env python3
"""Gate for scannerens fejlvej: en besøgende må aldrig se motorens eller
browserens interne fejltekst.

Fundet bag porten, målt 2026-09-28 mod den udgivne worker
`eucomply-scan.mahope-eeb.workers.dev`:

    $ curl ".../scan?url=this-domain-does-not-exist.invalidtld"
    502  {"error":"Scan failed: The site responded with HTTP 530 — a compliance
          scan needs a reachable page."}

Alle fem scannere gjorde sådan her:

    var d = await r.json();
    if (!r.ok) throw new Error(d.error || 'Scan failed.');
    ...
    } catch (ex) { errEl.textContent = ex.message || 'Network error. Try again.'; }

Sådan viser den sig for den besøgende:

  1. **Et domæne der ikke findes** — det første en ny besøgende skriver, hvis
     der er en tastefejl i — fik motorens egen sætning med et HTTP-statusnummer
     i, og den fik ingen antydning om, hvad man så gør.
  2. **En Cloudflare-kantfejl** (520/522/524, kvota) er HTML, så `.json()`
     kaster en `SyntaxError`, og `ex.message` lagde browserens egen
     `Unexpected token '<' …` i feltet.

Begge dele landt i `errEl`, altså i det felt hele scannerens resultat står i.

Porten har to dele, og de siger hver især hvad de dækker:

  * **Kilde.** De fem sider skal have en `apiError`, skal ikke læse svaret med
    et ubeskyttet `await r.json()`, og må ikke skrive `ex.message` i
    `#scan-err`. Det er en kildekontrol, og den er den eneste der kan fange en side
    hvor funktionen findes, men fejlvejen alligevel omgår den.
  * **Adfærd.** `tools/scan_error_probe.mjs` tager sidens **egne** `apiError`
    og `T` og kører de **rigtige** svarsvar fra den udgivne worker gennem dem i
    en `vm`. Det er den, der kan bevise at teksten en besøgende ser er den
    tekst, porten siger den burde være.

Uden `node` er adfærdsdelen **rød** med en besked, fordi en port der springer
sin egen kontrol over er grøn uden at have kontrolleret noget (samme fejlklasse
som opgave 9's kanin-hul).

Brug:
    python3.13 tools/check_scan_errors.py
    python3.13 tools/check_scan_errors.py --selftest
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
PROBE = TOOLS / "scan_error_probe.mjs"
WORKER = "https://eucomply-scan.mahope-eeb.workers.dev"

# Alle fem sider har en scanningsformular, der kalder den samme worker. Listen
# er hårdkodet, så en ny scanner-side uden en fejlvej gør porten rød, når
# nogen tilføjer den — det er den fælde "reglen læser mindre end den påstår",
# opgave 30/32/41/63/65.
PAGES = (
    "scan/index.html",
    "da/scan/index.html",
    "gdpr-scanner-free/index.html",
    "gdpr-compliance-check/index.html",
    "cookie-banner-check/index.html",
)

# Kilder til de fire rigtige svar. 200 er et site der svarer, 400 en adresse der
# ikke er en webadresse, 429 den elvte scanning i samme minut, 502 et domæne
# der ikke findes. Sidste er fundet fra `curl` 2026-09-28.
RECORDED = [
    {"status": 200, "body": '{"url":"https://example.com/","score":{"pct":60}}'},
    {"status": 400, "body": '{"error":"Please provide a valid public http(s) URL, e.g. ?url=example.com"}'},
    {"status": 429, "body": '{"error":"Rate limit reached. Try again in a few minutes."}'},
    {"status": 502, "body": '{"error":"Scan failed: The site responded with HTTP 530 — a compliance scan needs a reachable page."}'},
]

# De tre domæner der skal svare hvert sit svar. Kun brugt når der er netværk.
LIVE_CASES = (
    ("https://example.com", 200),
    ("not-a-web-address", 400),
    ("this-domain-does-not-exist-9f8a7b6c5d4e3f2a1b.invalidtld", 502),
)

NODE_MISSING = "node ikke fundet — adfærdskontrollen kan ikke køres"


def read(rel: str) -> str:
    return (ROOT / "site" / rel).read_text(encoding="utf-8")


# ---------------------------------------------------------------- kildekontrol

# Den gamle kode kastede workerens egen tekst videre som en fejl:
#     throw new Error(d.error || 'Scan failed.')
THROWS_RAW = re.compile(r"throw\s+new\s+Error\(\s*d\.error")
# Rens er den beskyttede læsning, så en kantfejl (HTML) ikke kaster:
#     var d = null;  try { d = await r.json(); } catch (e) { }
GUARDED = re.compile(r"var\s+d\s*=\s*null;[\s\S]{0,80}?try\s*\{\s*d\s*=\s*await\s+\w+\.json\(\);\s*\}\s*catch")
# `ex.message` i fejlvejen er præcis det, der lagde browserens SyntaxError i
# feltet. Ingen anden sted bruger denne sider det i `#scan-err`.
LEAKS_EX = re.compile(r"errEl\.textContent\s*=\s*ex\.message")


def source_findings(rel: str, src: str | None = None) -> list[str]:
    text = read(rel) if src is None else src
    out: list[str] = []
    if "function apiError(" not in text:
        out.append(f"{rel}: ingen apiError — en fejl fra workeren når besøgende i rå tekst")
    if THROWS_RAW.search(text):
        out.append(f"{rel}: `throw new Error(d.error …)` gør workerens egen tekst til det, der vises")
    if not GUARDED.search(text):
        out.append(f"{rel}: svaret læses uden `try` omkring `.json()`, så en kantfejl (HTML) kaster i stedet for at give en besked")
    if LEAKS_EX.search(text):
        out.append(f"{rel}: `errEl.textContent = ex.message` lægger browserens egen undtagelsestekst i resultatfeltet")
    if "errEl.textContent = apiError(r.status, d)" not in text:
        out.append(f"{rel}: fejlvejen kalder ikke apiError, så status og besked hænger ikke sammen")
    return out


# ------------------------------------------------------------------ adfærd

def live_responses(timeout: float = 25.0) -> list[dict] | None:
    """Hent de rigtige svar fra den udgivne worker. None når der ikke er netværk."""
    out: list[dict] = []
    for target, expect in LIVE_CASES:
        url = f"{WORKER}/scan?url={urllib.parse.quote(target)}"
        req = urllib.request.Request(url, headers={"User-Agent": "eucomply-gate/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body, status = r.read().decode("utf-8", "replace"), r.status
        except urllib.error.HTTPError as e:
            body, status = e.read().decode("utf-8", "replace"), e.code
        except Exception:
            return None
        if status != expect:
            return None  # workerens svarstal har ændret sig — brug de optagede
        out.append({"status": status, "body": body})
    return out


def probe(page: Path, responses: list[dict]) -> tuple[list[str], str | None]:
    """Kør sidens egen kode gennem svarene. Returnerer (fund, fejltekst)."""
    if not shutil.which("node"):
        return [], NODE_MISSING
    with tempfile.TemporaryDirectory() as tmp:
        rf = Path(tmp) / "responses.json"
        rf.write_text(json.dumps(responses), encoding="utf-8")
        proc = subprocess.run(
            ["node", str(PROBE), str(page), str(rf)],
            capture_output=True, text=True, timeout=90,
        )
    return [l for l in proc.stdout.splitlines() if "FEJL" in l], (proc.stderr or None)


# ------------------------------------------------------------------- porten

def check(tree: Path | None = None) -> tuple[list[str], str]:
    base = tree or (ROOT / "site")
    findings: list[str] = []

    responses = live_responses()
    kilde = "optagede svar fra 2026-09-28"
    if responses is None:
        responses = RECORDED
        kilde = "optagede svar fra 2026-09-28 (ingen netværk)"

    node_mangler = False
    for rel in PAGES:
        page = base / rel
        if not page.exists():
            findings.append(f"{rel}: siden findes ikke, så dens fejlvej er ubeskyttet")
            continue
        findings += source_findings(rel, page.read_text(encoding="utf-8"))
        got, err = probe(page, responses)
        if err and NODE_MISSING in err:
            node_mangler = True
        findings += [f.replace(str(base) + "/", "") for f in got]

    if node_mangler:
        findings.append(NODE_MISSING)
    return findings, kilde


# ------------------------------------------------------------------ selftest

def _mutate(src: str, old: str, new: str, rel: str) -> list[str]:
    assert src.count(old) == 1, f"mutationen passer ikke: {old!r}"
    return source_findings(rel, src.replace(old, new))


def _selftest() -> bool:
    rel = "scan/index.html"
    src = read(rel)
    cases: list[tuple[str, list[str]]] = []

    # a) Tilbage til den gamle kode: workerens egen tekst som besked.
    cases.append((
        "siden mangler apiError",
        source_findings(rel, src.replace("function apiError(", "function bortlagt(")),
    ))

    # b) Ubeskyttet .json() — kantfejlen kaster igen.
    cases.append((
        "ubeskyttet .json() uden try",
        _mutate(
            src,
            "      var d = null;\n      try { d = await r.json(); }",
            "      var d = await r.json();\n      void (function(){});",
            rel,
        ),
    ))

    # b2) Den gamle kode: workerens tekst kastet videre som en fejl.
    cases.append((
        "throw new Error(d.error …)",
        _mutate(src, "if (!r.ok) { errEl.textContent = apiError(r.status, d); return; }",
                 "if (!r.ok) throw new Error(d.error || T.failed);", rel),
    ))

    # c) Browserens egen undtagelsestekst i feltet igen.
    cases.append((
        "ex.message i resultatfeltet",
        _mutate(src, "      errEl.textContent = T.network;", "      errEl.textContent = ex.message || T.network;", rel),
    ))

    # d) Fejlvejen kalder ikke apiError, så status og besved hænger ikke sammen.
    cases.append((
        "fejlvejen kalder ikke apiError",
        _mutate(src, "apiError(r.status, d); return;", "d && d.error ? d.error : T.failed; return;", rel),
    ))

    # e) Adfærden: en apiError der bare videregiver motorens tekst. Samme fejl
    #    som (a), men den side har stadig funktionen, så kun adfærdsdelen kan
    #    fange den — bevis på at de to dele ikke er det samme.
    passthrough = re.sub(
        r"function apiError\(status, d\) \{[\s\S]*?\n  \}",
        "function apiError(status, d) {\n    return (d && d.error) || T.failed;\n  }",
        src, count=1,
    )
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "scan.html"
        p.write_text(passthrough, encoding="utf-8")
        got, err = probe(p, RECORDED)
    cases.append((
        "apiError videregiver motorens egen tekst",
        got if got else ([f"fejl i stedet for fund: {err}"] if err else ["mutationen gav ingen fund"]),
    ))

    # f) Adfærden: alle statusser ender i netværksfejlen, så beskeden ikke
    #    længer hænger sammen med det der skete.
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "scan.html"
        p.write_text(
            re.sub(r"function apiError\(status, d\) \{[\s\S]*?\n  \}",
                   "function apiError(status, d) {\n    return T.network;\n  }", src, count=1),
            encoding="utf-8",
        )
        got, _ = probe(p, RECORDED)
    cases.append(("alle statusser giver netværksfejlen", got or ["mutationen gav ingen fund"]))

    # g) Adfærden: beskeden for et uopnåeligt domæne uden næste skridt. Den er
    #    stadig venlig, men den er en blindgade — præcis hvad en ny besøgende
    #    mød før rettelsen.
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "scan.html"
        p.write_text(
            re.sub(r"unreachable: '[^']*'", "unreachable: 'We could not reach that site.'", src, count=1),
            encoding="utf-8",
        )
        got, _ = probe(p, RECORDED)
    cases.append(("uopnåeligt domæne uden næste skridt", got or ["mutationen gav ingen fund"]))

    # g) Rens: den virkelige side skal være grøn, ellers må mutationerne fra
    #    (a)-(f) slet ikke tælle.
    rens, _ = probe(ROOT / "site" / rel, RECORDED)
    cases.append(("den uændrede side er grøn", rens))

    ok = True
    for name, findings in cases:
        rød = bool(findings)
        print(f"  {'fanget ' if rød else 'rens   '} {name}")
        for f in findings:
            print(f"           {f}")
        if name == "den uændrede side er grøn":
            if rød:
                ok = False
        elif not rød:
            ok = False

    # Bevis på at selftesten kan fejle: en mutation der umuligt kan findes
    # returnerer ingenting, så "ingen fund" kan ikke forveksles med "grøn".
    if _selftest_can_fail():
        print("  selftesten kan fejle: mutation uden fund returnerer False")
    else:
        print("  FEJL: selftesten kan ikke fejle")
        ok = False

    print(f"\n{'SELFTEST GRØN' if ok else 'SELFTEST RØD'} — {len(cases)} negative cases")
    return ok


def _selftest_can_fail() -> bool:
    """Bevis at kildekontrollen kan returnere fund.

    Selvtesten ovenfor siger "fanget" fordi porten meldte fund. Hvis porten
    aldrig kan finde noget, ville den sige det samme, og selftesten ville være
    grøn uden at have kontrolleret noget. Derfor kræves her det modsatte: en
    bevidst ødelagt kopi skal give fund, ellers er hver mutation ovenfor
    betydningsløs.
    """
    src = read("scan/index.html").replace("function apiError(", "function bortlagt(")
    return bool(source_findings("scan/index.html", src))


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return 0 if _selftest() else 1

    findings, kilde = check()
    for f in findings:
        print(f"  FEJL {f}")
    if findings:
        print(f"\nSCAN-FEJL-GATE RØD — {len(findings)} fund")
        return 1
    print(
        f"SCAN-FEJL-GATE GRØN — {len(PAGES)} scanner-sider, egen apiError mod "
        f"{kilde}, ingen intern tekst på #scan-err."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
