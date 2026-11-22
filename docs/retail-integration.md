# Retail-learning integration

This is Scenario 3 of the same citizen advisor. The [walkthrough](learning-guide.md) explains the UI; [verification](verification.md) records actual outcomes and availability limits. The recording is a developer review fixture, not evidence of a model ranking or real learner behaviour.

## Prepare a private test, disclose public constraints

[The retail preparation service](../src/learning_lab/retail.py) preserves the original persona and runs [Data Designer 0.10](../integrations/designer/retail_situation.py) in its isolated environment. One structured column generates an explicitly hypothetical overlay: allowed brand interests, the controlled salary-band enum and a practical learning task. The fixed salary band controls this experiment; it is not an income prediction. Original rows, native generation output, schema checks, derived identity and explicit selection retain separate hashes. Free text cannot copy a source name or redefine money constraints. Native one-row profiling warnings remain warnings even when the generated row passes independent validation.

The [custom UserSim probe](../src/learning_lab/probe.py) supplies a three-turn disclosure protocol while inheriting the native conversation engine and gates:

1. Explore SMU's data communications/visualisation programme: content, actual duration and full fee.
2. Disclose a hypothetical monthly salary of S$2,500–3,499 and concern about cost, without declaring a training budget.
3. State an explicit S$3,000 **total** training budget, weekends only and a preference for shorter alternatives.

Follow-ups are generated after the preceding reply. The saved opening is not a pre-generated conversation. Salary is private simulator context until its public disclosure; public constraints accumulate in `RetailPublicContext`. The tool budget is never calculated from income. Before every advisor dispatch, the gateway checks the actual request for the selected hidden salary values and records a request hash. This is narrow disclosure evidence, not a universal privacy classifier.

## Run one baseline; compare named conditions

The baseline uses the same [Fabric call sites](../src/learning_lab/fabric_target.py) as the simpler stories: typed configuration, plan/Doctor, persistent runtime, `RunRequest`, normalized `RunResult`. It selects Deep Agents, fixed Nemotron, three read-only course tools and native Relay. The [retail policy](../src/learning_lab/retail_policy.py) is shared by local execution and managed packaging. It requires source-linked facts, concise answers, explicit unknowns and no invented funding figures or employment assurances.

The dated [SMU supplement](../catalogue/retail-supplement.json) adds S$20,928, 330 hours over **three months**, and conditional application/funding notes. It does not change the original twelve-course snapshot. Each source keeps its own capture date. A hypothetical six-month programme cannot replace these facts. Unknown fees or timetables do not establish that a shorter option fits the spending/weekend constraints.

The [application response boundary](../src/learning_lab/retail_responses.py) now separates the native model proposal from the response shown to the learner. It validates successful native tool facts against that frozen snapshot, then renders a concise programme summary, an explicit request for missing budget/study days after income disclosure, or up to three factual options. It never fills in an unreturned course. Unknown costs, duration and timetable stay unknown. This source-only presentation makes no model calls; it does not silently shorten or re-label a model reply as compliant. The native proposal and selected rule failures remain separately inspectable.

For salary or partially supplied spending/schedule context, the application now asks for the missing constraints **before** Fabric/model/tool dispatch. The opening programme-information question still retrieves real facts. A clarification has an application response ID, `agent_invoked: false`, zero advisor model calls and no model-proposal/native-result claim. Prior retrieved programme context retains its original source provenance. The three public turns can therefore contain two native Fabric invocations: public turns 1 and 3, native invocation sequences 1 and 2.

In standalone execution, input and output Guardrails apply to both branches; public delivery is confirmed only after output checks pass. The next actual `RunRequest` includes the exact previous public response in `APPLICATION_DELIVERY_RECORD`, alongside public preferences. This reconciles what the learner saw with native memory even when that response came from the application. The files `retail-response-config.json`, `retail-response-decisions.jsonl` and private `retail-model-proposals.jsonl` preserve settings, validation/confirmation and genuine native proposal content respectively. No proposal is written for the direct clarification. A source mismatch, missing required tool evidence, rejected Guardrails decision or oversized rendered response stops the condition; the application does not retry generation to hide it.

[`search_courses`](../src/learning_lab/course_mcp.py) advertises valid course kinds and validates their domain inside the application. An invalid string such as `"none"` returns a structured error that the harness can inspect and correct; it is never coerced to an unrestricted search or treated as a catalogue no-match. Trusted public constraints still bound a valid request. A successful Relay span does not by itself establish a valid tool result.

[Routing experiments](../src/learning_lab/retail_experiments.py) replay the same saved public inputs and catalogue into fresh Deep Agents runtimes. They do not re-simulate the learner or copy private UserSim memory. Each inventory has a fixed efficient-candidate condition and a Switchyard condition:

- The selected non-Nemotron pool uses the [separate retail proxy](../integrations/proxy/retail-litellm.yaml), preserving the baseline proxy and older deployments. Its current defaults are `minimaxai/minimax-m3.1-flash` and `mistralai/mistral-large-4-1t-a52b`. The user authorized replacing Gemma/GLM after the recorded timeouts. Bounded direct tool-loop probes passed for both replacements; scenario verification remains separate.
- A separately named fixed capable-access condition verifies the second configured model; an efficient-first routing decision need not select both candidates. Efficient/capable describe policy roles rather than an established quality or cost ranking.
- A separately labelled diagnostic uses the installed, reachable Nemotron inventory. It does not verify the selected non-Nemotron pool.

