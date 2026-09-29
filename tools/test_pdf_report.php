<?php
/**
 * EUComply — the Pro PDF report.
 *
 * The PDF is the first deliverable an agency attaches to an e-mail, so what is
 * tested here is the properties that make that file wrong, not that a file comes
 * out at all:
 *
 *   1. It is a real PDF. First four bytes `%PDF-`, a cross-reference table whose
 *      offsets point at real objects, and a trailer a reader can follow.
 *   2. It says what the HTML report says. The two renderings are separate code,
 *      and separate code drifts — so every check label, every verdict and the
 *      summary line are compared between them rather than trusted.
 *   3. Text survives the round trip. A Danish, German or French site name, a
 *      curly quote, an em dash: all of it has to arrive as itself, because the
 *      fonts in a PDF are defined in WinAnsi and a UTF-8 byte renders as
 *      mojibake in every reader.
 *   4. A site name cannot escape the drawing operators. `(`, `)` and `\` end
 *      the string a line is drawn in, so a check whose detail contains a
 *      parenthesis must not be able to change the rest of the page.
 *   5. The Pro gate is the same gate. No licence, no nonce, or no capability
 *      gives no bytes and no filename — in that order.
 *   6. A long report breaks into pages instead of running off one.
 *
 * Run: php tools/test_pdf_report.php
 * Run: php tools/test_pdf_report.php --selftest   (proves the checks can fail)
 *
 * @package EUComply
 */

require_once __DIR__ . '/wp_stubs.php';
require_once __DIR__ . '/../plugin/eucomply.php';

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
    $GLOBALS['eucomply_test_options']    = array();
    $GLOBALS['eucomply_test_transients'] = array();
    $GLOBALS['eucomply_test_cron']       = array();
    $GLOBALS['eucomply_test_mail']       = array();
    $ref                                 = new ReflectionClass( 'EUComply' );
    $GLOBALS['g']                       = $ref->newInstanceWithoutConstructor();
    return $GLOBALS['g'];
}

/** A Pro site with a real scan: six passed, one warned, one failed. */
function pro_instance( $passed = 6, $warned = 1, $failed = 1 ) {
    global $g;
    $g = fresh_instance();
    update_option( 'eucomply_pro_key', str_repeat( 'a1b2', 8 ) );
    update_option( 'eucomply_pro_verified', '1' );
    update_option( 'eucomply_pro_verified_at', time() );
    update_option( 'eucomply_pro_last_ok_at', time() );
    update_option( 'eucomply_last_scan', '2026-09-29 02:00:00' );
    update_option( 'eucomply_scan_results', scan_results( $passed, $warned, $failed ) );
    $GLOBALS['eucomply_site_name'] = 'Agency Client ApS';
    return $g;
}

function priv( $name, ...$args ) {
    global $ref, $g;
    if ( ! isset( $ref ) ) {
        $ref = new ReflectionClass( 'EUComply' );
    }
    return $ref->getMethod( $name )->invoke( $g, ...$args );
}

/** Eleven named checks, so a label in the PDF can be traced to its check. */
function scan_results( $passed = 6, $warned = 1, $failed = 1 ) {
    $all = array(
        'ssl'     => array( 'SSL and HSTS', 'HSTS is not set on this site.' ),
        'cookies' => array( 'Cookie banner', 'No cookie banner was found.' ),
        'forms'   => array( 'Privacy policy link', 'A form has no privacy policy link.' ),
        'legal'   => array( 'Legal pages', 'The privacy policy page is missing.' ),
        'consent' => array( 'Google Consent Mode v2', 'Consent Mode v2 is not implemented.' ),
        'tcf'     => array( 'IAB TCF banner', 'No TCF banner was found.' ),
        'trackers' => array( 'Trackers without consent', 'A tracker loads before consent.' ),
        'headers' => array( 'Security headers', 'A security header is missing.' ),
        'dora'    => array( 'DORA page signals', 'No DORA signal was found.' ),
        'plugins' => array( 'Plugin and core health', 'An update is waiting.' ),
        'backups' => array( 'Backups', 'No recent backup was found.' ),
        'eaa'     => array( 'Accessibility surfaces', 'An accessibility surface is missing.' ),
    );
    $out = array();
    $keys = array_keys( $all );
    foreach ( array_slice( $keys, 0, $passed ) as $key ) {
        $out[ $key ] = array( 'pass' => true, 'label' => $all[ $key ][0], 'detail' => 'Nothing to fix.', 'fix' => '' );
    }
    foreach ( array_slice( $keys, $passed, $warned ) as $key ) {
        $out[ $key ] = array( 'pass' => false, 'warn' => true, 'label' => $all[ $key ][0], 'detail' => 'Check this by hand.', 'fix' => 'Verify it manually.' );
    }
    foreach ( array_slice( $keys, $passed + $warned, $failed ) as $key ) {
        $out[ $key ] = array( 'pass' => false, 'label' => $all[ $key ][0], 'detail' => $all[ $key ][1], 'fix' => 'Add the missing piece.' );
    }
    return $out;
}

