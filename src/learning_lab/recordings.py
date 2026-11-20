"""Read immutable, sanitized review packs; never discover private run folders."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from urllib.parse import quote

from .guide_sources import _git, repository_url
from .settings import ROOT

PACKS = ROOT / "recordings"


def pack_folder(run_id):
    if not isinstance(run_id, str) or str(uuid.UUID(run_id)) != run_id:
        raise ValueError("Choose a canonical recording identity")
    folder = PACKS / "photography" / run_id
    if any(p.is_symlink() for p in (PACKS, folder.parent, folder)):
        raise ValueError("Symbolic recording directories are not accepted")
    return folder


def load(run_id):
    folder = pack_folder(run_id)
    manifest = folder / "manifest.json"
    if not manifest.exists():
        return None
    if manifest.is_symlink():
        raise ValueError("Symbolic recording manifests are not accepted")
    record = json.loads(manifest.read_text())
    if (
        record.get("schema") != "citizen-recording/v1"
        or record.get("run_id") != run_id
        or record.get("scenario_id") != "photography"
    ):
        raise ValueError("Invalid recording manifest")
    for name, digest in record["files"].items():
        if not re.fullmatch(r"[a-z][a-z0-9-]*\.(?:json|jsonl|yaml)", name) or not re.fullmatch(
            "[a-f0-9]{64}", digest
        ):
            raise ValueError("Invalid recording file identifier")
        path = folder / name
        if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("Recording integrity check failed: " + name)
    if "trace.json" not in record["files"]:
        raise ValueError("Recording has no trace projection")
    return record


def listed():
    return [load(path.parent.name) for path in sorted((PACKS / "photography").glob("*/manifest.json"))]


def read(run_id, name):
    record = load(run_id)
    if record is None or name not in record["files"]:
        raise ValueError("File does not belong to this recording")
    return (pack_folder(run_id) / name).read_text()


def trace(run_id):
    record = load(run_id)
    if record is None:
        return None
    value = json.loads(read(run_id, "trace.json"))
    if (
        value.get("run", {}).get("run_id") != run_id
        or value["run"].get("scenario_id") != record["scenario_id"]
    ):
        raise ValueError("Recording trace belongs to another scenario or run")
    value["run"].update(
        kind="recorded",
        recording=True,
        owned_by_this_worker=False,
        run_directory=f"recordings/photography/{run_id}",
    )
    value["recording_notice"] = record["projection_notice"]
    value["artifacts"] = artifacts(run_id)
    return value


def artifacts(run_id):
    record = load(run_id)
    if record is None:
        return []
    relative = f"recordings/photography/{run_id}"
    revision = _git("log", "-1", "--format=%H", "--", relative) or None
    repository = repository_url()
    result = []
    for name, digest in record["files"].items():
        identity = hashlib.sha256((run_id + ":" + name).encode()).hexdigest()[:24]
        preview = f"/api/journey/artifact?run_id={run_id}&artifact_id={identity}"
        github = f"{repository}/blob/{revision}/{quote(relative)}/{name}" if repository and revision else None
        result.append(
            {
                "id": identity,
                "path": name,
                "sha256": digest,
                "kind": "recorded",
                "bytes": (pack_folder(run_id) / name).stat().st_size,
                "url": github or preview,
                "github_url": github,
                "preview_url": preview,
                "recording_revision": revision,
            }
        )
    return result


def artifact(run_id, identity):
    row = next((item for item in artifacts(run_id) if item["id"] == identity), None)
    if row is None:
        raise ValueError("Artifact does not belong to the selected recording")
    raw = read(run_id, row["path"])
    clipped = raw[: 1024 * 1024]
    try:
        content = json.loads(clipped)
    except ValueError:
        content = clipped
    return {
        **row,
        "run_id": run_id,
        "scenario_id": "photography",
        "content": content,
        "truncated": len(raw) > len(clipped),
    }
