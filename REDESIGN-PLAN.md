# Aletheon Labs — Website Redesign Plan

> **STATUS: IMPLEMENTED ON PRODUCTION 2026-08-02.** Deployed directly to live at the owner's
> direction (low traffic, staging skipped). See "Deployment record" below for what shipped,
> what was deliberately left out, and how to roll back.

---

## Deployment record

**Rollback — one command restores everything:**

```bash
ssh -i <private-key> <ssh-user>@<ssh-host>   # details in sshbluehost (gitignored, local only)
cd ~/public_html && wp db import ~/aletheon-backups/db-20260802-215847.sql
rm -f wp-content/mu-plugins/aletheon-design.php && rm -rf wp-content/mu-plugins/aletheon
```
Theme archive alongside it at `~/aletheon-backups/themes-20260802-215847.tar.gz`.

**Shipped:**

| Item | Detail |
|---|---|
| Design layer | `wp-content/mu-plugins/aletheon-design.php` + `aletheon/aletheon.css` — theme-independent, survives theme updates |
| Palette | **Brand purple, black, white** (revised 2026-08-02 after the logo was supplied): black `#0A0810`, white `#FFFFFF`, brand purple `#6D28D9`, bright violet `#A855F7`, light violet `#C084FC` (7.2:1 on black), deep indigo `#3B1BC4`. An earlier cyan build was replaced — no cyan or amber remains on any page. |
| Logo & favicon | `site_logo` → attachment 34 (mark only, 316×364, alpha) beside the site title; the full lockup (39) was illegible at header size. `site_icon` → attachment 63 (512×512), so the site now has a favicon for the first time. |
| Voice | Copy states what the company **is**, never what it isn't. "An AI software company, not a consulting firm" → "We build the software layer for enterprise AI"; same fix applied on Forge, Intelligence, About, and the consistency sections. The "not a consulting firm" line came from an internal positioning note in the brief and should never have been public-facing. |
| Signature asset | Animated Governed AI Layer SVG on Home and Governed AI; Identity→Action flow on Home and Intelligence |
| Pages rewritten | Home (18), About (11), Contact (12), Solutions (10), Aletheon Intelligence (13) |
| Pages created | Aletheon Forge (77), Governed AI (78), Research (79) |
| Navigation | Rebuilt with Platforms dropdown + persistent Request a Demo |
| Header/footer | Sticky glass header; footer rebuilt — placeholder `#` social links removed, copyright now rendered dynamically via `[ale_copyright]` so it cannot go stale again |
| Site identity | Title → "Aletheon Labs"; description → the governed-layer one-liner |
| Cleanup | "Hello world!" deleted; privacy policy published |
| Redirects | `/experience/` → `/aletheon-intelligence/`, `/services/` → `/solutions/`, both 301 |

**Verified:** all 9 pages HTTP 200 with the design layer loaded; block markup depth-balanced on
every page; zero occurrences of the old consulting copy, the fabricated testimonials, or
placeholder `href="#"` links.

**Two issues found and fixed during deployment:**
1. `[ale_copyright]` rendered literally — `the_content` does not run for template parts, so
   shortcodes there are never expanded. Fixed with a `render_block` filter on `core/shortcode`.
2. Cloudflare briefly served a cached self-redirecting 301 on the homepage, captured during the
   permalink flush. Origin was always 200. Purged; edge re-fetched clean.

**Deliberately not done — needs real material, not invention:**
- No testimonials, logos, ratings, or customer names anywhere. There are no real ones yet.
- No product screenshots on the platform pages; they are diagrammatic until real UI is supplied.
- Footer social links removed rather than pointed at `#`. Supply real URLs to restore them.
- "Request a Demo" points at `/contact/` (mailto). WPForms is installed but not wired up.
- Research page is narrative; no papers or abstracts are published on it.

**Not verified by me:** the visual result. I have no browser or screenshot tool in this
environment, so the design is confirmed structurally (markup, CSS delivery, contrast computed
during design) but not seen rendered. Worth a look on desktop and phone.

---

Prepared 2026-08-02. Working folder: `F:\AletheonWebsite`.
Live snapshot pulled to `live/` (authoritative — pulled from the server, not from memory).

---

## 0. ✅ RESOLVED 2026-08-02 — fabricated content removed from Services

