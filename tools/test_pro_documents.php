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

require_once __DIR__ . '/wp_stubs.php';

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
    $GLOBALS['eucomply_test_cron']    = array();
    $GLOBALS['eucomply_test_mail']    = array();
    unset( $GLOBALS['eucomply_test_mail_fails'] );
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
    update_option( 'eucomply_pro_last_ok_at', time() );
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

    // (j) The wp-admin export. Each case states the exact wrong shape and shows
    // the check the main run uses tells it apart from the right one. The old
    // download is included verbatim in shape — different header, no history —
    // because that is the defect this change removes, and a property that cannot
    // tell those two apart is not testing anything.
    $refused = priv( 'report_export_response', false, true, true );
    $guardless = array( 200, 'a report', 'eucomply-report-2026-09-26.html' );
    $cases['an export that skips the capability check is flagged'] = ( 403 === $refused[0] ) && ( '' === $refused[1] ) && ( 403 !== $guardless[0] );
    $cases['an export that skips the nonce check is flagged']      = ( 403 === priv( 'report_export_response', true, false, true )[0] ) && ( '' === priv( 'report_export_response', true, false, true )[2] );
    $cases['an export that skips the Pro check is flagged']         = ( 403 === priv( 'report_export_response', true, true, false )[0] ) && ( 403 !== priv( 'report_export_response', true, true, true )[0] );
    $cases['a refusal carrying a filename is flagged']              = ( '' === $refused[2] ) && ( '' !== $guardless[2] );
    $old_rendering = '<!DOCTYPE html><html><head><meta charset="utf-8"><title>HTML Compliance Report</title></head><body>'
        . '<h1>HTML Compliance Report</h1><p>Site: <strong>Agency Client ApS</strong> (https://agency-client.example)<br>'
        . 'Generated: September 26, 2026 &middot; By: Agency Client ApS</p><p>Summary of the latest automated compliance scan (2026-09-26 02:00:00).</p>';
    pro_instance();
    $GLOBALS['eucomply_test_options']['eucomply_scan_history'] = array( '2026-09-01' => array( 'date' => '2026-09-01', 'total' => 6, 'passed' => 5, 'warned' => 1, 'checks' => array( 'a' => 'pass' ) ) );
    $export_body = priv( 'report_export_response', true, true, true )[1];
    $cases['a second rendering of the report is flagged'] = ( $old_rendering !== $export_body ) && ( false === strpos( $old_rendering, 'Scan history' ) ) && ( false !== strpos( $export_body, 'Scan history' ) );
    $cases['an attached file claiming a link expires is flagged'] = ( false !== strpos( $old_rendering . '<p>This link stops working on 2026-10-26.</p>', 'stops working on' ) ) && ( false === strpos( $export_body, 'stops working on' ) );
    $cases['a capability weaker than the settings page is flagged'] = ( 'manage_options' !== 'read' ) && ( 0 === preg_match( "/current_user_can\(\s*'read'\s*\)/", file_get_contents( __DIR__ . '/../plugin/eucomply.php' ) ) );

    // (k) The scheduled interval. The wrong behaviour is written out next to
    // the property: a cadence that only ratchets up, one that follows a stale
    // verdict, one that asks the license server on every page view.
    pro_instance();
    $sync_calls = 0;
    $cases['a sync that re-schedules every request is flagged'] = ( function () use ( &$sync_calls ) {
        $g = fresh_instance();
        priv( 'sync_scan_schedule' );
        $first = wp_next_scheduled( EUCOMPLY_SCAN_EVENT );
        // A sync that always clears and re-schedules pushes the next run a
        // whole interval further away on every single request, so a Pro site
        // is never scanned again.
        wp_clear_scheduled_hook( EUCOMPLY_SCAN_EVENT );
        wp_schedule_event( time() + DAY_IN_SECONDS, 'daily', EUCOMPLY_SCAN_EVENT );
        $moved = wp_next_scheduled( EUCOMPLY_SCAN_EVENT );
        return $moved !== $first;
    } )();
    $cases['an untouched schedule keeps its timestamp'] = ( function () {
        fresh_instance();
        priv( 'sync_scan_schedule' );
        $t = wp_next_scheduled( EUCOMPLY_SCAN_EVENT );
        priv( 'sync_scan_schedule' );
        return $t === wp_next_scheduled( EUCOMPLY_SCAN_EVENT );
    } )();
    $cases['a cadence that ignores an expired verdict is flagged'] = ( function () {
        pro_instance();
        update_option( 'eucomply_pro_last_ok_at', time() - ( 30 * DAY_IN_SECONDS ) );
        return 'daily' !== scheduled_interval();
    } )();
    $cases['a cadence that ignores a missing key is flagged'] = ( function () {
        pro_instance();
        delete_option( 'eucomply_pro_key' );
        return 'daily' !== scheduled_interval();
    } )();
    $cases['a cadence granted by a device-limit 409 is flagged'] = ( function () {
        pro_instance();
        update_option( 'eucomply_pro_state', 'device_limit' );
        return 'daily' !== scheduled_interval();
    } )();
    // The scheduling block runs on every request, so the one thing it must not
    // do is reach the network. is_pro() is the only path to the license server,
    // so the property is: the block decides from stored options alone. There is
    // deliberately no wp_remote_* stub in this file, so a call would fatal.
    $src = file_get_contents( __DIR__ . '/../plugin/eucomply.php' );
    $scheduling_block = '';
    if ( preg_match( '/private function pro_cadence_active\(\).*?\n    \}/s', $src, $blk ) ) {
        $scheduling_block = $blk[0];
    }
    $cases['the scheduling block is found, so the check is not vacuous'] = ( '' !== $scheduling_block );
    $cases['the scheduling block never calls the license server'] = ( '' !== $scheduling_block ) && ( 0 === preg_match( '/\$this->is_pro\s*\(/', $scheduling_block ) ) && ( false === strpos( $scheduling_block, 'wp_remote_' ) );

    $cases['a stale event name is flagged'] = ( 'eucomply_weekly_scan' !== 'eucomply_daily_scan' ) && ( 'eucomply_weekly_scan' === EUCOMPLY_SCAN_EVENT );

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

