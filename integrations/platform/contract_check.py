"""Exercise the installed public Agents SDK against a local HTTP mock transport.

The mock is explicit: no Platform, deployment, sandbox or model is created.
"""

import asyncio
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

import httpx
from nemo_helix_plugin.agents.client import AsyncAgentsClient
from nemo_helix_plugin.client.types import RetryPolicy

sys.path.insert(0, str(Path(__file__).parent))
from bridge import execute, session_identity, versions, PINS


async def main():
    assert versions() == PINS
    captured = []
    empty_intake = False
    session_id = "1ed48234-9da7-4564-abc1-271f9fe078de"
    deployment_fixture = {
        "id": "deployment-one",
        "name": "lab-deployment",
        "status": "running",
        "agent": "lab-agent",
        "config": {
            "default_harness": "deepagents",
            "harnesses": {"deepagents": {"kind": "deepagents"}},
        },
    }

    def page_of(records):
        return {
            "data": records,
            "pagination": {
                "page": 1,
                "page_size": 100,
                "current_page_size": len(records),
                "total_pages": 1,
                "total_results": len(records),
            },
        }

    def handler(request):
        captured.append(request)
        path = request.url.path
        if "/v1/sessions/" in path:
            assert request.method == "DELETE"
            assert path.endswith(session_id)
            return httpx.Response(204)
        if "/intake/" in path:
            if empty_intake:
                return httpx.Response(200, json=page_of([]))
            common = {
                "session_id": session_id,
                "workspace": "persona-lab",
                "started_at": "2026-11-17T00:00:00Z",
            }
            if path.endswith("/traces"):
                result = page_of([{**common, "id": "trace-one", "status": "OK"}])
            elif path.endswith("/spans"):
                result = page_of(
                    [
                        {
                            **common,
                            "span_id": "span-one",
                            "trace_id": "trace-one",
                            "source": "relay",
                            "ingested_at": "2026-11-17T00:00:00Z",
                            "kind": "TOOL",
                            "name": "search_courses",
                            "status": "success",
                        }
                    ]
                )
            else:
                raise AssertionError("Unexpected Intake endpoint")
        elif "/sessions" in path and not path.endswith("/close"):
            result = {
                "id": session_id,
                "name": "lab-session",
                "deployment_id": "deployment-one",
                "status": "active",
            }
        elif path.endswith("/close"):
            result = {
                "id": session_id,
                "name": "lab-session",
                "deployment_id": "deployment-one",
                "status": "closed",
            }
        elif path.endswith("/chat/completions"):
            assert request.headers.get("X-Nemo-Session-Id") == session_id
            result = {"choices": [{"message": {"content": "offline SDK contract response"}}]}
        elif path.endswith("/logs"):
            result = {"data": [], "total_lines": 0, "next_offset": 0}
        elif path.endswith("/deployments") and request.method == "GET":
            result = {
                "data": [deployment_fixture],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "current_page_size": 1,
                    "total_pages": 1,
                    "total_results": 1,
                },
            }
        else:
            result = deployment_fixture
        return httpx.Response(200, json=result)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        async with AsyncAgentsClient(
            base_url="http://127.0.0.1:8080",
            workspace="persona-lab",
            http_client=http,
            owns_http_client=False,
            retry=RetryPolicy(max_retries=0),
        ) as client:
            deployment = await execute(
                client,
                "deploy",
                {"name": "lab-deployment", "agent": "lab-agent", "image": "example/lab:0.2.0"},
            )
            assert deployment["ready"]
            session = await execute(client, "sessions_create", {"deployment": "lab-deployment"})
            assert session["session"]["id"] == session_id
            result = await execute(
                client, "invoke", {"deployment": "lab-deployment", "session_id": session_id, "input": "test"}
            )
            assert result["response"]["choices"][0]["message"]["content"]
            logs = await execute(client, "logs", {"name": "lab-deployment", "session_id": "lab-session"})
            assert logs["intake"]["status"] == "observed"
            assert logs["intake"]["spans"][0]["name"] == "search_courses"
            assert not logs["intake"]["raw_relay_file_exported"]
            # The pinned Hermes adapter owns an independent Relay session UUID.
            # Never scan unrelated workspace records to fill a selected session.
            deployment_fixture["config"] = {
                "default_harness": "hermes",
                "harnesses": {"hermes": {"kind": "hermes"}},
            }
            empty_intake = True
            before = len(captured)
            missing = await execute(client, "logs", {"name": "lab-deployment", "session_id": "lab-session"})
            assert missing["intake"]["status"] == "no_records_observed"
            assert missing["intake"]["correlation"]["status"] == "unsupported"
            assert missing["intake"]["correlation"]["expected_platform_session_uuid"] == session_id
            assert missing["intake"]["correlation"]["native_relay_session_uuid"] is None
            for request in captured[before:]:
                if "/intake/" in request.url.path:
                    assert json.loads(request.url.params["filter"])["session_id"] == session_id
            # Exercise actual SDK resolution/close over its mock transport and
            # the native drain contract over another explicit HTTP mock.
            from nemo_deployments_plugin.endpoint_transport import DIRECT

            async_client = httpx.AsyncClient
            with (
                patch(
                    "nemo_agents_plugin.deployment_routing.get_deployment_endpoint",
                    return_value="http://runtime.test",
                ),
                patch("nemo_agents_plugin.deployment_routing.get_deployment_transport", return_value=DIRECT),
                patch(
                    "session_drain.httpx.AsyncClient",
                    side_effect=lambda **kw: async_client(transport=httpx.MockTransport(handler), **kw),
                ),
            ):
                closed = await execute(
                    client, "sessions_close", {"name": "lab-session", "require_runtime_drain": True}
                )
            assert closed["runtime_cleanup_confirmed"], closed
            assert closed["session"]["status"] == "closed"
    assert session_identity({"name": session_id}) == session_id
    assert any(request.method == "DELETE" and "/v1/sessions/" in request.url.path for request in captured)
    # Exercise the actual workspace/secret/model/environment request models and
    # environment merge rules without registering resources on a real server.
    from configure import configure
    from nemo_agents_plugin.environment_resolution import merge_environment_spec_into_agent_config
    from nemo_helix_plugin.agents.types import EnvironmentSpecInline

    resources = {}
    configured_requests = []

    def configure_handler(request):
        configured_requests.append(request)
        path = request.url.path
        if request.method == "GET":
            if path not in resources:
                return httpx.Response(404, json={"detail": "fixture resource does not exist"})
            return httpx.Response(200, json=resources[path])
        body = json.loads(request.content)
        if path.endswith("/providers"):
            assert body["api_key_secret_name"] == "lab-admission-key"
        result = {
            **body,
            "id": "fixture-id",
            "workspace": "persona-lab",
            "created_at": "2026-11-17T00:00:00Z",
            "updated_at": "2026-11-17T00:00:00Z",
        }
        result.pop("value", None)
        resources[path + "/" + body["name"]] = result
        return httpx.Response(200, json=result)

    os.environ["LAB_DEPLOYMENT_GATEWAY_KEY"] = "offline-fixture-provider-key-123456"
    os.environ["LAB_DEPLOYMENT_PREFERENCES_TOKEN"] = "offline-fixture-preferences-key-654321"
    async with httpx.AsyncClient(transport=httpx.MockTransport(configure_handler)) as http:
        async with AsyncAgentsClient(
            base_url="http://127.0.0.1:8080",
            workspace="persona-lab",
            http_client=http,
            owns_http_client=False,
            retry=RetryPolicy(max_retries=0),
        ) as client:
            result = await configure(
                client,
                {
                    "provider_url": "http://127.0.0.1:8766/v1",
                    "preferences_url": "http://172.17.0.1:8766/v1/lab/preferences",
                },
            )
            assert result["configured"] and not result["ready"]
    for item in resources.values():
        if "environment_spec" not in item:
            continue
        spec = EnvironmentSpecInline.model_validate(item["environment_spec"])
        merged = merge_environment_spec_into_agent_config(
            {
                "config_format": "nemo-agents-spec-v1",
                "mcp": {"servers": {"catalogue": {"transport": "stdio", "url": "fixture"}}},
            },
            spec,
            workspace="persona-lab",
        )
        mode = "openshell" if item["name"].endswith("openshell") else "docker"
        merged.require_runtime_support(mode)
    print(
        json.dumps(
            {
                "status": "passed",
                "kind": "mocked-http-real-installed-sdk",
                "requests": len(captured),
                "configure_requests": len(configured_requests),
                "versions": versions(),
                "inference_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
