/**
 * EUComply Universal Scan Engine — standalone Node.js core
 *
 * Platform-independent website compliance scanner:
 * takes any public URL, returns a structured JSON compliance report.
 * Works on any CMS/platform — WordPress, Shopify, Webflow, static
 * sites, Next.js, etc. No platform assumptions.
 *
 * Checks (header/HTML based, no CMS assumptions):
 *   consent_mode_v2  Google Consent Mode v2 signatures
 *   tcf              IAB Transparency & Consent Framework
 *   trackers         third-party trackers loaded without consent signals
 *   ssl              HTTPS + HSTS header
 *   cookies          cookie banner / consent platform detection in HTML
 *   forms            form markup + privacy-policy link presence
 *   legal            policy / imprint / accessibility statement links
 *   headers          security headers (CSP, X-Content-Type-Options, etc.)
 *   dora             DORA resilience check
 *   tech             platform fingerprint (informational)
 *
 * Usage:
 *   import { runScan, normalizeUrl } from '@mahope/eucomply-scanner'
 *   const report = await runScan('https://example.com')
 *
 * CLI:
 *   npx @mahope/eucomply-scanner https://example.com
 *
 * License: MIT
 */

// CLI entry point — run directly with `node engine/index.js https://example.com`
// or via the `eucomply-scanner` CLI wrapper
import { pathToFileURL } from 'node:url';

// Must stay identical to UA in ../../shared/scan-engine.js. runScan() reads it
// inside its try-block, so a missing const surfaces as "Could not reach <url>"
// and every scan fails with a message about a domain that is perfectly online.
const UA = "Mozilla/5.0 (compatible; EUComplyScan/1.0; +https://auditedwp.pages.dev)";

async function main() {
  const args = process.argv.slice(2);
  const url = args.find(a => !a.startsWith('--'));
  const jsonOutput = args.includes('--json');

  if (!url || args.includes('--help') || args.includes('-h')) {
    console.log(`
EUComply Scanner — Universal website compliance checker

USAGE:
  node engine/index.js [options] <url>

OPTIONS:
  --json           Output raw JSON (default: human-readable table)
  --timeout <ms>   Request timeout (default: 12000)
  --help, -h       Show this help

EXAMPLES:
  node engine/index.js https://example.com
  node engine/index.js --json https://example.com
  npx @mahope/eucomply-scanner https://example.com
`);
    process.exit(url ? 0 : 1);
  }

  try {
    const report = await runScan(url, { timeout: parseInt(args.find((_, i) => args[i-1] === '--timeout') || '12000', 10) });

    if (jsonOutput) {
      console.log(JSON.stringify(report, null, 2));
    } else {
      console.log(`\n🔍 EUComply Scan Report for ${report.url}`);
      console.log(`   Platform: ${report.platform}  |  Duration: ${report.durationMs}ms`);
      // Begge tal, fordi de ikke må læses i ét: `pct` er alle ni rækker,
      // `pct_applicable` er kun dem der gælder for sitet.
      const _nc = report.score.conditional || [];
      console.log(`   Score: ${report.score.passed_applicable}/${report.score.applicable_total} of the checks that apply to this site (${report.score.pct_applicable}%)\n`);
      if (_nc.length) {
        for (const k of _nc) {
          console.log(`   - not counted: ${k} — ${(report.checks[k] || {}).condition || CONDITIONAL_CHECKS[k] || ''}\n`);
        }
      }
      console.log(`   All ${report.score.total} checks: ${report.score.passed}/${report.score.total} (${report.score.pct}%)\n`);

      for (const [key, check] of Object.entries(report.checks)) {
        const icon = check.pass ? '✅' : check.warn ? '⚠️' : '❌';
        console.log(` ${icon} ${check.label}`);
        if (check.detail) console.log(`    ${check.detail}`);
        if (check.fix) console.log(`    💡 ${check.fix}`);
        console.log();
      }
      console.log(report.disclaimer);
    }
    process.exit(0);
  } catch (e) {
    console.error('❌ Error:', e.message);
    process.exit(1);
  }
}

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

