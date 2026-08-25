# The Website Compliance Handbook 2026

## GDPR, ePrivacy, NIS2 & Accessibility for European Small Business Owners

---

# Chapter 1: Why Website Compliance Matters in 2026

If you run a website that serves customers in the European Union — whether you're a freelancer, a small business owner, or running a growing e-commerce store — you're already subject to some of the world's most comprehensive digital regulations. The question is not whether these laws apply to you. It's whether you're ready for them.

## The Cost of Ignoring Compliance

The fines are not theoretical. In September 2025, a major e-commerce platform was fined €150 million by the French data protection authority CNIL for making it harder to reject cookies than to accept them. In Germany, a small web shop received a €50,000 administrative fine for operating without a proper Impressum — the mandatory legal notice required by German law. In the same year, a Dutch company was fined €10.5 million for failing to comply with a data subject access request.

These enforcement actions span the full range of business sizes, from solo entrepreneurs to multinational corporations. What they have in common is a straightforward regulatory principle: if your digital presence serves EU users, you are accountable for how that presence handles their data, their privacy, and their ability to access your services.

## Real Enforcement Cases That Affect Small Businesses

It is easy to assume that regulators only go after large corporations. The data tells a different story. Small and medium-sized businesses account for a significant portion of GDPR fines across Europe because they are more likely to lack basic compliance measures — a missing privacy policy, an unconsented analytics script, or an unsecured customer database.

A Spanish hotel was fined €5,000 for installing video surveillance that recorded common areas beyond what was necessary. A Romanian web design agency received a €3,000 fine for failing to respond to a data deletion request within the statutory 30-day window. A German online retailer was fined €12,000 because its checkout process transmitted customer data in plain text without encryption.

These enforcement actions are rarely initiated by regulators proactively. Most start with a customer complaint, a competitor report, or an automated scan performed by a privacy advocacy group. In Germany alone, over 300,000 GDPR-related complaints were filed between 2018 and 2025, and 15% of investigations resulted in fines.

## Fines at a Glance

| Regulation | Maximum Fine | Typical SME Range | Common Trigger |
|-----------|-------------|-------------------|----------------|
| GDPR | €20 million or 4% of global revenue | €2,000 — €100,000 | Missing privacy policy, no consent basis |
| ePrivacy Directive | Varies by member state | €5,000 — €150,000 | Non-compliant cookie banner |
| NIS2 | €10 million or 2% of revenue | Industry-specific | Inadequate security measures |
| EAA | Varies by member state | €5,000 — €50,000 | Inaccessible website |
| German Impressum law | Up to €50,000 | €500 — €50,000 | Missing or incomplete legal notice |

## What Has Changed in 2026

Three major regulatory shifts make 2026 the year to act on compliance.

**NIS2 is now in active enforcement.** The EU's updated Network and Information Security Directive became enforceable in October 2024, and by 2026 all member states have transposed it into national law. If you provide digital services, hosting, cloud computing, or SaaS, you may be classified as an "important entity" under the directive — with mandatory security measures, incident reporting obligations, and personal liability for management.

**The European Accessibility Act deadline has passed.** June 28, 2025, was the compliance deadline for most digital services under the EAA. If your website is not accessible to users with disabilities — including users who navigate by keyboard, use screen readers, or need high-contrast text — you are now outside the enforcement grace period. This is not an accessibility best-practice discussion anymore; it is a legal requirement with enforcement consequences.

**Cookie enforcement is accelerating across Europe.** The UK Information Commissioner's Office found that 564 of the UK's 1,000 largest websites failed basic cookie compliance checks in December 2025. National data protection authorities across the EU are transitioning from education-based enforcement (warnings and notices) to financial penalties. The Dutch DPA, the German DSK, and the French CNIL have each announced increased enforcement staffing for 2026 specifically focused on website compliance.

## The Business Case for Compliance

Beyond avoiding fines, compliance offers real business advantages:

- **Customer trust** — 73% of EU consumers say they are more likely to buy from a website that clearly explains how their data is used (European Consumer Survey, 2025)
- **Enterprise contracts** — Large companies increasingly require GDPR and security compliance documentation from their vendors as a condition of doing business
- **SEO benefits** — HTTPS, accessibility, and security headers are ranking signals for Google
- **Future-proofing** — The regulatory trend across Europe is toward more requirements, not fewer. Getting compliant now means you won't need a costly emergency response when the next directive comes into force

## Who This Book Is For

This handbook is written specifically for:

- **Small business owners** who need their website to comply with EU regulations without hiring a lawyer or a compliance consultant
- **Freelancers and consultants** running their own site or building sites for clients
- **E-commerce operators** on Shopify, WooCommerce, Magento, BigCommerce, or Squarespace
- **SaaS founders** who need to understand how NIS2, GDPR, and security requirements affect their platform and their customers
- **Web designers and agency owners** who need a practical, reference-able guide for client compliance projects

## What You Will Learn

By the end of this book, you will know:

1. Whether each regulation — GDPR, ePrivacy, NIS2, EAA — applies to your specific business
2. Exactly what you need to do to comply with each one: the minimum viable steps, nothing more, nothing less
3. How to implement each requirement in practice, with platform-specific instructions
4. Which tools and resources can help you maintain compliance on an ongoing basis
5. How to document your compliance so you can prove it if questioned

## How to Use This Book

Each chapter covers one regulation or compliance area. They are designed to work as standalone references, so you can jump directly to what you need. If you are starting from scratch, reading in order will give you a complete compliance framework.

Where a regulation does not apply to your specific situation, we will tell you clearly. The goal is practical, proportional compliance — not fear-driven over-investment.

---

# Chapter 2: GDPR — The Foundation

## Does GDPR Apply to You?

The General Data Protection Regulation applies to any organization that processes personal data of individuals located in the European Union — regardless of where the organization itself is based. This territorial scope is one of the most misunderstood aspects of GDPR.

If you have a website with any of the following, GDPR applies to you:

- A contact form that collects names and email addresses
- A newsletter signup that stores subscriber information
- Analytics tracking (Google Analytics, Matomo, Plausible, or any other tool)
- Customer accounts with saved addresses or payment information
- Cookies that collect personal data (which is most cookies)
- Any third-party scripts (social media buttons, remarketing pixels, chat widgets)

