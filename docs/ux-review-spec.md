# Integration Guide UX review specification

Status: **Implemented and verified for developer review. User acceptance remains pending.**

Recorded: 22 November 2026, Asia/Singapore. This is a supporting specification of the [single master plan](../PLAN.md), not an alternative plan or a new approval gate. Requirements marked Verified for review below have implementation and technical/editorial review evidence in the verification record. This is not a claim of user acceptance. The future UserSim extensions remain research items, rather than silently implemented features.

## Authority and scope

The [project goals](project-goals.md) remain the canonical North Star. This specification consolidates the user's detailed UX feedback, labels 1–31, subsequent teacher/developer-zero requirements and the critical review of all workflows. Later scheduling summaries did not replace these detailed requirements. The master plan controls delivery order: execution repair and complete new recordings first, this UX work second, and the generated Metadata tab third. The artifact inventory is shared with both the UX and Metadata work.

**UX-001 — Verified for review: apply the review to the whole guide.** Review all nine lessons for photography, board games and retail learning, in Simplified and Detailed. Review every selectable conceptual block, conceptual action, library block and technical operation. Fabric in the annotated screenshots is an example of the required treatment, not the boundary of the request. Present all nine redesigned lessons for review together; there is no Step-3-only review gate.

**UX-002 — Verified for review: freeze unrelated behaviour and presentation.** Preserve the accepted typography, colours, unrelated spacing, page structure, resizable inspector, map positions and layout controls, dataset browsing, runtime ownership, public/private data boundaries and compatible environments. Make only the content, selection/reference plumbing, diagrams and supporting tests necessary for the requested teaching experience. Metadata is a separate master-plan workstream. Do not use this specification to authorize another backend redesign, SDK upgrade or deployment feature.

## Teaching contract

**UX-010 — Verified for review: teach the one-person developer team.** The learner is developer zero, reviewing the actual application built in this repository. Be a quiet, precise, interactive teacher: provide enough background to understand a mechanism, enough reasoning to decide whether it fits, the actual settings expressing the choice, and an interpreted outcome. Treat implemented design as material to examine, not automatically as best practice. Explain material tradeoffs and one useful variation where it adds understanding.

Every explanation is responsible for establishing the citizen-facing problem, the mechanism, the implementation decision, how that decision becomes executable and the meaning of the result. These are editorial responsibilities, not five mandatory headings or repeated boxes. Paragraphs must connect causes and effects. Keyword lists, bare product names, unexplained field dumps and one-sentence restatements of headings do not meet the contract.

**UX-011 — Verified for review: write separately for each audience.** Simplified must let a beginner explain the behaviour in ordinary language. Introduce technical terms when needed and connect them to the citizen story. Detailed must teach the application/SDK boundary, important internal operations, configuration contracts and diagnostic interpretation. Detailed is not the same prose with more identifiers, table rows or links appended.

**UX-012 — Verified for review: use progressive detail without forced navigation.** A selected destination must answer its own question completely. Deeper selections reveal a new mechanism; they do not send the reader around circular links to assemble the explanation. Default to focused paragraphs. Add a small sequence, diagram or interpreted table only when relationships are clearer visually. Do not force every component to have three operations or every page to have identical sections.

**UX-013 — Verified for review: preserve the North Star and place the teaching promise once.** Do not change the canonical text in `docs/project-goals.md`. Preserve the user's agreed UI North Star wording:

> Teach developers to build a citizen-focused AI application with country-specific Nemotron Personas and the NVIDIA NeMo stack—by seeing how it works, following its information flow, and opening the code and evidence behind it.

Immediately below that UI North Star, place this requested text once, with the question chain bold:

Every lesson must answer:

**What are we trying to achieve → which components cooperate → what does the application call → what configuration is used → what comes back → where is the proof?**

Do not repeat that promise beneath the scenario cards as well.

## Content ownership and selection behaviour

**UX-020 — Verified for review: one substantive home for each explanation.** Scenario Summary owns the shared goal, constraints, selected preset, conversation length, curated recording identity, completion/cleanup status and material run-wide warnings. Do not repeat its full facts table or status box on every lesson, block and operation. Repeated nouns, breadcrumbs and essential context are acceptable; repeated substantive prose, full profiles, conversations and result tables are not.

**UX-021 — Verified for review: lessons explain cooperation.** A lesson answers what the scenario needs to achieve and how the participating responsibilities cooperate. Start with a substantive introduction paragraph without a `Why this matters` heading. `In this scenario` gives a concrete explanation and only useful scenario-specific facts or outcomes. `How it works` develops the causal sequence in readable paragraphs. A lesson is not an expandable directory of every component operation. Remove nested component-link lists and the entire generic `Check your implementation` section; do not rename the same checklist and retain it.

