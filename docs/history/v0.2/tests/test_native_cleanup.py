"""Mocked control planes; recovery tests never delete a real sandbox."""

from enum import IntEnum
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


PATH = Path(__file__).resolve().parents[1] / "integrations/platform/native_cleanup.py"
sys.path.insert(0, str(PATH.parent))
SPEC = importlib.util.spec_from_file_location("lab_native_cleanup", PATH)
cleanup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cleanup)
sys.path.pop(0)
SESSION = "1ed48234-9da7-4564-abc1-271f9fe078de"
SANDBOX = "00000000-0000-0000-0000-000000000002"


class NotFoundError(Exception):
    pass


class NativeNotFound(Exception):
    def code(self):
        return "NOT_FOUND"


class Outcome(IntEnum):
    UNSPECIFIED = 0
    COMPLETED = 1
    ACCEPTED = 2
    ALREADY_ABSENT = 3


def response(value):
    return SimpleNamespace(data=lambda: value)


class Page:
    def __init__(self, *records):
        self.records = records

    async def items(self):
        for record in self.records:
            yield record


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "grpc", SimpleNamespace(RpcError=NativeNotFound,
                                                            StatusCode=SimpleNamespace(NOT_FOUND="NOT_FOUND")))
    monkeypatch.setitem(sys.modules, "openshell.mutations", SimpleNamespace(DeletionOutcome=Outcome))
    monkeypatch.setitem(sys.modules, "nemo_helix_plugin.client.errors", SimpleNamespace(NotFoundError=NotFoundError))
    state = SimpleNamespace(exists=True, retired=False, authorized=True, deletes=0, outcome=Outcome.COMPLETED,
                            deletion_error=False, keep_native=False, replacement=False, receipt_id=SANDBOX)
    sequence = []
    session = SimpleNamespace(id=SESSION, entity_id=SESSION, session_uuid=SESSION, name="owned-session",
                              deployment_id="agent-deployment-one", status="active")
    agent = SimpleNamespace(id="agent-deployment-one", name="owned-deployment", deployment_mode="openshell")
    backend = SimpleNamespace(id="executor-deployment-one", name=agent.name, workspace="owned-workspace",
                              executor="owned-executor")
    labels = {"managed-by": "nemo-deployments", "deployment-workspace": "owned-workspace",
              "deployment-name": agent.name}
    native = SimpleNamespace(id=SANDBOX, name="native-owned-sandbox", workspace="native-workspace", labels=labels)
    ca, cert, key = (tmp_path / name for name in ("public-ca.pem", "public-client.pem", "client-key-reference"))
    ca.write_text("offline public CA fixture")
    cert.write_text("offline public client certificate fixture")
    key.touch()  # Only a path reference is needed; this mocked test creates no private-key content.
    tls = SimpleNamespace(ca_cert_path=str(ca), client_cert_path=str(cert), client_key_path=str(key))
    config = SimpleNamespace(gateway_endpoint="https://gateway.test", workspace=native.workspace, tls=tls,
                             use_insecure=lambda: False)
    receipt = tmp_path / "owned-job" / "recovery-receipt.json"

    class Native:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def list(self, *, workspace, page_size, label_selector=None):
            assert workspace == native.workspace
            if not state.authorized:
                raise PermissionError("private gateway auth details")
            sequence.append("native_authorized_list")
            return iter([SimpleNamespace(items=[native] if state.exists else [], next_page_token="")])

        def get(self, name, *, workspace):
            assert name == native.name and workspace == native.workspace
            sequence.append("native_get")
            if not state.exists:
                raise NativeNotFound()
            return native

        def delete(self, name, *, workspace):
            assert name == native.name and workspace == native.workspace
            saved = json.loads(receipt.read_text())
            assert saved["capture"]["sandbox"]["id"] == SANDBOX
            assert saved["phase"] == "native_delete_requested"
            sequence.append("native_delete")
            state.deletes += 1
            if not state.keep_native:
                state.exists = False
            if state.deletion_error:
                state.deletion_error = False
                raise TimeoutError("private path /tls/client.key must not escape")
            return SimpleNamespace(outcome=state.outcome, sandbox_id=state.receipt_id)

    async def get_agent(**kwargs):
        if state.retired:
            raise NotFoundError()
        return response(agent)

    async def get_backend(**kwargs):
        if state.retired:
            raise NotFoundError()
        return response(backend)

    async def delete_agent(**kwargs):
        assert kwargs == {"name": agent.name}
        sequence.append("sdk_delete_deployment")
        state.retired = True
        if state.replacement:
            state.exists = True
            native.id = "00000000-0000-0000-0000-000000000003"

    async def close(**kwargs):
        assert kwargs == {"name": session.name}
        assert not state.exists
        sequence.append("sdk_close_session")
        return response(SimpleNamespace(**{**vars(session), "status": "closed"}))

    client = SimpleNamespace(base_url="https://platform.test", workspace=backend.workspace,
                             list_deployments=AsyncMock(return_value=Page(agent)),
                             get_deployment=AsyncMock(side_effect=get_agent),
                             delete_deployment=AsyncMock(side_effect=delete_agent),
                             close_session=AsyncMock(side_effect=close))
    backend_client = SimpleNamespace(get_deployment=AsyncMock(side_effect=get_backend))
    monkeypatch.setattr(cleanup, "resolve_session", AsyncMock(return_value=session))
    monkeypatch.setattr(cleanup, "_backend_client", lambda _: backend_client)
    monkeypatch.setattr(cleanup, "_executor", lambda _: ("owned-executor", config))
    monkeypatch.setattr(cleanup, "_native_client", lambda _: Native())
    monkeypatch.setattr(cleanup, "_identity_labels", lambda *_: labels)
    monkeypatch.setattr(cleanup, "WAIT_SECONDS", 0)
    return SimpleNamespace(client=client, agent=agent, backend=backend, native=native, config=config,
                           state=state, receipt=receipt, sequence=sequence)


