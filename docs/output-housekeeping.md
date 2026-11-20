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

## Current versus historical documentation

README, plan, walkthrough, architecture, contracts and verification describe the
current gate. Consolidate superseded review decisions and test accounts in the
[dated review journal](history/guide-reviews-2026-11-19-20.md), with links from
current documentation. Preserve retained API/compatibility references and the
canonical North Star. Do not leave older journey counts presented as current
instructions or relabel a historical result as new acceptance.
