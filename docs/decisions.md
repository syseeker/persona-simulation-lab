# Architecture Decisions

## 21 November 2026: Continue implementation through Scenarios 2 and 3

The user authorised finishing the redesigned guide, then implementing board games and retail learning without waiting for an intermediate reply. Keep verified rounds on `dev`, with `main` unchanged. Photography remains the regression baseline.

Board games reuses the same Fabric call sites and selects its maintained Hermes adapter; its compatible Python 3.14 dependencies and native Guardrails 0.24.1 are isolated from the application's Python 3.12/UserSim environment. For three known tools, turn off Hermes deferred tool discovery in its supported managed configuration. Keep the host gateway's exact qualified-function allowlist. Native Guardrails validation runs inside OpenShell using custom deterministic Colang actions, with native status/action/configuration receipts. Its narrow policy probe stays separate from the legitimate learning conversation. UserSim generates the follow-up after the preceding reply; its custom relevance hook explains why the design-versus-play clarification belongs to this test. Preserve native quality flags even when application assertions pass.

Each implemented scenario has one curated manifest-verified pack and companion. Never reuse another scenario's recording. New companions can record invocation-to-tool scope IDs actually captured by the application, while native model/gateway joins stay unavailable unless established. Preserve failed development conditions privately and describe material findings in the curated review note.

## 21 November 2026: Scenario-bound developer review architecture

Treat the learner as developer zero: the guide must support reviewing our own integration, not just introducing product names. One shared operation model drives Simplified, Detailed and the teaching panel across all 27 scenario/lesson combinations. Seven plain-language responsibilities remain distinct from nine numbered lessons. Important substeps expose design/ownership, input, configuration, output and a meaningful check; exact committed code/configuration and scenario/run-specific proof open outside the limited panel. Raw previews and run-history selection are removed from the teaching UI, while retained APIs stay compatible.

Step 1 verifies/displays the actual original and does not activate UserSim. Step 2 configures UserSim and distinguishes source traits, supplied situation and saved generated wording; the loop executes in Step 4. Relay attaches to the harness; accounting and native scope identities remain separate. Safeguards surround the advisor’s public boundaries; OpenShell encloses the workload with a distinct trusted supervisor; Helix evaluation and managed operations have separate responsibilities.

Photography uses one canonical demo. A separately hashed offline companion fills its configuration/lifecycle/result publication gaps without changing any immutable pack. Board games and retail learning keep no execution artifacts. Preserve explicit missing, planned, unused and not-called states. No scenario execution, deployment, SDK upgrade or Scenario 2/3 backend work is part of this review redesign.

## 20 November 2026: Publish completed rounds and fixed review evidence on dev

The user requested a `dev` branch from `main` in the existing GitHub repository, then a commit/push after each completed round so direct code links resolve. Keep `main` unchanged. Publish fixed sanitized scenario recordings with manifest hashes, GitHub log permalinks and verified in-app previews. Raw private runs/datasets/prompts/credentials stay ignored. Preserve earlier failed/reviewed photography attempts instead of replacing them with a success-only pack. Scenarios 2/3 remain illustrative until separately executed. Future live-log linking is deferred.

## 20 November 2026: Shared foundation and photography implementation

The user authorised implementation after the wireframe and requested a non-scrolling process chart. Migrate the accepted guide into repository `web/`, keeping its typography, styles, panel resizing and dataset browser. The latest requested chart uses an alternating numbered timeline with three phase bands and a vertical narrow-screen layout. A restricted guide worker, CLI and developer MCP share a versioned `JourneyService` alongside retained APIs. Photography is live; the other two scenarios stay illustrative.

Use standalone OpenShell 0.1.6 with one persistent Fabric/Deep Agents runtime and read-only course MCP. Build a reusable image from an allowlisted context with no profiles or credentials. Deliver only public learner context at invocation. The native exec control channel carries model requests to the host budget gateway; no broad host-ingress workaround, Helix service, external credential driver or per-persona image is introduced. Preserve pinned API/interpreter/Relay-path workarounds. Fabric's optional runtime base directory defaults unchanged for retained callers and uses writable `/workspace` in the sandbox.

Keep explicit source locking, per-condition identity, cross-process lease/guard, cancellation and exact-label/native-ID cleanup. Cancellation waits for creation to settle; ambiguous creation needs explicit recovery. Playback/source/log reads never execute models. Saved native bytes retain checksums; JavaScript projections preserve uint64 revisions as strings. Code links derive the user's repository and committed reference; unpublished code is labelled. Log links bind opaque artifacts to the selected local run. Explanatory stage flows and attributable saved requests are distinct.

The first real reply correctly cited the catalogue URL but omitted the internal course ID. An overly strict application assertion failed it. Preserve that run; correct the validator to accept exact catalogue URLs, add positive/negative regression cases and explicitly rerun the same locked input as a new condition. No historical result is rewritten. Response assertions use no Helix or judge inference; UserSim's native stop judges remain separately accounted for. See [verification](verification.md).

## 20 November 2026: Nine-stage wireframe and progressive presets

