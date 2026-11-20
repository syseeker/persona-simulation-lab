"""Close a native Fabric runtime before closing its Helix session record.

The pinned Fabric registry removes a runtime before awaiting its stop. A later
404 therefore cannot confirm cleanup after a timed-out or failed invocation.
Only the owning deployment's positive 204 can release a required drain.
"""

from __future__ import annotations

import re
from urllib.parse import quote, urlsplit
from uuid import UUID

import httpx


RESOURCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}\Z")
LOOKUP_LIMIT = 200


def _identity(value: object) -> str:
    if not isinstance(value, str) or not RESOURCE.fullmatch(value):
        raise ValueError("Invalid Platform session identity")
    return value


def _field(record, key: str):
    return record.get(key) if isinstance(record, dict) else getattr(record, key, None)


def _uuid(value: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, AttributeError, TypeError):
        raise ValueError("Invalid native Platform session UUID") from None


def _entity_uuid(entity_id: str) -> str:
    if entity_id.startswith("agent-session-"):
        from nemo_agents_plugin.session_protocol import session_id_to_uuid

        try:
            return _uuid(session_id_to_uuid(entity_id))
        except (ValueError, TypeError):
            raise ValueError("Invalid native Platform session entity ID") from None
    # Older SDK fixtures and recorded resources used UUID entity IDs directly.
    return _uuid(entity_id)


def session_identity(session) -> dict:
    """Keep resource name, internal runtime ID and invocation UUID distinct."""
    resource = _identity(_field(session, "name"))
    entity_id = _identity(_field(session, "id") or _field(session, "entity_id"))
    alias = _field(session, "entity_id")
    if alias and alias != entity_id:
        raise ValueError("Conflicting native Platform session entity IDs")
    entity_uuid = _entity_uuid(entity_id)
    explicit = _field(session, "session_uuid")
    session_uuid = _uuid(explicit) if explicit else entity_uuid
    if session_uuid != entity_uuid:
        raise ValueError("Native Platform session UUID does not match its entity ID")
    return {
        "resource_name": resource,
        "entity_id": entity_id,
        "session_uuid": session_uuid,
        "header_identity": session_uuid,
    }


async def resolve_session(client, identity: str):
    """Resolve a resource name first, then a bounded exact native-ID lookup."""
    from nemo_helix_plugin.client.errors import NotFoundError

    identity = _identity(identity)
    try:
        session = (await client.get_session(name=identity)).data()
        session_identity(session)
        return session
    except NotFoundError:
        pass
    # Authentication, transport and other failures must never trigger fallback.
    page = await client.list_sessions()
    matches = []
    count = 0
    async for candidate in page.items():
        count += 1
        fields = {_field(candidate, key) for key in ("name", "id", "entity_id", "session_uuid")}
        if identity in fields:
            session_identity(candidate)
            matches.append(candidate)
        if count >= LOOKUP_LIMIT:
            break
    if len(matches) != 1:
        reason = "ambiguous" if matches else "not found in the first 200 records"
        raise ValueError(f"Platform session identity is {reason}")
    return matches[0]


async def _deployment(client, session):
    immutable_id = _field(session, "deployment_id")
    if not isinstance(immutable_id, str) or not immutable_id:
        raise ValueError("Native Platform session has no deployment ID")
    page = await client.list_deployments()
    matches = []
    count = 0
    async for candidate in page.items():
        count += 1
        if immutable_id in (_field(candidate, "id"), _field(candidate, "entity_id")):
            matches.append(candidate)
        if count >= LOOKUP_LIMIT:
            break
    if len(matches) != 1:
        raise ValueError("Owning Platform deployment is missing or ambiguous in the first 200 records")
    return matches[0]


async def close_session(client, identity: str, *, required_runtime_cleanup: bool = False) -> dict:
    """Drain through maintained deployment transport, then SDK logical close.

    Callers supply a session identity only; the trusted SDK session determines
    the immutable deployment and its endpoint. No caller URL is accepted.
    Errors omit response bodies, transport details and credential-bearing URLs.
    """
    if not isinstance(required_runtime_cleanup, bool):
        raise ValueError("required_runtime_cleanup must be a boolean")
    session = await resolve_session(client, identity)
    identities = session_identity(session)
    result = {
        "session": session,
        "session_identity": identities,
        "runtime_cleanup_confirmed": False,
        "runtime_cleanup_status": "unconfirmed",
        "runtime_cleanup_error": None,
    }
    try:
        from nemo_agents_plugin.deployment_routing import (
            get_deployment_endpoint,
            get_deployment_transport,
        )

        deployment = await _deployment(client, session)
        endpoint = get_deployment_endpoint(deployment)
        parsed = urlsplit(endpoint or "")
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Owning Platform deployment has no safe runtime endpoint")
        transport = get_deployment_transport(deployment)
        target = endpoint.rstrip("/") + "/v1/sessions/" + quote(identities["entity_id"], safe="")
        url, headers = transport.target(target)
        async with httpx.AsyncClient(
            timeout=160, follow_redirects=False, **transport.client_kwargs()
        ) as http:
            response = await http.delete(url, headers=headers)
        if response.status_code == 204:
            result["runtime_cleanup_confirmed"] = True
            result["runtime_cleanup_status"] = "confirmed"
        elif response.status_code == 404:
            result["runtime_cleanup_status"] = "runtime_missing"
            result["runtime_cleanup_error"] = "Runtime returned 404; shutdown is unconfirmed"
        else:
            result["runtime_cleanup_status"] = "failed"
            result["runtime_cleanup_error"] = f"Runtime shutdown returned HTTP {response.status_code}"
    except Exception as exc:
        # Native transport can include private TLS paths or URLs in errors.
        result["runtime_cleanup_status"] = "failed"
        result["runtime_cleanup_error"] = f"Runtime shutdown failed ({type(exc).__name__})"
        return result
    if result["runtime_cleanup_confirmed"] or (
        not required_runtime_cleanup and result["runtime_cleanup_status"] == "runtime_missing"
    ):
        result["session"] = (await client.close_session(name=identities["resource_name"])).data()
    return result
