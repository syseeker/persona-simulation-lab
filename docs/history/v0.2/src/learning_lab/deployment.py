"""Helix SDK isolation and explicit Platform operations for the UI and CLI.

No Platform is started, agent registered, image published or workload invoked by
importing this module or inspecting readiness. Secrets travel only in the child
environment, never in its JSON protocol or returned profile metadata.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import hmac
import json
import os
from pathlib import Path
import re
from typing import Literal

from aiohttp import web

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .runtime_profiles import PLATFORM_PINS, platform_python, public_endpoint
from .settings import ROOT, load_environment


OPERATIONS = frozenset(
    {
        "status",
        "register",
        "agent",
        "deploy",
        "deployment",
        "logs",
        "sessions_create",
        "invoke",
        "sessions_close",
        "sessions_recover",
        "undeploy",
        "delete_agent",
        "package",
        "configure",
    }
)


class PlatformSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target: Literal["local", "remote"] = "local"
    base_url: str = "http://127.0.0.1:8080"
    workspace: str = Field(default="persona-lab", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,62}$")
    token_env: str | None = Field(default=None, pattern=r"^[A-Z][A-Z0-9_]*$")

    @field_validator("base_url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        return public_endpoint(value)

    @model_validator(mode="after")
    def validate_target_endpoint(self):
        if self.target == "remote" and not self.base_url.startswith("https://"):
            raise ValueError("Remote Platform connections require HTTPS")
        return self

    @classmethod
    def configured(cls, target: Literal["local", "remote"] = "local") -> "PlatformSpec":
        if target not in {"local", "remote"}:
            raise ValueError("Choose an explicit local or remote Platform target")
        load_environment()
        if target == "remote":
            endpoint = os.getenv("LAB_HELIX_REMOTE_URL")
            if not endpoint:
                raise ValueError("Set LAB_HELIX_REMOTE_URL before connecting to a remote Platform")
            return cls(
                target=target,
                base_url=endpoint,
                workspace=os.getenv("LAB_HELIX_REMOTE_WORKSPACE", "persona-lab"),
                token_env="LAB_HELIX_REMOTE_TOKEN",
            )
        return cls(
            base_url=os.getenv("LAB_HELIX_URL", "http://127.0.0.1:8080"),
            workspace=os.getenv("LAB_HELIX_WORKSPACE", "persona-lab"),
            token_env="LAB_HELIX_TOKEN" if os.getenv("LAB_HELIX_TOKEN") else None,
        )


class PlatformUnavailable(RuntimeError):
    pass


class PlatformBridge:
    def __init__(self, spec: PlatformSpec | None = None):
        self.spec = spec or PlatformSpec.configured()

    async def call(self, operation: str, **arguments) -> dict:
        if operation not in OPERATIONS:
            raise ValueError("Unsupported Platform operation")
        python = platform_python()
        if not python.is_file():
            raise PlatformUnavailable(
                "Install the isolated Platform environment with "
                "uv sync --project integrations/platform --locked --python 3.12. "
                "No Platform operation was attempted."
            )
        if operation != "package" and self.spec.token_env and not os.getenv(self.spec.token_env):
            raise PlatformUnavailable(f"Set {self.spec.token_env} in the local environment")
        request = {
            "version": 1,
            "operation": operation,
            "platform": self.spec.model_dump(),
            "arguments": arguments,
        }
        # Restrict credentials sent to this child to the selected Platform token;
        # inference-provider credentials are held by LiteLLM, not this SDK bridge.
        env = {k: v for k, v in os.environ.items() if not re.search(r"(?:TOKEN|KEY|SECRET|PASSWORD)", k)}
        # Executor configuration belongs to the selected Platform connection.
        # A remote recovery must never discover a host-local gateway implicitly.
        env.pop("NHX_CONFIG_FILE_PATH", None)
        if self.spec.token_env and self.spec.token_env in os.environ:
            env[self.spec.token_env] = os.environ[self.spec.token_env]
        if operation == "configure":
            for name in ("LAB_DEPLOYMENT_GATEWAY_KEY", "LAB_DEPLOYMENT_PREFERENCES_TOKEN"):
                if name in os.environ:
                    env[name] = os.environ[name]
        local_executor_config = ROOT / ".private/platform/openshell-config.yaml"
        if self.spec.target == "local" and local_executor_config.is_file():
            env["NHX_CONFIG_FILE_PATH"] = str(local_executor_config)
        elif self.spec.target == "remote":
            remote_executor_config = os.getenv("LAB_HELIX_REMOTE_EXECUTOR_CONFIG")
            if remote_executor_config:
                selected_config = Path(remote_executor_config).expanduser().resolve()
                if not selected_config.is_file():
                    raise PlatformUnavailable("LAB_HELIX_REMOTE_EXECUTOR_CONFIG must identify an existing config file")
                env["NHX_CONFIG_FILE_PATH"] = str(selected_config)
            elif operation == "sessions_recover":
                raise PlatformUnavailable(
                    "Set LAB_HELIX_REMOTE_EXECUTOR_CONFIG before native recovery on the remote Platform; "
                    "no local executor configuration or default gateway was used"
                )
        process = await asyncio.create_subprocess_exec(
            str(python),
            str(ROOT / "integrations/platform/bridge.py"),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=ROOT,
            env=env,
        )
        try:
            stdout, _stderr = await asyncio.wait_for(
                process.communicate(json.dumps(request).encode()),
                timeout=900 if operation == "package" else 190,
            )
        except BaseException:
            if process.returncode is None:
                process.kill()
            await process.wait()
            raise
        try:
            response = json.loads(stdout)
        except (ValueError, UnicodeDecodeError) as exc:
            raise PlatformUnavailable(
                "Platform bridge returned no valid protocol result; inspect local service logs"
            ) from exc
        if process.returncode or not response.get("ok"):
            raise PlatformUnavailable(response.get("error", "Platform operation failed"))
        return response["result"]

    async def status(self) -> dict:
        try:
            return await self.call("status")
        except PlatformUnavailable as exc:
            return {
                "ready": False,
                "target": self.spec.target,
                "base_url": self.spec.base_url,
                "workspace": self.spec.workspace,
                "required_versions": PLATFORM_PINS,
                "error": str(exc),
            }


class AdmissionLease:
    """Exclusive run association for model traffic from a managed deployment.

    The inference service owns one instance. Every upstream call must resolve a
    lease before budget admission; acquiring/ending it does not contact a model.
    """

    def __init__(self):
        self.run_id: str | None = None
        self.budget = None
        self._lock = asyncio.Lock()

    async def acquire(self, run_id: str, budget) -> None:
        async with self._lock:
            if self.run_id is not None:
                raise RuntimeError("Another workload owns the deployed inference admission lease")
            self.run_id, self.budget = run_id, budget

    async def admit(self, *, role: str = "assistant", mode: str = "live") -> dict:
        async with self._lock:
            if self.run_id is None:
                raise RuntimeError("No active lab run; deployed inference is disabled")
            record = await self.budget.admit(role, mode)
            record["run_id"] = self.run_id
            return record

    async def release(self, run_id: str) -> None:
        async with self._lock:
            if self.run_id != run_id:
                raise RuntimeError("Only the owning run can release its admission lease")
            self.run_id, self.budget = None, None


class DeploymentInferenceBridge:
    """Stable Platform model-provider endpoint with an exclusive active-run lease.

    Bind this service once during the Python worker lifecycle. Activate it with
    the current run's existing Gateway before invoking a managed agent. Its
    complete() call admits exactly once through that Gateway, including the
    ordinary proxy routing policy. External provider credentials never enter
    the managed agent. This bridge offers no routing decisions of its own.
    """

    def __init__(self, key: str | None = None, prefs_key: str | None = None):
        self.key = key or os.getenv("LAB_DEPLOYMENT_GATEWAY_KEY")
        self.prefs_key = prefs_key or os.getenv("LAB_DEPLOYMENT_PREFERENCES_TOKEN")
        self.lease = AdmissionLease()
        self.gateway = None
        self.preferences: dict | None = None
        self._requests: set[asyncio.Task] = set()
        self.url: str | None = None

    async def activate(self, run_id: str, gateway, preferences: dict | None = None) -> None:
        from .catalogue import Preferences

        validated = (
            Preferences.model_validate(preferences).model_dump(mode="json")
            if preferences is not None
            else None
        )
        await self.lease.acquire(run_id, gateway.budget)
        self.gateway = gateway
        self.preferences = validated

    async def deactivate(self, run_id: str) -> None:
        if self.lease.run_id != run_id:
            raise RuntimeError("Only the owning run can close deployed inference")
        self.gateway = None
        self.preferences = None
        pending = list(self._requests)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        await self.lease.release(run_id)

    def _authorized(self, request: web.Request) -> bool:
        expected = f"Bearer {self.key}" if self.key else ""
        return bool(expected) and hmac.compare_digest(request.headers.get("Authorization", ""), expected)

    async def _models(self, request: web.Request) -> web.Response:
        if not self._authorized(request):
            raise web.HTTPUnauthorized()
        return web.json_response(
            {
                "object": "list",
                "data": [
                    {"id": name, "object": "model", "owned_by": "learning-lab"}
                    for name in ("lab-advisor-fixed", "lab-advisor-routed", "lab-support")
                ],
            }
        )

    async def _preferences(self, request: web.Request) -> web.Response:
        expected = f"Bearer {self.prefs_key}" if self.prefs_key else ""
        if not expected or not hmac.compare_digest(request.headers.get("Authorization", ""), expected):
            raise web.HTTPUnauthorized()
        if self.lease.run_id is None or self.preferences is None:
            return web.json_response({"error": "No active lab preference lease"}, status=409)
        return web.json_response({"version": 1, "run_id": self.lease.run_id, "preferences": self.preferences})

    async def _complete(self, request: web.Request) -> web.Response:
        if not self._authorized(request):
            raise web.HTTPUnauthorized()
        gateway = self.gateway
        run_id = self.lease.run_id
        if gateway is None or run_id is None:
            return web.json_response({"error": {"message": "No active lab workload lease"}}, status=409)
        task = asyncio.current_task()
        self._requests.add(task)
        try:
            try:
                payload = await request.json()
                if not isinstance(payload, dict):
                    raise ValueError("Expected an OpenAI request object")
            except (ValueError, UnicodeError):
                return web.json_response({"error": {"message": "Invalid model request JSON"}}, status=400)
            if self.gateway is not gateway or self.lease.run_id != run_id:
                return web.json_response({"error": {"message": "Workload lease changed"}}, status=409)
            requested_stream = bool(payload.get("stream"))
            result = await gateway.complete(payload, role="assistant")
            if not requested_stream:
                return web.json_response(result)
            # One admitted buffered call, projected for the Hermes SSE client.
            response = web.StreamResponse(
                headers={"Content-Type": "text/event-stream", "Cache-Control": "no-cache"}
            )
            await response.prepare(request)
            choice = result["choices"][0]
            message = choice["message"]
            delta = {"role": message.get("role", "assistant")}
            if message.get("content") is not None:
                delta["content"] = message["content"]
            if message.get("tool_calls"):
                delta["tool_calls"] = [
                    {"index": index, **call} for index, call in enumerate(message["tool_calls"])
                ]
            base = {key: result[key] for key in ("id", "created", "model") if key in result}
            base["object"] = "chat.completion.chunk"
            chunks = [
                {**base, "choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
                {
                    **base,
                    "choices": [
                        {"index": 0, "delta": {}, "finish_reason": choice.get("finish_reason", "stop")}
                    ],
                    "usage": result.get("usage"),
                },
            ]
            for chunk in chunks:
                await response.write(("data: " + json.dumps(chunk) + "\n\n").encode())
            await response.write(b"data: [DONE]\n\n")
            await response.write_eof()
            return response
        except Exception as exc:
            exhausted = type(exc).__name__ == "BudgetExceeded"
            message = (
                "Run inference budget exhausted"
                if exhausted
                else "Deployed inference failed; inspect this run's ledger"
            )
            return web.json_response(
                {
                    "error": {
                        "message": message,
                        "code": "lab_budget_exhausted" if exhausted else "lab_call_failed",
                    }
                },
                status=400,
            )
        finally:
            self._requests.discard(task)

    @asynccontextmanager
    async def serving(self, *, host: str = "127.0.0.1", port: int = 8766):
        if not self.key or len(self.key) < 24:
            raise PlatformUnavailable(
                "Set LAB_DEPLOYMENT_GATEWAY_KEY to a local secret of at least 24 characters"
            )
        if self.prefs_key and (len(self.prefs_key) < 24 or hmac.compare_digest(self.key, self.prefs_key)):
            raise PlatformUnavailable(
                "LAB_DEPLOYMENT_PREFERENCES_TOKEN must be a distinct secret of at least 24 characters"
            )
        app = web.Application(client_max_size=4 * 1024 * 1024)
        app.router.add_get("/v1/models", self._models)
        app.router.add_get("/v1/lab/preferences", self._preferences)
        app.router.add_post("/v1/chat/completions", self._complete)
        runner = web.AppRunner(app, access_log=None, shutdown_timeout=3)
        await runner.setup()
        try:
            await web.TCPSite(runner, host, port).start()
            self.url = f"http://{host}:{runner.addresses[0][1]}/v1"
            yield self
        finally:
            if self.lease.run_id is not None:
                await self.deactivate(self.lease.run_id)
            await runner.cleanup()
            self.url = None
