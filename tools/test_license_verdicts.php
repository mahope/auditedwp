<?php
/**
 * EUComply — license verdict regression tests.
 *
 * Covers the mapping from a Mahope license-server response to a Pro verdict,
 * the 7-day offline grace, and the "release this device" call. The cases come
 * from docs/eucomply-pro-spec.md section 3.3-3.5.
 *
 * Run: php tools/test_license_verdicts.php
 *
 * @package EUComply
 */

// ── Minimal WordPress stubs ──────────────────────────────────────────────────
define( 'ABSPATH', __DIR__ );
define( 'MINUTE_IN_SECONDS', 60 );
define( 'HOUR_IN_SECONDS', 3600 );
define( 'DAY_IN_SECONDS', 86400 );
define( 'ARRAY_A', 'ARRAY_A' );

$GLOBALS['eucomply_test_options']    = array();
$GLOBALS['eucomply_test_transients'] = array();
$GLOBALS['eucomply_test_http']       = array(); // Scripted wp_remote_post responses.
$GLOBALS['eucomply_test_calls']      = array(); // Recorded wp_remote_post calls.

function add_action() {}
function add_filter() {}
function register_activation_hook() {}
function register_deactivation_hook() {}

// The license verdict and the scheduled interval are the same decision read
// twice, so is_pro() re-syncs the schedule. These stubs keep that out of this
// file's way: the interval logic is covered by tools/test_pro_documents.php.
$GLOBALS['eucomply_test_cron'] = array();
function wp_schedule_event( $timestamp, $schedule, $hook ) {
    $GLOBALS['eucomply_test_cron'][] = array( 'timestamp' => (int) $timestamp, 'schedule' => $schedule, 'hook' => $hook );
    return true;
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
    $GLOBALS['eucomply_test_cron'] = array();
    return true;
}

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
    return $GLOBALS['eucomply_test_transients'][ $name ] ?? false;
}
function set_transient( $name, $value, $ttl = 0 ) {
    $GLOBALS['eucomply_test_transients'][ $name ] = $value;
    return true;
}
function delete_transient( $name ) {
    unset( $GLOBALS['eucomply_test_transients'][ $name ] );
    return true;
}
function home_url() {
    return 'https://agency-client.example';
}
function wp_parse_url( $url, $component = -1 ) {
    return parse_url( $url, $component );
}
function wp_json_encode( $data ) {
    return json_encode( $data );
}
function is_wp_error( $thing ) {
    return $thing instanceof WP_Error_Stub;
}
class WP_Error_Stub {
    public function __construct() {}
}
function wp_remote_retrieve_response_code( $response ) {
    return $response['response']['code'] ?? 0;
}
function wp_remote_retrieve_body( $response ) {
    return $response['body'] ?? '';
}

/**
 * Queue one scripted HTTP answer, or a WP_Error for a network failure.
 */
function eucomply_test_script( $code, $body = array() ) {
    if ( 'network-error' === $code ) {
        $GLOBALS['eucomply_test_http'][] = new WP_Error_Stub();
        return;
    }
    $GLOBALS['eucomply_test_http'][] = array(
        'response' => array( 'code' => $code ),
        'body'     => is_string( $body ) ? $body : json_encode( $body ),
    );
}
function wp_remote_post( $url, $args ) {
    $GLOBALS['eucomply_test_calls'][] = array( 'url' => $url, 'body' => json_decode( $args['body'], true ) );
    return array_shift( $GLOBALS['eucomply_test_http'] );
}

require_once __DIR__ . '/../plugin/eucomply.php';

// ── Tiny test harness ─────────────────────────────────────────────────────────
$passed = 0;
$failed = 0;
function ok( $label, $condition ) {
    global $passed, $failed;
    if ( $condition ) {
        $passed++;
        return;
    }
    $failed++;
    echo "FAIL: $label\n";
}
/**
 * Invoke a private method. PHP 8.1+ needs no setAccessible(), and calling it
 * here keeps the production code free of test-only visibility changes.
 */
function priv( $name, ...$args ) {
    global $ref, $g;
    return $ref->getMethod( $name )->invoke( $g, ...$args );
}
function verdict( $res, $flag = 'activated' ) {
    return priv( 'license_verdict', $res, $flag );
}

