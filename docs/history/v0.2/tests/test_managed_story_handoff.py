"""A managed condition reuses real saved inputs without inventing trace lineage."""

from contextlib import asynccontextmanager
import hashlib
import json
import uuid

import pytest

from learning_lab.catalogue import Preferences
from learning_lab.deployment import PlatformBridge
from learning_lab.service import LabService


def saved_story(folder):
    reference = {key: str(uuid.uuid4()) for key in ("run_id", "episode_id", "condition_id")}
    prefs = Preferences(goal="photography", budget_sgd=50, days=[5]).model_dump(mode="json")
    path = folder / reference["run_id"]
    path.mkdir()
    (path / "run.json").write_text(json.dumps({
        "run_id": reference["run_id"], "status": "completed", "catalogue_sha256": "source-snapshot",
        "spec": {"mode": "demo", "harness": "deepagents", "model_route": "fixed"},
    }))
    events = [
        {"type": "episode_started", "episode_id": reference["episode_id"], "preferences": prefs,
         "source_id": "labelled-offline-profile", "story_id": "photography"},
        {"type": "message", "episode_id": reference["episode_id"], "role": "user",
         "content": "Find a Saturday photography class within S$50."},
        {"type": "message", "episode_id": reference["episode_id"], "role": "assistant",
         "content": "This old reply must not become managed conversation memory."},
    ]
    (path / "events.jsonl").write_text("\n".join(map(json.dumps, events)) + "\n")
    return reference, prefs, events


@pytest.mark.parametrize("broken", ["unknown_episode", "missing_preferences", "no_public_input", "caller_labels"])
async def test_invalid_story_lineage_fails_before_sdk_creation(tmp_path, monkeypatch, broken):
    reference, prefs, events = saved_story(tmp_path)
    path = tmp_path / reference["run_id"] / "events.jsonl"
    if broken == "unknown_episode":
        reference["episode_id"] = str(uuid.uuid4())
    elif broken == "missing_preferences":
        events[0].pop("preferences")
    elif broken == "no_public_input":
        events = [event for event in events if event.get("role") != "user"]
    else:
        reference["source_profile_id"] = "caller-cannot-assert-this"
    path.write_text("\n".join(map(json.dumps, events)) + "\n")
    calls = []

    async def unexpected(self, operation, **arguments):
        calls.append(operation)
        raise AssertionError("Invalid lineage must stop before the SDK")

    monkeypatch.setattr(PlatformBridge, "call", unexpected)
    service = LabService(tmp_path)
    try:
        job = await service.platform_action({"operation": "sessions_create", "arguments": {
            "deployment": "demo", "story_reference": reference,
        }})
        await service.tasks[job["job_id"]]
        result = service.get_platform_job(job["job_id"])
        assert result["status"] == "failed" and result["calls"] == 0
        assert not calls and not service.managed_sessions and service.deployment_bridge is None
    finally:
        await service.close()


async def test_managed_story_lineage_is_verified_saved_and_never_forwarded_to_sdk(tmp_path, monkeypatch):
    reference, prefs, events = saved_story(tmp_path)
    sdk_invocations = []
    service = LabService(tmp_path)

    async def call(self, operation, **arguments):
        assert "story_reference" not in arguments
        if operation == "sessions_create":
            return {"session": {"name": "story-session", "status": "active"},
                    "deployment": {"harness_kind": "deepagents", "frozen_preferences": prefs}}
        if operation == "sessions_close":
            return {"session": {"name": "story-session", "status": "closed"},
                    "runtime_cleanup_confirmed": True}
        assert operation == "invoke"
        sdk_invocations.append(arguments)
        await next(iter(service.managed_sessions.values()))["budget"].admit("assistant", "mocked")
        return {"response": "Labelled mocked managed reply"}

    class LocalGateway:
        def __init__(self, budget, *args, **kwargs):
            self.budget = budget

        @asynccontextmanager
        async def serving(self):
            yield self

    class Admission:
        async def activate(self, run_id, gateway, preferences):
            assert preferences == prefs

        async def deactivate(self, run_id):
            pass

    async def admission():
        service.deployment_bridge = Admission()

    monkeypatch.setattr(PlatformBridge, "call", call)
    monkeypatch.setattr("learning_lab.service.Gateway", LocalGateway)
    monkeypatch.setattr(service, "_deployment_gateway", admission)

    async def action(operation, **arguments):
        job = await service.platform_action({"operation": operation, "arguments": arguments})
        await service.tasks[job["job_id"]]
        return service.get_platform_job(job["job_id"])

    try:
        created = await action("sessions_create", deployment="demo", story_reference=reference)
        assert created["story_reference"]["source_mode"] == "demo"
        assert created["story_reference"]["source_profile_id"] == "labelled-offline-profile"
        initial = events[1]["content"]
        assert created["story_reference"]["first_learner_input_sha256"] == hashlib.sha256(initial.encode()).hexdigest()
        args = {"deployment": "demo", "session_id": "story-session", "input": initial,
                "preferences": prefs, "model_route": "fixed", "story_reference": reference}
        for changed in (
            {"input": "A different request"},
            {"preferences": {**prefs, "budget_sgd": 100}},
            {"story_reference": {**reference, "condition_id": str(uuid.uuid4())}},
        ):
            rejected = await action("invoke", **{**args, **changed})
            assert rejected["status"] == "failed" and rejected["calls"] == 0
        assert not sdk_invocations
        first = await action("invoke", **args)
        assert first["status"] == "completed" and first["calls"] == 1
        assert first["story_reference"] == created["story_reference"]
        followup = {key: value for key, value in args.items() if key != "story_reference"}
        second = await action("invoke", **{**followup, "input": "What should I confirm before enrolling?"})
        assert second["status"] == "completed" and second["story_reference"] == first["story_reference"]
        assert len(sdk_invocations) == 2
        # A changed saved public input must not silently inherit the old lineage.
        events[1]["content"] += " changed"
        (tmp_path / reference["run_id"] / "events.jsonl").write_text("\n".join(map(json.dumps, events)))
        changed = await action("invoke", **followup)
        assert changed["status"] == "failed" and changed["calls"] == 0
        assert next(iter(service.managed_sessions.values()))["budget"].calls == 2
        assert "saved story inputs changed" in changed["error"]
        assert len(sdk_invocations) == 2
        assert (await action("sessions_close", name="story-session"))["status"] == "completed"
    finally:
        await service.close()
