import asyncio
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import yaml

from learning_lab.deployment import AdmissionLease, DeploymentInferenceBridge, PlatformSpec
from learning_lab.inference import Budget


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("operation", ["status", "sessions_recover"])
@pytest.mark.parametrize("explicit_remote", [False, True])
async def test_remote_bridge_never_inherits_local_executor_and_recovery_requires_explicit_remote_config(
    tmp_path, monkeypatch, operation, explicit_remote
):
    from learning_lab.deployment import PlatformBridge, PlatformUnavailable

    local = tmp_path / "local-executor.yaml"
    local.write_text("# offline local config fixture\n")
    remote = tmp_path / "remote-executor.yaml"
    remote.write_text("# offline explicit remote config fixture\n")
    monkeypatch.setenv("NHX_CONFIG_FILE_PATH", str(local))
    monkeypatch.delenv("LAB_HELIX_REMOTE_EXECUTOR_CONFIG", raising=False)
    if explicit_remote:
        monkeypatch.setenv("LAB_HELIX_REMOTE_EXECUTOR_CONFIG", str(remote))
    monkeypatch.setattr("learning_lab.deployment.platform_python", lambda: Path(sys.executable))
    captured = []

    class Process:
        returncode = 0

        async def communicate(self, request):
            assert json.loads(request)["platform"]["target"] == "remote"
            return json.dumps({"ok": True, "result": {"offline": True}}).encode(), b""

    async def spawn(*args, **kwargs):
        captured.append(kwargs["env"])
        return Process()

    monkeypatch.setattr("asyncio.create_subprocess_exec", spawn)
    bridge = PlatformBridge(PlatformSpec(target="remote", base_url="https://remote.example.test"))
    if operation == "sessions_recover" and not explicit_remote:
        with pytest.raises(PlatformUnavailable, match="Set LAB_HELIX_REMOTE_EXECUTOR_CONFIG"):
            await bridge.call(operation)
        assert captured == []  # No native lookup, SDK subprocess or destructive action.
    else:
        assert await bridge.call(operation) == {"offline": True}
        assert len(captured) == 1
        assert captured[0].get("NHX_CONFIG_FILE_PATH") == (str(remote) if explicit_remote else None)
        assert str(local) not in captured[0].get("NHX_CONFIG_FILE_PATH", "")


def test_unknown_platform_target_fails_before_loading_local_environment(monkeypatch):
    loader = AsyncMock()
    monkeypatch.setattr("learning_lab.deployment.load_environment", loader)
    with pytest.raises(ValueError, match="explicit local or remote"):
        PlatformSpec.configured("typo-remote")
    loader.assert_not_called()


def test_remote_target_requires_https_even_for_loopback_alias():
    with pytest.raises(ValueError, match="HTTPS"):
        PlatformSpec(target="remote", base_url="http://127.0.0.1:8080")


async def test_deactivation_cancels_slow_body_and_prevents_stale_gateway_use():
    bridge = DeploymentInferenceBridge("a" * 32)
    gateway = AsyncMock()
    gateway.budget = Budget(3)
    request = AsyncMock()
    request.headers = {"Authorization": "Bearer " + "a" * 32}
    parsing = asyncio.Event()

    async def read_body():
        parsing.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            # Even a parser that finishes despite cancellation cannot revive
            # the gateway captured before its body was available.
            return {"messages": [{"role": "user", "content": "late body"}]}

    request.json.side_effect = read_body
    await bridge.activate("old-run", gateway)
    task = asyncio.create_task(bridge._complete(request))
    await parsing.wait()
    await asyncio.wait_for(bridge.deactivate("old-run"), 1)
    assert (await task).status == 409
    gateway.complete.assert_not_awaited()
    assert gateway.budget.calls == 0
    assert not bridge._requests
    await bridge.activate("new-run", gateway)
    assert bridge.lease.run_id == "new-run"
    await bridge.deactivate("new-run")


