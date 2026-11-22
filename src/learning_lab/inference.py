"""A budgeted local OpenAI-compatible gateway shared by every model caller."""

from __future__ import annotations

import asyncio
import base64
import binascii
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import math
import os
import secrets
from pathlib import Path
from typing import Any, Iterable
import uuid
import time

from aiohttp import web
import httpx

from .settings import base_url, load_environment


class BudgetExceeded(RuntimeError):
    pass


class ProviderRateLimited(RuntimeError):
    """An actual upstream HTTP 429, eligible only for explicit bounded recovery."""

    def __init__(self, message, retry_after_seconds=None):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


def _retry_after_seconds(value):
    if not value:
        return None
    try:
        if str(value).isdigit():
            return float(value)
        date = parsedate_to_datetime(value)
        if date.tzinfo is None:
            return None
        return max(0.0, (date - datetime.now(timezone.utc)).total_seconds())
    except (ValueError, TypeError, OverflowError):
        return None


def _rate_limit_headers(headers):
    # Capture only quota/wait metadata received from this HTTP hop. Cookies,
    # authorization and arbitrary response headers never enter this record.
    allowed = {'retry-after', 'ratelimit-limit', 'ratelimit-remaining', 'ratelimit-reset',
               'x-ratelimit-limit-requests', 'x-ratelimit-remaining-requests', 'x-ratelimit-reset-requests',
               'x-ratelimit-limit-tokens', 'x-ratelimit-remaining-tokens', 'x-ratelimit-reset-tokens'}
    from .evidence import sanitize
    result = {}
    for name, value in headers.items():
        if name.lower() not in allowed:
            continue
        for env_name, secret in os.environ.items():
            if any(word in env_name.upper() for word in ('KEY', 'TOKEN', 'SECRET', 'PASSWORD')) and len(secret) >= 8:
                value = value.replace(secret, '[redacted]')
        result[name.lower()] = sanitize(value[:256])
    return result


MAX_TOOL_ROUNDS = 4


@dataclass
class Budget:
    limit: int = 120
    calls: int = 0
    records: list[dict] = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def admit(self, role: str, mode: str) -> dict:
        async with self.lock:
            if self.calls >= self.limit:
                raise BudgetExceeded(
                    f"Run stopped at the {self.limit}-call budget, including judges and retries"
                )
            self.calls += 1
            record = {"call": self.calls, "role": role, "mode": mode, "status": "started"}
            self.records.append(record)
            return record


def _tool_payload(content: Any) -> Any:
    if isinstance(content, str):
        try:
            return _tool_payload(json.loads(content))
        except json.JSONDecodeError:
            return content
    if isinstance(content, list) and content and isinstance(content[0], dict) and "text" in content[0]:
        return _tool_payload(content[0]["text"])
    return content


