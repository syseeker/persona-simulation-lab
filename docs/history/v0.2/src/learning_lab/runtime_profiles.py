"""Public integration readiness; checking a profile never installs or starts it."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
from urllib.parse import urlsplit

from .settings import ROOT, load_environment


PROFILE_VERSION = "learning-lab-runtime/v1"
PLATFORM_PINS = {"nemo-helix": "0.10.0", "nemo-fabric": "0.6.1", "nemo-relay": "0.11.0"}
HERMES_PINS = {
    "python": "3.14",
    "hermes_commit": "b200f5bc60e31588ba2cb60e288029c4a54ba5fa",
    "nemo-fabric": "0.6.1",
    "nemo-relay": "0.11.1",
}


def platform_python() -> Path:
    return Path(os.getenv("LAB_PLATFORM_PYTHON", str(ROOT / "integrations/platform/.venv/bin/python")))


def hermes_python() -> Path:
    return Path(os.getenv("LAB_HERMES_PYTHON", str(ROOT / "integrations/hermes/.venv/bin/python")))


def hermes_descriptor_dir() -> Path:
    return hermes_python().parent.parent / "share/nemo-fabric/adapters/hermes"


def hermes_runtime_environment() -> dict[str, str]:
    managed = ROOT / "integrations/hermes/managed"
    if not (managed / "config.yaml").is_file():
        raise ValueError("The explicit Hermes retry policy is missing")
    return {"HERMES_MANAGED_DIR": str(managed), "HERMES_STREAM_RETRIES": "0"}


def openshell_binary() -> Path | None:
    configured = os.getenv("LAB_OPENSHELL_BIN")
    candidates = [configured, shutil.which("openshell"), str(ROOT / ".private/openshell/bin/openshell")]
    return next(
        (Path(candidate) for candidate in candidates if candidate and Path(candidate).is_file()), None
    )


def public_endpoint(value: str, *, remote_https: bool = True) -> str:
    """Reject embedded credentials and tokens instead of accidentally displaying them."""
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Use an HTTP(S) service URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Service URLs cannot contain credentials, queries or fragments")
    if remote_https and parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("Remote Platform connections require HTTPS")
    return value.rstrip("/")


def runtime_profiles() -> dict:
    load_environment()
    proxy = public_endpoint(os.getenv("LAB_PROXY_BASE_URL", "http://127.0.0.1:4000/v1"), remote_https=False)
    remote = os.getenv("LAB_HELIX_REMOTE_URL")
    return {
        "schema": PROFILE_VERSION,
        "profiles": [
            {"id": "local", "label": "Local Deep Agents", "configured": True},
            {
                "id": "hermes",
                "label": "Fabric + Hermes",
                "configured": hermes_python().is_file(),
                "python": str(hermes_python()),
                "pins": HERMES_PINS,
                "setup": "integrations/hermes/bootstrap.py",
            },
            {
                "id": "proxy",
                "label": "LiteLLM + Switchyard",
                "configured": bool(os.getenv("LAB_PROXY_BASE_URL")),
                "endpoint": proxy,
                "key_present": bool(os.getenv("LAB_PROXY_API_KEY")),
                "status": "not_probed",
                "integration": "experimental; exact upstream source commit",
                "setup": "integrations/proxy/compose.yaml",
            },
            {
                "id": "platform-local",
                "label": "Local Helix Platform",
                "configured": platform_python().is_file(),
                "endpoint": public_endpoint(os.getenv("LAB_HELIX_URL", "http://127.0.0.1:8080")),
                "workspace": os.getenv("LAB_HELIX_WORKSPACE", "persona-lab"),
                "pins": PLATFORM_PINS,
                "status": "not_probed",
            },
            {
                "id": "platform-remote",
                "label": "Remote Helix Platform",
                "configured": bool(remote) and platform_python().is_file(),
                "endpoint": public_endpoint(remote) if remote else None,
                "workspace": os.getenv("LAB_HELIX_REMOTE_WORKSPACE", "persona-lab"),
                "key_present": bool(os.getenv("LAB_HELIX_REMOTE_TOKEN")),
                "status": "not_probed",
            },
            {
                "id": "openshell",
                "label": "Agent sandbox in OpenShell",
                "configured": openshell_binary() is not None,
                "cli": str(openshell_binary()) if openshell_binary() else None,
                "status": "not_probed",
                "policy": "integrations/platform/openshell-policy.yaml",
                "limitation": "A CLI on PATH does not establish a ready gateway or an enforced policy.",
            },
        ],
    }


def integration_preflight(profile: str) -> dict:
    selected = next((p for p in runtime_profiles()["profiles"] if p["id"] == profile), None)
    if selected is None:
        raise ValueError("Unknown runtime profile")
    return {
        **selected,
        "ready": False,
        "reason": "Run the profile health probe before using this integration.",
    }