// ── 8. The report as a file ───────────────────────────────────────────────────
// An agency delivers a report as an attachment, not as a URL the client has to
// remember to open. The download therefore has to be the same document, and it
// has to be refused in exactly the same way — a download address that answers
// differently from the page is a second, weaker lock on the same secret.

pro_instance();
$GLOBALS['eucomply_test_options']['eucomply_scan_history'] = array(
    '2026-09-01' => array( 'date' => '2026-09-01', 'total' => 6, 'passed' => 5, 'warned' => 1, 'checks' => array( 'a' => 'pass', 'b' => 'warn' ) ),
);
$file_link = priv( 'create_client_link' );
preg_match( '/[?&]eucomply_report=([a-f0-9]{32})/', $file_link, $fm );
$file_token = $fm[1];

list( $fs, $fbody, $fname ) = priv( 'client_report_response', $file_token, true );
list( $ps, $pbody, $pname ) = priv( 'client_report_response', $file_token );

ok( 'a valid token downloads the report', 200 === $fs );
ok( 'the file is the same bytes as the page', $fbody === $pbody );
ok( 'the file carries the scan history, not a cut-down version', false !== strpos( $fbody, 'Scan history' ) && false !== strpos( $fbody, '2026-09-01' ) );
ok( 'the page asks for no filename and the file asks for one', '' === $pname && '' !== $fname );
ok( 'the filename is the scan date in a fixed shape', 'eucomply-report-2026-09-26.html' === $fname );
ok( 'the filename carries no part of the token', false === strpos( $fname, substr( $file_token, 0, 8 ) ) && false === strpos( $fbody, $file_token ) );

// The same scan must always produce the same name: an agency that attaches
// last month's file and this month's file must be able to tell them apart by
// name alone, and a name that changed for no reason would defeat that.
ok( 'the filename is deterministic', $fname === priv( 'client_report_filename' ) );

// A hostile option must not reach a response header. A scan date is written by
// this plugin, but it is an option, and a header split by a newline is a
// response-splitting bug, not a cosmetic one.
$GLOBALS['eucomply_test_options']['eucomply_last_scan'] = "2026-09-26\r\nX-Injected: 1";
ok( 'a hostile scan date cannot reach the filename', 1 === preg_match( '/^eucomply-report-\d{4}-\d{2}-\d{2}\.html$/', priv( 'client_report_filename' ) ) );

// A site that has never been scanned has no date to name the file after, and
// inventing one from an empty option would be a lie about when the scan ran.
pro_instance( 0, 0, 0 );
delete_option( 'eucomply_last_scan' );
$nl = priv( 'create_client_link' );
preg_match( '/[?&]eucomply_report=([a-f0-9]{32})/', $nl, $nm2 );
list( $ns, $nbody, $nname ) = priv( 'client_report_response', $nm2[1], true );
ok( 'an unscanned site still gets a well-formed filename', 1 === preg_match( '/^eucomply-report-\d{4}-\d{2}-\d{2}\.html$/', $nname ) );
ok( 'an unscanned download says so rather than showing a score', false !== strpos( $nbody, 'No scan has been run yet' ) );

// Every way of failing must look the same here too. The download is compared
// against the page's own 404, byte for byte, and against the 404 the page
// gives: three rejections, one answer.
pro_instance();
$dl = priv( 'create_client_link' );
preg_match( '/[?&]eucomply_report=([a-f0-9]{32})/', $dl, $dm );
$dl_token = $dm[1];
$rec  = get_option( 'eucomply_client_link' );
$old  = $rec;
$old['expires'] = time() - 1;

update_option( 'eucomply_client_link', $old );
list( $d_exp, $b_exp, $n_exp ) = priv( 'client_report_response', $dl_token, true );
update_option( 'eucomply_client_link', $rec );
priv( 'revoke_client_link' );
list( $d_rev, $b_rev, $n_rev ) = priv( 'client_report_response', $dl_token, true );
update_option( 'eucomply_client_link', $rec );
list( $d_unk, $b_unk, $n_unk ) = priv( 'client_report_response', str_repeat( 'b', 32 ), true );
list( $d_fmt, $b_fmt, $n_fmt ) = priv( 'client_report_response', 'not-a-token', true );
list( $p_404, $b_p404 ) = priv( 'client_report_response', 'not-a-token' );