This means a US-based e-commerce store selling to EU customers is in scope. A UK business that still serves EU visitors through its website is in scope. A solo freelancer with a mailing list of fifty EU subscribers is in scope.

The size of your business does not matter. There is no small-business exemption in GDPR. The only proportional element is the fine calculation, which considers revenue — but the compliance obligations are the same whether you are a solopreneur or a multinational corporation.

## The Seven Principles

GDPR Article 5 establishes seven principles that govern every decision about personal data processing. Understanding these principles helps you make compliance decisions beyond just checking boxes.

### 1. Lawfulness, Fairness, and Transparency

You must have a valid legal basis for every piece of personal data you collect and process. The six legal bases are:

**Consent** — The user has given clear, affirmative consent for you to process their data for a specific purpose. This is the most common basis for marketing cookies, newsletter subscriptions, and non-essential tracking.

**Contractual necessity** — Processing is necessary to fulfill a contract with the user. This covers order processing, shipping information, and payment handling for e-commerce.

**Legal obligation** — You are required by law to process the data. This covers tax records, invoicing requirements, and regulatory reporting.

**Vital interests** — Processing is necessary to protect someone's life. Rarely relevant for website operators.

**Public task** — Processing is necessary for official authority functions. Not relevant for most businesses.

**Legitimate interests** — Processing is necessary for your legitimate business interests, provided they do not override the user's privacy rights. This can apply to fraud prevention, direct marketing (with opt-out), and network security — but you must document your legitimate interest assessment.

### 2. Purpose Limitation

You must collect data only for specified, explicit, and legitimate purposes, and you cannot process it further in ways that are incompatible with those purposes. In practice, this means: if you collect email addresses for a newsletter, you cannot use them for retargeting ads without obtaining separate consent for that purpose.

### 3. Data Minimization

You should collect only the personal data that is actually necessary for your stated purpose. If a contact form does not need a phone number, do not include a phone number field. If you do not need the user's date of birth to send them a newsletter, do not ask for it.

### 4. Accuracy

You must take reasonable steps to ensure personal data is accurate and kept up to date. Give users a way to update their information — a profile page, a reply-to-email mechanism, or a support channel.

### 5. Storage Limitation

You must not keep personal data longer than necessary for the purposes for which you collected it. This means establishing a data retention schedule: newsletter subscriber data is kept while the subscription is active and for a defined period after unsubscription; customer order data is kept for tax and warranty purposes and then anonymized.

### 6. Integrity and Confidentiality

You must process personal data securely, protecting it against unauthorized access, loss, or damage. This includes technical measures (HTTPS, encryption, access controls) and organizational measures (staff training, incident response procedures).

### 7. Accountability

You must be able to demonstrate your compliance with all of the above principles. This means maintaining documentation: a data processing register, consent records, data protection impact assessments where relevant, and written policies.

## What Your Website Needs Right Now

### Privacy Policy

Your privacy policy must disclose, in clear plain language:

- The identity and contact details of your organization
- The types of personal data you collect (names, emails, IP addresses, cookies, payment data)
- The purposes of processing (analytics, marketing, order fulfillment, customer support)
- The legal basis for each purpose (consent, contractual necessity, legitimate interest)
- Any recipients or categories of recipients (analytics providers, payment processors, hosting companies)
- Data retention periods for each category of data
- The user's rights (access, rectification, erasure, restriction, portability, objection)
- The right to withdraw consent at any time
- The right to lodge a complaint with a data protection authority
- Whether the data is transferred to a third country (e.g., US-based services like Google Analytics)
- How users can contact you about data protection matters

### Cookie Consent Mechanism

Non-essential cookies require prior consent. This requirement is covered in depth in Chapter 3.

### Data Subject Request Process

Users have eight specific rights under GDPR. You need a documented process for handling each one:

**Right to Access (Article 15):** Users can request a copy of all personal data you hold about them. You must respond within 30 days.

**Right to Rectification (Article 16):** Users can request correction of inaccurate data.

**Right to Erasure / "Right to be Forgotten" (Article 17):** Users can request deletion of their data when it is no longer necessary for the original purpose, or when they withdraw consent.

**Right to Restrict Processing (Article 18):** Users can request that you stop processing their data (but retain it) while a dispute is resolved.

**Right to Data Portability (Article 20):** Users can request their data in a machine-readable format (CSV, JSON) to transfer to another service.

**Right to Object (Article 21):** Users can object to processing based on legitimate interest or direct marketing.

**Rights related to automated decision-making (Article 22):** Users have the right not to be subject to decisions based solely on automated processing.

### Data Processing Register

If you have 250 or more employees, you are legally required to maintain a record of processing activities. Below 250 employees, you are exempt unless your processing poses a risk to individuals' rights, which it often does for e-commerce and analytics — so maintaining a register is still a best practice. It should list:

- What data you process
- Why you process it
- Where it is stored
- Who has access
- Retention periods
- Technical and organizational security measures

### Data Processing Agreements (DPAs)

You must have a DPA with every third-party service provider that processes personal data on your behalf. This includes:

- Hosting providers
- Analytics platforms
- Email marketing services
- Payment processors
- Cloud storage services
- Customer support platforms
- Any app or plugin that accesses your customer data

Most major providers (Shopify, Google, Mailchimp, Stripe) offer standard DPAs as part of their terms of service. You need to ensure these are signed and stored.

## Common GDPR Misconceptions

**"I'm too small to be fined."** Fines are proportional, but enforcement against SMEs is common. A single customer complaint can trigger an investigation, and the cost of responding to an investigation — legal fees, staff time, lost productivity — often exceeds the fine itself.

**"I only use Google Analytics."** Analytics cookies that track users across sessions require consent. Several EU data protection authorities — including the Austrian DPA, the French CNIL, and the Italian Garante — have found Google Analytics' standard configuration non-compliant with GDPR data transfer requirements.

**"My hosting is in the EU, so I'm compliant."** Hosting location does not determine GDPR applicability. If you serve EU users, GDPR applies regardless of where your servers are located.

**"I have a privacy policy, so I'm covered."** A privacy policy is one component of GDPR compliance, not the whole picture. You also need consent mechanisms, data subject request processes, DPAs, and documentation of your legal bases.

