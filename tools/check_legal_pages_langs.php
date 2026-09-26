<?php
/**
 * Kan den betalte `legal` finde sider på dansk, svensk og nederlandsk?
 *
 *   php tools/check_legal_pages_langs.php [--selftest]
 *
 * Hvorfor denne port findes. `check_legal_pages()` slår WordPress-sider op
 * efter sti og titel. Inden opgave 53 var listen `imprint`, `impressum`,
 * `accessibility-statement`, `accessibility` og to LIKE-opslag på `%Imprint%`
 * og `%Impressum%` — altså **kun engelsk og tysk**. Målt, ikke antaget: en dansk
 * butik med siderne *Om os*, *Handelsbetingelser* og *Privatlivspolitik* fik
 * `3 of 3 legal pages missing` i den rapport et bureau betaler $79 om året for.
 * Det er samme fejlklasse som opgave 50 (betalt `forms` svagere end den gratis
 * scanner) og opgave 52 (`legal` som score afhængig af sprog), en niveau længere
 * nede: her fejler det, fordi siden er skrevet på dansk.
 *
 * Fire regler, fordi fire forskellige fejl skal kunne fanges:
 *
 *   R1  En dansk, svensk og nederlandsk butik med de tre dokumenter skal
 *       **ikke** blive fortalt at de mangler. Det er hele fundet.
 *   R2  De samme tre dokumenter skal give **samme dom på fire sprog**. En port
 *       der kun testede dansk, ville være grøn for en motor der læser dansk og
 *       engelsk og intet andet.
 *   R3  Opslaget skal finde siden uanset hvilken af de to veje den ligger på —
 *       WordPress-sti (`/om-os/`) eller sidetitel ("Om os"). En butik har begge
 *       dele, og pluginen prøver stien først; en mutation der fjerner kun
 *       stierne må derfor være fanget, og det kræver en fixture der *kun* har
 *       stier.
 *   R4  En butik uden nogen af dem skal stadig få beskedet. R1 alene ville være
 *       opfyldt af et `legal` der siger "bestået" altid.
 *   R5  En press-side med titlen *Om os i pressen* må **ikke** tælles som
 *       imprint. Det er den fejltagelse lighedstegnet `=` i stedet for `%…%`
 *       forhindrer, og derfor skal den kunne slås *til* i selftesten.
 *
 * Selftesten muterer **repoets egen fil** — en kopi af `plugin/eucomply.php` i et
 * temp-mappe, kørt gennem den samme probe med `EUCOMPLY_PLUGIN_FILE` — fordi en
 * mutation der *påstander* at være fanget ikke er en mutation. Uden den kunne
 * porten være grøn, fordi den ikke kan fejle.
 *
 * @package EUComply
 */

ini_set( 'display_errors', 'stderr' );

$PROBE = __DIR__ . '/plugin_probe.php';
$PLUGIN = __DIR__ . '/../plugin/eucomply.php';

$passed = 0;
$failed = 0;
function ok( $label, $condition ) {
    global $passed, $failed;
    if ( $condition ) {
        $passed++;
        return true;
    }
    $failed++;
    echo "FAIL: $label\n";
    return false;
}

// ── Kør proben på én fixture ──────────────────────────────────────────────────

function probe( array $fixture, $only = 'legal', $plugin_file = null ) {
    global $PROBE;
    $file = tempnam( sys_get_temp_dir(), 'eucomply-legal-' ) . '.json';
    file_put_contents( $file, json_encode( $fixture, JSON_UNESCAPED_UNICODE ) );
    $out  = array();
    $code = 0;
    $cmd  = 'php ' . escapeshellarg( $PROBE ) . ' ' . escapeshellarg( $file );
    if ( '' !== $only ) {
        $cmd .= ' ' . escapeshellarg( $only );
    }
    if ( $plugin_file ) {
        $cmd = 'EUCOMPLY_PLUGIN_FILE=' . escapeshellarg( $plugin_file ) . ' ' . $cmd;
    }
    exec( $cmd . ' 2>&1', $out, $code );
    $json = is_array( $out ) ? implode( "\n", $out ) : '';
    unlink( $file );
    if ( 0 !== $code ) {
        return array( '_error' => trim( $json ) );
    }
    $decoded = json_decode( trim( $json ), true );
    if ( ! is_array( $decoded ) ) {
        return array( '_error' => 'probe output is not JSON: ' . substr( trim( $json ), 0, 200 ) );
    }
    return isset( $decoded[ $only ] ) && is_array( $decoded[ $only ] ) ? $decoded[ $only ] : $decoded;
}

