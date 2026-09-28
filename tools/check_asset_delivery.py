#!/usr/bin/env python3
"""Gat: en kunde skal kunne hente den version, der er rettet.

Baggrund
--------
Denne gate blev skrevet efter en måling den 27/9 23:46, som fandt at
**1.3.35 stadig blev serveret som en 200** — med det gamle indhold — lige
timer efter at 1.3.36 havde rettet den fejl, 1.3.35 havde:

    /assets/eucomply-1.3.35.zip -> 200 application/zip  62622 B
    age: 3946   cf-cache-status: HIT

Kilden er ikke en fejl i træet.Med cache-buster svarer samme adresse `301` ->
1.3.36, og 1.3.35 findes ikke i repoet. Det er **kant-cachen**: `site/_headers`
giver `/assets/*` `Cache-Control: public, max-age=31536000, immutable`, så en
fil der fjernes fra træet kan serveres i op til **et år** på den adresse den
havde.

Det er ikke en teoretisk fare. Den fejl 1.3.36 rettede var den dyreste i
rapporten: en side der kører OneTrust blev fortalt at den kørte fire
samtykkeplatforme. En kunde der har bogmærket sit downloadlink — og en kunde
der fik det tilsendt fra et gammel blogindlæg eller et gammelt skærmbillede —
fik den rapport, og betalte $79 for den, i op til et år efter rettelsen.

To ting skal være sande, så det ikke kan ske igen:

1. **`immutable` må kun dække filer med en version i navnet.** Et filnavn uden
   version (`site.css`, `eucomply-badge.js`) kan rediges på plads, og så
   når rettelsen ingen kunde. `eucomply-badge.js` er indlejret i kunders egne
   sider lige nu, og opgave 6's næste skridt er at omskrive den — den ville have
   nået nul kunder.
2. **Redirect-kæden skal være automatisk, ikke husket.** Den er blevet
   håndskrevet otte gange, én gang per udgivelse, og den er fuldstændig i dag
   (1.2.0 → 1.3.36, målt). Den er fuldstændig *fordi en agent måtte den efter
   hver release* — intet ville have sagt det, hvis den var droppet. Denne gate
   læser de faktiske filer, så kæden er en egenskab ved træet og ikke en
   hensigt.

Kontrol 1 og 2 er deterministiske og kræver ingen netværksadgang.

Kørsel
------
    python3 tools/check_asset_delivery.py             # gaten
    python3 tools/check_asset_delivery.py --selftest   # negative cases
"""

import json
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HEADERS = os.path.join("site", "_headers")
REDIRECTS = os.path.join("site", "_redirects")
ASSETS = os.path.join("site", "assets")
UPDATE_JSON = ("update.json", os.path.join("site", "update.json"))
PLUGIN_PAGE = os.path.join("site", "plugin", "index.html")

VERSION_RE = re.compile(r"\d+\.\d+\.\d+")
CHANGELOG_RE = re.compile(r"=\s*(\d+\.\d+\.\d+)\s*\(")
CHANGELOG_SPLIT_RE = re.compile(r"^=\s*(\d+\.\d+\.\d+)\s*\([^)]*\)\s*=\s*$", re.M)
ZIP_RE = re.compile(r"^(/assets/eucomply-[\d.]+\.zip)\s+(\S+)(?:\s+(\d+))?\s*$")

PLUGIN_README = os.path.join("plugin", "readme.txt")


def changelog_entries(text):
    """{version: body} for en changelog. Kun kroppen, aldrig datoen.

    Datoen er den eneste del de to filer med rimelighed kan have forskellig:
    manifestet skrives samme dag som udgivelsen, og readme.txt kan have været
    skrevet dagen før. Alt andet skal være ens, og det er kroppen kunden læser.
    """
    out = {}
    parts = CHANGELOG_SPLIT_RE.split(text)
    for i in range(1, len(parts), 2):
        out.setdefault(parts[i], parts[i + 1].strip())
    return out


