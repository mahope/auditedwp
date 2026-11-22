#!/usr/bin/env python3
"""Mål at der ikke længere findes en købsvej — mod LIVE.

## Hvad den målte før, og hvad den måler nu

Før 22/11-2026 var det den eneste gate der gik fra et link på den publicerede
side til det sted pengene endte. Den dømte at otte pengesider (`/pro/` og
`/pricing/` i fire sprog) svarede 200 med to Stripe-links, at hvert Stripe-link
svarede, at kvitteringen `mahope.tools/thanks` svarede, og at licens-API'et ikke
svarede 5xx på en ukendt nøgle. Fordi nul trafik ellers ligner en død port, var
det en LIVE-måling og ikke en dom over repoet.

Ejeren besluttede at fryse EUComply som gratis open source. Pro, skabelonerne og
e-bog-bundlet sælges ikke længere, og Stripe-linkene er deaktiveret. Gaten er
vendt, og den er stadig en LIVE-måling, fordi det er det en besøgende møder der
tæller, ikke det der ligger i træet:

  1. LUKKEDE STIER giver 301 til en side der findes og svarer 200: `/pricing/`,
     `/pro/`, `/store/`, `/vs/` og sprogversionerne, samt en underside pr.
     splat-regel. En 200 betyder at siden lever, en 404 at et gammelt link og
     en søgemaskine ingen vej har, og en 302 at lukningen ikke er permanent.
  2. FORSIDER OG NØGLESIDER (`/`, `/da/`, `/de/`, `/fr/`, `/scan/`, `/plugin/`)
     svarer 200, har ingen betalingslinks og ingen links til de lukkede stier,
     og de fire forsider har `id="frozen-notice"`.
  3. SITEMAPPET lister ingen lukket sti, og hver `<loc>` svarer 200. Det andet er
     den gamle kontrol, som består: en sitemap med 404'er sænker hele siden.
  4. LICENS-API'ET skal blive ved med at virke, for eksisterende licenser gælder
     stadig: en ukendt nøgle SKAL give 404. 5xx låser kunder med en gyldig
     licens ude.

Slettet fordi den handlede om at man kan BETALE: kravet om et Stripe-link pr.
pengeside, at hvert Stripe-link svarer, og at kvitteringen svarer. Der er intet at
betale, og et Stripe-link der svarer 200 på forsiden er nu en fejl, ikke en vare.

## Hvornår den må være rød, og hvorfor den ikke står i PR-gaten

Gaten måler det udgivne site. Før deployen er det udgivne site stadig det gamle,
og en PR kan ikke fikse det, så den live-del ville gøre hver PR rød alene fordi
dens egen ændring ikke er rullet ud. Derfor kører `quality_gate.sh` kun
`--selftest` (fixture-baseret, ingen netværk), og live-delen kører i
`deploy-site.yml` EFTER at Pages serverer den nye udgivelse. Den må aldrig køre
på en PR mod det gamle site.

Undtagelser i `tools/buy_path.json` (`dead_in_sitemap`) skal have en begrundelse
der kan lukkes, samme stilling som `funnel_drift.json`.

Kør:
    python3 tools/check_buy_path.py            # live, mod eucomplypro.com
    python3 tools/check_buy_path.py --selftest # fixtures, intet netværk
    python3 tools/check_buy_path.py --offline  # spring live-kaldene over
"""

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import no_sales  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGREEMENT = os.path.join(ROOT, "tools", "buy_path.json")
SITE = "https://eucomplypro.com"
LICENSE_API = "https://mahope.tools/api/license/validate"
TIMEOUT = 20

# Browser-UA: nogle kanter svarer anderledes en rigtig besøgende end en
# script-agent, og en gate der måler en anden side er ikke en gate.
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

LOC_RE = re.compile(r"<loc>([^<]+)</loc>")

# Stier der skal være lukkede, og et par undersider som splat-reglerne dækker.
CLOSED_PATHS = no_sales.REMOVED_TOP + ("/pro/dashboard/", "/store/dpa/", "/vs/termly/")
KEY_PAGES = ("/", "/da/", "/de/", "/fr/", "/scan/", "/plugin/")
HOME_PAGES = ("/", "/da/", "/de/", "/fr/")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # noqa: D401 - 3xx skal ses, ikke følges
        return None


