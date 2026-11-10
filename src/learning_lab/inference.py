"""A budgeted local OpenAI-compatible gateway shared by every model caller."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
import json
import os
import secrets
from typing import Any
import uuid
import time

from aiohttp import web
import httpx

from .settings import base_url, load_environment


class BudgetExceeded(RuntimeError):
    pass


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
    if latest["role"] == "tool":
        data = _tool_payload(latest["content"])
        matches = data.get("matches", []) if isinstance(data, dict) else []
        if matches:
            lines = ["These snapshot listings relate to your stated goal:"]
            for item in matches[:3]:
                c = item["course"]
                lines.append(f"- [{c['title']}]({c['source_url']}) [{c['id']}]: {c['summary']}")
            lines.append(
                "Confirm fees, timetable, prerequisites and availability with the provider. Personal funding eligibility is unknown."
            )
            text = "\n".join(lines)
        else:
            text = "I found no suitable match in this small catalogue. What other topics, days or budget could work?"
        message = {"role": "assistant", "content": text}
    else:
        user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "learning")
        prefs = {"goal": str(user)}
        if "LAB_PREFERENCES=" in str(user):
            prefs = json.loads(str(user).split("LAB_PREFERENCES=", 1)[1].split("\n", 1)[0])
        tools = payload.get("tools", [])
        name = next(
            (t["function"]["name"] for t in tools if t["function"]["name"].endswith("search_courses")), None
        )
        if name:
            message = {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_" + uuid.uuid4().hex,
                        "type": "function",
                        "function": {"name": name, "arguments": json.dumps(prefs)},
                    }
                ],
            }
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
    def __init__(self, budget: Budget, mode: str = "live"):
        self.budget = budget
        self.mode = mode
        self.key = secrets.token_urlsafe(24)
        self.url = ""
        self.tool_rounds = 0
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(50, connect=10))

    async def complete(self, payload: dict, role="assistant") -> dict:
        record = await self.budget.admit(role, self.mode)
        record["model"] = payload.get("model")
        started = time.perf_counter()
        payload = {**payload, "max_tokens": min(int(payload.get("max_tokens", 1024)), 1024), "stream": False}
        # The local gateway is the single admission boundary, including Fabric adapter calls.
        payload.pop("max_completion_tokens", None)
        if role == "assistant" and self.tool_rounds >= MAX_TOOL_ROUNDS:
            payload["tool_choice"] = "none"
            payload["messages"] = [
                {
                    "role": "system",
                    "content": "The four-tool-round budget for this turn is exhausted. Answer using the returned facts, or ask one clarification. Do not invent missing facts.",
                },
                *payload["messages"],
            ]
        try:
            if self.mode == "demo":
                result = scripted_completion(payload)
            else:
                load_environment()
                key = os.getenv("NVIDIA_API_KEY")
                if not key:
                    raise ValueError("NVIDIA_API_KEY is missing from the project .env")
                response = await self._client.post(
                    base_url() + "/chat/completions", json=payload, headers={"Authorization": f"Bearer {key}"}
                )
                if response.status_code >= 400:
                    raise RuntimeError(
                        f"NIM returned HTTP {response.status_code}; check the model, endpoint and access"
                    )
                result = response.json()
            if role == "assistant" and result["choices"][0]["message"].get("tool_calls"):
                if self.tool_rounds >= MAX_TOOL_ROUNDS:
                    raise BudgetExceeded(
                        "Model ignored the four-tool-round limit; execution stopped before another tool"
                    )
                self.tool_rounds += 1
            record.update(
                status="completed",
                usage=result.get("usage") if self.mode == "live" else None,
                latency_ms=round((time.perf_counter() - started) * 1000),
            )
            return result
        except BaseException:
            record["status"] = "cancelled" if asyncio.current_task().cancelling() else "failed"
            raise

    async def _handle(self, request: web.Request) -> web.Response:
        if request.headers.get("Authorization") != f"Bearer {self.key}":
            raise web.HTTPUnauthorized()
        try:
            payload = await request.json()
            if payload.get("stream"):
                return web.json_response(
                    {"error": {"message": "Streaming is disabled in this milestone"}}, status=400
                )
            result = await self.complete(payload)
            return web.json_response(result)
        except BudgetExceeded as exc:
            return web.json_response({"error": {"message": str(exc)}}, status=429)
        except (ValueError, RuntimeError, httpx.HTTPError) as exc:
            return web.json_response({"error": {"message": str(exc)}}, status=502)

    @asynccontextmanager
    async def serving(self):
        app = web.Application(client_max_size=4 * 1024 * 1024)
        app.router.add_post("/v1/chat/completions", self._handle)
        runner = web.AppRunner(app, access_log=None, shutdown_timeout=3)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        self.url = f"http://127.0.0.1:{runner.addresses[0][1]}/v1"
        try:
            yield self
        finally:
            await runner.cleanup()
            await self._client.aclose()
