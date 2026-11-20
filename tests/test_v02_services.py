"""Behavioural acceptance across the v0.2 shared application boundaries."""

import json

import httpx
import pytest

from learning_lab.inference import Budget, Gateway
from learning_lab.service import LabService, RunSpec


async def test_saved_platform_job_inspection_needs_no_current_remote_connection(tmp_path, monkeypatch):
    monkeypatch.delenv("LAB_HELIX_REMOTE_URL", raising=False)
    monkeypatch.setattr("learning_lab.settings.load_environment", lambda: None)
    service = LabService(tmp_path)
    identity = "04a2bf97-b124-4edb-b384-2e9ef0759704"
    folder = tmp_path / "platform-jobs" / identity
    folder.mkdir(parents=True)
    state = {"job_id": identity, "target": "remote", "operation": "invoke", "status": "failed",
             "calls": 0, "error": "Saved historical transport failure"}
    (folder / "job.json").write_text(json.dumps(state))
    try:
        assert await service.platform_action({"operation": "job", "target": "remote", "job_id": identity}) == state
        assert not service.tasks and service.deployment_bridge is None and not service.managed_sessions
    finally:
        await service.close()


async def test_failed_session_recovery_requires_native_proof_and_reuses_pinned_receipt(tmp_path, monkeypatch):
    from learning_lab.deployment import OPERATIONS, PlatformBridge, PlatformSpec

    monkeypatch.setattr(PlatformSpec, "configured", classmethod(lambda cls, target="local": cls(target=target)))
    monkeypatch.setattr("learning_lab.deployment.OPERATIONS", OPERATIONS | {"sessions_recover"})
    service = LabService(tmp_path)
    service.managed_guard = {"scope": ["local", "http://127.0.0.1:8080", "persona-lab"],
                             "session_name": "failed-session", "deployment": "failed-demo",
                             "harness": "hermes", "invocation_state": "uncertain"}
    service.managed_guard_path.write_text(json.dumps(service.managed_guard))
    seen = []

    async def call(self, operation, **arguments):
        assert operation == "sessions_recover"
        seen.append(arguments)
        assert arguments["name"] == "failed-session"
        assert Path(arguments["receipt_path"]).is_relative_to(tmp_path / "platform-jobs")
        return {"session": {"name": "failed-session", "status": "closed"},
                "runtime_cleanup_confirmed": len(seen) > 1,
                "deployment_removed": len(seen) > 2}

    from pathlib import Path
    monkeypatch.setattr(PlatformBridge, "call", call)
    try:
        with pytest.raises(ValueError, match="Recover only the retained failed session"):
            await service.platform_action({"operation": "sessions_recover", "arguments": {"name": "other"}})
        states = []
        for attempt in range(3):
            job = await service.platform_action({"operation": "sessions_recover", "arguments": {
                "name": "failed-session", "receipt_path": "/untrusted/caller/path"}})
            await service.tasks[job["job_id"]]
            states.append(service.get_platform_job(job["job_id"]))
            if attempt < 2:
                assert service.managed_guard and service.managed_guard_path.is_file()
        assert [state["status"] for state in states] == ["failed", "failed", "completed"]
        assert len({item["receipt_path"] for item in seen}) == 1
        assert not service.managed_guard and not service.managed_guard_path.exists()
        assert not service.managed_sessions and service.deployment_bridge is None
    finally:
        await service.close()


async def test_failed_close_after_valid_reply_requires_strict_cleanup_on_retry(tmp_path, monkeypatch):
    from learning_lab.deployment import PlatformBridge, PlatformSpec

    monkeypatch.setattr(PlatformSpec, "configured", classmethod(lambda cls, target="local": cls(target=target)))
    service = LabService(tmp_path)
    service.managed_guard = {"scope": ["local", "http://127.0.0.1:8080", "persona-lab"],
                             "session_name": "finished-session", "deployment": "demo",
                             "invocation_state": "idle"}
    seen = []

    async def call(self, operation, **arguments):
        seen.append(arguments["require_runtime_drain"])
        return {"session": {"name": "finished-session", "status": "active"}, "runtime_cleanup_confirmed": False}

    monkeypatch.setattr(PlatformBridge, "call", call)
    try:
        for _ in range(2):
            job = await service.platform_action({"operation": "sessions_close", "arguments": {"name": "finished-session"}})
            await service.tasks[job["job_id"]]
            assert service.get_platform_job(job["job_id"])["status"] == "failed"
            assert service.managed_guard["invocation_state"] == "uncertain"
        assert seen == [False, True]
    finally:
        await service.close()


