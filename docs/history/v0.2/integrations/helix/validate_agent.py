"""Validate the managed configuration locally without registering or deploying anything."""

from pathlib import Path
import json

from nemo_agents_plugin.agent_config import load_agent_config
from nemo_agents_plugin.fabric.translator import translate_agent_config
from nemo_fabric import Fabric

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / "agents/learning-advisor/agent.yaml"
config = load_agent_config(path)
runtime = translate_agent_config(config)
plan = Fabric().plan(runtime, base_dir=path.parent)
assert (path.parent / "skills/course-advisor/SKILL.md").read_bytes() == (
    ROOT / "runtime-skills/course-advisor/SKILL.md"
).read_bytes()
print(
    json.dumps(
        {
            "config": str(path),
            "format": config.config_format,
            "adapter": plan.adapter.adapter_id,
            "registered": False,
            "deployed": False,
        }
    )
)
