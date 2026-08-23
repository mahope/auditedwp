/**
 * EUComply Universal Scan Engine — shared core module
 *
 * Platform-independent compliance scanner: takes any URL, returns a JSON
 * compliance report. Works regardless of CMS/platform.
 *
 * Checks (header/HTML based, no CMS assumptions):
 *   0.  consent_mode_v2 — Google Consent Mode v2 signatures
 *   0a. tcf            — IAB Transparency & Consent Framework
 *   1.  ssl            — HTTPS + HSTS header
 *   2.  cookies        — cookie banner / consent platform detection in HTML
 *   3.  forms          — form markup + privacy-policy link presence
 *   4.  legal          — privacy policy / imprint / accessibility statement links
 *   5.  headers        — security headers (CSP, X-Content-Type-Options, Referrer-Policy, X-Frame-Options)
 *   6.  tech           — platform fingerprint (informational)
 *   7.  dora           — DORA resilience check (email redundancy, DNS failover signals)
 *
 * Import: import { runScan, normalizeUrl } from '../shared/scan-engine.js'
 */

export const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

const UA = "Mozilla/5.0 (compatible; EUComplyScan/1.0; +https://auditedwp.pages.dev)";

const IAB_TCF_SIGNATURES = [
  { re: /__tcfapi|tcfapi/i, name: "IAB TCF API (__tcfapi)" },
  { re: /IABTCF_[a-z]/i, name: "IAB TCF cookies set" },
  { re: /gdprApplies|tcf[_-]?gdpr/i, name: "GDPR applies / TCF GDPR signals" },
  { re: /IAB[_-]?Consent[_-]?String|tcstring|consent[_-]?string[_-]?tcf/i, name: "IAB Consent String present" },
  { re: /tcf[_-]?v[12]|tcfapiv[12]/i, name: "TCF version indicator" },
];
const CMV2_SIGNATURES = [
  { re: /google_consent_mode|consent_mode_v2|cmv2[\s_,]/i, name: "Google Consent Mode v2 class/attribute" },
  { re: /gtag\(['"]consent['"]|'consent',\s*['"]default['"]|consent.*default.*ad_storage|ad_storage.*consent/i, name: "Google Consent Mode v2 (gtag)" },
  { re: /dataLayer[\s\S]{0,200}consent[\s\S]{0,200}(default|update)/i, name: "Google Consent Mode v2 (dataLayer)" },
  { re: /granted|denied[\s\S]{0,40}ad_storage|ad_storage[\s\S]{0,40}(granted|denied)/i, name: "Consent signals for ad storage and personalization" },
  { re: /google_ads[\s\S]{0,100}consent|consent[\s\S]{0,100}google_ads/i, name: "Google Ads consent integration" },
  { re: /consent.*analytics_storage|analytics_storage.*consent/i, name: "Analytics storage consent signal" },
];

const CONSENT_SIGNATURES = [
  { re: /cookiebot|consentmanager|onetrust|usercentrics/i, name: "Cookiebot / OneTrust / Usercentrics / ConsentManager" },
  { re: /cookieyes|cookie-yes|cookieyes/i, name: "CookieYes" },
  { re: /tarteaucitron|klaro|osano|cookieconsent/i, name: "TarteAuCitron / Klaro / Osano / CookieConsent" },
  { re: /complianz|cmplz/i, name: "Complianz GDPR" },
  { re: /cookie[_-]?notice|gdpr[_-]?banner|eu[_-]?cookie/i, name: "Generic cookie consent banner" },
  { re: /axeptio/i, name: "Axeptio" },
  { re: /cookiescript/i, name: "CookieScript" },
  { re: /cookiehub|cookie[_-]?hub/i, name: "CookieHub" },
  { re: /iubenda|cookie[_-]?solution/i, name: "iubenda" },
  { re: /justuno|privy|optinmonster/i, name: "JustUno / Privy / OptinMonster (popup detected)" },
  { re: /shoper|shoprenter|idelo/i, name: "CEE/PL consent plugin" },
  { re: /wp-consent-api/i, name: "WP Consent API" },
  { re: /borlabs|cookieninja/i, name: "Borlabs / CookieNinja" },
  { re: /real[_-]?cookie[_-]?banner/i, name: "Real Cookie Banner" },
  { re: /cookie[_-]?notice[_-]?lite/i, name: "Cookie Notice Lite" },
  { re: /gdpr[_-]?cookie[_-]?compliance/i, name: "GDPR Cookie Compliance" },
  { re: /moove[_-]?gdpr/i, name: "Moove GDPR" },
  { re: /pixel[_-]?your[_-]?site/i, name: "PixelYourSite (GDPR)" },
  { re: /webtoffee|gdpr[_-]?cookie[_-]?consent/i, name: "WebToffee GDPR" },
  { re: /quantcast[_-]?choice/i, name: "Quantcast Choice" },
  { re: /analytics[_-]?cat/i, name: "Analytify/CAOS" },
];

const DORA_SIGNATURES = [
  { re: /spf[_-]?record|v[_-]?=spf/i, name: "SPF (Email sender auth)" },
  { re: /dkim|[_-]?domainkey/i, name: "DKIM (Email signing)" },
  { re: /dmarc_|dmarc[_-]?record|_dmarc\./i, name: "DMARC (Email policy)" },
  { re: /mx[_-]?record|mx [0-9]|mail[_-]?exchange/i, name: "MX (Mail exchange)" },
  { re: /multiple[_-]?server|failover|redundan|multi[_-]?az[_-]?dns/i, name: "Multi-server / failover signals" },
  { re: /cdn[_-]?failover|multi[_-]?cdn|backup[_-]?origin/i, name: "CDN failover / multi-CDN" },
  { re: /incident[_-]?response|soc[_-]?report|security[_-]?incident/i, name: "Incident response / SOC reporting" },
  { re: /bcdr|bcp[_-]?plan|dr[_-]?plan|business[_-]?continuity/i, name: "BC/DR planning reference" },
  { re: /status[_-]?page|uptime[_-]?monitor/i, name: "Status page / uptime monitoring" },
];

const FORM_PLUGIN_SIGNATURES = [
  // NOTE: all patterns are anchored tightly (boundaries/exact slugs) so they
  // cannot false-positive on arbitrary substrings in non-WordPress HTML.
  { re: /contact[_-]form[_-]7|\bwpforms\b|\bformidable\b|gravity[_-]?forms|fluent[_-]?forms?\b|ninja[_-]?forms\b|caldera[_-]?forms\b|\bwpforms?-|\belementor\b[^<>]{0,40}form|\bwpcf7\b|\bcf7[-_]/i, name: "Contact Form 7 / WPForms / Formidable / Gravity / Fluent / Elementor" },
  { re: /\btypeform\b|\bformspree\b|\bjotform\b|cognito[_-]?forms\b|\bformsort\b/i, name: "Typeform / Formspree / Jotform" },
  { re: /woocommerce[_-]?checkout|wc_[_-]?checkout/i, name: "WooCommerce Checkout" },
  { re: /shopify[_-]?checkout|checkout[_-]?shopify/i, name: "Shopify Checkout" },
  { re: /stripe[_-]?checkout|stripe[_-]?payment|[_-]?stripe[_-]?form/i, name: "Stripe Checkout / Payment" },
];

const PLATFORM_SIGNATURES = [
  { re: /wp-content|wp-includes|wp-json|wordpress\.org|wp-|wordpress_|class="wp-/i, name: "WordPress" },
  { re: /cdn\.shopify|shopify\.com|shopify[_-]?checkout/i, name: "Shopify" },
  { re: /wix[_-]?site|wix\.com|wixstatic/i, name: "Wix" },
  { re: /squarespace\.com|squarespace[_-]?cdn/i, name: "Squarespace" },
  { re: /webflow\.io|webflow\.com/i, name: "Webflow" },
  { re: /next[_-]?data|Next\.js|_next\/static/i, name: "Next.js" },
  { re: /nuxt\.io|_nuxt\//i, name: "Nuxt" },
  { re: /drupal\.org|drupal[_-]?settings/i, name: "Drupal" },
  { re: /joomla\.org|com_content|joomla/i, name: "Joomla" },
  { re: /craft\.cms|craftcms|cms[_-]?craft/i, name: "Craft CMS" },
  { re: /typo3|tx_[_-]?news|p[_-]?id[_-]?typo/i, name: "TYPO3" },
  { re: /umbraco|umbraco[_-]?page/i, name: "Umbraco" },
  { re: /ghost\.org|ghost[_-]?hq|ghost[_-]?portal/i, name: "Ghost" },
  { re: /bigcommerce\.com|bigcommerce[_-]?cdn/i, name: "BigCommerce" },
  { re: /elementor[_-]?page|elementor[_-]?kit|elementor/i, name: "Elementor (WP page builder)" },
  { re: /siteground/i, name: "SiteGround (hosting)" },
  { re: /magento|varien[_-]?form|require[_-]?js[_-]?min/i, name: "Magento/Adobe Commerce" },
  { re: /prestashop|presta[_-]?shop|ps_[_-]?config/i, name: "PrestaShop" },
  { re: /opencart|oc_[_-]?cart/i, name: "OpenCart" },
];

const LEGAL_PATTERNS = [
  { re: /privacy|privacy[_-]?policy|datenschutz|gdpr|privacypolicy|data[_-]?protection/i, name: "Privacy / GDPR" },
  { re: /impressum|imprint|legal[_-]?notice|legal[_-]?disclosure|about[_-]?the[_-]?company/i, name: "Imprint / Legal notice" },
  { re: /accessibility[_-]?statement|a11y|accessibility[_-]?declaration|eaa[_-]?statement|barrierefreiheit/i, name: "Accessibility statement" },
  { re: /cookie[_-]?policy|cookie[_-]?declaration|cookie[_-]?settings|cookie[_-]?preferences/i, name: "Cookie policy" },
  { re: /terms[_-]?of[_-]?service|terms[_-]?and[_-]?conditions|agb|terms[_-]?of[_-]?use/i, name: "Terms & Conditions" },
  { re: /legal[_-]?notice|legal[_-]?info|impressum|disclaimer|legal[_-]?mention/i, name: "Legal / Imprint" },
  { re: /returns[_-]?policy|refund[_-]?policy|cancellation[_-]?policy|widerrufsrecht/i, name: "Returns / Refund policy" },
  { re: /shipping[_-]?policy|delivery[_-]?information|versand/i, name: "Shipping policy" },
  { re: /data[_-]?processing[_-]?agreement|dpa|data[_-]?processor|auftragsverarbeitung/i, name: "Data processing agreement" },
  { re: /acceptable[_-]?use[_-]?policy|aup|fair[_-]?use[_-]?policy/i, name: "Acceptable use / Fair use" },
  { re: /subprocessor|sub[_-]-?processor|subprocessors/i, name: "Sub-processor list" },
  { re: /code[_-]?of[_-]?conduct|coc|ethik/i, name: "Code of conduct" },
  { re: /sla[_-]?service[_-]?level|service[_-]?level[_-]?agreement|garantie/i, name: "SLA / Warranty" },
  { re: /complaints[_-]?policy|complaint[_-]?procedure|beschwerde/i, name: "Complaints procedure" },
  { re: /modern[_-]?slavery|slavery[_-]?act[_-]?statement|human[_-]?trafficking/i, name: "Modern slavery statement" },
  { re: /whistleblower|whistle[_-]?blowing|hinweisgeber/i, name: "Whistleblower / Hinweisgeber" },
  { re: /environmental[_-]?policy|sustainability[_-]?policy|umwelt/i, name: "Environmental / Sustainability policy" },
  { re: /gdpr[_-]?contact|dpo[_-]?contact|data[_-]?protection[_-]?officer|datenschutzbeauftragte/i, name: "DPO / Data protection officer" },
  { re: /info@|contact@|hello@|mail@|support@|sales@/i, name: "General contact address" },
];

export function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...CORS, "Content-Type": "application/json" },
  });
}

export function normalizeUrl(raw) {
  if (!raw || typeof raw !== "string") return null;
  let u = raw.trim();
  if (!/^https?:\/\//i.test(u)) u = "https://" + u;
  try {
    const p = new URL(u);
    if (!/^https?:$/.test(p.protocol) || !p.hostname.includes(".")) return null;
    return p.origin + (p.pathname === "/" ? "" : p.pathname.replace(/\/+$/, ""));
  } catch { return null; }
}

export async function runScan(url) {
  const rawUrl = url;
  url = normalizeUrl(url);
  if (!url) throw new Error("Invalid URL");
  const started = Date.now();

  // Fetch the page content
  const resp = await fetch(url, {
    headers: { "User-Agent": UA, Accept: "text/html,application/xhtml+xml,*/*" },
    redirect: "follow",
    signal: AbortSignal.timeout(12_000),
  });
  const finalUrl = resp.url;
  let html = "";
  const contentType = resp.headers.get("Content-Type") || "";
  if (contentType.includes("text/html") || contentType.includes("application/xhtml")) {
    html = await resp.text().catch(() => "");
  } else {
    // Try to read anyway for meta-pages
    html = await resp.text().catch(() => "");
  }

  const checks = {};

  // 0. Google Consent Mode v2 (platform-independent — detects in-page JS/HTML patterns)
  const cmv2Matches = [];
  for (const sig of CMV2_SIGNATURES) {
    if (sig.re.test(html)) cmv2Matches.push(sig.name);
  }
  checks.consent_mode_v2 = {
    pass: cmv2Matches.length >= 2,
    warn: cmv2Matches.length === 1,
    label: cmv2Matches.length >= 2
      ? "Google Consent Mode v2 detected"
      : cmv2Matches.length === 1
        ? "Partial Consent Mode v2 signals"
        : "No Google Consent Mode v2 detected",
    detail: cmv2Matches.length > 0
      ? `Consent Mode v2 signals: ${cmv2Matches.join(", ")}.`
      : "No Consent Mode v2 signals found. Since March 2024, Google requires Consent Mode v2 for ad personalization in the EEA. Without it, Google Ads conversion tracking may be restricted.",
  };
  if (cmv2Matches.length < 2) {
    checks.consent_mode_v2.fix =
      "Implement Google Consent Mode v2 with the default consent state for ad_storage and analytics_storage. See https://developers.google.com/tag-platform/security/guides/consent.";
  }
  // 0a. IAB TCF (Transparency & Consent Framework)
  const tcfMatches = [];
  for (const sig of IAB_TCF_SIGNATURES) {
    if (sig.re.test(html)) tcfMatches.push(sig.name);
  }
  checks.tcf = {
    pass: tcfMatches.length >= 2,
    warn: tcfMatches.length === 1,
    label: tcfMatches.length >= 2
      ? "IAB TCF detected"
      : tcfMatches.length === 1
        ? "Partial IAB TCF signals"
        : "No IAB TCF detected",
    detail: tcfMatches.length > 0
      ? `TCF signals: ${tcfMatches.join(", ")}.`
      : "No IAB Transparency & Consent Framework signals found. TCF is used by ad-tech platforms and publishers for GDPR consent management in programmatic advertising.",
  };
  if (tcfMatches.length < 2) {
    checks.tcf.fix =
      tcfMatches.length === 1
        ? "Partial TCF implementation detected. Ensure __tcfapi is available and IAB consent strings are properly stored."
        : "If you run programmatic ads in the EEA, implement IAB TCF through your CMP. See https://iabeurope.eu/tcf/.";
  }

  const hsts = resp.headers.get("Strict-Transport-Security") || "";
  checks.ssl = {
    pass: url.startsWith("https:") && hsts.length > 0,
    warn: url.startsWith("https:") && hsts.length === 0,
    label: hsts ? "HTTPS + HSTS OK" : url.startsWith("https:") ? "HTTPS, no HSTS" : "Not HTTPS",
    detail: hsts
      ? `HSTS: ${hsts.replace(/;\s*/g, "; ")}`
      : url.startsWith("https:")
        ? 'SSL active but Strict-Transport-Security header missing.'
        : "Site is not served over HTTPS.",
  };
  if (!hsts && url.startsWith("https:")) {
    checks.ssl.fix =
      'Add header: Strict-Transport-Security: "max-age=31536000; includeSubDomains; preload" to all responses.';
  } else if (!url.startsWith("https:")) {
    checks.ssl.fix = "Redirect all traffic to https://";
  }

  // 2. Cookie consent detection
  const consentMatches = [];
  for (const sig of CONSENT_SIGNATURES) {
    if (sig.re.test(html)) consentMatches.push(sig.name);
  }
  checks.cookies = {
    pass: consentMatches.length > 0,
    warn: consentMatches.length === 0,
    label: consentMatches.length > 0
      ? `Consent platform: ${consentMatches[0]}`
      : "No consent banner detected",
    detail: consentMatches.length > 0
      ? `Detected: ${consentMatches.join(", ")}`
      : "No known cookie-consent platform found in the HTML. If you set any non-essential cookies, EU ePrivacy rules require prior consent.",
  };
  if (consentMatches.length === 0) {
    checks.cookies.fix =
      "Add a consent management platform (e.g. one of the open-source options: Klaro, Tarteaucitron).";
  }

  // 3. Form detection + privacy link
  const formMatches = [];
  for (const sig of FORM_PLUGIN_SIGNATURES) {
    if (sig.re.test(html)) formMatches.push(sig.name);
  }
  const hasFormAction = /<form[^>]*action\s*=\s*["'](?:[^"']+:)?\/\/[^"']*["']/i.test(html);
  const hasLocalForm = /<form[^>]*>[\s\S]*?<\/form>/i.test(html);
  const hasPrivLink = LEGAL_PATTERNS[0].re.test(html);
  checks.forms = {
    pass: !(hasLocalForm && !hasPrivLink),
    warn: hasLocalForm && !hasPrivLink,
    label: formMatches.length > 0
      ? `${formMatches[0]} detected`
      : hasLocalForm
        ? "Form(s) found, no consent link"
        : "No forms found",
    detail: formMatches.length > 0
      ? `Form plugins detected: ${formMatches.join(", ")}. Ensure privacy link is visible near each form.`
      : hasLocalForm
        ? "Form markup found, but no privacy-policy link detected in page HTML. EU law requires a privacy notice at the point of data collection."
        : "No HTML forms detected on this page. If forms exist, ensure they link to a privacy policy.",
  };
  if (hasLocalForm && !hasPrivLink) {
    checks.forms.fix =
      'Add a link to your privacy policy (e.g. <a href="/privacy/">Privacy Policy</a>) next to each form submit button.';
  }

  // 4. Legal pages (privacy, imprint, terms, accessibility, cookie policy)
  const foundLegal = [];
  for (const sig of LEGAL_PATTERNS) {
    if (sig.re.test(html)) foundLegal.push(sig.name);
  }
  const uniqueLegal = [...new Set(foundLegal)];
  checks.legal = {
    pass: uniqueLegal.length >= 2,
    warn: uniqueLegal.length === 1,
    label: uniqueLegal.length > 0
      ? `${uniqueLegal.length} legal pages linked`
      : "No legal pages linked",
    detail:
      uniqueLegal.length > 0
        ? `Found on page: ${uniqueLegal.join(", ")}.`
        : "No standard legal page links found in the page HTML.",
  };
  if (uniqueLegal.length < 2) {
    checks.legal.fix =
      "Ensure your footer links at least Privacy Policy + Imprint/Legal Notice. For EU visitors, also consider Cookie Policy and Accessibility Statement.";
  }

  // 5. Security headers
  const headers = {
    "Content-Security-Policy": resp.headers.get("Content-Security-Policy") || resp.headers.get("Content-Security-Policy-Report-Only") || "",
    "X-Content-Type-Options": resp.headers.get("X-Content-Type-Options") || "",
    "Referrer-Policy": resp.headers.get("Referrer-Policy") || "",
    "X-Frame-Options": resp.headers.get("X-Frame-Options") || "",
    "Permissions-Policy": resp.headers.get("Permissions-Policy") || "",
  };
  const headerIssues = [];
  if (!headers["Content-Security-Policy"]) headerIssues.push("Content-Security-Policy missing");
  if (!headers["X-Content-Type-Options"]) headerIssues.push("X-Content-Type-Options: nosniff missing");
  if (!headers["Referrer-Policy"]) headerIssues.push("Referrer-Policy missing");
  if (!headers["X-Frame-Options"] && !headers["Content-Security-Policy"].includes("frame-ancestors")) headerIssues.push("X-Frame-Options or CSP frame-ancestors missing");
  checks.headers = {
    pass: headerIssues.length === 0,
    warn: headerIssues.length > 0 && headerIssues.length <= 2,
    label: headerIssues.length > 0
      ? `${headerIssues.length} security header${headerIssues.length > 1 ? "s" : ""} missing`
      : "All common security headers present",
    detail: headerIssues.length > 0 ? "Missing: " + headerIssues.join("; ") : "CSP, HSTS (checked above), X-Content-Type-Options, Referrer-Policy, X-Frame-Options all set.",
  };
  if (headerIssues.length > 0) {
    checks.headers.fix =
      "Add security headers. See https://securityheaders.com for guidance on each.";
  }

  // 6. DORA resilience (DNS + email + redundancy signals in HTML)
  const doraMatches = [];
  for (const sig of DORA_SIGNATURES) {
    if (sig.re.test(html)) doraMatches.push(sig.name);
  }
  checks.dora = {
    pass: doraMatches.length >= 2,
    warn: doraMatches.length === 1,
    label: doraMatches.length > 0
      ? `DORA resilience signals: ${doraMatches.length} found`
      : "No DORA resilience signals detected",
    detail: doraMatches.length > 0
      ? `Signals found in page/footer: ${doraMatches.join(", ")}.`
      : "No email-authentication (SPF/DKIM/DMARC), failover, or incident-response signals found in page text. DORA Art. 5-7 require resilience planning, incident management and digital operational testing for financial entities.",
  };
  if (doraMatches.length < 2) {
    checks.dora.fix =
      "Ensure your site provides: SPF/DKIM/DMARC records, status page URL, incident-response contact, and business-continuity information in your legal/security documentation.";
  }

  // 7. Tech fingerprint (informational)
  let platform = "Unknown";
  if (html) {
    const hit = PLATFORM_SIGNATURES.find(s => s.re.test(html));
    if (hit) platform = hit.name;
  }
  const generator = html.match(/<meta[^>]+name=["']generator["'][^>]+content=["']([^"']+)/i);
  if (generator) platform = generator[1];

  return {
    url: finalUrl,
    scannedAt: new Date().toISOString(),
    durationMs: Date.now() - started,
    platform,
    checks,
    score: (() => {
      const scored = Object.values(checks).filter(c => typeof c.pass === "boolean");
      const passed = scored.filter(c => c.pass).length;
      return { passed, total: scored.length, pct: scored.length ? Math.round(100 * passed / scored.length) : 0 };
    })(),
    disclaimer: "Automated technical checks only — not legal advice. Full compliance review requires a qualified professional.",
  };
}