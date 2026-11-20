"""Offline lifecycle checks: no Platform, runtime or model is contacted."""

import importlib.util
from pathlib import Path
import ssl
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest


PATH = Path(__file__).resolve().parents[1] / "integrations/platform/session_drain.py"
SPEC = importlib.util.spec_from_file_location("lab_session_drain", PATH)
drain = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(drain)
SESSION_UUID = "1ed48234-9da7-4564-abc1-271f9fe078de"
ENTITY_ID = "agent-session-4oorwwUYWwVBEAZhNfAymX"


class NotFoundError(Exception):
    pass


def response(value):
    return SimpleNamespace(data=lambda: value)


class Page:
    def __init__(self, records):
        self.records = records
        self.visited = 0

    async def items(self):
        for record in self.records:
            self.visited += 1
            if self.visited > 200:
                raise AssertionError("Lookup exceeded its 200-item limit")
            yield record


@pytest.fixture
def native(monkeypatch):
    session = SimpleNamespace(
        id=ENTITY_ID,
        entity_id=ENTITY_ID,
        session_uuid=SESSION_UUID,
        name="owned-session",
        deployment_id="immutable-deployment-one",
        status="active",
    )
    deployment = SimpleNamespace(
        id="immutable-deployment-one", name="human-deployment-name", endpoint="https://sandbox.test/agent"
    )
    sequence = []
    client = SimpleNamespace(
        get_session=AsyncMock(return_value=response(session)),
        list_sessions=AsyncMock(return_value=Page([session])),
        list_deployments=AsyncMock(return_value=Page([deployment])),
    )

    async def close(*, name):
        sequence.append(("logical_close", name))
        return response(SimpleNamespace(**{**vars(session), "status": "closed"}))

    client.close_session = AsyncMock(side_effect=close)
    context = ssl.create_default_context()

    class Transport:
        def client_kwargs(self):
            return {"verify": context}

        def target(self, url):
            sequence.append(("target", url))
            return url.replace("https://sandbox.test", "https://127.0.0.1:3000"), {"Host": "sandbox.test"}

    monkeypatch.setitem(
        sys.modules, "nemo_helix_plugin.client.errors", SimpleNamespace(NotFoundError=NotFoundError)
    )
    monkeypatch.setitem(
        sys.modules,
        "nemo_agents_plugin.session_protocol",
        SimpleNamespace(session_id_to_uuid=lambda value: SESSION_UUID if value == ENTITY_ID else "invalid"),
    )
    monkeypatch.setitem(
        sys.modules,
        "nemo_agents_plugin.deployment_routing",
        SimpleNamespace(
            get_deployment_endpoint=lambda item: item.endpoint,
            get_deployment_transport=lambda item: Transport(),
        ),
    )
    return SimpleNamespace(
        session=session, deployment=deployment, client=client, sequence=sequence, context=context
    )