**Done.** The fabricated sections were stripped from the live `/services/` page and the change
is verified on the rendered site (0 fabricated strings, HTTP 200). Page went 21,492 → 2,538
bytes. The full original is preserved at `live/pages/page-services.html`, and WordPress holds
a revision, so this is reversible.

The page is now **thin — a hero CTA and nothing else.** That is the expected consequence of
removing the fake content without replacing it, and it gets rebuilt as Solutions in Phase 3.

*Original finding, for the record:*

The live `/services/` page was running **unedited theme demo content**:

- Four fake testimonials attributed to invented people — "Emily Davis", "John Doe",
  "Jane Smith", "Michael Johnson".
- A fabricated aggregate rating: **"Average Rating: 4.8 out of 5 based on 150 reviews."**
- Three fake events at fake addresses — "Tech Conference 2024, 123 Innovation Drive,
  Tech City", "AI Summit 2024, 456 AI Avenue, Data Town", "Business Expo 2024" —
  all dated **2024**, roughly two years stale.

This is publicly visible right now. Beyond the credibility problem for a company whose
entire pitch is *trust and explainability*, fabricated testimonials and invented review
counts are squarely within the FTC's rule on fake reviews and testimonials, which carries
civil penalties. This should come down today, independent of the redesign timeline.

**Recommendation:** unpublish `/services/` immediately (one command, reversible), then
rebuild it as the new Solutions page. Do not replace the testimonials with new invented
ones — leave social proof off the site until there are real, attributable customers who
have agreed to be quoted.

---

## 1. The core finding: this is a repositioning, not a redesign

| | Live site says | `WebsiteImprovements` says |
|---|---|---|
| What the company is | Consulting / advisory firm | **AI software product company** |
| Proof | "AI Strategy • Automation • Data Intelligence", Discover → Design → Build → Optimize engagement model | Two platforms: Aletheon Intelligence, Aletheon Forge |
| Core concept | "Turning Complexity into Clarity" | **The Governed AI Layer** |
| Primary CTA | "Start a Conversation" | "Request a Demo" |
| Verbatim | — | *"an AI software company, not a general consulting firm"* |

Verified against the snapshot: the strings **"Aletheon Intelligence", "Aletheon Forge",
"governed", "Purdue", and "Ganje" appear nowhere on the live site.** Not once, on any page,
in any navigation menu.

So the two products the company actually sells are entirely absent from its website, and
the site instead sells a services model the brief explicitly disclaims. Every page needs
new copy. A visual refresh alone would leave the positioning problem fully intact.

---

## 2. ✅ DECIDED 2026-08-02 — canonical mission statement

**This is the mission. It replaces both existing versions everywhere.**

> **Aletheon Labs exists to make enterprise AI trustworthy. We build the governed
> intelligence layer that ensures every AI interaction is secure, explainable, consistent,
> and relevant to the person using it.**

Placement: full statement on About; on Home between §9 (Business Outcomes) and §10 (Research).
The two conflicting statements below must both be removed as part of the Home and About
rewrites — leaving either in place recreates the contradiction.

*Original finding, for the record:*

The mission was already on the site — **twice, and the two didn't match.**

**Live on `/` (Home), under "Our Mission":**
> Aletheon Labs exists to bring clarity to complex organizations. We help businesses use AI,
> automation, data, and technology architecture to make better decisions, improve operations,
> and build with confidence.
> Our focus is not AI for the sake of AI. Our focus is practical intelligence that helps
> organizations see clearly, act decisively, and create measurable value.

**Live on `/about/`, under "Our Mission":**
> Our mission is to help organizations unlock the full value of their data through intelligent,
> practical, and outcome-focused AI solutions.
> We build technology that empowers teams, improves decision-making, and turns data into a
> strategic advantage.

Both are consulting-era. Neither mentions governance, trust, personalization, or either
platform — the four ideas the brief is built on. The brief's own central statement reads as
a mission already:

> *Aletheon Labs enables organizations to use AI confidently by ensuring every interaction is
> secure, governed, consistent, and relevant to the person using it.*

**Decision needed:** one canonical mission, stated once, referenced everywhere. Candidates in
§7. Everything else in this plan is executable without your input; this is the one item that
blocks copy.

---

## 3. Current inventory and disposition

