#!/usr/bin/env python3
"""
Generate WordPress block markup for every aletheonlabs.com page.

Copy is drawn from WebsiteImprovements, narrowed to what the company sells now:
Aletheon Forge and software development. The Aletheon Intelligence platform was
sold in 2026 and no longer appears anywhere on the site.

Nothing here invents customers, testimonials, metrics, or capabilities.

Run:  python generate.py     ->  writes build/pages/*.html
"""

import html
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


def tags(label, items):
    """A labelled row of pills — used for stack and provider compatibility."""
    pills = "".join(f'<span class="ale-tag">{esc(i)}</span>' for i in items)
    return raw(
        f'<div class="ale-tags"><b>{esc(label)}</b>'
        f'<div class="ale-tag-row">{pills}</div></div>'
    )


# The request path. The engineering variant is what Forge governs; the generic
# variant is the architecture as described on the Governed AI page.
FLOW_ENGINEERING = ["Identity", "Context", "Memory", "Standards", "Agent", "Review", "Merge"]
FLOW_GENERIC = ["Identity", "Context", "Memory", "Knowledge", "AI", "Governance", "Action"]


def flow(steps=None, label="How work flows through the governed layer"):
    steps = steps or FLOW_GENERIC
    out = [f'<div class="ale-flow" role="list" aria-label="{esc(label)}">']
    for i, s in enumerate(steps):
        out.append(
            f'<div class="ale-flow-step" role="listitem" style="--i:{i}"><span>{esc(s)}</span></div>'
        )
    out.append("</div>")
    return raw("".join(out))


def feature(kicker, title, body, side_label, side_items, cta=None):
    """The platform spotlight: copy on the left, what is inside on the right."""
    lis = "".join(f"<li>{esc(i)}</li>" for i in side_items)
    paras = "".join(f"<p>{esc(p)}</p>" for p in body)
    btn = (
        f'<p class="ale-feature-cta">'
        f'<a class="ale-btn" href="{cta[1]}">{esc(cta[0])}</a></p>'
        if cta
        else ""
    )
    return raw(
        '<div class="ale-feature">'
        f'<div class="ale-feature-main"><span class="ale-card-num">{esc(kicker)}</span>'
        f'<h3 class="ale-h3">{esc(title)}</h3>{paras}{btn}</div>'
        f'<div class="ale-feature-side"><b>{esc(side_label)}</b>'
        f'<ul class="ale-list">{lis}</ul></div>'
        "</div>"
    )


def mission_block():
    return raw(
        '<div class="ale-mission">'
        '<p class="ale-eyebrow is-centered">Our Mission</p>'
        "<blockquote>Aletheon Labs exists to make enterprise AI trustworthy. "
        "We build the governed AI layer that ensures every AI interaction is "
        "secure, explainable, consistent, and relevant to the person using it.</blockquote>"
        "</div>"
    )


# --------------------------------------------------------------------------
# the signature asset: the governed AI layer
# --------------------------------------------------------------------------

TOP_NODES = [
    "Engineers",
    "Tech Leads",
    "Architects",
    "Product Owners",
    "Source Control",
    "Aletheon Forge",
]
BOTTOM_NODES = [
    "OpenAI",
    "Anthropic",
    "Google",
    "Microsoft",
    "Local Models",
    "Approved Models",
]
LAYER_CHIPS = ["Identity", "Context", "Memory", "Knowledge", "Policy", "Audit", "Evaluation"]

DIAGRAM_W = 940
BAND_X = 18
BAND_W = DIAGRAM_W - (BAND_X * 2)


def _row(labels, x0=BAND_X, width=BAND_W, fixed_w=None, min_gap=16):
    """
    Distribute labelled nodes evenly across a band, returning (label, x, w).

    Widths are derived from label length so the layout survives copy changes.
    Raises if the labels cannot fit — a loud build failure beats silently
    overlapping boxes in the shipped SVG.
    """
    widths = [fixed_w or max(96, len(l) * 7.4 + 22) for l in labels]
    gaps = len(labels) - 1
    gap = (width - sum(widths)) / gaps if gaps else 0
    if gap < min_gap:
        raise ValueError(
            f"diagram row does not fit: {labels!r} needs {sum(widths):.0f}px of "
            f"{width}px, leaving {gap:.1f}px gaps (minimum {min_gap})"
        )
    out, x = [], float(x0)
    for label, w in zip(labels, widths):
        out.append((label, x, w))
        x += w + gap
    return out


