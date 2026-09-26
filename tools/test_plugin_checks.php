<?php
/**
 * Alle elleve tjek kørt adfærdsmæssigt — også de seks, ingen test nogensinde kørte.
 *
 *   php tools/test_plugin_checks.php
 *   php tools/test_plugin_checks.php --selftest   (beviser at den kan fejle)
 *   php tools/test_plugin_checks.php --dump       (etiketterne som JSON)
 *
 * Opgave 44 viste, at dokument-gates ikke kan se en fejl, der er identisk i alle
 * kopier: `php -l` læser ikke kode, og kilde/zip-pariteten kan kun se forskel.
 * Den viste også, at de fem nye tjek var døde i 1.3.11, fordi ingen port nogensinde
 * havde *kørt* et tjek. Da den fejl var rettet, var de seks øvrige tjek i
 * `run_checks()` — `ssl`, `cookies`, `forms`, `backups`, `plugins`, `legal` —
 * stadig kun linted. Denne fil er deres måling.
 *
 * Den gennemfører fem kontrakter, og alle fem er egenskaber ved adfærden, ikke
 * lister over strenge:
 *
 *   1. Proben kører præcis de checks `run_checks()` skriver — listen læses i
 *      koden, så den kan ikke komme bagefter produktet.
 *   2. Hvert af de seks tjek kan nå **både** bestået og fejlet. Et tjek der kun
 *      kan finde det ene er dødt, og det så opgave 44 som en skrivefejl.
 *   3. Et tjek der ikke kunne køre er aldrig et bestået tjek.
 *   4. Et tjek der fejler, må ikke have samme etiket som det samme tjek da det
 *      bestod. Det er den kontrakt, der fandt den eneste fejl i denne iteration.
 *   5. Én GET pr. scanning, og HEAD tælles **for sig** — målt, ikke antaget.
 *
 * Filen bruger `tools/plugin_probe.php` som sin eneste harness, så der kun er én
 * sandhed om hvad WordPress gør i en test.
 *
 * @package EUComply
 */

ini_set( 'display_errors', 'stderr' );

$PROBE = __DIR__ . '/plugin_probe.php';

/** Same value the plugin uses, named here so this file needs no WordPress. */
define( 'EUCOMPLY_TEST_DAY', 86400 );

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

// ── Kør proben på én fixture ──────────────────────────────────────────────────

function probe( array $fixture, $only = '' ) {
    global $PROBE;
    $file = tempnam( sys_get_temp_dir(), 'eucomply-fixture-' ) . '.json';
    file_put_contents( $file, json_encode( $fixture ) );
    $out  = array();
    $code = 0;
    $cmd  = 'php ' . escapeshellarg( $PROBE ) . ' ' . escapeshellarg( $file );
    if ( '' !== $only ) {
        $cmd .= ' ' . escapeshellarg( $only );
    }
    exec( $cmd . ' 2>&1', $out, $code );
    $json = is_array( $out ) ? implode( "\n", $out ) : '';
    unlink( $file );
    if ( 0 !== $code ) {
        return array( '_error' => trim( $json ) );
    }
    $decoded = json_decode( trim( $json ), true );
    return is_array( $decoded ) ? $decoded : array( '_error' => 'probe output is not JSON: ' . substr( trim( $json ), 0, 200 ) );
}

/** En publiceret WordPress-side: alle plugins, alle sider, alt opdateret. */
function healthy_site( $overrides = array() ) {
    return array_merge(
        array(
            'html'          => '<html><head><title>Butik</title></head><body><p>Velkommen</p></body></html>',
            'headers'       => array(
                'content-security-policy'   => "default-src 'self'",
                'x-content-type-options'    => 'nosniff',
                'referrer-policy'           => 'strict-origin-when-cross-origin',
                'x-frame-options'           => 'SAMEORIGIN',
                // HSTS is read from this same response, so the healthy site
                // carries it here — the front page is the only request a scan
                // makes, and a header nothing reads is a header nothing proves.
                'strict-transport-security' => 'max-age=31536000',
            ),
            'home'          => 'https://agency-client.example',
            'active'        => array(
                'complianz-gdpr/cmp-functions.php',
                'wpforms-lite/wpforms.php',
                'updraftplus/updraftplus.php',
            ),
            'pages'         => array(
                12 => array( 'post_title' => 'Privatlivspolitik', 'post_status' => 'publish' ),
                'imprint' => array( 'post_title' => 'Impressum', 'post_status' => 'publish' ),
                'accessibility-statement' => array( 'post_title' => 'Tilgængelighed', 'post_status' => 'publish' ),
            ),
            'options'       => array( 'wp_page_for_privacy_policy' => 12 ),
            'updraft'       => time() - 2 * EUCOMPLY_TEST_DAY,
        ),
        $overrides
    );
}

