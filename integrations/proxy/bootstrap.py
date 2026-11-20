"""Fetch exactly the official experimental Switchyard integration source.

This prepares source only. It neither starts a proxy nor contacts an LLM.
"""

from pathlib import Path
import subprocess

REVISION = "9e8408c9e06baf146b63cecda14959a30c34697b"
REPOSITORY = "https://github.com/NVIDIA-NeMo/Switchyard.git"
HERE = Path(__file__).resolve().parent


def main():
    target = HERE / ".upstream"
    target.mkdir(exist_ok=True)
    if not (target / ".git").exists():
        subprocess.run(["git", "init", "--quiet", str(target)], check=True)
        subprocess.run(["git", "-C", str(target), "remote", "add", "origin", REPOSITORY], check=True)
    remote = subprocess.check_output(
        ["git", "-C", str(target), "remote", "get-url", "origin"], text=True
    ).strip()
    if remote != REPOSITORY:
        raise RuntimeError("Existing Switchyard checkout has a different origin; refusing to replace it")
    subprocess.run(["git", "-C", str(target), "fetch", "--depth", "1", "origin", REVISION], check=True)
    subprocess.run(["git", "-C", str(target), "checkout", "--detach", REVISION], check=True)
    actual = subprocess.check_output(["git", "-C", str(target), "rev-parse", "HEAD"], text=True).strip()
    if actual != REVISION:
        raise RuntimeError("Switchyard checkout identity mismatch")
    print(f"Prepared Switchyard {actual}. No proxy or model has been started.")


if __name__ == "__main__":
    main()