def diagram():
    top = _row(TOP_NODES)
    bottom = _row(BOTTOM_NODES)
    chips = _row(LAYER_CHIPS, x0=BAND_X + 16, width=BAND_W - 32, fixed_w=104, min_gap=10)
    mid = DIAGRAM_W / 2

    p = [
        f'<svg class="ale-diagram" viewBox="0 0 {DIAGRAM_W} 520" role="img" '
        'xmlns="http://www.w3.org/2000/svg" '
        'aria-label="The governed AI layer sits between people, engineering tools and '
        'applications above, and AI models and providers below. Every request passes '
        'through identity, context, memory, knowledge, policy, audit and evaluation '
        'before reaching a model, and every response returns through the same layer.">'
    ]

    # band labels
    p.append(
        '<text x="18" y="26" class="d-accent" font-size="11" letter-spacing="2.2">'
        "PEOPLE, TOOLS &amp; APPLICATIONS</text>"
    )
    p.append(
        '<text x="18" y="288" class="d-accent" font-size="11" letter-spacing="2.2">'
        "THE GOVERNED AI LAYER</text>"
    )
    p.append(
        '<text x="18" y="452" class="d-accent" font-size="11" letter-spacing="2.2">'
        "AI MODELS &amp; PROVIDERS</text>"
    )

    # top row
    for label, x, w in top:
        p.append(f'<rect class="d-node" x="{x:.0f}" y="44" width="{w:.0f}" height="40" rx="8"/>')
        p.append(
            f'<text x="{x + w / 2:.0f}" y="69" text-anchor="middle" font-size="12">{esc(label)}</text>'
        )

    # flows down into the layer
    for label, x, w in top:
        cx = x + w / 2
        p.append(
            f'<path class="d-flow" d="M{cx:.0f} 84 C {cx:.0f} 140, {mid:.0f} 150, {mid:.0f} 196"/>'
        )

    # the layer itself
    p.append(f'<rect class="d-layer" x="{BAND_X}" y="200" width="{BAND_W}" height="86" rx="14"/>')
    for label, x, w in chips:
        p.append(f'<rect class="d-node" x="{x:.0f}" y="222" width="{w:.0f}" height="42" rx="7"/>')
        p.append(
            f'<text x="{x + w / 2:.0f}" y="248" text-anchor="middle" font-size="11.5">{esc(label)}</text>'
        )

    # flows down to providers
    for label, x, w in bottom:
        cx = x + w / 2
        p.append(
            f'<path class="d-flow" d="M{mid:.0f} 290 C {mid:.0f} 340, {cx:.0f} 348, {cx:.0f} 400"/>'
        )

    # bottom row
    for label, x, w in bottom:
        p.append(f'<rect class="d-node" x="{x:.0f}" y="400" width="{w:.0f}" height="40" rx="8"/>')
        p.append(
            f'<text x="{x + w / 2:.0f}" y="425" text-anchor="middle" font-size="12">{esc(label)}</text>'
        )

    # travelling pulses on the spine
    for i, y in enumerate((150, 330)):
        p.append(
            f'<circle class="d-pulse" cx="{mid:.0f}" cy="{y}" r="3.4" '
            f'style="animation-delay:{i * 1.1}s"/>'
        )

    p.append("</svg>")
    return raw("".join(p))


# --------------------------------------------------------------------------
# shared copy
# --------------------------------------------------------------------------

DEMO = "/contact/"
FORGE = "/aletheon-forge/"
GOVERNED = "/governed-ai/"
DEV = "/software-development/"
RESEARCH = "/research/"

FOUNDER = (
    "Aletheon Labs was founded by Dr. Andrew Ganje, combining doctoral research initiated "
    "at Purdue with extensive experience in enterprise architecture, software engineering, "
    "business applications, data platforms, integrations, and artificial intelligence."
)

PERSONALIZATION_NOTE = (
    "Personalization operates inside your security model. Every AI interaction stays "
    "subject to permissions, governance, and organizational policy."
)

ENGINEERING_ROLES = [
    ("Engineering Leader", "Delivery, risk, and where the work actually stands."),
    ("Enterprise Architect", "Systems, integration, and structural implication."),
    ("Tech Lead", "Scope, sequencing, and review of agent work."),
    ("Software Engineer", "Repositories, standards, context, and the work itself."),
    ("Platform Engineer", "Pipelines, environments, and operational guardrails."),
    ("Security and Compliance", "Policy, data boundaries, and audit history."),
]

FORGE_INSIDE = [
    "Agent coordination",
    "Engineering memory",
    "Context routing",
    "Coding and architecture standards",
    "Human technical oversight",
    "Agent evaluation",
]