// Hver række skal navngive **én** leverandør, fordi rækkens navn ryger lige i
// den rapport kunden læser: `checks.cookies.label` er
// `Consent platform: ${consentMatches[0]}`, og pluginens rapport skriver
// `Detected: …`. Så længe de fire delte én række, fik en jysk.dk-kunde at se
// *"Consent platform: Cookiebot / OneTrust / Usercentrics / ConsentManager"* —
// målt 2026-09-27 i deres 634 234 byte markup: `onetrust` stod der, de tre
// andre nul gange. Rapporten navngiver altså syv platforme den kørte én af.
//
// Unionen af alternativerne er uændret, bortset fra den nøgne `cookieconsent`:
// målt på jysk.dk er den **OneTrusts egen konfiguration**
// (`"cookieConsent":{…}`, `enableOneTrustCookieConsent`) og ikke Orestbidas
// bibliotek, så den kan ikke tilskrives én leverandør. Den dokumenterede sti
// bærer derimod versionsmærket: `cookieconsent@3.1.1`.
const CONSENT_SIGNATURES = [
  { re: /cookiebot/i, name: "Cookiebot" },
  { re: /consentmanager/i, name: "ConsentManager" },
  { re: /onetrust|cookielaw\.org|otSDKStub|optanon/i, name: "OneTrust" },
  { re: /usercentrics/i, name: "Usercentrics" },
  { re: /cookieyes|cookie-yes/i, name: "CookieYes" },
  { re: /tarteaucitron/i, name: "TarteAuCitron" },
  { re: /klaro/i, name: "Klaro" },
  { re: /osano/i, name: "Osano" },
  { re: /cookieconsent@|cookieconsent\.min\.js/i, name: "CookieConsent" },
  { re: /complianz|cmplz/i, name: "Complianz GDPR" },
  { re: /gdpr[_-]?cookie[_-]?banner|gdpr[_-]?banner|eu[_-]?cookie|cookie[_-]?solution/i, name: "Generic cookie consent banner" },
  { re: /axeptio|axept\.io/i, name: "Axeptio" },
  { re: /cookiehub|cookie[_-]?hub/i, name: "CookieHub" },
  { re: /iubenda/i, name: "iubenda" },
  { re: /optinmonster/i, name: "OptinMonster (popup detected)" },
  { re: /wp-consent-api/i, name: "WP Consent API" },
  { re: /borlabs/i, name: "Borlabs" },
  { re: /real[_-]?cookie[_-]?banner/i, name: "Real Cookie Banner" },
  { re: /cookie[_-]?notice[_-]?lite/i, name: "Cookie Notice Lite" },
  { re: /cookie[_-]?notice\/js\/front|cookie[_-]?notice\/css\/front/i, name: "Cookie Compliance for WordPress" },
  { re: /gdpr[_-]?cookie[_-]?compliance/i, name: "GDPR Cookie Compliance" },
  { re: /pixel[_-]?your[_-]?site/i, name: "PixelYourSite (GDPR)" },
  // Rækkens navn er *Analytify/CAOS*, men mønstret var `analytics[_-]?cat`, som
  // ingen af de to produkter kan matche: Analytifs plugin-slug er `analytify` og
  // CAOS (Cookie Assistant for Osano) hedder *caos*. Mønstret var altså dødt i
  // alle tre produkter, og ingen port kunne se det, fordi porten testede
  // mønstret mod rækkens **navn** — opgave 63 fund 2. R5 tester nu mønstret mod
  // en installationstest i stedet (`tools/check_signature_prose.mjs`, DAEKNING).
  { re: /analytify|caos/i, name: "Analytify/CAOS" },
];