**UX-022 — Verified for review: blocks explain responsibilities.** A Simplified block explains its whole conceptual responsibility across all constituent technologies. Citizen advisor includes the application, Fabric and selected harness; Course information includes MCP and catalogue; Model access includes gateway, proxy and applicable routing; Execution records and checks includes tracing, stored evidence and applicable evaluation. These blocks must not resolve to their first technical member. Detailed library blocks explain that library's responsibility, boundary, integration decision and limitations. Keep upstream architecture/workflow links at this explanatory home rather than repeating the link on every descendant page.

**UX-023 — Verified for review: actions explain one transformation.** A Simplified action retains its visible plain-language title and explains only that action. A Detailed operation retains its technical title and explains preparation, actual application call, SDK-owned work, important settings and returned result. Remove inherited broad scenario tables, component overview prose, related-lessons lists, generic checklists and integrity footnotes from operation pages. Do not duplicate the same concept as both introductory text and a `Design choice` callout.

**UX-024 — Verified for review: preserve semantic selection identity.** Represent conceptual blocks/actions independently from libraries/technical operations, with explicit many-to-many relationships for highlighting. Do not select `members[0]` as the conceptual page. Do not substitute `Build FabricConfig and resolve the adapter` after clicking `Connect the selected agent`. Preserve scenario, lesson and selected turn/condition. When changing Simplified/Detailed, return to that lesson's audience-specific explanation and show the whole architecture; explicit selections then focus their participating flow. Invalid persisted selections return to the corresponding lesson rather than an unrelated operation.

**UX-025 — Verified for review: retain intuitive navigation and focus.** Keep one permanently visible scenario dropdown. Use one curated demo per scenario, without a run-history selector. Collapse the remaining summary. Entering Integration Map, changing Simplified/Detailed or resetting layout shows the whole architecture without dimming. Explicit lesson/action selections then highlight only relevant participating operations and directional edges. Step 1 must not imply that UserSim has already executed; later lessons may involve several components. Only lessons use numbers 1–9; architecture blocks have names without competing numbers.

**UX-026 — Verified for review: retain read-only review.** Back/next, playback, map selection, explanation, configuration inspection and saved-log browsing never infer, simulate, register, deploy or modify execution ownership. Preserve reduced-motion behaviour and supported panel resizing, panning/zooming, saved selection and layout restoration. Explicit live execution remains distinct from recorded guide navigation.

## Configuration, code and evidence semantics

**UX-030 — Verified for review: label files by their real role.** Distinguish authored configuration input, a typed Python configuration object, generated effective/native configuration, a sanitized recorded snapshot, an application teaching projection, execution events and returned results. A Python builder must not be labelled as though it were a YAML/JSON settings file. A summary is not a complete runnable input. Some integrations need no standalone YAML at all; do not invent native file requirements merely to fill a table.

**UX-031 — Verified for review: purposeful references.** Place descriptive links beside the mechanism or claim they support: the exact application symbol/committed lines, the relevant configuration artifact and the specific scenario/run/condition record. Explain what useful fact the reader will find. A valid URL or existing file is insufficient if it establishes a different operation. Remove repeated four-link toolbars, raw JSON previews, partial code snippets, all-files dumps, duplicate Sources/Evidence navigation, source-hash-match filler and circular component links. Retain integrity/provenance verification internally.

**UX-032 — Verified for review: use native evidence at its actual boundary.** File presence is not proof of successful execution. Distinguish configured, invoked, completed, failed, unavailable and not applicable. Use a plan/preflight report for preparation, lifecycle events for startup, exact request/result for invocation, native trace scopes for observed model/tool relationships, criterion results for evaluation, and effective policy/probes/cleanup for operational enforcement. No scenario inherits another's records. Missing evidence is explained at the claim it limits; it must not silently open the first artifact or a generic source file.

**UX-033 — Verified for review: keep correlations and conditions honest.** A selected public turn must show only its associated conversation, invocation and attributable actions. A run-wide trace can be offered as run-wide context, clearly distinguished from turn-specific records. Do not invent gateway-to-Relay joins or parent IDs. Keep baseline, requested routing comparisons, separate diagnostics, negative policy probes, durable evaluation jobs and managed deployment conditions distinguishable. Opaque IDs help correlation, but are not the educational outcome.

**UX-034 — Verified for review: interpret domain results correctly.** Successful MCP transport is not automatically a successful course search. Explain structured errors, matching results, successful empty searches, details results and comparison results according to their actual schemas. Do not apply a `matches` lookup to every tool and label the resulting absence as no match. Preserve unknown usage, malformed replies, provider errors, UserSim flags, incomplete comparison pairs and failures. A perfect fraction from narrow checks does not establish universal answer quality.

