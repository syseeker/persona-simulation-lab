# Application Contracts

## Contents

- [Web And Worker](#web-and-worker)
- [Course Matching](#course-matching)
- [Target And Simulator](#target-and-simulator)
- [Artifacts And Outcomes](#artifacts-and-outcomes)

## Web And Worker

The browser calls SvelteKit routes under `/api`. Read operations are `status`, `catalogue`, `runs` and `run?id=...`. POST operations are `chat`, `runs`, `cancel` and `evaluate`.

The server maps these to a version-1 worker envelope containing `id`, `method` and `params`. A response contains the same ID and either `result` or a bounded `error`. Inputs use strict Pydantic models; unknown methods and unexpected fields are rejected. Individual worker lines are limited to 1 MiB, and web request bodies to 64 KiB.

Chat requests include a goal, optional explicit budget, day, area, prior-skill and category constraints, mode, runtime and optional session ID. Run requests select demo/live mode, direct/Relay/Fabric execution, HF profile-only or NGC source, one to three profiles, one or two strategies, one to three turns and optional enrichment.

## Course Matching

The catalogue stores stable IDs, official URLs, capture dates, descriptive tags, published fee bounds, known extras, schedules and prerequisites. Missing values are null. The current snapshot is dated 10 November 2026.

Matching excludes known closed intakes, known budget conflicts including material fees, incompatible class days and explicitly unmet prerequisites. Unknown costs or schedules stay conditional. Goal relevance and an optional area preference rank the remaining candidates; IDs resolve ties.

The model can refine search wording. It cannot relax constraints supplied explicitly through the application. The trusted MCP server binds these from the current conversation's local preferences record and returns constraint notes with details and comparisons.

## Target And Simulator

Both targets implement an async session with `reply(message, preferences)` and cleanup. A target response contains public text, thread identity and available tool/runtime evidence. The direct target and Fabric retain state only within that session.

The public `ProbeEpisodeRuntime` supplies exact activation messages and owns the conversation loop, gates, judges and final native outcome. The host answers user/judge/summary activations through NIM and assistant activations through the target. It records the activation ID and measured usage. Course tools are absent from the UserSim probe.

Stored resolved rows are the replay inputs. Experiments save them exactly; repeated sampling with the same seed is not assumed identical. Source IDs pair conditions, while target memory and application episode IDs remain distinct.

## Artifacts And Outcomes

`runs/<uuid>/` contains the run manifest, event JSONL, resolved inputs, condition folders, native UserSim results and optional Helix scores. Relay files and target histories stay there. Benchmarks and enrichment ablations have separate ignored subdirectories.

Terminal run states include completed, completed with warnings, completed with failed conditions, cancelled, interrupted, budget exhausted, timed out and failed. Reports preserve the native UserSim outcome rather than treating every finished loop as a quality success.

The gateway admits no more than 120 provider attempts per experiment or benchmark, caps output at 1,024 tokens per call and allows four tool rounds per advisor reply. At most one episode runs at a time. Cancellation retains the ledger, including failed or cancelled attempts whose billing or usage may be unknown.
