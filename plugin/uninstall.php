<?php
/**
 * EUComply — Uninstall Cleanup
 *
 * Fires when the plugin is deleted via wp-admin → Plugins → Delete.
 * Removes all stored options, transients, and unschedules cron events.
 *
 * @package EUComply
 */

// If uninstall is not called by WordPress, die.
if ( ! defined( 'WP_UNINSTALL_PLUGIN' ) ) {
    exit;
}

// ── Release the Pro device slot ──────────────────────────────────────────────
// Pro is sold per website, so deleting the plugin must free this site's slot —
// otherwise the customer cannot activate the same key on their new site. This
// is best-effort: a failure here must not block the uninstall.
$eucomply_key = strtolower( trim( (string) get_option( 'eucomply_pro_key', '' ) ) );
if ( '' !== $eucomply_key ) {
    $eucomply_host = wp_parse_url( home_url(), PHP_URL_HOST );
    $eucomply_res  = wp_remote_post(
        'https://mahope.tools/api/license/deactivate',
        array(
            'timeout' => 10,
            'headers' => array(
                'Content-Type' => 'application/json',
                'Accept'       => 'application/json',
            ),
            'body'    => wp_json_encode(
                array(
                    'license_key' => $eucomply_key,
                    'device_id'   => substr( $eucomply_host ? strtolower( $eucomply_host ) : 'eucomply', 0, 128 ),
                )
            ),
        )
    );
    unset( $eucomply_res, $eucomply_host, $eucomply_key );
}

// ── Options to remove ────────────────────────────────────────────────────────
$options = array(
    'eucomply_scan_results',
    'eucomply_scan_history',
    'eucomply_last_scan',
    'eucomply_pro_key',
    'eucomply_pro_verified',
    'eucomply_pro_verified_at',
    'eucomply_pro_last_ok_at',
    'eucomply_pro_state',
    'eucomply_license_activation',
    'eucomply_ls_instance_id',
    'eucomply_agency_name',
    'eucomply_contact_email',
    'eucomply_pro_dpa_date',
    'eucomply_pro_nis2_date',
    'eucomply_pro_eaa_date',
    'eucomply_pro_report_date',
);

foreach ( $options as $option ) {
    delete_option( $option );
    // For sites in a multisite network, also delete site-level.
    delete_site_option( $option );
}

delete_transient( 'eucomply_license_retry' );

// ── Unschedule the weekly scan cron ──────────────────────────────────────────
$timestamp = wp_next_scheduled( 'eucomply_weekly_scan' );
if ( $timestamp ) {
    wp_unschedule_event( $timestamp, 'eucomply_weekly_scan' );
}

// ── Clear any user meta (license key pre-fill) ──────────────────────────────
// None stored in user meta for v1.1.0 — future-proofing comment.