### Concrete Fabric standard

**UX-035 — Verified for review: explain native configuration assembly explicitly.** The Detailed configuration operation explains that `build_config` constructs the actual installed SDK `FabricConfig` and nested models, not an application JSON format later translated into Fabric. Explain the responsibilities of discovery, metadata, harness selection/resolution, model connection, instructions, environment, runtime contract/limits, tool allowlist, MCP registration and Relay settings. These classes group and validate parts of one configuration; they are not a chain of processing stages. Explain internal tool/model execution bounds separately from public conversation turns.

The SDK consumes the typed object for planning, preflight and persistent runtime startup. Separate those operations from `runtime.invoke(RunRequest)` and consuming the normalized `RunResult`. SDK adapter normalization and harness-specific translation are SDK-owned work; application serialization and record-reading are application-owned work. Constructing the configuration does not itself prove that adapter resolution or inference succeeded.

The current native local `fabric-config.json` is a sanitized serialization of the typed configuration. Its published recording counterpart is a limited allowlisted projection; `framework-config.json` is a separate application-created teaching projection. Neither published JSON is loaded as the runtime input or is a complete runnable Fabric configuration. Explain this beside the appropriate recorded-settings link. The new runs/capture workstream may improve captures; update the explanation from those actual artifacts without relabelling historical files.

A configuration page does not replay the entire lifecycle. Planning shows the resolved adapter/capabilities and preflight findings. Startup shows what persistent runtime was created. Invocation shows the selected public input and captured request. Result handling explains the returned response and available normalized fields. Hermes must use the same common Fabric application call sites with different adapter-specific settings, and evidence must demonstrate that difference.

**UX-036 — Verified for review: explain logs without inventing observability.** Relay attaches instrumentation to the selected harness; it is not a mandatory conversational hop or a response evaluator. Explain parent/child event relationships, actual model/tool inputs/results and exported records. The application's lifecycle events and model-call accounting are separate evidence sources. The retained demos used ATOF file output; no Phoenix/collector trace exists for those recordings. An optional future OpenTelemetry/OpenInference dashboard is not part of this UX repair and must not be implied by a `Scenario log` link. Ordinary syslog is not a substitute for an operation-specific input/result record.

## Nine lesson learning outcomes

All requirements in this section apply in Simplified and Detailed, with separate audience-appropriate writing and each scenario's own facts. The following defines ownership so neighbouring pages do not repeat the same tutorial.

### UX-L01 — Verified for review: Choose a test persona

Simplified introduces the actual selected synthetic person, interprets relevant original background/interests/traits and explains why preserving the same person helps reproduce the test. Do not present provenance jargon before explaining the person.

Detailed distinguishes original distribution loading, application selection and identity/hash verification. Explain the available fields and actual selection criteria. Use the recorded distribution, revision and hash to resolve the original; missing installed source produces unavailable, not a substitute. A retained selection receipt does not prove uncaptured sampling details. Source selection and hashing are application-owned, and UserSim has not run. Keep HF profile-only versus NGC Extended explicit.

### UX-L02 — Verified for review: Create a situation

Simplified explains that a profile describes a person while a situation describes what that person wants today. Separate original profile information, supplied constraints and hypothetical generated enrichment. Photography supplies beginner photography/Saturday/under S$50; UserSim does not independently invent those constraints. Board games uses its own authored request. Retail uses an explicitly hypothetical Designer overlay and disclosure rules.

Detailed follows locked original plus authored situation/Designer overlay into resolved UserSim persona, behaviour and probe configuration. Explain source seed/schema, SDK generation, application validation/lineage and custom probe hooks separately. Preparation configures the conversation; the loop generates the public message in Step 4. This lesson owns the prepared situation and configuration, not a repeated conversation preview. Retail salary is not a training budget and remains private until its specified public disclosure.

### UX-L03 — Verified for review: Build and connect the agent

Simplified explains how instructions, a model connection and read-only course tools become a runnable advisor. It does not introduce the system with a broken list of product names.

Detailed teaches configuration assembly, adapter resolution/preflight, persistent runtime startup, harness context, MCP connection/tool discovery, model connection and Relay attachment as related but distinct boundaries. Follow the Fabric standard above. Separate configured/discovered tools from actual calls; connection setup must not display investigation results or a whole conversation. No later invocation/closure list is presented as this lesson's output.

### UX-L04 — Verified for review: Run the application

Simplified owns the readable public conversation, why a lookup occurred, what came back and how it informed the answer. Show one/two/three turns for the respective scenario. Board games' honest no-match is a meaningful learning outcome.

