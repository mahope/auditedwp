#!/usr/bin/env python3
"""Build the extension package the site actually serves.

    python3 tools/build_extension_zip.py --write     # skriv zip'en
    python3 tools/build_extension_zip.py --check      # gaten: skal den publicerede zip matche?
    python3 tools/build_extension_zip.py --selftest

Why this exists, measured 28/9. The Chrome extension's published package had
been rebuilt by hand twice (1.0.1 → 1.0.2 var den anden), and the archive
carried no `LICENSE` at all — while `/extension/` said "Open source" in plain
text and shipped that archive to anyone who clicked Download. `chrome-ext/` is
in a public repo with no license file at the root either (`licenseInfo: null`),
so "open source" was a claim with no grant of rights behind it anywhere in the
package.

A zip nobody can reproduce is a zip that drifts silently, so the layout is
decided here instead of in a deploy note: every member is a path relative to
`chrome-ext/`, member order is sorted, and timestamps are fixed — otherwise
`--check` would fail on a rebuild that only differed by the clock, and the gate
would teach the next agent to ignore it.

The version is read from `manifest.json` and used as the file name, so the
archive, the page link and the manifest cannot disagree. Stale archives are
deleted on `--write`, because a zip left in the tree is one a reader can still
download under an old version number.
"""
from __future__ import annotations

import argparse
import io
import json
import pathlib
import re
import sys
import tempfile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXT = ROOT / "chrome-ext"
ASSETS = ROOT / "site" / "assets"

# Fixed timestamp (1980-01-01), the earliest a zip can represent. Chosen so two
# builds of the same source produce the same bytes.
FIXED_TIME = (1980, 1, 1, 0, 0, 0)

# Not shipped: the gate's own scratch, and anything a developer leaves behind.
EXCLUDE_DIRS = {"__pycache__", ".git", "node_modules"}
LICENSE_NAME = "LICENSE"
VERSION_RE = re.compile(r"^[0-9][0-9A-Za-z.+-]*$")


def manifest_version(root: pathlib.Path = EXT) -> str:
    path = root / "manifest.json"
    try:
        version = json.loads(path.read_text(encoding="utf-8")).get("version") or ""
    except (OSError, ValueError) as exc:
        sys.exit(f"FEJL: chrome-ext/manifest.json kan ikke læses ({exc})")
    if not VERSION_RE.match(version):
        sys.exit(f"FEJL: version {version!r} er ikke et filnavn, zip'en hedder så noget andet")
    return version


def sources(root: pathlib.Path = EXT) -> list[pathlib.Path]:
    """Alle filer under chrome-ext/, sorteret, i arkivets rækkefølge."""
    found = [
        path for path in root.rglob("*")
        if path.is_file() and not (EXCLUDE_DIRS & set(path.relative_to(root).parts))
    ]
    return sorted(found, key=lambda path: path.relative_to(root).as_posix())


def build(root: pathlib.Path = EXT) -> bytes:
    """Byg arkivet i hukommelsen. Deterministisk: samme kilde → samme bytes."""
    members = sources(root)
    if not members:
        sys.exit("FEJL: chrome-ext/ er tom — et tomt arkiv ville være grønt af en grund det ikke måtte")
    if LICENSE_NAME not in {path.name for path in members}:
        # En "open source"-påstand uden licenstekst er den mangel denne
        # script blev skrevet for. Den skal være umulig at bygge forbi.
        sys.exit(f"FEJL: chrome-ext/{LICENSE_NAME} mangler — zip'en ville sende en licenspåstand uden licens")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in members:
            info = zipfile.ZipInfo(path.relative_to(root).as_posix(), date_time=FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    return buffer.getvalue()


def zip_path(version: str) -> pathlib.Path:
    return ASSETS / f"eucomply-extension-{version}.zip"


def write_redirects(removed: list[str], version: str, path: pathlib.Path | None = None) -> None:
    """Sørg for at hver fjernet pakke stadig svarer 301 mod den nye.

    Dette er ikke pynt. `site/_headers` giver `/assets/*` `Cache-Control:
    immutable` i et år, så en pakke der forsvinder fra træet uden en redirect
    giver enten en 404 eller — værre — den gamle pakke i kant-cachen i op til
    et år. Det er sket tre gange i dette repo med pluginens zips, og det er
    derfor en handling ved sletningen og ikke en note i en deploy-plan.

    Skrivningen er idempotent: en eksisterende linje for samme kilde røres ikke
    ved, så gentagne builds ikke høster filen.
    """
    if not removed:
        return
    path = path or (ROOT / "site" / "_redirects")
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = text.splitlines()
    have = {line.split()[0] for line in lines if line.strip()}
    added = []
    for old in removed:
        source = f"/assets/eucomply-extension-{old}.zip"
        if source in have:
            continue
        lines.append(f"{source} /assets/eucomply-extension-{version}.zip 301")
        added.append(source)
    if not added:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for source in added:
        print(f"redirect: {source} -> /assets/eucomply-extension-{version}.zip 301")


def write(version: str, payload: bytes) -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    out = zip_path(version)
    out.write_bytes(payload)
    removed = []
    for path in sorted(ASSETS.glob("eucomply-extension-*.zip")):
        if path.name != out.name:
            stale_version = path.stem.rsplit("-", 1)[-1]
            path.unlink()
            removed.append(stale_version)
            print(f"fjernet forældet pakke: {path.name}")
    write_redirects(removed, version)
    with zipfile.ZipFile(out) as archive:
        names = archive.namelist()
    print(f"OK: {out.relative_to(ROOT)} — {version}, {len(names)} filer, {len(payload)} B")
    return len(names)


def check(version: str) -> int:
    out = zip_path(version)
    if not out.exists():
        print(f"FUND: {out.relative_to(ROOT)} mangler — kør build_extension_zip.py --write")
        return 1
    published = out.read_bytes()
    rebuilt = build()
    if published != rebuilt:
        with zipfile.ZipFile(io.BytesIO(published)) as archive:
            names = sorted(archive.namelist())
        print(f"FUND: {out.relative_to(ROOT)} er ikke en build af chrome-ext/ ({len(published)} B "
              f"publiceret, {len(rebuilt)} B bygget, {len(names)} medlemmer)")
        print("      kør python3 tools/build_extension_zip.py --write")
        return 1
    for path in sorted(ASSETS.glob("eucomply-extension-*.zip")):
        if path.name != out.name:
            print(f"FUND: {path.relative_to(ROOT)} er en forældet pakke, der stadig kan downloades")
            return 1
    # En redirect, der peger på en pakke der ikke findes, sender læseren i
    # 404 lige så stille som en manglende linje gør. Den skal pege på den
    # version, der ligger i træet.
    redirects = ROOT / "site" / "_redirects"
    if redirects.exists():
        for line in redirects.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) != 3 or not parts[0].startswith("/assets/eucomply-extension-"):
                continue
            if parts[1] != f"/assets/eucomply-extension-{version}.zip":
                print(f"FUND: site/_redirects: {parts[0]} -> {parts[1]}, som ikke er den version "
                      f"der ligger i træet ({version}) — læseren får en 404")
                return 1
    with zipfile.ZipFile(io.BytesIO(published)) as archive:
        names = archive.namelist()
        if LICENSE_NAME not in names:
            print(f"FUND: zip'en indeholder ikke {LICENSE_NAME} — licenspåstand uden licenstekst")
            return 1
        license_text = archive.read(LICENSE_NAME).decode("utf-8", "replace")
    if "Permission is hereby granted" not in license_text:
        print(f"FUND: {LICENSE_NAME} i zip'en er ikke en licenstekst (ingen 'Permission is hereby granted')")
        return 1
    print(f"Extensionens pakke er målt: {out.relative_to(ROOT)} er byte-identisk med en "
          f"frisk build af chrome-ext/ ({len(names)} filer, {LICENSE_NAME} med, {len(published)} B), "
          "og ingen forældet pakke ligger i træet.")
    return 0