@pytest.mark.parametrize(
    "allowed,role,expected",
    [
        ({"search_courses"}, "assistant", ["search_courses"]),
        (set(), "assistant", []),
        ({"search_courses"}, "user", ["read_file", "search_courses"]),
    ],
)
async def test_gateway_model_schema_boundary_is_explicit_and_assistant_only(
    monkeypatch, allowed, role, expected
):
    received = []

    async def provider(request):
        payload = json.loads(request.content)
        received.append(payload)
        return httpx.Response(
            200,
            json={
                "model": "local-provider-fixture",
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "Fixture output unchanged"},
                        "finish_reason": "stop",
                    }
                ],
            },
        )

    monkeypatch.setattr("learning_lab.inference.load_environment", lambda: None)
    monkeypatch.delenv("LAB_PROXY_BASE_URL", raising=False)
    monkeypatch.setenv("NVIDIA_API_KEY", "local-mocked-provider-key")
    gateway = Gateway(Budget(2), "live", allowed_tool_names=allowed)
    await gateway._client.aclose()
    gateway._client = httpx.AsyncClient(transport=httpx.MockTransport(provider))
    tools = [{"type": "function", "function": {"name": name}} for name in ["read_file", "search_courses"]]
    try:
        response = await gateway.complete(
            {"model": "local-provider-fixture", "messages": [{"role": "user", "content": "Fixture"}], "tools": tools}, role=role
        )
    finally:
        await gateway._client.aclose()
    assert response["choices"][0]["message"]["content"] == "Fixture output unchanged"
    assert [tool["function"]["name"] for tool in received[0].get("tools", [])] == expected
    assert len(tools) == 2  # Original native request is not rewritten in place.
    assert gateway.budget.calls == 1
    if role == "assistant":
        assert gateway.budget.records[0]["tool_surface"]["exposed"] == expected
    else:
        assert "tool_surface" not in gateway.budget.records[0]


async def test_hermes_sse_projection_keeps_one_bounded_upstream_attempt():
    async with Gateway(Budget(1), "demo").serving() as gateway:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                gateway.url + "/chat/completions",
                headers={"Authorization": "Bearer " + gateway.key},
                json={
                    "model": "offline-scripted",
                    "stream": True,
                    "messages": [{"role": "user", "content": "photography"}],
                    "tools": [{"type": "function", "function": {"name": "search_courses"}}],
                },
            )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        events = [
            line.removeprefix("data: ") for line in response.text.splitlines() if line.startswith("data:")
        ]
        assert events[-1] == "[DONE]"
        assert json.loads(events[0])["choices"][0]["delta"]["tool_calls"][0]["index"] == 0
        assert json.loads(events[1])["choices"][0]["finish_reason"] == "tool_calls"
        assert gateway.budget.calls == 1


async def test_one_offline_boardgame_story_keeps_real_empty_search_and_evaluation(tmp_path):
    service = LabService(tmp_path)
    try:
        state = await service.start_run(RunSpec(story_id="boardgames", engine="fabric"))
        await service.tasks[state["run_id"]]
        saved = service.get_run(state["run_id"])
        assert saved["status"] == "completed"
        assert saved["story"]["id"] == "boardgames"
        assert len(saved["episodes"]) == 1 and saved["calls"] == 2
        evidence = service.get_evidence(saved["run_id"])
        assert {scope["category"] for scope in evidence["relay"]["scopes"]} >= {"agent", "llm", "tool"}
        count = saved["calls"]
        from learning_lab.evaluation import evaluate_saved_run

        detailed = evaluate_saved_run(saved, tmp_path / saved["run_id"])
        assert any(
            row["criterion"] == "no_match_handling" and row["status"] == "pass" for row in detailed["rows"]
        )
        assert service.get_run(saved["run_id"])["calls"] == count
    finally:
        await service.close()


async def test_explicit_budget_comparison_reuses_the_frozen_catalogue(tmp_path):
    service = LabService(tmp_path)
    try:
        parent = await service.start_run(RunSpec(story_id="baking"))
        await service.tasks[parent["run_id"]]
        child = await service.start_run(
            RunSpec(
                story_id="baking",
                parent_run_id=parent["run_id"],
                budget_override_sgd=130,
                comparison_reason="Change only the total budget",
            )
        )
        await service.tasks[child["run_id"]]
        saved_parent = service.get_run(parent["run_id"])
        saved_child = service.get_run(child["run_id"])
        assert saved_parent["catalogue_sha256"] == saved_child["catalogue_sha256"]
        assert saved_child["status"] == "completed"
        started = next(e for e in saved_child["events"] if e["type"] == "episode_started")
        assert started["preferences"]["budget_sgd"] == 130
        assert saved_child["spec"]["parent_run_id"] == parent["run_id"]
    finally:
        await service.close()


