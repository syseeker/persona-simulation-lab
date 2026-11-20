# Build-Together Learning Guide

## Start with the application story

The [North Star](project-goals.md) is to teach a developer how the stack integrates into an application. Use the UI throughout this walkthrough. CLI commands are alternative developer entry points, not mandatory detours between lessons.

Start the web app using the [README](../README.md#run-locally). Offline demo exercises a real harness and MCP with scripted model replies. Live mode generates model outputs and UserSim conversations; label which mode you demonstrated. Installing a key does not turn an offline result into live evidence.

Choose **Guided walkthrough**, start with one source profile and keep strategy comparison off. Retain the selected run/episode as you move among conversation, evidence, evaluation and source code. Extra model calls should answer a named question; rereading evidence requires none.

## Story 1: A sourced recommendation

Choose the photography story: a beginner Saturday class within S$50 before funding. Observe the learner message, search request, tool results and advisor reply. Check the official source and any unknown additional costs.

Follow the saved profile and scenario separately. The source supplies synthetic interests and background; application constraints such as a budget/day are explicit scenario inputs. UserSim receives profile context; the advisor receives public learner messages and trusted explicit application constraints, not the hidden profile or judge rubric.

Open the run's evidence inspector. Read UserSim activation roles, the course MCP requests/results, gateway calls and outcome. Use a code reference to locate the shared service, target harness and tool implementation. A saved result may contain missing evidence; the UI should say so instead of reconstructing it.

## Story 2: A material budget difference

Choose baking with a total budget of S$120. Inspect known material fees and exclusions. Create a comparison at S$130 while keeping the selected source input and other configuration fixed. This is a purposeful second condition: the known material fee changes which listing fits.

Compare the two saved conditions and their tool evidence. A second LLM conversation can vary stochastically; it is not an exact replay of the first transcript. Reusing exact source rows and catalogue facts controls inputs, not model randomness.

## Story 3: An honest no-match

Ask: “Hello, I want to learn how to play board games.” This snapshot has no supported board-game class. The useful response explains the catalogue limit and can ask whether the learner wants another topic. Game design is not a substitute for playing board games.

Inspect a failed/missing answer as well as a successful one. A response containing `[ERROR: Max turns (10) exceeded]` is runtime failure evidence; it must not appear as a successful simulated advisor answer or receive a passing quality score. Distinguish UserSim public conversation turns from a harness's internal model/tool steps.

## Read Relay without hunting for files

Choose **Deep Agents + Relay** for a run when you want native observability. Open its evidence inspector and select the episode. Follow native parent/child relationships and matching start/end UUIDs across agent, model and tool scopes. Inspect raw events when a normalised summary is incomplete.

Use the artifact list to view the saved Relay file and copy the exact local run path. Direct Relay commonly writes the episode's `relay.jsonl`; Fabric writes beneath its episode's `fabric-traces` directory. The UI resolves the actual saved artifact instead of requiring a guessed UUID/path.

Compare this with the gateway ledger. One assistant activation can perform several model calls; the experiment also has simulated-user, judge and summary calls. An unknown usage entry is not zero usage. Relay target instrumentation and the coordinator's full-workload log have different responsibilities.

## Inspect Fabric and the harness

Choose **Fabric + Relay** and inspect its typed configuration/plan, selected harness, runtime/invocation IDs, lifecycle events, tool surface and Relay capture. Ask a follow-up within the same session, then explicitly start a fresh condition to inspect memory isolation.

Deep Agents and Hermes are different harnesses; Fabric is the runtime integration layer. Hermes requires its separately pinned Python/environment setup. Compare harnesses on a fixed model first. An unavailable Hermes environment should produce actionable readiness information, not a fallback to Deep Agents.

Use the code references to connect the plan to `build_config`, runtime start/invoke/close and course MCP registration. Configuration values that an installed adapter ignores must not be presented as effective limits.

## Inspect model routing

The integration profile uses LiteLLM for configurable provider transport and Switchyard for the explicit routing experiment. Fixed-model runs isolate a harness comparison; routed runs teach model-selection behaviour.

Inspect actual routing/model-call evidence, the selected endpoint/alias and the corresponding integration configuration. A gateway ledger records admitted calls; a configured Switchyard policy alone does not prove that policy made a decision. Provider credentials stay outside browser responses and agent environments. NIM, Brev and frontier-model endpoints are provider choices, independent of where Helix Platform runs.

## Read Helix criteria before totals

Evaluate the saved replies in the UI. Inspect each criterion's episode/turn, assertion, actual/expected result, reason and saved evidence. Open an intentionally failed or unsupported criterion before interpreting the total.

The local implementation uses deterministic application assertions passed through the real Helix Evals SDK. It is a narrow test of identifiers, links, explicit constraints and selected unsupported assertions, not a semantic certification of every sentence. Missing answers, execution failures, missing snapshots and inapplicable assertions have distinct meanings; a generic “8/8” does not establish end-to-end correctness.

Evaluating saved replies does not regenerate them. A fresh benchmark or prompt comparison is a separate explicit experiment. [Platform deployment](#follow-the-deployment-boundary) is also separate from local SDK scoring.

## Explore personas and generate data

Open **Data workbench**. Browse/filter the full pinned local HF corpus, inspect all fields and select a row. **Random profile** samples the available filtered corpus; lock selected source IDs for the next simulation. Three age groups are coverage categories, not the set of available personas.

Choose **Singapore NGC Extended** to inspect its readiness/schema. It is a separate Singapore dataset with independent access and behavioural fields. If the local dataset is unavailable or lacks required fields, stop that path clearly; do not silently substitute HF.

Use one of the three Data Designer operations:

1. **Generate learning scenarios:** source-seeded LLM generation of a goal, explicit hypothetical constraints and opening message.
2. **Add columns:** choose text, integer, decimal, boolean, enumeration or text list. Try hypothetical last drawn gross monthly salary in SGD and favourite brands; inspect the typed schema and field instructions.
3. **Generate additional profiles:** create new synthetic rows inspired by selected sources. Inspect their new identities and parent lineage; they are generated records, not additional original Nemotron rows.

Preview five rows by default. Generation is an explicit live operation and consumes the job budget. Read the original profile, generated fields, schema validation, native Data Designer artifacts and gateway calls. User-authored field instructions are data for closed generation templates; the UI does not accept executable code.

The saved generation job's call ledger shows each admitted call, role, requested/selected model, status and available usage. Unknown usage and failed attempts remain visible. Opening the ledger makes no model calls.

Select **Use generated data in the guided story** to map saved scenarios/fields to UserSim context or use a generated profile. Reusing saved generated rows makes no generation calls. Compare an original and its overlay under the same strategy only when you want to study that intervention; keep the original hash unchanged. Generated salary or preferences never establish eligibility or observed behaviour.

Data Designer 0.10 has a known one-row token-statistics profiling error. If generation succeeded and the independently validated native row was retained, the result records the profiling warning and unavailable statistics. The system does not rerun generation or fabricate a score to hide it.

## Follow the deployment boundary

Open the runtime/deployment view and inspect readiness before explicit Platform operations. Local reference Platform and existing remote Platform are different connection profiles. Registration, deployment, invocation and cleanup should produce actual resource/session/deployment evidence and logs.

From the saved story's deployment lesson, explicitly prepare a new managed condition. Inspect its source run, episode, first public learner input and original preferences. Preparation makes no Platform or model calls. Session creation and invocation remain separate explicit actions. This starts fresh managed conversation memory; it is not a replay of the earlier replies or a claim that the packaged catalogue matches the simulation snapshot.

The native OpenShell reference uses a reviewed public preset: photography, S$50, Saturday. Its image contains the hash-checked constraints and read-only catalogue; both the advisor and course MCP process run inside the sandbox. This keeps the supported native encrypted credential driver unchanged. A selected story with different preferences cannot silently become that preset; the inspector blocks invocation when they differ. The separate Docker profile implements changing authenticated session constraints, but its live invocation is blocked by host ingress on the recorded machine. The current OpenShell/Helix versions cannot share that dynamic credential path without an additional credential-driver compatibility change; the lab does not silently install one.

Create a fresh managed session, invoke up to three public turns, then read **deployment logs and native trace**. Intake trace/span counts come from Helix; they are separate from a local `relay.jsonl` export. The model-call ledger links each admitted call to its actual proxy selection and usage. Close the session before undeploying. If an invocation fails or the worker restarts, the retained-session notice blocks another learner until native runtime cleanup is confirmed.

The pinned Fabric Hermes adapter does not propagate the Platform session ID into native Relay export. Its managed-session inspector reports that correlation limit when no attributable trace is found; it does not imply that export is disabled. Use Deep Agents for the verified managed-session Intake walkthrough, or inspect the local Fabric/Hermes run's saved Relay artifacts. The [verification record](verification.md) preserves the native diagnosis and answer-quality failures.

If normal closure fails, or a retained session has uncertain/running runtime state, **Stop failed deployment and close session** provides explicit recovery. It stops the owning deployment and all its sessions. The guard remains until native evidence confirms the runtime stopped, the deployment was removed and the session closed; a deleted Platform record alone is insufficient. Rejected or incomplete recovery stays visible. After successful recovery, deploy again before starting another conversation. Recovery receipts remain local for inspection and retry.

To inspect an earlier deployment attempt without inference, paste its job ID into **Read saved operation**. The [verification record](verification.md) includes observed job IDs. This loads the saved result, error and call ledger; it does not reopen a closed conversation. Retrieving native logs remains a separate explicit inspection.

Inspect the OpenShell policy and verify the agent and its course tools execute inside the intended sandbox. A local configuration file, installed CLI or unprobed endpoint is preparation, not verified enforcement. Keep the [verification record](verification.md) open when presenting this lesson so unsupported/environment-blocked paths remain clear.

## Where to go next

Use the [architecture and source map](architecture.md), [contracts](contracts.md), [persona rules](personas.md), [compatibility record](sources.md) and [current plan](../PLAN.md). The [v0.1 walkthrough](history/v0.1/docs/learning-guide.md) remains available as historical material, including its earlier limitations.
