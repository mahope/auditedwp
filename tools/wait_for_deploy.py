#!/usr/bin/env python3
"""Vent på at Cloudflare Pages serverer den udgivne plugin-version.

Opgave 47. `deploy-site.yml`'s `tjek produktion`-job læste `/update.json` én
gang og slog fast ved første læsning. CI `36250487311` gjorde sådan:
kvalitetsgate grøn, deploy grøn, og `tjek produktion` rød med *"peger på
eucomply-1.3.12.zip, forventede eucomply-1.3.13.zip"* — og live-sitet serverede
1.3.13 **40 sekunder senere**. Det er en race mellem Pages' servering og det job
der verificerer den, ikke en fejl i udgivelsen. Og fordi verify er et separat
job fra uploaden, kostede den hele kørslen rød for en korrekt udgivelse.

Løsningen er at polle indtil den nye udgivelse ses, med et loft. Loftet er det
vigtige: en port der blot venter, kan aldrig fejle, så en udgivelse der
aldrig kommer ud ville stå som grøn. Derfor er der to separate krav her:

  1. `wait_for_manifest()` giver grønt ved forsøg N og rødt når N er brugt op.
  2. `workflow_findings()` læser `deploy-site.yml` og kræver, at jobbet
     faktisk bruger dette værktøj, at det ikke har den gamle inline-sammenligning
     liggende, og at jobbets `timeout-minutes` overstiger den værste ventetid.
     Uden (2) kunne værktøjet være grønt i porten og ubrugt i workflowen.

Bruges i workflowen som:

    python3 tools/wait_for_deploy.py --base https://eucomplypro.com \\
        --asset /assets/eucomply-1.3.13.zip --attempts 12 --wait 10

Ingen ny afhængighed: kun standardbiblioteket, og ingen secrets læses.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request

BASE = "https://eucomplypro.com"
MANIFEST_PATH = "/update.json"
FINGERPRINT_PATH = "/sitemap.xml"
DEFAULT_FINGERPRINT = "site/sitemap.xml"
DEFAULT_ATTEMPTS = 12
DEFAULT_WAIT = 10.0
DEFAULT_TIMEOUT = 15.0
USER_AGENT = "eucomply-deploy-check/1.0 (+https://eucomplypro.com)"

WORKFLOW = ".github/workflows/deploy-site.yml"

# Jobbets timeout skal overstige den værste ventetid, ellers dræber GitHub
# jobbet midt i ventetiden, og resultatet bliver en afbrudt kørsel i stedet for
# den røde meddelelse der siger HVAD der mangler.
MIN_JOB_TIMEOUT_MINUTES = 5

# De otte øvrige kontrolpunkter i jobbet. Opgave 47 kræver at de er urørte, så
# "urørt" skal være en målt egenskab og ikke en påstand. Hver er en substring
# der SKAL findes i check-production-jobbet.
REQUIRED_CHECKS = (
    ("de 12 interne stier", "/IMPLEMENTATION_PLAN.md"),
    ("cache-buster på de interne stier", "?cb=$GITHUB_RUN_ID"),
    ("nøglesiderne efter upload", "/da/pricing/ /de/pricing/ /fr/pricing/"),
    ("nøglesidernes minimumsstørrelse", '[ "$bytes" -lt 1000 ]'),
    ("zip'en hentes på den URL update.json peger på", "plug.zip"),
    ("zip'en er en zip-fil", '= "PK"'),
    ("Homepage har sin egen genindlæsning", 'grep -q "mahoje.dk" body.html'),
    ("opførslen samles i én fejlkode", "exit $fail"),
)

# Den gamle inline-kontrol, som dette værktøj erstatter. Den slog fast ved
# første læsning, og det er præcis den fejl.
INLINE_MANIFEST_MARKERS = (
    "manifest=$(curl",
    'echo "FEJL: /update.json peger på',
)


def expected_download_url(base: str, asset: str) -> str:
    """Den fulde URL, som /update.json skal pege på efter en udgivelse."""
    if not asset.startswith("/"):
        raise ValueError(f"asset skal starte med /, fik {asset!r}")
    return f"{base.rstrip('/')}{asset}"


def _request(url: str, timeout: float, urlopen=None):
    """Byg en Request med vores egen User-Agent.

    Fundet ved den første rigtige kørsel mod live: Cloudflare svarer **403** på
    `python-urllib/3.13`, som er standardagenten i urllib, og 200 på en
    identificeret agent. Uden denne header ville `tjek produktion` have været
    rød på ALLE 12 forsøg i hver eneste udgivelse — en permanent rød gate,
    præcis den skade opgave 35 beskrev med `reportlab`. Konstanten
    USER_AGENT lå i filen fra starten og blev ikke brugt; kun den rigtige
    kørsel mod live afslørede det, fordi selftestens fixtures ikke går gennem
    `read_manifest` overhovedet. Derfor er der nu en case der læser headeren
    på den Request der faktisk sendes.
    """
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    opener = urlopen or urllib.request.urlopen
    return opener(request, timeout=timeout)


def read_manifest(url: str, timeout: float = DEFAULT_TIMEOUT, opener=None) -> str:
    """Læs `download_url` fra et update.json. Kaster ved alt andet end JSON med feltet."""
    open_fn = opener or (lambda u: _request(u, timeout))
    with open_fn(url) as response:
        raw = response.read()
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    document = json.loads(raw)
    value = document["download_url"]
    if not isinstance(value, str) or not value:
        raise ValueError("download_url er ikke en ikke-tom streng")
    return value


def read_fingerprint(url: str, timeout: float = DEFAULT_TIMEOUT, opener=None) -> str:
    """Læs hele sitemapet som det afgørende fingeraftryk på *denne* udgivelse.

    Målt 29/9, efter at CI `36535432755` blev rød på en korrekt udgivelse:
    `update.json` pegede **allerede** på 1.3.40 da kørslen startede, fordi den
    forrige commit havde udgivet den. `wait_for_manifest()` svarede derfor
    grønt på **første** forsøg og ventede nul sekunder — og så ramte næste
    kontrol en kant der endnu ikke havde rullet den nye udgivelse ud, og
    `/assets/eucomply-1.3.40.zip` svarede 404. Det er præcis den race
    opgave 47 skrev dette værktøj for at slå ihjel, og den var stadig dér:
    værktøjet kan **kun** se en versionsbump og aldrig en almindelig
    indholdsudgivelse.

    Fingeraftrykket løser det, fordi `site/sitemap.xml` regenereres ved enhver
    redaktionel ændring, og dets `lastmod` kommer fra *commit*-historikken
    (`git_dates()`). Den committede fil er derfor et unikt mærke på netop
    den commit der deployes. Målt på de to seneste commits: de afviger i
    **16 `<lastmod>`-linjer** — altså nok til at skelne, selv om ingen af dem
    rørte plugin-versionen.

    Samme User-Agent som `read_manifest`, af den målte grund: Cloudflare
    svarer 403 på pythons standardagent.
    """
    open_fn = opener or (lambda u: _request(u, timeout))
    with open_fn(url) as response:
        raw = response.read()
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    # Det her skal være et sitemap, ikke en fejlside i HTML. Uden den prøve
    # ville en kants 200 med en Cloudflare-fejlside give et fingeraftryk der
    # bare aldrig matcher — grønt for alt andet end det rigtige, men rødt af
    # en grund der ingenting siger om udgivelsen.
    if "<urlset" not in raw:
        raise ValueError("svaret er ikke et sitemap")
    return raw


def local_fingerprint(path: str = DEFAULT_FINGERPRINT) -> str:
    """Det committede fingeraftryk for den commit der er på vej op."""
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    if "<urlset" not in text:
        raise ValueError(f"{path} er ikke et sitemap")
    return text


def wait_for_manifest(
    url: str,
    expected: str,
    attempts: int = DEFAULT_ATTEMPTS,
    wait: float = DEFAULT_WAIT,
    fetch=read_manifest,
    sleep=time.sleep,
) -> tuple[bool, str, int]:
    """Polle `url` indtil den svare præcis `expected`.

    Returnerer `(ok, senest_set_url, brugte_forsøg)`. `ok` er False når loftet
    er brugt op — altså også når serveren svarer noget andet hele vejen, og
    også når den ikke svarer overhovedet. Det er viljen: den eneste forskel
    på "endnu ikke serveret" og "aldrig kommer ud" er tiden, og tiden er præcis
    det loft vi bruger.
    """
    if attempts < 1:
        raise ValueError("attempts skal være mindst 1")
    if not expected:
        # En tom forventning ville være grøn for ALT, også for et svar der er
        # lige så tomt. Det er den værste fejl en port som denne kan have, så
        # den er en fejlkonfiguration og ikke et resultat. Selftestcasen der
        # giver `expected=""` dækker præcis dette.
        raise ValueError("expected må ikke være tom")
    seen = ""
    for attempt in range(1, attempts + 1):
        try:
            seen = fetch(url)
        except (urllib.error.URLError, OSError, ValueError, KeyError, TypeError) as exc:
            # Hvad `read_manifest` kan kaste for et svar der ikke er et
            # brugbart manifest: URLError/OSError for netværket (HTTPError er en
            # URLError), ValueError for ødelagt JSON og for et download_url der
            # ikke er en streng, KeyError for et dokument uden feltet, TypeError
            # for et dokument der ikke er et objekt. En utilgængelig kanten er
            # ikke en grøn udgivelse, og den skal heller ikke se ud som et
            # problem med filen — det gjorde den gamle kontrol.
            seen = f"<{type(exc).__name__}: {exc}>"
        if seen == expected:
            return True, seen, attempt
        if attempt < attempts:
            sleep(wait)
    return False, seen, attempts


# --------------------------------------------------------------------------
# Den samlede udgivelsesport: manifestet OG fingeraftrykket
# --------------------------------------------------------------------------

def wait_for_deploy(
    manifest_url: str,
    expected_url: str,
    fingerprint_url: str,
    expected_fingerprint: str,
    attempts: int = DEFAULT_ATTEMPTS,
    wait: float = DEFAULT_WAIT,
    fetch_manifest=read_manifest,
    fetch_fingerprint=read_fingerprint,
    sleep=time.sleep,
) -> tuple[bool, str, str, int]:
    """Polle begge kilder i **én** løkke, og kræv dem begge.

    Rækkefølgen er bevidst `og`, ikke `eller`: et grønt manifest uden et grønt
    fingeraftryk er præcis den tilstand CI `36535432755` redde på, fordi
    manifestet var gammelt. Og de to løkker er slået sammen, så loftet stadig
    er ét tal for hele ventetiden — ellers ville en port der blot venter kunne
    få dobbelt så lang tid til at blive grøn ved et uheld.

    Returnerer `(ok, set_manifest, set_fingeraftryk, brugte_forsøg)`. `ok` er
    False når loftet er brugt op, altså også når serveren aldrig svarer det
    forventede — porten kan stadig fejle, som den skal.
    """
    if attempts < 1:
        raise ValueError("attempts skal være mindst 1")
    if not expected_url:
        # Samme grund som i `wait_for_manifest`: en tom forventelse er grøn
        # for ALT. Her er den værre, fordi den ville få *fingeraftrykket* til at
        # være det eneste krav — så porten ville blive grøn for enhver udgivelse
        # uden at sammenligne noget som helhed.
        raise ValueError("expected må ikke være tom")
    if not expected_fingerprint:
        raise ValueError("fingerprint må ikke være tom")
    seen_url = ""
    seen_print = ""
    for attempt in range(1, attempts + 1):
        try:
            seen_url = fetch_manifest(manifest_url)
        except (urllib.error.URLError, OSError, ValueError, KeyError, TypeError) as exc:
            seen_url = f"<{type(exc).__name__}: {exc}>"
        try:
            seen_print = fetch_fingerprint(fingerprint_url)
        except (urllib.error.URLError, OSError, ValueError, KeyError, TypeError) as exc:
            seen_print = f"<{type(exc).__name__}: {exc}>"
        if seen_url == expected_url and seen_print == expected_fingerprint:
            return True, seen_url, seen_print, attempt
        if attempt < attempts:
            sleep(wait)
    return False, seen_url, seen_print, attempts


# --------------------------------------------------------------------------
# Krav 2: workflowen skal faktisk bruge værktøjet
# --------------------------------------------------------------------------

def _check_production_job(workflow_text: str) -> str:
    """Kun `tjek produktion`-jobbets egen YAML, så en anden jobs tekst ikke tæller med."""
    lines = workflow_text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if re.match(r"^  \S+:\s*$", line) and "check-production:" in line:
            start = index
            break
    if start is None:
        return ""
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if re.match(r"^  \S+:\s*$", lines[index]):
            end = index
            break
    return "\n".join(lines[start:end])


def workflow_findings(workflow_text: str, expected_asset: str = "") -> list[str]:
    """Fund i `deploy-site.yml` — tom liste betyder at kravet er opfyldt."""
    findings: list[str] = []
    job = _check_production_job(workflow_text)
    if not job:
        return ["check-production-jobbet findes ikke i workflowen"]

    if "tools/wait_for_deploy.py" not in job:
        findings.append("tjek produktion kalder ikke tools/wait_for_deploy.py")
    for marker in INLINE_MANIFEST_MARKERS:
        if marker in job:
            findings.append(f"den gamle inline-manifestkontrol er stadig i jobbet: {marker!r}")

    # Loftet skal være større end nogen rimelig ventetid, ellers afbryder
    # jobbet sig selv før det kan nå at svare.
    attempts = re.search(r"--attempts\s+(\d+)", job)
    wait = re.search(r"--wait\s+(\d+(?:\.\d+)?)", job)
    timeout = re.search(r"^    timeout-minutes:\s*(\d+)", job, re.MULTILINE)
    if not attempts or not wait or not timeout:
        # Ikke et tidlig return: de otte øvrige kontrolpunkter skal stadig
        # læses, ellers ville et job uden --attempts få ÉN fund og et job der
        # også har mistet fire kontrolpunkter få den samme ene. Rækken af fund
        # er diagnosen, så den skal være fuldstændig.
        findings.append("jobbet skal angive --attempts og --wait, og have timeout-minutes")
    else:
        worst = int(attempts.group(1)) * float(wait.group(1))
        if int(timeout.group(1)) * 60 <= worst:
            findings.append(
                f"timeout-minutes={timeout.group(1)} ({int(timeout.group(1)) * 60}s) "
                f"overstiger ikke den værste ventetid på {worst:.0f}s "
                f"({attempts.group(1)} × {wait.group(1)}s)"
            )
        if int(timeout.group(1)) < MIN_JOB_TIMEOUT_MINUTES:
            findings.append(
                f"timeout-minutes={timeout.group(1)} er under minimum {MIN_JOB_TIMEOUT_MINUTES}"
            )

    # En udgivelse uden nye filer skal ikke vente på noget: hvis jobbet slår
    # et loft på kun fordi der intet ændrede sig, er der en ny fejl indført.
    if not re.search(r"--expected-asset|--asset", job):
        findings.append("jobbet fortæller ikke hvilken asset der forventes")

    # 29/9: porten var grøn fordi `--asset` alene var nok. Uden `--fingerprint`
    # kan den ikke se en udgivelse der ikke bumper plugin-versionen — altså
    # næsten alle, og netop dem der fik `36535432755` rød. Uden denne linje
    # kunne fingeraftrykskravet fjernes fra workflowen og værktøjet fortsætte
    # med at være grønt, præcis som `REQUIRED_CHECKS` sigter mod.
    if not re.search(r"--fingerprint", job):
        findings.append(
            "jobbet kræver ikke --fingerprint, så porten kan ikke se "
            "en udgivelse der ikke bumper plugin-versionen"
        )

    for label, marker in REQUIRED_CHECKS:
        if marker not in job:
            findings.append(f"kontrolpunktet er væk fra jobbet: {label} ({marker!r})")

    if expected_asset and expected_asset not in job:
        findings.append(f"jobbet nævner ikke den forventede asset {expected_asset!r}")
    return findings


def read_workflow(path: str = WORKFLOW) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


# --------------------------------------------------------------------------
# Selftest — hver case skal kunne fejle
# --------------------------------------------------------------------------

def _sequence(values):
    """En fetch der svarer hvert element i rækkefølge, og kaster på sidste forsøg hvis den løber tør."""
    state = {"index": 0}

    def fetch(url):
        index = state["index"]
        state["index"] += 1
        if index >= len(values):
            raise ValueError("kalder flere gange end der er svar")
        value = values[index]
        if isinstance(value, Exception):
            raise value
        return value

    return fetch, state


class _Slept:
    def __init__(self):
        self.calls: list[float] = []

    def __call__(self, seconds):
        self.calls.append(seconds)


def _response_with(body: bytes):
    """Et svar der ligner det en server faktisk sender."""

    class _Response:
        def read(self):
            return body

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    return _Response()


def _xml_response(body: bytes):
    return _response_with(body)


def _html_response(body: bytes):
    return _response_with(body)


def _selftest() -> int:
    cases = 0
    failures: list[str] = []

    def case(name: str, ok: bool, detail: str = "") -> None:
        nonlocal cases
        cases += 1
        if ok:
            print(f"  fanget  {name}")
        else:
            print(f"  FEJL    {name}{(' — ' + detail) if detail else ''}")
            failures.append(name)

    expected = "https://eucomplypro.com/assets/eucomply-1.3.13.zip"
    old = "https://eucomplypro.com/assets/eucomply-1.3.12.zip"
    url = BASE + MANIFEST_PATH + "?cb=deadbeef"

    # 1. Ny version i første læsning: grønt, ét forsøg, ingen ventetid.
    slept = _Slept()
    fetch, _ = _sequence([expected])
    ok, seen, used = wait_for_manifest(url, expected, attempts=12, wait=10, fetch=fetch, sleep=slept)
    case("første læsning er den nye version → grøn uden at vente", ok and seen == expected and used == 1)
    case("ingen ventetid når svaret er rigtigt med det samme", slept.calls == [], repr(slept.calls))

    # 2. Præcis den målte fejl: gammel version to gange, ny tredje gang.
    slept = _Slept()
    fetch, _ = _sequence([old, old, expected])
    ok, seen, used = wait_for_manifest(url, expected, attempts=12, wait=10, fetch=fetch, sleep=slept)
    case("gammel version i de to første læsninger → grønt på forsøg 3", ok and used == 3)
    case("ventetiden er loft minus ét", slept.calls == [10, 10], repr(slept.calls))

    # 3. En version der ALDRIG kom ud skal give rødt, inden for loftet.
    slept = _Slept()
    fetch, state = _sequence([old] * 12)
    ok, seen, used = wait_for_manifest(url, expected, attempts=12, wait=10, fetch=fetch, sleep=slept)
    case("en version der aldrig serveres → rødt", not ok)
    case("alle tolv forsøg bruges", used == 12 and state["index"] == 12, f"used={used} index={state['index']}")
    case("sidste sette værdi står i resultatet", seen == old, seen)

    # 4. Serveren svarer slet ikke. Det må ikke blive grønt af et tilfælde.
    fetch, _ = _sequence([urllib.error.URLError("kanten svarer ikke")] * 12)
    slept = _Slept()
    ok, seen, _ = wait_for_manifest(url, expected, attempts=3, wait=10, fetch=fetch, sleep=slept)
    case("netværksfejl i hvert forsøg → rødt", not ok)
    case("netværksfejlen er i resultatet, ikke en stille grøn", "URLError" in seen, seen)

    # 5. Ugyldigt JSON og manglende felt må heller ikke være grønt.
    fetch, _ = _sequence([json.JSONDecodeError("bøvet", "<html>", 0)] * 3)
    ok, _, _ = wait_for_manifest(url, expected, attempts=3, wait=10, fetch=fetch, sleep=_Slept())
    case("ugyldigt JSON → rødt", not ok)

    fetch, _ = _sequence([KeyError("download_url")] * 3)
    ok, _, _ = wait_for_manifest(url, expected, attempts=3, wait=10, fetch=fetch, sleep=_Slept())
    case("manglende download_url → rødt", not ok)

    # 6. Et loft på 1 må give rødt på den gamle version med det samme — altså
    #    at loftet faktisk er det, der afgør, ikke et fast antal læsninger.
    fetch, _ = _sequence([old])
    ok, _, used = wait_for_manifest(url, expected, attempts=1, wait=10, fetch=fetch, sleep=_Slept())
    case("loft på 1 gør den gamle version rød", not ok and used == 1)

    # 7. En tom forventning er den værste fejl porten kan have: den er grøn for
    #    ALT, også for et lige så tomt svar. Den skal hæve, ikke svare grønt.
    #    Casen blev skrevet med `expected=""` og et tomt svar OG var grøn af den
    #    forkerte grund — den afslørede hullet.
    fetch, _ = _sequence([""] * 3)
    try:
        wait_for_manifest(url, "", attempts=3, wait=10, fetch=fetch, sleep=_Slept())
        case("en tom forventning hæver i stedet for at være grøn", False, "ingen undtagelse")
    except ValueError:
        case("en tom forventning hæver i stedet for at være grøn", True)

    # 8. Nul forsøg er en mislykket konfiguration, ikke et grønt resultat.
    try:
        wait_for_manifest(url, expected, attempts=0, fetch=lambda u: expected, sleep=_Slept())
        case("attempts=0 hæver i stedet for at være grøn", False, "ingen undtagelse")
    except ValueError:
        case("attempts=0 hæver i stedet for at være grøn", True)

    # 9. Asset uden førende slash må ikke give en stille forkert forventning.
    try:
        expected_download_url(BASE, "assets/eucomply-1.3.13.zip")
        case("asset uden førende slash afvises", False, "ingen undtagelse")
    except ValueError:
        case("asset uden førende slash afvises", True)

    # 9b. Den Request der faktisk sendes skal bære vores egen User-Agent.
    #     Cloudflare svarer 403 på `python-urllib/3.13` (målt live 26/9), så
    #     uden headeren ville porten være rød i hver eneste udgivelse. En case
    #     der læser headeren på den rigtige Request er det der gør det umuligt
    #     at fjerne den igen — de øvrige cases går alle uden om `read_manifest`.
    sent = {}

    class _Response:
        def read(self):
            return b'{"download_url": "https://eucomplypro.com/assets/eucomply-1.3.13.zip"}'

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def _recording_urlopen(request, timeout=None):
        sent["url"] = request.full_url
        sent["headers"] = {k.lower(): v for k, v in request.headers.items()}
        sent["timeout"] = timeout
        return _Response()

    value = read_manifest(
        "https://eucomplypro.com/update.json?cb=1",
        opener=lambda u: _request(u, 7, urlopen=_recording_urlopen),
    )
    case(
        "manifestet læses med vores egen User-Agent",
        "eucomply-deploy-check" in sent.get("headers", {}).get("user-agent", ""),
        repr(sent.get("headers")),
    )
    case("URL'en og timeout'en gives videre som de er", sent.get("url", "").endswith("?cb=1") and sent.get("timeout") == 7, repr(sent))
    case("det læste download_url er værdien fra svaret", value == expected, value)

    # 10. Workflow-kravet skal kunne fejle begge veje.
    good_workflow = f"""
