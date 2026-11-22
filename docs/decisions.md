# Architecture Decisions

## 22 November 2026: Retrieve an explicitly named programme before searching alternatives

A routed diagnostic applied a community-only search to the named SMU certificate, then interpreted its empty result as absence from the whole catalogue. Delivery validation correctly rejected the missing programme evidence. Retail instructions now identify the stable catalogue lookup key `SF-007` for that explicitly named programme and require the real details tool first for content/duration/fee questions. The instruction contains no fee or duration; those still come from the returned frozen record. Later alternatives still require a real search against the public budget/days. The matcher, provider inventory, validation and failure records remain unchanged.

## 22 November 2026: Clarify decision constraints before agent dispatch

The user approved an early clarification path after the baseline model made four searches using invented budgets and returned malformed tool-call text. Retail now asks for missing budget/study days before Fabric/model/tool execution when the learner supplies income or only part of the decision constraints. An opening request for programme information still runs the real course-tool path without first requiring a spending budget. The earlier invalid result remains invalid and unchanged; this branch is selected before dispatch, never after catching a native error.

`RetailResponseBoundary` owns the clarification and pending/confirmed delivery state. Input and output Guardrails still run. The branch records an application response ID, missing public constraints, zero advisor inference calls and no model proposal. Previously returned source context can be cited with its original provenance, while a pure question needs no new lookup. Only output-approved delivery becomes the next acknowledgement. Three public turns can therefore contain two real Fabric invocations, tagged with public turns 1/3 and native sequences 1/2. Native requests/results/preferences and Relay evidence remain actual-only; the clarification has no invented native result or span. Evaluation and publication distinguish these paths and keep their existing factual criteria.

## 22 November 2026: Keep comparison reasoning policy with each model deployment

Our Fabric configuration builder applied Deep Agents `reasoning_effort: none` to every model. The installed maintained adapter forwards that value into the request. This application-owned default can override a LiteLLM deployment's provider-specific policy; the selected Mistral endpoint rejected none while high passed controlled serving probes. The user authorized correcting the builder and verifying the actual Fabric path before another full retail run. No upstream Fabric defect is established by the SDK forwarding supplied settings.

For the three comparison aliases, the builder now omits that shared value. Each fixed/routed deployment retains its model's identical reasoning configuration in the retail proxy. Existing fixed-baseline and Hermes settings remain unchanged. MiniMax M3.1 Flash and Mistral Large 4 are the user-authorized replacement pool after Gemma/GLM timeouts; their efficient/capable names describe routing roles, not benchmark conclusions. Direct/proxy serving probes and actual Fabric execution remain separate verification milestones. Preserve the failed original pool and the source-specific settings/results for every new condition.

## 22 November 2026: Separate native proposals from application delivery

The retail prompt-only correction failed a new live replay. The user then approved explicit clarification and response validation. Retail now treats a successful native Fabric reply as a proposal. An application-owned boundary renders the programme facts or a budget/schedule clarification from successful native course-tool results, validating every returned course against the frozen catalogue. It does not fill missing tool evidence from the catalogue, estimate affordability, infer budget from income, or describe an unknown fee/duration/timetable as a confirmed fit. Presentation has an enforced 180-word maximum and makes no additional inference calls. Failed, empty or token-truncated native execution still stops.

Inside standalone OpenShell the sequence is native Fabric proposal → application validation/rendering → native output Guardrails → confirmed public delivery. A blocked check stops the turn. Subsequent Fabric requests carry the exact previously delivered response as explicit application metadata; native memory and immutable normalized results still retain the original proposal. The separate managed condition applies the same presentation boundary at its existing host caller, using completed tools from its exact fresh Helix session before output Guardrails. Missing or truncated Intake evidence cannot become a substitute success.

Effective response settings, validation/delivery decisions and private original proposals have separate artifacts. Public projections retain origins, source hashes, violations and proposal hashes, while omitting unpresented proposal text. Helix criteria score delivered application behaviour; selected proposal-rule failures remain visible separately. A passing public response does not establish that the model followed its instructions or that a routing strategy improved model quality. This is application response policy, distinct from native Guardrails and OpenShell enforcement.

