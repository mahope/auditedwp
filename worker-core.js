/**
 * EUComply Universal Scan Engine — Cloudflare Worker
 *
 * Platform-independent compliance scanner: takes any URL, returns a JSON
 * compliance report. Works regardless of what CMS/stack the target runs
 * (WordPress, Shopify, Webflow, Next.js, Squarespace, hand-written HTML…).
 *
 * This is the CORE. The WordPress plugin is one wrapper around it; the
 * /scan/ web page is another.
 *
 * Checks (platform-agnostic, header/HTML based):
 *   1. ssl       — HTTPS + HSTS header
 *   2. cookies   — cookie banner / consent platform detection in HTML
 *   3. forms     — form markup + privacy-policy link presence
 *   4. legal     — privacy policy / imprint / accessibility statement links
 *   5. headers   — security headers (CSP, X-Content-Type-Options, Referrer-Policy, X-Frame-Options)
 *   6. tech      — platform fingerprint (informational, feeds advice)
 *
 * Free endpoint. Rate-limited per IP via KV (best effort).
 */

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

const UA = "Mozilla/5.0 (compatible; EUComplyScan/1.0; +https://auditedwp.pages.dev)";

// Cookie-consent platforms detectable in served HTML (works for any stack).
const CONSENT_SIGNATURES = [
  { name: "Cookiebot", re: /cookiebot\.com|CybotCookiebot/i },
  { name: "CookieYes", re: /cookieyes|cdn-cookieyes\.com/i },
  { name: "Complianz", re: /complianz/i },
  { name: "Cookie Notice / Cookie Law Info", re: /cookie-law-info|cookielawinfo|cookie-notice/i },
  { name: "Osano", re: /osano/i },
  { name: "OneTrust", re: /onetrust|cdn\.cookielaw\.org/i },
  { name: "Termly", re: /termly/i },
  { name: "Borlabs", re: /borlabs/i },
  { name: "Klaro", re: /klaro/i },
  { name: "Tarteaucitron", re: /tarteaucitron/i },
  { name: "Iubenda", re: /iubenda/i },
  { name: "Usercentrics", re: /usercentrics/i },
  { name: "Funding Choices", re: /fundingchoices|googlefc/i },
  { name: "WP Consent API", re: /wp-consent-api|wp_consent/i },
];

// DORA / Operational Resilience signals (Jan 2025 regulation, financial & ICT entities).
const DORA_SIGNATURES = [
  // Explicit DORA / resilience mentions
  { key: "dora_mention", label: "DORA / resilience framework mentioned", re: /digital\s*operational\s*resilience|DORA\s+regulation|operational\s*resilience\s+act/i },
  // Incident reporting
  { key: "incident_report", label: "ICT incident reporting process", re: /incident\s*report|report\s+(an\s+)?incident|ict\s+incident|security\s+incident\s+report|inform.*breach/i },
  // Business continuity / disaster recovery
  { key: "business_continuity", label: "Business continuity / disaster recovery", re: /business\s+continuity|disaster\s+recovery|BCP|DR\s+plan|continuity\s+plan|resilience\s+plan/i },
  // ICT risk management
  { key: "ict_risk", label: "ICT risk management mentioned", re: /ict\s+risk|information\s+security\s+risk|it\s+risk\s+management|risk\s+framework|risk\s+assessment/i },
  // Third-party / supply chain risk
  { key: "third_party_risk", label: "Third-party / supply chain risk", re: /third.party\s+risk|supply\s+chain\s+risk|vendor\s+risk|outsource.*risk/i },
  // Testing / penetration testing
  { key: "resilience_testing", label: "Resilience / penetration testing", re: /penetration\s+test|security\s+test|vulnerability\s+scan|red\s+team|threat\s+led|resilience\s+test/i },
];

const FORM_PLUGIN_SIGNATURES = [
  { name: "Contact Form 7", re: /wpcf7|contact-form-7/i },
  { name: "WPForms", re: /wpforms/i },
  { name: "Gravity Forms", re: /gform|gravityforms/i },
  { name: "HubSpot Forms", re: /hsforms|hbspt/i },
  { name: "Typeform", re: /typeform/i },
  { name: "Calendly", re: /calendly/i },
  { name: "Formspree", re: /formspree/i },
  { name: "Webflow Forms", re: /data-wf-page|w-form/i },
];