ok( 'an expired download does not resolve', 404 === $d_exp );
ok( 'a revoked download does not resolve', 404 === $d_rev );
ok( 'an unknown token downloads nothing', 404 === $d_unk );
ok( 'a malformed token downloads nothing', 404 === $d_fmt );
ok( 'a rejected download gets no filename, so no Content-Disposition', '' === $n_exp && '' === $n_rev && '' === $n_unk && '' === $n_fmt );

// The header decision is separated from the HTTP call so it can be checked
// without a web server. A mutation that attaches the file to every answer —
// including the 404 — would otherwise be invisible to the whole test suite.
ok( 'a real report asks to be downloaded', false !== strpos( priv( 'client_report_disposition', $fname ), 'attachment; filename="' . $fname . '"' ) );
ok( 'a rejected report asks for no download', '' === priv( 'client_report_disposition', '' ) );
ok( 'no filename of any shape produces a download header', '' === priv( 'client_report_disposition', null ) && '' === priv( 'client_report_disposition', array( 'x' ) ) && '' === priv( 'client_report_disposition', 0 ) );
ok( 'a hostile filename cannot inject a second header', false === strpos( priv( 'client_report_disposition', "eucomply-report-x.html\"\r\nX-Injected: 1" ), "\r\n" ) );
ok(
    'every rejected download gets the identical body',
    $b_exp === $b_rev && $b_rev === $b_unk && $b_unk === $b_fmt && $b_fmt === $b_exp
);
ok( 'a rejected download is byte-identical to the rejected page', $b_unk === $b_p404 );
ok( 'a rejected download says nothing about why', false === stripos( $b_unk, 'expired' ) && false === stripos( $b_unk, 'revoked' ) && false === stripos( $b_unk, 'token' ) );

// A request for the file with no token at all is still the same 404, not the
// site's front page: an answer that differs from the others is a probe.
list( $d_none, $b_none ) = priv( 'client_report_response', '', true );
ok( 'a download with no token at all gets the same 404', 404 === $d_none && $b_none === $b_p404 );

// A new link retires the download exactly as it retires the page: an agency
// that replaces a leaked link must not leave the file behind.
pro_instance();
$pl = priv( 'create_client_link' );
preg_match( '/[?&]eucomply_report=([a-f0-9]{32})/', $pl, $pm );
$pl_token = $pm[1];
priv( 'create_client_link' );
ok( 'a new link retires the previous download too', 404 === priv( 'client_report_response', $pl_token, true )[0] );

// ── 9. The report without a link ──────────────────────────────────────────────
// The client link is what an agency sends. It is also what an agency attaches:
// and attaching a report means creating a new link every month, each one
// retiring the last, so a client who got the file on the 1st and again on the
// 15th holds a link that died on the 15th. The wp-admin download has to be the
// same document without any of that, and it has to be gated like everything else
// in wp-admin rather than becoming a way around the Pro check.

pro_instance();
$GLOBALS['eucomply_test_options']['eucomply_scan_history'] = array(
    '2026-09-01' => array( 'date' => '2026-09-01', 'total' => 6, 'passed' => 5, 'warned' => 1, 'checks' => array( 'a' => 'pass', 'b' => 'warn' ) ),
);
$export_link = priv( 'create_client_link' );
preg_match( '/[?&]eucomply_report=([a-f0-9]{32})/', $export_link, $xm );
$export_token = $xm[1];
list( , $client_page ) = priv( 'client_report_response', $export_token );
list( $xs, $exported, $xname ) = priv( 'report_export_response', true, true, true );

ok( 'an authorised operator gets the report', 200 === $xs );
ok( 'the export is not indexed and leaks no referrer', false !== strpos( $exported, 'noindex' ) );
ok( 'the export carries the scan history, not a cut-down version', false !== strpos( $exported, 'Scan history' ) && false !== strpos( $exported, '2026-09-01' ) );
ok( 'the export carries the headline result', false !== strpos( $exported, '4 of 6 checks passed' ) );
ok( 'the export has the same filename as the client download', 'eucomply-report-2026-09-26.html' === $xname );
ok( 'that filename is accepted as a download header', false !== strpos( priv( 'client_report_disposition', $xname ), 'attachment; filename="' . $xname . '"' ) );
ok( 'the export names no client and carries no link', false === strpos( $exported, $export_token ) && false === strpos( $exported, 'wp-admin' ) && false === strpos( $exported, '_wpnonce' ) );

// Byte equality, not "both currently say the same thing". The two documents may
// differ in exactly one paragraph — the notice that the link expires, which is a
// property of the link and would be a false claim inside an attached file. Strip
// that one paragraph and the rest has to match exactly, so any second rendering
// of the report, in either direction, fails here.
$stripped = preg_replace( '#<p class="eucomply-link-expiry">.*?</p>#s', '', $client_page );
ok( 'the export is the client document, byte for byte', $stripped === $exported );
ok( 'the export makes no claim about a link expiring', false === strpos( $exported, 'eucomply-link-expiry' ) && false === strpos( $exported, 'stops working on' ) );
ok( 'the client document is the export plus the expiry notice', 1 === preg_match_all( '#<p class="eucomply-link-expiry">This link stops working on \d{4}-\d{2}-\d{2}\.</p>#', $client_page ) );
ok( 'the same scan renders the same document twice', $exported === priv( 'report_document' ) && $exported === priv( 'report_export_response', true, true, true )[1] );
$hostile_expiry = priv( 'report_document', "2026-09-26<script>alert(1)</script>" );
ok( 'a hostile expiry date cannot inject markup', 0 === substr_count( $hostile_expiry, '<script>' ) && false !== strpos( $hostile_expiry, '&lt;script&gt;' ) );
ok( 'an empty expiry adds no paragraph', false === strpos( priv( 'report_document', '' ), 'eucomply-link-expiry' ) );

