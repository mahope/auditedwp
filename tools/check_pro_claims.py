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
from typing import Callable, Dict, Iterable, List, Optional, Pattern, Sequence, Set, Tuple
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
ORIGIN = "https://eucomplypro.com"
PRO_LINK = "https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03"
PLUGIN_VERSION = "1.3.18"
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
    "scripts/build_sample_report.py",
    "shared/sample-report.json",
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
# The files that ship the plugin itself. A daily cadence may be described in
# them, because the plugin is the thing that runs it — but only when the code
# really schedules one, and only when the sentence says where it runs. A
# hosted monitor claim is a different product and stays red everywhere.
PLUGIN_LOCAL_FILES = set(PLUGIN_TRUTH_PAGES)
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
# Where a cadence runs. "Every day" is a local fact only when the sentence says
# the checks happen on the customer's own installation; a hosted monitor never
# can, which is exactly the difference the daily-rescan grab cannot see on its
# own. WP-Cron counts, because it is definitionally local.
LOCAL_CADENCE_SCOPE = re.compile(
    r"\b(?:on|in|inside|within|at)\s+(?:your|the|this|each|its)\s+(?:own\s+)?(?:"
    r"site|website|web\s?site|server|wordpress|install(?:ation)?|host|instance|machine|box)\b|"
    r"\b(?:locally|on\s+your\s+own\s+wordpress(?:\s+install(?:ation)?)?|in\s+your\s+own\s+wordpress|"
    r"inside\s+your\s+own\s+wordpress|from\s+your\s+own\s+server)\b|"
    r"\bwp-?cron\b|"
    # "i din egen WordPress" and "in Ihrer eigenen Installation" are what the DA
    # and DE pages write; without these two branches a daily cadence in Danish
    # or German was an over-claim the gate could not see, which is the same
    # missing-word failure the name vocabularies above kept making.
    r"\bi\s+din\s+egen\w*\b|\bin\s+(?:Ihrer|ihrer|der)\s+eigenen?\b|"
    r"\bpå\s+(?:din|den\s+ne|deres|eget?)\b|\bvor\s+ort\b|\blokal\w*|\bvindues\w*\b|"
    r"\blocalement\b|\bsur\s+(?:votre|le\s+site|ce\s+site|votre\s+site)\b|\bdans\s+(?:votre\s+)?wordpress\b",
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
    # "Extension Pro", "Pro-Plugin", "Pro plugin": a translated header can lead
    # with the product name. The French one did not match, so the whole French
    # comparison column had never been read by a table claim -- neither by the
    # over-claim rules nor by the new under-claim one.
    if buying and re.search(r"(?:^|\s)pro$", text):
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


def php_method_body(text: str, name: str) -> str:
    """The body of a PHP method, brace-matched, or '' when there is no such method."""
    start = re.search(r"function\s+" + re.escape(name) + r"\s*\(", text)
    if not start:
        return ""
    depth = 0
    opened = False
    for index in range(start.start(), len(text)):
        char = text[index]
        if char == "{":
            depth += 1
            opened = True
        elif char == "}":
            depth -= 1
            if opened and depth == 0:
                return text[start.start():index + 1]
    return ""


def plugin_schedules_daily_scan(text: Optional[str] = None) -> bool:
    """Does the plugin put a daily interval on its own scan event?

    This is what lets the plugin describe a local daily cadence: the words are
    allowed because the code does it. So the answer is read from the code, by a
    trace and not by a search for the word — the interval handed to
    wp_schedule_event is followed back to the method that produced it, and only
    a 'daily' coming out of that method counts. Drop the daily interval in a
    later release and every sentence that leaned on this becomes a red claim
    again, which is the point: the hole is the size of the feature.

    $text lets the selftest hand in a plugin it broke on purpose, the same way
    redirect_findings() takes a _redirects.
    """
    if text is None:
        text = read_text(ROOT / "plugin/eucomply.php", "claims: plugin PHP", [])
        if text is None:
            return False
    call = re.search(r"wp_schedule_event\(\s*[^,]+,\s*\$(\w+)\s*,\s*EUCOMPLY_SCAN_EVENT", text, re.S)
    if not call:
        return False
    assigned = re.search(r"\$" + call.group(1) + r"\s*=\s*\$this->(\w+)\s*\(", text)
    if not assigned:
        return False
    return "'daily'" in php_method_body(text, assigned.group(1))


# A local cadence is a statement about one thing, so the statement has to be
# readable as one. Without this the hole would cover a whole update.json
# changelog, where the marker and the claim can sit in different releases — which
# is how this exact check was caught red on a file nobody had looked at.
LOCAL_CADENCE_MAX_CHARS = 400


def local_cadence_claim(relative: str, segment: str, text: Optional[str] = None) -> bool:
    """A daily cadence the site's own WordPress runs, in a file that schedules it.

    Two ways in, and the second one is new. A page *about* the plugin is allowed
    the sentence. A sales page has to earn it: the cadence is a plugin feature, so
    the sentence itself has to say where it runs ("in your own WordPress"). The
    old rule allowed neither on /pro/ and /pricing/, which is why the pricing
    table could tell a buyer that Pro scans on the same weekly schedule as the
    free plugin -- the one comparison on the site where the Pro column was
    identical to the Free column, and nobody read it as a bug because the rule
    that would have flagged it was a page list.
    """
    scoped = relative in PLUGIN_LOCAL_FILES or bool(LOCAL_CADENCE_SCOPE.search(segment))
    return (
        scoped
        and len(segment) <= LOCAL_CADENCE_MAX_CHARS
        and bool(LOCAL_CADENCE_SCOPE.search(segment))
        and plugin_schedules_daily_scan(text)
    )


# ---------------------------------------------------------------------------
# Denied features: the direction nobody watches.
#
# Every other rule in this file fires when a page says a feature IS there. This
# one fires when a page says a feature the plugin already ships is NOT there.
#
# That direction is silent when it is wrong. An over-claim trips this gate, gets
# fixed before merge and costs a diff. An under-claim trips nothing: the page
# stays published, the gate stays green, and the feature nobody buys stays
# unsold, for as long as the copy is wrong. It happened here for real —
# site/plugin/index.html told buyers that "scan history" was not part of Pro, on
# the one page selling exactly the Pro licence that unlocks it, for as long as
# the history shipped (1.3.4) without anybody re-reading that sentence.
#
# So the feature list is not a copy of the marketing. Every entry carries the
# predicate that proves the feature is still in the code, and a page may only
# deny a feature the code still backs. Drop the feature from a later release and
# the sentence denying it becomes true again — the hole is the size of the
# feature, in both directions.
# ---------------------------------------------------------------------------


def _plugin_text(text: Optional[str] = None) -> Optional[str]:
    if text is not None:
        return text
    return read_text(ROOT / "plugin/eucomply.php", "claims: plugin PHP", [])


PHP_COMMENT = re.compile(r"/\*.*?\*/|//[^\n]*|#[^\n]*", re.S)


def strip_php_comments(text: str) -> str:
    """Drop comments, so a `phpcs:ignore` note cannot stand in for the code.

    Found by mutation: the first version of plugin_ships_history() looked for
    "build_history_section()" inside build_report(), and the call sits on a line
    whose trailing phpcs:ignore comment names the same method. Deleting the real
    call left the comment, the string was still there, and the predicate still
    said the history was rendered. A gate that a comment can satisfy is not a
    gate, and this is the third time in this file's history that a text match was
    quietly reading a comment instead of the code.
    """
    return PHP_COMMENT.sub(" ", text)


def plugin_ships_history(text: Optional[str] = None) -> bool:
    """Does the plugin keep a scan history, and can only a Pro key see it?

    Traced, not searched: the history has to be written, actually rendered into
    the report, and reachable only through a document that both entry points hand
    out behind an is_pro() gate. A history that were written but never rendered,
    or rendered on a page anyone could open, is not a Pro feature to advertise.

    The export half tests for `! $pro` and not for `$pro`, because the parameter
    is named $pro in the signature: the name is there whether or not the guard is
    (also found by mutation).
    """
    source = _plugin_text(text)
    if source is None:
        return False
    if "update_option( 'eucomply_scan_history'" not in php_method_body(source, "record_history"):
        return False
    if "build_history_section()" not in strip_php_comments(php_method_body(source, "build_report")):
        return False
    # Every caller of report_document() is a Pro decision: the client link only
    # exists because create_client_link() refuses without a licence, and the
    # wp-admin export refuses unless the caller passed a true verdict.
    if "is_pro()" not in php_method_body(source, "create_client_link"):
        return False
    export = php_method_body(source, "report_export_response")
    return "! $pro" in export and "report_document()" in export


def plugin_ships_client_link(text: Optional[str] = None) -> bool:
    """A read-only report link a bureau can send its client."""
    source = _plugin_text(text)
    if source is None:
        return False
    create = php_method_body(source, "create_client_link")
    return "is_pro()" in create and "random_bytes" in create and "eucomply_client_link" in create


def plugin_ships_report_file(text: Optional[str] = None) -> bool:
    """The report as a file you can attach, not only a page you can link."""
    source = _plugin_text(text)
    if source is None:
        return False
    response = php_method_body(source, "client_report_response")
    return "eucomply_report_file" in source and "client_report_filename()" in response


# A denial is allowed to be about the *hosted* version of a feature, and it has
# to be: the history ships in the customer's own WordPress, so "hosted scan
# history is not included" is required honesty, not an under-claim.
#
# The qualifier has to govern the *same list item* as the name it qualifies. A
# coordinated list carries one modifier per item, so in "Hosted re-scans, scan
# history, PDF reports and a live badge are not part of it" the word "Hosted"
# belongs to "re-scans" and says nothing about the history — and reading it as
# if it did is exactly how the real under-claim on site/plugin/index.html stayed
# green. So the search starts after the last separator before the name, and runs
# to the end of the clause: a qualifier placed earlier in the same list is a
# different item's, and a qualifier placed in the previous sentence qualifies
# nothing at all.
LIST_SEPARATOR = re.compile(
    r"[,;:]|\b(?:and|or|und|oder|sowie|et|ou|og)\b|[.!?]|\n",
    re.I,
)
# "hostet" is the Danish indefinite and does not start "hostede", which is the
# definite form the Danish pages actually use ("den hostede tjeneste"). The old
# branch matched this file's selftest wording and not the site's, so the one real
# Danish sentence was the one the qualifier could not see.
HOSTED_QUALIFIER = re.compile(
    r"\b(?:hosted|hoste\w*|cloud|cloud-hosted|cloudbaseret\w*|remote|remotely|fjernt\w*|"
    r"our servers?|from our servers?|external|third-party|"
    r"gehostet\w*|extern\w*|ferngesteuert\w*|"
    r"h[ée]berg[ée]\w*|distants?|notre\w*\s+serveurs?)\b",
    re.I,
)

# The denial verbs, in the four languages the Pro pages ship in. "does not
# include" and "are not part of it" are the same promise in different words, and
# a page can deny a feature in any of them.
DENIAL = (
    r"(?:not\s+(?:part|include|included|available|offered|covered|shipped|provided)|"
    r"isn'?t|is\s+not|are\s+not|aren'?t|does\s+not|do\s+not|don'?t|"
    r"no\s+such|lacks?|without|excluded)"
    r"|(?:ikke\s+(?:en\s+del|del|inkluderet\w*|tilg[æa]ngelig\w*|medtaget\w*|dekket\w*)|"
    r"er\s+ikke|er\s+ikke\s+med)"
    r"|(?:nicht\s+(?:enthalten|inkludiert|dabei|Teil\s+von\s+Pro)|"
    r"ist\s+nicht|sind\s+nicht|kein\w*)"
    # "ne sont pas incluses" is the plural French denial; the branch below only
    # had the verb+pas forms, so a French page could deny a shipped feature in
    # the one wording the check could not read.
    r"|(?:n['']?(?:en)?\s+(?:contient|contiennent|font|comprend|fait|couvre|inclut|g\xe8re)\w*\s+pas|"
    r"ne\s+(?:sont|est)\s+pas|aucun\w*|hors\s+de)"
)

# One compiled copy, so the two directions of the truth gate cannot disagree
# about what a denial is.
DENIED_VERB = re.compile(DENIAL, re.I)

# PRO_CONTEXT is English-shaped, and that is deliberate: it guards the
# over-claim direction, where being conservative means missing a claim rather
# than inventing one. The denial direction has the opposite risk — reading no
# page at all — and a page only has to be one where a Pro licence is on the
# table. Saying that takes four languages: "Pro license" (EN), "Pro-licens"
# (DA), "Pro-Lizenz" (DE) and "licence Pro" (FR).
#
# The English pattern alone matched EN and DA and silently skipped DE and FR,
# which is the third time this file has been caught green on a check that never
# looked. So the denial gate gets its own page test, and there is a selftest
# case per language that fails if the pattern stops matching it.
PRO_PAGE_CONTEXT = re.compile(
    r"\bEUComply\s+Pro\b"
    r"|\bPro\b[^\n.!?;]{0,24}\b(?:licen[cs]e|licen[sz]s?|lizenz\w*|licen[cs]ei\w*)\b"
    r"|\b(?:licen[cs]e|licen[sz]s?)\s+Pro\b"
    r"|\bPro\s*(?:kaufen|acheter|k\xf6pa|abonn\w*|tar\w*)\b"
    r"|\b(?:kaufen|acheter|k\xf6pa|buy)\b[^\n.!?;]{0,40}\bPro\b",
    re.I,
)


@dataclass(frozen=True)
class ShippedFeature:
    """A Pro feature the code still ships, and the words that deny it."""

    key: str
    label: str
    shipped: Callable[[], bool]
    name: Pattern[str]
    denial: Pattern[str]

    @property
    def window(self) -> int:
        """How far apart the name and the denial may sit and still be one claim."""
        return DENIAL_WINDOW


# A name and a denial in the same sentence, or in the same clause either side of
# it. Long enough for "scan history and PDF reports are not part of it", short
# enough that two unrelated sentences about two products do not merge into one
# invented claim.
DENIAL_WINDOW = 80


def plugin_ships_alert(text: Optional[str] = None) -> bool:
    """Does the plugin mail the owner when a check changes, and only for Pro?

    Traced, the same three legs every other predicate here uses, because a
    feature that exists but is unreachable is not something a page may deny in
    one direction and promise in the other: the mail has to be sent
    (`wp_mail(`), it has to be a Pro decision (`is_pro()`), and it has to be
    wired into the scan that runs on its own — `maybe_send_alert(` called from
    `run_checks()`, not merely defined. 1.3.10 shipped the alerts; without this
    predicate a sales page could have kept listing them as planned, which is
    exactly what all four /pro/ pages did on the day it shipped.
    """
    source = _plugin_text(text)
    if source is None:
        return False
    alert = php_method_body(source, "maybe_send_alert")
    if "wp_mail(" not in alert or "is_pro()" not in alert:
        return False
    return "maybe_send_alert(" in strip_php_comments(php_method_body(source, "run_checks"))


def _shipped_pro_features() -> Tuple[ShippedFeature, ...]:
    """The features a page may not deny, each with its own code predicate.

    Built per call rather than at import time so the selftest can hand in a
    plugin it broke on purpose, exactly the way plugin_schedules_daily_scan()
    takes $text. The predicates read plugin/eucomply.php, never a cached answer.
    """
    return (
        ShippedFeature(
            label="shipped Pro feature denied on a sales page",
            key="history",
            shipped=plugin_ships_history,
            # Every name the four locales actually use. "Historie" was missing on
            # the first run and the German pages went unread for the same reason
            # the French ones did — one word of vocabulary, one silent language.
            name=re.compile(
                r"\b(?:scan\s+history|scanning\s+history|scanhistorik|scanningshistorik|"
                r"scan-verlauf|scanverlauf|verlauf|historie|scangeschichte|"
                r"historik|history|historique)\b",
                re.I,
            ),
            denial=re.compile(DENIAL, re.I),
        ),
        ShippedFeature(
            label="shipped Pro feature denied on a sales page",
            key="client link",
            shipped=plugin_ships_client_link,
            # "rapportlink", "Berichtslink" and "lien de rapport" are what the
            # DA/DE/FR pages write; before they were here the check read EN and
            # DA only, which is the same missing-word failure as above.
            name=re.compile(
                r"\b(?:client\s+(?:report\s+)?link|report\s+link|clientlink|"
                r"kundenlink|kundelink|klientlink|rapportlink|berichtslink|"
                r"read-?only\s+report\s+link|skrivebeskyttet\s+\w*link|"
                r"client-lien|lien\s+(?:de\s+)?(?:client|rapport))\b",
                re.I,
            ),
            denial=re.compile(DENIAL, re.I),
        ),
        ShippedFeature(
            label="shipped Pro feature denied on a sales page",
            key="report file",
            shipped=plugin_ships_report_file,
            name=re.compile(
                r"\b(?:download\w*\s+(?:the\s+|your\s+)?report|report\s+file|"
                r"bericht\s+herunterladen\w*|rapport\s+t[ée]l[ée]charg\w*)\b",
                re.I,
            ),
            denial=re.compile(DENIAL, re.I),
        ),
        ShippedFeature(
            label="shipped Pro feature denied on a sales page",
            key="alert",
            shipped=plugin_ships_alert,
            # Not a bare "e-mail": the site sends ordinary mail about plenty of
            # things. Each name is a change-notification in the language the
            # page actually writes it in, because a word of missing vocabulary is
            # how the German and French pages went unread in the first place.
            name=re.compile(
                r"\b(?:e-?mail\s+alerts?|alerts?\s+by\s+e-?mail|regression\s+alerts?|"
                r"e-?mail-alarmer?\b|e-?mail\s+ved\s+overgang|mail-?alarm\w*\b|"
                r"E-Mail-Meldung\w*|E-Mail-Benachrichtigung\w*|E-Mail\s+bei\s+Wechsel|"
                r"alertes?\s+(?:par\s+)?e-?mail|e-?mail\s+lors\s+du\s+passage)\b",
                re.I,
            ),
            denial=re.compile(DENIAL, re.I),
        ),
    )


# The eight pages that decide what a buyer believes Pro is. Not every page that
# mentions Pro, and not the vendor comparisons: this is the canonical truth
# surface, in the four languages, and a feature the code ships has to be sold
# somewhere a buyer actually compares plans.
PRO_TRUTH_SURFACES = {
    "site/pro/index.html",
    "site/da/pro/index.html",
    "site/de/pro/index.html",
    "site/fr/pro/index.html",
    "site/pricing/index.html",
    "site/da/pricing/index.html",
    "site/de/pricing/index.html",
    "site/fr/pricing/index.html",
}

# A cadence is not a noun, so it gets its own names. Each language writes its
# own adverb, and the roadmap line on every /pro/ page contains the same word in
# a sentence that is about the hosted service -- which is exactly the collision
# the check has to survive, so the pattern is deliberately the bare adverb.
DAILY_CADENCE_NAME = re.compile(
    r"\b(?:daily|once\s+a\s+day|every\s+day|"
    r"daglig\w*|t\xe4glich\w*|t\xe4gliche\w*|quotidien\w*|chaque\s+jour)\b",
    re.I,
)


def _under_claim_features() -> Tuple[Tuple[str, Callable[[], bool], Pattern[str]], ...]:
    """The shipped Pro features a canonical sales page has to name.

    The name patterns are the *same objects* the denial direction uses, so the
    two directions cannot drift apart into two vocabularies -- the failure mode
    of every hand-kept list in this file so far.
    """
    by_key = {feature.key: feature for feature in _shipped_pro_features()}
    return (
        ("a scan history", plugin_ships_history, by_key["history"].name),
        ("a client report link", plugin_ships_client_link, by_key["client link"].name),
        ("an e-mail alert", plugin_ships_alert, by_key["alert"].name),
        ("daily re-scans", plugin_schedules_daily_scan, DAILY_CADENCE_NAME),
    )


def under_claim_findings(relative: str, blocks: Sequence[TextBlock], text: Optional[str] = None) -> List[str]:
    """Pages that sell Pro while sitting on a Pro feature the plugin ships.

    The denial check above is the mirror image of this one, and neither is
    optional. A page that denies history is a promise the product breaks; a page
    that never mentions it is money left on the table, and it is how all eight
    truth pages read on 26/9: 1.3.4 through 1.3.10 shipped history, a client
    link, a report file, a daily cadence and pass-to-fail alerts, and /pro/ still
    listed three features and put the rest under "planned".

    A name only counts as *sold* when it is not scoped to the future or to the
    hosted service. The product requires both of those denials, so a check that
    could not tell them apart would push the site into over-claiming -- the same
    trade the denial check makes in the other direction.
    """
    findings: List[str] = []
    for label, shipped, name in _under_claim_features():
        if not shipped():
            continue
        if any(
            name.search(block.text)
            and not ROADMAP.search(block.text)
            and not ROADMAP_DISCLAIMER.search(block.text)
            and not DENIED_VERB.search(block.text)
            for block in blocks
        ):
            continue
        findings.append(
            f"{relative}: the plugin ships {label} behind the Pro licence, "
            "but no line on this page sells it"
        )
    return findings


# ---------------------------------------------------------------------------
# How many checks a Pro scan records: a number read from the code, not typed in.
#
# The Pro scan IS the plugin's run_checks(), and that method writes six checks:
# ssl, cookies, forms, backups, plugins and legal. Two of those six exist in no
# other product we ship -- "backups" and "plugins" are WordPress facts -- and
# five of the universal scanner's nine (consent_mode_v2, tcf, trackers, headers,
# dora) are not in it at all. So the two products genuinely disagree about what
# a check is, and site/plugin/index.html says so honestly.
#
# All four /pro/ pages did not. The scan-history ledger row described the paid
# history as recording "the state of each of the nine checks", which is the
# universal scanner's number, in the one sentence that describes what a paying
# customer gets in wp-admin. They get six. Nothing in the repo compared the two,
# because every other count in this file is a *name* pattern read off the plugin
# source: a number has no name to match, so it had no gate at all.
#
# The number is therefore parsed out of run_checks() here, and a sentence that
# counts checks has to agree with it. Both directions are the same comparison --
# a page cannot be wrong about a number by being too small either.
# ---------------------------------------------------------------------------

RESULT_ASSIGNMENT = re.compile(r"\$results\[\s*'([a-z0-9_]+)'\s*\]\s*=")


def plugin_check_keys(text: Optional[str] = None) -> List[str]:
    """The check keys run_checks() writes, in source order, duplicates dropped.

    Read from the assignments rather than from the report template, so a check
    that is computed but never reported does not count and a report row without
    a check behind it cannot. An empty list means the method could not be read
    at all, and every caller treats that as a finding rather than as "no claim
    to check" -- a count gate that measures nothing must not be green.
    """
    source = _plugin_text(text)
    if source is None:
        return []
    body = strip_php_comments(php_method_body(source, "run_checks"))
    if not body:
        return []
    keys: List[str] = []
    for key in RESULT_ASSIGNMENT.findall(body):
        if key not in keys:
            keys.append(key)
    return keys


# The numbers four locales actually write. A word outside this table is not
# guessed at: an unreadable numeral leaves the sentence alone and the check says
# so in its report, because a gate that invents a count invents a finding too.
NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "en": 1, "to": 2, "tre": 3, "fire": 4, "fem": 5, "seks": 6, "syv": 7,
    "otte": 8, "ni": 9, "ti": 10, "elleve": 11, "tolv": 12,
    "eins": 1, "zwei": 2, "drei": 3, "vier": 4, "fünf": 5, "sechs": 6,
    "sieben": 7, "acht": 8, "neun": 9, "zehn": 10, "elf": 11, "zwölf": 12,
    "un": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6,
    "sept": 7, "huit": 8, "neuf": 9, "dix": 10, "onze": 11, "douze": 12,
}

