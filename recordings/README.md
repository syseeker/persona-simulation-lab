# Fixed review recordings

These are sanitized, checked-in execution projections for the Integration Guide.
They remain available after cloning, without the developer's private `runs/`
directory. Each manifest binds a scenario/run to its files and SHA-256 hashes.
Log links open the corresponding file at its GitHub commit. The review panel
interprets selected facts; retained preview APIs read verified bytes and never infer.
The UI selects one curated demo per scenario, without run-history controls.

## Current selected demos

| Scenario | Recording | Teaching companion | Configuration and evidence captures | Reviewed outcome |
|---|---|---|---|---|
| **S1 — Photography** | [`94e49df8-7dfa-445b-9614-d79e31f2c024`](photography/94e49df8-7dfa-445b-9614-d79e31f2c024/manifest.json) | [Companion](guide-context/photography/94e49df8-7dfa-445b-9614-d79e31f2c024/manifest.json) | [28/28 applicable requirements](captures/photography/94e49df8-7dfa-445b-9614-d79e31f2c024/manifest.json) | 9/9 application assertions; standalone cleanup confirmed. |
| **S2 — Board games** | [`aa445222-7127-41f0-a451-685874bf343c`](boardgames/aa445222-7127-41f0-a451-685874bf343c/manifest.json) | [Companion](guide-context/boardgames/aa445222-7127-41f0-a451-685874bf343c/manifest.json) | [31/31 applicable requirements](captures/boardgames/aa445222-7127-41f0-a451-685874bf343c/manifest.json) | 11/11 application assertions; one native UserSim helpfulness flag retained; standalone cleanup confirmed. |
| **S3 — Retail learning** | [`8ce3ace2-0bb4-46f7-898c-795bc7da4794`](dreamjob/8ce3ace2-0bb4-46f7-898c-795bc7da4794/manifest.json) | [Companion](guide-context/dreamjob/8ce3ace2-0bb4-46f7-898c-795bc7da4794/manifest.json) | [181/181 applicable requirements](captures/dreamjob/8ce3ace2-0bb4-46f7-898c-795bc7da4794/manifest.json) | 24/24 baseline delivered-response criteria; native Designer profiling, durable Helix job, requested routing comparisons, separate diagnostic and managed condition verified; cleanup confirmed. |

Retail has three public turns. Its salary-only second turn receives an application clarification before agent invocation, with zero advisor inference; native Fabric calls occur on turns one and three. The complete run admitted 42 model attempts, including one HTTP 429 failure recovered after its recorded 30-second wait. The approved MiniMax/Mistral inventory completes fixed, routed and separate capable-model access conditions; the Nemotron diagnostic remains separate. Native proposal-rule failures and any application rendering corrections remain visible alongside delivered-response results.

Capture manifests distinguish actual settings, requests, results and public projections from opaque private-only artifacts and unused integrations. The guide selects these exact runs; exports and newer development runs do not change that selection automatically.

## Historical photography

- [Earlier corrected review condition](photography/7863c607-cb99-4a31-b60c-381bf2099f0e/manifest.json): one real public UserSim turn, Fabric/Deep Agents, fixed LiteLLM, native Relay, nine application assertions and standalone OpenShell cleanup.
- [Earlier URL-validator failure](photography/828da067-7d75-4c02-a763-f2a54cdbe457/manifest.json): a correct catalogue URL without the internal course ID was rejected by the original narrow assertion. Its five-of-seven result is preserved.
- [Earlier geography review finding](photography/a32ce555-2180-4558-a32a-f3d8b1198de2/manifest.json): original seven-of-seven checks missed an incorrect planning-area statement. The separate developer review note preserves that limitation; later checks/instructions address it.

These three historical executions use the same locked source/story/harness/route, with
fresh target memory. UserSim generated different public wording; they are not a
controlled model-quality comparison. No historical result is rewritten. A passed
application assertion is limited to its stated coverage.

## Historical photography teaching companion

The [review companion](guide-context/photography/7863c607-cb99-4a31-b60c-381bf2099f0e/manifest.json) adds allowlisted UserSim configuration/outcome, Fabric model/Relay configuration, lifecycle events and normalized invocation/result fields from the **same** native run. Its manifest records the original pack-manifest hash, source hashes and native input hashes. Original pack bytes are unchanged. It contains no original profile row, private resolved input, simulator prompt or raw reasoning. `python -m scripts.export_guide_context` is an offline, non-overwriting exporter; it does not run models.

## Historical board games

[Curated recording](boardgames/938bdb3f-568e-442e-889f-fed046edf5a0/manifest.json) and [teaching companion](guide-context/boardgames/938bdb3f-568e-442e-889f-fed046edf5a0/manifest.json): two actual UserSim turns with persistent Fabric/Hermes, an empty native MCP search, fixed LiteLLM, native Relay, 11 application assertions, four allowed Guardrails checks, a separate blocked policy probe and verified standalone OpenShell cleanup. The native UserSim assistant-quality flag and prior failed development conditions remain disclosed. A passing no-match assertion can disagree with an in-loop helpfulness judge; inspect both.

## Historical retail learning

[Curated recording](dreamjob/8542330d-d6df-494e-8509-d81a5841d69e/manifest.json) and [teaching companion](guide-context/dreamjob/8542330d-d6df-494e-8509-d81a5841d69e/manifest.json): source-seeded Designer overlay, three public UserSim turns, salary-disclosure audits, fixed Fabric/Deep Agents baseline, 20/20 native Helix-scored criteria, a completed durable job, native Guardrails and a separate cleaned-up Helix/OpenShell session. Overall status remains **failed** because both requested Gemma/GLM comparison conditions timed out. The separate reachable-Nemotron comparison completed with 20/20 checks per condition and six native Switchyard decisions. Its success does not verify the requested pool. Small successful endpoint probes do not establish full-context completion. Native Intake projections retain actual IDs/statuses and decoded public tool facts; arbitrary prompts/reasoning remain private.

## Publication boundary

Packs include public messages, the frozen public course facts, role-labelled call
metadata, selected native IDs/statuses/tool results, policy/probe/cleanup records
and assertion rows. They are explicitly **projections**, not full raw traces.
Original local artifact hashes retain provenance for the developer's private
audit. Source profiles/IDs, private simulator prompts, credentials, process
ownership and arbitrary native payloads are excluded. Dataset distribution links
and original hashes identify the source without redistributing its rows.

Use `uv run python scripts/export_guide_recording.py RUN_ID --note 'Review reason'`
only for a terminal, cleaned-up scenario condition. The exporter refuses to
overwrite an existing pack. Review the output and scan for secrets/private data
before staging. Run `uv run python scripts/check_docs.py`, the recording tests
and the regular application checks before publishing to `dev`.

Use `uv run python scripts/export_capture_evidence.py RUN_ID` to publish the separate configuration/evidence capture pack after verifying a terminal run. It reads retained captures offline, validates requirement coverage and content hashes, and writes an immutable `recordings/captures/SCENARIO/RUN_ID/manifest.json`. Private-only sources receive opaque descriptors; only allowlisted public content is exported. It neither changes the recording/companion bytes nor selects the demo.

Future live-log linking remains separate; this round adds fixed review packs.
