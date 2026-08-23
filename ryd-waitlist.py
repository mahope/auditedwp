#!/usr/bin/env python3
"""Rydder agentens egne testposter ud af EUComply-ventelisten.

Agenten taalte sine egne roegtests som rigtige tilmeldinger og rapporterede
"Waitlist: 6 personer" da tallet reelt var 0. Scriptet tager backup foerst,
sletter kun poster der beviseligt er tests, og roerer aldrig stats/ratelimit.
"""
import json, os, pathlib, sys, urllib.parse, urllib.request

NS = "8465f75104b44d1c933f772b25fe2060"
BASE = "https://api.cloudflare.com/client/v4"
T = os.environ.get("CLOUDFLARE_API_TOKEN") or os.environ.get("CF_API_TOKEN")
if not T:
    sys.exit("Intet Cloudflare-token i miljoeet.")

# Reserverede/aabenlyse testdomaener — kan pr. definition ikke modtage post
TEST = ("@example.com", "@example.org", "@example.net", "@test.com")


def api(sti, metode="GET", krop=None):
    r = urllib.request.Request(f"{BASE}{sti}", method=metode,
                               data=json.dumps(krop).encode() if krop else None,
                               headers={"Authorization": f"Bearer {T}",
                                        "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=60) as s:
        return json.loads(s.read().decode())


acc = api("/accounts")["result"][0]["id"]
noegler = [k["name"] for k in api(f"/accounts/{acc}/storage/kv/namespaces/{NS}/keys")["result"]]

# Hent alt, saa backuppen er komplet foer noget slettes
data = {}
for k in noegler:
    try:
        r = urllib.request.Request(
            f"{BASE}/accounts/{acc}/storage/kv/namespaces/{NS}/values/"
            f"{urllib.parse.quote(k, safe='')}", headers={"Authorization": f"Bearer {T}"})
        with urllib.request.urlopen(r, timeout=60) as s:
            data[k] = s.read().decode()
    except Exception as e:
        data[k] = f"__kunne ikke laeses__ {e}"

sik = pathlib.Path.home() / "hermes-ceo" / "waitlist-backup.json"
sik.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Backup af alle {len(data)} noegler: {sik}")

# Find testposterne og de tidsindeks der peger paa dem
slet = [k for k in noegler if any(t in k.lower() for t in TEST)]
slet += [k for k in noegler if k.startswith("by_time:")
         and any(t in data.get(k, "").lower() for t in TEST)]
beholdt = [k for k in noegler if k not in slet]

print(f"\nSletter {len(slet)} testposter:")
for k in slet:
    print("  -", k)
print(f"\nBeholder {len(beholdt)}:")
for k in beholdt:
    print("  +", k)

if "--toer" in sys.argv:
    sys.exit("\n(toerkoersel — intet slettet)")

svar = api(f"/accounts/{acc}/storage/kv/namespaces/{NS}/bulk/delete", "POST", slet)
print(f"\nSletning ok: {svar.get('success')}")
for e in svar.get("errors", []):
    print("  FEJL:", e)

rest = [k["name"] for k in api(f"/accounts/{acc}/storage/kv/namespaces/{NS}/keys")["result"]]
ægte = [k for k in rest if "@" in k]
print(f"\nTilbage i KV: {len(rest)} noegler")
print(f"AEGTE TILMELDINGER: {len(ægte)}")
for k in ægte:
    print("  ", k)