# A number that is immediately followed by the word for a check. That adjacency
# is the whole reason this can read a page: "the most recent 12" and "52 weeks
# of history" are numbers too, and neither says anything about how many checks
# exist.
COUNTED_CHECKS = re.compile(
    r"\b(\d{1,2}|" + "|".join(sorted(NUMBER_WORDS, key=len, reverse=True)) + r")[\s\-‐-―]+"
    r"([Ww]ord[Pp]ress[\s\-]?)?(checks?|tjek|prüfungen|contrôles?|kontroller|kontrollen)\b",
    re.I,
)

# A sentence counts the *plugin's* checks when it is about the plugin's own scan.
# Two bindings, because either alone is too wide or too narrow: a history row
# that says "nine checks" is the real defect, and a Pro row that says the plugin
# runs nine checks is the same defect wearing different words. A sentence about
# the universal scanner's nine checks carries neither, so /scan/ and /index/ stay
# green -- they are describing a different product and they are right to.
PLUGIN_SCAN_SUBJECT = re.compile(
    r"\b(?:plugin|WordPress|wp-admin)\b", re.I,
)

# The unit this gate reads is a ledger row, not a text block. The Pro pages write
# a row as <li><b>title</b><p>sentence</p></li>, and the parser splits that into
# two blocks -- so a first version that required the feature name and the number
# in the same block was green on all four pages, and its own selftest was the
# only reason that was found. The name and the number have to be read in the row
# that contains both, which is also the unit a buyer reads.
LEDGER_ROW = re.compile(r"<li\b[^>]*>(.*?)</li>|<tr\b[^>]*>(.*?)</tr>", re.I | re.S)
TAG = re.compile(r"<[^>]+>")


