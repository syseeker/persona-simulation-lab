# Configuration and evidence inventory

This is the supporting specification for **Workstream 1 (execution fixes and complete capture)** and **Workstream 3 (Metadata)** in the [authoritative plan](../PLAN.md). The current selected demos and their capture manifests are indexed below. The original **22 November 2026** audit at baseline **`19b26b8`** remains separately labelled, with its historical EXISTS/PRIVATE/NOT EXIST findings preserved. A documentation update or new export does not itself rerun a scenario or establish a successful result.

The learner should be able to follow a decision from application code to effective library settings and then to an attributable result. Some libraries consume Python objects, not YAML/JSON files. Do not invent a mandatory YAML file merely to populate a table. Retain actual authored inputs, generated settings, native results and useful application projections, and identify which role each plays.

**Implementation amendment, 22 November:** the 51 stable requirements below remain the baseline audit. The active registry and capture rules add retail application presentation artifacts under **CAP-FAB-07** (standalone baseline/comparisons) and **CAP-PLAT-05** (managed caller): generated `retail-response-config.json`, `retail-response-decisions.jsonl` and private `retail-model-proposals.jsonl`. They distinguish validated candidates, confirmed public delivery and original native proposals. Public projections expose response origin, source hashes and selected proposal-rule failures; original unpresented prose stays private. Their presence alone does not establish successful execution.

**Teaching and Metadata implementation, 22 November:** [the capture registry](../src/learning_lab/capture_registry.json) and [capture rules](../src/learning_lab/captures.py) supply the shared requirement IDs. [The read-only Metadata resolver](../src/learning_lab/guide_metadata.py) verifies the selected public capture pack; [Metadata](../web/src/lib/MetadataPage.svelte) renders the requested six columns with scenario/condition filters and module/file/status search. Inline teaching references use that same response. Distinct lesson, conceptual and technical destinations explain the purpose of each link instead of repeating a link checklist. All three selected demos have complete public capture inventories; a historical pack without an inventory remains explicitly unavailable rather than borrowing a new run's files or inferring that its private originals are missing.

## Current demos and location keys

The selected replacement demos completed their scenario checks and applicable capture requirements. Each link identifies the exact scenario/run; separate baseline, comparison and managed conditions retain their own settings and results. The Metadata tab and teaching links resolve the public capture manifests below.

| Scenario | Selected demo run | Published recording | Teaching companion | Configuration and evidence captures |
|---|---|---|---|---|
| **S1 — Photography** | `94e49df8-7dfa-445b-9614-d79e31f2c024` | [Recording](../recordings/photography/94e49df8-7dfa-445b-9614-d79e31f2c024/manifest.json) | [Companion](../recordings/guide-context/photography/94e49df8-7dfa-445b-9614-d79e31f2c024/manifest.json) | [28/28 applicable requirements](../recordings/captures/photography/94e49df8-7dfa-445b-9614-d79e31f2c024/manifest.json) |
| **S2 — Board games** | `aa445222-7127-41f0-a451-685874bf343c` | [Recording](../recordings/boardgames/aa445222-7127-41f0-a451-685874bf343c/manifest.json) | [Companion](../recordings/guide-context/boardgames/aa445222-7127-41f0-a451-685874bf343c/manifest.json) | [31/31 applicable requirements](../recordings/captures/boardgames/aa445222-7127-41f0-a451-685874bf343c/manifest.json) |
| **S3 — Retail learning** | `8ce3ace2-0bb4-46f7-898c-795bc7da4794` | [Recording](../recordings/dreamjob/8ce3ace2-0bb4-46f7-898c-795bc7da4794/manifest.json) | [Companion](../recordings/guide-context/dreamjob/8ce3ace2-0bb4-46f7-898c-795bc7da4794/manifest.json) | [181/181 applicable requirements](../recordings/captures/dreamjob/8ce3ace2-0bb4-46f7-898c-795bc7da4794/manifest.json) |

Photography passed 9/9 application assertions. Board games passed 11/11 and retains one native UserSim helpfulness flag. Retail passed 24/24 baseline delivered-response criteria, completed its native Designer profiling report, durable Helix job, MiniMax/Mistral fixed/routed and capable-access comparisons, separate Nemotron diagnostic and managed condition. Cleanup is confirmed for all three selected runs. Retail admitted 42 model attempts; one HTTP 429 attempt failed and recovered after its recorded 30-second wait. Native model-proposal findings remain separate from delivered-response checks.

