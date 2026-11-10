"""Render the implemented architecture as dependency-free, editable SVG diagrams."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/diagrams"


def node(x, y, w, h, title, lines, accent=False):
    return {"x": x, "y": y, "w": w, "h": h, "title": title, "lines": lines, "accent": accent}


def edge(points, label="", x=0, y=0):
    return {"points": points, "label": label, "x": x, "y": y}


GRAPHS = [
    {
        "file": "system-context",
        "title": "01 / System Context",
        "subtitle": "Singapore Learning & Classes Advisor | implemented local application",
        "width": 1500,
        "height": 900,
        "nodes": [
            node(
                55,
                165,
                280,
                125,
                "Learner",
                ["SvelteKit browser or CLI", "Explore classes and inspect tests"],
            ),
            node(
                470,
                165,
                500,
                160,
                "Learning Lab",
                [
                    "SvelteKit Node server and Python worker",
                    "Deep Agents or Fabric advisor runtime",
                    "UserSim experiment coordinator",
                ],
                True,
            ),
            node(
                1120,
                165,
                325,
                160,
                "NVIDIA NIM",
                [
                    "Advisor: Nemotron Lightning",
                    "Other roles: Nemotron Nano Omni",
                    "Hosted inference with a local API key",
                ],
            ),
            node(
                55,
                460,
                320,
                170,
                "Local Inputs",
                [
                    "Audited Singapore HF profiles",
                    "NGC Extended path: setup required",
                    "Data Designer preference hypotheses",
                    "Official course snapshot",
                ],
            ),
            node(
                470,
                460,
                500,
                170,
                "Boundaries",
                [
                    "Read-only course MCP tools",
                    "120-call budget per experiment",
                    "Fresh target memory per condition",
                    "Original profiles preserved",
                ],
                True,
            ),
            node(
                1120,
                460,
                325,
                170,
                "Evidence",
                [
                    "Relay agent / model / tool scopes",
                    "Local run events and usage ledger",
                    "Helix scoring of saved replies",
                    "Frozen inputs for paired comparisons",
                ],
            ),
        ],
        "edges": [
            edge([(335, 228), (470, 228)], "Ask / inspect", 351, 207),
            edge([(970, 228), (1120, 228)], "Budget gateway", 984, 207),
            edge([(375, 545), (470, 545)], "Facts", 393, 525),
            edge([(720, 325), (720, 460)], "Enforced by worker", 743, 394),
            edge([(970, 545), (1120, 545)], "Save / score", 991, 525),
        ],
        "footer": "Local-only application and artifacts. No booking, payment or Platform deployment.",
    },
    {
        "file": "runtime-components",
        "title": "02 / Runtime Components",
        "subtitle": "One application service shared by the web worker and CLI",
        "width": 1500,
        "height": 1050,
        "nodes": [
            node(
                55,
                155,
                300,
                125,
                "SvelteKit",
                ["Browser UI and Node server routes", "Lazy persistent child worker"],
            ),
            node(
                525,
                155,
                450,
                125,
                "Python LabService",
                ["Versioned JSON-lines messages with IDs", "Workload lock, cancellation and run state"],
                True,
            ),
            node(1145, 155, 300, 125, "CLI", ["Same application service", "Explicit offline / live modes"]),
            node(
                55,
                435,
                300,
                170,
                "UserSim External Runtime",
                [
                    "Immutable resolved profile input",
                    "User / assistant / judge activations",
                    "Native outcomes and warnings",
                ],
            ),
            node(
                525,
                420,
                450,
                190,
                "Advisor Target",
                [
                    "Direct Deep Agents or Fabric adapter",
                    "One conversation per memory workspace",
                    "Read-only tools and runtime skill",
                    "Native Relay instrumentation",
                ],
                True,
            ),
            node(
                1145,
                435,
                300,
                170,
                "Course MCP",
                [
                    "Search / details / compare",
                    "Explicit constraints bound by host",
                    "Frozen official catalogue",
                ],
            ),
            node(
                55,
                765,
                300,
                150,
                "Isolated SDK Environments",
                [
                    "Helix: exact-match local evaluation",
                    "Data Designer 0.10: overlays",
                    "Separate locks for compatibility",
                ],
            ),
            node(
                525,
                765,
                450,
                150,
                "Inference Gateway",
                [
                    "Counts all roles, judges and failures",
                    "1,024 output tokens; retries disabled",
                    "NVIDIA key remains server-side",
                ],
                True,
            ),
            node(
                1145,
                765,
                300,
                150,
                "Hosted NIM",
                ["OpenAI-compatible endpoint", "Configured model per role", "Measured provider usage"],
            ),
        ],
        "edges": [
            edge([(355, 218), (525, 218)], "JSON-lines", 391, 196),
            edge([(1145, 218), (975, 218)], "Python calls", 998, 196),
            edge([(675, 280), (675, 420)], "Own lifecycle", 698, 350),
            edge([(525, 250), (420, 250), (420, 385), (205, 385), (205, 435)], "Simulate", 238, 364),
            edge([(975, 515), (1145, 515)], "MCP stdio", 1009, 494),
            edge([(750, 610), (750, 765)], "Target requests", 774, 700),
            edge([(205, 605), (205, 683), (525, 683), (525, 815)], "Other role requests", 265, 661),
            edge([(975, 838), (1145, 838)], "Bounded HTTPS", 998, 815),
        ],
        "footer": "Relay observes advisor work. The gateway ledger counts the complete experiment.",
    },
    {
        "file": "episode-sequence",
        "title": "03 / One Paired Experiment",
        "subtitle": "Exact inputs, isolated target state, preserved execution failures",
        "width": 1500,
        "height": 1030,
        "nodes": [
            node(
                70,
                155,
                1360,
                125,
                "1. Freeze Inputs",
                [
                    "Resolve the source profile and UserSim preamble once. Save model identities and catalogue hash.",
                    "Reuse the exact rows for both advisor strategies; keep preference overlays labelled.",
                ],
                True,
            ),
            node(
                70,
                340,
                1360,
                135,
                "2. Start A Fresh Condition",
                [
                    "Create an isolated Deep Agents or Fabric runtime, memory workspace and MCP session.",
                    "Select concise or clarification-first policy; enable Relay once.",
                ],
            ),
            node(
                70,
                535,
                650,
                170,
                "3a. User / Judge / Summary Activation",
                [
                    "Forward exact UserSim role messages to the gateway.",
                    "Admit each provider call against the shared budget.",
                    "Record the response and measured token usage.",
                ],
            ),
            node(
                780,
                535,
                650,
                170,
                "3b. Advisor Activation",
                [
                    "Send only the latest public learner message to target.",
                    "Target performs real MCP lookups and bounded inference.",
                    "Return the final public reply to UserSim.",
                ],
            ),
            node(
                70,
                770,
                1360,
                140,
                "4. Finalize And Inspect",
                [
                    "Continue up to three conversation turns; preserve partial outputs, failures and native warnings.",
                    "Save the usage ledger and trace evidence. Score saved replies through the local Helix SDK.",
                ],
                True,
            ),
        ],
        "edges": [
            edge([(750, 280), (750, 340)]),
            edge([(395, 475), (395, 535)]),
            edge([(1105, 475), (1105, 535)]),
            edge([(395, 705), (395, 770)]),
            edge([(1105, 705), (1105, 770)]),
        ],
        "footer": "Repeat activation 3 within the bounded loop, then repeat steps 2–4 for the paired strategy.",
    },
]


def render(graph):
    width, height = graph["width"], graph["height"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9" fill="none" stroke="#738879" stroke-width="1.3"/></marker></defs>',
        '<rect width="100%" height="100%" fill="#f8faf6"/>',
        '<g font-family="Arial, sans-serif">',
        f'<text x="55" y="65" font-size="31" font-weight="700" fill="#193e31">{escape(graph["title"])}</text>',
        f'<text x="55" y="102" font-size="17" fill="#62766a">{escape(graph["subtitle"])}</text>',
    ]
    for item in graph["edges"]:
        points = " ".join(f"{x},{y}" for x, y in item["points"])
        parts.append(
            f'<polyline points="{points}" fill="none" stroke="#738879" stroke-width="2" marker-end="url(#arrow)"/>'
        )
        if item["label"]:
            parts.append(
                f'<text x="{item["x"]}" y="{item["y"]}" font-size="15" fill="#62766a">{escape(item["label"])}</text>'
            )
    for item in graph["nodes"]:
        x, y, w, h = (item[k] for k in ["x", "y", "w", "h"])
        fill = "#eaf3e5" if item["accent"] else "#ffffff"
        parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="#d5e1d0" stroke-width="1.5"/>'
        )
        parts.append(
            f'<text x="{x + 22}" y="{y + 36}" font-size="21" font-weight="700" fill="#1b4937">{escape(item["title"])}</text>'
        )
        for i, line in enumerate(item["lines"]):
            parts.append(
                f'<text x="{x + 22}" y="{y + 69 + i * 25}" font-size="16" fill="#52695b">{escape(line)}</text>'
            )
    parts.append(
        f'<text x="55" y="{height - 40}" font-size="16" fill="#687d6e">{escape(graph["footer"])}</text></g></svg>'
    )
    return "\n".join(parts)


if __name__ == "__main__":
    DEST.mkdir(parents=True, exist_ok=True)
    archive = ROOT / ".private/pre-implementation/docs/diagrams"
    archive.mkdir(parents=True, exist_ok=True)
    for path in DEST.iterdir():
        if path.suffix in {".png", ".json"} and not (archive / path.name).exists():
            (archive / path.name).write_bytes(path.read_bytes())
    (DEST / "diagram-data.json").write_text(json.dumps({"status": "implemented", "graphs": GRAPHS}, indent=2))
    for graph in GRAPHS:
        (DEST / f"{graph['file']}.svg").write_text(render(graph))
    print("Rendered three editable SVG diagrams.")