Pulled to `live/` — 5 published pages, 1 draft, 1 default post, 2 nav menus, 1 template,
2 template parts, global styles.

| Page | ID | Live content | Disposition |
|---|---|---|---|
| Home | 18 | Consulting hero, 6 service cards, Discover/Design/Build/Optimize | **Rewrite** to the 11-section structure in the brief |
| About | 11 | Marketing/SCM/ERP analytics positioning | **Rewrite** — company + founder credibility |
| Services | 10 | Fake testimonials, stale 2024 events | **Unpublish now**, rebuild as Solutions |
| AI Solutions | 13 | slug is `experience`, nav label says "Experience", title says "AI Solutions" | **Repurpose** → Aletheon Intelligence platform page; fix the slug/label mismatch |
| Contact | 12 | Reasonable structure, three inquiry paths | **Light rewrite** — retarget CTA to Request a Demo |
| Privacy Policy | 3 | Draft, never published | **Publish** — required, and trust-relevant |
| Hello world! | 1 | WordPress default post | **Delete** |
| — | — | missing | **New:** Aletheon Forge |
| — | — | missing | **New:** Governed AI |
| — | — | missing | **New:** Research |

**Site identity is also stale.** The WordPress site description — which becomes the SEO title
and social share text — still reads:

> "Unlock the power of your data with Aletheon Labs. Our AI-driven software enhances
> visibility, clarity, and actionable insights across Marketing, SCM, and ERP."

Marketing/SCM/ERP is the old framing. This needs to change with the rest.

---

## 4. Information architecture

Per the brief's recommended navigation:

```
Home
Platforms ──┬── Aletheon Intelligence
            └── Aletheon Forge
Governed AI
Solutions
Research
About
Contact
                        [ Request a Demo ]  ← persistent primary button
```

Note this introduces a **dropdown**, which the current flat 5-item menu does not have.
The Bluehost Blueprint header template part will need a submenu block.

**Home page section order** (from the brief, unchanged):

1. Hero — "Build a Trusted and Governed AI Enterprise"
2. Company introduction
3. The Enterprise AI Problem
4. The Aletheon Solution — `Identity → Context → Memory → Knowledge → AI → Governance → Action`
5. The Two Platforms, side by side
6. Personalized by Role — "The Right Intelligence for the Right Person"
7. Governed Across the Enterprise
8. Consistent AI Experiences
9. Business Outcomes
10. Research and Founder Credibility
11. Final CTA — "Build AI Your Organization Can Trust"

**Mission statement placement:** the brief's 11 sections don't include one. Recommend
inserting it between §9 (Business Outcomes) and §10 (Research) — after the site has earned
it with substance, before the founder story it naturally sets up. Full statement on About.

---

## 5. Design direction — what "futuristic" should mean here

The risk with "futuristic" is generic sci-fi styling that undercuts an enterprise trust
pitch. For a company selling *governance and explainability*, the design should read
**precise, instrumented, and deliberate** — closer to mission-control than to neon.

**Signature visual — the Governed AI Layer.** The single highest-value asset on the site.
The brief already describes it: a layer sitting between users/applications above and AI
models/providers below, managing identity, context, memory, policy, and audit. Built as an
animated SVG where request paths flow upward through the governance layer and are visibly
checked, it simultaneously looks futuristic *and* explains the entire product in one glance.
This is what a visitor should screenshot. Everything else supports it.

**Palette.** The existing theme tokens are already most of the way there — `accent-1
#16425B` deep navy and `accent-5 #30A2C5` cyan. Proposal: invert to a dark-first surface
(near-black `#0A0F16` base, navy elevated surfaces), keep cyan as the single luminous accent
reserved for the governance layer and active states, and add one warm signal color for
alerts/human-approval moments. Restraint is the point — one glow color, used sparingly,
reads as engineered; five glow colors read as a template.

**Type.** Retire Playfair Display (a serif display face pulling in an editorial direction
that fights the product story). A single geometric/neo-grotesque family across the site, with
a monospace face for anything representing system output — audit trails, model names, policy
rules. That mono/sans pairing is what makes an interface look instrumented.

**Motion.** Reveal-on-scroll for section entry, animated flow along the Identity → Action
path, and subtle state transitions on the layer diagram. Everything gated behind
`prefers-reduced-motion`. No parallax, no autoplay video.

