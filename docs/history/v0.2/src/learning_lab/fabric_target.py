"""Typed, public Fabric SDK integration with one persistent runtime per episode."""

from __future__ import annotations

import os
import json
from pathlib import Path
import sys
import uuid

from nemo_fabric import (
    DiscoveryConfig,
    EnvironmentConfig,
    Fabric,
    FabricConfig,
    HarnessConfig,
    InstructionConfig,
    InstructionsConfig,
    MetadataConfig,
    ModelConfig,
    RunRequest,
    RuntimeConfig,
    ToolsConfig,
)

from .catalogue import Preferences, freeze_catalogue
from .course_mcp import TOOL_NAMES
from .inference import Gateway
from .evidence import lifecycle, native_tool_records, relay_scopes, sanitize, save_evidence
from .outcomes import answer_outcome, require_valid_answer
from .settings import ROOT
from .target import system_prompt


def build_config(
    workspace: Path,
    model: str,
    endpoint: str,
    strategy="concise",
    relay=True,
    catalogue_path=None,
    harness="deepagents",
    model_route="fixed",
) -> FabricConfig:
    if harness not in {"deepagents", "hermes"}:
        raise ValueError("Choose the Deep Agents or Hermes Fabric harness")
    if model_route not in {"fixed", "switchyard"}:
        raise ValueError("Choose the fixed or Switchyard model route")
    discovery = DiscoveryConfig()
    if harness == "hermes":
        from .runtime_profiles import hermes_descriptor_dir

        discovery = DiscoveryConfig(local_paths=[str(hermes_descriptor_dir())])
    config = FabricConfig(
        metadata=MetadataConfig(name="singapore-learning-advisor"),
        discovery=discovery,
        harness=HarnessConfig(
            adapter_id="nvidia.fabric.hermes"
            if harness == "hermes"
            else "nvidia.fabric.langchain.deepagents",
            resolution="preinstalled",
            settings={"reasoning_config": {"enabled": False, "effort": "none"}, "save_trajectories": False}
            if harness == "hermes"
            else {"reasoning_effort": "none"},
        ),
        models={
            "default": ModelConfig(
                provider="openai-compatible",
                model=model,
                base_url=endpoint,
                api_key_env="LAB_GATEWAY_KEY",
                max_tokens=1024,
                temperature=0,
            )
        },
        instructions=InstructionsConfig(
            system=InstructionConfig(content=system_prompt(strategy), mode="replace")
        ),
        environment=EnvironmentConfig(
            provider="local",
            workspace=str(workspace),
            env_names=["LAB_GATEWAY_KEY"],
            env={"FABRIC_RELAY_CONFIG_PATH": str(workspace.parent / "fabric-relay.json")} if relay else {},
        ),
        runtime=RuntimeConfig(
            input_schema="chat", output_schema="message", timeout_seconds=120, max_turns=24
        ),
        # Hermes takes native toolset selectors here, not raw MCP function names.
        # Its maintained adapter resolves mcp-<server> to that server's tools.
        tools=ToolsConfig(enabled=["mcp-catalogue"] if harness == "hermes" else TOOL_NAMES),
    )
    config.add_mcp_server(
        "catalogue",
        transport="stdio",
        url=sys.executable,
        args=["-m", "learning_lab.course_mcp"],
        env={
            "LAB_PREFERENCES_FILE": str(workspace.parent / "preferences.json"),
            "LAB_CATALOGUE_FILE": str(catalogue_path or workspace.parent / "catalogue-snapshot.json"),
        },
    )
    config.add_skill_path(str(ROOT / "runtime-skills/course-advisor"))
    if relay:
        config.enable_relay(
            output_dir=workspace.parent / "fabric-traces",
            observability={
                "version": 4,
                "enable_full_payloads": False,
                "atof": {
                    "enabled": True,
                    "sinks": [
                        {
                            "type": "file",
                            "output_directory": str(workspace.parent / "fabric-traces"),
                            "filename": "relay.jsonl",
                            "mode": "append",
                        }
                    ],
                },
            },
        )
    return config