class Net:
    """Netværket. Selvtesten erstatter den med `FakeNet`, så intet rammer et rigtigt site."""

    def get(self, url, method="GET", data=None):
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
        except Exception as exc:  # noqa: BLE001
            return None, "", str(exc)

    def probe(self, url):
        """Returnér (status, Location, fejl) UDEN at følge en redirect."""
        opener = urllib.request.build_opener(_NoRedirect)
        request = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with opener.open(request, timeout=TIMEOUT) as response:
                return response.status, response.headers.get("Location"), None
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers.get("Location"), None
        except Exception as exc:  # noqa: BLE001
            return None, None, str(exc)


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


def check_closed_paths(net, live):
    """Hver lukket sti skal give en 301 til en side der findes og svarer 200."""
    findings, notes, measured = [], [], 0
    if not live:
        return findings, notes, measured
    for rel in CLOSED_PATHS:
        status, location, err = net.probe(SITE + rel)
        if err:
            notes.append("%s kunne ikke hentes: %s" % (rel, err))
            continue
        measured += 1
        if status == 200:
            findings.append("%s svarer 200 — salgssiden lever stadig" % rel)
        elif status != 301:
            findings.append("%s svarer %s, ikke 301 — et gammelt link eller en søgemaskine får ikke "
                            "den permanente vej videre" % (rel, status))
        elif not location:
            findings.append("%s giver 301 uden Location" % rel)
        else:
            target = urllib.parse.urljoin(SITE + rel, location)
            path = urllib.parse.urlparse(target).path
            if no_sales.removed_links(path):
                findings.append("%s peger på %s, en anden lukket side" % (rel, target))
                continue
            code, _body, terr = net.get(target)
            if terr:
                notes.append("%s -> %s kunne ikke hentes: %s" % (rel, target, terr))
            elif code != 200:
                findings.append("%s peger på %s, som svarer %s" % (rel, target, code))
    return findings, notes, measured


def check_key_pages(net, live):
    """Nøglesiderne svarer 200 uden købsspor, og forsiderne siger at EUComply er frosset."""
    findings, notes, measured = [], [], 0
    if not live:
        return findings, notes, measured
    for rel in KEY_PAGES:
        status, body, err = net.get(SITE + rel)
        if err:
            notes.append("%s kunne ikke hentes: %s" % (rel, err))
            continue
        measured += 1
        if status != 200:
            findings.append("%s svarer %s" % (rel, status))
            continue
        for link in no_sales.checkout_links(body):
            findings.append("%s har stadig et betalingslink: %s" % (rel, link))
        for link in sorted(set(no_sales.removed_links(body))):
            findings.append("%s linker stadig til den lukkede side %s" % (rel, link))
        if rel in HOME_PAGES:
            notice = no_sales.parse_blocks(body).ids.get("frozen-notice")
            if notice is None:
                findings.append('%s mangler id="frozen-notice" — forsiden siger ikke at EUComply er frosset' % rel)
            elif rel == "/" and no_sales.FROZEN_PHRASE not in " ".join(notice.split()).lower():
                findings.append('%s: frozen-notice siger ikke "%s"' % (rel, no_sales.FROZEN_PHRASE))
    return findings, notes, measured


def check_license_api(net, live):
    """En ukendt nøgle SKAL give 404. 5xx låser kunder med en gyldig licens ude."""
    findings, notes, measured = [], [], 0
    if not live:
        return findings, notes, measured
    status, body, err = net.get(
        LICENSE_API, method="POST",
        data={"license_key": "0" * 32, "device_id": "check-buy-path", "product": "eucomply-pro"},
    )
    if err:
        notes.append("licens-API kunne ikke kaldes: %s" % err)
        return findings, notes, measured
    measured += 1
    if status in (500, 502, 503, 504):
        findings.append("licens-API svarer %s på en ukendt nøgle — en nede server låser kunder med "
                        "en gyldig licens ude (503 skal klienten klare blødt)" % status)
    elif status != 404:
        findings.append("licens-API svarer %s på en ukendt nøgle; 404 er det forventede "
                        "og sikre svar, så svaret skal forstås: %s" % (status, body[:120]))
    return findings, notes, measured


def check_sitemap(net, live, agreement):
    """Ingen lukket sti i sitemapet, og hver <loc> svarer 200."""
    findings, notes, measured = [], [], 0
    if not live:
        return findings, notes, measured
    status, body, err = net.get(SITE + "/sitemap.xml")
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
        if no_sales.removed_links(loc):
            findings.append("%s står i sitemapet, men siden er lukket — fjern den fra kortet" % loc)
            continue
        code, _b, err = net.get(loc)
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