BUILD_CARDS = [
    ("01", "AI applications", "Production software with AI designed into the architecture — identity, context, and policy in place from the first commit."),
    ("02", "Agent systems", "Multi-agent workflows with context routing, memory, standards, and human approval where it matters."),
    ("03", "Enterprise integration", "Connecting business applications, services, and systems so AI has something trustworthy to work from."),
    ("04", "Data platforms", "The pipelines, models, and storage that any dependable AI capability rests on."),
    ("05", "Enterprise architecture", "Target architecture, standards, and a sequence for getting there from what exists today."),
    ("06", "Platform modernization", "Bringing existing systems into a state where AI can be applied to them safely."),
]

WORK_STRUCTURE = [
    ("01", "Product", "The business outcome the work serves, so engineering effort stays connected to why it matters."),
    ("02", "Repository", "The codebase in scope, with its standards, architecture, and accumulated context."),
    ("03", "Mission", "A defined unit of engineering work with requirements, constraints, and success criteria."),
    ("04", "Run", "A single governed agent execution, observable and evaluated against the mission."),
]

PAGES = {}

# ------------------------------ HOME --------------------------------------

PAGES["home"] = "\n\n".join(
    [
        # 1. hero
        section(
            "\n\n".join(
                [
                    eyebrow("Aletheon Labs — Governed AI for Software Engineering", centered=True),
                    h1("Build Software Your Organization Can Trust"),
                    lede(
                        "Aletheon Labs is an AI software development company. We build Aletheon Forge, "
                        "a governed AI software development and engineering platform, and we build AI "
                        "software for enterprises on the same governed foundation.",
                        centered=True,
                    ),
                    spacer(12),
                    buttons(
                        [
                            ("Request a Demo", DEMO, "solid"),
                            ("Explore Aletheon Forge", FORGE, "ghost"),
                        ]
                    ),
                    spacer(48),
                    flow(FLOW_ENGINEERING, "How engineering work flows through the governed AI layer"),
                ]
            ),
            "is-hero",
        ),
        # 2. company introduction
        section(
            "\n\n".join(
                [
                    eyebrow("Who We Are"),
                    heading("We build the software layer for enterprise AI"),
                    lede(
                        "Aletheon Labs builds software that lets organizations apply artificial "
                        "intelligence to engineering work without losing control of it. Our governed AI "
                        "layer connects people, organizational memory, technical context, enterprise "
                        "systems, and AI models to deliver secure, explainable, and role-relevant output."
                    ),
                    para(
                        "That layer reaches customers two ways: as Aletheon Forge, the platform, and as "
                        "the software we build and deliver directly.",
                        cls="ale-muted",
                    ),
                ]
            )
        ),
        # 3. the problem
        section(
            "\n\n".join(
                [
                    eyebrow("The Enterprise AI Problem"),
                    heading("Adoption is fast. Coordination is not."),
                    lede(
                        "Engineering organizations are adopting AI coding tools quickly, but adoption is "
                        "fragmented. Every engineer and every agent operates independently, with different "
                        "models, prompts, standards, and context."
                    ),
                    spacer(28),
                    cards(
                        [
                            ("01", "Inconsistent generated code", "The same problem is solved different ways depending on which agent ran, who prompted it, and how."),
                            ("02", "Security concerns", "Proprietary source and business data move through tools with no shared policy, isolation, or access model."),
                            ("03", "No architectural context", "Agents write code without knowing the system, its standards, its constraints, or the decisions already made."),
                            ("04", "Duplicate effort", "Teams resolve the same problems repeatedly because nothing retains what was already worked out."),
                            ("05", "Unmanaged agent usage", "No visibility into which tools and models are used, for what, by whom, or at what cost."),
                            ("06", "Poor traceability", "A change cannot be traced back to the requirement, the context, and the reasoning that produced it."),
                            ("07", "Lost engineering knowledge", "Technical understanding lives in individual chat histories rather than in the organization."),
                            ("08", "Review as the only control", "Human reviewers become the single checkpoint for volume no review process was sized for."),
                            ("09", "Dependence on prompting skill", "Output quality varies with individual prompt-writing ability rather than organizational standards."),
                        ],
                        variant="is-problem",
                        cols=3,
                    ),
                ]
            )
        ),
        # 4. the solution + diagram
        section(
            "\n\n".join(
                [
                    eyebrow("The Aletheon Solution", centered=True),
                    heading(
                        "A governed layer between people, systems, and models",
                        centered=True,
                    ),
                    lede(
                        "Every request carries identity, context, and memory into the layer, is governed "
                        "against policy on the way to a model, and returns through the same path with its "
                        "reasoning traceable.",
                        centered=True,
                    ),
                    spacer(40),
                    diagram(),
                ]
            )
        ),
        # 5. the platform
        section(
            "\n\n".join(
                [
                    eyebrow("The Platform"),
                    heading("Aletheon Forge"),
                    spacer(28),
                    feature(
                        "Governed AI engineering",
                        "One coordinated engineering system",
                        [
                            "Aletheon Forge helps engineering organizations coordinate AI agents, software "
                            "repositories, technical knowledge, engineering memory, and human leadership.",
                            "Every agent works from shared standards, shared context, and shared memory, "
                            "under human technical oversight — so AI coding tools are used consistently "
                            "and securely rather than agent by agent.",
                        ],
                        "Inside the platform",
                        FORGE_INSIDE,
                        cta=("Explore Aletheon Forge", FORGE),
                    ),
                ]
            )
        ),
        # 6. software development
        section(
            "\n\n".join(
                [
                    eyebrow("Software Development"),
                    heading("We also build the software itself"),
                    lede(
                        "Not every organization starts with a platform. Aletheon Labs builds AI software "
                        "for enterprises directly — applications, agent systems, integrations, and the data "
                        "platforms underneath them — governed the same way Forge governs its own agents."
                    ),
                    spacer(28),
                    cards(BUILD_CARDS, cols=3),
                    spacer(24),
                    buttons([("See how we build", DEV, "ghost")], centered=False),
                ]
            )
        ),
        # 7. personalized by role
        section(
            "\n\n".join(
                [
                    eyebrow("Personalized by Role"),
                    heading("The Right Context for the Right Person"),
                    lede(
                        "An engineering leader, an architect, and an engineer need different information "
                        "about the same work. Person-based login, memory, and context ensure each user "
                        "receives output relevant to their responsibilities."
                    ),
                    spacer(28),
                    roles(ENGINEERING_ROLES),
                    spacer(20),
                    para(PERSONALIZATION_NOTE, cls="ale-muted"),
                ]
            )
        ),
        # 8. governed across the enterprise
        section(
            "\n\n".join(
                [
                    eyebrow("Governed Across the Enterprise"),
                    heading("One Governed AI Layer Across Every Model and Tool"),
                    spacer(24),
                    checklist(
                        [
                            "User identity and role-based access",
                            "Engineering memory and retention rules",
                            "Source and data access, security, and isolation",
                            "Approved technical knowledge and retrieval",
                            "Coding and architecture standards",
                            "Approved models and providers",
                            "Change and decision traceability",
                            "Agent activity and observability",
                            "Human approval where required",
                            "Audit history and evaluation",
                        ]
                    ),
                ]
            )
        ),
        # 9. consistency
        section(
            "\n\n".join(
                [
                    eyebrow("Consistency"),
                    heading("Consistent Output, Regardless of the AI Model"),
                    lede(
                        "Aletheon holds terminology, standards, instructions, role context, and security "
                        "policy constant across every model. The same request produces the same grounded "
                        "result whichever tool or provider an engineer uses — so providers can change or "
                        "combine while governance, memory, and user experience stay intact."
                    ),
                ]
            )
        ),
        # 10. business outcomes
        section(
            "\n\n".join(
                [
                    eyebrow("Business Outcomes"),
                    heading("What changes when AI is governed"),
                    spacer(28),
                    stats(
                        [
                            ("Productivity", "Improved engineering productivity across teams."),
                            ("Code consistency", "Less inconsistent AI-generated code."),
                            ("Architecture", "Architectural decisions preserved over time."),
                            ("Knowledge", "Technical knowledge retained as people and agents change."),
                            ("Coordination", "Better coordination across engineering teams."),
                            ("Repetition", "Less repetitive engineering work."),
                            ("Standards", "Organizational standards applied to AI agents."),
                            ("Visibility", "Clear visibility into agent activity."),
                            ("Risk", "Reduced risk from unmanaged coding assistants."),
                        ]
                    ),
                ]
            )
        ),
        # 11. mission
        section(mission_block(), "is-tight"),
        # 12. research and founder credibility
        section(
            "\n\n".join(
                [
                    eyebrow("Research and Founder Credibility"),
                    heading("Grounded in research, built from practice"),
                    lede(FOUNDER),
                    para(
                        "The company's research and platform design are grounded in the belief that "
                        "successful enterprise AI requires more than model accuracy. It also requires "
                        "trusted information, governance, explainability, organizational context, memory, "
                        "and alignment with business outcomes.",
                        cls="ale-muted",
                    ),
                    spacer(20),
                    buttons([("Read the Research", RESEARCH, "ghost")], centered=False),
                ]
            )
        ),
        # 13. final CTA
        section(
            "\n\n".join(
                [
                    eyebrow("Get Started", centered=True),
                    heading("Scale AI-Assisted Development Responsibly", centered=True),
                    lede(
                        "Explore how Aletheon Labs can help your organization use artificial intelligence "
                        "securely and consistently across software engineering — as a platform, or as "
                        "software we build with you.",
                        centered=True,
                    ),
                    spacer(12),
                    buttons(
                        [
                            ("Request a Demonstration", DEMO, "solid"),
                            ("Discuss a Build", DEMO, "ghost"),
                        ]
                    ),
                ]
            ),
            "is-hero is-closing",
        ),
    ]
)

