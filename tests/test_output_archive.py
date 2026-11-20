"""Recovery must preserve evidence without overwriting data or escaping paths."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "output_archive", Path(__file__).parents[1] / "scripts/check_output_archive.py"
)
archive_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(archive_tool)


def make_archive(tmp_path):
    archive = tmp_path / "archive"
    file = archive / "outputs/runs/failed-example/events.jsonl"
    file.parent.mkdir(parents=True)
    payload = b'{"status":"failed","usage":null}\n'
    file.write_bytes(payload)
    row = {"path": "runs/failed-example/events.jsonl", "bytes": len(payload),
           "sha256": hashlib.sha256(payload).hexdigest()}
    (archive / "output-manifest.json").write_text(
        json.dumps({"version": 1, "verified": True, "files": [row]})
    )
    return archive, file, payload


def test_recovery_preserves_failed_evidence_and_refuses_overwrite(tmp_path):
    archive, _, payload = make_archive(tmp_path)
    target = tmp_path / "recovered"
    archive_tool.recover(archive, target)
    assert (target / "runs/failed-example/events.jsonl").read_bytes() == payload
    with pytest.raises(ValueError, match="new destination"):
        archive_tool.recover(archive, target)


@pytest.mark.parametrize("path", ["../secret", "/runs/file", "runs/../secret", "src/file",
                                   "runs//file", "runs/file", "runs/./file", "runs/evil\\file"])
def test_invalid_or_corrupt_manifest_writes_nothing(tmp_path, path):
    archive, _, _ = make_archive(tmp_path)
    manifest_path = archive / "output-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"][0]["path"] = path
    manifest_path.write_text(json.dumps(manifest))
    target = tmp_path / "must-not-exist"
    with pytest.raises(ValueError):
        archive_tool.recover(archive, target)
    assert not target.exists()


def test_tampering_and_symlinks_fail_before_recovery(tmp_path):
    archive, file, _ = make_archive(tmp_path)
    target = tmp_path / "must-not-exist"
    file.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="match"):
        archive_tool.recover(archive, target)
    file.unlink()
    file.symlink_to(tmp_path / "outside")
    with pytest.raises(ValueError, match="symbolic link"):
        archive_tool.recover(archive, target)
    assert not target.exists()
