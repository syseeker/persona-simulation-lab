#!/usr/bin/env python3
"""Verify private historical output, optionally recovering to a new directory.

This tool never imports the application or starts a worker, model or runtime.
Existing destinations are never overwritten; verify every source before writing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil


def _plain_file(root: Path, relative: str) -> Path:
    path = root
    for part in PurePosixPath(relative).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("Archive contains a symbolic link")
    if not path.is_file():
        raise ValueError("Archive file is missing")
    return path


def verify(archive: Path) -> list[dict]:
    archive = Path(os.path.abspath(archive))
    if any(parent.is_symlink() for parent in [archive, *archive.parents]):
        raise ValueError("Archive location must not traverse symbolic links")
    manifest = json.loads(_plain_file(archive, "output-manifest.json").read_text())
    if manifest.get("version") != 1 or manifest.get("verified") is not True:
        raise ValueError("Unsupported or incomplete output manifest")
    records = manifest.get("files")
    if not isinstance(records, list) or not records:
        raise ValueError("Archive has no file manifest")
    seen = set()
    for row in records:
        name = row.get("path")
        if not isinstance(name, str):
            raise ValueError("Invalid archive path")
        parts = PurePosixPath(name).parts
        if (
            not parts
            or name != str(PurePosixPath(name))
            or name.startswith("/")
            or "\\" in name
            or ":" in name
            or ".." in parts
            or parts[0] not in {"runs", "artifacts"}
            or len(parts) < 2
            or name in seen
        ):
            raise ValueError("Unsafe or duplicate archive path")
        seen.add(name)
        file = _plain_file(archive, "outputs/" + name)
        if file.stat().st_size != row.get("bytes"):
            raise ValueError("Archived size does not match")
        if hashlib.sha256(file.read_bytes()).hexdigest() != row.get("sha256"):
            raise ValueError("Archived checksum does not match")
    installed = archive / "outputs"
    actual = set()
    for folder, directories, files in os.walk(installed):
        if any((Path(folder) / item).is_symlink() for item in [*directories, *files]):
            raise ValueError("Archive output tree contains a symbolic link")
        actual.update(str((Path(folder) / item).relative_to(installed)) for item in files)
    if actual != seen:
        raise ValueError("Archived file set does not match the manifest")
    return records


def recover(archive: Path, destination: Path) -> list[dict]:
    records = verify(archive)
    destination = Path(os.path.abspath(destination))
    if destination.exists() or destination.is_symlink():
        raise ValueError("Recovery requires a new destination; nothing is overwritten")
    if any(parent.is_symlink() for parent in destination.parents):
        raise ValueError("Recovery destination must not traverse symbolic links")
    if destination.is_relative_to(Path(archive).resolve()):
        raise ValueError("Recovery must be outside the archive")
    destination.mkdir(parents=True, mode=0o700)
    for row in records:
        target = destination / row["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(Path(archive) / "outputs" / row["path"], target)
        if hashlib.sha256(target.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("Recovered checksum does not match")
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--restore", type=Path, help="Recover into a new directory; never execute output")
    args = parser.parse_args()
    records = recover(args.archive, args.restore) if args.restore else verify(args.archive)
    print(json.dumps({"verified": True, "files": len(records),
                      "bytes": sum(row["bytes"] for row in records),
                      "restored": args.restore is not None, "application_executed": False}))


if __name__ == "__main__":
    main()