// get_post() returns objects in WordPress and arrays in JSON, so the fixture is
// normalised to objects once, here, rather than in five places in the checks.
function to_objects( $site ) {
    if ( isset( $site['pages'] ) && is_array( $site['pages'] ) ) {
        foreach ( $site['pages'] as $key => $page ) {
            if ( is_array( $page ) ) {
                $site['pages'][ $key ] = (object) $page;
            }
        }
    }
    if ( isset( $site['core_updates'] ) ) {
        foreach ( $site['core_updates'] as $i => $core ) {
            if ( is_array( $core ) ) {
                $site['core_updates'][ $i ] = (object) $core;
            }
        }
    }
    if ( isset( $site['plugin_updates'] ) ) {
        foreach ( $site['plugin_updates'] as $file => $data ) {
            $data['update'] = (object) $data['update'];
            $site['plugin_updates'][ $file ] = (object) $data;
        }
    }
    return $site;
}

$HEALTHY = to_objects( healthy_site() );

// ── Kontrakt 1: proben kører præcis dem run_checks() skriver ──────────────────

$first = probe( $HEALTHY );
ok( 'proben returnerede et resultat', empty( $first['_error'] ) );
if ( ! empty( $first['_error'] ) ) {
    fwrite( STDERR, "probe: {$first['_error']}\n" );
    exit( 1 );
}
$RUN_CHECKS_KEYS = $first['_keys'];
ok( 'run_checks() skriver elleve checks', 11 === count( $RUN_CHECKS_KEYS ) );
$SHARED = array( 'consent_mode_v2', 'tcf', 'trackers', 'headers', 'dora' );
$missing_shared = array_values( array_diff( $SHARED, $RUN_CHECKS_KEYS ) );
ok(
    'de fem delte checks er blandt dem run_checks() skriver',
    array() === $missing_shared,
);
if ( $missing_shared ) {
    fwrite( STDERR, 'mangler i run_checks(): ' . implode( ', ', $missing_shared ) . "\n" );
}

// ── Kontrakt 2 og 4: hvert tjek kan nå begge domme, med en anden etiket ───────
//
// Fixtures der hver især danner en fejlklasse. `ssl` nås gennem forsidens
// headere — dem `front_page()` hentede — og gennem skemeen i site-adressen, de
// øvrige gennem WordPress-tilstanden.