const PLATFORM_SIGNATURES = [
  { name: "WordPress", re: /wp-content|wp-includes|\/wp-json\/|generator.*wordpress/i },
  { name: "Shopify", re: /cdn\.shopify\.com|shopify\.theme/i },
  { name: "Wix", re: /static\.wixstatic\.com|wix-code/i },
  { name: "Squarespace", re: /squarespace|static1\.squarespace\.com/i },
  { name: "Webflow", re: /webflow|data-wf-site/i },
  { name: "Next.js", re: /__NEXT_DATA__|_next\/static/i },
  { name: "Nuxt", re: /__NUXT__|_nuxt\//i },
  { name: "Drupal", re: /drupal|sites\/default\/files/i },
  { name: "Joomla", re: /joomla|\/media\/jui\//i },
  { name: "Craft CMS", re: /craftcms/i },
  { name: "TYPO3", re: /typo3/i },
  { name: "Umbraco", re: /umbraco/i },
  { name: "Ghost", re: /ghost-sdk|content_api_key|ghost\.min\.js/i },
  { name: "BigCommerce", re: /bigcommerce/i },
  { name: "WooCommerce", re: /woocommerce/i },
  { name: "SiteGround Optimizer", re: /siteground-optimizer/i },
];

const LEGAL_PATTERNS = [
  { key: "privacy", label: "Privacy Policy", re: /href="[^"]*(privacy|datenschutz|persondata|gdpr|confidentialite|privacypolicy)[^"]*"/i },
  { key: "imprint", label: "Imprint / Legal Notice", re: /href="[^"]*(impressum|imprint|legal[^"]*notice|colophon|mentions-legales)[^"]*"/i },
  { key: "accessibility", label: "Accessibility Statement", re: /href="[^"]*(accessibilit|tilgaengelighed|tilgængelighed|barrierefreiheit|a11y)[^"]*"/i },
  { key: "terms", label: "Terms & Conditions", re: /href="[^"]*(terms|vilkår|vilkaar|agb|conditions|nutzungsbeding)[^"]*"/i },
];

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...CORS },
  });
}

