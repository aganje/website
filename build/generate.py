#!/usr/bin/env python3
"""
Generate WordPress block markup for every aletheonlabs.com page.

Current offerings are Aletheon Forge and Software Development. The Business
Intelligence IP was sold and is no longer offered by Aletheon Labs. Forge copy
is grounded in its current user guides and implementation, reviewed 2026-10-04.
Nothing here invents customers, testimonials, metrics, or release availability.

Run:  python generate.py     ->  writes build/pages/*.html
"""

import html
import json
import os
import re

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages")

# --------------------------------------------------------------------------
# block helpers
# --------------------------------------------------------------------------


def esc(t):
    return html.escape(t, quote=False)


def section(inner, extra=""):
    cls = ("ale-section " + extra).strip()
    return (
        f'<!-- wp:group {{"className":"{cls}","align":"full",'
        f'"layout":{{"type":"constrained"}}}} -->\n'
        f'<div class="{cls} wp-block-group alignfull">{inner}</div>\n'
        f"<!-- /wp:group -->"
    )


def eyebrow(text, centered=False):
    cls = "ale-eyebrow is-centered" if centered else "ale-eyebrow"
    return (
        f'<!-- wp:paragraph {{"className":"{cls}"}} -->\n'
        f'<p class="{cls}">{esc(text)}</p>\n'
        f"<!-- /wp:paragraph -->"
    )


def heading(text, level=2, cls="ale-h2", centered=False, anchor=None):
    align = ' has-text-align-center' if centered else ""
    meta = f'"textAlign":"center",' if centered else ""
    a = f' id="{anchor}"' if anchor else ""
    return (
        f'<!-- wp:heading {{{meta}"level":{level},"className":"{cls}"}} -->\n'
        f'<h{level} class="wp-block-heading {cls}{align}"{a}>{esc(text)}</h{level}>\n'
        f"<!-- /wp:heading -->"
    )


def h1(text, centered=True):
    align = " has-text-align-center" if centered else ""
    meta = '"textAlign":"center",' if centered else ""
    return (
        f'<!-- wp:heading {{{meta}"level":1,"className":"ale-display"}} -->\n'
        f'<h1 class="wp-block-heading ale-display{align}">{esc(text)}</h1>\n'
        f"<!-- /wp:heading -->"
    )


def para(text, cls="", centered=False):
    classes = " ".join(c for c in [cls, "is-centered" if centered else ""] if c)
    align = " has-text-align-center" if centered else ""
    meta = '"textAlign":"center",' if centered else ""
    cmeta = f'"className":"{classes}",' if classes else ""
    return (
        f"<!-- wp:paragraph {{{meta}{cmeta.rstrip(',')}}} -->\n"
        f'<p class="{classes}{align}">{esc(text)}</p>\n'
        f"<!-- /wp:paragraph -->"
    )


def lede(text, centered=False):
    return para(text, cls="ale-lede", centered=centered)


def spacer(px=32):
    return (
        f'<!-- wp:spacer {{"height":"{px}px"}} -->\n'
        f'<div style="height:{px}px" aria-hidden="true" class="wp-block-spacer"></div>\n'
        f"<!-- /wp:spacer -->"
    )


def buttons(items, centered=True):
    """items: list of (label, url, 'solid'|'ghost')"""
    just = '"justifyContent":"center",' if centered else ""
    out = [
        f'<!-- wp:buttons {{"className":"ale-btns","layout":{{"type":"flex",{just}"flexWrap":"wrap"}}}} -->\n'
        f'<div class="ale-btns wp-block-buttons">'
    ]
    for label, url, style in items:
        cls = "ale-btn" if style == "solid" else "ale-btn-ghost"
        out.append(
            f'<!-- wp:button {{"className":"{cls}"}} -->\n'
            f'<div class="{cls} wp-block-button">'
            f'<a class="wp-block-button__link wp-element-button" href="{url}">{esc(label)}</a>'
            f"</div>\n<!-- /wp:button -->"
        )
    out.append("</div>\n<!-- /wp:buttons -->")
    return "\n\n".join(out)


def raw(markup):
    return f"<!-- wp:html -->\n{markup}\n<!-- /wp:html -->"


def cards(items, variant="", cols=3):
    """items: list of (label, title, body). Rendered as raw HTML grid."""
    v = f" {variant}" if variant else ""
    out = [f'<div class="ale-grid is-{cols}">']
    for label, title, body in items:
        num = f'<span class="ale-card-num">{esc(label)}</span>' if label else ""
        out.append(
            f'<div class="ale-card{v}">{num}'
            f'<h3 class="ale-h3">{esc(title)}</h3>'
            f"<p>{esc(body)}</p></div>"
        )
    out.append("</div>")
    return raw("".join(out))


def checklist(items, two_col=True):
    cls = "ale-list is-2col" if two_col else "ale-list"
    lis = "".join(f"<li>{esc(i)}</li>" for i in items)
    return raw(f'<ul class="{cls}">{lis}</ul>')


def stats(items):
    out = ['<div class="ale-grid is-3">']
    for label, text in items:
        out.append(f'<div class="ale-stat"><b>{esc(label)}</b><span>{esc(text)}</span></div>')
    out.append("</div>")
    return raw("".join(out))


def roles(items):
    out = ['<div class="ale-roles">']
    for name, desc in items:
        out.append(f'<div class="ale-role"><strong>{esc(name)}</strong><em>{esc(desc)}</em></div>')
    out.append("</div>")
    return raw("".join(out))


def flow():
    steps = ["Product", "Repository", "Mission", "Context", "Agent", "Review", "Evidence"]
    out = ['<div class="ale-flow" role="list" aria-label="A conceptual Forge engineering workflow">']
    for i, s in enumerate(steps):
        out.append(
            f'<div class="ale-flow-step" role="listitem" style="--i:{i}"><span>{esc(s)}</span></div>'
        )
    out.append("</div>")
    return raw("".join(out))