Detailed explains UserSim's learner/gate/judge/stop loop and the nested advisor model/tool loop. Follow selected turn → public message → Fabric request → selected harness → actual model/tool work → normalized result → UserSim continuation/stop. Follow-ups arise after earlier replies; they are not pre-generated. Correct the current all-invocations-under-selected-turn display. Explain what the advisor actually knew at that turn, including later retail disclosures and persistent conversation context.

### UX-L05 — Verified for review: Investigate execution

Simplified starts with an answer and traces the important observed lookup, returned fact and use in the reply. Tool/scope counts alone do not explain why the answer was produced. Explain when later advice reuses earlier public context without a new lookup.

Detailed interprets native Relay event order/parentage, domain tool results and relevant Fabric lifecycle records. Keep run-wide trees distinct from selected-turn associations. Explain tool errors/empty searches/details/comparisons correctly and model-call accounting separately. The recording reader is application infrastructure, not a UserSim subsystem. Missing correlations remain missing.

### UX-L06 — Verified for review: Evaluate behaviour

Simplified introduces the concrete questions before scores: did photography respect the schedule/budget and uncertainty, did board games admit a genuine no-match, did retail preserve disclosure and distinguish salary from budget? Explain expected behaviour, observed result, reason and coverage.

Detailed follows saved conversation/frozen facts/execution evidence through application-derived criterion inputs and selected evaluation. Distinguish application assertions, UserSim in-loop judges, optional unused UserSim post-loop evaluation, local Helix scoring and a durable Helix job. Submitting a job is separate from defining/computing a criterion. Narrow deterministic checks remain narrow when run through Helix; explain disagreement with UserSim helpfulness flags rather than deleting it. Outcomes and failures precede interpretation of aggregate scores.

### UX-L07 — Verified for review: Optimize model routing

Simplified explains S1/S2's fixed route without pretending optimization occurred. In retail, explain why distinct comparison conditions exist before showing their results.

Detailed separates gateway admission, LiteLLM alias/provider dispatch, Switchyard candidate/policy selection and provider completion. Explain what was held fixed and when inventory or limits also changed. Requested Gemma/GLM comparison failures must not be replaced by a successful Nemotron diagnostic. The execution-repair workstream aims to fix and rerun the requested pool; the UX must display the verified new outcome and preserve historical failure context without mixing conditions. Do not flatten native routing metadata into an unexplained dump or imply that plugin configuration proves a real decision.

### UX-L08 — Verified for review: Configure behavioural safeguards

Simplified teaches the intended boundary: legitimate learning requests proceed; a separate forbidden credential request is blocked. Ordinary no-match advice is not a safety refusal. Photography explains application restrictions and native Guardrails as unused.

Detailed connects effective YAML, Colang flows, application actions, `LLMRails` configuration/check calls, native decision and application continuation. Explain coverage of the specific deterministic/custom rules, actual executed actions and limits. Separate the legitimate conversation from the negative demonstration. State the actual placement for each condition: baseline Guardrails executes inside OpenShell; the retained retail managed condition uses the host caller boundary. A general diagram must not assert one placement for all conditions.

### UX-L09 — Verified for review: Deploy with controlled access

Simplified explains where the advisor/harness/course tools run, what they may access, what a demonstrated denial prevented and why host-side UserSim/model gateway/credentials remain outside. Raw errno values and hashes are not the introduction.

Detailed separates packaging, registration, deployment, sandbox creation, session/invocation and cleanup. Explain prerequisites and resource ownership, intended versus loaded policy, permitted activity and actual denial evidence. Connection failure alone is not enforcement proof. Standalone OpenShell is distinct from Helix-managed operations. The retail managed condition starts a new session with selected public context; it does not resume baseline private memory or add a fourth UserSim turn. Controls were applied before/during execution even though this teaching lesson appears last. Qualify historical compatibility issues only where relevant.

## Component and workflow coverage

**UX-040 — Verified for review: cover all eighteen current Detailed responsibilities.** Use official/pinned upstream architectures and installed integration boundaries as references, rather than reproducing every upstream subsystem. Every retained operation must explain a meaningful configuration, execution, information-crossing or result boundary. Audit the existing operation inventory; merge or relabel operations where separate clicks would not add understanding. Update documentation only when checked against actual code and new recording evidence.

