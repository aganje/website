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
		$path = WPMU_PLUGIN_DIR . '/aletheon/aletheon.css';

		if ( ! file_exists( $path ) ) {
			return;
		}

		$css = file_get_contents( $path ); // phpcs:ignore WordPress.WP.AlternativeFunctions

		if ( false === $css ) {
			return;
		}

		/*
		 * Printed inline rather than linked as a separate file.
		 *
		 * A linked stylesheet is cached independently of the HTML, so a visitor can end up
		 * holding new markup with a stale stylesheet (or the reverse) and see the previous
		 * design. Inlining makes that skew impossible — the styles always travel with the
		 * page that needs them. ~16KB uncompressed, a few KB gzipped, and it removes a
		 * render-blocking request.
		 */
		wp_register_style( 'aletheon-design', false, array(), null );
		wp_enqueue_style( 'aletheon-design' );
		wp_add_inline_style( 'aletheon-design', $css );
	},
	// Late priority so this wins over the theme's own stylesheets.
	99
);

/**
 * [ale_copyright] — footer copyright line.
 *
 * Rendered rather than hardcoded so the year cannot go stale the way the
 * previous footer did (it was still showing 2025 in August 2026).
 */
add_shortcode(
	'ale_copyright',
	function () {
		return sprintf(
			'<p class="ale-muted">&copy; %s Aletheon Labs &middot; San Diego, CA</p>',
			esc_html( wp_date( 'Y' ) )
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
 * Legacy URL redirects.
 *
 * /experience/ was the old slug for what is now the Aletheon Intelligence platform page.
 * Kept as a 301 so existing links and any indexed results do not 404.
 */
add_action(
	'template_redirect',
	function () {
		if ( is_admin() ) {
			return;
		}

		$map = array(
			'experience' => 'aletheon-intelligence',
			'services'   => 'solutions',
		);

		$path = trim( (string) wp_parse_url( add_query_arg( array() ), PHP_URL_PATH ), '/' );

		if ( isset( $map[ $path ] ) ) {
			wp_safe_redirect( home_url( '/' . $map[ $path ] . '/' ), 301 );
			exit;
		}
	}
);