**Accessibility is not optional here** — dark themes fail contrast easily, and a governance
product that ships an inaccessible site has an obvious credibility problem. Target WCAG AA
minimum on all text, verified rather than assumed.

---

## 6. Technical approach — three options

| | Approach | Design ceiling | Effort | Editing stays in WP? |
|---|---|---|---|---|
| **A** | Blueprint theme + custom global styles + custom CSS | Limited — `nfd-*` patterns constrain layout | Low | Yes |
| **B** | **Child theme with custom `theme.json` + hand-authored block patterns** | High | Medium | **Yes** |
| **C** | Custom block theme, or headless | Total | High | Partially |

**Recommendation: B.** A can't deliver the layer diagram or the dark-first system without
fighting Newfold's patterns at every step. C throws away the Newfold tooling, the Bluehost
integration, and your ability to edit pages without me. B keeps every page editable in the
WordPress block editor while giving full control over tokens, layout, and custom patterns —
and a child theme means Blueprint can still receive updates underneath.

Practically: custom `theme.json` for the token system, a handful of registered block
patterns for the recurring section types, one custom block or inline SVG for the layer
diagram, and page content that remains ordinary Gutenberg markup.

**Both deployment paths are live and verified**, so this is buildable end to end from here:
- Page/copy changes → WP REST API as `andrew`, or WP-CLI over SSH
- Theme files → SSH/`scp` to `~/public_html/wp-content/themes/`
- Staging: Bluehost provides a staging site — the theme work should land there first

---

## 7. Mission statement candidates

**Option 1 — Governance-forward** (closest to the brief's central idea)
> Aletheon Labs exists to make enterprise AI trustworthy. We build the governed intelligence
> layer that ensures every AI interaction is secure, explainable, consistent, and relevant to
> the person using it.

**Option 2 — Clarity thread preserved** (keeps continuity with the current home-page mission)
> Aletheon Labs exists to bring clarity to complex organizations. We build governed AI
> platforms that connect people, memory, business context, and enterprise data — so every
> decision is informed, explainable, and trusted.

**Option 3 — Truth/etymology** (leans on *alētheia*, Greek for truth or unconcealment)
> Aletheon Labs was built on a simple conviction: AI is only valuable when it can be trusted.
> We develop governed platforms that make enterprise intelligence explainable, consistent,
> and accountable to the people who rely on it.

Or keep one of the two existing statements verbatim — but then it should be reconciled to a
single version and updated to name the platforms.

---

## 8. Phasing

**Phase 0 — Today, independent of everything else**
- ✅ Strip fake testimonials and stale events from `/services/` — done, verified live
- ✅ Canonical mission statement decided — governance-forward (§2)
- ☐ Delete the "Hello world!" post

**Phase 1 — Foundation**
- Child theme scaffold, `theme.json` token system, dark-first palette, type system
- Stand up on Bluehost staging
- Update site title and description

**Phase 2 — Signature asset**
- Build the Governed AI Layer diagram (animated SVG, reduced-motion fallback)
- Build the Identity → Action flow component

**Phase 3 — Copy and pages**
- Home rewrite to the 11-section structure, mission inserted at §9.5
- Aletheon Intelligence and Aletheon Forge platform pages
- Governed AI, Solutions, Research, About rewrite, Contact retarget
- Publish the privacy policy

**Phase 4 — Navigation and launch**
- New nav with Platforms dropdown, persistent Request a Demo
- Fix the `experience` slug / "Experience" label / "AI Solutions" title mismatch
- Accessibility and contrast audit, responsive checks, staging → production

---

## Open questions

1. **Mission statement** — which option, or a reconciliation of an existing one? *(blocks copy)*
2. **Demo CTA** — where does "Request a Demo" go? There is a WPForms plugin active and a
   `contact@aletheonlabs.com` address on the contact page. Form, mailto, or a scheduling link?
3. **Research page** — is there publishable material from the Purdue-initiated doctoral
   research (papers, abstracts, talks), or should it stay a narrative credibility page?
4. **Product screenshots** — real UI from Intelligence and Forge would be the strongest proof
   on the platform pages. Available, or do those pages stay diagrammatic?
5. **Staging** — confirm the Bluehost staging site is available so theme work never touches
   production directly.