def readme_changelog(root=ROOT):
    path = os.path.join(root, PLUGIN_README)
    if not os.path.isfile(path):
        return None
    text = read(path)
    marker = text.find("== Changelog ==")
    if marker < 0:
        return None
    body = text[marker:].lstrip("=\n ")
    nxt = re.search(r"^== (?!Changelog)", body, re.M)
    if nxt:
        body = body[:nxt.start()]
    return changelog_entries(body)


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def parse_headers(text):
    """->_headers som [(pattern, {header: value})] i filens rækkefølge.

    Cloudflare Pages: en sti uden indrykning indtil næste sti, og indrykede
    `Header: værdi`-linjer under den.
    """
    rules = []
    pattern = None
    headers = {}
    for raw in text.splitlines():
        if not raw.strip():
            continue
        if not raw.startswith((" ", "\t")):
            if pattern is not None:
                rules.append((pattern, headers))
            pattern = raw.strip()
            headers = {}
        else:
            line = raw.strip()
            if ":" in line:
                key, _, value = line.partition(":")
                headers[key.strip().lower()] = value.strip()
    if pattern is not None:
        rules.append((pattern, headers))
    return rules


def pages_match(pattern, path):
    """Match Cloudflare Pages' egen mønsterdannelse.

    `*` dækker alt (også `/`), og der er ingen glob-escapes i Pages. Vi bruger
    derfor en ren regex-oversættelse i stedet for fnmatch, fordi fnmatch's
    `[0-9]` ville fortolke `[` i et mønster som et tegnssæt.
    """
    out = ["^"]
    for ch in pattern:
        out.append(".*" if ch == "*" else re.escape(ch))
    out.append("$")
    return re.match("".join(out), path) is not None


