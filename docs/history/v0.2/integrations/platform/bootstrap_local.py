"""Check, or explicitly start, the local reference Helix services.

No inference, agent registration, deployment, image build or package install.
OpenShell is an operator-owned prerequisite and is never replaced by this script.
"""

import argparse
import base64
import json
import os
from pathlib import Path
import shutil
import secrets
import subprocess
import urllib.error
import urllib.request

from dotenv import dotenv_values

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def health(url: str) -> bool:
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/status", timeout=3) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", action="store_true")
    parser.add_argument("--bind-host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    local_config = ROOT / ".private/platform/openshell-config.yaml"
    parser.add_argument(
        "--config", type=Path, default=local_config if local_config.is_file() else HERE / "config.local.yaml"
    )
    args = parser.parse_args()
    endpoint = f"http://127.0.0.1:{args.port}"
    if args.start and not health(endpoint):
        nemo = HERE / ".venv/bin/nemo"
        if not nemo.is_file():
            raise RuntimeError("Install the locked Platform environment first")
        env = dict(os.environ)
        # A stable local encryption key is required by the actual Secrets API.
        # Persist only under the ignored private runtime file, never in YAML.
        private_env = ROOT / ".private/v02-runtime.env"
        values = dict(dotenv_values(private_env)) if private_env.exists() else {}
        if not values.get("LAB_HELIX_ENCRYPTION_KEY"):
            private_env.parent.mkdir(exist_ok=True)
            existing = private_env.read_text() if private_env.exists() else ""
            key = base64.b64encode(secrets.token_bytes(32)).decode()
            descriptor = os.open(private_env, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            private_env.chmod(0o600)
            with os.fdopen(descriptor, "a") as stream:
                if existing and not existing.endswith("\n"):
                    stream.write("\n")
                stream.write("LAB_HELIX_ENCRYPTION_KEY=" + key + "\n")
            values["LAB_HELIX_ENCRYPTION_KEY"] = key
        env["LAB_HELIX_ENCRYPTION_KEY"] = values["LAB_HELIX_ENCRYPTION_KEY"]
        env["NEMO_TELEMETRY_ENABLED"] = "false"
        subprocess.run(
            [
                str(nemo),
                "services",
                "start",
                "--host",
                args.bind_host,
                "--port",
                str(args.port),
                "--config",
                str(args.config),
                "--instance",
                "persona-lab-v02",
                "--ready-timeout",
                "180",
            ],
            check=True,
            cwd=ROOT,
            env=env,
        )
    print(
        json.dumps(
            {
                "platform_ready": health(endpoint),
                "endpoint": endpoint,
                "openshell_cli_present": bool(shutil.which("openshell"))
                or (ROOT / ".private/openshell/bin/openshell").is_file(),
                "openshell_ready": None,
                "openshell_readiness_status": "not_probed",
                "openshell_setup": "Install the compatible official gateway and SDK, configure its TLS/executor, then verify openshell status.",
                "openshell_install_source": "https://github.com/NVIDIA/OpenShell/blob/v0.1.6/install.sh",
                "inference_calls": 0,
                "registered": False,
                "deployed": False,
            }
        )
    )


if __name__ == "__main__":
    main()