# --------------------------- ALETHEON FORGE -------------------------------

PAGES["aletheon-forge"] = "\n\n".join(
    [
        section(
            "\n\n".join(
                [
                    eyebrow("The Platform", centered=True),
                    h1("Aletheon Forge"),
                    lede(
                        "A governed AI software development and engineering platform. AI software "
                        "development with context, memory, governance, and human control.",
                        centered=True,
                    ),
                    spacer(12),
                    buttons(
                        [
                            ("Request a Demo", DEMO, "solid"),
                            ("See the Governed Layer", GOVERNED, "ghost"),
                        ]
                    ),
                    spacer(48),
                    flow(FLOW_ENGINEERING, "How a mission flows through Aletheon Forge"),
                ]
            ),
            "is-hero",
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("Positioning"),
                    heading("One coordinated engineering system"),
                    lede(
                        "Aletheon Forge helps engineering organizations coordinate AI agents, software "
                        "repositories, technical knowledge, engineering memory, and human leadership. "
                        "Every agent works from shared standards, shared context, and shared memory, "
                        "under human technical oversight."
                    ),
                    para(
                        "The platform enables organizations to use AI coding tools consistently and "
                        "securely rather than allowing each engineer or agent to operate independently.",
                        cls="ale-muted",
                    ),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("What It Replaces"),
                    heading("Agent by agent does not scale"),
                    spacer(28),
                    cards(
                        [
                            ("Without Forge", "Context is re-explained", "Each engineer re-establishes the architecture, standards, and history by hand, in every session, for every agent."),
                            ("Without Forge", "Standards are advisory", "Coding and architecture standards exist in documents that agents never read and cannot be held to."),
                            ("Without Forge", "Oversight is after the fact", "The first time anyone sees what an agent decided is in review, once the code already exists."),
                        ],
                        variant="is-problem",
                        cols=3,
                    ),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("Structure"),
                    heading("Work organized the way engineering actually runs"),
                    lede(
                        "Four levels, each inheriting context from the one above it, so an agent run is "
                        "never disconnected from the codebase it touches or the outcome it serves."
                    ),
                    spacer(28),
                    cards(WORK_STRUCTURE, cols=4),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("Core Capabilities"),
                    heading("What the platform does"),
                    spacer(24),
                    checklist(
                        [
                            "Coordinate AI engineering agents",
                            "Organize work by product, repository, mission, and run",
                            "Route relevant context to each agent",
                            "Maintain engineering memory",
                            "Capture lessons learned",
                            "Build knowledge across repositories and systems",
                            "Apply coding and architecture standards",
                            "Connect software work to business objectives",
                            "Govern AI-generated code and recommendations",
                            "Maintain human technical oversight",
                            "Integrate with source control and development workflows",
                            "Evaluate agent performance and outcomes",
                        ]
                    ),
                    spacer(32),
                    tags(
                        "Governs across",
                        [
                            "Source control",
                            "Development workflows",
                            "Approved model providers",
                            "Identity and access",
                            "Organizational standards",
                            "Audit and observability",
                        ],
                    ),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("Human Control"),
                    heading("Agents propose. People remain accountable."),
                    lede(
                        "Governance is only real if a person can see what happened and stop it. Forge "
                        "keeps technical leadership in the path rather than alongside it."
                    ),
                    spacer(24),
                    checklist(
                        [
                            "Human technical oversight of agent work",
                            "Human approval where required",
                            "Observable agent activity",
                            "Traceable AI-generated code and recommendations",
                            "Evaluation of agent performance and outcomes",
                            "Standards enforced rather than suggested",
                        ]
                    ),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("Business Value"),
                    heading("What it changes"),
                    spacer(28),
                    stats(
                        [
                            ("Productivity", "Improve engineering productivity across teams."),
                            ("Code consistency", "Reduce inconsistent AI-generated code."),
                            ("Architecture", "Preserve architectural decisions over time."),
                            ("Retention", "Retain technical knowledge as people and agents change."),
                            ("Coordination", "Improve coordination across engineering teams."),
                            ("Repetition", "Reduce repetitive engineering work."),
                            ("Standards", "Apply organizational standards to AI agents."),
                            ("Visibility", "Increase visibility into agent activity."),
                            ("Risk", "Reduce risk from unmanaged coding assistants."),
                        ]
                    ),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    heading("Scale AI-assisted development responsibly", centered=True),
                    lede(
                        "Explore how governed AI engineering would apply to your teams and your codebase.",
                        centered=True,
                    ),
                    spacer(12),
                    buttons(
                        [
                            ("Request a Demo", DEMO, "solid"),
                            ("See How We Build", DEV, "ghost"),
                        ]
                    ),
                ]
            ),
            "is-hero is-closing",
        ),
    ]
)