def collect(root=ROOT):
    findings = []
    facts = {}

    # ---- 1 + 2: immutable- og filkontrol over site/_headers -----------
    rules = parse_headers(read(os.path.join(root, HEADERS)))
    assets = []
    assets_dir = os.path.join(root, ASSETS)
    if os.path.isdir(assets_dir):
        for name in sorted(os.listdir(assets_dir)):
            full = os.path.join(assets_dir, name)
            if os.path.isfile(full):
                # Stien er relativ til site/ — det er dem `_headers`-mønstrene ser.
                assets.append("/%s/%s" % (os.path.basename(ASSETS), name))
    facts["assets"] = assets

    immutable = [(p, h) for p, h in rules
                 if "immutable" in h.get("cache-control", "").lower()]
    facts["immutable_patterns"] = [p for p, _ in immutable]

    for pattern, _ in immutable:
        matched = [a for a in assets if pages_match(pattern, a)]
        if not matched:
            findings.append(
                "%s: reglen `%s` siger immutable, men matcher ingen fil i %s/ — "
                "død konfiguration" % (HEADERS, pattern, ASSETS))
        for path in matched:
            if not VERSION_RE.search(os.path.basename(path)):
                findings.append(
                    "%s: `%s` giver immutable til %s, men filen har ingen version "
                    "i navnet. En redaktion af den fil er usynlig for alle kunder i "
                    "op til et år (max-age=31536000). Sæt versionen i filnavnet, "
                    "eller fjern immutable." % (HEADERS, pattern, path))

    # ---- 3: højst den nuværende plugin-zip i træet ---------------------
    update = None
    versions = set()
    current = None
    for rel in UPDATE_JSON:
        p = os.path.join(root, rel)
        if not os.path.isfile(p):
            findings.append("%s findes ikke" % rel)
            continue
        try:
            data = json.loads(read(p))
        except ValueError as exc:
            findings.append("%s er ikke gyldig JSON: %s" % (rel, exc))
            continue
        if update is not None and data != update:
            findings.append(
                "%s og %s er ikke ens. WordPress læser den i rodtræet, "
                "linket på sitet læser den anden, og de to skal være det samme."
                % UPDATE_JSON)
        update = data
        if isinstance(data.get("version"), str):
            versions.add(data["version"])
        for section in data.get("sections", {}) or {}:
            if isinstance(section, str):
                versions.update(CHANGELOG_RE.findall(section))
        if isinstance(data.get("changelog"), str):
            versions.update(CHANGELOG_RE.findall(data["changelog"]))
    facts["versions"] = sorted(versions)

    if not isinstance(update, dict):
        return findings, facts
    current = update.get("version")
    facts["current"] = current
    if not isinstance(current, str) or not VERSION_RE.fullmatch(current):
        findings.append("%s: `version` er %r, ikke en x.y.z" % (UPDATE_JSON[0], current))
        return findings, facts

    zips = [a for a in assets if re.search(r"^/assets/eucomply-[\d.]+\.zip$", a)]
    for path in zips:
        if not path.endswith("-%s.zip" % current):
            findings.append(
                "%s: %s ligger i træet, men den aktuelle version er %s. En gammel "
                "zip i træet er en download, der ikke kan forsvinde — den er "
                "serveret med immutable i et år. Kun den aktuelle version hører "
                "hjemme her; de gamle skal til /assets/ som 301."
                % (ASSETS, os.path.basename(path), current))
    if len(zips) != 1:
        findings.append(
            "%s: forventede præcis én plugin-zip (%s), fandt %d: %s"
            % (ASSETS, "eucomply-%s.zip" % current, len(zips),
               ", ".join(os.path.basename(z) for z in zips) or "ingen"))

    # ---- 4: redirect-kæden ---------------------------------------------
    target = "/assets/eucomply-%s.zip" % current
    seen = {}
    for lineno, line in enumerate(read(os.path.join(root, REDIRECTS)).splitlines(), 1):
        m = ZIP_RE.search(line.strip())
        if not m:
            continue
        source, dest, code = m.group(1), m.group(2), m.group(3)
        if not code:
            findings.append(
                "%s: %d: `%s` er en 301 uden mål. Den gør intet, og hvis den nogensinde "
                "bør begynde at gøre det, bliver hvert download en sløjfe. En regel "
                "skal pege på %s." % (REDIRECTS, lineno, source, target))
            continue
        if code != "301":
            findings.append(
                "%s: %d: `%s` bruger HTTP %s. En gammel version skal være en 301, så "
                "browseren og søgemaskinen ved at den flytted sig." % (REDIRECTS, lineno, source, code))
        if dest != target:
            findings.append(
                "%s: %d: `%s` peger på %s og ikke på %s. Kæden skal slutte i den "
                "aktuelle version, ellers beder en kunde om den næste."
                % (REDIRECTS, lineno, source, dest, target))
        if source == target:
            findings.append(
                "%s: %d: reglen skygger den aktuelle version (%s). Den skal ikke have "
                "nogen regel — den ligger i træet." % (REDIRECTS, lineno, target))
        seen[source] = dest
    facts["redirects"] = len(seen)

    for version in sorted(versions, key=version_key):
        if version == current:
            continue
        if "/assets/eucomply-%s.zip" % version not in seen:
            findings.append(
                "%s: version %s står i changelog'en, men har ingen 301 til %s. En "
                "installation der beder om den version får en 404 i stedet for den "
                "rettede plugin." % (REDIRECTS, version, target))

    # ---- 5: det kunden faktisk bliver sendt til -------------------------
    url = update.get("download_url")
    if not isinstance(url, str) or not url:
        findings.append("%s: `download_url` mangler" % UPDATE_JSON[0])
    else:
        name = url.rsplit("/", 1)[-1]
        if name != os.path.basename(target):
            findings.append(
                "%s: `download_url` peger på %s, men den aktuelle version er %s "
                "(%s). WordPress henter denne adresse, når den opdaterer."
                % (UPDATE_JSON[0], name, current, os.path.basename(target)))
        if ("/%s/%s" % (os.path.basename(ASSETS), name)) not in assets:
            findings.append(
                "%s: `download_url` peger på /assets/%s, som ikke findes i træet. "
                "Opdateringen henter en fil, der ikke er der." % (UPDATE_JSON[0], name))

    page = os.path.join(root, PLUGIN_PAGE)
    if os.path.isfile(page):
        found = set(re.findall(r"eucomply-[\d.]+\.zip", read(page)))
        stale = sorted(v for v in found if v != os.path.basename(target))
        if stale:
            findings.append(
                "%s: download-linket peger på %s, men den aktuelle version er %s. "
                "Det er den adresse kunden klikker på."
                % (PLUGIN_PAGE, ", ".join(stale), os.path.basename(target)))
    else:
        findings.append("%s findes ikke" % PLUGIN_PAGE)

    # ---- 7: changelog'en skal have én kilde ----------------------------
    #
    # `readme.txt` er den changelog WordPress viser i pluginlisten,
    # `update.json` den der vises i opdateringsvinduet. De er begge håndskrevet,
    # og de har i 39 udgaver fortalt to forskellige historier. Målt: ni
    # versioner manglede helt i manifestet (1.3.21, 1.3.25–1.3.28, 1.3.30–1.3.32
    # og den aktuelle), og 1.3.22 holdt 1.3.21's rettelse i stedet for sin egen.
    # En kunde der læser manifestet tror da, at en rettelse kom i en udgave den
    # ikke kom i, og den udgave den faktisk kom i, står slet ikke.
    entries = {}
    for section in (update.get("sections") or {}).values():
        if isinstance(section, str):
            entries.update(changelog_entries(section))
    top = changelog_entries(update["changelog"]) if isinstance(update.get("changelog"), str) else {}
    if not entries:
        findings.append(
            "%s: ingen changelog at læse. Uden den får en kunde ingen "
            "beskrivelse af, hvad der ændrede sig." % UPDATE_JSON[0])
    else:
        facts["changelog_entries"] = len(entries)
        if current not in entries:
            findings.append(
                "%s: den aktuelle version %s står ikke i changelog'en. En kunde "
                "læser den tekst, der forteller hvad den udgave rettede, og den "
                "findes ikke." % (UPDATE_JSON[0], current))
        readme = readme_changelog(root)
        if readme is None:
            findings.append(
                "%s findes ikke eller har ingen `== Changelog ==`. Den er den "
                "anden halvdel af den samme besked, og uden den kan de to ikke "
                "måles mod hinanden." % PLUGIN_README)
        else:
            facts["readme_entries"] = len(readme)
            for version in sorted(readme, key=version_key):
                if version not in entries:
                    findings.append(
                        "%s: version %s står i %s, men ikke i changelog'en. "
                        "WordPress læser manifestet i opdateringsvinduet."
                        % (UPDATE_JSON[0], version, PLUGIN_README))
                elif entries[version] != readme[version]:
                    findings.append(
                        "%s: version %s har anden tekst i changelog'en end i %s. "
                        "De to fortæller kunden to forskellige ting om samme "
                        "udgave." % (UPDATE_JSON[0], version, PLUGIN_README))
            if top and top != entries:
                only_top = sorted(set(top) - set(entries), key=version_key)
                findings.append(
                    "%s: `changelog` og `sections.changelog` beskriver %d og %d "
                    "versioner, og de er ikke ens%s. WordPress læser den ene på gamle "
                    "installationer og den anden på nye, så samme opdatering får "
                    "to forskellige historier."
                    % (UPDATE_JSON[0], len(top), len(entries),
                       (": %s findes kun i `changelog`" % ", ".join(only_top[:4]))
                       if only_top else ""))

    return findings, facts


