"""Offline published-pack contracts; fixtures are not executed scenario evidence."""

import hashlib
import json
import uuid

import pytest

from learning_lab import recordings
from learning_lab.journey import JourneyService
from scripts.export_guide_recording import clean


def pack(tmp_path, monkeypatch):
    root = tmp_path / "recordings"
    monkeypatch.setattr(recordings, "PACKS", root)
    monkeypatch.setattr(recordings, "_git", lambda *args: "fixture-commit")
    monkeypatch.setattr(recordings, "repository_url", lambda: "https://github.com/example/review")
    identity = str(uuid.uuid4())
    folder = root / "photography" / identity
    folder.mkdir(parents=True)
    state = {
        "run_id": identity,
        "scenario_id": "photography",
        "created_at": "2026-11-20T00:00:00Z",
        "status": "completed",
        "calls": 5,
    }
    bodies = {"trace.json": json.dumps({"run": state, "conversation": []}), "usage.json": '{"calls":5}'}
    for name, content in bodies.items():
        (folder / name).write_text(content)
    manifest = {
        "schema": "citizen-recording/v1",
        "run_id": identity,
        "scenario_id": "photography",
        "projection_notice": "Offline fixture",
        "files": {name: hashlib.sha256(content.encode()).hexdigest() for name, content in bodies.items()},
    }
    (folder / "manifest.json").write_text(json.dumps(manifest))
    return identity, folder


def test_checked_in_recording_works_without_local_runs(tmp_path, monkeypatch):
    identity, _ = pack(tmp_path, monkeypatch)
    service = JourneyService(tmp_path / "absent-private-runs")
    result = service.trace(identity)
    assert result["run"]["kind"] == "recorded" and result["run"]["recording"]
    assert result["inference_calls_for_inspection"] == 0
    assert service.list()["runs"][0]["run_id"] == identity
    assert not service.root.exists()
    usage = next(item for item in result["artifacts"] if item["path"] == "usage.json")
    assert (
        usage["url"]
        == f"https://github.com/example/review/blob/fixture-commit/recordings/photography/{identity}/usage.json"
    )
    assert service.artifact(identity, usage["id"])["content"] == {"calls": 5}


def test_corrupted_recording_never_falls_back_to_another_run(tmp_path, monkeypatch):
    identity, folder = pack(tmp_path, monkeypatch)
    (folder / "usage.json").write_text('{"calls":0}')
    with pytest.raises(ValueError, match="integrity"):
        JourneyService(tmp_path / "private").trace(identity)


def test_recording_cannot_escape_via_manifest_path_or_symlink(tmp_path, monkeypatch):
    identity, folder = pack(tmp_path, monkeypatch)
    path = folder / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["files"]["../private.json"] = "a" * 64
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="identifier"):
        recordings.load(identity)
    del manifest["files"]["../private.json"]
    path.write_text(json.dumps(manifest))
    (folder / "usage.json").unlink()
    (folder / "usage.json").symlink_to(tmp_path / "private")
    with pytest.raises(ValueError, match="integrity"):
        recordings.load(identity)


async def test_recording_has_no_live_cancellation_or_recovery(tmp_path, monkeypatch):
    identity, _ = pack(tmp_path, monkeypatch)
    service = JourneyService(tmp_path / "private")
    with pytest.raises(ValueError, match="recording"):
        await service.cancel(identity)
    with pytest.raises(ValueError, match="recording"):
        await service.recover(identity)
    assert not service.root.exists()


def test_public_export_redacts_known_credentials_and_local_paths(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "offline-fixture-secret-value")
    value = clean(
        {
            "api_key": "offline-fixture-secret-value",
            "nested": [{"detail": "oops offline-fixture-secret-value /home/fixture-user/private/path"}],
        }
    )
    assert "api_key" not in value
    assert "offline-fixture-secret-value" not in json.dumps(value)
    assert "/home/fixture-user" not in json.dumps(value)


def test_export_publishes_only_review_fields_and_refuses_overwrite(tmp_path, monkeypatch):
    import scripts.export_guide_recording as exporter

    identity = str(uuid.uuid4())
    local = tmp_path / "private" / identity
    local.mkdir(parents=True)
    state = {
        "run_id": identity,
        "scenario_id": "photography",
        "status": "completed",
        "cleanup_confirmed": True,
        "episode_id": "episode-fixture",
        "owner_pid": 777,
        "spec": {"source_id": "PRIVATE-ORIGINAL-ID"},
    }
    (local / "run.json").write_text(json.dumps(state))
    (local / "catalogue-snapshot.json").write_text('{"public":"facts"}')
    (local / "usersim-activations.jsonl").write_text(
        '{"role":"user","activation_id":"native-fixture","private_prompt":"PRIVATE-CONTEXT"}\n'
    )
    (local / "resolved-inputs.json").write_text('{"private":"PRIVATE-CONTEXT"}')
    trace = {
        "conversation": [
            {"turn": 1, "role": "user", "content": "Public photography request", "private": "PRIVATE-CONTEXT"}
        ],
        "relay": {"scopes": [{"uuid": "native-fixture", "input": "PRIVATE-CONTEXT", "status": "completed"}]},
        "tools": [],
        "usage": {"calls": 0, "records": []},
        "source_lock": {"source": "ngc", "source_id": "PRIVATE-ORIGINAL-ID"},
        "situation": {"kind": "authored"},
        "evaluation": None,
    }

    class Service:
        def folder(self, run_id):
            assert run_id == identity
            return local

        def trace(self, run_id):
            return trace

    monkeypatch.setattr(exporter, "JourneyService", Service)
    destination = tmp_path / "public" / identity
    exporter.export(identity, note="Offline privacy fixture", destination=destination)
    published = "".join(p.read_text() for p in destination.iterdir())
    assert "Public photography request" in published and "native-fixture" in published
    assert "PRIVATE-CONTEXT" not in published and "PRIVATE-ORIGINAL-ID" not in published
    assert "owner_pid" not in published and not (destination / "resolved-inputs.json").exists()
    with pytest.raises(ValueError, match="immutable"):
        exporter.export(identity, note="Do not replace", destination=destination)