# ------------------------ SOFTWARE DEVELOPMENT ----------------------------

PAGES["software-development"] = "\n\n".join(
    [
        section(
            "\n\n".join(
                [
                    eyebrow("Software Development", centered=True),
                    h1("AI Software, Built Governed"),
                    lede(
                        "Aletheon Labs builds AI software for enterprises — applications, agent systems, "
                        "integrations, and data platforms — on the same governed foundation that runs "
                        "inside Aletheon Forge.",
                        centered=True,
                    ),
                    spacer(12),
                    buttons(
                        [
                            ("Discuss a Build", DEMO, "solid"),
                            ("Explore Aletheon Forge", FORGE, "ghost"),
                        ]
                    ),
                ]
            ),
            "is-hero",
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("What We Build"),
                    heading("Software where AI is part of the architecture"),
                    lede(
                        "AI that an organization can depend on is an engineering problem before it is a "
                        "model problem. It needs identity, context, memory, policy, and traceability built "
                        "into the system — which is what we build."
                    ),
                    spacer(28),
                    cards(BUILD_CARDS, cols=3),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("How We Work"),
                    heading("Governed by default, not by review"),
                    lede(
                        "We build with AI agents, inside the same governance we sell. That means the work "
                        "arrives with its context, standards, and reasoning attached rather than "
                        "reconstructed afterwards."
                    ),
                    spacer(28),
                    cards(
                        [
                            ("01", "Your identity model", "Access, roles, and data boundaries are your existing ones. Nothing is granted to an agent that a person would not be granted."),
                            ("02", "Your standards", "Coding and architecture standards are applied to agent work as constraints, not as documentation nobody reads."),
                            ("03", "Traceable decisions", "Each change can be traced back to the requirement, the context it was given, and the reasoning that produced it."),
                            ("04", "Human accountability", "Technical leadership stays in the path. Agents propose; people approve and remain accountable."),
                        ],
                        cols=2,
                    ),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("Structure"),
                    heading("Engagements organized the way Forge organizes work"),
                    lede(
                        "The same four levels, so what we deliver is legible to your teams and portable "
                        "onto the platform if you later adopt it."
                    ),
                    spacer(28),
                    cards(WORK_STRUCTURE, cols=4),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("Who We Work With"),
                    heading("The same build, presented differently"),
                    lede(
                        "The same piece of work needs to reach an engineering leader, an architect, and an "
                        "engineer in three different forms. Each receives the detail, context, and "
                        "decisions relevant to their role."
                    ),
                    spacer(28),
                    roles(ENGINEERING_ROLES),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    heading("Find the right starting point", centered=True),
                    lede(
                        "Tell us what you are trying to build, and we will map it to the right shape of "
                        "engagement.",
                        centered=True,
                    ),
                    spacer(12),
                    buttons([("Start a Conversation", DEMO, "solid")]),
                ]
            ),
            "is-hero is-closing",
        ),
    ]
)