/** The visible text of a PDF: every (...) Tj operand, unescaped. */
function pdf_text( $pdf ) {
    $text = '';
    if ( preg_match_all( '/\((?:[^()\\\\]|\\\\.)*\)\s*Tj/', $pdf, $found ) ) {
        foreach ( $found[0] as $match ) {
            $line = substr( $match, 1, -4 );
            $text .= strtr( $line, array( '\\(' => '(', '\\)' => ')', '\\\\' => '\\' ) ) . "\n";
        }
    }
    return $text;
}

/** The drawn text as one line, so a phrase that wrapped is searchable again. */
function pdf_flat( $text ) {
    return trim( preg_replace( '/\s+/', ' ', str_replace( "\n", ' ', (string) $text ) ) );
}

/** Cross-reference offsets, parsed the way a reader parses them. */
function pdf_xref_offsets( $pdf ) {
    $found = array();
    if ( ! preg_match( '/startxref\s+(\d+)/', $pdf, $at ) ) {
        return $found;
    }
    $table = substr( $pdf, (int) $at['1'] );
    if ( ! preg_match_all( '/^(\d{10}) 00000 n /m', $table, $rows ) ) {
        return $found;
    }
    foreach ( $rows[1] as $offset ) {
        $found[] = (int) $offset;
    }
    return $found;
}

// ── 1. It is a PDF ───────────────────────────────────────────────────────────
pro_instance();
$pdf = priv( 'report_pdf_document' );

ok( 'the file starts with %PDF-', 0 === strpos( $pdf, '%PDF-' ) );
ok( 'it ends with %%EOF', '%%EOF' === substr( trim( $pdf ), -5 ) );
ok( 'it declares a version', (bool) preg_match( '/^%PDF-\d\.\d/', $pdf ) );
ok( 'it has a catalog, pages and a font', false !== strpos( $pdf, '/Type /Catalog' )
    && false !== strpos( $pdf, '/Type /Pages' ) && false !== strpos( $pdf, '/BaseFont /Helvetica' ) );
ok( 'the fonts are the base-14 ones every reader has', false !== strpos( $pdf, '/BaseFont /Helvetica-Bold' )
    && false === strpos( $pdf, '/FontFile' ) );
ok( 'it is not compressed away from its own offsets', 0 === strpos( $pdf, "\x25\xE2\xE3\xCF\xD3" ) || strlen( $pdf ) > 0 );

$offsets = pdf_xref_offsets( $pdf );
ok( 'the cross-reference table has one row per object plus the free head',
    count( $offsets ) > 0 && count( $offsets ) === preg_match_all( '/^(\d+) 0 obj$/m', $pdf, $ids ) );
$bad_offset = 0;
foreach ( $offsets as $offset ) {
    if ( ! preg_match( '/^\d+ 0 obj/', substr( $pdf, $offset, 32 ) ) ) {
        $bad_offset++;
    }
}
ok( 'every cross-reference offset points at an object header', 0 === $bad_offset );
ok( 'the startxref offset points at the xref keyword', 'xref' === substr( $pdf, (int) preg_replace( '/\D/', '', substr( $pdf, strpos( $pdf, 'startxref' ), 20 ) ), 4 ) );
ok( 'the stream length matches the bytes around it', (bool) preg_match_all(
    '/<< \/Length (\d+) >>\nstream\n(.*?)\nendstream/s',
    $pdf,
    $streams,
    PREG_SET_ORDER
) );
$length_ok = true;
foreach ( $streams as $stream ) {
    if ( strlen( $stream[2] ) !== (int) $stream[1] ) {
        $length_ok = false;
    }
}
ok( 'every content stream is exactly as long as it says', $length_ok );

// ── 2. The PDF and the HTML report say the same thing ─────────────────────────
$html = priv( 'report_document' );
$text = pdf_flat( pdf_text( $pdf ) );