jobs:
  check-production:
    name: tjek produktion
    timeout-minutes: 10
    steps:
    - name: Vent på udgivelsen
      run: |
        python3 tools/wait_for_deploy.py --base https://eucomplypro.com \\
            --asset /assets/eucomply-1.3.13.zip --fingerprint site/sitemap.xml \\
            --attempts 12 --wait 10

          if [ "$code" != "200" ]; then
            echo "FEJL: $url gav status $code"
          fi
          for route in /AGENTS.md /BUDGET.md /DECISION.md /STATUS.md /RESEARCH.md \\
                     /KANALPLAN.md /INTERVIEW-GUIDE.md /wrangler.toml \\
                     /ceo-loop3.sh /ops/auditlog.py /POSTS/01-eighty-five-niches.md \\
                     /IMPLEMENTATION_PLAN.md; do
            code=$(curl -sS -o leak.out -w '%{{http_code}}' "$url$route?cb=$GITHUB_RUN_ID" || echo 000)
          done
          for route in / /pro/ /pricing/ /da/pricing/ /de/pricing/ /fr/pricing/ \\
                     /da/pro/ /de/pro/ /fr/pro/ /scan/ /plugin/ /privacy/ /sample/; do
            bytes=$(wc -c < page.html | tr -d ' ')
            if [ "$code" != "200" ] || [ "$bytes" -lt 1000 ]; then
              fail=1
            fi
          done
          asset="/assets/eucomply-1.3.13.zip"
          code=$(curl -sS -o plug.zip -w '%{{http_code}}' "${{url%/}}$asset?cb=$GITHUB_RUN_ID" || echo 000)
          if [ "$code" = "200" ] && [ "$(head -c 2 plug.zip)" = "PK" ]; then
            echo "OK: $asset er 200 og en zip-fil"
          fi
          code=$(curl -sS -o body.html -w '%{{http_code}}' "$url" || echo 000)
          if [ "$code" = "200" ] && grep -q "mahoje.dk" body.html; then
            echo "OK: $url svarer 200 og indeholder mahoje.dk"
          fi
          exit $fail