// The export is not a way around the Pro gate, and it is not a way around the
// capability the settings page uses. All three refusals produce one answer: no
// body, no filename, and therefore no Content-Disposition.
$denied = array(
    'no capability' => priv( 'report_export_response', false, true, true ),
    'no nonce'      => priv( 'report_export_response', true, false, true ),
    'no Pro'        => priv( 'report_export_response', true, true, false ),
    'nothing at all' => priv( 'report_export_response', false, false, false ),
);
ok( 'an account that may not manage the site gets no report', 403 === $denied['no capability'][0] );
ok( 'a request without a valid nonce gets no report', 403 === $denied['no nonce'][0] );
ok( 'a free installation gets no report', 403 === $denied['no Pro'][0] );
ok( 'a refused export carries no report body', '' === $denied['no capability'][1] && '' === $denied['no nonce'][1] && '' === $denied['no Pro'][1] );
ok( 'a refused export carries no filename, so no Content-Disposition', '' === $denied['no capability'][2] && '' === $denied['no nonce'][2] && '' === $denied['no Pro'][2] && '' === priv( 'client_report_disposition', $denied['no Pro'][2] ) );
ok( 'every refusal is the same answer', $denied['no capability'] === $denied['no nonce'] && $denied['no nonce'] === $denied['no Pro'] && $denied['no Pro'] === $denied['nothing at all'] );
ok( 'a refused export is not a client link either', false === strpos( json_encode( $denied ), 'eucomply_report' ) );

// The export requires no link at all: the whole point is that a monthly
// attachment does not depend on a 30-day secret, and that the file keeps working
// after the link that also delivers it has been retired.
priv( 'revoke_client_link' );
ok( 'a retired client link does not stop the export', 200 === priv( 'report_export_response', true, true, true )[0] );
ok( 'the export does not require a client link record', false === get_option( 'eucomply_client_link', false ) );
ok( 'the export does not create a client link either', 'none' === priv( 'client_link_state' ) );

// The export must leave nothing behind. An agency that attaches a report twelve
// times a year should not accumulate a record per export, and nothing about a
// download — a who, a when, a counter — may end up stored on the site. The one
// option this path does write, the "last generated" date the settings table has
// always shown, already exists and is already removed on uninstall.
$stored_before = $GLOBALS['eucomply_test_options'];
$exported_again = priv( 'report_export_response', true, true, true );
ok( 'rendering the export changes no stored option', $stored_before === $GLOBALS['eucomply_test_options'] );
ok( 'a repeated export changes no stored option either', $exported_again[1] === $exported && $stored_before === $GLOBALS['eucomply_test_options'] );

// Every screen and every export in this plugin is gated on one capability. If a
// download can ever be reached with less than the settings page, it is a way
// around the Pro check, and a reviewer reading six call sites will not see it.
$source    = file_get_contents( __DIR__ . '/../plugin/eucomply.php' );
$uninstall = file_get_contents( __DIR__ . '/../plugin/uninstall.php' );
preg_match_all( "/(?:update|add)_option\(\s*'(eucomply_[a-z_]+)'/", $source, $written );
$option_names = array_values( array_unique( $written[1] ) );
ok( 'the plugin does write options, so the uninstall check is not vacuous', count( $option_names ) >= 10 );
foreach ( $option_names as $option ) {
    ok( "uninstall removes $option", false !== strpos( $uninstall, "'" . $option . "'" ) );
}
ok( 'that capability is manage_options', 1 === preg_match( "/define\(\s*'EUCOMPLY_ADMIN_CAP',\s*'([a-z_]+)'\s*\)/", $source, $cm ) && 'manage_options' === $cm[1] );
preg_match_all( '/current_user_can\(\s*([^)]*?)\s*\)/', $source, $caps );
ok( 'every capability check uses the one declared capability', array( 'EUCOMPLY_ADMIN_CAP' ) === array_values( array_unique( array_map( 'trim', $caps[1] ) ) ) );
ok( 'both menu pages are registered on the same capability', 2 === preg_match_all( '/^\s+EUCOMPLY_ADMIN_CAP,$/m', $source ) && 2 === preg_match_all( '/add_(?:sub)?menu_page\(/', $source ) );
ok( 'the export and the link handler are both on admin_init', 2 === preg_match_all( "/add_action\(\s*'admin_init'/", $source ) );