The retail capture pack exposes 198 Metadata rows across seven conditions, including explicit unused requirements; 181 are required applicable captures. Its salary-only public turn two is an application clarification with zero advisor inference, while turns one and three have native Fabric invocations. See [retail integration](retail-integration.md) for the source-rendering and initial-tool-choice boundaries. These new results do not relabel the earlier failed Gemma/GLM pool or remove development failures.

## Review presentation amendment · 27 November 2026

The v0.3.0 Metadata reader retains the same immutable inventories and adds each
artifact's representation, producer, consumer and input/output purpose. Native
configuration, captured SDK arguments, native results, application accounting and
sanitized projections are identified separately. The default is the relevant
selected condition. “All conditions” groups a requirement once and shares settings
only when content hash, schema and semantic role agree; condition-specific results
and their links remain separate. This changes presentation, not capture counts.

The new [retail review companion](../recordings/review-context/dreamjob/8ce3ace2-0bb4-46f7-898c-795bc7da4794/manifest.json)
recovers omitted **CAP-PLAT-01** client settings and **CAP-PLAT-02** registered-agent
settings from retained originals. It is a new sanitized publication with explicit
source hashes, including the deployment source used by the registered-agent
export. The reader checks those bindings. It does not replace an immutable capture,
claim a new deployment, or turn the registered configuration into a complete
reproducible package. Private authentication values and provider environment
values are excluded.

The read-only [execution reader](../src/learning_lab/guide_execution.py) resolves
native scopes, tool inputs/results and model accounting from those same selected
conditions. It does not invent a turn-to-scope or gateway-to-span join. Retail's
application-only Turn 2 has no native agent subtree. Its displayed gateway usage
is explicitly condition-wide. The optional [local Phoenix integration](../integrations/observability/README.md)
adds filtered historical advisor payloads privately, with explicit startup/import
and verified local project links. Browser inspection never starts either operation.

## Baseline audit · 22 November 2026 (`19b26b8`)

The P/B/R keys and 51 requirement rows below refer only to the original audit. Their run identities, locations and findings remain unchanged so a newly complete capture cannot be mistaken for an older run's evidence.

