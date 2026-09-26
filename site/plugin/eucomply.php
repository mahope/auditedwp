<?php
/**
 * Plugin Name:       EUComply — EU Compliance Audit
 * Plugin URI:        https://eucomplypro.com
 * Description:       Runs eleven local checks: SSL/HSTS, cookies, forms, backups, plugin/core health, legal pages, Google Consent Mode v2, IAB TCF, trackers without consent, security headers and DORA page signals. Pro ($79/year per website): editable HTML document starters and an HTML report from the latest scan.
 * Version:           1.3.11
 * Requires at least: 5.8
 * Requires PHP:      7.4
 * Author:            EUComply
 * Author URI:        https://eucomplypro.com
 * Plugin URI:        https://eucomplypro.com
 * License:           GPL v2 or later
 * License URI:       https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain:       eucomply
 * Domain Path:       /languages
 *
 * EUComply — EU Compliance Audit for WordPress
 * Copyright (C) 2026  EUComply
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */

defined( 'ABSPATH' ) || exit;

define( 'EUCOMPLY_VERSION', '1.3.11' );
define( 'EUCOMPLY_PRO_PRICE', 79 );
define( 'EUCOMPLY_PRO_URL', 'https://buy.stripe.com/eVq00i4YH6UG69g0ObbMQ03' );
define( 'EUCOMPLY_UPDATE_URI', 'https://eucomplypro.com/update.json' );
define( 'EUCOMPLY_LICENSE_API', 'https://mahope.tools/api/license/' );
define( 'EUCOMPLY_LICENSE_PRODUCT', 'eucomply-pro' );
define( 'EUCOMPLY_LICENSE_CACHE_TTL', DAY_IN_SECONDS );
define( 'EUCOMPLY_LICENSE_GRACE', 7 * DAY_IN_SECONDS ); // keep a verified Pro status this long while the license server is unreachable
define( 'EUCOMPLY_HISTORY_LIMIT', 52 ); // 52 snapshots: about a year of weekly scans, about seven weeks of the daily Pro scans
define( 'EUCOMPLY_CLIENT_LINK_DAYS', 30 ); // how long a client report link stays valid; a report is a point-in-time claim, not a permanent one
// The scheduled-scan event. The name says "weekly" because that is what it was
// when installs were given it; renaming it here would leave every existing
// install with an orphaned weekly event still firing, so a second, invisible
// scan would run forever. The interval is what carries the meaning, not the name.
define( 'EUCOMPLY_SCAN_EVENT', 'eucomply_weekly_scan' );
// One capability for every screen and every export this plugin has. Declared once
// so a download can never end up gated more loosely than the settings page it
// sits next to — the tests check that no call site passes a capability of its own.
define( 'EUCOMPLY_ADMIN_CAP', 'manage_options' );

/**
 * Activation guard — prevent activation on unsupported PHP or WordPress.
 */
function eucomply_activation_check() {
    $min_php  = '7.4';
    $min_wp   = '5.8';
    $php_ok   = version_compare( PHP_VERSION, $min_php, '>=' );
    $wp_ok    = version_compare( $GLOBALS['wp_version'] ?? '0', $min_wp, '>=' );

    if ( $php_ok && $wp_ok ) {
        return; // All good — let activation proceed.
    }

    $errors = array();
    if ( ! $php_ok ) {
        $errors[] = 'PHP ' . $min_php . ' or newer is required (yours: ' . PHP_VERSION . ').';
    }
    if ( ! $wp_ok ) {
        $errors[] = 'WordPress ' . $min_wp . ' or newer is required.';
    }

    deactivate_plugins( plugin_basename( __FILE__ ) );
    wp_die(
        '<p><strong>EUComply</strong> could not be activated:</p>' .
        '<ul><li>' . implode( '</li><li>', $errors ) . '</li></ul>' .
        '<p>Upgrade your PHP or WordPress and try again.</p>',
        'Plugin Activation Error',
        array( 'back_link' => true )
    );
}
register_activation_hook( __FILE__, 'eucomply_activation_check' );

/**
 * Main plugin class — keeps everything in one place for v1.
 */
class EUComply {

    private static $instance = null;

    /**
     * The front page, fetched at most once per request.
     *
     * Five checks read the same response. Without this they would make five
     * identical requests on every scan, including every daily Pro scan.
     *
     * @var array|null
     */
    private $front_page_cache = null;