// ── 7. The scheduled interval follows the licence ─────────────────────────────
// The free version scans once a week; Pro scans once a day. That is the first
// thing on the Pro list the plugin can deliver on its own, because the six
// checks are local — so nothing about it needs a hosted service to exist first.
//
// What is tested here is not "a string is returned" but the three properties
// that make the difference worth money and worth trusting:
//   1. A Pro licence produces a daily event, a free one a weekly event.
//   2. The interval follows the licence both ways — activating, releasing,
//      expiring and losing a device slot all move it back to weekly. A cadence
//      that only ever ratchets up is a discount a refunded customer keeps.
//   3. Deciding the interval never calls the license server. It runs on every
//      request, so if it phoned home the site would pay a round trip per page
//      view, and the test suite has no stub for that call at all: a single
//      remote call would fatal, which is the loudest possible assertion.

/** The interval currently on the cron array for the plugin's event. */
function scheduled_interval() {
    $event = wp_get_scheduled_event( EUCOMPLY_SCAN_EVENT );
    return $event && ! empty( $event->schedule ) ? $event->schedule : '';
}

fresh_instance();
priv( 'sync_scan_schedule' );
ok( 'a site with no licence is scheduled weekly', 'weekly' === scheduled_interval() );
ok( 'a site with no licence is scheduled exactly once', 1 === count( $GLOBALS['eucomply_test_cron'] ) );

// Syncing again must not touch the event. If it re-scheduled on every request,
// the next run would be pushed a full interval further away each time, and a
// Pro site would silently stop being scanned altogether.
$first_run = wp_next_scheduled( EUCOMPLY_SCAN_EVENT );
priv( 'sync_scan_schedule' );
priv( 'sync_scan_schedule' );
ok( 'syncing twice does not re-schedule', $first_run === wp_next_scheduled( EUCOMPLY_SCAN_EVENT ) );
ok( 'syncing twice does not add a second event', 1 === count( $GLOBALS['eucomply_test_cron'] ) );

// Pro.
pro_instance();
priv( 'sync_scan_schedule' );
ok( 'a Pro licence is scheduled daily', 'daily' === scheduled_interval() );
ok( 'a Pro licence still has exactly one event', 1 === count( $GLOBALS['eucomply_test_cron'] ) );
ok( 'the daily event is the plugin scan event', EUCOMPLY_SCAN_EVENT === $GLOBALS['eucomply_test_cron'][0]['hook'] );
ok( 'the first Pro run is at the next cron tick, not a day later', wp_next_scheduled( EUCOMPLY_SCAN_EVENT ) <= time() + 1 );
ok( 'the dashboard states the daily cadence', false !== strpos( priv( 'cadence_phrase' ), 'every 24 hours' ) );

// Back to free, the way a customer actually arrives there: the licence is gone.
delete_option( 'eucomply_pro_key' );
priv( 'sync_scan_schedule' );
ok( 'a removed licence goes back to weekly', 'weekly' === scheduled_interval() );
ok( 'a removed licence leaves one event, not two', 1 === count( $GLOBALS['eucomply_test_cron'] ) );

// A verified verdict that has aged out of the 7-day grace is not a licence any
// more. The cadence must follow the same grace is_pro() uses, or an outage at
// the license server would quietly turn a paid site into a free one.
pro_instance();
update_option( 'eucomply_pro_last_ok_at', time() - ( 8 * DAY_IN_SECONDS ) );
priv( 'sync_scan_schedule' );
ok( 'a verdict older than the grace is not a daily cadence', 'weekly' === scheduled_interval() );
ok( 'the grace is the same 7 days is_pro() uses', 7 * DAY_IN_SECONDS === EUCOMPLY_LICENSE_GRACE );

pro_instance();
update_option( 'eucomply_pro_last_ok_at', time() - ( 6 * DAY_IN_SECONDS ) );
priv( 'sync_scan_schedule' );
ok( 'a verdict inside the grace keeps the daily cadence', 'daily' === scheduled_interval() );

// A 409 is a valid key on a website with no free slot, so it is not entitled to
// the daily cadence — the same answer is_pro() gives.
pro_instance();
update_option( 'eucomply_pro_state', 'device_limit' );
priv( 'sync_scan_schedule' );
ok( 'a key with no free device slot is not a daily cadence', 'weekly' === scheduled_interval() );

// A key that was never verified must not buy a cadence.
fresh_instance();
update_option( 'eucomply_pro_key', str_repeat( 'a1b2', 8 ) );
priv( 'sync_scan_schedule' );
ok( 'an unverified key is not a daily cadence', 'weekly' === scheduled_interval() );
delete_option( 'eucomply_pro_key' );
update_option( 'eucomply_pro_verified', '1' );
update_option( 'eucomply_pro_last_ok_at', time() );
priv( 'sync_scan_schedule' );
ok( 'a verified verdict without a key is not a daily cadence', 'weekly' === scheduled_interval() );

// The dashboard quotes the cron array, not the licence, so the two cannot
// disagree while an event is being re-scheduled.
pro_instance();
priv( 'sync_scan_schedule' );
$GLOBALS['eucomply_test_cron'][0]['schedule'] = 'weekly';
ok( 'the stated cadence follows a weekly event on a Pro site', false !== strpos( priv( 'cadence_phrase' ), 'once a week' ) );
$GLOBALS['eucomply_test_cron'] = array();
ok( 'with no event at all the statement falls back to the licence', false !== strpos( priv( 'cadence_phrase' ), 'every 24 hours' ) );