def module(path):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(path.stem, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_recovery_receipt_is_server_job_scoped_and_rejects_symlinks(tmp_path, monkeypatch):
    bridge = module(ROOT / "integrations/platform/bridge.py")
    monkeypatch.setattr(bridge, "ROOT", tmp_path)
    job = "92c98be1-19b4-4b4c-ae86-7ff738403c08"
    receipt = tmp_path / "runs" / "platform-jobs" / job / "recovery-receipt.json"
    assert bridge.recovery_receipt({"receipt_path": str(receipt)}) == receipt
    for value in (
        str(tmp_path / "elsewhere.json"),
        str(receipt.parent / "arbitrary.json"),
        str(receipt).replace(job, "not-a-job"),
        "relative/recovery-receipt.json",
    ):
        with pytest.raises(ValueError):
            bridge.recovery_receipt({"receipt_path": value})
    receipt.parent.mkdir(parents=True)
    receipt.symlink_to(tmp_path / "outside.json")
    with pytest.raises(ValueError, match="symlinks"):
        bridge.recovery_receipt({"receipt_path": str(receipt)})


@pytest.mark.parametrize("harness", ["deepagents", "hermes"])
def test_intake_correlation_preserves_owned_records_and_explains_only_empty_hermes(harness):
    bridge = module(ROOT / "integrations/platform/bridge.py")
    config = {"default_harness": harness, "harnesses": {harness: {"kind": harness}}}
    evidence = {
        "status": "no_records_observed",
        "session_identity": {"session_uuid": "73831e5e-4234-458c-8033-c8af81aa79c5"},
        "traces": [],
        "spans": [],
    }
    bridge.annotate_intake_correlation(evidence, config)
    if harness == "hermes":
        assert evidence["correlation"]["status"] == "unsupported"
        assert evidence["correlation"]["native_relay_session_uuid"] is None
        assert (
            evidence["correlation"]["expected_platform_session_uuid"]
            == evidence["session_identity"]["session_uuid"]
        )
    else:
        assert "correlation" not in evidence
    for status in ("observed", "unavailable"):
        actual = {"status": status, "traces": [{"id": "owned-trace"}]}
        bridge.annotate_intake_correlation(actual, config)
        assert actual == {"status": status, "traces": [{"id": "owned-trace"}]}


@pytest.mark.parametrize(
    "value", ["https://key:secret@platform.test", "http://platform.test", "https://platform.test?key=secret"]
)
def test_platform_endpoints_never_embed_credentials_or_remote_plaintext(value):
    with pytest.raises(ValueError):
        PlatformSpec(base_url=value)


async def test_exclusive_deployment_lease_enforces_shared_budget_and_owner():
    lease = AdmissionLease()
    budget = Budget(1)
    with pytest.raises(RuntimeError, match="No active"):
        await lease.admit()
    await lease.acquire("run-one", budget)
    with pytest.raises(RuntimeError, match="Another workload"):
        await lease.acquire("run-two", Budget(10))
    assert (await lease.admit())["run_id"] == "run-one"
    assert budget.calls == 1
    with pytest.raises(RuntimeError, match="budget"):
        await lease.admit()
    with pytest.raises(RuntimeError, match="owning"):
        await lease.release("run-two")
    await lease.release("run-one")
    assert lease.run_id is None


async def test_deployed_model_traffic_is_denied_without_lease_and_admitted_once():
    bridge = DeploymentInferenceBridge("a" * 32)
    request = AsyncMock()
    request.headers = {"Authorization": "Bearer " + "a" * 32}
    request.json.return_value = {"messages": [{"role": "user", "content": "hello"}]}
    assert (await bridge._complete(request)).status == 409
    budget = Budget(3)

    class Gateway:
        async def complete(self, payload, role):
            await self.budget.admit(role, "demo")
            return {"choices": [{"message": {"content": "hello"}}]}

    gateway = Gateway()
    gateway.budget = budget
    await bridge.activate("run-one", gateway)
    response = await bridge._complete(request)
    assert response.status == 200
    assert budget.calls == 1
    await bridge.deactivate("run-one")
    assert (await bridge._complete(request)).status == 409


def test_switchyard_inventory_cannot_silently_collapse_into_fixed_mode():
    validator = module(ROOT / "integrations/proxy/validate_config.py")
    config = yaml.safe_load((ROOT / "integrations/proxy/litellm.yaml").read_text())
    env = {"LAB_PROXY_API_KEY": "a" * 32}
    for role in ("FIXED", "SUPPORT", "CAPABLE", "EFFICIENT"):
        env[f"LAB_{role}_MODEL"] = f"openai/{role.lower()}"
        env[f"LAB_{role}_API_BASE"] = "https://provider.test/v1"
        env[f"LAB_{role}_API_KEY"] = "test-key-only"
    assert validator.validate(config, env)["inference_calls"] == 0
    env["LAB_CAPABLE_MODEL"] = env["LAB_EFFICIENT_MODEL"]
    with pytest.raises(ValueError, match="distinct"):
        validator.validate(config, env)
    env["LAB_FIXED_MODEL"] = "openai/"
    with pytest.raises(ValueError, match="nonempty"):
        validator.validate(config, env)


def test_image_bundle_copies_same_mcp_source_without_root_simulator_dependencies(tmp_path, monkeypatch):
    packaging = module(ROOT / "integrations/platform/package_agent.py")
    monkeypatch.setattr(packaging, "HERE", tmp_path)
    (tmp_path / "install_hermes.py").write_text("# fixture installer\n")
    (tmp_path / "patch_mcp_context.py").write_text("# fixture context patch\n")
    (tmp_path / "hermes_python.sh").write_bytes(
        (ROOT / "integrations/platform/hermes_python.sh").read_bytes()
    )
    bundle = packaging.prepare_bundle("hermes")
    assert (bundle / "src/learning_lab/course_mcp.py").read_bytes() == (
        ROOT / "src/learning_lab/course_mcp.py"
    ).read_bytes()
    assert not (bundle / ".env").exists()
    assert yaml.safe_load((bundle / "hermes-managed/config.yaml").read_text())["agent"] == {
        "api_max_retries": 1,
        "auto_recovery_cycles": 0,
    }
    manifest = json.loads((bundle / "source-manifest.json").read_text())
    assert not manifest["deployed"]
    assert "usersim" not in (bundle / "pyproject.toml").read_text().lower()
    assert (bundle / "hermes-python.sh").read_bytes() == (
        ROOT / "integrations/platform/hermes_python.sh"
    ).read_bytes()
    assert "hermes-python.sh" in manifest["sources"]
    config = yaml.safe_load((bundle / "agent.yaml").read_text())
    assert config["tools"]["enabled"] == ["mcp-catalogue"]
    assert "base_url" not in config["models"]["default"]
    (bundle / ".env").write_text("DO_NOT_PACKAGE=fixture\n")
    with pytest.raises(ValueError, match="unexpected files"):
        packaging.prepare_bundle("hermes")


def test_hermes_packaging_patch_fails_closed_on_upstream_template_drift(tmp_path):
    packaging = module(ROOT / "integrations/platform/package_agent.py")
    source = tmp_path / "Dockerfile"
    source.write_text("FROM example\n")
    with pytest.raises(RuntimeError, match="template changed"):
        packaging.customize_dockerfile(source, "hermes")


def test_hermes_image_launcher_sets_only_static_runtime_selection():
    text = (ROOT / "integrations/platform/hermes_python.sh").read_text()
    exports = [line for line in text.splitlines() if line.startswith("export ")]
    assert exports == [
        "export ADAPTER_PYTHON=/opt/hermes-venv/bin/python",
        "export HERMES_MANAGED_DIR=/workspace/hermes-managed",
        "export HERMES_STREAM_RETRIES=0",
    ]
    assert text.endswith('exec /workspace/.venv/bin/python-real "$@"\n')


async def test_trusted_preferences_callback_is_separate_validated_and_lease_scoped():
    from aiohttp import web

    bridge = DeploymentInferenceBridge("a" * 32, "b" * 32)
    request = AsyncMock()
    request.headers = {"Authorization": "Bearer " + "a" * 32}
    with pytest.raises(web.HTTPUnauthorized):
        await bridge._preferences(request)
    request.headers = {"Authorization": "Bearer " + "b" * 32}
    assert (await bridge._preferences(request)).status == 409
    gateway = AsyncMock()
    gateway.budget = Budget(3)
    with pytest.raises(ValueError):
        await bridge.activate("invalid", gateway, {"goal": "baking", "budget_sgd": -1})
    assert bridge.lease.run_id is None
    await bridge.activate("real-run", gateway, {"goal": "baking", "budget_sgd": 50})
    payload = json.loads((await bridge._preferences(request)).text)
    assert payload["version"] == 1
    assert payload["run_id"] == "real-run"
    assert payload["preferences"]["budget_sgd"] == 50
    assert gateway.budget.calls == 0
    await bridge.deactivate("real-run")
    assert (await bridge._preferences(request)).status == 409


def test_mcp_context_patch_only_expands_one_allowlisted_slot_and_rejects_drift(tmp_path):
    patching = module(ROOT / "integrations/platform/patch_mcp_context.py")
    for name, (before, _) in patching.PATCHES.items():
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(before)
    patching.patch(tmp_path)
    for name in patching.PATCHES:
        assert 'key == "LAB_PREFERENCES_TOKEN"' in (tmp_path / name).read_text()
        assert "os.path.expandvars" in (tmp_path / name).read_text()
    with pytest.raises(RuntimeError, match="context changed"):
        patching.patch(tmp_path)