1. **Nemotron Personas:** distribution loading → original selection/inspection → identity/hash locking. These are application-owned operations over the dataset. Separate them from generated overlays and downstream simulation.
2. **Authored situation:** supply goal/constraints/disclosure rules → bind to the locked original without changing it. Explain the application-owned preset rather than implying a NeMo generation call.
3. **Data Designer:** seed and closed column schemas → actual requested-field generation → application validation and separate lineage. Distinguish native generated rows, execution callbacks and profiling output. Missing/failed profiling stays explicit.
4. **UserSim:** resolve persona/behaviour/probe → apply custom learning-advisor hooks → inherited conversation generation/gating/reply processing → stop/finalize trajectory. Explain custom hooks versus inherited engine, public target input versus private simulator context, and in-loop judging versus later evaluation.
5. **Fabric:** native typed configuration → resolution/plan/preflight → persistent runtime startup → common request invocation → normalized result consumption. Do not present nested config types as processing stages or public snapshots as runnable inputs.
6. **Selected harness:** Deep Agents or Hermes establishes instructions/context/tools → performs its actual model/tool loop → produces the response. Differentiate installed support from features actually exercised. No unobserved delegation, planning skill or persistent-memory claim merely because upstream supports it.
7. **Course MCP:** connection/discovery → search → details/comparison where actually called. Explain transport/schema versus application matching, available versus invoked tools and exact domain result interpretation.
8. **Frozen course catalogue:** preserve dated facts/source links → serve the same known snapshot to execution/evaluation. Explain coverage, unknown fees/availability and why snapshotting helps reproduction; it does not establish personal eligibility.
9. **Application inference gateway:** admit/count/bound each call → filter the provider-visible tool surface → dispatch and account for result/usage. These controls are application-owned, distinct from Fabric execution allowlists and Relay's original observed input.
10. **LiteLLM:** load alias/provider settings → dispatch to configured deployment → return provider output/usage. Explain fixed aliases and routing candidate groups without treating the proxy as another agent.
11. **Switchyard:** candidate inventory/policy → real decision → LiteLLM dispatch → retained decision/comparison. Distinguish requested model pool, diagnostic inventory, completion and evaluation. A chosen candidate is not automatically a successful answer.
12. **Relay:** attach integration/configuration → capture parent-linked model/tool/agent scopes → export/read native evidence. Explain instrumentation boundaries and file sink versus optional future collector. Never place it as a required request hop or call it an answer evaluator.
13. **Recorded evidence:** manifest validation → scenario/run/condition-specific artifact access. This application reader supports guide inspection, not execution. Integrity checks belong internally, not in repeated public teaching footers.
14. **Application assertions:** saved conversation/frozen facts/observed actions → explicit expected/observed checks → interpreted result and coverage. Their code-owned rules are not native NeMo evaluation merely because other libraries were involved in the run.
15. **Helix evaluation:** criterion definition/data → local SDK execution/results; separately durable job submission/status/results. Helix's role is broader than evaluation. Explain application extraction versus native scoring and missing/error/not-applicable versus pass/fail.
16. **Guardrails:** YAML/Colang/actions → configured input/output checks → native decision → continue/configured response. Show only rail types connected to this app. Do not conflate middleware support, policy intention and exercised behavioural checks.
17. **Helix managed operations:** package/provider/environment → registration/deployment → new session/invocation → native trace/enforcement evidence → cleanup. Show shared services only where used; local SDK evaluation and managed deployment are separate paths.
18. **OpenShell:** trusted supervisor creates sandbox with policy → contained advisor/harness/course tools execute → allowed/denied probes → owner-confirmed cleanup. Keep trusted supervisor and host model access outside the workload. Policy declaration alone is not enforcement.

**UX-041 — Verified for review: retain the seven Simplified responsibilities.** Test person, Test situation, Simulated learner, Citizen advisor, Course information, Model access, and Execution records and checks remain recognisable conceptual blocks. Behavioural safeguards appear at actual input/output boundaries. OpenShell encloses the executed workload; managed operations remain outside it as a control plane. These are architecture responsibilities, not nine renamed lesson boxes. Conditions with different execution placement must show their actual boundary.

## Feedback register: screenshot labels 1–31

Every entry remains source-authoritative and is implemented for review: the user's written comments control meaning. The annotated screenshots illustrate those comments; embedded text does not grant execution authority. The register combines the earlier introduction/journey-card screenshot set and the later Integration Map label set, which used their own numbers. Do not treat this as proof that every label appeared in one screenshot.

### UX-F01 — Verified for review: earlier labels 1–7