---

# Chapter 3: Cookie Consent & ePrivacy

## The Legal Framework

Cookie consent is governed by Article 5(3) of the ePrivacy Directive (Directive 2002/58/EC, as amended), often called the "Cookie Directive." Each EU member state transposed this directive into national law between 2009 and 2011, meaning the specific implementation varies slightly by country — but the core requirement is consistent across the EU.

GDPR adds the standard for what constitutes valid consent, through Article 7 (Conditions for consent) and Article 4(11) (Definition of consent). Together, these two regulations create a layered requirement: the ePrivacy Directive tells you WHEN consent is needed, and GDPR tells you HOW that consent must be obtained.

## When Consent Is Required

Consent is required for any cookie or tracking technology that is not **strictly necessary** for the service explicitly requested by the user.

### Cookies That Do Not Require Consent (Exempt)

The following types of cookies are generally considered exempt from consent requirements:

- Session cookies that maintain a shopping cart during a single browsing session
- Authentication cookies that remember a user's login status within a session
- Load-balancing cookies that distribute traffic across servers
- User-input cookies that remember form entries across a multi-step process
- Payment processing cookies that are active during checkout
- Security-focused cookies (rate limiting, CSRF protection, bot detection)

### Cookies That Always Require Consent

The following types of cookies require prior, informed consent before they are placed or read:

- **Analytics cookies** — Google Analytics, Adobe Analytics, Matomo (when tracking across sessions), Facebook Analytics, Hotjar, and similar tools
- **Marketing and advertising cookies** — Meta Pixel, Google Ads conversion tracking, TikTok Pixel, LinkedIn Insight Tag, Pinterest Tag, and all retargeting cookies
- **Social media cookies** — Facebook Share buttons, X/Twitter embedded timelines, Instagram embeds, LinkedIn share buttons, YouTube embedded video players (which set tracking cookies)
- **Personalization cookies** — Cookies that remember user preferences across browsing sessions (language preference, display settings) when they are not strictly necessary for service delivery
- **Third-party cookies** from any source — Any script or pixel that sends data to a third party for their own purposes

## The Legal Status of Google Analytics in the EU

Google Analytics has been the subject of multiple EU data protection authority rulings. In 2022, the Austrian DPA ruled that the use of Google Analytics violated GDPR because of data transfers to the US without adequate safeguards. Similar rulings followed from the French CNIL, the Italian Garante, and others.

This does not mean you cannot use Google Analytics at all, but it does mean:

- You must obtain consent before loading the Google Analytics tracking code
- You must have executed Google's updated Standard Contractual Clauses (SCCs) — these are included in your Google Analytics terms when you accept the data processing amendment
- You should enable IP anonymization (set `anonymizeIp: true` or use Google Consent Mode)
- You should consider Google Consent Mode V2 to pass consent signals from your CMP
- Privacy-preserving alternatives (Plausible, Fathom, Simple Analytics) avoid this issue entirely because they process no personal data

## Implementing a Compliant Cookie Banner

### Step 1: Choose a Consent Management Platform (CMP)

| Platform | Best For | Consent Type | Cookie Blocking | Auto-Scanning | Price |
|---------|---------|-------------|----------------|---------------|-------|
| Cookiebot | All platforms | Granular, multi-language | Yes (JavaScript) | Yes | Free for <50 pages, Pro from €12/mo |
| Klaro | Self-hosted sites | Granular, lightweight | Yes | No (manual setup) | Free, open source (MIT) |
| Tarteaucitron | Simple websites | Basic categories | Partial | Yes | Free, open source |
| Finsweet | Webflow sites | Granular | Yes | No | Free for Webflow |
| Complianz | WordPress | Full GDPR/ePrivacy | Yes | Yes | Free / Premium €45/yr |
| Osano | Enterprise | Full suite | Yes | Yes | From $30/mo |
| Didomi | Mid-market | Advanced | Yes | Yes | Custom pricing |
| Axeptio | E-commerce UX | Visual, UX-optimized | Yes | Yes | From €29/mo |

### Step 2: Configure the Banner

When setting up your CMP, ensure the following configuration:

1. **All cookie categories presented** — Necessary, Analytics, Marketing, Preferences (at minimum)
2. **Granular toggle for each category** — Not an all-or-nothing choice
3. **Reject All button equally prominent** as Accept All — Same color, same font size, same position
4. **Clear explanation per category** — What each category does, which cookies use it, and any third-party recipients
5. **"Learn more" link** to a detailed cookie policy page
6. **Language matching your site** — English for English sites, plus the language of your primary market
7. **Mobile responsive** — The banner must work on screens as small as 320px wide

### Step 3: Implement Blocking

Consent means nothing if cookies are set before the user makes a choice. Your CMP must block all non-essential cookies until the user gives consent. This typically works by:

- Replacing tracking scripts with placeholder elements that the CMP activates only after consent
- Using a callback function to load scripts dynamically when the user accepts a category
- For Google Tag Manager: integrating the CMP with GTM's consent overview so tags are blocked until consent signal is received

Do not rely on a "wait for page load then remove cookies" approach. By the time JavaScript removes cookies, the browser has already set them.

### Step 4: Document Consent

Every consent interaction must be recorded with:

- A unique identifier for the user (generated by the CMP, not linked to personal data)
- The timestamp of the consent action
- Exactly what the user consented to (which categories, which purposes)
- The user's IP address (for audit purposes, typically stored in anonymized form)
- The version of your cookie policy at the time of consent

Most commercial CMPs handle this automatically and provide a consent log export.

### Step 5: Provide Withdrawal

Users must be able to withdraw consent as easily as they gave it. This means:

- A visible "Cookie Settings" or "Revoke Consent" link in your website footer
- Clicking it re-opens the cookie banner with the user's current settings pre-selected
- Withdrawal is immediate — no script should continue loading after withdrawal

## Google Consent Mode V2

Since March 2024, Google requires Consent Mode V2 (the updated version) for all Google Ads and Google Analytics accounts serving traffic from the European Economic Area. This change is mandatory for compliance with Google's own EU Consent Policy, and failure to implement it may result in:

