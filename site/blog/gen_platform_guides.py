#!/usr/bin/env python3
"""Generate BigCommerce + Magento GDPR guides from the blog template."""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(os.path.dirname(BASE), "")

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://eucomplypro.com/blog/{slug}/">
<link rel="alternate" hreflang="x-default" href="https://eucomplypro.com/blog/{slug}/">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{ogdesc}">
<meta property="og:type" content="article">
<meta property="og:url" content="https://eucomplypro.com/blog/{slug}/">
<style>
  :root{{--ink:#101828;--muted:#475467;--line:#e4e7ec;--accent:#175cd3;--ok:#027a48;--warn:#b54708;--bg:#fff;}}
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;color:var(--ink);line-height:1.65;max-width:780px;margin:0 auto;padding:32px 24px;background:var(--bg)}}
  h1{{font-size:34px;letter-spacing:-.025em;line-height:1.2;margin-bottom:10px}}
  .meta{{color:var(--muted);font-size:14px;margin-bottom:32px}}
  .meta a{{color:var(--accent)}}
  h2{{font-size:22px;margin:40px 0 12px;letter-spacing:-.015em;padding-top:16px;border-top:1px solid var(--line)}}
  h3{{font-size:17px;margin:24px 0 8px}}
  p{{margin-bottom:14px}}
  li{{margin-bottom:6px}}
  ul,ol{{padding-left:22px;margin-bottom:16px}}
  .toc{{background:#f9fafb;border:1px solid var(--line);border-radius:10px;padding:18px 22px;margin:24px 0}}
  .toc h2{{font-size:16px;margin:0 0 10px;padding:0;border:none}}
  .toc a{{color:var(--accent);text-decoration:none;display:block;padding:3px 0;font-size:14px}}
  .toc a:hover{{text-decoration:underline}}
  code{{background:#f3f4f6;padding:2px 6px;border-radius:4px;font-size:.9em}}
  .box{{background:#fffbeb;border:1px solid #fde68a;border-radius:10px;padding:18px 22px;margin:24px 0}}
  .box a{{color:var(--accent)}}
  .btn{{display:inline-block;background:var(--accent);color:#fff;padding:11px 22px;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px;margin:6px 0}}
  .btn:hover{{filter:brightness(.9)}}
  .check{{color:var(--ok);font-weight:700}}
  .cross{{color:#ccc}}
  .further-reading{{background:#f9fafb;border:1px solid var(--line);border-radius:10px;padding:18px 22px;margin:24px 0}}
  .further-reading h2{{border:none;padding:0;margin:0 0 10px;font-size:16px}}
  .further-reading ul{{padding-left:20px;margin:0}}
  .further-reading li{{margin-bottom:4px}}
  .tblwrap{{overflow-x:auto;margin:16px 0}}
  table{{border-collapse:collapse;width:100%;font-size:14px}}
  table th,table td{{border:1px solid var(--line);padding:10px 12px;text-align:left}}
  table th{{background:#f9fafb;font-weight:700;font-size:13px}}
  @media(max-width:600px){{h1{{font-size:26px}}body{{padding:20px 16px}}table th,table td{{padding:7px 8px;font-size:12.5px}}}}
.keep-reading{{margin-top:48px;padding-top:24px;border-top:1px solid rgba(148,163,184,.25)}}
.keep-reading h2{{font-size:20px;margin-bottom:12px}}
.keep-reading ul{{list-style:none;padding:0;margin:0;display:grid;gap:8px}}
.keep-reading a{{color:#7dd3fc;text-decoration:none}}
.keep-reading a:hover{{text-decoration:underline}}
</style>
<script type="application/ld+json">{{"@context": "https://schema.org", "@type": "Article", "headline": "{title}", "description": "{desc}", "mainEntityOfPage": "https://eucomplypro.com/blog/{slug}/index.html", "author": {{"@type": "Organization", "name": "ComplianceDocs"}}, "publisher": {{"@type": "Organization", "name": "ComplianceDocs"}}}}</script>
</head>
<body>

<h1>{h1}</h1>
<p class="meta">
  <time datetime="2026-08-30">August 30, 2026</time> · Filed under: <a href="/blog/">Guides</a> ·
  <a href="/scan/">Free compliance scanner →</a>
</p>

<div class="toc">
  <h2>Table of Contents</h2>
{toc}
</div>

"""

FOOT = """
<footer style="border-top:1px solid var(--line);margin-top:40px;padding-top:20px;color:var(--muted);font-size:13px">
  <p>EUComply — EU compliance scanning for every website. ⚖️ Automated technical checks and general information only. Not legal advice.</p>
</footer>

<nav class="keep-reading" aria-label="Related guides" data-related><h2>Keep reading</h2><ul>{related}</ul></nav>
</body>
</html>
"""

PLATFORM_RELATED = [
    ("/blog/shopify-gdpr-compliance-guide/", "Shopify GDPR Compliance Guide 2026: What Store Owners Actually Need"),
    ("/blog/webflow-gdpr-compliance-guide/", "Webflow GDPR Compliance Guide 2026: What Site Owners Actually Need"),
    ("/blog/squarespace-gdpr-compliance-guide/", "Squarespace GDPR Compliance Guide 2026: What Site Owners Actually Need"),
    ("/blog/wix-gdpr-compliance-guide/", "Wix GDPR Compliance Guide 2026: What Site Owners Actually Need"),
    ("/blog/woocommerce-gdpr-compliance-guide/", "WooCommerce GDPR Compliance Guide 2026: What Store Owners Actually Need"),
]

def toc(items):
    return "\n".join(f'  <a href="#{i}">{n}</a>' for i, n in items)

def further(links):
    return "\n".join(f'    <li><a href="{u}">{t}</a></li>' for u, t in links)

def related(items):
    return "".join(f'<li><a href="{u}">{t}</a></li>' for u, t in items)

# ---------------------------------------------------------------- BigCommerce
bigcommerce_body = """
<p>If you run a store on BigCommerce and it gets visitors from the EU, GDPR applies to you — regardless of where your business is incorporated. GDPR follows your visitors, not your headquarters.</p>

<p>BigCommerce is a fully hosted SaaS commerce platform, which means some compliance work is handled for you — but plenty of it is not. This guide walks through exactly what a BigCommerce merchant needs to do, in plain language.</p>

<section id="applies">
<h2>1. Does GDPR apply to your BigCommerce store?</h2>
<p>Yes, if any of these are true:</p>
<ul>
<li>You sell or ship to customers in the EU or EEA</li>
<li>Your store is available in EU languages or prices in EUR (even without shipping there)</li>
<li>You run ads targeting EU shoppers (Google Shopping, Meta, TikTok)</li>
<li>You use analytics that record EU visitors</li>
</ul>
<p>If none of these apply and you actively block EU traffic, you're likely outside scope. Almost no serious store is.</p>
</section>

<section id="requirements">
<h2>2. Six compliance requirements for BigCommerce stores</h2>

<h3>a) A valid legal basis for tracking</h3>
<p>Marketing cookies and analytics cookies require consent <em>before</em> they fire. Under the ePrivacy Directive this applies to any non-essential cookie, even though GDPR itself only regulates personal data.</p>

<h3>b) Consent that meets the standard</h3>
<ul>
<li>Banners must offer <strong>Reject as easily as Accept</strong> — equal prominence buttons</li>
<li>No pre-ticked boxes</li>
<li>Consent must be logged (who, when, what exactly)</li>
<li>Withdrawing consent must be as easy as giving it</li>
</ul>

<h3>c) An accurate privacy policy</h3>
<p>It must name BigCommerce as a processor, list every app and script that touches customer data (payments, email marketing, reviews, live chat), state retention periods, and explain how to exercise data rights.</p>

<h3>d) Data Processing Agreements (DPAs)</h3>
<p>You need a DPA with every processor: BigCommerce itself (covered by their terms), plus each marketing, analytics, review, and support app you've installed. Keep a written list.</p>

<h3>e) Data subject rights handling</h3>
<p>EU customers can request access to, correction of, or deletion of their data — and you generally must respond within 30 days. In BigCommerce, customer records live in the admin, but copies also sit in abandoned-cart emails, order confirmation systems, and third-party apps. Deletion requests mean checking those too.</p>

<h3>f) Records and security basics</h3>
<ul>
<li>Two-factor authentication on all staff accounts</li>
<li>Minimal staff access — not everyone needs export rights</li>
<li>A simple record of what data you hold and why</li>
</ul>
</section>

<section id="consent">
<h2>3. Cookie consent setup on BigCommerce</h2>
<p>BigCommerce does not include a built-in CMP comparable to Shopify's Customer Privacy settings. Your options:</p>
<ol>
<li><strong>A consent management platform (CMP):</strong> Cookiebot, Usercentrics, Iubenda, Termly, or similar. These handle scanning, blocking, logging and renewal automatically. Typical cost: €5–€40/month depending on traffic.</li>
<li><strong>Script Manager gating:</strong> BigCommerce's Script Manager lets you set scripts to load only after consent events — workable if you're comfortable editing theme files, but you still need a UI for collecting consent.</li>
</ol>
<p>Whichever route you take, verify with your browser's dev tools that no Google Analytics or Meta Pixel request fires before consent. That single check catches the most common violation.</p>
</section>

<section id="privacy-policy">
<h2>4. Privacy policy requirements</h2>
<p>A compliant policy for a BigCommerce store states:</p>
<ul>
<li>Who you are and how to contact you (and your EU representative under Article 27 if you have none in the EU)</li>
<li>What data you collect: account data, orders, payment metadata, device/analytics data</li>
<li>Why: contract fulfilment, marketing (with consent), legal obligations</li>
<li>Who receives it: BigCommerce, payment providers, shipping carriers, each marketing tool</li>
<li>How long you keep it and how customers can get it deleted</li>
</ul>
</section>

<section id="dpa">
<h2>5. DPAs — the step most merchants miss</h2>
<p>Every app in your BigCommerce control panel that touches personal data is a separate processor. For each one you should be able to answer: who is it, what data does it get, and do we have an agreement covering it?</p>
<div class="box"><p><strong>Quick audit:</strong> open Apps → My Apps, list everything installed, and check each vendor's site for a downloadable DPA. If a tool processes EU data with no DPA and no clear terms, remove it.</p></div>
</section>

<section id="mistakes">
<h2>6. Common compliance mistakes on BigCommerce</h2>
<ul>
<li><span class="cross">✗</span> Analytics and pixels firing before any interaction with the banner</li>
<li><span class="cross">✗</span> "Accept all" as the only visible button</li>
<li><span class="cross">✗</span> Privacy policy last updated before the apps currently installed existed</li>
<li><span class="cross">✗</span> Newsletter checkboxes pre-ticked at checkout</li>
<li><span class="cross">✗</span> No way for a customer to actually request deletion</li>
<li><span class="cross">✗</span> Google Fonts loaded from Google's servers, transferring IP addresses without a basis</li>
</ul>
</section>

<section id="scan">
<h2>7. Free compliance check for your BigCommerce store</h2>
<p>You can verify the technical side in minutes. The free <a href="/scan/">EUComply scanner</a> checks any public URL — BigCommerce, custom storefronts, anything — for cookie banner behavior, tracking scripts firing before consent, missing privacy links, insecure forms and more.</p>
<p><a href="/scan/" class="btn">Scan your store free →</a></p>
<p>Ongoing monitoring across your whole domain plus prioritized fix reports are part of <a href="/pro/">EUComply Pro</a>.</p>
</section>
"""

# ------------------------------------------------------------------- Magento
magento_body = """
<p>If your Magento or Adobe Commerce store gets visitors from the EU, GDPR applies to you — wherever your company is based. GDPR follows your visitors, not your headquarters.</p>

<p>Magento is self-hosted (or PaaS-hosted Adobe Commerce Cloud), which cuts both ways: you control everything, and you're responsible for everything the platform would otherwise handle. Here is what that means concretely.</p>

<section id="applies">
<h2>1. Does GDPR apply to your Magento store?</h2>
<p>Yes, if any of these are true:</p>
<ul>
<li>You sell or ship to customers in the EU or EEA</li>
<li>The store targets EU customers in language or currency</li>
<li>You advertise to EU audiences</li>
<li>Your analytics record EU visitors</li>
</ul>
<p>Because Magento stores typically hold richer customer data than SaaS platforms (custom attributes, ERP syncs, order history going back years), the data-mapping burden is larger too.</p>
</section>

<section id="requirements">
<h2>2. Seven compliance requirements for Magento stores</h2>

<h3>a) Lawful basis for every processing activity</h3>
<p>Map your activities to bases: order fulfilment = contract; fraud prevention = legitimate interests; marketing cookies and newsletters = consent; tax records = legal obligation. Write the map down — regulators ask for it.</p>

<h3>b) Consent management</h3>
<ul>
<li>Non-essential cookies blocked until opt-in</li>
<li>Reject as prominent as accept, no pre-ticks, consent logs kept</li>
<li>Granular choices where practical (analytics vs. marketing)</li>
</ul>

<h3>c) Privacy policy that matches reality</h3>
<p>It must reflect your actual stack: hosting provider, payment gateways, ERP/accounting integrations, marketing automation, review platforms, live chat, and any extensions that transmit data externally.</p>

<h3>d) DPAs with every processor</h3>
<p>Hosting, payment providers, email service, analytics, each extension vendor whose module phones home. Magento's extension ecosystem makes this the most commonly failed item — many modules silently send data to third-party endpoints.</p>

<h3>e) Data subject rights — technically feasible</h3>
<p>Access and deletion requests must be answerable within a month. In Magento that means: customer account data, quotes, orders (which often can't be fully deleted for accounting reasons — pseudonymize instead), newsletter lists, logs, backups policy, and synced copies in connected systems.</p>

<h3>f) Security measures</h3>
<ul>
<li>Admin panel on a non-default path, restricted by IP where possible, with 2FA enforced</li>
<li>HTTPS everywhere, HSTS enabled</li>
<li>Up-to-date patches — unpatched Magento stores are a top breach vector</li>
<li>Least-privilege admin roles; encrypted database backups</li>
</ul>

<h3>g) Breach readiness</h3>
<p>Personal-data breaches must be reported to a supervisory authority within 72 hours where risk exists. Know in advance who decides and how you'd notify.</p>
</section>

<section id="consent">
<h2>3. Cookie consent options on Magento</h2>
<ol>
<li><strong>Dedicated extensions:</strong> several CMP extensions exist on the Magento Marketplace (Cookiebot connector, Mageplaza GDPR, Amasty GDPR and similar). Evaluate them on one criterion first: do they hard-block script execution, or merely hide the banner?</li>
<li><strong>External CMP via Google Tag Manager Consent Mode:</strong> works well if GTM manages your tags, but requires correct configuration of consent defaults per region — EU visitors must default to denied.</li>
</ol>
<p>Either way, test in a private window with dev tools open: search Network requests for <code>google-analytics</code>, <code>facebook</code>, <code>hotjar</code> before you click accept. Anything firing is a violation.</p>
</section>

<section id="mistakes">
<h2>4. Common compliance mistakes on Magento</h2>
<ul>
<li><span class="cross">✗</span> Extensions transmitting customer data to vendor endpoints nobody audited</li>
<li><span class="cross">✗</span> Old customer records retained forever with no retention policy</li>
<li><span class="cross">✗</span> Admin panels reachable on default URLs without 2FA</li>
<li><span class="cross">✗</span> Pixels firing server-side before consent (harder to spot than client-side)</li>
<li><span class="cross">✗</span> Privacy policy describing features removed two versions ago</li>
<li><span class="cross">✗</span> Backups containing personal data stored outside the EU with no transfer mechanism</li>
</ul>
</section>

<section id="scan">
<h2>5. Free compliance check for your Magento store</h2>
<p>The technical layer is checkable today. The free <a href="/scan/">EUComply scanner</a> takes any public URL — Magento, Adobe Commerce Cloud, headwind storefronts — and checks cookie banner behavior, pre-consent tracking, security headers, form handling and more.</p>
<p><a href="/scan/" class="btn">Scan your store free →</a></p>
<p>Scheduled re-scans across your whole domain and prioritized reports come with <a href="/pro/">EUComply Pro</a>.</p>
</section>
"""

PAGES = {
    "bigcommerce-gdpr-compliance-guide": dict(
        title="BigCommerce GDPR Compliance Guide 2026: What Store Owners Actually Need",
        desc="Complete GDPR compliance guide for BigCommerce store owners in 2026: cookie consent setup, privacy policy, DPAs, and how to check your store — without hiring a lawyer.",
        ogdesc="Practical GDPR compliance for BigCommerce stores: consent setup, privacy policies, DPAs, and a free compliance scanner that works on any BigCommerce site.",
        h1="BigCommerce GDPR Compliance Guide 2026: What Store Owners Actually Need",
        toc=toc([("applies", "1. Does GDPR apply to BigCommerce stores?"),
                 ("requirements", "2. Six compliance requirements for BigCommerce"),
                 ("consent", "3. Cookie consent setup on BigCommerce"),
                 ("privacy-policy", "4. Privacy policy requirements"),
                 ("dpa", "5. DPAs — the step most merchants miss"),
                 ("mistakes", "6. Common compliance mistakes on BigCommerce"),
                 ("scan", "7. Free compliance check for your store")]),
        body=bigcommerce_body,
    ),
    "magento-gdpr-compliance-guide": dict(
        title="Magento & Adobe Commerce GDPR Compliance Guide 2026",
        desc="GDPR compliance guide for Magento and Adobe Commerce stores in 2026: consent management, extensions and processors, data subject rights, security basics, and a free scanner.",
        ogdesc="GDPR for Magento and Adobe Commerce: consent management, auditing extensions, data subject rights, security, and a free scanner that works on any Magento site.",
        h1="Magento &amp; Adobe Commerce GDPR Compliance Guide 2026",
        toc=toc([("applies", "1. Does GDPR apply to Magento stores?"),
                 ("requirements", "2. Seven compliance requirements for Magento"),
                 ("consent", "3. Cookie consent options on Magento"),
                 ("mistakes", "4. Common compliance mistakes on Magento"),
                 ("scan", "5. Free compliance check for your store")]),
        body=magento_body,
    ),
}

FURTHER_LINKS = PLATFORM_RELATED + [
    ("/blog/eu-cookie-consent-guide-2026/", "EU Cookie Consent Requirements 2026"),
    ("/blog/gdpr-cookie-banner-fines/", "GDPR Cookie Banner Fines — what sites actually get fined for"),
    ("/blog/eu-compliance-checklist-2026/", "EU Compliance Checklist 2026"),
    ("/scan/", "Free compliance scanner →"),
    ("/pro/vs-cookiebot/", "EUComply vs Cookiebot"),
]

for slug, p in PAGES.items():
    d = os.path.join(BASE, slug)
    os.makedirs(d, exist_ok=True)
    html = HEAD.format(slug=slug, title=p["title"], desc=p["desc"], ogdesc=p["ogdesc"],
                       h1=p["h1"], toc=p["toc"]) + p["body"]
    fr = FURTHER_LINKS[:5] + [("/blog/%s/" % [s for s in PAGES if s != slug][0], "Platform GDPR Guides")]
    html += '<div class="further-reading">\n  <h2>Further reading</h2>\n  <ul>\n' + further(fr) + '\n  </ul>\n</div>'
    rel = PLATFORM_RELATED + [
        ("/blog/iab-tcf-compliance-guide/", "IAB Transparency &amp; Consent Framework (TCF) — Compliance Guide 2026"),
        ("/blog/google-analytics-gdpr-consent/", "Google Analytics and GDPR: When You Need Consent"),
    ]
    html += FOOT.format(related=related(rel))
    path = os.path.join(d, "index.html")
    with open(path, "w") as f:
        f.write(html)
    print("wrote", path, len(html))
