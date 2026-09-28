#!/usr/bin/env python3
"""Gate: er Chrome-extensionen målt klar til Chrome Web Store — og har /extension/ én købsvej?

    python3 tools/check_store_ready.py
    python3 tools/check_store_ready.py --selftest

Baggrund, målt 28/9. `chrome-ext/` lå målt "sun": zip'en byte-identisk med
kilden, ni rigtige elementer, `host_permissions` matchende den origin popup'en
kalder. Det er sandt, og det er **ikke** det samme som at den er
butiksparat. Fire ting manglede, og ingen af dem kunne ses ved at læse
koden:

1. **`alarms` var erklæret og aldrig brugt.** `chrome.alarms` findes 0 gange i
   `background.js` og `popup.js`. Det er ikke en skrivefejl — det er den
   permission-typedef Chrome Web Store-afviser reviews for ("unnecessary
   permissions"), og den modsiger samtidig `/extension/`s egen tekst: *"The
   extension sends your target URL to the public API — nothing else."*
2. **`chrome-ext/README.md` pegede to gange på `icons/generate-icons.py`**,
   en fil der ikke findes. Den er publiceret i zip'en, så det er en død
   reference i en fil en udvikler læser — samme klasse som opgave 32's døde
   checkout-løfte.
3. **`/extension/` lovede en butiksliste der ikke findes** — "Installation
   guide (once published) … (link will appear here)".
4. **`/extension/` havde ingen købsvej.** Kortet "Pro upgrade path" forklarede
   godt at licensen er til WordPress-pluginen, men **linkede ingen steder**:
   en Pro-tekst uden et købslink er ikke en købsvej. Popup'en har en
   (`/pro/`), landingssiden havde ikke. Det er præcis acceptkriteriet i
   opgave 91.

Derfor er denne port bygget som **en måling, ikke en rapport**. R5 er den
interessante regel: en permission skal **bevises brugt**, og beviset er et
mønster i koden, ikke strengens navn. Det er ikke en vilkårlig undtagelsesliste
— `activeTab` er deklarativt ubrugt i koden (ordet findes 0 gange) men
*bruges reelt*, fordi `chrome.tabs.query({active: true})` er præcis den
adgang den køber. En regel der krævede strengen ville have fundet en falsk
mangel og lært næste agent at slette en nødvendig permission; en regel der
bare sagde "alarm er ikke brugt" ville være en håndskrevet undtagelse, der
glemmer sig selv ved den næste permission. Sådan er den skrevet: hver
permission har sit **bevismønster**, og en permission uden bevis er rød.

Alt læses med standardbiblioteket, så porten dør ikke i CI på en
manglende pip-afhængighed — samme grund som `check_sample_coverage.py`'s
PDF. Selftesten er skrevet sådan, at en grøn case **også** skal være rød
uden sin mærke: ellers ville porten kunne være grøn af en grund den ikke måtte
være grøn af (samme krav som opgave 90's `data-competitor`-case).
"""
import json
import os
import re
import struct
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = os.path.join(ROOT, "chrome-ext")
PUBLISHED_PAGE = os.path.join(ROOT, "site-dist", "extension", "index.html")

# Chrome Web Stores egne grænser. De er ikke valgt af mig — en butiksafvisning
# på dem koster en ny review-uge, så de er skrevet som tal, ikke som "kort nok".
CWS_LIMITS = {"name": 45, "description": 132, "version": 15}
CWS_ICONS = (16, 48, 128)

# R5. En permission skal bevises brugt. Nøglen er permissionen, værdien er et
# mønster i extensionens egen kode der kun kan ramme den adgang.
PERMISSION_PROOF = {
    "activeTab": r"chrome\.tabs\.query\s*\(\s*\{[^}]*active\s*:\s*true",
    "tabs": r"chrome\.tabs\.",
    "storage": r"chrome\.storage\.",
    "alarms": r"chrome\.alarms\.",
    "scripting": r"chrome\.scripting\.",
    "identity": r"chrome\.identity\.",
}

# R8. Pladsholdere, der lover en URL der ikke findes. Samme ord som opgave 32
# fjernede fra et købsanker.
DEAD_PROMISE = (
    "link will appear here",
    "link coming here",
    "coming soon",
    "tbd",
    "todo:",
)

