#!/usr/bin/env python3
"""Generate the guides hub page (/devnotify/guides/) from existing guide dirs.
Auto-discovers every guide under site/devnotify/guides/ plus top-level articles,
reads each page's <title>, and renders a categorized, linked index."""
import os, re, html

BASE = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "devnotify-site"))
SITE = "https://auditedwp.pages.dev"

def title_of(path):
    t = re.search(r"<title>(.*?)</title>", open(path).read(), re.S)
    return html.unescape(t.group(1)).strip() if t else os.path.basename(os.path.dirname(path))

# discover guides/
guides = []
gdir = os.path.join(BASE, "guides")
for slug in sorted(os.listdir(gdir)):
    p = os.path.join(gdir, slug, "index.html")
    if os.path.isfile(p):
        guides.append((slug, title_of(p)))

# top-level article pages (exclude app pages)
TOP = ["best-github-notification-apps-macos", "github-desktop-notifications-mac",
       "gitlab-notifications-mac", "github-token-scopes-guide"]
tops = [(s, title_of(os.path.join(BASE, s, "index.html"))) for s in TOP]

# categorize by keyword
CATS = [
    ("Fixes & troubleshooting", ["not-showing", "not-working", "badge", "phantom",
                                 "sound-alert", "miss-pr-review", "coming-back-unread"]),
    ("Taming the noise", ["turn-off", "too-many", "slack-too-noisy", "vs-email-digests",
                          "emails-after-unsubscribing", "filter-github-emails-gmail",
                          "watch-vs-star", "org-repos", "multiple-computers-sync"]),
    ("Routing: Slack, Discord & Teams", ["slack-github-notifications", "discord", "teams"]),
    ("Platforms", ["on-windows", "not-showing-windows", "on-linux", "on-android",
                   "iphone", "-mac/", "see-github-notifications-on-mac", "gitlab"]),
]
def cat_for(slug):
    for name, kws in CATS:
        if any(k in slug + "/" for k in kws):
            return name
    return "More guides"

categorized = {name: [] for name, _ in CATS}
categorized["More guides"] = []
used = set()
for slug, t in guides:
    c = cat_for(slug)
    # avoid double-listing mac pages in both fixes and platforms: first match wins by order
    if slug not in used:
        categorized[c].append((slug, t))
        used.add(slug)

CSS = """
:root{--bg:#0d1117;--panel:#161b22;--border:#30363d;--text:#e6edf3;--muted:#8b949e;--accent:#2f81f7;--green:#3fb950;--radius:12px}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;line-height:1.6}
.wrap{max-width:900px;margin:0 auto;padding:0 20px}
a{color:var(--accent)}
header{padding:18px 0;border-bottom:1px solid var(--border)}
header .wrap{display:flex;align-items:center;justify-content:center}
.logo{font-weight:700;font-size:1.1rem;display:flex;align-items:center;gap:8px;text-decoration:none;color:var(--text)}
.logo .dot{width:10px;height:10px;border-radius:50%;background:var(--green)}
h1{font-size:clamp(1.7rem,4.5vw,2.4rem);margin:44px 0 12px;line-height:1.2}
.sub{color:var(--muted);font-size:1.05rem;margin-bottom:36px}
h2{font-size:1.3rem;margin:34px 0 14px;padding-bottom:8px;border-bottom:1px solid var(--border)}
ul.g{list-style:none}
ul.g li{padding:9px 0;border-bottom:1px solid #21262d}
ul.g a{text-decoration:none;font-size:.98rem}
ul.g a:hover{text-decoration:underline}
.count{color:var(--muted);font-size:.85rem;font-weight:400}
.cta{background:var(--panel);border:1px solid var(--border);border-radius:var(--radius);padding:26px;margin:44px 0;text-align:center}
.btn{display:inline-block;padding:13px 26px;border-radius:var(--radius);font-weight:600;text-decoration:none;background:var(--green);color:#04180a;margin-top:10px}
footer{border-top:1px solid var(--border);padding:28px 0;color:var(--muted);font-size:.85rem;margin-top:60px;text-align:center}
"""

parts = [f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>All GitHub Notification Guides — Fixes, Setup &amp; Noise Control | DevNotify</title>
<meta name="description" content="Every guide we've written about GitHub notifications: fix missing alerts, route Slack/Discord/Teams, tame the noise on macOS, Windows, Linux, iPhone and Android. Free, no signup.">
<link rel="canonical" href="{SITE}/devnotify/guides/">
<meta property="og:type" content="website">
<meta property="og:title" content="All GitHub Notification Guides | DevNotify">
<meta property="og:description" content="Fixes, routing and noise-control guides for GitHub notifications on every platform.">
<meta property="og:url" content="{SITE}/devnotify/guides/">
<style>{CSS}</style>
</head>
<body>
<header><div class="wrap"><a class="logo" href="/devnotify/"><span class="dot"></span> DevNotify</a></div></header>
<main class="wrap">
<h1>GitHub notification guides</h1>
<p class="sub">{len(guides)} step-by-step guides for the notification problems developers hit every week. No signup required.</p>"""]

for name, _ in CATS:
    items = categorized[name]
    if not items:
        continue
    parts.append(f'<h2>{html.escape(name)} <span class="count">({len(items)})</span></h2>\n<ul class="g">')
    for slug, t in sorted(items, key=lambda x: x[1].lower()):
        parts.append(f'<li><a href="/devnotify/guides/{slug}/">{t}</a></li>')
    parts.append("</ul>")

if tops:
    parts.append('<h2>Deep dives <span class="count">(4)</span></h2>\n<ul class="g">')
    for s, t in tops:
        parts.append(f'<li><a href="/devnotify/{s}/">{t}</a></li>')
    parts.append("</ul>")

parts.append(f"""
<div class="cta">
<strong>Tired of fixing your notification setup every month?</strong>
<p style="color:var(--muted);margin-top:8px">DevNotify puts your unread count in the menu bar — one glance instead of one more settings rabbit hole.</p>
<a class="btn" href="/devnotify/download/">Download free trial</a>
<p style="color:var(--muted);font-size:.85rem;margin-top:10px">$19 lifetime license after a free 7-day trial · macOS, Windows, Linux</p>
</div>
</main>
<footer><div class="wrap">© 2026 DevNotify · <a href="/devnotify/terms">Terms</a> · <a href="/devnotify/privacy">Privacy</a></div></footer>
</body>
</html>
""")

out = os.path.join(BASE, "guides", "index.html")
open(out, "w").write("\n".join(parts))

# add to sitemap
sm_path = os.path.join(BASE, "sitemap.xml")
sm = open(sm_path).read()
u = f"{SITE}/devnotify/guides/"
if u not in sm:
    sm = sm.replace("</urlset>", f"<url><loc>{u}</loc><changefreq>weekly</changefreq></url>\n</urlset>")
    open(sm_path, "w").write(sm)

print(f"wrote {out} with {len(guides)} guides + {len(tops)} deep dives")
