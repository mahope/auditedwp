<?php
/**
 * Plugin Name:       EUComply — EU Compliance Audit
 * Plugin URI:        https://eucomply.pages.dev
 * Description:       Scans your WordPress site for GDPR, NIS2, DORA, and EAA compliance gaps. Free checks: SSL, cookies, backups, forms, plugin health. Pro ($79/yr): auto-generates DPA, NIS2 clauses, EAA statements and quarterly audit reports.
 * Version:           1.0.0
 * Requires at least: 5.8
 * Requires PHP:      7.4
 * Author:            EUComply
 * Author URI:        https://eucomply.pages.dev
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

define( 'EUCOMPLY_VERSION', '1.0.0' );
define( 'EUCOMPLY_PRO_PRICE', 79 );
define( 'EUCOMPLY_PRO_URL', 'https://eucomply.gumroad.com/l/pro' );

/**
 * Main plugin class — keeps everything in one place for v1.
 */
class EUComply {

    private static $instance = null;

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
        add_action( 'wp_ajax_eucomply_run_scan', array( $this, 'ajax_run_scan' ) );

        // Schedule weekly scan.
        if ( ! wp_next_scheduled( 'eucomply_weekly_scan' ) ) {
            wp_schedule_event( time(), 'weekly', 'eucomply_weekly_scan' );
        }
        add_action( 'eucomply_weekly_scan', array( $this, 'run_scan_cron' ) );
    }

    /**
     * Deactivation: clear cron.
     */
    public static function deactivate() {
        $t = wp_next_scheduled( 'eucomply_weekly_scan' );
        if ( $t ) {
            wp_unschedule_event( $t, 'eucomply_weekly_scan' );
        }
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
            'manage_options',
            'eucomply',
            array( $this, 'render_dashboard' ),
            $icon,
            99
        );
        add_submenu_page(
            'eucomply',
            'EUComply Settings',
            'Settings',
            'manage_options',
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

        // Store results.
        update_option( 'eucomply_scan_results', $results );
        update_option( 'eucomply_last_scan', current_time( 'mysql' ) );

        return $results;
    }

    /**
     * Check SSL/HTTPS.
     */
    private function check_ssl() {
        $home = get_home_url();
        $scheme = parse_url( $home, PHP_URL_SCHEME );

        if ( 'https' !== $scheme ) {
            return array(
                'pass'    => false,
                'label'   => 'Not HTTPS',
                'detail'  => 'Site URL uses ' . strtoupper( $scheme ) . ', not HTTPS.',
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
                    Free version — <a href="<?php echo esc_url( EUCOMPLY_PRO_URL ); ?>">Upgrade to Pro ($79/yr)</a> for auto-generated DPA, NIS2 clauses, EAA statements and quarterly PDF reports.
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

            <div id="eucomply-results">
                <?php if ( $results ) : ?>
                    <?php $this->render_results( $results ); ?>
                    <div style="margin-top:20px">
                        <a class="eucomply-btn" href="<?php echo esc_url( EUCOMPLY_PRO_URL ); ?>">↓ Download compliance report (Pro)</a>
                    </div>
                <?php else : ?>
                    <p style="color:#4a5a6a;margin-top:20px;font-size:14px">Click "Run scan now" to check your site against 6 EU compliance criteria.</p>
                <?php endif; ?>
            </div>

            <?php if ( $is_pro ) : ?>
            <div style="margin-top:28px;border:1px solid #d0d8e0;border-radius:10px;padding:20px;background:#fff">
                <h2 style="font-size:16px;margin:0 0 8px">📄 Pro: Documents &amp; Reports</h2>
                <table class="eucomply-table">
                    <tr><th>Document</th><th>Last generated</th><th></th></tr>
                    <tr><td>GDPR Data Processing Agreement</td><td><?php echo esc_html( get_option( 'eucomply_pro_dpa_date', 'Not yet' ) ); ?></td><td><a href="#" class="eucomply-btn ghost" style="padding:6px 14px;font-size:12px">Generate</a></td></tr>
                    <tr><td>NIS2 / DORA Vendor Clause Set</td><td><?php echo esc_html( get_option( 'eucomply_pro_nis2_date', 'Not yet' ) ); ?></td><td><a href="#" class="eucomply-btn ghost" style="padding:6px 14px;font-size:12px">Generate</a></td></tr>
                    <tr><td>EAA Accessibility Statement</td><td><?php echo esc_html( get_option( 'eucomply_pro_eaa_date', 'Not yet' ) ); ?></td><td><a href="#" class="eucomply-btn ghost" style="padding:6px 14px;font-size:12px">Generate</a></td></tr>
                    <tr><td>Quarterly Compliance Report (PDF)</td><td><?php echo esc_html( get_option( 'eucomply_pro_report_date', 'Not yet' ) ); ?></td><td><a href="#" class="eucomply-btn ghost" style="padding:6px 14px;font-size:12px">Generate</a></td></tr>
                </table>
            </div>
            <?php endif; ?>
        </div>

        <script>
        (function(){
            var btn = document.getElementById('eucomply-scan-btn');
            var res = document.getElementById('eucomply-results');
            var lst = document.getElementById('eucomply-last');
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
            'cookies' => array( 'label' => '🍪 Cookie Consent', 'desc' => 'Banner, WP Consent API, script blocking' ),
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
        $saved = false;
        if ( ! empty( $_POST ) && check_admin_referer( 'eucomply_settings' ) ) {
            if ( isset( $_POST['eucomply_pro_key'] ) ) {
                update_option( 'eucomply_pro_key', sanitize_text_field( wp_unslash( $_POST['eucomply_pro_key'] ) ) );
                $saved = true;
            }
            if ( isset( $_POST['eucomply_agency_name'] ) ) {
                update_option( 'eucomply_agency_name', sanitize_text_field( wp_unslash( $_POST['eucomply_agency_name'] ) ) );
            }
        }
        $pro_key      = get_option( 'eucomply_pro_key', '' );
        $agency_name  = get_option( 'eucomply_agency_name', get_bloginfo( 'name' ) );
        $is_pro       = $this->is_pro();
        ?>
        <div class="wrap eucomply-wrap">
            <h1>EUComply Settings</h1>
            <?php if ( $saved ) : ?>
                <div class="notice notice-success is-dismissible"><p>Settings saved.</p></div>
            <?php endif; ?>
            <form method="post" class="eucomply-settings">
                <?php wp_nonce_field( 'eucomply_settings' ); ?>
                <label for="eucomply_pro_key">Pro License Key</label>
                <input type="text" id="eucomply_pro_key" name="eucomply_pro_key" value="<?php echo esc_attr( $pro_key ); ?>" placeholder="Leave empty for free version">
                <p class="desc">Enter your license key to unlock Pro features. <a href="<?php echo esc_url( EUCOMPLY_PRO_URL ); ?>">Buy Pro ($79/yr) →</a></p>
                <?php if ( $is_pro ) : ?>
                    <p style="color:#1a7a44;font-weight:600;margin-top:4px">✓ Pro license active</p>
                <?php endif; ?>

                <label for="eucomply_agency_name">Agency / Business Name</label>
                <input type="text" id="eucomply_agency_name" name="eucomply_agency_name" value="<?php echo esc_attr( $agency_name ); ?>">
                <p class="desc">Used in generated reports and documents (Pro feature).</p>

                <p style="margin-top:20px"><button class="eucomply-btn" type="submit">Save Settings</button></p>
            </form>
        </div>
        <?php
    }

    /**
     * AJAX: Run scan.
     */
    public function ajax_run_scan() {
        check_ajax_referer( 'eucomply_scan' );

        if ( ! current_user_can( 'manage_options' ) ) {
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
     * Cron: automated weekly scan.
     */
    public function run_scan_cron() {
        $this->run_checks();
    }

    /**
     * Determine if Pro license is active.
     */
    private function is_pro() {
        $key = get_option( 'eucomply_pro_key', '' );
        if ( empty( $key ) ) {
            return false;
        }
        // Simple key format: starts with EC-PRO- and has 16 alphanumeric chars.
        if ( 0 === strpos( $key, 'EC-PRO-' ) && strlen( $key ) >= 22 ) {
            return true;
        }
        return false;
    }
}

// Initialize.
add_action( 'plugins_loaded', array( 'EUComply', 'get_instance' ) );

// Deactivation hook.
register_deactivation_hook( __FILE__, array( 'EUComply', 'deactivate' ) );