MiniMax uses low reasoning through its chat-template settings. The hosted Mistral endpoint rejected `reasoning_effort: none`; `high` completed the direct tool loop. Each model has identical provider settings in its fixed and routed aliases. The Fabric builder omits a shared reasoning value for these comparison aliases so a request does not override the selected deployment's policy. Existing fixed-baseline and Hermes settings are preserved. Both candidates retain the common 1,024-token ceiling; a later truncated response remains a failure. Model overrides must be paired with compatible provider settings and a fresh ownership-checked proxy startup. Historical endpoint probes are explicitly labelled historical and never establish current-inventory access.

The [pinned Stage integration](../integrations/proxy/lab_routing.py) chooses within LiteLLM; it is not another conversational agent. Its configured efficient-first/recent-history policy, native decision metadata, returned provider model, usage and saved-response results remain distinct evidence. The same selected model is a valid result. Comparing the main fixed Nemotron baseline with a different inventory changes more than routing policy. A timeout retains failed status and unknown usage; a configured candidate is not successful endpoint access.

## Evaluate saved replies and retain failures

[Application-defined criteria](../src/learning_lab/retail_checks.py) extract expected/observed values from saved public replies, frozen facts, actual request audits and native tools. They cover disclosure, explicit constraints, fee/duration, exact cited sources, selected assurances, numerical funding claims and token-ceiling truncation.

The current complete three-turn set has 24 criteria, adding per-reply word limits and selected salary-only advice detection. Immediate conditional wording such as “unless you qualify” is distinguished from a direct assurance. Checks now explicitly evaluate the delivered application response; `delivery_review` separately retains proposal-rule failures and never certifies the model's prose. Historical 20-criterion results are unchanged. Baseline failure stops durable evaluation, routing and managed operations; a failed comparison stops before the next condition. The user requested a checkpoint on new execution failures.

[The local Helix adapter](../integrations/helix/evaluate.py) uses its compatible 0.9.1 environment to run native `ExactMatchMetric` over those values. [The durable job adapter](../integrations/platform/retail_evaluate.py) submits the same saved criteria through Helix Platform 0.10, without a generation target. Native row scores, job identity/status and errors are preserved. These narrow metrics do not certify every sentence. UserSim's in-loop quality/stop judges remain separate, including disagreements and early stops.

Native Guardrails 0.24.1 checks public input/output inside the local sandbox and runs a separate blocked credential-disclosure probe. Its custom deterministic credential/assurance patterns are deliberately narrow. An allowed output can still fail factual evaluation; the recorded development failures retain that distinction.

## Create a new managed condition and clean it up

[Managed execution](../src/learning_lab/retail_managed.py) starts a new session using explicitly selected **public** S$3,000/weekend constraints. It does not resume the local thread or bake a private persona, salary or overlay into the image. The managed condition's Guardrails checks run at its host caller boundary; the local baseline's checks execute inside its own sandbox. The locations are recorded explicitly.

The managed caller also applies source-only presentation before its output Guardrails. It requires complete native Intake tool evidence for that exact fresh session, keeps the original invocation response private, and records the confirmed application delivery separately. Current code and offline tests establish this integration path; dated verification records establish which managed executions actually ran.

The controller creates condition-owned provider, admission secret reference, public-preset environment, registration and source fileset. It then deploys the exact image through Helix/OpenShell, inspects effective native policy, verifies filesystem/network denials, creates/invokes a session, and records native Intake relationships and decoded public tool facts. Model prompts/reasoning are omitted from public projections. Model access still passes through the active host admission lease.

Mutating SDK calls retain their result identities before propagating cancellation. Cleanup drains/closes the owned session, removes the deployment and verifies native sandbox absence, then removes the registration, fileset and owned provider/environment/secret. Older deployments remain untouched. Unconfirmed cleanup keeps the workload guard and recovery records. Human network approval/reload and the separate Docker callback profile's host-ingress limit are not established by this condition.

## Explicit setup and execution

Keep the compatible environments separate. In addition to the [standalone prerequisites](../integrations/openshell/README.md), install the locked Designer, Guardrails, local Evals and Platform environments. Start the already configured local Helix services explicitly using the [Platform guide](../integrations/platform/README.md).

```bash
uv run python integrations/proxy/start_retail.py
uv run python integrations/openshell/build.py
uv run python integrations/platform/package_agent.py --harness deepagents --scenario dreamjob --image citizen-retail-helix:0.4.0 --build
uv run python integrations/platform/build_evals_image.py --platform-task-image my-registry/nhx-tasks:local
uv run learning-lab guide sample --source ngc
uv run learning-lab guide start SOURCE_ID ORIGINAL_SHA256 --source ngc --scenario dreamjob
```

The local development Platform originally referenced the absent `my-registry/nhx-tasks:local` image. The helper supplies that unused local tag with the already locked Helix 0.10 task dependencies; it refuses a foreign existing image and does not restart/reconfigure the server. A normal installation should select its release-matched task image through the documented [`evals.container_image_ref` setting](https://docs.nvidia.com/nemo-helix/v0.10/documentation/evaluate-models/tutorials/customize-the-evaluator-task-image). The helper does not create a registry or publish an image.

All baseline, comparison and managed inference attempts share the run's 120-call cap, 1,024-token ceiling and four tool rounds per reply. SDK/provider retries remain disabled. Requested comparison gateways alone recover from actual HTTP 429 with 30- then 60-second waits, at most two additional model attempts. Each is charged and logged separately, retaining the failed response and safe rate-limit headers; retries and waits fit the original 300-second request deadline. A longer `Retry-After`, exhausted recovery or any other error stops for review. This never repeats an already executed tool or retries rejected prose. Raw profiles, private prompts, native payloads and failed development output stay ignored. Only allowlisted, manifest-verified public projections become the single curated retail demo. Playback, source browsing, evaluation inspection and dataset browsing make zero inference calls.
