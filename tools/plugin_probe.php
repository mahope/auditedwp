<?php
/**
 * Probe: what every one of the plugin's checks says about one fixture.
 *
 *   php tools/plugin_probe.php <fixture.json>
 *
 * The fixture is one JSON object. Output is
 * `{ "<check key>": { "pass": bool, "warn": bool, "label": "…", "detail": "…" },
 *    "_fetches": n, "_heads": n, "_keys": [...] }` on stdout, and nothing else.
 *
 * Why this exists as a separate program: opgave 43 ported five check signatures
 * from `eucomply-scanner/engine/index.js` into the plugin so a WordPress customer
 * gets the same nine URL checks as the free scanner. That port was verified with
 * `php -l` and with the source/zip parity gate — both of which read the *code*,
 * and neither of which ever ran a check. A regex that compiles, lints and ships
 * can still disagree with the engine it was ported from. `tools/
 * test_plugin_engine_parity.mjs` runs this probe and the JS engine over the same
 * fixtures and requires the same verdict.
 *
 * Opgave 45 widened it: the probe now runs **every** check `run_checks()` writes,
 * not only the five that share an engine. The six WordPress-state checks —
 * cookies, forms, backups, plugins, legal and, through `front_page()`, ssl —
 * had never been executed by any test in the repo, so a bug identical in all
 * three copies of the file was invisible for the same reason it was invisible
 * for the other five.
 *
 * The check list is **read out of `run_checks()`**, not written here. A list
 * maintained by hand is a list that can quietly cover fewer checks than the
 * product runs, which is the failure this whole harness exists to catch.
 *
 * No network: every request is answered from the fixture or, when the fixture
 * carries an `error`, from a WP_Error — so "a page that cannot be read is never
 * a pass" is testable without anything being unreachable.
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

// ── The fixture every WordPress read is answered from ─────────────────────────

$EMPTY_STATE = array(
    'html'          => '',
    'headers'       => array(),
    'error'         => '',
    'head_headers'  => array(),
    'head_error'    => '',
    'active'        => array(),
    'pages'         => array(),
    'options'       => array(),
    'core_updates'  => array(),
    'plugin_updates' => array(),
    'updraft'       => null,
    'wpdb_hits'     => null,
    'wp_version'    => '6.5',
);
$GLOBALS['eucomply_probe_state'] = $EMPTY_STATE;
$GLOBALS['eucomply_probe_fetches'] = 0;
$GLOBALS['eucomply_probe_heads']   = 0;

/** Merge a raw fixture over the empty state, so a partial fixture is legal. */
function eucomply_probe_state( $raw ) {
    global $EMPTY_STATE;
    $out = array();
    foreach ( $EMPTY_STATE as $key => $blank ) {
        $out[ $key ] = array_key_exists( $key, $raw ) ? $raw[ $key ] : $blank;
    }
    return eucomply_probe_cast( $out );
}

/**
 * A fixture is JSON, so its posts and update objects arrive as arrays, while
 * WordPress hands the plugin objects. The casts belong here, in the adapter:
 * doing them in a fixture would mean a harness that is right by coincidence, and
 * `check_legal_pages()` reading `$page->post_status` off an array is a warning
 * that turns the check into a silent pass.
 */
function eucomply_probe_cast( $state ) {
    if ( isset( $state['pages'] ) && is_array( $state['pages'] ) ) {
        foreach ( $state['pages'] as $key => $page ) {
            if ( is_array( $page ) ) {
                $state['pages'][ $key ] = (object) $page;
            }
        }
    }
    foreach ( array( 'core_updates', 'plugin_updates' ) as $set ) {
        if ( ! isset( $state[ $set ] ) || ! is_array( $state[ $set ] ) ) {
            continue;
        }
        foreach ( $state[ $set ] as $key => $entry ) {
            if ( ! is_array( $entry ) ) {
                continue;
            }
            if ( isset( $entry['update'] ) && is_array( $entry['update'] ) ) {
                $entry['update'] = (object) $entry['update'];
            }
            $state[ $set ][ $key ] = (object) $entry;
        }
    }
    return $state;
}

function wp_remote_get( $url, $args = array() ) {
    $GLOBALS['eucomply_probe_fetches']++;
    $f = $GLOBALS['eucomply_probe_state'];
    if ( '' !== $f['error'] ) {
        return new WP_Error( 'http_request_failed', $f['error'] );
    }
    return array(
        'response' => array( 'code' => 200 ),
        'body'     => $f['html'],
        'headers'  => $f['headers'],
    );
}
/**
 * `check_ssl()` sends its own HEAD request instead of reading the front page it
 * already fetched. That is measured, not assumed: the probe counts the two
 * separately, because "one fetch per scan" is only a true statement about the
 * five static checks.
 */
