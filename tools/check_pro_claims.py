#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import struct
import sys
import unicodedata
import zipfile
import zlib
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Pattern, Sequence, Set, Tuple
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
ORIGIN = "https://eucomplypro.com"
PRO_LINK = "https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03"
PLUGIN_VERSION = "1.3.2"
FORCED_PRO_PAGES = {
    "site/pro/index.html",
    "site/da/pro/index.html",
    "site/de/pro/index.html",
    "site/fr/pro/index.html",
    "site/pro/dashboard/index.html",
    "site/pro/thank-you/index.html",
    "site/pro/vs-cookiebot/index.html",
    "site/pro/vs-iubenda/index.html",
    "site/pro/vs-onetrust/index.html",
    "site/pro/vs-osano/index.html",
    "site/pro/vs-termly/index.html",
}
BUYING_PAGES = {
    "pro/index.html": ("en", "https://eucomplypro.com/pro/"),
    "da/pro/index.html": ("da", "https://eucomplypro.com/da/pro/"),
    "de/pro/index.html": ("de", "https://eucomplypro.com/de/pro/"),
    "fr/pro/index.html": ("fr", "https://eucomplypro.com/fr/pro/"),
    "pricing/index.html": ("en", "https://eucomplypro.com/pricing/"),
    "da/pricing/index.html": ("da", "https://eucomplypro.com/da/pricing/"),
    "de/pricing/index.html": ("de", "https://eucomplypro.com/de/pricing/"),
    "fr/pricing/index.html": ("fr", "https://eucomplypro.com/fr/pricing/"),
}
MONITORING_PAGES = {
    "site/scan/index.html",
    "site/da/scan/index.html",
    "site/de/scan/index.html",
    "site/fr/scan/index.html",
}
PRODUCT_FILES = {
    "index.html",
    "update.json",
    "plugin/eucomply.php",
    "plugin/readme.txt",
    "chrome-ext/popup.html",
    "chrome-ext/README.md",
    "cli/README.md",
    "cli/bin/eucomply-scan.js",
    "eucomply-scanner/README.md",
    "eucomply-scanner/engine/index.js",
    "shared/scan-engine.js",
    "book/eu-website-compliance-guide-2026.md",
    "book/build-manuscript.py",
    "scripts/build_sample_report_pdf.py",
    "POSTS/launch-email.md",
    "site/LAUNCH-EUCOMPLY.md",
    "site/BUILD.md",
    "site/update.json",
    "site/plugin/eucomply.php",
    "site/plugin/readme.txt",
    "worker-watch/index.js",
}
FREE_LIMIT_PAGES = {
    "index.html",
    "site/index.html",
    "site/da/index.html",
    "site/de/index.html",
    "site/fr/index.html",
    "site/scan/index.html",
    "site/da/scan/index.html",
    "site/de/scan/index.html",
    "site/fr/scan/index.html",
    "site/llms.txt",
    "site/llms-full.txt",
    "site/blog/shopify-gdpr-compliance-guide/index.html",
    "site/blog/woocommerce-gdpr-compliance-guide/index.html",
    "site/blog/wix-gdpr-compliance-guide/index.html",
    "site/pricing/index.html",
    "site/da/pricing/index.html",
    "site/de/pricing/index.html",
    "site/fr/pricing/index.html",
    "site/how-it-works/index.html",
    "site/gdpr-scanner-free/index.html",
    "site/blog/cookiebot-alternative-2026/index.html",
    "site/blog/best-free-gdpr-compliance-checkers-2026/index.html",
    "site/vs/complianz/index.html",
    "site/vs/cookiebot/index.html",
    "site/vs/enzuzo/index.html",
    "site/vs/iubenda/index.html",
    "site/vs/onetrust/index.html",
    "site/vs/osano/index.html",
    "site/vs/termly/index.html",
    "site/vs/usercentrics/index.html",
}
PLUGIN_PARITY_PAGES = {
    "index.html",
    "site/plugin/index.html",
    "site/check-eu-compliance/index.html",
}
PLUGIN_TRUTH_PAGES = {
    "plugin/eucomply.php",
    "site/plugin/eucomply.php",
    "plugin/readme.txt",
    "site/plugin/readme.txt",
}
COMPARISON_TRUTH_PAGES = {
    "site/compare/index.html",
    "site/pro/vs-cookiebot/index.html",
    "site/pro/vs-iubenda/index.html",
    "site/pro/vs-onetrust/index.html",
    "site/pro/vs-osano/index.html",
    "site/pro/vs-termly/index.html",
}
STATIC_SCAN_PAGES = {
    "site/cookie-banner-check/index.html",
    "site/consent-mode-v2-check/index.html",
    "site/gdpr-compliance-check/index.html",
}
DORA_TRUTH_PAGES = {
    "site/compare/index.html",
    "site/blog/webflow-gdpr-compliance-guide/index.html",
    "site/vs/complianz/index.html",
    "site/vs/cookiebot/index.html",
    "site/vs/enzuzo/index.html",
    "site/vs/iubenda/index.html",
    "site/vs/onetrust/index.html",
    "site/vs/osano/index.html",
    "site/vs/termly/index.html",
    "site/vs/usercentrics/index.html",
    "eucomply-scanner/README.md",
    "eucomply-scanner/engine/index.js",
    "shared/scan-engine.js",
}
PRODUCT_TRUTH_RULES = (
    ("overbroad no-storage claim", re.compile(r"(?i)nothing (?:is )?stored|no account, nothing stored|results? (?:is|are) not stored anywhere|intet gemmes|nichts wird gespeichert|rien n’est conservé|conservé nulle part")),
    ("unlimited free-scan claim", re.compile(r"(?i)unlimited (?:one-off )?scans?|free, unlimited|no limits|unlimited with the Pro license")),
    ("plugin parity claim", re.compile(r"(?i)same checks, run from|same checks are also available|same checks plus WordPress-specific|same Pro upgrade")),
    ("unsupported script-blocking verification", re.compile(r"(?i)script blocking|GDPR-compliant script blocking")),
    ("unsupported PDF scorecard", re.compile(r"(?i)shareable PNG scorecard|penetration testing signals|WCAG-level page checks")),
    ("outdated rate-limit copy", re.compile(r"(?i)20 requests per 10 minutes|20 scans per 10 minutes")),
    ("legacy Pro link in monitoring mail", re.compile(r"(?i)auditedwp\.pages\.dev/pro/")),
)
GENERAL_TRUTH_RULES = (
    ("stale paid ebook CTA", re.compile(r"(?i)Get the ebook[^\n<]{0,40}\$14\.99")),
    ("persisted-result overclaim", re.compile(r"(?i)shareable result link|resultlink, der kan deles|teilbarer ergebnis-link|lien de résultat partageable")),
    (
        "free guide marked as paid template",
        re.compile(
            r"(?i)(?:guide and checklists|guide og tjeklister|leitfaden und checklisten|guide et checklists)</td><td>(?:Yes|Ja|Oui)</td><td>[^<]+</td><td>(?:Yes|Ja|Oui)</td>"
        ),
    ),
)
STATIC_SCAN_TRUTH_RULES = (
    ("runtime tracking overclaim", re.compile(r"(?i)pre-consent tracking|trackers before consent|reject-button reality")),
)
DORA_TRUTH_RULES = (
    ("unsupported DNS/email-authentication check", re.compile(r"(?i)email authentication, failover|email authentication \(SPF, DKIM, DMARC\)|email-authentication \(SPF/DKIM/DMARC\)|resilience signals \(email auth, failover\)")),
)
OG_IMAGES = {
    "site/pro/index.html": "site/images/og/pro.png",
    "site/pricing/index.html": "site/images/og/pricing.png",
    "site/da/pricing/index.html": "site/images/og/da-pricing.png",
    "site/de/pricing/index.html": "site/images/og/de-pricing.png",
    "site/fr/pricing/index.html": "site/images/og/fr-pricing.png",
}
PRICE_FORMS = {
    "en": (
        r"\b79\s+USD\s+per\s+website\s+per\s+year\b",
        r"\b79\s+USD\s+a\s+year\s+per\s+website\b",
    ),
    "da": (
        r"\b79\s+USD\s+pr\.?\s+web(?:sted|site)s?\s+pr\.?\s+år\b",
        r"\b79\s+USD\s+om\s+året\s+pr\.?\s+websites?\b",
    ),
    "de": (
        r"\b79\s+USD\s+pro\s+Website\s+pro\s+Jahr\b",
        r"\b79\s+USD\s+pro\s+Jahr\s+und\s+Website\b",
        r"\b79\s+USD\s+(?:je|pro)\s+Website\s+(?:und\s+)?pro\s+Jahr\b",
    ),
    "fr": (
        r"\b79\s+USD\s+par\s+site(?:\s+web)?\s*,?\s+et\s+par\s+an\b",
        r"\b79\s+USD\s+par\s+an\s+et\s+par\s+site(?:\s+web)?\b",
    ),
}
CONTRADICTORY_PRICE = re.compile(
    r"\b(?:EUComply\s+)?Pro\b[^\n.!?]{0,70}\b(?:costs?|priced at|price is)\s+(?:\$|USD\s*|EUR\s*|DKK\s*)?(?!79\b)\d+\b|"
    r"\b(?:EUComply\s+)?Pro\b[^\n.!?]{0,50}\b(?:at|for)\s+(?:\$|USD\s*|EUR\s*|DKK\s*)(?!79\b)\d+\b",
    re.I,
)
CLAIMS: Tuple[Tuple[str, Pattern[str]], ...] = (
    (
        "daily monitoring or rescans",
        re.compile(
            r"\b(?:daily|nightly|every\s+day|each\s+day|24\s*/\s*7|continuous(?:ly)?)\b[^\n.!?;]{0,60}\b(?:rescan(?:s|ning)?|re-?scans?|scans?|site\s+checks?|website\s+checks?|monitor(?:s|ing|ed)?)\b|"
            r"\b(?:rescan(?:s|ning)?|re-?scans?|scans?|site\s+checks?|website\s+checks?|monitor(?:s|ing|ed)?)\b[^\n.!?;]{0,60}\b(?:daily|nightly|every\s+day|each\s+day|24\s*/\s*7|continuous(?:ly)?)\b|"
            r"\b(?:täglich\w*|jeden\s+tag|taeglich\w*)\b[^\n.!?;]{0,60}\b(?:scan\w*|prüf\w*|überwach\w*|monitor\w*)\b|"
            r"\b(?:scan\w*|prüf\w*|überwach\w*|monitor\w*)\b[^\n.!?;]{0,60}\b(?:täglich\w*|jeden\s+tag|taeglich\w*)\b|"
            r"\b(?:daglig\w*|hver\s+dag)\b[^\n.!?;]{0,60}\b(?:scan\w*|tjek\w*|overvåg\w*|monitor\w*)\b|"
            r"\b(?:scan\w*|tjek\w*|overvåg\w*|monitor\w*)\b[^\n.!?;]{0,60}\b(?:daglig\w*|hver\s+dag)\b|"
            r"\b(?:chaque\s+jour|quotidien\w*|tous\s+les\s+jours)\b[^\n.!?;]{0,60}\b(?:scan\w*|surveill\w*|vérifi\w*|control\w*)\b|"
            r"\b(?:scan\w*|surveill\w*|vérifi\w*|control\w*)\b[^\n.!?;]{0,60}\b(?:chaque\s+jour|quotidien\w*|tous\s+les\s+jours)\b",
            re.I,
        ),
    ),
    (
        "automatic rechecks",
        re.compile(
            r"\bautomatic(?:ally)?\s+(?:daily\s+)?(?:rechecks?|rescans?|scans?)\b|"
            r"\b(?:rechecks?|rescans?|scans?)\s+automatically\b",
            re.I,
        ),
    ),
    (
        "30-day Pro history",
        re.compile(
            r"\b(?:30[- ]days?|last\s+30\s+days?|past\s+30\s+days?)\b[^\n.!?;]{0,60}\b(?:history|historical|trend|record|score)\b|"
            r"\b(?:six[- ]month|6[- ]month)\s+history\b|"
            r"\b(?:history|historical|trend|record|score)\b[^\n.!?;]{0,60}\b(?:30[- ]days?|last\s+30\s+days?|past\s+30\s+days?)\b|"
            r"\b30\s+(?:dage|dages|dagen|Tage|Tagen)\b[^\n.!?;]{0,60}\b(?:scanningshistorik\w*|(?:[a-zäöüß]+\s+){0,3}(?:historik\w*|verlauf\w*|trend\w*|record\w*|score\w*))\b|"
            r"\b(?:historik\w*|verlauf\w*|trend\w*|record\w*|score\w*)\b[^\n.!?;]{0,60}\b30\s+(?:dage|dagen|Tage|Tagen)\b|"
            r"\b(?:historique|historique\w*|tendance|record|score)\b[^\n.!?;]{0,60}\b30\s+jours\b|"
            r"\b30\s+jours\b[^\n.!?;]{0,60}\b(?:historique\w*|tendance|record|score)\b",
            re.I,
        ),
    ),
    (
        "pass-to-fail alerts",
        re.compile(
            r"\b(?:pass(?:ed|ing)?|bestået|bestående|bestanden|erfolgreich|bestehend|réussi|réussie)\b[^\n.!?;]{0,60}\b(?:to|til|zu|→|->|à|a|wechselt\w*|passage|de|devient\w*|becomes?)\b[^\n.!?;]{0,40}\b(?:fail\w*|fejl\w*|fehlgeschlagen|fehlschlag\w*|handlungsbedarf|échec\w*|échou\w*|red|rot|rouge)\b|"
            r"\b(?:green|grün|gruen|vert)\b[^\n.!?;]{0,40}\b(?:to|til|→|->|à|a|wechselt\w*|passage|de)\b[^\n.!?;]{0,40}\b(?:red|rot|rouge|fehlgeschlagen|échec\w*)\b",
            re.I,
        ),
    ),
    (
        "runtime PDF reports",
        re.compile(
            r"\b(?:runtime|downloadable|auditor[- ]ready|auditor\s+ready|client[- ]ready|printable)\s+(?:PDF\s+)?reports?\b|"
            r"\bgenerated\s+(?:PDF|compliance|audit|client|auditor)\s+reports?\b|"
            r"\bPDF\s+(?:compliance\s+|audit\s+|client\s+|auditor\s+)?reports?\b|"
            r"\bPDF\s+exports?\b|"
            r"\breports?\b[^\n.!?;]{0,50}\bas\s+(?:an?\s+)?PDF\b|"
            r"\b(?:runtime|generated|downloadable)\b[^\n.!?;]{0,50}\bPDF\b|"
            r"\bPDF-(?:Bericht\w*|rapport\w*)\b|"
            r"\b(?:rapport\w*|bericht\w*)\b[^\n.!?;]{0,50}\b(?:als|comme|som|au\s+format)\s+(?:un\s+)?PDF\b",
            re.I,
        ),
    ),
    (
        "live verification claims",
        re.compile(
            r"\b(?:live|real[- ]time|verifiable|verified|verification|public|offentlig\w*|verifizierbar\w*|vérifiable\w*|en\s+direct|aktuell\w*|letzten\w*|senest\w*)\b[^\n.!?;]{0,35}\b(?:badge|score|scan\s+record|scanregistrering\w*|scan[- ]vermerk\w*)\b|"
            r"\b(?:current|latest|actual|aktuell\w*|letzten\w*|senest\w*)\s+(?:public\s+)?scan\s+record\b|"
            r"\b(?:badge|score|scan\s+record|scanregistrering\w*|scan[- ]vermerk\w*)\b[^\n.!?;]{0,35}\b(?:live|real[- ]time|verifiable|verified|verification|public|offentlig\w*|verifizierbar\w*|vérifiable\w*|en\s+direct|aktuell\w*|letzten\w*|senest\w*)\b",
            re.I,
        ),
    ),
    (
        "customer dashboard or account",
        re.compile(
            r"\b(?:EUComply\s+)?Pro\s+(?:provides?|includes?|offers?|has)\s+(?:an?\s+)?(?:customer\s+|client\s+|hosted\s+)?(?:dashboard|portal|account|account\s+area|login|log[- ]in)\b|"
            r"\b(?:customer|client|hosted|your|Pro)\s+(?:[- ]?\s*)(?:dashboard|portal|account|account\s+area|login|log[- ]in)\b|"
            r"\b(?:log\s+in\s+to\s+your|your)\s+EUComply\s+(?:customer\s+|client\s+|hosted\s+)?(?:dashboard|portal|account|login)\b|"
            r"\bdashboard\s+for\s+(?:customers|clients|your\s+sites?)\b|"
            r"\b(?:kunde|kunder|kunden|kunde-)\s*[- ]?\s*(?:dashboard|portal|konto|bereich|login)\b|"
            r"\b(?:kundedashboard|kundeportal|kundenportal|kundenkonto|kundenbereich)\b|"
            r"\b(?:espace\s+client|portail\s+client|compte\s+client|tableau\s+de\s+bord\s+client)\b",
            re.I,
        ),
    ),
    (
        "priority support",
        re.compile(r"\b(?:priority|prioritized|premium)\s+support\b", re.I),
    ),
    (
        "multi-site or unlimited-domain entitlement",
        re.compile(
            r"\bunlimited[- ]domains?\b|"
            r"\b(?:unlimited\s+(?:number\s+of\s+)?|unbegrenzte?\s+(?:anzahl\s+)?|ubegrænset\s+(?:antal\s+)?|nombre\s+illimité\s+de\s+)(?:sites|websites|domains|domains|websteder|domæner|domainen|seiten|domaines)\b|"
            r"\b(?:multiple|multi[- ]site|several|mehrere|plusieurs|flere)\b[^\n.!?;]{0,30}\b(?:sites|websites|domains|domains|websteder|domæner|domainen|seiten|domaines)\b|"
            r"\b(?:two|three|four|five|ten|2|3|4|5|10)\s+(?:sites?|websites?|domains?|websteder|domæner\w*|domains?|domainen|seiten|domaines)\b|"
            r"\ball\s+(?:your\s+)?(?:sites?|websites?|domains?)\b",
            re.I,
        ),
    ),
    (
        "templates included",
        re.compile(
            r"\b(?:full\s+|complete\s+)?templates?\b[^\n.!?;]{0,40}\b(?:included|comes?|comes\s+with|unlocks?|includes?)\b|"
            r"\b(?:includes?|unlocks?|comes\s+with|kommer\s+med)\b[^\n.!?;]{0,50}\b(?:full\s+|complete\s+)?templates?\b|"
            r"\b(?:skabeloner|dokumentskabeloner)\b[^\n.!?;]{0,40}\b(?:inkluderet|med\w*|låser\s+op)\b|"
            r"\b(?:inkluderer|inkluderet|låser\s+op)\b[^\n.!?;]{0,50}\b(?:dokument\w*)?skabelon\w*\b|"
            r"\b(?:Vorlagen|Dokumentvorlagen)\b[^\n.!?;]{0,40}\b(?:inklusive|inkludiert|enthalten\w*|dabei)\b|"
            r"\b(?:inkludiert|inklusive|enthält|enthalten)\b[^\n.!?;]{0,50}\b(?:Dokument\w*)?vorlagen\w*\b|"
            r"\b(?:modèles?\s+(?:de\s+documents?\s+)?)\b[^\n.!?;]{0,40}\b(?:inclus\w*|fourni\w*|offert\w*)\b|"
            r"\b(?:inclut|offre|débloque)\b[^\n.!?;]{0,50}\b(?:modèles?\s+(?:de\s+documents?\s+)?)\b",
            re.I,
        ),
    ),
    (
        "unsupported proof or compliance-monitor positioning",
        re.compile(
            r"\bauditor[- ]ready\b|\bdocumented\s+proof\b|\bcompliance\s+monitor\b|\bmonitoring\s+depth\b|"
            r"\bAny\s+URL,?\s+no\s+install\s+needed\b|\bScanned\s+by\s+EUComply\b|"
            r"\bdokumenteret\w*\s+bevis\b|\bdokumentiert\w*\s+nachweis\b|\bpreuve\s+documentée\b",
            re.I,
        ),
    ),
    (
        "PayPal checkout promise",
        re.compile(
            r"\bPayPal\b[^\n.!?;]{0,50}\b(?:checkout|payment)\b[^\n.!?;]{0,30}\b(?:planned|coming\s+later|available|supported)\b|"
            r"\b(?:planned|coming\s+later)\b[^\n.!?;]{0,30}\bPayPal\s+(?:checkout|payment)\b",
            re.I,
        ),
    ),
    (
        "Merchant of Record claim",
        re.compile(r"\bMerchant\s+of\s+Record\b", re.I),
    ),
    (
        "Pro refund promise",
        re.compile(r"\b(?:14[- ]day|risk[- ]free)\s+(?:money[- ]back|refund)\b", re.I),
    ),
    (
        "broken Pro grammar",
        re.compile(
            r"\b(?:Pro|license)\s+get\b|\band\s+get\s+editable\b|\bget\s+editable\b|"
            r"\b(?:tools|document\s+tools)\s+of\.|\bdocument\s+tools\s+at\.",
            re.I,
        ),
    ),
)
PRO_CONTEXT = re.compile(
    r"\bEUComply\s+Pro\b|\bPro\b[^\n.!?;]{0,50}\b(?:license|licence|plugin|subscription|plan|tier|account|portal|dashboard|scope|product)\b|"
    r"\b(?:current|paid|premium|professional|professionel|professionell)\s+Pro\b|"
    r"\bPro\s+(?:costs?|includes?|provides?|offers?|covers?|supports?|is|has|unlocks?|creates?|manages?|:)\b|"
    r"\b(?:professionel|professionell)\b",
    re.I,
)
OTHER_PRODUCTS = re.compile(
    r"\b(?:OneTrust|Cookiebot|CookieYes|iubenda|Termly|Osano|Enzuzo|Complianz|Usercentrics)\b",
    re.I,
)
ROADMAP = re.compile(
    r"\b(?:planned(?:\s+features?)?|roadmap|future|coming\s+later)\b|"
    r"\b(?:geplant\w*|roadmap|zukünftig\w*|später)\b|"
    r"\b(?:planlagt\w*|roadmap|fremtid\w*|senere)\b|"
    r"\b(?:prévu\w*|roadmap|futur\w*|plus\s+tard)\b",
    re.I,
)
ROADMAP_DISCLAIMER = re.compile(
    r"\b(?:not\s+(?:included|available|part)|excluded)\b|"
    r"\b(?:geplant\w*|roadmap|zukünftig\w*|später)\b[^\n.!?;]{0,80}\bnicht\s+(?:enthalten|verfügbar)\b|"
    r"\b(?:nicht\s+(?:enthalten|verfügbar))\b|"
    r"\b(?:ikke\s+(?:inkluderet|tilgængelig|en\s+del))\b|"
    r"\b(?:non\s+(?:inclus\w*|disponible\w*)|n[’']est\s+pas)\b",
    re.I,
)
PRESENT_CLAIM = re.compile(
    r"\b(?:EUComply\s+)?Pro\s+(?:includes?|provides?|offers?|has|unlocks?|delivers?)\b|"
    r"\b(?:included|available|active|live)\s+(?:today|now)\b",
    re.I,
)
CONCEPT_LABEL = re.compile(
    r"\b(?:illustrative|static\s+(?:sample|concept)|concept\s+(?:demo|sample)|future)\b|"
    r"\b(?:illustrativ|futur|exemple|konzept)\w*\b",
    re.I,
)
ROADMAP_BREAK = re.compile(
    r"\b(?:aside|but|however|although|though|while|yet|nevertheless|nonetheless|so|therefore|thus|hence)\b|"
    r"\b(?:deshalb|darum|daher)\b|\b(?:donc|par\s+conséquent)\b",
    re.I,
)
NEGATIVE_BEFORE = re.compile(
    r"(?:\bdoes\s+not|\bdo\s+not|\bdid\s+not|\bis\s+not|\bare\s+not|\bisn't|\baren't|\bnot)\b[^\n.!?;]{0,70}$|"
    r"\b(?:no|contains?\s+no|has\s+no|have\s+no|offers?\s+no|includes?\s+no|provides?\s+no)\s*$|\bneither\b[^\n.!?;]{0,50}$|"
    r"\binstead\s+of\s+(?:an?\s+)?$|"
    r"\b(?:ikke\s+(?:inkluderet|tilgængelig|en\s+del)|ikke\s+et|ikke\s+en)\b[^\n.!?;]{0,70}$|"
    r"\b(?:nicht\s+(?:enthalten|verfügbar|enthalten)|kein\w*|erstellt\s+kein\w*)\b[^\n.!?;]{0,70}$|"
    r"\b(?:non\s+(?:inclus\w*|disponible\w*)|n[’']est\s+pas|ne\s+crée\s+pas)\b[^\n.!?;]{0,70}$",
    re.I,
)
NEGATIVE_AFTER = re.compile(
    r"^\s*(?:[^A-Za-zÀ-ÿ0-9]{0,12})(?:\b(?:is|are)\s+)?\b(?:not\s+(?:included|available|part)|excluded|isn't|aren't)\b|"
    r"^\s*(?:[^A-Za-zÀ-ÿ0-9]{0,12})(?:\b(?:does|do)\s+not\s+)?(?:show|provide|include|offer|support)\b|"
    r"^\s*(?:[^A-Za-zÀ-ÿ0-9]{0,12})(?:no|nej|nein|non)\b|"
    r"^\s*(?:\b(?:er|ist)\s+)?nicht\s+(?:enthalten|verfügbar|enthalten)\b|"
    r"^\s*ikke\s+(?:inkluderet|tilgængelig|en\s+del)\b|"
    r"^\s*(?:n[’']est\s+pas|non\s+(?:inclus\w*|disponible\w*))",
    re.I,
)
SHARED_NEGATIVE = re.compile(
    r"\b(?:is|are)\s+not\s+(?:included|available|part)\b|"
    r"\b(?:er|sind)\s+nicht\s+(?:enthalten|verfügbar)\b|"
    r"\ber\s+ikke\s+(?:inkluderet|tilgængelig)\b|"
    r"\best\s+(?:non\s+inclus\w*|n[’']est\s+pas)\b",
    re.I,
)


