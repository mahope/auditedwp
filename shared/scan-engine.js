/**
 * EUComply Universal Scan Engine — shared core module
 *
 * Platform-independent compliance scanner: takes any URL, returns a JSON
 * compliance report. Works regardless of CMS/platform.
 *
 * Checks (header/HTML based, no CMS assumptions):
 *   0.  consent_mode_v2 — Google Consent Mode v2 signatures
 *   0a. tcf            — IAB Transparency & Consent Framework
 *   0b. trackers       — third-party trackers loaded without consent signals
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

const TRACKER_SIGNATURES = [
  { re: /google-analytics\.com|googletagmanager\.com\/gtm\.js|gtag\(/i, name: "Google Analytics / GTM" },
  { re: /connect\.facebook\.net|fbq\(['"]/i, name: "Meta (Facebook) Pixel" },
  { re: /static\.hotjar\.com|hj\(['"]/i, name: "Hotjar" },
  { re: /clarity\.ms/i, name: "Microsoft Clarity" },
  { re: /snap\.licdn\.com|_linkedin_partner_id/i, name: "LinkedIn Insight Tag" },
  { re: /sc-static\.net|snaptr\(['"]/i, name: "Snapchat Pixel" },
  { re: /static\.tiktok\.com|ttq\./i, name: "TikTok Pixel" },
  { re: /matomo|piwik\.js/i, name: "Matomo / Piwik" },
  { re: /plausible\.io\/js/i, name: "Plausible" },
  { re: /cdn\.pinterest\.com.*pin.*js|pintrk\(/i, name: "Pinterest Tag" },
  { re: /googleadservices\.com|google_conversion/i, name: "Google Ads remarketing" },
  { re: /doubleclick\.net|googlesyndication/i, name: "DoubleClick / AdSense" },
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
  // NOTE: matches only TECHNICAL WP artifacts (asset paths, body classes, JS globals) —
  // never bare mentions of "wordpress" in marketing copy/compare tables.
  { re: /\/wp-(?:content|includes|json|admin)\b|[\s"'](?:wp-content|wp-includes)\//i, name: "WordPress" },
  { re: /\bwordpress_[a-z]|class="[^"]*\bwp-/i, name: "WordPress" },
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

/** Max redirect hops we follow before giving up. */
export const MAX_REDIRECTS = 5;
/** Hard cap on how much of a response body we read (bytes). */
export const MAX_BODY_BYTES = 2_000_000;

/**
 * Classify a bare IPv4 literal. Returns true when the address is routable on
 * the public internet, false for loopback/private/link-local/reserved ranges.
 * Range list covers RFC 1918, CGNAT, loopback, "this network", link-local
 * (incl. cloud metadata at 169.254.169.254), benchmarking, multicast and
 * reserved space.
 */
export function isPublicIPv4(a, b, c, d) {
  if (a === 0) return false;                                   // 0.0.0.0/8   "this network"
  if (a === 10) return false;                                  // 10/8        private
  if (a === 127) return false;                                 // 127/8       loopback
  if (a === 100 && b >= 64 && b <= 127) return false;          // 100.64/10   CGNAT
  if (a === 169 && b === 254) return false;                    // 169.254/16  link-local + cloud metadata
  if (a === 172 && b >= 16 && b <= 31) return false;           // 172.16/12   private
  if (a === 192 && b === 0 && c === 0) return false;           // 192.0.0/24  IETF protocol assignments
  if (a === 192 && b === 0 && c === 2) return false;           // 192.0.2/24  TEST-NET-1
  if (a === 192 && b === 88 && c === 99) return false;          // 192.88.99/24 6to4 relay anycast
  if (a === 192 && b === 168) return false;                     // 192.168/16  private
  if (a === 198 && (b === 18 || b === 19)) return false;        // 198.18/15   benchmarking
  if (a === 198 && b === 51 && c === 100) return false;         // 198.51.100/24 TEST-NET-2
  if (a === 203 && b === 0 && c === 113) return false;          // 203.0.113/24 TEST-NET-3
  if (a >= 224) return false;                                  // 224/4       multicast + 240/4 reserved
  return true;
}

