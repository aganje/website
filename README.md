# aletheonlabs.com

Source of truth for the [aletheonlabs.com](https://aletheonlabs.com/) website — a WordPress
site on Bluehost running the `bluehost-blueprint` block theme.

## What the site sells

Two things, and only these two:

- **Aletheon Forge** — the governed AI software development and engineering platform.
- **Software development** — AI applications, agent systems, integrations, and data platforms
  built for enterprises on the same governed foundation.

Both rest on the **governed AI layer**, which is the architecture the site explains.

> **Aletheon Intelligence was sold in 2026 and is not part of the company any more.** It must
> not appear anywhere on the site — not as a platform, not in navigation, not as "business
> intelligence" positioning. `build/generate.py` fails the build if that copy reappears; see
> "Conventions" below.

## Layout

```text
build/
  generate.py          page copy + block-markup generator — edit here, not the markup
  pages/*.html         generated WordPress block markup (regenerate, don't hand-edit)
  parts/               header, footer, navigation template parts
  assets/
    aletheon.css       the design system (dark, purple/black/white)
    aletheon-design.php  mu-plugin: enqueues CSS, [ale_copyright], legacy redirects
  global-styles.json   WordPress global styles (palette + element colors)
live/                  snapshot pulled from production before the 2026-08 rebuild, for reference
DEPLOY.md              deployment runbook, including the steps this change set needs
REDESIGN-PLAN.md       what was built, why, and how to roll it back
WebsiteImprovements    the positioning brief the copy is drawn from
```

Pages, and the WordPress post IDs they deploy to:

| Page | Slug | WP ID |
|---|---|---|
| Home | `/` | 18 |
| Aletheon Forge | `/aletheon-forge/` | 77 |
| Governed AI | `/governed-ai/` | 78 |
| Software Development | `/software-development/` | 10 |
| Research | `/research/` | 79 |
| About | `/about/` | 11 |
| Contact | `/contact/` | 12 |
| Privacy Policy | `/privacy-policy/` | 3 |

## Making changes

Copy and page structure live in `build/generate.py`. Edit it, then:

```bash
cd build && python generate.py     # regenerates build/pages/*.html
```

The generator is also the test suite. It exits non-zero and writes `BUILD FAILED` if any page
has unbalanced block markup, if forbidden copy reappears, or if the governed-layer diagram's
labels no longer fit their band. It warns about orphaned files in `pages/` left behind when a
page is removed from `PAGES` — delete those by hand.

Deploy is over SSH/WP-CLI (`wp post update <id> <file>`), with CSS and the mu-plugin `scp`'d to
`wp-content/mu-plugins/`. Connection details are in `sshbluehost`, which is **gitignored** — as
are the SSH keys and the WordPress application password. Nothing in this repo contains
credentials. See [DEPLOY.md](DEPLOY.md).

## Conventions

- **Brand is purple, black, and white.** Values in `build/assets/aletheon.css` `:root`. No cyan,
  no amber, no third accent hue.
- **Forge and software development only.** Aletheon Intelligence was sold. The `FORBIDDEN` tuple
  in `generate.py` holds the strings that must never ship again — `Aletheon Intelligence`,
  `aletheon-intelligence`, `business intelligence`, and the old consulting disclaimers — and the
  build fails rather than publishing any of them.
- **Say what the company is, never what it is not.** Avoid "not a…", "unlike…", "rather than…"
  when describing Aletheon itself.
- **No invented social proof.** No testimonials, logos, ratings, or customer names unless they
  are real and attributable. The Services page previously shipped fabricated testimonials and a
  fake review count; that is what this rule exists to prevent.
- **The copyright year is set deliberately, not derived from the clock.** It is the
  `ALE_COPYRIGHT_YEAR` constant in `build/assets/aletheon-design.php`, rendered through the
  `[ale_copyright]` shortcode so the footer markup never has to change. Currently `2025`.
- Custom CSS classes are namespaced `ale-` to avoid colliding with the theme's `nfd-` system.
- Generated markup is stored with LF endings (`.gitattributes`), because it is deployed to the
  server verbatim.

## Note on the snapshot

`live/` is a snapshot of production as it stood *before* the August 2026 rebuild. It is kept for
reference and diffing, not as a description of the current site.

The cPanel username appearing in a Bluehost installer tracking URL inside the privacy-policy
snapshot has been replaced with `REDACTED-CPANEL-USER`, since this repository is public.