def ledger_rows(text: str) -> List[str]:
    """One stripped text string per list item and per table row."""
    rows: List[str] = []
    for match in LEDGER_ROW.finditer(text):
        row = normalize(TAG.sub(" ", match.group(1) or match.group(2) or ""))
        if row:
            rows.append(row)
    return rows


def plugin_check_count_findings(
    relative: str, page: str, text: Optional[str] = None
) -> List[str]:
    """Counted checks on a Pro page that disagree with the code.

    Both directions are the same comparison: too many and too few are the same
    gate pointed both ways, and under-selling a paid feature is as wrong as
    over-selling it -- that is the mistake opgave 36 had to walk back.
    """
    keys = plugin_check_keys(text)
    if not keys:
        return [
            f"{relative}: run_checks() in the plugin could not be read, so no "
            "check count on a Pro page can be verified"
        ]
    real = len(keys)
    history_name = {feature.key: feature for feature in _shipped_pro_features()}["history"].name
    findings: List[str] = []
    for row in ledger_rows(page):
        if not history_name.search(row) and not PLUGIN_SCAN_SUBJECT.search(row):
            continue
        for match in COUNTED_CHECKS.finditer(row):
            word = match.group(1).lower()
            stated = int(word) if word.isdigit() else NUMBER_WORDS.get(word, 0)
            if stated and stated != real:
                findings.append(
                    f"{relative}: this page says the Pro scan covers {stated} checks, "
                    f"but the plugin's run_checks() writes {real} ({', '.join(keys)})"
                )
    return findings