def version_key(v):
    try:
        return tuple(int(p) for p in v.split("."))
    except ValueError:
        return (0, 0, 0)


# ------------------------------------------------------------------ selftest

MINIMAL_HEADERS = """\
/*
  X-Frame-Options: DENY

/assets/*.zip
  Cache-Control: public, max-age=31536000, immutable
"""

MINIMAL_REDIRECTS = """\
/assets/eucomply-1.3.0.zip /assets/eucomply-1.3.1.zip 301
"""

MINIMAL_README = """\
=== EUComply ===
Requires at least: 5.0
Tested up to: 6.7
Stable tag: 1.3.1

== Changelog ==

%s"""


def make_tree(tmp, version="1.3.1", changelog=("1.3.1", "1.3.0")):
    """Byg et minimalt træ, der er grønt, så hver mutation kan prøves."""
    os.makedirs(os.path.join(tmp, "site", "assets"))
    os.makedirs(os.path.join(tmp, "site", "plugin"))
    os.makedirs(os.path.join(tmp, "plugin"))
    write = lambda p, t: open(os.path.join(tmp, p), "w", encoding="utf-8").write(t)
    write(HEADERS, MINIMAL_HEADERS)
    write(REDIRECTS, MINIMAL_REDIRECTS)
    write("%s/eucomply-%s.zip" % (ASSETS, version), "zip")
    write(PLUGIN_PAGE, '<a href="/assets/eucomply-%s.zip">Download</a>' % version)
    body = "".join("= %s (2026-09-27) =\n* x\n\n" % v for v in changelog)
    write(PLUGIN_README, MINIMAL_README % body)
    data = {
        "version": version,
        "download_url": "https://example.test/assets/eucomply-%s.zip" % version,
        "changelog": body,
        "sections": {"changelog": body},
    }
    text = json.dumps(data, indent=2)
    write(UPDATE_JSON[0], text)
    write(UPDATE_JSON[1], text)
    return tmp