"""
    case("en workflow der bruger værktøjet korrekt har ingen fund", workflow_findings(good_workflow) == [], repr(workflow_findings(good_workflow)))

    # 11. Den gamle inline-kontrol, selvom værktøjet også kaldes.
    inline = good_workflow.replace(
        "          exit $fail",
        '          manifest=$(curl -sS "$url/update.json")\n'
        '          if [ "$manifest" = "$expected" ]; then :; else\n'
        '            echo "FEJL: /update.json peger på \'$manifest\', forventede \'$expected\'"\n'
        "          fi\n"
        "          exit $fail",
    )
    findings = workflow_findings(inline)
    case(
        "inline-kontrollen stadig i jobbet → fund",
        len(findings) == 2 and all("inline-manifestkontrol" in f for f in findings),
        repr(findings),
    )

    # 12. Værktøjet ikke kaldt.
    findings = workflow_findings(good_workflow.replace("tools/wait_for_deploy.py", "tools/andre.py"))
    case("værktøjet ikke kaldt → fund", any("kalder ikke tools/wait_for_deploy.py" in f for f in findings), repr(findings))

    # 13. `good_workflow` uden --fingerprint: værktøjet er der, og ser det
    #     ud til at virke, men porten kan ikke se en udgivelse uden
    #     versionsbump. Uden denne case kunne kravet slettes fra
    #     `workflow_findings` og workflowen samtidig, og selftesten ville
    #     stadig være grøn — to filer der hver især er grønne fordi de
    #     kontrollerer hinanden uden at nogen af dem gør det.
    findings = workflow_findings(good_workflow.replace(" --fingerprint site/sitemap.xml", ""))
    case("en workflow uden --fingerprint → fund",
         any("--fingerprint" in f for f in findings), repr(findings))

    # 14. Loft kortere end jobbets timeout er korrekt; et loft der overstiger
    #     jobbets timeout dræber jobbet — altså fund.
    findings = workflow_findings(good_workflow.replace("--attempts 12 --wait 10", "--attempts 60 --wait 10"))
    case("et loft der overstiger jobbets timeout → fund", any("overstiger ikke den værste ventetid" in f for f in findings), repr(findings))

    # 15. Et af de otte øvrige kontrolpunkter forsvundet → fund.
    findings = workflow_findings(good_workflow.replace('= "PK"', '= "XX"'))
    case("et øvrigt kontrolpunkt forsvundet → fund", any("kontrolpunktet er væk" in f for f in findings), repr(findings))

    # 16. Uden timeout-minutes må vi ikke gætte jobbets afgrænsning.
    findings = workflow_findings(good_workflow.replace("    timeout-minutes: 10\n", ""))
    case("uden timeout-minutes → fund", any("timeout-minutes" in f for f in findings), repr(findings))

    # 17. En anden jobs tekst må ikke tælle som dækning. check-production
    #     læser kun sit eget job, så en opgave i et andet job giver fund.
    other = """
