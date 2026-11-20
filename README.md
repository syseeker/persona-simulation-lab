# Building Citizen Apps with NeMo

*NeMo Stack Integration Guide · Singapore*

## North Star

Teach developers how to build a citizen-focused AI application with country-specific Nemotron Personas and the NVIDIA NeMo stack. **The product is the integration lesson:** follow one citizen request, understand each component’s responsibility, and connect behaviour to application code and attributable evidence.

Singapore learning and community activities are the concrete example. Isolated SDK snippets do not explain how personas, simulation, harnesses, tools, model routing, tracing, evaluation and deployment fit together. The [canonical project goals](docs/project-goals.md) remain the source of truth.

## Current review gate

The Integration Guide now runs in this checkout's **SvelteKit application**. It has four tabs: **Why NeMo Stack**, **Integration Map**, **Q&A** and **Datasets**. Datasets retains **Data schema** and the read-only **Explore profiles** browser for installed HF and Singapore NGC originals. The default is **Trace a Request → Find a photography class**. One scenario selector supplies a fixed preset; setup can be collapsed to focus on the walkthrough. The nine-step process chart uses an alternating timeline with three phase bands without horizontal scrolling.

**Photography is connected; scenarios 2 and 3 remain illustrative.** Trace prefers an available completed photography run; otherwise it displays an explicitly labelled illustration. **Simulate a Session** opens photography prerequisites, original-persona selection and a separate start action. It runs one real UserSim turn against Fabric/Deep Agents and read-only course tools inside a fresh native OpenShell sandbox. Inspect its public response, Relay records, role-labelled model ledger, application assertions, effective policy and cleanup receipt. Playback and inspection start no inference. See the [dated verification](docs/verification.md) for actual results and limitations.

The three presets teach distinct lessons:

- **Find a photography class:** one public turn with Fabric/Deep Agents and a fixed model through LiteLLM. Use the authored beginner/Saturday/S$50 situation, preserve unknown material fees, and skip Designer, Switchyard, native Guardrails and Helix. Standalone OpenShell is the implemented execution boundary.
- **Learn to play board games:** two public turns with Fabric/Hermes and a fixed model through LiteLLM; skip Designer generation and dynamic routing. After the catalogue no-match, “Is video-game design the same as playing board games?” tests scope explanation without an invented listing or substituted learning goal. A separate native Guardrails test introduces behavioural controls; Helix is omitted and OpenShell is standalone.
- **Build skills for my dream job:** three public turns with Fabric/Deep Agents, hypothetical brand/salary columns assigned to Data Designer, and dynamic Switchyard routing through LiteLLM. A UNIQLO or Decathlon ambition motivates learning; salary is disclosed only in turn 2, then an explicit training budget and weekend/shorter preferences in turn 3. Helix evaluation, explicit jobs and managed OpenShell operations are introduced here. This is a learning advisor, not a job site.

All three retain nine teaching-stage slots: persona, situation, build/connect, run, investigate, evaluate, route, safeguards and deployment. The first two presets use application assertions without Helix. Designer, native routing and Helix are assigned to retail learning; native Guardrails starts with board games. Only photography is executable in the guide today. Saved-record request attribution is distinct from explanatory stage animation. Controlled comparisons require common inputs and explicitly named conditions.

Read the [current walkthrough](docs/learning-guide.md) and [implementation gates](PLAN.md). The integrated v0.2 UI and its evidence are preserved in the [recovery archive](docs/history/v0.2/INDEX.md); they are not the current guide.

## Run locally

The guide requires Node.js 22.17 or newer, npm, Python 3.12 and the project-local uv environment:

```bash
npm --prefix web ci
uv sync --locked
npm --prefix web run dev
```

Open the local URL printed by Vite. Entry reads saved photography metadata; it does not start a workload. Illustrations work without recordings. Dataset browsing needs installed originals. Actual photography also needs configured LiteLLM aliases, a reachable native OpenShell gateway and the reusable image described in [standalone setup](integrations/openshell/README.md). Missing prerequisites remain visible.

## Retained backend and developer entry points

The new [JourneyService](src/learning_lab/journey.py) is shared by the guide's restricted persistent worker, `learning-lab guide` CLI and host-only developer MCP. It preserves the retained service APIs and [read-only dataset boundary](web/src/lib/server/datasetReader.ts). See the [architecture and source map](docs/architecture.md#integration-entry-points), [backend contracts](docs/contracts.md) and [pinned compatibility notes](docs/sources.md).

Backend setup uses Python 3.12 and uv; isolated adapters retain their own version requirements:

```bash
uv sync --locked
uv sync --project integrations/helix --locked
uv sync --project integrations/designer --locked
uv run learning-lab --help
```

CLI inspection and orchestration share application services. The host-only `learning-lab-developer-mcp` is a developer-control surface; it must never become an advisor runtime tool. Starting live generation, inference, deployment or sandbox operations requires a separate explicit action within the authorised task.

Use `uv run learning-lab guide status`, `guide runs` and `guide trace RUN_ID` for inspection. A CLI `guide start SOURCE_ID ORIGINAL_SHA256 --source ngc` explicitly runs and awaits its own photography condition. It cannot cancel a run owned by the web worker. Closing a UI panel never cancels that worker's run.

Completed rounds are committed and pushed to **`dev`**, leaving `main` unchanged. The [fixed recording packs](recordings/README.md) provide scenario-specific GitHub log links and verified in-app previews after cloning. Photography includes the successful review condition and preserved earlier findings; scenarios 2/3 have no executed packs. Only sanitized public projections are published. Future live-log linking is deferred.

Preserve an existing `.env`; [.env.example](.env.example) documents configuration. Dataset installation is required for Explore profiles; schema and scenario illustrations remain available without it. Original Parquet files stay in ignored local storage, outside Git. The retained [persona services](docs/personas.md) distinguish public HF profiles from **Singapore NGC Extended only**; missing Extended data must not be replaced silently.

## Evidence and limits

The [active verification record](docs/verification.md) describes housekeeping and links the immutable historical results. Past test counts, live replies and sandbox receipts are not current service-health claims or acceptance of the new guide.

Retained backend limits include three public conversation turns, four tool rounds per advisor reply, a 120-call workload cap and 1,024 output tokens per call. Preserve failed replies, warnings, incomplete traces and unknown usage. Course snapshots are dated; unknown fees, seats and personal funding eligibility remain unknown. The application cannot book, pay, verify vacancies or guarantee employment or salary outcomes.

Original persona records and generated hypotheses retain separate provenance. Keep `.env`, `.private/`, datasets, generated rows, transcripts and traces out of Git. Superseded local output is kept in verified private archives; see [housekeeping and recovery](docs/output-housekeeping.md). Code is [MIT licensed](LICENSE); datasets and dependencies have their own terms. See [attribution](NOTICE.md).

## Development checks

```bash
uv run pytest -q
uv run ruff check src tests scripts integrations
uv run python scripts/check_docs.py
python3 scripts/check_archive.py
npm --prefix web run check
npm --prefix web test
npm --prefix web run test:e2e
npm --prefix web run build
```

Offline tests cover retained services and guide contracts; browser fixtures are labelled separately from actual SDK execution in [verification](docs/verification.md). Consult [decisions](docs/decisions.md), [agent guidance](AGENTS.md) and the [coaching skill](.agents/skills/persona-lab-coach/SKILL.md) before extending the application.
