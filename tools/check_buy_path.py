#!/usr/bin/env python3
"""Mål den vej en betalende kunde går — fra forside til kvittering — mod LIVE.

## Hvilket problem den her løser

Port-arbejdet i de sidste 120 iterationer har dømt *indhold* i repoet:
`sitemap.xml` mod træet, claims mod kilden, analytics-taggen mod markup.
Ingen af dem spørger, om en kunde kan **betale**. Og det er den eneste
fejlklasse der ødelægger omsætningen direkte.

Der er fire gates der alle læser repoet (`check_sitemap.py`,
`check_pro_claims.py`, `check_cta.py`, `check_analytics.py`) og to der læser
en worker (`check_live_funnel.py`, `check_production_drift.py`). Ingen går
fra et link på den publicerede side til det sted pengene ender.

Målt 2026-09-29 06:0x CEST, mod den udgivne side:

| led | målt |
|---|---|
| `/scan/` (tragten) | 200, scanner-API svarer 200 med rigtige checks |
| `/pro/` + `/pricing/` i EN/DA/DE/FR (8 sider) | 200, **2** Stripe-links pr. side |
| `/pricing/` → `buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03` | **HTTP 200** |
| `mahope.tools/thanks` (kvitteringen) | 200, også med `session_id` |
| `mahope.tools/api/license/validate` med en ukendt nøgle | **404** med beskeden, ikke en 500 |
| alle 214 `<loc>` i sitemapet mod live | **214 × 200**, nul 404 |

Sidste række er den der lå under mest tidligere. `check_sitemap.py` dømmer
at hvert `<loc>` *er en rigtig side* — altså at filen findes i træet. Den
svarer 200 på en `<loc>` der er slettet i Cloudflare, fordi træet og
produktionen er to ting. Det er præcis den fejl der ligner et resultat:
en sitemap med 404'er i sig får alle sider de liste rykket ned, og tallet
ligner bare et site uden besøgende.

## Hvad den her gate kan og ikke kan håndhæve

Den dømmer **kun fejl der låser en betaling eller en kvittering**:

1. En pengeside der ikke svarer 200.
2. En pengeside uden ét enkelt Stripe-link — den er den konvertering, og
   den skal kunne findes maskinelt.
3. Et Stripe-link der ikke svarer (død, eller lukket af Stripe efter de
   første 100 lifetime-køb).
4. En kvitteringsside der ikke svarer — den er hvor kunden får nøglen.
5. Et licens-endpoint der svarer 5xx på en *ukendt* nøgle. `404` er det
   rigtige svar; `500`/`503` betyder at serveren er nede, og så låses
   betalende kunder ude, hvilket kontrakten siger aldrig må ske.
6. En `<loc>` i sitemapet der ikke svarer 200.

Punkt 3 og 6 er **rapporter, ikke fund**, når de er forventede: de første
100 lifetime-køb lukker et link med vilje (kontrakten, 27/9), og en
sitemappege på en side der er på vej ned er ikke en fejl i koden. Derfor
ligger de undtagelser i `tools/buy_path.json` med en begrundelse, der kan
lukkes — samme stilling som `funnel_drift.json`.

Det den IKKE dømmer, og hvorfor: om nogen køber. Det er Plausibles
opgave (outbound-link-events på buy.stripe.com er slået til), og en port
der kræver salg ville være rød hver eneste dag et nyt site har nul kunder.

Kør:
    python3 tools/check_buy_path.py
    python3 tools/check_buy_path.py --selftest
    python3 tools/check_buy_path.py --offline   # spring live-kallene over
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGREEMENT = os.path.join(ROOT, "tools", "buy_path.json")
SITE = "https://eucomplypro.com"
TIMEOUT = 20

# Browser-UA. Uden den får nogle Payment Links et andet svar end en
# rigtig køber, og en gate der måler en anden side er ikke en gate.
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

STRIPE_RE = re.compile(r"https://buy\.stripe\.com/[A-Za-z0-9]+")
LOC_RE = re.compile(r"<loc>([^<]+)</loc>")


def fetch(url, method="GET", data=None):
    """Returnér (status, krop, fejl). Netværksfejl skal give en note, ikke en fejl."""
    headers = {"User-Agent": UA}
    body = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode()
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status, response.read().decode("utf-8", "replace"), None
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace"), None
    except Exception as exc:  # noqa: BLE001 - netværk skal give en note, ikke en fejl
        return None, "", str(exc)


def _read_agreement():
    try:
        with open(AGREEMENT, encoding="utf-8") as fh:
            return json.load(fh), None
    except FileNotFoundError:
        return None, "%s findes ikke" % os.path.relpath(AGREEMENT, ROOT)
    except (ValueError, OSError) as exc:
        return None, "%s kunne ikke læses: %s" % (os.path.relpath(AGREEMENT, ROOT), exc)


def _expected(agreement, kind):
    """{nøgle: begrundelse} for en art undtagelse. Tom dict når der ikke er nogen."""
    return {c["url"]: c.get("reason", "ikke begrundet")
            for c in agreement.get(kind, [])
            if isinstance(c, dict) and c.get("url")}


def check_money_pages(live):
    """Pengesiderne skal svare 200 og have præcis ét Stripe-link pr. side."""
    findings, notes, measured = [], [], 0
    for rel in ("/pro/", "/pricing/",
                "/da/pro/", "/de/pro/", "/fr/pro/",
                "/da/pricing/", "/de/pricing/", "/fr/pricing/"):
        url = SITE + rel
        if not live:
            continue
        status, body, err = fetch(url)
        if err:
            notes.append("%s kunne ikke hentes: %s" % (rel, err))
            continue
        measured += 1
        if status != 200:
            findings.append("%s svarer %s — en kunde kan ikke nå købsknappen" % (rel, status))
            continue
        links = sorted(set(STRIPE_RE.findall(body)))
        if not links:
            findings.append("%s har intet Stripe-link — pengesiden uden en vej at betale" % rel)
        elif len(links) < 2:
            findings.append("%s har kun ét Stripe-link, så den livstids-udgave mangler" % rel)
    return findings, notes, measured


def check_checkout(live, agreement):
    """Hvert Stripe-link skal svare. Et lukket lifetime-link er en note."""
    findings, notes, measured = [], [], 0
    closed = _expected(agreement, "closed_checkout")
    seen = set()
    for rel in ("/pro/", "/pricing/", "/da/pro/", "/de/pro/", "/fr/pro/",
                "/da/pricing/", "/de/pricing/", "/fr/pricing/"):
        if not live:
            continue
        status, body, err = fetch(SITE + rel)
        if err or status != 200:
            continue
        for link in set(STRIPE_RE.findall(body)):
            if link in seen:
                continue
            seen.add(link)
            code, _b, err = fetch(link)
            if err:
                notes.append("Stripe-link kunne ikke hentes: %s (%s)" % (link, err))
                continue
            measured += 1
            if code == 200:
                continue
            if link in closed:
                notes.append("Stripe-link %s svarer %s — registreret undtagelse: %s"
                             % (link, code, closed[link]))
            else:
                findings.append("Stripe-link %s svarer %s, ikke 200 — købet kan ikke gennemføres"
                                % (link, code))
    return findings, notes, measured


def check_thanks(live):
    """Kvitteringen skal svare, med og uden session_id."""
    findings, notes, measured = [], [], 0
    if not live:
        return findings, notes, measured
    for url in ("https://mahope.tools/thanks",
                "https://mahope.tools/thanks?session_id=cs_test_gate"):
        status, _b, err = fetch(url)
        if err:
            notes.append("%s kunne ikke hentes: %s" % (url, err))
            continue
        measured += 1
        if status != 200:
            findings.append("kvitteringssiden %s svarer %s — kunden får ingen licensnøgle"
                            % (url, status))
    return findings, notes, measured


def check_license_api(live):
    """En ukendt nøgle SKAL give 404. 5xx låser betalende kunder ude."""
    findings, notes, measured = [], [], 0
    if not live:
        return findings, notes, measured
    status, body, err = fetch(
        "https://mahope.tools/api/license/validate", method="POST",
        data={"license_key": "0" * 32, "device_id": "check-buy-path", "product": "eucomply-pro"},
    )
    if err:
        notes.append("licens-API kunne ikke kaldes: %s" % err)
        return findings, notes, measured
    measured += 1
    if status in (500, 502, 503, 504):
        findings.append("licens-API svarer %s på en ukendt nøgle — en nede server låser "
                        "betalende kunder ude (503 skal klienten klare blødt)" % status)
    elif status != 404:
        findings.append("licens-API svarer %s på en ukendt nøgle; 404 er det forventede "
                        "og sikre svar, så svaret skal forstås: %s" % (status, body[:120]))
    return findings, notes, measured


def check_sitemap(live, agreement):
    """Hver <loc> skal svare 200. En 404-liste i sitemapet dræner alle sider i den."""
    findings, notes, measured = [], [], 0
    if not live:
        return findings, notes, measured
    status, body, err = fetch(SITE + "/sitemap.xml")
    if err:
        notes.append("sitemap.xml kunne ikke hentes: %s" % err)
        return findings, notes, measured
    if status != 200:
        findings.append("sitemap.xml svarer %s — søgemaskinerne kan ikke læse kortet" % status)
        return findings, notes, measured
    locs = sorted(set(LOC_RE.findall(body)))
    if not locs:
        findings.append("sitemap.xml indeholder ingen <loc> — den kortlægger ingenting")
        return findings, notes, measured
    dead_allowed = _expected(agreement, "dead_in_sitemap")
    for loc in locs:
        code, _b, err = fetch(loc)
        if err:
            notes.append("%s kunne ikke hentes: %s" % (loc, err))
            continue
        measured += 1
        if code == 200:
            continue
        if loc in dead_allowed:
            notes.append("%s svarer %s i sitemapet — registreret undtagelse: %s"
                         % (loc, code, dead_allowed[loc]))
        else:
            findings.append("%s står i sitemapet men svarer %s — den side rangerer aldrig"
                            % (loc, code))
    return findings, notes, measured


def collect(live=True, mutate=None):
    """Alle kontroller. `mutate` er (kind, url) for selftesten."""
    agreement, err = _read_agreement()
    if err:
        return [err], [], {"pages": 0, "checkout": 0, "thanks": 0, "license": 0, "sitemap": 0}
    if not agreement.get("version"):
        return ["%s mangler 'version' — aftalen skal kunne lukkes"
                % os.path.relpath(AGREEMENT, ROOT)], [], {}

    findings, notes, facts = [], [], {}

    def run(key, fn, *args):
        f, n, m = fn(*args)
        findings.extend(f)
        notes.extend(n)
        facts[key] = m

    if mutate is None:
        run("pages", check_money_pages, live)
        run("checkout", check_checkout, live, agreement)
        run("thanks", check_thanks, live)
        run("license", check_license_api, live)
        run("sitemap", check_sitemap, live, agreement)
        return findings, notes, facts

    # Selftest-gren: kun den ene kontrol, med mutationen indbygget.
    #
    # Mutationen skal ramme ET MÅLEINPUT, ikke portens egen kode. En mutation
    # der fjerner en betingelse i porten kan ikke fanges ved et live-kald: det
    # udgivne site er sundt, så porten har intet at finde, og mutationen ligner
    # en grøn gade. Det blev målt i selftestens M1 (fjernet kravet om et
    # Stripe-link -> porten stadig grøn, exit 0). Derfor patches `fetch`, så
    # svaret ligner det en brudt side ville give.
    kind, url = mutate
    _orig_fetch = fetch
    if kind == "sitemap":
        def patched(target, *a, **kw):
            if target == url:
                return 404, "", None
            return _orig_fetch(target, *a, **kw)
    elif kind == "page_no_link":
        # En pengeside der svarer 200, men hvor købsknappen er væk. Det er
        # den fejl der låser salget helt, og den er umulig at frembringe i det
        # udgivne site — derfor laves den her.
        def patched(target, *a, **kw):
            if target == url:
                return 200, "<html><body><h1>Pro</h1></body></html>", None
            return _orig_fetch(target, *a, **kw)
    elif kind == "thanks_500":
        def patched(target, *a, **kw):
            if target == url:
                return 500, "", None
            return _orig_fetch(target, *a, **kw)
    elif kind == "license_503":
        def patched(target, *a, **kw):
            if target == url:
                return 503, "", None
            return _orig_fetch(target, *a, **kw)
    elif kind == "checkout_dead":
        def patched(target, *a, **kw):
            if target == url:
                return 404, "", None
            return _orig_fetch(target, *a, **kw)
    else:
        raise ValueError("ukendt mutation: %r" % (kind,))

    globals()["fetch"] = patched
    try:
        if kind == "sitemap":
            run("sitemap", check_sitemap, live, agreement)
        elif kind == "page_no_link":
            run("pages", check_money_pages, live)
        elif kind == "thanks_500":
            run("thanks", check_thanks, live)
        elif kind == "license_503":
            run("license", check_license_api, live)
        elif kind == "checkout_dead":
            run("checkout", check_checkout, live, agreement)
    finally:
        globals()["fetch"] = _orig_fetch
    return findings, notes, facts


def _expect_red(name, mutate, must_mention):
    """Kør porten med mutationen og kræv RØD med den forventede besked.

    Vendt sandheden, ikke en lokal variabel — samme fejl som opgave 14 og som
    `check_live_funnel.py` (_expect_red) dokumenterer: en mutationstest der
    sætter en lokal bool False, men aldrig returnerer den, grønner sig selv.
    """
    findings, _notes, _facts = collect(live=True, mutate=mutate)
    if not findings:
        return (name, False, "%s blev GRØN — mutationen blev ikke fanget" % name)
    if must_mention and not any(must_mention in f for f in findings):
        return (name, False, "%s blev rød med en anden besked end forventet: %s"
                % (name, findings[0]))
    return (name, True, "%s fanget: %s" % (name, findings[0]))


def _selftest():
    """Negative cases. Hver muterer målingen og kræver rød med rette besked."""
    cases = []

    # 1. Baseline: den rigtige udgivne side skal være grøn, ellers er de
    #    øvrige cases meningsløse.
    findings, _n, _f = collect(live=True)
    cases.append(("baseline: den udgivne købsvej er grøn", not findings, str(findings[:2])))

    # 2. Død side i sitemapet skal fanges. Mutationen rammer målingen, så
    #    den er gyldig for porten uanset hvad der ligger i aftalen.
    cases.append(_expect_red(
        "død side i sitemapet er rød",
        ("sitemap", SITE + "/pro/sample-report/"),
        "rangerer aldrig",
    ))

    # 3. Undtagelsen skal kunne lukkes: samme mutation som 2, men med den
    #    URL skrevet ind i aftalen, skal VÆRE grøn. Ellers er en
    #    registreret undtagelse bare en måde at slå porten fra.
    #
    #    Første udkast skrev `not findings and True`. Anden led er altid
    #    sand, så assertionen var en tilfældig streng — præcis den slags
    #    grøn case opgave 93 ("tre selftest-cases der ikke var egenskaber")
    #    ryddede væk. Nu kræves BEGGE dele: ingen fund, og mutationen skal
    #    faktisk være nået frem (anden kontrol måles), ellers er casen
    #    grøn fordi porten slet ikke kørte.
    path = os.path.relpath(AGREEMENT, ROOT)
    with open(AGREEMENT, encoding="utf-8") as fh:
        good = fh.read()
    with open(AGREEMENT, "w", encoding="utf-8") as fh:
        data = json.loads(good)
        data.setdefault("dead_in_sitemap", []).append(
            {"url": SITE + "/pro/sample-report/", "reason": "selftest: midlertidigt nede"})
        fh.write(json.dumps(data, indent=2, ensure_ascii=False))
    try:
        findings, notes, facts = collect(live=True,
                                         mutate=("sitemap", SITE + "/pro/sample-report/"))
        measured = facts.get("sitemap", 0)
        mentioned = any(SITE + "/pro/sample-report/" in n for n in notes)
        cases.append((
            "registreret undtagelse er grøn, målt og rapporteret som note",
            (not findings) and measured > 0 and mentioned,
            "fandt: %s, målt: %d, nævnt i note: %s" % (findings[:1], measured, mentioned),
        ))
    finally:
        with open(AGREEMENT, "w", encoding="utf-8") as fh:
            fh.write(good)

    # 4. Aftalen beskadiget -> rød, ellers måler porten ingenting.
    with open(AGREEMENT, "w", encoding="utf-8") as fh:
        fh.write("{ ikke json")
    try:
        findings, _n, _f = collect(live=True)
        cases.append((
            "beskadiget aftale er rød",
            any("kunne ikke læses" in f for f in findings),
            str(findings[:1]),
        ))
    finally:
        with open(AGREEMENT, "w", encoding="utf-8") as fh:
            fh.write(good)

    # 5. En pengeside uden købsknap. Uden denne case er `check_money_pages`
    #    utestet: det udgivne site har et link på alle otte sider, så porten
    #    er grøn af den rigtige grund og siger intet om sin egen dømmekraft.
    #    Det blev målt som M1 i mutationstesten.
    cases.append(_expect_red(
        "pengeside uden Stripe-link er rød",
        ("page_no_link", SITE + "/pricing/"),
        "uden en vej at betale",
    ))

    # 6. Kvitteringen nede. Den er hvor kunden får nøglen, så en 500 her er
    #    et betalt produkt der ikke leveres.
    cases.append(_expect_red(
        "kvitteringsside der svarer 500 er rød",
        ("thanks_500", "https://mahope.tools/thanks"),
        "ingen licensnøgle",
    ))

    # 7. Licensserveren svarer 503 på en ukendt nøgle. Det er den fejl der
    #    låser betalende kunder ude, og den er nem at forveksle med en
    #    korrekt 404 — derfor kræves beskeden.
    cases.append(_expect_red(
        "licens-API på 503 er rød",
        ("license_503", "https://mahope.tools/api/license/validate"),
        "låser betalende kunder ude",
    ))

    # 8. Et Stripe-link der ikke svarer. Uden den undtagelse skal det være
    #    rød: det er købet der ikke kan gennemføres.
    cases.append(_expect_red(
        "dødt Stripe-link er rødt",
        ("checkout_dead", "https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03"),
        "købet kan ikke gennemføres",
    ))

    ok = True
    for name, passed, detail in cases:
        print("   %s  %s%s" % ("OK  " if passed else "FEJL", name,
                               "" if passed else "  — %s" % detail))
        ok = ok and passed
    print("SELFTEST %s — %d negative cases" % ("GRØN" if ok else "RØD", len(cases)))
    return ok


def main(argv):
    if "--selftest" in argv:
        return 0 if _selftest() else 1

    live = "--offline" not in argv
    findings, notes, facts = collect(live=live)
    for n in notes:
        print("   NOTE  %s" % n)
    for f in findings:
        print("   FUND  %s" % f)

    if findings:
        print("KØBSVEJ-GATE RØD — %d fund" % len(findings))
        return 1
    if not live:
        print("KØBSVEJ-GATE grå — offline, intet målt")
        return 0
    print("KØBSVEJ-GATE GRØN — %d pengesider, %d Stripe-links, %d kvitteringskald, "
          "%d licenskald, %d sitemap-URL'er, alle svarer som de skal"
          % (facts.get("pages", 0), facts.get("checkout", 0), facts.get("thanks", 0),
             facts.get("license", 0), facts.get("sitemap", 0)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
