"""SDK-boundary captures retain native envelopes and their real correlations."""

import asyncio
import base64
from datetime import timedelta
import hashlib
import json
import sys
from types import SimpleNamespace
import uuid

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from nemo_fabric import RunResult
import pytest
import yaml

from learning_lab.catalogue import Preferences
from learning_lab.fabric_target import FabricTarget
from learning_lab.sandbox import EXPORT_FILES, NativeSandbox
from learning_lab import sandbox_runtime


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


@pytest.mark.parametrize("terminal", ["succeeded", "failed", "raises", "cancelled"])
async def test_full_native_fabric_request_result_and_public_preferences_are_captured_before_validation(
    tmp_path, terminal
):
    gateway = SimpleNamespace(url="http://127.0.0.1:1/v1", key="unused-fixture", tool_rounds=0)
    target = FabricTarget(gateway, tmp_path / "workspace", "offline-scripted")
    target.workspace.mkdir()
    actual = []

    class Runtime:
        async def invoke(self, *, request):
            # The pre-invocation receipt already exists when the SDK receives it.
            assert lines(tmp_path / "fabric-run-requests.jsonl")[-1]["request"] == request.model_dump(mode="json")
            actual.append(request)
            if terminal == "raises":
                raise RuntimeError("Authorization failed: Bearer fixture-secret")
            if terminal == "cancelled":
                raise asyncio.CancelledError("cancelled during the native invocation")
            return RunResult.from_mapping({
                "agent_name": "capture-fixture", "harness": "deepagents", "adapter_kind": "python",
                "adapter_id": "nvidia.fabric.langchain.deepagents", "runtime_id": "runtime-fixture",
                "invocation_id": "invocation-fixture", "request_id": request.request_id,
                "status": terminal, "output": {"response": "The frozen catalogue contains a photography class."},
                "metadata": {"native_extension": {"kept": True}, "api_key": "never-persist-fixture"},
                "error": {"code": "offline_failure", "message": "Fixture failure"} if terminal == "failed" else None,
            })

    target.runtime = Runtime()
    public = Preferences(goal="photography", days=[5])
    if terminal == "succeeded":
        reply = await target.reply("I want a Saturday photography class.", public)
        assert reply["fabric"]["invocation_id"] == "invocation-fixture"
    else:
        with pytest.raises(asyncio.CancelledError if terminal == "cancelled" else RuntimeError):
            await target.reply("I want a Saturday photography class.", public)
    request = lines(tmp_path / "fabric-run-requests.jsonl")[0]
    result = lines(tmp_path / "fabric-run-results.jsonl")[0]
    preferences = lines(tmp_path / "preferences-by-turn.jsonl")[0]
    assert request["request_id"] == result["request_id"] == preferences["request_id"] == actual[0].request_id
    assert request["thread_id"] == result["thread_id"] == target.thread_id
    assert request["turn"] == result["turn"] == preferences["turn"] == 1
    assert request["request"]["input"].startswith("I want a Saturday photography class.\nLAB_PREFERENCES=")
    assert preferences["preferences"] == public.model_dump(mode="json")
    assert preferences["file_sha256"] == hashlib.sha256((tmp_path / "preferences.json").read_bytes()).hexdigest()
    if terminal in {"raises", "cancelled"}:
        assert result["result"] is None and result["boundary_status"] == "raised"
        assert result["error"]["type"] == ("CancelledError" if terminal == "cancelled" else "RuntimeError")
    else:
        native = result["result"]
        assert result["boundary_status"] == "returned"
        assert native["status"] == terminal and native["request_id"] == request["request_id"]
        assert native["metadata"]["native_extension"] == {"kept": True}
        assert {"usage", "events", "artifacts", "telemetry", "resource_snapshot", "execution"} <= native.keys()
    serialized = json.dumps(result)
    assert "never-persist-fixture" not in serialized and "fixture-secret" not in serialized