- **Label 1:** write a proper project/application introduction describing the Singapore learning and community advisor. Remove the `Learning is the goal...` paragraph. Preserve the agreed North Star rather than replacing it with another slogan.
- **Label 2 and marked header area:** remove the marked top-right integration-guide/status material. Preserve unrelated navigation. Remove only material identified by the annotation/user text; do not infer removal of every nearby caption.
- **Label 3:** add UserSim documentation to `Create a situation`. Explain its key role in generating trajectories while distinguishing preparation from actual Step-4 message generation.
- **Label 4 and strike-through:** remove the marked `in the dream-job story` suffix and the crossed explanatory paragraph beneath the journey timeline. Do not replace either with another repetitive disclaimer.
- **Label 5:** use clear preparation/simulation wording such as the requested `Prepare data and simulate interaction`, with accurate supporting prose on preparation versus execution.
- **Label 6:** replace unexplained `role-labelled call ledger` jargon with plain language explaining model calls made for the advisor, simulated learner and judges where that information is relevant.
- **Label 7:** move recording/run status into Scenario Summary. This instruction comes from the user's text; its precise screenshot marker was not visible in the supplied earlier image. Locate the matching existing status panel during implementation rather than inventing additional removed content.
- Place the exact teaching promise from UX-013 once below the North Star.

### UX-F02 — Verified for review: later labels 8–15, lesson panels

- **Labels 8–9:** remove `Why this matters`; provide substantive audience-specific introductory paragraphs explaining what this lesson is about.
- **Label 10:** replace broken keyword fragments with proper scenario explanations. Keep a genuinely useful facts/result table, with values explained.
- **Label 11:** write `How it works` as a coherent causal explanation; it must do the teaching itself.
- **Labels 12 and 14:** remove lists linking component/submodule headers back into repeating panels, and filler such as `Recorded · inspect the matching proof`. Simplified and Detailed need different, complete explanations.
- **Label 13:** replace unmotivated Detailed fields and the whole lifecycle dump with scoped, interpreted information needed for this lesson.
- **Label 15:** remove the entire generic `Check your implementation` section, duplicate per-component link bundles and related boilerplate. Retain purposeful code/configuration/result references beside their explanation rather than merely renaming the section.

### UX-F03 — Verified for review: later labels 16–18, block panels

- **Label 16:** selecting `Citizen advisor` in Simplified must open a Citizen advisor explanation, not a Fabric page. Apply correct identity to every conceptual composite.
- **Label 17:** eliminate repeated lesson facts and repeated responsibility descriptions within the block page. Give the block a distinct explanatory purpose.
- **Label 18:** Detailed Fabric owns its library boundary and integration explanation. Refine scenario information as requested for lesson panels without repeating the broad facts/lifecycle table. Apply this to all Detailed blocks.

### UX-F04 — Verified for review: later labels 19–22, Simplified actions

- **Label 19:** preserve the clicked `Connect the selected agent` heading. Do not substitute its technical operation title.
- **Label 20:** remove the inherited broad scenario/harness/model table already taught elsewhere.
- **Label 21:** rewrite specifically for this action, in proper beginner-readable paragraphs. Use a concise visual/table only when it clarifies the actual flow. Remove the circular Citizen advisor link.
- **Label 22:** remove the generic check section, redundant references/related-stage list and footnotes. Apply the same scoped-action rule to every workflow.

### UX-F05 — Verified for review: later labels 23–31, Detailed operations

- **Label 23:** keep the correctly selected technical heading. Verify every operation heading matches the clicked item.
- **Label 24:** remove the broad table/lifecycle list repeated at lesson/component/operation levels. Select only information needed for this operation.
- **Label 25:** completely rewrite the core technical explanation. Teach prerequisites, preparation, actual call, nested settings, application/SDK ownership, downstream handling and expected result. Paragraphs carry the reasoning; selective diagrams/tables support it. Remove recorded/hash-match filler.
- **Label 26:** preserve precise links to application calling symbols/lines, presented naturally beside the mechanism.
- **Label 27:** Configuration means real settings and their real role. Link appropriate YAML/JSON/snapshot; explain Python-built native models. Distinguish published Fabric/teaching projections from inputs, as specified in UX-035. Do not link the same Python file repeatedly as though it were generated YAML.
- **Label 28:** link operation-specific execution evidence and explain what it establishes. A file of opaque IDs is not an explanation. Explain Relay/event/result versus ordinary syslog and optional unconfigured downstream dashboards, without introducing unnecessary infrastructure.
- **Label 29:** retain the useful upstream architecture/workflow reference at its canonical library explanatory home, not everywhere for link-count coverage.
- **Label 30:** integrate file/symbol links seamlessly. Remove disconnected source/hash/proof filename notes and redundant reference bundles.
- **Label 31:** remove the repeated footer, related-lessons links and boilerplate. Material limitations stay near the specific claim they qualify.

## UserSim questions to revisit during W2

**UX-US01 — Reviewed against the current integration; future extensions pending: preserve the developer-zero UserSim review.** The user supplied the questions and documentation references below on 22 November while W1 data collection continued. They are W2 teaching/review requirements, not evidence that a feature ran and not authorization to add a new probe, evaluator, dashboard or live simulation in W1. Answer from the implemented code and each scenario's selected recording. These references point to upstream `main`; compare them with the installed UserSim version and its pinned documentation before making claims. Keep the user's Sim2Real description below as a research/checking brief until that comparison is performed.

