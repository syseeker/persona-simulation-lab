# Build-Together Learning Guide

## Contents

- [Phase 1: Follow One Recommendation](#phase-1-follow-one-recommendation)
- [Phase 2: Read A Trace](#phase-2-read-a-trace)
- [Phase 3: Change The Runtime](#phase-3-change-the-runtime)
- [Phase 4: Evaluate A Change](#phase-4-evaluate-a-change)
- [Phase 5: Inspect An Enrichment](#phase-5-inspect-an-enrichment)

## Phase 1: Follow One Recommendation

Start the web app in offline mode. Ask for a Saturday photography class with a S$50 budget. Inspect the official listing and compare its published fee with the unknown extra costs. Then select live NIM and ask the same question.

Follow `Preferences` through the advisor harness, inference gateway, MCP tool and matching service. The harness asks the model for an action, the model selects a course tool, the tool returns saved catalogue facts, and the model produces its reply.

For a live HF profile-only simulation, select one profile and keep Data Designer and strategy comparison off. After it finishes:

1. Open **Review results**. **Show experiments** filters the saved history by Live NVIDIA NIM, Offline demo or all inference modes. New-run inference settings belong to the advisor and simulation screens. The list contains the most recent 30 runs matching the filter.
2. Select the saved experiment and click **Trace sources**. Choose a profile/strategy under **Conversation to trace**.
3. Read **Source profile** for the dataset's original occupation, skills, interests and career ambitions. Read **Application scenario** for the theme, strategy and optional preference hypotheses added by the application.
4. Read each **Generated learner message** and **Generated advisor reply**. Compare their claims with the source fields above.
5. Expand **Saved tool steps** to inspect requested arguments and returned facts. Compare course IDs in the reply with **Frozen course facts**, including fees, unknown extras, prerequisites, funding notes and official links.

Opening a trace makes no model calls. A course ID found in the catalogue does not establish that every sentence in the reply is correct. A tool result may also list an excluded course; inspect the result's conditions before interpreting it as a recommendation.

Failed conditions retain their stop reason. A condition that stopped before a final reply will show that no reply was saved. New Deep Agents failures retain partial tool history; some earlier failed runs and Fabric runs have no structured tool records. Missing evidence is labelled explicitly. Use a completed episode for the full input-to-recommendation exercise.

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
