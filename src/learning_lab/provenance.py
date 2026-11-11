"""Read-only provenance assembled from saved inputs, tool records and frozen facts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from .catalogue import all_courses

PROFILE_FIELDS = [
    "age",
    "occupation",
    "planning_area",
    "education_level",
    "skills_and_expertise_list",
    "skills_and_expertise",
    "hobbies_and_interests_list",
    "hobbies_and_interests",
    "career_goals_and_ambitions",
]


def decode_content(value, depth=0):
    if depth > 5:
        return value
    if isinstance(value, str):
        try:
            return decode_content(json.loads(value), depth + 1)
        except (ValueError, TypeError):
            return value
    if isinstance(value, list) and len(value) == 1 and isinstance(value[0], dict) and "text" in value[0]:
        return decode_content(value[0]["text"], depth + 1)
    return value


def course_ids(text: str) -> set[str]:
    text = text.translate(str.maketrans({"\u2011": "-", "\u2013": "-", "\u2010": "-"}))
    return set(re.findall(r"\b(?:CC|SF)-\d{3}\b", text))


def saved_tool_turns(history: list) -> list[list[dict]]:
    """Keep each tool request/result in the same learner turn, including partial failures."""
    turns = []
    records = None
    for message in history:
        if message.get("role") == "human":
            records = []
            turns.append(records)
        elif records is not None and message.get("role") == "ai":
            for call in message.get("tool_calls") or []:
                records.append(
                    {
                        "name": call.get("name", "unknown"),
                        "arguments": call.get("args"),
                        "result": None,
                        "call_id": call.get("id"),
                    }
                )
        elif records is not None and message.get("role") == "tool":
            call_id = message.get("tool_call_id")
            record = next((r for r in records if call_id and r["call_id"] == call_id), None)
            pending = [r for r in records if r["result"] is None]
            # Older files lack tool_call_id. Pair only an unambiguous request.
            if record is None and len(pending) == 1:
                record = pending[0]
            if record is None:
                record = {
                    "name": message.get("name") or "unknown",
                    "arguments": None,
                    "result": None,
                    "call_id": call_id,
                }
                records.append(record)
            record["result"] = decode_content(message.get("content"))
    for records in turns:
        for record in records:
            record.pop("call_id", None)
    return turns


def build_trace(folder: Path, run: dict, episode_id: str) -> dict:
    notices = []

    def load(path, default):
        try:
            return json.loads(path.read_text())
        except FileNotFoundError:
            return default
        except (ValueError, OSError):
            notices.append(f"Could not read saved {path.name}.")
            return default

    events = [event for event in run.get("events", []) if event.get("episode_id") == episode_id]
    started = next((e for e in events if e["type"] == "episode_started"), None)
    if started is None:
        raise ValueError("Episode does not belong to this run")
    completed = next((e for e in events if e["type"] == "episode_completed"), {})
    rows = load(folder / "resolved-inputs.json", [])
    index = started.get("persona_index", 0)
    row = rows[index] if isinstance(index, int) and 0 <= index < len(rows) else {}
    persona = decode_content(row.get("persona", {}))
    profile = {k: persona[k] for k in PROFILE_FIELDS if k in persona} if isinstance(persona, dict) else {}
    if run["spec"]["mode"] == "live" and not profile:
        notices.append("The source profile was not retained for this episode.")
    history = load(folder / episode_id / "target-history.json", [])
    tool_turns = saved_tool_turns(history)
    snapshot_path = folder / "catalogue-snapshot.json"
    courses = {}
    snapshot = {"available": snapshot_path.exists(), "sha256": None, "integrity_matches": None}
    if snapshot_path.exists():
        snapshot["sha256"] = hashlib.sha256(snapshot_path.read_bytes()).hexdigest()
        expected = run.get("catalogue_sha256")
        snapshot["integrity_matches"] = snapshot["sha256"] == expected if expected else None
        try:
            courses = {c.id: c.model_dump(mode="json") for c in all_courses(snapshot_path)}
        except (ValueError, OSError):
            notices.append("The frozen catalogue could not be read.")
    else:
        notices.append("This older run has no frozen catalogue. Current listings are not substituted.")
    if snapshot["integrity_matches"] is False:
        notices.append("The saved catalogue hash differs from the run manifest.")
    turns = []
    for event in events:
        if event["type"] != "message":
            continue
        if event.get("role") == "user":
            number = len(turns) + 1
            tools = tool_turns[number - 1] if number <= len(tool_turns) else []
            turns.append(
                {
                    "number": number,
                    "user": event.get("content", ""),
                    "assistant": None,
                    "tools": tools,
                    "course_references": [],
                }
            )
        elif event.get("role") == "assistant" and turns:
            turn = turns[-1]
            turn["assistant"] = event.get("content", "")
            if not turn["tools"]:
                turn["tools"] = [
                    {
                        "name": t.get("name", "unknown"),
                        "arguments": None,
                        "result": decode_content(t.get("content")),
                    }
                    for t in event.get("tools", [])
                ]
    for turn in turns:
        observed = course_ids(json.dumps([t["result"] for t in turn["tools"]], ensure_ascii=False))
        turn["course_references"] = [
            {"id": course_id, "course": courses.get(course_id), "seen_in_tool_result": course_id in observed}
            for course_id in sorted(course_ids(turn["assistant"] or ""))
        ]
    if turns and not any(t["tools"] for t in turns):
        notices.append(
            "No structured tool records were saved for this episode. A final answer cannot establish which tools ran."
        )
    return {
        "version": 1,
        "run_id": run["run_id"],
        "episode_id": episode_id,
        "mode": run["spec"]["mode"],
        "status": completed.get("status", run["status"]),
        "error": completed.get("error"),
        "source_notice": run["source_notice"],
        "source": {
            "distribution": row.get("source_distribution", started.get("source")),
            "dataset": row.get("source_dataset"),
            "revision": row.get("source_revision"),
        },
        "profile": profile,
        "scenario": {
            "theme": row.get("theme"),
            "strategy": started.get("strategy"),
            "overlay": row.get("learning_overlay"),
            "probe": row.get("probe_type"),
        },
        "snapshot": snapshot,
        "turns": turns,
        "notices": notices,
    }
