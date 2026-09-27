=== EUComply — EU Compliance Audit ===
Contributors: mahope
Donate link: https://donate.stripe.com/7sYeVcbn50wieFM8gDbMQ0c
Tags: compliance, gdpr, nis2, eaa, dora, audit, security, privacy, cookies, ssl, backup, imprint, legal, accessibility
Requires at least: 5.8
Tested up to: 6.8
Requires PHP: 7.4
Stable tag: 1.3.36
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

Know your WordPress site's EU compliance status in 30 seconds — from your admin dashboard. Eleven checks: SSL/HSTS, cookies, forms, backups, plugin/core health, legal pages, Google Consent Mode v2, IAB TCF, trackers without consent, security headers and DORA page signals. Free. Pro ($79/year per website) unlocks editable HTML document starters and an HTML report from the latest WordPress scan.

== Description ==

EUComply scans your WordPress installation against **eleven EU compliance criteria** in a single click. The core checks run server-side on your WordPress; the plugin also checks the update manifest and Pro license status as described below.

= What it checks =

1. **🔒 SSL & HTTPS** — Is the site served over HTTPS, and is the HSTS response header present?
2. **🍪 Cookie Consent** — Is a known consent plugin or the WP Consent API active?
3. **📋 GDPR Forms** — Is a known form plugin active, and is a Privacy Policy page configured?
4. **💾 Backup Status** — Is a known backup plugin active? If UpdraftPlus exposes its last-backup time, how old is it?
5. **⚠️ Plugin & Core Health** — Are WordPress core or installed plugins reported as outdated?
6. **📄 Legal Pages** — Is a Privacy Policy assigned, and are common Imprint, Terms and EAA statement pages found?

= How it works =

1. Upload the plugin ZIP and activate the `eucomply` folder.
2. Activate it. The admin menu now shows "EUComply".
3. Click "Run scan now" — results appear in seconds.
4. Review pass/fail status with fix guidance for each check.
5. Let the automatic cron job do it. New results appear on their own — once a week on the free version, once a day on Pro.

= Free vs Pro =

| Feature | Free | Pro ($79/year per website) |
|---|---|---|
| Compliance scan dashboard (6 checks) | ✓ | ✓ |
| Pass/fail with fix guidance | ✓ | ✓ |
| Automated re-scan, run by WP-Cron on your own server | once a week | every day |
| GDPR Data Processing Agreement (Art. 28) | — | ✓ |
| NIS2/DORA vendor clause set (5 clauses) | — | ✓ |
| EAA Accessibility Statement | — | ✓ |
| HTML report from the latest WordPress scan, with 52 recorded scan snapshots | — | ✓ |
| Agency name branding in reports | — | ✓ |
| Read-only client report link, valid 30 days and revocable | — | ✓ |
| License revalidation at most once every 24 hours when the Pro admin view is used, with a 7-day offline grace after a temporary license-server failure | — | ✓ |

= Why another compliance plugin? =

Cookie banners and backup plugins solve one problem each. EUComply is a local WordPress compliance checker that scans eleven dimensions and generates editable HTML document starters plus an HTML report from the latest scan — DPA agreements, NIS2 clauses, and accessibility statements.

Scan data and generated reports stay on your site. The plugin checks your own WordPress installation locally, checks the EUComply update manifest at eucomplypro.com/update.json, and when Pro is used sends the license key, site hostname and product identifier to the Mahope license server at mahope.tools.

= Who is this for? =

- **Agency owners** who need a WordPress site checked and document starters generated on the site they manage.
- **Freelancers** who need configuration hints for forms and legal pages on client projects.
- **EU-based businesses** that must comply with NIS2, DORA, the European Accessibility Act, and GDPR — often simultaneously.
- **WordPress site owners** who want a quick technical check without hiring a consultant.

== Installation ==

1. Upload the `eucomply` folder to `/wp-content/plugins/` via FTP, or use **Plugins → Add New → Upload Plugin** and select the ZIP.
2. Activate the plugin through the 'Plugins' screen in WordPress.
3. Go to EUComply in your admin menu and click "Run scan now".

That's it. No configuration required for the free scan. Pro users enter their license key in EUComply → Settings.

== Frequently Asked Questions ==

= Does the plugin send data to external servers? =

No telemetry or analytics is sent by the plugin. The core compliance checks run inside WordPress and inspect the installation. The plugin also checks the EUComply update manifest at `https://eucomplypro.com/update.json`; when Pro is used, it sends the license key, the site's hostname and the product name (no site content) to the Mahope license server at `mahope.tools`.

= How do I buy Pro? =

Buy EUComply Pro at https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03 — $79 per website per year, paid securely through Stripe. The license key arrives on the confirmation page and by email. Paste it into EUComply → Settings.

= How is this different from Complianz, CookieYes or WP Activity Log? =

Those plugins solve one compliance problem (cookies or audit logs). EUComply combines **eleven compliance dimensions** in one local plugin, plus **editable HTML document generation** — DPA agreements, NIS2/DORA vendor clause sets, and EAA accessibility statements. It also generates an HTML report from the latest WordPress scan.

= Can I white-label reports for my clients? =

Pro users can set their agency or business name in Settings, and the generated HTML report uses that name. A separate white-label product is not currently available.

= Is the generated DPA legally binding? =

The DPA follows a common GDPR Article 28 structure. We recommend having a lawyer review the completed agreement for high-value contracts. The plugin provides a starting point, not legal advice or a substitute for legal review.

= What happens if I cancel my Pro subscription? =

The plugin continues in Free mode if the license is no longer valid. The current purchase does not create a hosted account, and renewal or cancellation terms are shown by the payment provider and applicable product terms.

= My site is in Germany. Does this help with the Telemediengesetz (TMG)? =

The "Legal Pages" check looks for an Imprint/Impressum page and the Pro EAA starter provides a structured accessibility-statement template. Neither determines whether your site meets German or EU legal requirements.

= Does this work on multisite? =

The checks run on a per-site basis within a network. Pro licenses are per-site. A network-wide license option is planned for a future release.

