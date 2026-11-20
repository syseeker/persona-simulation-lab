"""Verify the historical v0.2 source snapshot; optionally copy it to a new directory.

This standard-library tool never imports or executes archived application code.
It restores source files only, not Git state, credentials or local runtime setup.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import sys


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "docs/history/v0.2"
MANIFEST = "archive-manifest.json"
EXCLUDED = frozenset({
    ".git", ".private", "data", "runs", "artifacts", ".venv", "venv", "venvs",
    "environments", "node_modules", "__pycache__", ".cache", "cache", "caches",
    ".pytest_cache", ".ruff_cache", ".svelte-kit", "build", "coverage",
    "playwright-report", "test-results", ".aws", ".codex", ".upstream",
    ".bundle", ".data-designer", ".nemo-relay",
})


class ArchiveError(ValueError):
    """The snapshot or restore destination failed an integrity/safety check."""


def _relative(value: object) -> str:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        raise ArchiveError("Manifest paths must be nonempty canonical relative paths")
    path = PurePosixPath(value)
    if (path.is_absolute() or PureWindowsPath(value).drive or path.as_posix() != value
            or any(part in {".", ".."} for part in value.split("/"))):
        raise ArchiveError(f"Unsafe manifest path: {value!r}")
    for part in path.parts:
        if part in EXCLUDED or (part.startswith(".env") and part != ".env.example"):
            raise ArchiveError(f"Excluded local state in manifest: {value!r}")
    return value


def _regular(root: Path, relative: str) -> Path:
    """Reject symbolic links at every component, including the archive root."""
    current = root
    if not stat.S_ISDIR(current.lstat().st_mode):
        raise ArchiveError("The snapshot root must be an ordinary directory")
    for part in PurePosixPath(relative).parts[:-1]:
        current /= part
        if not stat.S_ISDIR(current.lstat().st_mode):
            raise ArchiveError(f"Snapshot parent is not an ordinary directory: {relative!r}")
    result = root / relative
    if not stat.S_ISREG(result.lstat().st_mode):
        raise ArchiveError(f"Snapshot entry is not an ordinary file: {relative!r}")
    return result


def _open_read(path: Path):
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise ArchiveError("Snapshot entry changed to a non-regular file")
    return os.fdopen(descriptor, "rb")


def _records(archive: Path) -> list[dict]:
    manifest = _regular(archive, MANIFEST)
    if manifest.stat().st_size > 4 * 1024 * 1024:
        raise ArchiveError("Archive manifest exceeds its read limit")
    with _open_read(manifest) as stream:
        payload = json.load(stream)
    if (not isinstance(payload, dict) or type(payload.get("format")) is not int
            or payload["format"] != 1 or not isinstance(payload.get("files"), list)
            or not payload["files"]):
        raise ArchiveError("Expected a nonempty format-1 source manifest")
    records, names = [], set()
    for entry in payload["files"]:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256", "bytes", "mode"}:
            raise ArchiveError("Malformed source-file manifest entry")
        relative = _relative(entry["path"])
        if relative in names:
            raise ArchiveError(f"Duplicate manifest path: {relative!r}")
        if (not isinstance(entry["sha256"], str)
                or not re.fullmatch(r"[a-f0-9]{64}", entry["sha256"])
                or type(entry["bytes"]) is not int or entry["bytes"] < 0
                or type(entry["mode"]) is not int or not 0 <= entry["mode"] <= 0o777):
            raise ArchiveError(f"Invalid hash, size or permission mode: {relative!r}")
        names.add(relative)
        records.append(dict(entry))
    for relative in names:
        if any(parent.as_posix() in names for parent in PurePosixPath(relative).parents):
            raise ArchiveError(f"A manifest file is also a parent directory: {relative!r}")
    return records


def _verify_files(root: Path, records: list[dict]) -> None:
    for entry in records:
        path = _regular(root, entry["path"])
        with _open_read(path) as stream:
            observed = os.fstat(stream.fileno())
            if observed.st_size != entry["bytes"] or stat.S_IMODE(observed.st_mode) != entry["mode"]:
                raise ArchiveError(f"Size or mode differs: {entry['path']!r}")
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if digest != entry["sha256"]:
                raise ArchiveError(f"SHA-256 differs: {entry['path']!r}")


def verify_archive(archive: Path = ARCHIVE) -> list[dict]:
    """Return verified manifest entries without creating files or loading the app."""
    archive = Path(os.path.abspath(archive))
    records = _records(archive)
    _verify_files(archive, records)
    return records


def _destination(destination: Path, checkout: Path) -> Path:
    target = Path(os.path.abspath(destination))
    if os.path.lexists(target):
        raise ArchiveError("Restore destination already exists; choose a new directory")
    if target.resolve().is_relative_to(checkout.resolve()):
        raise ArchiveError("Restore destination must be outside the active checkout")
    # Require an existing real parent: the tool only creates its new owned root
    # and the manifest's relative subdirectories, never arbitrary parent trees.
    for parent in target.parents:
        if not stat.S_ISDIR(parent.lstat().st_mode):
            raise ArchiveError("Restore destination needs existing non-symlink parent directories")
    return target


def restore_archive(destination: Path, *, archive: Path = ARCHIVE,
                    checkout: Path = ROOT) -> tuple[Path, list[dict]]:
    """Verify everything first, then restore only listed source into a fresh root."""
    archive = Path(os.path.abspath(archive))
    records = verify_archive(archive)
    target = _destination(destination, checkout)
    # Also forbid restoring inside a separately supplied archive outside ROOT.
    if target.resolve().is_relative_to(archive.resolve()):
        raise ArchiveError("Restore destination must be outside the snapshot")
    target.mkdir(mode=0o700)
    for entry in records:
        relative = PurePosixPath(entry["path"])
        parent = target
        for part in relative.parts[:-1]:
            parent /= part
            try:
                parent.mkdir(mode=0o700)
            except FileExistsError:
                if not stat.S_ISDIR(parent.lstat().st_mode):
                    raise ArchiveError("Restore parent changed to a non-directory") from None
        source = _regular(archive, entry["path"])
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(target / entry["path"], flags, 0o600)
        with os.fdopen(descriptor, "wb") as output, _open_read(source) as incoming:
            while chunk := incoming.read(1024 * 1024):
                output.write(chunk)
            output.flush()
            os.fchmod(output.fileno(), entry["mode"])
    _verify_files(target, records)
    return target, records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore", type=Path, metavar="NEW_DEST",
                        help="Copy verified source to a new directory outside this checkout")
    args = parser.parse_args(argv)
    try:
        if args.restore is None:
            target, records = None, verify_archive()
        else:
            target, records = restore_archive(args.restore)
    except (ArchiveError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"Archive check failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({
        "verified": True,
        "files": len(records),
        "bytes": sum(entry["bytes"] for entry in records),
        "restored_to": str(target) if target else None,
        "git_state_restored": False,
        "application_executed": False,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
