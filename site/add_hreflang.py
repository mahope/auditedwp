#!/usr/bin/env python3
"""Add hreflang tags to EUComply site files."""
import os, re

SITE = os.path.expanduser("~/hermes-ceo/site")
DOMAIN = "https://eucomplypro.com"

# Hreflang pairs (english_path, german_path)
pairs = {
    "/": "/de/",
    "/blog/german-impressum-foreign-sellers/": "/de/was-ist-ein-impressum/",
    "/blog/abmahnung-risk-ecommerce/": "/de/was-ist-ein-impressum/",
    "/impressum-generator/": "/de/was-ist-ein-impressum/",
}

# English-only pages: self-referencing x-default
self_hreflang = [
    "/scan/", "/tools/", "/pro/", "/store/", "/blog/",
    "/privacy-policy-generator/", "/cookie-policy-generator/",
    "/terms-of-service-generator/", "/refund-policy-generator/",
    "/checklist/", "/nis2-checklist/", "/eaa-checklist/",
    "/badge/", "/extension/", "/plugin/", "/privacy/", "/terms/",
    "/blog/gdpr-cookie-banner-fines/",
    "/blog/eu-cookie-consent-guide-2026/",
    "/blog/do-you-need-a-refund-policy/",
    "/blog/dora-compliance-guide/",
    "/blog/dora-nis2-gdpr-differences/",
    "/blog/eu-compliance-checklist-2026/",
    "/blog/european-accessibility-act-guide/",
    "/blog/nis2-vendor-supply-chain-compliance/",
    "/blog/website-compliance-scanner-comparison/",
    "/blog/hsts-preload-guide/",
    "/template/", "/sample/",
]

def add_hreflang(path, alternates):
    filepath = SITE + path + "index.html"
    if not os.path.exists(filepath):
        print(f"  NOT FOUND: {filepath}")
        return
    with open(filepath) as f:
        content = f.read()
    if "hreflang" in content:
        print(f"  SKIP (has hreflang): {path}")
        return
    canon_match = re.search(r'<link rel="canonical" href="[^"]+">', content)
    if not canon_match:
        print(f"  NO CANONICAL: {path}")
        return
    insert_pos = canon_match.end()
    hreflang_html = "\n"
    for href, hreflang in alternates:
        hreflang_html += f'  <link rel="alternate" hreflang="{hreflang}" href="{DOMAIN}{href}">\n'
    hreflang_html += "  "
    content = content[:insert_pos] + hreflang_html + content[insert_pos:]
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"  OK: {path}")

print("=== German pages → English hreflang ===")
add_hreflang("/de/", [("/", "en")])
add_hreflang("/de/was-ist-ein-impressum/", [("/blog/german-impressum-foreign-sellers/", "en")])

print("\n=== English paired pages → German hreflang ===")
for en_path, de_path in pairs.items():
    add_hreflang(en_path, [(de_path, "de")])

print("\n=== English-only self hreflang (x-default) ===")
for path in self_hreflang:
    add_hreflang(path, [(path, "x-default")])

print("\n=== Further reading sections on blog posts ===")