def home_hero():
    """Cinematic, code-native homepage hero. Decorative motion is CSS-only."""
    return raw(
        '<div class="ale-home-hero">'
        '<div class="ale-home-hero__copy">'
        '<div class="ale-system-state"><span aria-hidden="true"></span>'
        'AI engineering with human direction</div>'
        '<p class="ale-eyebrow">Aletheon Labs &middot; Software Engineering</p>'
        '<h1 class="ale-display">Coordinate AI Engineering '
        '<span class="ale-grad">with Human Control</span></h1>'
        '<p class="ale-lede">Aletheon Forge brings your AI coding assistants, repositories, '
        'context, and review gates into one engineering workflow. Our Software Development '
        'team builds, integrates, and modernizes the systems your organization needs.</p>'
        '<div class="ale-hero-actions">'
        '<a class="ale-hero-btn is-primary" href="/aletheon-forge/">Explore Aletheon Forge '
        '<span aria-hidden="true">&rarr;</span></a>'
        '<a class="ale-hero-btn is-secondary" href="/software-development/">Software Development</a>'
        '</div>'
        '<div class="ale-hero-proof" aria-label="Platform qualities">'
        '<span>Shared context</span><span>Review gates</span><span>Verification evidence</span>'
        '</div>'
        '</div>'
        '<div class="ale-core-visual" role="img" '
        'aria-label="A conceptual engineering workflow connects repositories, context, memory, and human review around AI coding agents.">'
        '<div class="ale-core-visual__frame" aria-hidden="true"></div>'
        '<svg class="ale-core-orbits" viewBox="0 0 620 620" aria-hidden="true" focusable="false" '
        'xmlns="http://www.w3.org/2000/svg">'
        '<defs>'
        '<linearGradient id="ale-orbit-gradient" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#C084FC"/><stop offset="0.52" stop-color="#A855F7"/>'
        '<stop offset="1" stop-color="#3B1BC4"/></linearGradient>'
        '<radialGradient id="ale-core-gradient"><stop offset="0" stop-color="#A855F7" stop-opacity=".8"/>'
        '<stop offset=".55" stop-color="#6D28D9" stop-opacity=".34"/>'
        '<stop offset="1" stop-color="#0A0810" stop-opacity="0"/></radialGradient>'
        '<filter id="ale-soft-glow" x="-80%" y="-80%" width="260%" height="260%">'
        '<feGaussianBlur stdDeviation="7" result="blur"/><feMerge><feMergeNode in="blur"/>'
        '<feMergeNode in="SourceGraphic"/></feMerge></filter>'
        '</defs>'
        '<circle class="hv-halo" cx="310" cy="310" r="178" fill="url(#ale-core-gradient)"/>'
        '<g class="hv-grid">'
        '<path d="M74 310H546M310 74V546"/><path d="M144 144L476 476M476 144L144 476"/>'
        '<circle cx="310" cy="310" r="92"/><circle cx="310" cy="310" r="156"/>'
        '<circle cx="310" cy="310" r="224"/>'
        '</g>'
        '<g class="hv-orbit is-outer"><ellipse cx="310" cy="310" rx="246" ry="106"/>'
        '<circle class="hv-node" cx="64" cy="310" r="5"/><circle class="hv-node" cx="556" cy="310" r="5"/></g>'
        '<g class="hv-orbit is-mid"><ellipse cx="310" cy="310" rx="206" ry="92" '
        'transform="rotate(58 310 310)"/><circle class="hv-node" cx="188" cy="144" r="5"/></g>'
        '<g class="hv-orbit is-inner"><ellipse cx="310" cy="310" rx="170" ry="74" '
        'transform="rotate(-54 310 310)"/><circle class="hv-node" cx="410" cy="172" r="4"/></g>'
        '<g class="hv-core" filter="url(#ale-soft-glow)">'
        '<path d="M310 207L398 258V360L310 411L222 360V258Z"/>'
        '<path class="hv-core-inner" d="M310 235L374 272V346L310 383L246 346V272Z"/>'
        '</g>'
        '<path class="hv-signal" d="M115 310C168 310 202 275 244 268"/>'
        '<path class="hv-signal is-reverse" d="M376 350C430 362 468 338 514 310"/>'
        '</svg>'
        '<div class="ale-core-center" aria-hidden="true">'
        '<small>AI Engineering</small><strong>ALETHEON</strong><span>Human direction</span>'
        '</div>'
        '<span class="ale-orbit-label is-identity" aria-hidden="true">Repository</span>'
        '<span class="ale-orbit-label is-context" aria-hidden="true">Context</span>'
        '<span class="ale-orbit-label is-memory" aria-hidden="true">Memory</span>'
        '<span class="ale-orbit-label is-policy" aria-hidden="true">Review</span>'
        '<div class="ale-telemetry is-top" aria-hidden="true"><b>01</b><span>Define the mission</span></div>'
        '<div class="ale-telemetry is-bottom" aria-hidden="true"><b>07</b><span>Review the evidence</span></div>'
        '</div>'
        '<div class="ale-signal-rail" role="list" aria-label="Engineering workflow stages">'
        '<div role="listitem"><span class="ale-status-dot" aria-hidden="true"></span><b>Repository</b><small>Project context</small></div>'
        '<div role="listitem"><span class="ale-status-dot" aria-hidden="true"></span><b>Mission</b><small>Defined scope</small></div>'
        '<div role="listitem"><span class="ale-status-dot" aria-hidden="true"></span><b>Review</b><small>Human decisions</small></div>'
        '<div role="listitem"><span class="ale-status-dot" aria-hidden="true"></span><b>Checks</b><small>Recorded evidence</small></div>'
        '</div>'
        '</div>'
    )