/**
 * Expand an IPv6 literal to its 8 hextets, resolving "::" and a trailing
 * IPv4 tail. Returns null when the input is not a valid IPv6 address.
 */
export function expandIPv6(input) {
  let h = String(input || "").toLowerCase();
  if (h.startsWith("[") && h.endsWith("]")) h = h.slice(1, -1);
  if (!h || h.indexOf(":") === -1) return null;

  // Split off a dotted-quad tail (e.g. "::ffff:127.0.0.1").
  let tail = [];
  const lastColon = h.lastIndexOf(":");
  const tailPart = h.slice(lastColon + 1);
  if (tailPart.includes(".")) {
    const octets = tailPart.split(".").map(Number);
    if (octets.length !== 4 || octets.some(n => !Number.isInteger(n) || n < 0 || n > 255)) return null;
    tail = [(octets[0] << 8) | octets[1], (octets[2] << 8) | octets[3]];
    // The tail occupies the final two 16-bit groups, so fold it into the text
    // and stop counting it separately.
    h = h.slice(0, lastColon + 1) + tail.map(v => v.toString(16)).join(":");
    tail = [];
  }

  const halves = h.split("::");
  if (halves.length > 2) return null;
  const head = halves[0] ? halves[0].split(":") : [];
  const rear = halves.length === 2 ? (halves[1] ? halves[1].split(":") : []) : [];
  const middle = 8 - (head.length + rear.length + tail.length);
  if (halves.length === 1) {
    if (head.length + tail.length !== 8) return null;
  } else if (middle < 0) {
    return null;
  }
  const groups = [...head, ...new Array(middle).fill("0"), ...rear, ...tail.map(v => v.toString(16))];
  if (groups.length !== 8) return null;
  const out = groups.map(g => (/^[0-9a-f]{1,4}$/.test(g) ? parseInt(g, 16) : NaN));
  return out.some(Number.isNaN) ? null : out;
}

/** Classify a bare IPv6 literal. Same contract as isPublicIPv4. */
export function isPublicIPv6(address) {
  const g = expandIPv6(address);
  if (!g) return false;
  const isZeroPrefix = g.slice(0, 5).every(v => v === 0);
  const last = g[7];

  // ::1 loopback and :: unspecified
  if (isZeroPrefix && g[5] === 0 && g[6] === 0) return false;
  // ::/96 "IPv4-compatible" (::a.b.c.d) is deprecated and reserved; it is
  // never a legitimate public destination and is a known loopback shorthand.
  if (isZeroPrefix && g[5] === 0) return false;
  // ::/128 handled above; 64:ff9b::/96 NAT64 and 64:ff9b:1::/48 map IPv4 — a
  // private v4 stays private through them, so validate the embedded address.
  if (g[0] === 0x0064 && g[1] === 0xff9b && g[2] === 0 && g[3] === 0 && g[4] === 0 && g[5] === 0) {
    return isPublicIPv4((last >> 8) & 0xff, last & 0xff, (g[6] >> 8) & 0xff, g[6] & 0xff);
  }
  // IPv4-mapped (::ffff:0:0/96) and IPv4-compatible (::a.b.c.d) — unwrap.
  if (isZeroPrefix && g[5] === 0xffff) {
    return isPublicIPv4((g[6] >> 8) & 0xff, g[6] & 0xff, (last >> 8) & 0xff, last & 0xff);
  }
  // 6to4 (2002::/16) embeds the v4 address in the next 32 bits.
  if (g[0] === 0x2002) {
    return isPublicIPv4((g[1] >> 8) & 0xff, g[1] & 0xff, (g[2] >> 8) & 0xff, g[2] & 0xff);
  }
  // Teredo (2001:0000::/32) — server/client IPv4 in the last 32 bits.
  if (g[0] === 0x2001 && g[1] === 0x0000) {
    return isPublicIPv4((g[6] >> 8) & 0xff, g[6] & 0xff, (last >> 8) & 0xff, last & 0xff);
  }
  if (g[0] === 0xfe80) return false;                 // fe80::/10  link-local
  if ((g[0] & 0xfe00) === 0xfc00) return false;       // fc00::/7   unique local
  if ((g[0] & 0xff00) === 0xff00) return false;   // ff00::/8   multicast
  if (g[0] === 0x2001 && g[1] === 0x0db8) return false; // 2001:db8::/32 documentation
  if (g[0] === 0x0100 && g[1] === 0x0000 && g[2] === 0x0000) return false; // 100::/64 discard
  return true;
}