# Blog posts → related articles (path, [(link, title)])
further_reading = {
    "gdpr-cookie-banner-fines": [
        ("/blog/eu-cookie-consent-guide-2026/", "EU Cookie Consent Guide 2026"),
        ("/blog/website-compliance-scanner-comparison/", "Free Compliance Scanner Comparison"),
        ("/scan/", "Scan your website free →"),
    ],
    "eu-cookie-consent-guide-2026": [
        ("/blog/gdpr-cookie-banner-fines/", "GDPR Cookie Fine Risks"),
        ("/blog/eu-compliance-checklist-2026/", "EU Compliance Checklist 2026"),
        ("/cookie-policy-generator/", "Generate a cookie policy →"),
    ],
    "do-you-need-a-refund-policy": [
        ("/refund-policy-generator/", "Generate a refund policy →"),
        ("/blog/eu-compliance-checklist-2026/", "EU Compliance Checklist 2026"),
        ("/scan/", "Scan your website →"),
    ],
    "dora-compliance-guide": [
        ("/blog/dora-nis2-gdpr-differences/", "DORA vs NIS2 vs GDPR"),
        ("/blog/nis2-vendor-supply-chain-compliance/", "NIS2 Supply Chain Compliance"),
        ("/pro/", "EUComply Pro — $79/yr"),
    ],
    "dora-nis2-gdpr-differences": [
        ("/blog/dora-compliance-guide/", "DORA Compliance Guide"),
        ("/blog/nis2-vendor-supply-chain-compliance/", "NIS2 Supply Chain Compliance"),
        ("/scan/", "Run a free compliance scan →"),
    ],
    "eu-compliance-checklist-2026": [
        ("/checklist/", "Interactive GDPR Checklist"),
        ("/blog/european-accessibility-act-guide/", "European Accessibility Act Guide"),
        ("/blog/eu-cookie-consent-guide-2026/", "EU Cookie Consent Guide 2026"),
    ],
    "european-accessibility-act-guide": [
        ("/eaa-checklist/", "Interactive EAA Checklist"),
        ("/blog/eu-compliance-checklist-2026/", "EU Compliance Checklist 2026"),
        ("/blog/dora-nis2-gdpr-differences/", "DORA vs NIS2 vs GDPR"),
    ],
    "german-impressum-foreign-sellers": [
        ("/impressum-generator/", "Free Impressum Generator"),
        ("/blog/abmahnung-risk-ecommerce/", "Abmahnung Risk for E-Commerce"),
        ("/de/was-ist-ein-impressum/", "🇩🇪 Was ist ein Impressum? (German)"),
    ],
    "nis2-vendor-supply-chain-compliance": [
        ("/blog/dora-nis2-gdpr-differences/", "DORA vs NIS2 vs GDPR"),
        ("/blog/dora-compliance-guide/", "DORA Compliance Guide"),
        ("/pro/", "EUComply Pro — $79/yr"),
    ],
}

for slug, links in further_reading.items():
    fp = f"{SITE}/blog/{slug}/index.html"
    if not os.path.exists(fp):
        print(f"  NOT FOUND: {fp}")
        continue
    with open(fp) as f:
        content = f.read()

    if 'class="further-reading"' in content:
        print(f"  SKIP (has further-reading): {slug}")
        continue

    footer_match = re.search(r'<footer>', content)
    if not footer_match:
        print(f"  NO FOOTER: {slug}")
        continue

    html = '\n<div class="further-reading">\n<h2>Further reading</h2>\n<ul>\n'
    for link, text in links:
        html += f'  <li><a href="{link}">{text}</a></li>\n'
    html += '</ul>\n</div>\n\n'

    content = content[:footer_match.start()] + html + content[footer_match.start():]
    with open(fp, 'w') as f:
        f.write(content)
    print(f"  OK further-reading: {slug}")

# Also add scanner CTA to generator pages
print("\n=== Scanner CTAs on generators ===")
generators = ["privacy-policy-generator", "cookie-policy-generator", "terms-of-service-generator", "refund-policy-generator", "impressum-generator"]
for gen in generators:
    fp = f"{SITE}/{gen}/index.html"
    if not os.path.exists(fp):
        continue
    with open(fp) as f:
        content = f.read()
    if 'scanner-cta' in content:
        print(f"  SKIP (has scanner-cta): {gen}")
        continue
    footer_match = re.search(r'<footer>', content)
    if not footer_match:
        print(f"  NO FOOTER: {gen}")
        continue
    cta = '\n<div class="scanner-cta" style="background:#f0f4ff;border:1px solid #b2ddff;border-radius:10px;padding:20px;text-align:center;margin:32px 0">\n  <p style="font-size:16px;font-weight:600;margin-bottom:8px">🔍 Already generated your document?</p>\n  <p style="font-size:14px;color:#475467;margin-bottom:12px">Check if your website passes a full EU compliance scan — free, no sign-up.</p>\n  <a href="/scan/" style="display:inline-block;background:#175cd3;color:#fff;text-decoration:none;font-weight:600;padding:10px 20px;border-radius:8px">Run free scan →</a>\n</div>\n'
    content = content[:footer_match.start()] + cta + content[footer_match.start():]
    with open(fp, 'w') as f:
        f.write(content)
    print(f"  OK scanner-cta: {gen}")

print("\nDone.")