def research_hero():
    """Research landing hero with a code-native architecture field."""
    return raw(
        '<div class="ale-research-hero">'
        '<div class="ale-research-hero__copy">'
        '<div class="ale-research-state"><span aria-hidden="true"></span>'
        'Research vector 01 &middot; Systems before models</div>'
        '<p class="ale-eyebrow">Research &amp; Foundations</p>'
        '<h1 class="ale-display">Architecting the conditions for '
        '<span class="ale-grad">trusted enterprise AI.</span></h1>'
        '<p class="ale-lede">Aletheon&rsquo;s engineering tools begin with a simple position: '
        'successful enterprise AI requires more than model accuracy. Trust must be designed '
        'into the system around the model.</p>'
        '<div class="ale-research-principles" aria-label="Research principles">'
        '<span>Architecture-led</span><span>Governance-native</span><span>Human-accountable</span>'
        '</div>'
        '</div>'
        '<div class="ale-research-field" role="img" '
        'aria-label="A systems architecture connects organizational context, governed memory, '
        'explainability, and governance around an AI model.">'
        '<div class="ale-research-field__grid" aria-hidden="true"></div>'
        '<svg viewBox="0 0 620 620" aria-hidden="true" focusable="false" '
        'xmlns="http://www.w3.org/2000/svg">'
        '<defs><linearGradient id="ale-research-line" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#C084FC"/><stop offset=".55" stop-color="#A855F7"/>'
        '<stop offset="1" stop-color="#3B1BC4"/></linearGradient>'
        '<radialGradient id="ale-research-core"><stop offset="0" stop-color="#A855F7" stop-opacity=".38"/>'
        '<stop offset="1" stop-color="#0A0810" stop-opacity="0"/></radialGradient></defs>'
        '<circle class="rf-glow" cx="310" cy="310" r="178" fill="url(#ale-research-core)"/>'
        '<circle class="rf-ring is-outer" cx="310" cy="310" r="236"/>'
        '<circle class="rf-ring is-inner" cx="310" cy="310" r="142"/>'
        '<path class="rf-axis" d="M310 74V546M74 310H546M143 143L477 477M477 143L143 477"/>'
        '<path class="rf-path" d="M310 74L477 143L546 310L477 477L310 546L143 477L74 310L143 143Z"/>'
        '<g class="rf-core"><path d="M310 216L391 263V357L310 404L229 357V263Z"/>'
        '<path class="rf-core__inner" d="M310 247L364 278V342L310 373L256 342V278Z"/></g>'
        '<g class="rf-node"><circle cx="310" cy="74" r="8"/><circle cx="546" cy="310" r="8"/>'
        '<circle cx="310" cy="546" r="8"/><circle cx="74" cy="310" r="8"/></g>'
        '</svg>'
        '<div class="ale-research-field__center" aria-hidden="true">'
        '<span>System layer</span><strong>TRUST</strong><small>Designed, not assumed</small></div>'
        '<span class="ale-research-node is-context" aria-hidden="true"><b>01</b>Context</span>'
        '<span class="ale-research-node is-memory" aria-hidden="true"><b>02</b>Memory</span>'
        '<span class="ale-research-node is-governance" aria-hidden="true"><b>03</b>Governance</span>'
        '<span class="ale-research-node is-explainability" aria-hidden="true"><b>04</b>Explainability</span>'
        '<div class="ale-research-field__caption" aria-hidden="true">'
        '<span>Architecture status</span><b>Properties aligned</b></div>'
        '</div>'
        '</div>'
    )


def founder_dossier():
    credentials = [
        (
            "01",
            "Engineering",
            "Former Microsoft engineer",
            "Software built and operated at platform scale, where correctness, security, and operational discipline are not optional.",
        ),
        (
            "02",
            "Architecture",
            "Software architecture",
            "Designing systems that stay coherent as they grow&mdash;the same problem governed AI faces once it spreads across an enterprise.",
        ),
        (
            "03",
            "Distributed systems",
            "Microservice expertise",
            "Decomposing systems so each part remains independently deployable, observable, and governable at scale.",
        ),
        (
            "04",
            "Transformation",
            "$100B to mid-cap",
            "Business transformation delivered across the full range of enterprise scale, where the constraints differ sharply at each end.",
        ),
        (
            "05",
            "Publication",
            "Published author",
            "Written work in the field, predating and informing the architecture Aletheon is built on.",
        ),
        (
            "06",
            "Research",
            "Doctoral research, Purdue",
            "Doctoral research initiated at Purdue, from which the governed AI layer&rsquo;s design principles are drawn.",
        ),
    ]
    items = []
    for number, label, title, body in credentials:
        items.append(
            f'<article class="ale-credential"><div class="ale-credential__meta">'
            f'<span>{number}</span><em>{label}</em></div>'
            f'<h3>{title}</h3><p>{body}</p></article>'
        )

    return raw(
        '<div class="ale-founder-dossier">'
        '<div class="ale-founder-profile">'
        '<div class="ale-founder-profile__top"><div class="ale-founder-portrait">'
        '<img src="/wp-content/uploads/2026/08/andrew-ganje-portrait.jpg" '
        'width="200" height="200" alt="Portrait of Dr. Andrew Ganje" loading="lazy" decoding="async">'
        '<span aria-hidden="true">AG</span></div><div><p class="ale-eyebrow">Founder / Research lead</p>'
        '<p class="ale-founder-index">Dossier &middot; 001</p></div></div>'
        '<h2 class="ale-h2">Dr. Andrew Ganje</h2>'
        '<p class="ale-founder-intro">Aletheon Labs was founded by Dr. Andrew Ganje&mdash;a '
        'former Microsoft engineer, software architect, and published author, whose doctoral '
        'research, initiated at Purdue, underpins the platform&rsquo;s design.</p>'
        '<p class="ale-founder-body">The work behind Aletheon draws on business transformations '
        'delivered across the full range of enterprise scale, from $100 billion organizations '
        'to mid-cap companies, alongside deep practice in enterprise architecture, microservice '
        'design, business applications, data platforms, integrations, and artificial intelligence.</p>'
        '<div class="ale-founder-tags" aria-label="Areas of experience">'
        '<span>Engineering</span><span>Architecture</span><span>Research</span></div>'
        '</div>'
        '<div class="ale-credential-matrix" aria-label="Founder credentials">'
        + ''.join(items)
        + '</div></div>'
    )


