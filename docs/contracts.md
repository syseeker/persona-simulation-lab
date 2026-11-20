# Application Contracts

The repository-hosted guide adds the strict journey contract below while retaining existing service APIs. Three-preset metadata does not replace the retained backend story enum. Only photography is executable through the guide; board games and retail learning remain illustrative. See the [current plan](../PLAN.md) and [frozen v0.2 record](history/v0.2/INDEX.md).

## Integration Guide journey contract

`JourneyService` uses schema `citizen-journey/v1` and versioned, read-only preset metadata. `/api/journey/[action]` delegates through a persistent **`--guide-only`** worker without initializing legacy recovery. CLI `guide` commands and developer MCP `lab_guide` use this same service. The advisor's three read-only course tools never expose it.

GET actions are `presets`, `readiness`, `list`, `get`, `trace`, `source`, `artifacts` and `artifact`. Queries reject unknown/repeated fields and values above 200 characters. POST actions are `sample`, `start`, `cancel` and `recover`; bodies are bounded at 16,000 characters, must be objects, cannot override `action` and reject a mismatching Origin. Responses disable caching. Reads do not initialize native execution or infer.

`start` accepts only `spec` with `scenario_id: photography`, source (`ngc` or `hf-profile-only`), selected source ID and original SHA-256. It resolves and revalidates the original, then creates fresh run/condition/episode IDs. Extra harness, routing, execution or budget fields are rejected. The preset fixes one public turn, Fabric/Deep Agents, fixed LiteLLM, standalone OpenShell, 120 total calls, 1,024 output tokens and four advisor tool rounds. No Designer, Switchyard, native Guardrails or Helix operation occurs. Exact private UserSim input stays local and is not an allowlisted browser log.

The simulator receives the locked profile plus authored situation. The advisor receives only its latest public message and constraints extracted from that message, never the private preamble/preferences. One native Fabric runtime/thread persists through the condition. Native exec carries the in-sandbox model bridge to the host budget gateway, keeping provider keys outside the agent image. Image source hashes are verified before model admission.

Output lives under ignored `runs/journeys/RUN_ID/`; its episode subdirectory retains native evidence. A cross-process file lease plus persisted guard prevents a second condition and preserves unresolved ownership. Navigation never cancels a workload. Explicit cancellation awaits native creation, retains partial output and attempts exact-condition cleanup. Ambiguous creation/failed cleanup retains the guard. Recovery refuses another live owner and checks ownership labels/native identity. No global sandbox deletion or implicit recovery is available.

`trace` projects saved public conversation, source lock, situation, checks, native Relay scopes/tools and gateway ledger. Native uint64 revisions become decimal strings only at the JavaScript boundary. Simulator stop judges stay distinct from response evaluation. Gateway and native span identities are not silently joined; an unknown saved request stays missing. Stage animation is explanatory unless a selected saved request supplies attributable boundaries.

`source` accepts allowlisted component/module identifiers, never a path. It returns the current working-tree excerpt, relative file/symbol/hash, configured-or-origin GitHub repository and committed reference. Unpublished files explicitly lack a resolving code URL. Run source revision/hashes remain separate. `artifact` requires a discovered, run-scoped opaque ID; same-named files in different runs have different IDs. Reads reject traversal and symlink escape, redact credentials, bound previews at 1 MiB and retain original-file checksums. Private-run log URLs are local/application-relative; fixed published recordings use the contract below. Missing logs stay unavailable.

**Fixed recording publication:** the later user request adds manifest-verified sanitized packs under `recordings/`. They take precedence over same-ID private runs and work without `runs/`. Their external log links target the pack's committed GitHub files; in-app previews use the same opaque-ID API. A pack cannot be cancelled/recovered as a workload. Raw private log linking retains its existing behavior; future live-log changes are deferred. Projections omit private inputs/prompts, secrets and process ownership while preserving native identities/statuses and original artifact checksums. Missing/corrupt packs fail explicitly. See the [recording index](../recordings/README.md).

## Browser, worker and shared services

SvelteKit routes under `/api` map to the version-1 worker envelope `{version, id, method, params}`. Replies correlate the same ID with `result` or a bounded `error`. Worker messages are limited to 1 MiB; web request bodies to 64 KiB. Pydantic request models reject unknown fields. Stdout contains protocol messages; diagnostics go to local stderr/artifacts.

Read endpoints include `status`, `catalogue`, `runs?mode=live|demo`, `run?id=...`, `trace?run_id=...&episode_id=...`, `stories`, `sources`, `source?id=...`, `evidence`, `artifact`, `datasets`, `workbench-job?job_id=...`, `workbench-history` and `profiles`. Evidence/artifact requests bind run and optional episode IDs; an artifact ID is an opaque discovered identifier, not a filesystem path.

POST endpoints include `chat`, `runs`, `cancel`, `evaluate`, `dataset-browse`, `persona-sample`, `persona-lock`, `workbench`, `workbench-cancel` and `platform`. These delegate to shared services; runtime course tools remain a separate, read-only MCP surface. Inspect [actual worker dispatch](../src/learning_lab/worker.py) for canonical operation names.