**Housekeeping location amendment, 22 November:** the old retail run `8542330d…`
and other superseded terminal output were subsequently archived with original
paths and verified recovery. The baseline table below retains its original
locations as dated provenance; use the [audit follow-up recovery map](output-housekeeping.md#audit-follow-up-cleanup--22-november-2026)
to locate those historical raw bytes. The three current demo roots above and all
immutable public packs remain unchanged.

### Baseline demos and location keys

| Key | Scenario | Current demo run | Published recording | Published teaching companion | Ignored private original |
|---|---|---|---|---|---|
| P | **S1 — Photography** | `7863c607-cb99-4a31-b60c-381bf2099f0e` | [P pack](../recordings/photography/7863c607-cb99-4a31-b60c-381bf2099f0e/) | [P companion](../recordings/guide-context/photography/7863c607-cb99-4a31-b60c-381bf2099f0e/) | `.private/history/2026-11-21-scenario3/outputs/runs/journeys/7863c607-cb99-4a31-b60c-381bf2099f0e/` |
| B | **S2 — Board games** | `938bdb3f-568e-442e-889f-fed046edf5a0` | [B pack](../recordings/boardgames/938bdb3f-568e-442e-889f-fed046edf5a0/) | [B companion](../recordings/guide-context/boardgames/938bdb3f-568e-442e-889f-fed046edf5a0/) | `.private/history/2026-11-21-scenario3/outputs/runs/journeys/938bdb3f-568e-442e-889f-fed046edf5a0/` |
| R | **S3 — Retail learning** (`dreamjob` in stored IDs) | `8542330d-d6df-494e-8509-d81a5841d69e` | [R pack](../recordings/dreamjob/8542330d-d6df-494e-8509-d81a5841d69e/) | [R companion](../recordings/guide-context/dreamjob/8542330d-d6df-494e-8509-d81a5841d69e/) | `runs/journeys/8542330d-d6df-494e-8509-d81a5841d69e/` |

Public packs and companions are separate immutable, manifest-verified publications. The private paths above are operator recovery references, deliberately not hyperlinks or public dependencies; they are absent from a public clone. Do not copy private original rows, simulator prompts, arbitrary model reasoning, credentials or private environment values into public documentation or Metadata responses.

**S2 is not an unresolved failed scenario:** its curated conversation passed 11 application assertions and cleanup. Its native UserSim helpfulness flag and failed development conditions remain retained. An honest no-match is not a defect to eliminate. **The baseline S3 experiment remains failed:** its fixed-Nemotron baseline, saved-response scoring and separate managed condition passed their reported checks, while the requested Gemma/GLM comparisons timed out. The successful reachable-Nemotron diagnostic is separate evidence and cannot replace that pool. The new selected retail run uses the later approved MiniMax/Mistral inventory and has its own successful comparison evidence; it does not replace this historical finding. See [verification](verification.md) and [retail integration](retail-integration.md).

Within a private run, `EP/native/` means its recorded baseline episode's native directory; locate it using that run's recorded episode ID. S3 comparison settings/results live under their own `comparisons/CONDITION_ID/` subdirectories. Managed Platform records are a separate condition with its own identities. A run directory containing all of them does not make them one execution.

### How to read the audit

- **EXISTS:** the stated source or retained artifact was found. Existence alone does not mean an operation succeeded.
- **PRIVATE:** already retained outside Git. This is not a missing file; publication can be a separate gap.
- **PARTIAL:** an allowlisted projection or summary exists, with less content than the underlying native object. It must not be presented as a complete runnable input.
- **NOT EXIST:** the stated capture was not found in the audited run. Workstream 1 must capture it prospectively where applicable. Do not reconstruct it and label it historical native output.
- **NOT USED:** the integration or optional operation was not executed by that preset. It does not create a capture requirement until used.
- **Proposed** filenames are future capture names, not claims about current files. The capture implementation may choose an equivalent native-safe name and must update this specification and bindings together.

Each `CAP-…` identifier is a stable inventory requirement. The six columns preserve the requested Metadata presentation. Journey steps refer to the nine teaching lessons, not necessarily execution order: policy and tracing are configured before the conversation even when taught later.

### Full module and operation audit

This table retains the original baseline findings. Source links open current repository templates, which can differ from the baseline's recorded source revision. Use the selected pack's Metadata response for current per-condition availability; do not treat a newly implemented capture rule as proof that an older run produced that file.

| Module | Steps | YAML/JSON file | Status | Location | Apply to scenario |
|---|---|---|---|---|---|
| **CAP-PER-01 · Nemotron Personas / application selection** | **1:** preserve the selected original | `source-lock.json`; `resolved-inputs.json` | **EXISTS** source-lock receipt; **PRIVATE** full original/selection. Application selects/hashes the record; no native Personas YAML is required. | P/B/R packs and private roots | S1, S2, S3 |
| **CAP-SIT-01 · Authored situation** | **2:** supply goal, constraints and disclosure rules | `situation.json` | **EXISTS** — application-owned scenario settings | P/B/R packs | S1, S2, S3 |
| **CAP-DD-01 · Data Designer** | **2:** configure seed and generated columns | `designer-private/configuration.json`; `designer-private/artifacts/retail/builder_config.json` | **PRIVATE** — native generation builder configuration | R private root | S3 generation |
| **CAP-DD-02 · Data Designer** | **2:** inspect selected generation settings | `designer-configuration.json` | **PARTIAL** — application summary, not complete native builder input | R pack | S3 generation |
| **CAP-DD-03 · Data Designer** | **2:** configure execution and provider | Proposed `designer-runtime-config.json`; `designer-provider-config.json` | **NOT EXIST** — effective native `RunConfig` and redacted provider snapshots. Settings are constructed in Python. | Future run-scoped capture | S3 generation |
| **CAP-DD-04 · Data Designer / application lineage** | **2:** retain generated fields, completion and lineage | `designer-output.json`; `designer-generation.json`; `designer-lineage.json` | **EXISTS** — selected generated output, execution summary and application lineage; full generation artifacts remain private | R pack and private generation directory | S3 generation |
| **CAP-DD-05 · Data Designer** | **2:** retain profiling outcome | Native profiling report JSON, if produced | **NOT EXIST** successful report — one-row profiling failed. Warning is retained in `designer-generation.json`. Capture a future report if produced; preserve an error/unavailable receipt otherwise. Do not fabricate successful statistics or make optional profiling success a condition for a valid generated row. | R pack warning; private generation artifacts | S3 generation |
| **CAP-US-01 · UserSim** | **2:** resolve persona, behaviour and probe | `resolved-inputs.json`; `usersim-result.json` | **PRIVATE** — full native `usersim_config` embedded. Runtime setup uses Python; no mandatory YAML input. | P/B/R private roots | S1, S2, S3 |
| **CAP-US-02 · UserSim** | **2:** inspect safe configuration summary | `usersim-setup.json` | **PARTIAL** — allowlisted configuration/outcome; private persona and prompts excluded | P/B/R companions | S1, S2, S3 |
| **CAP-US-03 · UserSim / model access** | **2/4:** configure learner and judge models | Proposed `usersim-role-models.json` | **NOT EXIST** — complete effective per-role model settings snapshot | Future run-scoped capture | S1, S2, S3 |
| **CAP-US-04 · UserSim** | **4:** generate turns and finalize trajectory | `usersim-activations.jsonl`; `public-conversation.json`; `usersim-result.json`; `usersim-quality-flags.json` | **EXISTS** public conversation/events; **PRIVATE** complete final native trajectory; quality flags have companion projections. Preparation and conversation execution remain separate. | P/B/R packs, companions and private roots | S1 one turn; S2 two turns; S3 baseline three turns |
| **CAP-US-05 · UserSim** | **6:** optional post-loop evaluation/report | Separate UserSim eval/report settings and output | **NOT USED** — those commands were not executed. Native in-loop judges are retained under CAP-US-04. | No additional artifact required unless introduced | None currently |
| **CAP-FAB-01 · Fabric** | **3:** assemble native configuration | Native `fabric-config.json` | **PRIVATE** — sanitized serialization of the actual typed `FabricConfig`; that Python object is consumed by the SDK | P/B/R private `EP/native/`; R comparison `runtime/native/` per condition | S1, S2, S3 baseline/comparisons |
| **CAP-FAB-02 · Fabric / teaching projection** | **3:** publish selected settings | Public `fabric-config.json`; companion `framework-config.json` | **PARTIAL** — public pack omits settings; companion is an application teaching projection. Neither published JSON is loaded to run the agent or is a complete replay configuration. | P/B/R packs and companions | S1, S2, S3 baseline |
| **CAP-FAB-03 · Fabric** | **3:** resolve adapter and check prerequisites | `fabric-plan.json`; `fabric-doctor.json` | **EXISTS** retained results; fuller native plan/descriptor/configuration retained privately | P/B/R packs/private native folders; comparisons separately | S1 Deep Agents; S2 Hermes; S3 Deep Agents |
| **CAP-FAB-04 · Fabric / application instrumentation** | **3/9:** start/close persistent runtime | `fabric-lifecycle.jsonl`; `runtime-receipt.json` | **EXISTS** — application lifecycle and startup receipts; not Relay's event stream | P/B/R companions/packs; private native records | S1, S2, S3 baseline/comparisons |
| **CAP-FAB-05 · Fabric** | **4:** retain exact invocation input | Proposed `fabric-run-requests.jsonl` | **NOT EXIST** — complete serialized native `RunRequest` at the actual call boundary | Future native private capture and explicit safe projection | Each S1/S2/S3 invocation and each separate comparison |
| **CAP-FAB-06 · Fabric** | **4:** retain complete normalized return | Proposed `fabric-run-results.jsonl` | **NOT EXIST** — complete top-level native `RunResult`. Do not treat the existing selected output fields as the full result. | Future native private capture and explicit safe projection | Each S1/S2/S3 invocation and each separate comparison |
| **CAP-FAB-07 · Fabric / application result handling** | **4:** inspect retained response and result fields | `reply-outcomes.jsonl`; `fabric-invocations.json` | **PRIVATE** native-output/status records; **PARTIAL** public projection, including response and selected identities | Private native folders; P/B/R companions | S1, S2, S3 baseline; private comparisons separately |
| **CAP-DA-01 · Deep Agents** | **3/4:** configure and execute harness | Harness settings inside native `fabric-config.json` and `fabric-plan.json` | **EXISTS PRIVATE** — no separate Deep Agents YAML is required by this integration | P/R native folders; R comparison folders | S1, S3 |
| **CAP-HER-01 · Hermes** | **3:** configure managed harness policy | `config.yaml` | **EXISTS** source; **NOT EXIST** exact run-bound YAML file copy | [Managed source configuration](../integrations/hermes/managed/config.yaml); future run-scoped copy | S2 |
| **CAP-HER-02 · Hermes** | **3/4:** inspect resolved native settings | `reply-outcomes.jsonl` → `raw_output.hermes_native_config` | **PRIVATE** effective settings embedded. This already exists; absence of a separate YAML export does not erase it. | B private native folder | S2 |
| **CAP-MCP-01 · Course MCP** | **3:** connect server/transport and expose tools | MCP settings inside native `fabric-config.json` and `fabric-plan.json` | **EXISTS PRIVATE** — registered through Python; no separate MCP JSON input is required | P/B/R private native folders | S1, S2, S3 |
| **CAP-MCP-02 · Course MCP / provider boundary** | **3/4:** retain exact discovery and permitted schemas | Proposed `mcp-tools-list.json`; `provider-tool-schemas.json` | **NOT EXIST** dedicated captures. Some offered schemas survive in raw Relay; that does not establish the gateway-filtered provider surface. Retain both boundaries and relate them. | Future run/condition/turn-scoped capture | S1, S2, S3 |
| **CAP-MCP-03 · Course MCP / catalogue** | **4/5:** inspect actual tool input/result and frozen facts | `native-tools.json`; `catalogue-snapshot.json` | **EXISTS** — preserve tool errors, empty searches, details and comparison results as distinct shapes | P/B/R packs; comparison-native artifacts privately | S1, S2, S3 |
| **CAP-MCP-04 · Course MCP / public preferences** | **4:** retain effective public preferences for each turn | Proposed `preferences-by-turn.jsonl` | **NOT EXIST** exact per-turn preference-file copies. Related constraints/audit values exist elsewhere, especially S3 `public-constraints.jsonl` and `disclosure-audit.jsonl`. | Future per-turn capture | S1, S2, S3 baseline/comparisons; managed condition separately |
| **CAP-GW-01 · Application model gateway** | **3/4:** configure call limits, filtering and dispatch | Proposed `gateway-effective-config.json` | **NOT EXIST** combined effective settings snapshot; settings currently come from Python/environment | Future condition-scoped capture, excluding credentials | S1, S2, S3; model roles distinguished |
| **CAP-GW-02 · Application model gateway** | **4/5:** retain admitted model calls and usage | `usage.json` | **EXISTS** accounting by model role/model/status; not a complete configuration or native Relay trace | P/B/R packs and private ledgers | S1, S2, S3 |
| **CAP-LLM-01 · LiteLLM** | **3/7:** configure baseline aliases/providers | `litellm.yaml`; `compose.yaml` | **EXISTS** maintained source files | [Proxy configuration](../integrations/proxy/) | S1, S2; S3 baseline/separate diagnostic |
| **CAP-LLM-02 · LiteLLM** | **7:** configure requested retail candidate pool | `retail-litellm.yaml` | **EXISTS** source; existence does not establish full-context tool-call completion | [Retail proxy configuration](../integrations/proxy/retail-litellm.yaml) | S3 requested Gemma/GLM comparison |
| **CAP-LLM-03 · LiteLLM** | **3/7:** retain actually loaded and resolved configuration | Proposed run-bound YAML copies; `litellm-effective-config.json` | **NOT EXIST** redacted loaded/resolved run-bound snapshots. Current source cannot establish historical loaded bytes. | Future per-proxy/condition capture | S1, S2, S3 baseline/comparisons |
| **CAP-SW-01 · Switchyard** | **7:** define candidates and routing policy | `routing-configuration.json` | **EXISTS** application inventory/policy summary; native policy is constructed in Python | R pack; [policy integration](../integrations/proxy/lab_routing.py) | S3 comparisons |
| **CAP-SW-02 · Switchyard** | **7:** retain decision and comparison outcomes | `routing-comparison.json` | **EXISTS** decisions embedded; requested-pool failures preserved. Separate requested/diagnostic inventories and fixed/routed conditions. | R pack; private comparison folders | S3 comparisons |
| **CAP-REL-01 · Relay** | **3:** activate instrumentation and export | Generated `fabric-relay.json` | **NOT EXIST** physical file in the retained canonical exports. Relevant Relay settings survive inside private Fabric configuration; capture this generated file before sandbox teardown. | Future private native export plus safe settings copy | S1, S2, S3 baseline/comparisons |
| **CAP-REL-02 · Relay** | **4/5:** retain native model/tool/agent events | `relay.jsonl` | **PRIVATE** — original ATOF event stream | P/B/R native `fabric-traces/`; R comparisons separately | S1, S2, S3 |
| **CAP-REL-03 · Relay / teaching projection** | **5:** publish interpretable execution evidence | `relay-scopes.json`; `native-tools.json` | **PARTIAL** — sanitized native projections, not the original event stream or an OTLP trace | P/B/R packs | S1, S2, S3 |
| **CAP-REL-04 · Relay / collector** | **5:** optional collector/Phoenix export | OTLP/Phoenix settings and trace output | **NOT USED** — no collector export configured for these demos | No additional artifact required; no collector installation in this workstream | None currently |
| **CAP-EVAL-01 · Application assertions** | **6:** evaluate saved answers and facts | `evaluation.json` | **EXISTS**; criterion definitions are Python, not YAML | P/B packs; [assertions](../src/learning_lab/journey_checks.py) | S1, S2 |
| **CAP-HX-01 · Helix Evals** | **6:** retain criteria and local native results | `helix-criteria.json`; `helix-evaluation.json`; `evaluation.json` | **EXISTS** — application-extracted criterion inputs, native SDK scores and interpreted rows | R pack | S3 baseline/comparisons where executed |
| **CAP-HX-02 · Helix Evals** | **6:** preserve exact evaluator definition | Proposed `helix-evaluator-config.json` | **NOT EXIST** — metric templates and effective native evaluation `RunConfig`; currently constructed in Python | Future capture linked to criterion dataset/result | S3 native local scoring |
| **CAP-HX-03 · Helix durable evaluation** | **6:** retain submitted job definition and outcome | `helix-job.json` | **PRIVATE** submitted specification exists; **EXISTS** public status/results projection | R private root and pack | S3 durable job over saved criteria |
| **CAP-GR-01 · Guardrails** | **3/8:** load policy and flows | `config.yml`; `rails.co`; `guardrails-config.json` | **EXISTS** source and snapshot with exact YAML/Colang text embedded. Colang is retained even though it is not YAML/JSON. | [Policy](../integrations/guardrails/config.yml), [flows](../integrations/guardrails/rails.co); B/R packs | S2, S3; native Guardrails unused in S1 |
| **CAP-GR-02 · Guardrails** | **8:** retain legitimate boundary decisions and separate negative probe | `guardrails-decisions.jsonl`; `guardrails-probe.json` | **EXISTS** — preserve configured versus actually executed checks and narrow deterministic coverage | B/R packs | S2/S3 baseline; S3 managed caller placement separately |
| **CAP-PLAT-01 · Helix Platform** | **9:** configure server and executor | `config.local.yaml`; private `openshell-config.yaml`; proposed run-bound effective settings | **EXISTS** maintained/current files; **NOT EXIST** sanitized effective run-bound server/executor snapshot | [Server reference](../integrations/platform/config.local.yaml); existing ignored Platform configuration; future run-bound capture | S3 managed condition |
| **CAP-PLAT-02 · Helix Platform** | **9:** package agent | `agent.yaml`; proposed final run-bound `agent.yaml` copy | **EXISTS** base/generated package; **NOT EXIST** exact final registration YAML copy bound to the managed condition. Native registered configuration already survives in CAP-PLAT-04. | [Base agent](../agents/learning-advisor/agent.yaml); [Platform directory](../integrations/platform/) contains the ignored generated `.bundle/dreamjob-deepagents/agent.yaml` after packaging | S3 managed condition |
| **CAP-PLAT-03 · Helix Platform** | **9:** define provider/environment and related resources | `platform-setup.json`; proposed sanitized creation request/response snapshots | **PARTIAL** setup metadata exists; **NOT EXIST** complete redacted provider/environment definition request/response copies | R pack; future condition-owned capture | S3 managed condition |
| **CAP-PLAT-04 · Helix Platform** | **9:** register and deploy | `platform-registration.json`; `platform-deployment.json`; `platform-package.json` | **EXISTS** — native registration/deployment configurations embedded, plus package receipt | R pack | S3 managed condition |
| **CAP-PLAT-05 · Helix Platform** | **9:** create session, invoke, observe and clean up | `platform-condition.json`; `platform-session.json`; `platform-invocation.json`; `platform-trace.json`; `platform-cleanup.json` | **EXISTS** selected native/public records; **NOT EXIST** exhaustive sanitized request/response envelopes for each native operation. Fill boundary-specific gaps without duplicating existing complete records. | R pack/private original; future condition-owned captures | S3 managed condition; not baseline memory resumption |
| **CAP-OS-01 · OpenShell** | **9:** submit intended workload policy | `policy.yaml`; per-execution `requested-policy.yaml` | **EXISTS** source; **PRIVATE** submitted copies | [Policy source](../integrations/openshell/policy.yaml); P/B/R episode folders and R comparisons | S1, S2, S3 baseline/comparisons |
| **CAP-OS-02 · OpenShell** | **9:** inspect loaded policy and observed enforcement/cleanup | `effective-policy.yaml`; `effective-policy.json`; `boundary-probes.json`; `cleanup.json`; `sandbox-identity.json` | **EXISTS** — policy intent, loaded policy, allowed/denied behaviour and cleanup are distinct | P/B/R packs; comparisons privately | S1, S2, S3 baseline/comparisons |
| **CAP-OS-03 · Helix-managed OpenShell** | **9:** inspect managed boundary | `platform-effective-policy.json`; `platform-boundary-probes.json`; `platform-cleanup.json`; private effective YAML | **EXISTS** public records; **PRIVATE** effective YAML | R pack and private managed records | S3 separate managed condition |

### Configuration meaning that the guide must explain

[Fabric configuration construction](../src/learning_lab/fabric_target.py) directly creates native SDK `FabricConfig`, `DiscoveryConfig`, `MetadataConfig`, `HarnessConfig`, `ModelConfig`, `InstructionsConfig`/`InstructionConfig`, `EnvironmentConfig`, `RuntimeConfig` and `ToolsConfig` objects. MCP and Relay are attached through the public configuration methods. These classes group settings; they are not a sequence of application-owned translation stages. The object is passed to Fabric planning/preflight/startup. The private native serialization is a snapshot; the two public JSON forms are narrower projections. [Companion export](../scripts/export_guide_context.py) does not create another runtime input layer.

The same distinction applies elsewhere: Designer and local Helix evaluation use typed Python settings; Hermes and Guardrails have real policy files; LiteLLM loads actual YAML whose resolved values also depend on its environment; Switchyard policy is built by the plugin; OpenShell has requested and effective policy. A source file, current template, generated effective settings, an invocation envelope and a result log must not all receive the label "Configuration."

## Workstream 1 capture contract

The registry, boundary capture rules, public exporter and read-only Metadata consumer implement this contract. The three selected replacement runs have complete applicable capture coverage and verified execution outcomes, as indexed above. Each immutable manifest binds its own conditions and publication; the original audit is not silently rewritten to describe newer output.

1. **One registry, two consumers.** The machine-readable registry uses these stable `CAP-…` requirements. The Integration Map references them for purposeful configuration/result links, and Metadata renders its six requested columns. Both resolve capture availability from the same selected public capture manifest; lesson observations additionally use the matching recording/companion. There is no second handwritten UI inventory.
2. **Retain shared sources and scenario-specific effective settings.** Do not duplicate all source YAML per scenario. Record the shared source reference/hash and the exact effective settings used for every applicable condition. Reuse equal content through explicit content identity while preserving each execution's binding. Do not hardcode a model inventory into narrative text as proof of what ran.
3. **Capture at the real boundary.** Save native request/configuration objects immediately before the SDK/native call and native results immediately after it, including terminal errors. Export sandbox-local generated settings before cleanup. Capture discovered tool schemas separately from schemas actually sent to the provider. Per-turn preferences must show only publicly disclosed information at that point.
4. **Preserve existing capture.** Continue retaining every currently saved public/private artifact, native warnings, failures and unknown usage. Missing public projections may be produced offline from matching retained private originals without rerunning; missing historical native objects cannot be reconstructed and called exact captures. The requested new S1-S3 runs must nevertheless exercise the newly completed capture paths.
5. **Separate privacy from completeness.** Native private capture remains ignored. Public output is a sanitized, allowlisted copy or projection whose omissions and relation to the private source are explicit. Secrets never enter either new logs or Git; redact configuration credentials at serialization. Preserve useful configuration structure and nonsecret values, rather than publishing a hollow list of IDs. Original persona/private context and unrestricted model reasoning remain private.
6. **Keep availability and execution independent.** A complete configuration can accompany a failed invocation. A captured error is a successful capture of a failed operation. Optional/unused integrations stay not-used; failed profiling retains an unavailable/error record rather than a pretend report. Demonstration promotion requires validated execution outcomes, not only inventory completeness.

Minimum artifact bindings for that registry and manifests:

- Stable requirement ID, module/component/operation IDs, journey lesson IDs, scenario applicability and optional/required-for-this-condition status.
- `scenario_id`, `run_id`, `condition_id`, baseline/comparison/managed purpose, episode identity, public turn and model role where applicable; not-applicable values stay explicit.
- Artifact role: authored source, native effective configuration, native request, native response/event, policy/enforcement receipt or application projection. State the native/application schema name and version when available, plus SDK/source revision used by the run.
- Availability (`exists`, `missing`, `not-used`, `unavailable`) separately from access (`public`, `private`, `projection`) and execution status. Missing expected files never resolve to another run or a generic source file.
- Content hash and manifest binding, capture time, repository-relative public location or opaque private artifact reference, and source-to-projection relation with included/omitted fields. Do not expose arbitrary host paths in browser responses.
- Meaningful relationships: configuration used by a call, request answered by a result, result evaluated by criteria, source projected into an artifact, policy verified by a probe. Link only recorded native/correlation identities; do not invent model-call/Relay parentage.

Metadata distinguishes **NOT EXIST** from **PRIVATE**, **PARTIAL** and **UNAVAILABLE**. An absent old-pack inventory leaves private availability unknown. Private-only descriptors expose no original contents or host filesystem URL. Configuration links open actual settings or explicitly labelled projections; application-call links open committed code; result links open the selected scenario/condition record. A URL is available only when the exact public capture bytes are committed. Multi-file references open the matching requirement and condition rather than guessing a file. Explicit condition reads never fall back to baseline; **CAP-SW-01/02** are identified as run-owned aggregates. Read-only registry/manifest resolution never initializes a model, simulation or deployment.

## Workstream 1 acceptance checklist

The execution and capture items below are verified for the three selected replacement demos. Final promoted-demo browser review verified the consumer bindings after check-in; [PLAN.md](../PLAN.md) records the run identities, commits and verification evidence. The historical table's gaps are not retroactively filled.

- [x] **CAP-DD-03/05:** retain Designer effective runtime/provider settings and the actual profiling outcome, without requiring a fictitious successful report.
- [x] **CAP-US-03:** retain effective learner/judge model-role settings.
- [x] **CAP-FAB-05/06:** retain full request/result boundary snapshots for every invocation, including comparison errors and safe publication projections.
- [x] **CAP-HER-01:** retain the exact run-bound managed Hermes YAML; preserve existing embedded effective settings.
- [x] **CAP-MCP-02/04:** retain actual discovery, gateway/provider schema filtering and per-turn public preferences, related to the corresponding calls.
- [x] **CAP-GW-01 and CAP-LLM-03:** retain effective gateway controls, actual loaded LiteLLM YAML and resolved redacted settings per selected proxy/condition.
- [x] **CAP-REL-01:** export the physical generated Relay configuration before teardown; continue retaining native ATOF events and public projections.
- [x] **CAP-HX-02:** retain native metric definitions and local evaluator run settings; preserve the already-retained durable job specification.
- [x] **CAP-PLAT-01/02/03/05:** retain managed server/executor snapshot, exact final agent YAML, provider/environment creation definitions and missing native request/response envelopes. Link existing complete embedded configurations rather than declaring them absent.
- [x] **Registry and manifest validation:** fail clearly for a missing required applicable capture, validate hashes and identities, and confirm the public projection excludes secret/private content. Exercise failures and not-used paths without inventing success.
- [x] **New attributable demos:** complete new S1, S2 and S3 runs with the applicable inventory; retain all previous packs unchanged and preserve failed attempts. Verify actual outcomes and exact-resource cleanup before promoting replacements. S3's approved non-Nemotron replacement pool must be verified independently of a Nemotron diagnostic; preserve the earlier Gemma/GLM failures.
- [x] **Consumer consistency:** prove the selected demo's UX links and implemented Metadata rows resolve from the same registry/manifests, with no scenario/condition borrowing and no inference/deployment on inspection.

When implementation completes an item, record its commit and actual verification evidence in the master plan. Update this inventory's dated current-state assessment alongside new run identities; do not silently convert baseline findings into claims about a later run.