= Can this replace a proper security audit? =

No. EUComply checks compliance posture, not security vulnerabilities. Use dedicated security plugins (Wordfence, Sucuri) for penetration testing and firewall protection. EUComply augments — it doesn't replace — security tooling.

== Screenshots ==

1. EUComply admin dashboard showing eleven compliance checks with pass/fail status.
2. Settings page with Pro license key input and agency name.
3. Pro document generation table — DPA, NIS2, EAA, and HTML report from the latest scan.

== Changelog ==

= 1.3.35 (2026-09-27) =
* Fix: three tracker markers in the test suite could not be traced to anything the report names, and two of them pointed at hosts that no longer exist. They are gone in this plugin, in the free scanner and in the published CLI engine.
* Hotjar's hj( call is no longer part of the pattern. It is Hotjar's own global function, and it is defined in the file its script URL points at - the scanner reads a page's markup and never opens a loaded script, so that call cannot be found on a site that actually has Hotjar. The test data for the row was also written from memory: static.hotjar.com/c/hotjar-<id>.js answers 200 with an empty body for any id, so 'the host answered 200' proved nothing. The row keeps static.hotjar.com, Hotjar's own host, which answers 200 with a real file. Measured before the fix on 2026-09-27.
* static.tiktok.com has no DNS at all - dig returns nothing - so it can never match a live site. The current pixel still counts: analytics.tiktok.com and the inlined ttq. call are both still recognised, and both were read in a real site's own inline loader on 2026-09-27.
* cdn.pinterest.com has no DNS either, so the old cdn.pinterest.com.*pin.*js form is gone. Pinterest's own two documented paths - s.pinimg.com/ct/core.js and the ct.pinterest.com/v3/ noscript pixel - are unchanged and still found.
* The LinkedIn Insight Tag row now also has a test for the line the shop itself writes. snap.licdn.com/li.lms-analytics/insight.min.js is the loader; the installation is the inline var _linkedin_partner_id = "..." line, which was in the pattern but in no test string, so a site carrying only the inline line had nothing to trace it to. The TikTok row got the same treatment for its inline loader.
* The TikTok test data named analytics.tiktok.com/i18n/pixel/<id>.js, which answers 404 on a made-up id - its own evidence said so. The path a real site actually uses is analytics.tiktok.com/i18n/pixel/events.js.
* If you scanned your site between 1.3.34 and now, run a new scan. No tracker lost its finding: three new tests cover the inline LinkedIn and TikTok lines and the Hotjar host, so the removals are provably not narrowing. One row can now report fewer findings: a page that mentioned Hotjar's hj( call in a code sample, without having Hotjar installed, was previously counted as a Hotjar site.

= 1.3.36 (2026-09-27) =
* Fix: the report named four consent platforms when the site runs one. The row was called 'Cookiebot / OneTrust / Usercentrics / ConsentManager' and a second one 'TarteAuCitron / Klaro / Osano / CookieConsent', and the row's name is printed in the report - the heading reads 'Consent platform: <name>' and the detail reads 'Detected: <names>'. A site running OneTrust was therefore told it ran Cookiebot, Usercentrics and ConsentManager as well.
* Measured before the fix, on a real site on 2026-09-27: of the eight platforms the two rows named, exactly one was in the page. The other seven were not - the report still listed every one of them.
* Each platform now has its own row and its own name, so the report names the one the site actually runs: OneTrust is still recognised by its own loader on cdn.cookielaw.org, its optanon fields, and its stub. This plugin, the free scanner and the published CLI engine give the same answer on the same page.
* One marker is no longer matched, and it could not honestly be attributed to a single product: the bare word 'cookieconsent'. On the measured site it was OneTrust's own configuration ("cookieConsent": {...}, enableOneTrustCookieConsent), not the CookieConsent library. That library is now recognised by its own documented file name, cookieconsent@3.1.1/cookieconsent.min.js, so a site installing it the documented way is still found. A site whose only consent marker was the bare word now needs a new scan to be named correctly.

* The same fix, in the form row. It was called 'Contact Form 7 / WPForms / Formidable / Gravity / Fluent / Ninja / Caldera / Elementor' and the report prints the row's name after 'Form plugins detected:', so a site running one form plugin was told it ran all eight. Each of the eight now has its own row, its own name and its own measured installation - the eight test strings are the ones already documented for them, nothing was narrowed. Typeform and Formspree were split the same way.

= 1.3.34 (2026-09-27) =
* Fix: the DORA row for multi-server and failover signals could not recognise two markers it had been written for, and reported a third under a name the report did not contain.
* 'multi-AZ' is now recognised. The pattern asked for the three-part form 'multi-AZ-DNS', which does not occur: AWS' own Amazon RDS documentation writes 'Multi-AZ' 62 times in running text and 'multi-AZ-DNS' 0 times. The pattern now matches 'Multi-AZ', which also still matches 'multi-AZ DNS'. A site describing its database as a Multi-AZ deployment is counted from now on.
* The row is now named 'Multi-server / failover / redundancy signals'. It has always matched the word 'redundant', and Microsoft's own Availability Zones page writes it 8 times in running text - 'Azure datacenters are designed with redundant infrastructure like power, cooling, and network connectivity' - but the row's name did not say so, so the report named a finding the customer could not look for in the page.
* 'BCP-plan' is no longer part of the BC/DR row. The pattern asked for 'bcp plan' exactly, a form that does not occur: the Wikipedia article on business continuity planning writes 'BCP' 23 times and 'business continuity' 227 times, and 'bcp plan' not once. 'BCDR', 'DR-plan' and 'business-continuity' are unchanged and still found, so the row loses nothing that was ever detected.
* The public marker table in the DORA guide now lists the same markers the code matches, in this plugin, in the free scanner and in the published CLI engine.
* If you scanned your site between 1.3.33 and now, run a new scan: a site describing a Multi-AZ deployment now registers a signal it did not, and the multi-server row is reported under a name that includes what was found.