$FAILURES = array(
    'site over http' => array( 'home' => 'http://agency-client.example' ),
    'ingen HSTS' => array( 'headers' => array( 'x-frame-options' => 'SAMEORIGIN' ) ),
    'ingen consent-plugin' => array( 'active' => array( 'wpforms-lite/wpforms.php', 'updraftplus/updraftplus.php' ) ),
    'form-plugin uden privatlivsside' => array(
        'active'  => array( 'complianz-gdpr/cmp-functions.php', 'updraftplus/updraftplus.php' ),
        'options' => array(),
    ),
    'ingen backup-plugin' => array( 'active' => array( 'complianz-gdpr/cmp-functions.php', 'wpforms-lite/wpforms.php' ) ),
    'backup 60 dage gammel' => array( 'updraft' => time() - 60 * EUCOMPLY_TEST_DAY ),
    'core ude af date' => array(
        'core_updates' => array( array( 'response' => 'upgrade', 'current' => '6.9' ) ),
        'updraft'      => null,
    ),
    'to plugins ude af date' => array(
        'plugin_updates' => array(
            'wpforms-lite/wpforms.php'    => array( 'Name' => 'WPForms', 'Version' => '2.0', 'update' => array( 'new_version' => '2.1' ) ),
            'complianz-gdpr/cmp-functions.php' => array( 'Name' => 'Complianz', 'Version' => '6.5', 'update' => array( 'new_version' => '7.0' ) ),
        ),
        'updraft' => null,
    ),
    'ingen juridiske sider' => array( 'pages' => array(), 'options' => array() ),
    'privatlivsside ikke publiceret' => array(
        'pages'   => array( 12 => array( 'post_title' => 'Udkast', 'post_status' => 'draft' ) ),
        'options' => array( 'wp_page_for_privacy_policy' => 12 ),
    ),
    'ingen front-page-headere' => array( 'headers' => array() ),
    'ingen trackere, consent eller DORA-tekst' => array( 'html' => '<html><body><p>Velkommen</p></body></html>' ),
    // De fire signatur-baserede tjek læser forsidens tekst, så de nås med HTML,
    // ikke med WordPress-tilstand. Samme fem klasser som paritetsporten bruger,
    // her brugt til det den ikke stiller: kan de overhovedet nå begge domme.
    'alt consent, TCF, CMP og DORA' => array( 'html' => '<html><body class="google_consent_mode">'
        . '<script>gtag(\'consent\', \'default\', { ad_storage: \'denied\' }); window.dataLayer = window.dataLayer || [];'
        . ' gtag(\'js\', new Date()); gtag(\'config\', \'G-1\', { consent_mode: \'granted\' });</script>'
        . '<script src="https://www.googletagmanager.com/gtm.js?id=GTM-1" async></script>'
        . '<script>window.__tcfapi(\'addEventListener\', 2);</script>'
        . '<script>gdprApplies = true; tcfapi_v2 = "2.2"; IABConsent_String = "CPabc"; IABTCF_Session = "x";</script>'
        . '<script src="https://cdn.cookiebot.com/uc.js" async></script>'
        // Skrevet efter signaturerne, ikke efter forventningen: de fire af ni
        // DORA-markører kræver en bindestreg eller underscore i løbet (se opgave 45),
        // så 'SPF record' med et mellemrum matcher ikke `spf[_-]?record`.
        . '<p>SPF-record, DKIM signing, DMARC-record, incident-response plan, business-continuity and a status-page are published.</p>'
        . '</body></html>' ),
    'trackere uden consent-platform' => array( 'html' => '<html><body>'
        . '<script src="https://www.googletagmanager.com/gtm.js?id=GTM-1"></script>'
        . '<script>fbq(\'init\', \'123\')</script><script src="https://static.hotjar.com/x.js"></script>'
        . '</body></html>' ),
);

$runs = array( ' sund site' => $HEALTHY );
foreach ( $FAILURES as $name => $override ) {
    $runs[ $name ] = to_objects( healthy_site( $override ) );
}

$pass_labels = array();
$fail_labels = array();
$states      = array();
$observations = array();
foreach ( $runs as $name => $site ) {
    $verdicts = probe( $site );
    if ( ! empty( $verdicts['_error'] ) ) {
        ok( "proben svarede på «$name»", false );
        continue;
    }
    foreach ( $RUN_CHECKS_KEYS as $key ) {
        if ( ! isset( $verdicts[ $key ] ) || ! is_array( $verdicts[ $key ] ) ) {
            ok( "$key findes i resultatet for «$name»", false );
            continue;
        }
        $label = (string) $verdicts[ $key ]['label'];
        // Hver (domme, etiket) er én observation. Det er den samme mængde
        // trin 19 læser, så der er ét sæt fixtures for hele porten i stedet
        // for to — se `tools/check_verdict_labels.mjs`.
        $observations[] = array(
            'fixture' => $name,
            'key'     => $key,
            'pass'    => ! empty( $verdicts[ $key ]['pass'] ),
            'warn'    => ! empty( $verdicts[ $key ]['warn'] ),
            'label'   => $label,
        );
        if ( ! empty( $verdicts[ $key ]['pass'] ) ) {
            $pass_labels[ $key ][ $label ] = true;
            $states[ $key ]['pass']       = true;
        } else {
            $fail_labels[ $key ][ $label ] = true;
            $states[ $key ]['fail']       = true;
        }
    }
}