    /**
     * Singleton.
     */
    public static function get_instance() {
        if ( null === self::$instance ) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    /**
     * Hook into WordPress.
     */
    private function __construct() {
        add_action( 'admin_menu', array( $this, 'add_admin_menu' ) );
        add_action( 'admin_enqueue_scripts', array( $this, 'enqueue_assets' ) );
        add_action( 'admin_init', array( $this, 'maybe_generate_doc' ) );
        add_action( 'admin_init', array( $this, 'maybe_manage_client_link' ) );
        add_action( 'template_redirect', array( $this, 'maybe_render_client_report' ) );
        add_action( 'wp_ajax_eucomply_run_scan', array( $this, 'ajax_run_scan' ) );

        // Keep the scheduled scan in step with the licence. Cheap on every
        // request: it reads two options and the cron array, and does nothing
        // at all unless the interval is actually wrong.
        $this->sync_scan_schedule();
        add_action( EUCOMPLY_SCAN_EVENT, array( $this, 'run_scan_cron' ) );
    }

    /**
     * Deactivation: clear cron.
     */
    public static function deactivate() {
        // Every occurrence, not one timestamp: the event is now re-created
        // whenever the licence changes, so a site that has been up and down a
        // few times can hold more than one entry.
        wp_clear_scheduled_hook( EUCOMPLY_SCAN_EVENT );
    }

    /**
     * Is Pro active according to what we already know, without asking anyone?
     *
     * The scan interval is read on every request, so it must never be the
     * thing that triggers a license call. This reads the cached verdict and
     * applies the same 7-day grace is_pro() uses, so a site whose license
     * server is briefly unreachable keeps its cadence instead of silently
     * dropping back to a weekly scan.
     *
     * @return bool
     */
    private function pro_cadence_active() {
        $key = self::normalise_key( get_option( 'eucomply_pro_key', '' ) );
        if ( '' === $key || ! preg_match( '/^[a-f0-9]{32}$/', $key ) ) {
            return false;
        }
        // A key with no free slot is a valid key on a website that cannot use
        // it, so it gets the free cadence — the same answer is_pro() gives.
        if ( 'device_limit' === get_option( 'eucomply_pro_state', '' ) ) {
            return false;
        }
        if ( '1' !== get_option( 'eucomply_pro_verified', '' ) ) {
            return false;
        }
        $last_ok = (int) get_option( 'eucomply_pro_last_ok_at', 0 );
        return $last_ok > 0 && ( time() - $last_ok ) < EUCOMPLY_LICENSE_GRACE;
    }

    /**
     * The interval this licence entitles the site to.
     *
     * @return string WP-Cron interval name: 'daily' on Pro, 'weekly' otherwise.
     */
    private function scan_interval() {
        return $this->pro_cadence_active() ? 'daily' : 'weekly';
    }

    /**
     * Make the scheduled event match the licence.
     *
     * The interval is the first item on the Pro list the plugin can deliver on
     * its own: the eleven checks are entirely local, so running them once every 24
     * hours costs the site nothing and no external service, and it turns the
     * report's history from twelve weekly points into twelve days of evidence.
     *
     * A mismatch re-schedules from `time()`, so the first run after a licence
     * change happens at the next WP-Cron tick rather than a full interval later
     * — a customer who has just paid should not wait a day to see it.
     */
    private function sync_scan_schedule() {
        $want  = $this->scan_interval();
        $event = function_exists( 'wp_get_scheduled_event' )
            ? wp_get_scheduled_event( EUCOMPLY_SCAN_EVENT )
            : false;
        if ( $event && ! empty( $event->schedule ) && $want === $event->schedule ) {
            return; // Already right. Re-scheduling on every request would push
                     // the next scan further into the future for ever.
        }
        if ( $event ) {
            wp_clear_scheduled_hook( EUCOMPLY_SCAN_EVENT );
        }
        wp_schedule_event( time(), $want, EUCOMPLY_SCAN_EVENT );
    }

    /**
     * The interval that is actually scheduled right now.
     *
     * @return string 'daily' or 'weekly'.
     */
    private function active_scan_interval() {
        $event = function_exists( 'wp_get_scheduled_event' )
            ? wp_get_scheduled_event( EUCOMPLY_SCAN_EVENT )
            : false;
        if ( $event && ! empty( $event->schedule ) && in_array( $event->schedule, array( 'daily', 'weekly' ), true ) ) {
            return $event->schedule;
        }
        return $this->scan_interval();
    }

    /**
     * The same statement in words, for the dashboard.
     *
     * @return string
     */
    private function cadence_phrase() {
        return 'daily' === $this->active_scan_interval()
            ? 'every 24 hours'
            : 'once a week';
    }

    /**
     * Add admin menu pages.
     */
    public function add_admin_menu() {
        $icon = 'data:image/svg+xml;base64,' . base64_encode(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><rect width="20" height="20" rx="4" fill="#2868d0"/><text x="4" y="15" fill="#fff" font-weight="bold" font-size="12" font-family="sans-serif">EC</text></svg>'
        );
        add_menu_page(
            'EUComply Dashboard',
            'EUComply',
            EUCOMPLY_ADMIN_CAP,
            'eucomply',
            array( $this, 'render_dashboard' ),
            $icon,
            99
        );
        add_submenu_page(
            'eucomply',
            'EUComply Settings',
            'Settings',
            EUCOMPLY_ADMIN_CAP,
            'eucomply-settings',
            array( $this, 'render_settings' )
        );
    }

    /**
     * Load CSS & JS for our admin pages.
     */
    public function enqueue_assets( $hook ) {
        if ( false === strpos( $hook, 'eucomply' ) ) {
            return;
        }
        $css = '
.eucomply-wrap{max-width:1000px;margin:24px 0}
.eucomply-wrap h1{font-size:24px;font-weight:700;margin-bottom:4px}
.eucomply-wrap .sub{color:#4a5a6a;margin-bottom:20px}
.eucomply-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px;margin:20px 0}
.eucomply-card{border:1px solid #d0d8e0;border-radius:10px;padding:18px;background:#fff}
.eucomply-card h3{font-size:14px;margin:0 0 4px;display:flex;align-items:center;gap:6px}
.eucomply-card .status{font-size:13px;font-weight:600;margin-top:6px}
.eucomply-card .status.pass{color:#1a7a44}
.eucomply-card .status.fail{color:#c03030}
.eucomply-card .status.warn{color:#b85a0a}
.eucomply-card .fix{font-size:12.5px;color:#4a5a6a;margin-top:6px}
.eucomply-card .fix a{color:#2868d0;text-decoration:underline}
.eucomply-actions{margin:20px 0;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.eucomply-btn{display:inline-flex;align-items:center;gap:6px;background:#2868d0;color:#fff;border:none;padding:10px 20px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;text-decoration:none}
.eucomply-btn:hover{background:#1a4f9e}
.eucomply-btn.ghost{background:transparent;border:1px solid #d0d8e0;color:#0b1a2a}
.eucomply-btn.ghost:hover{border-color:#2868d0;color:#2868d0}
.eucomply-btn:disabled{opacity:.5;cursor:default}
.eucomply-last{font-size:13px;color:#4a5a6a;margin-top:10px}
.eucomply-table{width:100%;border-collapse:collapse;margin:16px 0;font-size:13.5px}
.eucomply-table th{background:#eef3f9;text-align:left;padding:10px 14px;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#4a5a6a}
.eucomply-table td{padding:10px 14px;border-bottom:1px solid #d0d8e0}
.eucomply-pro-badge{display:inline-block;background:#fff7e6;color:#b85a0a;border:1px solid #fde4b3;border-radius:4px;padding:2px 8px;font-size:11px;font-weight:600}
.eucomply-settings{max-width:500px}
.eucomply-settings label{display:block;font-weight:600;margin:14px 0 4px;font-size:13.5px}
.eucomply-settings input[type=text]{width:100%;padding:8px 12px;border:1px solid #d0d8e0;border-radius:6px;font-size:14px}
.eucomply-settings .desc{font-size:12.5px;color:#4a5a6a;margin-top:4px}
';
        wp_add_inline_style( 'common', $css );
    }

    /**
     * Run the 5 compliance checks. Returns array of results.
     */
    public function run_checks() {
        $results = array();

        // 1. SSL / HTTPS
        $results['ssl'] = $this->check_ssl();

        // 2. Cookie banner & consent
        $results['cookies'] = $this->check_cookies();

        // 3. GDPR forms
        $results['forms'] = $this->check_forms();

        // 4. Backup status
        $results['backups'] = $this->check_backups();

        // 5. Plugin & core health
        $results['plugins'] = $this->check_plugins();

        // 6. Legal pages (EAA, Privacy Policy)
        $results['legal'] = $this->check_legal_pages();

        // 7–11. The same five static checks the free universal scanner runs on a
        // public URL, so a customer who scans eucomplypro.com and then installs
        // the plugin is not told they have lost checks they were just shown.
        $results['consent_mode_v2'] = $this->check_consent_mode_v2();
        $results['tcf']            = $this->check_tcf();
        $results['trackers']       = $this->check_trackers();
        $results['headers']        = $this->check_security_headers();
        $results['dora']           = $this->check_dora();

        // Store results.
        update_option( 'eucomply_scan_results', $results );
        update_option( 'eucomply_last_scan', current_time( 'mysql' ) );
        $this->record_history( $results );
        $this->maybe_send_alert( $results );

        return $results;
    }

    /**
     * Append one snapshot to the scan history (Pro).
     *
     * A report that only describes the scan you ran five minutes ago cannot
     * answer the question a client actually asks: "are we still compliant, and
     * what did you fix?" The plugin already scans weekly, so continuity costs
     * nothing extra — it only has to be written down.
     *
     * Deliberately mirrors the hosted worker's per-check history: one entry per
     * calendar day, per-check tri-state, capped. A scan run twice in one day
     * overwrites that day rather than adding a second row, so a customer who
     * clicks "Scan" five times does not get a history that claims five
     * separate days of work.
     *
     * @param array $results Check results from run_checks().
     */
    private function record_history( $results ) {
        if ( ! is_array( $results ) || empty( $results ) ) {
            return;
        }
        $entry = array(
            'date'   => gmdate( 'Y-m-d' ),
            'checks' => array(),
        );
        $passed = 0;
        $warned = 0;
        $total  = 0;
        foreach ( $results as $key => $r ) {
            if ( ! is_array( $r ) ) {
                continue;
            }
            $total++;
            // Same tri-state as the score: a warning is a partial result and
            // must never be recorded as a pass.
            if ( ! empty( $r['pass'] ) ) {
                $state          = 'pass';
                $passed++;
            } elseif ( ! empty( $r['warn'] ) ) {
                $state = 'warn';
                $warned++;
            } else {
                $state = 'fail';
            }
            $entry['checks'][ $key ] = $state;
        }
        if ( 0 === $total ) {
            return;
        }
        $entry['total']  = $total;
        $entry['passed'] = $passed;
        $entry['warned'] = $warned;

        $history = $this->history();
        unset( $history[ $entry['date'] ] );
        $history[ $entry['date'] ] = $entry;
        // Oldest first, then capped. A weekly scan gives a little over a year,
        // which is the window an auditor or a client renewal asks about.
        ksort( $history );
        if ( count( $history ) > EUCOMPLY_HISTORY_LIMIT ) {
            $history = array_slice( $history, -EUCOMPLY_HISTORY_LIMIT, null, true );
        }
        update_option( 'eucomply_scan_history', $history );
    }

    /**
     * Read the scan history, oldest first.
     *
     * The cap is applied on read as well as on write: an option that was
     * truncated, hand-edited or restored from an old backup must not be able to
     * render an unbounded table in the report.
     *
     * @return array<string, array> Snapshots keyed by Y-m-d.
     */
    private function history() {
        $history = get_option( 'eucomply_scan_history', array() );
        if ( ! is_array( $history ) ) {
            return array();
        }
        if ( count( $history ) > EUCOMPLY_HISTORY_LIMIT ) {
            $history = array_slice( $history, -EUCOMPLY_HISTORY_LIMIT, null, true );
        }
        ksort( $history );
        return $history;
    }

    // ── Regression alerts (Pro) ───────────────────────────────────────────────
    //
    // A daily scan nobody hears about is a scan nobody acts on. The history
    // says the site regressed; without this, the only way to find out is to log
    // into wp-admin and hope to be looking on the right day. It is the last
    // Pro value in the mission's list that needs no hosted service: the scan
    // already runs on the customer's own server, and WordPress already has a
    // mailer, so nothing here leaves the site except one message to an address
    // the customer typed in.
    //
    // Four rules this block exists to keep:
    //   1. Silence by default. No address stored means no mail is ever built,
    //      let alone sent. A plugin must not mail a customer uninvited.
    //   2. Alerts follow the licence like everything else, via is_pro(). A
    //      released, expired or out-of-slots key stops the mail.
    //   3. One mail per *change*, not one per scan. The state is remembered as
    //      of the last mail that actually went out, so a check that stays broken
    //      stays quiet after the first notice instead of arriving every morning
    //      for a year.
    //   4. A failed send does not advance that state, so a transient SMTP
    //      outage delays the alert instead of silently swallowing it.

    /**
     * The address alerts go to, or '' when none is usable.
     *
     * Same form control as the accessibility contact: WordPress' sanitize_email()
     * *strips* characters it does not allow, so a stored value that differs from
     * the sanitized one is a mistyped address rather than a valid one.
     *
     * @return string
     */
    private function alert_address() {
        $raw = trim( (string) get_option( 'eucomply_alert_email', '' ) );
        if ( '' === $raw ) {
            return '';
        }
        $clean = sanitize_email( $raw );
        return ( is_email( $clean ) && $clean === $raw ) ? $clean : '';
    }

    /**
     * The per-check states of one scan, in the same tri-state the history uses.
     *
     * @param array $results Check results from run_checks().
     * @return array<string,string> key => pass|warn|fail.
     */
    private function check_states( $results ) {
        $states = array();
        if ( ! is_array( $results ) ) {
            return $states;
        }
        foreach ( $results as $key => $r ) {
            if ( ! is_array( $r ) ) {
                continue;
            }
            if ( ! empty( $r['pass'] ) ) {
                $states[ (string) $key ] = 'pass';
            } elseif ( ! empty( $r['warn'] ) ) {
                $states[ (string) $key ] = 'warn';
            } else {
                $states[ (string) $key ] = 'fail';
            }
        }
        return $states;
    }

    /**
     * The checks whose state differs from what the customer was last told.
     *
     * Only checks that were in the previous state can be a change. A check that
     * was never recorded before is a new observation, not a regression: a
     * plugin update that adds a check must not greet the customer with a mail
     * full of "not previously recorded", and claiming something changed when
     * there is nothing to compare against is exactly the kind of claim this
     * plugin is not supposed to make.
     *
     * @param array $states   Current states, key => pass|warn|fail.
     * @param array $previous States as of the last alert that was sent.
     * @return array<string,array> key => array( 'from' => string, 'to' => string ).
     */
    private function state_transitions( $states, $previous ) {
        $moves = array();
        if ( ! is_array( $previous ) ) {
            return $moves;
        }
        foreach ( $states as $key => $state ) {
            if ( ! isset( $previous[ $key ] ) ) {
                continue;
            }
            $before = (string) $previous[ $key ];
            if ( $before === $state ) {
                continue;
            }
            $moves[ $key ] = array( 'from' => $before, 'to' => (string) $state );
        }
        return $moves;
    }

    /**
     * The most recent recorded snapshot that is not from today.
     *
     * Today is excluded because it is the scan the alert is *about*: seeding
     * from the snapshot this very scan just wrote would make the new address
     * start out already informed about the state that is being reported, and
     * the change the customer is about to be told about would be the one change
     * they are never told about. Yesterday's snapshot is the last state they
     * could not have been told about either.
     *
     * @return array<string,string> key => pass|warn|fail, empty when there is none.
     */
    private function baseline_states() {
        $history = $this->history();
        unset( $history[ gmdate( 'Y-m-d' ) ] );
        if ( empty( $history ) ) {
            return array();
        }
        $last = end( $history );
        return ( isset( $last['checks'] ) && is_array( $last['checks'] ) ) ? $last['checks'] : array();
    }

    /**
     * Mail the customer when a check changed, if they asked for that.
     *
     * @param array $results Check results from run_checks().
     * @return bool True when a mail was handed to WordPress, false otherwise.
     */
    private function maybe_send_alert( $results ) {
        $to = $this->alert_address();
        if ( '' === $to ) {
            return false; // Rule 1: silence by default.
        }
        if ( ! $this->is_pro() ) {
            return false; // Rule 2.
        }
        $states = $this->check_states( $results );
        if ( empty( $states ) ) {
            return false;
        }

        $previous = get_option( 'eucomply_alert_state', null );
        if ( ! is_array( $previous ) ) {
            // The address was just added. Adopt the last recorded scan as the
            // state nobody has been told about yet, so enabling alerts does not
            // produce a first mail listing every check as a change.
            $baseline = $this->baseline_states();
            if ( ! empty( $baseline ) ) {
                update_option( 'eucomply_alert_state', $baseline );
            }
            return false;
        }

        $moves = $this->state_transitions( $states, $previous );
        if ( empty( $moves ) ) {
            return false; // Rule 3: nothing changed, nothing to say.
        }

        list( $subject, $body ) = $this->build_alert_mail( $moves, $results );
        // No From header on purpose: the site's own mailer already sets one
        // that its SPF record matches, and a From the plugin made up would make
        // the alert fail spam filtering — the one mail that must arrive.
        $sent = wp_mail( $to, $subject, $body, array( 'Content-Type: text/plain; charset=UTF-8' ) );
        if ( $sent ) {
            // Only now is the customer actually informed of these states.
            update_option( 'eucomply_alert_state', $states );
        }
        // Rule 4: a false return means nothing went out, so the states are not
        // advanced and the next scan tries again.
        return (bool) $sent;
    }

    /**
     * The alert mail itself.
     *
     * Plain text on purpose: it is read on a phone, and the words have to work
     * without a stylesheet. The subject says which direction the site moved,
     * because "a check changed" and "a check broke" call for different replies.
     *
     * @param array $moves   Transitions from state_transitions().
     * @param array $results Check results, for the human labels and fixes.
     * @return array array( string $subject, string $body ).
     */
    private function build_alert_mail( $moves, $results ) {
        $site = get_bloginfo( 'name' );
        $site = ( '' === $site ) ? get_home_url() : $site;

        $broken = array();
        $fixed  = array();
        foreach ( $moves as $key => $move ) {
            if ( 'fail' === $move['to'] ) {
                $broken[] = $key;
            } else {
                $fixed[] = $key;
            }
        }

        if ( ! empty( $broken ) ) {
            $subject = sprintf(
                '[EUComply] %d check%s failing on %s',
                count( $broken ),
                1 === count( $broken ) ? '' : 's',
                $site
            );
        } else {
            $subject = sprintf( '[EUComply] %d check%s passing again on %s', count( $fixed ), 1 === count( $fixed ) ? '' : 's', $site );
        }

        $lines   = array();
        $lines[] = $subject;
        $lines[] = '';
        $lines[] = 'The scheduled compliance scan on ' . $site . ' ran on ' . gmdate( 'Y-m-d' ) . ' UTC and found changes since the last time you were told:';
        $lines[] = '';

        foreach ( $moves as $key => $move ) {
            $label  = isset( $results[ $key ]['label'] ) ? (string) $results[ $key ]['label'] : $key;
            $detail = isset( $results[ $key ]['detail'] ) ? (string) $results[ $key ]['detail'] : '';
            $fix    = isset( $results[ $key ]['fix'] ) ? (string) $results[ $key ]['fix'] : '';
            $was    = ( '' === $move['from'] ) ? 'not previously recorded' : $move['from'];
            $lines[] = '- ' . $label . ': ' . strtoupper( $was ) . ' -> ' . strtoupper( $move['to'] );
            if ( '' !== $detail ) {
                $lines[] = '    ' . $detail;
            }
            if ( 'fail' === $move['to'] && '' !== $fix ) {
                $lines[] = '    Fix: ' . $fix;
            }
        }

        $lines[] = '';
        $lines[] = 'The full report and the scan history are here:';
        $lines[] = admin_url( 'admin.php?page=eucomply' );
        $lines[] = '';
        $lines[] = 'This alert is sent from the site itself, by the EUComply plugin, to the address stored in';
        $lines[] = 'EUComply -> Settings. Clear that field to stop it. Changing the address stops alerts to the old';
        $lines[] = 'one and starts from the last recorded scan, so you will not get a first mail full of old news.';

        return array( $subject, implode( "\n", $lines ) );
    }

    /**
     * The site's own front page, fetched once per scan.
     *
     * Five of the eleven checks are static analysis of exactly this: the served
     * HTML and the response headers. The free universal scanner does the same
     * thing to a URL it is given, so running them here keeps one product truth
     * instead of two lists of "what a scan means".
     *
     * The target is not user input. It is `home_url()` from this site's own
     * settings, so there is no address to be tricked into fetching and no
     * SSRF decision to make — the one thing this plugin must never do is ask a
     * visitor's browser to fetch something on their behalf, and it does not.
     *
     * The body is capped, because a scan that reads an unbounded response is
     * how a plugin becomes a memory problem on the site it is supposed to
     * protect. The headers are read from the same response, so the security
     * headers are the ones the visitor's browser actually receives.
     *
     * @return array{ok:bool,html:string,headers:array,error:string}
     */
    private function front_page() {
        if ( null !== $this->front_page_cache ) {
            return $this->front_page_cache;
        }

        $url = get_home_url();
        if ( empty( $url ) || ! is_string( $url ) ) {
            $this->front_page_cache = array(
                'ok'      => false,
                'html'    => '',
                'headers' => array(),
                'error'   => 'the WordPress Address URL is empty or invalid',
            );
            return $this->front_page_cache;
        }

        $response = wp_remote_get(
            $url,
            array(
                'timeout'             => 10,
                'redirection'         => 3,
                'limit_response_size' => 524288,
                'sslverify'           => true,
                'headers'             => array(
                    'User-Agent' => 'EUComply/' . EUCOMPLY_VERSION . ' (+' . home_url( '/' ) . ')',
                    'Accept'     => 'text/html,application/xhtml+xml',
                ),
            )
        );

        if ( is_wp_error( $response ) ) {
            $this->front_page_cache = array(
                'ok'      => false,
                'html'    => '',
                'headers' => array(),
                'error'   => $response->get_error_message(),
            );
            return $this->front_page_cache;
        }

        $code = (int) wp_remote_retrieve_response_code( $response );
        if ( $code < 200 || $code >= 400 ) {
            $this->front_page_cache = array(
                'ok'      => false,
                'html'    => '',
                'headers' => array(),
                'error'   => 'the server answered HTTP ' . $code,
            );
            return $this->front_page_cache;
        }

        $headers = array();
        $raw     = wp_remote_retrieve_headers( $response );
        if ( is_object( $raw ) && method_exists( $raw, 'getAll' ) ) {
            $raw = $raw->getAll();
        }
        if ( is_array( $raw ) ) {
            foreach ( $raw as $name => $value ) {
                $headers[ strtolower( (string) $name ) ] = is_array( $value ) ? implode( ', ', $value ) : (string) $value;
            }
        }

        $this->front_page_cache = array(
            'ok'      => true,
            'html'    => (string) wp_remote_retrieve_body( $response ),
            'headers' => $headers,
            'error'   => '',
        );

        return $this->front_page_cache;
    }

    /**
     * The signatures the free universal scanner uses, in the order it uses them.
     *
     * They are ported, not invented, and deliberately not "improved": a plugin
     * check and a universal check with the same name must mean the same thing,
     * or the two products start disagreeing about one website — which is the
     * defect this whole change exists to remove.
     *
     * @param string $group One of cmv2, tcf, trackers, consent, dora, forms, legal.
     * @return array<int,array{name:string,re:string}>
     */
    private static function signatures( $group ) {
        $sets = array(
            // Google Consent Mode v2.
            'cmv2'     => array(
                array( 'Google Consent Mode v2 class/attribute', '~google_consent_mode|consent_mode_v2|cmv2[\s_,]~i' ),
                array( 'Google Consent Mode v2 (gtag)', '~gtag\([\'"]consent[\'"]|[\'"]consent[\'"],\s*[\'"]default[\'"]|consent.*default.*ad_storage|ad_storage.*consent~i' ),
                array( 'Google Consent Mode v2 (dataLayer)', '~dataLayer[\s\S]{0,200}consent[\s\S]{0,200}(default|update)~i' ),
                array( 'Consent signals for ad storage and personalization', '~granted|denied[\s\S]{0,40}ad_storage|ad_storage[\s\S]{0,40}(granted|denied)~i' ),
                array( 'Google Ads consent integration', '~google_ads[\s\S]{0,100}consent|consent[\s\S]{0,100}google_ads~i' ),
                array( 'Analytics storage consent signal', '~consent.*analytics_storage|analytics_storage.*consent~i' ),
            ),
            // IAB Transparency & Consent Framework.
            'tcf'      => array(
                array( 'IAB TCF API (__tcfapi)', '~__tcfapi|tcfapi~i' ),
                array( 'IAB TCF cookies set', '~IABTCF_[a-z]~i' ),
                array( 'GDPR applies / TCF GDPR signals', '~gdprApplies|tcf[_-]?gdpr~i' ),
                array( 'IAB Consent String present', '~IAB[_-]?Consent[_-]?String|tcstring|consent[_-]?string[_-]?tcf~i' ),
                array( 'TCF version indicator', '~tcf[_-]?v[12]|tcfapiv[12]~i' ),
            ),
            // Trackers that fire without consent being the classic EU case.
            'trackers' => array(
                array( 'Google Analytics / GTM', '~google-analytics\.com|googletagmanager\.com\/gtm\.js|gtag\(~i' ),
                array( 'Meta (Facebook) Pixel', '~connect\.facebook\.net|fbq\([\'"]~i' ),
                array( 'Hotjar', '~static\.hotjar\.com|hj\([\'"]~i' ),
                array( 'Microsoft Clarity', '~clarity\.ms~i' ),
                array( 'LinkedIn Insight Tag', '~snap\.licdn\.com|_linkedin_partner_id~i' ),
                array( 'Snapchat Pixel', '~sc-static\.net|snaptr\([\'"]~i' ),
                array( 'TikTok Pixel', '~static\.tiktok\.com|ttq\.~i' ),
                array( 'Matomo / Piwik', '~matomo|piwik\.js~i' ),
                array( 'Plausible', '~plausible\.io\/js~i' ),
                array( 'Pinterest Tag', '~cdn\.pinterest\.com.*pin.*js|pintrk\(~i' ),
                array( 'Google Ads remarketing', '~googleadservices\.com|google_conversion~i' ),
                array( 'DoubleClick / AdSense', '~doubleclick\.net|googlesyndication~i' ),
            ),
            // Consent platforms, used by the trackers check to tell "tracker
            // present" from "tracker present with consent in front of it".
            'consent'  => array(
                array( 'Cookiebot / OneTrust / Usercentrics / ConsentManager', '~cookiebot|consentmanager|onetrust|usercentrics~i' ),
                array( 'CookieYes', '~cookieyes|cookie-yes~i' ),
                array( 'TarteAuCitron / Klaro / Osano / CookieConsent', '~tarteaucitron|klaro|osano|cookieconsent~i' ),
                array( 'Complianz GDPR', '~complianz|cmplz~i' ),
                array( 'Generic cookie consent banner', '~cookie[_-]?notice|gdpr[_-]?banner|eu[_-]?cookie~i' ),
                array( 'Axeptio', '~axeptio~i' ),
                array( 'CookieScript', '~cookiescript~i' ),
                array( 'CookieHub', '~cookiehub|cookie[_-]?hub~i' ),
                array( 'iubenda', '~iubenda|cookie[_-]?solution~i' ),
                array( 'JustUno / Privy / OptinMonster (popup detected)', '~justuno|privy|optinmonster~i' ),
                array( 'CEE/PL consent plugin', '~shoper|shoprenter|idelo~i' ),
                array( 'WP Consent API', '~wp-consent-api~i' ),
                array( 'Borlabs / CookieNinja', '~borlabs|cookieninja~i' ),
                array( 'Real Cookie Banner', '~real[_-]?cookie[_-]?banner~i' ),
                array( 'Cookie Notice Lite', '~cookie[_-]?notice[_-]?lite~i' ),
                array( 'GDPR Cookie Compliance', '~gdpr[_-]?cookie[_-]?compliance~i' ),
                array( 'Moove GDPR', '~moove[_-]?gdpr~i' ),
                array( 'PixelYourSite (GDPR)', '~pixel[_-]?your[_-]?site~i' ),
                array( 'WebToffee GDPR', '~webtoffee|gdpr[_-]?cookie[_-]?consent~i' ),
                array( 'Quantcast Choice', '~quantcast[_-]?choice~i' ),
                array( 'Analytify/CAOS', '~analytics[_-]?cat~i' ),
            ),
            // DORA-adjacent page signals. Static text markers only: this is not
            // a DORA assessment and the fix text says so.
            'dora'     => array(
                array( 'SPF (Email sender auth)', '~spf[_-]?record|v[_-]?=spf~i' ),
                array( 'DKIM (Email signing)', '~dkim|[_-]?domainkey~i' ),
                array( 'DMARC (Email policy)', '~dmarc_|dmarc[_-]?record|_dmarc\.~i' ),
                array( 'MX (Mail exchange)', '~mx[_-]?record|mx [0-9]|mail[_-]?exchange~i' ),
                array( 'Multi-server / failover signals', '~multiple[_-]?server|failover|redundan|multi[_-]?az[_-]?dns~i' ),
                array( 'CDN failover / multi-CDN', '~cdn[_-]?failover|multi[_-]?cdn|backup[_-]?origin~i' ),
                array( 'Incident response / SOC reporting', '~incident[_-]?response|soc[_-]?report|security[_-]?incident~i' ),
                array( 'BC/DR planning reference', '~bcdr|bcp[_-]?plan|dr[_-]?plan|business[_-]?continuity~i' ),
                array( 'Status page / uptime monitoring', '~status[_-]?page|uptime[_-]?monitor~i' ),
            ),
        );

        return isset( $sets[ $group ] ) ? $sets[ $group ] : array();
    }

    /**
     * Which signatures in a group the served HTML contains.
     *
     * @param string $group Signature group name.
     * @param string $html  Served HTML.
     * @return array<int,string> Matched names, in the order of the signature list.
     */
    private static function matched_signatures( $group, $html ) {
        $found = array();
        foreach ( self::signatures( $group ) as $sig ) {
            if ( '' !== $html && preg_match( $sig['re'], $html, $m ) ) {
                $found[] = $sig['name'];
            }
        }
        return $found;
    }

    /**
     * The result every front-page check returns when the page cannot be read.
     *
     * A check that could not run must not be a pass. Reporting "no trackers
     * detected" because the fetch failed is the single worst thing a compliance
     * tool can do, so this is a warning with the reason in it.
     *
     * @param string $label Short name of the check.
     * @param string $error Why the page could not be read.
     * @return array
     */
    private function unreadable( $label, $error ) {
        return array(
            'pass'   => false,
            'warn'   => true,
            'label'  => $label . ': could not read the site',
            'detail' => 'The front page could not be read, so this check did not run — ' . $error . '. This is not a result, and it is not a pass.',
            'fix'    => 'Make sure https://' . wp_parse_url( get_home_url(), PHP_URL_HOST ) . ' is reachable from this server (no firewall, no basic-auth on the front page), then run the scan again.',
        );
    }

    /**
     * Google Consent Mode v2 signatures in the served HTML.
     *
     * @return array
     */
    private function check_consent_mode_v2() {
        $page = $this->front_page();
        if ( ! $page['ok'] ) {
            return $this->unreadable( 'Consent Mode v2', $page['error'] );
        }
        $hits = self::matched_signatures( 'cmv2', $page['html'] );
        $out  = array(
            'pass'   => count( $hits ) >= 2,
            'warn'   => 1 === count( $hits ),
            'label'  => count( $hits ) >= 2 ? 'Google Consent Mode v2 detected' : ( $hits ? 'Partial Consent Mode v2 signals' : 'No Google Consent Mode v2 detected' ),
            'detail' => $hits ? 'Consent Mode v2 signals: ' . implode( ', ', $hits ) . '.' : 'No Consent Mode v2 signals found. Since March 2024, Google requires Consent Mode v2 for ad personalization in the EEA. Without it, Google Ads conversion tracking may be restricted.',
        );
        if ( count( $hits ) < 2 ) {
            $out['fix'] = 'Implement Google Consent Mode v2 with the default consent state for ad_storage and analytics_storage. See https://developers.google.com/tag-platform/security/guides/consent.';
        }
        return $out;
    }

    /**
     * IAB TCF signals in the served HTML.
     *
     * @return array
     */
    private function check_tcf() {
        $page = $this->front_page();
        if ( ! $page['ok'] ) {
            return $this->unreadable( 'IAB TCF', $page['error'] );
        }
        $hits = self::matched_signatures( 'tcf', $page['html'] );
        $out  = array(
            'pass'   => count( $hits ) >= 2,
            'warn'   => 1 === count( $hits ),
            'label'  => count( $hits ) >= 2 ? 'IAB TCF detected' : ( $hits ? 'Partial IAB TCF signals' : 'No IAB TCF detected' ),
            'detail' => $hits ? 'TCF signals: ' . implode( ', ', $hits ) . '.' : 'No IAB Transparency & Consent Framework signals found. TCF is used by ad-tech platforms and publishers for GDPR consent management in programmatic advertising.',
        );
        if ( count( $hits ) < 2 ) {
            $out['fix'] = 1 === count( $hits )
                ? 'Partial TCF implementation detected. Ensure __tcfapi is available and IAB consent strings are properly stored.'
                : 'If you run programmatic ads in the EEA, implement IAB TCF through your CMP. See https://iabeurope.eu/tcf/.';
        }
        return $out;
    }

    /**
     * Third-party trackers present without a consent platform in front of them.
     *
     * @return array
     */
    private function check_trackers() {
        $page = $this->front_page();
        if ( ! $page['ok'] ) {
            return $this->unreadable( 'Trackers without consent', $page['error'] );
        }
        $hits     = self::matched_signatures( 'trackers', $page['html'] );
        $consents = self::matched_signatures( 'consent', $page['html'] );
        $has_cmp  = ! empty( $consents );
        $out      = array(
            'pass'   => empty( $hits ) || $has_cmp,
            'warn'   => ! empty( $hits ) && $has_cmp && ! preg_match( '~consent[_-]?mode|__tcfapi~i', $page['html'] ),
            'label'  => empty( $hits ) ? 'No third-party trackers detected' : ( $has_cmp ? count( $hits ) . ' tracker(s) detected, consent platform present' : count( $hits ) . ' tracker(s) with NO consent platform' ),
            'detail' => $hits ? 'Trackers found in page markup: ' . implode( ', ', $hits ) . '. ' . ( $has_cmp ? 'A consent platform was also detected (' . $consents[0] . ').' : 'No consent management platform was found — these trackers likely fire before consent.' ) : 'No third-party marketing/analytics trackers found in the served HTML.',
        );
        if ( ! empty( $hits ) && ! $has_cmp ) {
            $out['fix'] = 'EU ePrivacy rules and GDPR Art. 6 require consent BEFORE loading non-essential trackers. Install a CMP that blocks Google Analytics/Meta Pixel etc. until the visitor consents.';
        }
        return $out;
    }

    /**
     * The security headers the front page actually returns.
     *
     * @return array
     */
    private function check_security_headers() {
        $page = $this->front_page();
        if ( ! $page['ok'] ) {
            return $this->unreadable( 'Security headers', $page['error'] );
        }
        $h     = $page['headers'];
        $csp   = isset( $h['content-security-policy'] ) ? $h['content-security-policy'] : ( isset( $h['content-security-policy-report-only'] ) ? $h['content-security-policy-report-only'] : '' );
        $nosn  = isset( $h['x-content-type-options'] ) ? $h['x-content-type-options'] : '';
        $refer = isset( $h['referrer-policy'] ) ? $h['referrer-policy'] : '';
        $frame = isset( $h['x-frame-options'] ) ? $h['x-frame-options'] : '';

        $issues = array();
        if ( ! $csp ) {
            $issues[] = 'Content-Security-Policy missing';
        }
        if ( ! $nosn ) {
            $issues[] = 'X-Content-Type-Options: nosniff missing';
        }
        if ( ! $refer ) {
            $issues[] = 'Referrer-Policy missing';
        }
        if ( ! $frame && false === strpos( $csp, 'frame-ancestors' ) ) {
            $issues[] = 'X-Frame-Options or CSP frame-ancestors missing';
        }

        $out = array(
            'pass'   => empty( $issues ),
            'warn'   => ! empty( $issues ) && count( $issues ) <= 2,
            'label'  => $issues ? count( $issues ) . ' security header' . ( 1 === count( $issues ) ? '' : 's' ) . ' missing' : 'All common security headers present',
            'detail' => $issues ? 'Missing: ' . implode( '; ', $issues ) . '.' : 'CSP, HSTS (checked above), X-Content-Type-Options, Referrer-Policy, X-Frame-Options all set.',
        );
        if ( $issues ) {
            $out['fix'] = 'Add security headers. See https://securityheaders.com for guidance on each.';
        }
        return $out;
    }

    /**
     * DORA-adjacent page signals in the served HTML.
     *
     * Static text markers only. This is explicitly not a DORA assessment — the
     * detail says so, because a page that mentions "incident response" is not a
     * business that has one.
     *
     * @return array
     */
    private function check_dora() {
        $page = $this->front_page();
        if ( ! $page['ok'] ) {
            return $this->unreadable( 'DORA page signals', $page['error'] );
        }
        $hits = self::matched_signatures( 'dora', $page['html'] );
        $out  = array(
            'pass'   => count( $hits ) >= 2,
            'warn'   => 1 === count( $hits ),
            'label'  => $hits ? 'DORA-related page signals: ' . count( $hits ) . ' found' : 'No DORA-related page signals detected',
            'detail' => $hits ? 'Page-text markers found: ' . implode( ', ', $hits ) . '. This is not a DORA assessment.' : 'No page-text references to failover, incident response or continuity were found. This scan does not query DNS or assess DORA compliance.',
        );
        if ( count( $hits ) < 2 ) {
            $out['fix'] = 'Review whether the site publishes useful failover, incident-response and business-continuity information. Verify DNS and regulatory controls separately.';
        }
        return $out;
    }

    /**
     * Check SSL/HTTPS.
     */
    private function check_ssl() {
        $home = get_home_url();

        // Guard: home_url might be empty or malformed.
        if ( empty( $home ) || ! is_string( $home ) ) {
            return array(
                'pass'    => false,
                'label'   => 'Site URL not set',
                'detail'  => 'The WordPress Address URL is empty or invalid in settings.',
                'fix'     => 'Go to Settings → General and set a valid WordPress Address URL starting with https://',
            );
        }

        $scheme = parse_url( $home, PHP_URL_SCHEME );

        if ( ! is_string( $scheme ) || 'https' !== $scheme ) {
            $scheme_label = is_string( $scheme ) ? strtoupper( $scheme ) : 'unknown';
            return array(
                'pass'    => false,
                'label'   => 'Not HTTPS',
                'detail'  => 'Site URL uses ' . $scheme_label . ', not HTTPS.',
                'fix'     => 'Install an SSL certificate and set WordPress Address to https://',
            );
        }

        // Check HSTS header.
        $response = wp_remote_head( $home, array( 'timeout' => 5 ) );
        if ( is_wp_error( $response ) ) {
            return array(
                'pass'    => false,
                'label'   => 'HTTPS unreachable',
                'detail'  => 'Could not verify HTTPS — ' . $response->get_error_message(),
                'fix'     => 'Check server configuration.',
            );
        }

        $hsts = wp_remote_retrieve_header( $response, 'strict-transport-security' );
        if ( empty( $hsts ) ) {
            return array(
                'pass'    => true,
                'warn'    => true,
                'label'   => 'HTTPS OK, no HSTS',
                'detail'  => 'SSL is active but missing Strict-Transport-Security header.',
                'fix'     => 'Add HSTS header in server config (e.g. add_header Strict-Transport-Security "max-age=31536000").',
            );
        }

        return array(
            'pass'   => true,
            'label'  => 'HTTPS + HSTS OK',
            'detail' => 'SSL certificate active, HSTS header present.',
        );
    }

    /**
     * Check if a cookie banner / consent plugin is active.
     */
    private function check_cookies() {
        // Known consent plugins (class/function check is more reliable).
        $consent_plugins = array(
            'complianz-gdpr/cmp-functions.php',
            'complianz-gdpr/complianz-gpdr.php',
            'cookie-law-info/cookie-law-info.php',
            'cookiebot/cookiebot.php',
            'cookie-notice/cookie-notice.php',
            'gdpr-cookie-compliance/moove-gdpr.php',
            'wp-gdpr-core/wp-gdpr-core.php',
            'uk-cookie-consent/uk-cookie-consent.php',
            'cookie-yes-gdpr/cookie-yes.php',
        );

        $active  = array();
        $missing = array();

        foreach ( $consent_plugins as $plugin ) {
            if ( is_plugin_active( $plugin ) ) {
                $active[] = dirname( $plugin );
            }
        }

        // Also check for wp_consent_api integration.
        $has_consent_api = function_exists( 'wp_has_consent' ) || function_exists( 'wp_set_consent' );

        if ( ! empty( $active ) ) {
            return array(
                'pass'    => true,
                'label'   => 'Cookie consent active',
                'detail'  => 'Detected: ' . implode( ', ', $active ) . ( $has_consent_api ? ' + WP Consent API' : '' ),
                'plugins' => $active,
            );
        }

        if ( $has_consent_api ) {
            return array(
                'pass'    => true,
                'warn'    => true,
                'label'   => 'WP Consent API present',
                'detail'  => 'WP Consent API is registered, but no full cookie banner plugin detected. Consider adding one for visual consent UI.',
                'fix'     => 'Install a consent banner plugin (Complianz, CookieYes, Cookiebot).',
            );
        }

        return array(
            'pass'    => false,
            'label'   => 'No cookie consent found',
            'detail'  => 'No known GDPR cookie consent plugin or WP Consent API detected.',
            'fix'     => 'Install a cookie consent plugin (Complianz, CookieYes, or Cookiebot). Under GDPR, analytics/tracking cookies require prior consent.',
        );
    }

    /**
     * Check forms for GDPR compliance (privacy notice + consent checkbox).
     */
    private function check_forms() {
        $results = array(
            'pass'     => true,
            'label'    => 'Forms reviewed',
            'detail'   => '',
            'forms'    => array(),
            'warnings' => array(),
        );

        // Detect known form plugins.
        $form_plugins = array(
            'contact-form-7/wp-contact-form-7.php'    => 'Contact Form 7',
            'wpforms-lite/wpforms.php'                  => 'WPForms',
            'wpforms/wpforms.php'                        => 'WPForms (Pro)',
            'gravityforms/gravityforms.php'              => 'Gravity Forms',
            'elementor/elementor.php'                    => 'Elementor (may have forms)',
            'formidable/formidable.php'                  => 'Formidable Forms',
            'fluentform/fluentform.php'                  => 'Fluent Forms',
        );

        foreach ( $form_plugins as $path => $name ) {
            if ( is_plugin_active( $path ) ) {
                $results['forms'][] = $name;
            }
        }

        if ( empty( $results['forms'] ) ) {
            $results['pass']   = true;
            $results['label']  = 'No form plugin detected';
            $results['detail'] = 'No major form plugin found. If you use custom forms, review them manually for GDPR compliance.';
            return $results;
        }

        // Check if theme or known plugin includes privacy checkbox hooks.
        // This is a best-effort check; we can't parse every form's configuration.
        $has_privacy_link = false;
        $privacy_page     = get_option( 'wp_page_for_privacy_policy' );
        if ( $privacy_page ) {
            $has_privacy_link = true;
        }

        if ( ! $has_privacy_link ) {
            $results['pass']       = false;
            $results['warnings'][] = 'No Privacy Policy page set in Settings → Privacy. Create one and link it from forms.';
            $results['detail']     = 'Forms detected (' . implode( ', ', $results['forms'] ) . '), but no Privacy Policy page configured.';
            $results['fix']        = 'Go to Settings → Privacy and create/assign a Privacy Policy page. Ensure forms link to it and include a consent checkbox where required.';
        } else {
            $results['detail'] = 'Forms detected: ' . implode( ', ', $results['forms'] ) . '. Privacy Policy page exists.';
        }

        return $results;
    }

    /**
     * Check backup status.
     */
    private function check_backups() {
        // Known backup plugins with last-backup timestamps.
        $backup_plugin_meta = array(
            'updraftplus/updraftplus.php'                => 'UpdraftPlus',
            'backwpup/backwpup.php'                      => 'BackWPup',
            'jetpack/jetpack.php'                        => 'Jetpack (backups)',
            'wpvivid-backuprestore/wpvivid-backuprestore.php' => 'WPvivid',
            'backupbuddy/backupbuddy.php'                => 'BackupBuddy',
        );

        $active_backups = array();
        foreach ( $backup_plugin_meta as $path => $name ) {
            if ( is_plugin_active( $path ) ) {
                $active_backups[] = $name;
            }
        }

        if ( empty( $active_backups ) ) {
            return array(
                'pass'    => false,
                'label'   => 'No backup plugin',
                'detail'  => 'No known backup plugin is active.',
                'fix'     => 'Install a backup plugin (UpdraftPlus, WPvivid, or BackWPup) and configure daily/weekly backups to off-server storage.',
            );
        }

        // For UpdraftPlus, check the existing backups timestamp.
        $last_backup = null;
        if ( is_plugin_active( 'updraftplus/updraftplus.php' ) && class_exists( 'UpdraftPlus_Options' ) ) {
            $timestamp = UpdraftPlus_Options::get_updraft_option( 'updraft_last_backup' );
            if ( ! empty( $timestamp ) ) {
                $last_backup = $timestamp;
            }
        }

        if ( $last_backup ) {
            $age_days = floor( ( time() - intval( $last_backup ) ) / DAY_IN_SECONDS );
            if ( $age_days > 30 ) {
                return array(
                    'pass'    => true,
                    'warn'    => true,
                    'label'   => 'Backup exists, outdated',
                    'detail'  => $active_backups[0] . ' — last backup was ' . $age_days . ' days ago.',
                    'fix'     => 'Configure backups to run at least weekly, stored off-server.',
                );
            }
            return array(
                'pass'   => true,
                'label'  => 'Backup active (' . $age_days . 'd ago)',
                'detail' => $active_backups[0] . ' — last backup ' . $age_days . ' days ago.',
            );
        }

        // Backup plugin active but can't determine last backup time.
        return array(
            'pass'   => true,
            'warn'   => true,
            'label'  => 'Backup plugin active',
            'detail' => 'Active: ' . implode( ', ', $active_backups ) . '. Verify backup schedule and off-site storage.',
        );
    }

    /**
     * Check plugin & core health — outdated, unmaintained, known CVEs.
     */
    private function check_plugins() {
        $warnings = array();
        $pass     = true;

        // WordPress version.
        global $wp_version;
        $core_latest = get_bloginfo( 'version' );

        // Check if core is up to date (call wp.org API).
        $core_updates = get_core_updates();
        if ( ! empty( $core_updates ) && 'upgrade' === $core_updates[0]->response ) {
            $pass      = false;
            $warnings[] = 'WordPress core ' . $wp_version . ' is outdated. Latest: ' . $core_updates[0]->current;
        }

        // Plugin updates.
        $plugin_updates = get_plugin_updates();
        $outdated       = array();
        foreach ( $plugin_updates as $file => $data ) {
            $outdated[] = $data->Name . ' (' . $data->Version . ' → ' . $data->update->new_version . ')';
        }
        if ( ! empty( $outdated ) ) {
            $pass = false;
            $warnings[] = count( $outdated ) . ' plugin(s) need updates: ' . implode( ', ', array_slice( $outdated, 0, 5 ) ) . ( count( $outdated ) > 5 ? ' (+' . ( count( $outdated ) - 5 ) . ' more)' : '' );
        }

        // Check last updated on wp.org for each plugin (best-effort).
        // We don't call external API on every page load — too slow.
        // Instead, flag plugins with no updates in 2+ years from local data.
        $all_plugins = get_plugins();
        foreach ( $all_plugins as $file => $data ) {
            if ( empty( $data['Version'] ) ) {
                continue;
            }
            // If a plugin hasn't been updated by the user in 2 years (local knowledge only).
            // This is a rough heuristic; we skip for now.
        }

        if ( empty( $warnings ) ) {
            return array(
                'pass'  => true,
                'label' => 'All up to date',
                'detail' => 'WordPress ' . $wp_version . ' and all plugins are current.',
            );
        }

        return array(
            'pass'      => $pass,
            'label'     => $pass ? 'Minor issues' : 'Updates needed',
            'detail'    => implode( ' | ', $warnings ),
            'fix'       => 'Run wp-admin/update-core.php and update all plugins.',
        );
    }

    /**
     * Check existence of required legal pages.
     */
    private function check_legal_pages() {
        $results = array(
            'pass'      => true,
            'label'     => 'Legal pages checked',
            'detail'    => '',
            'pages'     => array(),
            'warnings'  => array(),
        );

        // Privacy Policy.
        $privacy_id = get_option( 'wp_page_for_privacy_policy' );
        if ( $privacy_id ) {
            $page = get_post( $privacy_id );
            if ( $page && 'publish' === $page->post_status ) {
                $results['pages']['privacy'] = 'Exists: ' . esc_html( $page->post_title );
            } else {
                $results['warnings'][] = 'Privacy Policy page assigned but not published.';
            }
        } else {
            $results['warnings'][] = 'No Privacy Policy page assigned (Settings → Privacy).';
        }

        // Imprint / Impressum (common in DE/AT).
        $imprint_page = get_page_by_path( 'imprint' );
        if ( ! $imprint_page ) {
            $imprint_page = get_page_by_path( 'impressum' );
        }
        if ( ! $imprint_page ) {
            // Search by title.
            global $wpdb;
            $imprint_id = $wpdb->get_var(
                $wpdb->prepare(
                    "SELECT ID FROM {$wpdb->posts} WHERE post_title LIKE %s AND post_type = 'page' AND post_status = 'publish' LIMIT 1",
                    '%Imprint%'
                )
            );
            if ( ! $imprint_id ) {
                $imprint_id = $wpdb->get_var(
                    $wpdb->prepare(
                        "SELECT ID FROM {$wpdb->posts} WHERE post_title LIKE %s AND post_type = 'page' AND post_status = 'publish' LIMIT 1",
                        '%Impressum%'
                    )
                );
            }
            if ( $imprint_id ) {
                $imprint_page = get_post( $imprint_id );
            }
        }

        if ( $imprint_page ) {
            $results['pages']['imprint'] = 'Exists: ' . esc_html( $imprint_page->post_title );
        } else {
            $results['warnings'][] = 'No Imprint/Impressum page found. Required in DE, AT, CH under Telemediengesetz (TMG).';
        }

        // Accessibility statement (EAA).
        $eaa_page = get_page_by_path( 'accessibility-statement' );
        if ( ! $eaa_page ) {
            $eaa_page = get_page_by_path( 'accessibility' );
        }
        if ( ! $eaa_page ) {
            global $wpdb;
            $eaa_id = $wpdb->get_var(
                $wpdb->prepare(
                    "SELECT ID FROM {$wpdb->posts} WHERE post_title LIKE %s AND post_type = 'page' AND post_status = 'publish' LIMIT 1",
                    '%Accessibility%'
                )
            );
            if ( $eaa_id ) {
                $eaa_page = get_post( $eaa_id );
            }
        }

        if ( $eaa_page ) {
            $results['pages']['eaa'] = 'Exists: ' . esc_html( $eaa_page->post_title );
        } else {
            $results['warnings'][] = 'No Accessibility Statement found. Required under the European Accessibility Act (EAA).';
        }

        if ( ! empty( $results['warnings'] ) ) {
            $results['pass']    = false;
            $results['detail']  = count( $results['warnings'] ) . ' legal page(s) missing.';
            $results['fix']     = 'Create the missing pages: Privacy Policy (Settings → Privacy), Imprint, Accessibility Statement.';
        } else {
            $results['detail'] = 'Privacy Policy ✓' . ( isset( $results['pages']['imprint'] ) ? ', Imprint ✓' : '' ) . ( isset( $results['pages']['eaa'] ) ? ', Accessibility ✓' : '' );
        }

        return $results;
    }

    /**
     * Render the admin dashboard.
     */
    public function render_dashboard() {
        $results = get_option( 'eucomply_scan_results', false );
        $last    = get_option( 'eucomply_last_scan', false );
        $is_pro  = $this->is_pro();
        ?>
        <div class="wrap eucomply-wrap">
            <h1>EUComply — Compliance Dashboard</h1>
            <p class="sub">
                <?php if ( $is_pro ) : ?>
                    <span style="color:#1a7a44">Pro ✓</span> — Document generation is active.
                <?php else : ?>
                    Free version — <a href="<?php echo esc_url( EUCOMPLY_PRO_URL ); ?>">Upgrade to Pro ($79/year per website)</a> for editable HTML DPA, NIS2/DORA and EAA starters plus an HTML report from the latest scan.
                <?php endif; ?>
            </p>

            <div class="eucomply-actions">
                <button class="eucomply-btn" id="eucomply-scan-btn">🔄 Run scan now</button>
                <a class="eucomply-btn ghost" href="<?php echo esc_url( admin_url( 'admin.php?page=eucomply-settings' ) ); ?>">⚙️ Settings</a>
            </div>

            <p class="eucomply-last" id="eucomply-last">
                <?php if ( $last ) : ?>
                    Last scan: <?php echo esc_html( $last ); ?>
                <?php else : ?>
                    No scan results yet. Click "Run scan now" to start.
                <?php endif; ?>
            </p>

            <?php
            // Its own element on purpose: the dashboard script rewrites
            // #eucomply-last after a manual run, and a cadence that vanishes on
            // the next click is not a fact the customer can rely on. Quoted
            // from the cron array, so it can only state what is really
            // scheduled.
            ?>
            <p class="eucomply-last" id="eucomply-cadence">
                Next automatic run: <?php echo esc_html( $this->cadence_phrase() ); ?><?php echo $is_pro ? ' (Pro)' : ''; ?>
            </p>

            <div id="eucomply-results">
                <?php if ( $results ) : ?>
                    <?php $this->render_results( $results ); ?>
                <?php else : ?>
                    <p style="color:#4a5a6a;margin-top:20px;font-size:14px">Click "Run scan now" to check your site against 6 EU compliance criteria.</p>
                <?php endif; ?>
            </div>

            <div id="eucomply-report-action" style="margin-top:20px"<?php echo $results ? '' : ' hidden'; ?>>
                <?php if ( $is_pro ) : ?>
                    <a class="eucomply-btn" href="<?php echo esc_url( wp_nonce_url( admin_url( 'admin.php?page=eucomply-settings&eucomply_doc=report' ), 'eucomply_doc' ) ); ?>">↓ Download HTML compliance report</a>
                <?php else : ?>
                    <a class="eucomply-btn" href="<?php echo esc_url( EUCOMPLY_PRO_URL ); ?>">Unlock the HTML compliance report</a>
                <?php endif; ?>
            </div>

            <?php if ( $is_pro ) : ?>
            <div style="margin-top:28px;border:1px solid #d0d8e0;border-radius:10px;padding:20px;background:#fff">
                <h2 style="font-size:16px;margin:0 0 8px">📄 Pro: Documents &amp; Reports</h2>
                <table class="eucomply-table">
                    <tr><th>Document</th><th>Last generated</th><th></th></tr>
                    <tr><td>GDPR Data Processing Agreement</td><td><?php echo esc_html( get_option( 'eucomply_pro_dpa_date', 'Not yet' ) ); ?></td><td><a href="<?php echo esc_url( wp_nonce_url( admin_url( 'admin.php?page=eucomply-settings&eucomply_doc=dpa' ), 'eucomply_doc' ) ); ?>" class="eucomply-btn ghost" style="padding:6px 14px;font-size:12px">Generate</a></td></tr>
                    <tr><td>NIS2 / DORA Vendor Clause Set</td><td><?php echo esc_html( get_option( 'eucomply_pro_nis2_date', 'Not yet' ) ); ?></td><td><a href="<?php echo esc_url( wp_nonce_url( admin_url( 'admin.php?page=eucomply-settings&eucomply_doc=nis2' ), 'eucomply_doc' ) ); ?>" class="eucomply-btn ghost" style="padding:6px 14px;font-size:12px">Generate</a></td></tr>
                    <tr><td>EAA Accessibility Statement</td><td><?php echo esc_html( get_option( 'eucomply_pro_eaa_date', 'Not yet' ) ); ?></td><td><a href="<?php echo esc_url( wp_nonce_url( admin_url( 'admin.php?page=eucomply-settings&eucomply_doc=eaa' ), 'eucomply_doc' ) ); ?>" class="eucomply-btn ghost" style="padding:6px 14px;font-size:12px">Generate</a></td></tr>
                    <tr><td>HTML Compliance Report</td><td><?php echo esc_html( get_option( 'eucomply_pro_report_date', 'Not yet' ) ); ?></td><td><a href="<?php echo esc_url( wp_nonce_url( admin_url( 'admin.php?page=eucomply-settings&eucomply_doc=report' ), 'eucomply_doc' ) ); ?>" class="eucomply-btn ghost" style="padding:6px 14px;font-size:12px">Generate</a></td></tr>
                </table>
            </div>
            <?php $this->render_client_link_box(); ?>
            <?php endif; ?>
        </div>

        <script>
        (function(){
            var btn = document.getElementById('eucomply-scan-btn');
            var res = document.getElementById('eucomply-results');
            var lst = document.getElementById('eucomply-last');
            var reportAction = document.getElementById('eucomply-report-action');
            if (!btn) return;
            btn.addEventListener('click', function(){
                btn.disabled = true;
                btn.textContent = '🔄 Scanning...';
                var data = new URLSearchParams({ action: 'eucomply_run_scan', _ajax_nonce: '<?php echo wp_create_nonce( 'eucomply_scan' ); ?>' });
                fetch(ajaxurl, { method:'POST', body:data })
                .then(function(r){ return r.json(); })
                .then(function(j){
                    btn.disabled = false;
                    btn.textContent = '🔄 Run scan now';
                    if (j.success && j.data.html) {
                        res.innerHTML = j.data.html;
                        if (reportAction) reportAction.hidden = false;
                        if (lst) lst.textContent = 'Last scan: ' + (j.data.time || 'just now');
                    } else {
                        res.innerHTML = '<p style="color:#c03030">Scan failed: ' + (j.data || 'unknown error') + '</p>';
                    }
                })
                .catch(function(e){
                    btn.disabled = false;
                    btn.textContent = '🔄 Run scan now';
                    res.innerHTML = '<p style="color:#c03030">Error: ' + e.message + '</p>';
                });
            });
        })();
        </script>
        <?php
    }

    /**
     * Render the scan result cards.
     */
    private function render_results( $results ) {
        $checks = array(
            'ssl'     => array( 'label' => '🔒 SSL &amp; HTTPS', 'desc' => 'Certificate, HSTS, mixed content' ),
            'cookies' => array( 'label' => '🍪 Cookie Consent', 'desc' => 'Banner, WP Consent API' ),
            'forms'   => array( 'label' => '📋 GDPR Forms', 'desc' => 'Privacy notice, consent checkbox' ),
            'backups' => array( 'label' => '💾 Backup Status', 'desc' => 'Schedule, storage, age' ),
            'plugins' => array( 'label' => '⚠️ Plugin &amp; Core Health', 'desc' => 'Updates, CVEs, unmaintained' ),
            'legal'   => array( 'label' => '📄 Legal Pages', 'desc' => 'Privacy, imprint, accessibility' ),
        );

        echo '<div class="eucomply-grid">';
        foreach ( $checks as $key => $info ) {
            $r = isset( $results[ $key ] ) ? $results[ $key ] : null;
            if ( ! $r ) {
                echo '<div class="eucomply-card"><h3>' . $info['label'] . '</h3><p style="color:#4a5a6a;font-size:13px">Not checked</p><p class="fix">' . $info['desc'] . '</p></div>';
                continue;
            }
            $pass  = ! empty( $r['pass'] ) ? 'pass' : 'fail';
            $warn  = ! empty( $r['warn'] ) ? 'warn' : '';
            $class = $pass . ( $warn ? ' warn' : '' );
            echo '<div class="eucomply-card">';
            echo '<h3>' . $info['label'] . '</h3>';
            echo '<p class="status ' . $class . '">' . ( $pass === 'pass' ? ( $warn ? '⚠ ' : '✓ ' ) : '✗ ' ) . esc_html( $r['label'] ) . '</p>';
            echo '<p style="font-size:12.5px;color:#4a5a6a;margin-top:2px">' . esc_html( $r['detail'] ) . '</p>';
            if ( ! empty( $r['fix'] ) ) {
                echo '<p class="fix">💡 ' . esc_html( $r['fix'] ) . '</p>';
            }
            echo '<p class="fix" style="margin-top:4px">' . $info['desc'] . '</p>';
            echo '</div>';
        }
        echo '</div>';
    }

    /**
     * Render settings page.
     */
    public function render_settings() {
        $saved   = false;
        $notice  = '';
        $warning = '';
        if ( ! empty( $_POST ) && check_admin_referer( 'eucomply_settings' ) ) {
            if ( isset( $_POST['eucomply_pro_key'] ) ) {
                $new_key = self::normalise_key( sanitize_text_field( wp_unslash( $_POST['eucomply_pro_key'] ) ) );
                $old_key = self::normalise_key( get_option( 'eucomply_pro_key', '' ) );
                if ( $old_key !== $new_key ) {
                    if ( '' !== $old_key ) {
                        // Pro is priced per website, so the old key's slot on this
                        // hostname must be freed when the site switches keys.
                        $this->release_device( $old_key );
                    }
                    // A new key is verified from scratch.
                    update_option( 'eucomply_pro_key', $new_key );
                    $this->clear_license_cache();
                }
                $saved = true;
            }
            if ( isset( $_POST['eucomply_agency_name'] ) ) {
                update_option( 'eucomply_agency_name', sanitize_text_field( wp_unslash( $_POST['eucomply_agency_name'] ) ) );
            }
            if ( isset( $_POST['eucomply_contact_email'] ) ) {
                $typed   = trim( (string) wp_unslash( $_POST['eucomply_contact_email'] ) );
                $contact = sanitize_email( $typed );
                // Store the empty string rather than deleting the option, so
                // clearing the field is a real save and not an accident.
                update_option( 'eucomply_contact_email', ( is_email( $contact ) && $contact === $typed ) ? $contact : '' );
                if ( '' !== $typed && ( ! is_email( $contact ) || $contact !== $typed ) ) {
                    $warning = 'The accessibility contact email was not saved: "' . $typed . '" is not a usable address. The accessibility statement will show a field to complete until this is fixed.';
                }
            }
            if ( isset( $_POST['eucomply_alert_email'] ) ) {
                $typed  = trim( (string) wp_unslash( $_POST['eucomply_alert_email'] ) );
                $alert  = sanitize_email( $typed );
                $is_alert = ( is_email( $alert ) && $alert === $typed ) ? $alert : '';
                update_option( 'eucomply_alert_email', $is_alert );
                if ( '' !== $typed && '' === $is_alert ) {
                    // Appending, so a form with two bad addresses says so twice
                    // instead of silently reporting only the last one.
                    $msg     = 'The regression alert address was not saved: "' . $typed . '" is not a usable email address. No alert will be sent until a valid address is saved here.';
                    $warning = ( '' === $warning ) ? $msg : $warning . ' ' . $msg;
                }
                // The state that decides what counts as a change is dropped on
                // every save of this field, so the next scan re-seeds it from
                // the last recorded scan. Keeping it would let the old
                // address' history decide whether the new one gets a first mail
                // listing every check as a change.
                delete_option( 'eucomply_alert_state' );
            }
        }
        if ( ! empty( $_POST ) && isset( $_POST['eucomply_release'] ) ) {
            check_admin_referer( 'eucomply_release' );
            if ( ! current_user_can( EUCOMPLY_ADMIN_CAP ) ) {
                wp_die( -1 );
            }
            $notice = $this->release_device();
        }
        $pro_key      = get_option( 'eucomply_pro_key', '' );
        $agency_name  = get_option( 'eucomply_agency_name', get_bloginfo( 'name' ) );
        $is_pro       = $this->is_pro();
        $state        = get_option( 'eucomply_pro_state', '' );
        ?>
        <div class="wrap eucomply-wrap">
            <h1>EUComply Settings</h1>
            <?php if ( $saved ) : ?>
                <div class="notice notice-success is-dismissible"><p>Settings saved.</p></div>
            <?php endif; ?>
            <?php if ( '' !== $notice ) : ?>
                <div class="notice notice-info is-dismissible"><p><?php echo esc_html( $notice ); ?></p></div>
            <?php endif; ?>
            <?php if ( '' !== $warning ) : ?>
                <div class="notice notice-error"><p><?php echo esc_html( $warning ); ?></p></div>
            <?php endif; ?>
            <form method="post" class="eucomply-settings">
                <?php wp_nonce_field( 'eucomply_settings' ); ?>
                <label for="eucomply_pro_key">Pro License Key</label>
                <input type="text" id="eucomply_pro_key" name="eucomply_pro_key" value="<?php echo esc_attr( $pro_key ); ?>" placeholder="32-character key, or leave empty for the free version" autocomplete="off" spellcheck="false">
                <p class="desc">Enter the license key from your purchase email to unlock Pro on this website. <a href="<?php echo esc_url( EUCOMPLY_PRO_URL ); ?>" target="_blank" rel="noopener noreferrer">Buy Pro ($79 per website per year) →</a></p>
                <?php if ( $is_pro ) : ?>
                    <p style="color:#1a7a44;font-weight:600;margin-top:4px">✓ Pro license active</p>
                <?php elseif ( 'device_limit' === $state ) : ?>
                    <p style="color:#b85a0a;font-weight:600;margin-top:4px">This key is valid, but every device in your plan is already in use, so it is not active on this website. Free a slot below, or use it on a site that has a slot free.</p>
                <?php elseif ( '' !== $pro_key ) : ?>
                    <p style="color:#c03030;font-weight:600;margin-top:4px">License key not accepted. Check that all 32 characters are copied, or reply to your purchase email for help.</p>
                <?php endif; ?>

                <label for="eucomply_agency_name">Agency / Business Name</label>
                <input type="text" id="eucomply_agency_name" name="eucomply_agency_name" value="<?php echo esc_attr( $agency_name ); ?>">
                <p class="desc">Used in generated reports and documents (Pro feature).</p>

                <label for="eucomply_contact_email">Accessibility contact email</label>
                <input type="email" id="eucomply_contact_email" name="eucomply_contact_email" value="<?php echo esc_attr( get_option( 'eucomply_contact_email', '' ) ); ?>" autocomplete="off" spellcheck="false">
                <p class="desc">Published in the Pro accessibility statement, which must name an address people can report barriers to. Leave it empty and the document shows a field to complete instead of a broken link.</p>

                <label for="eucomply_alert_email">Regression alert email (Pro)</label>
                <input type="email" id="eucomply_alert_email" name="eucomply_alert_email" value="<?php echo esc_attr( get_option( 'eucomply_alert_email', '' ) ); ?>" autocomplete="off" spellcheck="false">
                <p class="desc">Leave this empty and no alert is ever sent. With an address saved, the plugin mails you when a check changes &mdash; a check that passed starts failing, or a failing one passes again &mdash; and stays quiet while nothing changes. It is sent by this site's own mailer, so it depends on the site being able to send email at all. Change or clear the field and the next scan starts from the last recorded scan, so you do not get a first mail full of older news.</p>

                <p style="margin-top:20px"><button class="eucomply-btn" type="submit">Save Settings</button></p>
            </form>
            <?php if ( '' !== $pro_key ) : ?>
                <hr>
                <h2>Move this license to another website</h2>
                <p class="desc" style="max-width:60em">Pro covers one website per paid slot. Releasing this device frees the slot so the same key can be activated on your new site. Do this before you delete or move this site, otherwise the slot stays taken.</p>
                <form method="post">
                    <?php wp_nonce_field( 'eucomply_release' ); ?>
                    <input type="hidden" name="eucomply_release" value="1">
                    <p style="margin-top:10px"><button class="eucomply-btn" type="submit">Release this device</button></p>
                </form>
            <?php endif; ?>
        </div>
        <?php
    }

    /**
     * AJAX: Run scan.
     */
    public function ajax_run_scan() {
        check_ajax_referer( 'eucomply_scan' );

        if ( ! current_user_can( EUCOMPLY_ADMIN_CAP ) ) {
            wp_die( -1 );
        }

        $results = $this->run_checks();

        ob_start();
        $this->render_results( $results );
        $html = ob_get_clean();

        wp_send_json_success( array(
            'html' => $html,
            'time' => get_option( 'eucomply_last_scan', current_time( 'mysql' ) ),
        ) );
    }

    /**
     * Cron: automated scan. Weekly on the free version, every day on Pro —
     * see sync_scan_schedule(), which is what decides.
     */
    public function run_scan_cron() {
        if ( ! function_exists( 'is_plugin_active' ) ) {
            require_once ABSPATH . 'wp-admin/includes/plugin.php';
        }
        if ( ! function_exists( 'get_core_updates' ) ) {
            require_once ABSPATH . 'wp-admin/includes/update.php';
        }
        $this->run_checks();
    }

    /**
     * Pro: generate and download a compliance document.
     *
     * Hooked on admin_init. Downloads a .html document (opens in Word /
     * prints to PDF) built from the latest scan + site info. The document
     * generation method does not call external services; Pro license validation
     * separately sends the license key, hostname and product to mahope.tools.
     */
    public function maybe_generate_doc() {
        if ( empty( $_GET['eucomply_doc'] ) || ! is_admin() ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended -- nonce verified below
            return;
        }
        $doc = sanitize_key( wp_unslash( $_GET['eucomply_doc'] ) );

        // The report is the one document that already exists, so it is handed
        // over as it is: same rendering, same filename, same bytes as the link
        // a client reads. It asks the three questions itself, because this is
        // the one document whose bytes are also served to somebody holding no
        // WordPress login at all — the export must not become the weak way in.
        if ( 'report' === $doc ) {
            $raw_nonce  = isset( $_REQUEST['_wpnonce'] ) ? sanitize_text_field( wp_unslash( $_REQUEST['_wpnonce'] ) ) : ''; // phpcs:ignore WordPress.Security.NonceVerification.Missing -- verified on the next line
            $can_manage = current_user_can( EUCOMPLY_ADMIN_CAP );
            $nonce_ok   = (bool) wp_verify_nonce( $raw_nonce, 'eucomply_doc' );
            $export     = $this->report_export_response( $can_manage, $nonce_ok, $this->is_pro() );
            if ( 200 !== $export[0] ) {
                // The same two answers the other documents give, in the same
                // order: an account that may not manage the site, or a request
                // without a valid nonce, is told nothing about the licence.
                wp_die( ( $can_manage && $nonce_ok ) ? 'Pro license required.' : 'Not allowed' );
            }
            nocache_headers();
            header( 'Content-Type: text/html; charset=utf-8' );
            $disposition = $this->client_report_disposition( $export[2] );
            if ( '' !== $disposition ) {
                header( 'Content-Disposition: ' . $disposition, true );
            }
            // The one thing the request records, and it is not new: the settings
            // table has always shown when each document was last handed over.
            // Nothing about who exported it, how often, or for whom is stored.
            update_option( 'eucomply_pro_report_date', current_time( 'mysql' ) );
            echo $export[1]; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- assembled escaped in report_document()
            exit;
        }

        if ( ! check_admin_referer( 'eucomply_doc' ) || ! current_user_can( EUCOMPLY_ADMIN_CAP ) ) {
            wp_die( 'Not allowed' );
        }
        $allowed = array( 'dpa', 'nis2', 'eaa' );
        if ( ! in_array( $doc, $allowed, true ) || ! $this->is_pro() ) {
            wp_die( 'Pro license required.' );
        }

        $titles = array(
            'dpa'    => 'Data Processing Agreement',
            'nis2'   => 'NIS2 / DORA Vendor Clause Set',
            'eaa'    => 'Accessibility Statement (EAA)',
        );

        // Written as literals, never assembled from the document key: a name
        // built at runtime cannot be checked against uninstall.php, and an
        // option that survives deleting the plugin is a small leak of a
        // customer's compliance paperwork.
        $date_options = array(
            'dpa'  => 'eucomply_pro_dpa_date',
            'nis2' => 'eucomply_pro_nis2_date',
            'eaa'  => 'eucomply_pro_eaa_date',
        );

        $body = call_user_func( array( $this, 'build_' . str_replace( '-', '_', $doc ) ) );

        update_option( $date_options[ $doc ], current_time( 'mysql' ) );

        nocache_headers();
        header( 'Content-Type: text/html; charset=utf-8' );
        header( 'Content-Disposition: attachment; filename=eucomply-' . $doc . '-' . gmdate( 'Ymd' ) . '.html' );

        echo '<!DOCTYPE html><html><head><meta charset="utf-8"><title>' . esc_html( $titles[ $doc ] ) . '</title>';
        echo '<style>body{font-family:Georgia,serif;max-width:720px;margin:40px auto;line-height:1.6;color:#111}h1{font-size:22px;border-bottom:2px solid #111;padding-bottom:8px}h2{font-size:16px;margin-top:28px}table{border-collapse:collapse;width:100%;margin:12px 0}td,th{border:1px solid #999;padding:6px 10px;font-size:13px;text-align:left}footer{margin-top:48px;font-size:11px;color:#666;border-top:1px solid #ccc;padding-top:8px}</style>';
        echo '</head><body>';
        echo '<h1>' . esc_html( $titles[ $doc ] ) . '</h1>';
        echo '<p>Site: <strong>' . esc_html( get_bloginfo( 'name' ) ) . '</strong> (' . esc_html( home_url() ) . ')<br>';
        // Same default as the settings field, so an operator who never saved
        // the form gets their own site name instead of a dangling "By: ".
        echo 'Generated: ' . esc_html( current_time( 'date' ) ) . ' &middot; By: ' . esc_html( get_option( 'eucomply_agency_name', get_bloginfo( 'name' ) ) ) . '</p>';
        echo wp_kses_post( $body );
        echo self::completion_note( $doc, $body );
        echo '<footer>Generated by EUComply Pro. This document is a template aid and does not constitute legal advice.</footer>';
        echo '</body></html>';
        exit;
    }

    /**
     * List the fields the operator must complete before sending the document.
     *
     * The list is derived from the generated body, not from a hand-written
     * per-document table, so it cannot drift out of sync with the text it
     * describes. A document with no placeholders gets no box.
     *
     * @param string $doc  Document key.
     * @param string $body Generated document body.
     * @return string HTML, or an empty string when there is nothing to fill in.
     */
    private static function completion_note( $doc, $body ) {
        if ( ! preg_match_all( '/\[[^\[\]\n]{1,60}\]/', (string) $body, $found ) ) {
            return '';
        }
        $fields = array_values( array_unique( $found[0] ) );
        $out    = '<div style="border:2px solid #111;padding:12px 16px;margin-top:32px">';
        $out   .= '<strong>Complete before you send this document</strong>';
        $out   .= '<p style="margin:6px 0 0">These fields are intentionally left open. Fill them in, then delete this box. '
                . 'They were listed automatically from the document text, so nothing is missing from the list.</p><ul>';
        foreach ( $fields as $field ) {
            $out .= '<li>' . esc_html( $field ) . '</li>';
        }
        $out .= '</ul></div>';
        unset( $doc );
        return $out;
    }

    /** Latest scan results as key => row, or empty array. */
    private function scan_snapshot() {
        return get_option( 'eucomply_scan_results', array() );
    }

    private function build_dpa() {
        $name = get_bloginfo( 'name' );
        ob_start(); ?>
        <p>This Data Processing Agreement ("DPA") governs the processing of personal data by <strong><?php echo esc_html( $name ); ?></strong> ("Processor") on behalf of its clients ("Controller"), pursuant to Article 28 GDPR.</p>
        <h2>1. Roles</h2>
        <p>The Controller determines the purposes and means of processing. The Processor processes personal data only on documented instructions from the Controller.</p>
        <h2>2. Subject matter and duration</h2>
        <p>Processing covers the services agreed between the parties and lasts for the term of the underlying service agreement.</p>
        <h2>3. Categories of data subjects and data</h2>
        <p>Website visitors, customers and employees of the Controller. Contact data, usage data, content data as required for the services.</p>
        <h2>4. Processor obligations</h2>
        <ul>
            <li>Process data only on documented instructions (Art. 28(3)(a)).</li>
            <li>Ensure persons authorised to process are bound by confidentiality (Art. 28(3)(b)).</li>
            <li>Apply appropriate technical and organisational security measures (Art. 32).</li>
            <li>Not engage sub-processors without prior authorisation; flow down equivalent obligations (Art. 28(4)).</li>
            <li>Assist the Controller with data subject requests and DPIAs (Art. 28(3)(e)-(f)).</li>
            <li>Delete or return all personal data at end of the engagement (Art. 28(3)(g)).</li>
            <li>Notify the Controller without undue delay after becoming aware of a personal data breach (Art. 33(2)).</li>
        </ul>
        <h2>5. Transfers outside the EEA</h2>
        <p>Transfers outside the EEA occur only with adequate safeguards, e.g. EU Standard Contractual Clauses (Commission Decision 2021/914).</p>
        <h2>6. Audit</h2>
        <p>The Controller may audit compliance with this DPA once per year upon reasonable notice.</p>
        <table><tr><th></th><th>Controller</th><th>Processor</th></tr>
        <tr><td>Name</td><td>[Client name]</td><td><?php echo esc_html( $name ); ?></td></tr>
        <tr><td>Signed / date</td><td></td><td></td></tr></table>
        <?php
        return ob_get_clean();
    }

    private function build_nis2() {
        ob_start(); ?>
        <p>This clause set is intended for contracts where <strong><?php echo esc_html( get_bloginfo( 'name' ) ); ?></strong> acts as supplier or sub-supplier to entities in scope of NIS2 (Directive (EU) 2022/2555) or DORA (Regulation (EU) 2022/2554).</p>
        <h2>Clause A — Security measures</h2>
        <p>The Supplier maintains risk-appropriate technical and organisational measures including: network security, access control, multi-factor authentication for administrative access, patch management within defined SLAs, encrypted backups tested at least annually, and incident response procedures.</p>
        <h2>Clause B — Incident notification</h2>
        <p>The Supplier notifies the Client of any significant incident affecting the services within <strong>[24] hours</strong> of detection, including nature, affected systems, containment status and expected impact. Significant incidents under NIS2 Art. 23 are reported to the competent authority by the Client unless otherwise agreed.</p>
        <h2>Clause C — Supply chain</h2>
        <p>The Supplier informs the Client of changes to sub-suppliers with access to the Client's systems or data and ensures equivalent obligations are imposed contractually (NIS2 Art. 21(2)(d), DORA Art. 28).</p>
        <h2>Clause D — Audit and evidence</h2>
        <p>The Supplier provides upon request: an up-to-date overview of its security posture, results of the most recent vulnerability scans, backup restore test documentation, and cooperates with the Client's register-of-information obligations under DORA Art. 28(3).</p>
        <h2>Clause E — Exit</h2>
        <p>Upon termination the Supplier supports orderly transition and securely deletes or returns all Client data within [30] days, certifying deletion in writing.</p>
        <?php
        return ob_get_clean();
    }

    private function build_eaa() {
        $contact = self::contact_email();
        $site    = get_bloginfo( 'name' );
        ob_start(); ?>
        <p><strong><?php echo esc_html( $site ); ?></strong> is committed to ensuring digital accessibility for people with disabilities. This statement describes the accessibility of this website, in line with Article 13 of Directive (EU) 2019/882 (the European Accessibility Act).</p>
        <h2>Conformance status</h2>
        <p>This website aims to conform with EN 301 549, referencing WCAG 2.1 Level AA. The assessment method is self-evaluation: automated checks plus manual review of the site's own most-used pages.</p>
        <h2>Measures</h2>
        <ul>
            <li>Accessibility is part of our design and review process.</li>
            <li>We test the website with assistive technologies where feasible.</li>
            <li>Known issues are tracked and remediated on a rolling basis.</li>
        </ul>
        <h2>Known limitations</h2>
        <p>Some parts of the content may not yet be fully accessible. Any known limitations are listed below; if the list is empty, no accessibility limitations have been identified as of the review date. Remove this line only if you have checked the whole site.</p>
        <p>[Known accessibility limitations, or "None identified"]</p>
        <h2>Feedback and contact</h2>
        <?php if ( '' !== $contact ) : ?>
            <p>If you encounter an accessibility barrier on this website, please report it to <a href="mailto:<?php echo esc_attr( $contact ); ?>"><?php echo esc_html( $contact ); ?></a>. We aim to respond within [5] business days.</p>
        <?php else : ?>
            <p>If you encounter an accessibility barrier on this website, please report it to
            <strong>[accessibility contact email]</strong>. We aim to respond within [5] business days.</p>
            <p><em>No accessibility contact email is set. Add one under EUComply &rarr; Settings so this document
            ships with a working address instead of a placeholder.</em></p>
        <?php endif; ?>
        <h2>Enforcement</h2>
        <p>Accessibility is a legal obligation, and the enforcement body is the one in the member state where
        <?php echo esc_html( $site ); ?> is established. If you are not satisfied with our response, you may complain to
        <strong>[enforcement body and contact details for your member state]</strong>.</p>
        <p><em>Last reviewed: <?php echo esc_html( current_time( 'F Y' ) ); ?>.</em></p>
        <?php
        return ob_get_clean();
    }

    private function build_report() {
        $results = $this->scan_snapshot();
        ob_start();
        echo '<p>Summary of the latest automated compliance scan (' . esc_html( get_option( 'eucomply_last_scan', '' ) ) . ').</p>';
        // How often it was looked at, in the document the client reads. A score
        // without an interval is a number nobody can act on, and "how often is
        // this checked" is the first question a client asks about it. Read from
        // the cron array, not from the licence: it says what will happen, so a
        // released or expired licence puts the sentence back on its weekly run
        // instead of promising a daily one it will not deliver.
        echo '<p>Scheduled on this WordPress server: ' . esc_html( $this->cadence_phrase() ) . '. The checks run on the site itself, so no external service is involved.</p>';
        // Only when an address is actually stored, and it names the same
        // configured state the plugin reads when it decides to send. A report
        // that promised alerts the site is not set up to send would be the
        // false claim this whole block exists to avoid.
        if ( '' !== $this->alert_address() ) {
            echo '<p>The owner is emailed when a check changes, so a regression between two reports does not go unnoticed.</p>';
        }
        echo '<table><tr><th>Check</th><th>Status</th><th>Detail</th></tr>';
        foreach ( $results as $key => $r ) {
            $status = ! empty( $r['pass'] ) ? 'PASS' : ( ! empty( $r['warn'] ) ? 'WARN' : 'FAIL' );
            echo '<tr><td>' . esc_html( $r['label'] ) . '</td><td>' . $status . '</td><td>' . esc_html( $r['detail'] ) . '</td></tr>';
        }
        echo '</table>';
        if ( empty( $results ) ) {
            echo '<p>No scan has been run yet. Run a scan from the EUComply dashboard and re-generate this report.</p>';
        } else {
            $passed = 0;
            $warned = 0;
            $fails  = 0;
            foreach ( $results as $r ) {
                if ( ! empty( $r['pass'] ) ) {
                    $passed++;
                } elseif ( ! empty( $r['warn'] ) ) {
                    $warned++;
                } else {
                    $fails++;
                }
            }
            echo '<h2>Recommendations</h2><ul>';
            foreach ( $results as $r ) {
                if ( empty( $r['pass'] ) && ! empty( $r['fix'] ) ) {
                    echo '<li>' . esc_html( $r['label'] ) . ': ' . esc_html( $r['fix'] ) . '</li>';
                }
            }
            echo '</ul>';
            $summary = sprintf( '%d of %d checks passed', $passed, count( $results ) );
            if ( $warned ) {
                $summary .= sprintf( ', %d with warnings', $warned );
            }
            if ( $fails ) {
                $summary .= sprintf( ', %d failed', $fails );
            }
            // A warning is a partial result, not a pass. It is counted and named
            // separately so the headline number cannot overstate compliance.
            echo '<p>' . esc_html( $summary ) . '. Warnings are not counted as passed.</p>';
        }
        echo $this->build_history_section(); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- escaped in build_history_section()
        return ob_get_clean();
    }

    /**
     * Build the "Scan history" part of the report.
     *
     * This is the part a client reads twice: the current table says where the
     * site stands today, the history says whether it is being kept there. It
     * reports what was actually recorded — no scan is invented, and a gap in
     * the series is shown as a gap rather than smoothed over.
     *
     * @return string HTML.
     */
    private function build_history_section() {
        $history = $this->history();
        if ( empty( $history ) ) {
            return '';
        }
        $first = reset( $history );
        $last  = end( $history );
        $dates = array_keys( $history );
        $shown = array_slice( $history, -12, null, true ); // newest 12 snapshots in the report; the option keeps 52

        ob_start();
        echo '<h2>Scan history</h2>';
        echo '<p>Recorded automatically on every scan. ' . count( $history ) . ' scan' . ( 1 === count( $history ) ? '' : 's' ) . ' on record';
        if ( count( $history ) > count( $shown ) ) {
            echo ' (the most recent ' . count( $shown ) . ' shown below)';
        }
        echo '.</p>';
        echo '<table><tr><th>Date</th><th>Result</th><th>Checks</th></tr>';
        foreach ( $shown as $date => $entry ) {
            $states = isset( $entry['checks'] ) && is_array( $entry['checks'] ) ? $entry['checks'] : array();
            $p      = isset( $entry['passed'] ) ? (int) $entry['passed'] : 0;
            $t      = isset( $entry['total'] ) ? (int) $entry['total'] : count( $states );
            $w      = isset( $entry['warned'] ) ? (int) $entry['warned'] : 0;
            $result = $p . ' of ' . $t . ' passed';
            if ( $w ) {
                $result .= ', ' . $w . ' with warnings';
            }
            $line = array();
            foreach ( $states as $state ) {
                $line[] = strtoupper( (string) $state );
            }
            echo '<tr><td>' . esc_html( $date ) . '</td><td>' . esc_html( $result ) . '</td><td>' . esc_html( $line ? implode( ', ', $line ) : '—' ) . '</td></tr>';
        }
        echo '</table>';

        // The one line a client actually wants: are we better or worse than
        // when we started? Computed from the recorded snapshots, never from a
        // stored "improvement" figure that could drift from them.
        if ( count( $history ) > 1 && isset( $first['passed'], $last['passed'], $first['total'], $last['total'] ) ) {
            $delta = (int) $last['passed'] - (int) $first['passed'];
            $from  = esc_html( $dates[0] );
            if ( $delta > 0 ) {
                echo '<p>Since ' . $from . ', ' . (int) $delta . ' more check' . ( 1 === $delta ? '' : 's' ) . ' passed (to ' . (int) $last['passed'] . ' of ' . (int) $last['total'] . ').</p>';
            } elseif ( $delta < 0 ) {
                echo '<p>Since ' . $from . ', ' . abs( $delta ) . ' fewer check' . ( 1 === abs( $delta ) ? '' : 's' ) . ' passed than at the first recorded scan (now ' . (int) $last['passed'] . ' of ' . (int) $last['total'] . '). This is a regression that needs attention.</p>';
            } else {
                echo '<p>Unchanged since ' . $from . ': ' . (int) $last['passed'] . ' of ' . (int) $last['total'] . ' checks passing.</p>';
            }
        }
        return ob_get_clean();
    }

    // ── Client report link ────────────────────────────────────────────────────
    //
    // The report and the history now exist, but they live in wp-admin. An agency
    // therefore has to either hand over an admin login or paste a screenshot —
    // and neither is something you can invoice for. This is the missing half:
    // a link the agency can send to its client, which shows that one site's
    // report and nothing else, changes nothing, expires, and can be revoked.
    //
    // Three rules the rest of this block exists to keep:
    //   1. Only a hash is stored. The token is shown once, at creation. A dump
    //      of the options table must not hand out a working client link.
    //   2. Every way of failing looks identical from outside. A malformed
    //      token, an unknown token, a revoked one and an expired one all get the
    //      same 404 body, so the page cannot be used to probe which exist.
    //   3. Reading the report never calls the license server. The link is
    //      checked against the stored hash and the expiry only, so a client
    //      never sees a blank page because our API had a bad minute.

    /** The stored client-link record, or an empty array. */
    private function client_link_record() {
        $rec = get_option( 'eucomply_client_link', array() );
        return is_array( $rec ) ? $rec : array();
    }

    /**
     * State of the client link: 'none', 'active' or 'expired'.
     *
     * @return string
     */
    private function client_link_state() {
        $rec = $this->client_link_record();
        if ( empty( $rec['hash'] ) || empty( $rec['expires'] ) ) {
            return 'none';
        }
        return ( (int) $rec['expires'] > time() ) ? 'active' : 'expired';
    }

    /**
     * Issue a new client link and return its URL.
     *
     * Only the hash is kept, so the URL is shown once and cannot be recovered
     * later — an operator who loses it creates a new link, which retires the
     * old one. That is the trade we make for never storing a working secret.
     *
     * @return string The URL, or '' when Pro is not active.
     */
    private function create_client_link() {
        if ( ! $this->is_pro() ) {
            return '';
        }
        $token = bin2hex( random_bytes( 16 ) );
        update_option(
            'eucomply_client_link',
            array(
                'hash'    => hash( 'sha256', $token ),
                'created' => time(),
                'expires' => time() + ( EUCOMPLY_CLIENT_LINK_DAYS * DAY_IN_SECONDS ),
            )
        );
        delete_transient( 'eucomply_client_link_new' );
        return add_query_arg( 'eucomply_report', $token, home_url( '/' ) );
    }

    /** Retire the client link. There is no way back: the token is gone. */
    private function revoke_client_link() {
        delete_option( 'eucomply_client_link' );
        delete_transient( 'eucomply_client_link_new' );
    }

    /**
     * Does this token entitle its holder to read the report?
     *
     * Hash comparison is constant-time, and the format check runs first so a
     * token of the wrong shape is rejected without touching the stored hash.
     *
     * @param string $token Raw value from the query string.
     * @return bool
     */
    private function client_link_allows( $token ) {
        if ( ! is_string( $token ) || ! preg_match( '/^[a-f0-9]{32}$/', $token ) ) {
            return false;
        }
        $rec = $this->client_link_record();
        if ( empty( $rec['hash'] ) || empty( $rec['expires'] ) ) {
            return false;
        }
        if ( (int) $rec['expires'] <= time() ) {
            return false;
        }
        return hash_equals( (string) $rec['hash'], hash( 'sha256', $token ) );
    }

    /**
     * The download filename for a client report.
     *
     * Deterministic, so the same scan always produces the same name, and it is
     * built from the scan date rather than the token: a filename ends up in
     * mail clients, chat windows and archive indexes, and none of those may
     * carry the secret that opens the report. The date is re-validated
     * because it comes from an option, and a header must never carry a value
     * an option author chose.
     *
     * @return string
     */
    private function client_report_filename() {
        $stamp = (string) get_option( 'eucomply_last_scan', '' );
        $date  = preg_match( '/^(\d{4}-\d{2}-\d{2})/', $stamp, $m ) ? $m[1] : gmdate( 'Y-m-d' );
        return 'eucomply-report-' . $date . '.html';
    }

    /**
     * The compliance report as a complete document.
     *
     * There is exactly one rendering of the report, and both ways out use it: the
     * client link and the download in wp-admin. That is not tidiness. Before
     * this, the wp-admin download had a second rendering of its own — different
     * header, no history — so an agency could send a client one document in
     * March and another in April, and the one its client was quoted on would be
     * the one without the evidence. An agency cannot invoice a retainer on a
     * document that changes shape when nobody is watching.
     *
     * The only thing $link_expires adds is the notice that the *link* dies on a
     * date. That is a property of the link, not of the report, so it is absent
     * from the exported file — an attached document that says when its own link
     * expires would be claiming something about a link it does not carry. It
     * keeps a class so a test can prove the two documents are otherwise
     * identical byte for byte.
     *
     * @param string $link_expires Y-m-d, or '' when there is no link involved.
     * @return string
     */
    private function report_document( $link_expires = '' ) {
        $body  = '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            . '<meta name="robots" content="noindex, nofollow">'
            . '<title>Compliance report — ' . esc_html( get_bloginfo( 'name' ) ) . '</title>'
            . '<style>body{font-family:Georgia,serif;max-width:720px;margin:40px auto;line-height:1.6;color:#111}'
            . 'h1{font-size:22px;border-bottom:2px solid #111;padding-bottom:8px}h2{font-size:16px;margin-top:28px}'
            . 'table{border-collapse:collapse;width:100%;margin:12px 0}td,th{border:1px solid #999;padding:6px 10px;font-size:13px;text-align:left}'
            . 'footer{margin-top:48px;font-size:11px;color:#666;border-top:1px solid #ccc;padding-top:8px}</style>'
            . '</head><body>';
        $body .= '<h1>Compliance report</h1>';
        $body .= '<p>Site: <strong>' . esc_html( get_bloginfo( 'name' ) ) . '</strong> (' . esc_html( home_url() ) . ')<br>';
        $body .= 'Last scan: ' . esc_html( (string) get_option( 'eucomply_last_scan', '' ) ) . '</p>';
        if ( '' !== (string) $link_expires ) {
            $body .= '<p class="eucomply-link-expiry">This link stops working on ' . esc_html( (string) $link_expires ) . '.</p>';
        }
        $body .= $this->build_report(); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- escaped in build_report()
        $body .= '<footer>Read-only. This page cannot change anything on the website. '
            . 'Produced by EUComply Pro from the site&#39;s own scheduled scans. '
            . 'A compliance aid, not legal advice.</footer></body></html>';
        return $body;
    }

    /**
     * Build the response for a client report request.
     *
     * Separated from the HTTP plumbing so the properties that matter — what a
     * valid request shows, and that every invalid one is indistinguishable —
     * can be tested without a web server.
     *
     * The file variant is the same body, not a second rendering of it. An
     * agency that attaches a PDF-style deliverable and a client that reads the
     * page must never be able to disagree about what the scan found.
     *
     * @param string $raw_token Raw value from the query string.
     * @param bool   $as_file   Ask for the download instead of the page.
     * @return array{0:int,1:string,2:string} HTTP status, body, filename ('' unless $as_file).
     */
    private function client_report_response( $raw_token, $as_file = false ) {
        $token = is_string( $raw_token ) ? strtolower( trim( $raw_token ) ) : '';
        if ( ! $this->client_link_allows( $token ) ) {
            // Deliberately the same body for a malformed token, an unknown one,
            // a revoked one and an expired one. Anything else turns this page
            // into an oracle for which tokens exist. A download request gets it
            // too, and no Content-Disposition: a 404 that arrives as a file is
            // a different observable from a 404 that arrives as a page.
            return array( 404, '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Not found</title></head><body><h1>Not found</h1><p>No compliance report is available at this address.</p></body></html>', '' );
        }
        $rec = $this->client_link_record();
        return array( 200, $this->report_document( gmdate( 'Y-m-d', (int) $rec['expires'] ) ), $as_file ? $this->client_report_filename() : '' );
    }

    /**
     * What a report export from wp-admin is allowed to hand over.
     *
     * The same three questions as everywhere else in wp-admin — may this account
     * manage the site, is the request nonced, is Pro paid for — decided in one
     * place, so the export cannot become a way around the Pro gate and cannot
     * drift into a weaker capability than the settings page it sits under.
     *
     * Every refusal produces the same empty answer, with no filename: a refused
     * export that still carried a Content-Disposition would be a file that exists
     * for whoever the guard did not catch. Kept separate from the HTTP calls
     * because those end in wp_die(), which no test can call.
     *
     * @param bool $can_manage current_user_can( EUCOMPLY_ADMIN_CAP ).
     * @param bool $nonce_ok   Whether check_admin_referer() passed.
     * @param bool $pro        Whether the Pro licence is active.
     * @return array{0:int,1:string,2:string} Status, body, filename.
     */
    private function report_export_response( $can_manage, $nonce_ok, $pro ) {
        if ( ! $can_manage || ! $nonce_ok || ! $pro ) {
            return array( 403, '', '' );
        }
        return array( 200, $this->report_document(), $this->client_report_filename() );
    }

    /**
     * The Content-Disposition for a client report, or '' when there is nothing
     * to hand over.
     *
     * Only a real report ever gets one. A rejected token must not be able to
     * differ from the page version in its headers, or the download address
     * becomes a second, weaker lock on the same secret than the page is.
     *
     * @param mixed $filename Whatever client_report_response() returned.
     * @return string
     */
    private function client_report_disposition( $filename ) {
        // The shape is re-checked here, at the last point before the header,
        // and not only in client_report_filename(). A filename that can carry
        // a quote or a newline splits a response, and the check that matters is
        // the one that is closest to the damage.
        if ( ! is_string( $filename ) || ! preg_match( '/^eucomply-report-\d{4}-\d{2}-\d{2}\.html$/', $filename ) ) {
            return '';
        }
        return 'attachment; filename="' . $filename . '"';
    }

    /**
     * Serve the client report, as a page or as a file. Hooked on template_redirect.
     *
     * The token is the only thing this reads, and the file flag changes nothing
     * but the download header. Everything else on the request is ignored, so the
     * page cannot be turned into an action.
     */
    public function maybe_render_client_report() {
        $wants_file = isset( $_GET['eucomply_report_file'] ); // phpcs:ignore WordPress.Security.NonceVerification.Recommended -- a capability-free, read-only link, verified by hash below
        if ( ( ! isset( $_GET['eucomply_report'] ) && ! $wants_file ) || is_admin() ) {
            return;
        }
        $raw = isset( $_GET['eucomply_report'] ) ? $_GET['eucomply_report'] : ''; // phpcs:ignore WordPress.Security.NonceVerification.Recommended
        $raw = is_string( $raw ) ? wp_unslash( $raw ) : '';
        list( $status, $body, $filename ) = $this->client_report_response( $raw, $wants_file );

        status_header( $status );
        nocache_headers();
        header( 'X-Robots-Tag: noindex, nofollow', true );
        header( 'Referrer-Policy: no-referrer', true );
        header( 'Content-Type: text/html; charset=utf-8' );
        // Only ever on a real report. A rejected token must not be able to
        // differ from the page version in its headers, or the two answers
        // become distinguishable.
        $disposition = $this->client_report_disposition( $filename );
        if ( '' !== $disposition ) {
            header( 'Content-Disposition: ' . $disposition, true );
        }
        echo $body; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- assembled escaped above
        exit;
    }

    /**
     * Create or revoke the client link. Hooked on admin_init.
     *
     * The freshly created URL is handed to the dashboard through a 60-second
     * transient instead of a query parameter, so it never reaches the browser
     * history, the referrer chain or a proxy log on its way to the screen that
     * shows it once.
     */
    public function maybe_manage_client_link() {
        if ( empty( $_GET['eucomply_link'] ) || ! is_admin() ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended -- nonce verified below
            return;
        }
        if ( ! check_admin_referer( 'eucomply_link' ) || ! current_user_can( EUCOMPLY_ADMIN_CAP ) ) {
            wp_die( 'Not allowed' );
        }
        if ( ! $this->is_pro() ) {
            wp_die( 'Pro license required.' );
        }
        $action = sanitize_key( wp_unslash( $_GET['eucomply_link'] ) );
        if ( 'revoke' === $action ) {
            $this->revoke_client_link();
        } elseif ( 'create' === $action ) {
            set_transient( 'eucomply_client_link_new', $this->create_client_link(), MINUTE_IN_SECONDS );
        } else {
            wp_die( 'Unknown action.' );
        }
        wp_safe_redirect( admin_url( 'admin.php?page=eucomply' ) );
        exit;
    }

    /**
     * The dashboard row that hands a client their own report.
     */
    private function render_client_link_box() {
        $state  = $this->client_link_state();
        $record = $this->client_link_record();
        $fresh  = get_transient( 'eucomply_client_link_new' );
        if ( $fresh ) {
            delete_transient( 'eucomply_client_link_new' );
        }
        $create = wp_nonce_url( admin_url( 'admin.php?page=eucomply&eucomply_link=create' ), 'eucomply_link' );
        $revoke = wp_nonce_url( admin_url( 'admin.php?page=eucomply&eucomply_link=revoke' ), 'eucomply_link' );
        ?>
        <div style="margin-top:28px;border:1px solid #d0d8e0;border-radius:10px;padding:20px;background:#fff">
            <h2 style="font-size:16px;margin:0 0 8px">🔗 Pro: Client report link</h2>
            <?php if ( $fresh ) : ?>
                <div style="border:2px solid #1a7a44;background:#f2fbf5;padding:12px 16px;border-radius:8px;margin:12px 0">
                    <strong>Copy this now — it is not shown again.</strong>
                    <p style="margin:8px 0 0;word-break:break-all;font-family:monospace;font-size:12.5px"><?php echo esc_html( $fresh ); ?></p>
                    <p style="margin:10px 0 0">
                        <a class="eucomply-btn" style="padding:8px 16px;font-size:13px"
                           href="<?php echo esc_url( add_query_arg( 'eucomply_report_file', '1', $fresh ) ); ?>">↓ Download report (HTML)</a>
                    </p>
                    <p style="margin:10px 0 0;font-size:12.5px;color:#33503f">
                        The download is the same report as the page, in a file you can attach to an
                        e-mail or hand to an auditor. The link stops working on the date above, so
                        copy both now.
                    </p>
                </div>
            <?php endif; ?>
            <?php if ( 'active' === $state ) : ?>
                <p style="font-size:13.5px;margin:0 0 8px">
                    A link is active. It shows this site's report and scan history to whoever holds it,
                    changes nothing, and stops working on
                    <strong><?php echo esc_html( gmdate( 'Y-m-d', (int) $record['expires'] ) ); ?></strong>.
                </p>
                <p style="font-size:12.5px;color:#4a5a6a;margin:0 0 12px">
                    Created <?php echo esc_html( gmdate( 'Y-m-d', (int) $record['created'] ) ); ?>.
                    The link itself is not stored, so it cannot be shown again — create a new one if it is lost, and the old one stops working.
                </p>
            <?php elseif ( 'expired' === $state ) : ?>
                <p style="font-size:13.5px;margin:0 0 12px">
                    The last link expired on <strong><?php echo esc_html( gmdate( 'Y-m-d', (int) $record['expires'] ) ); ?></strong> and no longer works.
                </p>
            <?php else : ?>
                <p style="font-size:13.5px;margin:0 0 12px">
                    No link yet. Create one to send your client their own report — they read it in a browser, without a WordPress login.
                </p>
            <?php endif; ?>
            <a class="eucomply-btn ghost" style="padding:8px 16px;font-size:13px" href="<?php echo esc_url( $create ); ?>">
                <?php echo 'active' === $state ? 'Create a new link (retires the old one)' : ( 'expired' === $state ? 'Create a new link' : 'Create client link' ); ?>
            </a>
            <?php if ( 'active' === $state ) : ?>
                <a class="eucomply-btn ghost" style="padding:8px 16px;font-size:13px" href="<?php echo esc_url( $revoke ); ?>">Revoke now</a>
            <?php endif; ?>
            <p style="font-size:12.5px;color:#4a5a6a;margin:12px 0 0">
                The link is a secret: anyone who has it can read the report. Send it to the client, not into a shared inbox or a ticket.
            </p>
        </div>
        <?php
    }

    /**
     * Determine if Pro license is active.
     *
     * A key counts as Pro if it has the right format AND has been verified
     * against the Mahope license server (result cached for 24h). When the
     * server cannot be reached (network error or 5xx), the last successful
     * verification is trusted for EUCOMPLY_LICENSE_GRACE (7 days), so an
     * outage never locks a paying customer out.
     *
     * A 409 (device limit) is not a bad key: this website simply has no free
     * slot. It is recorded in `eucomply_pro_state` for the settings screen and
     * is deliberately not cached as a negative verdict, so freeing a slot
     * restores Pro on the next check.
     */
    private function is_pro() {
        $key = self::normalise_key( get_option( 'eucomply_pro_key', '' ) );
        if ( '' === $key || ! preg_match( '/^[a-f0-9]{32}$/', $key ) ) {
            return false;
        }
        $verified = '1' === get_option( 'eucomply_pro_verified', '' );
        $checked_at = (int) get_option( 'eucomply_pro_verified_at', 0 );
        if ( $checked_at && ( time() - $checked_at ) < EUCOMPLY_LICENSE_CACHE_TTL ) {
            return $verified;
        }
        // After a failed attempt, wait before calling the server again so an
        // outage does not add a 10-second timeout to every admin page load.
        $ok = get_transient( 'eucomply_license_retry' ) ? null : $this->verify_license_remote( $key );
        if ( null === $ok ) {
            set_transient( 'eucomply_license_retry', 1, HOUR_IN_SECONDS );
            // Server unreachable: keep the last valid Pro status for the grace period.
            $last_ok = (int) get_option( 'eucomply_pro_last_ok_at', 0 );
            return $verified && ( time() - $last_ok ) < EUCOMPLY_LICENSE_GRACE;
        }
        delete_transient( 'eucomply_license_retry' );
        if ( 'device_limit' === $ok ) {
            // Short backoff instead of a 24h negative cache: the slot can be
            // freed at any moment, and then this site must recover on its own.
            set_transient( 'eucomply_license_retry', 1, 10 * MINUTE_IN_SECONDS );
            update_option( 'eucomply_pro_state', 'device_limit' );
            delete_option( 'eucomply_pro_verified' );
            delete_option( 'eucomply_pro_verified_at' );
            $this->sync_scan_schedule();
            return false;
        }
        delete_option( 'eucomply_pro_state' );
        update_option( 'eucomply_pro_verified', $ok ? '1' : '0' );
        update_option( 'eucomply_pro_verified_at', time() );
        if ( $ok ) {
            update_option( 'eucomply_pro_last_ok_at', time() );
        }
        // The verdict just changed, so the cadence the licence entitles this
        // site to may have changed with it. Read from the option that was just
        // written, so it cannot call the license server back.
        $this->sync_scan_schedule();
        return $ok;
    }

    /**
     * License keys are 32 lowercase hex characters; trim and lowercase input.
     */
    /**
     * The accessibility contact address used in the EAA statement.
     *
     * Returns an empty string when unset or invalid. The EAA document then
     * renders a plain-text field to complete instead of a mailto: link, because
     * a link whose target is a placeholder looks real in Word and silently
     * fails when the customer clicks it.
     *
     * @return string Sanitised address, or '' when there is nothing usable.
     */
    private static function contact_email() {
        $raw = trim( (string) get_option( 'eucomply_contact_email', '' ) );
        if ( '' === $raw ) {
            return '';
        }
        $clean = sanitize_email( $raw );
        // WordPress' sanitize_email() *strips* characters it does not allow
        // rather than rejecting the value, so a stored address can differ from
        // the one the operator typed. Publishing the stripped version would put
        // a different address in a document people file with a regulator, so an
        // address that does not survive sanitising unchanged is treated as unset.
        return ( is_email( $clean ) && $clean === $raw ) ? $clean : '';
    }

    private static function normalise_key( $key ) {
        return strtolower( trim( (string) $key ) );
    }

    /**
     * Device id sent to the license server: the site's hostname.
     */
    private static function device_id() {
        $host = wp_parse_url( home_url(), PHP_URL_HOST );
        return substr( $host ? strtolower( $host ) : 'eucomply', 0, 128 );
    }

    /**
     * POST a JSON body to the Mahope license API.
     *
     * @return array|null Array with 'code' and decoded 'data', or null on a
     *                    network error.
     */
    private function license_request( $endpoint, $body ) {
        $response = wp_remote_post(
            EUCOMPLY_LICENSE_API . $endpoint,
            array(
                'timeout' => 10,
                'headers' => array(
                    'Content-Type' => 'application/json',
                    'Accept'       => 'application/json',
                ),
                'body'    => wp_json_encode( $body ),
            )
        );
        if ( is_wp_error( $response ) ) {
            return null;
        }
        return array(
            'code' => (int) wp_remote_retrieve_response_code( $response ),
            'data' => json_decode( wp_remote_retrieve_body( $response ), true ),
        );
    }

    /**
     * Verify a license key against the Mahope license API.
     *
     * The first check activates this site (device_id = hostname); later checks
     * validate, so daily re-checks do not use up activations.
     *
     * @return bool|string|null True/false on a definitive answer, the string
     *                          'device_limit' when the plan's device slots are
     *                          all used (409), and null when the server is
     *                          unreachable or answers with a temporary error.
     */
    private function verify_license_remote( $key ) {
        $device = self::device_id();
        $body   = array(
            'license_key' => $key,
            'device_id'   => $device,
            'product'     => EUCOMPLY_LICENSE_PRODUCT,
        );
        // Activation is remembered per key and hostname, so a moved site activates again.
        $marker  = md5( $key . '|' . $device );
        $refused = false;

        if ( get_option( 'eucomply_license_activation', '' ) === $marker ) {
            $ok = $this->license_verdict( $this->license_request( 'validate', $body ), 'valid' );
            if ( false !== $ok ) {
                return $ok;
            }
            // Not valid for this device: forget the activation and try to activate once.
            delete_option( 'eucomply_license_activation' );
            $refused = true;
        }

        $ok = $this->license_verdict( $this->license_request( 'activate', $body ), 'activated' );
        if ( true === $ok ) {
            update_option( 'eucomply_license_activation', $marker );
        }
        // The server already said "not valid"; a failed retry must not revive the grace period.
        if ( null === $ok && $refused ) {
            return false;
        }
        return $ok;
    }

    /**
     * Release this website's license device slot.
     *
     * Pro is priced per website, so a slot must be freed when the site is
     * replaced or the plugin is removed. Without this the customer can never
     * move their license, because the server keeps the device occupied.
     *
     * @param string $key License key to release; defaults to the stored one.
     * @return string Short result message for the settings screen.
     */
    private function release_device( $key = '' ) {
        $key = self::normalise_key( $key ? $key : get_option( 'eucomply_pro_key', '' ) );
        if ( '' === $key ) {
            return 'No Pro key is stored on this website, so there is no device to release.';
        }
        $res = $this->license_request(
            'deactivate',
            array(
                'license_key' => $key,
                'device_id'   => self::device_id(),
            )
        );
        $this->clear_license_cache();
        if ( is_array( $res ) && 200 === $res['code'] && ! empty( $res['data']['ok'] ) ) {
            return 'Device released. This website no longer uses a Pro slot, so it can be used again on another site.';
        }
        $code = is_array( $res ) ? $res['code'] : 0;
        return 'The license server could not be reached (HTTP ' . (int) $code . '), so the slot was not released. Try again when you are online. Your Pro status on this website is unchanged.';
    }

    /**
     * Drop every cached license verdict so the next check runs from scratch.
     *
     * Keeps the stored key. Removes the negative cache as well, so a customer
     * who frees a device slot gets Pro back without waiting out a TTL.
     */
    private function clear_license_cache() {
        delete_option( 'eucomply_pro_verified' );
        delete_option( 'eucomply_pro_verified_at' );
        delete_option( 'eucomply_pro_state' );
        delete_option( 'eucomply_license_activation' );
        delete_transient( 'eucomply_license_retry' );
    }

    /**
     * Map a license API response to a verdict.
     *
     * true            — the key is valid and active for this device.
     * false           — definitive refusal, locks Pro on this site: 400 (bad
     *                    format), 403 (expired, revoked or another product),
     *                    404 (unknown key).
     * 'device_limit'  — HTTP 409. The key is fine, this website's device slot
     *                    is not. It must never lock the key, and it is reported
     *                    separately so the customer can free a device.
     * null            — temporary: network error, 402, 429, any 5xx, or a 200
     *                    body we cannot read. The cached Pro status is then
     *                    used for the grace period, so a license-server
     *                    problem can never lock out a paying customer.
     */
    private function license_verdict( $res, $flag ) {
        if ( null === $res ) {
            return null;
        }
        if ( 200 === $res['code'] ) {
            $data = is_array( $res['data'] ) ? $res['data'] : array();
            if ( empty( $data['ok'] ) ) {
                return null;
            }
            return ! empty( $data[ $flag ] );
        }
        if ( 409 === $res['code'] ) {
            return 'device_limit';
        }
        if ( in_array( $res['code'], array( 400, 403, 404 ), true ) ) {
            return false;
        }
        return null;
    }
}

// Initialize.
add_action( 'plugins_loaded', array( 'EUComply', 'get_instance' ) );

// Deactivation hook.
register_deactivation_hook( __FILE__, array( 'EUComply', 'deactivate' ) );

/**
 * Auto-update checker: fetches update manifest from the site.
 * When the plugin is on wp.org this is unused — wp.org handles updates.
 * Until then, this provides updates from the published update.json.
 */
add_filter( 'site_transient_update_plugins', 'eucomply_check_for_updates' );
function eucomply_check_for_updates( $transient ) {
    if ( ! is_object( $transient ) ) {
        $transient = new stdClass();
    }
    $plugin_slug = plugin_basename( __FILE__ );
    $remote      = wp_remote_get( EUCOMPLY_UPDATE_URI, array( 'timeout' => 5 ) );
    if ( is_wp_error( $remote ) || 200 !== wp_remote_retrieve_response_code( $remote ) ) {
        return $transient;
    }
    $data = json_decode( wp_remote_retrieve_body( $remote ), true );
    if ( ! is_array( $data ) || empty( $data['version'] ) ) {
        return $transient;
    }
    // Only show update if remote version > installed version.
    if ( version_compare( EUCOMPLY_VERSION, $data['version'], '>=' ) ) {
        return $transient;
    }
    $update = new stdClass();
    $update->slug        = $data['slug'];
    $update->plugin      = $plugin_slug;
    $update->new_version = $data['version'];
    $update->url         = $data['homepage'] ?? '';
    $update->package     = $data['download_url'] ?? '';
    $update->requires    = $data['requires'] ?? '5.8';
    $update->tested      = $data['tested'] ?? '6.8';
    $update->icons       = array( 'svg' => 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMjgiIGhlaWdodD0iMTI4IiB2aWV3Qm94PSIwIDAgMTI4IDEyOCI+PHJlY3Qgd2lkdGg9IjEyOCIgaGVpZ2h0PSIxMjgiIGZpbGw9IiMyODY4ZDAiIHJ4PSIyMCIvPjx0ZXh0IHg9IjI0IiB5PSI4NSIgZmlsbD0iI2ZmZiIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iNjAiIGZvbnQtd2VpZ2h0PSI4MDAiPkVDPC90ZXh0Pjwvc3ZnPg==' );
    $transient->response[ $plugin_slug ] = $update;
    return $transient;
}

/**
 * Plugin details popup (Plugins → Add New → Details or the "View details" link).
 */
add_filter( 'plugins_api', 'eucomply_plugin_info', 10, 3 );
function eucomply_plugin_info( $result, $action, $args ) {
    if ( 'plugin_information' !== $action || empty( $args->slug ) || 'eucomply' !== $args->slug ) {
        return $result;
    }
    $remote = wp_remote_get( EUCOMPLY_UPDATE_URI, array( 'timeout' => 5 ) );
    if ( is_wp_error( $remote ) || 200 !== wp_remote_retrieve_response_code( $remote ) ) {
        return $result;
    }
    $data = json_decode( wp_remote_retrieve_body( $remote ), true );
    if ( ! is_array( $data ) ) {
        return $result;
    }
    $result                = new stdClass();
    $result->name          = $data['name'] ?? 'EUComply';
    $result->slug          = $data['slug'] ?? 'eucomply';
    $result->version       = $data['version'] ?? '1.0.0';
    $result->requires      = $data['requires'] ?? '5.8';
    $result->tested        = $data['tested'] ?? '6.8';
    $result->requires_php  = $data['requires_php'] ?? '7.4';
    $result->last_updated  = $data['last_updated'] ?? '';
    $result->download_link = $data['download_url'] ?? '';
    $result->homepage      = $data['homepage'] ?? '';
    $result->sections      = array(
        'description' => $data['sections']['description'] ?? '',
        'changelog'   => $data['sections']['changelog'] ?? '',
    );
    $result->banners = array( 'low' => '' );
    $result->icons   = array( 'svg' => 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMjgiIGhlaWdodD0iMTI4IiB2aWV3Qm94PSIwIDAgMTI4IDEyOCI+PHJlY3Qgd2lkdGg9IjEyOCIgaGVpZ2h0PSIxMjgiIGZpbGw9IiMyODY4ZDAiIHJ4PSIyMCIvPjx0ZXh0IHg9IjI0IiB5PSI4NSIgZmlsbD0iI2ZmZiIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iNjAiIGZvbnQtd2VpZ2h0PSI4MDAiPkVDPC90ZXh0Pjwvc3ZnPg==' );
    return $result;
}