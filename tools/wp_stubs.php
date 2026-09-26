<?php
/**
 * Minimal WordPress stubs for the EUComply test harnesses.
 *
 * Extracted from tools/test_pro_documents.php so a second harness (the plugin
 * / engine parity probe) cannot drift from the first: two harnesses that each
 * carry their own WordPress are two harnesses that can disagree about what
 * WordPress does, and then a test is green for the wrong reason.
 *
 * There are no wp_remote_* stubs here on purpose — a harness that cannot reach
 * the network cannot pass because a network happened to be up. The probe that
 * does need a front page adds its own, returning a fixture or a WP_Error.
 *
 * @package EUComply
 */


// ── Minimal WordPress stubs ──────────────────────────────────────────────────
define( 'ABSPATH', __DIR__ );
define( 'MINUTE_IN_SECONDS', 60 );
define( 'HOUR_IN_SECONDS', 3600 );
define( 'DAY_IN_SECONDS', 86400 );
define( 'WEEK_IN_SECONDS', 604800 );

$GLOBALS['eucomply_test_options'] = array();
$GLOBALS['eucomply_test_transients'] = array();
$GLOBALS['eucomply_site_name']    = 'Agency Client ApS';

function add_action() {}
function add_filter() {}
function register_activation_hook() {}
function register_deactivation_hook() {}

function get_option( $name, $default = false ) {
    return array_key_exists( $name, $GLOBALS['eucomply_test_options'] ) ? $GLOBALS['eucomply_test_options'][ $name ] : $default;
}
function update_option( $name, $value ) {
    $GLOBALS['eucomply_test_options'][ $name ] = $value;
    return true;
}
function delete_option( $name ) {
    unset( $GLOBALS['eucomply_test_options'][ $name ] );
    return true;
}
function get_transient( $name ) {
    return isset( $GLOBALS['eucomply_test_transients'][ $name ] ) ? $GLOBALS['eucomply_test_transients'][ $name ] : false;
}
function set_transient( $name, $value, $ttl = 0 ) {
    $GLOBALS['eucomply_test_transients'][ $name ] = $value;
    return true;
}
function delete_transient( $name ) {
    unset( $GLOBALS['eucomply_test_transients'][ $name ] );
    return true;
}
function add_query_arg( $key, $value, $url ) {
    return $url . ( false === strpos( $url, '?' ) ? '?' : '&' ) . rawurlencode( $key ) . '=' . rawurlencode( $value );
}
/**
 * The site's own address. A harness can move it with the `eucomply_test_home`
 * global — one place, because `check_ssl()` reads the scheme from it and
 * `front_page()` fetches from it, and two ways to spell the same site is how a
 * harness ends up testing a combination no real site has.
 */
function home_url( $path = '' ) {
    $home = isset( $GLOBALS['eucomply_test_home'] ) ? $GLOBALS['eucomply_test_home'] : 'https://agency-client.example';
    return $home . $path;
}
function get_bloginfo( $what = 'name' ) {
    return 'name' === $what ? $GLOBALS['eucomply_site_name'] : '';
}
function current_time( $type ) {
    if ( 'date' === $type ) {
        return 'September 26, 2026';
    }
    if ( 'F Y' === $type ) {
        return 'September 2026';
    }
    return '2026-09-26 02:00:00';
}
function sanitize_text_field( $s ) {
    return trim( strip_tags( (string) $s ) );
}
function sanitize_email( $s ) {
    // Mirrors WordPress: it *strips* characters it does not allow rather than
    // rejecting the value. That is why the plugin has to compare the sanitised
    // result with what was typed, or a mangled address gets published.
    $s = trim( (string) $s );
    $s = preg_replace( '/[^a-zA-Z0-9!#$%&\'*+\/=?^_`{|}~.@-]/', '', $s );
    return trim( (string) $s, " \t\n\r\0\x0B." );
}
function is_email( $s ) {
    // Structural, like WordPress: sanitising successfully is not enough —
    // "not-an-address" survives sanitising and is still not an address.
    $s = (string) $s;
    if ( ! preg_match( '/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/', $s ) ) {
        return false;
    }
    return sanitize_email( $s ) === $s ? $s : false;
}
function esc_html( $s ) {
    return htmlspecialchars( (string) $s, ENT_QUOTES, 'UTF-8' );
}
function esc_attr( $s ) {
    return esc_html( $s );
}
function esc_url( $s ) {
    return esc_html( $s );
}
function wp_kses_post( $s ) {
    return (string) $s;
}

// ── WP-Cron stubs ─────────────────────────────────────────────────────────────
// A real $wp_cron array: one entry per (timestamp, hook, schedule key), which
// is what makes wp_get_scheduled_event() and wp_clear_scheduled_hook() behave
// the way the plugin's scheduling logic assumes.
$GLOBALS['eucomply_test_cron'] = array();

function wp_schedule_event( $timestamp, $schedule, $hook ) {
    $GLOBALS['eucomply_test_cron'][] = array(
        'timestamp' => (int) $timestamp,
        'schedule'  => $schedule,
        'hook'      => $hook,
    );
    return true;
}
function wp_next_scheduled( $hook ) {
    foreach ( $GLOBALS['eucomply_test_cron'] as $event ) {
        if ( $event['hook'] === $hook ) {
            return $event['timestamp'];
        }
    }
    return false;
}
function wp_get_scheduled_event( $hook ) {
    foreach ( $GLOBALS['eucomply_test_cron'] as $event ) {
        if ( $event['hook'] === $hook ) {
            return (object) $event;
        }
    }
    return false;
}
function wp_clear_scheduled_hook( $hook ) {
    $before         = count( $GLOBALS['eucomply_test_cron'] );
    $GLOBALS['eucomply_test_cron'] = array_values(
        array_filter(
            $GLOBALS['eucomply_test_cron'],
            function ( $event ) use ( $hook ) {
                return $event['hook'] !== $hook;
            }
        )
    );
    return $before - count( $GLOBALS['eucomply_test_cron'] );
}
function wp_unschedule_event( $timestamp, $hook ) {
    return wp_clear_scheduled_hook( $hook );
}

// The regression alert is the one feature that hands a message to something
// outside the request, so the mailer is recorded rather than stubbed to
// nothing: "no mail was sent" has to be provable, not assumed. There is no
// wp_remote_* stub in this file, so nothing here can reach the network either.
function admin_url( $path = '' ) {
    return 'https://agency-client.example/wp-admin/' . ltrim( (string) $path, '/' );
}
function wp_mail( $to, $subject, $message, $headers = array() ) {
    $GLOBALS['eucomply_test_mail'][] = array(
        'to'      => $to,
        'subject' => $subject,
        'message' => $message,
        'headers' => $headers,
    );
    return empty( $GLOBALS['eucomply_test_mail_fails'] );
}
/** Every mail the plugin handed to WordPress so far. */
function sent_mail() {
    return isset( $GLOBALS['eucomply_test_mail'] ) ? $GLOBALS['eucomply_test_mail'] : array();
}


/**
 * WordPress Address (home) URL. Derived from home_url() so a harness can only
 * move both by moving one — the plugin fetches the front page through
 * get_home_url() and calls home_url() for its own User-Agent string.
 */
function get_home_url( $path = '' ) {
    return home_url( $path );
}

/**
 * WordPress' parse_url() wrapper. It is a thin layer over the native function,
 * so the stub is too — a harness that reimplemented it would be testing its own
 * URL parser instead of the plugin's.
 */
function wp_parse_url( $url, $component = -1 ) {
    return parse_url( $url, $component );
}