// ── Fixtures: den samme butik, skrevet på fire sprog ───────────────────────────

/** Sideformerne hver markedes butikker bruger. Målt i `docs/eucomply-privatlivsprog.md`. */
function legal_page_names( $lang ) {
    $names = array(
        'en' => array(
            'imprint' => array( 'imprint', 'Imprint' ),
            'eaa'     => array( 'accessibility-statement', 'Accessibility Statement' ),
            'privacy' => array( 'privacy-policy', 'Privacy Policy' ),
        ),
        'da' => array(
            'imprint' => array( 'om-os', 'Om os' ),
            'eaa'     => array( 'tilgaengelighedserklaering', 'Tilgængelighedserklæring' ),
            'privacy' => array( 'privatlivspolitik', 'Privatlivspolitik' ),
        ),
        'sv' => array(
            'imprint' => array( 'om-oss', 'Om oss' ),
            'eaa'     => array( 'tillganglighetsredogorelse', 'Tillgänglighetsredogörelse' ),
            'privacy' => array( 'integritetspolicy', 'Integritetspolicy' ),
        ),
        'nl' => array(
            'imprint' => array( 'over-ons', 'Over ons' ),
            'eaa'     => array( 'toegankelijkheidsverklaring', 'Toegankelijkheidsverklaring' ),
            'privacy' => array( 'privacybeleid', 'Privacybeleid' ),
        ),
    );
    return isset( $names[ $lang ] ) ? $names[ $lang ] : array();
}

/**
 * One shop, three legal documents, one language. Only the page names differ.
 *
 * `via` says which of the plugin's two lookups the fixture can answer, and that
 * is the point: `paths` is a shop whose pages are reachable by URL slug, `titles`
 * a shop whose pages are only findable by name, `both` an ordinary WordPress
 * site, which has both. Without that split a mutation that removes one lookup
 * from the plugin is invisible, because the other one still finds the page.
 *
 * @param string $lang da|sv|nl|en.
 * @param string $via  paths|titles|both|none.
 * @param array  $extra_pages Extra pages, slug => title, for the false-positive case.
 * @param array  $omit Document keys the shop does not have at all: imprint, eaa, privacy.
 * @return array
 */
function shop( $lang, $via = 'both', $extra_pages = array(), $omit = array() ) {
    $pages  = array();
    $titles = array();
    $options = array();
    $id     = 10;
    foreach ( legal_page_names( $lang ) as $key => $entry ) {
        if ( in_array( $key, $omit, true ) ) {
            continue;
        }
        list( $slug, $title ) = $entry;
        $post = array(
            'ID'          => $id,
            'post_title'  => $title,
            'post_status' => 'publish',
        );
        // Both keys, because a real WordPress site answers two different
        // questions: `get_page_by_path('om-os')` and `get_post(10)`. The probe's
        // page map is one flat array, so a fixture that only had the slug would
        // make a correctly found page look unfound the moment the title lookup
        // returned an id — which is exactly the kind of false green a fixture
        // that was written to fit the code produces.
        if ( 'paths' === $via || 'both' === $via || 'privacy' === $key ) {
            $pages[ $slug ] = $post;
        }
        $pages[ $id ] = $post;
        if ( 'titles' === $via || 'both' === $via ) {
            $titles[] = array( 'id' => $id, 'title' => $title, 'status' => 'publish' );
        }
        if ( 'privacy' === $key ) {
            // The privacy page is read through the WordPress option, not through
            // a lookup, so it is assigned either way.
            $options['wp_page_for_privacy_policy'] = $slug;
        }
        $id += 10;
    }
    foreach ( $extra_pages as $slug => $title ) {
        $post            = array( 'ID' => $id, 'post_title' => $title, 'post_status' => 'publish' );
        $pages[ $slug ]  = $post;
        $pages[ $id ]    = $post;
        $titles[]        = array( 'id' => $id, 'title' => $title, 'status' => 'publish' );
        $id++;
    }
    if ( 'none' === $via ) {
        $pages   = array();
        $titles  = array();
        $options = array();
    }

    return array(
        'html'    => '<html><head><title>Butik</title></head><body><p>Hej</p></body></html>',
        'headers' => array( 'strict-transport-security' => 'max-age=31536000' ),
        'home'    => 'https://agency-client.example',
        'pages'   => $pages,
        'titles'  => $titles,
        'options' => $options,
    );
}

