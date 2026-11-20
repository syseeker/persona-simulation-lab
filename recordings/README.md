# Fixed review recordings

These are sanitized, checked-in execution projections for the Integration Guide.
They remain available after cloning, without the developer's private `runs/`
directory. Each manifest binds a scenario/run to its files and SHA-256 hashes.
Log links open the corresponding file at its GitHub commit. The review panel
interprets selected facts; retained preview APIs read verified bytes and never infer.
The UI selects one curated demo per scenario, without run-history controls.

## Photography

- [Corrected review condition](photography/7863c607-cb99-4a31-b60c-381bf2099f0e/manifest.json): one real public UserSim turn, Fabric/Deep Agents, fixed LiteLLM, native Relay, nine application assertions and standalone OpenShell cleanup.
- [Earlier URL-validator failure](photography/828da067-7d75-4c02-a763-f2a54cdbe457/manifest.json): a correct catalogue URL without the internal course ID was rejected by the original narrow assertion. Its five-of-seven result is preserved.
- [Earlier geography review finding](photography/a32ce555-2180-4558-a32a-f3d8b1198de2/manifest.json): original seven-of-seven checks missed an incorrect planning-area statement. The separate developer review note preserves that limitation; later checks/instructions address it.

These are three executions of the same locked source/story/harness/route, with
fresh target memory. UserSim generated different public wording; they are not a
controlled model-quality comparison. No historical result is rewritten. A passed
application assertion is limited to its stated coverage.

## Photography teaching companion

The [review companion](guide-context/photography/7863c607-cb99-4a31-b60c-381bf2099f0e/manifest.json) adds allowlisted UserSim configuration/outcome, Fabric model/Relay configuration, lifecycle events and normalized invocation/result fields from the **same** native run. Its manifest records the original pack-manifest hash, source hashes and native input hashes. Original pack bytes are unchanged. It contains no original profile row, private resolved input, simulator prompt or raw reasoning. `python -m scripts.export_guide_context` is an offline, non-overwriting exporter; it does not run models.

## Board games

[Curated recording](boardgames/938bdb3f-568e-442e-889f-fed046edf5a0/manifest.json) and [teaching companion](guide-context/boardgames/938bdb3f-568e-442e-889f-fed046edf5a0/manifest.json): two actual UserSim turns with persistent Fabric/Hermes, an empty native MCP search, fixed LiteLLM, native Relay, 11 application assertions, four allowed Guardrails checks, a separate blocked policy probe and verified standalone OpenShell cleanup. The native UserSim assistant-quality flag and prior failed development conditions remain disclosed. A passing no-match assertion can disagree with an in-loop helpfulness judge; inspect both.

## Retail learning

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

Future live-log linking remains separate; this round adds fixed review packs.