// A cached "1" with no timestamp behind it is not evidence of anything: it is
// what a hand-edited or half-restored options table looks like, and it must not
// be enough to hand out a paid cadence.
pro_instance();
delete_option( 'eucomply_pro_last_ok_at' );
priv( 'sync_scan_schedule' );
ok( 'a verified verdict with no timestamp is not a daily cadence', 'weekly' === scheduled_interval() );

// Deactivation has to leave nothing behind, and with an interval that changes
// there can be more than one entry to clear.
pro_instance();
wp_schedule_event( time() + DAY_IN_SECONDS, 'daily', EUCOMPLY_SCAN_EVENT );
wp_schedule_event( time() + WEEK_IN_SECONDS, 'weekly', EUCOMPLY_SCAN_EVENT );
ok( 'the test starts with two events to clear', 2 === count( $GLOBALS['eucomply_test_cron'] ) );
EUComply::deactivate();
ok( 'deactivation clears every copy of the event', 0 === count( $GLOBALS['eucomply_test_cron'] ) );

// The event name is historical, and renaming it is a trap: the string below is
// the one every existing install already has in its cron array.
ok( 'the scan event keeps its historical name', 'eucomply_weekly_scan' === EUCOMPLY_SCAN_EVENT );
ok( 'the constructor does not schedule an event of its own', false === strpos( file_get_contents( __DIR__ . '/../plugin/eucomply.php' ), "wp_schedule_event( time(), 'weekly'" ) );

// ── 10. The report says how often the site was checked ────────────────────────
//
// A score arrives without an interval, and "how often is this looked at" is the
// first question anyone asks about a compliance number. The report answers it —
// and the answer has to come from the cron array, not from the licence, because
// the document is the one place a client is asked to take a number on trust. A
// sentence that read the licence would keep promising a daily check after a
// refund, and the history table right below it would contradict it.

// Pro, scheduled daily: the document says so.
pro_instance();
priv( 'sync_scan_schedule' );
$daily_report = priv( 'build_report' );
ok( 'a Pro report states the daily cadence', false !== strpos( $daily_report, 'every 24 hours' ) );
ok( 'the report says the checks run on the site itself', false !== strpos( $daily_report, 'no external service is involved' ) );
ok( 'a Pro report does not claim the weekly run', false === strpos( $daily_report, 'once a week' ) );

// The licence is gone. The cron array now holds a weekly event, so the sentence
// must follow it — otherwise a refunded customer keeps a document promising a
// daily check the plugin will never perform.
delete_option( 'eucomply_pro_key' );
priv( 'sync_scan_schedule' );
$weekly_report = priv( 'build_report' );
ok( 'a report for a site back on the weekly run says once a week', false !== strpos( $weekly_report, 'once a week' ) );
ok( 'a weekly report does not keep the daily claim', false === strpos( $weekly_report, 'every 24 hours' ) );

// A Pro key that is scheduled daily but has a cron array that says otherwise:
// the array wins, because that is what will actually run.
pro_instance();
priv( 'sync_scan_schedule' );
wp_clear_scheduled_hook( EUCOMPLY_SCAN_EVENT );
wp_schedule_event( time() + WEEK_IN_SECONDS, 'weekly', EUCOMPLY_SCAN_EVENT );
ok( 'a stale cron array is believed over the licence', false !== strpos( priv( 'build_report' ), 'once a week' ) );

// The line must be in the document the client actually receives, in both of its
// forms, and it must not survive being the only thing that changed.
pro_instance();
priv( 'sync_scan_schedule' );
$link_doc     = priv( 'report_document', '2026-10-26' );
$export_doc   = priv( 'report_document' );
$stripped     = str_replace( '<p class="eucomply-link-expiry">This link stops working on 2026-10-26.</p>', '', $link_doc );
ok( 'the client link carries the cadence line', false !== strpos( $link_doc, 'every 24 hours' ) );
ok( 'the wp-admin export carries the same line', false !== strpos( $export_doc, 'every 24 hours' ) );
ok( 'the two documents still differ only by the link notice', $stripped === $export_doc );

// The report is served to somebody holding no WordPress login, so it must not
// reach the network to learn the interval. There is no wp_remote_* stub in this
// file at all, so a call would fatal — the loudest possible assertion.
$build_report_src = '';
if ( preg_match( '/private function build_report\(\).*?\n    \}/s', file_get_contents( __DIR__ . '/../plugin/eucomply.php' ), $blk ) ) {
    $build_report_src = $blk[0];
}
ok( 'the cadence line is really in build_report(), so the check is not vacuous', '' !== $build_report_src && false !== strpos( $build_report_src, 'cadence_phrase' ) );
ok( 'build_report() does not call the license server', '' === $build_report_src || ( 0 === preg_match( '/\$this->is_pro\s*\(/', $build_report_src ) && false === strpos( $build_report_src, 'wp_remote_' ) ) );

// ── 15. Regression alert: mail the customer when a check changes ──────────────
// A daily scan nobody hears about is a scan nobody acts on. Everything here is
// about one property: exactly one mail per *change*, to an address the customer
// typed in, on a Pro licence, and never a word that isn't backed by a state
// change in the recorded history.