def _expect_red(name, mutate, must_mention, extra):
    tmp = tempfile.mkdtemp(prefix="assetgate-")
    try:
        make_tree(tmp)
        mutate(tmp)
        findings, _ = collect(tmp)
        hit = next((f for f in findings if must_mention in f), None)
        if not findings:
            print("   SELFTEST %s:FEJL: mutationen gav ingen fund" % name)
            return False
        if hit is None:
            print("   SELFTEST %s:FEJL: intet fund nævner %r (fandt: %s)"
                  % (name, must_mention, findings[0][:90]))
            return False
        print("   ok  %s -> %s" % (name, hit[:96]))
        extra[0] += 1
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _drop_redirect(tmp):
    lines = [l for l in read(os.path.join(tmp, REDIRECTS)).splitlines()
             if "1.3.0" not in l]
    open(os.path.join(tmp, REDIRECTS), "w", encoding="utf-8").write("\n".join(lines))


def _selftest():
    print("SELFTEST check_asset_delivery — hver mutation skal gøre gaten rød")
    ok = True
    extra = [0]

    # 0: et korekt træ er grønt — ellers tester vi intet.
    tmp = tempfile.mkdtemp(prefix="assetgate-")
    try:
        make_tree(tmp)
        findings, _ = collect(tmp)
        if findings:
            print("   SELFTEST baseline:FEJL: et korekt træ gav fund: %s" % findings[0])
            ok = False
        else:
            print("   ok  baseline (grønt træ giver ingen fund)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    cases = [
        ("immutable på /assets/* med en fil uden version",
         lambda t: (open(os.path.join(t, ASSETS, "site.css"), "w").write("a{}"),
                    open(os.path.join(t, HEADERS), "w").write(
                        MINIMAL_HEADERS.replace("/assets/*.zip", "/assets/*"))),
         "men filen har ingen version i navnet"),
        ("immutable på css-mønster",
         lambda t: (open(os.path.join(t, ASSETS, "site.css"), "w").write("a{}"),
                    open(os.path.join(t, HEADERS), "w").write(
                        MINIMAL_HEADERS
                        + "\n/assets/*.css\n  Cache-Control: public, max-age=31536000, immutable\n")),
         "men filen har ingen version i navnet"),
        ("immutable på et mønster uden filer",
         lambda t: open(os.path.join(t, HEADERS), "w").write(
             MINIMAL_HEADERS + "\n/assets/*.woff2\n  Cache-Control: public, max-age=31536000, immutable\n"),
         "død konfiguration"),
        ("gammel zip lig i træet",
         lambda t: open(os.path.join(t, ASSETS, "eucomply-1.3.0.zip"), "w").write("z"),
         "ikke kan forsvinde"),
        ("changelog-version uden redirect",
         _drop_redirect,
         "ingen 301 til"),
        ("redirect uden mål",
         lambda t: open(os.path.join(t, REDIRECTS), "a").write(
             "/assets/eucomply-1.3.0.zip 301\n"),
         "301 uden mål"),
        ("redirect der peger på en gammel version",
         lambda t: open(os.path.join(t, REDIRECTS), "w").write(
             "/assets/eucomply-1.3.0.zip /assets/eucomply-1.3.0.zip 301\n"),
         "peger på"),
        ("download_url på en anden version",
         lambda t: _patch_update(t, {"download_url": "https://example.test/assets/eucomply-9.9.9.zip"}),
         "download_url"),
        ("download_url på en fil der ikke findes",
         lambda t: _patch_update(t, {"download_url": "https://example.test/assets/eucomply-1.3.2.zip"}),
         "ikke findes i træet"),
        ("pluginsiden linker en gammel version",
         lambda t: open(os.path.join(t, PLUGIN_PAGE), "w").write(
             '<a href="/assets/eucomply-1.3.0.zip">Download</a>'),
         "download-linket peger på"),
        ("de to update.json er ikke ens",
         lambda t: _patch_update(t, {"homepage": "https://example.test/gammel"},
                                 only_second=True),
         "ikke ens"),
        ("version der ikke er en x.y.z",
         lambda t: _patch_update(t, {"version": "seneste"}),
         "ikke en x.y.z"),
        ("den aktuelle version står ikke i changelog'en",
         lambda t: _set_changelog(t, "= 1.3.0 (2026-09-27) =\n* x\n\n"),
         "står ikke i changelog'en"),
        ("en version fra readme.txt mangler i changelog'en",
         lambda t: _set_changelog(t, "= 1.3.1 (2026-09-27) =\n* x\n\n"),
         "men ikke i changelog'en"),
        ("samme version med to forskellige tekster",
         lambda t: _set_changelog(t, "= 1.3.1 (2026-09-27) =\n* x\n\n"
                                     "= 1.3.0 (2026-09-27) =\n* en anden tekst\n\n"),
         "anden tekst i changelog'en"),
        ("`changelog` og `sections.changelog` er ikke ens",
         lambda t: _set_changelog(t, None, top="= 1.3.0 (2026-09-27) =\n* kun i top\n\n"),
         "to forskellige historier"),
        ("readme.txt mangler changelog-sektionen",
         lambda t: open(os.path.join(t, PLUGIN_README), "w").write(
             "=== EUComply ===\nStable tag: 1.3.1\n"),
         "har ingen `== Changelog ==`"),
    ]
    for name, mutate, mention in cases:
        if not _expect_red(name, mutate, mention, extra):
            ok = False

    if ok:
        print("SELFTEST GRØN — alle %d negative cases fanges" % (extra[0] + 1))
    else:
        print("SELFTEST RØD — se ovenfor")
    return ok


