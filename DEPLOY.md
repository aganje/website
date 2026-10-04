# Deployment runbook

Written for whoever has the Bluehost SSH credentials — they are gitignored, so this repo can
describe the deployment but cannot perform it.

Connection details live in `sshbluehost` (local only, gitignored). Everything below runs from
`~/public_html` on the server unless stated otherwise.

```bash
ssh -i <private-key> <ssh-user>@<ssh-host>
cd ~/public_html
```

## Always: back up first

```bash
mkdir -p ~/aletheon-backups
wp db export ~/aletheon-backups/db-$(date +%Y%m%d-%H%M%S).sql
```

A database export is the whole rollback. Page content, navigation, template parts, and site
options all live in the database; only the CSS and the mu-plugin are files.

---

## The 2026-10 change set

This release removes the sold Aletheon Intelligence platform, makes Aletheon Forge the single
platform, adds a Software Development page in place of Solutions, and sets the footer copyright
to a fixed year. It touches pages, navigation, the footer, the mu-plugin, and the CSS.

Run the steps in order — step 3 must land before step 5, or `/software-development/` 301s to
itself until the slug changes.

### 1. Build locally and copy up

```bash
cd build && python generate.py        # must print OK for every page, no BUILD FAILED
```

```bash
scp build/assets/aletheon.css        <ssh-user>@<ssh-host>:~/public_html/wp-content/mu-plugins/aletheon/aletheon.css
scp build/assets/aletheon-design.php <ssh-user>@<ssh-host>:~/public_html/wp-content/mu-plugins/aletheon-design.php
```

The mu-plugin is not linted in CI — there is no PHP locally — so lint it on the server before
trusting it:

```bash
php -l wp-content/mu-plugins/aletheon-design.php
```

If that reports anything other than `No syntax errors detected`, restore the previous copy
immediately: a fatal error in an mu-plugin takes the whole site down.

### 2. Retire the Intelligence page

The platform was sold. Trash the page rather than deleting it permanently, so the content is
recoverable if a question comes up during the sale's transition period.

```bash
wp post get 13 --field=post_title      # confirm this is "Aletheon Intelligence" before trashing
wp post delete 13                      # to trash, not permanent
```

### 3. Repoint page 10: Solutions → Software Development

Page 10 is reused rather than replaced, so its history and inbound redirects survive.

```bash
wp post update 10 --post_title="Software Development" --post_name=software-development
```

### 4. Push page content

```bash
wp post update 18 --post_content="$(cat home.html)"
wp post update 77 --post_content="$(cat aletheon-forge.html)"
wp post update 78 --post_content="$(cat governed-ai.html)"
wp post update 10 --post_content="$(cat software-development.html)"
wp post update 79 --post_content="$(cat research.html)"
wp post update 11 --post_content="$(cat about.html)"
wp post update 12 --post_content="$(cat contact.html)"
```

(`wp post update <id> <file>` also works and avoids the shell mangling long content — prefer it
if the files are on the server.)

### 5. Navigation and footer

The navigation menu is post 7; the Platforms dropdown is gone, since there is one platform now.

```bash
wp post update 7 --post_content="$(cat parts/nav.html)"
```

The footer is a `wp_template_part`. Find it and update its content:

```bash
wp post list --post_type=wp_template_part --fields=ID,post_name
wp post update <footer-id> --post_content="$(cat parts/footer.html)"
```

### 6. Site identity

The description becomes the SEO title and social share text, and still carried the
consulting-era Marketing/SCM/ERP framing.

```bash
wp option update blogname "Aletheon Labs"
wp option update blogdescription "Governed AI for software engineering. Aletheon Labs builds Aletheon Forge and custom AI software for enterprise teams."
```

### 7. Flush and verify

```bash
wp rewrite flush
```

Then purge the Cloudflare cache. During the August 2026 deploy, Cloudflare briefly served a
cached self-redirecting 301 on the homepage captured during the permalink flush — origin was
always fine, but the edge needs a purge.

Verify:

```bash
for p in / aletheon-forge governed-ai software-development research about contact privacy-policy; do
  printf '%-24s %s\n' "$p" "$(curl -s -o /dev/null -w '%{http_code}' https://aletheonlabs.com/$p)"
done
```

All should be `200`. Then check the redirects return `301` and land on the right page:

```bash
for p in experience aletheon-intelligence services solutions; do
  printf '%-24s %s -> %s\n' "$p" \
    "$(curl -s -o /dev/null -w '%{http_code}' https://aletheonlabs.com/$p/)" \
    "$(curl -s -o /dev/null -w '%{redirect_url}' https://aletheonlabs.com/$p/)"
done
```

Expected: `experience` and `aletheon-intelligence` → `/aletheon-forge/`; `services` and
`solutions` → `/software-development/`.

Finally, confirm the sold platform is gone from the rendered site:

```bash
for p in / aletheon-forge governed-ai software-development research about contact; do
  curl -s "https://aletheonlabs.com/$p" | grep -ci "aletheon intelligence" | xargs printf "$p: %s hits\n"
done
```

Every line should read `0 hits`.

And confirm the footer renders the copyright rather than the literal shortcode:

```bash
curl -s https://aletheonlabs.com/ | grep -o "Copyright 2025. All rights reserved."
curl -s https://aletheonlabs.com/ | grep -c "\[ale_copyright\]"    # must be 0
```

---

## Rollback

```bash
wp db import ~/aletheon-backups/<the-export-you-took>.sql
```

For the file layer, restore the previous `aletheon.css` and `aletheon-design.php`, or remove the
design layer entirely:

```bash
rm -f wp-content/mu-plugins/aletheon-design.php && rm -rf wp-content/mu-plugins/aletheon
```

That reverts the site to the stock Blueprint theme — unstyled relative to the current design,
but functional.

---

## Not automated

There is no CI and no staging step in this repo. `python generate.py` is the only gate that runs
before deploy, and it checks markup structure and copy, not rendered appearance. Look at the
site on desktop and phone after deploying.
