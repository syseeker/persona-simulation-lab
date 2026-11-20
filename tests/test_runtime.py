import asyncio
import json

import pytest

from learning_lab.catalogue import Preferences
from learning_lab.fabric_target import FabricTarget, build_config
from learning_lab.inference import Budget, BudgetExceeded, Gateway
from learning_lab.service import ChatSpec, LabService, RunSpec, atomic_json
from learning_lab.settings import ROOT
from learning_lab.target import DirectTarget, relay_config


async def test_budget_admission_is_atomic():
    budget = Budget(2)
    results = await asyncio.gather(
        *[budget.admit("assistant", "demo") for _ in range(8)], return_exceptions=True
    )
    assert budget.calls == 2
    assert sum(isinstance(r, BudgetExceeded) for r in results) == 6


@pytest.mark.parametrize("relay", [False, True])
async def test_real_harness_uses_real_mcp_and_retains_one_thread(tmp_path, relay):
    from contextlib import AsyncExitStack
    import nemo_relay

    async with AsyncExitStack() as stack:
        gateway = await stack.enter_async_context(Gateway(Budget(20), "demo").serving())
        if relay:
            await stack.enter_async_context(nemo_relay.plugin.activate({}, str(relay_config(tmp_path))))
        target = await stack.enter_async_context(
            DirectTarget(gateway, tmp_path / "workspace", "offline-scripted", relay=relay)
        )
        first = await target.reply("photography", Preferences(goal="photography", budget_sgd=50))
        second = await target.reply("calligraphy", Preferences(goal="calligraphy", budget_sgd=250))
        assert "CC-001" in first["content"] and "CC-003" in second["content"]
        assert first["thread_id"] == second["thread_id"]
        assert {t["name"] for t in first["tools"]} == {"search_courses"}
    if relay:
        # Test folders are outside the repo; inspect the event file directly.
        events = [json.loads(line) for line in (tmp_path / "relay.jsonl").read_text().splitlines()]
        assert {"agent", "llm", "tool"} <= {
            e.get("category") for e in events if e.get("scope_category") == "end"
        }


async def test_fabric_plan_and_stateful_invocations(tmp_path):
    from nemo_fabric import Fabric

    config = build_config(tmp_path / "workspace", "offline-scripted", "http://127.0.0.1:1/v1")
    assert Fabric().plan(config, base_dir=ROOT).adapter.adapter_id == "nvidia.fabric.langchain.deepagents"
    async with Gateway(Budget(20), "demo").serving() as gateway:
        async with FabricTarget(gateway, tmp_path / "workspace", "offline-scripted") as target:
            one = await target.reply("photography", Preferences(goal="photography"))
            two = await target.reply("calligraphy", Preferences(goal="calligraphy"))
            assert "CC-001" in one["content"] and "CC-003" in two["content"]
            assert one["fabric"]["runtime_id"] == two["fabric"]["runtime_id"]


async def test_crash_recovery_and_run_path_validation(tmp_path):
    folder = tmp_path / "00000000-0000-0000-0000-000000000000"
    atomic_json(folder / "run.json", {"run_id": folder.name, "status": "running"})
    service = LabService(tmp_path)
    assert service.get_run(folder.name)["status"] == "interrupted"
    with pytest.raises(ValueError):
        service.get_run("../../.env")
    await service.close()


async def test_sequential_chat_then_experiment_releases_resources(tmp_path):
    service = LabService(tmp_path)
    try:
        first = await service.chat(ChatSpec(preferences=Preferences(goal="photography")))
        second = await service.chat(
            ChatSpec(session_id=first["session_id"], preferences=Preferences(goal="calligraphy"))
        )
        assert first["thread_id"] == second["thread_id"]
        state = await service.start_run(RunSpec())
        with pytest.raises(ValueError):
            await service.start_run(RunSpec())
        await service.tasks[state["run_id"]]
        final = service.get_run(state["run_id"])
        assert final["status"] == "completed"
        assert final["calls"] == 2 and len(final["episodes"]) == 1
        assert "no real persona" in final["source_notice"]
    finally:
        await service.close()