def _set_changelog(tmp, sections, top=None):
    """Skriv changelog'en i begge felter, medmindre casen vil se dem uoverens."""
    for rel in UPDATE_JSON:
        path = os.path.join(tmp, rel)
        data = json.loads(read(path))
        if top is not None:
            data["changelog"] = top
        if sections is not None:
            data["sections"]["changelog"] = sections
            if top is None:
                data["changelog"] = sections
        open(path, "w", encoding="utf-8").write(json.dumps(data, indent=2))


def _patch_update(tmp, patch, only_second=False):
    """Ret begge kopier af update.json, medmindre casen vil se en uoverens."""
    targets = [UPDATE_JSON[1]] if only_second else list(UPDATE_JSON)
    for rel in targets:
        path = os.path.join(tmp, rel)
        data = json.loads(read(path))
        data.update(patch)
        open(path, "w", encoding="utf-8").write(json.dumps(data, indent=2))


def main(argv):
    if "--selftest" in argv:
        return 0 if _selftest() else 1

    findings, facts = collect()
    for f in findings:
        print("   FUND  %s" % f)
    if findings:
        print("ASSET-GATE RØD — %d fund" % len(findings))
        return 1
    print("ASSET-GATE GRØN — %d filer i %s, immutable kun på versionerede navne, "
          "%d udgivne versioner i kæden til eucomply-%s.zip"
          % (len(facts["assets"]), ASSETS, max(len(facts["versions"]) - 1, 0),
             facts.get("current") or "?"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
