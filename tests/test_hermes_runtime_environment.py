"""Offline SDK lifecycle fixtures for Hermes's supported retry environment."""

from contextlib import nullcontext
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from learning_lab import fabric_target, runtime_profiles


def test_hermes_managed_policy_uses_its_public_scope_and_single_attempt_settings():
    environment = runtime_profiles.hermes_runtime_environment()
    managed = Path(environment["HERMES_MANAGED_DIR"])
    assert managed.is_absolute()
    assert environment["HERMES_STREAM_RETRIES"] == "0"
    policy = yaml.safe_load((managed / "config.yaml").read_text())
    assert policy["agent"]["api_max_retries"] == 1
    assert policy["agent"]["auto_recovery_cycles"] == 0


@pytest.mark.parametrize("previous", [None, "preexisting-fixture-value"])
@pytest.mark.parametrize("failure", [None, "plan", "start", "exit", "plan_logging", "entered_logging", "exit_logging"])
async def test_hermes_retry_environment_and_runtime_identity_are_scoped_and_restored(
    tmp_path, monkeypatch, previous, failure
):
    selected = {"HERMES_MANAGED_DIR": str(tmp_path / "managed"), "HERMES_STREAM_RETRIES": "0"}
    names = ["LAB_GATEWAY_KEY", "ADAPTER_PYTHON", *selected]
    for name in names:
        if previous is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, previous)
    interpreter = tmp_path / "hermes-python"
    interpreter.touch()
    descriptor = tmp_path / "descriptor"
    descriptor.mkdir()
    monkeypatch.setattr(runtime_profiles, "hermes_python", lambda: interpreter)
    monkeypatch.setattr(runtime_profiles, "hermes_descriptor_dir", lambda: descriptor)
    monkeypatch.setattr(runtime_profiles, "hermes_runtime_environment", lambda: selected)
    observed = []
    original_lifecycle = fabric_target.lifecycle

    def lifecycle(folder, event, **values):
        if (failure == "plan_logging" and event == "runtime_start_failed") or (
            failure == "exit_logging" and event == "runtime_closed"
        ) or (
            failure == "entered_logging" and event in {"runtime_started", "runtime_start_failed"}
        ):
            raise OSError("offline evidence write failure")
        return original_lifecycle(folder, event, **values)

    monkeypatch.setattr(fabric_target, "lifecycle", lifecycle)

    def check(phase):
        observed.append(phase)
        assert {name: os.environ.get(name) for name in selected} == selected
        assert os.environ["ADAPTER_PYTHON"] == str(interpreter)
        assert os.environ["LAB_GATEWAY_KEY"] == "offline-gateway-key"
        if failure == phase or (failure == "plan_logging" and phase == "plan"):
            raise RuntimeError("offline lifecycle failure")

    class Runtime:
        async def __aenter__(self):
            check("enter")
            return self

        async def __aexit__(self, *exc):
            check("exit")

    class Fabric:
        def plan(self, config, **kwargs):
            check("plan")
            assert config.harness.adapter_id == "nvidia.fabric.hermes"
            assert config.tools.enabled == ["mcp-catalogue"]
            assert not {"api_max_retries", "auto_recovery_cycles"} & config.harness.settings.keys()
            return {"adapter_id": config.harness.adapter_id}

        async def doctor(self, *args, **kwargs):
            check("doctor")
            return SimpleNamespace(status="pass")

        async def start_runtime(self, *args, **kwargs):
            check("start")
            return Runtime()

    monkeypatch.setattr(fabric_target, "Fabric", Fabric)
    gateway = SimpleNamespace(url="http://127.0.0.1:1/v1", key="offline-gateway-key", allowed_tool_names=None)
    target = fabric_target.FabricTarget(gateway, tmp_path / "workspace", "offline-scripted", harness="hermes")
    expectation = (
        pytest.raises(OSError, match="offline evidence write failure")
        if failure in {"entered_logging", "exit_logging"}
        else pytest.raises(RuntimeError, match="offline lifecycle failure") if failure else nullcontext()
    )
    with expectation as caught:
        async with target:
            check("active")
            assert gateway.allowed_tool_names is None  # Native Hermes discovery remains available.
    assert observed[0] == "plan"
    if failure == "entered_logging":
        assert observed[-1] == "exit"  # The allocated runtime closes despite both failed evidence writes.
    if failure in {"plan_logging", "entered_logging"}:
        assert any("lifecycle evidence could not be saved" in note for note in caught.value.__notes__)
    assert {name: os.environ.get(name) for name in names} == dict.fromkeys(names, previous)


@pytest.mark.parametrize("failure", ["plan", "exit_logging"])
async def test_deepagents_does_not_load_or_override_the_hermes_retry_scope(tmp_path, monkeypatch, failure):
    monkeypatch.setenv("HERMES_MANAGED_DIR", "other-managed-scope")
    monkeypatch.setenv("HERMES_STREAM_RETRIES", "7")

    def unused():
        pytest.fail("Deep Agents must not load the Hermes runtime policy")

    monkeypatch.setattr(runtime_profiles, "hermes_runtime_environment", unused)
    original_lifecycle = fabric_target.lifecycle

    def lifecycle(folder, event, **values):
        if failure == "exit_logging" and event == "runtime_closed":
            raise OSError("offline evidence write failure")
        return original_lifecycle(folder, event, **values)

    monkeypatch.setattr(fabric_target, "lifecycle", lifecycle)

    class Runtime:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            assert gateway.allowed_tool_names == frozenset(fabric_target.TOOL_NAMES)

    class Fabric:
        def plan(self, *args, **kwargs):
            assert os.environ["HERMES_MANAGED_DIR"] == "other-managed-scope"
            assert os.environ["HERMES_STREAM_RETRIES"] == "7"
            if failure == "plan":
                raise RuntimeError("offline stop before any native runtime")
            return {"adapter_id": "nvidia.fabric.langchain.deepagents"}

        async def doctor(self, *args, **kwargs):
            return SimpleNamespace(status="pass")

        async def start_runtime(self, *args, **kwargs):
            return Runtime()

    monkeypatch.setattr(fabric_target, "Fabric", Fabric)
    gateway = SimpleNamespace(url="http://127.0.0.1:1/v1", key="offline-gateway-key", allowed_tool_names=None)
    target = fabric_target.FabricTarget(gateway, tmp_path / "workspace", "offline-scripted")
    expectation = (pytest.raises(RuntimeError, match="offline stop") if failure == "plan"
                   else pytest.raises(OSError, match="offline evidence write failure"))
    with expectation:
        async with target:
            pass
    assert os.environ["HERMES_MANAGED_DIR"] == "other-managed-scope"
    assert os.environ["HERMES_STREAM_RETRIES"] == "7"
    assert gateway.allowed_tool_names is None