function normalizeUrl(raw) {
  let u = (raw || "").trim();
  if (!u) return null;
  if (!/^https?:\/\//i.test(u)) u = "https://" + u;
  try {
    const parsed = new URL(u);
    if (!/^https?:$/.test(parsed.protocol)) return null;
    // Block obvious internal targets.
    const h = parsed.hostname;
    if (/^(localhost|127\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.|0\.|\[?::1)/.test(h)) return null;
    if (!h.includes(".")) return null;
    return parsed;
  } catch { return null; }
}

async function checkRateLimit(env, ip) {
  if (!env?.RATE) return; // KV optional
  const key = `rl:${ip}:${Math.floor(Date.now() / 600000)}`; // 10-min window
  const n = parseInt((await env.RATE.get(key)) || "0", 10);
  if (n >= 20) throw new Error("rate");
  await env.RATE.put(key, String(n + 1), { expirationTtl: 700 });
}

async function runScan(url) {
  const checks = {};
  const started = Date.now();

  // --- Fetch with redirect following ---
  let resp, finalUrl = url, fetchError = null;
  try {
    resp = await fetch(url.toString(), {
      redirect: "follow",
      headers: { "User-Agent": UA, "Accept": "text/html,application/xhtml+xml" },
    });
    finalUrl = resp.url || url.toString();
  } catch (e) {
    fetchError = String(e && e.message || e);
  }

  // 1. SSL
  if (fetchError) {
    checks.ssl = { pass: false, label: "Unreachable", detail: `Could not fetch the site: ${fetchError}`, fix: "Check that the URL is correct and the site is online." };
  } else if (url.protocol !== "https:") {
    checks.ssl = { pass: false, label: "Not HTTPS", detail: "Site is served over plain HTTP.", fix: "Install an SSL certificate and redirect all traffic to https:// (GDPR Art. 32)." };
  } else {
    const hsts = resp.headers.get("strict-transport-security");
    checks.ssl = hsts
      ? { pass: true, label: "HTTPS + HSTS OK", detail: `HSTS: ${hsts}` }
      : { pass: true, warn: true, label: "HTTPS, no HSTS", detail: "SSL active but Strict-Transport-Security header missing.", fix: 'Add header: Strict-Transport-Security: "max-age=31536000" (GDPR Art. 32 hardening).' };
  }

  let html = "";
  if (resp && resp.ok) {
    const ct = resp.headers.get("content-type") || "";
    if (/text\/html|application\/xhtml/i.test(ct)) {
      try { html = (await resp.text()).slice(0, 600_000); } catch { /* ignore */ }
    }
  }

  // 2. Cookies / consent
  if (html) {
    const found = CONSENT_SIGNATURES.filter(s => s.re.test(html)).map(s => s.name);
    const dedup = [...new Set(found)];
    checks.cookies = dedup.length
      ? { pass: true, label: `Consent platform detected (${dedup.slice(0, 3).join(", ")})`, detail: "A cookie-consent mechanism was found in the page HTML (ePrivacy Directive)." }
      : { pass: false, warn: true, label: "No consent banner detected", detail: "No known cookie-consent platform found in the HTML. If you set any non-essential cookies, EU ePrivacy rules require prior consent.", fix: "Add a consent management platform (e.g. one of the open-source options: Klaro, Tarteaucitron)." };
  } else if (!fetchError) {
    checks.cookies = { pass: false, warn: true, label: "Could not inspect HTML", detail: "Response was not HTML — cookie check skipped.", fix: "Verify manually that a consent banner is present." };
  }

  // 3. Forms
  if (html) {
    const hasForms = /<form[\s>]/i.test(html);
    const fp = [...new Set(FORM_PLUGIN_SIGNATURES.filter(s => s.re.test(html)).map(s => s.name))];
    const privacyLinked = LEGAL_PATTERNS.find(p => p.key === "privacy").re.test(html);
    if (!hasForms && !fp.length) {
      checks.forms = { pass: true, label: "No forms found", detail: "No form markup detected on the landing page — nothing to flag.", warn: true };
    } else {
      checks.forms = privacyLinked
        ? { pass: true, label: `Forms present${fp.length ? " (" + fp.slice(0, 2).join(", ") + ")" : ""}, privacy policy linked`, detail: "Form(s) found and a privacy-policy link is present on the page (GDPR transparency)." }
        : { pass: false, label: "Forms without visible privacy link", detail: "Form(s) detected but no privacy-policy link found in the page HTML. GDPR requires informing users at collection.", fix: "Link your Privacy Policy next to every form and add a consent checkbox." };
    }
  }

  // 4. Legal pages
  if (html) {
    const found = LEGAL_PATTERNS.filter(p => p.re.test(html)).map(p => p.label);
    const missing = LEGAL_PATTERNS.filter(p => !p.re.test(html)).map(p => p.label);
    const hasPrivacy = found.some(f => f === "Privacy Policy");
    checks.legal = hasPrivacy
      ? { pass: true, label: `Legal pages linked (${found.join(", ")})`, detail: missing.length ? `Not detected on homepage: ${missing.join(", ")} — they may exist on other pages.` : "All key legal pages detected." }
      : { pass: false, label: "No privacy policy link found", detail: "GDPR Art. 13 requires an accessible privacy policy. None was linked from the homepage HTML.", fix: "Publish a privacy policy and link it in the footer of every page." };
  }

  // 5. Security headers
  if (resp) {
    const want = {
      "content-security-policy": "Content-Security-Policy",
      "x-content-type-options": "X-Content-Type-Options",
      "referrer-policy": "Referrer-Policy",
      "x-frame-options": "X-Frame-Options (or CSP frame-ancestors)",
    };
    const missing = Object.entries(want).filter(([h]) => !resp.headers.get(h)).map(([, label]) => label);
    checks.headers = missing.length
      ? { pass: missing.length < 3, warn: missing.length >= 2, label: `${4 - missing.length}/4 security headers present`, detail: `Missing: ${missing.join(", ")}.`, fix: "Add the missing security headers in your server/CDN config (NIS2 Art. 21 / OWASP baseline)." }
      : { pass: true, label: "All 4 security headers present", detail: "CSP, X-Content-Type-Options, Referrer-Policy and frame protection all set." };
  }

  // 6. DORA / Operational Resilience (new Jan 2025 — informational but flags gaps)
  if (html) {
    const found = DORA_SIGNATURES.filter(s => s.re.test(html)).map(s => s.label);
    let warn, fix;
    let label, detail, pass;
    if (found.length >= 3) {
      pass = true; warn = false;
      label = `${found.length} resilience signals found`;
      detail = `Detected: ${found.slice(0, 4).join(", ")}. DORA applies to financial entities and critical ICT providers.`;
    } else if (found.length >= 1) {
      pass = true; warn = true;
      label = `${found.length} resilience signal${found.length > 1 ? "s" : ""} found`;
      detail = `Found: ${found.join(", ")}. Not all DORA-required disclosures detected on this page — entity-specific requirements vary.`;
    } else {
      pass = false; warn = true;
      label = "No DORA / resilience disclosures detected";
      detail = "No mentions of DORA, incident reporting, business continuity, or ICT risk management found in the page HTML. Most financial entities under DORA must publish certain operational resilience information.";
      fix = "Review DORA requirements (EU 2022/2554) — if your entity falls in scope, publish incident reporting, business continuity, and ICT risk management information on your site.";
    }
    checks.resilience = { pass, label, detail };
    if (warn) checks.resilience.warn = true;
    if (fix) checks.resilience.fix = fix;
  } else if (!fetchError) {
    checks.resilience = { pass: false, warn: true, label: "No HTML to check for DORA signals", detail: "Response was not HTML — DORA/resilience check skipped.", fix: "Verify manually whether your site addresses digital operational resilience if DORA-scoped." };
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

