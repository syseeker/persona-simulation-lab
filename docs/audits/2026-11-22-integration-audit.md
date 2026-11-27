# Integration audit — 22 November 2026

This is an append-only audit record. The original report below describes `a4a5f73`; later findings, corrections and updated status reports are appended rather than replacing existing content. Repository links are relative for portability. This report records requirements and findings; `../../PLAN.md` remains the single delivery plan.

## Original read-only report — baseline `a4a5f73`

**Most of the requested implementation is present, but I cannot honestly mark everything complete.** This audit found remaining gaps in the diagrams, saved selection, UserSim teaching, private-file navigation and housekeeping.

I audited `dev` at **`a4a5f73`**, inspected source and saved evidence, and checked archive/publication hashes. **No files, application state or running workloads were changed.**

**Status:** Met = implemented and supported by evidence; Partial = a specific gap remains; Deferred = deliberately outside the current implementation; Review = needs your assessment.

---

**1. The application and three scenarios**

| Your ask | Current version | Status |
|---|---|---|
| Teach developers through a Singapore learning and community advisor | The North Star, application introduction and scenario-based guide are present. | **Met** |
| Connect concept → components → application call → configuration → result → proof | Separate teaching pages, inline code/configuration references and recorded observations implement this structure. Some gaps are listed below. | **Partial** |
| Photography: simplest preset, one turn, Deep Agents, fixed model, application assertions | Implemented without Designer, Switchyard, native Guardrails or Helix. | **Met** |
| Board games: two turns, Hermes, honest no-match, separate negative Guardrails demonstration | Implemented with its own conversation, persistent runtime and blocked credential-disclosure probe. | **Met** |
| Retail: three turns, Designer, disclosure, routing comparisons, Guardrails and Helix evaluation/deployment | Implemented. The salary-only second turn uses the approved application clarification branch; native agent execution occurs on turns 1 and 3. | **Met, with quality limits** |
| Each scenario must have its own evidence | Explicit demo bindings prevent another scenario’s records being substituted. | **Met** |
| One curated demo per scenario | The UI has no run-history selector. Historical evidence remains preserved separately. | **Met** |

The selected recordings are:

| Scenario | Demo | Recorded application checks | Applicable capture requirements | Native UserSim quality flags |
|---|---|---:|---:|---:|
| Photography | `94e49df8…` | 9/9 | 28/28 | 0 |
| Board games | `aa445222…` | 11/11 | 31/31 | 1 |
| Retail learning | `8ce3ace2…` | 24/24 baseline | 181/181 across its conditions | 2 |

These are **recorded results**, not a fresh claim that the remote model endpoints are healthy now. Passing application checks also does not erase the UserSim disagreements.

