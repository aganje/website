<?php
/**
 * Plugin Name: Aletheon Design Layer
 * Description: Front-end design system for aletheonlabs.com, plus legacy URL redirects.
 *              Lives in mu-plugins so it is independent of the active theme and survives theme updates.
 * Version:     1.0.0
 * Author:      Aletheon Labs
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Enqueue the design layer on the front end only.
 * Version is derived from the file mtime so edits bust caches without manual bumping.
 */
add_action(
	'wp_enqueue_scripts',
	function () {
		$rel  = '/aletheon/aletheon.css';
		$path = WPMU_PLUGIN_DIR . $rel;

		if ( ! file_exists( $path ) ) {
			return;
		}

		wp_enqueue_style(
			'aletheon-design',
			WPMU_PLUGIN_URL . $rel,
			array(),
			(string) filemtime( $path )
		);
	},
	// Late priority so this wins over the theme's own stylesheets.
	99
);

/**
 * The copyright year shown in the footer.
 *
 * Set explicitly at the owner's direction rather than derived from the current
 * date, so it does not move on its own. Bump this one constant to change it.
 */
if ( ! defined( 'ALE_COPYRIGHT_YEAR' ) ) {
	define( 'ALE_COPYRIGHT_YEAR', '2025' );
}

/**
 * [ale_copyright] — footer copyright line.
 *
 * Still a shortcode rather than literal text in the footer template part, so the
 * line lives in exactly one place and the footer markup never has to be edited
 * to change it.
 */
add_shortcode(
	'ale_copyright',
	function () {
		return sprintf(
			'<p class="ale-muted">Copyright %s. All rights reserved.</p>',
			esc_html( ALE_COPYRIGHT_YEAR )
		);
	}
);

/**
 * Process shortcodes inside block template parts.
 *
 * `the_content` does not run for template parts (header/footer), so a shortcode placed
 * there renders literally as "[ale_copyright]". This expands core/shortcode blocks
 * wherever they appear.
 */
add_filter(
	'render_block',
	function ( $content, $block ) {
		if ( isset( $block['blockName'] ) && 'core/shortcode' === $block['blockName'] ) {
			return do_shortcode( $content );
		}
		return $content;
	},
	10,
	2
);

/**
 * Legacy URL redirects, all 301, so existing links and indexed results do not 404.
 *
 * /experience/ and /services/ were consulting-era slugs. /aletheon-intelligence/ was the
 * Intelligence platform page; that platform was sold in 2026, so the page is gone and its
 * traffic now lands on Forge. /solutions/ was replaced by the Software Development page.
 */
add_action(
	'template_redirect',
	function () {
		if ( is_admin() ) {
			return;
		}

		$map = array(
			'experience'             => 'aletheon-forge',
			'aletheon-intelligence'  => 'aletheon-forge',
			'services'               => 'software-development',
			'solutions'              => 'software-development',
		);

		$path = trim( (string) wp_parse_url( add_query_arg( array() ), PHP_URL_PATH ), '/' );

		if ( isset( $map[ $path ] ) ) {
			wp_safe_redirect( home_url( '/' . $map[ $path ] . '/' ), 301 );
			exit;
		}
	}
);
