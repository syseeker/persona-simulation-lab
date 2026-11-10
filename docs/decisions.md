# Architecture Decisions

## Contents

- [Application And Harness](#application-and-harness)
- [Data And Evaluation](#data-and-evaluation)
- [Compatibility](#compatibility)

## Application And Harness

Use SvelteKit 3 and TypeScript for UI and server routes, with a persistent Python worker for NVIDIA SDKs. A versioned JSON-lines transport keeps the local application simple and avoids another web service framework.

Use Deep Agents as the target harness because a maintained Fabric adapter and native Relay integration exist. Keep its model-visible tools limited to the course catalogue. UserSim owns simulated conversation dynamics; the application owns orchestration, budgets and target isolation.

Attach Relay before Fabric for learning clarity. The Fabric path uses the adapter's native instrumentation once. Helix evaluates saved replies locally before any Platform deployment. The legacy NeMo Agent Toolkit library is migration context and is not a baseline dependency.

## Data And Evaluation

Study the real Singapore dataset before selecting course scenarios. Use an explicit HF profile-only mode for the publicly available records and keep the documented NGC path distinct. The public profiles support career goals, skills and interests, but do not establish OCEAN scores or individual eligibility.

Use verified snapshots for course facts. Bind explicit user constraints inside the trusted tools. Preserve uncertainty in model responses and evaluate unsupported assertions rather than assuming model compliance.

Data Designer is Phase 5's authored enrichment pipeline. Its earlier presence as a UserSim dependency does not mean that pipeline was already implemented. Use labelled categorical scenario hypotheses for the first enrichment experiment; this makes the intervention auditable and requires zero generation calls.

## Compatibility

The root environment combines UserSim 0.3.0, Data Designer 0.9.7, Deep Agents 0.7.35, Relay 0.11.1, Fabric 0.6.1 and MCP 1.30. Data Designer 0.10 requires a separate environment. Helix 0.9.1 selects its own older compatible Fabric/Relay set in another environment.

The installed Fabric 0.6.1 descriptor lacks per-server MCP filters, so the app uses its supported global tool allowlist. The wheel also needs an explicit generated Relay configuration path. The app derives that file from the typed config and sets the adapter interpreter explicitly.

SvelteKit 3 moved configuration into the Vite plugin, changed the built-in TypeScript config and uses package imports. TypeScript 6 is pinned because the installed Svelte checker does not support TypeScript 7. The Node-compatible DOM test version is pinned separately.

A live run showed that two tool rounds were too restrictive for multi-course comparison. The limit is four rounds while the total 120-call cap remains unchanged. The earlier failed conditions are retained locally.

The advisor defaults to Nemotron 3.5 Lightning after a real course-tool check succeeded on an input that caused repeated calls with Nano Omni. UserSim user, judge and summary roles keep Nano Omni. This is an explicit configuration choice; no runtime fallback silently changes models. The final paired run still contains one tool-limit failure, so the model change does not establish universal reliability.

The clarification-first candidate scored below the concise baseline on the frozen diagnostic cases. Keep the concise strategy as the interactive default and preserve both sets of results for the learning exercise.
