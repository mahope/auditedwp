#!/usr/bin/env python3
"""Build the plugin package the site actually serves.

    python3 tools/build_plugin_zip.py [--version 1.3.13]

Why this is a script and not a `zip` line in a deploy note: the archive layout
is part of the product, and it was got wrong twice in one iteration — once with
`eucomply/` missing, once with absolute staging paths inside the archive. Neither
mistake reached a customer, because `artifact_findings()` opens the zip and looks
for `eucomply/eucomply.php`, but both cost a full gate run to find. The rule the
archive has to keep is one line: every member is `eucomply/<file>`, sourced from
`plugin/`, and nothing else is in there.

The version is checked against three places that must agree — `PLUGIN_VERSION` in
tools/check_pro_claims.py, `EUCOMPLY_VERSION` in the plugin, and the manifest —
so a release cannot ship a zip whose name does not match its contents. Stale
archives are removed rather than left behind, because a zip left in the tree is
one a `wp.org` style upgrade can still be served.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugin"
ASSETS = ROOT / "site" / "assets"

# Only these three files are shipped. Anything else in plugin/ is either a test
# fixture or an internal note, and a WordPress install has no use for it.
MEMBERS = ("eucomply.php", "readme.txt", "uninstall.php")


def plugin_version() -> str:
    text = (PLUGIN / "eucomply.php").read_text(encoding="utf-8")
    match = re.search(r"EUCOMPLY_VERSION',\s*'([0-9]+\.[0-9]+\.[0-9]+)", text)
    if not match:
        sys.exit("FEJL: EUCOMPLY_VERSION findes ikke i plugin/eucomply.php")
    return match.group(1)


def gate_version() -> str:
    text = (ROOT / "tools" / "check_pro_claims.py").read_text(encoding="utf-8")
    match = re.search(r'PLUGIN_VERSION\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"', text)
    if not match:
        sys.exit("FEJL: PLUGIN_VERSION findes ikke i tools/check_pro_claims.py")
    return match.group(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="", help="fail unless this is the version in the plugin")
    args = parser.parse_args()

    version = plugin_version()
    if args.version and args.version != version:
        sys.exit(f"FEJL: --version {args.version} men pluginen er {version}")
    if gate_version() != version:
        sys.exit(f"FEJL: PLUGIN_VERSION i porten er {gate_version()}, pluginen er {version}")

    for rel in ("update.json", "site/update.json"):
        manifest = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        if manifest.get("version") != version:
            sys.exit(f"FEJL: {rel} siger {manifest.get('version')}, pluginen er {version}")
        if manifest.get("download_url", "").endswith(f"eucomply-{version}.zip") is False:
            sys.exit(f"FEJL: {rel} peger ikke på eucomply-{version}.zip")

    for name in MEMBERS:
        if not (PLUGIN / name).exists():
            sys.exit(f"FEJL: plugin/{name} mangler")

    out = ASSETS / f"eucomply-{version}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in MEMBERS:
            zf.write(PLUGIN / name, f"eucomply/{name}")

    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
        bad = [n for n in names if not n.startswith("eucomply/")]
        if bad:
            sys.exit(f"FEJL: arkivet indeholder stier uden eucomply/-præfiks: {bad}")
        if sorted(names) != sorted(f"eucomply/{n}" for n in MEMBERS):
            sys.exit(f"FEJL: arkivet indeholder {names}")

    # Only the WordPress plugin packages. The glob is anchored on a version
    # number on purpose: `eucomply-*.zip` also matches
    # `eucomply-extension-1.0.1.zip`, and an earlier version of this script
    # deleted the Chrome extension's published package because of it.
    for stale in sorted(ASSETS.glob("eucomply-[0-9]*.zip")):
        if stale.name != out.name:
            stale.unlink()
            print(f"fjernet forældet pakke: {stale.name}")

    print(f"OK: {out.relative_to(ROOT)} — {version}, {len(MEMBERS)} filer under eucomply/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
