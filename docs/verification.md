# Verification Record

## Contents

- [Offline Checks](#offline-checks)
- [Live Checks](#live-checks)
- [Practical Limits](#practical-limits)

## Offline Checks

On 11 November 2026, the Python suite passed **26 tests without API credentials**. Coverage includes source parsing, immutable snapshots, constraint enforcement, repairable model tool arguments, real local MCP calls, Deep Agents and Fabric lifecycles, Relay events, UserSim hosted parity, cancellation, crash recovery, worker messaging, actual Helix pass/fail scoring and actual Data Designer source integrity.

The frontend passed **four unit tests and three browser tests**, with zero Svelte type errors or warnings. Browser checks exercise a real advisor request, saved simulation and local Helix scoring, a narrow viewport and inert rendering of supplied active markup. The Node production build also passed.

The full public dataset audit covered **148,000 records**. The coaching skill passed its validator. The managed Helix YAML passed schema loading, translation and Fabric planning in its compatible environment. That check performs no registration or deployment.

## Live Checks

The final bounded acceptance run used Nemotron 3.5 Lightning for the advisor and Nano Omni for UserSim user, judge and summary roles. Each experiment retained its own 120-call ceiling; these are separate checks, not a single 120-call allowance across the entire verification session.

- **UserSim with Relay:** three source profiles, two strategies and at most two turns per condition. Five of six episodes completed; one clarification-first condition stopped when the model ignored the four-tool-round guard. The run used **70 provider calls**. There were 165 native Relay events with paired agent, LLM and tool scopes.
- **Saved-reply Helix checks:** 38 of 40 narrow checks passed on saved replies from that run. Execution failure is reported separately; this score does not count the absent response as a passed output.
- **Fabric with NIM:** the maintained Deep Agents adapter completed a real photography recommendation through MCP and the budget gateway in **two provider calls**.
- **Frozen held-out cases:** twelve strategy/case combinations used **34 provider calls**. Ten executed successfully; two clarification-first cases hit the tool-round guard. Helix scored the concise baseline **36/42 criteria** and clarification-first **24/42**. The candidate did not outperform the baseline. These include execution checks, so failed cases remain in the denominator.
- **Data Designer ablation:** both three-turn conversations completed under the same advisor strategy and frozen catalogue, using **35 provider calls** in total. Original profile hashes were preserved. The enriched condition had three native assistant inline-quality findings, despite a completed loop. The overlay pipeline itself used zero inference calls.

Full transcripts, native rows, token usage and detailed failure evidence remain local under ignored `runs/`. The final summary is `runs/verification.json`; earlier failed trials are preserved separately. Model responses are stochastic, so a later run can produce different outcomes even with the same saved inputs.

## Practical Limits

NGC Extended download and behavioural conditioning are **not verified on this host**. A valid inference key does not establish dataset access. The local NGC CLI still needs a working organization/access configuration; the application fails clearly when the required dataset cannot be materialized. The working public mode is explicitly HF profile-only.

Deterministic text checks cover limited assertions and identifiers. They can miss paraphrased claims or flag an excluded course mentioned only as an explanation. Inspect raw replies and official listings before interpreting the aggregate. Native inline judges can also report findings even when UserSim marks a loop complete.

This is a diagnostic learning application. The small panel does not estimate population effects, course demand or human learning outcomes. Helix Platform deployment has not been performed, and its managed configuration requires equivalent budget admission before deployment.
