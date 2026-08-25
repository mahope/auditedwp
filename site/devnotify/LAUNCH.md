# Launch-tekster — KLAR, venter på Mads' ja (23. august)

Ingen af disse må postes uden Mads' udtrykkelige godkendelse. Alt er skrevet
færdigt; hans arbejde er at sige ja.

---

## Product Hunt

**Navn:** DevNotify

**Tagline (max 60 tegn):**
GitHub notifications in your macOS menu bar

**Description:**
DevNotify puts your GitHub unread count in the macOS menu bar — one click
shows PRs, issues and mentions; another click opens them on GitHub. Native
Tauri app (not Electron), your personal access token never leaves your machine.
Free 7-day trial, then $19 lifetime. Also works with GitLab.

**First comment (maker's):**
We built DevNotify because "just check github.com" wasn't working for us —
notifications arrived while we were heads-down, and by the time we looked,
reviews had been sitting for hours. So now the count lives where our eyes
already are: the menu bar. Everything is local (token included), polling is
polite, and a license is a one-time $19. Happy to answer questions about the
Tauri build or how we handle tokens safely.

**Topics:** developer tools, mac, productivity, github

---

## Show HN

**Title:** Show HN: DevNotify – GitHub notifications in your macOS menu bar

**Body:**
Hi HN! We built DevNotify: a native-ish (Tauri) macOS menu bar app that shows
your GitHub unread notification count and lets you open any item in one click.
It also supports GitLab.

Why: GitHub has no desktop client, the web bell only works while a tab is
open, and email digests bury review requests. Existing menu bar options are
Electron apps with sporadic maintenance.

Details worth mentioning:
- Your GitHub PAT stays on your machine; nothing is proxied through a server.
- Polls every 60s against the notifications API, respects rate limits.
- Licensing via Lemon Squeezy with remote key validation; 7-day trial,
  $19 lifetime.
- Built with Tauri v2 — ~4.5 MB DMG vs. typical Electron footprint.

Site: https://eucomplypro.com/
Downloads (Apple Silicon + Intel, SHA-256 checksums published):
https://eucomplypro.com/#download

Ask: what would make this a daily driver for you? GitLab support just shipped;
other forges (Gitea/Bitbucket) are plausible next.

---

## Postings-regel

Før Mads siger ja til EN af disse, postes intet. Når han siger ja:
1. Han poster selv ELLER giver skriftligt grønt lys med hvilken konto.
2. Teksterne bruges som de ligger her — ingen sidste-øjebliks-ændringer.
