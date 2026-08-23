=== EUComply — EU Compliance Scanner ===
Contributors: eucomply
Tags: gdpr, compliance, nis2, eaa, security, audit
Requires at least: 5.9
Tested up to: 6.7
Requires PHP: 7.4
Stable tag: 1.0.0
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

Scan your WordPress site for EU compliance gaps (GDPR, NIS2, EAA) and get plain-language fixes in your admin dashboard.

== Description ==

EU laws like the GDPR, NIS2 and the European Accessibility Act apply to your website — but nobody tells you what to actually fix.

**EUComply scans your site in one click** and gives you a pass/fail/warning report with concrete, plain-language actions for each gap:

* **HTTPS / SSL certificate** — GDPR Art. 32 security of processing
* **Cookie consent banner** — GDPR / ePrivacy Directive
* **Privacy policy page published & selected** — GDPR Art. 13 transparency
* **WordPress core up to date** — GDPR / NIS2 basic hygiene
* **Dormant administrator accounts (>90 days)** — NIS2 access control

Each check maps to the specific EU regulation it addresses, so you can hand the report to your lawyer, your client or your board.

**Free forever:** unlimited manual scans + dashboard report.

**EUComply Pro ($79/year)** adds auto-generated compliance paperwork:
* Data Processing Agreement (GDPR)
* NIS2 vendor clause kit
* EAA accessibility statement generator
* Scheduled quarterly scans with email reports

== Installation ==

1. In your WordPress admin go to Plugins > Add New.
2. Search for "EUComply" and click Install Now, then Activate.
3. Go to the new "EUComply" menu item and click "Run scan now".

== Frequently Asked Questions ==

= Does this make my site legally compliant? =

No tool can guarantee legal compliance. EUComply highlights common technical gaps and generates starting-point documents. Always confirm obligations that apply to you with qualified counsel.

= Does it send any data anywhere? =

No. All checks run locally on your own server. Nothing leaves your site except the HTTPS request used to verify your own SSL certificate.

= What does Pro cost? =

$79 per year per site. See https://eucomply.pages.dev/plugin/

== Changelog ==

= 1.0.0 =
* Initial release: five-check EU compliance scan with admin dashboard report.