def runtime(monkeypatch, native, *, status=204, error=None):
    real_client = httpx.AsyncClient

    def handler(request):
        native.sequence.append(("runtime_delete", request))
        if error:
            raise error
        return httpx.Response(status, content=b"private response must not escape")

    def factory(**kwargs):
        assert kwargs == {"timeout": 160, "follow_redirects": False, "verify": native.context}
        return real_client(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(drain.httpx, "AsyncClient", factory)


async def test_required_cleanup_uses_native_runtime_id_transport_then_sdk_resource_name(native, monkeypatch):
    runtime(monkeypatch, native)
    result = await drain.close_session(native.client, "owned-session", required_runtime_cleanup=True)
    assert result["runtime_cleanup_confirmed"]
    assert result["runtime_cleanup_status"] == "confirmed"
    assert result["session"].status == "closed"
    assert result["session_identity"] == {
        "resource_name": "owned-session",
        "entity_id": ENTITY_ID,
        "session_uuid": SESSION_UUID,
        "header_identity": SESSION_UUID,
    }
    assert [entry[0] for entry in native.sequence] == ["target", "runtime_delete", "logical_close"]
    request = native.sequence[1][1]
    assert request.method == "DELETE"
    assert str(request.url) == "https://127.0.0.1:3000/agent/v1/sessions/" + ENTITY_ID
    assert request.headers["Host"] == "sandbox.test"
    native.client.close_session.assert_awaited_once_with(name="owned-session")


@pytest.mark.parametrize("status", [200, 202, 301, 404, 502])
async def test_required_cleanup_never_treats_absence_redirect_or_transport_success_as_stop(
    native, monkeypatch, status
):
    runtime(monkeypatch, native, status=status)
    result = await drain.close_session(native.client, "owned-session", required_runtime_cleanup=True)
    assert result["runtime_cleanup_confirmed"] is False
    assert result["session"].status == "active"
    assert result["runtime_cleanup_status"] == ("runtime_missing" if status == 404 else "failed")
    assert "private response" not in result["runtime_cleanup_error"]
    native.client.close_session.assert_not_awaited()
    assert len([entry for entry in native.sequence if entry[0] == "runtime_delete"]) == 1


async def test_timed_out_stop_cannot_release_taint_and_does_not_expose_private_transport(native, monkeypatch):
    runtime(monkeypatch, native, error=httpx.ReadTimeout("secret at https://key:private@host/key.pem"))
    result = await drain.close_session(native.client, "owned-session", required_runtime_cleanup=True)
    assert not result["runtime_cleanup_confirmed"]
    assert result["runtime_cleanup_error"] == "Runtime shutdown failed (ReadTimeout)"
    native.client.close_session.assert_not_awaited()


async def test_uninvoked_ordinary_session_can_close_with_explicit_unconfirmed_absence(native, monkeypatch):
    runtime(monkeypatch, native, status=404)
    result = await drain.close_session(native.client, "owned-session")
    assert result["runtime_cleanup_confirmed"] is False
    assert result["runtime_cleanup_status"] == "runtime_missing"
    assert result["session"].status == "closed"
    native.client.close_session.assert_awaited_once_with(name="owned-session")


async def test_uuid_and_entity_fallback_lookup_resolves_immutable_session_name(native):
    native.client.get_session.side_effect = NotFoundError()
    assert await drain.resolve_session(native.client, SESSION_UUID) is native.session
    assert await drain.resolve_session(native.client, ENTITY_ID) is native.session
    native.client.close_session.assert_not_awaited()
    native.session.session_uuid = "00000000-0000-0000-0000-000000000001"
    with pytest.raises(ValueError, match="does not match"):
        await drain.resolve_session(native.client, ENTITY_ID)


async def test_lookup_is_bounded_and_never_falls_back_on_authentication_failure(native):
    native.client.get_session.side_effect = PermissionError("private authentication error")
    with pytest.raises(PermissionError):
        await drain.resolve_session(native.client, "owned-session")
    native.client.list_sessions.assert_not_awaited()
    native.client.get_session.side_effect = NotFoundError()
    page = Page([SimpleNamespace(name=f"other-{index}") for index in range(201)] + [native.session])
    native.client.list_sessions.return_value = page
    with pytest.raises(ValueError, match="first 200"):
        await drain.resolve_session(native.client, ENTITY_ID)
    assert page.visited == 200


async def test_deployment_name_collision_never_selects_another_runtime(native, monkeypatch):
    runtime(monkeypatch, native)
    native.client.list_deployments.return_value = Page(
        [SimpleNamespace(id="another-id", name="immutable-deployment-one", endpoint="https://wrong.test")]
    )
    result = await drain.close_session(native.client, "owned-session", required_runtime_cleanup=True)
    assert not result["runtime_cleanup_confirmed"] and result["runtime_cleanup_status"] == "failed"
    assert native.sequence == []
    native.client.close_session.assert_not_awaited()


@pytest.mark.parametrize("endpoint", ["https://key:secret@host", "file:///tmp/a", "http://host?secret=key"])
async def test_deployment_endpoint_credentials_or_nonhttp_are_not_requested(native, monkeypatch, endpoint):
    runtime(monkeypatch, native)
    native.deployment.endpoint = endpoint
    result = await drain.close_session(native.client, "owned-session")
    assert not result["runtime_cleanup_confirmed"] and result["runtime_cleanup_status"] == "failed"
    assert native.sequence == []
    native.client.close_session.assert_not_awaited()


async def test_client_url_and_ambiguous_session_identity_are_rejected(native):
    with pytest.raises(ValueError, match="Invalid"):
        await drain.close_session(native.client, "https://untrusted.test/runtime")
    native.client.get_session.assert_not_awaited()
    native.client.get_session.side_effect = NotFoundError()
    native.client.list_sessions.return_value = Page([native.session, native.session])
    with pytest.raises(ValueError, match="ambiguous"):
        await drain.resolve_session(native.client, SESSION_UUID)


def test_legacy_uuid_entity_uses_uuid_header_without_confusing_resource_name(native):
    native.session.id = native.session.entity_id = SESSION_UUID
    native.session.session_uuid = ""
    result = drain.session_identity(native.session)
    assert result["resource_name"] == "owned-session"
    assert result["entity_id"] == result["header_identity"] == SESSION_UUID
