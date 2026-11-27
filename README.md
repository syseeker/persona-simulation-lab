# Building Citizen Apps with NeMo

**v0.3.0 · Developer review.** The first page displays the application version at
the top right. The nine existing lesson titles are preserved; the bodies explain
the same integrations in connected, plain English. Execution inspection now has a
condition-scoped in-app viewer and a separate local Phoenix historical viewer.
See the [v0.3 walkthrough](docs/learning-guide.md#v030-review-flow--27-november-2026)
and [local Phoenix setup](integrations/observability/README.md).

*NeMo Stack Integration Guide · Singapore*

## North Star

Teach developers how to build a citizen-focused AI application with country-specific Nemotron Personas and the NVIDIA NeMo stack. **The product is the integration lesson:** follow one citizen request, understand each component’s responsibility, and connect behaviour to application code and attributable evidence.

Singapore learning and community activities are the concrete example. Isolated SDK snippets do not explain how personas, simulation, harnesses, tools, model routing, tracing, evaluation and deployment fit together. The [canonical project goals](docs/project-goals.md) remain the source of truth.

## Current review gate

The [master plan and delivery ledger](PLAN.md) track the verified scenario recordings and developer review of the [teaching UX revision](docs/ux-review-spec.md) and [scenario-aware artifact inventory](docs/configuration-evidence-inventory.md). The redesigned teaching panel and Metadata tab are implemented with separate, complete capture packs for all three selected demos. Developer review of the resulting UI, code, configuration and evidence remains the next gate. Chat summaries do not replace the saved detailed specifications.

The Integration Guide runs in this checkout's **SvelteKit application**. It has five tabs: **Why NeMo Stack**, **Integration Map**, **Q&A**, **Datasets** and **Metadata**. Datasets retains **Data schema** and the read-only **Explore profiles** browser for installed HF and Singapore NGC originals. The default is **Trace a Request → Find a photography class**. One scenario selector supplies a fixed preset; its summary can be collapsed to focus on the walkthrough. The nine-step process chart uses an alternating timeline with three phase bands without horizontal scrolling.

**All three scenarios have their own execution evidence.** Trace uses one explicitly selected recording per scenario, never a latest-run fallback. Missing evidence remains unavailable. **Simulate a Session** opens prerequisites, original-persona selection and a separate start action. Photography runs one UserSim turn with Fabric/Deep Agents; board games runs two with Fabric/Hermes and native Guardrails. Retail learning adds three public turns, source-seeded Designer generation with a completed native profiling report, native Helix evaluation/jobs, verified MiniMax/Mistral fixed/routed comparisons and a separate Helix-managed OpenShell session. Its salary-only second reply is an application clarification with zero advisor inference; native Fabric runs on public turns 1 and 3. Earlier Gemma/GLM failures and separate Nemotron diagnostics remain distinct historical evidence. Playback and inspection start no inference. See the [selected demos and capture coverage](docs/configuration-evidence-inventory.md#current-demos-and-location-keys) and [dated verification](docs/verification.md).

The three presets teach distinct lessons:

- **Find a photography class:** one public turn with Fabric/Deep Agents and a fixed model through LiteLLM. Use the authored beginner/Saturday/S$50 situation, preserve unknown material fees, and skip Designer, Switchyard, native Guardrails and Helix. Standalone OpenShell is the implemented execution boundary.
- **Learn to play board games:** two public turns with Fabric/Hermes and a fixed model through LiteLLM; skip Designer generation and dynamic routing. After the catalogue no-match, “Is video-game design the same as playing board games?” tests scope explanation without an invented listing or substituted learning goal. A separate native Guardrails test introduces behavioural controls; Helix is omitted and OpenShell is standalone.
- **Build skills for my dream job:** three public turns with Fabric/Deep Agents and source-seeded Designer brand/salary hypotheses. The fixed Nemotron baseline is followed by explicitly named Switchyard/LiteLLM comparisons. Salary is disclosed only in turn 2; an explicit S$3,000 total budget and weekend/shorter preferences arrive in turn 3. The real SMU example is S$20,928 over three months. Helix scores saved criteria, runs a durable evaluation job and manages a new public-context OpenShell session. A brand ambition motivates learning; it establishes neither employer requirements nor job outcomes. See [retail integration](docs/retail-integration.md).

All three retain nine teaching-stage slots: persona, situation, build/connect, run, investigate, evaluate, route, safeguards and deployment. The map shows one architecture at two levels: seven plain-language responsibilities in Simplified, and the corresponding library operations in Detailed. Lessons explain how components cooperate; conceptual blocks/actions and technical library/operation pages each own a distinct explanation. Purposeful links sit beside the explanation they support. Calling code opens the committed symbol, settings open the relevant capture, and results belong to the selected scenario and condition. Library architecture references live at library pages. Raw JSON previews, repeated checklists and circular teaching links are absent. Scenario choice stays visible when its summary is collapsed. Only explicit lesson/operation interaction dims the map; entering or resetting it shows the whole architecture. Saved-record attribution remains distinct from explanatory animation, and controlled comparisons require common inputs and explicitly named conditions.

**Metadata** shows **Module · Steps · YAML/JSON file · Status · Location · Apply to scenario**, with scenario/condition selection and module/file/status search. It uses the same capture requirement IDs as teaching references and validates the selected pack's hashes and identities. It separates retained private originals, public projections, missing files and unused integrations from execution success. Old packs without a capture inventory show unavailable rather than borrowing a newer run. New exports do not change the demo selection; see the [current demo keys](docs/configuration-evidence-inventory.md#current-demos-and-location-keys).

Read the [current walkthrough](docs/learning-guide.md) and [implementation gates](PLAN.md). The integrated v0.2 UI and its evidence are preserved in the [recovery archive](docs/history/v0.2/INDEX.md); they are not the current guide.

## Run locally

The guide requires Node.js 22.17 or newer, npm, Python 3.12 and the project-local uv environment:

```bash
npm --prefix web ci
uv sync --locked
npm --prefix web run dev
```

Open the local URL printed by Vite. Entry reads the curated demo and resolves its original profile by distribution, revision and recorded hash; it does not start a workload. An absent original or recording stays unavailable. Planned lessons work without recordings. Dataset browsing needs installed originals. Actual photography also needs configured LiteLLM aliases, a reachable native OpenShell gateway and the reusable image described in [standalone setup](integrations/openshell/README.md). Missing prerequisites remain visible.

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

Use `uv run learning-lab guide status`, `guide runs --scenario boardgames` and `guide trace RUN_ID` for inspection. A CLI `guide start SOURCE_ID ORIGINAL_SHA256 --source ngc --scenario photography|boardgames|dreamjob` explicitly runs and awaits its own condition; omit `--scenario` for photography. It cannot cancel a run owned by the web worker. Closing a UI panel never cancels that worker's run. Retail execution additionally requires the isolated Designer/Helix environments, requested-pool proxy and managed images described in [retail setup](docs/retail-integration.md#explicit-setup-and-execution).

Completed rounds are committed and pushed to **`dev`**, leaving `main` unchanged. The [fixed recording packs](recordings/README.md) provide scenario-specific GitHub log links after cloning; the teaching panel interprets selected proof facts with purposeful expandable execution details in v0.3.0. The selected demos retain their own configuration, native records and cleanup evidence, including the board-games helpfulness warning. Earlier failed conditions remain preserved separately. Only sanitized public projections are published. Future live-log linking is deferred.

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