@dataclass
class TextBlock:
    text: str
    line: int
    kind: str = "text"
    forced: bool = False


@dataclass
class Cell:
    text: str
    line: int


@dataclass
class TableData:
    rows: List[Tuple[List[Cell], int]] = field(default_factory=list)


@dataclass
class ScriptData:
    content: str
    script_type: str
    line: int


@dataclass
class HtmlDocument:
    blocks: List[TextBlock]
    scripts: List[ScriptData]
    links: List[Tuple[str, Dict[str, str], int]]
    meta: Dict[str, str]
    tables: List[TableData]
    product_state: str
    h1: str

    def claim_blocks(self, relative: str) -> List[TextBlock]:
        result = list(self.blocks)
        result.extend(table_claim_blocks(relative, self.tables))
        for script in self.scripts:
            script_type = script.script_type.lower()
            if script_type == "application/ld+json" or script_type.endswith("+json"):
                try:
                    value = json.loads(html.unescape(script.content))
                except (json.JSONDecodeError, TypeError):
                    continue
                for text in json_strings(value):
                    result.append(TextBlock(text, script.line, "json"))
            elif script.content:
                for value_text in javascript_strings(script.content):
                    result.append(TextBlock(value_text, script.line, "javascript"))
        return result


class SiteParser(HTMLParser):
    BLOCK_TAGS = {
        "address", "article", "aside", "blockquote", "button", "caption", "dd", "div", "dl", "dt",
        "figcaption", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "li",
        "main", "nav", "ol", "option", "p", "pre", "section", "summary", "table", "td", "th", "tr", "ul",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: List[TextBlock] = []
        self.scripts: List[ScriptData] = []
        self.links: List[Tuple[str, Dict[str, str], int]] = []
        self.meta: Dict[str, str] = {}
        self.tables: List[TableData] = []
        self.product_state = ""
        self.h1 = ""
        self._parts: List[str] = []
        self._line = 1
        self._table_stack: List[TableData] = []
        self._row: Optional[List[Cell]] = None
        self._row_line = 1
        self._cell_parts: Optional[List[str]] = None
        self._cell_line = 1
        self._script_parts: Optional[List[str]] = None
        self._script_type = ""
        self._script_line = 1
        self._style_depth = 0
        self._h1_parts: Optional[List[str]] = None
        self._h1_line = 1

    def _attrs(self, attrs: Sequence[Tuple[str, Optional[str]]]) -> Dict[str, str]:
        return {key.lower(): value or "" for key, value in attrs}

    def _start_line(self) -> int:
        return self.getpos()[0]

    def _flush(self) -> None:
        text = normalize(" ".join(self._parts))
        if text:
            self.blocks.append(TextBlock(text, self.getpos()[0]))
        self._parts = []

    def handle_starttag(self, tag: str, attrs: Sequence[Tuple[str, Optional[str]]]) -> None:
        tag = tag.lower()
        values = self._attrs(attrs)
        line = self._start_line()
        if values.get("data-product-state"):
            self.product_state = values["data-product-state"].strip().lower()
        if tag == "meta":
            name = values.get("name", "").lower()
            if name and values.get("content"):
                self.meta[name] = values["content"]
        if tag in {"a", "link"}:
            self.links.append((tag, values, line))
        if not self._table_stack:
            for name in ("content", "alt", "title", "aria-label", "placeholder", "value", "data-description", "data-label"):
                value = values.get(name, "").strip()
                if value:
                    self.blocks.append(TextBlock(value, line, "attribute"))
        if tag == "script":
            self._flush()
            self._script_parts = []
            self._script_type = values.get("type", "")
            self._script_line = line
            return
        if tag == "style":
            self._flush()
            self._style_depth += 1
            return
        if tag == "table":
            self._flush()
            table = TableData()
            self._table_stack.append(table)
            self.tables.append(table)
            return
        if tag == "tr" and self._table_stack:
            self._flush()
            self._row = []
            self._row_line = line
            return
        if tag in {"td", "th"} and self._table_stack:
            self._cell_parts = []
            self._cell_line = line
            return
        if tag == "h1":
            self._flush()
            self._h1_parts = []
            self._h1_line = line
        if tag in self.BLOCK_TAGS:
            self._flush()

    def handle_startendtag(self, tag: str, attrs: Sequence[Tuple[str, Optional[str]]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "script" and self._script_parts is not None:
            self.scripts.append(ScriptData("".join(self._script_parts), self._script_type, self._script_line))
            self._script_parts = None
            self._script_type = ""
            return
        if tag == "style" and self._style_depth:
            self._style_depth -= 1
            return
        if tag in {"td", "th"} and self._cell_parts is not None:
            text = normalize(" ".join(self._cell_parts))
            if self._row is not None:
                self._row.append(Cell(text, self._cell_line))
            self._cell_parts = None
            return
        if tag == "tr" and self._row is not None and self._table_stack:
            self._table_stack[-1].rows.append((self._row, self._row_line))
            self._row = None
            return
        if tag == "table" and self._table_stack:
            self._table_stack.pop()
            return
        if tag == "h1" and self._h1_parts is not None:
            self.h1 = normalize(" ".join(self._h1_parts))
            self._h1_parts = None
            self._flush()
            return
        if tag in self.BLOCK_TAGS:
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._script_parts is not None:
            self._script_parts.append(data)
            return
        if self._style_depth:
            return
        if self._cell_parts is not None:
            self._cell_parts.append(data)
            return
        if self._table_stack:
            return
        self._parts.append(data)
        if self._h1_parts is not None:
            self._h1_parts.append(data)

    def close(self) -> None:
        super().close()
        self._flush()


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", html.unescape(text))).strip()


def parse_html(text: str) -> HtmlDocument:
    parser = SiteParser()
    parser.feed(text)
    parser.close()
    return HtmlDocument(parser.blocks, parser.scripts, parser.links, parser.meta, parser.tables, parser.product_state, parser.h1)


def json_strings(value) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from json_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from json_strings(item)


def javascript_strings(source: str) -> List[str]:
    result: List[str] = []
    index = 0
    length = len(source)
    while index < length:
        char = source[index]
        if char not in {'"', "'", "`"}:
            index += 1
            continue
        quote = char
        index += 1
        value: List[str] = []
        while index < length:
            char = source[index]
            if char == "\\" and index + 1 < length:
                value.append(source[index + 1])
                index += 2
                continue
            if char == quote:
                index += 1
                break
            value.append(char)
            index += 1
        result.append("".join(value))
    return result


def context_relative(relative: str) -> str:
    return relative[5:] if relative.startswith("site/") else relative


def is_pro_page(relative: str) -> bool:
    normalized = relative.replace("\\", "/")
    return normalized in FORCED_PRO_PAGES


def target_header(value: str, relative: str) -> bool:
    text = normalize(value).lower()
    if "eucomply" in text:
        return True
    buying = context_relative(relative) in BUYING_PAGES
    if buying and (text == "pro" or re.match(r"^pro(?:\s|[-])", text)):
        return True
    return False


def table_claim_blocks(relative: str, tables: Sequence[TableData]) -> List[TextBlock]:
    result: List[TextBlock] = []
    for table in tables:
        if not table.rows:
            continue
        header = table.rows[0][0]
        indexes = [index for index, cell in enumerate(header) if target_header(cell.text, relative)]
        if not indexes:
            continue
        for cells, line in table.rows[1:]:
            if not cells:
                continue
            feature = cells[0].text
            for index in indexes:
                if index >= len(cells):
                    continue
                value = cells[index].text
                if re.fullmatch(r"(?:—|–|-|✗|×|x|no|nej|nein|non)(?:\.|$)", value, re.I):
                    continue
                result.append(TextBlock("EUComply Pro " + feature + " Result: " + value, cells[index].line, "table", True))
    return result


def claim_applies(relative: str, label: str, text: str) -> bool:
    if label in {"PayPal checkout promise", "Merchant of Record claim"}:
        return True
    if label == "Pro refund promise":
        return is_pro_page(relative) and bool(re.search(r"\bEUComply\b", text, re.I))
    if is_pro_page(relative):
        return True
    if relative in MONITORING_PAGES and label == "pass-to-fail alerts":
        return True
    if OTHER_PRODUCTS.search(text) and not re.search(r"\bEUComply\b", text, re.I):
        return False
    return False


def claim_exempt(segment: str, match: re.Match) -> bool:
    if re.search(r"\b(?:not|never|isn't|aren't|ikke|nicht|non)\b", match.group(0), re.I):
        return True
    start, end = match.span()
    prefix = segment[max(0, start - 120):start]
    suffix = segment[end:end + 120]
    disclaimer = ROADMAP_DISCLAIMER.search(segment)
    if disclaimer and not PRESENT_CLAIM.search(segment[disclaimer.end():]):
        return True
    if CONCEPT_LABEL.search(segment) and not PRESENT_CLAIM.search(segment):
        return True
    roadmap_match = ROADMAP.search(segment)
    if roadmap_match and roadmap_match.end() <= start:
        between = segment[roadmap_match.end():start]
        if len(between) <= 20 and not ROADMAP_BREAK.search(between):
            return True
    if SHARED_NEGATIVE.search(prefix) or SHARED_NEGATIVE.search(suffix):
        return True
    return bool(NEGATIVE_BEFORE.search(prefix) or NEGATIVE_AFTER.search(prefix) or NEGATIVE_AFTER.search(suffix))


def claim_findings_for_blocks(relative: str, blocks: Sequence[TextBlock], force_pro: bool = False) -> List[str]:
    findings: List[str] = []
    seen: Set[Tuple[int, str]] = set()
    for block in blocks:
        text = normalize(block.text)
        if not text:
            continue
        if block.kind == "table":
            result = text.rsplit(" Result: ", 1)[-1]
            if NEGATIVE_AFTER.search(result) or SHARED_NEGATIVE.search(result):
                continue
        context_active = force_pro or block.forced
        for segment in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-Þ])|;\s+|\s+(?i:but|aber|mais)\s+", text):
            segment = segment.strip()
            if not segment:
                continue
            context_match = PRO_CONTEXT.search(segment)
            inherited_context = context_active and bool(re.match(r"^(?:it|they|this|those|these)\b", segment, re.I))
            for label, pattern in CLAIMS:
                for match in pattern.finditer(segment):
                    segment_context = bool(
                        context_match
                        and context_match.start() < match.end()
                        and match.start() - context_match.start() <= 80
                    )
                    if label == "Pro refund promise" and not claim_applies(relative, label, segment):
                        continue
                    if not inherited_context and not segment_context and not claim_applies(relative, label, segment):
                        continue
                    if claim_exempt(segment, match):
                        continue
                    key = (block.line, label)
                    if key in seen:
                        break
                    seen.add(key)
                    findings.append(f"{relative}:{block.line}: {label}: {segment}")
                    break
            if context_match:
                context_active = True
    return findings


def text_findings(relative: str, text: str) -> List[str]:
    document = parse_html(text)
    blocks = list(document.blocks)
    blocks.extend(table_claim_blocks(relative, document.tables))
    for script in document.scripts:
        script_type = script.script_type.lower()
        if script_type == "application/ld+json" or script_type.endswith("+json"):
            try:
                value = json.loads(html.unescape(script.content))
            except (json.JSONDecodeError, TypeError):
                continue
            for value_text in json_strings(value):
                blocks.append(TextBlock(value_text, script.line, "json"))
        elif script.content:
            for value_text in javascript_strings(script.content):
                blocks.append(TextBlock(value_text, script.line, "javascript"))
    return claim_findings_for_blocks(relative, blocks)


def raw_blocks(relative: str, text: str) -> List[TextBlock]:
    path = Path(relative)
    if path.suffix.lower() == ".json":
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            return [TextBlock(text, 1, "text")]
        return [TextBlock(value_text, 1, "json") for value_text in json_strings(value)]
    if path.suffix.lower() == ".js":
        return [TextBlock(value, 1, "javascript") for value in javascript_strings(text)]
    return [TextBlock(line, number, "text") for number, line in enumerate(text.splitlines(), 1) if line.strip()]


def raw_claim_findings(relative: str, text: str) -> List[str]:
    if Path(relative).suffix.lower() in {".html", ".htm", ".svg"}:
        return text_findings(relative, text)
    return claim_findings_for_blocks(relative, raw_blocks(relative, text))


def product_truth_findings(relative: str, text: str) -> List[str]:
    findings: List[str] = []
    if relative in FREE_LIMIT_PAGES:
        for label, pattern in PRODUCT_TRUTH_RULES[:2]:
            if pattern.search(text):
                findings.append(f"{relative}: {label}")
    if relative in PLUGIN_PARITY_PAGES:
        for label, pattern in PRODUCT_TRUTH_RULES[2:3]:
            if pattern.search(text):
                findings.append(f"{relative}: {label}")
    if relative in PLUGIN_TRUTH_PAGES:
        for label, pattern in PRODUCT_TRUTH_RULES[3:4]:
            if pattern.search(text):
                findings.append(f"{relative}: {label}")
    if relative in COMPARISON_TRUTH_PAGES:
        for label, pattern in PRODUCT_TRUTH_RULES[4:5]:
            if pattern.search(text):
                findings.append(f"{relative}: {label}")
    if relative == "site/terms/index.html":
        for label, pattern in PRODUCT_TRUTH_RULES[5:6]:
            if pattern.search(text):
                findings.append(f"{relative}: {label}")
    if relative == "worker-watch/index.js":
        for label, pattern in PRODUCT_TRUTH_RULES[6:7]:
            if pattern.search(text):
                findings.append(f"{relative}: {label}")
    for label, pattern in GENERAL_TRUTH_RULES:
        if pattern.search(text):
            findings.append(f"{relative}: {label}")
    if relative in STATIC_SCAN_PAGES:
        for label, pattern in STATIC_SCAN_TRUTH_RULES:
            if pattern.search(text):
                findings.append(f"{relative}: {label}")
    if relative in DORA_TRUTH_PAGES:
        for label, pattern in DORA_TRUTH_RULES:
            if pattern.search(text):
                findings.append(f"{relative}: {label}")
    if relative == "site/pro/sample-report/index.html":
        if re.search(r"(?i)meets basic DORA|compliant with European Accessibility", text):
            findings.append(f"{relative}: unsupported compliance determination in static sample")
    return findings


def price_findings(language: str, text: str) -> List[str]:
    value = normalize(text)
    if CONTRADICTORY_PRICE.search(value):
        return [f"contradictory Pro price in {language}"]
    if any(re.search(pattern, value, re.I) for pattern in PRICE_FORMS[language]):
        return []
    return [f"expected exact 79 USD per website per year entitlement in {language}"]


def expected_alternates(relative: str) -> Dict[str, str]:
    page = "pro" if "/pro/" in f"/{relative}" or relative.startswith("pro/") else "pricing"
    paths = {"en": "", "da": "da/", "de": "de/", "fr": "fr/"}
    result = {language: f"https://eucomplypro.com/{prefix}{page}/" for language, prefix in paths.items()}
    result["x-default"] = result["en"]
    return result


def stripe_cta_findings(relative: str, text: str) -> List[str]:
    document = parse_html(text)
    anchors = [(attrs, line) for tag, attrs, line in document.links if tag == "a"]
    purchase_links = [attrs.get("href", "") for attrs, _ in anchors if attrs.get("href") == PRO_LINK]
    findings: List[str] = []
    if len(purchase_links) != 1 or text.count(PRO_LINK) != 1:
        findings.append(f"{relative}: expected exactly one Pro Stripe CTA")
    for url in set(re.findall(r"https?://[^\s\"'<>]+", html.unescape(text))):
        normalized = url.rstrip(".,);")
        if any(host in normalized.lower() for host in ("buy.stripe.com", "lemonsqueezy.com", "gumroad.com")) and normalized != PRO_LINK:
            findings.append(f"{relative}: unexpected checkout CTA {normalized}")
    return findings


def buying_page_findings(relative: str, text: str) -> List[str]:
    language, canonical = BUYING_PAGES[relative]
    document = parse_html(text)
    findings: List[str] = []
    findings.extend(stripe_cta_findings(relative, text))
    canonical_links = [attrs.get("href", "") for tag, attrs, _ in document.links if tag == "link" and "canonical" in attrs.get("rel", "").lower().split()]
    if canonical_links != [canonical]:
        findings.append(f"{relative}: expected self-canonical {canonical}")
    hreflangs = {
        attrs.get("hreflang", ""): attrs.get("href", "")
        for tag, attrs, _ in document.links
        if tag == "link" and "alternate" in attrs.get("rel", "").lower().split() and attrs.get("hreflang")
    }
    expected = expected_alternates(relative)
    if hreflangs != expected:
        findings.append(f"{relative}: expected complete alternate map {expected}")
    if hreflangs.get(language) != canonical:
        findings.append(f"{relative}: incorrect self hreflang")
    all_text = " ".join(block.text for block in document.blocks)
    all_text += " " + " ".join(value for script in document.scripts for value in javascript_strings(script.content))
    if "WordPress" not in all_text or "HTML" not in all_text:
        findings.append(f"{relative}: missing current WordPress/HTML product truth")
    findings.extend(price_findings(language, all_text))
    return findings


def png_text_metadata(data: bytes) -> Tuple[Dict[str, str], int, int]:
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("invalid PNG signature")
    offset = 8
    metadata: Dict[str, str] = {}
    width = 0
    height = 0
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        chunk_type = data[offset + 4:offset + 8]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError("truncated PNG chunk")
        payload = data[offset + 8:offset + 8 + length]
        if chunk_type == b"IHDR" and length >= 8:
            width, height = struct.unpack(">II", payload[:8])
        elif chunk_type == b"tEXt":
            keyword, value = payload.split(b"\x00", 1)
            metadata[keyword.decode("latin-1")] = value.decode("latin-1")
        elif chunk_type == b"zTXt":
            keyword, rest = payload.split(b"\x00", 1)
            if not rest or rest[0] != 0:
                raise ValueError("invalid zTXt chunk")
            metadata[keyword.decode("latin-1")] = zlib.decompress(rest[1:]).decode("latin-1")
        elif chunk_type == b"iTXt":
            keyword, rest = payload.split(b"\x00", 1)
            compression_flag = rest[0]
            compression_method = rest[1]
            rest = rest[2:]
            _language, rest = rest.split(b"\x00", 1)
            _translated, text = rest.split(b"\x00", 1)
            if compression_flag:
                if compression_method != 0:
                    raise ValueError("invalid iTXt compression method")
                text = zlib.decompress(text)
            metadata[keyword.decode("latin-1")] = text.decode("utf-8")
        elif chunk_type == b"IEND":
            break
        offset = end
    return metadata, width, height


def page_copy(relative: str) -> Tuple[str, str]:
    path = ROOT / relative
    document = parse_html(path.read_text(encoding="utf-8"))
    return document.h1, html.unescape(document.meta.get("description", ""))


def og_image_findings() -> List[str]:
    findings: List[str] = []
    for page_relative, image_relative in OG_IMAGES.items():
        image_path = ROOT / image_relative
        page_path = ROOT / page_relative
        if not page_path.exists():
            findings.append(f"{page_relative}: missing source page for social image")
            continue
        if not image_path.exists():
            findings.append(f"{image_relative}: missing social image")
            continue
        try:
            title, description = page_copy(page_relative)
            metadata, width, height = png_text_metadata(image_path.read_bytes())
        except (OSError, UnicodeError, ValueError, zlib.error) as error:
            findings.append(f"{image_relative}: unreadable social image metadata: {error}")
            continue
        if (width, height) != (1200, 630):
            findings.append(f"{image_relative}: expected 1200x630 PNG")
        if metadata.get("Title") != title:
            findings.append(f"{image_relative}: Title metadata does not match page H1")
        if metadata.get("Description") != description:
            findings.append(f"{image_relative}: Description metadata does not match page meta description")
        for value in (metadata.get("Title", ""), metadata.get("Description", "")):
            findings.extend(claim_findings_for_blocks(page_relative, [TextBlock(value, 1, "image-metadata")]))
    return findings


def read_bytes(path: Path, label: str, findings: List[str]) -> Optional[bytes]:
    try:
        return path.read_bytes()
    except OSError as error:
        findings.append(f"{label}: cannot read required artifact: {error}")
        return None


def read_text(path: Path, label: str, findings: List[str]) -> Optional[str]:
    data = read_bytes(path, label, findings)
    if data is None:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        findings.append(f"{label}: invalid UTF-8: {error}")
        return None


def load_json(path: Path, label: str, findings: List[str]) -> Optional[dict]:
    text = read_text(path, label, findings)
    if text is None:
        return None
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        findings.append(f"{label}: invalid JSON: {error}")
        return None
    if not isinstance(value, dict):
        findings.append(f"{label}: expected a JSON object")
        return None
    return value


def artifact_findings() -> List[str]:
    findings: List[str] = []
    pairs = (
        (ROOT / "plugin/eucomply.php", SITE / "plugin/eucomply.php", "plugin PHP"),
        (ROOT / "plugin/readme.txt", SITE / "plugin/readme.txt", "plugin readme"),
        (ROOT / "update.json", SITE / "update.json", "update manifest"),
    )
    for source, deployed, label in pairs:
        source_bytes = read_bytes(source, f"artifacts: {label} source", findings)
        deployed_bytes = read_bytes(deployed, f"artifacts: {label} deployed copy", findings)
        if source_bytes is not None and deployed_bytes is not None and source_bytes != deployed_bytes:
            findings.append(f"artifacts: {label} source and deployed copy differ")
    plugin_text = read_text(ROOT / "plugin/eucomply.php", "artifacts: plugin PHP", findings)
    if plugin_text is not None:
        version_matches = set(re.findall(r"(?:Version:\s+|EUCOMPLY_VERSION',\s*')([0-9]+\.[0-9]+\.[0-9]+)", plugin_text))
        if version_matches != {PLUGIN_VERSION}:
            findings.append(f"artifacts: plugin version markers are {sorted(version_matches)}, expected {PLUGIN_VERSION}")
    for manifest_path in (ROOT / "update.json", SITE / "update.json"):
        manifest = load_json(manifest_path, str(manifest_path.relative_to(ROOT)), findings)
        if manifest is None:
            continue
        expected_url = f"https://eucomplypro.com/assets/eucomply-{PLUGIN_VERSION}.zip"
        if manifest.get("version") != PLUGIN_VERSION:
            findings.append(f"{manifest_path.relative_to(ROOT)}: expected version {PLUGIN_VERSION}")
        if manifest.get("download_url") != expected_url:
            findings.append(f"{manifest_path.relative_to(ROOT)}: expected download URL {expected_url}")
    plugin_zip = SITE / "assets" / f"eucomply-{PLUGIN_VERSION}.zip"
    if not plugin_zip.exists():
        findings.append(f"artifacts: missing {plugin_zip.relative_to(ROOT)}")
    else:
        try:
            with zipfile.ZipFile(plugin_zip) as archive:
                corrupt = archive.testzip()
                if corrupt is not None:
                    findings.append(f"{plugin_zip.relative_to(ROOT)}: corrupt archive member {corrupt}")
                for name in ("eucomply.php", "readme.txt", "uninstall.php"):
                    expected_path = ROOT / "plugin" / name
                    expected = read_bytes(expected_path, f"artifacts: plugin source {name}", findings)
                    if expected is None:
                        continue
                    try:
                        actual = archive.read(f"eucomply/{name}")
                    except KeyError:
                        findings.append(f"{plugin_zip.relative_to(ROOT)}: missing eucomply/{name}")
                        continue
                    if actual != expected:
                        findings.append(f"{plugin_zip.relative_to(ROOT)}: eucomply/{name} differs from source")
        except (OSError, zipfile.BadZipFile, RuntimeError) as error:
            findings.append(f"{plugin_zip.relative_to(ROOT)}: cannot inspect archive: {error}")
    extension_zip = SITE / "assets/eucomply-extension-1.0.1.zip"
    extension_root = ROOT / "chrome-ext"
    extension_files = {
        path.relative_to(extension_root).as_posix(): path
        for path in extension_root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    } if extension_root.exists() else {}
    if not extension_zip.exists():
        findings.append(f"artifacts: missing {extension_zip.relative_to(ROOT)}")
    else:
        try:
            with zipfile.ZipFile(extension_zip) as archive:
                corrupt = archive.testzip()
                if corrupt is not None:
                    findings.append(f"{extension_zip.relative_to(ROOT)}: corrupt archive member {corrupt}")
                archived_files = {name for name in archive.namelist() if not name.endswith("/")}
                if archived_files != set(extension_files):
                    findings.append(f"{extension_zip.relative_to(ROOT)}: file list differs from chrome-ext source")
                for name, path in extension_files.items():
                    expected = read_bytes(path, f"artifacts: extension source {name}", findings)
                    if expected is None:
                        continue
                    try:
                        actual = archive.read(name)
                    except KeyError:
                        findings.append(f"{extension_zip.relative_to(ROOT)}: missing {name}")
                        continue
                    if actual != expected:
                        findings.append(f"{extension_zip.relative_to(ROOT)}: {name} differs from source")
        except (OSError, zipfile.BadZipFile, RuntimeError) as error:
            findings.append(f"{extension_zip.relative_to(ROOT)}: cannot inspect archive: {error}")
    for archive in (SITE / "assets").glob("eucomply-*.zip"):
        if archive.name not in {plugin_zip.name, extension_zip.name}:
            findings.append(f"artifacts: stale plugin package {archive.name}")
    plugin_page_path = SITE / "plugin/index.html"
    plugin_page = read_text(plugin_page_path, "site/plugin/index.html", findings)
    if plugin_page is not None:
        if f"/assets/eucomply-{PLUGIN_VERSION}.zip" not in plugin_page:
            findings.append("site/plugin/index.html: current plugin download is missing")
        if "eucomply-1.3.0.zip" in plugin_page:
            findings.append("site/plugin/index.html: stale 1.3.0 download remains")
    badge_page = read_text(SITE / "badge/index.html", "site/badge/index.html", findings)
    if badge_page is not None:
        for fragment in ('href="/" target="_blank"', 'src="/images/compliance-badge.svg"', 'src="/assets/eucomply-badge.js"'):
            if fragment in badge_page:
                findings.append(f"site/badge/index.html: embed snippet must not use {fragment}")
    manuscript_path = ROOT / "book/eu-website-compliance-guide-2026.docx"
    manuscript = read_bytes(manuscript_path, "book/eu-website-compliance-guide-2026.docx", findings)
    if manuscript is not None:
        try:
            with zipfile.ZipFile(manuscript_path) as archive:
                document_xml = archive.read("word/document.xml").decode("utf-8")
        except (KeyError, OSError, UnicodeError, zipfile.BadZipFile, RuntimeError) as error:
            findings.append(f"book/eu-website-compliance-guide-2026.docx: cannot read document text: {error}")
        else:
            document_text = html.unescape(re.sub(r"<[^>]+>", " ", document_xml))
            for forbidden in ("Automated daily monitoring", "auditedwp.pages.dev"):
                if forbidden.lower() in document_text.lower():
                    findings.append(f"book/eu-website-compliance-guide-2026.docx: contains stale text {forbidden}")
            findings.extend(text_findings("book/eu-website-compliance-guide-2026.docx", document_text))
    return findings


def structured_data_findings() -> List[str]:
    findings: List[str] = []
    for path in sorted(SITE.rglob("*.html")):
        text = read_text(path, str(path.relative_to(ROOT)), findings)
        if text is None:
            continue
        document = parse_html(text)
        number = 0
        for script in document.scripts:
            if script.script_type.lower() != "application/ld+json":
                continue
            number += 1
            try:
                json.loads(html.unescape(script.content))
            except json.JSONDecodeError as error:
                findings.append(f"{path.relative_to(ROOT)}: invalid JSON-LD block {number}: {error.msg}")
    return findings


def self_test_cases() -> List[Tuple[str, str, str, Optional[str]]]:
    cases: List[Tuple[str, str, str, Optional[str]]] = []
    positives = (
        ("daily EN", "daily monitoring or rescans", "EUComply Pro rescans your website every day."),
        ("daily DA", "daily monitoring or rescans", "Pro scanner dit websted dagligt."),
        ("daily DE", "daily monitoring or rescans", "Pro prüft die Website täglich."),
        ("daily FR", "daily monitoring or rescans", "Pro lance un nouveau scan chaque jour."),
        ("history EN", "30-day Pro history", "EUComply Pro keeps 30-day compliance history."),
        ("history DA", "30-day Pro history", "Pro gemt 30 dages scanningshistorik."),
        ("history DE", "30-day Pro history", "Pro bietet 30 Tage Scan-Verlauf."),
        ("history FR", "30-day Pro history", "Pro propose un historique de 30 jours."),
        ("six-month history", "30-day Pro history", "EUComply Pro keeps a six-month history."),
        ("automatic rechecks", "automatic rechecks", "EUComply Pro provides automatic daily rechecks."),
        ("pass EN", "pass-to-fail alerts", "Get an email when a check changes from passing to failing."),
        ("pass DA", "pass-to-fail alerts", "Få en e-mail, når et tjek går fra bestående til fejlende."),
        ("pass DE", "pass-to-fail alerts", "Eine E-Mail, wenn eine Prüfung von bestanden zu fehlgeschlagen wechselt."),
        ("pass FR", "pass-to-fail alerts", "Recevez un e-mail quand un contrôle passe de réussi à échec."),
        ("pdf EN", "runtime PDF reports", "EUComply Pro lets you download your report as a PDF."),
        ("pdf DA", "runtime PDF reports", "Pro giver dig rapporten som PDF."),
        ("pdf DE", "runtime PDF reports", "Pro erstellt PDF-Berichte zur Laufzeit."),
        ("pdf FR", "runtime PDF reports", "Pro permet de télécharger le rapport au format PDF."),
        ("PDF export", "runtime PDF reports", "EUComply Pro includes PDF exports."),
        ("live EN", "live verification claims", "EUComply Pro provides a real-time verification badge."),
        ("live DA", "live verification claims", "Pro tilbyder et badge med verificerbart live-resultat."),
        ("live DE", "live verification claims", "Pro bietet ein verifizierbares Compliance-Badge."),
        ("live FR", "live verification claims", "Pro propose un badge de conformité vérifiable."),
        ("dashboard EN", "customer dashboard or account", "Log in to your EUComply dashboard."),
        ("dashboard DA", "customer dashboard or account", "Pro indeholder en kundeportal."),
        ("dashboard DE", "customer dashboard or account", "Pro enthält ein Kundendashboard."),
        ("dashboard FR", "customer dashboard or account", "Pro comprend un espace client."),
        ("account area", "customer dashboard or account", "EUComply Pro provides an account area."),
        ("priority support", "priority support", "EUComply Pro includes priority support."),
        ("multi EN", "multi-site or unlimited-domain entitlement", "Your Pro license covers three websites."),
        ("multi DA", "multi-site or unlimited-domain entitlement", "Pro dækker flere domæner."),
        ("multi DE", "multi-site or unlimited-domain entitlement", "Pro deckt mehrere Domains ab."),
        ("multi FR", "multi-site or unlimited-domain entitlement", "Pro couvre plusieurs domaines."),
        ("templates EN", "templates included", "EUComply Pro includes full document templates."),
        ("templates DA", "templates included", "Pro inkluderer færdige dokumentskabeloner."),
        ("templates DE", "templates included", "Pro enthält vollständige Dokumentvorlagen."),
        ("templates FR", "templates included", "Pro inclut des modèles de documents complets."),
        ("proof EN", "unsupported proof or compliance-monitor positioning", "EUComply Pro is auditor-ready."),
        ("proof DA", "unsupported proof or compliance-monitor positioning", "Pro leverer dokumenteret bevis."),
        ("proof DE", "unsupported proof or compliance-monitor positioning", "Pro liefert dokumentierten Nachweis."),
        ("proof FR", "unsupported proof or compliance-monitor positioning", "Pro fournit une preuve documentée."),
        ("PayPal promise", "PayPal checkout promise", "EUComply Pro will support PayPal checkout as a planned payment option."),
        ("Merchant of Record", "Merchant of Record claim", "EUComply Pro purchases are handled as Merchant of Record."),
        ("Pro refund", "Pro refund promise", "EUComply Pro includes a 14-day money-back guarantee."),
        ("grammar", "broken Pro grammar", "EUComply Pro get editable tools."),
        ("mixed clause", "customer dashboard or account", "Planned monitoring is not included today, but your customer dashboard is available in Pro."),
        ("roadmap aside", "customer dashboard or account", "Planned features aside, EUComply Pro includes a customer dashboard today."),
        ("roadmap then claim", "customer dashboard or account", "A customer dashboard is planned. EUComply Pro includes a customer dashboard today."),
        ("future lead-in", "runtime PDF reports", "PDF reports are planned. EUComply Pro includes PDF reports today."),
        ("future German", "runtime PDF reports", "Zukünftig sind PDF-Berichte geplant. Pro bietet PDF-Berichte heute an."),
    )
    for name, label, text in positives:
        cases.append((name, "site/pro/index.html", text, label))
    negatives = (
        ("negative roadmap EN", "Planned features, not included today: daily monitoring and a customer dashboard."),
        ("negative roadmap DA", "Planlagte funktioner, ikke inkluderet i dag: daglig overvågning og et kundedashboard."),
        ("negative roadmap DE", "Geplante Funktionen, nicht enthalten: tägliche Überwachung und ein Kundendashboard."),
        ("negative roadmap FR", "Fonctionnalités prévues, non incluses : surveillance quotidienne et tableau de bord client."),
        ("negative PDF", "EUComply Pro has no runtime PDF report."),
        ("negative dashboard", "EUComply Pro isn't a customer dashboard."),
        ("negative multi", "EUComply Pro offers no multiple sites."),
        ("negative live", "The live verification badge does not show a current score."),
        ("negative no PDF", "No PDF reports are available in Pro."),
        ("negative contains no PDF", "Pro contains no PDF reports."),
        ("negative future dashboard", "Future: a customer dashboard."),
        ("negative coming later", "Coming later: daily monitoring."),
        ("negative PayPal", "PayPal is not a planned checkout option for Pro."),
        ("negative Merchant of Record", "Stripe is the payment processor; EUComply is not a Merchant of Record."),
    )
    for name, text in negatives:
        cases.append((name, "site/pro/index.html", text, None))
    cases.append(("generic qualifier is not a marker", "site/pro/index.html", "EUComply Pro supports multiple sites without a subscription fee.", "multi-site or unlimited-domain entitlement"))
    cases.extend(
        (
            ("attribute", "site/pro/index.html", '<meta name="description" content="EUComply Pro provides a real-time verification badge">', "live verification claims"),
            ("multiline", "site/pro/index.html", "<p>EUComply Pro provides a <strong>real-time verification badge</strong></p>", "live verification claims"),
            ("json", "site/pro/index.html", '<script type="application/ld+json">{"description":"EUComply Pro provides a 30-day compliance history"}</script>', "30-day Pro history"),
            ("javascript", "site/pro/index.html", "<script>const claim = `EUComply Pro supports multiple sites`;</script>", "multi-site or unlimited-domain entitlement"),
            ("sample marker", "site/pro/sample-report/index.html", '<body data-product-state="sample"><p>EUComply Pro includes a customer dashboard.</p></body>', "customer dashboard or account"),
            ("nested concept marker", "site/pro/index.html", '<div data-product-state="concept-demo"><p>EUComply Pro includes daily monitoring.</p></div>', "daily monitoring or rescans"),
            ("sample word is not marker", "site/pro/index.html", "<p>EUComply Pro includes a sample report and a customer dashboard.</p>", "customer dashboard or account"),
            ("table target cell", "site/compare/index.html", "<table><tr><th>Feature</th><th>Cookiebot</th><th>EUComply Pro</th></tr><tr><td>Pass-to-fail email alerts</td><td>Manual</td><td>Yes</td></tr></table>", "pass-to-fail alerts"),
            ("table competitor ignored", "site/compare/index.html", "<table><tr><th>Feature</th><th>Cookiebot</th><th>EUComply Pro</th></tr><tr><td>Customer dashboard</td><td>Yes</td><td>No</td></tr></table>", None),
            ("monitoring pass-to-fail", "site/scan/index.html", "<p>You receive an email when a check changes from pass to fail.</p>", "pass-to-fail alerts"),
            ("monitoring score drop", "site/scan/index.html", "<p>You receive an email when the overall score drops.</p>", None),
        )
    )
    return cases


def run_self_tests() -> Tuple[int, List[str]]:
    failures: List[str] = []
    checks = 0
    cases = self_test_cases()
    checks += len(cases)
    for name, relative, text, expected in cases:
        findings = text_findings(relative, text)
        if expected is None:
            if findings:
                failures.append(f"self-test {name}: unexpected findings: {findings}")
        elif not any(expected in finding for finding in findings):
            failures.append(f"self-test {name}: expected {expected}, got {findings}")
    price_cases = (
        ("price EN", "en", "Pro costs 79 USD per website per year."),
        ("price DA", "da", "Pro koster 79 USD pr. websted pr. år."),
        ("price DA website", "da", "Pro koster 79 USD pr. website pr. år."),
        ("price DE", "de", "Pro kostet 79 USD pro Website pro Jahr."),
        ("price DE je", "de", "Pro kostet 79 USD je Website und pro Jahr."),
        ("price FR", "fr", "Pro coûte 79 USD par site web et par an."),
        ("price FR comma", "fr", "Pro coûte 79 USD par site, et par an."),
    )
    checks += len(price_cases)
    for name, language, text in price_cases:
        if price_findings(language, text):
            failures.append(f"self-test {name}: valid localized price rejected")
    for language, text in (
        ("en", "Pro costs $79 per month."),
        ("da", "Pro koster 79 USD pr. måned."),
        ("de", "Pro kostet 79 USD pro Monat."),
        ("fr", "Pro coûte 79 USD par mois."),
    ):
        checks += 1
        if not price_findings(language, text):
            failures.append(f"self-test price {language}: invalid price accepted")
    for language, text in (
        ("en", "EUComply Pro keeps its history for 30 days."),
        ("da", "Pro gemmer historik for 30 dage."),
        ("de", "Pro ist für 3 Märkte gedacht."),
    ):
        checks += 1
        if CONTRADICTORY_PRICE.search(text):
            failures.append(f"self-test price false positive {language}: {CONTRADICTORY_PRICE.search(text).group(0)}")
    checks += 1
    if not price_findings("en", "Pro costs $79 per website per month."):
        failures.append("self-test contradictory Pro price accepted")
    png = minimal_test_png({})
    checks += 1
    metadata, width, height = png_text_metadata(png)
    if metadata or (width, height) != (1, 1):
        failures.append("self-test png metadata: minimal PNG parse failed")
    metadata, width, height = png_text_metadata(minimal_test_png({"Title": "Pro", "Description": "Current"}))
    checks += 1
    if metadata != {"Title": "Pro", "Description": "Current"} or (width, height) != (1, 1):
        failures.append("self-test png metadata: textual metadata parse failed")
    missing_findings: List[str] = []
    checks += 1
    if read_bytes(ROOT / "__missing_required_artifact__", "missing artifact", missing_findings) is not None or not missing_findings:
        failures.append("self-test missing artifact: clean failure not reported")
    malformed_findings: List[str] = []
    checks += 1
    with mock.patch.object(Path, "read_bytes", return_value=b"{"):
        malformed = load_json(Path("malformed.json"), "malformed artifact", malformed_findings)
    if malformed is not None or not any("invalid JSON" in finding for finding in malformed_findings):
        failures.append("self-test malformed artifact: clean failure not reported")
    checks += 1
    try:
        png_text_metadata(b"not a png")
    except ValueError:
        pass
    else:
        failures.append("self-test malformed PNG: clean failure not reported")
    stripe_cases = (
        ("single Stripe CTA", f'<a href="{PRO_LINK}">Buy</a>', False),
        ("duplicate Stripe CTA", f'<a href="{PRO_LINK}">Buy</a><a href="{PRO_LINK}">Buy again</a>', True),
        ("legacy Lemon CTA", f'<a href="https://example.lemonsqueezy.com/checkout">Buy</a>', True),
        ("JavaScript Stripe CTA", f'<button onclick="location.href=\'{PRO_LINK}\'">Buy</button>', True),
    )
    for name, text, should_fail in stripe_cases:
        checks += 1
        findings = stripe_cta_findings("site/pro/index.html", text)
        if should_fail != bool(findings):
            failures.append(f"self-test {name}: unexpected stripe findings {findings}")
    truth_cases = (
        ("no-storage guard", "site/index.html", "No account, nothing stored.", "overbroad no-storage claim"),
        ("free limit guard", "site/pricing/index.html", "Free — unlimited scans.", "unlimited free-scan claim"),
        ("plugin parity guard", "site/plugin/index.html", "The same checks plus WordPress-specific ones.", "plugin parity claim"),
        ("script blocking guard", "plugin/readme.txt", "GDPR-compliant script blocking?", "unsupported script-blocking verification"),
        ("comparison capability guard", "site/compare/index.html", "Free, shareable PNG scorecard.", "unsupported PDF scorecard"),
        ("legacy monitoring link guard", "worker-watch/index.js", "View history: https://auditedwp.pages.dev/pro/", "legacy Pro link in monitoring mail"),
        ("stale ebook price guard", "site/blog/index.html", "Get the ebook — $14.99", "stale paid ebook CTA"),
        ("result-link guard", "site/pricing/index.html", "Shareable result link", "persisted-result overclaim"),
        ("template-table guard", "site/pricing/index.html", "Guide and checklists</td><td>Yes</td><td>No</td><td>Yes</td>", "free guide marked as paid template"),
        ("static-scan guard", "site/cookie-banner-check/index.html", "Pre-consent tracking", "runtime tracking overclaim"),
        ("DORA DNS guard", "site/compare/index.html", "Email authentication, failover and incident-response signals", "unsupported DNS/email-authentication check"),
        ("sample compliance guard", "site/pro/sample-report/index.html", "Compliant with European Accessibility Act requirements", "unsupported compliance determination"),
    )
    for name, relative, text, expected in truth_cases:
        checks += 1
        findings = product_truth_findings(relative, text)
        if not any(expected in finding for finding in findings):
            failures.append(f"self-test {name}: expected {expected}, got {findings}")
    return checks, failures


def minimal_test_png(metadata: Dict[str, str]) -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    data = b"\x89PNG\r\n\x1a\n"
    data += chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    for key, value in metadata.items():
        data += chunk(b"iTXt", key.encode("latin-1") + b"\x00\x00\x00\x00\x00" + value.encode("utf-8"))
    data += chunk(b"IEND", b"")
    return data


def claim_paths() -> Set[Path]:
    paths = set(SITE.rglob("*.html"))
    paths.update(SITE.glob("llms*.txt"))
    paths.update((SITE / "assets").glob("*.js"))
    paths.update({SITE / "search-index.json", SITE / "images/compliance-badge.svg"})
    paths.update(ROOT / relative for relative in PRODUCT_FILES)
    return paths


def main() -> int:
    findings: List[str] = []
    buying_pages_checked: Set[str] = set()
    self_test_count, self_test_failures = run_self_tests()
    findings.extend(self_test_failures)
    for path in sorted(claim_paths()):
        relative = path.relative_to(ROOT).as_posix()
        if not path.exists():
            findings.append(f"claims: missing required file {relative}")
            continue
        text = read_text(path, f"claims: {relative}", findings)
        if text is None:
            continue
        findings.extend(product_truth_findings(relative, text))
        if relative.startswith("site/") and context_relative(relative) in BUYING_PAGES:
            buying_pages_checked.add(context_relative(relative))
            findings.extend(buying_page_findings(context_relative(relative), text))
        has_checkout = any(host in text.lower() for host in ("buy.stripe.com", "lemonsqueezy.com", "gumroad.com"))
        has_pro_scope = is_pro_page(relative) or bool(re.search(r"\bEUComply\s+Pro\b", text, re.I))
        if path.suffix.lower() in {".html", ".htm"} and has_checkout and has_pro_scope:
            findings.extend(stripe_cta_findings(relative, text))
        if path.suffix.lower() in {".html", ".htm", ".svg"}:
            findings.extend(text_findings(relative, text))
        else:
            findings.extend(raw_claim_findings(relative, text))
    expected_buying_pages = set(BUYING_PAGES)
    if buying_pages_checked != expected_buying_pages:
        missing = sorted(expected_buying_pages - buying_pages_checked)
        findings.append(f"buying-page gate skipped: {missing}")
    findings.extend(artifact_findings())
    findings.extend(structured_data_findings())
    findings.extend(og_image_findings())
    findings = list(dict.fromkeys(findings))
    if findings:
        for finding in findings:
            print(f"ERROR {finding}")
        print(f"\n{len(findings)} Pro product-truth findings")
        return 1
    print(f"{self_test_count} self-tests passed")
    print("0 unexpected EUComply Pro claims")
    return 0


if __name__ == "__main__":
    sys.exit(main())
