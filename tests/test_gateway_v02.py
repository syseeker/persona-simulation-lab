"""Provider evidence remains native, bounded and free of local credentials."""

import base64
import json

import httpx
import pytest

from learning_lab.inference import Budget, Gateway


async def test_guessed_forbidden_tool_is_blocked_before_runtime_and_keeps_provider_usage(monkeypatch):
    monkeypatch.setattr("learning_lab.inference.load_environment", lambda: None)
    monkeypatch.setenv("LAB_PROXY_BASE_URL", "http://proxy.test/v1")
    monkeypatch.setenv("LAB_PROXY_API_KEY", "local-proxy-test-value-only")

    def provider(request):
        assert [tool["function"]["name"] for tool in json.loads(request.content)["tools"]] == ["search_courses"]
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": None,
            "tool_calls": [{"id": "guessed", "type": "function", "function": {
                "name": "read_file", "arguments": '{"path":"/etc/passwd"}'}}]}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 12, "total_tokens": 22}})

    gateway = Gateway(Budget(1), "live", allowed_tool_names={"search_courses"})
    await gateway._client.aclose()
    gateway._client = httpx.AsyncClient(transport=httpx.MockTransport(provider))
    try:
        with pytest.raises(ValueError, match="outside the application's effective allowlist"):
            await gateway.complete({"model": "fixture", "messages": [], "tools": [
                {"type": "function", "function": {"name": name}} for name in ("read_file", "search_courses")]})
        record = gateway.budget.records[0]
        assert record["status"] == "failed" and record["tool_surface"]["blocked_returned"] == ["read_file"]
        assert record["usage"]["total_tokens"] == 22 and gateway.budget.calls == 1
    finally:
        await gateway._client.aclose()


async def test_gateway_retains_native_proxy_selection_and_switchyard_decision(monkeypatch):
    monkeypatch.setenv("LAB_PROXY_BASE_URL", "http://proxy.test/v1")
    monkeypatch.setenv("LAB_PROXY_API_KEY", "local-proxy-test-value-only")
    decision = {"version": 1, "source": "switchyard", "decision": {"selected_model_id": "openai/efficient"}}

    def provider(request):
        payload = json.loads(request.content)
        assert payload["model"] == "lab-advisor-routed"
        assert payload["max_tokens"] == 1024 and payload["stream"] is False
        return httpx.Response(200, json={"model": "lab-advisor-routed", "choices": [
            {"message": {"role": "assistant", "content": "A catalogue lists courses."}}]},
            headers={"x-litellm-model-name": "openai/efficient", "x-request-id": "native-request",
                     "x-lab-routing-decision": base64.urlsafe_b64encode(json.dumps(decision).encode()).decode()})

    gateway = Gateway(Budget(1), "live", model_route="switchyard")
    await gateway._client.aclose()
    gateway._client = httpx.AsyncClient(transport=httpx.MockTransport(provider))
    try:
        await gateway.complete({"model": "original", "messages": [], "max_tokens": 4000})
        record = gateway.budget.records[0]
        assert record["selected_model"] == "openai/efficient"
        assert record["routing_decision"] == decision
        assert record["provider_request_id"] == "native-request"
        assert record["usage"] is None  # Missing provider accounting is unknown.
        assert gateway.budget.calls == 1
    finally:
        await gateway._client.aclose()


async def test_failed_provider_diagnostic_redacts_actual_process_secret(monkeypatch):
    key = "not-a-real-provider-credential-123456"
    monkeypatch.setenv("LAB_PROXY_BASE_URL", "http://proxy.test/v1")
    monkeypatch.setenv("LAB_PROXY_API_KEY", key)
    gateway = Gateway(Budget(1), "live")
    await gateway._client.aclose()
    gateway._client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request:
        httpx.Response(400, json={"error": {"message": "Rejected supplied key " + key, "code": "bad_model"}})))
    try:
        with pytest.raises(RuntimeError, match="HTTP 400"):
            await gateway.complete({"model": "test", "messages": []})
        record = gateway.budget.records[0]
        assert record["status"] == "failed" and record["http_status"] == 400
        assert record["provider_error"]["code"] == "bad_model"
        assert key not in json.dumps(record)
        assert "usage" not in record
    finally:
        await gateway._client.aclose()