PAID_SURFACES = ("/pro/", "/plugin/", "/pricing/", "/store/")

# R11. En licens skal have et navn, der kan efterprøves, og en tekst der giver
# rettighederne. `open source` er et juridisk begreb — det er en hensigtserklæring
# om en tilladelse, ikke en tilladelse. Navnet er det, en læser kan slå op.
LICENSE_NAME = "LICENSE"
LICENSES = ("MIT", "Apache", "BSD", "GPL", "MPL", "Unlicense")
LICENSE_PROMISE = ("open source", "open-source", "opensource", "free software", "source available")
GRANT_PHRASE = "Permission is hereby granted"

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
CODE_SUFFIXES = (".js", ".html", ".json")
HOSTISH = re.compile(r"https?://[a-z0-9.-]+", re.I)
# R4. Bemærk at IPv6-gruppen **ikke** er valgfri: `\[?::1\]?` matcher den tomme
# streng foran hvert tegn, så porten ville have fundet på al kode. Selftesten
# fangede det, fordi den grønne case var rød med et fund den ikke kunne forklare.
# Og `.local` matcher kun **i en URL** — `chrome.storage.local` er lovlig kode,
# en `.local`-vært er ikke. Begge fejl var falske fund i min egen port.
BAD_HOST = re.compile(
    r"\blocalhost\b|127\.0\.0\.1|\b::1\b|file://|https?://[^\s'\"]*\.local\b",
    re.I,
)
MAIN = re.compile(r"<main\b.*?</main>", re.S | re.I)
HREF = re.compile(r'href="([^"]+)"')
BACKTICK_PATH = re.compile(r"`([\w][\w./-]*\.(?:json|js|py|png|html|md|zip|txt|yml))`")
STORE_URL = re.compile(r"https?://chrome(?:google)?\.com/webstore|https?://chromewebstore\.google\.com")
ZIP_NAME = re.compile(r"/assets/(eucomply-extension-([0-9][0-9A-Za-z.+-]*)\.zip)")


def read_text(path, findings, label):
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except OSError as exc:
        findings.append(f"{label}: kan ikke læses ({exc})")
        return None


def read_zip_names(path, findings, label):
    """Medlemmerne i et arkiv. Kun filer — en mappe-sti tæller ikke som indhold."""
    try:
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                findings.append(f"{label}: korrupt arkiv")
                return None
            return {name for name in archive.namelist() if not name.endswith("/")}
    except (OSError, zipfile.BadZipFile) as exc:
        findings.append(f"{label}: kan ikke læses ({exc})")
        return None


def archive_contains_license_text(path):
    """Har arkivet en LICENSE, der faktisk er en licenstekst?"""
    try:
        with zipfile.ZipFile(path) as archive:
            return GRANT_PHRASE in archive.read(LICENSE_NAME).decode("utf-8", "replace")
    except (OSError, KeyError, zipfile.BadZipFile):
        return False