= 1.3.33 (2026-09-27) =
* Fix: a form plugin was found but never named. The pattern has always matched Caldera Forms, but the row it belongs to was named 'Contact Form 7 / WPForms / Formidable / Gravity / Fluent / Ninja / Elementor' - Caldera is not in that name. A site running Caldera was therefore reported as running Contact Form 7 or one of the other six, a finding the customer cannot check against the page, and the row is the one that decides whether a site is asked for consent. The same mistake was found and fixed for Ninja Forms in 1.3.31, one row further down the same list.
* Caldera is closed in the public WordPress catalogue - the catalogue reports the plugin as closed since 5 April 2022, permanently, at the author's request - so it cannot be read there. It is documented from the vendor's own repository instead. caldera-core.php sets CFCORE_URL to the plugin's own folder, and classes/render/assets.php builds the front-end script URL from it, so the installation is /wp-content/plugins/caldera-forms/assets/build/js/caldera-forms-front.min.js - the plugin's own folder, read in the vendor's code rather than assumed. Caldera has its own name and its own test now, and every pattern that matched something still matches it. This plugin, the free scanner and the published CLI engine give the same answer on the same page.
* Two plugin versions that shipped without a download redirect now have one. 1.3.29 and 1.3.31 were removed from the download folder with no redirect line, so an installation still on either asked for its own package and got a 404. Both now redirect to the current version.
* If you scanned your site between 1.3.32 and now, run a new scan: a site running Caldera Forms is now named correctly.

= 1.3.32 (2026-09-27) =
* Fix: a cookie-consent row could report a platform this report never names. The generic row matched cookie-notice, which is not a generic banner: it is the WordPress slug of two different consent plugins. One of them, Cookie Notice Lite, has its own row; the other - Cookie Compliance for WordPress, version 3.1.12 - had no row at all, so a site running it was reported as running a generic banner instead of the platform it actually runs.
* The generic row now names only generic banners, and the second plugin has its own row, read from the plugin's own code: it enqueues /js/front.min.js and /css/front.min.css. A site running Cookie Compliance for WordPress is now reported under its own name in this plugin, in the free scanner and in the published CLI engine.
* The iubenda row no longer matches cookie-solution. iubenda's own code (3.13.5) writes //cdn.iubenda.com/cs/iubenda_cs.js, never the words cookie-solution, so the pattern made the report name iubenda on sites that do not run it. The marker is kept, in the generic row, where an unnamed marker belongs.
* OneTrust's optanon marker is now documented instead of assumed: the platform's own loader, served from cdn.cookielaw.org, sets optanonCookieName="OptanonConsent", optanonHtmlGroupData and optanonHostData. Nothing was narrowed, and the generic markers gdpr-banner and eu-cookie stay exactly where they were.
* If you scanned your site between 1.3.31 and now, run a new scan: a site running Cookie Compliance for WordPress is now named correctly, and a site that was reported as iubenda without running it is no longer.

= 1.3.31 (2026-09-27) =
* Fix: one of the most common WordPress form plugins was invisible in the row's name. The pattern already matched `ninja-forms`, but the row was named 'Contact Form 7 / WPForms / Formidable / Gravity / Fluent / Elementor' - Ninja Forms is not in that name. A site running Ninja Forms was therefore reported as running Contact Form 7 or one of the other five, a finding the customer cannot check against the page, and the row is the one that decides whether a site is asked for consent.
* Nothing was narrowed. `ninja-forms` answers 200 in the WordPress catalogue, so the platform is now named and has its own test, and every pattern that matched something still matches it. This plugin, the free scanner and the published CLI engine give the same answer on the same page.
* A new rule in this plugin's test suite fails when a pattern in a row can find a platform the row's name does not mention. The same mistake, with Cognito Forms and Formsort in the form row, was removed in the previous release - this is the rule that would have caught it.

= 1.3.30 (2026-09-27) =
* Two consent platforms that the report named are now found where they are really installed, and three that nobody could read are no longer named at all. TarteAuCitron installs itself with a script called /tarteaucitron/tarteaucitron.js, which is what the vendor's own repository documents - the earlier note only looked in the WordPress catalogue and on npm, where it is not published. Osano's own Tag Manager template builds its own address, https://cmp.osano.com/<id>/<id>/osano.js; the old note measured cdn.osano.com, which is a marketing page and never carried the script.
* The rows that are gone: the popup row is now 'OptinMonster' and the form row 'Typeform / Formspree'. JustUno, Privy and Jotform answered 520, 403 and 404 on every documented address from here, and nothing could be read that says how they are installed - so a report no longer names a platform this check cannot find. The form row also stopped matching Cognito Forms and Formsort, which were in the pattern but not in the row's name.
* If you scanned your site between 1.3.29 and now, run a new scan: a site running TarteAuCitron or Osano is now reported correctly, and a site running one of the three removed platforms is no longer named for it.

= 1.3.29 (2026-09-27) =
* Fix: OneTrust was invisible in its own normal installation, so a site running OneTrust - the most widely deployed consent platform in Europe - was told 'No consent banner detected', which is the same verdict as a site with no consent platform at all. OneTrust installs itself with a single script tag, src="https://cdn.cookielaw.org/scripttemplates/otSDKStub.js" with a data-domain-script attribute, and that path contains no occurrence of the word 'onetrust', which was all the pattern looked for. Measured before the fix: 0 findings for that installation in this plugin, in the free scanner and in the published CLI engine, while Cookiebot, Usercentrics and ConsentManager - the other three platforms the same row names - were found in all three. The vendor's own stub answers 200 and is OneTrust's SDK: it defines OneTrustStub, reads window.OneTrust and uses OneTrust's own optanon fields. The pattern now matches what the markup actually contains, so it is read rather than assumed.
* Fix: the WordPress plugin 'GDPR Cookie Banner' (slug gdpr-cookie-banner) was not matched. The pattern read 'gdpr' and 'banner' with a hyphen, an underscore or nothing between them, and the word 'cookie' stands in the middle of the slug. The plugin exists - the public WordPress catalogue answers 200 for it - and its own source enqueues public/css/gdpr-cookie-banner-public.css and public/js/gdpr-cookie-banner-public.js on the front end, and the banner's own markup carries the class gdpr-cookie-banner. All three are now matched, so a site running it no longer reads as having no banner at all. The existing 'cookie-notice' form is still matched.
* The row named 'Borlabs / CookieNinja' is now named 'Borlabs', because 'CookieNinja' is not a product anyone can read documentation for: neither cookieninja nor cookie-ninja exists in the public WordPress catalogue. A report that names a platform cannot find is not coverage. Borlabs is unchanged and still found - it is documented from Borlabs' own Google Tag Manager template.
* Nothing else in the list narrowed. The test suite's test data now uses the OneTrust installation and the gdpr-cookie-banner enqueue, and two new cases fail if either marker stops matching, so neither can come back unnoticed.
* Plugin 1.3.29. If you scanned your site between 1.3.28 and now, treat the cookie-consent row as unknown rather than as a finding: run a new scan.