- Google Ads conversion tracking showing incomplete data for EEA users
- Google Analytics data gaps where user consent was not communicated
- Limited remarketing functionality

Consent Mode V2 works by passing four consent signals from your CMP to Google:

- `ad_storage` — consent for advertising cookies
- `ad_user_data` — consent for sending user data to Google
- `ad_personalization` — consent for personalized advertising
- `analytics_storage` — consent for analytics cookies

Your CMP must integrate with Google Consent Mode V2. Most major CMPs (Cookiebot, Osano, Complianz, CookieYes) support this natively.

---

# Chapter 4: NIS2 — The Network and Information Security Directive

## A New Standard for Digital Security

The NIS2 Directive (EU 2022/2555) represents the most significant expansion of EU cybersecurity law since the original NIS Directive in 2016. It came into effect on October 18, 2024, and member states were required to transpose it into national law by October 17, 2024. By 2026, enforcement is active across the EU.

NIS2 significantly broadens the scope of entities that must comply. If your business was outside the scope of the original NIS Directive, you may be inside the scope of NIS2.

## Is Your Business in Scope?

### Sector Classification

NIS2 divides covered entities into two categories with different compliance requirements:

**Essential entities** face the strictest requirements, including proactive supervision and pre-approval of security measures:

- Energy (electricity, oil, gas, district heating, hydrogen)
- Transport (air, rail, water, road)
- Banking and financial market infrastructure
- Health (hospitals, healthcare providers, pharmaceutical manufacturers)
- Drinking water supply and distribution
- Digital infrastructure (internet exchange points, DNS, TLD registries, cloud computing, data centers)
- ICT service management (managed service providers, managed security service providers)
- Public administration (central government entities)

**Important entities** face moderate requirements, including ex-post supervision:

- Digital providers (online marketplaces, online search engines, social networking platforms)
- Postal and courier services
- Waste management
- Manufacture, production, and distribution of chemicals
- Food production, processing, and distribution
- Manufacturing (medical devices, computer equipment, machinery, vehicles)
- Digital providers not classified as essential

### Size Thresholds

- **Large enterprises** (250+ employees or €50M+ annual revenue and €43M+ balance sheet): Full compliance required regardless of sector classification
- **Medium enterprises** (50-249 employees or €10M-€50M revenue): Compliance required in designated sectors
- **Small enterprises** (below 50 employees and below €10M revenue): Generally exempt unless specifically designated by a member state as important to national security

If your SaaS or digital service business has fewer than 50 employees and less than €10M in revenue, you are likely exempt from NIS2 — but you should still implement the security measures, because your enterprise customers will require them in their vendor assessments.

## What NIS2 Requires

### Risk Management Measures (Article 21)

NIS2 Article 21 requires organizations to implement "appropriate and proportionate technical, operational and organizational measures" to manage cybersecurity risks. These must cover:

- **Risk analysis and information system security policies** — Documented risk assessments identifying critical assets, threat vectors, and mitigation strategies
- **Incident handling** — Processes for detection, triage, containment, eradication, and recovery from security incidents
- **Business continuity management** — Disaster recovery plans, backup procedures, and system restoration capabilities
- **Supply chain security** — Security requirements for vendors, subcontractors, and service providers, including third-party risk assessments
- **Network and system security** — Secure acquisition, development, and maintenance of network and information systems
- **Vulnerability handling and disclosure** — A process for receiving, assessing, and remediating vulnerability reports
- **Policies and procedures for testing and auditing** — Regular security testing, including vulnerability scanning and penetration testing
- **Cryptography and encryption** — Use of strong encryption for data in transit and at rest

### Incident Reporting Requirements (Article 23)

Significant cybersecurity incidents must be reported through a structured process:

1. **Early warning** — Within 24 hours of becoming aware of the incident, submit an initial notification
2. **Incident notification** — Within 72 hours, submit a full notification with initial assessment, severity, and indicators of compromise
3. **Intermediate report** — Upon request from the CSIRT (Computer Security Incident Response Team), provide status updates
4. **Final report** — Within one month of the incident, submit a detailed report including root cause analysis, impact assessment, and remediation measures

An incident is considered "significant" if it causes or is capable of causing severe operational disruption or financial loss to the entity.

### Management Accountability (Article 20)

One of the most significant provisions of NIS2 is personal liability for management. Senior management is:

- Required to approve the cybersecurity risk management measures
- Personally accountable for compliance failures
- Subject to liability for violations in some member states
- Required to undergo cybersecurity training

This is not theoretical — several member states have implemented management liability provisions that can result in personal fines for directors who fail to ensure adequate cybersecurity measures.

## Practical Steps for Small Digital Businesses

Even if you are below the NIS2 size threshold, these steps are increasingly required by enterprise customers and insurance providers.

### 1. Document Your Risk Assessment

Start with a straightforward risk assessment document that answers:

- What are our critical digital assets? (website, database, customer data, proprietary code)
- What threats do we face? (data breach, DDoS, ransomware, insider threat, supply chain attack)
- What is our current security posture? (HTTPS, encryption, access controls, backup procedures)
- What gaps exist? (missing security headers, no vulnerability scanning, no incident plan)

### 2. Implement Baseline Security Measures

These measures are required under NIS2 and recommended for all websites regardless of size:

- **HTTPS with HSTS** — All pages must serve over HTTPS. HTTP Strict Transport Security ensures browsers always connect securely
- **Security headers** — Content-Security-Policy, X-Frame-Options, X-Content-Type-Options, Referrer-Policy
- **Multi-factor authentication** — For all administrative access to your website, hosting, and cloud services
- **Regular patching** — A documented process for applying security updates to your CMS, plugins, libraries, and server software
- **Backup and recovery** — Automated daily backups with tested restoration procedures
- **Access control** — Principle of least privilege for all user accounts

### 3. Create an Incident Response Plan

A basic incident response plan should document:

- Who is on the incident response team (even if it is just you)
- How incidents are reported internally (email, phone tree, Slack channel)
- The incident classification system (low/medium/high/critical)
- Containment procedures (disconnect affected systems, rotate credentials)
- Recovery procedures (restore from backup, verify no persistent access)
- Notification procedures (customers, regulators, law enforcement)
- Post-incident review process