def research_thesis():
    return raw(
        '<div class="ale-research-thesis">'
        '<div class="ale-research-thesis__copy">'
        '<p class="ale-eyebrow">Why it matters here</p>'
        '<h2 class="ale-h2">Enterprise AI is an <span class="ale-grad">architecture problem.</span></h2>'
        '<p class="ale-lede">Governance, traceability, memory, and role-relevance are not '
        'features a model provides. They are properties a system has to be designed to hold. '
        'That is why Aletheon is built by people whose background is distributed systems and '
        'enterprise architecture&mdash;and why the research came before the product.</p>'
        '</div>'
        '<div class="ale-thesis-path" role="list" aria-label="Path from information to accountable action">'
        '<div role="listitem"><span>01</span><b>Source</b><small>Trusted information</small></div>'
        '<i aria-hidden="true">&rarr;</i>'
        '<div role="listitem"><span>02</span><b>Context</b><small>Role and responsibility</small></div>'
        '<i aria-hidden="true">&rarr;</i>'
        '<div role="listitem"><span>03</span><b>Policy</b><small>Governance applied</small></div>'
        '<i aria-hidden="true">&rarr;</i>'
        '<div role="listitem"><span>04</span><b>Action</b><small>Traceable decision</small></div>'
        '</div>'
        '</div>'
    )


def mission_block():
    return raw(
        '<div class="ale-mission">'
        '<p class="ale-eyebrow is-centered">Our Mission</p>'
        "<blockquote>Aletheon Labs exists to make enterprise AI trustworthy. "
        "We build AI engineering tools and custom software that connect technical work "
        "to its context, standards, evidence, and the people responsible for delivery.</blockquote>"
        "</div>"
    )


# --------------------------------------------------------------------------
# the signature asset: the governed AI layer
# --------------------------------------------------------------------------

TOP_NODES = [
    ("Product Leads", 60),
    ("Engineering Leads", 205),
    ("Developers", 350),
    ("Architects", 470),
    ("Repositories", 600),
    ("Delivery Teams", 762),
]
BOTTOM_NODES = [
    ("Claude Code", 70),
    ("Codex", 210),
    ("Gemini CLI", 350),
    ("Grok", 490),
    ("GitHub Copilot", 620),
    ("AI Coding Tools", 780),
]
LAYER_CHIPS = [
    ("Product", 62),
    ("Context", 180),
    ("Memory", 296),
    ("Skills", 412),
    ("Review", 540),
    ("Evidence", 648),
    ("Evaluation", 754),
]


def diagram():
    p = []
    p.append(
        '<svg class="ale-diagram" viewBox="0 0 940 520" role="img" '
        'xmlns="http://www.w3.org/2000/svg" '
        'aria-label="Conceptual Forge workflow: engineering teams and repositories define '
        'work above; AI coding tools execute it below. Product context, memory, skills, '
        'human review, evidence, and evaluation support the engineering workflow.">'
    )

    # band labels
    p.append('<text x="18" y="26" class="d-accent" font-size="11" letter-spacing="2.2">ENGINEERING TEAMS &amp; REPOSITORIES</text>')
    p.append('<text x="18" y="288" class="d-accent" font-size="11" letter-spacing="2.2">FORGE ENGINEERING WORKFLOW</text>')
    p.append('<text x="18" y="452" class="d-accent" font-size="11" letter-spacing="2.2">AI CODING ASSISTANTS</text>')

    # top row
    for label, x in TOP_NODES:
        w = max(96, len(label) * 7.4 + 22)
        p.append(f'<rect class="d-node" x="{x}" y="44" width="{w:.0f}" height="40" rx="8"/>')
        p.append(f'<text x="{x + w / 2:.0f}" y="69" text-anchor="middle" font-size="12">{esc(label)}</text>')

    # flows down into the layer
    for label, x in TOP_NODES:
        w = max(96, len(label) * 7.4 + 22)
        cx = x + w / 2
        p.append(f'<path class="d-flow" d="M{cx:.0f} 84 C {cx:.0f} 140, 470 150, 470 196"/>')

    # the layer itself
    p.append('<rect class="d-layer" x="18" y="200" width="904" height="86" rx="14"/>')
    for label, x in LAYER_CHIPS:
        p.append(f'<rect class="d-node" x="{x}" y="222" width="104" height="42" rx="7"/>')
        p.append(f'<text x="{x + 52}" y="248" text-anchor="middle" font-size="11.5">{esc(label)}</text>')

    # flows down to providers
    for label, x in BOTTOM_NODES:
        w = max(96, len(label) * 7.4 + 22)
        cx = x + w / 2
        p.append(f'<path class="d-flow" d="M470 290 C 470 340, {cx:.0f} 348, {cx:.0f} 400"/>')

    # bottom row
    for label, x in BOTTOM_NODES:
        w = max(96, len(label) * 7.4 + 22)
        p.append(f'<rect class="d-node" x="{x}" y="400" width="{w:.0f}" height="40" rx="8"/>')
        p.append(f'<text x="{x + w / 2:.0f}" y="425" text-anchor="middle" font-size="12">{esc(label)}</text>')

    # travelling pulses on the spine
    for i, y in enumerate((150, 330)):
        p.append(f'<circle class="d-pulse" cx="470" cy="{y}" r="3.4" style="animation-delay:{i * 1.1}s"/>')

    p.append("</svg>")
    return raw("".join(p))


# --------------------------------------------------------------------------
# pages
# --------------------------------------------------------------------------

DEMO = "/contact/"
PAGES = {}

# The two current offerings: Aletheon Forge and Software Development.
OFFERINGS_GRID = (
    '<div class="ale-grid is-2">'
    '<div class="ale-card is-platform"><span class="ale-card-num">Product</span>'
    '<h3 class="ale-h3">Aletheon Forge</h3>'
    '<p>Bring your AI coding agents into one engineering workflow. Define missions, '
    'connect repositories, supply shared skills and project knowledge, and follow '
    'execution, review, verification, and lessons in a local-first Windows application.</p>'
    '<p style="margin-top:1.1rem"><a class="ale-btn" href="/aletheon-forge/">Explore Forge</a></p></div>'
    '<div class="ale-card is-platform"><span class="ale-card-num">Services</span>'
    '<h3 class="ale-h3">Software Development</h3>'
    '<p>Custom software engineering for systems that need to be built, integrated, '
    'or modernized. Our work spans enterprise architecture, business applications, '
    'data platforms, integrations, and applied AI.</p>'
    '<p style="margin-top:1.1rem"><a class="ale-btn" href="/software-development/">Explore Software Development</a></p></div>'
    '</div>'
)