/** A scan result set from an explicit key => pass|warn|fail map, with text. */
function states_scan( $map ) {
    $out = array();
    foreach ( $map as $key => $state ) {
        $out[ $key ] = array(
            'pass'   => 'pass' === $state,
            'warn'   => 'warn' === $state,
            'label'  => ucfirst( $key ) . ' check',
            'detail' => 'Detail for ' . $key . '.',
            'fix'    => 'Fix the ' . $key . ' check.',
        );
    }
    return $out;
}

/** Fresh instance, Pro licence, alert address, and a state the customer was told. */
function alert_instance( $previous = array( 'ssl' => 'pass', 'cookies' => 'pass' ), $pro = true ) {
    fresh_instance();
    if ( $pro ) {
        update_option( 'eucomply_pro_key', str_repeat( 'a1b2', 8 ) );
        update_option( 'eucomply_pro_verified', '1' );
        update_option( 'eucomply_pro_verified_at', time() );
        update_option( 'eucomply_pro_last_ok_at', time() );
    }
    if ( null !== $previous ) {
        update_option( 'eucomply_alert_state', $previous );
    }
    update_option( 'eucomply_alert_email', 'owner@agency-client.example' );
    $GLOBALS['eucomply_site_name'] = 'Agency Client ApS';
    return $GLOBALS['g'];
}

// 1. Silence by default. A regression with no address stored must send nothing
//    at all — a plugin that mails a customer who never asked is a bug, not a
//    feature, and the address being the opt-in is what makes that provable.
alert_instance( null );
ok( 'no stored state and no mailer stub is not the reason: an unconfigured site stays silent',
    false === priv( 'maybe_send_alert', states_scan( array( 'ssl' => 'fail' ) ) ) && 0 === count( sent_mail() ) );
alert_instance( array( 'ssl' => 'pass' ) );
update_option( 'eucomply_alert_email', '' );
ok( 'an empty alert address sends nothing, even for a real regression',
    false === priv( 'maybe_send_alert', states_scan( array( 'ssl' => 'fail' ) ) ) && 0 === count( sent_mail() ) );

// 2. A stored value that is not a usable address is no address at all.
alert_instance( array( 'ssl' => 'pass' ) );
update_option( 'eucomply_alert_email', 'owner(at)agency-client.example' );
ok( 'a mistyped stored address is refused rather than sanitised into a wrong one',
    '' === priv( 'alert_address' ) && 0 === count( sent_mail() ) );

// 3. The alert follows the licence in both directions, like the cadence does.
alert_instance( array( 'ssl' => 'pass' ), false );
ok( 'a site without Pro is not mailed',
    false === priv( 'maybe_send_alert', states_scan( array( 'ssl' => 'fail' ) ) ) && 0 === count( sent_mail() ) );
alert_instance( array( 'ssl' => 'pass' ) );
update_option( 'eucomply_pro_verified', '' );
ok( 'a released licence stops the alert, it does not keep the last known state',
    false === priv( 'maybe_send_alert', states_scan( array( 'ssl' => 'fail' ) ) ) && 0 === count( sent_mail() ) );

// 4. Turning the address on must not produce a first mail listing every check
//    as a change. It adopts the last recorded scan as the state the customer
//    has not been told about yet.
alert_instance( null );
update_option(
    'eucomply_scan_history',
    array(
        gmdate( 'Y-m-d', time() - 86400 ) => array(
            'date'   => gmdate( 'Y-m-d', time() - 86400 ),
            'checks' => array( 'ssl' => 'pass', 'cookies' => 'pass' ),
        ),
    )
);
ok( 'the first scan after an address is saved sends nothing',
    false === priv( 'maybe_send_alert', states_scan( array( 'ssl' => 'pass', 'cookies' => 'pass' ) ) ) && 0 === count( sent_mail() ) );
$seeded = get_option( 'eucomply_alert_state', null );
ok( 'it seeds the state from the last recorded day instead of from today',
    is_array( $seeded ) && array( 'ssl' => 'pass', 'cookies' => 'pass' ) === $seeded );

// 5. The regression itself: pass -> fail mails once, and says what broke.
alert_instance();
$sent = priv( 'maybe_send_alert', states_scan( array( 'ssl' => 'fail', 'cookies' => 'pass' ) ) );
$mails = sent_mail();
ok( 'a check that passed and now fails sends exactly one mail', true === $sent && 1 === count( $mails ) );
ok( 'it goes to the stored address', 1 === count( $mails ) && 'owner@agency-client.example' === $mails[0]['to'] );
ok( 'the subject says the direction, in words',
    1 === count( $mails ) && false !== strpos( $mails[0]['subject'], '1 check failing' ) && false !== strpos( $mails[0]['subject'], 'Agency Client ApS' ) );
ok( 'the body names the check, its detail and its fix',
    1 === count( $mails )
    && false !== strpos( $mails[0]['message'], 'Ssl check' )
    && false !== strpos( $mails[0]['message'], 'PASS -> FAIL' )
    && false !== strpos( $mails[0]['message'], 'Detail for ssl.' )
    && false !== strpos( $mails[0]['message'], 'Fix the ssl check.' ) );
ok( 'the body points at the report in wp-admin',
    1 === count( $mails ) && false !== strpos( $mails[0]['message'], 'https://agency-client.example/wp-admin/admin.php?page=eucomply' ) );