### 4. Review Your Supply Chain

Every third-party service you use is a potential vector for security incidents. For each vendor, ask:

- Do they have a published security policy?
- Do they offer a DPA or terms that address data security?
- Do they undergo independent security audits (SOC 2, ISO 27001)?
- What would happen to our data if they suffered a breach?

---

# Chapter 5: The European Accessibility Act

## Understanding the EAA

The European Accessibility Act (Directive 2019/882) establishes EU-wide accessibility requirements for products and services. For digital businesses, the most relevant provisions concern websites, mobile applications, and e-commerce platforms.

The compliance deadline for most products and services was June 28, 2025. If your website or e-commerce store was operational after this date and serves EU customers, you are subject to the EAA's requirements.

## Who Must Comply

The EAA applies to any organization placing products or services on the EU market after the compliance deadline. This includes:

- E-commerce websites selling products or services to EU consumers
- Online booking platforms (travel, accommodation, events)
- Banking and financial service websites
- E-books and digital content platforms
- Air, bus, rail, and waterborne passenger transport services
- Emergency services communication systems

### Exemptions

The only categorical exemption is for **microenterprises** — businesses with fewer than 10 employees and annual turnover or balance sheet below €2 million — when providing services. However, if a microenterprise operates an e-commerce platform, accessibility is still considered a best practice and is increasingly expected by customers.

## WCAG 2.1 Level AA — What It Means

The EAA references the Web Content Accessibility Guidelines (WCAG) 2.1 Level AA as the technical compliance standard. WCAG is organized around four principles, with testable success criteria at three levels (A, AA, AAA).

### Principle 1: Perceivable

Information and user interface components must be presentable to users in ways they can perceive.

**Level A requirements:**
- All non-text content has a text alternative (alt text for images, transcripts for audio)
- Captions are provided for synchronized media (video with audio)
- Audio descriptions or full-text alternatives are provided for prerecorded video
- Content does not rely solely on sensory characteristics (shape, size, color)

**Level AA requirements:**
- Live audio has captions
- Color is not the only means of conveying information (an icon or text label must accompany color indicators)

### Principle 2: Operable

User interface components and navigation must be operable by all users.

**Level A requirements:**
- All functionality is available from a keyboard
- Users are given enough time to read and use content (adjustable or extendable time limits)
- Content does not flash more than three times per second
- A mechanism is provided to bypass blocks of content (skip navigation link)
- Page titles describe the topic or purpose
- Focus order preserves meaning and operability
- Link purpose is determinable from the link text alone

**Level AA requirements:**
- Multiple ways are available to find content on a site (search, sitemap, navigation menu)
- Headings and labels describe topic or purpose
- Focus indicators are visible (clearly visible keyboard focus)
- Navigation is consistent across pages

### Principle 3: Understandable

Information and the operation of the user interface must be understandable.

**Level A requirements:**
- The language of each page is programmatically determinable (declare `lang` attribute on `<html>`)
- When a component receives focus, it does not initiate an unexpected change (no automatic page refresh, new window, or form submission on focus)
- Error messages are provided when input validation fails

**Level AA requirements:**
- The language of parts of a page can be determined (for content in a different language, declare `lang` on the containing element)
- Navigation that is repeated across pages appears in the same relative order
- Consistent identification — the same icon or function is labeled the same way throughout the site
- Suggestions are provided when input errors are detected

### Principle 4: Robust

Content must be robust enough to be interpreted by a wide variety of user agents, including assistive technologies.

**Level A requirements:**
- All HTML elements have complete start and end tags
- Elements are nested according to their specifications
- ID attributes are unique

**Level AA requirements:**
- ARIA landmark roles are used to identify regions of the page (`navigation`, `main`, `contentinfo`, `banner`)

## Practical Accessibility Tasks

### Quick Wins (One Hour or Less)

1. **Add alt text to every image.** Every `<img>` element needs descriptive alt text. Decorative images (purely visual, no informational content) should use empty alt (`alt=""`) so screen readers skip them.

2. **Check color contrast.** The contrast ratio between text and background must be at least 4.5:1 for normal text and 3:1 for large text (18px+ bold or 24px+ regular). Use the WebAIM Contrast Checker — enter your hex color values and it tells you whether you pass.

3. **Verify keyboard navigation.** Tab through every interactive element on your most important pages. Can you reach every link, button, and form field? Can you submit forms? Can you close modals? If you get stuck on an element or can't reach something, you have a keyboard trap that needs fixing.

4. **Add focus indicators.** Remove `outline: none` from your CSS — or replace it with a custom focus style that is visible at a 3:1 contrast ratio against its background. Users who navigate by keyboard need to see where they are on the page.

5. **Check heading hierarchy.** Your page should have one `<h1>` (the page title), followed by `<h2>` for major sections, `<h3>` for subsections, and so on. Skip-level headings (jumping from `<h2>` to `<h4>`) confuse screen reader users.

6. **Label all form fields.** Every `<input>`, `<select>`, and `<textarea>` needs an associated `<label>` element, linked by the `for` attribute matching the input's `id`. Placeholder text is not a substitute for a label.

### One-Day Tasks

7. **Add a skip-to-content link.** The very first link on every page should be "Skip to main content" or similar, invisible by default but visible on keyboard focus. This lets keyboard and screen reader users bypass repetitive navigation.

8. **Implement ARIA landmarks.** Use semantic HTML elements (`<nav>`, `<main>`, `<footer>`, `<aside>`, `<header>`) or add ARIA role attributes (`role="navigation"`, `role="main"`) to define page regions. Screen reader users can then jump between regions.

9. **Fix link text.** Every link should describe its destination. "Click here" and "Read more" are not accessible. Use "Read the cookie consent guide" and "View pricing for our compliance scanner" instead.

10. **Test with a screen reader.** Try navigating your site with just a screen reader:
    - **Mac:** Turn on VoiceOver (Cmd + F5), navigate with Tab and VoiceOver modifiers
    - **Windows:** Install NVDA (free, open source)
    - **Chrome:** Install the ChromeVox extension

---

# Chapter 6: Platform-Specific Compliance

The compliance requirements described in previous chapters apply regardless of your platform, but each platform offers different tools, settings, and limitations for meeting them. This chapter provides platform-specific guidance.

