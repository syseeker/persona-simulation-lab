import json
from types import SimpleNamespace
import uuid

import pytest

from learning_lab.catalogue import Preferences, all_courses, freeze_catalogue
from learning_lab.evaluation import evaluate_saved_run, score_response
from learning_lab.evidence import (
    build_evidence,
    decode_native,
    list_artifacts,
    native_tool_records,
    read_artifact,
    sanitize,
)
from learning_lab.fabric_target import FabricTarget
from learning_lab.inference import Budget, Gateway
from learning_lab.outcomes import InvalidAnswer, answer_outcome, require_valid_answer
from learning_lab.target import DirectTarget


@pytest.mark.parametrize(
    "content,code",
    [
        ("", "empty_answer"),
        (None, "empty_answer"),
        ({"unexpected": "output"}, "empty_answer"),
        ("[ERROR: Max turns (10) exceeded]", "model_error_text"),
        ("<tool_call>\n<function=search_courses>game design</function>\n</tool_call>", "unparsed_tool_call"),
        ('{"tool_calls":[{"name":"search_courses","arguments":{}}]}', "unparsed_tool_call"),
    ],
)
def test_invalid_final_content_never_passes_legacy_checks(content, code):
    assert answer_outcome(content)["code"] == code
    with pytest.raises(InvalidAnswer):
        require_valid_answer(content)
    assert not any(score_response(content, Preferences(goal="boardgame")).values())


def test_public_text_blocks_and_no_match_are_valid_answers():
    assert require_valid_answer(
        [{"type": "text", "text": "No matching class is in this catalogue."}]
    ).startswith("No matching")
    assert (
        answer_outcome("The previous run displayed an error; here is the sourced reply.")["status"] == "valid"
    )


@pytest.mark.parametrize("kind", ["direct", "fabric"])
async def test_provider_error_text_is_rejected_after_local_evidence_is_saved(tmp_path, kind):
    text = "[ERROR: Max turns (10) exceeded]"
    async with Gateway(Budget(), "demo").serving() as gateway:
        if kind == "direct":
            target = DirectTarget(gateway, tmp_path / "workspace", "offline-scripted")
            target.workspace.mkdir()
            output = SimpleNamespace(type="ai", content=text, name="advisor", tool_calls=[])

            class Graph:
                async def aget_state(self, config):
                    return SimpleNamespace(values={"messages": []})

                async def ainvoke(self, request, config):
                    return {"messages": [output]}

            target.agent = Graph()
        else:
            target = FabricTarget(gateway, tmp_path / "workspace", "offline-scripted")
            target.workspace.mkdir()

            class Runtime:
                async def invoke(self, request):
                    return SimpleNamespace(
                        status="succeeded",
                        runtime_id="real-fixture-runtime",
                        invocation_id="fixture-invocation",
                        artifacts=[],
                        output=SimpleNamespace(to_dict=lambda: {"response": text}),
                    )

            target.runtime = Runtime()
        with pytest.raises(InvalidAnswer, match="model returned error text"):
            await target.reply("Find a class", Preferences(goal="Find a class"))
    saved = json.loads((tmp_path / "reply-outcomes.jsonl").read_text().splitlines()[0])
    assert saved["content"] == text and saved["runtime_status"] == "succeeded"
    assert saved["outcome"]["code"] == "model_error_text"


def relay_event(uid, phase, category="tool", **kwargs):
    return {
        "uuid": uid,
        "scope_category": phase,
        "category": category,
        "name": "search_courses",
        "timestamp": "2026-11-17T00:00:00Z",
        **kwargs,
    }