/** Fresh instance with an empty store and no constructor side effects. */
function fresh_instance( $key = 'a1b2c3d4e5f60718293a4b5c6d7e8f90' ) {
    $GLOBALS['eucomply_test_options']    = array();
    $GLOBALS['eucomply_test_transients'] = array();
    $GLOBALS['eucomply_test_http']       = array();
    $GLOBALS['eucomply_test_calls']      = array();
    if ( null !== $key ) {
        $GLOBALS['eucomply_test_options']['eucomply_pro_key'] = $key;
    }
    $GLOBALS['ref'] = new ReflectionClass( 'EUComply' );
    $GLOBALS['g']   = $GLOBALS['ref']->newInstanceWithoutConstructor();
    return $GLOBALS['g'];
}
function is_pro() {
    return priv( 'is_pro' );
}

// ── 3.3 Response-to-verdict mapping ───────────────────────────────────────────
$obj = fresh_instance();

// Pass.
eucomply_test_script( 200, array( 'ok' => true, 'activated' => true ) );
ok( '200 ok+activated is a pass', true === verdict( priv( 'license_request', 'activate', array() ), 'activated' ) );
eucomply_test_script( 200, array( 'ok' => true, 'valid' => true ) );
ok( '200 ok+valid is a pass', true === verdict( priv( 'license_request', 'validate', array() ), 'valid' ) );

// Definitive refusals lock Pro.
eucomply_test_script( 200, array( 'ok' => true, 'valid' => false ) );
ok( '200 ok+valid:false locks', false === verdict( priv( 'license_request', 'validate', array() ), 'valid' ) );
foreach ( array( 400, 403, 404 ) as $code ) {
    eucomply_test_script( $code, array( 'error' => 'no' ) );
    ok( "HTTP $code is a definitive refusal", false === verdict( priv( 'license_request', 'activate', array() ), 'activated' ) );
}

// 409 is its own verdict and must never lock the key.
eucomply_test_script( 409, array( 'error' => 'device_limit' ) );
ok( 'HTTP 409 reports device_limit', 'device_limit' === verdict( priv( 'license_request', 'activate', array() ), 'activated' ) );

// Temporary answers keep the grace period alive.
foreach ( array( 402, 429, 500, 502, 503 ) as $code ) {
    eucomply_test_script( $code, array( 'error' => 'temporary' ) );
    ok( "HTTP $code is temporary", null === verdict( priv( 'license_request', 'activate', array() ), 'activated' ) );
}
eucomply_test_script( 200, array( 'ok' => false ) );
ok( '200 ok:false is temporary', null === verdict( priv( 'license_request', 'activate', array() ), 'activated' ) );
eucomply_test_script( 200, 'not json at all' );
ok( 'unreadable 200 body is temporary', null === verdict( priv( 'license_request', 'activate', array() ), 'activated' ) );
eucomply_test_script( 'network-error' );
ok( 'network error is temporary', null === verdict( priv( 'license_request', 'activate', array() ), 'activated' ) );
ok( 'null response is temporary', null === verdict( null, 'activated' ) );

// ── is_pro(): 7-day offline grace ─────────────────────────────────────────────
fresh_instance();
$GLOBALS['eucomply_test_options']['eucomply_pro_verified']    = '1';
$GLOBALS['eucomply_test_options']['eucomply_pro_last_ok_at']  = time() - ( 2 * DAY_IN_SECONDS );
eucomply_test_script( 503 );
ok( '503 keeps Pro during the 7-day grace', true === is_pro() );
ok( '503 sets a retry backoff', (bool) get_transient( 'eucomply_license_retry' ) );

fresh_instance();
$GLOBALS['eucomply_test_options']['eucomply_pro_verified']   = '1';
$GLOBALS['eucomply_test_options']['eucomply_pro_last_ok_at'] = time() - ( 8 * DAY_IN_SECONDS );
eucomply_test_script( 503 );
ok( '503 after 7 days does not keep Pro', false === is_pro() );

fresh_instance();
$GLOBALS['eucomply_test_options']['eucomply_pro_verified']   = '1';
$GLOBALS['eucomply_test_options']['eucomply_pro_last_ok_at'] = time() - ( 2 * DAY_IN_SECONDS );
eucomply_test_script( 429 );
ok( '429 keeps Pro during the grace period', true === is_pro() );

// A never-verified key must not get grace from an outage.
fresh_instance();
eucomply_test_script( 503 );
ok( 'an unverified key gets no grace', false === is_pro() );