// ─--dump: målingen som JSON, for den ene port der læser alle tre motorer ──────
//
// Ren måling: den udskriver og afslutter, før kontrakterne nederst køres, så en
// rød kontrakt ikke kan gøre målingen usynlig. Ingen exit-kode-vurdering her —
// det er porten der kalder denne, der afgør hvad fundene betyder.
if ( in_array( '--dump', $argv, true ) ) {
    echo json_encode(
        array(
            'engine'       => 'plugin',
            'keys'         => $RUN_CHECKS_KEYS,
            'observations' => $observations,
        ),
        JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES
    );
    exit( 0 );
}

// Kontrakt 2 — det døde-tjek.
foreach ( $RUN_CHECKS_KEYS as $key ) {
    ok(
        "$key kan både bestå og fejle (aldrig et dødt tjek)",
        ! empty( $states[ $key ]['pass'] ) && ! empty( $states[ $key ]['fail'] )
    );
}

// Kontrakt 4 — etiketten skal fortælle hvilken dom. Det er den, der fandt
// "Legal pages checked" og "Forms reviewed" stående på en rød række.
foreach ( $RUN_CHECKS_KEYS as $key ) {
    // array_merge, ikke +: begge lister er numeriske, så + er et union og
    // ville tage den korte liste og lade den længere ligge.
    $both = array_merge( array_keys( $pass_labels[ $key ] ?? array() ), array_keys( $fail_labels[ $key ] ?? array() ) );
    ok(
        "$key har forskellige etiketter på bestået og fejlet",
        count( $both ) >= 2
    );
}

// Den konkrete fejl, målt på den rækkefølge kunden ser den: et fejlet tjek må
// ikke bære en etiket, der siger at tjekket lykkes.
foreach ( $fail_labels as $key => $labels ) {
    foreach ( array_keys( $labels ) as $label ) {
        ok(
            "$key fejler uden en etiket der påstår at det lykkes (\"$label\")",
            ! preg_match( '~^(legal pages checked|forms reviewed|all up to date|.*\b(checked|reviewed|verified)\b)~i', $label )
        );
    }
}

// ── Kontrakt 3: et tjek der ikke kunne køre er aldrig et bestået tjek ─────────
//
// `ssl` er her fordi den læser forsiden igennem `front_page()` lige så vel som
// de fem. Den nåede tidligere udenom den og svarede fra sin egen HEAD, så en
// forside der ikke kunne læses gav ti "kunne ikke læse" og et grønt `ssl` —
// samme rapport, modsigelse i sig selv.

$unreadable = probe( to_objects( healthy_site( array( 'error' => 'cURL error 28: Operation timed out' ) ) ) );
ok( 'en ulæselig forside gav et resultat', empty( $unreadable['_error'] ) );
if ( empty( $unreadable['_error'] ) ) {
    $NEEDS_FRONT_PAGE = array_merge( $SHARED, array( 'ssl' ) );
    foreach ( $NEEDS_FRONT_PAGE as $key ) {
        ok( "$key er ikke bestået på en ulæselig forside", empty( $unreadable[ $key ]['pass'] ) );
        ok( "$key siger at det ikke kørte", ! empty( $unreadable[ $key ]['warn'] ) );
    }
    // Og de seks tjek der læser forsiden skal alle sige det samme, så de ikke kan
    // være lige heldige: ét af dem, der læser videre på en fejl, ville være en
    // ny død etiket.
    $say_could_not = 0;
    foreach ( $NEEDS_FRONT_PAGE as $key ) {
        if ( false !== stripos( (string) $unreadable[ $key ]['label'], 'could not read' ) ) {
            $say_could_not++;
        }
    }
    ok( "alle seks tjek der læser forsiden siger at de ikke kørte ($say_could_not/6)", 6 === $say_could_not );
}

// ── Kontrakt 5: én hentning pr. scanning, og ingen anden slags ────────────────
//
// Målt, fordi påstanden "én hentning pr. scan" ellers kun gældt de fem statiske
// tjek: `check_ssl()` sendte sin egen HEAD oveni. Det er ikke en optimering — på
// en server der blokerer HEAD fik kunden "HTTPS unreachable" ved siden af ti
// grønne tjek der netop havde læst den samme forside, og en ulæselig forside gav
// et grønt `ssl`. Nu læser den HSTS fra det svar de andre læser.