jobs:
  deploy:
    timeout-minutes: 10
    steps:
      - run: python3 tools/wait_for_deploy.py --attempts 12 --wait 10
  check-production:
    timeout-minutes: 10
    steps:
      - run: echo "ingenting"
"""
    findings = workflow_findings(other)
    case(
        "et andet jobs kald dækker ikke check-production",
        any("kalder ikke tools/wait_for_deploy.py" in f for f in findings) and any("kontrolpunktet er væk" in f for f in findings),
        repr(findings),
    )

    # 18. FINGERPRINT. De otte cases ovenfor kan alle være grønne mens
    #     værktøjet i virkeligheden ikke ser en udgivelse. Det er præcis hvad
    #     der skete i CI 36535432755: manifestet var rigtigt fra første
    #     læsning, så porten svarede grønt uden at vente, og næste kontrol
    #     ramte en kant der ikke havde rullet ud. Case 16a er den målte fejl.
    print_sitemap = '<?xml version="1.0"?><urlset><url><loc>/pro/</loc><lastmod>2026-09-29</lastmod></url></urlset>'
    new_sitemap = '<?xml version="1.0"?><urlset><url><loc>/pro/</loc><lastmod>2026-09-30</lastmod></url></urlset>'

    # 18a. Manifestet er rigtigt hele vejen, fingeraftrykket kommer først til
    #      sidst. Det er den rigtige grøn, og den må IKKE komme på forsøg 1.
    fetch_m, _ = _sequence([expected] * 3)
    fetch_f, _ = _sequence([print_sitemap, print_sitemap, new_sitemap])
    slept = _Slept()
    ok, seen_url, seen_print, used = wait_for_deploy(
        url, expected, url.replace("update.json", "sitemap.xml"), new_sitemap,
        attempts=12, wait=10, fetch_manifest=fetch_m, fetch_fingerprint=fetch_f, sleep=slept,
    )
    case("manifestet rigtigt fra start, fingeraftrykket først til sidst → grønt på forsøg 3",
         ok and used == 3, f"ok={ok} used={used}")
    case("et gammelt fingeraftryk er ikke grønt, selv med rigtigt manifest",
         used == 3 and seen_print == new_sitemap, seen_print[:60])

    # 18b. DEN MÅLTE FEJL. Manifestet er rigtigt på **første** forsøg —
    #      nøjagtig som det var live i 36535432755 — og fingeraftrykket er
    #      aldrig det nye. Et værktøj uden fingerprint-kravet svarer grønt her.
    fetch_m, state_m = _sequence([expected] * 12)
    fetch_f, _ = _sequence([print_sitemap] * 12)
    ok, _, _, used = wait_for_deploy(
        url, expected, url.replace("update.json", "sitemap.xml"), new_sitemap,
        attempts=12, wait=10, fetch_manifest=fetch_m, fetch_fingerprint=fetch_f, sleep=_Slept(),
    )
    case("manifestet alene er IKKE grønt, når fingeraftrykket aldrig kommer",
         not ok, "porten ville have svaret grønt uden fingerprint-kravet")
    case("den afventende port bruger hele loftet", used == 12, f"used={used}")

    # 18c. Omvendt: nyt fingeraftryk uden nyt manifest må heller ikke være
    #      grønt, ellers er det kun den ene halvdel af kravet der tæller.
    fetch_m, _ = _sequence([old] * 12)
    fetch_f, _ = _sequence([new_sitemap] * 12)
    ok, _, _, _ = wait_for_deploy(
        url, expected, url.replace("update.json", "sitemap.xml"), new_sitemap,
        attempts=12, wait=10, fetch_manifest=fetch_m, fetch_fingerprint=fetch_f, sleep=_Slept(),
    )
    case("nyt fingeraftryk uden nyt manifest → rødt", not ok)

    # 18d. Begge rigtige fra første læsning: grønt uden ventetid, fordi så
    #      sket der intet at vente på. Loftet må ikke gøre en korrekt
    #      udgivelse langsommere end nødvendigt.
    fetch_m, _ = _sequence([expected])
    fetch_f, _ = _sequence([new_sitemap])
    slept = _Slept()
    ok, _, _, used = wait_for_deploy(
        url, expected, url.replace("update.json", "sitemap.xml"), new_sitemap,
        attempts=12, wait=10, fetch_manifest=fetch_m, fetch_fingerprint=fetch_f, sleep=slept,
    )
    case("begge rigtige fra første læsning → grønt uden at vente",
         ok and used == 1 and slept.calls == [], f"ok={ok} used={used} slept={slept.calls}")

    # 18e. En fejlside i HTML er ikke et fingeraftryk. Uden prøven ville
    #      kanten svare 200 med en Cloudflare-side, og porten ville rødde
    #      på en grund der ingenting siger om udgivelsen.
    try:
        read_fingerprint("https://eucomplypro.com/sitemap.xml",
                         opener=lambda u: _html_response(b"<html>error 1000</html>"))
        case("en HTML-fejlside er ikke et fingeraftryk", False, "ingen undtagelse")
    except ValueError:
        case("en HTML-fejlside er ikke et fingeraftryk", True)

    # 18f. Fingeraftrykket skal læses med vores egen User-Agent, af den målte
    #      grund fra 26/9: Cloudflare svarer 403 på pythons standardagent.
    sent_fp = {}

    def _recording_fp(request, timeout=None):
        sent_fp["headers"] = {k.lower(): v for k, v in request.headers.items()}
        return _xml_response(b'<?xml version="1.0"?><urlset><url><loc>/pro/</loc></url></urlset>')

    read_fingerprint("https://eucomplypro.com/sitemap.xml?cb=1",
                     opener=lambda u: _request(u, 7, urlopen=_recording_fp))
    case("fingeraftrykket læses med vores egen User-Agent",
         "eucomply-deploy-check" in sent_fp.get("headers", {}).get("user-agent", ""),
         repr(sent_fp.get("headers")))

    # 18g. Et tomt fingerprint-krav er den værste fejl: det gør manifestet
    #      alene afgørende, hvilket er præcis den målte fejl 16b.
    fetch_m, _ = _sequence([expected])
    fetch_f, _ = _sequence([new_sitemap])
    try:
        wait_for_deploy(url, expected, url, "", attempts=3, wait=10,
                        fetch_manifest=fetch_m, fetch_fingerprint=fetch_f, sleep=_Slept())
        case("et tomt fingerprint-krav hæver i stedet for at være grønt", False, "ingen undtagelse")
    except ValueError:
        case("et tomt fingerprint-krav hæver i stedet for at være grønt", True)

    print()
    if failures:
        print(f"SELFTEST RØD — {len(failures)} af {cases} cases fejlede:")
        for name in failures:
            print(f"  - {name}")
        return 1
    print(f"SELFTEST GRØN — alle {cases} negative cases fanges")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default=BASE, help="sitets rod-URL")
    parser.add_argument(
        "--asset",
        default=None,
        help="den asset /update.json skal pege på, fx /assets/eucomply-1.3.13.zip",
    )
    parser.add_argument(
        "--fingerprint",
        default=DEFAULT_FINGERPRINT,
        help="den committede fil der identificerer netop denne udgivelse "
             "(default " + DEFAULT_FINGERPRINT + ")",
    )
    parser.add_argument("--attempts", type=int, default=DEFAULT_ATTEMPTS)
    parser.add_argument("--wait", type=float, default=DEFAULT_WAIT)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument(
        "--check-workflow",
        action="store_true",
        help="kontrollér bare at deploy-site.yml bruger værktøjet korrekt, uden netværk",
    )
    parser.add_argument("--workflow", default=WORKFLOW, help="stien til workflowen (default " + WORKFLOW + ")")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    if args.check_workflow:
        # Uden denne tilstand ville kravet "workflowen bruger værktøjet" kun
        # være testet mod fixtures i selftesten, og værktøjet kunne glide fra
        # workflowen igen helt uopdaget — præcis den fejlklasse opgave 39
        # handlede om en kontrol der så ud som en gate uden at være det.
        try:
            text = read_workflow(args.workflow)
        except OSError as exc:
            print(f"FEJL: {args.workflow} kan ikke læses: {exc}")
            return 1
        found = workflow_findings(text)
        if found:
            print(f"FEJL: {len(found)} fund i {args.workflow}:")
            for finding in found:
                print(f"  - {finding}")
            return 1
        print(f"WORKFLOW GRØN: {args.workflow} bruger wait_for_deploy.py, og de otte øvrige kontrolpunkter er der")
        return 0

    if not args.asset:
        # Uden --asset ved værktøjet ikke hvad der forventes, og så ville det
        # godkende uanset hvad der står i live. Det er en fejlkonfiguration,
        # ikke et grønt resultat.
        print("FEJL: --asset skal angive hvilken version der forventes")
        return 2

    try:
        expected_fingerprint = local_fingerprint(args.fingerprint)
    except (OSError, ValueError) as exc:
        # Uden det lokale fingeraftryk er der intet at sammenligne imod, og så
        # ville porten uden denne fejl vente på en udgivelse den aldrig kan
        # genkende — altså rød for alt andet end en rigtig udgivelse, eller
        # grøn fordi kravet var tomt. Begge er værre end at stoppe her.
        print(f"FEJL: {args.fingerprint} kan ikke bruges som fingeraftryk: {exc}")
        return 2

    stamp = int(time.time())
    manifest_url = f"{args.base.rstrip('/')}{MANIFEST_PATH}?cb={stamp}"
    fingerprint_url = f"{args.base.rstrip('/')}{FINGERPRINT_PATH}?cb={stamp}"
    expected = expected_download_url(args.base, args.asset)

    ok, seen, seen_print, used = wait_for_deploy(
        manifest_url, expected, fingerprint_url, expected_fingerprint,
        attempts=args.attempts, wait=args.wait,
        fetch_manifest=lambda u: read_manifest(u, args.timeout),
        fetch_fingerprint=lambda u: read_fingerprint(u, args.timeout),
    )
    if ok:
        print(
            f"OK: {manifest_url} peger på {expected} (forsøg {used} af {args.attempts}), "
            f"og {FINGERPRINT_PATH} er byte-identisk med {args.fingerprint}"
        )
        return 0
    print(
        f"FEJL: {manifest_url} peger på '{seen}' og {FINGERPRINT_PATH} er "
        f"{'byte-identisk med' if seen_print == expected_fingerprint else 'IKKE den nye'} "
        f"({args.fingerprint}) efter {used} forsøg "
        f"({args.attempts} × {args.wait:g}s), forventede '{expected}'.\n"
        "Hvis udgivelsen lige er kørt, kan Cloudflare Pages endnu ikke have serveret den.\n"
        "Efterprøv selv med cache-buster, før du genkører workflowen."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