async def test_comparison_rejects_changed_story_and_modified_catalogue_before_inference(tmp_path):
    service = LabService(tmp_path)
    try:
        parent = await service.start_run(RunSpec(story_id="baking"))
        await service.tasks[parent["run_id"]]
        changed = await service.start_run(
            RunSpec(
                story_id="photography",
                parent_run_id=parent["run_id"],
                comparison_reason="Attempt to change two inputs",
            )
        )
        await service.tasks[changed["run_id"]]
        failed = service.get_run(changed["run_id"])
        assert failed["status"] == "failed" and failed["calls"] == 0
        assert "retain the parent's story_id" in failed["error"]
        snapshot = tmp_path / parent["run_id"] / "catalogue-snapshot.json"
        snapshot.write_text(snapshot.read_text() + "\n")
        changed = await service.start_run(
            RunSpec(
                story_id="baking",
                parent_run_id=parent["run_id"],
                budget_override_sgd=130,
                comparison_reason="Change budget only",
            )
        )
        await service.tasks[changed["run_id"]]
        failed = service.get_run(changed["run_id"])
        assert failed["status"] == "failed" and failed["calls"] == 0 and "hash check" in failed["error"]
    finally:
        await service.close()


async def test_parent_resolved_profiles_keep_identity_and_fresh_runtime_trajectory(tmp_path, monkeypatch):
    import uuid
    from learning_lab.catalogue import freeze_catalogue
    from learning_lab.service import atomic_json

    parent_id = str(uuid.uuid4())
    parent_folder = tmp_path / parent_id
    parent_spec = RunSpec(mode="live", story_id="photography", seed=7)
    trajectory = str(uuid.uuid4())
    profile = {"uuid": "frozen-fixture-profile", "age": 42}
    original = {"persona": profile, "trajectory_id": trajectory, "theme": {"description": "Fixture topic"}}
    digest = freeze_catalogue(parent_folder / "catalogue-snapshot.json")
    atomic_json(parent_folder / "resolved-inputs.json", [original])
    atomic_json(
        parent_folder / "run.json",
        {
            "run_id": parent_id,
            "spec": parent_spec.model_dump(),
            "status": "completed",
            "episodes": [],
            "catalogue_sha256": digest,
        },
    )
    observed = []

    async def inspect_inputs(spec, folder, gateway, save_event, **kwargs):
        observed.extend(kwargs["resolved_rows"])

    monkeypatch.setattr("learning_lab.service.inference_configured", lambda: True)
    monkeypatch.setattr("learning_lab.service.run_experiment", inspect_inputs)
    service = LabService(tmp_path)
    try:
        child = await service.start_run(
            RunSpec(
                **{
                    **parent_spec.model_dump(),
                    "parent_run_id": parent_id,
                    "comparison_reason": "Compare the harness",
                    "engine": "fabric",
                }
            )
        )
        await service.tasks[child["run_id"]]
        assert service.get_run(child["run_id"])["status"] == "completed"
        assert observed[0]["persona"] == profile and observed[0]["trajectory_id"] != trajectory
        assert observed[0]["pair_input_id"] == trajectory
        assert json.loads((parent_folder / "resolved-inputs.json").read_text()) == [original]
    finally:
        await service.close()


def test_run_spec_rejects_unbound_harness_and_generated_source():
    with pytest.raises(ValueError, match="Hermes"):
        RunSpec(harness="hermes", engine="direct")
    with pytest.raises(ValueError, match="saved Data Designer"):
        RunSpec(source="generated")
    with pytest.raises(ValueError, match="same number"):
        RunSpec(source_ids=["one", "two"], personas=1)


async def test_platform_failure_remains_a_failed_saved_job(tmp_path, monkeypatch):
    from learning_lab.deployment import PlatformBridge

    async def unavailable(*args, **kwargs):
        raise RuntimeError("Platform prerequisite missing")

    monkeypatch.setattr(PlatformBridge, "call", unavailable)
    service = LabService(tmp_path)
    try:
        job = await service.platform_action({"operation": "register", "arguments": {"harness": "deepagents"}})
        await service.tasks[job["job_id"]]
        saved = service.get_platform_job(job["job_id"])
        assert saved["status"] == "failed"
        assert "prerequisite missing" in saved["error"]
        assert saved["calls"] == 0
    finally:
        await service.close()


async def test_cancellation_before_job_start_is_terminal_without_sdk_or_model_call(tmp_path):
    service = LabService(tmp_path)
    try:
        workbench = await service.start_workbench({"operation": "scenarios", "count": 1})
        cancelled = await service.cancel_workbench(workbench["job_id"])
        assert cancelled["status"] == "cancelled" and cancelled["calls"] == 0
        platform = await service.platform_action({"operation": "register", "arguments": {"harness": "deepagents"}})
        cancelled = await service.platform_action({"operation": "cancel_job", "job_id": platform["job_id"]})
        assert cancelled["status"] == "cancelled" and cancelled["calls"] == 0
        assert not list(tmp_path.glob("workbench/*/designer-request.json"))
    finally:
        await service.close()