def scripted_completion(payload: dict) -> dict:
    """Explicitly labelled offline demonstration of the real harness and tools."""
    messages = payload["messages"]
    latest = messages[-1]
    user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "learning")
    prefs = {"goal": str(user)}
    if "LAB_PREFERENCES=" in str(user):
        prefs = json.loads(str(user).split("LAB_PREFERENCES=", 1)[1].split("\n", 1)[0])
    names = {t["function"]["name"] for t in payload.get("tools", [])}

    def call(name, arguments):
        return {"role": "assistant", "content": None, "tool_calls": [{
            "id": "call_" + uuid.uuid4().hex, "type": "function",
            "function": {"name": name, "arguments": json.dumps(arguments)},
        }]}

    def course_result(value, depth=0):
        if depth > 6:
            return None
        if isinstance(value, str) and value.startswith("<untrusted_tool_result"):
            # Hermes labels real MCP output as untrusted data. Decode only the
            # returned JSON segment; never adopt its text as executable policy.
            start = value.find("\n\n{")
            if start >= 0:
                return course_result(value[start + 2:].rsplit("\n</untrusted_tool_result>", 1)[0], depth + 1)
        value = _tool_payload(value)
        if isinstance(value, dict):
            matches = value.get("matches")
            if isinstance(matches, list) and "query" not in value and "total_available" not in value:
                if not matches or all(isinstance(item, dict) and "course" in item for item in matches):
                    return value
            for key in ("result", "results", "content", "output"):
                if key in value:
                    found = course_result(value[key], depth + 1)
                    if found is not None:
                        return found
        if isinstance(value, list):
            for item in value:
                found = course_result(item, depth + 1)
                if found is not None:
                    return found
        return None

    data = _tool_payload(latest["content"]) if latest["role"] == "tool" else None
    deferred = data.get("tools") if isinstance(data, dict) else None
    qualified = next((name for name in deferred if "catalogue" in name and name.endswith("search_courses")), None) if isinstance(deferred, dict) else None
    if qualified and "tool_describe" in names and "results" in data:
        # Hermes exposes maintained deferred-tool bridge schemas. Discover the
        # actual server name and schema instead of fabricating a native call.
        message = call("tool_describe", {"names": [qualified]})
    elif qualified and "tool_call" in names:
        message = call("tool_call", {"calls": [{"name": qualified, "arguments": prefs}]})
    elif latest["role"] == "tool":
        facts = course_result(data)
        matches = facts.get("matches", []) if facts is not None else []
        if matches:
            lines = ["These snapshot listings relate to your stated goal:"]
            for item in matches[:3]:
                c = item["course"]
                lines.append(f"- [{c['title']}]({c['source_url']}) [{c['id']}]: {c['summary']}")
            lines.append(
                "Confirm fees, timetable, prerequisites and availability with the provider. Personal funding eligibility is unknown."
            )
            text = "\n".join(lines)
        elif facts is not None:
            text = "I found no suitable match in this small catalogue. What other topics, days or budget could work?"
        else:
            text = "[ERROR: Offline scripted harness did not return catalogue facts; inspect the saved tool evidence]"
        message = {"role": "assistant", "content": text}
    else:
        name = next((name for name in names if name.endswith("search_courses")), None)
        if name:
            message = call(name, prefs)
        elif "tool_search" in names:
            message = call("tool_search", {"queries": ["catalogue search courses"], "limit": 3})
        else:
            message = {
                "role": "assistant",
                "content": "Offline scripted response; configure NIM for generated conversations.",
            }
    return {
        "id": "demo-" + uuid.uuid4().hex,
        "object": "chat.completion",
        "created": 0,
        "model": payload.get("model", "offline-scripted"),
        "choices": [
            {
                "index": 0,
                "message": message,
                "finish_reason": "tool_calls" if message.get("tool_calls") else "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


class Gateway:
    def __init__(self, budget: Budget, mode: str = "live", model_route: str = "fixed",
                 allowed_tool_names: Iterable[str] | None = None, *, proxy_url: str | None = None,
                 assistant_alias: str | None = None, on_request=None, request_timeout: float = 50,
                 evidence_dir: Path | None = None, fail_on_truncated_output: bool = False,
                 rate_limit_retry_delays: tuple[float, ...] = ()):
        self.budget = budget
        self.mode = mode
        if model_route not in {"fixed", "switchyard"}:
            raise ValueError("Choose fixed or switchyard model routing")
        self.model_route = model_route
        if assistant_alias not in {None, 'lab-advisor-fixed', 'lab-advisor-candidate', 'lab-advisor-capable', 'lab-advisor-routed', 'lab-support'}:
            raise ValueError('Choose an allowlisted advisor alias')
        self.proxy_url, self.assistant_alias, self.on_request = proxy_url, assistant_alias, on_request
        self.key = secrets.token_urlsafe(24)
        self.url = ""
        self.tool_rounds = 0
        # Optional application-owned schema boundary. Some maintained harness
        # adapters gate execution but still advertise their built-in tools.
        if isinstance(allowed_tool_names, str):
            raise ValueError("Supply allowed tool names as a collection, not a string")
        self.allowed_tool_names = frozenset(allowed_tool_names) if allowed_tool_names is not None else None
        if not 1 <= request_timeout <= 300:
            raise ValueError('Model requests must have a one-to-300-second timeout')
        self.request_timeout = request_timeout
        self.evidence_dir = evidence_dir
        self.fail_on_truncated_output = fail_on_truncated_output
        delays = tuple(rate_limit_retry_delays)
        if len(delays) > 2 or any(isinstance(delay, bool) or not isinstance(delay, (int, float))
                                 or not math.isfinite(delay) or not 0 < delay <= 60 for delay in delays):
            raise ValueError('Configure at most two rate-limit waits, each above zero and at most 60 seconds')
        self.rate_limit_retry_delays = delays
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(request_timeout, connect=10))

    def configuration(self):
        """Application controls, distinct from downstream LiteLLM/provider settings."""
        return {
            'schema': 'citizen-gateway-config/v1', 'mode': self.mode,
            'attempt_limit': self.budget.limit, 'output_token_ceiling': 1024,
            'tool_round_limit_per_turn': MAX_TOOL_ROUNDS, 'request_timeout_seconds': self.request_timeout,
            'connect_timeout_seconds': 10, 'provider_retries': 0,
            'model_route': self.model_route, 'assistant_alias': self.assistant_alias,
            'support_alias': 'lab-support', 'allowed_tool_names': sorted(self.allowed_tool_names)
            if self.allowed_tool_names is not None else None,
            'schema_filter_owner': 'application gateway', 'buffered_upstream_response': True,
            'fail_on_truncated_output': self.fail_on_truncated_output,
            'application_rate_limit_recovery': {
                'enabled': self.mode == 'live' and bool(self.rate_limit_retry_delays),
                'status_codes': [429], 'retry_delays_seconds': list(self.rate_limit_retry_delays),
                'max_retries': len(self.rate_limit_retry_delays), 'maximum_wait_seconds': 60,
                'attempts_count_toward_budget': True,
                'total_request_deadline_seconds': self.request_timeout,
                'scope': 'Assistant calls only; SDK/provider retries remain disabled.',
            },
        }

    def capture(self, name, value, *, append=False):
        if self.evidence_dir is not None:
            from .evidence import save_evidence
            save_evidence(self.evidence_dir / name, value, append=append)

    async def complete(self, payload: dict, role="assistant", *, evidence_context: dict | None = None) -> dict:
        delays = self.rate_limit_retry_delays if self.mode == 'live' and role == 'assistant' else ()
        deadline = time.monotonic() + self.request_timeout if delays else None
        logical_id = str(uuid.uuid4()) if delays else None
        previous = None
        waited = None
        for attempt in range(len(delays) + 1):
            record = await self.budget.admit(role, self.mode)
            if evidence_context:
                record.update({key: evidence_context[key] for key in
                               ('control_request_id', 'thread_id', 'transport', 'public_turn') if key in evidence_context})
            if delays:
                record.update(logical_request_id=logical_id, attempt=attempt + 1, retry_of_call=previous)
                if waited is not None:
                    record['retry_wait_seconds'] = waited
            try:
                return await self._complete_admitted(payload, role, record, deadline=deadline)
            except ProviderRateLimited as exc:
                if attempt == len(delays):
                    if delays:
                        record['retry_status'] = 'exhausted'
                    raise
                if self.budget.calls >= self.budget.limit:
                    record['retry_status'] = 'budget_exhausted'
                    raise BudgetExceeded('No call budget remains for a rate-limit retry') from exc
                wait = max(delays[attempt], exc.retry_after_seconds or 0)
                if wait > 60:
                    record['retry_status'] = 'provider_wait_exceeds_bound'
                    raise
                if wait >= deadline - time.monotonic():
                    record['retry_status'] = 'request_deadline_exhausted'
                    raise
                record.update(retry_status='scheduled', retry_delay_seconds=wait)
            except BaseException as exc:
                if record['status'] == 'started':
                    record.update(status='cancelled' if isinstance(exc, asyncio.CancelledError) else 'failed',
                                  error_type=type(exc).__name__)
                raise
            finally:
                # A 429 receipt is durable before waiting. A cancellation during
                # that wait cannot create another model attempt or repeat tools.
                self.capture('gateway-calls.jsonl', record, append=True)
            previous = record['call']
            wait_started = time.monotonic()
            await asyncio.sleep(wait)
            waited = round(time.monotonic() - wait_started, 3)

    async def _complete_admitted(self, payload: dict, role: str, record: dict, *, deadline=None) -> dict:
        record["model"] = payload.get("model")
        started = time.perf_counter()
        # Fabric's maintained OpenAI adapter supplies max_completion_tokens;
        # NIM expects max_tokens. Preserve the configured (possibly lower)
        # limit rather than discarding it while translating the field name.
        try:
            limits = [1024, *[int(payload[name]) for name in ('max_tokens', 'max_completion_tokens')
                             if payload.get(name) is not None]]
            if min(limits) < 1:
                raise ValueError('Output token limits must be positive')
        except (ValueError, TypeError) as exc:
            record.update(status='failed', error_type='ValueError', latency_ms=0)
            raise ValueError('Output token limits must be positive integers') from exc
        payload = {**payload, "max_tokens": min(limits), "stream": False}
        record['output_token_limit'] = payload['max_tokens']
        # The local gateway is the single admission boundary, including Fabric adapter calls.
        payload.pop("max_completion_tokens", None)
        if role == "assistant" and self.allowed_tool_names is not None:
            received = payload.get("tools") or []
            def name(tool):
                return tool["function"].get("name") if isinstance(tool, dict) and isinstance(tool.get("function"), dict) else None
            names = [name(tool) for tool in received]
            exposed = [tool for tool in received if name(tool) in self.allowed_tool_names]
            if exposed:
                payload["tools"] = exposed
            else:
                payload.pop("tools", None)
            record["tool_surface"] = {
                "source": "application_allowlist", "received": names,
                "exposed": [tool["function"]["name"] for tool in exposed],
                "withheld": [name for name in names if name not in self.allowed_tool_names],
            }
        if role == "assistant" and self.tool_rounds >= MAX_TOOL_ROUNDS:
            # Some providers serialize a forbidden tool call as XML when tool
            # schemas remain present with tool_choice=none. Withdraw the tool
            # surface for this final response; malformed output still fails validation.
            payload.pop("tools", None)
            payload.pop("tool_choice", None)
            if "tool_surface" in record:
                record["tool_surface"]["exposed"] = []
                record["tool_surface"]["limit_reached"] = True
            payload["messages"] = [
                {
                    "role": "system",
                    "content": "The four-tool-round budget for this turn is exhausted. Answer using the returned facts, or ask one clarification. Do not invent missing facts.",
                },
                *payload["messages"],
            ]
        try:
            # Capture the final provider-visible schema after allowlist/round-limit
            # filtering. This is not the server's MCP discovery response.
            self.capture('gateway-effective-config.json', self.configuration())
            self.capture('provider-tool-schemas.jsonl', {
                'call': record['call'], 'role': role, 'tools': payload.get('tools', []),
                'tool_choice': payload.get('tool_choice'), 'mode': self.mode,
                'schema': 'OpenAI chat completions tools',
                'context': {key: record[key] for key in ('control_request_id', 'thread_id', 'public_turn') if key in record},
            }, append=True)
            if self.mode == "demo":
                result = scripted_completion(payload)
            else:
                load_environment()
                proxy = (self.proxy_url if self.proxy_url is not None else os.getenv("LAB_PROXY_BASE_URL", "")).rstrip("/")
                if self.model_route == "switchyard" and not proxy:
                    raise ValueError("Switchyard requires LAB_PROXY_BASE_URL; no direct-provider fallback was used")
                key = os.getenv("LAB_PROXY_API_KEY") if proxy else os.getenv("NVIDIA_API_KEY")
                if not key:
                    raise ValueError("Configure LAB_PROXY_API_KEY" if proxy else "NVIDIA_API_KEY is missing from the project .env")
                endpoint = proxy or base_url()
                record["provider_route"] = "litellm" if proxy else "nim-direct"
                if proxy:
                    payload["model"] = (
                        self.assistant_alias if role == 'assistant' and self.assistant_alias else
                        "lab-advisor-routed" if role == "assistant" and self.model_route == "switchyard"
                        else "lab-advisor-fixed" if role == "assistant" else "lab-support"
                    )
                record["requested_model"] = payload["model"]
                if self.on_request:
                    await self.on_request(payload, role, record)
                remaining = self.request_timeout if deadline is None else deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('The total model-request deadline expired before dispatch')
                async with asyncio.timeout(remaining):
                    response = await self._client.post(
                        endpoint + "/chat/completions", json=payload,
                        headers={"Authorization": f"Bearer {key}"},
                    )
                record['http_status'] = response.status_code
                record['rate_limit_headers'] = _rate_limit_headers(response.headers)
                record['rate_limit_header_source'] = record['provider_route']
                if response.status_code >= 400:
                    from .evidence import sanitize
                    try:
                        detail = response.json().get("error", {})
                        safe_detail = {k: str(detail[k])[:800] for k in ("message", "type", "code") if k in detail}
                        # Provider diagnostics sometimes quote configuration. Remove
                        # actual process credentials as well as common key forms.
                        for field, value in safe_detail.items():
                            for name, secret in os.environ.items():
                                if any(word in name.upper() for word in ("KEY", "TOKEN", "SECRET", "PASSWORD")) and len(secret) >= 8:
                                    value = value.replace(secret, "[redacted]")
                            safe_detail[field] = value
                        record["provider_error"] = sanitize(safe_detail)
                    except (ValueError, TypeError, AttributeError):
                        record["provider_error"] = {"message": "Non-JSON provider error; inspect local proxy logs"}
                    record["http_status"] = response.status_code
                    message = f"{'LiteLLM' if proxy else 'NIM'} returned HTTP {response.status_code}; check the model, endpoint and access"
                    if response.status_code == 429:
                        retry_after = _retry_after_seconds(response.headers.get('retry-after'))
                        if retry_after is not None:
                            record['retry_after_seconds'] = retry_after
                        raise ProviderRateLimited(message, retry_after)
                    raise RuntimeError(message)
                result = response.json()
                record["selected_model"] = response.headers.get("x-litellm-model-name") or result.get("model")
                record["routing"] = self.model_route if role == "assistant" else "fixed-support"
                record["provider_request_id"] = response.headers.get("x-request-id")
                native_decision = response.headers.get("x-lab-routing-decision", "")
                if native_decision and len(native_decision) <= 8192:
                    try:
                        decoded = json.loads(base64.urlsafe_b64decode(native_decision))
                        if decoded.get("version") == 1 and decoded.get("source") == "switchyard" and isinstance(decoded.get("decision"), dict):
                            from .evidence import sanitize
                            record["routing_decision"] = sanitize(decoded)
                    except (ValueError, TypeError, binascii.Error):
                        record["routing_notice"] = "The proxy returned an invalid native routing evidence header"
            # Provider usage is evidence even if its returned tool call is invalid.
            record["usage"] = result.get("usage") if self.mode == "live" else None
            record['finish_reason'] = result['choices'][0].get('finish_reason')
            if role == 'assistant' and self.fail_on_truncated_output and record['finish_reason'] == 'length':
                raise ValueError('Advisor output reached its token ceiling; no partial proposal was released')
            if role == "assistant" and self.allowed_tool_names is not None:
                effective = set(record["tool_surface"]["exposed"])
                returned = [call.get("function", {}).get("name")
                            for choice in result.get("choices", [])
                            for call in choice.get("message", {}).get("tool_calls", [])]
                blocked = [name for name in returned if name not in effective]
                if blocked:
                    record["tool_surface"]["blocked_returned"] = blocked
                    raise ValueError("Model requested a tool outside the application's effective allowlist")
            if role == "assistant" and result["choices"][0]["message"].get("tool_calls"):
                if self.tool_rounds >= MAX_TOOL_ROUNDS:
                    raise BudgetExceeded(
                        "Model ignored the four-tool-round limit; execution stopped before another tool"
                    )
                self.tool_rounds += 1
            record.update(
                status="completed",
                finish_reason=result['choices'][0].get('finish_reason'),
                usage=result.get("usage") if self.mode == "live" else None,
                latency_ms=round((time.perf_counter() - started) * 1000),
            )
            return result
        except BaseException as exc:
            record["status"] = "cancelled" if asyncio.current_task().cancelling() else "failed"
            record["error_type"] = type(exc).__name__
            record["latency_ms"] = round((time.perf_counter() - started) * 1000)
            raise

    async def _handle(self, request: web.Request) -> web.Response:
        if request.headers.get("Authorization") != f"Bearer {self.key}":
            raise web.HTTPUnauthorized()
        try:
            payload = await request.json()
            requested_stream = bool(payload.get("stream"))
            result = await self.complete(payload)
            if requested_stream:
                # Hermes consumes SSE even when the application presents a buffered
                # reply. Admit and complete one bounded upstream call, then project
                # its exact structured output into the public OpenAI chunk format.
                response = web.StreamResponse(headers={"Content-Type": "text/event-stream",
                                                       "Cache-Control": "no-cache"})
                await response.prepare(request)
                choice = result["choices"][0]
                message = choice["message"]
                delta = {"role": message.get("role", "assistant")}
                if message.get("content") is not None:
                    delta["content"] = message["content"]
                if message.get("tool_calls"):
                    delta["tool_calls"] = [{"index": index, **call}
                                           for index, call in enumerate(message["tool_calls"])]
                base = {key: result[key] for key in ("id", "created", "model") if key in result}
                base["object"] = "chat.completion.chunk"
                chunks = [
                    {**base, "choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
                    {**base, "choices": [{"index": 0, "delta": {},
                                           "finish_reason": choice.get("finish_reason", "stop")}],
                     "usage": result.get("usage")},
                ]
                for chunk in chunks:
                    await response.write(("data: " + json.dumps(chunk) + "\n\n").encode())
                await response.write(b"data: [DONE]\n\n")
                await response.write_eof()
                return response
            return web.json_response(result)
        except BudgetExceeded as exc:
            # This workload cannot recover by waiting. A non-retryable response
            # prevents a harness SDK from retrying an exhausted application run.
            return web.json_response({"error": {"message": str(exc), "code": "lab_budget_exhausted"}}, status=400)
        except (ValueError, RuntimeError, TimeoutError, httpx.HTTPError) as exc:
            return web.json_response({"error": {"message": str(exc), "code": "lab_call_failed"}}, status=400)

    @asynccontextmanager
    async def serving(self, *, port: int = 0):
        app = web.Application(client_max_size=4 * 1024 * 1024)
        app.router.add_post("/v1/chat/completions", self._handle)
        runner = web.AppRunner(app, access_log=None, shutdown_timeout=3)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", port)
        await site.start()
        self.url = f"http://127.0.0.1:{runner.addresses[0][1]}/v1"
        try:
            self.capture('gateway-effective-config.json', self.configuration())
            if self.evidence_dir is not None and self.mode == 'live':
                from .proxy_capture import capture_proxy
                load_environment()
                endpoint = self.proxy_url if self.proxy_url is not None else os.getenv('LAB_PROXY_BASE_URL', '')
                if endpoint:
                    await capture_proxy(self.evidence_dir, endpoint)
            yield self
        finally:
            await runner.cleanup()
            await self._client.aclose()
