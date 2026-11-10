# Build-Together Learning Guide

## Contents

- [Phase 1: Follow One Recommendation](#phase-1-follow-one-recommendation)
- [Phase 2: Read A Trace](#phase-2-read-a-trace)
- [Phase 3: Change The Runtime](#phase-3-change-the-runtime)
- [Phase 4: Evaluate A Change](#phase-4-evaluate-a-change)
- [Phase 5: Inspect An Enrichment](#phase-5-inspect-an-enrichment)

## Phase 1: Follow One Recommendation

Start the web app in offline mode. Ask for a Saturday photography class with a S$50 budget. Inspect the official listing and compare its published fee with the unknown extra costs. Then select live NIM and ask the same question.

Follow `Preferences` through the matching service, MCP tool, advisor harness and gateway. Run one live HF profile-only simulation and read every user and assistant message. Explain which parts came from the source persona, which came from the catalogue and which were generated.

Try changing the budget for baking from S$120 to S$130. The known material fee changes which course fits. Unknown fees must stay unknown.

## Phase 2: Read A Trace

Choose Deep Agents + Relay. Inspect the condition's `relay.jsonl` under the local run folder. Pair start/end events by UUID and follow parent UUIDs from agent to model to tool.

Use the gateway ledger to distinguish target inference from simulated-user, judge and summary inference. Explain why a completed assistant activation can include multiple provider calls, and why a model call without usage data is not zero cost.

## Phase 3: Change The Runtime

Choose Fabric + Relay and repeat a question. Inspect the runtime ID and typed configuration. Ask a follow-up in the same chat and compare it with a new chat.

Explain which lifecycle Fabric owns, why the app keeps the experiment coordinator, and how both targets use the same course MCP surface and budget gateway. Check that a new condition receives fresh memory.

## Phase 4: Evaluate A Change

Use **Evaluate saved replies** in the results view, or run `uv run learning-lab benchmark --live` for the frozen cases. Read row-level failures before comparing aggregate scores.

The candidate prompt adds explicit cost checks and clarification guidance. A difference on this small regression suite is evidence for these cases, not proof of general improvement. Model failures, source-citation gaps and unsupported fee claims remain visible. The criteria do not verify every sentence.

The managed YAML can be validated locally with `uv run --project integrations/helix python integrations/helix/validate_agent.py`. This performs no Platform registration or deployment.

## Phase 5: Inspect An Enrichment

Run `uv run learning-lab enrich`, then inspect the local overlays. Check a source hash and verify the original JSON is unchanged. Identify the generated goal, familiarity, delivery preference, budget and availability as hypotheses.

Run `uv run learning-lab ablate` to verify paired inputs without inference. Add `--live` to compare the same source profile with and without the overlay under the same advisor strategy. Read the changed utterances and raw outcomes before interpreting any score difference.