# ---------------------------- GOVERNED AI ---------------------------------

PAGES["governed-ai"] = "\n\n".join(
    [
        section(
            "\n\n".join(
                [
                    eyebrow("The Architecture", centered=True),
                    h1("The Governed AI Layer"),
                    lede(
                        "The foundation connecting users, organizational knowledge, business systems, and "
                        "AI providers — so organizations can adopt new models without rebuilding their "
                        "standards, user context, memory, or governance architecture each time.",
                        centered=True,
                    ),
                ]
            ),
            "is-hero",
        ),
        section("\n\n".join([diagram()]), "is-tight"),
        section(
            "\n\n".join(
                [
                    eyebrow("What the Layer Manages"),
                    heading("Fourteen responsibilities, one place"),
                    spacer(24),
                    checklist(
                        [
                            "Authentication",
                            "User identity",
                            "Role and permissions",
                            "Context routing",
                            "Organizational memory",
                            "Prompt standards",
                            "Model selection",
                            "Knowledge retrieval",
                            "Data security",
                            "AI policies",
                            "Observability",
                            "Evaluation",
                            "Explainability",
                            "Audit history",
                        ]
                    ),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("Core Principles"),
                    heading("What governance has to deliver"),
                    spacer(28),
                    cards(
                        [
                            ("Principle 01", "Trust", "Users must be able to trust the information, recommendations, and code produced by AI — through explainable output, traceable sources, transparent interactions, human review, secure access controls, and consistent organizational knowledge."),
                            ("Principle 02", "Governance", "AI should operate within defined organizational, security, and business boundaries — role-based access, data isolation, usage policies, approved models, prompt and context governance, decision traceability, human approval, and monitoring."),
                            ("Principle 03", "Consistency", "Terminology, standards, instructions, role context, approved knowledge, and security policy stay constant across every model, so the same request returns the same grounded result whichever tool an engineer reaches for."),
                            ("Principle 04", "Innovative Use of AI", "Moving beyond basic chatbots and isolated automation into agent orchestration, organizational memory, knowledge discovery, decision support, risk identification, and continuous organizational learning."),
                        ],
                        cols=2,
                    ),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("Person-Based Memory"),
                    heading("Memory that stays governed"),
                    lede(
                        "Aletheon maintains governed memory to help AI understand the user over time — "
                        "previous questions, relevant decisions, accepted or rejected recommendations, "
                        "preferred level of detail, current objectives, role-specific priorities, and "
                        "lessons learned. This reduces repetitive prompting and makes AI increasingly "
                        "relevant."
                    ),
                    spacer(24),
                    checklist(
                        [
                            "User-level access controls",
                            "Organizational policies",
                            "Clear retention rules",
                            "Auditability",
                            "User visibility",
                            "Administrative controls",
                        ]
                    ),
                    spacer(20),
                    para(PERSONALIZATION_NOTE, cls="ale-muted"),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("Where It Runs"),
                    heading("One layer, two ways to adopt it"),
                    spacer(28),
                    cards(
                        [
                            ("Path 01", "Aletheon Forge", "Adopt the layer as a platform. Forge applies it to AI software development and engineering across your products, repositories, and agents."),
                            ("Path 02", "Software we build", "Adopt the layer inside software we build with you — applications, agent systems, integrations, and data platforms, governed the same way."),
                        ],
                        cols=2,
                    ),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    heading("See the layer applied to your organization", centered=True),
                    spacer(12),
                    buttons(
                        [
                            ("Request a Demo", DEMO, "solid"),
                            ("Explore Aletheon Forge", FORGE, "ghost"),
                        ]
                    ),
                ]
            ),
            "is-hero is-closing",
        ),
    ]
)