def _selftest() -> int:
    """Den grønne case skal også være rød, ellers er den grøn af en grund
    den ikke måtte være grøn af."""
    cases = []

    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        ext = root / "chrome-ext"
        ext.mkdir()
        (ext / "manifest.json").write_text('{"version": "1.0.2"}', encoding="utf-8")
        (ext / "LICENSE").write_text("MIT License\n\nPermission is hereby granted, free of charge\n",
                                     encoding="utf-8")
        (ext / "popup.js").write_text("// hej\n", encoding="utf-8")
        try:
            build(ext)
        except SystemExit as exc:
            cases.append(f"case 'rent træ bygger': {exc}")

    with tempfile.TemporaryDirectory() as tmp:
        ext = pathlib.Path(tmp) / "chrome-ext"
        ext.mkdir()
        (ext / "manifest.json").write_text('{"version": "1.0.2"}', encoding="utf-8")
        (ext / "popup.js").write_text("// hej\n", encoding="utf-8")
        try:
            build(ext)
            cases.append("case 'manglende LICENSE': Forventet rød, men build() gav en zip")
        except SystemExit as exc:
            if LICENSE_NAME not in str(exc):
                cases.append(f"case 'manglende LICENSE': rød, men uden grund: {exc}")

    with tempfile.TemporaryDirectory() as tmp:
        ext = pathlib.Path(tmp) / "chrome-ext"
        ext.mkdir()
        (ext / "manifest.json").write_text('{"version": "../escape"}', encoding="utf-8")
        try:
            manifest_version(ext)
            cases.append("case 'ugyldig version': Forventet rød, men versionen blev accepteret")
        except SystemExit:
            pass

    with tempfile.TemporaryDirectory() as tmp:
        redirects = pathlib.Path(tmp) / "_redirects"
        redirects.write_text("/assets/eucomply-extension-1.0.1.zip /assets/eucomply-extension-1.0.3.zip 301\n",
                             encoding="utf-8")
        write_redirects(["1.0.1", "1.0.2"], "1.0.3", path=redirects)
        text = redirects.read_text(encoding="utf-8")
        if text.count("1.0.1.zip") != 1:
            cases.append("case 'redirect er idempotent': eksisterende linje blev duplikeret")
        if "/assets/eucomply-extension-1.0.2.zip /assets/eucomply-extension-1.0.3.zip 301" not in text:
            cases.append("case 'fjernet pakke får redirect': 1.0.2 mangler i _redirects")
        write_redirects(["1.0.2"], "1.0.3", path=redirects)
        if redirects.read_text(encoding="utf-8") != text:
            cases.append("case 'redirect er idempotent': en gentaget build ændrede filen")

    broken = [message for message in cases if message]
    for message in broken:
        print("SELFTEST FEJLET:", message)
    if broken:
        return 1
    print(f"SELFTEST GRØN — alle {4} negative cases fanges")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="skriv zip'en og fjern forældede")
    parser.add_argument("--check", action="store_true", help="kør som gate: skal den publicerede zip matche?")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        return _selftest()
    version = manifest_version()
    if args.check:
        return check(version)
    write(version, build())
    return 0


if __name__ == "__main__":
    sys.exit(main())