def denial_findings(relative: str, blocks: Sequence[TextBlock], text: Optional[str] = None) -> List[str]:
    """Pages that deny a Pro feature the plugin still ships.

    Four things have to line up, and each one closes a hole the others leave
    open — the same shape as local_cadence_claim():

    * the page talks about the Pro licence at all (decided by the caller);
    * the code still ships the feature, read by predicate, not from a list;
    * a name and a denial sit in the same clause — and the clause is not scoped
      to the hosted version, which is the one denial the product requires;
    * the block is not a paragraph about other vendors.

    That last one is a limit of a text check, so it is worth being explicit about
    what it costs. OTHER_PRODUCTS is read on the **block**, because a competitor
    comparison is a promise about somebody else's product: "TrustScan's free scan
    does not include a downloadable report" is not a claim about our licence and
    flagging it would only teach the next edit to leave the comparison out.

    ROADMAP used to sit next to it, on the same reasoning — a roadmap box is the
    same promise in a different frame. That was correct when the check was
    written and it stopped being correct the moment the plugin shipped two of the
    things its roadmap said were absent: 1.3.4 put 52 weeks of per-check history
    behind is_pro(), and 1.3.10 put the pass-to-fail mail there. The Danish box
    kept saying "30 dages historik pr. tjek" and "e-mail ved overgang fra
    bestået til fejlet" were not included — a false statement in the buy flow, in
    all four languages, on the page that sells the 79 USD product. So a roadmap
    item now stands or falls on the same test as every other item: it is exempt
    when it is scoped to the hosted version, and red when it denies a shipped
    feature flatly. The over-claim gate still reads ROADMAP, so a roadmap box can
    still not over-promise.
    """
    findings: List[str] = []
    for feature in _shipped_pro_features():
        if not feature.shipped():
            continue
        for block in blocks:
            if block.kind == "image-metadata":
                continue
            if OTHER_PRODUCTS.search(block.text):
                continue
            for name in feature.name.finditer(block.text):
                start = max(0, name.start() - feature.window)
                end = min(len(block.text), name.end() + feature.window)
                clause = block.text[start:end]
                if not feature.denial.search(clause):
                    continue
                # Only a qualifier in this item's own run of text qualifies it.
                separators = list(LIST_SEPARATOR.finditer(clause, 0, name.start() - start))
                item = clause[separators[-1].end():] if separators else clause
                if HOSTED_QUALIFIER.search(item):
                    continue
                findings.append(
                    f"{relative}:{block.line}: {feature.label}: {clause.strip()}"
                )
    return findings