# ------------------------------ RESEARCH ----------------------------------

PAGES["research"] = "\n\n".join(
    [
        section(
            "\n\n".join(
                [
                    eyebrow("Research", centered=True),
                    h1("Research and Foundations"),
                    lede(
                        "Aletheon's platform design is grounded in the belief that successful enterprise "
                        "AI requires more than model accuracy.",
                        centered=True,
                    ),
                ]
            ),
            "is-hero",
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("Founder"),
                    heading("Dr. Andrew Ganje"),
                    lede(FOUNDER),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("Research Position"),
                    heading("Model accuracy is not sufficient"),
                    lede(
                        "Enterprise AI also requires trusted information, governance, explainability, "
                        "organizational context, memory, and alignment with business outcomes. These are "
                        "architectural properties, not model properties — which is why Aletheon builds "
                        "them into a layer rather than expecting them from a provider."
                    ),
                    spacer(28),
                    cards(
                        [
                            ("Area 01", "Trusted information", "What has to be true about a source, and about the path from source to output, before a person should act on it."),
                            ("Area 02", "Organizational context", "How role, responsibility, permission, and technical meaning change what the correct answer actually is."),
                            ("Area 03", "Governed memory", "How systems retain what matters across interactions without exceeding what a user is authorized to know."),
                            ("Area 04", "Explainability in practice", "What traceability has to look like for an engineer or a decision-maker, rather than for a model evaluator."),
                        ],
                        cols=2,
                    ),
                ]
            )
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
            "is-hero is-closing",
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
                    h1("The Governed AI Layer"),
                    lede(
                        "Aletheon Labs is an AI software development company building governed software "
                        "for enterprise engineering organizations.",
                        centered=True,
                    ),
                ]
            ),
            "is-hero",
        ),
        section(mission_block(), "is-tight"),
        section(
            "\n\n".join(
                [
                    eyebrow("What We Build"),
                    heading("One governed foundation, two ways to adopt it"),
                    lede(
                        "Aletheon Labs develops software that connects people, technical context, "
                        "organizational memory, enterprise systems, and AI models. The governed AI layer "
                        "is the foundation — one place where identity, context, memory, knowledge, policy, "
                        "and audit are held for the whole enterprise."
                    ),
                    spacer(28),
                    cards(
                        [
                            ("The platform", "Aletheon Forge", "A governed AI software development and engineering platform that coordinates agents, repositories, knowledge, and human oversight."),
                            ("The practice", "Software development", "AI applications, agent systems, integrations, and data platforms that we build for enterprises on the same governed foundation."),
                        ],
                        cols=2,
                    ),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("What We Believe"),
                    heading("Enterprise AI should be intelligent, trusted, governed, and consistent"),
                    lede(
                        "This enables organizations to deliver AI experiences that are relevant to each "
                        "user, consistent across teams, secure and governed, explainable and traceable, "
                        "informed by organizational context, and continuously improved through memory and "
                        "learning."
                    ),
                    spacer(24),
                    checklist(
                        [
                            "Relevant to each user",
                            "Consistent across teams",
                            "Secure and governed",
                            "Explainable and traceable",
                            "Informed by organizational context",
                            "Continuously improved through memory and learning",
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
                    lede(FOUNDER),
                    spacer(20),
                    buttons([("Read the Research", RESEARCH, "ghost")], centered=False),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    heading("Build AI Your Organization Can Trust", centered=True),
                    spacer(12),
                    buttons(
                        [
                            ("Request a Demo", DEMO, "solid"),
                            ("Discuss a Partnership", DEMO, "ghost"),
                        ]
                    ),
                ]
            ),
            "is-hero is-closing",
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
                    h1("Request a Demonstration"),
                    lede(
                        "Explore how Aletheon Labs can help your organization use artificial intelligence "
                        "securely and consistently across software engineering.",
                        centered=True,
                    ),
                    spacer(12),
                    buttons(
                        [
                            ("Email contact@aletheonlabs.com", "mailto:contact@aletheonlabs.com", "solid")
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
                            ("01", "Platform Demonstration", "See Aletheon Forge applied to a scenario that resembles your engineering organization."),
                            ("02", "A Software Build", "Discuss an AI application, agent system, integration, or data platform you need built."),
                            ("03", "Governed AI Discussion", "Talk through the governed AI layer, how it would sit in your architecture, and what it would govern."),
                            ("04", "Partnership or Research", "Partnership opportunities, strategic collaboration, or technical discussion of the research behind the platform."),
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
                            ("Step 01", "Share your goals", "Tell us what you are trying to solve, improve, or build."),
                            ("Step 02", "Discuss opportunities", "We identify where governed AI creates meaningful value for your organization."),
                            ("Step 03", "Define the path forward", "We outline the right next steps based on your needs, systems, codebase, and desired outcomes."),
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
                    lede("We would be glad to learn more about your goals.", centered=True),
                    spacer(12),
                    buttons(
                        [
                            ("Email contact@aletheonlabs.com", "mailto:contact@aletheonlabs.com", "solid")
                        ]
                    ),
                ]
            ),
            "is-hero is-closing",
        ),
    ]
)