# ------------------------------ HOME --------------------------------------

PAGES["home"] = "\n\n".join([
    section(home_hero(), "is-home-hero"),
    section("\n\n".join([
        eyebrow("Who We Are"),
        heading("AI engineering tools and the team to build with you"),
        lede("Aletheon Labs develops Aletheon Forge and delivers custom Software Development. "
             "Forge helps developers and engineering leads coordinate AI coding agents. "
             "Our engineering services turn requirements into applications, integrations, "
             "and modernized systems."),
    ]), "is-home-intro"),
    section("\n\n".join([
        eyebrow("The Engineering Challenge"),
        heading("Give AI-assisted work a shared structure"),
        lede("Coding assistants work best with a clear task, relevant project context, "
             "and a way to review what they produce. Those foundations need to carry "
             "across agents, repositories, and the people directing the work."),
        spacer(28),
        cards([
            ("01", "Defined missions", "Describe the work, its constraints, and the evidence needed to accept it."),
            ("02", "Repository context", "Keep each agent connected to the codebase and instructions in scope."),
            ("03", "Shared skills", "Give coding agents reusable engineering instructions suited to the task."),
            ("04", "Retained decisions", "Keep architectural choices and lessons available for future work."),
            ("05", "Coordinated execution", "Follow agent runs within a common product and mission structure."),
            ("06", "Human review", "Record questions and approval decisions as work progresses."),
            ("07", "Verification evidence", "Review configured checks and acceptance evidence alongside the implementation."),
            ("08", "Connected knowledge", "Explore relationships between repositories, work, and retained project knowledge."),
            ("09", "Reviewable delivery", "Connect the resulting changes to source control and pull request workflows."),
        ], variant="is-problem", cols=3),
    ]), "is-home-problem"),
    section("\n\n".join([
        eyebrow("The Forge Workflow", centered=True),
        heading("Connect the work, the context, and the people responsible", centered=True),
        lede("A conceptual view of how Forge brings engineering teams, repositories, "
             "shared knowledge, and installed AI coding tools into one workflow.", centered=True),
        spacer(40), diagram(),
    ]), "is-home-layer"),
    section("\n\n".join([
        eyebrow("What We Offer"),
        heading("Two ways to move your software work forward"),
        lede("Aletheon Forge for AI-assisted engineering, and Software Development "
             "for the systems your organization needs built."),
        spacer(28), raw(OFFERINGS_GRID),
    ]), "is-home-platforms"),
    section("\n\n".join([
        eyebrow("Skills and Project Knowledge"),
        heading("Give agents context they can use"),
        lede("Forge routes repository instructions, focused skills, and approved memories "
             "into agent work. Decisions and lessons can be assessed and retained for "
             "the next mission, while the knowledge map helps teams explore what is connected."),
        spacer(28),
        roles([
            ("Product lead", "Define the intended outcome and the scope of the work."),
            ("Engineering lead", "Guide technical direction, review decisions, and acceptance."),
            ("Developer", "Work with coding agents, repositories, changes, and checks."),
            ("Architect", "Connect implementation work to system design and retained decisions."),
        ]),
    ]), "is-home-roles"),
    section("\n\n".join([
        eyebrow("Human Direction"),
        heading("Review the work with its evidence"),
        lede("Keep mission history, agent questions, approval decisions, and configured "
             "verification results together. Forge gives teams a place to follow the "
             "work and decide what is ready to move forward."),
        spacer(24), checklist([
            "Mission scope and acceptance criteria", "Agent run history",
            "Questions and approval decisions", "Configured checks and acceptance evidence",
            "Repository changes and pull request preparation", "Assessed memories and retained lessons",
        ]),
    ]), "is-home-governance"),
    section("\n\n".join([
        eyebrow("Engineering Outcomes"), heading("Build a workflow your team can follow"),
        spacer(28), stats([
            ("Context", "Give agent runs the repository instructions and knowledge relevant to their work."),
            ("Continuity", "Retain decisions and lessons across missions."),
            ("Coordination", "Connect products, repositories, missions, and runs."),
            ("Review", "Bring human decisions and acceptance evidence into the workflow."),
            ("Delivery", "Prepare changes for existing source control and review practices."),
            ("Engineering", "Work with our team on custom applications, integrations, and modernization."),
        ]),
    ]), "is-home-outcomes"),
    section(mission_block(), "is-tight is-home-mission"),
    section("\n\n".join([
        eyebrow("Research and Founder Credibility"), heading("Grounded in research, built from practice"),
        lede("Aletheon Labs was founded by Dr. Andrew Ganje — a former Microsoft engineer, "
             "software architect, microservice specialist, and published author, whose "
             "doctoral research was initiated at Purdue."),
        para("That work spans business transformations from $100 billion organizations "
             "to mid-cap companies, across enterprise architecture, business applications, "
             "data platforms, integrations, and artificial intelligence.", cls="ale-muted"),
        spacer(20), buttons([("Read the Research", "/research/", "ghost")], centered=False),
    ]), "is-home-research"),
    section("\n\n".join([
        heading("Start with Forge or a software project", centered=True),
        lede("Explore Forge with your engineering team, or discuss a system you need "
             "built, integrated, or modernized.", centered=True),
        spacer(12), buttons([
            ("Request a Forge Demo", "/contact/", "solid"),
            ("Discuss a Project", "/contact/", "ghost"),
        ]),
    ]), "is-hero is-home-cta"),
])

# ------------------------ ALETHEON INTELLIGENCE ---------------------------


# --------------------------- ALETHEON FORGE -------------------------------