def test_artifacts_redact_credentials_reject_paths_and_keep_native_scope_evidence(tmp_path):
    episode = tmp_path / str(uuid.uuid4())
    runtime = episode / "fabric-traces" / "runtime-fixture"
    runtime.mkdir(parents=True)
    uid, parent = str(uuid.uuid4()), str(uuid.uuid4())
    events = [
        relay_event(parent, "start", "agent", name="advisor"),
        relay_event(
            uid,
            "start",
            parent_uuid=parent,
            data={"goal": "boardgame", "headers": {"Authorization": "Bearer hidden"}},
        ),
        relay_event(uid, "end", parent_uuid=parent, data={"result": {"matches": []}, "is_error": False}),
        relay_event(parent, "end", "agent", name="advisor"),
    ]
    (runtime / "relay.jsonl").write_text("\n".join(json.dumps(item) for item in events) + "\n{partial")
    (tmp_path / ".env").write_text("DO_NOT_READ=private-value")
    (tmp_path / "run.json").write_text(
        json.dumps({"nested": {"api_key": "hidden-key"}, "safe": "Bearer token-value"})
    )
    outside = tmp_path.parent / (str(uuid.uuid4()) + ".json")
    outside.write_text('{"secret":"must not be read"}')
    (tmp_path / "target-history.json").symlink_to(outside)
    try:
        artifacts = list_artifacts(tmp_path)
        assert {item["kind"] for item in artifacts} == {"manifest", "relay"}
        assert not any(item["name"] == ".env" for item in artifacts)
        with pytest.raises(ValueError, match="Unknown"):
            read_artifact(tmp_path, "../../.env")
        manifest = read_artifact(
            tmp_path, next(item["id"] for item in artifacts if item["kind"] == "manifest")
        )
        assert "hidden-key" not in json.dumps(manifest) and "token-value" not in json.dumps(manifest)
        evidence = build_evidence(tmp_path)
        scopes = evidence["relay"]["scopes"]
        child = next(item for item in scopes if item["uuid"] == uid)
        assert child["parent_available"] is True and child["status"] == "completed"
        assert child["input"]["headers"] == "[redacted]"
        assert evidence["relay"]["notices"]
        tools = native_tool_records(tmp_path)
        assert tools[0]["arguments"]["goal"] == "boardgame" and tools[0]["result"] == {"matches": []}
        assert native_tool_records(tmp_path, exclude_uuids=[uid]) == []
    finally:
        outside.unlink()


def evaluation_fixture(tmp_path, content, *, preferences=None, tools=None):
    episode = str(uuid.uuid4())
    freeze_catalogue(tmp_path / "catalogue-snapshot.json")
    return {
        "started_at": "2026-11-17T00:00:00Z",
        "episodes": [{"episode_id": episode, "strategy": "concise", "status": "completed"}],
        "events": [
            {"type": "message", "role": "user", "episode_id": episode, "content": "boardgame"},
            {
                "type": "message",
                "role": "assistant",
                "episode_id": episode,
                "content": content,
                "preferences": preferences,
                "tools": tools or [],
            },
        ],
    }


def test_evaluation_does_not_reward_error_only_or_missing_answers(tmp_path):
    run = evaluation_fixture(tmp_path, "[ERROR: Max turns (10) exceeded]")
    result = evaluate_saved_run(run, tmp_path)
    assert result["summary"]["concise"] == {
        "criteria": 1,
        "passed": 0,
        "failed": 1,
        "errors": 0,
        "not_applicable": 6,
    }
    assert result["helix_rows"][0]["output"] == "false"
    run["events"].pop()
    missing = evaluate_saved_run(run, tmp_path)
    assert missing["rows"][0]["status"] == "error" and missing["summary"]["concise"]["passed"] == 0


def test_evaluation_uses_saved_budget_and_per_course_official_links(tmp_path):
    course = next(course for course in all_courses() if course.id == "CC-001")
    run = evaluation_fixture(
        tmp_path, f"Try CC-001 at {course.source_url}", preferences={"goal": "photography", "budget_sgd": 1}
    )
    result = evaluate_saved_run(run, tmp_path)
    rows = {row["criterion"]: row for row in result["rows"]}
    assert rows["constraint_compliance"]["status"] == "fail"
    assert rows["constraint_compliance"]["evidence"]["preferences"]["budget_sgd"] == 1
    assert rows["source_citation"]["status"] == "pass"
    run["events"][-1]["content"] = "Try CC-001 at https://example.invalid/fake"
    assert (
        next(
            row for row in evaluate_saved_run(run, tmp_path)["rows"] if row["criterion"] == "source_citation"
        )["status"]
        == "fail"
    )


def test_evaluation_no_match_and_missing_evidence_are_explicit(tmp_path):
    run = evaluation_fixture(
        tmp_path,
        "No boardgame class is listed in this small catalogue.",
        tools=[{"name": "search_courses", "content": json.dumps({"matches": []})}],
    )
    result = evaluate_saved_run(run, tmp_path)
    rows = {row["criterion"]: row for row in result["rows"]}
    assert rows["no_match_handling"]["status"] == "pass"
    assert rows["constraint_compliance"]["status"] == "not_applicable"
    (tmp_path / "catalogue-snapshot.json").unlink()
    missing = {row["criterion"]: row for row in evaluate_saved_run(run, tmp_path)["rows"]}
    assert missing["catalogue_grounding"]["status"] == "error"


