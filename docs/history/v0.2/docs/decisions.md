# Architecture Decisions

## v0.2: Teach the whole application

The [North Star](project-goals.md) supersedes the earlier phase-completion framing. The sample exists to make country personas, simulation, generation, harnesses, routing, tracing, evaluation and deployment understandable as one application. Keep the course advisor as a concrete bounded example and the UI as the primary teaching surface.

Use one selected citizen story and saved episode across inspectors. Do not rerun simulations merely to display another tool. Make additional conditions explicit: change one constraint, strategy, overlay, harness or routing policy and state the comparison purpose. Repeated LLM runs can vary even with frozen inputs.

Keep SvelteKit and the persistent Python worker. Expose reusable application services to developer entry points while preserving the read-only course MCP boundary seen by the advisor. Developer-control operations must not become model tools.

## v0.2: Honest evidence before badges

Separate transport/runtime completion from answer validity. Preserve native runtime errors, malformed pseudo-tool output, partial histories, UserSim warnings and missing responses. Link per-turn evidence and narrow evaluation criteria; missing evidence is not a passed check. Preserve native IDs and actual Switchyard decisions instead of fabricating a unified trace.

Keep current local source excerpts separate from saved-run revision references. Use opaque allowlisted artifact identifiers and bounded redacted browser projections; raw evidence stays local. Reopening a run must not generate new model outputs or substitute current catalogue facts.

## v0.2: Original, enriched and generated data

Sample the full audited local corpus; the old diagnostic panel is not the persona universe. HF public and Singapore NGC Extended remain explicitly separate distributions. NGC access/OCEAN conditioning must fail clearly when unavailable rather than inferring behavioural fields.

Data Designer now demonstrates genuine source-seeded LLM scenarios, typed custom columns and new synthetic rows. Preserve original JSON/hashes. Added salary/brand values are hypotheses; new profiles have new identities and parent lineage. Saved derived data becomes simulator input only through an explicit selection, retaining its generated distribution/context.

## v0.2: Runtime, proxy and deployment isolation

Use maintained Fabric adapters for Deep Agents and Hermes. Keep Hermes in its compatible Python environment rather than relaxing the main UserSim dependencies. Harness comparisons use the same fixed model before exploring routing differences.

Fabric 0.6.1's global Deep Agents allowlist gates execution but does not hide the pinned harness's built-in schemas. Live diagnosis observed eleven advertised tools and repeated empty catalogue searches; direct/Relay exposed only the three catalogue tools. Apply an explicit assistant-role schema allowlist at the shared Gateway for local and managed Deep Agents workloads, retaining the adapter's execution gate. Record received/exposed/withheld names per call and preserve the original native Relay request. The fixed-model Fabric board-game check then completed in two actual calls with one native catalogue search; this is a bounded observed result, not a general reliability claim.

Keep Hermes's native catalogue discovery tools. Do not apply Deep Agents function-name rules to a different harness protocol, patch installed adapter code to implement this schema filter, execute pseudo-tool text or replace failed model output with a plausible reply. Revisit this compatibility boundary only against a tested upstream release. Other separately documented image compatibility workarounds retain their own validation requirements.

LiteLLM provides configurable provider transport; Switchyard owns the explicit routing experiment. NIM, Brev and frontier APIs are inference choices, independent of local/remote Helix Platform hosting. The gateway continues to own attempt admission and usage; the managed deployment inference bridge requires an active run lease.

Helix local SDK assertions and Platform deployment are distinct operations/environments. OpenShell is the intended agent-and-course-tool boundary; a checked-in policy intent file or installed CLI is insufficient evidence of enforcement. Record real readiness, registration/deployment/session output and native sandbox audit results before claiming the full stack works.

Use OpenShell's official encrypted credential store with a hash-checked public photography/S$50/Saturday preset in the reviewed image. The pinned native Helix external driver accepts signed secret registrations but cannot store OpenShell's internally generated sandbox materials. Keep that unsupported dynamic OpenShell callback disabled; no custom credential-driver adapter is installed. The separate Docker environment demonstrates authenticated changing session constraints. Preserve both paths' actual runtime and model-call evidence separately.

## Retained v0.1 decisions

The original [decision record](history/v0.1/docs/decisions.md) remains unchanged in the historical archive. Still-applicable choices include the bounded worker protocol, explicit source uncertainty, frozen paired inputs, separate UserSim/Designer/Helix environments, native Relay integration and tested Fabric adapter workarounds.

v0.1 selected Nemotron 3.5 Lightning for the advisor after a real tool check and Nano Omni for UserSim roles; configuration changes must remain explicit, with no silent model fallback. Its clarification-first candidate scored below the concise baseline and some conditions hit the tool guard. Those are historical findings, not universal reliability or v0.2 live acceptance. See [verification](verification.md) for current evidence and [compatibility](sources.md) before changing adapters.
