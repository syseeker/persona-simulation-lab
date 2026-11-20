"""Render a private mTLS executor config from actual local gateway artifacts.

By default use the maintained native encrypted store and public frozen preset,
without external credential bindings. Optional external context requires an
actual successful credential_refresh_verified observation.
"""

import argparse
import json
import os
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def render(*, gateway_root: Path, destination: Path, evidence: Path | None = None) -> dict:
    from nemo_deployments_plugin.backends.openshell.config import OpenShellExecutorConfig

    tls = gateway_root / "tls"
    paths = {
        "ca_cert_path": tls / "ca.crt",
        "client_cert_path": tls / "client/tls.crt",
        "client_key_path": tls / "client/tls.key",
    }
    registration = gateway_root / "driver/registration.key"
    for path in [*paths.values(), *([registration] if evidence else [])]:
        if not path.is_file():
            raise ValueError(f"Missing local gateway artifact: {path}")
    verified = False
    if evidence:
        proof = json.loads(evidence.read_text())
        verified = proof.get("credential_refresh_verified") is True
        if not verified:
            raise ValueError("Credential refresh evidence does not record a successful actual verification")
    config = yaml.safe_load((HERE / "config.local.yaml").read_text())
    for executor in config["deployments"]["executors"]:
        if executor["name"] != "lab-openshell":
            continue
        selected = executor["config"]
        selected["gateway_endpoint"] = "https://127.0.0.1:17670"
        selected["tls"] = {key: str(path.resolve()) for key, path in paths.items()}
        if evidence:
            selected["gateway_credentials"] = {
                "gateway_id": "persona-lab-openshell",
                "registration_key_file": str(registration.resolve()),
                "profiles": {
                    "lab-preferences": {
                        "workspaces": ["persona-lab"],
                        "credential_keys": ["LAB_CONTEXT_TOKEN"],
                        "profile_workspace": "default",
                    }
                },
                "renewal_mode": "gateway",
                "renewal_interval_seconds": 10,
                "credential_refresh_verified": verified,
            }
        else:
            selected.pop("gateway_credentials", None)
        OpenShellExecutorConfig.model_validate(selected)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        yaml.safe_dump(config, stream, sort_keys=False)
    destination.chmod(0o600)
    return {
        "config": str(destination),
        "external_context_enabled": bool(evidence),
        "credential_refresh_verified": verified,
        "runtime_modified": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gateway-root", type=Path, default=ROOT / ".private/openshell")
    parser.add_argument("--output", type=Path, default=ROOT / ".private/platform/openshell-config.yaml")
    parser.add_argument("--refresh-evidence", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            render(gateway_root=args.gateway_root, destination=args.output, evidence=args.refresh_evidence)
        )
    )
