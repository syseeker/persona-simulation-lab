# Five-Phase Implementation Plan

## Contents

- [Objective](#objective)
- [Preparation](#preparation)
- [Implementation Phases](#implementation-phases)
- [Acceptance And Learning](#acceptance-and-learning)

## Objective

Build a generic Singapore learning advisor using hosted NVIDIA NIM inference. Implement a working application first, then add observability, a managed harness interface, evaluation and optional synthetic enrichment. Each phase includes executable code, meaningful checks and a learner walkthrough.

## Preparation

- Audit Singapore Personas before curating the catalogue. Completed: all 148,000 public records inspected; a diagnostic review panel saved locally.
- Use real official course listings with source dates. Completed: six career-learning programmes and six community classes; absent facts remain unknown.
- Use SvelteKit and TypeScript for the web application and Python for NVIDIA SDKs. Keep Data Designer 0.10 and Helix in separate locked environments.
- Publish generic application code and documentation to a public repository. Keep private materials, credentials, datasets and run artifacts local.

## Implementation Phases

1. **Functional application.** Implement chat, typed course MCP tools, a budget gateway, a persistent JSON-lines worker, direct Deep Agents and a public UserSim extension. Freeze resolved profile inputs for paired conditions; isolate memory and preserve partial output on failure.
2. **Relay.** Attach the maintained Deep Agents integration. Verify paired agent, LLM and tool scopes using actual generated events. Keep simulator and judge usage separate in the gateway ledger.
3. **Fabric.** Build an in-memory typed configuration, validate the installed adapter and use one persistent runtime per episode. Reuse the same MCP tools, system policy and budget gateway. Attach Relay through the adapter once.
4. **Helix.** Score saved output through the local Evals SDK. Generate fresh baseline and candidate responses on a frozen regression suite; retain failures and row-level criteria. Validate a declarative managed-agent artifact locally. Platform deployment is a separate operation.
5. **Data Designer.** Generate explicit preference hypotheses over existing profiles. Preserve source IDs, revisions and hashes, and compare one source profile with and without enrichment under the same advisor strategy.

## Acceptance And Learning

Implementation is established by working code and offline contract checks. Live verification is reported separately for NIM, UserSim, Relay, Fabric, Helix and the enrichment ablation. A failed model response remains a failed experimental condition. Full live evidence stays local; [verification](docs/verification.md) contains the shareable status.

Default limits: one active model workload per worker, one concurrent episode, at most three conversation turns, four tool rounds per reply, 1,024 output tokens per call and 120 calls per experiment or benchmark. Tests, demos and live calls are labelled distinctly.

Booking, payment, Singpass, live catalogue crawling, fine-tuning and multi-agent social environments remain outside this implementation.
