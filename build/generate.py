#!/usr/bin/env python3
"""
Generate WordPress block markup for every aletheonlabs.com page.

Current offerings are Aletheon Forge and Software Development. The Business
Intelligence IP was sold and is no longer offered by Aletheon Labs. Forge copy
is grounded in its current user guides and implementation, reviewed 2026-10-09
at AletheonForge commit a13e24f4294d1a9ea6cbbf73fea4216ad8bdf908.
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
        'AI engineering under human direction</div>'
        '<p class="ale-eyebrow">Aletheon Labs &middot; Software Engineering</p>'
        '<h1 class="ale-display">Run AI Coding Agents '
        '<span class="ale-grad">Like an Engineering Team</span></h1>'
        '<p class="ale-lede">Aletheon Forge gives your AI coding assistants a clear mission, '
        'the right project knowledge, and a review process your team controls. When you need '
        'a system built, our engineers design, integrate, and modernize it with you.</p>'
        '<div class="ale-hero-actions">'
        '<a class="ale-hero-btn is-primary" href="/aletheon-forge/">Explore Aletheon Forge '
        '<span aria-hidden="true">&rarr;</span></a>'
        '<a class="ale-hero-btn is-secondary" href="/software-development/">Software Development</a>'
        '</div>'
        '<div class="ale-hero-proof" aria-label="Platform qualities">'
        '<span>Focused context</span><span>Human review gates</span><span>Acceptance evidence</span>'
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
        '<h1 class="ale-display">Designing the systems '
        '<span class="ale-grad">that make AI work trustworthy.</span></h1>'
        '<p class="ale-lede">Our research starts from one position: dependable AI work takes '
        'more than an accurate model. Context, memory, governance, and review have to be '
        'designed into the system around it.</p>'
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
            "Designing systems that stay coherent as they grow&mdash;the same challenge AI-assisted engineering faces as it spreads across teams.",
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
            "Published work in the field that predates and informs Aletheon&rsquo;s approach.",
        ),
        (
            "06",
            "Research",
            "Doctoral research, Purdue",
            "Doctoral research initiated at Purdue, the source of the design principles behind Aletheon&rsquo;s tools.",
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
        'former Microsoft engineer, software architect, and published author whose doctoral '
        'research, initiated at Purdue, underpins Aletheon&rsquo;s approach to AI engineering.</p>'
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
        '<p class="ale-lede">Context, memory, traceability, and review are not features a model '
        'ships with. A system has to be designed to provide them. That is why Aletheon is built '
        'by people with backgrounds in distributed systems and enterprise architecture&mdash;and '
        'why the research came before the product.</p>'
        '</div>'
        '<div class="ale-thesis-path" role="list" aria-label="Path from intent to accountable delivery">'
        '<div role="listitem"><span>01</span><b>Intent</b><small>Defined mission</small></div>'
        '<i aria-hidden="true">&rarr;</i>'
        '<div role="listitem"><span>02</span><b>Context</b><small>Skills, memory, code</small></div>'
        '<i aria-hidden="true">&rarr;</i>'
        '<div role="listitem"><span>03</span><b>Review</b><small>Human decisions</small></div>'
        '<i aria-hidden="true">&rarr;</i>'
        '<div role="listitem"><span>04</span><b>Evidence</b><small>Checked result</small></div>'
        '</div>'
        '</div>'
    )


def forge_hero():
    return raw(
        '<div class="ale-forge-wrap">'
        '<div class="ale-forge-hero">'
        '<div class="ale-forge-hero__copy">'
        '<div class="ale-forge-brand"><img src="/wp-content/mu-plugins/aletheon/forge-mark.png" '
        'width="72" height="76" alt="" decoding="async"><span>Aletheon Forge</span></div>'
        '<p class="ale-forge-kicker">Engineering intelligence &amp; orchestration</p>'
        '<h1 class="ale-forge-title">Give your AI agents '
        '<span class="ale-grad">an engineering organization.</span></h1>'
        '<p class="ale-forge-intro">Forge turns the AI coding assistants you already use into a '
        'coordinated team. You set the objective. Forge briefs the agents, coordinates the work, '
        'and keeps the evidence you need to accept it.</p>'
        '<div class="ale-forge-actions">'
        '<a class="ale-forge-button" href="/contact/">Request a Forge demo <span aria-hidden="true">&rarr;</span></a>'
        '<a class="ale-forge-button is-secondary" href="#forge-workflow">See how it works</a></div>'
        '<p class="ale-forge-platform">Runs locally on Windows with the coding tools your team already has.</p>'
        '</div>'
        '<figure class="ale-forge-console" aria-labelledby="forge-console-title">'
        '<div class="ale-forge-console__header"><span id="forge-console-title">Mission control</span>'
        '<span class="ale-forge-caption">Illustrative workflow</span></div>'
        '<div class="ale-forge-console__brief"><small>Start with an outcome</small>'
        '<strong>Add appointment rescheduling</strong>'
        '<p>Keep availability accurate. Preserve confirmation. Define the checks before work starts.</p></div>'
        '<div class="ale-forge-context-line" aria-label="Engineering work structure">'
        '<span>Product</span><span>Repository</span><span>Mission</span><span>Run</span></div>'
        '<div class="ale-forge-captain"><small>Coordination</small><strong>The Captain</strong>'
        '<p>Assign the work. Make the stages and exit gates visible.</p></div>'
        '<div class="ale-forge-workers">'
        '<div><span>01 / Build</span><strong>Implement</strong></div>'
        '<div><span>02 / Inspect</span><strong>Review</strong></div>'
        '<div><span>03 / Check</span><strong>Verify</strong></div></div>'
        '<figcaption class="ale-forge-console__footer">'
        'Requirements <span aria-hidden="true">&rarr;</span> Context '
        '<span aria-hidden="true">&rarr;</span> Evidence '
        '<span aria-hidden="true">&rarr;</span> Reusable knowledge</figcaption></figure>'
        '</div>'
        '<div class="ale-forge-integrations"><div><p class="ale-forge-kicker">Your tools. A shared workflow.</p>'
        '<p>Bring the coding assistants you have installed.</p></div>'
        '<div class="ale-forge-provider-list" aria-label="Supported coding tool integrations">'
        '<span>Claude Code</span><span>Codex</span><span>Gemini CLI</span><span>Grok</span><span>GitHub Copilot</span>'
        '</div></div></div>'
    )


FORGE_VIDEOS = [
    ("forge-demo", "Forge Demo", "7:18",
     "Follow one mission from start to finish: define the product and requirements, watch "
     "agents build a CSV invoice import, explore the knowledge map, and review the evidence."),
    ("forge-ai-enabler-deep-dive", "AI Enabler Deep Dive", "5:41",
     "A closer look at how skills, approved memory, and context routing come together in "
     "each agent's briefing, and how to measure whether it makes the work more efficient."),
]


def forge_demo():
    figures = ''.join(
        f'<figure class="ale-forge-demo">'
        f'<video controls playsinline preload="metadata" aria-labelledby="{slug}-title">'
        f'<source src="/wp-content/uploads/2026/10/{slug}.mp4" type="video/mp4">'
        f'<a href="/wp-content/uploads/2026/10/{slug}.mp4">Watch {esc(title)}</a></video>'
        f'<figcaption><h3 id="{slug}-title">{esc(title)}</h3><p>{esc(body)}</p>'
        f'<span class="ale-forge-caption">{length} &middot; '
        f'<a href="/wp-content/uploads/2026/10/{slug}.mp4">Open video</a></span>'
        f'</figcaption></figure>'
        for slug, title, length, body in FORGE_VIDEOS
    )
    return raw(
        '<div class="ale-forge-wrap" id="forge-demo">'
        '<div class="ale-forge-section-head"><p class="ale-forge-kicker">Forge in action</p>'
        '<h2 class="ale-forge-heading">Watch a mission come together.</h2>'
        '<p class="ale-forge-description">Both walkthroughs follow LedgerLite, a sample invoice app. '
        'Start with the full mission, then go deeper into how Forge briefs each agent.</p></div>'
        f'<div class="ale-forge-videos">{figures}</div></div>'
    )


def forge_outcomes():
    return raw(
        '<div class="ale-forge-wrap">'
        '<div class="ale-forge-section-head"><p class="ale-forge-kicker">Built for developers and engineering leads</p>'
        '<h2 class="ale-forge-heading">From a stated goal to changes you can review.</h2>'
        '<p class="ale-forge-description">Forge keeps the plan, the methods, the decisions, and '
        'the lessons attached to the work, where the whole team can find them.</p></div>'
        '<div class="ale-forge-outcomes">'
        '<article><span class="ale-forge-case-number">01 / Direction</span><h3>A clear definition of done</h3>'
        '<p>Turn a product goal into scoped missions, with acceptance criteria agreed before any agent starts.</p></article>'
        '<article><span class="ale-forge-case-number">02 / Continuity</span><h3>A shared engineering brain</h3>'
        '<p>Every agent gets the skills, repository knowledge, and approved memories that apply to its task.</p></article>'
        '<article><span class="ale-forge-case-number">03 / Evidence</span><h3>Work you can inspect</h3>'
        '<p>See the questions asked, decisions made, code changed, and checks run before you decide what is ready.</p></article>'
        '</div></div>'
    )


def forge_workflow():
    steps = [
        ("01", "Define the outcome", "Describe what should change and what acceptance requires. "
         "Draft requirements with AI-assisted planning, or derive them from your reference documents.", "You choose the scope and criteria."),
        ("02", "Brief the agents", "Forge assembles a focused briefing from repository instructions, "
         "relevant skills, and approved knowledge for the product or repository.", "The briefing is recorded with the run."),
        ("03", "Coordinate the work", "Run visible stages with exit gates in Captain, or let Autopilot "
         "coordinate implementation, verification, and fixes for review findings.", "Agent questions and approval requests stay in view."),
        ("04", "Review, deliver, learn", "Inspect the changes and acceptance evidence, prepare a pull request, "
         "and assess lessons that can inform the next mission.", "Human decisions and evidence stay with the work."),
    ]
    items = ''.join(
        f'<li><span class="ale-forge-step-number">{number}</span><h3>{esc(title)}</h3>'
        f'<p>{esc(body)}</p><span class="ale-forge-step-detail">{esc(detail)}</span></li>'
        for number, title, body, detail in steps
    )
    return raw(
        '<div class="ale-forge-wrap" id="forge-workflow">'
        '<div class="ale-forge-section-head"><p class="ale-forge-kicker">From intent to delivery</p>'
        '<h2 class="ale-forge-heading">One mission. A connected workflow.</h2>'
        '<p class="ale-forge-description">Set the goal, brief the agents, coordinate the work, '
        'and review the result, with every step tied to the outcome you asked for.</p></div>'
        f'<ol class="ale-forge-workflow" role="list">{items}</ol>'
        '<p class="ale-forge-brain-caption">Captain stages: Discovery &rarr; Architecture &rarr; Context '
        '&rarr; Implementation &rarr; Validation &rarr; Governance &rarr; Learning &rarr; Delivery.</p>'
        '</div>'
    )


def forge_brain():
    return raw(
        '<div class="ale-forge-wrap ale-forge-brain" id="forge-knowledge">'
        '<div><p class="ale-forge-kicker">One Brain</p>'
        '<h2 class="ale-forge-heading">Give the next agent the benefit of the last mission.</h2>'
        '<p class="ale-forge-description">Your team&rsquo;s knowledge should outlast any single session. '
        'Forge keeps methods, approved experience, repository context, and recorded decisions with the '
        'product, and its context router picks what each run needs, whichever coding tool does the work.</p>'
        '<div class="ale-forge-knowledge-list">'
        '<article><h3>Skills provide the method</h3><p>Start with Forge&rsquo;s shipped engineering skills or write your own, '
        'so every agent plans, builds, reviews, and tests the same way.</p></article>'
        '<article><h3>Memory carries experience</h3><p>AI assesses proposed lessons and approves eligible ones automatically. '
        'Anything that needs attention waits for review with its sources and reasoning.</p></article>'
        '<article><h3>Grounding connects the code</h3><p>Repository instructions and relevant code excerpts '
        'keep each briefing tied to the system being changed.</p></article>'
        '</div></div>'
        '<figure class="ale-forge-brain-map" aria-labelledby="forge-brain-title">'
        '<div class="ale-forge-brain-core"><span>Shared engineering knowledge</span><strong id="forge-brain-title">One Brain</strong></div>'
        '<div class="ale-forge-brain-node"><strong>Skills</strong><p>Methods &amp; guidance</p></div>'
        '<div class="ale-forge-brain-node"><strong>Memory</strong><p>Approved experience</p></div>'
        '<div class="ale-forge-brain-node"><strong>Repository</strong><p>Code &amp; context</p></div>'
        '<div class="ale-forge-brain-node"><strong>Decisions</strong><p>Reasoning &amp; sources</p></div>'
        '<figcaption class="ale-forge-brain-caption">Explore the connections in a 2D or 3D knowledge map. '
        'Select any node to see its sources, related work, and history.</figcaption></figure>'
        '</div>'
    )


def forge_evidence():
    return raw(
        '<div class="ale-forge-wrap ale-forge-evidence" id="forge-verification">'
        '<div class="ale-forge-evidence-copy"><p class="ale-forge-kicker">Verification &amp; evaluation</p>'
        '<h2 class="ale-forge-heading">See what was checked. Decide what is ready.</h2>'
        '<p class="ale-forge-description">Verification results stay attached to the work, with the '
        'records behind them. Independent acceptance checks are approved before the run and executed '
        'against a captured copy of the source, so each result shows exactly what was tested.</p>'
        '<ul class="ale-forge-evidence-points" role="list">'
        '<li><strong>Acceptance tied to requirements.</strong> See each check&rsquo;s definition, the source it tested, and the retained result.</li>'
        '<li><strong>Decisions on the record.</strong> Follow review findings, approvals, and any recorded exceptions.</li>'
        '<li><strong>Measure with evidence.</strong> Use Evaluation to compare recorded outcomes, available token usage, and reported human effort.</li>'
        '</ul></div>'
        '<figure class="ale-forge-receipt" aria-labelledby="forge-receipt-title">'
        '<div class="ale-forge-receipt-head"><span class="ale-forge-caption">Illustrative evidence record</span>'
        '<h3 id="forge-receipt-title">A result with its supporting record</h3></div>'
        '<div class="ale-forge-receipt-row"><span>Requirement</span><strong>The outcome being checked</strong></div>'
        '<div class="ale-forge-receipt-row"><span>Check definition</span><strong>Approved before execution</strong></div>'
        '<div class="ale-forge-receipt-row"><span>Source</span><strong>The captured checkout</strong></div>'
        '<div class="ale-forge-receipt-row"><span>Result</span><strong>Checks and evidence retained</strong></div>'
        '<figcaption class="ale-forge-receipt-note">Independent verification applies to supported checks '
        'approved for the mission before the run. Results describe the source that was tested.</figcaption>'
        '</figure></div>'
    )


def forge_use_cases():
    return raw(
        '<div class="ale-forge-wrap"><div class="ale-forge-section-head">'
        '<p class="ale-forge-kicker">Where Forge fits</p><h2 class="ale-forge-heading">Build. Improve. Carry the learning forward.</h2>'
        '<p class="ale-forge-description">For teams using AI coding tools on new products and '
        'established codebases alike.</p></div>'
        '<div class="ale-forge-usecases">'
        '<article><span class="ale-forge-case-number">01</span><h3>Plan an application or feature</h3>'
        '<p>Turn an outcome into requirements and scoped missions that agents can work from.</p>'
        '<ul role="list"><li>AI-assisted product planning</li><li>Requirements from reference documents</li><li>Mission acceptance criteria</li></ul></article>'
        '<article><span class="ale-forge-case-number">02</span><h3>Fix, refactor, and review</h3>'
        '<p>Give agents the repository context they need, and keep their changes tied to review and verification.</p>'
        '<ul role="list"><li>Skills and code grounding</li><li>Implementation and fixes</li><li>Pull requests to GitHub or Azure Repos</li></ul></article>'
        '<article><span class="ale-forge-case-number">03</span><h3>Build on what you have learned</h3>'
        '<p>Keep useful decisions and approved lessons available as people, agents, and tasks change.</p>'
        '<ul role="list"><li>Scoped and versioned memories</li><li>Connected engineering knowledge</li><li>Evidence-backed evaluation</li></ul></article>'
        '</div></div>'
    )


def forge_faq():
    answers = [
        ("Who is Forge built for?", "Developers, engineering leads, and architects who use AI coding tools "
         "and want planning, shared context, execution, review, and retained knowledge in one workflow."),
        ("Which coding tools can I connect?", "Forge has adapters for Claude Code, Codex, Gemini CLI, Grok, "
         "and GitHub Copilot. Install and sign in to the tools you plan to use; each needs its own "
         "provider access. Supported approvals, features, and telemetry vary by tool."),
        ("How do Captain and Autopilot differ?", "Captain organizes worker assignments into visible delivery "
         "stages with exit gates. Autopilot coordinates a mission's implementation, verification, and fixes "
         "for review findings. Both keep the mission's requirements and review decisions in view."),
        ("What is One Brain?", "Forge's shared engineering knowledge. Skills provide methods, approved "
         "memories carry experience, repository grounding supplies code context, and the knowledge map "
         "shows how they connect. The context router selects relevant guidance for each run, and with "
         "knowledge on demand enabled, a compatible agent can ask Forge for more guidance as it works."),
        ("What does independent acceptance verify?", "It runs eligible checks, approved before the run, "
         "against a captured copy of the source, and keeps their definitions and results. Checks written "
         "by agents are kept distinct from independent checks, and a recorded exception or forced completion "
         "is tracked separately from verified acceptance."),
        ("Can Forge reduce AI usage costs?", "Forge selects context locally, so preparing a briefing needs no "
         "extra model call, and a focused briefing sends less input than full documents. Whether that lowers "
         "your bill depends on your provider and plan. To find out, compare the same task with the same "
         "success criteria using recorded usage and billing, including retries."),
        ("Where does Forge run?", "Forge is a local-first Windows application. Connected coding tools "
         "use their own provider services. Contact us to talk through setup, prerequisites, and a demonstration built around your workflow."),
    ]
    details = ''.join(
        f'<details><summary>{esc(question)}</summary><p>{esc(answer)}</p></details>'
        for question, answer in answers
    )
    return raw(
        '<div class="ale-forge-wrap"><div class="ale-forge-section-head">'
        '<p class="ale-forge-kicker">A few practical questions</p>'
        '<h2 class="ale-forge-heading">Start with the workflow you have.</h2></div>'
        f'<div class="ale-forge-faq">{details}</div></div>'
    )


def forge_final():
    return raw(
        '<div class="ale-forge-wrap ale-forge-final"><p class="ale-forge-kicker">Bring your engineering goals</p>'
        '<h2 class="ale-forge-heading">See how your team could work with Forge.</h2>'
        '<p class="ale-forge-description">Tell us about your repositories, coding tools, and review process, '
        'and we will walk you through a Forge workflow that matches how your team works.</p>'
        '<div class="ale-forge-actions"><a class="ale-forge-button" href="/contact/">Request a Forge demo '
        '<span aria-hidden="true">&rarr;</span></a>'
        '<a class="ale-forge-button is-secondary" href="/software-development/">Discuss custom development</a></div>'
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
    '<p>A local-first Windows application that turns AI coding assistants into a coordinated '
    'engineering team. Plan missions, brief agents with shared project knowledge, coordinate '
    'the work with Captain or Autopilot, and review the evidence before you accept it.</p>'
    '<p style="margin-top:1.1rem"><a class="ale-btn" href="/aletheon-forge/">Explore Forge</a></p></div>'
    '<div class="ale-card is-platform"><span class="ale-card-num">Services</span>'
    '<h3 class="ale-h3">Software Development</h3>'
    '<p>Custom engineering for systems you need built, connected, or modernized, '
    'from enterprise architecture and business applications to data platforms, '
    'integrations, and applied AI.</p>'
    '<p style="margin-top:1.1rem"><a class="ale-btn" href="/software-development/">Explore Software Development</a></p></div>'
    '</div>'
)

# ------------------------------ HOME --------------------------------------

PAGES["home"] = "\n\n".join([
    section(home_hero(), "is-home-hero"),
    section("\n\n".join([
        eyebrow("Who We Are"),
        heading("A product for AI-assisted engineering, and a team to build with you"),
        lede("Aletheon Labs makes Aletheon Forge, which helps developers and engineering "
             "leads direct AI coding agents through planned, reviewable work. Our Software "
             "Development team designs and builds applications, integrations, and modernized "
             "systems for organizations."),
    ]), "is-home-intro"),
    section("\n\n".join([
        eyebrow("The Engineering Challenge"),
        heading("AI agents write code quickly. Good engineering still needs structure."),
        lede("Coding assistants do their best work with a clear task, the right project "
             "knowledge, and someone reviewing the result. That structure has to hold up "
             "across every agent, every repository, and every person directing the work."),
        spacer(28),
        cards([
            ("01", "Defined missions", "State what should change, the constraints, and the evidence needed to accept it."),
            ("02", "Repository context", "Brief each agent on the codebase and instructions that apply to its task."),
            ("03", "Shared skills", "Give every agent the same proven methods for planning, building, reviewing, and testing."),
            ("04", "Retained decisions", "Keep architecture choices and lessons available for the next mission."),
            ("05", "Human review", "Keep agent questions, approvals, and review findings visible as the work progresses."),
            ("06", "Reviewable delivery", "Inspect checks and acceptance evidence, then prepare a pull request for your usual review."),
        ], variant="is-problem", cols=3),
    ]), "is-home-problem"),
    section("\n\n".join([
        eyebrow("The Forge Workflow", centered=True),
        heading("One workflow from your team to your AI tools", centered=True),
        lede("Your team sets direction and reviews results. Forge supplies the context, "
             "memory, skills, and checks. The coding assistants you already use do the "
             "implementation.", centered=True),
        spacer(40), diagram(),
    ]), "is-home-layer"),
    section("\n\n".join([
        eyebrow("What We Offer"),
        heading("Two ways to move your software work forward"),
        lede("Use Aletheon Forge to direct AI-assisted engineering in your own repositories, "
             "or bring in our team to build the system with you."),
        spacer(28), raw(OFFERINGS_GRID),
    ]), "is-home-platforms"),
    section("\n\n".join([
        eyebrow("One Brain"),
        heading("Every agent starts with what your team already knows"),
        lede("Forge's One Brain brings together repository instructions, shipped and "
             "team-written skills, approved memories, and recorded decisions. Each run "
             "starts with a focused briefing, and the knowledge map shows where the "
             "guidance came from."),
        spacer(28),
        roles([
            ("Product lead", "Defines the outcome and the scope of the work."),
            ("Engineering lead", "Sets technical direction and decides what is ready."),
            ("Developer", "Works alongside agents on code, changes, and checks."),
            ("Architect", "Keeps the work aligned with system design and recorded decisions."),
        ]),
    ]), "is-home-roles"),
    section("\n\n".join([
        eyebrow("Human Direction"),
        heading("Decide what ships with the evidence in front of you"),
        lede("Mission history, agent questions, approval decisions, and verification "
             "results stay together, so reviewers can see what was asked, what changed, "
             "and what was checked."),
        spacer(24), checklist([
            "Mission scope and acceptance criteria", "Agent run history",
            "Questions and approval decisions", "Checks and acceptance evidence",
            "Source changes and pull request preparation", "Assessed memories and lessons learned",
        ]),
    ]), "is-home-governance"),
    section("\n\n".join([
        eyebrow("Engineering Outcomes"), heading("What changes for your team"),
        spacer(28), stats([
            ("Context", "Agents begin with the instructions, skills, and knowledge that apply to the task."),
            ("Continuity", "Decisions and lessons carry forward to the next mission."),
            ("Coordination", "Products, repositories, missions, and runs stay connected."),
            ("Review", "People make the approval and acceptance decisions, with evidence in view."),
            ("Delivery", "Changes flow into your existing source control and review practices."),
            ("Engineering", "Our team can build the custom applications and integrations you need."),
        ]),
    ]), "is-home-outcomes"),
    section(mission_block(), "is-tight is-home-mission"),
    section("\n\n".join([
        eyebrow("Founder"), heading("Grounded in research, built from practice"),
        lede("Aletheon Labs was founded by Dr. Andrew Ganje, a former Microsoft engineer, "
             "software architect, and published author whose doctoral research was "
             "initiated at Purdue."),
        para("The founder's experience spans business transformations at organizations "
             "from $100 billion enterprises to mid-cap companies, across enterprise "
             "architecture, business applications, data platforms, integrations, and AI.",
             cls="ale-muted"),
        spacer(20), buttons([("Read the Research", "/research/", "ghost")], centered=False),
    ]), "is-home-research"),
    section("\n\n".join([
        heading("See Forge in action, or tell us what to build", centered=True),
        lede("Book a Forge demo for your engineering team, or tell us about a system you "
             "need built, integrated, or modernized.", centered=True),
        spacer(12), buttons([
            ("Request a Forge Demo", "/contact/", "solid"),
            ("Discuss a Project", "/contact/", "ghost"),
        ]),
    ]), "is-hero is-home-cta"),
])

# ------------------------ ALETHEON INTELLIGENCE ---------------------------


# --------------------------- ALETHEON FORGE -------------------------------

PAGES["aletheon-forge"] = "\n\n".join([
    section(forge_hero(), "ale-forge-section is-forge-hero"),
    section(forge_demo(), "ale-forge-section is-forge-section"),
    section(forge_outcomes(), "ale-forge-section is-forge-section"),
    section(forge_workflow(), "ale-forge-section is-forge-section"),
    section(forge_brain(), "ale-forge-section is-forge-section"),
    section(forge_evidence(), "ale-forge-section is-forge-section"),
    section(forge_use_cases(), "ale-forge-section is-forge-section"),
    section(forge_faq(), "ale-forge-section is-forge-section"),
    section(forge_final(), "ale-forge-section is-forge-final"),
])

# ---------------------------- GOVERNED AI ---------------------------------

PAGES["governed-ai"] = "\n\n".join([
    section("\n\n".join([
        eyebrow("Engineering Principles", centered=True), h1("Governed AI Engineering"),
        lede("Clear scope, relevant context, human review, and verification evidence. "
             "These four principles shape Aletheon Forge and the custom systems our "
             "Software Development team builds.", centered=True),
    ]), "is-hero"),
    section("\n\n".join([diagram()]), "is-tight"),
    section("\n\n".join([
        eyebrow("In the Workflow"), heading("Where the principles show up in Forge"),
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
            ("01", "Clear intent", "Agree on what needs to change, the constraints, and what acceptance requires before an agent starts work."),
            ("02", "Relevant context", "Brief agents with repository instructions, focused skills, and the knowledge that applies to the task."),
            ("03", "Human decisions", "Make questions, approvals, and technical review part of the workflow."),
            ("04", "Evidence", "Weigh checks, acceptance results, and source changes before deciding the work is ready."),
        ], cols=2),
    ])),
    section("\n\n".join([
        eyebrow("Engineering Memory"), heading("Keep what your team learns"),
        lede("Forge assesses proposed lessons before they are reused. Skills, approved "
             "memories, and repository context then inform later missions, and the "
             "knowledge map shows how they connect."),
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
                    heading("Accuracy is only the starting point"),
                    lede(
                        "Dependable AI work also needs trusted sources, governance, explainability, "
                        "organizational context, and memory. These belong to the system around the model, "
                        "so Aletheon designs them into its tools from the start."
                    ),
                    spacer(28),
                    cards(
                        [
                            ("Area 01", "Trusted information", "What has to be true about a source, and about the path from source to result, before a person should rely on it."),
                            ("Area 02", "Organizational context", "How repository instructions, architectural decisions, and project requirements shape engineering work."),
                            ("Area 03", "Governed memory", "How systems carry lessons forward across tasks while keeping each one scoped, versioned, and traceable to its source."),
                            ("Area 04", "Explainability in practice", "What traceability has to look like for the person accepting the work: what was asked, what was used, and what was checked."),
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
                        "For research collaboration, academic partnership, or a technical discussion of "
                        "the ideas behind Aletheon's tools.",
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
                        "Direct AI coding agents with Aletheon Forge, or bring in our engineers to build, "
                        "integrate, and modernize the software your organization depends on.",
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
                    heading("What teams bring to Aletheon"),
                    spacer(28),
                    cards(
                        [
                            ("01", "Coordinate coding work", "Use Forge's Captain stages or Autopilot to tie implementation, review, and verification to a defined mission."),
                            ("02", "Brief agents with your knowledge", "Use One Brain to give coding agents the relevant skills, approved memories, and repository knowledge."),
                            ("03", "Review changes and results", "See review decisions, checks, and acceptance evidence alongside the source changes."),
                            ("04", "Keep what the team learns", "Capture useful lessons and approved memories so future missions build on them."),
                            ("05", "Build business software", "Develop applications and data platforms around your requirements, existing systems, and day-to-day operations."),
                            ("06", "Integrate and modernize", "Connect services and data, plan architecture changes, and update existing software without losing its business logic."),
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
                        "Choose Forge when your team wants to work with AI coding assistants in a structured, "
                        "reviewable way. Choose Software Development when you want our engineers to design and build the system."
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
                        "Aletheon Labs builds Aletheon Forge, a Windows application for directing AI coding "
                        "agents, and delivers custom software development for organizations.",
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
                        "Forge gives the AI coding assistants your team already uses a shared plan, shared "
                        "knowledge, and a review process. Our Software Development practice brings enterprise "
                        "architecture and engineering experience to custom applications, data platforms, "
                        "integrations, applied AI, and modernization."
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
                        "Aletheon Labs was founded by Dr. Andrew Ganje, a former Microsoft engineer, "
                        "software architect, microservice specialist, and published author whose doctoral "
                        "research was initiated at Purdue."
                    ),
                    para(
                        "That background spans business transformations at organizations from $100 billion "
                        "enterprises to mid-cap companies, along with enterprise architecture, microservice "
                        "design, business applications, data platforms, integrations, and artificial intelligence.",
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
                    heading("Talk With Us About What You're Building", centered=True),
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
                        "Custom software for organizations that need systems built, connected, or "
                        "modernized, delivered by the team behind Aletheon Forge.",
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
                            ("02", "Business applications", "Applications shaped around how your organization works: its processes, requirements, and people."),
                            ("03", "Data platforms", "Data foundations, pipelines, and models that turn enterprise information into something teams can use."),
                            ("04", "Integrations", "Connect systems, services, and data so information moves where it is needed."),
                            ("05", "Applied AI", "AI features designed around a real task, with the context, review, and human oversight to use them responsibly."),
                            ("06", "Modernization", "Update existing software while protecting the business logic and operations it already supports."),
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
                    heading("Clear decisions. Reviewable work."),
                    lede(
                        "Every engagement starts with your requirements, system constraints, and intended outcome. "
                        "That context guides the architecture, implementation, review, and verification."
                    ),
                    spacer(24),
                    checklist(
                        [
                            "Capture requirements and architecture decisions",
                            "Use AI-assisted engineering under human oversight",
                            "Follow your codebase's engineering standards",
                            "Review the implementation against the requirements",
                            "Design for security and access from the start",
                            "Document what the next team will need to know",
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
                        "Share the problem, the systems involved, and the outcome you need, "
                        "and we will help you find the right starting point.",
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
                        "See how Aletheon Forge fits your AI-assisted coding workflow, or talk with us "
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
                    heading("Tell us what you need"),
                    spacer(28),
                    cards(
                        [
                            ("01", "Aletheon Forge Demo", "See Captain, Autopilot, One Brain, and verification evidence applied to your team's coding workflow."),
                            ("02", "Custom Software Development", "Discuss an application, data platform, integration, applied AI feature, or modernization project."),
                            ("03", "Engineering Workflow", "Talk through how your team handles context, skills, approvals, verification, and lessons learned when coding with AI."),
                            ("04", "Research Collaboration", "Explore academic collaboration or the research behind Aletheon's approach to AI systems and software engineering."),
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
                    heading("Three steps to get started"),
                    spacer(28),
                    cards(
                        [
                            ("Step 01", "Share your goals", "Tell us about your engineering workflow or the software you need built."),
                            ("Step 02", "Discuss the fit", "We look at the systems involved and recommend a Forge demo or a custom engineering engagement."),
                            ("Step 03", "Agree on next steps", "Together we settle the scope and what is needed to move forward."),
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
                    lede("Email us your goals and the systems or workflow involved. We will take it from there.", centered=True),
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
