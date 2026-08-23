<?php
/**
 * Plugin Name: EUComply — EU Compliance Scanner
 * Description: Scans your WordPress site for EU compliance gaps (GDPR, NIS2, EAA/DORA basics): SSL, cookie banner, privacy policy page, WP updates, user hygiene. Free scan in your admin dashboard. Pro adds auto-generated DPA, NIS2 vendor clauses and EAA statements.
 * Version:     1.0.0
 * Author:      eucomply
 * License:     GPL-2.0-or-later
 * Text Domain: eucomply
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'EUCOMPLY_VERSION', '1.0.0' );

class EUComply_Scanner {

	public static function init() {
		add_action( 'admin_menu', array( __CLASS__, 'register_menu' ) );
		add_action( 'admin_post_eucomply_run_scan', array( __CLASS__, 'handle_scan' ) );
	}

	public static function register_menu() {
		add_menu_page(
			'EUComply',
			'EUComply',
			'manage_options',
			'eucomply',
			array( __CLASS__, 'render_dashboard' ),
			'dashicons-shield',
			59
		);
	}

	/**
	 * Run the free scan. Returns an array of checks.
	 */
	public static function run_scan() {
		global $wp_version;

		$checks = array();

		// 1. SSL / HTTPS
		$is_ssl    = is_ssl();
		$site_url  = home_url();
		$https_url = set_url_scheme( $site_url, 'https' );
		$ssl_ok    = false;
		if ( 'https' === wp_parse_url( $https_url, PHP_URL_SCHEME ) ) {
			$res = wp_remote_get( $https_url, array( 'timeout' => 10 ) );
			$ssl_ok = ! is_wp_error( $res ) && 200 <= intval( wp_remote_retrieve_response_code( $res ) ) && 500 > intval( wp_remote_retrieve_response_code( $res ) );
		}
		$checks[] = array(
			'id'       => 'ssl',
			'label'    => __( 'HTTPS / valid SSL certificate', 'eucomply' ),
			'reg'      => 'GDPR Art. 32 — security of processing',
			'status'   => $is_ssl && $ssl_ok ? 'pass' : 'fail',
			'fix'      => __( 'Install an SSL certificate and force HTTPS (Settings > General > WordPress and Site Address must start with https://).', 'eucomply' ),
		);

		// 2. Cookie/consent banner heuristic: look for known consent plugins or output.
		$consent = class_exists( 'Cookie_Notice' )
			|| defined( 'CMP_COOKIE_NAME' )
			|| class_exists( 'CookieYes\CTY' )
			|| has_action( 'wp_head', 'wp_consent_api_register_consent_api' )
			|| function_exists( 'cmplz_has_consent' );
		$checks[] = array(
			'id'       => 'cookies',
			'label'    => __( 'Cookie consent banner present', 'eucomply' ),
			'reg'      => 'GDPR / ePrivacy Directive',
			'status'   => $consent ? 'pass' : 'warn',
			'fix'      => __( 'No recognized consent plugin detected. Install a consent management plugin (e.g. any GDPR cookie-banner plugin) before collecting non-essential cookies.', 'eucomply' ),
		);

		// 3. Privacy policy page configured.
		$pp_id = (int) get_option( 'wp_page_for_privacy_policy' );
		$pp_ok = $pp_id > 0 && get_post_status( $pp_id ) === 'publish';
		$checks[] = array(
			'id'       => 'privacy_policy',
			'label'    => __( 'Privacy policy page published & selected', 'eucomply' ),
			'reg'      => 'GDPR Art. 13 — transparency',
			'status'   => $pp_ok ? 'pass' : 'fail',
			'fix'      => __( 'Create a privacy policy, then select it under Settings > Privacy.', 'eucomply' ),
		);

		// 4. WordPress core up to date.
		$core_updates = get_site_transient( 'update_core' );
		$core_current = empty( $core_updates->updates ) || ! in_array( 'upgrade', wp_list_pluck( (array) $core_updates->updates, 'action' ), true );
		$checks[] = array(
			'id'       => 'core_updates',
			'label'    => __( 'WordPress core is up to date', 'eucomply' ),
			'reg'      => 'GDPR Art. 32 / NIS2 basic hygiene',
			'status'   => $core_current ? 'pass' : 'fail',
			'fix'      => sprintf( __( 'Your site reports version %s with pending core updates. Update now from Dashboard > Updates.', 'eucomply' ), (string) $wp_version ),
		);

		// 5. No administrators with weak/exposed state: count admins + check for inactive admins >90 days.
		$admins = get_users( array( 'role' => 'administrator' ) );
		$stale  = 0;
		$now    = time();
		foreach ( $admins as $a ) {
			$last = get_user_meta( $a->ID, 'session_tokens', true );
			if ( is_array( $last ) && ! empty( $last ) ) {
				$newest = 0;
				foreach ( $last as $t ) {
					$newest = max( $newest, isset( $t['login'] ) ? (int) $t['login'] : 0 );
				}
				if ( $newest > 0 && ( $now - $newest ) > 90 * DAY_IN_SECONDS ) {
					$stale++;
				}
			}
		}
		$checks[] = array(
			'id'       => 'admin_hygiene',
			'label'    => __( 'No dormant administrator accounts (>90 days inactive)', 'eucomply' ),
			'reg'      => 'NIS2 Art. 21 — access control',
			'status'   => 0 === $stale ? 'pass' : 'warn',
			'fix'      => sprintf( _n( '%d administrator account has not logged in for over 90 days. Remove or downgrade it under Users.', '%d administrator accounts have not logged in for over 90 days. Remove or downgrade them under Users.', $stale, 'eucomply' ), $stale ),
		);

		return apply_filters( 'eucomply_checks', $checks );
	}

	public static function handle_scan() {
		if ( ! current_user_can( 'manage_options' ) ) {
			wp_die( esc_html__( 'Not allowed.', 'eucomply' ) );
		}
		check_admin_referer( 'eucomply_run_scan' );

		$checks = self::run_scan();

		update_option(
			'eucomply_last_scan',
			array(
				'time'   => time(),
				'checks' => $checks,
			),
			false
		);

		wp_safe_redirect( add_query_arg( array( 'page' => 'eucomply', 'scanned' => 1 ), admin_url( 'admin.php' ) ) );
		exit;
	}

	private static function score( $checks ) {
		$total = count( $checks );
		$pass  = 0;
		$warn  = 0;
		foreach ( $checks as $c ) {
			if ( 'pass' === $c['status'] ) {
				$pass++;
			} elseif ( 'warn' === $c['status'] ) {
				$warn++;
			}
		}
		return array( 'pass' => $pass, 'warn' => $warn, 'fail' => max( 0, $total - $pass - $warn ), 'total' => $total );
	}

	public static function render_dashboard() {
		if ( ! current_user_can( 'manage_options' ) ) {
			return;
		}
		$last = get_option( 'eucomply_last_scan' );
		?>
		<div class="wrap">
			<h1>EUComply — EU Compliance Scan</h1>
			<p>
				<a class="button button-primary button-hero"
					href="<?php echo esc_url( wp_nonce_url( admin_url( 'admin-post.php?action=eucomply_run_scan' ), 'eucomply_run_scan' ) ); ?>">
					Run scan now
				</a>
			</p>

			<?php if ( is_array( $last ) && isset( $last['time'] ) ) : ?>
				<?php $s = self::score( $last['checks'] ); ?>
				<h2>Last scan: <?php echo esc_html( date_i18n( get_option( 'date_format' ) . ' ' . get_option( 'time_format' ), $last['time'] ) ); ?></h2>
				<p style="font-size:15px">
					<strong style="color:#1a7a44"><?php echo (int) $s['pass']; ?> passed</strong> ·
					<span style="color:#b85a0a"><?php echo (int) $s['warn']; ?> warnings</span> ·
					<span style="color:#c03030"><?php echo (int) $s['fail']; ?> failed</span>
					of <?php echo (int) $s['total']; ?> checks
				</p>
				<table class="widefat striped" style="max-width:900px">
					<thead><tr><th width="26%">Check</th><th width="20%">Regulation</th><th width="10%">Status</th><th>Action</th></tr></thead>
					<tbody>
					<?php foreach ( $last['checks'] as $c ) : ?>
						<tr>
							<td><?php echo esc_html( $c['label'] ); ?></td>
							<td><?php echo esc_html( $c['reg'] ); ?></td>
							<td>
								<?php if ( 'pass' === $c['status'] ) : ?>
									<span style="color:#1a7a44">✔ Pass</span>
								<?php elseif ( 'warn' === $c['status'] ) : ?>
									<span style="color:#b85a0a">▲ Warning</span>
								<?php else : ?>
									<span style="color:#c03030">✖ Fail</span>
								<?php endif; ?>
							</td>
							<td><?php echo 'pass' === $c['status'] ? '—' : esc_html( $c['fix'] ); ?></td>
						</tr>
					<?php endforeach; ?>
					</tbody>
				</table>

				<hr />
				<h2>Go further</h2>
				<p>The free scan shows where you stand. <strong>EUComply Pro</strong> ($79/year) fixes the paperwork automatically:</p>
				<ul style="list-style:disc;padding-left:22px">
					<li>Auto-generated Data Processing Agreement (GDPR)</li>
					<li>NIS2 vendor clause kit</li>
					<li>EAA accessibility statement generator</li>
					<li>Scheduled quarterly scans with email report</li>
				</ul>
				<p><a class="button button-secondary" href="https://eucomply.pages.dev/plugin/" target="_blank" rel="noopener">Get EUComply Pro →</a></p>
			<?php else : ?>
				<p>No scan yet. Click <strong>Run scan now</strong> above.</p>
			<?php endif; ?>
		</div>
		<?php
	}
}

EUComply_Scanner::init();