@pytest.mark.parametrize("outcome", [Outcome.COMPLETED, Outcome.ACCEPTED])
async def test_native_identity_capture_precedes_parent_retirement_and_cleanup_precedes_logical_close(fixture, outcome):
    fixture.state.outcome = outcome
    result = await cleanup.recover_session(fixture.client, "owned-session", receipt_path=fixture.receipt)
    assert result["runtime_cleanup_confirmed"] and result["deployment_removed"]
    assert result["session"].status == "closed"
    assert fixture.sequence.index("sdk_delete_deployment") < fixture.sequence.index("native_delete")
    assert fixture.sequence[-1] == "sdk_close_session"
    receipt = json.loads(fixture.receipt.read_text())
    assert receipt["phase"] == "completed"
    assert receipt["native_deletion"]["sandbox_id"] == SANDBOX
    assert receipt["native_absence"]["proof"] == "native_get_not_found_and_authorized_workspace_list"
    assert "key_path" not in json.dumps(receipt)


async def test_capture_survives_ambiguous_native_delete_and_retries_without_rediscovering(fixture):
    fixture.state.deletion_error = True
    first = await cleanup.recover_session(fixture.client, "owned-session", receipt_path=fixture.receipt)
    assert not first["runtime_cleanup_confirmed"]
    assert first["runtime_cleanup_error"] == "Recovery failed (TimeoutError)"
    assert "client.key" not in json.dumps(first, default=str)
    fixture.client.close_session.assert_not_awaited()
    fixture.client.delete_deployment.assert_awaited_once()
    saved = json.loads(fixture.receipt.read_text())
    assert saved["phase"] == "native_delete_requested" and saved["capture"]["sandbox"]["id"] == SANDBOX
    second = await cleanup.recover_session(fixture.client, "owned-session", receipt_path=fixture.receipt)
    assert second["runtime_cleanup_confirmed"] and second["deployment_removed"]
    assert fixture.state.deletes == 1


@pytest.mark.parametrize("outcome", [Outcome.COMPLETED, Outcome.ACCEPTED])
async def test_transport_or_delete_receipt_cannot_replace_actual_native_absence(fixture, outcome):
    fixture.state.outcome, fixture.state.keep_native = outcome, True
    result = await cleanup.recover_session(fixture.client, "owned-session", receipt_path=fixture.receipt)
    assert not result["runtime_cleanup_confirmed"] and not result["deployment_removed"]
    fixture.client.close_session.assert_not_awaited()
    fixture.client.delete_deployment.assert_awaited_once()


async def test_permission_failure_cannot_turn_native_not_found_into_absence_proof(fixture, monkeypatch):
    fixture.state.deletion_error = True
    await cleanup.recover_session(fixture.client, "owned-session", receipt_path=fixture.receipt)
    fixture.state.authorized = False
    result = await cleanup.recover_session(fixture.client, "owned-session", receipt_path=fixture.receipt)
    assert not result["runtime_cleanup_confirmed"]
    fixture.client.close_session.assert_not_awaited()