/** The two documents the report names, out of the verdict the customer reads. */
function found_documents( array $verdict ) {
    $found = array();
    if ( isset( $verdict['pages'] ) && is_array( $verdict['pages'] ) ) {
        foreach ( $verdict['pages'] as $key => $value ) {
            $found[ $key ] = (string) $value;
        }
    }
    return $found;
}

$langs = array( 'da', 'sv', 'nl', 'en' );

// R1 — en dansk, svensk og nederlandsk butik med alle tre dokumenter.
$dom = array();
foreach ( $langs as $lang ) {
    $v = probe( shop( $lang ) );
    if ( ! empty( $v['_error'] ) ) {
        ok( "R1 $lang: proben svarede uden fejl", false );
        fwrite( STDERR, "probe: {$v['_error']}\n" );
        exit( 1 );
    }
    $dom[ $lang ]      = ! empty( $v['pass'] );
    $docs              = found_documents( $v );
    ok( "R1 $lang: butikken med de tre dokumenter består legal", ! empty( $v['pass'] ) );
    ok( "R1 $lang: dommen nævner ikke 'legal pages missing'", false === strpos( (string) $v['label'], 'missing' ) );
    ok( "R1 $lang: imprint er fundet (ikke kun privatliv)", isset( $docs['imprint'] ) );
    ok( "R1 $lang: tilgængelighedserklæringen er fundet", isset( $docs['eaa'] ) );
}

// R2 — samme dom på fire sprog.
$flipped = array();
foreach ( $dom as $lang => $pass ) {
    if ( ! $pass ) {
        $flipped[] = $lang;
    }
}
ok( 'R2: de fire sprog giver samme dom' . ( $flipped ? ' (fejler: ' . implode( ', ', $flipped ) . ')' : '' ), ! $flipped );

// R3 — begge opslagsveje, hver for sig.
foreach ( $langs as $lang ) {
    foreach ( array( 'paths', 'titles' ) as $via ) {
        $v    = probe( shop( $lang, $via ) );
        $docs = found_documents( $v );
        ok( "R3 $lang/$via: butikken består på denne vej alene", ! empty( $v['pass'] ) );
        ok( "R3 $lang/$via: imprint er fundet", isset( $docs['imprint'] ) );
        ok( "R3 $lang/$via: tilgængelighedserklæringen er fundet", isset( $docs['eaa'] ) );
    }
}

// R4 — en butik uden nogen af dem skal stadig høre det.
$v = probe( shop( 'da', 'none' ) );
ok( 'R4: en butik uden juridiske sider fejler', empty( $v['pass'] ) );
ok( 'R4: etiketten tæller de manglende sider', (bool) preg_match( '/\b3 of 3 legal pages missing\b/', (string) $v['label'] ) );
ok( 'R4: detaljen siger hvad der ikke blev fundet', false !== stripos( strtolower( (string) $v['detail'] ), 'not found' ) );

// R5 — en press-side med "Om os i pressen" er ikke en imprint.
$press_page = array( 'om-os-i-pressen' => 'Om os i pressen' );
$v          = probe( shop( 'da', 'titles', $press_page, array( 'imprint' ) ) );
$docs = found_documents( $v );
ok( 'R5: "Om os i pressen" tælles ikke som imprint', ! isset( $docs['imprint'] ) );
ok( 'R5: butikken uden rigtig imprint fejler stadig', empty( $v['pass'] ) );

printf( "%d juridiske-sidetest bestået — 4 sprog, 2 opslagsveje, 1 tom butik, 1 press-side\n", $passed );