def claim_exempt(segment: str, match: re.Match, relative: str = "", label: str = "") -> bool:
    if label == "daily monitoring or rescans" and local_cadence_claim(relative, segment):
        return True
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
                    if claim_exempt(segment, match, relative, label):
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
    findings.extend(redirect_findings())
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


def plugin_manifest_versions() -> List[str]:
    """Every version named in the update manifest, newest first."""
    manifest = load_json(ROOT / "update.json", "update.json", [])
    if manifest is None:
        return []
    sections = manifest.get("sections")
    changelog = str(sections.get("changelog", "")) if isinstance(sections, dict) else ""
    return re.findall(r"=\s*([0-9]+\.[0-9]+\.[0-9]+)\s*(?:\([^)]*\))?\s*=", changelog)


def redirect_findings(redirects_text: Optional[str] = None) -> List[str]:
    """The version a release replaces must keep redirecting to the new one.

    Removing a plugin package from the tree without a redirect line sends every
    installation still on that version to a 404 on its own download — and it has
    now happened three times in this repo, because the deploy notes asked for the
    line and nobody read _redirects. So it is a check, not a note.

    The previous version is read from the manifest's own changelog rather than
    from git, so the check needs no history and cannot be satisfied by a commit
    that never existed. $redirects_text lets the selftest hand in a file it
    broke on purpose instead of patching the reader under every other check.
    """
    findings: List[str] = []
    if redirects_text is None:
        redirects = read_text(SITE / "_redirects", "site/_redirects", findings)
        if redirects is None:
            return findings
    else:
        redirects = redirects_text
    versions = plugin_manifest_versions()
    if len(versions) < 2:
        findings.append("update.json: changelog names fewer than two versions, so the replaced one cannot be checked")
        return findings
    previous = versions[1]
    if previous == PLUGIN_VERSION:
        findings.append(f"update.json: changelog does not mention a version before {PLUGIN_VERSION}")
        return findings
    current_zip = f"/assets/eucomply-{PLUGIN_VERSION}.zip"
    previous_zip = f"/assets/eucomply-{previous}.zip"
    for line in redirects.splitlines():
        parts = line.split()
        if len(parts) < 2 or parts[0].startswith("#"):
            continue
        if parts[0] == previous_zip:
            if parts[1] != current_zip:
                findings.append(f"site/_redirects: {previous_zip} must redirect to {current_zip}, not {parts[1]}")
            break
    else:
        findings.append(f"site/_redirects: {previous_zip} has no redirect, so installs on {previous} get a 404")
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
    # The replaced-version redirect, proved against a temp _redirects that has no
    # line for the version this release replaced — the exact state that shipped a
    # 404 to every install on 1.3.4, 1.3.5 and now 1.3.6.
    real_redirects = (SITE / "_redirects").read_text(encoding="utf-8")
    replaced = plugin_manifest_versions()[1]
    checks += 1
    if redirect_findings(real_redirects):
        failures.append(f"self-test redirect: the real _redirects was rejected: {redirect_findings(real_redirects)}")
    stripped = "\n".join(line for line in real_redirects.splitlines() if f"eucomply-{replaced}.zip" not in line)
    checks += 1
    if not any(replaced in finding for finding in redirect_findings(stripped)):
        failures.append(f"self-test redirect: a missing {replaced} line was not flagged")
    checks += 1
    if not any("0.0.1" in finding for finding in redirect_findings(real_redirects.replace(
            f"/assets/eucomply-{replaced}.zip /assets/eucomply-{PLUGIN_VERSION}.zip",
            f"/assets/eucomply-{replaced}.zip /assets/eucomply-0.0.1.zip"))):
        failures.append("self-test redirect: a redirect to the wrong package was not flagged")
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
    failures.extend(local_cadence_self_tests())
    checks += LOCAL_CADENCE_CHECKS
    checks += DENIAL_CHECKS
    checks += UNDER_CLAIM_CHECKS
    failures.extend(under_claim_self_tests())
    checks += UNDER_CLAIM_CHECKS
    checks += CHECK_COUNT_CHECKS
    failures.extend(check_count_self_tests())
    failures.extend(denial_self_tests())
    return checks, failures


# The one hole in the daily-rescan grab, and the properties that keep it narrow.
# It exists because the plugin really does schedule a daily scan, so the plugin
# is allowed to say so — but "says so" is three conditions, not one: the file is
# the plugin, the sentence says the cadence is local, and the code schedules a
# daily interval. Remove any one and the claim comes back. Two more hold it
# still: the gate must actually reach the sentence, and the hole must not leak
# sideways into the claims it has nothing to do with.
LOCAL_CADENCE_CHECKS = 9
LOCAL_DAILY = "EUComply Pro scans your site every day, on your own WordPress server."
LOCAL_DAILY_HOSTED = "EUComply Pro monitors your website daily in the background, from our servers."


def local_cadence_self_tests() -> List[str]:
    failures: List[str] = []
    real = read_text(ROOT / "plugin/eucomply.php", "self-test: plugin PHP", [])
    if real is None:
        return ["self-test local cadence: the plugin source could not be read"]
    if not plugin_schedules_daily_scan(real):
        # Without this, the first case below would be green for the wrong reason.
        failures.append("self-test local cadence: the plugin does not schedule a daily scan, so the hole has nothing to justify it")
    if text_findings("plugin/readme.txt", LOCAL_DAILY):
        failures.append("self-test local cadence: a scheduled daily scan in the plugin was flagged")
    # A sales page earns the daily cadence by naming where it runs. The sentence
    # the plugin readme is allowed, the same words without the local marker are
    # not, and that pair is the property -- not a page list.
    if text_findings("site/pro/index.html", LOCAL_DAILY):
        failures.append("self-test local cadence sales page: a daily scan scoped to your own WordPress was flagged on the Pro page")
    if not any("daily monitoring or rescans" in finding for finding in
               text_findings("site/pro/index.html", LOCAL_DAILY_HOSTED)):
        failures.append("self-test local cadence sales page: a hosted daily monitor was allowed on the Pro page")
    if not any("daily monitoring or rescans" in finding for finding in text_findings("plugin/readme.txt", LOCAL_DAILY_HOSTED)):
        failures.append("self-test local cadence: a hosted daily monitor inside the plugin was allowed")
    # Non-vacuity, and the property the first case rests on: the gate really does
    # look inside the plugin files, so the sentence above is let through by the
    # local marker and by nothing else.
    if not any("daily monitoring or rescans" in finding for finding in
               text_findings("plugin/readme.txt", "EUComply Pro scans your site every day, from our servers.")):
        failures.append("self-test local cadence: a plugin sentence without the local marker was not reached, so the hole is untested")
    # The hole is one label wide. A PDF claim that happens to sit in the same
    # sentence in the same file is a different promise and must stay red.
    if not any("runtime PDF reports" in finding for finding in
               text_findings("plugin/readme.txt", "EUComply Pro saves a daily PDF report on your own WordPress server.")):
        failures.append("self-test local cadence: the hole leaked into a claim it has nothing to do with")
    without_daily = real.replace("? 'daily' : 'weekly'", "? 'hourly' : 'weekly'")
    if plugin_schedules_daily_scan(without_daily) or local_cadence_claim("plugin/readme.txt", LOCAL_DAILY, without_daily):
        failures.append("self-test local cadence: the local sentence survived a plugin that no longer scans daily")
    if plugin_schedules_daily_scan(real.replace("$want", "'weekly'")):
        failures.append("self-test local cadence: a hardcoded interval was read as a decided one")
    # A changelog is not a sentence. A whole update.json blob carries the marker
    # in one release and the claim in another, so the hole must not reach it.
    if local_cadence_claim("plugin/readme.txt", "on your own WordPress server. " + "Earlier release text. " * 40 + LOCAL_DAILY):
        failures.append("self-test local cadence: a wall of text was accepted as one local statement")
    return failures


