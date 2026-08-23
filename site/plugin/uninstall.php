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

// ── Options to remove ────────────────────────────────────────────────────────
$options = array(
    'eucomply_scan_results',
    'eucomply_last_scan',
    'eucomply_pro_key',
    'eucomply_pro_verified',
    'eucomply_pro_verified_at',
    'eucomply_agency_name',
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

// ── Unschedule the weekly scan cron ──────────────────────────────────────────
$timestamp = wp_next_scheduled( 'eucomply_weekly_scan' );
if ( $timestamp ) {
    wp_unschedule_event( $timestamp, 'eucomply_weekly_scan' );
}

// ── Clear any user meta (license key pre-fill) ──────────────────────────────
// None stored in user meta for v1.1.0 — future-proofing comment.