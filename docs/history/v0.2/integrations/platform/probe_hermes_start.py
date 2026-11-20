"""Zero-inference image probe, launched with the image's serving interpreter.

Run inside the exact Hermes image/native sandbox. It deliberately supplies an
unreachable local model origin and never invokes the runtime. Successful startup
with Relay enabled exercises the isolated Hermes imports that failed previously.
"""

import asyncio
import json
import os
from pathlib import Path
import tempfile

import yaml
from nemo_agents_plugin.agent_config import AgentConfig
from nemo_agents_plugin.fabric.translator import translate_agent_config
from nemo_fabric import Fabric


async def main():
    expected = {
        "ADAPTER_PYTHON": "/opt/hermes-venv/bin/python",
        "HERMES_MANAGED_DIR": "/workspace/hermes-managed",
        "HERMES_STREAM_RETRIES": "0",
    }
    if any(os.environ.get(name) != value for name, value in expected.items()):
        raise RuntimeError("Hermes image launcher did not select its exact public runtime settings")
    os.environ["LAB_STARTUP_PROBE_KEY"] = "no-provider-key-and-no-invocation"
    config = yaml.safe_load(Path("/workspace/agent.yaml").read_text())
    if config.get("default_harness") != "hermes":
        raise RuntimeError("This probe requires the packaged Hermes image")
    config["models"]["default"].update(base_url="http://127.0.0.1:9/v1", api_key_env="LAB_STARTUP_PROBE_KEY")
    config["skills"]["paths"] = ["/workspace/skills/course-advisor"]
    with tempfile.TemporaryDirectory(prefix="hermes-start-", dir="/workspace/scratch") as tmp:
        config["environment"]["workspace"] = tmp + "/workspace"
        config["environment"]["artifacts"] = tmp + "/artifacts"
        config["telemetry"]["output_dir"] = tmp + "/relay"
        for name in ("workspace", "artifacts", "relay"):
            Path(tmp, name).mkdir()
        fabric = Fabric()
        translated = translate_agent_config(AgentConfig.model_validate(config))
        doctor = await fabric.doctor(translated, base_dir=Path("/workspace"))
        if str(doctor.status) != "pass":
            raise RuntimeError("Native image Doctor did not pass")
        runtime = await fabric.start_runtime(translated, base_dir=Path("/workspace"))
        await runtime.stop()
    print(
        json.dumps(
            {
                "verified": True,
                "inference_calls": 0,
                "doctor": doctor.to_dict(),
                "relay_enabled_runtime_started_and_stopped": True,
                "runtime_selection": expected,
                "launcher_root_owned": Path("/workspace/.venv/bin/python").stat().st_uid == 0,
                "managed_policy_root_owned": Path("/workspace/hermes-managed/config.yaml").stat().st_uid == 0,
            }
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