# --------------------------------------------------------------------------

# Copy that must never reappear on the site. The Intelligence platform was sold;
# any surviving reference is a bug, so the build fails rather than ships one.
FORBIDDEN = (
    "Aletheon Intelligence",
    "aletheon-intelligence",
    "business intelligence",
    "not a consulting",
    "not a general consulting",
)


def main():
    os.makedirs(OUT, exist_ok=True)
    failures = []

    for slug, markup in PAGES.items():
        path = os.path.join(OUT, f"{slug}.html")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(markup + "\n")

        # block balance check — an unbalanced page breaks the editor
        depth = 0
        for m in re.finditer(r"<!--\s+(/?)wp:([a-z0-9/-]+)(.*?)-->", markup, re.S):
            if m.group(1) == "/":
                depth -= 1
            elif not m.group(3).rstrip().endswith("/"):
                depth += 1

        hits = [t for t in FORBIDDEN if t.lower() in markup.lower()]
        if depth != 0:
            failures.append(f"{slug}: block depth {depth}, expected 0")
        if hits:
            failures.append(f"{slug}: forbidden copy present -> {', '.join(hits)}")

        flag = "OK " if depth == 0 and not hits else "BAD"
        print(f"{flag} {slug:24s} {len(markup):6d} bytes  depth={depth}")

    # Stale page files from earlier builds would otherwise be deployed by hand.
    expected = {f"{slug}.html" for slug in PAGES}
    orphans = sorted(f for f in os.listdir(OUT) if f.endswith(".html") and f not in expected)
    for f in orphans:
        print(f"!!  orphan page file in pages/: {f} -- delete it")

    if failures:
        raise SystemExit("\nBUILD FAILED\n  " + "\n  ".join(failures))


if __name__ == "__main__":
    main()
