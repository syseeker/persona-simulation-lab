"""Bounded, read-only access to allowlisted local evidence and native Relay scopes.

Artifact IDs are derived from discovered files, never interpreted as paths. Browser
projections redact credentials while original SDK records remain on local disk.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from .settings import ROOT

MAX_BYTES = 1024 * 1024
MAX_EVENTS = 2000
_UUID = re.compile(r"[a-f0-9-]{36}")
_FILES = {
    "chat.json": "chat_manifest",
    "usage.json": "usage",
    "run.json": "manifest",
    "events.jsonl": "application_events",
    "resolved-inputs.json": "inputs",
    "catalogue-snapshot.json": "catalogue",
    "target-history.json": "target_history",
    "reply-outcomes.jsonl": "replies",
    "usersim-result.json": "usersim",
    "relay.jsonl": "relay",
    "fabric-config.json": "fabric_config",
    "fabric-plan.json": "fabric_plan",
    "fabric-doctor.json": "fabric_doctor",
    "fabric-lifecycle.jsonl": "fabric_lifecycle",
    "helix-criteria.json": "evaluation_criteria",
    "helix-results.json": "evaluation_metrics",
    "evaluation-details.json": "evaluation_details",
    "overlays.json": "overlays",
}
CODE_REFS = {
    "application": "src/learning_lab/service.py",
    "simulation": "src/learning_lab/simulation.py",
    "relay": "src/learning_lab/target.py",
    "fabric": "src/learning_lab/fabric_target.py",
    "mcp": "src/learning_lab/course_mcp.py",
    "gateway": "src/learning_lab/inference.py",
    "evaluation": "src/learning_lab/evaluation.py",
}
_SECRET_KEY = re.compile(
    r"(?:authorization|cookie|password|credential|secret|access.?token|refresh.?token|api.?key|gateway.?key|private.?key|(?:^|_)token$|^key$)",
    re.I,
)


def sanitize(value, depth=0):
    """Redact headers, secret-valued fields and common bearer/key forms recursively."""
    if depth > 25:
        return "[depth limit]"
    if isinstance(value, dict):
        return {
            str(k): (
                "[redacted]"
                if str(k).lower() == "headers"
                or (_SECRET_KEY.search(str(k)) and not str(k).endswith(("_env", "_present")))
                else sanitize(v, depth + 1)
            )
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [sanitize(item, depth + 1) for item in value]
    if isinstance(value, str):
        if value.lstrip().startswith(("{", "[")):
            try:
                decoded = json.loads(value)
                if isinstance(decoded, (dict, list)):
                    return json.dumps(sanitize(decoded, depth + 1), ensure_ascii=False)
            except (ValueError, RecursionError):
                pass
        value = re.sub(r"\bBearer\s+[^\s\"'<>]+", "Bearer [redacted]", value, flags=re.I)
        value = re.sub(r"\bnvapi-[A-Za-z0-9_-]+", "[redacted NVIDIA key]", value)
        value = re.sub(
            r"(?i)(api[_-]?key|access[_-]?token|password|secret)=([^&\s]+)", r"\1=[redacted]", value
        )
        return value
    if value is None or isinstance(value, (int, float, bool)):
        return value
    if hasattr(value, "model_dump"):
        return sanitize(value.model_dump(mode="json"), depth + 1)
    if hasattr(value, "to_dict"):
        return sanitize(value.to_dict(), depth + 1)
    return str(value)


def save_evidence(path: Path, value, *, append=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a" if append else "w") as file:
        file.write(json.dumps(sanitize(value), default=str, ensure_ascii=False) + "\n")


def decode_native(value, depth=0):
    """Decode known Relay value envelopes and MCP text, preserving the raw file.

    Deserialization is data-only: class names are never imported and source
    strings are never evaluated. Unknown wrapper kinds remain visible as data.
    """
    if depth > 16:
        return value
    if isinstance(value, str):
        if value.startswith("<untrusted_tool_result"):
            start = value.find("\n\n{")
            if start >= 0:
                return decode_native(value[start + 2 :].rsplit("\n</untrusted_tool_result>", 1)[0], depth + 1)
        if value.lstrip().startswith(("{", "[")):
            try:
                return decode_native(json.loads(value), depth + 1)
            except ValueError:
                pass
        return value
    if isinstance(value, dict):
        kind = value.get("kind")
        if (
            isinstance(kind, str)
            and kind in {"model", "dict", "list", "tuple", "json"}
            and "value" in value
            and set(value) <= {"kind", "value", "type", "fields_set"}
        ):
            decoded = decode_native(value["value"], depth + 1)
            if (
                value.get("kind") == "model"
                and str(value.get("type", "")).endswith(".ToolMessage")
                and isinstance(decoded, dict)
            ):
                return decode_native(decoded.get("content", decoded), depth + 1)
            return decoded
        return {key: decode_native(item, depth + 1) for key, item in value.items()}
    if isinstance(value, list):
        decoded = [decode_native(item, depth + 1) for item in value]
        if (
            len(decoded) == 1
            and isinstance(decoded[0], dict)
            and "text" in decoded[0]
            and decoded[0].get("type", "text") == "text"
        ):
            return decode_native(decoded[0]["text"], depth + 1)
        return decoded
    return value


def _safe(root: Path, path: Path) -> bool:
    try:
        relative = path.relative_to(root)
        if any((root / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)):
            return False
        return path.is_file() and path.resolve().is_relative_to(root.resolve())
    except (OSError, ValueError):
        return False


def _paths(folder: Path):
    """Only fixed filenames and known episode/runtime directory topology are eligible."""
    if not folder.exists():
        return
    bases = [folder]
    bases.extend(
        sorted(p for p in folder.iterdir() if _UUID.fullmatch(p.name) and p.is_dir() and not p.is_symlink())[
            :200
        ]
    )
    for base in bases:
        for name in _FILES:
            path = base / name
            if _safe(folder, path):
                yield path
        traces = base / "fabric-traces"
        if traces.is_dir() and not traces.is_symlink():
            for runtime in sorted(traces.iterdir())[:200]:
                path = runtime / "relay.jsonl"
                if runtime.is_dir() and not runtime.is_symlink() and _safe(folder, path):
                    yield path


def _code_refs(kind):
    keys = ["application"]
    keys += ["relay", "gateway", "mcp"] if kind in {"relay", "target_history", "replies"} else []
    keys += ["fabric"] if kind.startswith("fabric") else []
    keys += ["evaluation"] if kind.startswith("evaluation") else []
    return [{"label": key, "path": CODE_REFS[key], "local_path": str(ROOT / CODE_REFS[key])} for key in keys]


def list_artifacts(folder: Path) -> list[dict]:
    result = []
    for path in sorted(_paths(folder) or []):
        relative = path.relative_to(folder).as_posix()
        kind = _FILES[path.name]
        result.append(
            {
                "id": hashlib.sha256(relative.encode()).hexdigest()[:24],
                "name": relative,
                "kind": kind,
                "size": path.stat().st_size,
                "path": str(path.absolute()),
                "code_refs": _code_refs(kind),
            }
        )
    return result


def _read(path: Path):
    notices = []
    if path.suffix == ".jsonl":
        values, size = [], 0
        with path.open("rb") as file:
            while line := file.readline(MAX_BYTES + 1):
                size += len(line)
                if size > MAX_BYTES or len(values) >= MAX_EVENTS:
                    notices.append(
                        "Evidence is truncated by the local read limit; inspect the original local file for the remainder."
                    )
                    break
                try:
                    values.append(json.loads(line))
                except (ValueError, UnicodeDecodeError):
                    notices.append("A malformed or partially written event was skipped.")
        return values, notices
    if path.stat().st_size > MAX_BYTES:
        return None, ["Artifact exceeds the local read limit; inspect the original local file."]
    try:
        return json.loads(path.read_text()), notices
    except (ValueError, UnicodeDecodeError):
        return None, ["Artifact is malformed or still being written."]


def read_artifact(folder: Path, artifact_id: str) -> dict:
    selected = next((item for item in list_artifacts(folder) if item["id"] == artifact_id), None)
    if selected is None:
        raise ValueError("Unknown or unavailable evidence artifact")
    path = folder / selected["name"]
    if not _safe(folder, path):
        raise ValueError("Evidence artifact is unavailable")
    value, notices = _read(path)
    return {**selected, "content": sanitize(value), "truncated": bool(notices), "notices": notices}


def _duration(start, end):
    try:
        return max(
            0,
            round(
                (
                    datetime.fromisoformat(end.replace("Z", "+00:00"))
                    - datetime.fromisoformat(start.replace("Z", "+00:00"))
                ).total_seconds()
                * 1000,
                3,
            ),
        )
    except (TypeError, ValueError, AttributeError):
        return None


def relay_scopes(folder: Path) -> dict:
    scopes, notices, count = [], [], 0
    for artifact in list_artifacts(folder):
        if artifact["kind"] != "relay":
            continue
        events, warnings = _read(folder / artifact["name"])
        notices.extend(warnings)
        count += len(events)
        grouped = {}
        for event in events:
            if (
                not isinstance(event, dict)
                or event.get("scope_category") not in {"start", "end"}
                or not event.get("uuid")
            ):
                continue
            uid = str(event["uuid"])
            category = event.get("category")
            key = (uid, str(category))
            pair = grouped.setdefault(key, {})
            phase = event["scope_category"]
            if phase in pair:
                notices.append("Duplicate native Relay scope phase; the first saved record is displayed.")
            else:
                pair[phase] = event
        for (uid, category), pair in grouped.items():
            start, end = pair.get("start", {}), pair.get("end", {})
            event = start or end
            parent = event.get("parent_uuid")
            failed = str(end.get("metadata", {}).get("otel.status_code", "")).upper() == "ERROR"
            failed = failed or isinstance(end.get("data"), dict) and end["data"].get("is_error") is True
            scopes.append(
                {
                    "id": artifact["id"] + ":" + uid,
                    "uuid": uid,
                    "parent_uuid": parent,
                    "parent_id": artifact["id"] + ":" + str(parent) if parent else None,
                    "artifact_id": artifact["id"],
                    "category": category,
                    "name": event.get("name", category),
                    "status": "failed" if failed else "completed" if start and end else "incomplete",
                    "started_at": start.get("timestamp"),
                    "ended_at": end.get("timestamp"),
                    "duration_ms": _duration(start.get("timestamp"), end.get("timestamp")),
                    "input": sanitize(decode_native(start.get("data"))),
                    "output": sanitize(decode_native(end.get("data"))),
                    "metadata": sanitize(end.get("metadata", {})),
                    "code_refs": _code_refs("relay"),
                }
            )
    ids = {scope["id"] for scope in scopes}
    for scope in scopes:
        scope["parent_available"] = scope["parent_id"] in ids if scope["parent_id"] else True
    roots = [scope["id"] for scope in scopes if not scope["parent_id"] or not scope["parent_available"]]
    if not scopes:
        notices.append(
            "No native Relay scopes were saved for this selection; application messages are separate evidence."
        )
    return {"events": count, "scopes": scopes, "roots": roots, "notices": list(dict.fromkeys(notices))}


def native_tool_records(folder: Path, *, exclude_uuids=()) -> list[dict]:
    """Project only observed paired native tool scopes; never infer tools from replies."""
    excluded = set(exclude_uuids)
    result = []
    for scope in relay_scopes(folder)["scopes"]:
        if scope["category"] != "tool" or scope["uuid"] in excluded:
            continue
        output = decode_native(scope["output"])
        for _ in range(4):
            if isinstance(output, str):
                try:
                    output = json.loads(output)
                except ValueError:
                    break
            elif isinstance(output, dict) and "result" in output:
                output = output["result"]
            else:
                break
        content = output.get("result", output.get("content", output)) if isinstance(output, dict) else output
        result.append(
            {
                "name": scope["name"],
                "arguments": scope["input"],
                "result": content,
                "content": json.dumps(content, ensure_ascii=False),
                "scope_uuid": scope["uuid"],
                "status": scope["status"],
                "evidence_origin": "native_relay",
            }
        )
    return result


def build_evidence(folder: Path) -> dict:
    artifacts = list_artifacts(folder)
    fabric = {"config": [], "plan": [], "doctor": [], "lifecycle": []}
    for artifact in artifacts:
        if artifact["kind"].startswith("fabric_"):
            name = artifact["kind"].removeprefix("fabric_")
            if name in fabric:
                value = read_artifact(folder, artifact["id"])
                fabric[name].append(
                    {"artifact_id": artifact["id"], "content": value["content"], "notices": value["notices"]}
                )
    return {
        "version": 2,
        "folder": str(folder.absolute()),
        "artifacts": artifacts,
        "relay": relay_scopes(folder),
        "fabric": fabric,
        "code_refs": [
            {"label": key, "path": value, "local_path": str(ROOT / value)} for key, value in CODE_REFS.items()
        ],
    }


def lifecycle(folder: Path, event: str, **metadata):
    save_evidence(
        folder / "fabric-lifecycle.jsonl",
        {"at": datetime.now(timezone.utc).isoformat(), "event": event, **metadata},
        append=True,
    )