## Shopify

Shopify provides several built-in compliance features but also has important limitations.

**Cookie consent:** Shopify's native cookie banner is available in all stores. Enable it under Settings > Privacy. The native banner covers Shopify's own cookies but does not block third-party scripts from apps. For comprehensive cookie blocking, use a Shopify-compatible CMP app like Cookiebot, Pandectes, or CookieYes.

**Privacy policy:** Shopify provides a privacy policy template generator under Settings > Policies. It covers standard data processing but you should review and customize it, especially if you use analytics, marketing, or third-party apps that process customer data.

**Data Processing Agreement:** Shopify acts as a data processor for your customer data. Their standard Terms of Service include data processing terms for GDPR compliance. You can access Shopify's DPA in your admin under Settings > Policies.

**Customer data requests:** Customers can request data exports and account deletion through the customer account portal. Ensure this feature is enabled in Settings > Checkout > Customer accounts.

**Third-party apps:** Each app you install may set cookies or process customer data. Review each app's privacy policy and cookie usage. Apps from unverified developers are a common compliance risk.

## WooCommerce (WordPress)

WooCommerce is self-hosted, which gives you full control over compliance — but also full responsibility.

**Cookie consent:** Install a WordPress-compatible CMP plugin. Complianz works well with WooCommerce and can automatically detect WooCommerce-related cookies. Cookiebot for WordPress also integrates well.

**Privacy policy:** WooCommerce generates a basic privacy policy in Settings > Privacy. Expand it to cover your specific data processing activities. The generated page is a starting point, not a final document.

**Data erasure:** WooCommerce has built-in GDPR tools under WooCommerce > Status > Tools. Enable order data anonymization after a configurable period (typically 12-24 months after order completion). This automatically replaces customer personal data with anonymized entries.

**Security:** As a self-hosted platform, security is your responsibility. Key measures include:
- Keep WordPress core, WooCommerce, and all plugins updated
- Use strong, unique passwords for all admin accounts
- Implement two-factor authentication for admin logins
- Use a WordPress security plugin (WordFence, Sucuri) for firewall and monitoring
- Regularly back up your database and files

## Wix

Wix offers a guided compliance setup through its admin interface.

**Cookie consent:** Enable the cookie banner under Settings > Legal > Cookies. Wix's banner supports granular categories and automatically blocks Wix's own tracking scripts until consent is given. However, it may not block tracking from third-party apps integrated through Wix App Market.

**Privacy policy:** Wix provides a template Privacy Policy under Settings > Legal > Privacy Policy. Like all templates, customize it to your actual data processing practices.

**Data requests:** Wix allows customers to submit data access and deletion requests through your site. Enable this feature under Settings > Legal > Privacy Requests.

**Analytics:** Wix's native analytics are considered "necessary" cookies by Wix and are exempt from consent. However, if you add Google Analytics or other third-party tracking, they require consent.

## Webflow

Webflow gives you full design control but requires more manual setup for compliance.

**Cookie consent:** Webflow does not have a built-in CMP. Use Finsweet's Cookie Consent (free, built by the Webflow team for Webflow), or install a third-party CMP via custom code in your site head.

**Privacy policy:** Webflow does not generate privacy policies. Write your own or use a third-party generator (Iubenda, TermsFeed). Add it to a dedicated page and link it from your footer.

**Forms:** Webflow forms submit data to Webflow's servers by default. If you collect personal data through forms, ensure you have a DPA with Webflow (included in their terms of service) and include form data handling in your privacy policy.

**Custom code:** Any custom code you add to Webflow (analytics, tracking pixels, chat widgets, marketing scripts) must be included in your cookie consent categories. Webflow does not automatically block third-party scripts — your CMP must handle this.

## Squarespace

Squarespace provides solid built-in compliance tools.

**Cookie consent:** Enable the cookie banner under Settings > Cookies & Visitor Data. Squarespace automatically blocks analytics cookies until consent is given. The banner supports granular categories.

**Privacy policy:** Squarespace generates a privacy policy under Settings > Legal. It covers basic data processing but should be reviewed and customized.

**Data requests:** Squarespace handles data subject requests through their standard support process. Document this in your privacy policy so users know how to submit requests. They also offer a data processing addendum.

**Analytics:** Squarespace's native analytics are considered necessary cookies. Any additional tracking (Google Analytics, Facebook Pixel) requires consent through the banner.

## Magento / Adobe Commerce

As a self-hosted enterprise solution, Magento requires the most manual compliance work.

**Cookie consent:** Magento has a default cookie notice, but it is not compliant with GDPR requirements for consent. You need to install a CMP extension from the Magento Marketplace or integrate a JavaScript-based CMP.

**Customer data:** Magento has comprehensive customer data management built in. Use the native export and delete tools under Customers > Manage Customers. Magento can also be configured to anonymize customer data automatically after a set period.

**Security:** Security is fully your responsibility — and Magento is a frequent target for attacks. Essential security measures include:
- Apply all security patches within 48 hours of release
- Use Magento's built-in Security Scan tool
- Implement Web Application Firewall (WAF) protection
- Use HTTPS across all pages, including the admin panel

## BigCommerce

BigCommerce offers a good balance of built-in tools and flexibility.

**Cookie consent:** Enable the cookie consent banner under Advanced Settings > Cookie Consent. BigCommerce blocks its own tracking scripts until consent is given and supports granular cookie categories.

**Privacy policy:** BigCommerce provides templates but recommends customization. Find them under Store Settings > Legal > Privacy Policy.

**Data requests:** BigCommerce supports data access and deletion requests. Enable this in store settings and document the process in your privacy policy.

---

# Chapter 7: DORA and Other Regulations

## Digital Operational Resilience Act (DORA)

DORA (Regulation 2022/2554) applies specifically to financial entities — but its principles are increasingly relevant for any business that processes digital transactions or customer data.

### Who Must Comply

The regulation applies to banks, investment firms, payment institutions, insurance companies, and other financial entities operating in the EU. If you run a SaaS platform that integrates with financial services, your customers may require DORA-aligned practices from you.

### Key Requirements