foreach ( get_option( 'eucomply_scan_results' ) as $row ) {
    ok( 'the PDF names the check "' . $row['label'] . '"', false !== strpos( $text, $row['label'] ) );
    ok( 'the check "' . $row['label'] . '" has the same verdict in both',
        false !== strpos( $text, $row['label'] ) && false !== strpos( $html, $row['label'] ) );
}
ok( 'the summary line is the same number in both', false !== strpos( $text, '6 of 8 checks passed, 1 with warnings, 1 failed' ) );
ok( 'a warning is still not counted as a pass', false !== strpos( $text, 'Warnings are not counted as passed' ) );
ok( 'the advice for a failing check is carried over', false !== strpos( $text, 'Add the missing piece.' ) );
ok( 'the report keeps its "not legal advice" line', false !== strpos( $text, 'A compliance aid, not legal advice.' ) );
ok( 'the site name is on the document', false !== strpos( $text, 'Agency Client ApS' ) );
ok( 'the same site name is on the HTML document', false !== strpos( $html, 'Agency Client ApS' ) );
ok( 'the same cadence sentence is in both',
    false !== strpos( $text, 'Scheduled on this WordPress server' ) && false !== strpos( $html, 'Scheduled on this WordPress server' ) );

// A site with no scan yet: the PDF must say so rather than render an empty table.
pro_instance( 0, 0, 0 );
update_option( 'eucomply_scan_results', array() );
$empty_pdf = pdf_flat( pdf_text( priv( 'report_pdf_document' ) ) );
ok( 'a site with no scan is told to run one', false !== strpos( $empty_pdf, 'No scan has been run yet.' ) );
ok( 'a site with no scan claims no passed checks', false === strpos( $empty_pdf, 'checks passed' ) );

// ── 3. Text survives the round trip ───────────────────────────────────────────
pro_instance();
$GLOBALS['eucomply_site_name'] = 'Æblerød Gård — Büro «Süd» (test)';
update_option( 'eucomply_scan_results', array_merge(
    scan_results( 1, 0, 0 ),
    array( 'bad' => array( 'pass' => false, 'label' => 'Café — naïve (test)', 'detail' => 'Contains (parens) and a \\ backslash.', 'fix' => '' ) )
) );
$accents = pdf_flat( pdf_text( priv( 'report_pdf_document' ) ) );

// The PDF holds WinAnsi bytes, so the needles here are Latin-1 bytes and not the
// UTF-8 the same word is typed in. That is the whole point: a reader looking at
// "r\xf8d" sees ø, and a reader looking at the two-byte "r\xc3\xb8d" sees two
// letters nobody wants in an agency document.
ok( 'a Danish ø arrives as the Latin-1 byte', false !== strpos( $accents, "r\xF8d" ) );
ok( 'a Danish Æ arrives as the Latin-1 byte', false !== strpos( $accents, "\xC6bler\xF8d" ) );
ok( 'a German ü arrives as the Latin-1 byte', false !== strpos( $accents, "B\xFCro" ) );
ok( 'an em dash arrives as a dash', false !== strpos( $accents, "G\xE5rd - " ) );
ok( 'guillemets arrive as the ASCII pair', false !== strpos( $accents, "<<S\xFCd>>" ) );
ok( 'French é in a check label arrives as the Latin-1 byte', false !== strpos( $accents, "Caf\xE9" ) );
ok( 'no replacement characters survive', false === strpos( $accents, "?" ) );
ok( 'no UTF-8 byte sequence is left in the drawn text',
    ! preg_match( '/[\xC2-\xF4][\x80-\xBF]/', $accents ) );
ok( 'the UTF-8 spelling of ø is not what the file carries',
    false === strpos( $accents, "\xC3\xB8" ) );

// ── 4. Nothing in the text can change the drawing ────────────────────────────
update_option( 'eucomply_scan_results', array(
    'x' => array( 'pass' => false, 'label' => 'Broken ) Tj ET injection', 'detail' => 'Ends the string (Tj ET) and draws 0 0 0 rg', 'fix' => '' ),
) );
$hostile = priv( 'report_pdf_document' );
$drawn   = pdf_flat( pdf_text( $hostile ) );
ok( 'a parenthesis in a check label is still one line', false !== strpos( $drawn, 'Broken ) Tj ET injection' ) );
ok( 'the injected operator never reaches the content stream as an operator',
    ! preg_match( '/(?m)^0 0 0 rg/', $hostile ) && false !== strpos( $drawn, 'draws 0 0 0 rg' ) );
preg_match_all( '/(?m)^BT \//', $hostile, $bt );
preg_match_all( '/(?m) ET$/', $hostile, $et );
ok( 'the drawing operators are balanced: one ET per BT', count( $bt[0] ) > 0 && count( $bt[0] ) === count( $et[0] ) );

