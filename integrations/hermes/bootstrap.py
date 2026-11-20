"""Install exactly Hermes v0.22.7 into a project-local Python 3.14 environment.

Uses the release's dependency override checker and source lock, as the maintained
Fabric integration does. Does not load provider credentials or run inference.
"""

import json
import os
from pathlib import Path
from runpy import run_path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
REVISION = "b200f5bc60e31588ba2cb60e288029c4a54ba5fa"
REPOSITORY = "https://github.com/NousResearch/hermes-agent.git"


def run(*args):
    subprocess.run(list(map(str, args)), check=True, cwd=HERE)


def install(checkout: Path, python: Path):
    checker = run_path(str(checkout / "pm/pip_check.py"))
    source_lock = checkout / "uv.lock"
    with tempfile.TemporaryDirectory(prefix="lab-hermes-") as temporary:
        override = Path(temporary) / "overrides.txt"
        override.write_text("\n".join(checker["override_requirements"](source_lock)) + "\n")
        run(
            "uv",
            "--no-config",
            "pip",
            "install",
            "--prerelease=allow",
            "--python",
            python,
            "--overrides",
            override,
            "nemo-fabric==0.6.1",
            "nemo-fabric-adapters-hermes[relay]==0.6.1",
            "nemo-relay==0.11.1",
            "mcp>=1.30,<2",
            "--editable",
            checkout,
        )
    checked = subprocess.run(
        ["uv", "--no-config", "pip", "check", "--python", str(python)], capture_output=True, text=True
    )
    if checked.returncode and checker["unexpected_incompatibilities"](
        checked.stdout + checked.stderr, source_lock
    ):
        raise RuntimeError("Hermes dependency validation failed; inspect uv pip check in this environment")


def main():
    target = HERE / ".upstream"
    target.mkdir(exist_ok=True)
    if not (target / ".git").exists():
        run("git", "init", "--quiet", target)
        run("git", "-C", target, "remote", "add", "origin", REPOSITORY)
    remote = subprocess.check_output(
        ["git", "-C", str(target), "remote", "get-url", "origin"], text=True
    ).strip()
    if remote != REPOSITORY:
        raise RuntimeError("Existing Hermes source has another origin; refusing to replace it")
    run("git", "-C", target, "fetch", "--depth", "1", "origin", REVISION)
    run("git", "-C", target, "checkout", "--detach", REVISION)
    run("uv", "venv", "--python", "3.14", HERE / ".venv")
    python = HERE / ".venv/bin/python"
    install(target, python)
    command = [
        str(python),
        "-c",
        (
            "import json,sys; from importlib.metadata import version; "
            "assert sys.version_info[:2] == (3,14); "
            "assert version('nemo-fabric') == '0.6.1'; "
            "assert version('nemo-relay') == '0.11.1'; "
            "from nemo_fabric_adapters.hermes import adapter; "
            "print(json.dumps({'python':sys.version.split()[0],'fabric':version('nemo-fabric'),"
            "'relay':version('nemo-relay')}))"
        ),
    ]
    result = json.loads(subprocess.check_output(command, text=True))
    result.update(hermes_commit=REVISION, inference_calls=0, runtime_verified=False)
    (HERE / ".venv/installation.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == "__main__":
    # Keep all dependency caches local to this integration.
    os.environ.setdefault("UV_CACHE_DIR", str(HERE / ".cache/uv"))
    main()