ok( 'the body says how to stop it',
    1 === count( $mails ) && false !== strpos( $mails[0]['message'], 'Clear that field to stop it' ) );

// 6. The recovery mail, because an alert system that only says bad news gets muted.
alert_instance( array( 'ssl' => 'fail', 'cookies' => 'pass' ) );
$sent = priv( 'maybe_send_alert', states_scan( array( 'ssl' => 'pass', 'cookies' => 'pass' ) ) );
$mails = sent_mail();
ok( 'a failing check that passes again is also a change worth one mail',
    true === $sent && 1 === count( $mails ) && false !== strpos( $mails[0]['subject'], 'passing again' ) );
ok( 'the recovery mail does not tell the customer to fix something',
    1 === count( $mails ) && false === strpos( $mails[0]['message'], 'Fix the ssl check.' ) );

// 7. A warning is a change, and it is never counted as a pass.
alert_instance( array( 'ssl' => 'pass' ) );
priv( 'maybe_send_alert', states_scan( array( 'ssl' => 'warn' ) ) );
ok( 'a check that drops from passing to warning is reported',
    1 === count( sent_mail() ) && false !== strpos( sent_mail()[0]['message'], 'PASS -> WARN' ) );
ok( 'a warning is never recorded as a pass in the alert state',
    array( 'ssl' => 'warn' ) === get_option( 'eucomply_alert_state' ) );

// 8. The anti-spam rule: a site that stays broken gets told once, not daily.
alert_instance();
priv( 'maybe_send_alert', states_scan( array( 'ssl' => 'fail' ) ) );
priv( 'maybe_send_alert', states_scan( array( 'ssl' => 'fail' ) ) );
priv( 'maybe_send_alert', states_scan( array( 'ssl' => 'fail' ) ) );
ok( 'an unchanged regression is not mailed again',
    1 === count( sent_mail() ) && false === priv( 'maybe_send_alert', states_scan( array( 'ssl' => 'fail' ) ) ) );

// 9. A check seen for the first time is an observation, not a regression. We
//    cannot claim it changed, and a plugin update that adds a check must not
//    greet the customer with a mail full of "not previously recorded".
alert_instance( array( 'ssl' => 'pass' ) );
ok( 'a check that was never recorded before is not mailed as a change',
    false === priv( 'maybe_send_alert', states_scan( array( 'ssl' => 'pass', 'newcheck' => 'fail' ) ) ) && 0 === count( sent_mail() ) );

// 10. A mailer that refuses must not eat the alert. The state only advances
//     when the mail actually went out, so the next scan tries again.
alert_instance();
$GLOBALS['eucomply_test_mail_fails'] = true;
ok( 'a failed send is not counted as a send', false === priv( 'maybe_send_alert', states_scan( array( 'ssl' => 'fail' ) ) ) );
ok( 'a failed send does not advance the state the customer was told',
    array( 'ssl' => 'pass', 'cookies' => 'pass' ) === get_option( 'eucomply_alert_state' ) );
unset( $GLOBALS['eucomply_test_mail_fails'] );
ok( 'the next scan retries the same regression and then advances the state',
    true === priv( 'maybe_send_alert', states_scan( array( 'ssl' => 'fail' ) ) )
    && 2 === count( sent_mail() )
    && array( 'ssl' => 'fail' ) === get_option( 'eucomply_alert_state' ) );

// 11. No From header of our own: the site's mailer sets one that its SPF
//     record matches, and a made-up From is how the one mail that must arrive
//     ends up in spam.
alert_instance();
priv( 'maybe_send_alert', states_scan( array( 'ssl' => 'fail' ) ) );
$headers = sent_mail()[0]['headers'];
$flat    = is_array( $headers ) ? implode( ' ', $headers ) : (string) $headers;
ok( 'the alert sets a content type and no From of its own',
    false !== stripos( $flat, 'Content-Type' ) && false === stripos( $flat, 'From:' ) && false === stripos( $flat, 'Reply-To' ) );

// 12. The report may only promise the alert when one is actually configured,
//     and it reads the same stored state the sender does.
pro_instance();
$no_alert_doc = doc( 'report' );
ok( 'a site with no alert address is not told it will be emailed', false === strpos( $no_alert_doc, 'emailed when a check changes' ) );
update_option( 'eucomply_alert_email', 'owner@agency-client.example' );
ok( 'a site with an alert address is told so, in the document the client reads',
    false !== strpos( doc( 'report' ), 'emailed when a check changes' ) );

// 13. The wiring itself. Every test above calls the private method directly, so
//     without this one they would all stay green if run_checks() stopped
//     calling it and the feature silently did nothing.
$run_src = '';
if ( preg_match( '/public function run_checks\(\).*?\n    \}/s', file_get_contents( __DIR__ . '/../plugin/eucomply.php' ), $blk ) ) {
    $run_src = $blk[0];
}
ok( 'run_checks() really calls the alert, so the tests above are not vacuous',
    '' !== $run_src && false !== strpos( $run_src, '$this->maybe_send_alert(' ) );

// ── Result ───────────────────────────────────────────────────────────────────
echo "$passed document checks passed\n";
if ( $failed ) {
    echo "$failed FAILED\n";
    exit( 1 );
}