if ( ! empty( $argv ) && in_array( '--selftest', $argv, true ) ) {
    // ── Selftest: mutationer mod repoets egen fil ─────────────────────────────
    //
    // Fire mutationer, én pr. fejltagelse porten skal kunne se. Hver mutation er
    // en kopi af `plugin/eucomply.php` i et temp-mappe, så pluginen i repoet
    // aldrig røres, og proben køres med EUCOMPLY_PLUGIN_FILE peget på kopien.
    // Efter mutationerne efterprøves det med `cmp`, at pluginen er uændret.

    $source = file_get_contents( $PLUGIN );
    $dir    = sys_get_temp_dir() . '/eucomply-legal-mutant-' . getmypid();
    @mkdir( $dir, 0777, true );

    $mutations = array(
        // M1: de danske, svenske og nederlandske stier forsvinder.
        'M1 de nye sidespor forsvinder' => array(
            'probe'  => 'paths',
            'edits'  => array(
                array( "'om-os',", '' ),
                array( "'om-oss',", '' ),
                array( "'over-ons',", '' ),
                array( "'tilgaengelighedserklaering',", '' ),
            ),
        ),
        // M2: titel-opslaget bliver et LIKE med jokertegn — R5's fejltagelse.
        // Begge dele hører sammen: et LIKE uden `%` er i SQL stadig et eksakt
        // match, så en mutation der kun bytter operatoren ville være grøn af
        // design. Det er den redaktionelle slaphed — LIKE plus `%Om os%` — der
        // gør "Om os i pressen" til en imprint.
        'M2 titel-opslaget bliver et vildt LIKE' => array(
            'probe'  => 'none',
            'press'  => true,
            'edits'  => array(
                array( 'WHERE post_title = %s AND', 'WHERE post_title LIKE %s AND' ),
                array( "'Om os',", "'%Om os%'," ),
            ),
        ),
        // M3: hjælpefunktionen holder op med at slå titler op.
        'M3 titel-opslaget slås ikke op' => array(
            'probe'  => 'titles',
            'edits'  => array(
                array( 'foreach ( $titles as $title ) {', 'foreach ( array() as $title ) {' ),
            ),
        ),
        // M4: de nye sprognavn forsvinder fra titel-listen.
        'M4 de nye sprognavn forsvinder' => array(
            'probe'  => 'titles',
            'edits'  => array(
                array( "'Om os',", '' ),
                array( "'Om oss',", '' ),
                array( "'Over ons',", '' ),
                array( "'Tilgængelighedserklæring',", '' ),
            ),
        ),
    );

    $applied = 0;
    foreach ( $mutations as $label => $spec ) {
        $mutant = $source;
        $hit    = true;
        foreach ( $spec['edits'] as $edit ) {
            if ( false === strpos( $mutant, $edit[0] ) ) {
                $hit = false;
                break;
            }
            $mutant = str_replace( $edit[0], $edit[1], $mutant );
        }
        if ( ! ok( "selftest: mutationen '$label' fandt sin egen tekst i pluginen", $hit ) ) {
            continue;
        }
        $file = $dir . '/mutant-' . $applied . '.php';
        file_put_contents( $file, $mutant );
        $applied++;

        if ( ! empty( $spec['press'] ) ) {
            // M2 skal gøre R5 grøn: med et LIKE tæller "Om os i pressen" som
            // imprint. Er den stadig rød, så R5 læser pluginens kode.
            $press = probe( shop( 'da', 'titles', array( 'om-os-i-pressen' => 'Om os i pressen' ), array( 'imprint' ) ), 'legal', $file );
            ok(
                "selftest: '$label' tæller nu press-siden som imprint",
                ! empty( found_documents( $press )['imprint'] )
            );
        } else {
            // Alle andre mutationer skal gøre den angivne opslagsvej rød for den
            // danske butik.
            $da = probe( shop( 'da', $spec['probe'] ), 'legal', $file );
            ok(
                "selftest: '$label' gør den danske butik rød ({$spec['probe']})",
                empty( $da['_error'] ) && empty( $da['pass'] )
            );
        }

        @unlink( $file );
    }
    @rmdir( $dir );

    // Revert efterprøvet: mutationerne rørte kun kopier, så pluginen i repoet
    // skal være byte-identisk med det vi læste ind.
    ok( 'selftest: pluginen i repoet er uændret efter mutationerne', file_get_contents( $PLUGIN ) === $source );
    ok( "selftest: $applied mutationer blev kørt", $applied >= 4 );
}

if ( $failed ) {
    printf( "%d FAILED, %d bestået\n", $failed, $passed );
    exit( 1 );
}
printf( "%d bestået\n", $passed );
exit( 0 );
