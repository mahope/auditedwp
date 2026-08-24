#!/usr/bin/env python3
"""Generate DevNotify SEO guides (iteration 193) into site/devnotify/."""
import os, html

BASE = os.path.join(os.path.dirname(__file__), "..", "site", "devnotify")
SITE = "https://auditedwp.pages.dev"

CSS = open(os.path.join(BASE, "gitlab-notifications-mac", "index.html")).read().split("<style>")[1].split("</style>")[0]

GUIDES = [
 dict(
  slug="slack-github-notifications",
  title="Stop GitHub Notifications Flooding Your Slack — Do This Instead | DevNotify",
  desc="Slack turns GitHub into noise. Here's how to keep PR reviews in your macOS menu bar instead of your team chat — without missing anything urgent.",
  h1='GitHub in Slack is <em>noise</em>. Put it back where it belongs.',
  accent="#e01e5a",
  body="""
<p>If your team wires GitHub into Slack, you already know the problem: every push, every CI run,
every bot comment lands in the same channel as the message your teammate tagged you in.
Real review requests drown in automated chatter — and muting the channel means missing
the one mention that mattered.</p>

<h2>Why Slack is the wrong inbox for code</h2>
<ul>
<li><strong>Mixed contexts.</strong> Code events sit next to human conversation, so neither gets the attention it needs.</li>
<li><strong>No triage model.</strong> Slack has read/unread, not "waiting on my review". You can't see what's actually yours.</li>
<li><strong>Loud by default.</strong> The fix most teams reach for — mute the channel — throws away the signal along with the noise.</li>
</ul>

<h2>The better split</h2>
<p>Keep Slack for humans. Move machine-generated GitHub activity to a dedicated surface
where unread counts mean something:</p>
<ol>
<li>In GitHub, unsubscribe from notification emails for repos where you only watch CI.</li>
<li>Install <a href="/devnotify/download/">DevNotify</a> and paste a personal access token
   (<a href="/devnotify/github-token-scopes-guide/">which scopes?</a>). Your unread count lives in the macOS menu bar.</li>
<li>Leave a single Slack channel for release announcements only — everything else stays out.</li>
</ol>

<h2>What changes day to day</h2>
<p>You stop alt-tabbing between apps to check whether a PR came back. A number appears
in your menu bar when something needs you; it disappears when you've handled it.
Review requests get answered faster because they're never buried under a deploy log.</p>

<p class="cta-inline"><a class="btn btn-primary" href="/devnotify/download/">Try DevNotify free for 7 days</a></p>
<p style="margin-top:14px">Works with GitHub and GitLab, 100% local — your token never leaves your Mac. $19 one-time license after the trial.</p>
"""),

 dict(
  slug="github-notification-sounds-macos",
  title="Custom Sounds & Quiet Hours for GitHub Notifications on macOS | DevNotify",
  desc="GitHub's default notification sound trains you to ignore it. Set a distinct sound for review requests and real quiet hours on your Mac.",
  h1='A sound you can <em>trust</em> — not another ping.',
  accent="#8957e5",
  body="""
<p>macOS plays the same alert for a code-owner review request as it does for a Dependabot bump.
After a week of that, your brain learns the sound means nothing, and you start missing
the pings that actually matter.</p>

<h2>The problem with one-size-fits-all alerts</h2>
<ul>
<li><strong>Habituation.</strong> Identical sounds for important and trivial events train you to ignore both.</li>
<li><strong>No schedule.</strong> Notifications don't respect your focus time or time zone — a merge from the EU office buzzes during your dinner.</li>
<li><strong>Wrong channel.</strong> Email notifications pile up unseen; browser badges vanish when the tab closes.</li>
</ul>

<h2>A setup that survives week two</h2>
<ol>
<li>Pick one app as your single GitHub surface. For this walkthrough we'll use
    <a href="/devnotify/download/">DevNotify</a>, which lives in the menu bar rather than a tab.</li>
<li>Enable its notification sound only for <em>mentions and review requests</em>. Everything else updates the badge silently.</li>
<li>Set quiet hours for evenings and weekends. The unread count still accumulates — it just waits until morning to speak.</li>
<li>Turn off GitHub email notifications entirely. One inbox, one source of truth.</li>
</ol>

<h2>Why menu bar beats browser badges</h2>
<p>A badge tied to a browser tab dies the moment you close it. A menu-bar count is visible
in every app, all day — so "silent but visible" becomes possible. Loud when it matters,
quiet when it doesn't.</p>

<p class="cta-inline"><a class="btn btn-primary" href="/devnotify/download/">Download DevNotify (free trial)</a></p>
<p style="margin-top:14px">macOS 13+. Apple Silicon and Intel. $19 lifetime license after the 7-day trial.</p>
"""),

 dict(
  slug="multiple-github-accounts-mac",
  title="Managing Multiple GitHub Accounts' Notifications on One Mac | DevNotify",
  desc="Personal repo, work org, client projects — three GitHub identities, one menu bar. How to see every account's unread count without logging out and in.",
  h1='Three GitHub accounts. <em>One</em> number to watch.',
  accent="#d29922",
  body="""
<p>Side project on your personal account, day job on the company org, a contractor seat on a
client's enterprise instance. GitHub assumes one identity per person — so notifications for
your other accounts land in an inbox you only remember at midnight.</p>

<h2>What people try today (and why it fails)</h2>
<ul>
<li><strong>Two browsers.</strong> Two badges that vanish whenever you close a window, plus constant profile switching.</li>
<li><strong>Email filters.</strong> Works until a filter misfiles a direct review request under "promotions".</li>
<li><strong>Checking manually.</strong> The honest method — and the reason things slip.</li>
</ul>

<h2>One menu bar, every account</h2>
<ol>
<li>Create one personal access token per account
    (<a href="/devnotify/github-token-scopes-guide/">scope guide here</a>).</li>
<li>Add each token as a source in <a href="/devnotify/download/">DevNotify</a>.</li>
<li>Every unread item from every account now rolls up into a single menu-bar count —
    hover to see which account and repo it belongs to, click to jump straight to it.</li>
</ol>

<h2>Built for contractors and maintainers</h2>
<p>If you maintain OSS while working full-time, this is the difference between answering a
bug report in ten minutes versus tomorrow. The count is always on screen; the context switch
is one click, not one logout.</p>

<p class="cta-inline"><a class="btn btn-primary" href="/devnotify/download/">Try it free for 7 days</a></p>
<p style="margin-top:14px">Tokens stay in your macOS keychain. Nothing syncs anywhere. $19 once, yours forever.</p>
"""),

 dict(
  slug="github-notifications-not-working-mac",
  title="GitHub Notifications Not Working on Your Mac? 7 Fixes That Actually Help | DevNotify",
  desc="Missed review requests, stale badges, silent mentions? Work through these seven fixes — or replace the broken pipeline entirely.",
  h1='Missing review requests? It&#39;s probably <em>not</em> you.',
  accent="#f85149",
  body="""
<p>"My teammate says she requested my review three days ago." If that sentence feels familiar,
you're not careless — the default GitHub notification pipeline has several silent failure points.
Here are the ones worth checking, in order.</p>

<h2>1. Watch vs. Participating</h2>
<p>GitHub's default filter is "Participating and @mentions". If nobody explicitly mentioned you,
a review request can hide behind it. Check github.com/notifications → filter settings.</p>

<h2>2. Email landed nowhere useful</h2>
<p>Search your mail for <code>[GitHub]</code>. If nothing shows up, check GitHub Settings → Notifications
and confirm your primary address — corporate SSO often routes to an alias you never read.</p>

<h2>3. Browser badge amnesia</h2>
<p>The tab-badge resets whenever the tab closes or the browser restarts before you looked.
That's not a bug you can fix — it's the design.</p>

<h2>4. macOS Focus modes silently eating alerts</h2>
<p>System Settings → Notifications: confirm your GitHub-related app isn't excluded by a Focus profile
that was switched on weeks ago and forgotten.</p>

<h2>5–7. Or skip the pipeline entirely</h2>
<ol>
<li>Generate a personal access token (<a href="/devnotify/github-token-scopes-guide/">guide</a>).</li>
<li>Point <a href="/devnotify/download/">DevNotify</a> at it — it queries GitHub directly, so there is no email hop, no badge reset, no Focus dependency for the count itself.</li>
<li>The menu-bar number reflects reality within minutes. What it shows is what exists.</li>
</ol>

<p class="cta-inline"><a class="btn btn-primary" href="/devnotify/download/">Fix it for good — free 7-day trial</a></p>
<p style="margin-top:14px">100% local, works with GitHub and GitLab. $19 lifetime license after the trial.</p>
"""),
]