PAGES["aletheon-forge"] = "\n\n".join([
    section("\n\n".join([
        eyebrow("AI Engineering Orchestration", centered=True), h1("Aletheon Forge"),
        lede("Bring your AI coding agents into one engineering workflow. Define the work, "
             "connect repositories, supply shared skills and project knowledge, and follow "
             "execution, review, verification, and lessons in a local-first Windows application.", centered=True),
        spacer(12), buttons([
            ("Request a Forge Demo", "/contact/", "solid"),
            ("Discuss Software Development", "/contact/", "ghost"),
        ]),
    ]), "is-hero"),
    section("\n\n".join([
        eyebrow("Connected Coding Tools"), heading("Coordinate the assistants your team uses"),
        lede("Forge connects installed Claude Code, Codex, Gemini CLI, Grok, and GitHub "
             "Copilot command-line tools. Their adapters bring agent work into a common "
             "mission and run workflow while using each tool's supported capabilities."),
        para("Forge runs locally on Windows. Connected coding tools require their own "
             "installation and provider access, and their available capabilities vary.", cls="ale-muted"),
    ])),
    section("\n\n".join([
        eyebrow("Core Capabilities"), heading("From a scoped task to reviewable results"), spacer(24),
        checklist([
            "Connect installed AI coding assistants", "Organize products, repositories, missions, and runs",
            "Plan features, fixes, refactoring, and new applications", "Define mission acceptance criteria",
            "Route repository instructions, skills, and approved memories",
            "Coordinate mission execution with Autopilot", "Follow agent questions and approval decisions",
            "Review configured checks and independent acceptance evidence",
            "Explore connected engineering knowledge", "Assess and retain memories and lessons",
            "Work with Git repositories", "Prepare GitHub and Azure Repos pull requests when configured",
        ]),
    ])),
    section("\n\n".join([
        eyebrow("Structure"), heading("Keep work connected from product to run"),
        lede("Plans break larger goals into missions. Each mission stays connected to the "
             "product, repository, acceptance criteria, and the agent runs carrying it out."),
        spacer(28), cards([
            ("01", "Product", "The system or product being built, with its goals and shared knowledge."),
            ("02", "Repository", "The codebase, repository instructions, and technical context in scope."),
            ("03", "Mission", "A defined unit of engineering work with constraints and acceptance criteria."),
            ("04", "Run", "An agent execution with recorded activity, questions, and available verification evidence."),
        ], cols=4),
    ])),
    section("\n\n".join([
        eyebrow("AI Enablers"), heading("Keep useful engineering knowledge in the workflow"),
        spacer(28), cards([
            ("01", "Skills", "Focused, reusable instructions that guide agents through particular kinds of engineering work."),
            ("02", "Context", "Repository instructions and selected knowledge routed into the mission and agent run."),
            ("03", "Memories", "Assessed engineering decisions and lessons retained for later work."),
            ("04", "Knowledge map", "A connected view of engineering knowledge that helps teams explore relationships and context."),
        ], cols=2),
    ])),
    section("\n\n".join([
        eyebrow("Review and Delivery"), heading("Follow the decisions as well as the code"),
        lede("Review run history, agent questions, approval decisions, and configured checks "
             "alongside repository changes. Prepare pull requests for GitHub or Azure Repos "
             "when those integrations are configured, and retain lessons from the work."),
        spacer(24), flow(),
    ])),
    section("\n\n".join([
        heading("See Forge with your engineering workflow", centered=True),
        lede("Discuss your repositories, coding tools, and review process with our team.", centered=True),
        spacer(12), buttons([
            ("Request a Forge Demo", "/contact/", "solid"),
            ("Explore Software Development", "/software-development/", "ghost"),
        ]),
    ]), "is-hero"),
])

# ---------------------------- GOVERNED AI ---------------------------------

PAGES["governed-ai"] = "\n\n".join([
    section("\n\n".join([
        eyebrow("Engineering Principles", centered=True), h1("Governed AI Engineering"),
        lede("Give AI-assisted software work clear scope, relevant context, human review, "
             "and verification evidence. These principles shape Aletheon Forge and the "
             "custom systems our Software Development team builds.", centered=True),
    ]), "is-hero"),
    section("\n\n".join([diagram()]), "is-tight"),
    section("\n\n".join([
        eyebrow("In the Workflow"), heading("Make engineering work reviewable"),
        spacer(24), checklist([
            "Product and repository context", "Defined missions and acceptance criteria",
            "Repository instructions and reusable skills", "Selected context for agent runs",
            "Approved memories and retained decisions", "Agent questions and approval decisions",
            "Run history and configured verification checks", "Independent acceptance evidence",
            "Source control and pull request preparation", "Lessons assessed for future use",
        ]),
    ])),
    section("\n\n".join([
        eyebrow("Core Principles"), heading("Keep people accountable for delivery"),
        spacer(28), cards([
            ("01", "Clear intent", "Define what needs to change, the constraints, and what acceptance requires before an agent starts work."),
            ("02", "Relevant context", "Give agents repository instructions, focused skills, and selected knowledge connected to the task."),
            ("03", "Human decisions", "Bring questions, approval decisions, and technical review into the engineering workflow."),
            ("04", "Evidence", "Review configured checks, acceptance results, and source changes when deciding whether work is ready."),
        ], cols=2),
    ])),
    section("\n\n".join([
        eyebrow("Engineering Memory"), heading("Retain decisions teams can reuse"),
        lede("Forge retains engineering knowledge and assesses proposed memory revisions "
             "for reuse. Skills, approved memories, and repository context can inform later "
             "missions, while the knowledge map helps teams explore their connections."),
        spacer(24), checklist([
            "Architectural decisions and project context", "Focused instructions and reusable skills",
            "Assessed memories and lessons", "Connections across engineering knowledge",
        ]),
    ])),
    section("\n\n".join([
        heading("Put these principles to work", centered=True), spacer(12),
        buttons([("Explore Aletheon Forge", "/aletheon-forge/", "solid"),
                 ("Explore Software Development", "/software-development/", "ghost")]),
    ]), "is-hero"),
])

# ------------------------------ RESEARCH ----------------------------------