def collect(net=None, live=True):
    """Alle kontroller. Returnér (fund, noter, målte antal)."""
    net = net or Net()
    agreement, err = _read_agreement()
    facts = {"closed": 0, "pages": 0, "license": 0, "sitemap": 0}
    if err:
        return [err], [], facts
    if not agreement.get("version"):
        return ["%s mangler 'version' — aftalen skal kunne lukkes"
                % os.path.relpath(AGREEMENT, ROOT)], [], facts

    findings, notes = [], []
    for key, check, args in (
        ("closed", check_closed_paths, ()),
        ("pages", check_key_pages, ()),
        ("license", check_license_api, ()),
        ("sitemap", check_sitemap, (agreement,)),
    ):
        f, n, m = check(net, live, *args)
        findings.extend(f)
        notes.extend(n)
        facts[key] = m
    return findings, notes, facts


# ---------------------------------------------------------------------------
# Selvtest: et falsk, helt lukket site er grønt, og hver afvigelse gør det rødt.
# ---------------------------------------------------------------------------
NOTICE_EN = ('<div id="frozen-notice">EUComply is frozen as free open source as of 22 November 2026. '
             "The free scanner stays; Pro is no longer sold; existing licences keep working.</div>")
NOTICE_LOCAL = '<div id="frozen-notice">EUComply er frosset som gratis open source pr. 22. november 2026.</div>'


class FakeNet:
    """Et lukket site som fixtures: (status, krop/Location). Intet rammer netværket."""

    def __init__(self):
        self.pages = {SITE + "/": (200, "<main>%s</main>" % NOTICE_EN)}
        for rel in ("/da/", "/de/", "/fr/"):
            self.pages[SITE + rel] = (200, "<main>%s</main>" % NOTICE_LOCAL)
        for rel in ("/scan/", "/plugin/"):
            self.pages[SITE + rel] = (200, "<main><p>Free scan.</p></main>")
        self.redirects = {SITE + rel: (301, "/scan/") for rel in CLOSED_PATHS}
        locs = "".join("<url><loc>%s%s</loc></url>" % (SITE, rel) for rel in ("/", "/scan/", "/plugin/"))
        self.pages[SITE + "/sitemap.xml"] = (200, "<urlset>%s</urlset>" % locs)
        self.license = (404, '{"valid":false}')

    def get(self, url, method="GET", data=None):
        if url == LICENSE_API:
            return self.license[0], self.license[1], None
        if url in self.pages:
            return self.pages[url][0], self.pages[url][1], None
        if url in self.redirects:
            return self.redirects[url][0], "", None
        return 404, "", None

    def probe(self, url):
        if url in self.redirects:
            return self.redirects[url][0], self.redirects[url][1], None
        if url in self.pages:
            return self.pages[url][0], None, None
        return 404, None, None


def _expect(name, mutate, must_mention):
    """Kør porten mod et mutéret falsk site og kræv RØD med den forventede besked."""
    net = FakeNet()
    mutate(net)
    findings, _notes, _facts = collect(net)
    if not findings:
        return (name, False, "%s blev GRØN — mutationen blev ikke fanget" % name)
    if must_mention and not any(must_mention in f for f in findings):
        return (name, False, "%s blev rød med en anden besked end forventet: %s" % (name, findings[0]))
    return (name, True, "%s fanget: %s" % (name, findings[0]))