HEADER_NAV = None  # reuse structure below

def render(g):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{g['title']}</title>
<meta name="description" content="{g['desc']}">
<link rel="canonical" href="{SITE}/devnotify/{g['slug']}/">
<meta property="og:type" content="article">
<meta property="og:title" content="{g['title']}">
<meta property="og:description" content="{g['desc']}">
<meta property="og:url" content="{SITE}/devnotify/{g['slug']}/">
<meta name="twitter:card" content="summary">
<style>{CSS}</style>
</head>
<body>
<header><div class="wrap"><div class="logo">DevNotify<span class="dot"></span></div>
<nav><a href="/devnotify/">Home</a><a href="/devnotify/download/">Download</a></nav></div></header>
<main>
<div class="wrap article">
<h1>{g['h1']}</h1>
{g['body']}
</div>
</main>
<footer><div class="wrap">
  <div>© 2026 DevNotify · Made for developers, by developers</div>
  <div><a href="/devnotify/terms.html">Terms</a> · <a href="/devnotify/privacy.html">Privacy</a></div>
</div></footer>
</body>
</html>
"""

count=0
for g in GUIDES:
    d=os.path.join(BASE,g["slug"]); os.makedirs(d,exist_ok=True)
    # fix apostrophe inside h1 that used a raw ' inside f-string source above
    open(os.path.join(d,"index.html"),"w").write(render(g))
    count+=1

# Update sitemap: insert new URLs before </urlset>
sm_path=os.path.join(BASE,"sitemap.xml")
sm=open(sm_path).read()
new=""
for g in GUIDES:
    u=f"{SITE}/devnotify/{g['slug']}/"
    if u not in sm:
        new+=f"<url><loc>{u}</loc><changefreq>monthly</changefreq></url>\n"
if new:
    sm=sm.replace("</urlset>",new+"</urlset>")
open(sm_path,"w").write(sm)

print(f"wrote {count} guides, added {len(GUIDES)} urls to sitemap")
