# Singapore Citizen Application Learning Lab

## North Star

Teach developers how to build a citizen-focused AI application with country-specific Nemotron Personas and the NVIDIA NeMo stack. **The product is the integration lesson:** a developer should demonstrate one citizen story in the UI, understand the responsibility of each component, and follow actual behaviour into source code, configuration and native logs.

Singapore learning and community activities provide a concrete application. This repository exists because isolated SDK snippets do not explain how personas, simulation, agent harnesses, inference routing, observability, evaluation and deployment work together. Read the [agreed project goals](docs/project-goals.md) before extending it.

The walkthrough uses Singapore Nemotron Personas, NeMo UserSim, Data Designer, Relay, Fabric, Switchyard with LiteLLM, and Helix, with LangChain Deep Agents and Hermes harnesses and an OpenShell deployment boundary. **An implemented integration path is not proof that its external service is running.** The UI reports readiness; the [verification record](docs/verification.md) separates offline checks, recorded live results and current limitations.

## Run locally

Requires Python 3.12, uv, a supported Node.js release at least 22.17, and npm. Additional integration environments have their own Python/version requirements.

```bash
uv sync --locked
uv sync --project integrations/helix --locked
uv sync --project integrations/designer --locked
npm --prefix web ci
npm --prefix web run dev
```

Open the local URL printed by Vite. Startup makes no inference calls. **Offline demo** uses scripted model responses through the actual harness and course MCP tools; it does not generate realistic persona conversations. Preserve an existing `.env`; otherwise copy [.env.example](.env.example) and configure local credentials for explicit live operations.

To install and audit the pinned public Singapore dataset:

```bash
uv run python scripts/inspect_personas.py --download
```

This downloads approximately 275 MB, audits all 148,000 records and retains a small diagnostic panel. The data workbench samples the full local corpus. Public HF profiles have no OCEAN fields. **Singapore NGC Extended** is a separate distribution requiring its own installed assets/access; this application does not browse all NGC assets or substitute HF records for unavailable Extended data.

## Follow one story

Use the **Guided walkthrough** workspace for the main demonstration. Start with one persona and one condition. Carry its saved run through conversation, source inputs, UserSim activations, Relay scopes, runtime lifecycle, model calls, Helix criteria and artifacts. Inspecting saved evidence makes no model calls.

Three distinct application lessons are available: a sourced Saturday photography recommendation within S$50, baking with known material costs, and an honest no-match response for board games. Changing the baking budget from S$120 to S$130 is a purposeful comparison. Changing a harness, prompt or scenario starts a new condition; advancing the inspector does not.

The **data workbench** lets a developer inspect and select original source rows, sample and lock profiles, and run source-seeded Data Designer generation. Add typed hypothetical fields such as last drawn gross monthly salary in SGD or favourite brands; generate learning scenarios or additional synthetic profiles. Original records, overlays and new generated identities retain separate provenance. Generation uses actual LLM calls and explicit budgets; browsing uses none.

The free advisor and advanced simulation controls remain useful for exploration. The [learning guide](docs/learning-guide.md) describes the UI journey and [integration source map](docs/architecture.md#integration-entry-points) points to the backend. In-app source references show current local excerpts and repository locations.

The deployment lesson can explicitly prepare a new managed condition from a saved episode's first public learner input and original structured preferences. Preparation makes no model or Platform calls. Source run/episode identities remain inspectable; previous conversation memory and hidden persona fields are not copied. The deployed image has its own catalogue and configuration. A story that differs from OpenShell's frozen preset is flagged rather than silently replaced.

## Understand the stack

- **Personas and UserSim:** synthetic country context plus an explicit conversation/activation lifecycle; profiles do not prove citizenship or entitlement.
- **Data Designer:** source-seeded generation with closed schemas, immutable originals and traceable derived rows.
- **Deep Agents or Hermes:** the advisor harness. Fabric manages the selected supported harness runtime; comparisons keep the model fixed.
- **Relay:** native agent/model/tool evidence. The experiment event log and gateway ledger also include simulator and evaluation roles.
- **Switchyard and LiteLLM:** routing policy and a configurable provider proxy for NIM, Brev OpenAI-compatible endpoints or frontier APIs. Configuration presence alone is not a routing trace.
- **Helix:** inspectable local SDK evaluation and separate explicit Platform operations. Platform hosting and inference hosting are independent choices.
- **OpenShell:** a native sandbox boundary for the deployed agent and its course tools, demonstrated with a hash-checked public photography/S$50/Saturday preset. The separate Docker profile implements authenticated changing session preferences; live invocation remains blocked by host ingress on the recorded machine. A policy file or installed CLI alone does not prove enforcement.

See [architecture](docs/architecture.md), [contracts](docs/contracts.md), [sources and compatibility](docs/sources.md), [current plan](PLAN.md) and [decisions](docs/decisions.md). 

## Developer entry points

UI, CLI and the host-only developer MCP service share application services. Use `uv run learning-lab --help` for commands such as `stories`, `datasets`, `personas browse`, `personas sample`, `evidence`, `artifact`, `source`, `workbench` and `platform`. Start `uv run learning-lab-developer-mcp` for the developer-control MCP surface; never register it among the advisor's course tools.

Read-only inspection does not invoke a model. Workbench starts and Platform mutations are explicit commands. A standalone CLI process cannot cancel a task owned by an already-running web worker; use that worker's UI/MCP lifecycle for cancellation. The [contracts](docs/contracts.md) describe the shared boundaries.

## Data and limits

Course facts are dated official snapshots, not a live catalogue. Unknown fees, schedules and eligibility remain unknown. The advisor cannot book, pay or establish funding entitlement. Synthetic salary and brand preferences are hypotheses rather than observations; source descriptions and model outputs cannot authorize tools.

Runs and generation jobs have a 120-call ceiling. Calls have at most 1,024 output tokens; simulations have at most three public conversation turns and four tool rounds per advisor reply. Preserve failed answers, partial runs, UserSim warnings and unknown usage. Small diagnostic scores do not estimate human demand or behaviour.

Credentials, raw datasets, generated profiles, conversations and traces remain in ignored local directories. Application code is [MIT licensed](LICENSE); datasets and dependencies retain their own licenses. See [attribution](NOTICE.md) and [persona provenance](docs/personas.md).

## Development

```bash
uv run pytest -q
uv run ruff check src tests scripts integrations
uv run python scripts/check_docs.py
npm --prefix web run check
npm --prefix web test
npm --prefix web run test:e2e
npm --prefix web run build
```

Browser tests require Chromium. Offline tests use actual local SDKs and clearly labelled local provider fixtures where applicable; they do not establish external-service readiness. Live acceptance must be requested explicitly and recorded against the current code/environment. [Agent guidance](AGENTS.md) and the [coaching skill](.agents/skills/persona-lab-coach/SKILL.md) keep future work aligned with the North Star.
