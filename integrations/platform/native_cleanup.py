"""Explicit whole-deployment recovery when strict session drain cannot finish.

Platform resource absence is not sandbox-stop evidence: the pinned deployment
reconciler can remove records without an executor, and its OpenShell backend
does not inspect the native deletion outcome. Capture the native identity before
deletion, then require authenticated native absence on the same gateway.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlsplit
from uuid import UUID

from session_drain import resolve_session, session_identity


WAIT_SECONDS = 60
POLL_SECONDS = 1


class RecoveryBlocked(ValueError):
    """A bounded application-owned explanation safe to show to the learner."""


def _now():
    return datetime.now(timezone.utc).isoformat()


def _save(path: Path, value: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n")
    temp.replace(path)


def _id(value):
    return getattr(value, "id", None) or getattr(value, "entity_id", None)


def _backend_client(client):
    from nemo_helix_plugin.deployments.client import AsyncDeploymentsClient

    return AsyncDeploymentsClient.from_client(client)


def _executor(name: str | None):
    from nemo_deployments_plugin.config import DeploymentsConfig
    from nemo_deployments_plugin.backends.openshell.config import OpenShellExecutorConfig

    config = DeploymentsConfig.get()
    name = name or config.default_executor
    entry = next((entry for entry in config.executors if entry.name == name), None)
    if entry is None or entry.backend != "openshell":
        raise RecoveryBlocked("The owning OpenShell executor is unavailable; recovery remains blocked")
    return name, OpenShellExecutorConfig.model_validate(entry.config)


def _gateway_identity(config):
    endpoint = config.gateway_endpoint.rstrip("/")
    parsed = urlsplit(endpoint)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise RecoveryBlocked("The configured native gateway has an unsafe address")
    tls = config.tls
    # This recovery client supplies no separate bearer/OIDC identity. Its
    # authenticated workspace proof therefore requires pinned mutual TLS.
    if (parsed.scheme != "https" or config.use_insecure() or tls is None
            or not tls.ca_cert_path or not tls.client_cert_path or not tls.client_key_path):
        raise RecoveryBlocked("Native recovery requires configured mutual TLS with a CA, client certificate and key")
    if not Path(tls.client_key_path).is_file():
        raise RecoveryBlocked("The native recovery mutual TLS client key is unavailable")

    def digest(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest() if path else None

    return {
        "endpoint": endpoint,
        "workspace": config.workspace,
        "insecure": config.use_insecure(),
        "ca_sha256": digest(tls.ca_cert_path) if tls else None,
        "client_certificate_sha256": digest(tls.client_cert_path) if tls else None,
    }


def _native_client(config):
    from openshell import SandboxClient, TlsConfig

    _gateway_identity(config)
    tls = None
    if not config.use_insecure():
        source = config.tls
        tls = TlsConfig(
            ca_path=Path(source.ca_cert_path) if source and source.ca_cert_path else None,
            cert_path=Path(source.client_cert_path) if source and source.client_cert_path else None,
            key_path=Path(source.client_key_path) if source and source.client_key_path else None,
        )
    return SandboxClient(config.grpc_target(), tls=tls, timeout=10)


def _identity_labels(workspace, name):
    from nemo_deployments_plugin.backends.labels import (
        DEPLOYMENT_NAME_LABEL, DEPLOYMENT_WORKSPACE_LABEL, MANAGED_BY_KEY,
    )
    from nemo_deployments_plugin.constants import MANAGED_BY_LABEL

    return {MANAGED_BY_KEY: MANAGED_BY_LABEL, DEPLOYMENT_WORKSPACE_LABEL: workspace,
            DEPLOYMENT_NAME_LABEL: name}


def _capture_sandbox(config, labels):
    selector = ",".join(f"{name}={value}" for name, value in labels.items())
    matches, count = [], 0
    with _native_client(config) as native:
        for page in native.list(workspace=config.workspace, label_selector=selector, page_size=100):
            for sandbox in page.items:
                count += 1
                if sandbox.workspace != config.workspace or any(sandbox.labels.get(k) != v for k, v in labels.items()):
                    raise RecoveryBlocked("The gateway returned a sandbox outside the owning deployment")
                UUID(sandbox.id)
                matches.append({"id": sandbox.id, "name": sandbox.name, "workspace": sandbox.workspace,
                                "labels": labels})
                if count >= 200:
                    raise RecoveryBlocked("Native sandbox identity lookup exceeded its bounded scope")
    if len(matches) != 1:
        raise RecoveryBlocked("Capture requires exactly one native sandbox owned by this deployment")
    return matches[0]


def _absent(native, sandbox):
    import grpc

    try:
        current = native.get(sandbox["name"], workspace=sandbox["workspace"])
    except grpc.RpcError as exc:
        if exc.code() != grpc.StatusCode.NOT_FOUND:
            raise
        # GetSandbox deliberately hides permission denial as NOT_FOUND. A
        # successful list in this exact workspace requires the same User role.
        page = next(iter(native.list(workspace=sandbox["workspace"], page_size=1)), None)
        if page is None or any(item.id == sandbox["id"] or item.name == sandbox["name"] for item in page.items):
            raise RecoveryBlocked("Native absence was not confirmed by the authorized workspace")
        return True
    if current.id != sandbox["id"]:
        raise RecoveryBlocked("A replacement sandbox uses the captured name; recovery will not delete it")
    if current.workspace != sandbox["workspace"] or any(current.labels.get(k) != v for k, v in sandbox["labels"].items()):
        raise RecoveryBlocked("The captured native sandbox ownership changed")
    return False


def _remove_native(config, receipt, path):
    from openshell.mutations import DeletionOutcome

    sandbox = receipt["capture"]["sandbox"]
    with _native_client(config) as native:
        if not _absent(native, sandbox):
            receipt["phase"] = "native_delete_requested"
            _save(path, receipt)  # Capture survives cancellation or partial deletion.
            deleted = native.delete(sandbox["name"], workspace=sandbox["workspace"])
            if deleted.sandbox_id != sandbox["id"]:
                raise RecoveryBlocked("Native deletion receipt does not identify the captured sandbox")
            receipt["native_deletion"] = {"sandbox_id": deleted.sandbox_id, "outcome": int(deleted.outcome),
                                          "at": _now()}
            _save(path, receipt)
            if deleted.outcome not in {DeletionOutcome.COMPLETED, DeletionOutcome.ACCEPTED, DeletionOutcome.ALREADY_ABSENT}:
                raise RecoveryBlocked("The native gateway returned an unknown deletion outcome")
        deadline = time.monotonic() + WAIT_SECONDS
        while True:
            if _absent(native, sandbox):
                receipt["native_absence"] = {"sandbox_id": sandbox["id"], "at": _now(),
                                              "proof": "native_get_not_found_and_authorized_workspace_list"}
                receipt["phase"] = "native_absence_confirmed"
                _save(path, receipt)
                return
            if time.monotonic() >= deadline:
                raise TimeoutError("The native sandbox is still present")
            time.sleep(POLL_SECONDS)


async def _current_deployment(client, name, expected_id):
    from nemo_helix_plugin.client.errors import NotFoundError

    try:
        deployment = (await client.get_deployment(name=name)).data()
    except NotFoundError:
        return None
    if _id(deployment) != expected_id:
        raise RecoveryBlocked("The owning deployment name now identifies a different resource")
    return deployment


async def recover_session(client, identity: str, *, receipt_path: Path) -> dict:
    """Retire only the SDK-owned deployment and close its session after proof.

    The bridge supplies an allowlisted local job receipt path. Browser arguments
    never select gateway URLs, sandbox IDs, executor configuration or file paths.
    Failure keeps the session/guard blocked and preserves the resumable capture.
    """
    session = await resolve_session(client, identity)
    identities = session_identity(session)
    scope = {"base_url": str(client.base_url).rstrip("/"), "workspace": client.workspace}
    path = Path(receipt_path)
    result = {"session": session, "session_identity": identities, "runtime_cleanup_confirmed": False,
              "runtime_cleanup_status": "unconfirmed", "runtime_cleanup_error": None,
              "deployment_cleanup_confirmed": False, "deployment_removed": False,
              "recovery_receipt": str(path)}
    receipt = None
    try:
        backend = _backend_client(client)
        if path.is_file():
            receipt = json.loads(path.read_text())
            capture = receipt["capture"]
            if (receipt.get("version") != 1 or capture["platform"] != scope
                    or capture["session"] != identities or capture["deployment"]["id"] != session.deployment_id):
                raise RecoveryBlocked("The recovery receipt does not belong to this Platform session")
            executor_name, config = _executor(capture["executor"])
            if _gateway_identity(config) != capture["gateway"] or executor_name != capture["executor"]:
                raise RecoveryBlocked("The captured native gateway or executor identity changed")
        else:
            page = await client.list_deployments()
            matches, count = [], 0
            async for item in page.items():
                count += 1
                if _id(item) == session.deployment_id:
                    matches.append(item)
                if count >= 200:
                    break
            if len(matches) != 1 or matches[0].deployment_mode != "openshell":
                raise RecoveryBlocked("The session does not identify one available OpenShell deployment")
            deployment = matches[0]
            native_deployment = (await backend.get_deployment(name=deployment.name)).data()
            if native_deployment.workspace != client.workspace:
                raise RecoveryBlocked("The executor deployment belongs to another workspace")
            if not isinstance(_id(native_deployment), str) or not _id(native_deployment):
                raise RecoveryBlocked("The executor deployment has no immutable SDK identity")
            executor_name, config = _executor(native_deployment.executor)
            gateway_identity = _gateway_identity(config)
            labels = _identity_labels(client.workspace, deployment.name)
            sandbox = await asyncio.to_thread(_capture_sandbox, config, labels)
            capture = {"platform": scope, "session": identities,
                       "deployment": {"name": deployment.name, "id": _id(deployment)},
                       "backend_deployment_id": _id(native_deployment), "executor": executor_name,
                       "gateway": gateway_identity, "sandbox": sandbox}
            receipt = {"version": 1, "capture": capture, "phase": "captured", "captured_at": _now()}
            _save(path, receipt)
        # Revalidate both immutable SDK identities before touching the gateway.
        name = capture["deployment"]["name"]
        deployment = await _current_deployment(client, name, capture["deployment"]["id"])
        await _current_deployment(backend, name, capture["backend_deployment_id"])
        # Retire controllers first so their Always drift policy cannot recreate
        # the sandbox after native deletion. Metadata absence is only a fence;
        # the authenticated native proof below is still mandatory.
        if deployment is not None:
            receipt["phase"] = "deployment_delete_requested"
            _save(path, receipt)
            await client.delete_deployment(name=name)
        deadline = time.monotonic() + WAIT_SECONDS
        while True:
            agent = await _current_deployment(client, name, capture["deployment"]["id"])
            executor = await _current_deployment(backend, name, capture["backend_deployment_id"])
            if agent is None and executor is None:
                break
            if time.monotonic() >= deadline:
                raise TimeoutError("Platform deployment retirement is incomplete")
            await asyncio.sleep(POLL_SECONDS)
        receipt.update(phase="platform_retirement_confirmed", platform_retired_at=_now())
        _save(path, receipt)
        await asyncio.to_thread(_remove_native, config, receipt, path)
        # A separately created replacement is outside this recovery's captured
        # ownership. Its different immutable ID must never be deleted here.
        def final_native_check():
            with _native_client(config) as native:
                if not _absent(native, capture["sandbox"]):
                    raise RecoveryBlocked("A native sandbox remains after deployment retirement")
        await asyncio.to_thread(final_native_check)
        receipt.update(phase="deployment_removed", deployment_removed_at=_now())
        _save(path, receipt)
        result.update(runtime_cleanup_confirmed=True, runtime_cleanup_status="confirmed",
                      deployment_cleanup_confirmed=True, deployment_removed=True)
        closed = (await client.close_session(name=identities["resource_name"])).data()
        if session_identity(closed) != identities or closed.status != "closed":
            raise RecoveryBlocked("Platform did not confirm closure of the captured session")
        result["session"] = closed
        receipt.update(phase="completed", completed_at=_now())
        _save(path, receipt)
    except Exception as exc:
        detail = str(exc) if isinstance(exc, RecoveryBlocked) else f"Recovery failed ({type(exc).__name__})"
        result.update(runtime_cleanup_status="failed", runtime_cleanup_error=detail)
        if receipt is not None:
            receipt.update(last_error_type=type(exc).__name__, last_error=detail, last_error_at=_now())
            _save(path, receipt)
    return result
