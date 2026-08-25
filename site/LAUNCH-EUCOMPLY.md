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

The paid tier ($79/yr) adds continuous monitoring, PDF reports you can hand to a client or auditor, and report white-labeling — aimed at agencies that run these checks for customers.

Happy to answer questions about the detection heuristics or the false-positive trade-offs of header-only scanning.

---

## Product Hunt

**Navn:** EUComply Pro

**Tagline (max 60 tegn):**
Website compliance scans for GDPR, DSA & EAA — any CMS

**Description:**
EUComply scans any website for compliance gaps regulators actually fine for: missing consent before tracking, absent Consent Mode v2 / TCF signals, weak security headers, missing legal pages. Works on every platform because it reads what browsers read — no plugins, no server access. Free instant scan; $79/yr Pro adds monitoring, branded PDF reports and an API.

**First comment (maker's):**
We built this for agencies and small teams who get asked "are we compliant?" and currently answer with a spreadsheet. Paste a URL, get a prioritized report in seconds. The core is open source (MIT), so you can self-host the scanner — Pro is for people who want it running continuously with client-ready PDFs. Ask us anything about what the scanner can and can't see.

**Topics:** compliance, gdpr, web, developer tools, saas

---

## Reddit-r/darknetplan nej — r/msp og r/webdev-variant

**Subreddit:** r/msp eller r/webdev (som kommentar/selvpost efter sub-regler)

**Titel:** Free tool: run a quick GDPR/EAA compliance sanity-check on any client site

**Tekst:**
I keep seeing MSPs and freelancers asked by clients "is our website GDPR-ok?" and the honest answer usually requires a consultant. I built a free scanner that checks the mechanical parts in seconds: consent banner before trackers, Google Consent Mode v2 signals, IAB TCF, security headers, presence of privacy/imprint/accessibility pages.

Works on any CMS since it just fetches the page like a browser: https://eucomplypro.com/scan/

The Node core is MIT on GitHub if you'd rather run it yourself. Not a legal opinion — it's a technical smoke test so you know where the gaps are before anyone paid gets involved. Feedback welcome, especially false positives/negatives.
