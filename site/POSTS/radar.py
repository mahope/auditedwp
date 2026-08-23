#!/usr/bin/env python3
"""Graveyard radar — gratis lyttepost (0 kr, læsning uden login/konto).

Samler ferske shutdown/deprecation-signaler fra offentlige kilder:
  - IndieHackers feed
  - r/SaaS og r/EntrepreneurRideAlong via Reddit .rss (officiel, ingen API-nøgle)
  - Hacker News Algolia (stories om shutdowns, sidste 7 dage)
  - GitHub search: populære repos (>=500 stjerner) arkiveret de sidste 14 dage
Output: RADAR.md (seneste signaler, dedupe mod forrige kørsel i radar_seen.json).

Kør: python3 radar.py   (cron-venlig, ingen netværksnøgler)
"""
import json, re, time, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).parent
SEEN = HERE / "radar_seen.json"
FEEDS = {
    "r/SaaS": "https://www.reddit.com/r/SaaS/search.rss?q=shutting+down+OR+shut+down&restrict_sr=1&sort=new&t=week",
    "r/EntrepreneurRideAlong": "https://www.reddit.com/r/EntrepreneurRideAlong/search.rss?q=shutdown+OR+%22winding+down%22&restrict_sr=1&sort=new&t=week",
    "IndieHackers": "https://www.indiehackers.com/feed.xml",
}
KEY = re.compile(r"(shut\w*\s*down|winding down|sunset|deprecat|discontinu|no longer maintained|archived)", re.I)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "radar/0.1 (research listening post)"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def fetch_json(url):
    return json.loads(fetch(url))


def parse_rss(data):
    items = []
    try:
        root = ET.fromstring(data)
        for e in root.iter():
            if e.tag.rsplit("}", 1)[-1] == "item" or e.tag == "entry":
                title = link = date = ""
                for c in e:
                    tag = c.tag.rsplit("}", 1)[-1]
                    if tag == "title":
                        title = (c.text or "").strip()
                    elif tag == "link":
                        link = c.get("href") or (c.text or "").strip()
                    elif tag in ("pubDate", "published", "updated"):
                        date = (c.text or "").strip()
                if title:
                    items.append({"title": title, "link": link, "date": date})
    except ET.ParseError:
        pass
    return items


def hn_algolia(hits, seen):
    # HN Algolia: ferske stories om shutdowns (sidste 7 dage)
    t = int(time.time()) - 7 * 86400
    q = '("shutting down" OR "winding down" OR "sunsetting") AND ("SaaS" OR "app" OR "service" OR "product")'
    url = ("https://hn.algolia.com/api/v1/search_by_date?query=" + urllib.parse.quote(q) +
           f"&tags=story&numericFilters=created_at_i>{t}&hitsPerPage=50")
    for h in fetch_json(url).get("hits", []):
        title = h.get("title") or ""
        if KEY.search(title):
            link = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
            key = f"hn:{h.get('objectID')}"
            if key not in seen:
                hits.append({"source": "HN", "title": title, "link": link,
                             "date": (h.get("created_at") or "")[:16]})
                new_key = h["link"] if False else key
                hits[-1]["_key"] = key


def github_archived(hits, seen):
    # GitHub: populære repos arkiveret de sidste 14 dage (>=500 stjerner)
    since = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 14 * 86400))
    url = ("https://api.github.com/search/repositories?q=archived:true+stars:%3E%3D500"
           f"+pushed:%3E{since}&sort=updated&per_page=30")
    for r in fetch_json(url).get("items", []):
        title = f"{r['full_name']} ({r['stargazers_count']}★) archived"
        key = f"gh:{r['id']}"
        if key not in seen:
            hits.append({"source": "GitHub", "title": title, "link": r["html_url"],
                         "date": (r.get("updated_at") or "")[:16], "_key": key})


def main():
    seen = set(json.loads(SEEN.read_text())) if SEEN.exists() else set()
    hits, new = [], []
    for src, url in FEEDS.items():
        try:
            for it in parse_rss(fetch(url)):
                key = it["link"] or it["title"]
                if KEY.search(it["title"]) and key not in seen:
                    it["source"] = src
                    it["_key"] = key
                    hits.append(it)
                    new.append(key)
        except Exception as e:
            print(f"radar: {src} fejlede: {e}")
    try:
        hn_algolia(hits, seen)
    except Exception as e:
        print(f"radar: HN Algolia fejlede: {e}")
    try:
        github_archived(hits, seen)
    except Exception as e:
        print(f"radar: GitHub fejlede: {e}")
    # dedupe mod seen for HN/GH-hits
    final = [h for h in hits if h.get("_key") and h["_key"] not in seen]
    already = len(hits) - len(final)
    new.extend(h["_key"] for h in final)
    for h in final:
        h.pop("_key", None)

    lines = ["# RADAR — graveyard lyttepost", "", f"Kørsel: {time.strftime('%Y-%m-%d %H:%M')}",
             f"Nye signaler denne kørsel: {len(final)} (allerede set og sprunget over: {already})", ""]
    for h in final[:40]:
        lines.append(f"- [{h['source']}] {h['date'][:16]} — {h['title']}  {h['link']}")
    if not final:
        lines.append("_Ingen nye shutdown-signaler i kilderne denne kørsel._")
    lines += ["", "Screening (manuel, 4 kriterier fra RESEARCH.md): betalingsvilje bevist /",
              "<2 konkurrenter ved dybdegrav / moat tilgængelig fra DK / ikke én-blogpost-beskrivelig.",
              "Kandidater der består alle fire → evalueres i STATUS.md samme dag."]
    out = HERE / "RADAR.md"
    prev = out.read_text() if out.exists() else ""
    if prev:
        parts = prev.split("\n---\n")
        lines.append("\n---\n" + "\n".join(parts[:2])[:4000])
    out.write_text("\n".join(lines))
    seen.update(new)
    SEEN.write_text(json.dumps(sorted(seen)[-2000:]))
    print(f"radar: {len(final)} nye signaler → {out}")


if __name__ == "__main__":
    main()