async def test_uncertain_managed_session_survives_restart_until_runtime_cleanup_is_confirmed(tmp_path, monkeypatch):
    from learning_lab.deployment import PlatformBridge

    guard = {"scope": ["local", "http://127.0.0.1:8080", "persona-lab"],
             "session_name": "old-session", "deployment": "demo", "invocation_state": "running"}
    (tmp_path / "platform-session.json").write_text(json.dumps(guard))
    confirmed = False

    async def close(self, operation, **arguments):
        assert operation == "sessions_close" and arguments["require_runtime_drain"] is True
        return {"session": {"name": "old-session", "status": "closed"},
                "runtime_cleanup_confirmed": confirmed}

    monkeypatch.setattr(PlatformBridge, "call", close)
    service = LabService(tmp_path)
    try:
        with pytest.raises(ValueError, match="Close the current managed session"):
            await service.platform_action({"operation": "sessions_create", "arguments": {"deployment": "new"}})
        async def cleanup():
            job = await service.platform_action({"operation": "sessions_close", "arguments": {"name": "old-session"}})
            await service.tasks[job["job_id"]]
            return service.get_platform_job(job["job_id"])
        assert (await cleanup())["status"] == "failed"
        assert service.managed_guard and service.managed_guard_path.exists()
        confirmed = True
        assert (await cleanup())["status"] == "completed"
        assert service.managed_guard is None and not service.managed_guard_path.exists()
    finally:
        await service.close()


async def test_managed_conversation_freezes_constraints_and_preserves_failed_usage(tmp_path, monkeypatch):
    from contextlib import asynccontextmanager
    from learning_lab.deployment import PlatformBridge

    attempts = 0

    async def call(self, operation, **arguments):
        nonlocal attempts
        if operation == "sessions_create":
            return {"session": {"name": "test-session", "status": "active"},
                    "deployment": {"harness_kind": "deepagents"}}
        if operation == "sessions_close":
            assert arguments.get("require_runtime_drain") is True
            return {"session": {"name": "test-session", "status": "closed"},
                    "runtime_cleanup_confirmed": True}
        if operation == "invoke":
            attempts += 1
            budget = next(iter(service.managed_sessions.values()))["budget"]
            await budget.admit("assistant", "test")
            if attempts == 2:
                raise TimeoutError("Upstream did not finish")
            return {"response": "No catalogue match", "session_id": arguments["session_id"]}

    class LocalGateway:
        def __init__(self, budget, *args, **kwargs):
            self.budget = budget

        @asynccontextmanager
        async def serving(self):
            yield self

    class LocalBridge:
        async def activate(self, run_id, gateway, preferences):
            assert preferences["budget_sgd"] == 50

        async def deactivate(self, run_id):
            pass

    async def local_bridge():
        service.deployment_bridge = LocalBridge()
        return service.deployment_bridge

    monkeypatch.setattr(PlatformBridge, "call", call)
    monkeypatch.setattr("learning_lab.service.Gateway", LocalGateway)
    service = LabService(tmp_path)
    monkeypatch.setattr(service, "_deployment_gateway", local_bridge)

    async def action(operation, **arguments):
        job = await service.platform_action({"operation": operation, "arguments": arguments})
        await service.tasks[job["job_id"]]
        return service.get_platform_job(job["job_id"])

    try:
        assert (await action("sessions_create", deployment="demo"))["status"] == "completed"
        with pytest.raises(ValueError, match="Close the current managed session"):
            await action("sessions_create", deployment="other-demo")
        with pytest.raises(ValueError, match="Close the managed session before undeploying"):
            await action("undeploy", name="demo")
        args = {
            "deployment": "demo",
            "session_id": "test-session",
            "input": "Find photography",
            "preferences": {"goal": "photography", "budget_sgd": 50},
        }
        assert (await action("invoke", **args))["calls"] == 1
        changed = {**args, "preferences": {"goal": "photography", "budget_sgd": 100}}
        assert "new session" in (await action("invoke", **changed))["error"]
        failed = await action("invoke", **args)
        assert failed["status"] == "failed" and failed["calls"] == 2
        assert len(failed["usage"]) == 2
        assert "incomplete invocation" in (await action("invoke", **args))["error"]
        assert attempts == 2
        assert (await action("sessions_close", name="test-session"))["status"] == "completed"
        assert not service.managed_sessions
    finally:
        await service.close()