class FabricTarget:
    def __init__(
        self,
        gateway: Gateway,
        workspace: Path,
        model: str,
        strategy="concise",
        relay=True,
        catalogue_path=None,
        harness="deepagents",
        model_route="fixed",
    ):
        self.gateway, self.workspace = gateway, workspace
        self.harness, self.model_route = harness, model_route
        self.catalogue_path = catalogue_path or workspace.parent / "catalogue-snapshot.json"
        self.config = build_config(
            workspace,
            model,
            gateway.url,
            strategy,
            relay,
            self.catalogue_path,
            harness=harness,
            model_route=model_route,
        )
        self.fabric = Fabric()
        self.runtime = None
        self.thread_id = str(uuid.uuid4())
        self.old_key = None
        self.old_adapter = None
        self.old_tool_names = None
        self.old_harness_env: dict[str, str | None] = {}

    async def __aenter__(self):
        self.old_tool_names = self.gateway.allowed_tool_names
        self.workspace.mkdir(parents=True, exist_ok=True)
        freeze_catalogue(self.catalogue_path)
        save_evidence(self.workspace.parent / "fabric-config.json", self.config)
        lifecycle(
            self.workspace.parent,
            "configuration_saved",
            thread_id=self.thread_id,
            harness=self.harness,
            model_route=self.model_route,
        )
        runtime_environment = {}
        if self.harness == "hermes":
            from .runtime_profiles import hermes_descriptor_dir, hermes_python, hermes_runtime_environment

            if not hermes_python().is_file() or not hermes_descriptor_dir().is_dir():
                lifecycle(
                    self.workspace.parent,
                    "runtime_not_ready",
                    reason="The isolated Hermes interpreter or Fabric adapter descriptor is missing.",
                )
                raise RuntimeError(
                    "Install the isolated Hermes runtime with integrations/hermes/bootstrap.py before selecting Fabric + Hermes"
                )
            runtime_environment = hermes_runtime_environment()
        if self.config.relay:
            # The 0.6.1 wheel requires an explicit plugin-file path at adapter start.
            # Derive it from the same typed config; the native adapter still attaches Relay once.
            payload = {
                "relay": {
                    "config": {
                        "version": 1,
                        "components": [
                            {
                                "kind": "observability",
                                "enabled": True,
                                "config": self.config.relay.observability.model_dump(
                                    mode="json", exclude_none=True
                                ),
                            }
                        ],
                    }
                }
            }
            (self.workspace.parent / "fabric-relay.json").write_text(json.dumps(payload))
        self.old_key = os.environ.get("LAB_GATEWAY_KEY")
        self.old_adapter = os.environ.get("ADAPTER_PYTHON")
        self.old_harness_env = {name: os.environ.get(name) for name in runtime_environment}
        try:
            os.environ["LAB_GATEWAY_KEY"] = self.gateway.key
            os.environ.update(runtime_environment)
            if self.harness == "hermes":
                from .runtime_profiles import hermes_python

                os.environ["ADAPTER_PYTHON"] = str(hermes_python())
                lifecycle(self.workspace.parent, "harness_environment_selected", environment=runtime_environment)
            else:
                os.environ.setdefault("ADAPTER_PYTHON", sys.executable)
            self.plan = self.fabric.plan(self.config, base_dir=ROOT)
            save_evidence(self.workspace.parent / "fabric-plan.json", self.plan)
            lifecycle(self.workspace.parent, "plan_created")
            report = await self.fabric.doctor(self.config, base_dir=ROOT)
            save_evidence(self.workspace.parent / "fabric-doctor.json", report)
            lifecycle(self.workspace.parent, "doctor_completed", status=report.status)
            if report.status == "fail":
                raise RuntimeError("Fabric preflight failed; run learning-lab doctor for details")
            if self.harness == "deepagents":
                # Fabric 0.6.1's adapter blocks forbidden tool execution while
                # still advertising built-in filesystem/subagent schemas.
                # Apply the same course-only boundary to the provider request.
                self.gateway.allowed_tool_names = frozenset(TOOL_NAMES)
            self.runtime = await self.fabric.start_runtime(self.config, base_dir=ROOT)
            await self.runtime.__aenter__()
            lifecycle(self.workspace.parent, "runtime_started", thread_id=self.thread_id)
            return self
        except BaseException as exc:
            try:
                lifecycle(self.workspace.parent, "runtime_start_failed", error_type=type(exc).__name__)
            except Exception as evidence_error:
                # Preserve the original startup failure even if its evidence
                # directory became unwritable. Cleanup must still run.
                exc.add_note(f"Fabric lifecycle evidence could not be saved ({type(evidence_error).__name__})")
            finally:
                try:
                    if self.runtime is not None:
                        await self.runtime.__aexit__(type(exc), exc, exc.__traceback__)
                finally:
                    self.runtime = None
                    self._restore_key()
            raise

    async def reply(self, message: str, preferences: Preferences | None = None) -> dict:
        self.gateway.tool_rounds = 0
        user_message = message
        path = self.workspace.parent / "preferences.json"
        if preferences:
            path.write_text(preferences.model_dump_json())
        else:
            path.unlink(missing_ok=True)
        if preferences:
            message += "\nLAB_PREFERENCES=" + preferences.model_dump_json(exclude_none=True)
        before = {scope["uuid"] for scope in relay_scopes(self.workspace.parent)["scopes"]}
        lifecycle(self.workspace.parent, "invocation_started", thread_id=self.thread_id)
        try:
            result = await self.runtime.invoke(
                request=RunRequest(input=message, relay_session_root=self.thread_id)
            )
        except BaseException as exc:
            lifecycle(self.workspace.parent, "invocation_failed", error_type=type(exc).__name__)
            save_evidence(
                self.workspace.parent / "reply-outcomes.jsonl",
                {
                    "user": user_message,
                    "preferences": preferences.model_dump(mode="json") if preferences else None,
                    "runtime_status": "failed",
                    "error_type": type(exc).__name__,
                    "outcome": {
                        "status": "invalid",
                        "code": "execution_error",
                        "reason": "Fabric stopped before a public answer.",
                    },
                },
                append=True,
            )
            raise
        lifecycle(
            self.workspace.parent,
            "invocation_finished",
            status=result.status,
            runtime_id=result.runtime_id,
            invocation_id=result.invocation_id,
        )
        if result.status != "succeeded":
            error_info = sanitize(result.error)
            save_evidence(
                self.workspace.parent / "reply-outcomes.jsonl",
                {
                    "user": user_message,
                    "preferences": preferences.model_dump(mode="json") if preferences else None,
                    "runtime_status": result.status,
                    "runtime_error": error_info,
                    "raw_output": result.output,
                    "outcome": {
                        "status": "invalid",
                        "code": "execution_error",
                        "reason": "Fabric did not complete the invocation.",
                    },
                },
                append=True,
            )
            detail = (
                error_info.get("message", error_info.get("code", "Inspect the saved runtime error"))
                if isinstance(error_info, dict)
                else "Inspect the saved runtime error"
            )
            raise RuntimeError(f"Fabric invocation ended with status {result.status}: {str(detail)[:600]}")
        output = result.output.to_dict()
        content = output.get("response", output.get("content", output.get("message")))
        if isinstance(content, dict):
            content = content.get("content", content.get("text"))
        tools = native_tool_records(self.workspace.parent, exclude_uuids=before)
        outcome = answer_outcome(content)
        save_evidence(
            self.workspace.parent / "reply-outcomes.jsonl",
            {
                "user": user_message,
                "content": content,
                "raw_output": output,
                "preferences": preferences.model_dump(mode="json") if preferences else None,
                "runtime_status": result.status,
                "outcome": outcome,
                "tools": tools,
                "runtime_id": result.runtime_id,
                "invocation_id": result.invocation_id,
            },
            append=True,
        )
        if outcome["status"] != "valid":
            lifecycle(
                self.workspace.parent, "answer_rejected", outcome=outcome, invocation_id=result.invocation_id
            )
        content = require_valid_answer(content)
        return {
            "content": content,
            "outcome": outcome,
            "tools": tools,
            "preferences": preferences.model_dump(mode="json") if preferences else None,
            "thread_id": self.thread_id,
            "fabric": {
                "status": result.status,
                "runtime_id": result.runtime_id,
                "invocation_id": result.invocation_id,
                "artifacts": [str(a) for a in result.artifacts],
            },
        }

    def _restore_key(self):
        self.gateway.allowed_tool_names = self.old_tool_names
        for name, value in self.old_harness_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        if self.old_adapter is None:
            os.environ.pop("ADAPTER_PYTHON", None)
        else:
            os.environ["ADAPTER_PYTHON"] = self.old_adapter
        if self.old_key is None:
            os.environ.pop("LAB_GATEWAY_KEY", None)
        else:
            os.environ["LAB_GATEWAY_KEY"] = self.old_key

    async def __aexit__(self, *exc):
        try:
            if self.runtime:
                await self.runtime.__aexit__(*exc)
        finally:
            try:
                lifecycle(self.workspace.parent, "runtime_closed", thread_id=self.thread_id)
            finally:
                self._restore_key()