## CLI and developer MCP

The CLI exposes `stories`, `datasets`, `personas browse|sample`, `evidence`, `artifact`, `source`, `workbench preview|start|job|cancel` and `platform status|action|job|conversation`, alongside the existing advisor/simulation/evaluation commands. JSON specifications use the same strict service models. Generation/Platform commands wait for their own job's terminal state; inspecting a saved job makes no inference calls.

`learning-lab platform conversation DEPLOYMENT --messages '["Find photography", "Any evening option?"]' --preferences '{"goal":"photography","budget_sgd":50,"days":[5]}'` owns one trusted session, awaits each bounded invocation and closes the session even after failure. These preferences match the native OpenShell teaching preset. Use this command or the long-lived UI/developer MCP service for a conversation; separate `platform action` processes cannot continue another process's trusted session.

`learning-lab-developer-mcp` starts a host-only FastMCP server with its own service lifecycle. It exposes developer orchestration/inspection, separate from the three course tools available to advisor runtimes. Starting another process does not acquire cancellation authority over a job owned by the running web worker; the UI or owning service must cancel it.

## Stories, sessions and conditions

Run requests preserve demo/live mode and direct/Relay/Fabric execution, and add a named story, locked source IDs, optional sampling seed, Deep Agents/Hermes harness, fixed/Switchyard model route, saved overlay/generated-data job references and comparison provenance. One to ten profiles and up to three public conversation turns are supported. Hermes requires Fabric. Generated-profile selection requires an explicit saved Designer job; source labels must identify generated data.

Stories are photography, baking, board games or the selected profile's goal. A comparison records its parent and reason, retains the source/story/locked IDs/seed and generated job, checks the frozen catalogue and original profile hashes, and uses fresh target memory and trajectory IDs linked by `pair_input_id`. Explicit comparison changes may select a harness, route, strategy, budget or approved scenario overlay.

An explicitly selected saved Designer scenario binds its typed learning goal and budget to the target's trusted `Preferences`, with `scenario_binding` labelled hypothetical in saved evidence. Its title may replace the named story. Availability remains narrative text; the application does not infer weekday constraints from that text. Added salary and favourite-brand columns remain context hypotheses and never become eligibility or tool policy.

Advisor chat has a three-turn cap. Startup, successful, failed and cancelled chat outcomes are retained under `runs/chats/<id>/chat.json` with `usage.json`; failure closes target memory. A saved failure is not replaced with a plausible reply.

Chat requests contain goal and optional explicit budget/day/area/prior-skill/category constraints, mode, runtime, harness, routing and session identity. Changing session configuration requires a new conversation. A model-visible request cannot relax trusted explicit constraints. A successfully completed transport/invocation is insufficient to declare the answer valid.

## Dataset and Designer interfaces

The original-data explorer accepts `hf-profile-only` or `ngc` for **Singapore NGC Extended only**. Queries contain offset/limit, source-field text search and optional age/area/occupation/education filters. Shared-service pages are bounded at 100 records. Source IDs are resolved against the chosen local distribution; callers cannot supply a filesystem path or arbitrary NGC resource.

The external guide uses a narrower server-only reader with three GET routes: `/api/local-datasets`, `/api/persona-options?source=…` and `/api/personas?source=…`. Its page limit is twenty (default ten); accepted filters are `search`, `age_min`, `age_max`, `planning_area`, `occupation` and `education_level`, with bounded `offset`/`limit`. `planning_area` maps to NGC's actual `district` column only within the shared adapter; the UI labels each source correctly. Options are source-wide location/education values and counts, not filtered counts. Unknown/repeated parameters, path/method injection, reversed ages and oversized limits fail before worker dispatch. POST is not exported. Responses disable caching. The persistent worker uses `--datasets-only`, allowing only `dataset_catalogue`, `persona_facets`, `browse_personas` and shutdown; it never initializes execution-state recovery. Filters/pages are read-only and make zero inference calls.

Sampling is without replacement over the filtered local corpus and returns the actual seed, exact rows, source IDs/revision, per-record hashes and a lock hash. Locking resolves one to twenty distinct source IDs. The simulation currently accepts a smaller per-run count. HF and NGC readiness are independent; missing Extended assets/behavioural fields fail clearly.

A workbench specification chooses `scenarios`, `columns` or `profiles`, source/selected IDs, a count (default five, up to twenty), optional sampling seed and up to eight custom fields. Each field has a safe name, type, description and applicable bounds/choices. Types are text, integer, decimal, boolean, enum and text list. Original and reserved provenance field names cannot be overwritten. No arbitrary code, executable expression or path is accepted.

Designer uses actual native structured columns in the isolated 0.10 environment. Requests freeze original JSON/hashes and source lineage. Results separate `profile`, `generated_fields`, optional `scenario`, generated identity and parent lineage. New profiles use a generated distribution and new UUID; an overlay retains the original profile. Independently validated saved results can become UserSim input without regenerating data.

