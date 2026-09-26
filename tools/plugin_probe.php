<?php
/**
 * Probe: what the plugin's five front-page checks say about one fixture page.
 *
 *   php tools/plugin_probe.php <fixture.json>
 *
 * The fixture is `{ "html": "...", "headers": {…}, "error": "…" }`. The output is
 * `{ "<check key>": { "pass": bool, "warn": bool, "label": "…", "detail": "…" } }`
 * on stdout, and nothing else — a parser must be able to read it.
 *
 * Why this exists as a separate program: opgave 43 ported five check signatures
 * from `eucomply-scanner/engine/index.js` into the plugin so a WordPress customer
 * gets the same nine URL checks as the free scanner. That port was verified with
 * `php -l` and with the source/zip parity gate — both of which read the *code*,
 * and neither of which ever ran a check. A regex that compiles, lints and ships
 * can still disagree with the engine it was ported from, and then the same
 * website is "no trackers detected" in the dashboard and "3 trackers with NO
 * consent platform" on /scan/. `tools/test_plugin_engine_parity.mjs` runs this
 * probe and the JS engine over the same fixtures and requires the same verdict.
 *
 * No network: wp_remote_get() is answered from the fixture or, when the fixture
 * carries an `error`, from a WP_Error — so the "a page that cannot be read is
 * never a pass" property is testable without anything being unreachable.
 *
 * @package EUComply
 */

// Warnings and deprecations must never end up on stdout: this program's
// contract is "one line of JSON on stdout", and a parser that can be fed a
// PHP warning is a parser that will someday parse one as a result.
ini_set( 'display_errors', 'stderr' );

require_once __DIR__ . '/wp_stubs.php';

/** A WordPress error object, small enough to be honest about. */
class WP_Error {
    private $message;
    public function __construct( $code = '', $message = '' ) {
        $this->message = $message;
    }
    public function get_error_message() {
        return $this->message;
    }
}
function is_wp_error( $thing ) {
    return $thing instanceof WP_Error;
}

/** The fixture the harness answers every front-page fetch with. */
$GLOBALS['eucomply_probe_fixture'] = array(
    'html'    => '',
    'headers' => array(),
    'error'   => '',
);
/** How many times the plugin actually fetched the front page. */
$GLOBALS['eucomply_probe_fetches'] = 0;

function wp_remote_get( $url, $args = array() ) {
    $GLOBALS['eucomply_probe_fetches']++;
    $f = $GLOBALS['eucomply_probe_fixture'];
    if ( '' !== $f['error'] ) {
        return new WP_Error( 'http_request_failed', $f['error'] );
    }
    return array(
        'response' => array( 'code' => 200 ),
        'body'     => $f['html'],
        'headers'  => $f['headers'],
    );
}
function wp_remote_retrieve_response_code( $response ) {
    return isset( $response['response']['code'] ) ? $response['response']['code'] : 0;
}
function wp_remote_retrieve_body( $response ) {
    return isset( $response['body'] ) ? $response['body'] : '';
}
function wp_remote_retrieve_headers( $response ) {
    return isset( $response['headers'] ) ? $response['headers'] : array();
}

require_once __DIR__ . '/../plugin/eucomply.php';

// ── Read the fixture ──────────────────────────────────────────────────────────

$path = isset( $argv[1] ) ? $argv[1] : '';
if ( '' === $path || ! is_readable( $path ) ) {
    fwrite( STDERR, "usage: php tools/plugin_probe.php <fixture.json>\n" );
    exit( 2 );
}
$raw = json_decode( file_get_contents( $path ), true );
if ( ! is_array( $raw ) ) {
    fwrite( STDERR, "fixture is not JSON\n" );
    exit( 2 );
}
$GLOBALS['eucomply_probe_fixture'] = array(
    'html'    => isset( $raw['html'] ) ? $raw['html'] : '',
    'headers' => isset( $raw['headers'] ) ? $raw['headers'] : array(),
    'error'   => isset( $raw['error'] ) ? $raw['error'] : '',
);

/**
 * The five checks opgave 43 ported, and the private method that produces each.
 * The keys are the ones `run_checks()` writes, so a check that is renamed in one
 * place and not the other fails here instead of silently disappearing from the
 * report.
 */
$CHECKS = array(
    'consent_mode_v2' => 'check_consent_mode_v2',
    'tcf'             => 'check_tcf',
    'trackers'        => 'check_trackers',
    'headers'         => 'check_security_headers',
    'dora'            => 'check_dora',
);

$ref = new ReflectionClass( 'EUComply' );
$obj = $ref->newInstanceWithoutConstructor();

$out = array();
foreach ( $CHECKS as $key => $method ) {
    if ( ! $ref->hasMethod( $method ) ) {
        fwrite( STDERR, "plugin has no method $method\n" );
        exit( 2 );
    }
    $m = $ref->getMethod( $method );
    // setAccessible() is a no-op since PHP 8.1 and deprecated in 8.5, so it is
    // only called where it is still needed — on the PHP versions CI may run.
    if ( PHP_VERSION_ID < 80100 ) {
        $m->setAccessible( true );
    }
    $out[ $key ] = $m->invoke( $obj );
}
$out['_fetches'] = $GLOBALS['eucomply_probe_fetches'];

echo json_encode( $out, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE ), "\n";