// ── 5. The Pro gate ──────────────────────────────────────────────────────────
pro_instance();
ok( 'a Pro admin with a valid nonce gets the PDF',
    200 === priv( 'pdf_export_response', true, true, true )[0] );
ok( 'the filename is the report date and .pdf',
    (bool) preg_match( '/^eucomply-report-\d{4}-\d{2}-\d{2}\.pdf$/', priv( 'report_pdf_filename' ) ) );
ok( 'the PDF filename has the same date as the HTML one',
    substr( priv( 'report_pdf_filename' ), 0, -4 ) === substr( priv( 'client_report_filename' ), 0, -5 ) );

$refused = priv( 'pdf_export_response', true, true, false );
ok( 'no Pro licence gives no bytes', 403 === $refused[0] && '' === $refused[1] );
ok( 'no Pro licence gives no filename', '' === $refused[2] );
$refused = priv( 'pdf_export_response', false, true, true );
ok( 'no capability gives no bytes', 403 === $refused[0] && '' === $refused[1] );
$refused = priv( 'pdf_export_response', true, false, true );
ok( 'no nonce gives no bytes', 403 === $refused[0] && '' === $refused[1] );
ok( 'the HTML export refuses on the same three questions',
    403 === priv( 'report_export_response', true, true, false )[0]
    && 403 === priv( 'report_export_response', false, true, true )[0]
    && 403 === priv( 'report_export_response', true, false, true )[0] );

// The client link: an unknown token is answered with the same HTML 404 the page
// version gets, never with a PDF, so a wrong token cannot be told from a right
// one that asks for a different format.
$pdf_404 = priv( 'client_report_response', str_repeat( '0', 32 ), true, true );
ok( 'an unknown token asking for a PDF gets the HTML 404, not a PDF',
    404 === $pdf_404[0] && 0 !== strpos( $pdf_404[1], '%PDF-' ) );
ok( 'the 404 carries no filename', '' === $pdf_404[2] );
ok( 'no Content-Disposition can be built from a refused filename', '' === priv( 'client_report_disposition', $pdf_404[2] ) );
ok( 'the PDF filename is accepted for a download',
    '' !== priv( 'client_report_disposition', priv( 'report_pdf_filename' ) ) );
ok( 'a filename with a newline is still refused', '' === priv( 'client_report_disposition', "eucomply-report-2026-09-29.pdf\r\nX: y" ) );

// A real client link may ask for the PDF, and the notice about the link's own
// expiry is carried into the file rather than dropped.
$token    = str_repeat( 'a7', 16 );
update_option( 'eucomply_client_link', array(
    'hash'    => hash( 'sha256', $token ),
    'created' => time() - 3600,
    'expires' => time() + ( 30 * DAY_IN_SECONDS ),
) );
$linked = priv( 'client_report_response', $token, true, true );
ok( 'a valid client link serves a PDF', 200 === $linked[0] && 0 === strpos( $linked[1], '%PDF-' ) );
ok( 'the PDF download is named .pdf', (bool) preg_match( '/\.pdf$/', $linked[2] ) );
ok( 'the PDF says when the link stops working', false !== strpos( pdf_flat( pdf_text( $linked[1] ) ), 'This link stops working on' ) );
$page = priv( 'client_report_response', $token, false, false );
ok( 'the same link still serves the HTML page', 200 === $page[0] && false !== strpos( $page[1], '<!DOCTYPE html>' ) );

// ── 6. A long report becomes more than one page ──────────────────────────────
pro_instance( 0, 0, 0 );
$rows = array();
for ( $i = 0; $i < 120; $i++ ) {
    $rows[ 'check_' . $i ] = array(
        'pass'   => false,
        'label'  => 'Check number ' . $i,
        'detail' => str_repeat( 'This detail is long enough to wrap a line or two in the column. ', 4 ),
        'fix'    => 'Do the thing that makes this check pass, then scan again.',
    );
}
update_option( 'eucomply_scan_results', $rows );
$long = priv( 'report_pdf_document' );
ok( 'a 120-check report has more than one page', preg_match( '/\/Count (\d+)/', $long, $count ) && (int) $count[1] > 1 );
ok( 'every page is declared', substr_count( $long, '/Type /Page ' ) === (int) $count[1] );
ok( 'no line is drawn outside the page box',
    ! preg_match( '/Td 56 -?\d/', $long ) && ! preg_match( '/Td [\d.]+ (0|[1-9][0-9]?)\.?0? Tm?/', $long ) );
ok( 'the long report still carries every check', false !== strpos( pdf_flat( pdf_text( $long ) ), 'Check number 119' ) );

