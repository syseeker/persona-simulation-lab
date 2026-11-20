import json
import os
import uuid

import pytest

from learning_lab.catalogue import freeze_catalogue
from learning_lab.provenance import saved_tool_turns
from learning_lab.service import LabService, atomic_json


def trace_fixture(root, *, failed=False):
    run_id, episode_id = str(uuid.uuid4()), str(uuid.uuid4())
    folder = root / run_id
    snapshot = folder / "catalogue-snapshot.json"
    freeze_catalogue(snapshot)
    catalogue = json.loads(snapshot.read_text())
    course = next(c for c in catalogue["courses"] if c["id"] == "SF-005")
    course["title"] = "A saved course title distinct from the current catalogue"
    snapshot.write_text(json.dumps(catalogue))
    digest = freeze_catalogue(snapshot)
    state = {
        "run_id": run_id,
        "status": "completed_with_failures" if failed else "completed",
        "spec": {"mode": "live", "engine": "direct"},
        "source_notice": "Synthetic fixture profile",
        "catalogue_sha256": digest,
        "episodes": [],
    }
    atomic_json(folder / "run.json", state)
    atomic_json(
        folder / "resolved-inputs.json",
        [
            {
                "persona": {
                    "age": 30,
                    "occupation": "Fabricated role",
                    "career_goals_and_ambitions": "Learn project coordination",
                },
                "source_distribution": "hf-profile-only",
                "source_revision": "fixture-revision",
                "theme": {"description": "Explore professional learning"},
            }
        ],
    )
    events = [
        {
            "type": "episode_started",
            "episode_id": episode_id,
            "persona_index": 0,
            "strategy": "concise",
            "source": "hf-profile-only",
        },
        {"type": "message", "episode_id": episode_id, "role": "user", "content": "Find a course"},
    ]
    if not failed:
        events += [
            {"type": "message", "episode_id": episode_id, "role": "assistant", "content": "Try SF\u2011005"},
            {"type": "message", "episode_id": episode_id, "role": "user", "content": "Now photography"},
            {"type": "message", "episode_id": episode_id, "role": "assistant", "content": "CC-001 or CC-999"},
        ]
        history = [
            {"role": "human"},
            {
                "role": "ai",
                "tool_calls": [{"id": "a", "name": "get_course_details", "args": {"course_id": "SF-005"}}],
            },
            {"role": "tool", "content": [{"type": "text", "text": json.dumps(course)}]},
            {"role": "ai"},
            {"role": "human"},
            {
                "role": "ai",
                "tool_calls": [{"id": "b", "name": "search_courses", "args": {"goal": "photography"}}],
            },
            {"role": "tool", "content": json.dumps({"matches": [{"course": {"id": "CC-001"}}]})},
        ]
        atomic_json(folder / episode_id / "target-history.json", history)
    events.append(
        {
            "type": "episode_completed",
            "episode_id": episode_id,
            "status": "failed" if failed else "completed",
            "error": "tool limit reached" if failed else None,
        }
    )
    (folder / "events.jsonl").write_text("\n".join(json.dumps(e) for e in events))
    return LabService(root), run_id, episode_id


def test_trace_preserves_source_and_uses_frozen_facts_per_turn(tmp_path):
    service, run_id, episode_id = trace_fixture(tmp_path)
    trace = service.get_trace(run_id, episode_id)
    assert trace["profile"]["career_goals_and_ambitions"] == "Learn project coordination"
    assert trace["scenario"]["theme"]["description"] == "Explore professional learning"
    first, second = trace["turns"]
    assert first["tools"][0]["arguments"] == {"course_id": "SF-005"}
    assert first["course_references"][0]["course"]["title"].startswith("A saved course title")
    assert first["course_references"][0]["seen_in_tool_result"] is True
    assert second["tools"][0]["arguments"] == {"goal": "photography"}
    assert [c["id"] for c in second["course_references"]] == ["CC-001", "CC-999"]
    assert second["course_references"][1]["course"] is None
    assert trace["snapshot"]["integrity_matches"] is True


def test_failed_trace_does_not_invent_an_answer_or_tool_result(tmp_path):
    service, run_id, episode_id = trace_fixture(tmp_path, failed=True)
    trace = service.get_trace(run_id, episode_id)
    assert trace["status"] == "failed" and trace["error"] == "tool limit reached"
    assert trace["turns"][0]["assistant"] is None
    assert trace["turns"][0]["tools"] == []
    assert any("No structured tool records" in n for n in trace["notices"])


def test_missing_snapshot_never_substitutes_current_course_facts(tmp_path):
    service, run_id, episode_id = trace_fixture(tmp_path)
    (tmp_path / run_id / "catalogue-snapshot.json").unlink()
    trace = service.get_trace(run_id, episode_id)
    assert trace["snapshot"]["available"] is False
    assert trace["turns"][0]["course_references"][0]["course"] is None


def test_trace_requires_an_episode_in_the_selected_run(tmp_path):
    service, run_id, _ = trace_fixture(tmp_path)
    with pytest.raises(ValueError, match="Invalid episode ID"):
        service.get_trace(run_id, "../../.env")
    with pytest.raises(ValueError, match="does not belong"):
        service.get_trace(run_id, str(uuid.uuid4()))


def test_old_parallel_tool_results_are_not_associated_by_guessing():
    turns = saved_tool_turns(
        [
            {"role": "human"},
            {
                "role": "ai",
                "tool_calls": [
                    {"id": "a", "name": "first", "args": {"x": 1}},
                    {"id": "b", "name": "second", "args": {"x": 2}},
                ],
            },
            {"role": "tool", "content": "a result lacking an ID"},
        ]
    )
    assert turns[0][0]["result"] is None and turns[0][1]["result"] is None
    assert turns[0][2]["name"] == "unknown" and turns[0][2]["arguments"] is None


def test_history_filter_applies_before_the_thirty_run_limit(tmp_path):
    live_id = str(uuid.uuid4())
    atomic_json(
        tmp_path / live_id / "run.json", {"run_id": live_id, "status": "completed", "spec": {"mode": "live"}}
    )
    os.utime(tmp_path / live_id / "run.json", (1, 1))
    for _ in range(31):
        demo_id = str(uuid.uuid4())
        atomic_json(
            tmp_path / demo_id / "run.json",
            {"run_id": demo_id, "status": "completed", "spec": {"mode": "demo"}},
        )
    service = LabService(tmp_path)
    assert [r["run_id"] for r in service.list_runs("live")] == [live_id]
    assert len(service.list_runs("demo")) == 30
    with pytest.raises(ValueError):
        service.list_runs("arbitrary")