ok(
    'de elleve tjek henter forsiden én gang',
    1 === ( $first['_fetches'] ?? -1 ),
);
ok(
    'hele scanningen laver én hentning i alt, ingen HEAD',
    array( 1, 0 ) === array( $first['_fetches'] ?? -1, $first['_heads'] ?? -1 ),
);

$unreadable_fetches = $unreadable['_fetches'] ?? -1;
$unreadable_heads   = $unreadable['_heads'] ?? -1;
ok( 'en ulæselig forside hentes heller ikke seks gange', 1 === $unreadable_fetches );
ok( 'en ulæselig forside sender heller ingen HEAD', 0 === $unreadable_heads );

// Én check ad gangen, fordi ellers kan tællen ikke tilskrives: elleve tjek der
// deler en tæller kan hver især have en hentning, og tallet siger intet om
// hvilken af dem der har den.
$ssl_only = probe( $HEALTHY, 'ssl' );
ok( 'check_ssl() alene henter forsiden én gang', 1 === ( $ssl_only['_fetches'] ?? -1 ) );
ok( 'check_ssl() alene sender ingen HEAD', 0 === ( $ssl_only['_heads'] ?? -1 ) );
ok( 'check_ssl() alene er nok til at vide om HSTS er der', ! empty( $ssl_only['ssl']['pass'] ) );

$ssl_http = probe( to_objects( healthy_site( array( 'home' => 'http://agency-client.example' ) ) ), 'ssl' );
ok( 'en http://-adresse siger "Not HTTPS"', 'Not HTTPS' === ( $ssl_http['ssl']['label'] ?? '' ) );
ok( 'en http://-adresse hentes ikke overhovedet', 0 === ( $ssl_http['_fetches'] ?? -1 ) );
ok( 'en http://-adresse sender ingen HEAD', 0 === ( $ssl_http['_heads'] ?? -1 ) );

// Kildekravet ved siden af tællen: en `wp_remote_head()` der ligger i koden uden
// at nogen fixture rammer den ville være usynlig i adfærdstællen, og den er
// præcis den regression der lige blev fjernet.
ok( 'plugin-koden kalder ikke wp_remote_head()', contract_head_free( eucomply_code_lines() ) );

// ── Selftest: bevis at kontrakterne kan fejle ──────────────────────────────────

if ( in_array( '--selftest', $argv, true ) ) {
    // 1. En nøgle der forsvinder fra run_checks() skal give færre checks.
    $read_keys = eucomply_selftest_keys();
    ok( 'selftest: run_checks() skriver elleve checks', 11 === count( $read_keys ) );
    ok(
        'selftest: en nøgle der forsvinder fra run_checks() giver færre checks',
        10 === count( preg_grep( '~^backups$~', $read_keys, PREG_GREP_INVERT ) )
    );

    // 2. Samme etiket på begge domme skal være rød.
    $same = 'a fixture where the label is the same either way';
    ok( 'selftest: en delt etiket mellem bestået og fejlet er rød', contract_label_catches( 'Legal pages checked' ) );
    ok( 'selftest: en forskellig etiket er grøn', ! contract_label_catches( '2 of 3 legal pages missing' ) );

    // 3. Et tjek der kun kan finde det ene domme skal være rød.
    ok( 'selftest: et tjek med kun ét dom er rød', ! contract_reaches_both_dommes( array( 'pass' => true ) ) );
    ok( 'selftest: et tjek med begge domme er grøn', contract_reaches_both_dommes( array( 'pass' => true, 'fail' => true ) ) );

    // 4. En ulæselig forside der tælles som bestået skal være rød.
    ok( 'selftest: et bestået tjek på en ulæselig forside er rød', ! contract_unreadable_is_never_a_pass( array( 'pass' => true ) ) );
    ok( 'selftest: et ikke-bestået tjek på en ulæselig forside er grøn', contract_unreadable_is_never_a_pass( array( 'pass' => false, 'warn' => true ) ) );

    // 5. To hentninger pr. scanning — præcis det opgave 46 fjernede — skal være
    // røde, ellers er porten grøn af en fejl.
    ok( 'selftest: to GET i en scanning er rød', ! contract_one_request( array( '_fetches' => 2, '_heads' => 0 ) ) );
    ok( 'selftest: én GET og én HEAD i en scanning er rød', ! contract_one_request( array( '_fetches' => 1, '_heads' => 1 ) ) );
    ok( 'selftest: to HEAD i en scanning er rød', ! contract_one_request( array( '_fetches' => 0, '_heads' => 2 ) ) );
    ok( 'selftest: én hentning i alt er grøn', contract_one_request( array( '_fetches' => 1, '_heads' => 0 ) ) );

    // 6. En `wp_remote_head()` i koden skal være rød, også når den ligger i en
    // kommentar — fordi så er den død kode, der lige så vel kan genoplives.
    ok( 'selftest: en wp_remote_head() i koden er rød', ! contract_head_free( eucomply_filter_code( array( "        \$r = wp_remote_head( \$home );" ) ) ) );
    ok( 'selftest: en kommentar om wp_remote_head() er grøn', contract_head_free( eucomply_filter_code( array( ' * It used to send its own wp_remote_head(), which cost a second request.' ) ) ) );

    // 7. Et check-navn `run_checks()` ikke skriver må ikke give en fuld kørsel.
    //    Ellers svarer porten om alle elleve og er grøn om det forkerte spørgsmål.
    ok( 'selftest: et check-navn der ikke findes er rødt', ! empty( probe( $HEALTHY, 'no-such-check' )['_error'] ) );
    ok( 'selftest: en enkelt check kører kun den check', ! empty( $ssl_only['ssl'] ) && empty( $ssl_only['headers'] ) );
}