async def test_restarted_replacement_sandbox_blocks_without_deleting_the_new_identity(fixture):
    fixture.state.replacement = True
    result = await cleanup.recover_session(fixture.client, "owned-session", receipt_path=fixture.receipt)
    assert not result["runtime_cleanup_confirmed"] and not result["deployment_removed"]
    assert fixture.state.deletes == 0
    fixture.client.close_session.assert_not_awaited()


@pytest.mark.parametrize("changed", ["gateway", "scope", "session", "deployment"])
async def test_resumed_recovery_rejects_changed_scope_or_immutable_identity_before_mutation(fixture, changed):
    fixture.state.keep_native = True
    await cleanup.recover_session(fixture.client, "owned-session", receipt_path=fixture.receipt)
    assert fixture.state.deletes == 1
    if changed == "gateway":
        fixture.config.gateway_endpoint = "https://different-gateway.test"
    elif changed == "scope":
        fixture.client.workspace = "different-workspace"
    elif changed == "session":
        cleanup.resolve_session.return_value.deployment_id = "another-deployment"
    else:
        fixture.state.retired = False
        fixture.agent.id = "another-deployment"
    result = await cleanup.recover_session(fixture.client, "owned-session", receipt_path=fixture.receipt)
    assert not result["runtime_cleanup_confirmed"] and fixture.state.deletes == 1
    fixture.client.close_session.assert_not_awaited()


async def test_missing_initial_native_identity_cannot_recover_from_control_plane_metadata_only(fixture):
    fixture.state.exists = False
    result = await cleanup.recover_session(fixture.client, "owned-session", receipt_path=fixture.receipt)
    assert not result["runtime_cleanup_confirmed"] and not fixture.receipt.exists()
    fixture.client.close_session.assert_not_awaited()


async def test_native_delete_receipt_for_another_sandbox_never_closes_the_session(fixture):
    fixture.state.receipt_id = "00000000-0000-0000-0000-000000000003"
    result = await cleanup.recover_session(fixture.client, "owned-session", receipt_path=fixture.receipt)
    assert not result["runtime_cleanup_confirmed"]
    assert "does not identify" in result["runtime_cleanup_error"]
    fixture.client.close_session.assert_not_awaited()


async def test_logical_close_retry_reuses_proof_after_both_sdk_deployments_have_disappeared(fixture):
    original = fixture.client.close_session.side_effect
    first_close = True

    async def close(**kwargs):
        nonlocal first_close
        if first_close:
            first_close = False
            raise TimeoutError("private SDK connection detail")
        return await original(**kwargs)

    fixture.client.close_session.side_effect = close
    first = await cleanup.recover_session(fixture.client, "owned-session", receipt_path=fixture.receipt)
    assert first["runtime_cleanup_confirmed"] and first["deployment_removed"]
    assert first["session"].status == "active"
    assert json.loads(fixture.receipt.read_text())["phase"] == "deployment_removed"
    second = await cleanup.recover_session(fixture.client, "owned-session", receipt_path=fixture.receipt)
    assert second["runtime_cleanup_confirmed"] and second["session"].status == "closed"
    assert fixture.state.deletes == 1
    fixture.client.delete_deployment.assert_awaited_once()


@pytest.mark.parametrize("missing", ["plaintext", "insecure", "tls", "ca", "client_certificate", "client_key"])
async def test_recovery_requires_pinned_mutual_tls_before_native_lookup_or_destructive_action(fixture, missing):
    if missing == "plaintext":
        fixture.config.gateway_endpoint = "http://gateway.test"
    elif missing == "insecure":
        fixture.config.use_insecure = lambda: True
    elif missing == "tls":
        fixture.config.tls = None
    elif missing == "ca":
        fixture.config.tls.ca_cert_path = None
    elif missing == "client_certificate":
        fixture.config.tls.client_cert_path = None
    else:
        fixture.config.tls.client_key_path = None
    result = await cleanup.recover_session(fixture.client, "owned-session", receipt_path=fixture.receipt)
    assert not result["runtime_cleanup_confirmed"]
    assert "mutual TLS" in result["runtime_cleanup_error"]
    assert fixture.sequence == [] and not fixture.receipt.exists()
    fixture.client.delete_deployment.assert_not_awaited()
    fixture.client.close_session.assert_not_awaited()
