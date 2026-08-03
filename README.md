# aletheonlabs.com

Source of truth for the [aletheonlabs.com](https://aletheonlabs.com/) website — a WordPress
site on Bluehost running the `bluehost-blueprint` block theme.

## Layout

```
build/
  generate.py          page copy + block-markup generator — edit here, not the markup
  pages/*.html         generated WordPress block markup (regenerate, don't hand-edit)
  parts/               header, footer, navigation template parts
  assets/
    aletheon.css       the design system (dark, purple/black/white)
    aletheon-design.php  mu-plugin: enqueues CSS, [ale_copyright], legacy redirects
  global-styles.json   WordPress global styles (palette + element colors)
live/                  snapshot pulled from production, for reference and diffing
REDESIGN-PLAN.md       what was built, why, and how to roll it back
WebsiteImprovements    the positioning brief the copy is drawn from
```

## Making changes

Copy and page structure live in `build/generate.py`. Edit it, then:

```bash
cd build && python generate.py     # regenerates build/pages/*.html
```

Deploy is over SSH/WP-CLI (`wp post update <id> <file>`), with CSS and the mu-plugin `scp`'d to
`wp-content/mu-plugins/`. Connection details are in `sshbluehost`, which is **gitignored** — as
are the SSH keys and the WordPress application password. Nothing in this repo contains
credentials.

## Conventions

- **Brand is purple, black, and white.** Values in `build/assets/aletheon.css` `:root`. No cyan,
  no amber, no third accent hue.
- **Say what the company is, never what it is not.** Avoid "not a…", "unlike…", "rather than…"
  when describing Aletheon itself.
- **No invented social proof.** No testimonials, logos, ratings, or customer names unless they
  are real and attributable. The Services page previously shipped fabricated testimonials and a
  fake review count; that is what this rule exists to prevent.
- Custom CSS classes are namespaced `ale-` to avoid colliding with the theme's `nfd-` system.

## Note on the snapshot

The cPanel username appearing in a Bluehost installer tracking URL inside the privacy-policy
snapshot has been replaced with `REDACTED-CPANEL-USER`, since this repository is public.