/** Hostnames that always resolve inside a private/local network. */
const BLOCKED_HOST_SUFFIXES = [
  ".localhost", ".local", ".internal", ".home.arpa", ".lan", ".intranet", ".corp", ".private",
];
const BLOCKED_HOSTS = new Set([
  "localhost", "metadata", "metadata.google.internal", "instance-data",
  "metadata.goog", "169.254.169.254", "metadata.azure.com",
]);

export function isPublicHostname(hostname) {
  const raw = String(hostname || "").toLowerCase();
  const h = raw.replace(/\.$/, "");
  if (!h) return false;
  if (BLOCKED_HOSTS.has(h) || BLOCKED_HOST_SUFFIXES.some(sfx => h.endsWith(sfx))) return false;
  // IPv6 literal — may arrive with the URL parser's surrounding brackets.
  if (h.startsWith("[") || h.includes(":")) return isPublicIPv6(h);
  if (/^\d{1,3}(\.\d{1,3}){3}$/.test(h)) {
    const [a, b, c, d] = h.split(".").map(Number);
    if ([a, b, c, d].some(n => !Number.isInteger(n) || n < 0 || n > 255)) return false;
    return isPublicIPv4(a, b, c, d);
  }
  // Anything that is only digits and dots but is not a full quad ("127.1",
  // "1.2.3") is a shorthand an attacker can use to reach loopback. The URL
  // parser expands it, but callers may pass a bare hostname, so fail closed.
  if (/^[\d.]+$/.test(h)) return false;
  return true;
}

/**
 * Best-effort DNS check for hostnames that are not IP literals. A public host
 * can resolve to a private address (DNS rebinding, or a redirect to a name that
 * points at 127.0.0.1), so each hop is verified against Cloudflare's resolver
 * before the request is made. Results are cached per isolate.
 *
 * Fails OPEN when the resolver itself is unavailable: the request is still sent,
 * because otherwise an outage of the resolver would take the whole scanner down.
 * Fail-closed on an explicit private answer.
 */
const DNS_CACHE = new Map();
const DNS_CACHE_MAX = 200;
const DNS_TTL_MS = 60_000;

async function dnsResolvesPrivate(hostname) {
  const now = Date.now();
  const hit = DNS_CACHE.get(hostname);
  if (hit && now - hit.at < DNS_TTL_MS) return hit.private;

  let priv = false;
  try {
    const types = ["A", "AAAA"];
    const results = await Promise.all(types.map(async (type) => {
      const r = await fetch(
        `https://cloudflare-dns.com/dns-query?name=${encodeURIComponent(hostname)}&type=${type}`,
        { headers: { Accept: "application/dns-json" }, signal: AbortSignal.timeout(3000) },
      );
      if (!r.ok) return null;
      return await r.json();
    }));
    for (const answer of results) {
      if (!answer || answer.Status !== 0 || !Array.isArray(answer.Answer)) continue;
      for (const a of answer.Answer) {
        const data = String(a.data || "");
        if (a.type === 1 && /^\d{1,3}(\.\d{1,3}){3}$/.test(data)) {
          const [x, y, z, w] = data.split(".").map(Number);
          if (!isPublicIPv4(x, y, z, w)) { priv = true; break; }
        } else if (a.type === 28 && data.includes(":")) {
          if (!isPublicIPv6(data)) { priv = true; break; }
        }
      }
      if (priv) break;
    }
  } catch { /* resolver unavailable — fail open, see doc comment */ }

  if (DNS_CACHE.size >= DNS_CACHE_MAX) DNS_CACHE.clear();
  DNS_CACHE.set(hostname, { private: priv, at: now });
  return priv;
}

