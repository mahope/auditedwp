#!/usr/bin/env python3
"""Gate: ingen død betalingsudbyder i den kode, der kan nå en kunde.

Baggrund
--------
Lemon Squeezy lukkede, og kontrakten siger det aldrig må genoplives. Gumroad
blev droppet samtidig. Alligevel lå der to fejl af den slags i dette repo, og
 ingen af dem var synlig for porten:

1. `deskuptime/src/license.js` kalder `api.lemonsqueezy.com/v1/licenses/*`.
   Den rigtige app ligger i repoet `deskuptime`, hvor samme fil kalder
   `mahope.tools/api/license/*`. To kopier af samme produkts licensklient,
   der er uenige om udbyderen — og den i dette repo er den forkerede.
2. `devnotify/src-tauri/src/lib.rs` gør det samme.

Portene så dem ikke, fordi `check_pro_claims.py` kun læser det publicerede
træ. Det er den fejltype, planen nu har dokumenteret seks gange: en kontrol
der læser en mængde, der er mindre end den, den skal dække.

Sådan afgør porten
------------------
Et fund er **levende kode** hvis linjen indeholder en URL eller et API-sti til
den døde udbyder (`https://api.lemonsqueezy.com/...`, `/v1/licenses/`). Det er
kode, der *ville* ringe, hvis nogen byggede den.

Et fund er **prose**, når linjen blot nævner udbyderen — en changelog der
siger "License API (former Lemon Squeezy)". Det er ærlig historie, og den skal
stå, fordi en kunde der læser den skal kunne se at vi flyttede.

Prose er altså ikke tilstrækkeligt i sig selv: den skal være på en sti, der
ikke kan publiceres, eller være tilladt i `dead_provider_allowlist.json` med
en skrevet begrundelse. Hver linje i allowlisten skal have en `reason` — en
post uden en er et fund, fordi en tilladelse uden begrundelse ikke kan
gennemgås.

Alt i allowlisten rapporteres hver kørsel, opdelt i levende kode og prose, så
registret viser hvor meget død udbyder-kode der faktisk stadig står i repoet.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWLIST = ROOT / "tools" / "dead_provider_allowlist.json"

# Døde udbydere. Lemon Squeezy blev afvist 24/9, Gumroad blev droppet 23/8.
DEAD_PROVIDERS = ("lemonsqueezy", "lemon squeezy", "gumroad")

SKIP_DIRS = {".git", "node_modules", "__pycache__", "site-dist", ".deploy-staging",
             "dist", ".venv", "venv"}
SKIP_SUFFIXES = {".zip", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
                 ".woff", ".woff2", ".ttf", ".pdf", ".mp4", ".tar", ".gz", ".sqlite"}

# En levende reference: en URL med værten, eller et af Lemon Squeezys API-stier.
LIVE_URL = re.compile(
    r"https?://[^\s'\"<>]*?(?:lemonsqueezy|gumroad)[^\s'\"<>]*|/v1/licenses/", re.I)
# Værten nævnt uden scheme, fx et config-felt der kun siger "lemonsqueezy.com".
LIVE_HOST = re.compile(r"\b[a-z0-9.-]*(?:lemonsqueezy|gumroad)\.(?:com|app|io)\b", re.I)

SCANNED_EXT = {".py", ".js", ".mjs", ".cjs", ".ts", ".json", ".php", ".html", ".css",
               ".md", ".txt", ".rs", ".sh", ".yml", ".yaml", ".toml", ""}

# Extensions der *kan* bygges eller publiceres. En død udbyder i en af disse
# skal altid have en begrundet tilladelse, uanset om filen ligger i site/.
# Alt andet (.md, .txt, .sh, .yml, .toml) er dokumentation, medmindre det
# publiceres — og publiceret dokumentation skal stadig have en begrundelse,
# fordi en kunde kan læse den.
SHIPPABLE = {".py", ".js", ".mjs", ".cjs", ".ts", ".json", ".php", ".html", ".css", ".rs"}


def iter_files():
    """Alle læsbare tekstfiler i repoet, uden .git, node_modules og byggetræer."""
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        if path.suffix.lower() not in SCANNED_EXT:
            continue
        yield rel


def is_live(line: str) -> bool:
    return bool(LIVE_URL.search(line) or LIVE_HOST.search(line))


def scan():
    """Find alle linjer der nævner en død udbyder. -> (hits, unreadable)"""
    hits, unreadable = [], []
    for rel in iter_files():
        try:
            text = (ROOT / rel).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            unreadable.append(str(rel))
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            if any(provider in lowered for provider in DEAD_PROVIDERS):
                hits.append((str(rel), number, line.strip(), is_live(line)))
    return hits, unreadable


def load_allowlist():
    """(fejl, prefixer) — en post uden begrundelse er selv et fund."""
    errors, prefixes = [], []
    if not ALLOWLIST.exists():
        return [f"allowlisten mangler: {ALLOWLIST.relative_to(ROOT)}"], prefixes
    data = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    for entry in data.get("entries", []):
        path = entry.get("path", "")
        if not entry.get("reason", "").strip():
            errors.append(f"allowlist uden begrundelse: {path or '(tom sti)'}")
            continue
        if not path:
            errors.append("allowlist uden sti")
            continue
        prefixes.append(path.rstrip("/") + "/")
    return errors, prefixes


def is_allowed(rel: str, prefixes) -> bool:
    for prefix in prefixes:
        if rel == prefix.rstrip("/") or rel.startswith(prefix):
            return True
    return False


def _internal_rules():
    """Den publicerede mængde læses fra byggerens egen regel, ikke fra et gæt."""
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import build_public_tree as builder
        return set(builder.INTERNAL_SUFFIXES), set(builder.INTERNAL_NAMES), set(builder.INTERNAL_PARTS)
    except Exception:  # noqa: BLE001
        return {".md", ".sh", ".py", ".toml", ".log", ".bak", ".env"}, set(), set()


def published(rel: str) -> bool:
    """Stier der faktisk kan nå en kunde.

    Første version af denne port gættede på `site/`-præfikset og meldte 20
    fund i `site/BUDGET.md`, `site/DECISION.md`, `site/RESEARCH.md` og
    `site/devnotify/LAUNCH.md`. De er ikke publiceret — `build_public_tree.py`
    sender `.md` væk, og det blev efterprøvet live (`/BUILD.md` → 404,
    `/RESEARCH.md` → 404). Det er den fejltype planen har dokumenteret seks
    gange: porten læste en anden mængde end den, den skulle dække. Reglen
    læses derfor nu fra byggeren selv, så de to ikke kan komme i uoverensstemmelse.
    """
    suffixes, names, parts = _internal_rules()
    path = Path(rel)
    if path.suffix.lower() in suffixes or path.name in names:
        return False
    if parts & set(path.parts):
        return False
    return rel.startswith("site/") or rel.startswith("plugin/")


def check(report_only: bool = False):
    errors, prefixes = load_allowlist()
    hits, unreadable = iter(scan())
    for name in unreadable:
        errors.append(f"kunne ikke læses som tekst (springes over): {name}")

    findings, live_allowed, prose_allowed = [], [], []
    for rel, number, line, live in hits:
        if is_allowed(rel, prefixes):
            (live_allowed if live else prose_allowed).append((rel, number, line))
            continue
        if not live and not published(rel):
            # Historie i en fil der ikke publiceres, uden en levende adresse.
            prose_allowed.append((rel, number, line))
            continue
        if live and not published(rel) and Path(rel).suffix.lower() not in SHIPPABLE:
            # En plan-, rapport- eller logfil der ikke publiceres. Den kan ikke
            # ringe nogen steder hen, uanset at den nævner en adresse.
            prose_allowed.append((rel, number, line))
            continue
        reason = "levende adresse" if live else "prose i en publiceret fil"
        findings.append(f"{rel}:{number}: {reason} — {line[:110]}")

    if not report_only:
        for entry in errors:
            findings.append(entry)

    return findings, live_allowed, prose_allowed, len(hits)


def selftest() -> int:
    """Bevis at porten kan fejle. Muterer kun egne fixtures, ikke repoet."""
    scratch = Path("/tmp/eucomply-dead-providers-selftest")
    passed, failed = 0, 0

    def run(files, allowlist_entries, expect_red, label):
        nonlocal passed, failed
        import shutil
        if scratch.exists():
            shutil.rmtree(scratch)
        scratch.mkdir(parents=True)
        for name, body in files.items():
            p = scratch / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")
        (scratch / "allow.json").write_text(
            json.dumps({"entries": allowlist_entries}), encoding="utf-8")
        try:
            findings, _, _, _ = check()
        except Exception as exc:  # noqa: BLE001
            print(f"  selftest: {label} — kastede {exc!r}")
            failed += 1
            return
        red = bool(findings)
        if red == expect_red:
            passed += 1
            print(f"  selftest: {label} — {'rød som forventet' if red else 'grøn som forventet'}")
        else:
            failed += 1
            print(f"  selftest: {label} — {'RØD' if red else 'GRØN'} men forventet "
                  f"{'rød' if expect_red else 'grøn'}")

    # Kortene lægges oveni de ægte moduler, så check() scanner scratch'en.
    global ROOT, ALLOWLIST
    real_root, real_allow = ROOT, ALLOWLIST
    ROOT, ALLOWLIST = scratch, scratch / "allow.json"
    try:
        run({"src/license.js": "fetch('https://api.lemonsqueezy.com/v1/licenses/activate')"},
            [], True, "levende adresse i uvedkommende fil")
        run({"src/license.js": "fetch('https://api.lemonsqueezy.com/v1/licenses/activate')"},
            [{"path": "src/", "reason": "kendt undtagelse"}], False,
            "allowlist med begrundelse dækker den")
        run({"src/license.js": "fetch('https://api.lemonsqueezy.com/v1/licenses/activate')"},
            [{"path": "src/"}], True, "allowlist uden begrundelse er selv et fund")
        run({"notes.md": "License API (former Lemon Squeezy) integration."},
            [], False, "changelog-prose i en ikke-publiceret fil er tilladt")
        run({"site/x.html": "<p>former Lemon Squeezy</p>"},
            [], True, "prose i en publiceret fil skal stå i allowlisten")
        run({"site/x.html": "fetch('https://api.lemonsqueezy.com/v1/licenses/validate')"},
            [], True, "levende adresse i site/ er aldrig tilladt")
        run({"a.js": "const h = 'gumroad.com';"}, [], True,
            "værtnavn uden scheme er også en levende adresse")
        run({"a.js": "const h = 'https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03';"},
            [], False, "den levende udbyder giver ingen fund")
        run({"a.js": "vi brugte Lemon Squeezy i 2025"}, [], False,
            "historie i .js der ikke publiceres er tilladt")
        run({"DECISION.md": "**Opret Gumroad-konto** (gumroad.com, gratis)"}, [], False,
            "planfil der ikke publiceres er tilladt selv med en adresse")
        run({"DECISION.md": "**Opret Gumroad-konto** (gumroad.com, gratis)"}, [], False,
            "samme planfil: .md sendes væk af byggeren, så den er ikke publiceret")
        run({"src/app.py": "URL = 'https://api.lemonsqueezy.com/v1/licenses/validate'"},
            [], True, "død adresse i shipbar kode i en ikke-publiceret sti er rød")
        run({"site/readme.txt": "Upgrade for Lemon Squeezy license API integration"},
            [], True, "publiceret changelog skal have en begrundet tilladelse")
    finally:
        ROOT, ALLOWLIST = real_root, real_allow
        import shutil
        if scratch.exists():
            shutil.rmtree(scratch, ignore_errors=True)

    total = passed + failed
    if failed:
        print(f"SELFTEST RØD — {failed} af {total} negative cases slipper")
        return 1
    print(f"SELFTEST GRØN — alle {total} negative cases fanges")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="store_true",
                        help="rapportér uden at fejle (til en rapport, ikke til porten)")
    parser.add_argument("--selftest", action="store_true",
                        help="kør selftesten: bevis at porten kan fejle")
    args = parser.parse_args()

    if args.selftest:
        return selftest()

    findings, live_allowed, prose_allowed, total = check(report_only=args.report)

    print(f"død udbyder: {total} nævnt i repoet "
          f"({len(live_allowed)} levende adresse tilladt, "
          f"{len(prose_allowed)} prose tilladt)")

    if live_allowed:
        print("  LEVENDE ADRESSE TILLADT (død udbyder-kode, stadig i repoet):")
        for rel, number, line in live_allowed:
            print(f"    {rel}:{number}: {line[:100]}")

    for entry in findings:
        print(f"  FUND {entry}")

    if findings and not args.report:
        print(f"FEJL {len(findings)} fund — se tools/dead_provider_allowlist.json")
        return 1
    if findings:
        print(f"RAPPORT {len(findings)} fund (--report: fejler ikke med vilje)")
        return 0
    print("OK    ingen død betalingsudbyder i den kode, der kan nå en kunde")
    return 0


if __name__ == "__main__":
    sys.exit(main())