def test_failed_search_is_not_evidence_for_successful_no_match(tmp_path):
    run = evaluation_fixture(
        tmp_path,
        "No boardgame class is listed in this catalogue.",
        tools=[{"name": "search_courses", "result": {"error": "Invalid trusted constraints", "matches": []}}],
    )
    result = evaluate_saved_run(run, tmp_path)
    row = next(row for row in result["rows"] if row["criterion"] == "no_match_handling")
    assert row["status"] == "error" and row["output"] == "false"


def test_native_relay_typed_tool_result_drives_no_match_evaluation_without_rewriting_raw(tmp_path):
    facts = {"matches": [], "message": "No courses match the stated preferences."}
    typed = {
        "kind": "model",
        "type": "langchain_core.messages.tool.ToolMessage",
        "value": {
            "content": {
                "kind": "list",
                "value": [
                    {
                        "kind": "dict",
                        "value": {
                            "text": {"kind": "json", "value": json.dumps(facts)},
                            "type": {"kind": "json", "value": "text"},
                        },
                    }
                ],
            },
            "tool_call_id": {"kind": "json", "value": "observed-call-id"},
        },
    }
    assert decode_native(typed) == facts
    uid = str(uuid.uuid4())
    raw = "\n".join(
        json.dumps(item)
        for item in [
            relay_event(uid, "start", data={"goal": "boardgame"}),
            relay_event(uid, "end", data={"result": typed}),
        ]
    )
    trace = tmp_path / "relay.jsonl"
    trace.write_text(raw)
    tools = native_tool_records(tmp_path)
    assert tools[0]["result"] == facts
    run = evaluation_fixture(
        tmp_path,
        "No boardgame class is listed in this small catalogue.",
        tools=[{"name": "search_courses", "result": typed}],
    )
    result = evaluate_saved_run(run, tmp_path)
    assert next(row for row in result["rows"] if row["criterion"] == "no_match_handling")["status"] == "pass"
    assert trace.read_text() == raw
    assert decode_native({"kind": "unknown", "value": "leave visible"}) == {
        "kind": "unknown",
        "value": "leave visible",
    }
    assert decode_native({"kind": {"type": "object"}, "value": "domain data"}) == {
        "kind": {"type": "object"},
        "value": "domain data",
    }


def test_json_strings_and_secret_environment_fields_are_redacted():
    value = sanitize(
        {
            "env": {"NVIDIA_API_KEY": "hidden-value"},
            "data": '{"headers":{"Authorization":"opaque"},"usage":{"total_tokens":5}}',
        }
    )
    assert "hidden-value" not in json.dumps(value) and "opaque" not in json.dumps(value)
    assert "total_tokens" in value["data"]


async def test_real_offline_fabric_saves_plan_lifecycle_and_observed_mcp_tools(tmp_path):
    async with Gateway(Budget(12), "demo").serving() as gateway:
        async with FabricTarget(gateway, tmp_path / "workspace", "offline-scripted") as target:
            first = await target.reply("photography", Preferences(goal="photography"))
            second = await target.reply("calligraphy", Preferences(goal="calligraphy"))
            assert [tool["name"] for tool in first["tools"]] == ["search_courses"]
            assert first["tools"][0]["arguments"]["goal"] == "photography"
            assert second["tools"][0]["arguments"]["goal"] == "calligraphy"
            assert first["tools"][0]["scope_uuid"] != second["tools"][0]["scope_uuid"]
            surfaces = [record["tool_surface"] for record in gateway.budget.records]
            assert all(
                set(item["exposed"]) == {"search_courses", "get_course_details", "compare_courses"}
                for item in surfaces
            )
            assert any("read_file" in item["withheld"] for item in surfaces)
        assert gateway.allowed_tool_names is None
    evidence = build_evidence(tmp_path)
    assert len(evidence["fabric"]["plan"]) == 1 and len(evidence["fabric"]["doctor"]) == 1
    events = [item["event"] for item in evidence["fabric"]["lifecycle"][0]["content"]]
    assert events[0] == "configuration_saved" and events[-1] == "runtime_closed"
