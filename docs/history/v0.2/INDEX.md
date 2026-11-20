# v0.2 historical source snapshot

This directory preserves **173 source files, 3,773,514 bytes**, captured on
**19 November 2026**, immediately before housekeeping. It includes tracked and
nonignored untracked files from a **dirty working tree** based on commit
`b49cd85b506848e2d3ac64372387b7c9408adb33`. That commit alone does not reconstruct
these files. The original relative topology is retained, including the existing
v0.1 documentation archive.

The [manifest](archive-manifest.json) records every captured path, byte size,
permission mode and SHA-256. Files in the snapshot are historical payloads;
correcting an old document or test here would invalidate its recorded hash.
The index and current integrity checker are outside that captured file list.

## What this archive means

The snapshot preserves the retired v0.2 browser implementation, its source and
tests, the old documentation and diagrams, their renderer, the unused
`configs/models.toml`, and the historical `scripts/verify_live.py` sweep. It also
contains the backend and integration sources as they stood at capture, so the
old UI's dependencies remain inspectable in their original topology.

Archiving a copy does not retire the reusable backend. Current shared services,
CLI, developer MCP, compatible SDK environments, catalogue, inference controls,
evidence readers and lifecycle/security checks remain active in the main
checkout. Consult the [current README](../../../README.md),
[project goals](../../project-goals.md), [architecture](../../architecture.md)
and [verification record](../../verification.md) for current status.

Historical results describe their recorded conditions. They are **not fresh
live verification**, current endpoint readiness, proof that all replies were
correct, or acceptance of later scenario designs. In particular, preserve the
recorded model failures, unsupported Hermes correlation and unverified dynamic
deployment paths rather than treating archived configuration as success.

- [Captured README](README.md)
- [Captured plan](PLAN.md)
- [Captured verification](docs/verification.md)
- [Captured architecture](docs/architecture.md)
- [Captured browser source](web/src/routes/+page.svelte)
- [Captured source registry](src/learning_lab/source_index.py)

## Retired from the active tree

- The previous page, eight UI components, shared UI stylesheet and four dashboard browser-test files. Active `web/` keeps its API, worker bridge, reusable helpers and a static service landing page.
- The old walkthrough/narrative versions, architecture diagrams and advisor screenshot. Current root documentation identifies the wireframe review gate; the dated verification remains here.
- The old diagram renderer, unreferenced model-materialisation TOML and historical live-sweep script. They remain inspectable in this snapshot and are not current launch instructions.

The duplicated managed-agent skill is now a link to the canonical runtime skill in the active tree. The captured older copy remains unchanged here. The runtime modules, SDK environments/lockfiles, source data boundaries and meaningful backend tests remain in their original active locations. Snapshot directories are excluded from current Python test discovery and linting.

## Check or recover source

From the active repository root, checking makes no application or network calls:

```bash
python3 scripts/check_archive.py
```

To recover source, choose a **new, nonexistent directory outside the active
checkout**, whose parent directory already exists:

```bash
python3 scripts/check_archive.py --restore /tmp/persona-lab-v02-recovered
```

The standard-library checker verifies the complete manifest before creating the
destination. It rejects unsafe/duplicate paths, excluded local state, symbolic
links and mismatched file hashes, sizes or modes. Recovery copies only listed
ordinary files, recreates their relative paths and file modes, then checks every
output. Existing destinations and symlinked parent directories are refused.
If copying fails after creation, the partial destination remains for inspection;
it is not reported as verified and will not be overwritten on a retry.

This is **source recovery**, not Git restoration. It does not reconstruct the
Git index, branches, dirty status, history, remotes, services or containers, and
it does not execute the recovered code or install dependencies. A separate
private full Git/source backup was preserved before housekeeping; its
machine-local location is intentionally absent here.

Actual `.env` files, `.private/`, datasets, run payloads, transcripts, traces,
installed environments and caches were excluded. `.env.example` is retained as
a source template. Supply credentials and approved source assets separately,
recreate the pinned environments from the captured manifests/lockfiles, and
review the historical setup before choosing to run it. The snapshot does not
contain the local state needed to resume a deployed service or reproduce a
saved private conversation.
