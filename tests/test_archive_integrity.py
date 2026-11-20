"""Archive recovery must never follow payload links or create an unsafe target."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


SPEC = importlib.util.spec_from_file_location(
    "archive_integrity", Path(__file__).resolve().parents[1] / "scripts/check_archive.py"
)
archive_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(archive_tool)


@pytest.fixture
def snapshot(tmp_path):
    archive = tmp_path / "snapshot"
    archive.mkdir()
    source = archive / "src/example.py"
    source.parent.mkdir()
    source.write_bytes(b"raise RuntimeError('must never execute archived code')\n")
    source.chmod(0o640)
    entry = {"path": "src/example.py", "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
             "bytes": source.stat().st_size, "mode": 0o640}
    manifest = archive / "archive-manifest.json"
    manifest.write_text(json.dumps({"format": 1, "files": [entry]}))
    return archive, manifest, entry


def rewrite(manifest, entries):
    manifest.write_text(json.dumps({"format": 1, "files": entries}))


def test_restore_copies_only_verified_manifest_files_without_execution(snapshot, tmp_path):
    archive, _, entry = snapshot
    (archive / ".env").write_text("excluded fixture, not a real credential")
    target = tmp_path / "recovered"
    checkout = tmp_path / "active"
    checkout.mkdir()
    restored, entries = archive_tool.restore_archive(target, archive=archive, checkout=checkout)
    assert restored == target and entries == [entry]
    assert (target / entry["path"]).read_bytes() == (archive / entry["path"]).read_bytes()
    assert (target / entry["path"]).stat().st_mode & 0o777 == 0o640
    assert not (target / ".env").exists()
    assert not (target / "archive-manifest.json").exists()


@pytest.mark.parametrize("relative", [
    "../outside.py", "/absolute.py", "a/../../outside.py", "a/./file.py", "a//file.py",
    "C:/outside.py", "C:outside.py", "a\\outside.py", ".env", "x/.env.production",
    ".private/secret", "x/data/personas.json", "runs/trace.json", "x/.venv/bin/python",
])
def test_unsafe_manifest_paths_fail_before_destination_creation(snapshot, tmp_path, relative):
    archive, manifest, entry = snapshot
    rewrite(manifest, [{**entry, "path": relative}])
    target = tmp_path / "not-created"
    with pytest.raises(archive_tool.ArchiveError):
        archive_tool.restore_archive(target, archive=archive, checkout=tmp_path / "active")
    assert not target.exists()


def test_duplicate_and_file_parent_collisions_are_rejected(snapshot):
    archive, manifest, entry = snapshot
    for entries in ([entry, entry], [entry, {**entry, "path": "src/example.py/child"}]):
        rewrite(manifest, entries)
        with pytest.raises(archive_tool.ArchiveError):
            archive_tool.verify_archive(archive)


@pytest.mark.parametrize("kind", ["file", "parent", "root"])
def test_payload_symlinks_even_inside_snapshot_are_rejected(snapshot, tmp_path, kind):
    archive, _, entry = snapshot
    if kind == "file":
        source = archive / entry["path"]
        source.rename(archive / "ordinary.py")
        source.symlink_to(archive / "ordinary.py")
    elif kind == "parent":
        (archive / "src").rename(archive / "ordinary-directory")
        (archive / "src").symlink_to(archive / "ordinary-directory", target_is_directory=True)
    else:
        alias = tmp_path / "snapshot-link"
        alias.symlink_to(archive, target_is_directory=True)
        archive = alias
    with pytest.raises(archive_tool.ArchiveError):
        archive_tool.verify_archive(archive)


@pytest.mark.parametrize("change", ["hash", "size", "mode"])
def test_corruption_fails_before_creation(snapshot, tmp_path, change):
    archive, manifest, entry = snapshot
    changed = dict(entry)
    changed[{"hash": "sha256", "size": "bytes", "mode": "mode"}[change]] = {
        "hash": "0" * 64, "size": entry["bytes"] + 1, "mode": 0o600,
    }[change]
    rewrite(manifest, [changed])
    target = tmp_path / "not-created"
    with pytest.raises(archive_tool.ArchiveError):
        archive_tool.restore_archive(target, archive=archive, checkout=tmp_path / "active")
    assert not target.exists()


def test_existing_checkout_and_symlinked_destinations_are_rejected(snapshot, tmp_path):
    archive, _, _ = snapshot
    checkout = tmp_path / "active"
    checkout.mkdir()
    existing = tmp_path / "existing"
    existing.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(checkout, target_is_directory=True)
    for target in (existing, checkout / "new", linked / "new", archive / "new"):
        with pytest.raises(archive_tool.ArchiveError):
            archive_tool.restore_archive(target, archive=archive, checkout=checkout)
        assert not target.exists() or target == existing
    assert list(existing.iterdir()) == []