function wp_remote_head( $url, $args = array() ) {
    $GLOBALS['eucomply_probe_heads']++;
    $f = $GLOBALS['eucomply_probe_state'];
    if ( '' !== $f['head_error'] ) {
        return new WP_Error( 'http_request_failed', $f['head_error'] );
    }
    return array(
        'response' => array( 'code' => 200 ),
        'headers'  => $f['head_headers'],
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
function wp_remote_retrieve_header( $response, $name ) {
    $name = strtolower( (string) $name );
    $all  = is_array( $response ) && isset( $response['headers'] ) ? $response['headers'] : array();
    foreach ( $all as $key => $value ) {
        if ( strtolower( (string) $key ) === $name ) {
            return $value;
        }
    }
    return '';
}

// ── The WordPress state the six WordPress-only checks read ────────────────────
// These are the reads `check_cookies()`, `check_forms()`, `check_backups()`,
// `check_plugins()` and `check_legal_pages()` make. A check that reads something
// no stub answers is a check that fatals in this harness — which is the point:
// a missing stub shows up as a red test, not as a silently skipped check.

function is_plugin_active( $path ) {
    $f = $GLOBALS['eucomply_probe_state'];
    return in_array( $path, (array) $f['active'], true );
}
function get_plugins() {
    return array();
}
function get_core_updates() {
    return (array) $GLOBALS['eucomply_probe_state']['core_updates'];
}
function get_plugin_updates() {
    return (array) $GLOBALS['eucomply_probe_state']['plugin_updates'];
}
function get_post( $id ) {
    $f = $GLOBALS['eucomply_probe_state'];
    return isset( $f['pages'][ $id ] ) ? $f['pages'][ $id ] : null;
}
function get_page_by_path( $path ) {
    $f = $GLOBALS['eucomply_probe_state'];
    return isset( $f['pages'][ $path ] ) ? $f['pages'][ $path ] : null;
}
/** The private class the backup check looks for before it trusts a timestamp. */
class UpdraftPlus_Options {
    public static function get_updraft_option( $key ) {
        return $GLOBALS['eucomply_probe_state']['updraft'];
    }
}
/** `$wpdb`, for the two page lookups that fall back to a title search. */
class EUComplyProbeWPDB {
    public $posts = 'wp_posts';
    public $queries = array();
    public function prepare( $sql, $arg = null ) {
        return 'PREPARED(' . $arg . ')';
    }
    public function get_var( $sql ) {
        $this->queries[] = $sql;
        return $GLOBALS['eucomply_probe_state']['wpdb_hits'];
    }
}
$GLOBALS['wpdb']       = new EUComplyProbeWPDB();
$GLOBALS['wp_version'] = $GLOBALS['eucomply_probe_state']['wp_version'];

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
$GLOBALS['eucomply_probe_state'] = eucomply_probe_state( $raw );
$GLOBALS['eucomply_test_options'] = (array) $GLOBALS['eucomply_probe_state']['options'];

// ── Which checks run_checks() actually writes ─────────────────────────────────

/**
 * The check keys `run_checks()` writes, in source order, with the method each
 * one calls. Read from the plugin's own source rather than listed here: a
 * hand-written list here is a list that can fall behind `run_checks()`, and then
 * this harness reports "every check agrees" about a smaller set than the product
 * runs — the same false green opgave 44 was about.
 *
 * @return array<string,string> key => method name.
 */
function eucomply_probe_check_map() {
    $source = file_get_contents( __DIR__ . '/../plugin/eucomply.php' );
    if ( ! preg_match( '/public function run_checks\(\).*?\n    \}/s', $source, $block ) ) {
        return array();
    }
    $map = array();
    // Tolerate any run of whitespace around the key and the call, so an editor's
    // alignment cannot be mistaken for a check that no longer runs.
    if ( preg_match_all(
        '/\$results\[\s*[\'"]([a-z0-9_]+)[\'"]\s*\]\s*=\s*\$this->([a-z0-9_]+)\s*\(/i',
        $block[0],
        $hits,
        PREG_SET_ORDER
    ) ) {
        foreach ( $hits as $hit ) {
            $map[ $hit[1] ] = $hit[2];
        }
    }
    return $map;
}

$CHECKS = eucomply_probe_check_map();
if ( ! $CHECKS ) {
    fwrite( STDERR, "run_checks() could not be read, so no check can be run\n" );
    exit( 2 );
}

$ref = new ReflectionClass( 'EUComply' );
$obj = $ref->newInstanceWithoutConstructor();

$out = array();
foreach ( $CHECKS as $key => $method ) {
    if ( ! $ref->hasMethod( $method ) ) {
        fwrite( STDERR, "run_checks() writes $key but the plugin has no method $method\n" );
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
$out['_heads']   = $GLOBALS['eucomply_probe_heads'];
$out['_keys']    = array_keys( $CHECKS );

echo json_encode( $out, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE ), "\n";
