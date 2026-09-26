=== EUComply — EU Compliance Audit ===
Contributors: mahope
Donate link: https://donate.stripe.com/7sYeVcbn50wieFM8gDbMQ0c
Tags: compliance, gdpr, nis2, eaa, dora, audit, security, privacy, cookies, ssl, backup, imprint, legal, accessibility
Requires at least: 5.8
Tested up to: 6.8
Requires PHP: 7.4
Stable tag: 1.3.4
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

Know your WordPress site's EU compliance status in 30 seconds — from your admin dashboard. Six checks: SSL, cookies, forms, backups, plugins, legal pages. Free. Pro ($79/year per website) unlocks editable HTML document starters and an HTML report from the latest WordPress scan.

== Description ==

EUComply scans your WordPress installation against **six EU compliance criteria** in a single click. The core checks run server-side on your WordPress; the plugin also checks the update manifest and Pro license status as described below.

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
5. Let the weekly automated cron re-scan your site. New results appear automatically.

= Free vs Pro =

| Feature | Free | Pro ($79/year per website) |
|---|---|---|
| Compliance scan dashboard (6 checks) | ✓ | ✓ |
| Pass/fail with fix guidance | ✓ | ✓ |
| Weekly automated re-scan | ✓ | ✓ |
| GDPR Data Processing Agreement (Art. 28) | — | ✓ |
| NIS2/DORA vendor clause set (5 clauses) | — | ✓ |
| EAA Accessibility Statement | — | ✓ |
| HTML report from the latest WordPress scan, with 52 weeks of scan history | — | ✓ |
| Agency name branding in reports | — | ✓ |
| Read-only client report link, valid 30 days and revocable | — | ✓ |
| License revalidation at most once every 24 hours when the Pro admin view is used, with a 7-day offline grace after a temporary license-server failure | — | ✓ |

= Why another compliance plugin? =

Cookie banners and backup plugins solve one problem each. EUComply is a local WordPress compliance checker that scans six dimensions and generates editable HTML document starters plus an HTML report from the latest scan — DPA agreements, NIS2 clauses, and accessibility statements.

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

Those plugins solve one compliance problem (cookies or audit logs). EUComply combines **six compliance dimensions** in one local plugin, plus **editable HTML document generation** — DPA agreements, NIS2/DORA vendor clause sets, and EAA accessibility statements. It also generates an HTML report from the latest WordPress scan.

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

1. EUComply admin dashboard showing six compliance checks with pass/fail status.
2. Settings page with Pro license key input and agency name.
3. Pro document generation table — DPA, NIS2, EAA, and HTML report from the latest scan.

== Changelog ==

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
* Six compliance checks: SSL, cookies, forms, backups, plugins, legal pages.
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