The accepted plan replaces the earlier seven-stage/all-components gate with nine generic journey stages and progressive capability presets. Keep one Simplified and one Detailed map; highlight relevant modules without changing the graph layout per scenario. Preserve unrelated styling and content. Stable stage IDs migrate the earlier seven saved meanings, including the separated build/run and safeguards stages.

Photography uses authored inputs, Deep Agents, fixed-model LiteLLM, Relay, application assertions and standalone OpenShell, with no Designer, Switchyard, native Guardrails or Helix. Board games adds Hermes, two-turn no-match persistence and a separate native Guardrails demonstration, still without Designer/routing/Helix. Retail learning adds Designer, routing comparison, Helix Evals and managed lifecycle/jobs over three public turns. Helix is a broader control plane, not an evaluation-only product.

At that wireframe gate, standalone launch and Guardrails were unimplemented and simulation was disabled. The subsequent implementation decision above adds standalone photography; Guardrails and the other scenario lifecycles remain future gates. Do not require Helix services for simpler presets or bake personas into images.

The user also authorised output housekeeping. Verify owning-host processes and open files, preserve live/unknown ownership, archive historical output with paths/hashes and recovery checks, then remove verified stale originals. Preserve source archives, datasets and environments. See [output policy](output-housekeeping.md); prior dated evidence is not relabelled.

## 20 November 2026: Freeze unrelated content and presentation

At the user's explicit request, each new change starts from the preceding version as a frozen baseline. Modify only the requested items and strictly necessary supporting code, tests and documentation. Preserve unrelated wording, fonts, colours, spacing, layout, navigation and behaviour; do not include unsolicited corrections or improvements. Separate visible content/design changes require agreement. Retain a recoverable baseline and review the final diff for scope.

The naming update keeps **Building Citizen Apps with NeMo**, its requested subtitle, the requested step labels and dataset/documentation link changes. Its additional header styling, prerequisites rewrite and unrelated explanatory additions were reverted. Restore UserSim documentation coverage rather than dropping the component because it publishes documentation in its upstream repository.

## Guide identity and learning links

Use **Building Citizen Apps with NeMo** and **NeMo Stack Integration Guide · Singapore**. The nine current stage names and scenario allocations are defined in the [plan](../PLAN.md); do not keep a competing seven-stage specification in active documentation.

Keep **Locate in the Map** as internal navigation. Adjacent learning links open actual dataset distributions or current official package documentation. The UserSim link uses its upstream README. Pinned API/source references remain in the code inspector and compatibility record; current documentation is not evidence of an adapter upgrade. Historical archives, package identifiers and saved browser keys keep their identities.

## 19 November 2026: Inspect schemas and installed original profiles separately

At the user's request, Datasets has **Data schema** and **Explore profiles** subtabs. Preserve the existing schema/audit content, adding human labels and groups ordered as names/identity, personal details, location, education/work, skills/interests, narratives and OCEAN. This changes presentation, not physical column names, types or original values.

Explore profiles is an authorised exception to the otherwise illustrative guide: it reads installed originals through the retained worker/shared Python dataset services. Keep the connection narrow and read-only, with source-aware geography, text/age/education filtering, source-wide facet counts, bounded pages and original row/revision/hash inspection. Load neither a bundled full corpus nor invented fallback rows. Store filters/subtab choice, not raw profiles, in browser preferences. Display a clear unavailable state when configuration/source readiness fails. Operator `LAB_ROOT` configuration stays server-only; browser queries cannot choose paths or worker methods. No model, Designer, simulation or deployment operation follows from browsing.

## Retained runtime and evidence boundaries

The checkout retains SvelteKit, persistent Python workers, shared CLI/developer-MCP services and compatible isolated SDK environments. The accepted guide now replaces the inert landing page; the superseded dashboard remains archived. Photography connects the new restricted guide boundary; the dataset reader remains independently read-only.

Application assertions, native Relay observations, role-labelled gateway accounting, Helix Evals, behavioural Guardrails and native OpenShell enforcement are distinct evidence. Missing correlations, failed answers and unknown usage remain visible. Current source excerpts do not establish the code revision of a recording. See [contracts](contracts.md) and [compatibility](sources.md) before adapter changes.

HF and Singapore NGC Extended remain separate distributions. Preserve immutable originals, exact source identities/hashes and traceable derived rows; generated salary/brand hypotheses never establish behaviour, citizenship or eligibility. Harness comparisons keep the model fixed; routing comparisons keep the harness and public inputs fixed with an explicitly controlled candidate pool.

Preserve the tested Fabric tool-schema boundary, generated Relay path and interpreter setup. Keep UserSim, Designer, Hermes, local Helix and Platform environments separate. Do not enable the unsupported historical external-credential-driver callback or install the rejected research adapter. The official OpenShell credential store, native-policy evidence and historical Docker ingress limitation remain separate reference paths. See [pinned workarounds](sources.md#compatibility-workarounds).

## Historical decisions

The [consolidated 19–20 November review journal](history/guide-reviews-2026-11-19-20.md) preserves the earlier seven-stage plan, naming/freeze changes and dated dataset/verification decisions. It is superseded for current journey sequencing. The immutable [v0.2](history/v0.2/INDEX.md) and [v0.1](history/v0.1/INDEX.md) archives preserve their original designs and findings. Historical runs are not current service readiness or acceptance of the replacement UI.