**ICT Risk Management:** A comprehensive framework covering identification, protection, detection, response, and recovery of ICT systems.

**Incident Reporting:** Major ICT incidents must be reported within specified timelines, with initial notification, intermediate reports, and a final root cause analysis.

**Digital Operational Resilience Testing:** Regular testing including vulnerability assessments, penetration testing, and scenario-based testing.

**ICT Third-Party Risk:** Financial entities must manage risk from ICT third-party providers (this is where your SaaS service could be affected if you serve financial sector clients).

### Practical Steps

If you serve financial sector clients, you should document:
- Your ICT system classification and business impact analysis
- Incident response and recovery procedures
- Your testing schedule and results
- Your own third-party vendor risk assessments

## German-Specific Requirements

### Impressum

If you operate a commercial website that reaches German users, you are required by the German Telemediengesetz (TMG) to provide a clear Impressum — a legal notice that includes:

- Business name and legal form (e.g., "Jane Smith, sole proprietor" or "Example GmbH")
- Complete physical address (not a PO box)
- Contact information (email address and phone number)
- Commercial register number (if applicable)
- VAT identification number (if applicable)
- Managing directors or authorized representatives' names

The Impressum must be easily reachable from every page on your site — typically in the footer. It must be in German. Failure to provide a compliant Impressum can result in fines up to €50,000 and is a common target for competitors and Abmahnungen (cease-and-desist letters).

### Abmahnung Risk

An Abmahnung is a formal cease-and-desist letter, common in German e-commerce law. If your website is missing an Impressum, has incorrect legal text, or has non-compliant terms, a competitor or a specialized law firm can send you an Abmahnung demanding you stop the violation and pay legal fees (typically €200-€1,000 per violation).

The costs add up quickly, which is why having correct legal documentation is essential for any site that targets German customers.

---

# Chapter 8: Compliance Tools and Resources

## Free Website Scanners

Start your compliance journey by scanning your current website. These tools provide immediate visibility into your compliance gaps.

| Tool | What It Checks | Price |
|------|---------------|-------|
| **EUComply Scanner** | GDPR compliance signals, security headers, SSL/TLS configuration, cookie presence, common vulnerabilities | Free |
| **SSL Labs** | SSL/TLS certificate depth, protocol support, cipher strength, known vulnerabilities | Free |
| **SecurityHeaders.com** | HTTP security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy) | Free |
| **WebAIM WAVE** | Accessibility issues — color contrast, missing alt text, heading structure, ARIA usage | Free |
| **W3C Validator** | HTML and CSS validation — code quality that affects accessibility | Free |
| **Google PageSpeed / Lighthouse** | Performance, accessibility, best practices, SEO — built into Chrome DevTools | Free |
| **Mozilla Observatory** | Security headers, SSL/TLS configuration, overall security score | Free |

## Consent Management Platforms