The exact recordings and configuration manifests are indexed in [the current demo inventory](../configuration-evidence-inventory.md#current-demos-and-location-keys).

---

**2. Your nine-step teaching journey**

| Step and your expected explanation | Current implementation | Status |
|---|---|---|
| **1. Choose a test persona:** show the actual original, explain selection and identity preservation; UserSim has not run | Resolves the recorded original against the installed dataset, displays it, verifies identity and reports unavailable rather than substituting another person. Selection/hashing are labelled application-owned. | **Met** |
| **2. Create a situation:** separate original background, supplied constraints, Designer additions and generated wording | Explains authored situations for S1/S2 and Designer hypotheses for S3. UserSim preparation is distinguished from actual message generation in Step 4. | **Met** |
| **3. Build and connect the agent:** explain Fabric configuration, adapter, tools, model connection and startup | Explains the typed SDK configuration, plan, Doctor preflight, persistent runtime, MCP registration and Relay attachment. | **Met** |
| **4. Run the application:** follow UserSim → application → Fabric → harness/tools → normalized result → learner | Actual public conversations and invocation boundaries are present. Retail’s direct clarification is explicitly distinguished from a Fabric result. **The S2/S3 diagram omits the directed reply path through Guardrails.** | **Partial** |
| **5. Investigate execution:** explain why the answer happened using actual actions and returned facts | Selected-turn tool evidence, native Relay scopes, lifecycle records and separate gateway accounting are shown. Missing correlations remain explicit. | **Met** |
| **6. Evaluate behaviour:** show expected, observed, reason and coverage | S1/S2 assertions and S3 Helix scoring are distinguished from UserSim’s in-loop judges and unused post-loop evaluator. Native disagreements remain visible. | **Met, narrow coverage** |
| **7. Optimize model routing:** distinguish fixed routes, actual routing decisions and controlled comparisons | S1/S2 correctly say routing optimization was unused. Retail has completed fixed/routed comparisons and separately labelled diagnostics. **The selected comparison condition is not restored after reload.** | **Partial** |
| **8. Configure behavioural safeguards:** distinguish application restrictions, native checks and negative tests | Effective configuration, native decisions and separate negative probes exist. **The diagram’s return flow is incomplete, and managed placement is wrong.** | **Partial** |
| **9. Deploy with controlled access:** explain workload boundary, supervisor, policy, enforcement and cleanup | Standalone and Helix-managed execution have separate records and cleanup evidence. **The managed diagram still places Guardrails inside OpenShell although that condition checks at the host caller.** | **Partial** |

The component coverage includes Personas, Designer, UserSim, Fabric, Deep Agents/Hermes, MCP/catalogue, gateway, LiteLLM, Switchyard, Relay, assertions, Helix evaluation/jobs, Guardrails, Helix managed operations and OpenShell.

Official architecture references and the relevant operation subsets are present. **The diagrams are not yet fully faithful to every execution condition.**

---

**3. Your screenshot feedback—labels 1–31**

All labels are retained in [the feedback specification](../ux-review-spec.md#feedback-register-screenshot-labels-131). Recording a requirement is separate from satisfying it.

| Feedback | What I found | Status |
|---|---|---|
| **Earlier label 1:** proper project introduction; remove “Learning is the goal…” | Replaced with a concrete introduction to the advisor and the three tests. | **Met** |
| **Earlier label 2:** remove marked top-right badge/status | Removed. | **Met** |
| **Earlier label 3:** add UserSim to situation preparation/documentation | Added, with preparation versus execution explained. | **Met** |
| **Earlier label 4:** remove marked suffix and crossed paragraph | Removed. | **Met** |
| **Earlier label 5:** “Prepare data and simulate interaction” | Present. | **Met** |
| **Earlier label 6:** remove unexplained “role-labelled call ledger” jargon | Replaced with explanations of calls made for the advisor, learner and judges. | **Met** |
| **Earlier label 7:** move run status into Scenario Summary | Status is owned by the collapsible summary. | **Met** |
| Put your exact “Every lesson must answer…” statement beneath the North Star | Present once. | **Met** |
| **Labels 8–9:** remove “Why this matters”; write a proper introduction for each audience | Audience-specific introductory paragraphs replace that heading. | **Met structurally; Review for teaching quality** |
| **Label 10:** replace keyword fragments with meaningful scenario explanation | Coherent prose and scenario observations replace the fragments. | **Met structurally; Review for clarity** |
| **Labels 11–14:** explain “How it works” properly; remove circular component directories, filler and repeated dumps | Paragraphs explain cooperation. The old component-link lists and “Recorded—inspect proof” filler are removed. Broad setup facts are confined to their lesson. | **Met structurally; Review for depth** |
| **Label 15:** remove generic “Check your implementation” sections | Removed from the active teaching panel. | **Met** |
| **Labels 16–18:** Citizen advisor must explain that responsibility, not resolve to Fabric; Detailed Fabric must explain its own boundary | Conceptual and technical destinations have separate identities and content. | **Met** |
| **Labels 19–21:** keep “Connect the selected agent” as the Simplified action; explain that action without repeating the block | Plain-language title and action-specific explanation are present. | **Met** |
| **Label 22:** remove redundant checklist, related lessons and footer | Removed. | **Met** |
| **Labels 23–25:** technical operation title must match; explain actual preparation, mechanism, settings and expected return | Detailed operation pages are focused. Fabric’s configuration explanation now addresses the actual SDK classes and configuration contract. | **Met structurally; Review for teaching quality** |
| **Label 26:** link directly to the application call | Exact committed symbols/lines are used. | **Met** |
| **Label 27:** configuration means actual settings, not another Python link; explain JSON/native transformations | Actual settings captures and their roles are distinguished. Fabric’s native typed object versus public projections is explicitly explained. | **Met** |
| **Label 28:** logs must help diagnose execution, not merely show session IDs | Native scopes, tool inputs/results, invocation records and interpreted observations exist. **Finding private originals from the UI remains awkward.** | **Partial** |
| **Label 29:** architecture reference at one appropriate home | Library pages own their architecture links instead of repeating them on every operation page. | **Met** |
| **Label 30:** integrate code references naturally into the explanation | Purposeful inline references replace disconnected source-note bundles. | **Met structurally; Review for usability** |
| **Label 31:** remove generic integrity/related-lesson footnotes | Removed from the active teaching panel. Integrity verification remains internal. | **Met** |
| Apply this treatment to **all nine steps, scenarios, views and workflows** | All 54 scenario/lesson/audience combinations and separate block/action/operation destinations exist. The omissions below prevent a blanket completion claim. | **Partial** |
| Do not repeat substantive content across destinations | The old repeated tables and copied sections are removed; no exact repeated long teaching paragraphs were found. Whether the remaining conceptual overlap feels repetitive requires your review. | **Review** |

The Fabric explanation specifically now says that `build_config` constructs the **actual SDK `FabricConfig`**. Its nested classes group settings; they are not sequential translation stages. Public `fabric-config.json` and `framework-config.json` are explicitly described as review projections, not complete runnable inputs. See [the Detailed explanation](../../web/src/lib/teaching/detailedRuntime.ts).

---

**4. Other UI and navigation requests**

| Your ask | Current status |
|---|---|
| Alternating nine-step timeline matching the supplied design, with three phase bands | **Met.** It changes to a vertical presentation on narrow screens rather than using the old horizontal scrollbar. |
| Generic step names without product names | **Met.** |
| One Simplified map and one Detailed map | **Met.** Seven conceptual responsibilities expand into the relevant technical responsibilities. |
| Architecture blocks without competing step numbers | **Met.** |
| Permanent scenario dropdown; no repeated scenario labels/run-history controls | **Met.** |
| Changing scenario changes its summary and evidence | **Met.** |
| Enter map, switch level or reset layout: show the whole architecture; focus only after explicit interaction | **Met by source and prior browser verification.** |
| Highlight relevant operations and directional flows | **Partial.** Highlighting exists, but S2/S3’s reply arrows are missing. |
| Preserve scenario, lesson, turn, selection and layout | **Partial.** Most selections persist; comparison condition does not. |
| Preserve typography, colours, resizing, layout controls and reduced motion | **Met for this revamp.** |
| Remove confusing dataset explanation/audit sections | **Met.** |
| Subsequently remove “The main difference” replacement box too | **Met.** |
| Preserve HF/NGC browsing and their actual schema differences | **Met**, with a previously recorded actual installed-dataset browser check. |
| Playback and inspection must make zero inference/deployment calls | **Met by implementation boundary and prior browser verification.** |

---

**5. Configuration capture, evidence and Metadata**

| Your ask | Current version | Status |
|---|---|---|
| Rerun S1–S3 and capture previously missing applicable configuration/output | New demos have complete applicable capture coverage: 28/28, 31/31 and 181/181. | **Met** |
| Continue retaining existing and private outputs | Native originals remain private; public projections retain their relationship to originals. | **Met** |
| Add Metadata with `[module, steps, YAML/JSON file, status, location, apply to scenario]` | Exactly those six columns are implemented. | **Met** |
| Group by scenario and distinguish conditions | Scenario/condition filters and module/file/status search exist. Inventories contain 51/51/198 entries, including unused requirements. | **Met** |
| Distinguish EXISTS, PRIVATE, NOT EXIST, PARTIAL and NOT USED | Availability, access and execution state are represented separately. | **Met** |
| Distinguish configuration, calling code, native result and teaching projection | Implemented; no artificial requirement that every SDK needs a YAML file. | **Met** |
| Code links go directly to your GitHub repository | Committed code references are used. | **Met** |
| Log links identify the exact scenario/run/condition | Public recording links are specifically bound. | **Met** |
| Help developer zero locate private originals | Metadata shows private availability but deliberately hides host paths. **There is no convenient owner-facing locator to the current raw capture manifest.** | **Partial usability** |
| Do not expose private profiles, prompts, proposals or credentials | Private originals remain outside Git; only curated projections are published. | **Met within audited boundaries** |

I independently checked **393 published payload hashes**. Together with their nine manifests, these are the **402 publication files**. No mismatch was found.

---

**6. Your UserSim questions**

| Question/request | Current answer and status |
|---|---|
| Where are the person, behaviour and task defined and recorded? | **Answered.** Original selection, interpreted behaviour, scenario/probe configuration and resolved records are distinguished. |
| What does “assistant” mean here? | **Answered.** The external citizen advisor application, including its selected harness/model/tools—not the simulator or judge model. |
| Existing sovereign-AI/safety probe or a custom probe? | **Answered.** The custom `learning_advisor` probe uses inherited conversation machinery. Python registration/hooks and effective settings are referenced. |
| Did authoring follow `AUTHORING_A_PROBE.md` and its templates? | **Partial.** The question is preserved, but the teaching content gives neither a verified history nor an explicit “not established” answer. |
| Where are trajectory Parquet, evaluation dataset and dashboard? | **Explicitly absent.** This external-runtime integration stores JSON/native outcomes. It did not execute the optional CLI Parquet/eval/report workflow. |
| Does Step 6 use UserSim’s post-loop evaluator? | **Answered: no.** It uses application assertions or Helix. In-loop UserSim judgments remain separately visible. |
| Explain OCEAN-derived behaviour and authored disclosure | **Implemented**, including the distinction between original traits and scenario-controlled disclosure. |
| Revisit 60/40 disclosure, reactive frustration, response-shape handling, D1–D4 and MATTR against the installed version | **Partial.** The full requested explanation and explicit per-feature execution states are unfinished. |
| Demonstrate those Sim2Real features in a future live exercise | **Deferred.** Not demonstrated by these runs. |

These outstanding questions are still present in [the UserSim review register](../ux-review-spec.md#usersim-questions-to-revisit-during-w2); preserving them is not the same as completing their explanation.

---

**7. Execution failures and approved corrections**

| Your ask/decision | Status |
|---|---|
| Fix missing-budget/schedule behaviour before agent/tool execution | **Met.** Retail turn 2 has zero advisor inference and no fabricated Fabric invocation/result. |
| Validate the delivered response and retain the native proposal separately | **Met.** Source-based application delivery is explicitly identified. |
| Fix Gemma/GLM connectivity, or use another working non-Nemotron model as subsequently approved | **Approved replacement completed.** MiniMax M3.1 Flash and Mistral Large 4 completed the required comparisons. **Gemma/GLM themselves were not demonstrated repaired.** |
| Remove the shared reasoning setting only for comparison aliases | **Met.** The conflicting setting came from our builder; it is not established as an upstream Fabric SDK bug. |
| Handle HTTP 429 with bounded 30/60-second recovery | **Met.** The selected retail run retains a 429, approximately 30-second wait and successful recovery. |
| Do not hide failed attempts, unknown usage or incomplete conditions | **Met.** Historical failures and separate diagnostics remain preserved. |
| Fix Designer profiling | **Met for the selected retail runner.** The generic workbench still has an explicit one-row profiling-warning/salvage path; a universal repair cannot be claimed. |
| Resolve every quality problem rather than treating transport success as success | **Not a blanket pass.** Native UserSim flags and proposal-rule failures remain. The narrow delivered-response checks passed; overall helpfulness still needs review. |
| Popup MCQ and wait at new blockers; temporarily decide autonomously during your absence | **Recorded.** The temporary exception and restoration of popup-and-wait are preserved. Future adherence is an operating obligation, not a tested application feature. |

---

**8. Plans, housekeeping and publication**

| Your ask | Current status |
|---|---|
| Stop overwriting plans and preserve the detailed UX plan | **Met.** One [master plan](../../PLAN.md#where-requirements-and-progress-live) links the detailed UX specification and configuration inventory. |
| Track lifecycle, dependencies, amendments, implementation and verification | **Met.** Draft → Agreed → Queued → Implementing → Verified → Complete, with blocked/superseded records. The plan explicitly has no automatic executor. |
| Preserve decisions and failures rather than rewriting history | **Met.** Historical entries are labelled as such. |
| Check in completed rounds on `dev`; leave `main` unchanged | **Met.** Local `dev` and `origin/dev` match `a4a5f73`; `main` remains `b49cd85`. Working tree is clean. |
| Preserve unrelated styling, datasets, environments, dependency pins and source archives | **Met for the revamp.** The frozen-baseline comparison confirms these boundaries. |
| Initial ownership audit of nine ready chats and three PID records | **Completed.** Their ownership findings and preserved records are documented. |
| Archive obsolete output with original paths, hashes, provenance and recovery checks | **Completed for the archived batches.** Initial 1,700-file and later 182-file archives rehashed successfully. |
| Keep `runs/` for current work; clean obsolete public/private output | **Partial. New historical output accumulated again.** `runs/` currently contains 2,577 files, including 21 terminal journey records. Ownership/reference review is still needed before deciding which to archive. |
| Remove verified stale PID files | **Partial.** Three stale PID records remain under `artifacts/foundation/`. The web-review PID is live and correctly retained. |
| Preserve immutable v0.1/v0.2 archives | **Met.** All 173 v0.2 manifest files matched; neither source archive changed. |
| Keep raw runs outside Git; publish fixed sanitized demo evidence | **Met.** |
| Link future live sessions to local run directories | **Deferred as requested.** |

There is also some unused, obsolete wireframe-only wording in the internal `content.ts` metadata. The active panels use the new teaching content, but the source is not completely free of stale descriptions.

Earlier “wireframe only / scenarios illustrative / stop before foundation” restrictions were subsequently replaced by your explicit instructions to implement the foundation and all three scenarios. The future two-agent story remains a concept, not a feature implemented in this application.

---

**The concrete outstanding items**

1. **Missing checked-reply arrows for S2/S3** — [edge definitions](../../web/src/lib/lessonArchitecture.ts).
2. **Incorrect managed Guardrails placement in the map** — [fixed sandbox nesting](../../web/src/lib/IntegrationGraph.svelte).
3. **Comparison condition lost after reload** — [saved-selection snapshot](../../web/src/routes/+page.svelte).
4. **Incomplete UserSim authoring/Sim2Real explanation.**
5. **Private evidence lacks convenient owner-facing navigation.**
6. **Housekeeping backlog, three stale PID files and some stale internal wording.**
7. **Your acceptance of teaching clarity, depth, repetition and usefulness remains pending.**

The previous verification records **727 Python tests, 41 web unit tests and 32 browser cases**. I did not rerun those suites during this read-only audit. Those results support technical coverage; they did not catch all the requirement gaps above.

## Follow-up authorization and additional findings

The user authorized fixing original items **1, 2, 3 and 6**, keeping items 4/5 open, and requested an updated copy of the same report. The user subsequently required that new findings be appended without deleting existing report content. The original section above is therefore retained unchanged.

**Additional finding A8 — stale Q&A is visible, not only unused metadata.** During item 6's wording review, `web/src/lib/content.ts` was found to supply active Q&A answers claiming that the guide has no observed calls, no source dataset access, disabled simulation and no attached recording. Those statements describe the old wireframe and contradict the implemented application. The earlier audit correctly found stale wording but understated its reach. Correct only those obsolete claims and corresponding unused wireframe descriptions; preserve unrelated Q&A and existing teaching content. Status when recorded: **Open under authorized item 6**.

**Additional finding A9 — managed component proof scope is not fully propagated.** The managed deployment lesson has its own explicit managed evidence links. However, inspecting an individual component such as Guardrails from that lesson can still resolve generic component configuration references against the baseline capture condition. Keeping the map's host-caller placement correct does not make every component page's evidence managed-specific. Baseline records must not be relabelled as managed. Status: **Open; separate evidence-navigation work, outside the requested map-placement correction**.

**Supporting defect A10 — layout reset timing.** Correcting managed placement exposed a timing issue: Reset layout clears focus and returns to the standalone overview before the graph's managed layout prop has updated. An immediate graph reset could therefore remove the wrong layout key. The scoped correction waits for the overview update before resetting; it belongs to original item 2's preservation of layout behaviour. Status when recorded: **Correction implemented; verification follows below**.


## Updated complete report — scoped corrections verified, 22 November 2026

**Requested corrections 1, 2, 3 and 6 are implemented and verified.** The full project remains partial: UserSim teaching (4), private-file navigation (5), the newly identified managed component-proof scope (A9) and your UX acceptance remain open.

This update compares the scoped correction round with frozen baseline **`a4a5f73`**. The implementation revision is the Git commit containing this appended report; publication is recorded in the completion entry below. UI/source wording and verified output locations changed. **No scenario was rerun, no inference or deployment was performed, and no service was stopped.**

**Status:** Met = implemented and supported by evidence; Partial = a specific gap remains; Deferred = deliberately outside the current implementation; Review = needs your assessment.

---

**1. The application and three scenarios**

| Your ask | Current version | Status |
|---|---|---|
| Teach developers through a Singapore learning and community advisor | The North Star, application introduction and scenario-based guide are present. | **Met** |
| Connect concept → components → application call → configuration → result → proof | Separate teaching pages, inline code/configuration references and recorded observations implement this structure. Some gaps are listed below. | **Partial** |
| Photography: simplest preset, one turn, Deep Agents, fixed model, application assertions | Implemented without Designer, Switchyard, native Guardrails or Helix. | **Met** |
| Board games: two turns, Hermes, honest no-match, separate negative Guardrails demonstration | Implemented with its own conversation, persistent runtime and blocked credential-disclosure probe. | **Met** |
| Retail: three turns, Designer, disclosure, routing comparisons, Guardrails and Helix evaluation/deployment | Implemented. The salary-only second turn uses the approved application clarification branch; native agent execution occurs on turns 1 and 3. | **Met, with quality limits** |
| Each scenario must have its own evidence | Explicit demo bindings prevent another scenario’s records being substituted. | **Met** |
| One curated demo per scenario | The UI has no run-history selector. Historical evidence remains preserved separately. | **Met** |

The selected recordings are:

| Scenario | Demo | Recorded application checks | Applicable capture requirements | Native UserSim quality flags |
|---|---|---:|---:|---:|
| Photography | `94e49df8…` | 9/9 | 28/28 | 0 |
| Board games | `aa445222…` | 11/11 | 31/31 | 1 |
| Retail learning | `8ce3ace2…` | 24/24 baseline | 181/181 across its conditions | 2 |

These are **recorded results**, not a fresh claim that the remote model endpoints are healthy now. Passing application checks also does not erase the UserSim disagreements.

The exact recordings and configuration manifests are indexed in [the current demo inventory](../configuration-evidence-inventory.md#current-demos-and-location-keys).

---

**2. Your nine-step teaching journey**

| Step and your expected explanation | Current implementation | Status |
|---|---|---|
| **1. Choose a test persona:** show the actual original, explain selection and identity preservation; UserSim has not run | Resolves the recorded original against the installed dataset, displays it, verifies identity and reports unavailable rather than substituting another person. Selection/hashing are labelled application-owned. | **Met** |
| **2. Create a situation:** separate original background, supplied constraints, Designer additions and generated wording | Explains authored situations for S1/S2 and Designer hypotheses for S3. UserSim preparation is distinguished from actual message generation in Step 4. | **Met** |
| **3. Build and connect the agent:** explain Fabric configuration, adapter, tools, model connection and startup | Explains the typed SDK configuration, plan, Doctor preflight, persistent runtime, MCP registration and Relay attachment. | **Met** |
| **4. Run the application:** follow UserSim → application → Fabric → harness/tools → normalized result → learner | Actual public conversations and invocation boundaries are present. Retail’s direct clarification is explicitly distinguished from a Fabric result. Both map levels now show learner → Guardrails → advisor and advisor → Guardrails → learner. | **Met** |
| **5. Investigate execution:** explain why the answer happened using actual actions and returned facts | Selected-turn tool evidence, native Relay scopes, lifecycle records and separate gateway accounting are shown. Missing correlations remain explicit. | **Met** |
| **6. Evaluate behaviour:** show expected, observed, reason and coverage | S1/S2 assertions and S3 Helix scoring are distinguished from UserSim’s in-loop judges and unused post-loop evaluator. Native disagreements remain visible. | **Met, narrow coverage** |
| **7. Optimize model routing:** distinguish fixed routes, actual routing decisions and controlled comparisons | S1/S2 correctly say routing optimization was unused. Retail has completed fixed/routed comparisons and separately labelled diagnostics. The selected comparison and its producing run now persist across reload; stale, foreign and different-run selections are rejected. | **Met** |
| **8. Configure behavioural safeguards:** distinguish application restrictions, native checks and negative tests | Effective configuration, native decisions and separate negative probes exist. Request/reply arrows and managed host-caller placement are corrected. Generic component evidence can still be baseline-oriented in managed inspection; see A9. | **Partial — A9** |
| **9. Deploy with controlled access:** explain workload boundary, supervisor, policy, enforcement and cleanup | Standalone and Helix-managed execution have separate records and cleanup evidence. Recorded managed scope now places Guardrails in an explicit host-caller group outside OpenShell and retains it during Step-9 inspection. Generic component proof condition propagation remains open under A9. | **Partial — A9** |

The component coverage includes Personas, Designer, UserSim, Fabric, Deep Agents/Hermes, MCP/catalogue, gateway, LiteLLM, Switchyard, Relay, assertions, Helix evaluation/jobs, Guardrails, Helix managed operations and OpenShell.

Official architecture references and relevant operation subsets remain present. **The identified directional-flow and managed-placement defects are corrected.** Managed condition propagation into generic component proof links remains a separate open finding, A9.

---

**3. Your screenshot feedback—labels 1–31**

All labels are retained in [the feedback specification](../ux-review-spec.md#feedback-register-screenshot-labels-131). Recording a requirement is separate from satisfying it.

| Feedback | What I found | Status |
|---|---|---|
| **Earlier label 1:** proper project introduction; remove “Learning is the goal…” | Replaced with a concrete introduction to the advisor and the three tests. | **Met** |
| **Earlier label 2:** remove marked top-right badge/status | Removed. | **Met** |
| **Earlier label 3:** add UserSim to situation preparation/documentation | Added, with preparation versus execution explained. | **Met** |
| **Earlier label 4:** remove marked suffix and crossed paragraph | Removed. | **Met** |
| **Earlier label 5:** “Prepare data and simulate interaction” | Present. | **Met** |
| **Earlier label 6:** remove unexplained “role-labelled call ledger” jargon | Replaced with explanations of calls made for the advisor, learner and judges. | **Met** |
| **Earlier label 7:** move run status into Scenario Summary | Status is owned by the collapsible summary. | **Met** |
| Put your exact “Every lesson must answer…” statement beneath the North Star | Present once. | **Met** |
| **Labels 8–9:** remove “Why this matters”; write a proper introduction for each audience | Audience-specific introductory paragraphs replace that heading. | **Met structurally; Review for teaching quality** |
| **Label 10:** replace keyword fragments with meaningful scenario explanation | Coherent prose and scenario observations replace the fragments. | **Met structurally; Review for clarity** |
| **Labels 11–14:** explain “How it works” properly; remove circular component directories, filler and repeated dumps | Paragraphs explain cooperation. The old component-link lists and “Recorded—inspect proof” filler are removed. Broad setup facts are confined to their lesson. | **Met structurally; Review for depth** |
| **Label 15:** remove generic “Check your implementation” sections | Removed from the active teaching panel. | **Met** |
| **Labels 16–18:** Citizen advisor must explain that responsibility, not resolve to Fabric; Detailed Fabric must explain its own boundary | Conceptual and technical destinations have separate identities and content. | **Met** |
| **Labels 19–21:** keep “Connect the selected agent” as the Simplified action; explain that action without repeating the block | Plain-language title and action-specific explanation are present. | **Met** |
| **Label 22:** remove redundant checklist, related lessons and footer | Removed. | **Met** |
| **Labels 23–25:** technical operation title must match; explain actual preparation, mechanism, settings and expected return | Detailed operation pages are focused. Fabric’s configuration explanation now addresses the actual SDK classes and configuration contract. | **Met structurally; Review for teaching quality** |
| **Label 26:** link directly to the application call | Exact committed symbols/lines are used. | **Met** |
| **Label 27:** configuration means actual settings, not another Python link; explain JSON/native transformations | Actual settings captures and their roles are distinguished. Fabric’s native typed object versus public projections is explicitly explained. | **Met** |
| **Label 28:** logs must help diagnose execution, not merely show session IDs | Native scopes, tool inputs/results, invocation records and interpreted observations exist. **Finding private originals from the UI remains awkward.** | **Partial** |
| **Label 29:** architecture reference at one appropriate home | Library pages own their architecture links instead of repeating them on every operation page. | **Met** |
| **Label 30:** integrate code references naturally into the explanation | Purposeful inline references replace disconnected source-note bundles. | **Met structurally; Review for usability** |
| **Label 31:** remove generic integrity/related-lesson footnotes | Removed from the active teaching panel. Integrity verification remains internal. | **Met** |
| Apply this treatment to **all nine steps, scenarios, views and workflows** | All 54 scenario/lesson/audience combinations and separate block/action/operation destinations exist. The omissions below prevent a blanket completion claim. | **Partial** |
| Do not repeat substantive content across destinations | The old repeated tables and copied sections are removed; no exact repeated long teaching paragraphs were found. Whether the remaining conceptual overlap feels repetitive requires your review. | **Review** |

The Fabric explanation specifically now says that `build_config` constructs the **actual SDK `FabricConfig`**. Its nested classes group settings; they are not sequential translation stages. Public `fabric-config.json` and `framework-config.json` are explicitly described as review projections, not complete runnable inputs. See [the Detailed explanation](../../web/src/lib/teaching/detailedRuntime.ts).

---

**4. Other UI and navigation requests**

| Your ask | Current status |
|---|---|
| Alternating nine-step timeline matching the supplied design, with three phase bands | **Met.** It changes to a vertical presentation on narrow screens rather than using the old horizontal scrollbar. |
| Generic step names without product names | **Met.** |
| One Simplified map and one Detailed map | **Met.** Seven conceptual responsibilities expand into the relevant technical responsibilities. |
| Architecture blocks without competing step numbers | **Met.** |
| Permanent scenario dropdown; no repeated scenario labels/run-history controls | **Met.** |
| Changing scenario changes its summary and evidence | **Met.** |
| Enter map, switch level or reset layout: show the whole architecture; focus only after explicit interaction | **Met by source and prior browser verification.** |
| Highlight relevant operations and directional flows | **Met.** Both message directions are present for guarded presets; photography retains its direct request/reply path. |
| Preserve scenario, lesson, turn, selection and layout | **Met.** Scenario, lesson, turn, semantic destination and layout persist; comparison selection additionally records and validates its producing run. Legacy preferences still migrate. |
| Preserve typography, colours, resizing, layout controls and reduced motion | **Met for this revamp.** |
| Remove confusing dataset explanation/audit sections | **Met.** |
| Subsequently remove “The main difference” replacement box too | **Met.** |
| Preserve HF/NGC browsing and their actual schema differences | **Met**, with a previously recorded actual installed-dataset browser check. |
| Playback and inspection must make zero inference/deployment calls | **Met by implementation boundary and prior browser verification.** |

---

**5. Configuration capture, evidence and Metadata**

| Your ask | Current version | Status |
|---|---|---|
| Rerun S1–S3 and capture previously missing applicable configuration/output | New demos have complete applicable capture coverage: 28/28, 31/31 and 181/181. | **Met** |
| Continue retaining existing and private outputs | Native originals remain private; public projections retain their relationship to originals. | **Met** |
| Add Metadata with `[module, steps, YAML/JSON file, status, location, apply to scenario]` | Exactly those six columns are implemented. | **Met** |
| Group by scenario and distinguish conditions | Scenario/condition filters and module/file/status search exist. Inventories contain 51/51/198 entries, including unused requirements. | **Met** |
| Distinguish EXISTS, PRIVATE, NOT EXIST, PARTIAL and NOT USED | Availability, access and execution state are represented separately. | **Met** |
| Distinguish configuration, calling code, native result and teaching projection | Implemented; no artificial requirement that every SDK needs a YAML file. | **Met** |
| Code links go directly to your GitHub repository | Committed code references are used. | **Met** |
| Log links identify the exact scenario/run/condition | Public recording links are specifically bound. | **Met** |
| Help developer zero locate private originals | Metadata shows private availability but deliberately hides host paths. **There is no convenient owner-facing locator to the current raw capture manifest.** | **Partial usability** |
| Do not expose private profiles, prompts, proposals or credentials | Private originals remain outside Git; only curated projections are published. | **Met within audited boundaries** |

I independently checked **393 published payload hashes**. Together with their nine manifests, these are the **402 publication files**. No mismatch was found.

---

**6. Your UserSim questions**

| Question/request | Current answer and status |
|---|---|
| Where are the person, behaviour and task defined and recorded? | **Answered.** Original selection, interpreted behaviour, scenario/probe configuration and resolved records are distinguished. |
| What does “assistant” mean here? | **Answered.** The external citizen advisor application, including its selected harness/model/tools—not the simulator or judge model. |
| Existing sovereign-AI/safety probe or a custom probe? | **Answered.** The custom `learning_advisor` probe uses inherited conversation machinery. Python registration/hooks and effective settings are referenced. |
| Did authoring follow `AUTHORING_A_PROBE.md` and its templates? | **Partial.** The question is preserved, but the teaching content gives neither a verified history nor an explicit “not established” answer. |
| Where are trajectory Parquet, evaluation dataset and dashboard? | **Explicitly absent.** This external-runtime integration stores JSON/native outcomes. It did not execute the optional CLI Parquet/eval/report workflow. |
| Does Step 6 use UserSim’s post-loop evaluator? | **Answered: no.** It uses application assertions or Helix. In-loop UserSim judgments remain separately visible. |
| Explain OCEAN-derived behaviour and authored disclosure | **Implemented**, including the distinction between original traits and scenario-controlled disclosure. |
| Revisit 60/40 disclosure, reactive frustration, response-shape handling, D1–D4 and MATTR against the installed version | **Partial.** The full requested explanation and explicit per-feature execution states are unfinished. |
| Demonstrate those Sim2Real features in a future live exercise | **Deferred.** Not demonstrated by these runs. |

These outstanding questions are still present in [the UserSim review register](../ux-review-spec.md#usersim-questions-to-revisit-during-w2); preserving them is not the same as completing their explanation.

---

**7. Execution failures and approved corrections**

| Your ask/decision | Status |
|---|---|
| Fix missing-budget/schedule behaviour before agent/tool execution | **Met.** Retail turn 2 has zero advisor inference and no fabricated Fabric invocation/result. |
| Validate the delivered response and retain the native proposal separately | **Met.** Source-based application delivery is explicitly identified. |
| Fix Gemma/GLM connectivity, or use another working non-Nemotron model as subsequently approved | **Approved replacement completed.** MiniMax M3.1 Flash and Mistral Large 4 completed the required comparisons. **Gemma/GLM themselves were not demonstrated repaired.** |
| Remove the shared reasoning setting only for comparison aliases | **Met.** The conflicting setting came from our builder; it is not established as an upstream Fabric SDK bug. |
| Handle HTTP 429 with bounded 30/60-second recovery | **Met.** The selected retail run retains a 429, approximately 30-second wait and successful recovery. |
| Do not hide failed attempts, unknown usage or incomplete conditions | **Met.** Historical failures and separate diagnostics remain preserved. |
| Fix Designer profiling | **Met for the selected retail runner.** The generic workbench still has an explicit one-row profiling-warning/salvage path; a universal repair cannot be claimed. |
| Resolve every quality problem rather than treating transport success as success | **Not a blanket pass.** Native UserSim flags and proposal-rule failures remain. The narrow delivered-response checks passed; overall helpfulness still needs review. |
| Popup MCQ and wait at new blockers; temporarily decide autonomously during your absence | **Recorded.** The temporary exception and restoration of popup-and-wait are preserved. Future adherence is an operating obligation, not a tested application feature. |

---

**8. Plans, housekeeping and publication**

| Your ask | Current status |
|---|---|
| Stop overwriting plans and preserve the detailed UX plan | **Met.** One [master plan](../../PLAN.md#where-requirements-and-progress-live) links the detailed UX specification and configuration inventory. |
| Track lifecycle, dependencies, amendments, implementation and verification | **Met.** Draft → Agreed → Queued → Implementing → Verified → Complete, with blocked/superseded records. The plan explicitly has no automatic executor. |
| Preserve decisions and failures rather than rewriting history | **Met.** Historical entries are labelled as such. |
| Check in completed rounds on `dev`; leave `main` unchanged | **Met for the baseline; this scoped round is verified for publication on `dev`.** The appended publication receipt identifies its actual commit and final clean state. `main` remains `b49cd85`. |
| Preserve unrelated styling, datasets, environments, dependency pins and source archives | **Met for the revamp.** The frozen-baseline comparison confirms these boundaries. |
| Initial ownership audit of nine ready chats and three PID records | **Completed.** Their ownership findings and preserved records are documented. |
| Archive obsolete output with original paths, hashes, provenance and recovery checks | **Completed for the archived batches.** Initial 1,700-file and later 182-file archives rehashed successfully. |
| Keep `runs/` for current work; clean obsolete public/private output | **Met for eligible superseded output.** Owner/reference/open-file checks preceded archiving 18 old journey runs, seven focused retail roots and obsolete checks/reviews. `runs/` decreased from 2,577 to 447 files. Current demos, live-owned records and unresolved runtime state remain with documented reasons. |
| Remove verified stale PID files | **Met.** All three host-verified stale PID files were removed after archive/restore checks. The live web-review PID/log and other live services were preserved. |
| Preserve immutable v0.1/v0.2 archives | **Met.** All 173 v0.2 manifest files matched; neither source archive changed. |
| Keep raw runs outside Git; publish fixed sanitized demo evidence | **Met.** |
| Link future live sessions to local run directories | **Deferred as requested.** |

Obsolete wireframe-only wording in `content.ts` and false active Q&A claims were corrected. The guide no longer claims there are no recordings, no dataset access or no execution controls. Other Q&A, typography and navigation were preserved. Additional finding A8 is closed under item 6.

Earlier “wireframe only / scenarios illustrative / stop before foundation” restrictions were subsequently replaced by your explicit instructions to implement the foundation and all three scenarios. The future two-agent story remains a concept, not a feature implemented in this application.

---

**The concrete outstanding items**

1. **Fixed — checked-reply arrows for S2/S3.** Both levels show all four guarded message edges; photography stays direct.
2. **Fixed — managed Guardrails placement.** Recorded managed inspection uses a host-caller group outside OpenShell; standalone and saved layouts remain distinct.
3. **Fixed — comparison restoration.** Selection includes producing-run identity and rejects stale/foreign conditions.
4. **Open — incomplete UserSim authoring/Sim2Real explanation.** Unchanged this round.
5. **Open — private evidence lacks convenient owner-facing navigation.** Unchanged this round.
6. **Fixed for eligible output — housekeeping, stale PID files and obsolete wording.** Live/unknown resources remain explicitly protected.
7. **Pending — your acceptance of teaching clarity, depth, repetition and usefulness.**
8. **Fixed — A8 active Q&A still described the old wireframe.** Corrected as part of item 6.
9. **Open — A9 managed component proof scope.** Generic Guardrails/component references can still resolve baseline evidence while the map shows managed placement; the managed lesson’s explicit managed links remain separate.
10. **Fixed — A10 managed layout-reset timing.** Reset waits for the overview layout scope before removing its saved key.

This correction round passed **50 focused Python archive/guide tests, 45 web unit tests and all 39 browser cases**, including the three actual selected-demo reviews and the actual installed HF/NGC check, with zero skips. Svelte reported **zero errors/warnings** and the production build passed with its pre-existing bundle-size advisory. Browser inspection used read-only calls. The prior 727-test full Python suite is historical verification and was not rerun for these UI/docs/housekeeping changes. Archive hashes, all 389 current native files and the original audit prefix were independently rechecked. Passing tests do not close findings 4, 5 or A9, or establish UX acceptance.


## Publication receipt — 22 November 2026

The scoped implementation is committed as
[`4881f79166c5b751ecb5200c82391c53a1cc41cb`](https://github.com/syseeker/persona-simulation-lab/commit/4881f79166c5b751ecb5200c82391c53a1cc41cb)
and was successfully pushed to `origin/dev`. This completes original findings
**1, 2, 3 and 6**, together with supporting corrections A8 and A10. The original
report and its findings remain above; the full updated assessment begins at
[Updated complete report](#updated-complete-report--scoped-corrections-verified-22-november-2026).

The original **22,452-byte** report prefix still has SHA-256
`b61bd657e66a49cc627672933aea3b87eb95cb78aac9513e214cc4270dcc5c47`.
The publication review found no forbidden raw-output paths or configured
credentials in the staged changes. The implementation commit contains 15 scoped
files. `main` remains at `b49cd85b506848e2d3ac64372387b7c9408adb33`.
The subsequent documentation completion commit is the Git commit containing this
receipt and the completed A1 ledger entry; it changes no application behaviour.

Verification remains **50 focused Python tests, 45 web unit tests and 39 browser
cases**, with zero skipped browser cases, zero Svelte errors/warnings and a
successful production build. All 2,207 output archive entries, 156 private archive
entries and 389 retained native files were hash-verified. No new scenario,
inference or deployment was executed during this correction round.

**Still open:** UserSim authoring/Sim2Real teaching (4), convenient private-original
evidence navigation (5), managed component-proof scope (A9), and your acceptance
of the teaching experience (7). Completion of A1 does not close those findings.


## A11 — Review-server error overlay and readiness check · 23 November 2026

**Reported:** the user opened the review URL and saw a Vite import-error overlay
for `teaching/OperationObservation.svelte`. The preceding readiness check fetched
the HTML and saved-run endpoints but did not render the application in a browser.
That was insufficient to establish a usable review link.

**Diagnosis and recovery:** the component is present, tracked and readable, and
its import matches exactly. Both affected modules compiled with HTTP 200, and a
fresh Chromium session rendered the map before restart. Stale Vite/HMR error
state is the likely explanation; the original browser's internal state was not
captured, so this is an inference rather than a proven source defect. The exact
owned port-5189 Vite process, running since 20 November, was restarted after its
command, directory and ownership were checked. The previous log/PID and a hashed
source baseline were preserved. No simulation, provider or deployment service
was restarted. No application source, dependency or recording changed.

**Observed after recovery:** Chromium at the actual review URL rendered all three
selected personas/scenarios, Simplified maps, Detailed Fabric configuration
operations and their observed results, all five tabs, Metadata and reload. Both
affected JavaScript modules loaded successfully. There were zero page exceptions,
module-load errors, HTTP failures or API writes. Seven screenshots and request
receipts remain under ignored `.private/review/` for this incident.

Two diagnostic checks initially rejected three cancelled photography GET requests
under a blanket zero-cancellations assertion. Those results remain recorded.
Each cancelled reader also has a matching HTTP-200 response and its rendered
output; the three `ERR_ABORTED` events are retained as cancellations, not erased
or called successful requests. They do not reproduce the import-error overlay.

**Status:** review rendering recovered and browser-verified. The user should
hard-refresh the existing tab. Future link-readiness claims must include an actual
browser module/render check at the exact shared URL. Findings 4, 5, A9 and teaching
UX acceptance remain open; this incident does not change their status.


## A12 · 27 November 2026 · v0.3.0 review corrections started

The user approved implementation of feedback 1–48 and the nine-step body-writing
sample, with all existing titles preserved. New findings from read-only review:
Caroline is the selected original profile's preferred English name; managed proof
links can resolve baseline; retail investigation mixes baseline scopes with whole-run
accounting; two Helix configuration projections omit requested settings; the
Guardrails negative request displayed in the UI is not the exact executed wording.
These findings are queued/implementing, not verified corrections. Their full
requirements are in the new dated UX register and W4 in the single master plan.

Both an in-app trace viewer and local Phoenix are now explicitly authorized.
Phoenix imports existing advisor records locally; it does not rerun scenarios or
retroactively establish live OTLP collection. Immutable files, private originals,
previous failures and all preceding audit bytes remain unchanged.


## A13 · 27 November 2026 · v0.3.0 implementation verified

The approved F01–F48 revision is implemented for developer review. The dated
[feedback register](../ux-review-spec.md#implementation-and-verification--27-november-2026)
records each result; the [verification receipt](../verification.md#v030-developer-review--27-november-2026)
contains current checks and limitations. All existing lesson/component/operation
titles were preserved. The approved connected body style covers 54 lesson/view
pages and all reachable Simplified/Detailed destinations. First-page changes,
Caroline's existing preferred-name display and the v0.3.0 review badge are scoped
to the user's requests.

Updated findings:

1. **Original finding 4 — implementation addressed:** UserSim authoring now
   explains the participant, interpreted behaviour, probe/task, disclosure,
   advisor strategy, harness, tools, model and evaluation, with real extension
   points and the distinction from legacy `spec["strategies"]`. It does not claim
   a 100,000-case orchestrator or validated Sim2Real behaviour.
2. **Original finding 5 — scoped navigation addressed:** the in-app viewer shows
   curated hierarchy, timing, tool results and separate gateway accounting. Local
   Phoenix gives the owner filtered retained advisor model/tool I/O. Original
   persona records, private UserSim prompts, reasoning and credentials remain
   excluded. This is historical import, not retroactive live instrumentation.
3. **A9 — managed proof scope addressed:** an explicit standalone/managed selector
   resolves the map, policy, probes, configuration and Metadata links to one
   condition. New client/agent configuration companions recover omitted fields
   with original and secondary-source hashes. Old packs are immutable.
4. **New findings from A12 — addressed:** negative-test wording matches executed
   source; ordinary Guardrails checks group by turn/boundary; evaluation authors,
   categories and disagreements are explained; routing options distinguish public
   turns, attempts, decisions, criterion results, tokens, durations and retry waits.
5. **Original finding 7 — still open:** user acceptance of teaching clarity and
   usefulness. Automated/editorial review does not substitute for that acceptance.

The current full checks passed **759 Python tests, 69 web unit tests and 42 browser
cases**, including actual selected demos and installed datasets. Svelte reports
zero errors/warnings; production build, Ruff, documentation and immutable archive
checks pass. Representative node movement/saved layouts, label/card collision
checks, managed/narrow views, reduced motion and GET-only guide inspection were
verified. Initial browser assertion failures reflected changed requested labels,
Turn 1/default-deployment behavior and grouped Metadata counts; expectations were
updated without weakening exact source/condition bindings. A sandbox thread-wakeup
limitation was isolated; the unchanged web worker tests passed on the host.

Phoenix 22.1.0 is isolated and loopback-only. All **94 imported records / nine
conditions / ten trace groups** passed read-back, privacy and duplicate-free
reimport checks. Actual browser inspection displayed model → course tool → model
and the saved reply. Stop/restart retained history; the guide never starts a
service/import. Managed model payloads are absent from the hash-bound source;
six missing end times remain explicit unknown-duration markers. Phoenix displays
microsecond precision and optional bundled-price cost estimates. Those limits,
missing parents and absent gateway/span joins are preserved, not reconstructed.

All **389 native files** and **751 pre-existing public/historical files** still
match baseline. This audit's entire **52,753-byte pre-round prefix**, including
all earlier follow-ups and A11, retains SHA-256
`cf38c78dc16bf07b447af7ae53727adadf15949ca712e2c9c388b935470f175b`.
The earlier 22,452-byte original prefix remains contained within that unchanged
prefix. No new scenario, model experiment, SDK upgrade or deployment occurred.
Publication is tracked in W4; `main` remains unchanged.