async def test_chat_retains_bounded_turn_and_usage_evidence(tmp_path):
    service = LabService(tmp_path)
    try:
        reply = await service.chat(ChatSpec(preferences=Preferences(goal="photography")))
        for goal in ("calligraphy", "baking"):
            reply = await service.chat(
                ChatSpec(session_id=reply["session_id"], preferences=Preferences(goal=goal))
            )
        assert reply["calls"] == 6 and reply["turns"] == 3
        with pytest.raises(ValueError, match="three-turn"):
            await service.chat(
                ChatSpec(session_id=reply["session_id"], preferences=Preferences(goal="photography"))
            )
        folder = tmp_path / "chats" / reply["session_id"]
        state = json.loads((folder / "chat.json").read_text())
        usage = json.loads((folder / "usage.json").read_text())
        assert state["status"] == "turn_limit_reached" and len(state["turns"]) == 3
        assert len(usage) == state["calls"] == 6 and all(call["status"] == "completed" for call in usage)
    finally:
        await service.close()
    assert json.loads((folder / "chat.json").read_text())["closed_at"]


@pytest.mark.parametrize("failure", ["timeout", "cancel"])
async def test_failed_chat_closes_memory_and_retains_unknown_call_usage(tmp_path, monkeypatch, failure):
    from contextlib import asynccontextmanager

    started = asyncio.Event()
    closed = []

    class LocalGateway:
        def __init__(self, budget, *args, **kwargs):
            self.budget = budget

        @asynccontextmanager
        async def serving(self):
            yield self

    class Target:
        def __init__(self, gateway, *args, **kwargs):
            self.gateway = gateway

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            closed.append(True)

        async def reply(self, *args):
            await self.gateway.budget.admit("assistant", "offline-test")
            started.set()
            if failure == "timeout":
                raise TimeoutError("Fixture provider timeout")
            await asyncio.Event().wait()

    monkeypatch.setattr("learning_lab.service.Gateway", LocalGateway)
    monkeypatch.setattr("learning_lab.service.DirectTarget", Target)
    service = LabService(tmp_path)
    task = asyncio.create_task(service.chat(ChatSpec(preferences=Preferences(goal="photography"))))
    await started.wait()
    if failure == "cancel":
        task.cancel()
    with pytest.raises(TimeoutError if failure == "timeout" else asyncio.CancelledError):
        await task
    assert closed == [True] and not service.chats
    path = next((tmp_path / "chats").glob("*/chat.json"))
    state = json.loads(path.read_text())
    assert state["status"] == ("timed_out" if failure == "timeout" else "cancelled")
    assert state["calls"] == 1 and state["closed_at"]
    assert json.loads(path.with_name("usage.json").read_text())[0]["status"] == "started"
    with pytest.raises(ValueError, match="ended"):
        await service.chat(
            ChatSpec(session_id=state["session_id"], preferences=Preferences(goal="photography"))
        )
    await service.close()


async def test_cancellation_keeps_a_terminal_manifest(tmp_path):
    service = LabService(tmp_path)
    state = await service.start_run(RunSpec(personas=3))
    await asyncio.sleep(0.01)
    result = await service.cancel(state["run_id"])
    assert result["status"] == "cancelled"
    assert result["ended_at"]
    await service.close()


async def test_failed_model_turn_retains_partial_real_tool_history(tmp_path):
    async with Gateway(Budget(1), "demo").serving() as gateway:
        async with DirectTarget(gateway, tmp_path / "workspace", "offline-scripted") as target:
            with pytest.raises(Exception, match="1-call budget"):
                await target.reply("photography", Preferences(goal="photography"))
    history = json.loads((tmp_path / "target-history.json").read_text())
    tools = [m for m in history if m["role"] == "tool"]
    assert tools and tools[0]["name"] == "search_courses"
    assert tools[0]["tool_call_id"]
    assert "CC-001" in json.dumps(tools[0]["content"])