= 1.3.28 (2026-09-27) =
* Four consent rows are removed rather than kept on an assumption. CookieScript, the CEE/PL consent plugin, Moove GDPR and WebToffee GDPR each carried a test string naming a file that was written from memory, and none of the four exists in the public WordPress catalogue under the slug the test data used - all four slugs redirect to a search page, while contact-form-7, complianz-gdpr, cookiehub and wp-consent-api answer 200 in the same measurement. A row that cannot find the platform it names is not coverage: it is a green line in a report the customer reads as coverage. If you scanned your site between 1.3.27 and now, a site running one of those four platforms may report fewer consent findings than before. Nothing else in the row list narrowed.
* The Borlabs row is now documented from the vendor's own code instead of a guessed file name. Borlabs' own Google Tag Manager template calls callInWindow('BorlabsCookie.checkCookieConsent') and callInWindow('BorlabsCookie.Consents.hasConsent'), so the global BorlabsCookie - not any particular asset filename - is the installation Borlabs documents. The test data now uses that global, so a site running Borlabs Cookie is found whatever its enqueued file is called.
* The test suite's cap on assumed rows is lowered from twelve to zero, and now fails on the first one. Each consent row already has a test that fails if its own pattern stops matching the installation it is written for; this is the same rule for the opposite mistake - an installation that was never read.
* Plugin 1.3.28. If you scanned your site between 1.3.27 and now, treat the cookie-consent row as unknown rather than as a finding: run a new scan.