Retail orchestration now stops after failed baseline scoring, failed auxiliary execution or the first failed comparison. Unstarted operations stay `not_run`; cancellation preserves attempted receipts and unknown usage. Incomplete required captures cannot leave a run marked completed. Cleanup confirmation continues to determine ownership release.

## 22 November 2026: Bounded recovery from provider throttling

After the MiniMax comparison received upstream HTTP 429, the user authorized waiting 30 seconds, then 60 seconds if still throttled. Implement that exception in the application gateway only for requested retail assistant comparisons. SDK/proxy/provider retries remain zero. Every attempt consumes the shared budget and keeps a distinct receipt; successful tool execution is never repeated. All waits and attempts share the original model-request deadline. Honor a received `Retry-After` up to the approved 60-second wait bound; a longer wait, exhausted schedule or different failure stops for the existing user checkpoint.

Capture selected quota/wait headers from the received HTTP hop, not arbitrary response headers. Keep raw errors, planned/actual waits and logical request/attempt identities without claiming that LiteLLM headers prove the provider's exact quota. Publication retains the failed attempts alongside a recovered result. Default/baseline, simulator, judge and Hermes calls retain their previous single-attempt behavior.

## 22 November 2026: One durable master plan and preserved detailed requirements

The user identified that successive chat proposals had not been consolidated into repository state and explicitly requested a tracking repair. [PLAN.md](../PLAN.md) is the single active delivery plan, with stable workstream IDs, statuses, dependencies, acceptance criteria, amendments and completion references. Its linked [UX specification and feedback register](ux-review-spec.md) and [configuration/evidence inventory](configuration-evidence-inventory.md) preserve detail; they are subordinate requirements, not competing schedules. A short summary never discards their requirements. Reconcile a new instruction into the affected item before implementing it and record actual verification separately.

The agreed order is execution/capture fixes plus fresh S1–S3 demos, the full teaching UX revision, then the Metadata tab. The shared artifact contract is defined at the start of the execution work and later drives both UI surfaces. All nine lessons and every workflow/selection in both views remain in the UX scope; no Step 3-only review gate replaces it. Metadata is the requested fifth tab; preserve the existing four. Earlier dated entries below retain historical rationale and do not override the newer master/specification.

The current repair changes documentation only. It does not rerun scenarios, fix Gemma/GLM, change SDKs, update demo IDs, implement the UX or add Metadata. Those workstreams remain queued with the user's authorization preserved. The existing four-tab application and its recordings remain the baseline until separately verified replacement work is completed.

## 21 November 2026: Retail disclosure, comparisons and managed ownership

Keep one fixed-Nemotron baseline and separate fresh-memory comparison conditions. Designer generates a closed hypothetical overlay from the locked source; free text cannot redefine the salary/budget protocol or copy a source name. UserSim generates three public turns after preceding replies; actual advisor dispatches are audited for hidden salary before disclosure. Public salary never becomes a budget. Use actual SMU fee/duration facts from the separately dated supplement.

Local Helix scores explicit application-extracted values; a durable Platform job consumes the same saved criteria without inference. The requested Gemma/GLM pair timed out. Publish that failed state alongside the separately labelled successful native-routing diagnostic, without substituting one inventory for another. Native MCP transport success must include a valid domain result before it counts as a successful search; invalid optional kinds return a structured error and weekday names normalize to validated indices.

Managed execution is a new public-context condition, with native registration, deployment, session/invocation, Intake, enforcement probes and confirmed cleanup. It owns its provider/environment/secret/fileset and never changes older deployments. Cancellation records identities before cleanup; unresolved cleanup keeps the guard. The managed reply is deployment evidence, not a replay of the baseline multi-turn evaluation. Guardrails placement differs explicitly: inside baseline OpenShell versus at the managed host caller.

Preserve all failed development runs privately. A later photography regression exposed narrow-space place-name parsing; normalize horizontal whitespace without merging field lines, retain the original 8/9 result and verify a new condition rather than rewriting it.

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
