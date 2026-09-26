#!/usr/bin/env python3
"""Er SSRF-guarden på den gratis scanner LIVE — og har den ikke lukket scanneren?

## Hvilket problem den her løser

Den gratis scanner (`/scan/` og `@mahope/eucomply-scanner`) er tragten, og
`worker-scan` er det eneste endpoint alle besøgende rammer. Dens SSRF-guard
blev skrevet i to omgange:

- `6422adc` lagde `isPublicHostname()` ind i `normalizeUrl()` — private
  loopback/RFC1918/CGNAT/link-local/TEST-NET-værter afvises ved indlæsning.
  Den blev **deployet** da den blev skrevet ("begge workers deployet og
  verificeret live" i commit-beskeden).
- `28795c3` (opgave 3a) lagde `assertPublicTarget()` ind i `safeFetch()`, som
  følger redirects **manuelt** og validerer hvert hop, plus DNS-svar, 2 MB
  body-cap og hop-grænse. Den blev **ikke** deployet: `worker-scan/` uploades
  aldrig af CI (spørgsmål 9), og planen har ført den som `UNVERIFICERET`.

Det betyder at der i dag står **to forskellige påstande om samme ting**:

1. `tools/production_drift.json` siger at scan-workerens `floor` 1.0.0 er
   **UVERIFICERET** — den følger af kildekoden, ikke af en måling, fordi
   rod-endpointet i produktion svarer 404 uden versionsfelt.
2. En agent har én gang håndmålt at private mål afvises, og noteret det i en
   deploy-log. Det er ikke en egenskab nogen gate holder.

Resultatet er, at **intet i repoet fejler, hvis guarden forsvinder fra
produktion**. En rollback af `eucomply-scan`, en fejltolket deploy, eller en
ny fælde i `isPublicHostname` ville gør scanneren til et SSRF-våben uden at
nogen opdager det — og det er det våben, der rammer *alle* besøgende.

## Hvad der er bevisligt, og hvad der ikke er

En `400` med motorens egen fejltekst beviser **ikke** at 3a-hærdningen er
live. `isPublicHostname` har siddet i `normalizeUrl` siden `6422adc`, og den
lag lagde præcis de samme private mål væk med præcis den samme tekst — så de
gamle og de nye kode vejer ens for de prøver, der kan sendes uden at røre en
tredjepart. Uden en offentlig adresse der *omdirigerer* til et privat mål er
hop-valideringen ikke målbar herfra.

Derfor gør denne gate **præcis det den kan bevise**, og siger resten højt:

- **Påstand (rød hvis den fejler).** En adresse i et reserveret interval må
  aldrig få en scanning serveret. 200 med et `checks`-objekt er et live
  SSRF-hul.
- **Påstand (rød hvis den fejler).** En helt offentlig adresse skal stadig
  give en scanning med **alle ni** tjek. En guard der bliver for stram, er
  lige sådan en fejl som en der forsvinder — den slår scanneren ihjel, og
  det er den retning der ikke var dækket.
- **Regel-kobling (rød hvis den fejler).** Hver prøve bærer det stykke kode
  der afviser dens interval. Uden kravet kan en prøve leve længere end den
  regel den måler, og gaten så grøn uden at dække noget.
- **Rapport (aldrig rød).** Watch-workerens hærdede ruter. Den ligger bag
  spørgsmål 9 og er registreret i `production_drift.json`; en rapport der var
  rød ville låse hvert merge og dermed hele sitets deploy — præcis skaden
  opgave 35 lavede, da `reportlab` døde i CI.

## Brug

    python3 tools/check_live_hardening.py             # mål mod produktion
    python3 tools/check_live_hardening.py --offline   # kun regelkoblingen
    python3 tools/check_live_hardening.py --selftest  # kræv at hver regel kan fejle

Selftesten bruger en transport der ikke taler med nettet, så den er
deterministisk og kan fejle begge veje.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "shared" / "scan-engine.js"
SCAN_URL = "https://eucomply-scan.mahope-eeb.workers.dev/scan?url="
WATCH_URL = "https://eucomply-watch.mahope-eeb.workers.dev"
TIMEOUT = 20
UA = {"User-Agent": "eucomply-live-hardening-gate/1.0"}

# Det ni tjek motoren kører. Navnene læses fra `shared/sample-report.json`,
# fordi opgave 34 gjorde det til det ene datasæt — tallet og navnene skal
# ikke kunne komme i uoverensstemmelse mellem datasæt og gate.
SAMPLE = ROOT / "shared" / "sample-report.json"

# Hver prøve er et reserveret interval, den *skal* afvises. `rule` er det
# stykke kode i `shared/scan-engine.js` der afviser det, så prøven dør med
# reglen i stedet for for at blive en grøn løfte om noget der ikke længere
# findes i koden.
PROBES = (
    {"target": "http://127.0.0.1/", "why": "loopback", "rule": "if (a === 127) return false;"},
    {"target": "http://10.0.0.1/", "why": "RFC 1918 private", "rule": "if (a === 10) return false;"},
    {"target": "http://192.168.1.1/", "why": "RFC 1918 private", "rule": "if (a === 192 && b === 168) return false;"},
    {"target": "http://172.16.0.1/", "why": "RFC 1918 private", "rule": "if (a === 172 && b >= 16 && b <= 31) return false;"},
    {"target": "http://100.64.0.1/", "why": "CGNAT 100.64/10", "rule": "if (a === 100 && b >= 64 && b <= 127) return false;"},
    {
        "target": "http://169.254.169.254/latest/meta-data/",
        "why": "link-local cloud metadata",
        "rule": "if (a === 169 && b === 254) return false;",
    },
    {"target": "http://192.0.2.1/", "why": "TEST-NET-1", "rule": "if (a === 192 && b === 0 && c === 2) return false;"},
    {"target": "http://198.18.0.1/", "why": "benchmarking 198.18/15", "rule": "if (a === 198 && (b === 18 || b === 19)) return false;"},
    {"target": "http://localhost/", "why": "lokalt værtnavn", "rule": 'BLOCKED_HOSTS.has(h)'},
    {"target": "http://foo.internal/", "why": "internt suffiks", "rule": "BLOCKED_HOST_SUFFIXES.some(sfx => h.endsWith(sfx))"},
    {"target": "http://127.1/", "why": "forkortet loopback (ikke fuld quad)", "rule": 'if (/^[\\d.]+$/.test(h)) return false;'},
    {"target": "http://0x7f.1/", "why": "hex-form af loopback", "rule": 'if (/^0[xX][\\da-fA-F.]+$/.test(h)'},
)

VALID = "https://example.com/"

# Intervaller der ER dækket i `shared/scan-engine.js`, men ikke i den motor der
# kører i produktion. Fundet ved den første live-kørsel af denne gate, og
# bekræftet mod koden: `6422adc` (24. august, "begge workers deployet og
# verificeret live") havde otte regler i `isPublicIPv4`; `28795c3` (opgave 3a)
# føjede TEST-NET-1 og 198.18/15 til. Målingen passer de to kilder **præcis**:
# alle otte gamle regler afvises med 400, og de to ny-tilføjede forsøges hentet
# (502). Det identificerer den kørende kode adfærdsmæssigt — noget
# `check_production_drift.py` erklærede umuligt, fordi rod-endpointet i
# produktion svarer 404 uden versionsfelt.
#
# Konsekvensen er lille (begge intervaller er uroutbare, så intet lækker), men
# den er reel: en besøgende kan få vores worker til at *forsøge* en udgående
# hentning til en adresse den burde afvise, og det er præcis samme adfærd en
# rigtig intern adresse ville give, hvis den blev angivet som værtsnavn — den
# fanges først af `assertPublicTarget()` i 28795c3.
#
# Rettelsen er IKKE mere kode: `worker-scan/` skal deployes (spørgsmål 9).
# Når det er sket, svarer begge 400, og denne liste kan slettes — hvilket
# selftesten bekræfter, så den ikke kan blive stående som en løgn.
KNOWN_LAG = {
    "http://192.0.2.1/": "TEST-NET-1 kom først med i 28795c3 (opgave 3a)",
    "http://198.18.0.1/": "198.18/15 benchmarking kom først med i 28795c3 (opgave 3a)",
}

# Watch-workerens ruter som opgave 3a/6 tilføjede. Rapporteres, ikke håndhævet.
WATCH_ROUTES = (
    {"label": "POST /status (kræver ownerToken)", "path": "/status", "method": "POST", "body": '{"url":"https://example.org/"}'},
    {"label": "GET /badge/{site_id}.json (offentligt badge-endpoint)", "path": "/badge/aaaa1111bbbb2222cccc3333dddd4444.json", "method": "GET", "body": None},
)


def transport_get(url: str, method: str = "GET", body: str | None = None) -> tuple[int | None, str, str | None]:
    """Returnér (http_status, krop, fejl). Read-only mod egne endpoints."""
    data = body.encode("utf-8") if body else None
    headers = dict(UA)
    if data:
        headers["content-type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status, response.read().decode("utf-8", errors="replace"), None
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, exc.read().decode("utf-8", errors="replace"), None
        except Exception:
            return exc.code, "", None
    except Exception as exc:
        return None, "", f"kunne ikke nås: {exc}"


def expected_checks() -> list[str]:
    try:
        data = json.loads(SAMPLE.read_text(encoding="utf-8"))
        return [entry["key"] for entry in data["checks"]]
    except Exception:
        return []


def run_checks(probes: tuple = PROBES, get=transport_get, engine_text: str | None = None,
               valid: str = VALID, skip_live: bool = False) -> tuple[list[str], list[str], int]:
    """Returnér (fejl, bemærkninger, antal målinger).

    `engine_text` og `valid` er parametre så selftesten kan læse en kopi
    af motoren i stedet for repoets.
    """
    failures: list[str] = []
    notes: list[str] = []
    attempted: list[str] = []
    measured = 0

    # 0. Selve prøveinstrumentet skal kunne sige noget. En tom liste, en prøve
    #    uden begrundelse eller en motor der ikke kan læses må ikke give grønt.
    if not probes:
        return (["gaten læser ingen prøver — en grøn udgang ville være meningsløs"], notes, 0)
    for probe in probes:
        if not probe.get("why", "").strip():
            failures.append(f"prøven {probe.get('target')!r} har ingen begrundelse")
        if not probe.get("rule", "").strip():
            failures.append(f"prøven {probe.get('target')!r} har ingen regel-kobling")

    if engine_text is None:
        if not ENGINE.is_file():
            return (["shared/scan-engine.js findes ikke — regelkoblingen kan ikke efterprøves"], notes, 0)
        engine_text = ENGINE.read_text(encoding="utf-8", errors="replace")

    missing = [p for p in probes if p["rule"] not in engine_text]
    for probe in missing:
        failures.append(
            f"reglen for {probe['target']} ({probe['why']}) findes ikke længere i "
            f"shared/scan-engine.js — prøven dør med reglen, så den skal fjernes ikke vedligeholdes"
        )
    if missing and len(missing) == len(probes):
        notes.append("ingen prøve har en levende regel-kobling")

    if skip_live:
        notes.append("live-måling sprunget over (--offline)")
        return failures, notes, 0

    # 1. Et reserveret interval må aldrig få en scanning.
    for probe in probes:
        status, body, error = get(SCAN_URL + urllib.parse.quote(probe["target"], safe=""))
        if error:
            notes.append(f"{probe['target']}: {error}")
            continue
        measured += 1
        served = status == 200 and '"checks"' in body
        refused = status is not None and 400 <= status < 500
        if served:
            failures.append(
                f"PRODUKTION SERVEREDE EN SCANNING AF {probe['target']} ({probe['why']}) — "
                f"det er et live SSRF-hul, ikke en afvigelse i copy"
            )
        elif status is not None and 200 <= status < 300:
            failures.append(f"{probe['target']} svarede {status} uden et checks-objekt — svarformen er uventet")
        elif refused:
            notes.append(f"{probe['target']} ({probe['why']}) afvist ved kanten med {status}")
        else:
            # 5xx betyder at workeren *forsøgte* hentningen. Det er ikke en
            # afvisning: en 502 på et reserveret interval er det samme
            # adfærd som en 502 på en intern adresse, og forskellen er præcis
            # det denne gate skal finde. Første live-kørsel af denne gate
            # kaldte 502 "afvist" og var dermed grøn af en fejl.
            attempted.append(probe["target"])
            if probe["target"] not in KNOWN_LAG:
                failures.append(
                    f"PRODUKTION FORSØGTE at hente {probe['target']} ({probe['why']}) og svarede "
                    f"{status} — guarden dækker ikke intervallet, og det er ikke registreret i "
                    f"KNOWN_LAG. Reglen findes i shared/scan-engine.js, så koden er på plads og "
                    f"kun worker-deployet mangler (spørgsmål 9)."
                )
            else:
                notes.append(
                    f"{probe['target']} ({probe['why']}) FORSØGT hentet, svar {status} — "
                    f"intervalet mangler i den motor der kører; kendt og registreret "
                    f"({KNOWN_LAG[probe['target']]})"
                )

    # 2. Guarden må ikke have lukket scanneren. Uden denne påstand er den
    #    første nem at "rette" ved at gøre isPublicHostname() strammere.
    expected = expected_checks()
    if not expected:
        failures.append("shared/sample-report.json kunne ikke læses — de ni tjek er ikke kendt")
    else:
        status, body, error = get(SCAN_URL + urllib.parse.quote(valid, safe=""))
        if error:
            notes.append(f"offentlig adresse: {error}")
        else:
            measured += 1
            if status != 200:
                failures.append(
                    f"en helt offentlig adresse svarede {status} — guarden har lukket scanneren, "
                    f"hvilket er lige sådan en fejl som en forsvunden guard"
                )
            else:
                try:
                    keys = set(json.loads(body).get("checks", {}))
                except Exception as exc:
                    failures.append(f"svaret på en offentlig adresse er ikke JSON: {exc}")
                    keys = set()
                missing_checks = [key for key in expected if key not in keys]
                if missing_checks:
                    failures.append(
                        "scanneren svarer uden "
                        + ", ".join(missing_checks)
                        + f" — motoren kører {len(expected)} tjek, produktion {len(keys)}"
                    )
                else:
                    notes.append(f"offentlig adresse giver alle {len(expected)} tjek")

    return failures, notes, measured


def report_watch(get=transport_get) -> list[str]:
    """Rapporter watch-workerens hærdede ruter. Aldrig rød — se docstring."""
    lines = []
    for route in WATCH_ROUTES:
        status, body, error = get(WATCH_URL + route["path"], method=route["method"], body=route["body"])
        if error:
            lines.append(f"watch: {route['label']} — {error}")
        elif status == 200:
            lines.append(f"watch: {route['label']} — LIVE")
        else:
            lines.append(
                f"watch: {route['label']} — ikke live ({status}); registreret i "
                f"tools/production_drift.json, lukkes ved wrangler deploy (spørgsmål 9)"
            )
    return lines


def selftest() -> int:
    good_engine = ENGINE.read_text(encoding="utf-8", errors="replace")
    cases: list[tuple[str, bool, tuple, object, str]] = []

    REFUSAL = '{"error":"Please provide a valid public http(s) URL, e.g. ?url=example.com"}'

    def _is_probe(url: str) -> bool:
        target = urllib.parse.unquote(url.split("url=", 1)[-1]) if "url=" in url else url
        return any(target.rstrip("/") == probe["target"].rstrip("/") for probe in PROBES)

    def refusing_get(url, method="GET", body=None):
        if _is_probe(url):
            return 400, REFUSAL, None
        return 200, json.dumps({"checks": {k: {"pass": True} for k in expected_checks()}}), None

    def serving_private(url, method="GET", body=None):
        if "url=" in url and not url.split("url=", 1)[-1].endswith("example.com/"):
            return 200, json.dumps({"url": "http://127.0.0.1/", "checks": {"ssl": {}}}), None
        return 200, json.dumps({"checks": {k: {"pass": True} for k in expected_checks()}}), None

    def truncated_product(url, method="GET", body=None):
        if _is_probe(url):
            return 400, REFUSAL, None
        return 200, json.dumps({"checks": {"ssl": {"pass": True}}}), None

    def lag_unregistered(url, method="GET", body=None):
        # 502 = forsøgt hentet. Kun de to intervaller i KNOWN_LAG er kendt.
        if _is_probe(url):
            if any(p["target"] in url for p in PROBES if p["target"] in KNOWN_LAG):
                return 502, '{"error":"upstream"}', None
            return 502, '{"error":"upstream"}', None
        return 200, json.dumps({"checks": {k: {"pass": True} for k in expected_checks()}}), None

    def dead_network(url, method="GET", body=None):
        return None, "", "kunne ikke nås: offline"

    def broken_json(url, method="GET", body=None):
        if _is_probe(url):
            return 400, REFUSAL, None
        return 200, "<html>oops</html>", None

    cases.append(("rent sæt: alle private afvist, ni tjek", True, PROBES, refusing_get, good_engine))
    cases.append(("live SSRF-hul: privat mål får en scanning", False, PROBES, serving_private, good_engine))
    cases.append(("guarden har lukket scanneren (færre tjek)", False, PROBES, truncated_product, good_engine))
    cases.append(("svaret er ikke JSON", False, PROBES, broken_json, good_engine))
    cases.append(("netværket er væk: ikke rød, men må ikke være grøn tavst", True, PROBES, dead_network, good_engine))
    cases.append(
        (
            "uregistreret interval forsøgt hentet (502) er rød",
            False,
            ({"target": "http://203.0.113.1/", "why": "TEST-NET-3", "rule": "if (a === 203 && b === 0 && c === 113) return false;"},),
            lag_unregistered,
            good_engine,
        )
    )
    cases.append(
        (
            "registreret interval forsøgt hentet (502) er grøn men rapporteret",
            True,
            ({"target": "http://192.0.2.1/", "why": "TEST-NET-1", "rule": "if (a === 192 && b === 0 && c === 2) return false;"},),
            lag_unregistered,
            good_engine,
        )
    )
    cases.append(("tom prøveliste må ikke være grøn", False, (), refusing_get, good_engine))
    cases.append(
        (
            "regel-kobling væk i motoren",
            False,
            ({"target": "http://10.0.0.1/", "why": "privat", "rule": "denne regel findes ikke"},),
            refusing_get,
            good_engine,
        )
    )
    cases.append(
        (
            "prøve uden begrundelse",
            False,
            ({"target": "http://10.0.0.1/", "why": "  ", "rule": "if (a === 10) return false;"},),
            refusing_get,
            good_engine,
        )
    )

    failures: list[str] = []
    for name, should_pass, probes, get, engine in cases:
        errs, notes, _ = run_checks(probes=probes, get=get, engine_text=engine)
        passed = not errs
        if passed != should_pass:
            failures.append(
                f"case '{name}': forventet {'grøn' if should_pass else 'rød'}, "
                f"fik {'grøn' if passed else 'rød'}"
                + (f" ({'; '.join(errs)})" if errs else "")
            )
        else:
            print(f"  selftest: {name} — {'grøn som forventet' if passed else 'rød som forventet'}")

    # KNOWN_LAG må ikke holde på en adresse der ikke længere er en prøve: en
    # gammel registrering ville skjule et intervall der nu er dækket, og gaten
    # ville så rapportere en fejl der ikke findes.
    probe_targets = {p["target"] for p in PROBES}
    for stale in sorted(set(KNOWN_LAG) - probe_targets):
        failures.append(f"KNOWN_LAG nævner {stale}, som ikke er blandt prøverne — fjern registreringen")

    # Dækkelsen skal være reel: en grøn kørsel skal have *målt* noget, ellers er
    # den tavst og må ikke tælle som bevis (opgave 33's fejl 3).
    _, _, measured = run_checks(probes=PROBES, get=refusing_get, engine_text=good_engine)
    if measured < 2:
        failures.append("en grøn kørsel måles på færre end to svar")
    else:
        print(f"  selftest: grøn kørsel måler {measured} svar")

    # Offline skal heller ikke være en tavs grøn.
    errs_offline, notes_offline, measured_offline = run_checks(probes=PROBES, get=refusing_get, engine_text=good_engine, skip_live=True)
    if measured_offline != 0 or not any("sprunget over" in n for n in notes_offline):
        failures.append("--offline skal springe live-målingen over og sige det")

    if failures:
        for line in failures:
            print(f"  SELFTEST FEJL: {line}", file=sys.stderr)
        print(f"SELFTEST RØD — {len(failures)} fejl", file=sys.stderr)
        return 1
    print(f"SELFTEST GRØN — alle {len(cases)} negative cases fanges")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    offline = "--offline" in sys.argv

    failures, notes, measured = run_checks(skip_live=offline)
    for note in notes:
        print(f"  {note}")
    if not offline:
        for line in report_watch():
            print(f"  {line}")

    if failures:
        for line in failures:
            print(f"FEJL {line}", file=sys.stderr)
        print(f"FEJL {len(failures)} fund i live-hærdningen", file=sys.stderr)
        return 1
    if measured == 0:
        if offline:
            print("OK    regelkobling grøn — live-målingen er sprunget over med vilje (--offline)")
        else:
            print(
                "ADVARSEL  ingen prøve kunne måles — det er IKKE et bevis på at guarden er live "
                "(trin 11 i gaten er den der fejler på et dødt netværk)"
            )
    else:
        print(f"OK    {measured} målinger: private intervaller afvises, offentlig adresse scanner")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