PAGES["research"] = "\n\n".join(
    [
        section(
            research_hero(),
            "is-research-hero",
        ),
        section(
            founder_dossier(),
            "is-research-founder",
        ),
        section(
            research_thesis(),
            "is-research-thesis",
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("Research Position"),
                    heading("Model accuracy is not sufficient"),
                    lede(
                        "Enterprise AI also requires trusted information, governance, explainability, "
                        "organizational context, memory, and alignment with business outcomes. These are "
                        "architectural properties, not model properties — which is why Aletheon builds them "
                        "into a layer rather than expecting them from a provider."
                    ),
                    spacer(28),
                    cards(
                        [
                            ("Area 01", "Trusted information", "What has to be true about a source, and about the path from source to recommendation, before a person should act on it."),
                            ("Area 02", "Organizational context", "How repository instructions, architectural decisions, and project requirements shape engineering work."),
                            ("Area 03", "Governed memory", "How systems retain what matters across interactions without exceeding what a user is authorized to know."),
                            ("Area 04", "Explainability in practice", "What traceability has to look like for a decision-maker, rather than for a model evaluator."),
                        ],
                        variant="is-research-area",
                        cols=2,
                    ),
                ]
            ),
            "is-research-areas",
        ),
        section(
            "\n\n".join(
                [
                    heading("Discuss the research", centered=True),
                    lede(
                        "For research collaboration, academic partnership, or technical discussion of the "
                        "governed AI layer.",
                        centered=True,
                    ),
                    spacer(12),
                    buttons([("Start a Conversation", DEMO, "solid")]),
                ]
            ),
            "is-research-cta",
        ),
    ]
)

# ------------------------------ SOLUTIONS ---------------------------------

PAGES["solutions"] = "\n\n".join(
    [
        section(
            "\n\n".join(
                [
                    eyebrow("Solutions", centered=True),
                    h1("Put AI to Work in Software Engineering"),
                    lede(
                        "Organize AI-assisted coding with Aletheon Forge, or work with Aletheon Labs "
                        "to build, integrate, and modernize the software your organization needs.",
                        centered=True,
                    ),
                    spacer(12),
                    buttons([("Request a Forge Demo", DEMO, "solid"), ("Discuss a Project", DEMO, "ghost")]),
                ]
            ),
            "is-hero",
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("Engineering Use Cases"),
                    heading("Connect the work, the context, and the people responsible"),
                    spacer(28),
                    cards(
                        [
                            ("01", "Coordinate coding work", "Use Forge to organize products, repositories, missions, and runs with the AI coding assistants installed on your machine."),
                            ("02", "Prepare repository context", "Give coding assistants the relevant repository context, skills, and approved memories for each mission."),
                            ("03", "Review changes and results", "Use approvals and verification to keep people involved in the coding workflow and evaluate the work produced."),
                            ("04", "Retain engineering knowledge", "Capture useful lessons and approved memories so future missions can draw on what the team has learned."),
                            ("05", "Build business software", "Develop applications and data platforms around your organization's requirements, existing systems, and operating needs."),
                            ("06", "Integrate and modernize", "Connect services and data, plan architecture changes, and update existing software with attention to its business logic."),
                        ],
                        cols=3,
                    ),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("Two Offerings"),
                    heading("Choose the right starting point"),
                    lede(
                        "Forge brings structure to work with AI coding assistants. Software Development "
                        "provides custom engineering for the applications, integrations, and architecture you need."
                    ),
                    spacer(28),
                    raw(OFFERINGS_GRID),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    heading("Start with your engineering goals", centered=True),
                    lede("Tell us about your workflow or the software you need built.", centered=True),
                    spacer(12),
                    buttons([("Request a Forge Demo", DEMO, "solid"), ("Discuss a Project", DEMO, "ghost")]),
                ]
            ),
            "is-hero",
        ),
    ]
)

# -------------------------------- ABOUT -----------------------------------

PAGES["about"] = "\n\n".join(
    [
        section(
            "\n\n".join(
                [
                    eyebrow("About Aletheon Labs", centered=True),
                    h1("AI Software and Engineering, Built on Research"),
                    lede(
                        "Aletheon Labs develops Aletheon Forge for AI-assisted software engineering "
                        "and provides custom software development for organizations.",
                        centered=True,
                    ),
                ]
            ),
            "is-hero",
        ),
        section(
            mission_block(),
            "is-tight",
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("What We Build"),
                    heading("Aletheon Forge and Software Development"),
                    lede(
                        "Forge organizes work with installed AI coding assistants. Our software development "
                        "services bring enterprise architecture and engineering experience to custom applications, "
                        "data platforms, integrations, applied AI, and modernization."
                    ),
                    spacer(28),
                    raw(OFFERINGS_GRID),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("What We Believe"),
                    heading("Good software begins with context and accountable decisions"),
                    lede(
                        "AI-assisted engineering needs the same discipline as the systems it helps build: "
                        "clear requirements, relevant context, reviewable work, and people responsible for the outcome."
                    ),
                    spacer(24),
                    checklist(
                        [
                            "Understand the organization and its systems",
                            "Give AI assistants relevant context and skills",
                            "Keep people involved in approvals and review",
                            "Verify the work against its requirements",
                            "Capture architecture decisions and useful lessons",
                            "Carry approved knowledge into future work",
                        ]
                    ),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("Founder"),
                    heading("Founded on research and enterprise practice"),
                    lede(
                        "Aletheon Labs was founded by Dr. Andrew Ganje — a former Microsoft engineer, "
                        "software architect, microservice specialist, and published author, whose doctoral "
                        "research was initiated at Purdue."
                    ),
                    para(
                        "That background spans business transformations from $100 billion organizations to "
                        "mid-cap companies, alongside enterprise architecture, microservice design, "
                        "business applications, data platforms, integrations, and artificial intelligence.",
                        cls="ale-muted",
                    ),
                    spacer(20),
                    buttons([("Read the Research", "/research/", "ghost")], centered=False),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    heading("Build Your Next Step with Aletheon", centered=True),
                    spacer(12),
                    buttons([("Request a Forge Demo", DEMO, "solid"), ("Discuss a Project", DEMO, "ghost")]),
                ]
            ),
            "is-hero",
        ),
    ]
)