/** True when the host is a bare IP literal (so no DNS lookup is useful). */
function isIpLiteral(hostname) {
  const h = String(hostname || "").replace(/^\[|\]$/g, "");
  return /^\d{1,3}(\.\d{1,3}){3}$/.test(h) || h.includes(":");
}

/**
 * Reject any URL that points at a non-public destination. Used for the caller
 * supplied URL AND for every redirect hop, so a public host cannot bounce us
 * into a private network or the cloud metadata endpoint.
 */
export async function assertPublicTarget(rawUrl, base) {
  let u;
  try {
    u = base ? new URL(rawUrl, base) : new URL(rawUrl);
  } catch {
    throw new Error("Invalid URL");
  }
  if (!/^https?:$/.test(u.protocol)) throw new Error("Only http and https URLs can be scanned.");
  if (!isPublicHostname(u.hostname)) {
    throw new Error("That address is not a public website, so it cannot be scanned.");
  }
  if (!isIpLiteral(u.hostname) && await dnsResolvesPrivate(u.hostname)) {
    throw new Error("That domain resolves to a private address, so it cannot be scanned.");
  }
  return u;
}

export function normalizeUrl(raw) {
  if (!raw || typeof raw !== "string") return null;
  let u = raw.trim();
  if (u.length > 2048) return null;
  if (!/^https?:\/\//i.test(u)) u = "https://" + u;
  try {
    const p = new URL(u);
    if (!/^https?:$/.test(p.protocol) || !p.hostname.includes(".")) return null;
    if (!isPublicHostname(p.hostname)) return null;
    return p.origin + (p.pathname === "/" ? "" : p.pathname.replace(/\/+$/, ""));
  } catch { return null; }
}

/**
 * Fetch a URL following redirects MANUALLY, validating every hop, so no
 * redirect can steer the request at a private or link-local address.
 * Never lets the runtime follow a redirect on its own.
 */
export async function safeFetch(rawUrl, { headers = {}, timeout = 12_000, maxRedirects = MAX_REDIRECTS } = {}) {
  let current = await assertPublicTarget(rawUrl);
  const chain = [];
  for (let hop = 0; hop <= maxRedirects; hop++) {
    const resp = await fetch(current.toString(), {
      headers,
      redirect: "manual",
      signal: AbortSignal.timeout(timeout),
    });
    const status = resp.status;
    const isRedirect = status >= 300 && status < 400 && resp.headers.get("location");
    if (!isRedirect) return { resp, url: current.toString(), chain };

    if (hop === maxRedirects) {
      throw new Error(`The site redirected more than ${maxRedirects} times.`);
    }
    const next = await assertPublicTarget(resp.headers.get("location"), current.toString());
    chain.push({ from: current.toString(), to: next.toString(), status });
    current = next;
  }
  throw new Error("Too many redirects.");
}

/** Read a response body, refusing to buffer more than MAX_BODY_BYTES. */
export async function readCappedText(resp, cap = MAX_BODY_BYTES) {
  if (!resp.body) return "";
  const reader = resp.body.getReader();
  const chunks = [];
  let total = 0;
  while (total < cap) {
    const { done, value } = await reader.read();
    if (done) break;
    const room = cap - total;
    chunks.push(value.length > room ? value.subarray(0, room) : value);
    total += Math.min(value.length, room);
  }
  if (total >= cap) await reader.cancel().catch(() => {});
  const buf = new Uint8Array(total);
  let off = 0;
  for (const c of chunks) { buf.set(c, off); off += c.length; }
  return new TextDecoder("utf-8", { fatal: false }).decode(buf);
}

export async function runScan(url) {
  url = normalizeUrl(url);
  if (!url) throw new Error("Invalid URL");
  const started = Date.now();

  // Fetch the page content. Redirects are followed manually and every hop is
  // validated, so a public host cannot redirect us into a private network.
  let resp, finalUrl;
  try {
    const out = await safeFetch(url, { headers: { "User-Agent": UA, Accept: "text/html,application/xhtml+xml,*/*" } });
    resp = out.resp;
    finalUrl = out.url;
  } catch (e) {
    const msg = String((e && e.message) || e);
    if (/not a public website|private address|redirected more than|Only http/.test(msg)) throw new Error(msg);
    throw new Error(`Could not reach ${url} — check that the domain exists and is online.`);
  }
  if (!resp.ok && resp.status >= 400) {
    throw new Error(`The site responded with HTTP ${resp.status} — a compliance scan needs a reachable page.`);
  }
  const html = await readCappedText(resp);

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

  // 0b. Trackers without consent (GDPR/ePrivacy — the classic enforcement target)
  const trackerMatches = [];
  for (const sig of TRACKER_SIGNATURES) {
    if (sig.re.test(html)) trackerMatches.push(sig.name);
  }
  const hasConsentPlatform = CONSENT_SIGNATURES.some(s => s.re.test(html));
  checks.trackers = {
    pass: trackerMatches.length === 0 || hasConsentPlatform,
    warn: trackerMatches.length > 0 && hasConsentPlatform && !/consent[_-]?mode|__tcfapi/i.test(html),
    label: trackerMatches.length === 0
      ? "No third-party trackers detected"
      : hasConsentPlatform
        ? `${trackerMatches.length} tracker(s) detected, consent platform present`
        : `${trackerMatches.length} tracker(s) with NO consent platform`,
    detail: trackerMatches.length > 0
      ? `Trackers found in page markup: ${trackerMatches.join(", ")}. ${hasConsentPlatform ? "A consent platform was also detected." : "No consent management platform was found — these trackers likely fire before consent."}`
      : "No third-party marketing/analytics trackers found in the served HTML.",
  };
  if (trackerMatches.length > 0 && !hasConsentPlatform) {
    checks.trackers.fix =
      "EU ePrivacy rules and GDPR Art. 6 require consent BEFORE loading non-essential trackers. Install a CMP that blocks Google Analytics/Meta Pixel etc. until the visitor consents.";
  }

  // The header value is echoed back to the browser. It is only ever rendered
  // as text, but a hostile origin can control it, so strip anything that is not
  // a header directive before it reaches a result page.
  const hsts = (resp.headers.get("Strict-Transport-Security") || "")
    .split(";")
    .map(part => part.trim().replace(/[^A-Za-z0-9=\-.:/ _]/g, ""))
    .filter(Boolean)
    .join("; ");
  const finalIsHttps = finalUrl.startsWith("https:");
  checks.ssl = {
    pass: finalIsHttps && hsts.length > 0,
    warn: finalIsHttps && hsts.length === 0,
    label: hsts ? "HTTPS + HSTS OK" : finalIsHttps ? "HTTPS, no HSTS" : "Not HTTPS",
    detail: hsts
      ? `HSTS: ${hsts.replace(/;\s*/g, "; ")}`
      : finalIsHttps
        ? 'SSL active but Strict-Transport-Security header missing.'
        : "Site is not served over HTTPS.",
  };
  if (!hsts && finalIsHttps) {
    checks.ssl.fix =
      'Add header: Strict-Transport-Security: "max-age=31536000; includeSubDomains; preload" to all responses.';
  } else if (!finalIsHttps) {
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

  // 6. DORA-related page references (static HTML signals; no DNS lookup)
  const doraMatches = [];
  for (const sig of DORA_SIGNATURES) {
    if (sig.re.test(html)) doraMatches.push(sig.name);
  }
  checks.dora = {
    pass: doraMatches.length >= 2,
    warn: doraMatches.length === 1,
    label: doraMatches.length > 0
      ? `DORA-related page signals: ${doraMatches.length} found`
      : "No DORA-related page signals detected",
    detail: doraMatches.length > 0
      ? `Page-text markers found: ${doraMatches.join(", ")}. This is not a DORA assessment.`
      : "No page-text references to failover, incident response or continuity were found. This scan does not query DNS or assess DORA compliance.",
  };
  if (doraMatches.length < 2) {
    checks.dora.fix =
      "Review whether the site publishes useful failover, incident-response and business-continuity information. Verify DNS and regulatory controls separately.";
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