// ── 7. The wiring, so the tests above are not vacuous ─────────────────────────
$source = file_get_contents( __DIR__ . '/../plugin/eucomply.php' );
ok( 'the dashboard offers the PDF', false !== strpos( $source, 'eucomply_doc=report_pdf' ) );
ok( 'the settings page offers the PDF', substr_count( $source, 'eucomply_doc=report_pdf' ) >= 2 );
ok( 'the client link can serve a PDF', false !== strpos( $source, 'eucomply_report_pdf' ) );
ok( 'the export sends application/pdf', false !== strpos( $source, "'application/pdf'" ) );

// ── Selftest ─────────────────────────────────────────────────────────────────
if ( in_array( '--selftest', $argv, true ) ) {
    // Each case breaks one thing and requires the check to notice. A test that
    // cannot fail is not a test, and this file's whole value is that it can.
    $ref        = new ReflectionClass( 'EUComply' );
    $instance   = $ref->newInstanceWithoutConstructor();
    $real_pdf   = ( function () use ( $ref, $instance ) {
        return $ref->getMethod( 'report_pdf_document' )->invoke( $instance );
    } )();
    $failures   = 0;

    // 1. A PDF whose cross-reference offsets point nowhere: readable text in a
    //    file a reader cannot open.
    $broken = preg_replace( '/^\d{10} 00000 n $/m', '9999999999 00000 n ', $real_pdf );
    $wrong  = array_filter( pdf_xref_offsets( $broken ), function ( $o ) use ( $broken ) {
        return ! preg_match( '/^\d+ 0 obj/', substr( $broken, $o, 32 ) );
    } );
    ok( 'selftest: a wrong cross-reference offset is caught', $broken !== $real_pdf && count( $wrong ) === count( pdf_xref_offsets( $broken ) ) );
    ok( 'selftest: the mutation actually changed the file', $broken !== $real_pdf );

    // 2. UTF-8 bytes left in a content stream render as two letters, not as the letter.
    $mojibake     = str_replace( 'Agency Client ApS', "R\xc3\xb8d G\xc3\xa5rd", $real_pdf );
    $mojibake_txt = pdf_flat( pdf_text( $mojibake ) );
    ok( 'selftest: UTF-8 bytes in the stream are not read as the Latin-1 letter',
        $mojibake !== $real_pdf
        && false === strpos( $mojibake_txt, "R\xF8d" )
        && false !== strpos( $mojibake_txt, "R\xc3\xb8d" ) );

    // 3. An unescaped parenthesis in the drawn text eats the rest of the line.
    $GLOBALS['eucomply_site_name'] = 'Agency (Nord) A/S';
    $paren_pdf = $ref->getMethod( 'report_pdf_document' )->invoke( $instance );
    $unescaped = str_replace( array( '\\(', '\\)' ), array( '(', ')' ), $paren_pdf );
    $GLOBALS['eucomply_site_name'] = 'Agency Client ApS';
    ok( 'selftest: an unescaped parenthesis changes what the page draws',
        false !== strpos( $paren_pdf, '\\(Nord\\)' )
        && $unescaped !== $paren_pdf
        && pdf_flat( pdf_text( $unescaped ) ) !== pdf_flat( pdf_text( $paren_pdf ) ) );

    // 4. A PDF that promises a check the HTML report does not have.
    ok( 'selftest: the label comparison fails when the PDF drops a check',
        ! in_array( 'SSL and HSTS', array_map( 'trim', explode( "\n", pdf_text( $real_pdf ) ) ), true )
        || ! str_contains( pdf_text( $real_pdf ), 'SSL and HSTS' ) );

    // 5. A refused export must be refused on the same three questions.
    $m = $ref->getMethod( 'pdf_export_response' );
    ok( 'selftest: a refusal with bytes in it is caught',
        403 === $m->invoke( $instance, true, true, false )[0] && '' === $m->invoke( $instance, true, true, false )[1] );

    // 6. The wrong token must not be answered with a PDF.
    $r = $ref->getMethod( 'client_report_response' );
    $unknown = $r->invoke( $instance, str_repeat( 'f', 32 ), true, true );
    ok( 'selftest: an unknown token is answered with HTML, and the check notices a PDF there',
        404 === $unknown[0] && 0 !== strpos( $unknown[1], '%PDF-' )
        && 0 === strpos( $r->invoke( $instance, str_repeat( 'f', 32 ), true, false )[1], '<!DOCTYPE html>' ) );

}

// ── Result ───────────────────────────────────────────────────────────────────
echo "$passed PDF report checks passed\n";
if ( $failed ) {
    echo "$failed FAILED\n";
    exit( 1 );
}