def png_size(path):
    """Returnér (bredde, højde) fra PNG'ens IHDR, eller None hvis ikke en PNG."""
    try:
        with open(path, "rb") as handle:
            head = handle.read(24)
    except OSError:
        return None
    if len(head) < 24 or not head.startswith(PNG_MAGIC) or head[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", head[16:24])
    return width, height


def main_content(page_html):
    """Sidens `<main>`. Header og footer skal ikke tælle som købsvej."""
    found = MAIN.search(page_html or "")
    return found.group(0) if found else (page_html or "")


def collect(root=ROOT, ext=None, page=None, published=ROOT):
    """Læs extensionen og den publicerede side. Returnér fund."""
    findings = []
    ext = ext or os.path.join(root, "chrome-ext")
    page = page or os.path.join(published, "site-dist", "extension", "index.html")

    manifest_path = os.path.join(ext, "manifest.json")
    raw = read_text(manifest_path, findings, "manifest")
    if raw is None:
        return findings
    try:
        manifest = json.loads(raw)
    except ValueError as exc:
        findings.append(f"manifest: ugyldig JSON ({exc})")
        return findings

    # R1 — manifestversionen. CWS afviser alt under 3 i dag.
    if manifest.get("manifest_version") != 3:
        findings.append(
            f"manifest: manifest_version er {manifest.get('manifest_version')!r}, Chrome Web Store kræver 3"
        )

    # R2 — de tre længdegrænser butikken håndhæver.
    for field in ("name", "description", "version"):
        value = manifest.get(field)
        limit = CWS_LIMITS[field]
        if not isinstance(value, str) or not value:
            findings.append(f"manifest: {field} mangler")
        elif len(value) > limit:
            findings.append(f"manifest: {field} er {len(value)} tegn, grænsen er {limit}")

    # R3 — ikonerne skal findes og være rigtige PNG'er i rigtige mål. En 0-byte
    # fil er det, man opdager efter uploaden.
    icons = manifest.get("icons") or {}
    for size in CWS_ICONS:
        rel = icons.get(str(size))
        if not rel:
            findings.append(f"manifest: icon {size} er ikke erklæret")
            continue
        actual = png_size(os.path.join(ext, rel))
        if actual is None:
            findings.append(f"icon {size}: {rel} findes ikke som en læsbar PNG")
        elif actual != (size, size):
            findings.append(f"icon {size}: {rel} er {actual[0]}x{actual[1]}, skal være {size}x{size}")

    # Kode — alle skibsfiler, til både R4 og R5.
    code = []
    calls = []  # kun JS og HTML: manifesten kan hverken kalde noget eller bevise sit eget brug
    for dirpath, _dirs, names in os.walk(ext):
        for name in sorted(names):
            if not name.endswith(CODE_SUFFIXES):
                continue
            path = os.path.join(dirpath, name)
            text = read_text(path, findings, f"extension/{name}")
            if text is not None:
                code.append(text)
                if not name.endswith(".json"):
                    calls.append(text)
    if not code:
        findings.append("extension: ingen JS/HTML/JSON læst — et grønt resultat ville være meningsløst")
    joined = "\n".join(code)
    called = "\n".join(calls)

    # R4 — ingen lokale eller fil-URL'er. De virker aldrig for en butiks-bruger.
    for match in sorted(set(BAD_HOST.findall(joined))):
        findings.append(f"extension: lokal adresse i koden ({match}) — virker ikke for butiks-brugere")

    # R5 — erklærede permissions skal bevises brugt.
    for perm in manifest.get("permissions") or []:
        proof = PERMISSION_PROOF.get(perm)
        if proof is None:
            findings.append(
                f"permission: {perm!r} har intet bevismønster i porten — tilføj mønstret, "
                "så porten dømmer det samme næste gang"
            )
        elif not re.search(proof, joined):
            findings.append(
                f"permission: {perm!r} er erklæret, men koden bruger den ikke "
                f"(bevismønsteret {proof} rammer 0 gange)"
            )

    # R6 — host_permissions og den origin koden kalder skal være de samme,
    # i begge retninger. Den første retning fanger en tilladelse der er død,
    # den anden et API-kald uden tilladelse (som fejler i brugerens browser).
    hosts = manifest.get("host_permissions") or []
    for host in hosts:
        # Match-mønsteret rammer hele origin'en, så man ikke må strippe med det:
        # `HOSTISH.sub('', host)` efterlod tom streng. Værten ryddes i stedet
        # for sin sti-jokerte.
        origin = host.rstrip("/*")
        if origin and origin not in called:
            findings.append(f"host_permissions: {host} bruges aldrig i koden")
    for origin in sorted(set(HOSTISH.findall(called))):
        if "://eucomplypro.com" in origin:
            continue  # dokumentations-URL i popup'ens markup, ikke et API-kald
        if not any(host.rstrip("/*") == origin for host in hosts):
            findings.append(f"koden kalder {origin}, som ikke står i host_permissions")

    # R7 — én version i hele kæden. En side der peger på en gammel zip er
    # dømt af asset-gaten, en *ny* zip med et gammelt navn er dømt af ingen.
    version = manifest.get("version")
    page_html = read_text(page, findings, "site-dist/extension/index.html")
    if page_html is None:
        return findings
    zips = sorted({match.group(2) for match in ZIP_NAME.finditer(page_html)})
    if not zips:
        findings.append("site-dist/extension: ingen link til eucomply-extension-*.zip")
    for found in zips:
        if version and found != version:
            findings.append(
                f"version: siden linker til extension-{found}.zip, manifestet siger {version}"
            )

    # R8 — ingen død butiks-løfte i den publicerede tekst.
    lowered = page_html.lower()
    for phrase in DEAD_PROMISE:
        if phrase in lowered:
            findings.append(f"site-dist/extension: dødt løfte i markup'en ({phrase!r})")
    for url in sorted(set(STORE_URL.findall(page_html))):
        findings.append(f"site-dist/extension: butiks-URL {url} — hvis der ikke er en udgivet liste, er den et dødt løfte")

    # R9 — præcis én købsvej i sidens indhold, og den skal findes i det
    # publicerede træ. Nav-linket i headeren tæller ikke med: en global
    # `/pricing/` i navigationen er ikke den vej, opgaven beder om.
    body = main_content(page_html)
    targets = []
    for href in HREF.findall(body):
        path = href.split("?")[0].split("#")[0]
        if any(path.rstrip("/") == paid.rstrip("/") for paid in PAID_SURFACES):
            if path not in targets:
                targets.append(path)
    if not targets:
        findings.append("site-dist/extension: ingen købsvej i <main> — en Pro-tekst uden link er ikke en vej")
    elif len(targets) > 1:
        findings.append(f"site-dist/extension: {len(targets)} købsveje i <main> ({', '.join(targets)}) — opgaven vil have én")
    for target in targets:
        if not os.path.isdir(os.path.join(published, "site-dist", target.strip("/"))):
            findings.append(f"site-dist/extension: købsvejen {target} findes ikke i det publicerede træ")

    # R10 — README'en må ikke pege på filer der ikke findes. Den ligger i
    # zip'en, så en død reference er publiceret.
    readme = read_text(os.path.join(ext, "README.md"), findings, "chrome-ext/README.md")
    if readme is not None:
        for token in sorted(set(BACKTICK_PATH.findall(readme))):
            if os.path.exists(os.path.join(ext, token)) or os.path.exists(os.path.join(root, token)):
                continue
            findings.append(f"chrome-ext/README.md: peger på {token!r}, som ikke findes")

    # R11 — en licenspåstand skal have en licenstekst bag sig, i kilden **og**
    # i den zip læseren henter. Målt 28/9: `chrome-ext/` havde ingen LICENSE,
    # zip'en havde ni medlemmer og ingen af dem var en, og `/extension/` sagde
    # "Open source" i ren tekst — et løfte uden rettigheder. To sider af samme
    # mangel, så porten dømmer begge: teksten i kilden, og medlemmet i
    # arkivet. Ordet "open source" er ikke nok, for det er et juridisk begreb
    # og en hensigtserklæring; porten vil have licensens **navn**.
    license_path = os.path.join(ext, LICENSE_NAME)
    if not os.path.exists(license_path):
        findings.append(
            f"extension: {LICENSE_NAME} mangler i chrome-ext/ — en licenspåstand uden licenstekst "
            "giver læseren ingen rettigheder"
        )
    else:
        license_text = read_text(license_path, findings, f"chrome-ext/{LICENSE_NAME}") or ""
        if GRANT_PHRASE not in license_text:
            findings.append(f"chrome-ext/{LICENSE_NAME}: er ikke en licenstekst (ingen {GRANT_PHRASE!r})")

    for found in zips:
        archive = os.path.join(published, "site-dist", "assets", f"eucomply-extension-{found}.zip")
        names = read_zip_names(archive, findings, f"site-dist/assets/eucomply-extension-{found}.zip")
        if names is None:
            continue
        if LICENSE_NAME not in names:
            findings.append(
                f"site-dist/assets/eucomply-extension-{found}.zip: indeholder ikke {LICENSE_NAME} — "
                "det er den fil læseren henter, så det er den der skal give rettighederne"
            )
            continue
        if not archive_contains_license_text(archive):
            findings.append(
                f"site-dist/assets/eucomply-extension-{found}.zip: {LICENSE_NAME} er der, men er ikke en licenstekst"
            )

    named = [name for name in LICENSES if re.search(rf"\b{re.escape(name)}\b", page_html, re.I)]
    gesturing = [phrase for phrase in LICENSE_PROMISE if phrase in lowered]
    if gesturing and not named:
        findings.append(
            f"site-dist/extension: lover en licens med ordene {gesturing} uden at nævne hvilken — "
            "en licens skal have et navn, der kan efterprøves"
        )

    return findings


def _fixture(root, manifest_extra=None, permissions=None, hosts=None, name=None, description=None,
             readme=None, page_body=None, version="1.0.2", write_icon=True, broken_icon=None,
             code_extra="", license_source=True, license_zip=True, license_text=GRANT_PHRASE):
    """Skriv et minimalt, grønt extension-træ. Hvert argument bryder præcis én regel."""
    ext = os.path.join(root, "chrome-ext")
    os.makedirs(os.path.join(ext, "icons"), exist_ok=True)
    for size in CWS_ICONS:
        path = os.path.join(ext, "icons", f"icon{size}.png")
        if not write_icon:
            open(path, "wb").close()
            continue
        # `broken_icon` skriver en rigtig PNG i forkert mål, så R3 dømmer
        # dimensionen og ikke filformatet.
        drawn = 32 if broken_icon == size else size
        with open(path, "wb") as handle:
            handle.write(PNG_MAGIC + b"\x00\x00\x00\x0dIHDR")
            handle.write(struct.pack(">II", drawn, drawn))
            handle.write(b"\x00\x00\x00\x00\x00\x00")

    manifest = {
        "manifest_version": 3,
        "name": name if name is not None else "EUComply — Website Compliance Checker",
        "version": version,
        "description": description or "One-click scan for nine technical website signals.",
        "permissions": permissions if permissions is not None else ["activeTab", "storage"],
        "host_permissions": hosts if hosts is not None else ["https://api.example.com/*"],
        "background": {"service_worker": "background.js"},
        "icons": {str(s): f"icons/icon{s}.png" for s in CWS_ICONS},
    }
    if manifest_extra:
        manifest.update(manifest_extra)
    with open(os.path.join(ext, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

    with open(os.path.join(ext, "background.js"), "w", encoding="utf-8") as handle:
        handle.write("chrome.storage.local.get('x', function() {});\n")
    with open(os.path.join(ext, "popup.js"), "w", encoding="utf-8") as handle:
        handle.write(
            "chrome.tabs.query({ active: true, currentWindow: true }, function(t) {});\n"
            "fetch('https://api.example.com/scan?url=');\n" + code_extra
        )
    with open(os.path.join(ext, "README.md"), "w", encoding="utf-8") as handle:
        handle.write(readme if readme is not None else "# EUComply\n\nFiles: `manifest.json`, `popup.js`.\n")
    if license_source:
        with open(os.path.join(ext, LICENSE_NAME), "w", encoding="utf-8") as handle:
            handle.write(f"MIT License\n\n{license_text}\n")

    for paid in ("pro", "extension"):
        os.makedirs(os.path.join(root, "site-dist", paid), exist_ok=True)
    os.makedirs(os.path.join(root, "site-dist", "assets"), exist_ok=True)
    with zipfile.ZipFile(
        os.path.join(root, "site-dist", "assets", f"eucomply-extension-{version}.zip"), "w"
    ) as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        if license_zip:
            archive.writestr(LICENSE_NAME, f"MIT License\n\n{license_text}\n")
    body = page_body if page_body is not None else (
        '<main><a href="/assets/eucomply-extension-{v}.zip">Download</a>'
        '<a href="/pro/" class="btn">See Pro</a></main>'
    ).format(v=version)
    with open(os.path.join(root, "site-dist", "extension", "index.html"), "w", encoding="utf-8") as handle:
        handle.write(
            "<!doctype html><html><head><title>EUComply</title></head><body>"
            "<nav><a href='/pricing/'>Pricing</a></nav>" + body + "</body></html>"
        )
    return ext


def _selftest():
    def run(**kwargs):
        with tempfile.TemporaryDirectory() as tmp:
            _fixture(tmp, **kwargs)
            return collect(root=tmp, ext=os.path.join(tmp, "chrome-ext"),
                           page=os.path.join(tmp, "site-dist", "extension", "index.html"),
                           published=tmp)

    def expect_red(label, marker, **kwargs):
        def case():
            findings = run(**kwargs)
            if not findings:
                return f"case {label!r}: Forventet rød, men porten var grøn"
            if not any(marker in finding for finding in findings):
                return f"case {label!r}: rød, men ingen fund nævner {marker!r} — {findings[0]}"
            return None
        return case

    def expect_green(label):
        def case():
            findings = run()
            return None if not findings else f"case {label!r}: rent træ gav {findings[0]}"
        return case

    cases = [
        # Den grønne case skal være **rød** uden sin mærke, ellers er den
        # grøn af en grund den ikke måtte være grøn af.
        expect_green("rent træ er grønt"),
        # R1
        expect_red("manifest_version 2 er rød", "manifest_version", manifest_extra={"manifest_version": 2}),
        # R2
        expect_red("langt navn", "grænsen er 45", name="EUComply " + "x" * 50),
        expect_red("lang beskrivelse", "grænsen er 132", description="x" * 200),
        # R3
        expect_red("tom ikon", "læsbar PNG", write_icon=False),
        expect_red("forkert ikon-mål", "skal være", broken_icon=48),
        # R4
        expect_red("localhost i koden", "lokal adresse", code_extra="fetch('http://localhost:8787/scan');\n"),
        # R5 — kernen i opgaven
        expect_red("ubrugt permission", "koden bruger den ikke", permissions=["activeTab", "storage", "alarms"]),
        expect_red("ubevist permission", "bevismønster", permissions=["activeTab", "storage", "webRequest"]),
        # R6
        expect_red("død host_permission", "bruges aldrig", hosts=["https://api.example.com/*", "https://gammel.example.org/*"]),
        expect_red("API-kald uden tilladelse", "ikke står i host_permissions", hosts=["https://andet.example.net/*"]),
        # R7
        expect_red("version-drift", "manifestet siger",
                   page_body='<main><a href="/assets/eucomply-extension-1.0.1.zip">Download</a><a href="/pro/">Pro</a></main>'),
        # R8
        expect_red("pladsholder", "dødt løfte",
                   page_body='<main><p>link will appear here</p><a href="/pro/">Pro</a></main>'),
        expect_red("butiks-URL", "dødt løfte",
                   page_body='<main><a href="https://chromewebstore.google.com/detail/x">Store</a>'
                             '<a href="/assets/eucomply-extension-1.0.2.zip">Download</a><a href="/pro/">Pro</a></main>'),
        # R9
        expect_red("ingen købsvej", "ikke en vej",
                   page_body='<main><a href="/assets/eucomply-extension-1.0.2.zip">Download</a></main>'),
        expect_red("to købsveje", "købsveje i <main>",
                   page_body='<main><a href="/pro/">Pro</a><a href="/plugin/">Plugin</a></main>'),
        expect_red("død købsvej", "ikke i det publicerede træ",
                   page_body='<main><a href="/store/">Store</a></main>'),
        # R10
        expect_red("død reference i README", "som ikke findes",
                   readme="# EUComply\n\nKør `icons/generate-icons.py` forst.\n"),
        # R11 — dagens fund: kilde, arkiv og påstand er tre sider af samme mangel
        expect_red("ingen LICENSE i kilden", "mangler i chrome-ext", license_source=False),
        expect_red("LICENSE uden for zip'en", "indeholder ikke LICENSE", license_zip=False),
        expect_red("LICENSE der ikke er en licens", "ikke en licenstekst", license_text="Se vilkår."),
        expect_red("licenspåstand uden navn", "uden at nævne hvilken",
                   page_body='<main><p>Open source.</p>'
                             '<a href="/assets/eucomply-extension-1.0.2.zip">Download</a><a href="/pro/">Pro</a></main>'),
    ]
    broken = [message for message in (case() for case in cases) if message]
    if broken:
        for message in broken:
            print("SELFTEST FEJLET:", message)
        return 1
    print(f"SELFTEST GRØN — alle {len(cases)} negative cases fanges")
    return 0


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    findings = collect()
    if findings:
        for finding in findings:
            print("FUND:", finding)
        print(f"\n{len(findings)} fund — extensionen er ikke butiksparat, og /extension/ har ikke én købsvej.")
        return 1
    print("Butiksparat: manifestet er målt mod Chrome Web Stores grænser, hver permission "
          "er bevilget, og /extension/ har præcis én købsvej i det publicerede træ.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