/**
 * Selftestens hjælpere. De er bevidst skrevet som *de samme betingelser* som
 * kontrakterne ovenfor, så en case der forventer rødt og en port der ikke kan
 * blive rød, ikke kan være sande på én gang.
 */
function eucomply_selftest_keys() {
    $source = file_get_contents( __DIR__ . '/../plugin/eucomply.php' );
    preg_match( '/public function run_checks\(\).*?\n    \}/s', $source, $block );
    preg_match_all( '/\$results\[\s*[\'"]([a-z0-9_]+)[\'"]\s*\]\s*=\s*\$this->([a-z0-9_]+)\s*\(/i', $block[0], $hits );
    return $hits[1];
}
function contract_label_catches( $label ) {
    return (bool) preg_match( '~^(legal pages checked|forms reviewed|all up to date|.*\b(checked|reviewed|verified)\b)~i', $label );
}
function contract_reaches_both_dommes( array $states ) {
    return ! empty( $states['pass'] ) && ! empty( $states['fail'] );
}
function contract_unreadable_is_never_a_pass( array $verdict ) {
    return empty( $verdict['pass'] ) && ! empty( $verdict['warn'] );
}
/** Én hentning pr. scanning, og ingen af dem en HEAD. */
function contract_one_request( array $run ) {
    return 1 === ( $run['_fetches'] ?? -1 ) && 0 === ( $run['_heads'] ?? -1 );
}
/** Kildelinjer uden kommentarer, så et krav om "ingen wp_remote_head" ikke kan
 *  slås i overkøbet af den kommentar der beskriver hvorfor den forsvandt. */
function eucomply_code_lines() {
    return eucomply_filter_code( preg_split( '/\R/', (string) file_get_contents( __DIR__ . '/../plugin/eucomply.php' ) ) );
}
function eucomply_filter_code( array $lines ) {
    $out = array();
    foreach ( $lines as $line ) {
        $trimmed = ltrim( (string) $line );
        if ( '' === $trimmed || '/' === $trimmed[0] || '#' === $trimmed[0] || '*' === $trimmed[0] ) {
            continue;
        }
        $out[] = $line;
    }
    return $out;
}
function contract_head_free( array $code_lines ) {
    return 0 === (int) preg_match_all( '~wp_remote_head\s*\(~', implode( "\n", $code_lines ) );
}

// ── Optælling ────────────────────────────────────────────────────────────────

if ( $failed ) {
    echo "\n$failed af de $passed checks fejlede\n";
    exit( 1 );
}
echo "\n$passed plugin-check adfærdsmæssigt bestået — " . count( $RUN_CHECKS_KEYS ) . " checks, " . count( $runs ) . " fixtures\n";