# The denied-feature check, and the properties that keep it from being a blunt
# "no negatives on sales pages" rule. Each negative case below is a sentence the
# product REQUIRES — a hosted-only disclaimer, a roadmap box, a competitor
# comparison — so a gate that simply forbade them would push the site into
# over-claiming instead, which is the other half of the same problem.
UNDER_CLAIM_CHECKS = 8

# The eight truths the four published pages must reach. Written as the pages
# actually read, because a selftest written after the pattern is the reason a
# vocabulary gap survives: the EN/DE/FR words here were each absent from a name
# pattern on the first run, which is how a whole language goes unread and green.
UNDER_CLAIM_SAMPLE = {
    "site/pro/index.html": (
        "<li><b>Daily automatic re-scans</b><p>A Pro site is scanned once a day.</p></li>"
        "<li><b>Scan history: one snapshot per day, per check</b><p>52 days of history.</p></li>"
        "<li><b>Email alert when a check breaks</b><p>The plugin emails the owner.</p></li>"
        "<li><b>A read-only report link for your client</b><p>The client opens it without a login.</p></li>"
    ),
    "site/da/pro/index.html": (
        "<li><b>Daglige automatiske scanninger</b><p>Scannes én gang om dagen.</p></li>"
        "<li><b>Scanningshistorik: ét snapshot om dagen</b><p>52 dages historik.</p></li>"
        "<li><b>Mailalarm, når et tjek bryder</b><p>Pluginen sender en mail.</p></li>"
        "<li><b>Et skrivebeskyttet rapportlink til din kunde</b><p>Kunden åbner det uden login.</p></li>"
    ),
    "site/de/pro/index.html": (
        "<li><b>Tägliche automatische Scans</b><p>Wird einmal täglich gescannt.</p></li>"
        "<li><b>Scan-Verlauf: täglich ein Eintrag</b><p>52 Einträge Verlauf.</p></li>"
        "<li><b>E-Mail-Alarm, wenn eine Prüfung ausfällt</b><p>Das Plugin verschickt eine E-Mail.</p></li>"
        "<li><b>Ein schreibgeschützter Berichtslink für Ihren Kunden</b><p>Ohne Anmeldung.</p></li>"
    ),
    "site/fr/pro/index.html": (
        "<li><b>Scans automatiques quotidiens</b><p>Scanné une fois par jour.</p></li>"
        "<li><b>Historique de scan : une entrée par jour</b><p>52 relevés.</p></li>"
        "<li><b>Alerte e-mail quand un contrôle échoue</b><p>L\'extension envoie un e-mail.</p></li>"
        "<li><b>Un lien de rapport en lecture seule pour votre client</b><p>Sans connexion.</p></li>"
    ),
    "site/pricing/index.html": (
        "<tr><td>Daily scheduled WordPress scan</td><td>\u2014</td><td>Yes, in the plugin</td></tr>"
        "<tr><td>Scan history: one snapshot per day, per check</td><td>\u2014</td><td>Yes, in the plugin</td></tr>"
        "<tr><td>Email alert when a check passes and later fails</td><td>\u2014</td><td>Yes, in the plugin</td></tr>"
        "<tr><td>Read-only report link for a client</td><td>\u2014</td><td>Yes, in the plugin</td></tr>"
    ),
}


def under_claim_self_tests() -> List[str]:
    """Both directions of the new check, and the real pages behind them.

    The positive half is the part that matters: it reads the eight *published*
    pages, so a vocabulary gap in a language is red here rather than a page that
    ships three features and calls the rest planned.
    """
    failures: List[str] = []
    for relative, markup in UNDER_CLAIM_SAMPLE.items():
        for feature in ("a scan history", "a client report link", "an e-mail alert", "daily re-scans"):
            if under_claim_findings(relative, parse_html(markup).claim_blocks(relative)):
                failures.append(f"self-test under-claim {relative}: a complete Pro page was flagged")
    # The page as it read on 26/9: three features, the rest under "planned".
    bare = "<ul><li><b>Pro license in WordPress</b><p>Validated in the plugin.</p></li></ul>"
    findings = under_claim_findings("site/pro/index.html", parse_html(bare).claim_blocks("site/pro/index.html"))
    for feature in ("a scan history", "an e-mail alert", "daily re-scans"):
        if not any(feature in finding for finding in findings):
            failures.append(f"self-test under-claim silent: a page that never mentions {feature} passed")
    # A hosted roadmap line names the same words and sells nothing: it must not
    # be able to satisfy the check, or the site could stay exactly as it is.
    hosted = (
        "<p class=\"status\">Planned features, not included today: hosted daily re-scans, "
        "a scan history in the hosted service, runtime PDF reports and a live badge.</p>"
    )
    findings = under_claim_findings("site/pro/index.html", [TextBlock(re.sub(r"<[^>]+>", " ", hosted), 1)])
    if len(findings) < 3:
        failures.append("self-test under-claim roadmap: a hosted roadmap line was able to pass as a sale")
    for relative in sorted(PRO_TRUTH_SURFACES):
        path = ROOT / relative
        if not path.exists():
            continue
        text = read_text(path, f"self-test under-claim: {relative}", [])
        if text is None:
            continue
        if under_claim_findings(relative, parse_html(text).claim_blocks(relative)):
            failures.append(f"self-test under-claim real page {relative}: the published page does not sell everything the plugin ships")
    return failures


DENIAL_CHECKS = 24
DENIED_LOCAL = "Hosted re-scans, scan history, PDF reports and a live badge are not part of it."
DENIED_LOCAL_DA = "Hosted re-scans, historik, PDF og det live badge er ikke en del af det."
DENIED_LOCAL_DE = "Hostete Re-Scans, Historie, PDF und das Live-Badge sind nicht enthalten."
DENIED_LOCAL_FR = "Les re-scans hébergés, l’historique, le PDF et le badge en direct n’en font pas partie."