Generation failures preserve artifacts and usage. A recognised one-row SDK profiling failure can retain independently validated generated rows with an explicit profiling warning and unavailable statistics. It does not turn a failed generation/schema check into success or trigger a hidden retry.

## Matching, evidence and evaluation

The catalogue uses stable IDs, official URLs, capture dates, fee bounds, known extras, schedules and prerequisites. Missing facts are null. Matching enforces known budget/material/day/prerequisite/intake conflicts and rejects irrelevant goals; no-match is a supported outcome. Date-sensitive evaluation uses the saved run context where available.

The course search tool accepts weekday indices (Monday=0 through Sunday=6) or names such as `Saturday` and normalizes them before matching. Invalid weekday strings return an explicit error; they never relax availability. Trusted application or frozen-preset constraints still take precedence over model arguments.

A target response carries public text, session/thread identity and available tool/runtime evidence. Error strings, empty answers and malformed pseudo-tool output remain invalid. Native Relay scopes retain UUID/category/parent relationships; partial or missing events stay partial. Artifact reads allow fixed filenames/topologies, reject path traversal/symlink escape, redact credentials and bound payload size. Current local source excerpts identify their revision limits.

Tool execution policy and provider-visible schemas are separate boundaries. Fabric 0.6.1's Deep Agents global allowlist blocks non-catalogue execution but its pinned runtime still advertises eleven schemas internally. The shared Gateway's optional `allowed_tool_names` filters assistant-role provider requests to `search_courses`, `get_course_details` and `compare_courses` for local Fabric Deep Agents workloads and managed Deep Agents sessions. Other model roles keep their own protocol. Hermes retains its maintained catalogue discovery tools; it does not receive the Deep Agents function-name filter.

Each filtered call's usage record contains `tool_surface` with `source: application_allowlist` and the actual `received`, `exposed` and `withheld` names. When the four-round guard withdraws all tools, `exposed` is empty and `limit_reached` is true. Original native Relay events retain the adapter-side request. This ledger records the provider boundary without replacing native tracing, fabricating a tool execution or converting pseudo-tool text into a call.

Evaluation rows retain episode/turn/condition, criterion, status, reason, expected/actual and evidence. Pass/fail/error/not-applicable are distinct; missing structured constraints are not replaced with model tool arguments. Missing frozen snapshots never fall back to the current catalogue. Applicable deterministic rows are scored through the actual local Helix Evals SDK. This does not certify every factual sentence.

## Artifacts, budgets and external operations

Simulation artifacts live under ignored `runs/<run-id>/`; generation jobs under ignored `runs/workbench/<job-id>/`. Saved manifests identify configuration, models, code revision and exact inputs where recorded. Native UserSim outcomes, target history, Relay/Fabric evidence, evaluation rows and partial failures remain local.

Workloads have a 120-provider-attempt cap, a 1,024-output-token ceiling per call, four tool rounds per advisor reply and one active workload per worker. Count simulator, advisor, judge, summary and Designer roles separately. Cancellation preserves completed, failed and cancelled attempts; unknown usage remains unknown.

Platform operations explicitly select a local or remote connection and a supported SDK operation. Inspection does not register/deploy/invoke. The deployed inference bridge requires the active run's admission lease and routes through that run's gateway. OpenShell enforcement requires native runtime/policy evidence beyond a checked-in intent file. [Compatibility](sources.md) and [verification](verification.md) state the actual supported/environment-tested combinations.

`sessions_recover` is an explicit recovery action for the retained failed session and its original Platform scope. It stops that session's owning deployment, requires native sandbox cleanup proof and confirms SDK session closure before releasing the guard. A missing runtime or deleted Platform record alone is insufficient. The service chooses the receipt path under its saved job directory and reuses it across retries; callers cannot supply a different sandbox, gateway or receipt path. Missing proof and unknown replacement identities keep the session blocked.

The native OpenShell package uses an explicit hash-checked public photography/S$50/Saturday preset and read-only catalogue, with the official encrypted OpenShell credential store. It does not accept an arbitrary new preferences payload as though the frozen deployed story had changed. The separate Docker environment delivers authenticated per-session preferences. A dynamic OpenShell callback would require resolving the [external-driver compatibility limit](sources.md#compatibility-workarounds); that path is not enabled.

`sessions_create` and `invoke` optionally accept `story_reference: {run_id, episode_id, condition_id}` in their arguments. All three are canonical UUIDs; caller-supplied provenance labels are rejected. The service resolves the original episode's structured preferences and first public input from saved events, records their lineage and input hash in the Platform job, and strips the reference before calling the SDK. The first invocation must reuse those exact inputs. Later turns retain the reference and original preferences; changing it or modifying the source inputs requires a new managed condition. This reference does not copy simulator persona data or previous target memory, and does not establish an identical deployed catalogue/configuration.

## Historical output retention

The [private output archive policy](output-housekeeping.md) separates active or unresolved work from superseded records. Archived raw records retain their original identities and statuses. Recovery verifies checksums into a new directory; it does not install a recording pack, reopen a session or rewrite the retained worker protocol.