// `ns.html` er Googles egen no-JavaScript-fallback for GTM — det snippet
// Googles dokumentation beder **alle** GTM-sites installere, og det er den
// eneste GTA-reference på en side der kun har fallbacken. Mønsteret matchede
// kun container-scriptet (`gtm.js`), så "Third-party trackers: 0 found" stod på
// en side der sender et pixel. Ikke en regression fra opgave 57: mønsteret har
// aldrig matchet den. Målt før rettelsen: 0 fund i alle tre produkter.
//
// `gtag/js` er den anden del af samme hullet og den dyreste af alle: GA4
// indlæses som `<script async src="…/gtag/js?id=G-…">`, og når konfigurationen
// ligger i en **aparte fil** står der intet `gtag(` i markup'en — kun den
// indlejrede konfiguration rammer det gamle `gtag(`. Det er den mest almindelige
// analytics-opsætning i dag, og den gav `Third-party trackers: 0 found` med
// detaljen *"No third-party marketing/analytics trackers found"*: en kunde med
// GA4 fik en grøn række og ingen grund til at sætte samtykke ind. Målt før
// rettelsen: 0 fund i alle tre produkter. Mønsteret må ikke bindes til
// `?id=G-` — Googles Ads-tags bruger samme URL med `AW-`, så alternativet er
// kun filstien. Spec: `docs/eucomply-signatur-prosa.md`.
const TRACKER_SIGNATURES = [
  { re: /google-analytics\.com|googletagmanager\.com\/(?:gtm\.js|ns\.html|gtag\/js)|gtag\(/i, name: "Google Analytics / GTM" },
  { re: /connect\.facebook\.net|fbq\(['"]/i, name: "Meta (Facebook) Pixel" },
  // `hj(` er væk, og det er målt, ikke antaget (2026-09-27) — se
  // `shared/scan-engine.js`: det er leverandørens egen globale funktion i den
  // fil dens script-URL peger på, og scanneren læser aldrig ind i et indlæst
  // script. Værtens fil på den adresse rækken blev testet med svarer 200 med
  // nul byte på ethvert id, så beviset "vaert 200" var en måling der ikke kan fejle.
  { re: /static\.hotjar\.com/i, name: "Hotjar" },
  { re: /clarity\.ms/i, name: "Microsoft Clarity" },
  { re: /snap\.licdn\.com|_linkedin_partner_id/i, name: "LinkedIn Insight Tag" },
  { re: /sc-static\.net|snaptr\(['"]/i, name: "Snapchat Pixel" },
  // Se `shared/scan-engine.js` for kilderne på de to nye stier: Googles egen
  // Google tag (`googletagservices.com/tag/js/gpt.js`, 200 fra Googles vært
  // 2026-09-27) og TikToks nuværende pixel-sti (`analytics.tiktok.com/`,
  // hjælpe-siden ads.tiktok.com/help/article/get-started-pixel). Begge gav
  // `Third-party trackers: 0 found` i alle tre produkter før rettelsen.
  // `static.tiktok.com` er væk: `dig +short` svarer intet (2026-09-27).
  { re: /analytics\.tiktok\.com\/|ttq\./i, name: "TikTok Pixel" },
  { re: /matomo|piwik\.js/i, name: "Matomo / Piwik" },
  { re: /plausible\.io\/js/i, name: "Plausible" },
  // Pinterests egen dokumentation ("Install the base code",
  // help.pinterest.com, hentet 2026-09-27) indlæser tagget fra
  // `s.pinimg.com/ct/core.js` og lægger et `<noscript>`-pixel på
  // `ct.pinterest.com/v3/`. Ingen af de to findes i det gamle mønster, så den
  // **dokumenterede** installation var kun synlig gennem det indlejrede
  // `pintrk(`-kald. Kun **stien**, ikke værten: Pinterests billed-CDN ligger også
  // på `pinimg.com`. `cdn.pinterest.com.*pin.*js` er væk: `dig +short` svarer
  // intet (2026-09-27). Spec: `docs/eucomply-signatur-prosa.md`.
  { re: /s\.pinimg\.com\/ct\/|ct\.pinterest\.com\/v3\/|pintrk\(/i, name: "Pinterest Tag" },
  { re: /googleadservices\.com|googletagservices\.com\/tag\/js\/gpt\.js|google_conversion/i, name: "Google Ads remarketing" },
  { re: /doubleclick\.net|googlesyndication/i, name: "DoubleClick / AdSense" },
];

// Separatoren er `[ _-]?` — bindestreg, understreg **eller mellemrum**.
// Den var `[_-]?`, hvilket aldrig matcher et mellemrum, og det gjorde hver
// flerords-markør ufandet i sin egen lange form: "business continuity plan",
// "incident response" og "status page" er skrevet med mellemrum på en
// engelsk sikkerhedsside og blev læst som nul. Målt før rettelsen: 0 af de 3
// flerords-markører, i begge motorer og i pluginen. Samme fejlklasse som
// opgave 52 (`terms`) og opgave 55 (`sla`). Spec: `docs/eucomply-signatur-prosa.md`.
const DORA_SIGNATURES = [
  { re: /spf[ _-]?record|v[ _-]?=spf/i, name: "SPF (Email sender auth)" },
  { re: /dkim|[_-]?domainkey/i, name: "DKIM (Email signing)" },
  { re: /dmarc_|dmarc[ _-]?record|_dmarc\./i, name: "DMARC (Email policy)" },
  { re: /mx[ _-]?record|mx [0-9]|mail[ _-]?exchange/i, name: "MX (Mail exchange)" },
  { re: /multiple[ _-]?server|failover|redundan|multi[ _-]?az/i, name: "Multi-server / failover / redundancy signals" },
  { re: /cdn[ _-]?failover|multi[ _-]?cdn|backup[ _-]?origin/i, name: "CDN failover / multi-CDN" },
  { re: /incident[ _-]?response|soc[ _-]?report|security[ _-]?incident/i, name: "Incident response / SOC reporting" },
  { re: /bcdr|dr[ _-]?plan|business[ _-]?continuity/i, name: "BC/DR planning reference" },
  { re: /status[ _-]?page|uptime[ _-]?monitor/i, name: "Status page / uptime monitoring" },
];

const FORM_PLUGIN_SIGNATURES = [
  // NOTE: all patterns are anchored tightly (boundaries/exact slugs) so they
  // cannot false-positive on arbitrary substrings in non-WordPress HTML.
  // Én leverandør pr. række, fordi rækkens navn ryger i rapporten:
  // `Form plugins detected: <navn>`. Målt 2026-09-27 — samme fejl som de to
  // consent-rækker i samme rapport, otte leverandøre i én.
  { re: /contact[_-]form[_-]7|\bwpcf7\b|\bcf7[-_]/i, name: "Contact Form 7" },
  { re: /\bwpforms\b|\bwpforms?-/i, name: "WPForms" },
  { re: /\bformidable\b/i, name: "Formidable" },
  { re: /gravity[_-]?forms/i, name: "Gravity" },
  { re: /fluent[_-]?forms?\b/i, name: "Fluent" },
  { re: /ninja[_-]?forms\b/i, name: "Ninja" },
  { re: /caldera[_-]?forms\b/i, name: "Caldera" },
  { re: /\belementor\b[^<>]{0,40}form/i, name: "Elementor" },
  { re: /\btypeform\b/i, name: "Typeform" },
  { re: /\bformspree\b/i, name: "Formspree" },
  { re: /woocommerce[_-]?checkout|wc_[_-]?checkout/i, name: "WooCommerce Checkout" },
  // Shopify and Stripe were both **dead rows** until 2026-09-27 (task 65
  // part 2). Neither pattern could match anything the vendor actually ships:
  // `shopify[_-]?checkout` requires the two words next to each other, and a
  // real Shopify cart page and checkout page say `shopify-accelerated-checkout`
  // (4 stores, 6 pages, measured); `stripe[_-]?checkout` needs "stripe" first,
  // but every real Stripe marker puts "checkout" first (`checkout.stripe.com`)
  // or carries neither word (`js.stripe.com/v3`, `<div id="payment-element">`).
  // The added alternatives are the measured forms; the old ones stay, because
  // they cost nothing and a bespoke theme may well use them.
  // Opgave 72 del 3. `checkout[_-]?shopify` er **fjernet**, målt 2026-09-27 på
  // tre rigtige Shopify-kurvsider: allbirds.com (423 051 B), gymshark.com
  // (51 683 B) og kith.com (1 523 685 B). Alle tre er Shopify-butikker —
  // `cdn.shopify.com` 15/10/9 gange — og alle tre har den målte markør
  // `shopify-accelerated-checkout` 4 gange, så strengen holder. Den omvendte
  // ordstilling: **0 forekomster på 3 af 3 sider**. Den var en gæt, så den er
  // væk — samme metode som Quantcast i 1.3.25 og CookieNinja i 1.3.29.
  // `shopify[_-]?checkout` i PLATFORM_SIGNATURES nedenfor er en anden række og
  // urørt.
  { re: /shopify[_-]?(accelerated[_-]?)?checkout/i, name: "Shopify Checkout" },
  // Opgave 72 del 3. `[_-]?stripe[_-]?form` er **fjernet**: leverandørens egen
  // `https://js.stripe.com/v3/` (200, 1 121 765 B) rummer **0** forekomster af
  // `stripe_form`, `stripe-form` og `stripeForm` — målt 2026-09-27 i samme fil
  // der bærer den streng denne række har (`js.stripe.com` 27 gange).
  //
  // Opgave 72 del 6. `data-stripe-(key|publishable)` er **også fjernet**, og
  // den var den dyreste af de tre: attributterne findes i **nogen** målt kilde.
  // Målt 2026-09-27, alle fem svar 200: `checkout.stripe.com/checkout.js`
  // (90 238 B), `js.stripe.com/v3/` (1 121 765 B — de to attributter 0 gange,
  // og de eneste to `data-stripe-` i filen er `data-stripe-backdrop-id`, som
  // Stripe selv sætter), `docs.stripe.com/payments/accept-a-payment`
  // (1 711 358 B), `docs.stripe.com/js/custom_checkout/init` (2 149 961 B) og
  // `docs.stripe.com/payments/checkout` (489 398 B). `checkout.js` læser slet
  // ingen data-attributter (0 `dataset`, 2 `getAttribute`) — nøglen kommer fra
  // købmandens egen markup, ikke fra leverandørens fil.
  //
  //Fjernelsen taber **intet målbart**: attributten betyder kun noget for
  // Stripe.js, og Stripe.js hentes fra `js.stripe.com/v3` — det er allerede et
  // alternativ i denne række og den eneste streng den har. Den opførte
  // installationstest `<div id="payment-element" data-stripe-key="pk_live_…">`
  // var skrevet fra hukommelsen, så det var den **kun**, der holdt porten grøn.
  { re: /stripe[_-]?checkout|stripe[_-]?payment|js\.stripe\.com\/v[0-9]/i, name: "Stripe" },
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

// Sprogsneutralt, ikke engelsk. En tysk, fransk eller engelsk side ramte
// privatlivsmønsteret før dette; en dansk, svensk eller nederlandsk side gjorde
// det ikke, og fik derfor "no privacy-policy link" på en side der linker sin
// privatlivspolitik lige ved formularen. Hver stængel er et helt ord fra sit
// sprog, aldrig et fragment der også er et ord i et andet. Spec:
// `docs/eucomply-privatlivsprog.md`. Samme sæt i `shared/scan-engine.js`
// og i `plugin/eucomply.php` — et tjek med samme navn skal betyde det samme.
//
// **Mønsteret matcher et ord, og det er ikke nok.** Det må først tælle når
// ordet står i et **link** — se `linkAnchors` og `linkedLegalNames` nedenfor.
// Opgave 56 målte 22 falske fund på fire rene prosa-sider, fordi mønstrene
// læste hele HTML'en. Spec: `docs/eucomply-juridiske-links.md`.
const PRIVACY_LINK_SIGNATURE =
  /privacy|privacy[_-]?policy|datenschutz|gdpr|privacypolicy|data[_-]?protection|privatliv|persondata|databeskyttelse|integritetsskydd|dataskydd|personuppgifter|persoonsgegevens|gegevensbescherming|confidentialit|privacidad|datos personales/i;

/**
 * Hver `<a>`-element på siden, som browseren ville læse det: åbnings-tagget med
 * `href` **og** den synlige tekst indeni.
 *
 * Et juridisk dokument skal være et **link**. Før dette læste mønstrene hele
 * HTML'en, så en side der *beskriver* at den behandler persondata fik en
 * privatlivsside den ikke har — og en side med otte af slags ord i en
 * almindelig indledning fik `legal` **bestået** med nul links i foden. Det er
 * en falsk beståelse i en betalt rapport, som er værre end en falsk advarsel,
 * fordi den er usynlig for kunden.
 *
 * Negativt lookahead frem for `\s\S]*?`: scanningen fra hvert `<a` stopper ved
 * den næste `</a>`, så en `<a` tæller højst ét elements indhold. Det er
 * lineært i praksis — mange `<a` betyder mange korte scans — og der er ingen
 * indlejrede lændekøringer, en `<a`-fri side kan lokke os ind i.
 *
 * @param {string} html
 * @returns {string[]}
 */
function linkAnchors(html) {
  return (html || "").match(/<a\b[^>]*>(?:(?!<\/a>)[\s\S])*/gi) || [];
}

/**
 * Navnene på de juridiske dokumenter siden faktisk **linker**, i mønsternes
 * rækkefølge. Samme navne som før — de er den tekst kunden læser i rapporten.
 *
 * @param {string} html
 * @returns {string[]}
 */
function linkedLegalNames(html) {
  const anchors = linkAnchors(html);
  const names = [];
  for (const sig of LEGAL_PATTERNS) {
    if (anchors.some((a) => sig.re.test(a))) names.push(sig.name);
  }
  return names;
}

/**
 * Linker siden et dokument med `sig`s mønster? Samme regel som
 * `linkedLegalNames`, for ét mønster.
 *
 * @param {string} html
 * @param {{ re: RegExp, name: string }} sig
 * @returns {boolean}
 */
function linksLegal(html, sig) {
  return linkAnchors(html).some((a) => sig.re.test(a));
}

/**
 * Det `<script>`, `<style>`, `<noscript>` og `<template>`-indhold, der findes i
 * HTML'en, ordret. Én regex, brugt både til at finde blokkene og til at fjerne
 * dem — to lister der ligner hinanden er præcis den fejlklasse denne opgave
 * lukker.
 */
const CODE_BLOCK = /(?:script|style|noscript|template)\b[^>]*>[\s\S]*?(?:<\/(?:script|style|noscript|template)\s*>|$)/gi;

/**
 * Den **synlige tekst** i et HTML-fragment.
 *
 * Tekstnoderne er alt mellem `>` og `<`. Både en `<p>` med en hel sætning og
 * en `<a>`-linktekst forsvinder, og det er hele pointen.
 *
 * @param {string} fragment
 * @returns {string}
 */
function visibleText(fragment) {
  return fragment.replace(/>[^<]*</g, "><");
}

/**
 * Den del af HTML'en hvor **et værktøj faktisk kører** — altså alt andet end
 * synlig tekst. Opgave 57s måling: `TRACKER_SIGNATURES`, `CONSENT_SIGNATURES`
 * og `FORM_PLUGIN_SIGNATURES` læste hele HTML'en, så en side der *skriver*
 * "vi bruger Matomo" fik **en rød række** i alle tre produkter, og en side der
 * skriver "Typeform" fik *"Typeform / Formspree / Jotform detected"* — på den
 * betalte `forms`-række. Målt i 12 fund pr. sprog i fire sprog, i begge motorer
 * og i pluginen. 48 fund i alt, ingen af dem ærlige.
 *
 * Bevis er to ting: **kode** — inline `<script>`, `src`/`href` på et eksternt
 * arkiv, og `<noscript>`-pixel-fallbacken — og **attributter** på elementerne,
 * fordi Contact Form 7 lever som `<div class="wpcf7">` i markupen, ikke som et
 * script. Kun de to ville fundet `FORM_PLUGIN_SIGNATURES` uden at miste en eneste
 * ægte detektion; det er R2 i porten trin 24, der beviser det.
 *
 * Ordene i signaturerne er **uændrede**, så opgave 51-55s sprogdækning og
 * opgave 56s juridiske links er bevaret. Det er beholderen der ændrer sig,
 * præcis som i opgave 56.
 *
 * @param {string} html
 * @returns {string}
 */
export function codeAndAttributes(html) {
  if (!html) return "";
  // `<script src="…">` uden en afsluttende `</script>` er almindeligt på
  // afkortede sider. Regex'en tager da resten af dokumentet med, så
  // kodebevis ikke forsvinder bare fordi et tag ikke blev lukket.
  const kode = html.match(CODE_BLOCK);
  if (!kode) return visibleText(html);
  return visibleText(html.replace(CODE_BLOCK, "\u0000")) + "\n" + kode.join("\n");
}

const LEGAL_PATTERNS = [
  { re: PRIVACY_LINK_SIGNATURE, name: "Privacy / GDPR" },
    // Opgave 54 målte de otte øvrige mønstre gennem `legal` i begge motorer: **0 af 24**
  // (mønster, sprog) blev fundet i nogen af dem. Følgen er en score, en kunde
  // kan se: en dansk butik med *Om os*, *Retur- og forbrugerrettigheder* og
  // *Fragt og levering* får **null** juridiske sider, fordi listen kun kendte
  // engelsk og tysk.
  //
  // Samme to regler som privatliv, cookie og vilkår:
  //
  // 1. **En stængel er et helt ord fra sit sprog**, aldrig et fragment der
  //    også er et ord i et andet. Derfor er imprint på dansk
  //    `virksomhedsoplysninger` og ikke bare `om os`, der er almindelig prosa
  //    ("læs mere om os").
  // 2. **Separatoren er nødvendig, og den er ikke altid samme.** `om[-_]?os`
  //    matcher stien `/om-os/` men **aldrig** "om os" med mellemrum i en sætning.
  //    Det er samme måleme som opgave 52 fandt med `[_-]?` vs `[ _-]?`.
  //
  // To stængler er bevidst **uden** det hele ord, fordi porten har en fixture der
  // måler den fejltagelse: DA `returbetingelser` (prosa om retur i en sætning er
  // almindelig, sidenavnet er *Retur- og forbrugerrettigheder*) og SV
  // `returvillkor`, som ligger i *returvillkoren* på en ganske normal svensk
  // butiksside. Begge ville være falske fund på den betalte rapport.
  //
  // Port: `tools/check_legal_langs.mjs`. Spec: `docs/eucomply-juridiske-sprog.md`.
{ re: /impressum|imprint|legal[_-]?notice|legal[_-]?disclosure|about[_-]?the[_-]?company|om[-_]?os|virksomhedsoplysninger|om[-_]?oss|bolagsuppgifter|colofon|bedrijfsgegevens|kvk[ _-]?nummer/i, name: "Imprint / Legal notice" },
  { re: /accessibility[_-]?statement|a11y|accessibility[_-]?declaration|eaa[_-]?statement|barrierefreiheit|tilg[æa]ngelighedserkl[æa]ring|tilg[æa]ngelighedspolitik|tillg[äa]nglighetsredog[öo]relse|toegankelijkheidsverklaring|toegankelijkheidsbeleid/i, name: "Accessibility statement" },
  // Samme sprogregel som privatlivsmønsteret: en stængel er et helt ord fra sit
  // sprog, aldrig et fragment der også er et ord i et andet. `cookiepolitik` (DA),
  // `cookiesbeleid` (NL) og `kakpolicy` (SV) er de navne en butiks footer
  // faktisk bruger.
  //
  // `terms` havde en fejl, der var større end sprog: separatoren var `[_-]?`, som
  // matcher bindestreg OG understreg, men **aldrig et mellemrum**. Den fandt
  // altså `terms-of-service` og `terms_of_service` og ingen af de former en side
  // faktisk skriver: "Terms of Service", "Terms & Conditions", "Terms of Use".
  // Målt før denne ændring, ikke antaget. Separatoren er derfor `[ _-]?`.
  // Vilkårssiderne er de lange, entydige sidenavne — `vilka` alene er et
  // almindeligt dansk og svensk ord ("vilka produkter vi har"), og `villkor`/
  // `voorwaarden` alene rammer "Köpvillkoren" og "Onze voorwaarden", så porten
  // har fixtures på præcis den fejltagelse. Port: `tools/check_legal_langs.mjs`.
  // Spec: `docs/eucomply-juridiske-sprog.md`.
  { re: /cookie[_-]?policy|cookie[_-]?declaration|cookie[_-]?settings|cookie[_-]?preferences|cookiepolitik|cookies?beleid|kakpolicy/i, name: "Cookie policy" },
  { re: /terms[ _-]?(?:of[ _-]?use|of[ _-]?services?|and[ _-]?conditions|&\s*(?:amp;)?\s*conditions|conditions)|handelsbetingelser|vilk[aå]?r[ _-]?(?:og[ _-]?)?(?:betingelser|for[ _-]?(?:brug|anvendelse|køb))|allm[aä]nna[ _-]?villkor|anv[äa]ndningsvillkor|algemene[ _-]?(?:leverings)?voorwaarden/i, name: "Terms & Conditions" },
  { re: /legal[_-]?notice|legal[_-]?info|impressum|disclaimer|legal[_-]?mention|juridisk[ _-]?information|juridische[ _-]?informatie/i, name: "Legal / Imprint" },
  { re: /returns[_-]?policy|refund[_-]?policy|cancellation[_-]?policy|widerrufsrecht|retur[ _-]?(?:og[ _-]?)?(?:forbrugerrettigheder|fortrydelsesret|politik)|fortrydelsesret|retur[ _-]?och[ _-]?[åa]ngerr[aä]tt|retourbeleid|retour[ _-]?voorwaarden|retourtermijn/i, name: "Returns / Refund policy" },
  { re: /shipping[_-]?policy|delivery[_-]?information|versand|fragt[ _-]?(?:og|&amp;?)?[ _-]?(?:levering|leverans|vilk[aå]r)|leveringsvilk[aå]r|forsendelsesvilk[aå]r|frakt[ _-]?(?:och|&amp;?)?[ _-]?leverans|leverans(?:villkor|information)|verzend[ _-]?(?:beleid|voorwaarden)|bezorg(?:informatie|beleid)/i, name: "Shipping policy" },
  { re: /data[_-]?processing[_-]?agreement|dpa|data[_-]?processor|auftragsverarbeitung|databehandleraftale|personuppgiftsbitr[aä]desavtal|bitr[aä]desavtal[ _-]?f[öo]r[ _-]?personuppgifter|verwerkersovereenkomst|verwerkersav[aä]nk|verwerkersbeding/i, name: "Data processing agreement" },
  { re: /acceptable[_-]?use[_-]?policy|aup|fair[_-]?use[_-]?policy|acceptabel[ _-]?brug|rimlig[ _-]?anv[aä]ndning|redelijk[ _-]?gebruik/i, name: "Acceptable use / Fair use" },
  { re: /subprocessor|sub[_-]-?processor|subprocessors|underbehandler(?:e)?[ _-]?(?:liste|list|oversigt)|liste[ _-]?over[ _-]?underbehandler|bitr[äa]desf[öo]rteckning|underbitr[äa]deslista|subverwerkers(?:lijst)?/i, name: "Sub-processor list" },
  { re: /code[_-]?of[_-]?conduct|coc|ethik|adf[æa]rdskodeks|uppf[öo]randekodex|gedragcode/i, name: "Code of conduct" },
  { re: /sla[_-]?service[_-]?level|service[ _-]?level[ _-]?(?:agreement|overeenkomst)|garantie(?:bedingungen|erkl[äa]rung)|gew[äa]hrleistung|serviceniveau|serviceavtal|serviceniv[åa][ _-]?avtal/i, name: "SLA / Warranty" },
  { re: /complaints[_-]?policy|complaint[_-]?procedure|beschwerde|klageprocedure|klage[ _-]?h[æa]ndtering|klagf[öo]rfarande|klachtprocedure|klachtenbeleid|klachtenafhandeling/i, name: "Complaints procedure" },
  { re: /modern[_-]?slavery|slavery[_-]?act[_-]?statement|human[_-]?trafficking|moderne[ _-]?slaveri|modernt[ _-]?slaveri|moderne[ _-]?slavernij/i, name: "Modern slavery statement" },
  { re: /whistleblower|whistle[_-]?blowing|hinweisgeber|visselbl[åa]sare|klokkenluider(?:sregeling)?/i, name: "Whistleblower / Hinweisgeber" },
  { re: /environmental[_-]?policy|sustainability[_-]?policy|umwelt|b[æa]redygtighedspolitik|milj[øo]politik|h[åa]llbarhetspolicy|duurzaamheids?(?:beleid|verklaring)/i, name: "Environmental / Sustainability policy" },
  { re: /gdpr[_-]?contact|dpo[_-]?contact|data[_-]?protection[_-]?officer|datenschutzbeauftragte|databeskyttelsesr[åa]dgiver|dataskyddsansvarig|functionaris(?:[ _-]?voor)?[ _-]?gegevensbescherming/i, name: "DPO / Data protection officer" },
  { re: /info@|contact@|hello@|mail@|support@|sales@/i, name: "General contact address" },
];

export function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...CORS, "Content-Type": "application/json" },
  });
}

/** Max redirect hops we follow before giving up. */
// ---------------------------------------------------------------------------
// Betingede rækker. Et tjek der kun kan fejle, hvis sitet gør noget bestemt, kan
// ikke være en mangel på et site der ikke gør det. Før dette var de fire
// rækker talt med i tallet uden forudsætning, så et site uden annoncering,
// cookies og finansielle forpligtelser scorede 56 % (5 af 9) — og båndet blev
// grønt ved 80, altså et tal ingen kunne nå. Samme fejlklasse som EAA-omfanget
// og opgave 45: dokumenteret betingelse, ubetinget dom i talform.
//
// Nøglerne og grunden er **motorens**, fordi motoren er det eneste sted der
// ved hvilke fund der gør en række relevant. En side må ikke finde på sin egen
// liste — det er præcis det, der får ni overflader til at fortælle ni
// historier. `tools/check_score_split.py` læser listen her og kræver at de
// publicerede sider nævner præcis de samme nøgler.
export const CONDITIONAL_CHECKS = {
  cookies: "Not counted here \u2014 this check only applies to a site that sets cookies or loads non-essential trackers.",
  tcf: "Not counted here \u2014 IAB TCF only applies to a site that runs programmatic advertising in the EEA.",
  consent_mode_v2: "Not counted here \u2014 Consent Mode v2 is only required of a site that runs Google Ads in the EEA.",
  dora: "Not counted here \u2014 DORA applies to financial entities, and a public page scan cannot tell whether the operator is one. This scan is not a DORA assessment.",
};
export const CONDITIONAL_CHECK_KEYS = Object.keys(CONDITIONAL_CHECKS);

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
  // Hex and integer forms ("0x7f.0.0.1", "2130706433") are expanded by the URL
  // parser, so they reach loopback through it. Reject the bare form too, so a
  // caller that hands this function a hostname gets the same answer as one
  // that went through new URL().
  if (/^0[xX][\da-fA-F.]+$/.test(h) || /^\d{9,}$/.test(h)) return false;
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
  // Signaturerne læser `teknisk`, altså kode og attributter — se `codeAndAttributes`.
  // Opgave 57 målte 12 falske fund pr. sprog, fordi hele HTML'en blev læst.
  const teknisk = codeAndAttributes(html);
  const trackerMatches = [];
  for (const sig of TRACKER_SIGNATURES) {
    if (sig.re.test(teknisk)) trackerMatches.push(sig.name);
  }
  // Navnet følger med. Pluginen skrev "…was also detected (Klaro / …)" mens
  // motoren skrev "…was also detected." — samme dom, to forskellige rapporter om
  // det *samme* website, og den betalte var den mere informative. Rækkefølgen er
  // tabellens, som i pluginen, så de to produkter vælger samme navn.
  const consentMatches = CONSENT_SIGNATURES.filter(s => s.re.test(teknisk)).map(s => s.name);
  const hasConsentPlatform = consentMatches.length > 0;
  checks.trackers = {
    pass: trackerMatches.length === 0 || hasConsentPlatform,
    warn: trackerMatches.length > 0 && hasConsentPlatform && !/consent[_-]?mode|__tcfapi/i.test(html),
    label: trackerMatches.length === 0
      ? `Third-party trackers: ${trackerMatches.length} found`
      : hasConsentPlatform
        ? `${trackerMatches.length} tracker(s) detected, consent platform present`
        : `${trackerMatches.length} tracker(s) with NO consent platform`,
    detail: trackerMatches.length > 0
      ? `Trackers found in page markup: ${trackerMatches.join(", ")}. ${hasConsentPlatform ? `A consent platform was also detected (${consentMatches[0]}).` : "No consent management platform was found — these trackers likely fire before consent."}`
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
    // `finalIsHttps` tested FØRST, ikke `hsts` — samme fejl som i
    // `shared/scan-engine.js`: en side der svarer over http men sender
    // HSTS fik en rød række med etiketten "HTTPS + HSTS OK".
    label: !finalIsHttps ? "Not HTTPS" : hsts ? "HTTPS + HSTS OK" : "HTTPS, no HSTS",
    detail: !finalIsHttps
      ? "Site is not served over HTTPS."
      : hsts
        ? `HSTS: ${hsts.replace(/;\s*/g, "; ")}`
        : "SSL active but Strict-Transport-Security header missing.",
  };
  if (!hsts && finalIsHttps) {
    checks.ssl.fix =
      'Add header: Strict-Transport-Security: "max-age=31536000; includeSubDomains; preload" to all responses.';
  } else if (!finalIsHttps) {
    checks.ssl.fix = "Redirect all traffic to https://";
  }

  // 2. Cookie consent detection
  // Samme liste som `trackers` regel 0b brugte. Den lå to gange i denne fil —
  // to steder der læser det samme og skriver det samme, hvilket er præcis
  // hvad der gør at de to rækker kan komme til at svare forskelligt.
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
    if (sig.re.test(teknisk)) formMatches.push(sig.name);
  }
  const hasFormAction = /<form[^>]*action\s*=\s*["'](?:[^"']+:)?\/\/[^"']*["']/i.test(html);
  const hasLocalForm = /<form[^>]*>[\s\S]*?<\/form>/i.test(html);
  const hasPrivLink = linksLegal(html, LEGAL_PATTERNS[0]);
  checks.forms = {
    pass: !(hasLocalForm && !hasPrivLink),
    warn: hasLocalForm && !hasPrivLink,
    // The pass path and the warn path are different sentences, not one shared
    // one. A site with plain form markup AND a privacy link passes this check,
    // and it used to be handed the *failing* sentence for both label and
    // detail — a green row whose entire text said the opposite. A customer
    // reading the report could not tell the two verdicts apart.
    label: formMatches.length > 0
      ? `${formMatches[0]} detected`
      : hasLocalForm && !hasPrivLink
        ? "Form(s) found, no privacy-policy link"
        : hasLocalForm
          ? `Form(s) found, privacy-policy link detected`
          : "Page has neither form markup nor a form plugin",
    detail: formMatches.length > 0
      ? `Form plugins detected: ${formMatches.join(", ")}. Ensure privacy link is visible near each form.`
      : hasLocalForm && !hasPrivLink
        ? "Form markup found, but no privacy-policy link detected in page HTML. EU law requires a privacy notice at the point of data collection."
        : hasLocalForm
          ? "Form markup found and a privacy-policy link was detected in the page HTML."
          : "No HTML forms detected on this page. If forms exist, ensure they link to a privacy policy.",
  };
  if (hasLocalForm && !hasPrivLink) {
    checks.forms.fix =
      'Add a link to your privacy policy next to each form submit button, and give the link text the name of your privacy policy page.';
  }

  // 4. Legal pages (privacy, imprint, terms, accessibility, cookie policy).
  //    Kun links tæller — en sætning i løbende tekst er ikke en juridisk side.
  const uniqueLegal = linkedLegalNames(html);
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

  // Betingelserne beregnes på de samme fund, rækkerne selv er bygget af, så de
  // kan ikke komme i utakt med det tjekket siger. `set-cookie` er et svar fra
  // den side vi netop hentede — det er det eneste direkte bevis på cookies.
  const setCookieHeader = (resp.headers.get("set-cookie") || "").length > 0;
  const adSignals = /googleadservices|googletagservices|doubleclick|googlesyndication|adnxs|adsrv|criteo|taboola|outbrain|prebid|adsbygoogle|\/gpt\.js/i.test(teknisk);
  checks.cookies.applies = consentMatches.length > 0 || trackerMatches.length > 0 || setCookieHeader;
  checks.tcf.applies = adSignals;
  checks.consent_mode_v2.applies = adSignals || /google_ads|gtag\(|AW-[0-9]|gtag\/js\//i.test(teknisk);
  // DORA gælder finansielle enheder. En offentlig side kan ikke se om
  // driftsselskabet er en bank — og rækkens egen `detail` siger allerede
  // "This is not a DORA assessment". At tælle den ville gøre 100 % uopnåeligt
  // for alle, også for et site der har gjort alt andet rigtigt.
  checks.dora.applies = false;
  for (const key of CONDITIONAL_CHECK_KEYS) {
    checks[key].condition = CONDITIONAL_CHECKS[key];
  }

  return {
    url: finalUrl,
    scannedAt: new Date().toISOString(),
    durationMs: Date.now() - started,
    platform,
    checks,
    // To tal, fordi de ikke må læses i ét: `pct` er alle ni rækker (det tal
    // kunder har set), `pct_applicable` er kun dem der gælder for sitet. Begge
    // findes, så en gammel klient der kender det første tal fortsætter med at
    // virke, og en ny får betingelsen ved siden af sit tal.
    score: (() => {
      const scored = Object.values(checks).filter(c => typeof c.pass === "boolean");
      const passed = scored.filter(c => c.pass).length;
      const applicable = scored.filter(c => c.applies !== false);
      const passedApplicable = applicable.filter(c => c.pass).length;
      return {
        passed,
        total: scored.length,
        pct: scored.length ? Math.round(100 * passed / scored.length) : 0,
        applicable_total: applicable.length,
        passed_applicable: passedApplicable,
        pct_applicable: applicable.length ? Math.round(100 * passedApplicable / applicable.length) : 0,
        conditional: CONDITIONAL_CHECK_KEYS.filter(k => checks[k] && checks[k].applies === false),
        conditional_applied: CONDITIONAL_CHECK_KEYS.filter(k => checks[k] && checks[k] && checks[k].applies !== false),
      };
    })(),
    disclaimer: "Automated technical checks only — not legal advice. Full compliance review requires a qualified professional.",
  };
}
// Automatically detect CLI invocation — only when THIS file is the direct entry point.
// (Name-based matching breaks when npm's .bin shim is named "eucomply-scanner": the engine
// then runs main() during import, before `const UA` is initialized -> TDZ crash. Verified 25/8.)
try {
  const entry = process.argv[1] ? pathToFileURL(process.argv[1]).href : null;
  if (entry && import.meta.url === entry) main();
} catch { /* non-file context — never auto-run */ }