= 1.3.27 (2026-09-27) =
* Fix: one of the biggest consent platforms was invisible in its normal installation. Axeptio is installed by adding a single script tag, src="https://static.axept.io/sdk.js" - the platform's own SDK, read directly on 2026-09-27. That address contains no occurrence of the word "axeptio", and the pattern matched only that word, so a site installing Axeptio the documented way was told 'No consent banner detected' - the same verdict as a site with no consent platform at all.
* The inlined axeptio( init call still counts, so an installation that has it does not lose its finding. The match is on the platform's own file path, and the old address in the test data (axeptio.cdn.app) does not resolve - it was written from memory and had never been read.
* Twelve of the twenty consent rows in the test suite rested on that kind of assumed address. Each was checked against the vendor's own WordPress catalogue entry or the vendor's own code, and eight are now documented: CookieYes, Axeptio, CookieHub, iubenda, OptinMonster, PixelYourSite and Analytify were installed under a different folder than the test data claimed (Analytify is wp-analytify, PixelYourSite is pixelyoursite, OptinMonster loads assets/dist/js/), and their test data now names the real file. Five remain marked as assumptions and are listed as such, because none of them exists in the public WordPress catalogue under the name used here.
* A new rule in this plugin's test suite caps assumed rows at twelve, so a new platform cannot be added on an assumption the way these were. Each consent row already has a test that fails if its own pattern stops matching the installation it is written for.
* If you scanned your site between 1.3.26 and now, treat the cookie-consent row as unknown rather than as a finding: run a new scan. No other row changed.

= 1.3.26 (2026-09-27) =
* Fix: one row in the consent-platform list could never match anything. The row is named 'Analytify/CAOS', but the pattern read 'analytics-cat' - a word neither product is called. Analytify is installed as the plugin folder /wp-content/plugins/analytify/ and CAOS is called caos, so a site running either was told 'No consent banner detected', which is the same verdict as a site with no consent platform. Measured before the fix: 0 findings for that installation in this plugin, in the free scanner and in the published CLI engine.
* Nothing was narrowed. The other nineteen consent rows are unchanged, and each of them now has a test that fails if its own pattern stops matching the installation it is written for - the same test that caught this one, so it cannot come back unnoticed.
* Three rows are honest about what they do not cover yet, and are listed with the evidence behind them rather than presented as full coverage: OneTrust's own loader is served from cdn.cookielaw.org and does not contain the word 'onetrust'; 'CookieNinja' is not a product anyone has read documentation for; and the popular WordPress slug gdpr-cookie-banner is not matched by the 'GDPR banner' alternative. If you scanned your site between 1.3.25 and now, treat the cookie-consent row as unknown rather than as a finding: run a new scan.

= 1.3.25 (2026-09-27) =
* Fix: one consent platform in this list could never be found by anything. The pattern read the two words of the name with a hyphen, an underscore or nothing between them, and the platform is loaded from a path - quantcast.mgr.consensu.org/choice/.../quantcast.js - where a dot and a slash stand between the words. So the pattern matched nothing at all, here and in the free scanner and the published CLI engine. Measured before the fix: a page loading the platform from its own path was reported as 'No consent banner detected', which is the same verdict as a site with no consent banner - on a site that asks every visitor for consent.
* The entry is removed rather than rewritten. The vendor's own installation instructions could not be read from the machine this plugin is built on, and a pattern written against an address nobody has read is exactly how the first mistake got in. It comes back in a later version, with the documented path and a test that fails if it stops matching.
* If you scanned your site between 1.3.24 and now, treat the cookie-consent row as unknown rather than as a finding: run a new scan. No other row changed, and every pattern that did match something still matches it.

= 1.3.24 (2026-09-27) =
* Fix: two of the most common advertising tags were invisible, so a site running one of them was told 'Third-party trackers: 0 found' - a clean row, and no reason to ask a visitor for consent, on a page that was loading an advertising script on every page view. Measured before the fix: 0 findings for each of them in this plugin, in the free scanner and in the published CLI engine.
* Google's own Google tag loads from googletagservices.com/tag/js/gpt.js. That host is neither the old googleadservices.com nor AdSense's googlesyndication.com, so the pattern knew neither, and a site running only the current Google tag was reported as clean. The address answers on Google's own server, and the finding is reported as Google Ads remarketing, not as AdSense.
* TikTok's current pixel loads from analytics.tiktok.com/i18n/pixel/. The pattern knew only the older static.tiktok.com path and the inlined ttq. call, so a site installing the pixel as TikTok's own help page describes was reported as clean. A TikTok video embedded from www.tiktok.com is not a pixel and is still not counted - the match is on the host and the path, not on the name.
* The older forms still count: googleadservices.com/pagead/conversion.js, static.tiktok.com and the inlined ttq. call are all still recognised, so an older integration does not lose its finding. This plugin, the free scanner and the published CLI engine give the same answer on the same page.
* If you scanned your site between 1.3.23 and now, treat the tracker row as unknown rather than as clean: a scan before may have reported 0 trackers on a site that had one. Run a new scan.

= 1.3.23 (2026-09-27) =
* Fix: the most common way to install the Pinterest tag was invisible. Pinterest's own documentation (help.pinterest.com, "Install the base code") loads the tag from s.pinimg.com/ct/core.js and adds a <noscript> conversion pixel on ct.pinterest.com/v3/. The pattern knew neither path: it only matched the inlined pintrk( call and an old cdn.pinterest.com URL that the current documentation no longer uses. A site that installs the tag exactly as documented was therefore only seen while its inline scripts were still inline - move them into a bundle, or block them with a content security policy, and the row said "Third-party trackers: 0 found" on a site that was running the tag. Measured before the fix: 0 findings for both documented paths in this plugin, in the free scanner and in the published CLI engine.
* * The match is on the file path, not on the host. Pinterest serves images from i.pinimg.com, and a shop with three lookbook photos has no tag to remove; the image CDN is now measured as well, so a pattern broad enough to catch it would turn the build red.
* * The inline pintrk( call still counts, and the old cdn.pinterest.com form is still recognised, so an older integration does not lose its finding. This plugin, the free scanner and the published CLI engine give the same answer on the same page.
* * If you scanned your site between 1.3.22 and now, treat the tracker row as unknown rather than as clean: a scan before may have reported 0 trackers on a site that had one. Run a new scan.

= 1.3.22 (2026-09-27) =
* Fix: the most common way to install Google Analytics 4 was invisible. GA4 loads as a single external script from googletagmanager.com/gtag/js, and when the configuration lives in a separate file there is no inline gtag( call anywhere in the page. The pattern only matched the inlined call, so such a site was told "Third-party trackers: 0 found" - a clean row, and no reason to ask a visitor for consent, on a site that was sending a pixel on every page load. Measured before the fix: 0 findings for that installation in this plugin, in the free scanner and in the published CLI engine.
* This was the more expensive direction of the error. The 1.3.20 fix removed false findings, and a false finding at least shows up in the report; a tracker that is not reported cannot be found by anyone reading it.
* Google's Ads tags load from the same URL with an AW- id instead of a G- id. Both are now recognised, because the match is on the file path and not on the id - a match bound to G- would keep passing the most common installation and still miss the other one.
* Nothing else was narrowed. The other eight tracker patterns are untouched, and this plugin, the free scanner and the published CLI engine give the same answer on the same page, as they now do for every signature.
* If you scanned your site between 1.3.21 and now, treat the tracker row as unknown rather than as clean: a scan before may have reported 0 trackers on a site that had one. Run a new scan.

= 1.3.21 (2026-09-27) =
* Fix: a DORA page signal was only recognised with a hyphen or an underscore between the words, so the wording an English security page actually uses was read as nothing. "Business continuity plan", "incident response" and "status page" are written with spaces. Measured before the fix: 0 of those three markers in this plugin, in the free scanner and in the published CLI engine, on a page that lists all three. The row now recognises hyphen, underscore or a space, in all three products.
* The Google Tag Manager fallback was invisible. Google's own documentation asks every GTM site to add a <noscript> iframe pointing at googletagmanager.com/ns.html, and on a site that has only the fallback that iframe is the only analytics reference there is. The pattern matched the container script alone, so such a site was told "Third-party trackers: 0 found" - a clean row on a page that still sends a pixel. This was never a false positive from the 1.3.20 narrowing: the pattern had never matched it.
* The scanner and this plugin answered the same question in two different sentences. The plugin wrote "A consent platform was also detected (Klaro / ...)" and the scanner wrote "A consent platform was also detected." The scanner now names the platform, reading the same signature list in the same order, so the same website produces the same report from both products.
* The DORA row still reads the whole page, on purpose. Its markers are claims about the organisation rather than about code running, and a company that writes "we have a business continuity plan" on its security page has said exactly what that row asks about.
* If you scanned your site between 1.3.20 and now, treat the DORA and tracker rows as unknown rather than as clean: a scan before may now report signals it did not. Run a new scan.

= 1.3.20 (2026-09-26) =
* Fix: the words of a tool counted as the tool. Every signature - trackers, consent platforms, form plugins - was tried against the whole page HTML, so a paragraph that merely *writes* "we use Matomo" produced a red tracker row and a fix instructing the customer to install a consent platform they already do not need, and a blog post naming Typeform produced "Forms detected (Typeform / Formspree / Jotform), but no Privacy Policy page configured".
* Measured before the fix: 12 false findings per language across Danish, Swedish, Dutch and English, in this plugin, the free scanner and the published CLI engine - 48 in total, none of them true.
* Evidence is now code - an inline script, a src or href on an external asset, the noscript pixel fallback - and element attributes, because Contact Form 7 ships as <div class="wpcf7"> in markup rather than as a script. Prose is not evidence for either.
* The patterns themselves are unchanged, so nothing that was really detected stopped being detected: the same pages with a real script, a real pixel or a real wpcf7 class give the same rows as before. Measured in both directions.
* The DORA signals are deliberately left reading the whole page. Their markers - SPF record, business continuity plan, status page - are claims about the organisation rather than about code running, and a company that writes "we have a business continuity plan" on its security page has said exactly what that row asks about.
* If you scanned your site between 1.3.19 and now, treat the trackers, cookie-consent and forms rows as unknown rather than as clean: a row passed on a sentence may now be reported as a finding. Run a new scan.
= 1.3.19 (2026-09-26) =
* Fix: the words of a legal document counted as a legal document. The privacy pattern was tried against the whole page HTML, so a sentence in running text was read as a link - "we process personal data in this form", or a Dutch page whose sub-processor notice mentions "persoonsgegevens" without linking anything.
* Measured before the fix: 22 false legal pages across four plain-text pages, in Danish, Swedish, Dutch and English. One Swedish paragraph named eight of the documents and the row came back green with no links in the footer at all. A green row a customer cannot check is worse than a red one, because the false pass is invisible.
* The forms row was the worse half. A contact page whose only privacy mention was a sentence telling the visitor it processes their data was reported as "Form(s) on the page, privacy-policy link detected" and passed - a site told it was compliant on the strength of a sentence.
* A legal document is now counted only when the page links it. Both the href and the visible link text count, so a link reading "Privatlivspolitik" to /juridisk/ is still the notice. The wording of every pattern is unchanged, so the language coverage added in 1.3.17 is untouched: the same five links are still found, in all three products.
* This reverses a decision 1.3.17 stated openly, and it was the wrong one. It was written as "it still matches the word wherever it appears, not only inside an href" - true, and the reason a sentence in a paragraph was enough. The requirement is a link, and 1.3.17 measured the link and not the requirement.
* Now measured in all three products - this plugin, the free scanner and the published CLI engine - on plain text in three languages, in both directions: prose must find nothing, and the same documents as links must still be found. Three mutations of the source files turn the build red, so the whole-page reading cannot come back unnoticed.
* If you scanned your site between 1.3.18 and now, treat the legal-pages and forms rows as unknown rather than as clean: a page that was passed on a sentence may now be reported as missing its link. Run a new scan.

= 1.3.18 (2026-09-26) =
* Fix: the legal-pages check only knew English and German page names, so a Danish, Swedish or Dutch shop was told every legal page was missing. A shop with the pages "Om os", "Handelsbetingelser" and "Privatlivspolitik" - all three published, all three required - was reported as "3 of 3 legal pages missing" in the report an agency pays to send its client.
* It now looks for the page forms each market actually uses: /om-os/, /om-oss/, /over-ons/, /colofon/, /bedrijfsgegevens/ and the matching accessibility slugs, and it also finds a page by its name, not only by its URL.
* The name lookup matches the title exactly, on purpose. The Danish imprint page is called "Om os", and a substring match would also count "Om os i pressen" - a press page - as the imprint the report tells you have.
* The same three documents now give the same verdict in Danish, Swedish, Dutch and English, and a site with none of them is still told so. Four mutations of this plugin turn the build red, so it cannot come back unnoticed.

= 1.3.17 (2026-09-26) =
* Fix: the privacy-link pattern only knew English and German, so a Danish, Swedish or Dutch site that linked its privacy policy next to its contact form failed the forms row for doing exactly what the row asks for. A shop with a hand-written form and a /privatlivspolitik/ link was told "no privacy-policy link" here and in the free scanner.
* The pattern is now language-neutral: Danish, Swedish, Dutch, French and Spanish wording joins English and German. The free universal scanner, the published CLI engine and this plugin all read the same signature, so a check with the same name means the same thing in all three products.
* It still matches the word wherever it appears, not only inside an href, because a link whose text says "Privatlivspolitik" and whose URL says /juridisk/ is still the notice.
* The forms row is now measured across all three engines in both directions: a privacy link the port can see must pass everywhere, and one it cannot see must fail everywhere - and a mutation that removes a language, or one that reads only href, turns the port red.
= 1.3.16 (2026-09-26) =
* Fix: the forms check answered a smaller question than the free scanner does about the same website. It only looked at installed WordPress plugins and at the Privacy Policy page assigned in Settings, so a contact form written by hand in the theme, or rendered by a shortcode in a widget, was invisible: the same page failed "forms" in the free scanner and passed "forms" in the report an agency pays to send its client.
* It now reads the served markup as well, using the free scanner's own patterns, and unions the two sources. A page that shows a form and does not link a privacy notice now fails here too - including when a Privacy Policy page does exist in WordPress, because the notice has to be given at the point of collection.
* A form that posts to an external service counts as a form here, even when the markup is unclosed. That is the one place the plugin is stricter than the scanner, and it is deliberate.
* A front page that cannot be read is now reported as "did not run", never as a pass: the markup is one of the two sources, so a site with unreadable markup has an unknown forms result, not a clean one.
* The forms row is measured against the free scanner on the same fixtures, in both directions: the plugin may never pass what the scanner fails, and it may fail more only with a reason the fixture shows.

= 1.3.15 (2026-09-26) =
* Fix: a green row could carry a label that described a lack. The tracker check said "No third-party trackers detected" on a site with none, and the forms check said "No form plugin detected" on a site with no form plugin - both true, and both written as findings. The label is where the verdict goes, so it now states the result first: "Third-party trackers: 0 found" and "Nothing for this check to review". The detail under each label still says exactly what was not found.
* The tracker row now uses the same wording as the free universal scanner, so the plugin and the website cannot drift apart in the sentence a customer reads.
* Warning rows are deliberately left as they are: "HTTPS OK, no HSTS" is meant to say both things at once.
* All eleven checks are now measured for this, in the plugin and in both scanner engines at once, so a label that stops matching its verdict fails the build instead of reaching a report.

= 1.3.14 (2026-09-26) =
* Fix: the SSL/HSTS check sent its own HEAD request instead of reading the front page the other ten checks had already fetched, so a scan made two local requests where one is enough. On a server that answers HEAD with a 403 or a timeout - some firewalls and managed hosts do - the check reported \"HTTPS unreachable\" next to ten green checks that had just read the same site successfully.
* It also disagreed with itself: a front page that could not be read produced ten \"could not read the site\" results and a green SSL check, because the HEAD had happened to work. A check that could not run is now reported as one that did not run, never as a pass.
* HSTS is now read from the same response the visitor's browser receives, and a scan makes exactly one request. A site whose WordPress Address is not https:// still reports \"Not HTTPS\" without making a request at all.
* The eleven checks are now measured against a plugin that contains no HEAD request anywhere, so this cannot come back unnoticed.

= 1.3.13 (2026-09-26) =
* Fix: two checks reported a label that said they had succeeded on the row that said they failed. The legal-pages check read "Legal pages checked" and the forms check read "Forms reviewed" next to a red FAIL, in the dashboard, in the downloadable report an agency sends to a client, and in the regression mail. Both now name the outcome: "3 of 3 legal pages missing" and "Form plugins found, no Privacy Policy page", and the legal check lists what it did not find instead of only counting it.\n* The plugin- and core-health check no longer reads the list of installed plugins and throws it away. It did that on every scan and could not change the verdict.\n* All eleven checks are now measured by running them, not by reading them. The six WordPress-state checks had only ever been syntax-checked, which is how four other checks stayed dead in 1.3.11.\n\n= 1.3.12 (2026-09-26) =
* Fix: the five front-page checks introduced in 1.3.11 never matched anything. The signature list is an array of [name, pattern] pairs, and the matcher read them as if they were named keys, so every pattern was empty and the plugin reported "no trackers detected" on a page with Google Analytics and Meta Pixel in its markup. A WordPress site could pass the tracker check in the dashboard and fail the same check on the free scanner, and a Pro report sent to a client would say so.
* Affected checks: Google Consent Mode v2, IAB TCF, third-party trackers, and DORA page signals. The security-header check was not affected.
* The five checks are now measured against the same fixtures the free scanner runs, so the two products cannot quietly disagree about the same website again.
* If you scanned your site between 1.3.11 and now, treat those four results as unknown rather than as clean: run a new scan.

= 1.3.12 (2026-09-26) =
* Fix: the five front-page checks introduced in 1.3.11 never matched anything. The signature list is an array of [name, pattern] pairs, and the matcher read them as if they were named keys, so every pattern was empty and the plugin reported "no trackers detected" on a page with Google Analytics and Meta Pixel in its markup. A WordPress site could pass the tracker check in the dashboard and fail the same check on the free scanner, and a Pro report sent to a client would say so.
* Affected checks: Google Consent Mode v2, IAB TCF, third-party trackers, and DORA page signals. The security-header check was not affected.
* The five checks are now measured against the same fixtures the free scanner runs, so the two products cannot quietly disagree about the same website again.
* If you scanned your site between 1.3.11 and now, treat those four results as unknown rather than as clean: run a new scan.

= 1.3.11 (2026-09-26) =
* Five more checks, taken from the free universal scanner: Google Consent Mode v2, IAB TCF, trackers loaded without a consent platform, the security headers the front page returns, and DORA page signals. The plugin now runs the same eleven checks the scanner shows you, plus the two WordPress facts only a plugin can see (backups, plugin/core health).
* The five new checks read the site's own front page, fetched once per scan and capped in size, so a scan still makes one local request and no external service is contacted.
* A front page that cannot be read is reported as "did not run" with the reason, never as a pass. A missing check is not a compliance result.
* The check signatures are the scanner's, ported unchanged, so a check with the same name means the same thing in both products.

= 1.3.10 (2026-09-26) =
* Pro: set an address in Settings and the plugin mails you when a check changes — a check that passed starts failing, or a failing one passes again. Silence by default: with no address stored, nothing is ever sent.
* One mail per change, not one per scan. The state is remembered as of the last mail that actually went out, so a site that stays broken is told once instead of every morning for a year.
* Changing or clearing the address re-seeds that state from the last recorded scan, so you never get a first mail listing every check as old news.
* The mail is sent by your own site, with your own mailer, and carries no From address of its own — a made-up sender is how the one mail that must arrive ends up in spam. A mailer that refuses does not mark the change as reported, so the next scan tries again.
* A check seen for the first time is an observation, not a regression, and is not mailed as a change.
* The compliance report says you are emailed when a check changes, but only on a site where an address is actually set.
* The alert follows the licence like the daily interval does: a released, expired or out-of-slots key stops it.

= 1.3.9 (2026-09-26) =
* Pro: the compliance report now states the interval the site is actually scheduled for, so the document a client reads says how often it was checked instead of leaving them to ask.
* The line follows WP-Cron, not the licence: a released, expired or out-of-slots licence puts it back to saying once a week.
* The 1.3.8 entry now says in plain words that Pro scans your site every day, on your own WordPress server. The wording avoided the word until now because the product-truth check could not tell a local cadence from a hosted one; it can now, and only because the code schedules the run.

= 1.3.8 (2026-09-26) =
* Pro: EUComply Pro scans your site every day, on your own WordPress server, instead of once a week. The checks are local, so the extra runs cost the site nothing and need no external service.
* The free version keeps its weekly run. The interval follows the licence, including when a licence is released, expires or loses its device slot — then it goes back to weekly.
* The dashboard states the interval the site is actually scheduled for, so it cannot promise more than the cron array holds.
* A changed interval re-schedules from now, so the first run after activating a licence happens at the next WP-Cron tick instead of a day later.
* Deactivation now clears every copy of the scheduled event, not just the first one found.
* The report's scan history now fills one row per day on Pro, so its twelve rows are twelve days of evidence instead of twelve weeks.

= 1.3.7 (2026-09-26) =
* Pro: the compliance report can be downloaded from wp-admin without creating a client link, so an agency that attaches it every month no longer has to issue a new 30-day link each time.
* The download is the same document as the one a client link serves — same report, same scan history, same filename — and it is now the only rendering of the report in the plugin.
* The download requires the same account permission, nonce and active Pro licence as every other screen in wp-admin, and a refused download returns no document and no filename.
* Every screen and export in the plugin is gated on one declared capability, so a download can never be reached more loosely than the settings page.

= 1.3.6 (2026-09-26) =
* Pro: the client report can be downloaded as a file. Next to a freshly created link there is now a "Download report (HTML)" button, so an agency can attach the report to an e-mail or hand it to an auditor instead of only sending a URL.
* The file is the same report as the page, with the same scan history — not a second, shorter rendering that could disagree with it.
* The filename is "eucomply-report-<date>.html" and contains no part of the link, because filenames end up in mail clients and archive indexes.
* A download without a valid link returns the same "not found" page as the report, so the download address cannot be used to find out which links exist.
* The download and the page stop working at the same moment, and a new link retires both.

= 1.3.5 (2026-09-26) =
* Pro: a client report link. Create one in the dashboard and send it to your client; they read this site's report and scan history in a browser, without a WordPress login.
* The link is read-only, expires after 30 days, and can be revoked at any time. Creating a new one retires the old one.
* Only a hash of the link is stored, so it cannot be shown a second time. If you lose it, create a new one.
* Every rejected link returns the same "not found" page, so the address cannot be used to find out which links exist.
* Reading a report never contacts our license server, so a client is never shown a broken page because our API was slow.
* The link is a secret: anyone who has it can read the report. It is deleted when you uninstall the plugin.

= 1.3.4 (2026-09-26) =
* Pro: the compliance report now carries a scan history, so you can show a client that the site is still compliant and what changed since the first recorded scan.
* One snapshot per day, per check, kept for 52 weeks. A warning is still never counted as a pass.
* Regressions are reported as regressions, not as progress.
* The history holds no URLs, e-mail addresses or scan details, and is deleted when you uninstall the plugin.
* You need at least one scan before a history exists; the report says so instead of showing an empty table.

= 1.3.3 (2026-09-26) =
* The accessibility statement now includes the "known limitations" and enforcement-body elements that Article 13(2) of Directive (EU) 2019/882 asks for.
* The statement no longer ships a broken contact link: set an accessibility contact email in Settings and the statement publishes it, or the document shows a field to complete.
* Every generated document now lists the fields you must complete, read from the document itself, so nothing is missed.
* An invalid or mangled contact address is reported instead of being published.

= 1.3.2 (2026-09-25) =

* **Fixed**: A "device limit reached" (HTTP 409) response no longer locks your license. The key is valid; only this website's slot is taken, and the settings screen now says so and offers to free it.
* **New**: "Release this device" on the settings screen frees the slot, so you can move your license to another website. Changing the license key releases the old one, and deleting the plugin releases the slot too.
* **Fixed**: A license-server error (network problem, 402, 429, 5xx) keeps your verified Pro status for 7 days instead of being treated as a bad key.
* **Changed**: The Pro report counts warnings separately from passes instead of reporting them as plain passes, so the score cannot overstate compliance.

= 1.3.1 (2026-09-25) =

* **Fixed**: Pro marketing and plugin copy now describe the actual HTML report.
* **Fixed**: Pro users can download the HTML report directly from the scan results.
* **Changed**: The update package and manifest now point to version 1.3.1.

= 1.3.0 (2026-09-24) =

* **Changed**: Pro licenses are sold through Stripe and verified by the Mahope license server (mahope.tools). Keys are now 32 hex characters. The former Lemon Squeezy validation is removed.
* **New**: First check activates the site (hostname as device), daily checks validate it.
* **New**: If the license server cannot be reached, a verified Pro status is kept for 7 days.
* **Fixed**: Saving a new key now clears the previous key's verification.

= 1.2.0 (2026-08-23) =

* **New**: uninstall.php — full option cleanup when plugin is deleted.
* **New**: Activation guard — prevents activation on PHP < 7.4 or WP < 5.8 with clear error message.
* **Fixed**: SSL check now handles empty or malformed site URLs without causing PHP notices.
* **Fixed**: readme.txt overhauled with proper wp.org sections, upgrade notice, and detailed FAQ.

= 1.1.0 (2026-08-23) =

* **New**: Lemon Squeezy license API integration with daily verification and refund detection.
* **New**: Auto-update checker via update.json manifest (works before wp.org listing).
* **New**: Pro document generation — DPA, NIS2/DORA clause set, EAA statement, and HTML report from the latest scan.
* **New**: Agency name setting for report branding.
* **Improved**: License validation UX showing activation status in settings.
* **Fixed**: All URLs now point to the official EUComply site.

= 1.0.0 (2026-08-20) =

* **Initial public release.**
* Eleven compliance checks: SSL/HSTS, cookies, forms, backups, plugin/core health, legal pages, Consent Mode v2, IAB TCF, trackers, security headers, DORA page signals.
* Weekly automated re-scan via WP-Cron.
* AJAX-powered scan from admin dashboard (no page reload).
* Pro license system with document generation.

== Upgrade Notice ==

= 1.3.1 =
Corrects Pro product wording and adds a direct HTML report download for licensed sites. Update from Plugins → Installed Plugins or download the latest zip.

= 1.3.0 =
Required for Pro: licenses now come from Stripe and are checked against mahope.tools. Enter the new 32-character key from your purchase email in EUComply → Settings.

= 1.2.0 =
Upgrade for the automatic cleanup (uninstall.php), activation guard (no silent failures on old PHP/WP), and a polished readme.txt for wp.org listing. Update from Plugins → Installed Plugins or download the latest zip.

= 1.1.0 =
Upgrade to 1.1.0 for Lemon Squeezy license API integration with refund detection, auto-update checker from the official manifest, and full Pro document generation (DPA, NIS2, EAA, and HTML reports). The plugin checks for updates automatically — update from Plugins → Installed Plugins or download the latest zip.
