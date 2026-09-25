# Launch-tekster — EUComply — KLARE, venter på Mads' ja (26. august)

Ingen af disse må postes uden Mads' udtrykkelige godkendelse. Alt er skrevet
færdigt; hans arbejde er at sige ja. Site: https://eucomplypro.com/

---

## Show HN

**Titel:** Show HN: EUComply – free compliance scan of any website (GDPR, DSA, EAA)

**Tekst:**

Hi HN! I built EUComply after watching companies pay consultants thousands to check things a script can check in seconds: is there a consent mechanism before trackers fire, are Consent Mode v2 / TCF signals present, do security headers exist, are privacy policy / imprint / accessibility statement links in place?

Paste any URL at https://eucomplypro.com/scan/ and get a scored report in ~10 seconds. It works on any CMS — WordPress, Shopify, Webflow, Next.js, static HTML — because it only reads what any browser sees: headers and HTML. No plugin, no account, no server access.

The scanning core is open source (Node.js, MIT): https://github.com/mahope/eucomply-scanner — run it locally or call the free public API:

    curl "https://eucomply-scan.mahope-eeb.workers.dev/scan?url=example.com"

What it checks today: SSL/HSTS, cookie-consent platform detection, third-party trackers without consent signals, Google Consent Mode v2, IAB TCF, form/privacy-link hygiene, security headers, DORA email/DNS redundancy signals.

The current paid tier ($79/year per website) is a WordPress license. It unlocks editable DPA, NIS2/DORA and EAA HTML starters plus an HTML report from the latest WordPress scan. Full templates are sold separately.

Happy to answer questions about the detection heuristics or the false-positive trade-offs of header-only scanning.

---

## Product Hunt

**Navn:** EUComply Pro

**Tagline (max 60 tegn):**
Website compliance scans for GDPR, DSA & EAA — any CMS

**Description:**
EUComply scans any public website for technical compliance signals: missing consent before tracking, absent Consent Mode v2 / TCF signals, weak security headers and missing legal pages. The free scanner works on every platform because it reads what browsers read — no plugin or server access. The current $79/year-per-website Pro license is for WordPress document tools; hosted monitoring and runtime PDF reports are not included today.

**First comment (maker's):**
We built the scanner for agencies and small teams that get asked "are we compliant?" and currently answer with a spreadsheet. Paste a URL and get a prioritised technical result in seconds. The core is open source (MIT), so you can self-host the scanner. The current Pro license is for editable WordPress document starters and an HTML report from the latest WordPress scan — not continuous hosted monitoring or client-ready PDFs.

**Topics:** compliance, gdpr, web, developer tools, saas

---

## Reddit-r/darknetplan nej — r/msp og r/webdev-variant

**Subreddit:** r/msp eller r/webdev (som kommentar/selvpost efter sub-regler)

**Titel:** Free tool: run a quick GDPR/EAA compliance sanity-check on any client site

**Tekst:**
I keep seeing MSPs and freelancers asked by clients "is our website GDPR-ok?" and the honest answer usually requires a consultant. I built a free scanner that checks the mechanical parts in seconds: consent banner before trackers, Google Consent Mode v2 signals, IAB TCF, security headers, presence of privacy/imprint/accessibility pages.

Works on any CMS since it just fetches the page like a browser: https://eucomplypro.com/scan/

The Node core is MIT on GitHub if you'd rather run it yourself. Not a legal opinion — it's a technical smoke test so you know where the gaps are before anyone paid gets involved. Feedback welcome, especially false positives/negatives.
