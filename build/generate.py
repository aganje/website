#!/usr/bin/env python3
"""
Generate WordPress block markup for every aletheonlabs.com page.

Copy is drawn strictly from WebsiteImprovements. Nothing here invents customers,
testimonials, metrics, or capabilities that the brief does not state.

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


def flow():
    steps = ["Identity", "Context", "Memory", "Knowledge", "AI", "Governance", "Action"]
    out = ['<div class="ale-flow" role="list" aria-label="How a request flows through Aletheon">']
    for i, s in enumerate(steps):
        out.append(
            f'<div class="ale-flow-step" role="listitem" style="--i:{i}"><span>{esc(s)}</span></div>'
        )
    out.append("</div>")
    return raw("".join(out))


def mission_block():
    return raw(
        '<div class="ale-mission">'
        '<p class="ale-eyebrow is-centered">Our Mission</p>'
        "<blockquote>Aletheon Labs exists to make enterprise AI trustworthy. "
        "We build the governed intelligence layer that ensures every AI interaction is "
        "secure, explainable, consistent, and relevant to the person using it.</blockquote>"
        "</div>"
    )


# --------------------------------------------------------------------------
# the signature asset: the governed AI layer
# --------------------------------------------------------------------------

TOP_NODES = [
    ("Executives", 60),
    ("Business Leaders", 205),
    ("Analysts", 350),
    ("Engineers", 470),
    ("Enterprise Apps", 600),
    ("Aletheon Platforms", 762),
]
BOTTOM_NODES = [
    ("OpenAI", 70),
    ("Anthropic", 210),
    ("Microsoft", 350),
    ("Google", 490),
    ("Local Models", 620),
    ("Approved Models", 780),
]
LAYER_CHIPS = [
    ("Identity", 62),
    ("Context", 180),
    ("Memory", 296),
    ("Knowledge", 412),
    ("Policy", 540),
    ("Audit", 648),
    ("Evaluation", 754),
]


def diagram():
    p = []
    p.append(
        '<svg class="ale-diagram" viewBox="0 0 940 520" role="img" '
        'xmlns="http://www.w3.org/2000/svg" '
        'aria-label="The governed AI layer sits between users and applications above, and AI '
        'models and providers below. Every request passes through identity, context, memory, '
        'knowledge, policy, audit and evaluation before reaching a model, and every response '
        'returns through the same layer.">'
    )

    # band labels
    p.append('<text x="18" y="26" class="d-accent" font-size="11" letter-spacing="2.2">USERS &amp; APPLICATIONS</text>')
    p.append('<text x="18" y="288" class="d-accent" font-size="11" letter-spacing="2.2">THE GOVERNED AI LAYER</text>')
    p.append('<text x="18" y="452" class="d-accent" font-size="11" letter-spacing="2.2">AI MODELS &amp; PROVIDERS</text>')

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

# The three offerings. Intelligence and Forge are separate products, each built for its
# own job — they are deliberately not described as sharing an architecture.
OFFERINGS_GRID = (
    '<div class="ale-grid is-3">'
    '<div class="ale-card is-platform">'
    '<span class="ale-card-num">Product</span>'
    '<h3 class="ale-h3">Aletheon Intelligence</h3>'
    "<p>A personalized and governed AI business intelligence platform. It helps organizations "
    "understand what is happening, why it is happening, and what actions should be considered — "
    "adding business context, organizational memory, AI reasoning, and governed recommendations "
    "to the data they already have.</p>"
    '<p style="margin-top:1.1rem"><a class="ale-btn" href="/aletheon-intelligence/">Explore Intelligence</a></p>'
    "</div>"
    '<div class="ale-card is-platform">'
    '<span class="ale-card-num">Product</span>'
    '<h3 class="ale-h3">Aletheon Forge</h3>'
    "<p>A governed AI software development and engineering platform. It coordinates AI agents, "
    "repositories, technical knowledge, engineering memory, and human leadership so engineering "
    "organizations can apply AI to their own software work consistently and under oversight.</p>"
    '<p style="margin-top:1.1rem"><a class="ale-btn" href="/aletheon-forge/">Explore Forge</a></p>'
    "</div>"
    '<div class="ale-card is-platform">'
    '<span class="ale-card-num">Services</span>'
    '<h3 class="ale-h3">Software Development</h3>'
    "<p>Custom software engineering for organizations that need systems built, integrated, or "
    "modernized — spanning enterprise architecture, business applications, data platforms, "
    "integrations, and applied AI.</p>"
    '<p style="margin-top:1.1rem"><a class="ale-btn" href="/software-development/">Explore Software Development</a></p>'
    "</div>"
    "</div>"
)

# ------------------------------ HOME --------------------------------------

PAGES["home"] = "\n\n".join(
    [
        # 1. hero
        section(
            "\n\n".join(
                [
                    eyebrow("Aletheon Labs — Governed AI for the Enterprise", centered=True),
                    h1("Build a Trusted and Governed AI Enterprise"),
                    lede(
                        "Aletheon Labs develops AI software platforms for business intelligence and "
                        "software engineering, providing secure, personalized, and consistent AI "
                        "experiences across the enterprise.",
                        centered=True,
                    ),
                    spacer(12),
                    buttons([("Request a Demo", DEMO, "solid"), ("Explore Our Platforms", "/governed-ai/", "ghost")]),
                    spacer(48),
                    flow(),
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
                        "Aletheon Labs builds platforms that help organizations apply artificial "
                        "intelligence across business operations and software engineering. Our governed "
                        "AI layer connects people, organizational memory, business context, enterprise "
                        "data, and AI models to deliver secure, explainable, and role-relevant intelligence."
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
                        "Organizations are rapidly adopting AI, but adoption is often fragmented. "
                        "Employees use different models, prompts, tools, and information sources."
                    ),
                    spacer(28),
                    cards(
                        [
                            ("01", "Inconsistent answers", "The same question produces different answers depending on who asked, which tool they used, and how they phrased it."),
                            ("02", "Security concerns", "Sensitive business information moves through tools with no shared policy, isolation, or access model."),
                            ("03", "Limited organizational context", "Models answer without knowing the business, its terminology, its rules, or the person asking."),
                            ("04", "Duplicate effort", "Teams solve the same problems repeatedly because nothing retains what was already learned."),
                            ("05", "Unmanaged AI usage", "No visibility into which models are used, for what, by whom, or at what cost."),
                            ("06", "Poor traceability", "Recommendations cannot be traced back to the data and reasoning that produced them."),
                            ("07", "Loss of organizational knowledge", "Insight lives in individual chat histories rather than in the organization."),
                            ("08", "Role-blind recommendations", "Output ignores what the user is actually responsible for and authorized to see."),
                            ("09", "Dependence on prompting skill", "Quality varies with individual prompt-writing ability rather than organizational standards."),
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
                    heading("A governed intelligence layer between people, systems, and models", centered=True),
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
        # 5. the offerings
        section(
            "\n\n".join(
                [
                    eyebrow("What We Offer"),
                    heading("Three ways we help organizations apply AI"),
                    lede(
                        "Two products, each purpose-built for what it does, and an engineering team that "
                        "builds alongside you."
                    ),
                    spacer(28),
                    raw(OFFERINGS_GRID),
                ]
            )
        ),
        # 6. personalized by role
        section(
            "\n\n".join(
                [
                    eyebrow("Personalized by Role"),
                    heading("The Right Intelligence for the Right Person"),
                    lede(
                        "Aletheon understands that an executive, analyst, architect, and engineer require "
                        "different information. Person-based login, memory, and context ensure each user "
                        "receives intelligence relevant to their responsibilities."
                    ),
                    spacer(28),
                    roles(
                        [
                            ("Executive", "Direction, exposure, and the decisions that need to be made."),
                            ("Finance Leader", "Drivers, variance, and financial consequence."),
                            ("Operations Manager", "What changed, what it affects, and what to do now."),
                            ("Supply Chain Analyst", "Demand signals, inventory movement, and emerging risk."),
                            ("Enterprise Architect", "Systems, integration, and structural implication."),
                            ("Software Engineer", "Repositories, standards, context, and the work itself."),
                        ]
                    ),
                    spacer(20),
                    para(
                        "Personalization operates inside your security model. Every AI interaction stays "
                        "subject to permissions, governance, and organizational policy.",
                        cls="ale-muted",
                    ),
                ]
            )
        ),
        # 7. governed across the enterprise
        section(
            "\n\n".join(
                [
                    eyebrow("Governed Across the Enterprise"),
                    heading("One Governed AI Layer Across Every Model and Application"),
                    spacer(24),
                    checklist(
                        [
                            "User identity and role-based access",
                            "Organizational memory and retention rules",
                            "Data access, security, and isolation",
                            "Approved knowledge and knowledge retrieval",
                            "Prompt standards and context governance",
                            "Approved models and providers",
                            "Recommendations and decision traceability",
                            "Agent activity and observability",
                            "Human approval where required",
                            "Audit history and evaluation",
                        ]
                    ),
                ]
            )
        ),
        # 8. consistent AI experiences
        section(
            "\n\n".join(
                [
                    eyebrow("Consistency"),
                    heading("Consistent Intelligence, Regardless of the AI Model"),
                    lede(
                        "Aletheon holds terminology, business rules, instructions, role context, and "
                        "security policy constant across every model. The same question returns the same "
                        "grounded answer whichever tool or provider an employee uses — so providers can "
                        "change or combine while governance, memory, and user experience stay intact."
                    ),
                ]
            )
        ),
        # 9. business outcomes
        section(
            "\n\n".join(
                [
                    eyebrow("Business Outcomes"),
                    heading("What changes when AI is governed"),
                    spacer(28),
                    stats(
                        [
                            ("Relevance", "More relevant information for every user, based on role and responsibility."),
                            ("Decision speed", "Faster and better-supported decisions across the business."),
                            ("Consistency", "Consistent use of AI across teams, tools, and providers."),
                            ("Risk", "Reduced risk from unmanaged and unmonitored AI tools."),
                            ("Engineering", "Improved software engineering productivity and coordination."),
                            ("Knowledge", "Greater retention of organizational knowledge over time."),
                            ("Flexibility", "Secure adoption of multiple AI models without re-architecture."),
                            ("Visibility", "Clear visibility into how AI is actually being used."),
                            ("Trust", "Improved trust in AI-generated recommendations."),
                        ]
                    ),
                ]
            )
        ),
        # 9.5 mission
        section(mission_block(), "is-tight"),
        # 10. research and founder credibility
        section(
            "\n\n".join(
                [
                    eyebrow("Research and Founder Credibility"),
                    heading("Grounded in research, built from practice"),
                    lede(
                        "Aletheon Labs was founded by Dr. Andrew Ganje, combining doctoral research "
                        "initiated at Purdue with extensive experience in enterprise architecture, software "
                        "engineering, business applications, data platforms, integrations, and artificial "
                        "intelligence."
                    ),
                    para(
                        "The company's research and platform design are grounded in the belief that "
                        "successful enterprise AI requires more than model accuracy. It also requires trusted "
                        "information, governance, explainability, organizational context, memory, and "
                        "alignment with business outcomes.",
                        cls="ale-muted",
                    ),
                    spacer(20),
                    buttons([("Read the Research", "/research/", "ghost")], centered=False),
                ]
            )
        ),
        # 11. final CTA
        section(
            "\n\n".join(
                [
                    eyebrow("Get Started", centered=True),
                    heading("Build AI Your Organization Can Trust", centered=True),
                    lede(
                        "Explore how Aletheon Labs can help your organization use artificial intelligence "
                        "securely, consistently, and effectively across business intelligence and software "
                        "development.",
                        centered=True,
                    ),
                    spacer(12),
                    buttons([("Request a Demonstration", DEMO, "solid"), ("Discuss a Partnership", DEMO, "ghost")]),
                ]
            ),
            "is-hero",
        ),
    ]
)

# ------------------------ ALETHEON INTELLIGENCE ---------------------------

PAGES["aletheon-intelligence"] = "\n\n".join(
    [
        section(
            "\n\n".join(
                [
                    eyebrow("Platform 01", centered=True),
                    h1("Aletheon Intelligence"),
                    lede(
                        "A personalized and governed AI business intelligence platform. Business "
                        "intelligence that understands your organization and the person using it.",
                        centered=True,
                    ),
                    spacer(12),
                    buttons([("Request a Demo", DEMO, "solid"), ("See the Governed Layer", "/governed-ai/", "ghost")]),
                ]
            ),
            "is-hero",
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("Positioning"),
                    heading("Reports tell you what. Aletheon tells you why, and what to do"),
                    lede(
                        "Aletheon Intelligence helps organizations understand what is happening, why it is "
                        "happening, and what actions should be considered. It brings business context, "
                        "organizational memory, AI reasoning, and governed recommendations to the data you "
                        "already have."
                    ),
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
                            "Connect enterprise and external data",
                            "Interpret business performance",
                            "Identify trends, risks, and anomalies",
                            "Explain contributing factors",
                            "Generate role-specific recommendations",
                            "Present information based on the user's responsibilities",
                            "Maintain memory of prior decisions and interactions",
                            "Preserve traceability between source data and recommendations",
                            "Support human review and approval",
                            "Learn from organizational outcomes",
                        ]
                    ),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("How It Works"),
                    heading("Every insight carries its provenance"),
                    lede(
                        "A recommendation is only useful if the person receiving it can see where it came "
                        "from. Each request travels through the governed layer, and the path it took remains "
                        "attached to the answer."
                    ),
                    spacer(32),
                    flow(),
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
                            ("Analysis time", "Reduce time spent analyzing reports."),
                            ("Early warning", "Identify issues earlier, before they compound."),
                            ("Executive visibility", "Improve visibility at the leadership level."),
                            ("Role relevance", "Deliver more relevant information to each role."),
                            ("Consistency", "Create consistency across business decisions."),
                            ("Interpretation", "Reduce dependence on manual interpretation."),
                            ("Security", "Apply AI securely to enterprise data."),
                            ("Knowledge", "Preserve organizational knowledge over time."),
                            ("Posture", "Move from reactive reporting to proactive intelligence."),
                        ]
                    ),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    heading("See Aletheon Intelligence in context", centered=True),
                    lede("Explore how governed business intelligence would apply to your organization.", centered=True),
                    spacer(12),
                    buttons([("Request a Demo", DEMO, "solid"), ("Explore Aletheon Forge", "/aletheon-forge/", "ghost")]),
                ]
            ),
            "is-hero",
        ),
    ]
)

# --------------------------- ALETHEON FORGE -------------------------------

PAGES["aletheon-forge"] = "\n\n".join(
    [
        section(
            "\n\n".join(
                [
                    eyebrow("Platform 02", centered=True),
                    h1("Aletheon Forge"),
                    lede(
                        "A governed AI software development and engineering platform. AI software "
                        "development with context, memory, governance, and human control.",
                        centered=True,
                    ),
                    spacer(12),
                    buttons([("Request a Demo", DEMO, "solid"), ("See the Governed Layer", "/governed-ai/", "ghost")]),
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
                        "repositories, technical knowledge, engineering memory, and human leadership. Every "
                        "agent works from shared standards, shared context, and shared memory, under human "
                        "technical oversight."
                    ),
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
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("Structure"),
                    heading("Work organized the way engineering actually runs"),
                    spacer(28),
                    cards(
                        [
                            ("01", "Product", "The business outcome the work serves, so engineering effort stays connected to why it matters."),
                            ("02", "Repository", "The codebase in scope, with its standards, architecture, and accumulated context."),
                            ("03", "Mission", "A defined unit of engineering work with requirements, constraints, and success criteria."),
                            ("04", "Run", "A single governed agent execution, observable and evaluated against the mission."),
                        ],
                        cols=4,
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
                    lede("Explore how governed AI engineering would apply to your teams.", centered=True),
                    spacer(12),
                    buttons([("Request a Demo", DEMO, "solid"), ("Explore Aletheon Intelligence", "/aletheon-intelligence/", "ghost")]),
                ]
            ),
            "is-hero",
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
                        "business rules, user context, memory, or governance architecture each time.",
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
                            ("Principle 01", "Trust", "Users must be able to trust the information, recommendations, and actions produced by AI — through explainable recommendations, traceable sources, transparent interactions, human review, secure access controls, and consistent organizational knowledge."),
                            ("Principle 02", "Governance", "AI should operate within defined organizational, security, and business boundaries — role-based access, data isolation, usage policies, approved models, prompt and context governance, decision traceability, human approval, and monitoring."),
                            ("Principle 03", "Consistency", "Terminology, business rules, instructions, role context, approved knowledge, and security policy stay constant across every model, so the same question returns the same grounded answer whichever tool an employee reaches for."),
                            ("Principle 04", "Innovative Use of AI", "Moving beyond basic chatbots and isolated automation into decision support, organizational memory, knowledge discovery, agent orchestration, risk identification, and continuous organizational learning."),
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
                        "preferred reporting detail, current objectives, role-specific priorities, and "
                        "lessons learned. This reduces repetitive prompting and makes AI increasingly relevant."
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
                    para(
                        "Personalization operates inside your security model. Every AI interaction stays "
                        "subject to permissions, governance, and organizational policy.",
                        cls="ale-muted",
                    ),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    heading("See the layer applied to your organization", centered=True),
                    spacer(12),
                    buttons([("Request a Demo", DEMO, "solid")]),
                ]
            ),
            "is-hero",
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
                        "Aletheon's platform design is grounded in the belief that successful enterprise AI "
                        "requires more than model accuracy.",
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
                    lede(
                        "Aletheon Labs was founded by Dr. Andrew Ganje, combining doctoral research "
                        "initiated at Purdue with extensive experience in enterprise architecture, software "
                        "engineering, business applications, data platforms, integrations, and artificial "
                        "intelligence."
                    ),
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
                        "architectural properties, not model properties — which is why Aletheon builds them "
                        "into a layer rather than expecting them from a provider."
                    ),
                    spacer(28),
                    cards(
                        [
                            ("Area 01", "Trusted information", "What has to be true about a source, and about the path from source to recommendation, before a person should act on it."),
                            ("Area 02", "Organizational context", "How role, responsibility, permission, and business meaning change what the correct answer actually is."),
                            ("Area 03", "Governed memory", "How systems retain what matters across interactions without exceeding what a user is authorized to know."),
                            ("Area 04", "Explainability in practice", "What traceability has to look like for a decision-maker, rather than for a model evaluator."),
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
            "is-hero",
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
                    h1("Where Governed AI Applies"),
                    lede(
                        "Aletheon's platforms apply AI across business decision-making and software "
                        "engineering, while maintaining security, governance, organizational context, and "
                        "human oversight.",
                        centered=True,
                    ),
                ]
            ),
            "is-hero",
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("By Application"),
                    heading("What the platforms are used for"),
                    spacer(28),
                    cards(
                        [
                            ("01", "Business intelligence", "Interpret performance, identify trends and anomalies, and explain contributing factors with traceable sources."),
                            ("02", "Decision support", "Role-specific recommendations that reflect what a person is responsible for and authorized to see."),
                            ("03", "Organizational memory", "Retain decisions, rationale, and lessons learned so knowledge stays with the organization."),
                            ("04", "Knowledge discovery", "Surface relevant organizational knowledge at the moment it applies to the work."),
                            ("05", "Software engineering", "Coordinate AI agents across products, repositories, missions, and runs under human oversight."),
                            ("06", "Agent orchestration", "Route context, apply standards, and evaluate agent performance and outcomes."),
                            ("07", "Process improvement", "Identify where work is repetitive, inconsistent, or disconnected across systems."),
                            ("08", "Risk identification", "Detect exceptions, emerging risk, and conditions that warrant human attention."),
                            ("09", "Continuous learning", "Improve relevance over time by learning from organizational outcomes."),
                        ],
                        cols=3,
                    ),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    eyebrow("By Role"),
                    heading("The same condition, presented differently"),
                    lede(
                        "The same business condition may need to reach an executive, a finance leader, and "
                        "an engineer in three different forms. Each person receives the information, level of "
                        "detail, recommendations, and actions most relevant to their role."
                    ),
                    spacer(28),
                    roles(
                        [
                            ("Executive", "Direction, exposure, and the decisions that need to be made."),
                            ("Finance Leader", "Drivers, variance, and financial consequence."),
                            ("Operations Manager", "What changed, what it affects, and what to do now."),
                            ("Supply Chain Analyst", "Demand signals, inventory movement, and emerging risk."),
                            ("Enterprise Architect", "Systems, integration, and structural implication."),
                            ("Software Engineer", "Repositories, standards, context, and the work itself."),
                        ]
                    ),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    heading("Find the right starting point", centered=True),
                    lede("Tell us what you are trying to solve and we will map it to the platform that fits.", centered=True),
                    spacer(12),
                    buttons([("Request a Demo", DEMO, "solid")]),
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
                    h1("The Governed Intelligence Layer"),
                    lede(
                        "Aletheon Labs is an AI software development company building governed platforms "
                        "for business intelligence and software engineering.",
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
                    heading("Two products and an engineering team"),
                    lede(
                        "Aletheon Labs develops AI software that connects people, business context, "
                        "organizational memory, enterprise data, and AI models — and builds custom systems "
                        "for organizations that need engineering alongside the products."
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
                    lede(
                        "Aletheon Labs was founded by Dr. Andrew Ganje, combining doctoral research "
                        "initiated at Purdue with extensive experience in enterprise architecture, software "
                        "engineering, business applications, data platforms, integrations, and artificial "
                        "intelligence."
                    ),
                    spacer(20),
                    buttons([("Read the Research", "/research/", "ghost")], centered=False),
                ]
            )
        ),
        section(
            "\n\n".join(
                [
                    heading("Build AI Your Organization Can Trust", centered=True),
                    spacer(12),
                    buttons([("Request a Demo", DEMO, "solid"), ("Discuss a Partnership", DEMO, "ghost")]),
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
                        "integrated, or modernized — delivered by the team that builds our platforms.",
                        centered=True,
                    ),
                    spacer(12),
                    buttons([("Discuss a Project", DEMO, "solid"), ("See Our Products", "/governed-ai/", "ghost")]),
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
                            ("02", "Business applications", "Applications built around how the organization actually operates, rather than around what a package assumes."),
                            ("03", "Data platforms", "Data foundations, pipelines, and models that make enterprise information usable and trustworthy."),
                            ("04", "Integrations", "Connecting systems, services, and data so information moves reliably between them."),
                            ("05", "Applied AI", "AI capability built into software with the same governance, traceability, and oversight our platforms are designed around."),
                            ("06", "Modernization", "Bringing existing systems forward without discarding the business logic already proven in them."),
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
                    heading("Governance is not bolted on afterwards"),
                    lede(
                        "The same principles behind our products shape the software we build for others: "
                        "decisions are traceable, context is retained, AI operates inside defined boundaries, "
                        "and a person remains accountable for what ships."
                    ),
                    spacer(24),
                    checklist(
                        [
                            "Architecture decisions captured and retained",
                            "AI-assisted engineering under human oversight",
                            "Standards applied consistently across the codebase",
                            "Traceability from requirement to implementation",
                            "Security and access considered from the start",
                            "Knowledge that stays with your organization",
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
                        "Share the problem, the systems involved, and the outcome you need. We will tell you "
                        "honestly whether we are the right team for it.",
                        centered=True,
                    ),
                    spacer(12),
                    buttons([("Discuss a Project", DEMO, "solid")]),
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
                    h1("Request a Demonstration"),
                    lede(
                        "Explore how Aletheon Labs can help your organization use artificial intelligence "
                        "securely, consistently, and effectively across business intelligence and software "
                        "development.",
                        centered=True,
                    ),
                    spacer(12),
                    buttons([("Email contact@aletheonlabs.com", "mailto:contact@aletheonlabs.com", "solid")]),
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
                            ("01", "Platform Demonstration", "See Aletheon Intelligence or Aletheon Forge applied to a scenario that resembles your organization."),
                            ("02", "Governed AI Discussion", "Talk through the governed AI layer, how it would sit in your architecture, and what it would govern."),
                            ("03", "Partnership Inquiry", "Discuss partnership opportunities, strategic collaboration, or technology-enabled business innovation."),
                            ("04", "Research Collaboration", "Academic partnership or technical discussion of the research behind the platform."),
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
                            ("Step 01", "Share your goals", "Tell us what you are trying to solve, improve, or explore."),
                            ("Step 02", "Discuss opportunities", "We identify where governed AI creates meaningful value for your organization."),
                            ("Step 03", "Define the path forward", "We outline the right next steps based on your needs, data, systems, and desired outcomes."),
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
                    buttons([("Email contact@aletheonlabs.com", "mailto:contact@aletheonlabs.com", "solid")]),
                ]
            ),
            "is-hero",
        ),
    ]
)


# --------------------------------------------------------------------------

def main():
    os.makedirs(OUT, exist_ok=True)
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
        flag = "OK " if depth == 0 else "BAD"
        print(f"{flag} {slug:24s} {len(markup):6d} bytes  depth={depth}")


if __name__ == "__main__":
    main()