def denial_self_tests() -> List[str]:
    failures: List[str] = []
    real = read_text(ROOT / "plugin/eucomply.php", "self-test: plugin PHP", [])
    if real is None:
        return ["self-test denial: the plugin source could not be read"]
    if not plugin_ships_history(real):
        # Without this the cases below would be green for the wrong reason: the
        # check has nothing to enforce, so it enforces nothing and looks calm.
        failures.append("self-test denial: the plugin ships no Pro-gated history, so the check has nothing to justify it")
    if not plugin_ships_alert(real):
        failures.append("self-test denial alert: the plugin ships no Pro-gated alert, so the check has nothing to justify it")

    def denied(text: str, relative: str = "site/plugin/index.html") -> List[str]:
        return denial_findings(relative, [TextBlock(text, 1)])

    # Caught, once per language. DE and FR are here for a reason: the first run
    # of this check reported EN and DA and read neither, so nothing was red and
    # nothing was tested.
    for name, text in (
        ("EN", DENIED_LOCAL),
        ("DA", DENIED_LOCAL_DA),
        ("DE", DENIED_LOCAL_DE),
        ("FR", DENIED_LOCAL_FR),
    ):
        if not denied(text):
            failures.append(f"self-test denial {name}: a page denying shipped Pro history was allowed")
    # The page gate has to reach all four, or the cases above pass on two.
    for name, text in (
        ("EN", "Pro is a license key you paste into the plugin's settings screen."),
        ("DA", "79 USD pr. websted pr. år er en Pro-licens."),
        ("DE", "79 USD pro Website pro Jahr ist eine Pro-Lizenz."),
        ("FR", "79 USD par site web et par an est une licence Pro."),
    ):
        if not PRO_PAGE_CONTEXT.search(text):
            failures.append(f"self-test denial page gate {name}: the gate would never read a {name} page")
    # Required honesty: a denial scoped to the hosted version is not an
    # under-claim, because the history ships in the customer's own WordPress.
    for name, text in (
        ("hosted EN", "Hosted scan history is not included in your Pro license."),
        ("hosted DA", "Hostet scanningshistorik er ikke inkluderet i din Pro-licens."),
        ("hosted DE", "Gehosteter Scan-Verlauf ist nicht in Ihrer Pro-Lizenz enthalten."),
        ("hosted FR", "L’historique hébergé n’est pas inclus dans votre licence Pro."),
    ):
        if denied(text):
            failures.append(f"self-test denial {name}: a hosted-only disclaimer was flagged, so the site is pushed into over-claiming")
    # A roadmap box is the same promise in a different frame — but only while
    # each item is scoped. This case used to be green unconditionally, written
    # when the plugin shipped no history; 1.3.4 and 1.3.10 made it false, and all
    # four /pro/ pages kept denying two shipped features until this flip.
    if not denied("Planlagte funktioner (ikke inkluderet i dag): 30 dages historik pr. tjek."):
        failures.append("self-test denial roadmap: a roadmap item denying shipped history flatly was allowed")
    if denied("Planlagte funktioner (ikke inkluderet i dag): scanningshistorik i den hostede tjeneste, som du kan læse uden WordPress."):
        failures.append("self-test denial roadmap hosted: a hosted-scoped roadmap item was flagged, so the site is pushed into over-claiming")
    # Somebody else's product is not our licence.
    if denied("Cookiebot and CookieYes are consent platforms. TrustScan's free scan does not include a downloadable report."):
        failures.append("self-test denial competitor: a competitor comparison was flagged")
    # A claim, not a denial, is the over-claim gate's business and stays there.
    if denied("EUComply Pro keeps a scan history of your latest scans."):
        failures.append("self-test denial no-denial: a sentence that denies nothing was flagged")
    # Two mutations that were green the first time round, so both are properties
    # now: a comment must not stand in for the call it names, and the guard must
    # be the denial and not the parameter that is called $pro.
    if plugin_ships_history(real.replace("echo $this->build_history_section();", "// gone;")):
        failures.append("self-test denial comment: a phpcs:ignore comment kept a deleted history render looking shipped")
    if plugin_ships_history(real.replace("|| ! $pro )", "")):
        failures.append("self-test denial guard: the export's $pro parameter passed as a Pro gate that was deleted")
    if not plugin_ships_history(real):
        failures.append("self-test denial trace: the untouched plugin no longer reads as shipping a Pro history")
    # The alert cases, once per language, plus the three mutations that would
    # each leave the pages above free to deny a feature that is no longer sent.
    for name, text in (
        ("alert EN", "Pass-to-fail email alerts are planned and are not included in the current Pro license."),
        ("alert DA", "E-mail-alarmer er planlagt og ikke inkluderet i den nuværende Pro-licens."),
        ("alert DE", "E-Mail-Meldungen beim Wechsel von bestanden zu fehlgeschlagen sind nicht enthalten."),
        ("alert FR", "Les alertes par e-mail lors du passage d'un contrôle à un échec ne sont pas incluses."),
    ):
        if not denied(text):
            failures.append(f"self-test denial {name}: a page denying the Pro mail alert was allowed")
    if denied("Hosted email alerts are not included in your Pro license."):
        failures.append("self-test denial alert hosted: a hosted-only alert disclaimer was flagged")
    if plugin_ships_alert(real.replace("$this->maybe_send_alert( $results );", "// gone;")):
        failures.append("self-test denial alert wire: an alert that run_checks() no longer sends read as shipped")
    if plugin_ships_alert(real.replace("if ( ! $this->is_pro() ) {\n            return false; // Rule 2.", "if ( false ) {\n            return false;")):
        failures.append("self-test denial alert guard: a free-tier alert passed as a Pro-gated one")
    if plugin_ships_alert(real.replace("wp_mail(", "/* no mail */ not_mail(")):
        failures.append("self-test denial alert send: an alert that never mails read as shipped")
    return failures


# The counted-checks gate. Every case below is a sentence the product either
# requires or forbids, written as the four locales actually write it -- the
# reason a vocabulary gap survives is a selftest written after the pattern.
CHECK_COUNT_CHECKS = 13

# The published history rows, with the count they must be allowed to state.
# The number a history row has to state, in each language, built from the code
# rather than written here. A fixture that says "six" stops testing anything the
# day a seventh check ships -- which is exactly what happened when 1.3.11 went
# out, so the fixture is now derived and cannot rot.
_NUMBER_WORDS_BY_LANG = {
    "en": "zero one two three four five six seven eight nine ten eleven twelve".split(),
    "da": "nul en to tre fire fem seks syv otte ni ti elleve tolv".split(),
    "de": "null eins zwei drei vier fünf sechs sieben acht neun zehn elf zwölf".split(),
    "fr": "zéro un deux trois quatre cinq six sept huit neuf dix onze douze".split(),
}


def number_word(value: int, lang: str = "en") -> str:
    """The word NUMBER_WORDS parses back, for the same number.

    Round-trips through the table the gate actually uses, so a fixture written
    with this cannot disagree with the parser it is testing.
    """
    words = _NUMBER_WORDS_BY_LANG.get(lang, _NUMBER_WORDS_BY_LANG["en"])
    if value < 0 or value >= len(words):
        raise ValueError(f"no word for {value} in {lang}")
    word = words[value]
    if NUMBER_WORDS.get(word) != value:
        raise ValueError(f"{word!r} does not round-trip to {value} in {lang}")
    return word


def plugin_check_count() -> int:
    """How many checks run_checks() writes right now.

    One reader for every count claim in this file, so the self-test and the gate
    cannot end up with two different ideas of the product's size.
    """
    return len(plugin_check_keys())


