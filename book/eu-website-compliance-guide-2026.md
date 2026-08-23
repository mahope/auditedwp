# EU Website Compliance Guide 2026

## The Practical Handbook for Website Owners Serving EU Visitors

**By EUComply**

---

*Disclaimer: This guide provides practical compliance information based on current EU regulations. It does not constitute legal advice. For high-risk compliance decisions, consult a qualified attorney licensed in your jurisdiction.*

---

# Table of Contents

1. [Introduction: Why Compliance Matters](#1)
2. [GDPR Fundamentals for Websites](#2)
3. [Cookie Consent — What the Law Actually Requires](#3)
4. [Privacy Policy — The Art. 13 Checklist](#4)
5. [Imprint / Legal Notice (Impressum)](#5)
6. [Security Headers — Technical Compliance](#6)
7. [Third-Party Trackers — Google, Meta, and Beyond](#7)
8. [European Accessibility Act (EAA) 2025](#8)
9. [NIS2 and DORA — Resilience Requirements](#9)
10. [Email Compliance — SPF, DKIM, DMARC](#10)
11. [Compliance by Platform — Quick Reference](#11)
12. [Maintaining Compliance — Monthly Checklist](#12)
13. [Tools and Resources](#13)
14. [Appendix: Regulation Overview Table](#14)

---

# 1. Introduction: Why Compliance Matters

Every website that reaches users in the European Union falls under EU law — regardless of where the site owner lives. This is not hypothetical. Since the General Data Protection Regulation (GDPR) took effect in 2018, regulators across all 27 member states have issued hundreds of millions of euros in fines.

But here is what the headlines don't tell you: **most fines are avoidable.** The majority of enforcement actions target basic failures — no privacy policy, no cookie consent, no imprint. These are not complex issues. They are gaps that can be fixed in a single afternoon.

This guide walks you through exactly what your website needs, regulation by regulation, in plain English. No legalese. No "it depends" rabbit holes. Every chapter ends with an actionable checklist you can run against your own site.

## What has changed in 2026

Three major regulatory developments have reshaped compliance requirements this year:

1. **European Accessibility Act (EAA)** — full enforcement began June 28, 2025. Websites serving EU consumers must meet WCAG 2.1 Level AA standards. This is now law, not a recommendation.

2. **NIS2 Directive** — transposed into national law across EU member states. If you provide digital services (hosting, SaaS, online marketplaces), you likely fall under its incident reporting and security requirements.

3. **DORA (Digital Operational Resilience Act)** — applies to financial sector entities and their ICT providers, but its spillover effects reach any business that processes financial data.

**The bottom line:** compliance in 2026 is broader than GDPR alone. A website that only handles cookies but ignores accessibility or security headers is exposed.

## How to use this guide

This book is designed as a workbook. Read it cover to cover once, then return to individual chapters as you work through each requirement. Each chapter ends with:

- A **checklist** you can tick off for your own site
- A **common mistake** to avoid
- A **free tool** reference to verify your work

Where you see references to the EUComply scanner (https://auditedwp.pages.dev/scan/), these are genuinely free tools that check the technical requirements described in that chapter — you can verify your progress without signing up or paying anything.

Let's begin.

---

# 2. GDPR Fundamentals for Websites

The GDPR (Regulation (EU) 2016/679) is the foundation of EU website compliance. Everything else — cookie laws, ePrivacy, accessibility — builds on top of it.

## Key principles that affect your website

### Lawfulness, fairness, and transparency (Art. 5(1)(a))

Every processing of personal data must have a legal basis. For most websites, this is either:

- **Consent** — for cookies, tracking, marketing emails
- **Legitimate interest** — for security measures, basic analytics
- **Contractual necessity** — for processing orders, accounts

### Purpose limitation (Art. 5(1)(b))

You must specify why you collect data before you collect it. A sign-up form that says "Subscribe to our newsletter" cannot then use that email for unrelated marketing without fresh consent.

### Data minimisation (Art. 5(1)(c))

Only collect what you actually need. A contact form that requires a phone number when an email address would suffice is likely excessive.

### Storage limitation (Art. 5(1)(e))

Delete data when you no longer need it. Newsletter subscriber lists should be cleaned annually.

## What this means for your website in practice

| Requirement | What to do |
|-------------|------------|
| Transparent data collection | Privacy policy on every page (footer link) |
| Consent for cookies | Cookie consent banner before any non-essential scripts |
| Lawful processing | Document your legal basis for each data processing activity |
| Data subject rights | Process for access, rectification, erasure requests |
| Data breach notification | Procedure for notifying DPA within 72 hours |
| DPA (Art. 28) | Signed data processing agreement with every third-party service that processes your users' data |

## The one thing most site owners miss

The **Data Processing Agreement (DPA)** required by Art. 28 is often overlooked. Every service you use that processes personal data on your behalf — web hosts, email platforms, analytics providers, CDNs — needs a signed DPA. Most major providers (Cloudflare, Google, Shopify) offer these in your account dashboard.

**Chapter 2 checklist:**
- [ ] Privacy policy published and linked from every page footer
- [ ] Cookie consent banner active before tracking scripts
- [ ] Legal basis documented for all data processing
- [ ] DPAs signed with all third-party processors
- [ ] Data subject request procedure documented
- [ ] Breach notification procedure documented

**Common mistake:** Assuming a template privacy policy is sufficient without customising it to your actual data processing activities. A generic policy that lists services you don't use (or omits ones you do) is worse than none — it is misleading.

---

# 3. Cookie Consent — What the Law Actually Requires

This is the most visible compliance requirement for most website owners, and also the most misunderstood.

## The legal framework

Cookie consent is governed by **ePrivacy Directive** (2002/58/EC, updated 2009), implemented differently by each member state. The GDPR's definition of consent (Art. 4(11) and Art. 7) adds additional requirements: consent must be freely given, specific, informed, and unambiguous.

## What valid consent looks like

| Element | Requirement |
|---------|-------------|
| **Prior** | Consent must be obtained before any non-essential script runs |
| **Active** | Pre-ticked checkboxes are illegal. User must take affirmative action |
| **Granular** | Users can accept/reject different cookie categories separately |
| **Informed** | Each category must be clearly described |
| **Revocable** | Withdrawing consent must be as easy as giving it |
| **Recorded** | You must store proof of consent (timestamp, user ID, consent string) |

## The Google Consent Mode v2 requirement

From March 2024, Google requires Consent Mode v2 for all advertising and measurement products. Without it, your Google Ads, Analytics, and Conversion Tracking lose modelling data. For EU sites this is effectively mandatory if you use any Google marketing tools.

## Consent Management Platforms (CMPs)

Do not build your own cookie banner. Use a CMP:

| CMP | Free tier | Annual pricing | Notes |
|-----|-----------|----------------|-------|
| Cookiebot | Up to 100 pages | €12-49/mo | Industry leader, automatic scanning |
| Osano | Limited free | $99-499/mo | Also handles privacy policy |
| CookieYes | Up to 100 pages | $10-69/mo | Good for small sites |
| Finsweet (Webflow) | Free via Webflow | Free | Webflow-only, basic |

## Implementation checklist

1. Install your chosen CMP on every page (head tag)
2. Move ALL tracking scripts (Google Analytics, Meta Pixel, LinkedIn, Hotjar, etc.) into the CMP
3. Configure cookie categories: Necessary, Preferences, Statistics, Marketing
4. Set default consent state to "denied" for all non-essential categories
5. Enable Google Consent Mode v2 if using Google services
6. Record consent for each user (CMP handles this)
7. Add a "Cookie Settings" link in your footer
8. Test: open your site in incognito mode — no scripts should run before consent

**Chapter 3 checklist:**
- [ ] CMP installed before all tracking scripts
- [ ] All non-essential scripts blocked until consent
- [ ] Granular cookie categories configured
- [ ] Google Consent Mode v2 active (if applicable)
- [ ] Consent record stored per user
- [ ] Cookie settings link in footer
- [ ] Tested in incognito mode

**Common mistake:** Installing the CMP script in the page but keeping tracking scripts in the HTML outside the CMP's control. The scripts still fire. Everything must move into the CMP.

---

# 4. Privacy Policy — The Art. 13 Checklist

Article 13 of the GDPR specifies exactly what information your privacy policy must contain. This is not a suggestion — each item is a legal requirement.

## Mandatory information (Art. 13(1))

1. **Identity and contact details** of the data controller (your business name, address, email)
2. **Contact details of your Data Protection Officer** (if applicable)
3. **Purposes and legal basis** for each processing activity
4. **Legitimate interests** pursued (if relying on legitimate interest as basis)
5. **Recipients** of personal data (third parties you share data with)
6. **International transfers** — if data is transferred outside the EU/EEA

## Mandatory information (Art. 13(2))

7. **Retention period** or criteria used to determine it
8. **Data subject rights** — access, rectification, erasure, restriction, portability, objection
9. **Right to withdraw consent** at any time (if processing is based on consent)
10. **Right to complain** to a supervisory authority
11. **Whether providing data is a contractual requirement** and consequences of not providing it
12. **Automated decision-making** including profiling, meaningful information about the logic involved

## Where your privacy policy goes

- Link in the **footer of every page** (not just the homepage)
- Link in the **cookie consent banner**
- Link in **account sign-up** forms
- Link in **checkout** pages

## Free privacy policy generators

- EUComply Privacy Policy Generator: https://auditedwp.pages.dev/privacy-policy-generator/
- TermsFeed: privacy policy + terms of service
- Iubenda: comprehensive legal generator

**Important:** A generated policy is a starting point. You must review it and customise it to match your actual data processing. Run a scan on your site (https://auditedwp.pages.dev/scan/) to verify your privacy policy link is properly placed and accessible.

**Chapter 4 checklist:**
- [ ] All 12 Art. 13 items present in privacy policy
- [ ] Controller identity and contact details listed
- [ ] All processing purposes and legal bases documented
- [ ] All third-party recipients listed
- [ ] International transfer mechanisms documented
- [ ] Data subject rights section present
- [ ] Privacy policy linked from every page footer
- [ ] Privacy policy linked in cookie banner
- [ ] Privacy policy linked in sign-up/checkout forms

**Common mistake:** Writing a privacy policy that says "we may collect data such as name, email, and address" without actually listing which specific services collect what. Be specific: "Shopify processes your payment data; Mailchimp stores your email for newsletters; Google Analytics collects browsing behaviour."

---

# 5. Imprint / Legal Notice (Impressum)

An imprint (Impressum) is a legal requirement in Germany (§ 5 DDG / § 5 TMG), Austria, and Switzerland for commercial websites. If you serve customers in these countries, you need one.

## What an imprint must contain

1. **Business name** and legal form (e.g. "John Smith trading as Smith Consulting")
2. **Full physical address** (not a PO box)
3. **Contact information** — email address and phone number
4. **Commercial register** entry (if registered) — register number and court
5. **VAT ID** (if applicable)
6. **Managing directors / authorised representatives** (for companies)
7. **Professional licensing** details (for regulated professions)

## Where it goes

- Separate page: yourdomain.com/imprint/
- Linked from every page footer
- Easily accessible within two clicks from any page

**Chapter 5 checklist:**
- [ ] Imprint page published
- [ ] Business name and legal form listed
- [ ] Full physical address included
- [ ] Email and phone listed
- [ ] Commercial register details (if applicable)
- [ ] VAT ID (if applicable)
- [ ] Linked from every page footer

**Common mistake:** Using a PO box or virtual office address. German law requires a "substantial physical address" where legal documents can be served.

---

# 6. Security Headers — Technical Compliance

Technical security measures are required by GDPR Art. 32 (security of processing), NIS2 (risk management), and DORA (ICT risk management). Security headers are the easiest way to demonstrate implementation.

## Essential headers

| Header | Purpose | Recommended value |
|--------|---------|-------------------|
| **Strict-Transport-Security** | Forces HTTPS connections | `max-age=31536000; includeSubDomains; preload` |
| **Content-Security-Policy** | Prevents XSS and data injection | Restrict script sources to trusted domains |
| **X-Frame-Options** | Prevents clickjacking | `DENY` or `SAMEORIGIN` |
| **X-Content-Type-Options** | Prevents MIME sniffing | `nosniff` |
| **Referrer-Policy** | Controls referrer information | `strict-origin-when-cross-origin` |
| **Permissions-Policy** | Restricts browser features | Disable camera, mic, geolocation unless needed |

## Email authentication headers

Required by DORA and increasingly enforced by mail providers:

| Record | Purpose |
|--------|---------|
| **SPF** | Authorises which servers can send email for your domain |
| **DKIM** | Digital signature verifying email integrity |
| **DMARC** | Policy for unauthenticated email (quarantine/reject) |

## How to verify

Run your site through the free EUComply scanner at https://auditedwp.pages.dev/scan/ — it checks all security headers and email authentication records.

**Chapter 6 checklist:**
- [ ] HTTPS enabled (SSL certificate valid)
- [ ] HSTS header with `includeSubDomains`
- [ ] Content-Security-Policy configured
- [ ] X-Frame-Options: DENY or SAMEORIGIN
- [ ] X-Content-Type-Options: nosniff
- [ ] Referrer-Policy set
- [ ] SPF record published
- [ ] DKIM record published
- [ ] DMARC record published (at least p=none, ideally p=quarantine)

**Common mistake:** Setting HSTS without `includeSubDomains` and `preload`, or setting a short `max-age`. Use `max-age=31536000` (one year) for full protection.

---

# 7. Third-Party Trackers — Google, Meta, and Beyond

Third-party trackers are the most common compliance failure on websites. Every script that loads from an external domain and processes user data requires a legal basis.

## Common trackers and their data processing

| Service | Data collected | Legal basis required |
|---------|---------------|---------------------|
| Google Analytics | IP, behaviour, device data | Consent |
| Google Ads / Conversion | Purchase/conversion data | Consent |
| Meta Pixel | Visits, purchases, device | Consent |
| LinkedIn Insight Tag | Visits, job title, company | Consent |
| Hotjar | Session recordings, clicks | Consent |
| Facebook/Meta CAPI | Server-side conversion data | Consent |
| TikTok Pixel | Visits, engagement | Consent |
| Reddit Pixel | Visits, conversions | Consent |

## Server-side vs client-side tracking

**Client-side:** Script runs in the browser. Easier to block via CMP, but still fires on the user's device.

**Server-side:** Data sent from your server directly (e.g., Meta Conversions API, Google Analytics 4 Measurement Protocol). Harder to block because the CMP in the browser cannot control server-to-server requests.

**If you implement server-side tracking, you must also implement server-side consent management** — the CMP communicates consent decisions to your server, which then decides whether to forward data to tracking endpoints.

## Google Consent Mode v2 — mandatory

If you use any Google service (Analytics, Ads, Campaign Manager, Floodlight), you must implement Consent Mode v2. Without it:

- Conversion modelling is disabled
- Remarketing lists stop populating
- Analytics data loses modelling

**Implementation:** Your CMP must support Consent Mode v2 and pass `ad_storage`, `ad_user_data`, `ad_personalization`, and `analytics_storage` consent signals to the Google tag.

**Chapter 7 checklist:**
- [ ] All third-party trackers documented
- [ ] Each tracker has a legal basis (usually consent)
- [ ] All trackers moved inside CMP
- [ ] Server-side tracking (if used) respects consent signals
- [ ] Google Consent Mode v2 implemented (if using Google services)
- [ ] IAB TCF implemented (if using programmatic ads)
- [ ] Tested: no tracker fires before consent in incognito mode

**Common mistake:** Moving Google Analytics into the CMP but forgetting about server-side Meta CAPI calls. The browser banner can't block server-to-server requests — you need server-side consent logic.

---

# 8. European Accessibility Act (EAA) 2025

The EAA (Directive (EU) 2019/882) took full effect on **June 28, 2025**. It requires products and services sold in the EU — including websites — to meet accessibility standards.

## What it requires

The EAA references **EN 301 549**, which aligns with **WCAG 2.1 Level AA**. Key requirements:

| Principle | What it means | Example |
|-----------|---------------|---------|
| **Perceivable** | Information must be presentable to all users | Alt text on images, captions on videos |
| **Operable** | UI components must be usable | Keyboard navigation, enough time to read content |
| **Understandable** | Content must be readable | Clear language, predictable navigation |
| **Robust** | Content must work with assistive tech | Proper HTML semantics, ARIA labels |

## Who is affected

The EAA applies to any business selling digital products or services in the EU:

- E-commerce websites
- Banking services
- E-books and digital publishing
- Online marketplaces
- Communication services (messaging, email)
- Access to audio-visual media services

Small businesses (fewer than 10 employees and annual turnover under €2 million) face lighter requirements but are not exempt.

## Practical steps for EAA compliance

1. **Run an automated accessibility check** — tools like WAVE, axe DevTools, or Lighthouse
2. **Fix colour contrast** — minimum 4.5:1 for normal text, 3:1 for large text
3. **Add alt text** to every image
4. **Ensure keyboard navigation** — can you tab through your entire site?
5. **Structure headings correctly** — h1 → h2 → h3, not skipping levels
6. **Label all form fields** — each input needs a `<label>` element
7. **Provide captions** for video content
8. **Published accessibility statement** (required by EN 301 549)

**Chapter 8 checklist:**
- [ ] Automated accessibility audit run
- [ ] Colour contrast meets WCAG 2.1 AA
- [ ] Alt text on all meaningful images
- [ ] Full keyboard navigation possible
- [ ] Correct heading hierarchy
- [ ] All form fields labelled
- [ ] Video captions provided
- [ ] Accessibility statement published

**Common mistake:** Assuming an automated audit is sufficient. Automated tools catch ~30% of accessibility issues. Manual testing with screen readers (VoiceOver, NVDA) is essential.

---

# 9. NIS2 and DORA — Resilience Requirements

The NIS2 Directive (Directive (EU) 2022/2555) and DORA (Regulation (EU) 2022/2554) extend compliance beyond data protection into operational resilience.

## NIS2 — Who is affected

NIS2 applies to "essential" and "important" entities:

| Sector | Examples |
|--------|----------|
| Digital infrastructure | DNS providers, cloud computing, data centres |
| Digital providers | Online marketplaces, search engines, social media |
| Managed security | MSSPs, incident response providers |
| Hosting | Web hosting, email hosting |

If you operate a SaaS platform, hosting service, or online marketplace that serves EU customers, you likely fall under NIS2.

## NIS2 requirements

1. **Risk management measures** — documented cybersecurity policies
2. **Incident reporting** — report significant incidents within 24 hours (early warning), 72 hours (notification), and 1 month (final report)
3. **Supply chain security** — assess security of vendors and third-party services
4. **Security training** — regular cybersecurity training for employees
5. **Encryption** — data encrypted at rest and in transit
6. **Access control** — multi-factor authentication, principle of least privilege
7. **Business continuity** — backup and disaster recovery plans

## DORA — Financial sector (and their ICT providers)

DORA applies to financial entities (banks, insurers, investment firms) AND their ICT third-party providers. If you provide software, hosting, or data processing to a financial entity, DORA requirements flow down to you.

## Practical steps for NIS2/DORA readiness

1. **Enable MFA** on all administrative accounts
2. **Encrypt data** at rest (database) and in transit (TLS)
3. **Implement logging and monitoring** — know when something changes
4. **Document supplier security** — which third parties have access to what?
5. **Create an incident response plan** — who gets called, when, and how
6. **Run backups** — automated, tested monthly, stored separately
7. **Verify email security** — SPF, DKIM, DMARC (see Chapter 6)

**Chapter 9 checklist:**
- [ ] MFA enabled on all admin accounts
- [ ] Data encryption at rest and in transit
- [ ] Incident response plan documented
- [ ] Supplier security assessment completed
- [ ] Backups configured and tested
- [ ] Email authentication (SPF, DKIM, DMARC) active
- [ ] Security incident reporting procedure documented

**Common mistake:** Assuming NIS2 doesn't apply because "we're small." If you provide digital services — even a simple SaaS — across EU borders, NIS2 likely applies. The threshold is lower than most business owners expect.

---

# 10. Email Compliance — SPF, DKIM, DMARC

Email is often overlooked in compliance audits, but it is a critical requirement for three reasons:

1. **DORA** explicitly requires email authentication for financial communications
2. **GDPR Art. 32** — security of processing includes authenticating communication channels
3. **DMARC enforcement** — Google and Yahoo require DMARC for bulk senders (2024 onwards)

## SPF (Sender Policy Framework)

Publishes a list of servers authorised to send email for your domain. Without SPF, anyone can send email appearing to come from your domain (spoofing).

```
example.com  TXT  "v=spf1 include:_spf.google.com include:spf.mailchimp.com ~all"
```

## DKIM (DomainKeys Identified Mail)

Cryptographically signs outgoing email so recipients can verify the email was not tampered with. Set up through your email provider (Google Workspace, Mailchimp, SendGrid, etc.)

## DMARC (Domain-based Message Authentication, Reporting & Conformance)

Tells receiving servers what to do when an email fails SPF or DKIM:

| Policy | Meaning |
|--------|---------|
| `p=none` | Monitor only — no action taken |
| `p=quarantine` | Put in spam folder |
| `p=reject` | Reject the email entirely |

Start with `p=none`, monitor reports for 2-4 weeks, then move to `p=quarantine`.

**Chapter 10 checklist:**
- [ ] SPF record published for your domain
- [ ] DKIM key paired with your email provider
- [ ] DMARC record published (start with p=none)
- [ ] DMARC reporting enabled (rua= address)
- [ ] Tested with a mail authentication checker

**Common mistake:** Publishing multiple SPF records. You can only have ONE SPF record per domain. Include multiple services by adding them to the `include:` list within the single record.

---

# 11. Compliance by Platform — Quick Reference

Different website platforms have different compliance requirements and capabilities. This chapter provides platform-specific guidance.

## WordPress

| Requirement | How to handle |
|-------------|---------------|
| Cookie consent | Cookiebot or CookieYes plugin |
| Privacy policy | Built-in privacy page + WP's privacy checklist |
| Security headers | Wordfence + Sucuri or manual .htaccess |
| EAA (accessibility) | WP Accessibility plugin + accessible theme |
| DPA | DPA available in WordPress.com or via hosting provider |

## Shopify

| Requirement | How to handle |
|-------------|---------------|
| Cookie consent | Shopify's built-in cookie banner (limited) or Cookiebot app |
| Privacy policy | Shopify generates one based on your settings |
| Security headers | Shopify handles server-level security. SSL by default |
| EAA | Use an accessible theme (Dawn is a good start) |
| DPA | Available in your Shopify admin under Settings → Legal |

## Webflow

| Requirement | How to handle |
|-------------|---------------|
| Cookie consent | Add via Custom Code (head) — Finsweet for Webflow-native |
| Privacy policy | CMS page → link in footer |
| Security headers | Webflow handles SSL. HSTS and other headers via Pro plan |
| EAA | Check Webflow's accessibility checker in the Designer |
| DPA | Available in Account Settings → Billing → DPA |

## Squarespace

| Requirement | How to handle |
|-------------|---------------|
| Cookie consent | Built-in cookie banner (Settings → Cookies) |
| Privacy policy | Built-in privacy page template |
| Security headers | Handled by Squarespace infrastructure |
| EAA | Squarespace templates are generally accessible |
| DPA | Available in account settings |

## Wix

| Requirement | How to handle |
|-------------|---------------|
| Cookie consent | Wix built-in cookie banner |
| Privacy policy | Wix privacy policy generator |
| Security headers | Handled by Wix |
| EAA | Wix Accessibility Wizard |
| DPA | Request from Wix support |

## Custom-built (Next.js, static HTML, etc.)

| Requirement | How to handle |
|-------------|---------------|
| Cookie consent | Cookiebot script in the HTML `<head>` |
| Privacy policy | Static page, link in footer |
| Security headers | Configure in your hosting platform (Cloudflare, Vercel, Netlify) |
| EAA | Manual WCAG audit required |
| DPA | Sign DPA with your hosting provider |

**Chapter 11 checklist:**
- [ ] Platform-specific compliance configured
- [ ] Cookie consent working on your platform
- [ ] Security headers appropriate for your stack
- [ ] DPA signed with your platform provider
- [ ] Accessibility checked for your platform

---

# 12. Maintaining Compliance — Monthly Checklist

Compliance is not a one-time project. Regulations change, your site changes, and third-party services change. A monthly check keeps you protected.

## Monthly tasks (15 minutes)

- [ ] Run a compliance scan (https://auditedwp.pages.dev/scan/)
- [ ] Check SSL certificate expiry
- [ ] Review and remove unused tracking scripts
- [ ] Test cookie consent banner in incognito mode
- [ ] Check for new platform updates (Shopify, WordPress, Webflow)

## Quarterly tasks (1 hour)

- [ ] Review and update privacy policy
- [ ] Sign new DPAs for any new services
- [ ] Run full accessibility audit
- [ ] Review email authentication (DMARC reports)
- [ ] Check for new regulatory guidance from EU DPAs

## Annual tasks (2 hours)

- [ ] Full compliance audit across all regulations
- [ ] Update this guide's regulation references
- [ ] Review and purge outdated user data (GDPR Art. 5(1)(e))
- [ ] Renew SSL certificates if auto-renew not configured
- [ ] Review incident response plan
- [ ] Penetration test or vulnerability scan

**For automated monthly scanning**, consider EUComply Pro (https://auditedwp.pages.dev/pro/) which runs daily checks and alerts you when something changes.

---

# 13. Tools and Resources

## Free compliance scanners
- **EUComply Scanner** (free, no signup): https://auditedwp.pages.dev/scan/
- **SSL Labs**: https://www.ssllabs.com/ssltest/
- **Security Headers**: https://securityheaders.com/
- **DMARC Analyzer**: https://www.dmarcanalyzer.com/

## Accessibility tools
- **WAVE**: https://wave.webaim.org/
- **axe DevTools**: Browser extension
- **Lighthouse**: Built into Chrome DevTools
- **NVDA**: Free screen reader for Windows

## Consent management
- **Cookiebot**: https://www.cookiebot.com/
- **CookieYes**: https://www.cookieyes.com/
- **Osano**: https://www.osano.com/

## Legal resources
- **EU GDPR text**: https://eur-lex.europa.eu/eli/reg/2016/679/oj
- **NIS2 text**: https://eur-lex.europa.eu/eli/dir/2022/2555
- **DORA text**: https://eur-lex.europa.eu/eli/reg/2022/2554
- **EAA text**: https://eur-lex.europa.eu/eli/dir/2019/882

## Document generators (free)
- **EUComply generators**: https://auditedwp.pages.dev/tools/
- **TermsFeed**: https://www.termsfeed.com/
- **Iubenda**: https://www.iubenda.com/

---

# 14. Appendix: Regulation Overview Table

| Regulation | Full name | Effective | Scope | Max fine |
|------------|-----------|-----------|-------|----------|
| GDPR | General Data Protection Regulation (2016/679) | May 25, 2018 | Any entity processing EU personal data | €20M or 4% global turnover |
| ePrivacy | Directive on Privacy and Electronic Communications (2002/58/EC) | July 31, 2003 (updated 2009) | Electronic communications, cookies | Varies by member state |
| EAA | European Accessibility Act (2019/882) | June 28, 2025 | Digital products/services sold in EU | Varies by member state |
| NIS2 | Security of Network and Information Systems (2022/2555) | October 18, 2024 (transposition deadline) | Essential and important digital entities | €10M or 2% global turnover |
| DORA | Digital Operational Resilience Act (2022/2554) | January 17, 2025 | Financial entities and their ICT providers | 2% of average daily turnover or €1M |

---

*This guide was written in August 2026 by EUComply. Laws and regulations may have changed since publication. Always verify current requirements with your legal advisor.*

*For a free compliance scan of your website, visit https://auditedwp.pages.dev/scan/*

*For automated daily monitoring with alerts and PDF reports, visit https://auditedwp.pages.dev/pro/*

---

**End of guide.**