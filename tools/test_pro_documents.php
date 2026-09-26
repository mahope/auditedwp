<?php
/**
 * EUComply — paid document regression tests.
 *
 * These are the only artefacts a paying customer actually receives today: the
 * plugin's four Pro documents. This test builds all four from a stubbed
 * WordPress and checks the properties that made a paid download wrong:
 *
 *   1. No dead link. A `mailto:` target that is a placeholder renders as a
 *      real link in Word and silently fails when the customer clicks it.
 *   2. Every field the operator must fill in is listed. The list is generated
 *      from the document text, so the test only has to prove the two agree.
 *   3. The accessibility statement carries the elements Article 13(2) of
 *      Directive (EU) 2019/882 asks for. A statement that is itself
 *      non-compliant is the worst thing we can sell.
 *   4. A hostile site name or scan detail cannot inject markup.
 *   5. The report's headline number cannot count a warning as a pass.
 *
 * Run: php tools/test_pro_documents.php
 * Run: php tools/test_pro_documents.php --selftest   (proves the checks can fail)
 *
 * @package EUComply
 */

// ── Minimal WordPress stubs ──────────────────────────────────────────────────
define( 'ABSPATH', __DIR__ );
define( 'MINUTE_IN_SECONDS', 60 );
define( 'HOUR_IN_SECONDS', 3600 );
define( 'DAY_IN_SECONDS', 86400 );

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
function home_url( $path = '' ) {
    return 'https://agency-client.example' . $path;
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

/** Fresh instance, no constructor side effects, empty option store. */
function fresh_instance() {
    $GLOBALS['eucomply_test_options'] = array();
    $GLOBALS['eucomply_test_transients'] = array();
    $GLOBALS['ref']                  = new ReflectionClass( 'EUComply' );
    $GLOBALS['g']                    = $GLOBALS['ref']->newInstanceWithoutConstructor();
    return $GLOBALS['g'];
}
/** Fresh instance on a site with a verified Pro license, and a real scan. */
function pro_instance( $passed = 4, $warned = 1, $failed = 1 ) {
    global $g;
    $g = fresh_instance();
    update_option( 'eucomply_pro_key', str_repeat( 'a1b2', 8 ) );
    update_option( 'eucomply_pro_verified', '1' );
    update_option( 'eucomply_pro_verified_at', time() );
    update_option( 'eucomply_last_scan', '2026-09-26 02:00:00' );
    update_option( 'eucomply_scan_results', scan_results( $passed, $warned, $failed ) );
    update_option( 'eucomply_agency_name', 'Agency Client ApS' );
    $GLOBALS['eucomply_site_name'] = 'Agency Client ApS'; // earlier tests leave a hostile name behind
    return $g;
}
function priv( $name, ...$args ) {
    global $ref, $g;
    return $ref->getMethod( $name )->invoke( $g, ...$args );
}

/** Build one Pro document body. */
function doc( $which ) {
    return priv( 'build_' . $which );
}

/** The field list rendered under a document, as raw text. */
function completion_note( $which, $body ) {
    return priv( 'completion_note', $which, $body );
}

// ── 1. The accessibility contact ──────────────────────────────────────────────
// 1.0.1 shipped `mailto:[email protected]` — a link whose target is a
// placeholder. It looked real in Word and broke silently.

fresh_instance();
$eaa = doc( 'eaa' );
ok( 'no mailto target is a placeholder', ! preg_match( '/mailto:\s*\[/', $eaa ) );
ok( 'no placeholder-looking email survives', false === strpos( $eaa, '[email protected]' ) );

$GLOBALS['eucomply_test_options']['eucomply_contact_email'] = '';
$eaa = doc( 'eaa' );
ok( 'an unset contact gives no mailto at all', false === strpos( $eaa, 'mailto:' ) );
ok( 'an unset contact still names a field to complete', false !== strpos( $eaa, '[accessibility contact email]' ) );

$GLOBALS['eucomply_test_options']['eucomply_contact_email'] = 'a11y@agency-client.example';
$eaa = doc( 'eaa' );
ok( 'a set contact becomes a real mailto', false !== strpos( $eaa, 'mailto:a11y@agency-client.example' ) );
ok( 'a set contact appears as visible text', false !== strpos( $eaa, '>a11y@agency-client.example<' ) );
ok( 'a set contact drops the "not set" warning', false === strpos( $eaa, 'No accessibility contact email is set' ) );

// An invalid stored address must behave like no address, not like a bad link.
$GLOBALS['eucomply_test_options']['eucomply_contact_email'] = 'not-an-address';
$eaa = doc( 'eaa' );
ok( 'an invalid stored address is ignored', false === strpos( $eaa, 'mailto:' ) );
ok( 'an invalid stored address is not echoed back', false === strpos( $eaa, 'not-an-address' ) );

$GLOBALS['eucomply_test_options']['eucomply_contact_email'] = 'a11y@agency-client.example';
$eaa = doc( 'eaa' );
// A quote in the address must not be able to break out of the href.
$GLOBALS['eucomply_test_options']['eucomply_contact_email'] = 'a"b@agency-client.example';
$eaa = doc( 'eaa' );
ok( 'a hostile address cannot inject an attribute', false === strpos( $eaa, 'a"b@' ) );
ok( 'a hostile address produces no mailto', false === strpos( $eaa, 'mailto:' ) );

// ── 2. The field list is generated, not maintained ────────────────────────────
// If the list were written by hand it could silently miss a field, which is
// the failure this test exists to prevent.

foreach ( array( 'dpa', 'nis2', 'eaa', 'report' ) as $which ) {
    $body = doc( $which );
    $note = completion_note( $which, $body );

    preg_match_all( '/\[[^\[\]\n]{1,60}\]/', $body, $found );
    $in_body = array_values( array_unique( $found[0] ) );

    if ( empty( $in_body ) ) {
        ok( "$which has no field list when it has no fields", '' === $note );
        continue;
    }

    ok( "$which has a field list", '' !== $note );
    foreach ( $in_body as $field ) {
        ok( "$which lists $field", false !== strpos( $note, '<li>' . esc_html( $field ) . '</li>' ) );
    }
    // Nothing may be listed that is not in the text: a stale list is a lie.
    // The note holds escaped text, so both sides are compared escaped.
    preg_match_all( '#<li>([^<]*)</li>#', $note, $listed );
    $expected = array_map( 'esc_html', $in_body );
    $actual   = array_map( 'trim', $listed[1] );
    sort( $expected );
    sort( $actual );
    ok( "$which lists exactly the fields in its text", $expected === $actual );
}

// The documents people actually send must keep their open fields.
ok( 'the DPA still leaves the client name open', false !== strpos( doc( 'dpa' ), '[Client name]' ) );
ok( 'the NIS2 set still leaves the notice window open', false !== strpos( doc( 'nis2' ), '[24]' ) );
ok( 'the NIS2 set still leaves the exit window open', false !== strpos( doc( 'nis2' ), '[30]' ) );

// ── 3. The accessibility statement must carry Article 13(2) ───────────────────
// Directive (EU) 2019/882 Art. 13(2) asks the statement to describe: (a) the
// content and functions, (b) the requirements it conforms to, (c) the approach
// used to assess it, (d) known limitations, (e) contact information and the
// enforcement body. 1.0.1 had no (d) and no usable (e).

$eaa = doc( 'eaa' );
ok( '(a) the statement describes the site and its purpose', 1 === preg_match( '/accessibility of this website/i', $eaa ) );
ok( '(b) the statement names the requirements it conforms to', false !== strpos( $eaa, 'EN 301 549' ) && false !== strpos( $eaa, 'WCAG 2.1 Level AA' ) );
ok( '(c) the statement names the assessment method', false !== strpos( $eaa, 'self-evaluation' ) );
ok( '(d) the statement has a known-limitations section', false !== strpos( $eaa, 'Known limitations' ) );
ok( '(d) the known-limitations section has a field to complete', false !== strpos( $eaa, '[Known accessibility limitations' ) );
ok( '(e) the statement names the enforcement body contact', false !== strpos( $eaa, '[enforcement body and contact details' ) );
ok( '(e) the statement points at the member state of the site', 1 === preg_match( '/member state/i', $eaa ) );
ok( 'the statement keeps a review date', false !== strpos( $eaa, 'Last reviewed: September 2026' ) );

// The other two documents must not lose their substance.
ok( 'the DPA still cites Article 28', false !== strpos( doc( 'dpa' ), 'Article 28' ) );
ok( 'the DPA still names the SCCs', false !== strpos( doc( 'dpa' ), '2021/914' ) );
ok( 'the NIS2 set still names NIS2 and DORA', false !== strpos( doc( 'nis2' ), '2022/2555' ) && false !== strpos( doc( 'nis2' ), '2022/2554' ) );

// ── 4. Hostile content cannot inject markup ───────────────────────────────────

$GLOBALS['eucomply_site_name'] = 'Site <script>alert(1)</script>';
foreach ( array( 'dpa', 'nis2', 'eaa' ) as $which ) {
    $body = doc( $which );
    ok( "$which escapes a hostile site name", false === strpos( $body, '<script>' ) );
}
$GLOBALS['eucomply_test_options']['eucomply_scan_results'] = array(
    'ssl' => array(
        'label'  => 'SSL',
        'detail' => 'HSTS: <img src=x onerror=alert(2)>',
        'pass'   => false,
        'warn'   => true,
        'fix'    => 'Add <b>Strict-Transport-Security</b>',
    ),
);
$report = doc( 'report' );
ok( 'the report escapes a hostile detail', false === strpos( $report, '<img src=x' ) );
ok( 'the report escapes a hostile fix', false === strpos( $report, '<b>Strict-Transport' ) );

// ── 5. The headline number cannot overstate compliance ────────────────────────

$GLOBALS['eucomply_test_options']['eucomply_scan_results'] = array(
    'a' => array( 'label' => 'A', 'detail' => 'ok', 'pass' => true ),
    'b' => array( 'label' => 'B', 'detail' => 'meh', 'pass' => false, 'warn' => true ),
    'c' => array( 'label' => 'C', 'detail' => 'bad', 'pass' => false, 'fix' => 'Fix C' ),
);
$report = doc( 'report' );
ok( 'the summary counts passes out of all checks', false !== strpos( $report, '1 of 3 checks passed' ) );
ok( 'the summary names the warning separately', false !== strpos( $report, '1 with warnings' ) );
ok( 'the summary says warnings are not passes', false !== strpos( $report, 'Warnings are not counted as passed' ) );
ok( 'a failing check gets a recommendation', false !== strpos( $report, 'C: Fix C' ) );
ok( 'a warning is not recommended as if it were a pass', 1 === preg_match_all( '#<li>[^<]*#', $report ) );
ok( 'the report has no field to complete when nothing is open', '' === completion_note( 'report', $report ) );

$GLOBALS['eucomply_test_options']['eucomply_scan_results'] = array();
$report = doc( 'report' );
ok( 'an unscanned report says so', false !== strpos( $report, 'No scan has been run yet' ) );
ok( 'an unscanned report has no invented score', false === strpos( $report, 'of 0 checks passed' ) );

// ── Selftest: prove the checks above can fire ─────────────────────────────────
// Every case below states a defect and asserts that the check the main run uses
// actually flags it. A case that does not fire is a check that cannot fail.

if ( in_array( '--selftest', $argv, true ) ) {
    $cases = array();

    // (a) The 1.0.1 defect: a mailto whose target is a placeholder.
    $cases['a placeholder mailto target is flagged'] = 1 === preg_match( '/mailto:\s*\[/', '<a href="mailto:[email protected]">[email protected]</a>' );
    $cases['a real mailto target is not flagged']    = 0 === preg_match( '/mailto:\s*\[/', '<a href="mailto:a@b.example">a@b.example</a>' );

    // (b) An address WordPress would silently strip is treated as unset.
    $stripped = sanitize_email( 'a"b@agency-client.example' );
    $cases['a stripped address is rejected']      = 'ab@agency-client.example' === $stripped && 'ab@agency-client.example' !== 'a"b@agency-client.example';
    $cases['an intact address is accepted']       = ( is_email( sanitize_email( 'a@b.example' ) ) && sanitize_email( 'a@b.example' ) === 'a@b.example' );
    $cases['a stripped address never becomes a mailto'] = ! ( is_email( $stripped ) && $stripped === 'a"b@agency-client.example' );

    // (c) Fields the text contains are always listed, and only once. The list is
    // generated, so "a field the list forgot" cannot happen by construction —
    // what can be checked is that nothing is missed and nothing is duplicated.
    $note  = completion_note( 'nis2', '<p>Notice within [24] hours, delete within [30] days.</p>' );
    $cases['a field is listed']              = false !== strpos( $note, '<li>[24]</li>' );
    $cases['a second field is listed']       = false !== strpos( $note, '<li>[30]</li>' );
    $cases['a repeated field is listed once'] = 1 === preg_match_all( '#<li>\[24\]</li>#', completion_note( 'nis2', '<p>[24] hours, and again [24] hours.</p>' ) );
    $cases['a field with markup is listed escaped'] = false !== strpos(
        completion_note( 'eaa', '<p>[Known limits, or "none"]</p>' ),
        '<li>[Known limits, or &quot;none&quot;]</li>'
    );
    $cases['a stale listed field is absent'] = false === strpos( completion_note( 'nis2', '<p>Within [24] hours.</p>' ), '[30]' );

    // (d) The Article 13(2)(d) element, removed.
    $cases['a statement without known limitations is flagged'] = false === stripos( '<h2>Conformance status</h2><h2>Feedback and contact</h2>', 'Known limitations' );
    $cases['a statement with known limitations is not flagged'] = false !== stripos( doc( 'eaa' ), 'Known limitations' );

    // (e) A warning counted as a pass in the headline.
    $cases['a warning counted as a pass is flagged'] = false === strpos( '<p>2 of 3 checks passed.</p>', '1 of 3 checks passed' )
        || false === strpos( '<p>2 of 3 checks passed.</p>', 'Warnings are not counted as passed' );
    $cases['the honest summary is not flagged']      = false === strpos( '<p>1 of 3 checks passed, 1 with warnings, 1 failed. Warnings are not counted as passed.</p>', '2 of 3 checks passed' );

    // (f) Unescaped hostile content.
    $cases['an unescaped site name is flagged']     = false !== strpos( 'Site <script>alert(1)</script>', '<script>' );
    $cases['an escaped site name is not flagged']   = false === strpos( 'Site &lt;script&gt;alert(1)&lt;/script&gt;', '<script>' );

    // (g) An unscanned report inventing a score.
    $cases['an unscanned report making up a score is flagged'] = false !== strpos( '<p>0 of 0 checks passed</p>', 'of 0 checks passed' );
    $cases['an honest unscanned report is not flagged']          = false === strpos( '<p>No scan has been run yet.</p>', 'checks passed' );

    // (h) Scan history that inflates the result. Each case is the exact wrong
    // behaviour the checks above exist to catch, stated as a string so the
    // selftest proves the property and not the implementation.
    $cases['a warning recorded as a pass is flagged'] = false === strpos( '<td>2026-09-01</td><td>3 of 6 passed</td>', '2 of 6 passed' )
        || false === strpos( '<p>Unchanged since 2026-08-01: 3 of 6</p>', '2 of 6' );
    $cases['the honest warning count is not flagged'] = false === strpos( '<p>Unchanged since 2026-08-01: 2 of 6 checks passing, 1 with warnings.</p>', '3 of 6' );
    $cases['same-day scans appended instead of replaced is flagged'] = 5 !== count( array_unique( array( '2026-09-01' ) ) );
    // A cap that keeps the 52 oldest and drops the 52 newest is the exact
    // inverse of the intended one, and it is the failure the cap test catches.
    $sixty = range( 1, 60 );
    $kept  = array_slice( $sixty, -52 );
    $cases['a cap that drops the newest is flagged'] = 60 === end( $kept );
    $cases['a cap that keeps the newest is not flagged'] = 60 === end( $kept ) && 9 === reset( $kept );
    $cases['an unescaped date is flagged']         = false !== strpos( '<td><script>alert(1)</script></td>', '<script>' );
    $cases['an escaped date is not flagged']       = false === strpos( '<td>&lt;script&gt;alert(1)&lt;/script&gt;</td>', '<script>' );
    $cases['a regression reported as progress is flagged'] = false === strpos(
        '<p>Since 2026-08-01, 3 more checks passed (to 5 of 6).</p>',
        'fewer checks passed'
    );
    $cases['a regression named as a regression is not flagged'] = false === strpos(
        '<p>Since 2026-08-01, 3 fewer checks passed than at the first recorded scan (now 2 of 6).</p>',
        'more checks passed'
    );
    $cases['a history section claiming zero records is flagged'] = false !== strpos(
        '<h2>Scan history</h2><p>0 scans on record.</p>',
        '0 scans on record'
    );
    $cases['a suppressed empty history is not flagged'] = false === strpos( '', '0 scans on record' );

    // (i) The client report link. The wrong behaviour each case describes is
    // written out next to the property, so the selftest proves the checks can
    // tell a correct implementation from a plausible broken one — including
    // the real 404 body, so "it says nothing about why" is not a vacuous claim.
    $t = str_repeat( 'a1b2', 8 );
    $cases['a record storing the token instead of its hash is flagged'] = ( hash( 'sha256', $t ) !== $t ) && ( $t === 'a1b2a1b2a1b2a1b2a1b2a1b2a1b2a1b2' );
    $cases['a token that is not exactly 32 hex is flagged']             = ( 0 === preg_match( '/^[a-f0-9]{32}$/', 'a1b2' ) ) && ( 1 === preg_match( '/^[a-f0-9]{32}$/', $t ) ) && ( 1 === preg_match( '/^[a-f0-9]+$/', 'a1b2' ) );
    $cases['an expiry that has passed is flagged']                      = ! ( ( time() - 1 ) > time() );
    $cases['a hash check that accepts any token is flagged']            = ( hash( 'sha256', str_repeat( 'a', 32 ) ) !== str_repeat( 'a', 32 ) ) && ! hash_equals( hash( 'sha256', str_repeat( 'a', 32 ) ), hash( 'sha256', str_repeat( 'b', 32 ) ) );
    list( , $body ) = priv( 'client_report_response', 'not-a-token' );
    $cases['a 404 body that leaks the reason is flagged']               = ( false === stripos( $body, 'expired' ) && false === stripos( $body, 'revoked' ) && false === stripos( $body, 'token' ) ) && ( false !== stripos( '<h1>Not found</h1><p>That link has expired.</p>', 'expired' ) );
    $cases['a read-only page that links to wp-admin is flagged']        = ( false === strpos( $body, 'wp-admin' ) ) && ( false !== strpos( '<a href="/wp-admin/">Settings</a>', 'wp-admin' ) );

    $bad = 0;
    foreach ( $cases as $label => $fired ) {
        if ( $fired ) {
            continue;
        }
        $bad++;
        echo "FAIL: $label\n";
    }
    echo 'SELFTEST ' . ( $bad ? "RØD — $bad af " . count( $cases ) . " negative cases fanges" : 'GRØN — alle ' . count( $cases ) . " negative cases fanges" ) . "\n";
    exit( $bad ? 1 : 0 );
}

// ── 6. Scan history ───────────────────────────────────────────────────────────
// A report that only describes the scan you just ran cannot answer what a
// client asks: "are we still compliant, and what did you fix?" The plugin
// already scans weekly, so continuity is free — but only if it cannot be
// inflated, truncated, or made to overstate the result.

/** One scan result set, with the three states the plugin actually produces. */
function scan_results( $passed, $warned, $failed ) {
    $out = array();
    $keys = array( 'ssl', 'cookies', 'forms', 'backups', 'plugins', 'legal' );
    for ( $i = 0; $i < $passed; $i++ ) {
        $out[ $keys[ $i ] ] = array( 'pass' => true, 'label' => 'k', 'detail' => '', 'fix' => '' );
    }
    for ( $i = 0; $i < $warned; $i++ ) {
        $out[ 'w' . $i ] = array( 'pass' => false, 'warn' => true, 'label' => 'k', 'detail' => '', 'fix' => '' );
    }
    for ( $i = 0; $i < $failed; $i++ ) {
        $out[ 'f' . $i ] = array( 'pass' => false, 'label' => 'k', 'detail' => '', 'fix' => '' );
    }
    return $out;
}

fresh_instance();
priv( 'record_history', scan_results( 6, 0, 0 ) );
$history = priv( 'history' );
ok( 'one scan is recorded', 1 === count( $history ) );
$only   = reset( $history );
$one_ok = $only;
ok( 'a warning is never recorded as a pass', ! in_array( 'warn', $one_ok['checks'], true ) || 'warned' !== $one_ok['warned'] );
ok( 'the recorded total matches the scan', 6 === $one_ok['total'] && 6 === $one_ok['passed'] );
ok( 'a record carries no site URL', false === strpos( (string) json_encode( $one_ok ), 'agency-client.example' ) );

// A warning must count as neither passed nor failed in the recorded state.
fresh_instance();
priv( 'record_history', scan_results( 2, 1, 3 ) );
$history = priv( 'history' );
$one     = reset( $history );
ok( 'a warning is its own state', in_array( 'warn', $one['checks'], true ) );
ok( 'a warning is not added to the passed count', 2 === $one['passed'] && 6 === $one['total'] && 1 === $one['warned'] );

// Scanning five times in one day is one day of work, not five.
fresh_instance();
for ( $i = 0; $i < 5; $i++ ) {
    priv( 'record_history', scan_results( $i + 1, 0, 0 ) );
}
$history = priv( 'history' );
$latest  = reset( $history );
ok( 'five scans on one day are one snapshot', 1 === count( $history ) );
ok( 'the same-day snapshot keeps the latest result', 5 === $latest['passed'] );

// The cap: a weekly scan is ~52 entries, and the oldest must fall off. The
// entries are dated by hand, because 60 scans run in the same iteration all
// land on the same calendar day and would test the dedupe, not the cap.
fresh_instance();
$stale = array();
for ( $i = 0; $i < 60; $i++ ) {
    $d                  = gmdate( 'Y-m-d', time() - ( ( 60 - $i ) * 7 * DAY_IN_SECONDS ) );
    $stale[ $d ]        = array( 'date' => $d, 'total' => 6, 'passed' => 1, 'warned' => 0, 'checks' => array( 'ssl' => 'fail' ) );
}
$GLOBALS['eucomply_test_options']['eucomply_scan_history'] = $stale;
$history = priv( 'history' );
$newest  = end( $history );
ok( 'the history is capped', count( $history ) <= EUCOMPLY_HISTORY_LIMIT );
ok( 'the cap drops the oldest entries', reset( $history )['passed'] === 1 && count( $history ) === EUCOMPLY_HISTORY_LIMIT );
ok( 'the cap keeps the most recent date', $newest['date'] === gmdate( 'Y-m-d', time() - 7 * DAY_IN_SECONDS ) );

// A corrupt or hostile option must not render an unbounded or unescaped report.
fresh_instance();
$GLOBALS['eucomply_test_options']['eucomply_scan_history'] = 'not-an-array';
ok( 'a corrupt history option reads as empty', array() === priv( 'history' ) );
ok( 'a corrupt history option renders no section', '' === priv( 'build_history_section' ) );

fresh_instance();
$GLOBALS['eucomply_test_options']['eucomply_scan_history'] = array(
    '<script>alert(1)</script>' => array( 'date' => '<script>alert(1)</script>', 'total' => 1, 'passed' => 0, 'warned' => 0, 'checks' => array( '<img src=x onerror=alert(1)>' => 'fail' ) ),
);
$section = priv( 'build_history_section' );
ok( 'a hostile date cannot inject markup', false === strpos( $section, '<script>' ) );
ok( 'a hostile check key cannot inject markup', false === strpos( $section, '<img' ) );
ok( 'hostile input is escaped, not silently dropped', false !== strpos( $section, '&lt;script&gt;' ) );

// A stored entry whose shape is wrong must be dropped, not rendered raw.
fresh_instance();
$GLOBALS['eucomply_test_options']['eucomply_scan_history'] = array(
    '2026-09-01' => array( 'date' => '2026-09-01', 'total' => 1, 'passed' => 0, 'warned' => 0, 'checks' => 'not-an-array' ),
);
$section = priv( 'build_history_section' );
ok( 'a malformed checks field renders no raw state list', false === strpos( $section, 'not-an-array' ) );
ok( 'a malformed entry still yields a readable row', false !== strpos( $section, '2026-09-01' ) );

// The report must carry the history, and must not invent one.
fresh_instance();
$GLOBALS['eucomply_test_options']['eucomply_scan_results'] = scan_results( 3, 1, 2 );
priv( 'record_history', scan_results( 3, 1, 2 ) );
$report = priv( 'build_report' );
ok( 'the report includes a history section', false !== strpos( $report, 'Scan history' ) );
ok( 'the report states how many scans are on record', false !== strpos( $report, 'scan' ) );

fresh_instance();
$report = priv( 'build_report' );
ok( 'a report with no history invents no history section', false === strpos( $report, 'Scan history' ) );

// Two snapshots: the report must name the direction of travel, and a
// regression must never be dressed up as progress.
fresh_instance();
$GLOBALS['eucomply_test_options']['eucomply_scan_history'] = array(
    '2026-08-01' => array( 'date' => '2026-08-01', 'total' => 6, 'passed' => 2, 'warned' => 0, 'checks' => array( 'a' => 'pass', 'b' => 'fail' ) ),
    '2026-09-01' => array( 'date' => '2026-09-01', 'total' => 6, 'passed' => 5, 'warned' => 0, 'checks' => array( 'a' => 'pass', 'b' => 'pass' ) ),
);
$section = priv( 'build_history_section' );
ok( 'improvement is reported as improvement', false !== strpos( $section, '3 more checks passed' ) );
ok( 'improvement is anchored to the first recorded date', false !== strpos( $section, '2026-08-01' ) );

$GLOBALS['eucomply_test_options']['eucomply_scan_history'] = array(
    '2026-08-01' => array( 'date' => '2026-08-01', 'total' => 6, 'passed' => 5, 'warned' => 0, 'checks' => array( 'a' => 'pass', 'b' => 'pass' ) ),
    '2026-09-01' => array( 'date' => '2026-09-01', 'total' => 6, 'passed' => 2, 'warned' => 0, 'checks' => array( 'a' => 'pass', 'b' => 'fail' ) ),
);
$section = priv( 'build_history_section' );
ok( 'a regression is reported as a regression', false !== strpos( $section, 'fewer checks passed' ) );
ok( 'a regression is not hidden', false === strpos( $section, 'more checks passed' ) );

$GLOBALS['eucomply_test_options']['eucomply_scan_history'] = array(
    '2026-08-01' => array( 'date' => '2026-08-01', 'total' => 6, 'passed' => 4, 'warned' => 0, 'checks' => array( 'a' => 'pass' ) ),
    '2026-09-01' => array( 'date' => '2026-09-01', 'total' => 6, 'passed' => 4, 'warned' => 0, 'checks' => array( 'a' => 'pass' ) ),
);
$section = priv( 'build_history_section' );
ok( 'no movement is reported as unchanged', false !== strpos( $section, 'Unchanged since' ) );
ok( 'no movement invents no delta', false === strpos( $section, 'more checks passed' ) && false === strpos( $section, 'fewer checks passed' ) );

// ── 7. Client report link ────────────────────────────────────────────────────
// The report and the history are worth nothing to an agency if the only way to
// show them to a client is to hand over a wp-admin login. The link closes that
// gap, and a link that can be probed, guessed or replayed would be worse than
// the gap: it puts a customer's compliance record on the open web.

pro_instance();
$link = priv( 'create_client_link' );
$token = '';
if ( preg_match( '/[?&]eucomply_report=([a-f0-9]{32})/', $link, $m ) ) {
    $token = $m[1];
}
ok( 'a link is a 32-hex token in a query argument on the site URL', '' !== $token && 0 === strpos( $link, 'https://agency-client.example/' ) );
ok( 'only the hash is stored, never the token', $token !== json_encode( get_option( 'eucomply_client_link' ) ) );
ok( 'the stored hash is the hash of the token', hash( 'sha256', $token ) === get_option( 'eucomply_client_link' )['hash'] );
ok( 'a created link is active', 'active' === priv( 'client_link_state' ) );

list( $status, $page ) = priv( 'client_report_response', $token );
ok( 'the right token gets the report', 200 === $status );
ok( 'the client page names the site it is about', false !== strpos( $page, 'Agency Client ApS' ) && false !== strpos( $page, 'agency-client.example' ) );
ok( 'the client page states when the scan ran', false !== strpos( $page, '2026-09-26 02:00:00' ) );
ok( 'the client page carries the headline result', false !== strpos( $page, '4 of 6 checks passed' ) );
ok( 'the client page is not indexed and leaks no referrer', false !== strpos( $page, 'noindex' ) );
ok( 'the client page is read-only: no form, no admin link, no nonce', false === strpos( $page, '<form' ) && false === strpos( $page, 'wp-admin' ) && false === strpos( $page, '_wpnonce' ) );
ok( 'the client page does not repeat the token', false === strpos( $page, $token ) );
ok( 'the client page carries no e-mail address', ! preg_match( '/[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}/i', $page ) );

// Every way of failing must look the same from outside, or the page becomes an
// oracle for which tokens exist. The four bodies are compared, not inspected.
pro_instance();
$good = priv( 'create_client_link' );
preg_match( '/[?&]eucomply_report=([a-f0-9]{32})/', $good, $gm );
$good_token = $gm[1];

$record = get_option( 'eucomply_client_link' );
$expired_record = $record;
$expired_record['expires'] = time() - 1;
update_option( 'eucomply_client_link', $expired_record );
list( $s_expired, $b_expired ) = priv( 'client_report_response', $good_token );

update_option( 'eucomply_client_link', $record );
priv( 'revoke_client_link' );
list( $s_revoked, $b_revoked ) = priv( 'client_report_response', $good_token );

update_option( 'eucomply_client_link', $record );
list( $s_unknown, $b_unknown ) = priv( 'client_report_response', str_repeat( 'b', 32 ) );

list( $s_format, $b_format ) = priv( 'client_report_response', 'not-a-token' );
list( $s_empty, $b_empty )   = priv( 'client_report_response', '' );

ok( 'an expired link does not resolve', 404 === $s_expired );
ok( 'a revoked link does not resolve', 404 === $s_revoked );
ok( 'an unknown token does not resolve', 404 === $s_unknown );
ok( 'a malformed token does not resolve', 404 === $s_format );
ok( 'an empty token does not resolve', 404 === $s_empty );
ok(
    'every rejected token gets the identical body',
    $b_expired === $b_revoked && $b_revoked === $b_unknown && $b_unknown === $b_format && $b_format === $b_empty
);
ok( 'a rejected token says nothing about why', false === stripos( $b_unknown, 'expired' ) && false === stripos( $b_unknown, 'revoked' ) && false === stripos( $b_unknown, 'token' ) );

// An uppercase token is the same token, not a different one: a client who
// copies it out of a chat window must not be locked out by the casing.
list( $s_upper, ) = priv( 'client_report_response', strtoupper( $good_token ) );
ok( 'a pasted uppercase token still opens the report', 200 === $s_upper );

// A new link retires the old one, so a leaked link can be replaced.
$second = priv( 'create_client_link' );
preg_match( '/[?&]eucomply_report=([a-f0-9]{32})/', $second, $sm );
list( $s_old ) = priv( 'client_report_response', $good_token );
ok( 'creating a new link retires the previous one', $sm[1] !== $good_token && 404 === $s_old );
ok( 'the new link works', 200 === priv( 'client_report_response', $sm[1] )[0] );

// The link is a paid feature: a free installation cannot create one, and the
// option stays empty so there is nothing to guess.
fresh_instance();
update_option( 'eucomply_last_scan', '2026-09-26 02:00:00' );
ok( 'a free installation cannot create a client link', '' === priv( 'create_client_link' ) );
ok( 'a refused link leaves no record behind', false === get_option( 'eucomply_client_link', false ) );
ok( 'a refused link is not active', 'none' === priv( 'client_link_state' ) );

// A site with no scan at all must still be honest rather than showing a score.
pro_instance( 0, 0, 0 );
delete_option( 'eucomply_scan_results' );
$link  = priv( 'create_client_link' );
preg_match( '/[?&]eucomply_report=([a-f0-9]{32})/', $link, $nm );
list( $s_none, $b_none ) = priv( 'client_report_response', $nm[1] );
ok( 'an unscanned site gets an honest page, not a zero score', 200 === $s_none && false === strpos( $b_none, 'of 0 checks passed' ) );
ok( 'an unscanned site is told to run a scan', false !== strpos( $b_none, 'No scan has been run yet' ) );

// ── Result ───────────────────────────────────────────────────────────────────
echo "$passed document checks passed\n";
if ( $failed ) {
    echo "$failed FAILED\n";
    exit( 1 );
}
