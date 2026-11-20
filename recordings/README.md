# Fixed review recordings

These are sanitized, checked-in execution projections for the Integration Guide.
They remain available after cloning, without the developer's private `runs/`
directory. Each manifest binds a scenario/run to its files and SHA-256 hashes.
Log links open the corresponding file at its GitHub commit. In-app previews use
the same verified bytes and never infer.

## Photography

- [Corrected review condition](photography/7863c607-cb99-4a31-b60c-381bf2099f0e/manifest.json): one real public UserSim turn, Fabric/Deep Agents, fixed LiteLLM, native Relay, nine application assertions and standalone OpenShell cleanup.
- [Earlier URL-validator failure](photography/828da067-7d75-4c02-a763-f2a54cdbe457/manifest.json): a correct catalogue URL without the internal course ID was rejected by the original narrow assertion. Its five-of-seven result is preserved.
- [Earlier geography review finding](photography/a32ce555-2180-4558-a32a-f3d8b1198de2/manifest.json): original seven-of-seven checks missed an incorrect planning-area statement. The separate developer review note preserves that limitation; later checks/instructions address it.

These are three executions of the same locked source/story/harness/route, with
fresh target memory. UserSim generated different public wording; they are not a
controlled model-quality comparison. No historical result is rewritten. A passed
application assertion is limited to its stated coverage.

## Board games and retail learning

No executed recording is installed. Their UI content is illustrative. Add a
separate, reviewed pack only after implementing and verifying each scenario.

## Publication boundary

Packs include public messages, the frozen public course facts, role-labelled call
metadata, selected native IDs/statuses/tool results, policy/probe/cleanup records
and assertion rows. They are explicitly **projections**, not full raw traces.
Original local artifact hashes retain provenance for the developer's private
audit. Source profiles/IDs, private simulator prompts, credentials, process
ownership and arbitrary native payloads are excluded. Dataset distribution links
and original hashes identify the source without redistributing its rows.

Use `uv run python scripts/export_guide_recording.py RUN_ID --note 'Review reason'`
only for a terminal, cleaned-up photography condition. The exporter refuses to
overwrite an existing pack. Review the output and scan for secrets/private data
before staging. Run `uv run python scripts/check_docs.py`, the recording tests
and the regular application checks before publishing to `dev`.

Future live-log linking remains separate; this round adds fixed review packs.
