# aletheonlabs.com

Source for the [aletheonlabs.com](https://aletheonlabs.com/) website — a WordPress site on
Bluehost running the `bluehost-blueprint` block theme.

> **`build/` mirrors production as of 2026-10-04.** It was re-synced from the live server on that
> date after the repo was found to have drifted badly. See "The 2026-10 re-sync" below before
> assuming anything in here is generated.

## Layout

```text
build/
  pages/*.html         the live site's block markup — hand-edit these, they are the source
  parts/               nav, header, footer template parts
  templates/           block template(s)
  assets/
    aletheon.css       the design system (1,721 lines)
    aletheon-design.php  mu-plugin: inlines the CSS, [ale_copyright], legacy redirects
  global-styles.json   WordPress global styles (palette + element colors)
  PAGE-IDS.txt         which file deploys to which WordPress post ID
  generate.py          STALE. The August 2026 copy generator. Guarded — see below.
snapshots/2026-10-04/  verbatim read-only capture of production, for diffing
live/                  older snapshot, pulled before the August 2026 rebuild
DEPLOY.md              deployment runbook
REDESIGN-PLAN.md       the August 2026 rebuild: what shipped, why, how to roll back
WebsiteImprovements    the positioning brief the August copy was drawn from
```

## The 2026-10 re-sync

The repo had fallen behind the live site, badly enough that deploying it would have destroyed
real work. Pulled down and committed on 2026-10-04:

| | Repo held | Live had |
|---|---|---|
| `aletheon.css` | 476 lines | **1,721 lines** — `.ale-founder-dossier`, `.ale-credential-matrix`, `.ale-core-visual`, `.ale-hero-btn` and more existed only on the server |
| `aletheon-design.php` | enqueued the CSS as a linked file | **inlines it** via `wp_add_inline_style`, to stop HTML and CSS caching out of sync |
| Software Development | nothing | a **published page** (WP 97) with real service copy |
| Research | 4.6KB | **10.7KB** — a founder dossier with real credentials |
| Home / About | — | hand-written Software Development sections |
| Navigation | flat menu | an **Offerings** submenu: Intelligence, Forge, Software Development |

Forge, Governed AI, Contact and Solutions were untouched since August and matched exactly.

**Why `generate.py` is stale and guarded.** It reproduces the August site. The pages above were
authored by hand in the WordPress editor, so they cannot be round-tripped back into it. Running
it would silently overwrite the founder dossier, the Software Development page, and the Home and
About additions. It now refuses to run without `--force` and prints what it would destroy. Treat
it as a historical artifact; **`build/pages/*.html` is the source of truth.**

## Making changes

Edit `build/pages/*.html` (or `parts/`, or `assets/`) directly, then deploy per
[DEPLOY.md](DEPLOY.md). `build/PAGE-IDS.txt` maps each file to its WordPress post ID.

Before deploying, diff against the server so you know exactly what you are about to change —
the repo going stale once is the reason this README exists.

## Conventions

- **Brand is purple, black, and white.** Values in `build/assets/aletheon.css` `:root`. No cyan,
  no amber, no third accent hue.
- **Say what the company is, never what it is not.** Avoid "not a…", "unlike…" when describing
  Aletheon itself. The August build shipped "an AI software company, not a general consulting
  firm", which came from an internal note and should never have been public.
- **No invented social proof.** No testimonials, logos, ratings, or customer names unless they
  are real and attributable. The old Services page shipped fabricated testimonials and a fake
  review count; that is why this rule exists.
- **The founder credentials on Research are real and specific.** Microsoft, published author,
  microservice design, $100B-to-mid-cap transformations, doctoral research at Purdue. Do not
  paraphrase them into vaguer language.
- Custom CSS classes are namespaced `ale-` to avoid colliding with the theme's `nfd-` system.
- Block markup is stored LF (`.gitattributes`) because it is deployed verbatim.

## Credentials

Nothing in this repo contains credentials. `sshbluehost`, the SSH keys, and the WordPress
application password are all gitignored. Connection details are in `build/PAGE-IDS.txt` (host and
username only — no secrets).

## Note on the snapshots

`snapshots/2026-10-04/` is a verbatim capture of production, named by WordPress post ID, kept for
diffing. `live/` is an older capture from before the August 2026 rebuild. Neither is edited.

The cPanel username in a Bluehost installer tracking URL inside the privacy-policy snapshot was
replaced with `REDACTED-CPANEL-USER`, since this repository is public.