async def test_each_invocation_freezes_public_preferences_and_records_absence_instead_of_stale_values(tmp_path):
    gateway = SimpleNamespace(url="http://127.0.0.1:1/v1", key="unused-fixture", tool_rounds=0)
    target = FabricTarget(gateway, tmp_path / "workspace", "offline-scripted")
    target.workspace.mkdir()

    class Runtime:
        async def invoke(self, *, request):
            return RunResult.from_mapping({"agent_name": "capture-fixture", "harness": "deepagents",
                "adapter_kind": "python", "runtime_id": "fixture", "invocation_id": request.request_id,
                "request_id": request.request_id, "status": "succeeded", "output": {"response": "A public answer."}})

    target.runtime = Runtime()
    await target.reply("My goal", Preferences(goal="photography"))
    await target.reply("My budget is S$50", Preferences(goal="photography", budget_sgd=50))
    await target.reply("No current public preference preset")
    snapshots = lines(tmp_path / "preferences-by-turn.jsonl")
    assert [row["turn"] for row in snapshots] == [1, 2, 3]
    assert snapshots[0]["preferences"]["budget_sgd"] is None
    assert snapshots[1]["preferences"]["budget_sgd"] == 50
    assert snapshots[2]["preferences"] is None and snapshots[2]["present"] is False
    assert snapshots[2]["file_sha256"] is None and not (tmp_path / "preferences.json").exists()
    assert len({row["request_id"] for row in snapshots}) == 3


async def test_mcp_capture_is_the_real_native_tools_list_response(tmp_path):
    capture = tmp_path / "mcp-tools-list.jsonl"
    server = StdioServerParameters(command=sys.executable, args=["-m", "learning_lab.course_mcp"],
                                   env={"LAB_MCP_EVIDENCE_FILE": str(capture)})
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=20)) as session:
            await session.initialize()
            assert not capture.exists()  # Preparation is not discovery evidence.
            result = await session.list_tools()
            recorded = lines(capture)
            assert len(recorded) == 1 and recorded[0]["method"] == "tools/list"
            assert recorded[0]["server_request_id"]
            assert recorded[0]["result"]["tools"] == [
                tool.model_dump(mode="json", by_alias=True) for tool in result.tools
            ]
            assert {tool.name for tool in result.tools} == {
                "search_courses", "get_course_details", "compare_courses"
            }


def test_hermes_yaml_capture_retains_generated_bytes_and_redacts_secrets(tmp_path):
    target = FabricTarget(SimpleNamespace(url="http://127.0.0.1:1/v1"), tmp_path / "workspace",
                          "offline-scripted", harness="hermes", base_dir=tmp_path)
    runtime_id = "runtime-fixture"
    target.runtime = SimpleNamespace(runtime_id=runtime_id)
    source = tmp_path / "artifacts/.fabric/hermes/runtimes" / runtime_id / "config.yaml"
    source.parent.mkdir(parents=True)
    raw = b"# Native adapter formatting\nmodel:\n  default: fixture\nplatform_toolsets:\n  cli: [mcp-catalogue]\n"
    source.write_bytes(raw)
    target._capture_hermes_native_config({"hermes_config_path": str(source)})
    assert (tmp_path / "hermes-native-config.yaml").read_bytes() == raw
    first = lines(tmp_path / "hermes-config-capture.jsonl")[0]
    assert first["byte_exact"] is True and first["runtime_id"] == runtime_id
    source.write_text("model:\n  default: fixture\n  api_key: never-persist-fixture\n")
    target._capture_hermes_native_config({"hermes_config_path": str(source)})
    captured = yaml.safe_load((tmp_path / "hermes-native-config.yaml").read_text())
    assert captured["model"]["api_key"] == "[redacted]"
    assert lines(tmp_path / "hermes-config-capture.jsonl")[-1]["byte_exact"] is False
    other = tmp_path / "unrelated/config.yaml"
    other.parent.mkdir()
    other.write_text("model: unrelated")
    with pytest.raises(ValueError, match="selected runtime"):
        target._capture_hermes_native_config({"hermes_config_path": str(other)})


def test_every_native_export_is_verified_by_the_host_without_widening_private_files(tmp_path, monkeypatch):
    sandbox_files = tmp_path / "sandbox"
    sandbox_files.mkdir()
    for name in EXPORT_FILES:
        (sandbox_files / name).write_bytes((name + "\n").encode())
    (sandbox_files / "private-source.json").write_text("never export this")
    monkeypatch.setattr(sandbox_runtime, "RUN", sandbox_files)
    frames = []
    sandbox_runtime.export_artifacts(SimpleNamespace(emit=frames.append))
    assert {frame["path"] for frame in frames} == EXPORT_FILES
    host = NativeSandbox(str(uuid.uuid4()), tmp_path / "host", None, catalogue=tmp_path / "catalogue.json")
    for frame in frames:
        host.artifact(frame)
        assert base64.b64decode(frame["data"]) == (sandbox_files / frame["path"]).read_bytes()
    assert set(host.artifacts) == EXPORT_FILES
    for name in EXPORT_FILES:
        assert (tmp_path / "host/native" / name).read_bytes() == (sandbox_files / name).read_bytes()
    assert not (tmp_path / "host/native/private-source.json").exists()