def check_count_sample() -> Dict[str, str]:
    """The rows the Pro/pricing pages have to state, with the real number."""
    en, da, de, fr = (number_word(plugin_check_count(), lang) for lang in ("en", "da", "de", "fr"))
    return {
        "site/pro/index.html": f"<li><b>Scan history</b><p>Every Pro scan records one snapshot per day with the state of each of the {en} checks the plugin runs.</p></li>",
        "site/da/pro/index.html": f"<li><b>Scanningshistorik</b><p>Hver Pro-scanning registrerer ét snapshot om dagen med tilstanden for hvert af de {da} tjek pluginen kører.</p></li>",
        "site/de/pro/index.html": f"<li><b>Scan-Verlauf</b><p>Jeder Pro-Scan schreibt einen Eintrag je Tag mit dem Zustand jeder der {de} Prüfungen, die das Plugin ausführt.</p></li>",
        "site/fr/pro/index.html": f"<li><b>Historique de scan</b><p>Chaque scan Pro enregistre une entrée par jour avec l’état de chacun des {fr} contrôles exécutés par le plugin.</p></li>",
        "site/pricing/index.html": "<tr><td>Scan history: one snapshot per day, per check</td><td>—</td><td>Yes, in the plugin</td></tr>",
    }


def check_count_self_tests() -> List[str]:
    """Both directions of the count, the real pages behind them, and the read.

    The number in the product is read from run_checks() rather than written here,
    and every fixture below is built from that number. A self-test with a
    hardcoded count silently stops testing the day the count changes -- which is
    not hypothetical: when 1.3.11 took the plugin from six checks to eleven, the
    old fixtures asked for "run_checks() writes 6", every case failed, and the
    only thing that was actually wrong was the test.
    """
    failures: List[str] = []
    real = read_text(ROOT / "plugin/eucomply.php", "self-test: plugin PHP", [])
    if real is None:
        return ["self-test check count: the plugin source could not be read"]
    keys = plugin_check_keys(real)
    count = len(keys)
    if count < 2:
        failures.append(
            f"self-test check count: run_checks() reads as {count} checks {keys}, "
            "so the fixtures below would be testing a product that does not exist"
        )
    for expected in ("ssl", "cookies", "forms", "backups", "plugins", "legal"):
        if expected not in keys:
            failures.append(f"self-test check count: run_checks() no longer writes {expected}")
    # Both directions on the same number: too high is the bug that shipped, too
    # low is the same gate pointed the other way, and under-selling a paid
    # feature is the mistake opgave 36 had to walk back. Both wrong numbers are
    # derived, so neither can become the real one by accident.
    for name, relative, text in (
        ("EN", "site/pro/index.html", f"<li><b>Scan history</b><p>Every Pro scan records one snapshot per day with the state of each of the {number_word(count + 1)} checks.</p></li>"),
        ("DA", "site/da/pro/index.html", f"<li><b>Scanningshistorik</b><p>Hver Pro-scanning registrerer ét snapshot om dagen med tilstanden for hvert af de {number_word(count - 1, 'da')} tjek.</p></li>"),
        ("DE", "site/de/pro/index.html", f"<li><b>Scan-Verlauf</b><p>Jeder Pro-Scan schreibt einen Eintrag je Tag mit dem Zustand jeder der {number_word(count + 1, 'de')} Prüfungen.</p></li>"),
        ("FR", "site/fr/pro/index.html", f"<li><b>Historique de scan</b><p>Chaque scan Pro enregistre une entrée par jour avec l’état de chacun des {number_word(count - 1, 'fr')} contrôles.</p></li>"),
    ):
        found = plugin_check_count_findings(relative, text, real)
        if not any(f"run_checks() writes {count}" in finding for finding in found):
            failures.append(f"self-test check count {name}: a wrong count on a history row was allowed: {found}")
    for relative, text in check_count_sample().items():
        found = plugin_check_count_findings(relative, text, real)
        if found:
            failures.append(f"self-test check count required {relative}: {found}")
    # The universal scanner's nine checks are a different product, and the pages
    # that say so are right. A gate that flagged these would push the site into
    # denying a scan that really does run nine checks.
    for name, relative, text in (
        ("scan EN", "site/scan/index.html", '<p class="status">The nine checks above are the technical basics; Pro adds the documents that go with them.</p>'),
        ("home EN", "site/index.html", "<li><b>It runs nine checks</b><p>Each check looks for concrete evidence.</p></li>"),
        ("vs EN", "site/pro/vs-cookiebot/index.html", "<p>Run our free scan on your own URL &mdash; nine checks, no signup, results in seconds.</p>"),
    ):
        found = plugin_check_count_findings(relative, text, real)
        if found:
            failures.append(f"self-test check count {name}: the universal scanner's nine checks were read as the plugin's: {found}")
    # The gate must be able to say that it read nothing, or "no claim to check"
    # and "no claim" look identical.
    if not plugin_check_count_findings("site/pro/index.html", "", "<?php class X { function other() {} }"):
        failures.append("self-test check count unreadable: an unreadable run_checks() was not reported")
    # An unreadable numeral is not guessed at.
    odd = "<li><b>Scan history</b><p>Every Pro scan records the state of each of the sixteen-ish checks.</p></li>"
    if plugin_check_count_findings("site/pro/index.html", odd, real):
        failures.append("self-test check count unknown word: a numeral outside the table was turned into a finding")
    # Numbers that are not check counts stay untouched: a history length and a
    # price are the same digits as a count and a different promise.
    for name, text in (
        ("history length", "<li><b>Scan history</b><p>The report shows the most recent 12 and says how many are on record, up to 52.</p></li>"),
        ("price", "<li><b>Scan history</b><p>Pro costs 79 USD per website per year.</p></li>"),
    ):
        found = plugin_check_count_findings("site/pro/index.html", text, real)
        if found:
            failures.append(f"self-test check count {name}: a number that is not a check count was flagged: {found}")
    # The read follows the code. A plugin that drops a check moves the number
    # the pages have to state, so the gate cannot be satisfied by editing four
    # locales until they agree with each other.
    line = next((ln for ln in real.splitlines() if "$results['backups']" in ln), "")
    if not line:
        failures.append("self-test check count read: the backups assignment is gone, so the read cannot be tested")
    else:
        fewer = real.replace(line + "\n", "")
        if len(plugin_check_keys(fewer)) != count - 1:
            failures.append("self-test check count read: removing a check from run_checks() did not move the count")
        stale = f"<li><b>Scan history</b><p>Every Pro scan records the state of each of the {number_word(count)} checks.</p></li>"
        if not plugin_check_count_findings("site/pro/index.html", stale, fewer):
            failures.append("self-test check count read: a count that matched the old plugin was accepted after a check was removed")
    return failures


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
        if path.suffix.lower() in {".html", ".htm"} and PRO_PAGE_CONTEXT.search(text):
            # A page that talks about the Pro licence may not deny a feature that
            # licence unlocks. This direction is otherwise unwatched: the gate
            # stays green, the page stays published, the feature stays unsold.
            findings.extend(denial_findings(relative, parse_html(text).claim_blocks(relative)))
        if relative in PRO_TRUTH_SURFACES:
            # The other direction, on the pages a buyer compares plans on: a
            # shipped feature nobody names is a feature nobody pays extra for.
            findings.extend(under_claim_findings(relative, parse_html(text).claim_blocks(relative)))
            # And a number on those same pages, which no name pattern can see:
            # how many checks the Pro scan covers is parsed out of run_checks().
            findings.extend(plugin_check_count_findings(relative, text))
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