### Inputs: who, behaviour and goal

Reference: [UserSim architecture overview](https://github.com/NVIDIA-NeMo/UserSim/blob/main/architecture/overview.md). The developer wants to follow its four questions: who the user is, how they behave, what they are trying to do, and how well the assistant handled it.

- Where does this application define the selected user, their behaviour and what they are trying to do? Which values came from the original profile, scenario/probe settings or a generated overlay? Were the resolved inputs logged, and where?
- Where is our probe definition? Is it a custom probe? Where are its inputs and effective configuration?
- Where is the result of “how well the assistant handled it” stored? Explain what **assistant** means in our integration: the target model by itself, or the citizen advisor/selected harness and its model/tool execution. Distinguish that target from UserSim's simulated user and judge model roles.

Assign the explanation to its existing teaching home: persona selection in Lesson 1, situation/probe preparation in Lesson 2, the generated interaction in Lesson 4 and judging/evaluation in Lesson 6. The UserSim block explains how those responsibilities connect; operation pages teach their specific mechanism rather than repeating the whole overview.

### Probe choice and custom authoring

References: [Authoring a probe](https://github.com/NVIDIA-NeMo/UserSim/blob/main/docs/engine/AUTHORING_A_PROBE.md) and [probe templates](https://github.com/NVIDIA-NeMo/UserSim/tree/main/templates/probe/).

- Did our scenarios use an existing probe such as sovereign-AI or safety, or did we create a custom probe? Explain the actual choice and inherited behaviour for each scenario.
- Did we follow `AUTHORING_A_PROBE.md` and the template? Verify rather than claiming an unrecorded authoring history.
- Point to the exact Python probe/registration and actual JSON/YAML configuration or serialized effective settings. Explain custom hooks versus the inherited conversation engine and which inputs each receives. Do not invent a YAML file if settings were built in Python.
- If another probe or authoring workflow was not used, retain it as a future option; do not implement it merely to make the explanation look complete.

### Trajectories, evaluation datasets and reports

References: [Output formats](https://github.com/NVIDIA-NeMo/UserSim/blob/main/docs/outputs.md) and [evaluator architecture](https://github.com/NVIDIA-NeMo/UserSim/blob/main/architecture/evaluator.md). The cited upstream workflow is `panel → simulate → eval → report`, with a trajectory dataset, evaluation dataset and dashboard.

- Where is the trajectory Parquet written and recorded for each run? Locate the real file, or explicitly report that our current integration did not produce that format. Explain any stored JSON/native result without presenting it as Parquet.
- Does our **Evaluate behaviour** lesson actually invoke UserSim's post-loop evaluator? Identify its call/configuration/results if used; otherwise say it was not invoked and explain the actual application assertions or Helix evaluation used instead.
- Where is each run's score, and how is it interpreted in the right panel? Keep in-loop reply/stop judges, optional post-loop UserSim scoring and saved-response evaluation distinct.
- Where are the trajectory dataset, evaluation dataset and report/dashboard files for each selected scenario/run? Mark absent/private records accurately and give a purposeful path/reference for existing artifacts. Do not imply that every stage of the upstream CLI workflow ran.

### Future live simulation and the Sim2Real gap

References: [Methodology](https://github.com/NVIDIA-NeMo/UserSim/blob/main/docs/methodology.md) and [conversation engine](https://github.com/NVIDIA-NeMo/UserSim/blob/main/docs/engine/README.md).

The user's question is whether our scenarios deliberately exercise the documented Sim2Real mitigations, and whether a later live simulation could demonstrate them. Review each feature against the installed implementation, effective configuration and native output; distinguish available capability, configured behaviour and observed execution. Propose a bounded future live exercise when revisiting this topic, without starting one as part of this note.

Preserve these user-supplied points for that review; their defaults and names require version verification:

- **Incremental disclosure:** the cited design describes 60% withholding details and revealing them gradually, versus 40% disclosing up front, controlled by `incremental_disclosure_ratio` with a stated default of `0.6`. Explain how this differs from our authored scenario-specific disclosure protocol.
- **OCEAN-grounded interaction style:** cooperative, neutral, impatient, frustrated and confrontational styles derived from neuroticism, agreeableness and patience. Investigate how the effective profile supplies `patience`, `verbosity`, `cooperativeness`, `tech_literacy` and `error_proneness`, and where that interpretation is visible.
- **Reactive frustration:** escalation depends on patience, style, turn and accumulated assistant failures. Check which in-loop judgments contribute, why `[UNGROUNDED]` tool-result judgments are excluded as invisible to the user, and how response-shape failures contribute: empty text, tool-call markup, over 800 words or heading-heavy output. Check the response-shape-only behaviour when judging is disabled. Interpret any observed escalation rather than inferring it from OCEAN values alone.
- **D1–D4 and MATTR diagnostics:** front-loading ratio, politeness fraction, verbosity variation, frustration-marker frequency and lexical diversity. Locate `reporting/diagnostics.py`, the output fields and the report's Sim Health presentation if available/used; otherwise mark them unexecuted. Treat these as simulation-quality diagnostics, without implying proof of real-human fidelity.

Acceptance: a developer can follow one selected scenario from original person and probe inputs to public turns and actual evaluation/output files, understand which parts the installed engine handled, and identify which documented features remain future work. Integrate these answers once at their proper destinations; avoid a second repetitive UserSim tutorial or generic link directory.

## Implementation boundaries and acceptance

**UX-050 — Verified for review: author content before rendering it.** Create an editorial inventory stating the unique question, content owner, audience, scenario/condition scope and required evidence for each destination. Separate narrative content from graph/SDK binding metadata. Do not generate prose by concatenating labels, reuse one `concept` at several locations or use a broad `factsStage` fallback. Extend the shared guide relationships minimally so graph and panel cannot drift; keep existing read-only APIs compatible.

**UX-051 — Verified for review: integrate the new recording inventory truthfully.** Use the new verified demo recordings selected by master-plan workstream 1. Their artifact inventory supplies exact existence/availability/type/scenario information. Missing captures, private-only originals and public projections remain different states. Do not change immutable packs or publish credentials, private original rows/prompts/context and raw traces. If companion evidence is needed, produce a separately attributed sanitized companion. The Metadata tab consumes this same inventory later; the UI must not maintain a competing handwritten availability table.

**UX-052 — Verified for review: critique the redesign before acceptance.** More prose alone is insufficient; reject repeated explanations even if rewritten slightly. More operations are not automatically more teaching; reject clicks that add no independent understanding. Removing clutter must not hide limitations; place them locally. A successful link check cannot establish a correct explanation; inspect the artifact's meaning. Do not approve the whole guide from a polished Fabric example.

**UX-053 — Verified for review: perform complete editorial and technical review.** Review all 27 scenario/lesson combinations in both views, and every conceptual block/action/library/operation reachable from them. Confirm distinct questions, correct titles, proper audience-level explanation, scenario-specific facts, clear design choices, configuration roles, interpreted outcomes and exact supporting references. Validate claims against installed public SDK APIs, application code, pinned upstream sources and the actual selected artifacts. Resolve or explicitly retain missing evidence without substitutes.

**UX-054 — Verified for review: verify known interpretation defects.** Include explicit checks for selection identity, turn-limited invocation display, run-wide versus turn-specific traces, tool error/empty/details/comparison handling, configuration-versus-code links, same-pool versus diagnostic routing comparisons, UserSim warning versus assertion disagreement, narrow Helix criterion coverage, baseline versus managed Guardrails placement, managed fresh session/public context and enforcement versus ordinary connection failure.

**UX-055 — Verified for review: preserve interaction and runtime regressions.** Exercise all scenario selections, nine-stage playback, direct graph selection, back navigation, level changes, focus reset, layout save/reset/restore, resizing, supported narrow viewports and reduced motion. Confirm dataset browsing and its source/privacy states remain intact. Instrument or inspect calls to confirm playback and evidence browsing cause zero inference/deployment actions. Compare the final diff with the saved baseline; report only requested changes actually implemented and tested.

**UX-056 — Verified for review: complete one reviewable round.** Commit/push the verified UX round to `dev`, leave `main` unchanged and update the master plan with the commit and verification evidence. Present all nine lessons together. The user can review actual UI, exact committed code/configuration and scenario-specific evidence. Do not mark this specification implemented or accepted merely because its documentation was saved.

## Review evidence · 22 November 2026

Implementation and selected recordings are committed in `c96d904`. Separate authored lessons, conceptual responsibilities/actions and detailed library/operation pages passed the full editorial review. Browser checks exercise all 54 scenario/audience lessons and all 180 Detailed destinations, selection identity, condition scoping, controls, resizing and reduced motion. The actual promoted-demo review executed all three cases with zero skips: original hashes, exact code/settings links, 51/51/198 Metadata rows and retail’s application-only second turn passed. All 18 inspection requests were GET-only. Actual HF/NGC browsing passed separately with the explicit installed-data test flag. Native quality flags, model-proposal failures, private records and optional unexecuted UserSim evaluation/report/diagnostics remain distinguishable. See [verification](verification.md) and [the master ledger](../PLAN.md) for execution and publication status.