# ------------------------ SOFTWARE DEVELOPMENT ----------------------------
# NOTE: WebsiteImprovements contains no material on this offering. Copy below is
# grounded only in the founder's stated experience areas (enterprise architecture,
# software engineering, business applications, data platforms, integrations, AI).
# It claims no clients, no metrics, and no capabilities beyond those. Review and replace.

PAGES["software-development"] = "\n\n".join(
    [
        section(
            "\n\n".join(
                [
                    eyebrow("Services", centered=True),
                    h1("Software Development"),
                    lede(
                        "Custom software engineering for organizations that need systems built, "
                        "integrated, or modernized, from the team behind Aletheon Forge.",
                        centered=True,
                    ),
                    spacer(12),
                    buttons([("Discuss a Project", DEMO, "solid"), ("Explore Aletheon Forge", "/aletheon-forge/", "ghost")]),
                ]
            ),
            "is-hero",
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("What We Build"),
                    heading("Engineering across the enterprise stack"),
                    spacer(28),
                    cards(
                        [
                            ("01", "Enterprise architecture", "System design, integration strategy, and technical direction for organizations modernizing how their software fits together."),
                            ("02", "Business applications", "Applications built around the organization's processes, requirements, and people."),
                            ("03", "Data platforms", "Data foundations, pipelines, and models that make enterprise information usable."),
                            ("04", "Integrations", "Connecting systems, services, and data so information can move between them."),
                            ("05", "Applied AI", "AI capabilities designed around the task, with attention to context, review, and human oversight."),
                            ("06", "Modernization", "Updating existing software with attention to the business logic and operational needs it already supports."),
                        ],
                        cols=3,
                    ),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("How We Work"),
                    heading("Make decisions clear and the work reviewable"),
                    lede(
                        "Our approach starts with your requirements, system constraints, and intended outcome. "
                        "We use that context to guide architecture, implementation, review, and verification."
                    ),
                    spacer(24),
                    checklist(
                        [
                            "Capture requirements and architecture decisions",
                            "Use AI-assisted engineering under human oversight",
                            "Apply the codebase's engineering standards",
                            "Review implementation against the requirements",
                            "Consider security and access in the design",
                            "Document useful knowledge for future work",
                        ]
                    ),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    heading("Tell us what you need built", centered=True),
                    lede(
                        "Share the problem, the systems involved, and the outcome you need. "
                        "We will discuss the engineering work and the right starting point.",
                        centered=True,
                    ),
                    spacer(12),
                    buttons([("Discuss a Project", DEMO, "solid"), ("Request a Forge Demo", DEMO, "ghost")]),
                ]
            ),
            "is-hero",
        ),
    ]
)

# ------------------------------- CONTACT ----------------------------------

PAGES["contact"] = "\n\n".join(
    [
        section(
            "\n\n".join(
                [
                    eyebrow("Contact", centered=True),
                    h1("See Forge or Discuss a Software Project"),
                    lede(
                        "Explore Aletheon Forge for your AI-assisted coding workflow, or talk with us "
                        "about custom software development.",
                        centered=True,
                    ),
                    spacer(12),
                    buttons(
                        [
                            ("Request a Forge Demo", "mailto:contact@aletheonlabs.com?subject=Forge%20demo", "solid"),
                            ("Discuss a Project", "mailto:contact@aletheonlabs.com?subject=Software%20development%20project", "ghost"),
                        ]
                    ),
                ]
            ),
            "is-hero",
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("How We Can Help"),
                    heading("Reach out based on what you need"),
                    spacer(28),
                    cards(
                        [
                            ("01", "Aletheon Forge Demo", "See how Forge organizes products, repositories, missions, and runs with installed AI coding assistants."),
                            ("02", "Custom Software Development", "Discuss an application, data platform, integration, applied AI capability, or modernization project."),
                            ("03", "Engineering Workflow", "Talk through repository context, skills, approvals, verification, and retained learning in your AI-assisted coding process."),
                            ("04", "Research Collaboration", "Explore academic collaboration or discuss the research informing Aletheon's approach to AI systems and software engineering."),
                        ],
                        cols=2,
                    ),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("What Happens Next"),
                    heading("Three steps"),
                    spacer(28),
                    cards(
                        [
                            ("Step 01", "Share your goals", "Tell us about your engineering workflow or the software you need built."),
                            ("Step 02", "Discuss the fit", "We review the systems involved and discuss a Forge demonstration or custom engineering engagement."),
                            ("Step 03", "Define the next step", "We agree on the scope and information needed to move the conversation forward."),
                        ],
                        cols=3,
                    ),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    heading("Start the conversation", centered=True),
                    lede("Email us with your goals and the systems or workflow involved.", centered=True),
                    spacer(12),
                    buttons([("Email contact@aletheonlabs.com", "mailto:contact@aletheonlabs.com", "solid")]),
                ]
            ),
            "is-hero",
        ),
    ]
)


# --------------------------------------------------------------------------

def validate_blocks(slug, markup):
    """Reject mismatched block tags and invalid attributes before writing pages."""
    stack = []
    for match in re.finditer(r"<!--\s+(/?)wp:([a-z0-9/-]+)(.*?)-->", markup, re.S):
        closing, name, attrs = match.groups()
        attrs = attrs.strip()
        if closing:
            if not stack or stack[-1] != name:
                raise ValueError(f"{slug}: unexpected closing block {name}")
            stack.pop()
            continue
        self_closing = attrs.endswith("/")
        if self_closing:
            attrs = attrs[:-1].strip()
        if attrs:
            json.loads(attrs)
        if not self_closing:
            stack.append(name)
    if stack:
        raise ValueError(f"{slug}: unclosed blocks {stack}")


def main():
    # Validate every page first so a failure cannot partially replace the site.
    for slug, markup in PAGES.items():
        validate_blocks(slug, markup)
    os.makedirs(OUT, exist_ok=True)
    for slug, markup in PAGES.items():
        path = os.path.join(OUT, f"{slug}.html")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(markup + "\n")
        print(f"OK  {slug:24s} {len(markup.encode('utf-8')):6d} bytes")


if __name__ == "__main__":
    main()