| Platform | Best For | Key Strength | Price |
|---------|---------|-------------|-------|
| Cookiebot | All website platforms | Automatic cookie scanning, Google Consent Mode V2 integration, multi-language | Free (<50 pages), Pro from €12/mo |
| Klaro | Self-hosted or developer-run sites | Open source, lightweight (under 10KB), no third-party dependencies, fully customizable | Free (MIT license) |
| Finsweet | Webflow sites | Free, built for Webflow by Finsweet (Webflow's design partner), simple setup | Free |
| Complianz | WordPress/WooCommerce sites | Deep WordPress integration, automatically detects WordPress cookies, GDPR + ePrivacy compliant | Free / Premium €45/yr |
| Osano | Mid-market to enterprise | Full compliance automation, data subject request handling, consent management | From $30/mo |
| CookieYes | All platforms | Good balance of features and price, Google Consent Mode V2, cookie scanning | Free up to 100 pages, from $10/mo |

## Privacy Policy Generators

- **Iubenda** — Comprehensive, covers GDPR, ePrivacy, and other international regulations. From €9/year for basic plans.
- **TermsFeed** — Simple and straightforward, good for standard websites and e-commerce. From $10/year.
- **GetTerms** — Focused on small businesses and startups, free tier available.
- **Shopify's built-in** — Basic but sufficient for simple Shopify stores. Free.
- **Wix's built-in** — Good starting point for Wix sites. Free.

## Accessibility Testing Tools

- **WAVE by WebAIM** — Browser extension that provides visual feedback on your page with icons and indicators showing accessibility issues. Free.
- **axe DevTools** — Developer-focused accessibility testing tool that integrates into browser DevTools. Free and paid versions.
- **Lighthouse** — Built into Chrome DevTools, audits accessibility, performance, best practices, and SEO. Free.
- **NV Access NVDA** — Free, open-source screen reader for Windows. Essential for real-world accessibility testing.
- **VoiceOver** — Built into macOS, no installation needed. Turn on with Cmd+F5.
- **Colour Contrast Analyzer** — Desktop app that picks colors from your screen and calculates contrast ratios. Free.

---

# Chapter 9: Creating Your Compliance Action Plan

## Week 1: Audit

Run these five free checks on your website. Each takes less than five minutes.

**1. Security headers scan.** Go to SecurityHeaders.com and enter your website URL. If you score below A, you have security gaps to address. At minimum you need HSTS, X-Frame-Options, and X-Content-Type-Options.

**2. Cookie audit.** Open your browser's developer tools (F12), go to the Application tab, and look at Cookies. List every cookie your site sets. Does each one have a purpose? Is it necessary or tracking?

**3. Accessibility check.** Install the WAVE browser extension. Run it on your three most visited pages. Note the contrast errors (most common issue), missing alt text, and heading structure problems.

**4. SSL/TLS check.** Enter your URL at SSL Labs. Any score below A needs immediate attention. Check for certificate expiry date and weak protocol support (TLS 1.0 and 1.1 should be disabled).

**5. Privacy policy review.** Read your current privacy policy. Does it cover all the points in Chapter 2? If you don't have one, it is your highest-priority task.

## Week 2: Quick Fixes

**Implement these immediately:**

- Add or update your privacy policy
- Install and configure a cookie consent banner
- Add alt text to all images on your homepage and top product pages
- Enable HTTPS with HSTS if not already configured
- Add your Impressum (if targeting German customers)
- Add a clear contact/privacy link in your footer

## Week 3: Foundation

- Document your data processing activities in a register (start with a simple spreadsheet)
- Sign DPAs with your key service providers (hosting, analytics, email marketing)
- Write an incident response plan (one page is enough to start)
- Test your website with a screen reader
- Publish an accessibility statement

## Month 2: Ongoing

- Set up monthly security header checks (they can change if you update your site)
- Schedule quarterly accessibility audits
- Plan annual policy reviews
- Monitor regulatory changes — GDPR and ePrivacy are under ongoing review

## Compliance Budget

Compliance does not have to be expensive. For a small business with a standard website:

| Item | Cost |
|------|------|
| Consent Management Platform (Cookiebot free tier) | €0 |
| Privacy policy (Iubenda or DIY) | €0-€9/year |
| Free scanners (SSL Labs, SecurityHeaders, WAVE, EUComply) | €0 |
| **Total** | **€0-€9/year** |

Even the paid solutions (Cookiebot Pro at €12/mo, Iubenda from €9/yr) represent a minimal investment compared to a potential GDPR fine of €2,000-€100,000.

---

# Chapter 10: Checklists and Templates

## GDPR Compliance Checklist

Every website serving EU visitors should pass these checks:

- [ ] Privacy policy is published on a dedicated, accessible page
- [ ] Privacy policy is written in clear, plain language (not legalese)
- [ ] Privacy policy specifies legal basis for each processing purpose
- [ ] Cookie consent banner is installed and functional on all pages
- [ ] Non-essential cookies are blocked before the user gives consent
- [ ] Cookie banner offers granular categories (not all-or-nothing)
- [ ] "Reject All" is as easy to click as "Accept All"
- [ ] Consent records are stored (who consented, when, to what)
- [ ] Data Processing Agreements are signed with all service providers
- [ ] Data subject request process is documented and staff know how to handle requests
- [ ] Data retention schedule is defined and followed
- [ ] Security measures are documented (HTTPS, access controls, passwords)
- [ ] Analytics consent is configured (Google Consent Mode V2 if applicable)
- [ ] Cookie categories are clearly defined (necessary, analytics, marketing, preferences)
- [ ] A mechanism for withdrawing consent is available on all pages

## Accessibility Checklist (WCAG 2.1 AA)

- [ ] All images have appropriate alt text (decorative images use empty alt)
- [ ] Text has at least 4.5:1 contrast ratio against background
- [ ] Keyboard navigation works for all interactive elements
- [ ] Visible focus indicators are present (never use `outline: none` without replacement)
- [ ] Page heading hierarchy is logical (h1 → h2 → h3, no skips)
- [ ] All form fields have associated labels
- [ ] Skip-to-content link is present as the first focusable element
- [ ] ARIA landmark roles identify page regions (nav, main, footer)
- [ ] Link text is descriptive (not "click here" or "read more")
- [ ] Video content has captions or transcripts
- [ ] Accessibility statement is published describing current status and how to report issues
- [ ] Tested with WAVE or axe DevTools
- [ ] Tested with a screen reader (VoiceOver or NVDA)

## NIS2 Compliance Checklist (for in-scope organizations)

- [ ] Risk assessment completed and documented
- [ ] Security measures documented to meet Article 21 requirements
- [ ] Incident response plan created and tested at least annually
- [ ] Supply chain security assessed for each vendor
- [ ] Business continuity plan documented
- [ ] CSIRT contact information is on file and accessible
- [ ] Employee security awareness training has been completed
- [ ] Management accountability for cybersecurity is formally assigned
- [ ] Vulnerability management process is active (patches applied within defined timelines)
- [ ] Backup and recovery procedures are tested quarterly
- [ ] Encryption is used for data in transit (HTTPS) and at rest
- [ ] Multi-factor authentication is enabled for all administrative access

---

## Appendix: Key Regulations at a Glance

| Regulation | Full Name | Scope | Key Requirement | Max Fine |
|-----------|-----------|-------|-----------------|---------|
| GDPR | General Data Protection Regulation | All EU personal data processing | Lawful processing, consent, rights, accountability | €20M or 4% of global revenue |
| ePrivacy Directive | Directive on Privacy and Electronic Communications | Electronic communications, cookies | Cookie consent for non-essential trackers | National (varies) |
| NIS2 | Network and Information Security Directive 2 | Essential and important entities | Cybersecurity risk management, incident reporting | €10M or 2% of annual revenue |
| EAA | European Accessibility Act | Digital products and services in EU | WCAG 2.1 Level AA accessibility | National (varies) |

---

## Quick Reference: Enforcement Bodies by Country

| Country | DPA / Supervisory Authority | Website |
|---------|---------------------------|---------|
| Austria | Österreichische Datenschutzbehörde (DSB) | dsb.gv.at |
| Belgium | Autorité de la protection des données (APD) | autoriteprotectiondonnees.be |
| Denmark | Datatilsynet | datatilsynet.dk |
| France | Commission Nationale de l'Informatique et des Libertés (CNIL) | cnil.fr |
| Germany | Die Bundesbeauftragte für den Datenschutz (BfDI) | bfdi.bund.de |
| Ireland | Data Protection Commission (DPC) | dataprotection.ie |
| Italy | Garante per la protezione dei dati personali | garanteprivacy.it |
| Netherlands | Autoriteit Persoonsgegevens (AP) | autoriteitpersoonsgegevens.nl |
| Spain | Agencia Española de Protección de Datos (AEPD) | aepd.es |
| Sweden | Integritetsskyddsmyndigheten (IMY) | imy.se |
| UK | Information Commissioner's Office (ICO) | ico.org.uk |

---

*This guide is for informational purposes and does not constitute legal advice. Regulations vary by member state, and specific situations may require professional legal consultation. Laws and enforcement practices change over time. Verify current requirements with your national data protection authority. Last updated: August 2026.*

---

**About This Book**

This handbook was compiled by EUComply — a free website compliance scanner that checks any URL for GDPR compliance signals, security headers, SSL/TLS configuration, and common vulnerabilities. Visit https://auditedwp.pages.dev to scan your website for free.

The author holds no legal qualifications. This book is a practical guide written from research and industry experience, not a substitute for professional legal advice.