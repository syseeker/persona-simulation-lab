"""Image-only compatibility patch: Hermes .22.7 and Relay .11.1, no inference."""

import argparse
from pathlib import Path
from runpy import run_path
import subprocess
import tempfile


def install(checkout: Path, python: Path):
    checker = run_path(str(checkout / "pm/pip_check.py"))
    lock = checkout / "uv.lock"
    with tempfile.TemporaryDirectory(prefix="lab-hermes-") as directory:
        override = Path(directory) / "overrides.txt"
        override.write_text("\n".join(checker["override_requirements"](lock)) + "\n")
        subprocess.run(
            [
                "uv",
                "--no-config",
                "pip",
                "install",
                "--prerelease=allow",
                "--python",
                str(python),
                "--overrides",
                str(override),
                "nemo-fabric==0.6.1",
                "nemo-fabric-adapters-hermes[relay]==0.6.1",
                "nemo-relay==0.11.1",
                "mcp==1.30.0",
                "--editable",
                str(checkout),
            ],
            check=True,
        )
    report = subprocess.run(
        ["uv", "--no-config", "pip", "check", "--python", str(python)], capture_output=True, text=True
    )
    if report.returncode and checker["unexpected_incompatibilities"](report.stdout + report.stderr, lock):
        raise RuntimeError("Hermes image dependency check failed; do not deploy this image")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    args = parser.parse_args()
    install(args.checkout.resolve(), args.python.absolute())
