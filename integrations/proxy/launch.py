"""Configure/validate the local proxy from environment references; start only with --start."""

import argparse
import json
import os
from pathlib import Path
import subprocess

from dotenv import load_dotenv
import yaml

from validate_config import validate

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def configured_environment(source=None) -> dict[str, str]:
    env = dict(os.environ if source is None else source)
    main_model = env.get("NIM_MODEL") or "nvidia/nemotron-3.5-lightning-30b-a3b"
    support_model = env.get("NIM_USER_MODEL") or "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
    for role, model in (
        ("FIXED", main_model),
        ("SUPPORT", support_model),
        ("CAPABLE", main_model),
        ("EFFICIENT", support_model),
    ):
        env.setdefault(f"LAB_{role}_MODEL", "openai/" + model)
        env.setdefault(f"LAB_{role}_API_BASE", env.get("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1"))
        env.setdefault(f"LAB_{role}_API_KEY", env.get("NVIDIA_API_KEY", ""))
    return env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", action="store_true")
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")
    load_dotenv(ROOT / ".private/v02-runtime.env", override=False)
    env = configured_environment()
    result = validate(yaml.safe_load((HERE / "litellm.yaml").read_text()), env)
    if args.start:
        if not (HERE / ".upstream/.git").exists():
            raise RuntimeError("Run integrations/proxy/bootstrap.py to prepare the exact upstream source")
        command = ["docker", "compose", "-f", str(HERE / "compose.yaml"), "up", "--detach", "--wait"]
        if args.build:
            command.append("--build")
        subprocess.run(command, check=True, cwd=ROOT, env=env)
    print(json.dumps({**result, "started": args.start, "endpoint": "http://127.0.0.1:4000/v1"}))


if __name__ == "__main__":
    main()
