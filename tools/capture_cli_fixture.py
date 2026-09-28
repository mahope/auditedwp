#!/usr/bin/env python3
"""Optag en rigtig HTTP-svar som fixture, så /cli/'s eksempel kan genereres.

    python3 tools/capture_cli_fixture.py https://webflow.com

Skriver `tools/fixtures/<vaert>.json` med status, de overskrifter motoren
læser, og gzip'et HTML. **Kun til en ny optagelse** — gaten kører aldrig
netværk; den læser den committede fixture.

Hvorfor en fixture og ikke et netværkskald i gaten: en port der kan fejle
fordi en tredjepartsside ændrede sig, lærer ingenting om vores egen kode, og
den ville være rød en dag af en grund der ikke findes i repoet. Optagelsen er
engangsk og målbar (sha256 + bytes), og alt efterfølgende er deterministisk.
"""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tools" / "fixtures"

# Præcis de overskrifter motoren læser — se `headers.get(` i
# eucomply-scanner/engine/index.js. Resten af svaret er ikke en del af et
# resultat, så den gemmes ikke.
MOTOR_HEADERS = [
    "strict-transport-security",
    "content-security-policy",
    "content-security-policy-report-only",
    "x-content-type-options",
    "referrer-policy",
    "x-frame-options",
    "permissions-policy",
    "set-cookie",
]

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: capture_cli_fixture.py <url>", file=sys.stderr)
        return 2
    url = sys.argv[1]
    if not url.startswith("http"):
        url = "https://" + url

    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*"},
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
            status = r.status
            raw_headers = {k.lower(): v for k, v in r.headers.items()}
            body = r.read()
            final_url = r.geturl()
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} — ikke optaget, et fejlsvar er ikke et scanningseksempel", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001 — rapportér alt, giv ikke op i stilhed
        print(f"kunne ikke hente {url}: {e}", file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    host = urlparse(final_url).hostname or "ukendt"
    path = OUT / f"{host}.json"

    payload = {
        "url": final_url,
        "status": status,
        "captured": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "bytes": len(body),
        "body_sha256": hashlib.sha256(body).hexdigest(),
        "headers": {k: raw_headers[k] for k in MOTOR_HEADERS if k in raw_headers},
        "body_gz_b64": base64.b64encode(gzip.compress(body, 9)).decode("ascii"),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"skrev {path.relative_to(ROOT)} — {status}, {len(body)} bytes, sha256 {payload['body_sha256'][:16]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