def _selftest():
    cases = []

    net = FakeNet()
    findings, _n, facts = collect(net)
    cases.append(("baseline: det lukkede site er grønt og målt",
                  not findings and facts["closed"] == len(CLOSED_PATHS) and facts["sitemap"] == 3,
                  "fund %s, målt %s" % (findings[:2], facts)))

    def live_page(net):
        net.redirects.pop(SITE + "/pricing/")
        net.pages[SITE + "/pricing/"] = (200, "<main>Pricing</main>")

    def moved_temporarily(net):
        net.redirects[SITE + "/da/pro/"] = (302, "/da/")

    def gone(net):
        net.redirects.pop(SITE + "/store/")

    def dead_target(net):
        net.redirects[SITE + "/vs/"] = (301, "/findes-ikke/")

    def to_closed(net):
        net.redirects[SITE + "/store/"] = (301, "/pricing/")

    def buy_link(net):
        net.pages[SITE + "/"] = (200, "<main>%s<a href=\"https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03\">Buy</a></main>" % NOTICE_EN)

    def pricing_link(net):
        net.pages[SITE + "/scan/"] = (200, '<main><a href="/pricing/">Pricing</a></main>')

    def no_notice(net):
        net.pages[SITE + "/de/"] = (200, "<main>EUComply</main>")

    def no_phrase(net):
        net.pages[SITE + "/"] = (200, '<main><div id="frozen-notice">Welcome to our compliance scanner today.</div></main>')

    def page_down(net):
        net.pages[SITE + "/plugin/"] = (500, "")

    def sitemap_lists_closed(net):
        net.pages[SITE + "/sitemap.xml"] = (200, "<urlset><url><loc>%s/pro/</loc></url></urlset>" % SITE)

    def sitemap_dead(net):
        net.pages[SITE + "/sitemap.xml"] = (200, "<urlset><url><loc>%s/borte/</loc></url></urlset>" % SITE)

    def license_503(net):
        net.license = (503, "")

    def license_200(net):
        net.license = (200, '{"valid":true}')

    for name, mutate, needle in (
        ("en lukket side der lever er rød", live_page, "lever stadig"),
        ("302 i stedet for 301 er rød", moved_temporarily, "ikke 301"),
        ("en lukket sti uden redirect er rød", gone, "ikke 301"),
        ("redirect til en side der ikke findes er rød", dead_target, "som svarer 404"),
        ("redirect til en anden lukket side er rød", to_closed, "anden lukket side"),
        ("betalingslink på forsiden er rødt", buy_link, "betalingslink"),
        ("link til /pricing/ er rødt", pricing_link, "lukkede side"),
        ("forside uden frozen-notice er rød", no_notice, "frozen-notice"),
        ("engelsk frozen-notice uden frasen er rød", no_phrase, "frozen as free open source"),
        ("nøgleside der er nede er rød", page_down, "svarer 500"),
        ("lukket side i sitemapet er rød", sitemap_lists_closed, "siden er lukket"),
        ("død side i sitemapet er rød", sitemap_dead, "rangerer aldrig"),
        ("licens-API på 503 er rød", license_503, "gyldig licens"),
        ("licens-API der svarer 200 på en ukendt nøgle er rød", license_200, "404 er det forventede"),
    ):
        cases.append(_expect(name, mutate, needle))

    # Undtagelsen skal kunne lukkes: den samme døde sitemap-side er grøn og
    # rapporteret som note, når aftalen registrerer den med en begrundelse.
    with open(AGREEMENT, encoding="utf-8") as fh:
        good = fh.read()
    data = json.loads(good)
    data.setdefault("dead_in_sitemap", []).append({"url": SITE + "/borte/", "reason": "selftest: midlertidigt nede"})
    with open(AGREEMENT, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(data, indent=2, ensure_ascii=False))
    try:
        net = FakeNet()
        sitemap_dead(net)
        findings, notes, facts = collect(net)
        mentioned = any(SITE + "/borte/" in n for n in notes)
        cases.append(("registreret undtagelse er grøn, målt og rapporteret som note",
                      not findings and facts["sitemap"] > 0 and mentioned,
                      "fund %s, målt %s, note %s" % (findings[:1], facts["sitemap"], mentioned)))
    finally:
        with open(AGREEMENT, "w", encoding="utf-8") as fh:
            fh.write(good)

    # Aftalen beskadiget -> rød, ellers måler porten ingenting.
    with open(AGREEMENT, "w", encoding="utf-8") as fh:
        fh.write("{ ikke json")
    try:
        findings, _n, _f = collect(FakeNet())
        cases.append(("beskadiget aftale er rød", any("kunne ikke læses" in f for f in findings), str(findings[:1])))
    finally:
        with open(AGREEMENT, "w", encoding="utf-8") as fh:
            fh.write(good)

    ok = True
    for name, passed, detail in cases:
        print("   %s  %s%s" % ("OK  " if passed else "FEJL", name, "" if passed else "  — %s" % detail))
        ok = ok and passed
    print("SELFTEST %s — %d cases (lukket site grønt, hver afvigelse rød)" % ("GRØN" if ok else "RØD", len(cases)))
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
        print("KØBSVEJ-GATE RØD — %d fund: sitet har stadig et købsspor, eller noget der skal virke er nede" % len(findings))
        return 1
    if not live:
        print("KØBSVEJ-GATE grå — offline, intet målt")
        return 0
    print("KØBSVEJ-GATE GRØN — %d lukkede stier 301'er, %d nøglesider uden købsspor, %d licenskald, "
          "%d sitemap-URL'er, alle svarer som de skal"
          % (facts.get("closed", 0), facts.get("pages", 0), facts.get("license", 0), facts.get("sitemap", 0)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
