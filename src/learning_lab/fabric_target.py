"""Typed, public Fabric SDK integration with one persistent runtime per episode."""

from __future__ import annotations

import os
import json
from pathlib import Path
import sys
import uuid

from nemo_fabric import (
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
from .settings import ROOT
from .target import system_prompt


def build_config(
    workspace: Path, model: str, endpoint: str, strategy="concise", relay=True, catalogue_path=None
) -> FabricConfig:
    config = FabricConfig(
        metadata=MetadataConfig(name="singapore-learning-advisor"),
        harness=HarnessConfig(
            adapter_id="nvidia.fabric.langchain.deepagents",
            resolution="preinstalled",
            settings={"reasoning_effort": "none"},
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
        tools=ToolsConfig(enabled=TOOL_NAMES),
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
    ):
        self.gateway, self.workspace = gateway, workspace
        self.catalogue_path = catalogue_path or workspace.parent / "catalogue-snapshot.json"
        self.config = build_config(workspace, model, gateway.url, strategy, relay, self.catalogue_path)
        self.fabric = Fabric()
        self.runtime = None
        self.thread_id = str(uuid.uuid4())
        self.old_key = None
        self.old_adapter = None

    async def __aenter__(self):
        self.workspace.mkdir(parents=True, exist_ok=True)
        freeze_catalogue(self.catalogue_path)
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
        os.environ["LAB_GATEWAY_KEY"] = self.gateway.key
        os.environ.setdefault("ADAPTER_PYTHON", sys.executable)
        try:
            self.plan = self.fabric.plan(self.config, base_dir=ROOT)
            report = await self.fabric.doctor(self.config, base_dir=ROOT)
            if report.status == "fail":
                raise RuntimeError("Fabric preflight failed; run learning-lab doctor for details")
            self.runtime = await self.fabric.start_runtime(self.config, base_dir=ROOT)
            await self.runtime.__aenter__()
            return self
        except BaseException:
            self._restore_key()
            raise

    async def reply(self, message: str, preferences: Preferences | None = None) -> dict:
        self.gateway.tool_rounds = 0
        path = self.workspace.parent / "preferences.json"
        if preferences:
            path.write_text(preferences.model_dump_json())
        else:
            path.unlink(missing_ok=True)
        if preferences:
            message += "\nLAB_PREFERENCES=" + preferences.model_dump_json(exclude_none=True)
        result = await self.runtime.invoke(
            request=RunRequest(input=message, relay_session_root=self.thread_id)
        )
        if result.status != "succeeded":
            raise RuntimeError(f"Fabric invocation ended with status {result.status}: {result.error}")
        output = result.output.to_dict()
        content = output.get("response", output.get("content", output.get("message", output)))
        if isinstance(content, dict):
            content = content.get("content", content.get("text", content))
        return {
            "content": content if isinstance(content, str) else str(content),
            "tools": [],
            "thread_id": self.thread_id,
            "fabric": {
                "status": result.status,
                "runtime_id": result.runtime_id,
                "invocation_id": result.invocation_id,
                "artifacts": [str(a) for a in result.artifacts],
            },
        }

    def _restore_key(self):
        if self.old_adapter is None:
            os.environ.pop("ADAPTER_PYTHON", None)
        if self.old_key is None:
            os.environ.pop("LAB_GATEWAY_KEY", None)
        else:
            os.environ["LAB_GATEWAY_KEY"] = self.old_key

    async def __aexit__(self, *exc):
        try:
            if self.runtime:
                await self.runtime.__aexit__(*exc)
        finally:
            self._restore_key()
