# Active output and historical evidence

`runs/` and `artifacts/` are ignored local output, not source code. Keep current or
unresolved workloads there. Superseded output belongs in ignored, dated
`.private/history/` archives. Do not commit source profiles, transcripts, native
trace payloads, generated rows or credentials.

## Archive policy

Before moving output, check actual owner processes on the owning host, open files,
saved workload status and any `runs/platform-session.json` guard. A local process
namespace, old timestamp or terminal-looking filename is not sufficient proof.
Preserve active/unknown owners and their recovery records. Never stop a service,
release a native session guard or rewrite a failure just to clean a directory.

Copy eligible output while preserving its `runs/` or `artifacts/` relative tree.
Record every original path, byte count, SHA-256, timestamp and disposition in
`output-manifest.json`. Verify all copied bytes before removing originals. Retain
historical status values unchanged, including orphaned chats once owner absence
has been established. Record why other outputs remain active. Never expire SDK
environments, datasets or source recovery archives as if they were caches.

Apply the same ownership checks to `.private/`: move obsolete review notes,
old check logs/screenshots, downloaded documentation and abandoned probes into
the dated archive rather than leaving several competing working folders. Store
identical private payloads once, retaining each original path in
`private-manifest.json`. Its standalone `recover-private.py` verifies all hashes
and restores original paths only into a new destination. Never run recovered
probe scripts as part of recovery.

Redundant binary download archives may be removed after every member is hashed
against the retained installed binary. Keep the comparison receipt. Installed
binaries, reusable upstream source, live databases/logs, credential stores,
current configuration and unresolved native session state are not disposable
downloads. A process check must distinguish the owning host from a restricted
tool process namespace.

## Verify and recover

The archive path below is a template; substitute an actual directory from
`.private/history/`:

```bash
python3 scripts/check_output_archive.py .private/history/ARCHIVE_DIRECTORY
python3 scripts/check_output_archive.py .private/history/ARCHIVE_DIRECTORY --restore /tmp/recovered-lab-output
```

Recovery requires a new destination and verifies every file before writing. It
does not launch application code, reopen sessions or overwrite active output.
Inspect recovered evidence before explicitly copying a needed condition back.
Historical payloads may retain their original paths; the manifest maps those
unchanged paths into the archive. Archived evidence is not a currently installed
recording pack or proof of live readiness.

Each archive also contains a standalone `recover.py` copy of this checker. From
the archive directory, `python3 recover.py .` verifies it without the checkout.
The immutable public v0.1/v0.2 source archives are separate and remain unchanged.

## Superseded publication attempts · 22 November 2026

Four untracked photography/board-games publication attempts were archived under
`.private/history/20261122T120816466155Z-superseded-publication-attempts/`:
182 files, 783,364 bytes, preserving their `recordings/` trees. Host ownership and
open-file checks preceded copying; every hash, size and timestamp was verified,
including a complete restore into a new temporary directory, before originals
were removed. Raw runs, tracked immutable packs and the latest photography pack
were unchanged. The archive's `completion-receipt.json` records the checks.

This publication archive uses its narrowly scoped `recover-recordings.py`, rather
than the output checker for `runs/` and `artifacts/`:

```bash
python3 .private/history/20261122T120816466155Z-superseded-publication-attempts/recover-recordings.py .private/history/20261122T120816466155Z-superseded-publication-attempts --restore /tmp/NEW_RECOVERY_DESTINATION
```

Choose a destination that does not exist. Recovery verifies data and writes files;
it does not promote a demo, execute a probe or overwrite current recordings.

## Audit follow-up cleanup · 22 November 2026

The append-only [integration audit](audits/2026-11-22-integration-audit.md) found
that generated history had accumulated again. The user authorized correcting
that backlog. The verified archive is
`.private/history/2026-11-22-audit-follow-up-housekeeping/`.

- **2,207 output files / 42,093,475 bytes:** 18 superseded terminal journey runs,
  seven focused retail replay/probe roots, old foundation smoke/check output and
  dataset presentation captures. Failed and cancelled outcomes remain unchanged.
- **156 private review files / 9,372,415 bytes:** obsolete screenshots and
  verification material, with duplicate payloads retained once and every original
  path preserved in the private manifest.
- Three stale PID files were removed only after their owning-host processes were
  confirmed absent. The live web-review PID/log, live services and their output,
  live-owned run/job/workbench records, unknown runtime databases, recovery locks,
  current configuration, data and compatible environments remain in place.
- All **389 current demo-native files** remain byte-identical. The three selected
  raw demos remain under `runs/journeys/`; published recording packs are unchanged.

Owner and open-file checks were repeated immediately before removal. Every copied
file was checked for hash, size, mode and timestamp, and restored into a fresh
temporary directory before the active original was removed. The completion,
eligibility, ownership and restore receipts remain beside the manifests.
`runs/` decreased from 2,577 to 447 files; `artifacts/` from 171 to 94. These counts
describe this cleanup checkpoint, not a permanent quota for future current work.

Older verification entries and baseline inventory rows deliberately retain their
original `runs/...` locations as historical provenance. For those archived paths,
read `output-manifest.json` and `outputs/ORIGINAL_PATH` in this archive, or recover
to a new destination. Private review paths are mapped by `private-manifest.json`;
`reference-inventory.txt` records references found during the move. Never execute
historical probe scripts merely to recover their output.

```bash
python3 scripts/check_output_archive.py .private/history/2026-11-22-audit-follow-up-housekeeping
python3 .private/history/2026-11-22-audit-follow-up-housekeeping/recover.py .private/history/2026-11-22-audit-follow-up-housekeeping --restore /tmp/NEW_OUTPUT_DESTINATION
python3 .private/history/2026-11-22-audit-follow-up-housekeeping/recover-private.py .private/history/2026-11-22-audit-follow-up-housekeeping --restore /tmp/NEW_PRIVATE_DESTINATION
```

Both recovery destinations must be absent. Recovery does not overwrite current
files, promote evidence or start any application process. This archive is local
and ignored; it is absent from a public clone.

## Current versus historical documentation

README, plan, walkthrough, architecture, contracts and verification describe the
current gate. Consolidate superseded review decisions and test accounts in the
[dated review journal](history/guide-reviews-2026-11-19-20.md), with links from
current documentation. Preserve retained API/compatibility references and the
canonical North Star. Do not leave older journey counts presented as current
instructions or relabel a historical result as new acceptance.