// ── is_pro(): 409 does not cache a 24-hour lock ───────────────────────────────
fresh_instance();
eucomply_test_script( 409 );
ok( '409 disables Pro on this site', false === is_pro() );
ok( '409 records the device_limit state', 'device_limit' === get_option( 'eucomply_pro_state', '' ) );
ok( '409 sets no negative cache TTL', ! get_option( 'eucomply_pro_verified_at', 0 ) );
ok( '409 uses a short backoff, not an hour', (bool) get_transient( 'eucomply_license_retry' ) );

// A slot that frees up restores Pro on the next check, with no customer action.
fresh_instance();
eucomply_test_script( 409 );
is_pro();
eucomply_test_script( 200, array( 'ok' => true, 'activated' => true ) );
delete_transient( 'eucomply_license_retry' );
ok( 'a freed slot restores Pro', true === is_pro() );
ok( 'a valid key clears the device_limit state', '' === get_option( 'eucomply_pro_state', '' ) );

// ── is_pro(): definitive refusals do cache ───────────────────────────────────
fresh_instance();
eucomply_test_script( 404 );
ok( '404 disables Pro', false === is_pro() );
ok( '404 caches a negative verdict', (int) get_option( 'eucomply_pro_verified_at' ) > 0 );
ok( '404 records no device_limit state', '' === get_option( 'eucomply_pro_state', '' ) );

// ── is_pro(): validate path and the activate retry ───────────────────────────
fresh_instance();
// A site that has already activated carries the marker, so it validates.
$GLOBALS['eucomply_test_options']['eucomply_license_activation'] = md5( 'a1b2c3d4e5f60718293a4b5c6d7e8f90|agency-client.example' );
eucomply_test_script( 200, array( 'ok' => true, 'valid' => true ) );
ok( 'an activated site validates without re-activating', true === is_pro() );
$calls = $GLOBALS['eucomply_test_calls'];
ok( 'validate is used once activated', 1 === count( $calls ) && false !== strpos( $calls[0]['url'], '/validate' ) );
ok( 'the device id is the hostname', 'agency-client.example' === $calls[0]['body']['device_id'] );
ok( 'the product is eucomply-pro', 'eucomply-pro' === $calls[0]['body']['product'] );

// A site whose device was released server-side re-activates exactly once.
fresh_instance();
$GLOBALS['eucomply_test_options']['eucomply_license_activation'] = md5( 'a1b2c3d4e5f60718293a4b5c6d7e8f90|agency-client.example' );
eucomply_test_script( 200, array( 'ok' => true, 'valid' => false ) );
eucomply_test_script( 200, array( 'ok' => true, 'activated' => true ) );
ok( 'a released device re-activates', true === is_pro() );
$calls = $GLOBALS['eucomply_test_calls'];
ok( 'the retry order is validate then activate', 2 === count( $calls )
    && false !== strpos( $calls[0]['url'], '/validate' )
    && false !== strpos( $calls[1]['url'], '/activate' ) );

// ── release_device() ─────────────────────────────────────────────────────────
fresh_instance();
eucomply_test_script( 200, array( 'ok' => true, 'deactivated' => true ) );
$msg = priv( 'release_device' );
$calls = $GLOBALS['eucomply_test_calls'];
ok( 'release_device posts to deactivate', 1 === count( $calls ) && false !== strpos( $calls[0]['url'], '/deactivate' ) );
ok( 'release_device sends the stored key', 'a1b2c3d4e5f60718293a4b5c6d7e8f90' === $calls[0]['body']['license_key'] );
ok( 'release_device sends the hostname', 'agency-client.example' === $calls[0]['body']['device_id'] );
ok( 'release_device reports success', false !== strpos( $msg, 'released' ) );
ok( 'release_device clears the negative cache', ! get_option( 'eucomply_pro_verified_at', 0 ) && ! get_transient( 'eucomply_license_retry' ) );
ok( 'release_device keeps the key for re-verification', 'a1b2c3d4e5f60718293a4b5c6d7e8f90' === get_option( 'eucomply_pro_key' ) );

// A license server that is down must not claim success.
fresh_instance();
eucomply_test_script( 503 );
$msg = priv( 'release_device' );
ok( 'a failed release is reported as failed', false !== strpos( $msg, 'could not be reached' ) );

fresh_instance( null );
$msg = priv( 'release_device' );
ok( 'release without a key makes no HTTP call', 0 === count( $GLOBALS['eucomply_test_calls'] ) );

// ── Result ───────────────────────────────────────────────────────────────────
echo "$passed license checks passed\n";
if ( $failed ) {
    echo "$failed FAILED\n";
    exit( 1 );
}
