"""Application services used by the CLI and SvelteKit worker."""

from __future__ import annotations

from . import __version__

import asyncio
from contextlib import AsyncExitStack
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Literal
import uuid

from pydantic import Field, model_validator

from .catalogue import Preferences, StrictModel, all_courses, search_courses
from .fabric_target import FabricTarget
from .inference import Budget, BudgetExceeded, Gateway
from .settings import ROOT, load_environment, model_id, inference_configured
from .simulation import run_experiment
from .target import DirectTarget, relay_config, relay_evidence


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2, default=str) + "\n")
    temp.replace(path)


class RunSpec(StrictModel):
    enrichment: bool = False
    turns: int = Field(default=3, ge=1, le=3)
    mode: Literal["demo", "live"] = "demo"
    engine: Literal["direct", "relay", "fabric"] = "direct"
    source: Literal["hf-profile-only", "ngc", "generated"] = "hf-profile-only"
    personas: int = Field(default=1, ge=1, le=10)
    strategies: list[Literal["concise", "clarification-first"]] = Field(default_factory=lambda: ["concise"])
    story_id: Literal["photography", "baking", "boardgames", "profile-goal"] = "profile-goal"
    source_ids: list[str] = Field(default_factory=list, max_length=10)
    seed: int | None = Field(default=None, ge=0, le=2**63 - 1)
    harness: Literal["deepagents", "hermes"] = "deepagents"
    model_route: Literal["fixed", "switchyard"] = "fixed"
    parent_run_id: str | None = None
    comparison_reason: str | None = Field(default=None, max_length=500)
    overlay_job_id: str | None = None
    generated_job_id: str | None = None
    budget_override_sgd: float | None = Field(default=None, ge=0, le=1_000_000)

    @model_validator(mode="after")
    def validate_conditions(self):
        if self.harness == "hermes" and self.engine != "fabric":
            raise ValueError("Hermes is available through Fabric; select the Fabric runtime")
        if self.source_ids and len(self.source_ids) != self.personas:
            raise ValueError("Choose the same number of locked profiles and requested personas")
        if len(set(self.source_ids)) != len(self.source_ids):
            raise ValueError("Locked source IDs must be distinct")
        if self.source == "generated" and not self.generated_job_id:
            raise ValueError("Generated profiles require a saved Data Designer job")
        if self.generated_job_id and self.source != "generated":
            raise ValueError("A generated profile job requires the generated source distribution")
        if self.overlay_job_id and self.source == "generated":
            raise ValueError(
                "Scenario overlays apply to their original source profiles; choose an original distribution"
            )
        if self.enrichment and (self.overlay_job_id or self.generated_job_id):
            raise ValueError(
                "Choose one saved Designer input rather than combining it with legacy enrichment"
            )
        if self.parent_run_id and not (self.comparison_reason or "").strip():
            raise ValueError("A comparison requires a reason explaining the changed condition")
        return self


class ChatSpec(StrictModel):
    preferences: Preferences
    session_id: str | None = None
    mode: Literal["demo", "live"] = "demo"
    engine: Literal["direct", "relay", "fabric"] = "direct"
    strategy: Literal["concise", "clarification-first"] = "concise"
    harness: Literal["deepagents", "hermes"] = "deepagents"
    model_route: Literal["fixed", "switchyard"] = "fixed"

    @model_validator(mode="after")
    def validate_harness(self):
        if self.harness == "hermes" and self.engine != "fabric":
            raise ValueError("Hermes requires the Fabric runtime")
        return self


class LabService:
    def __init__(self, runs: Path | None = None):
        self.runs = runs or ROOT / "runs"
        self.tasks: dict[str, asyncio.Task] = {}
        self.run_state: dict[str, dict] = {}
        self.lock = asyncio.Lock()
        self.chats: dict[str, dict] = {}
        self.workbench_state: dict[str, dict] = {}
        self.platform_state: dict[str, dict] = {}
        self.managed_budgets: dict[str, Budget] = {}
        self.managed_sessions: dict[tuple, dict] = {}
        self.managed_guard_path = self.runs / "platform-session.json"
        self.managed_guard = None
        if self.managed_guard_path.is_file():
            try:
                self.managed_guard = json.loads(self.managed_guard_path.read_text())
            except (OSError, ValueError):
                self.managed_guard = {"error": "Inspect the retained session file before starting another session"}
        self.deployment_stack = AsyncExitStack()
        self.deployment_bridge = None
        self.recover_interrupted()

    def recover_interrupted(self):
        paths = [
            *self.runs.glob("*/run.json"),
            *self.runs.glob("workbench/*/job.json"),
            *self.runs.glob("platform-jobs/*/job.json"),
            *self.runs.glob("chats/*/chat.json"),
        ]
        for path in paths:
            try:
                run = json.loads(path.read_text())
                pid = run.get("owner_pid")
                if pid:
                    try:
                        os.kill(pid, 0)
                        continue
                    except ProcessLookupError:
                        pass
                    except PermissionError:
                        continue
                if run["status"] in {"queued", "running"}:
                    run.update(status="interrupted", ended_at=now(), error="Worker stopped before completion")
                    atomic_json(path, run)
            except (ValueError, KeyError):
                continue

    def status(self):
        self.recover_interrupted()
        load_environment()
        return {
            "app": "Singapore Learning & Classes Advisor",
            "version": __version__,
            "nim_key_present": bool(os.getenv("NVIDIA_API_KEY")),
            "inference_configured": inference_configured(),
            "ngc_key_present": bool(os.getenv("NGC_CLI_API_KEY")),
            "model": model_id(),
            "catalogue_count": len(all_courses()),
            "snapshot_date": "2026-11-10",
            "active_run": next((k for k, task in self.tasks.items() if not task.done()), None),
            "personas_audited": (ROOT / "data/persona-audit.json").exists(),
            "limits": {"calls": 120, "output_tokens_per_call": 1024, "turns": 3, "concurrent_episodes": 1},
            "proxy_configured": bool(os.getenv("LAB_PROXY_BASE_URL")),
            "provider_route": "litellm" if os.getenv("LAB_PROXY_BASE_URL") else "nim-direct",
            "managed_session": self.managed_guard,
            "deployment_model_url": os.getenv("LAB_DEPLOYMENT_PROVIDER_URL") or (
                f"http://{os.getenv('LAB_DEPLOYMENT_GATEWAY_HOST', '127.0.0.1')}:"
                f"{os.getenv('LAB_DEPLOYMENT_GATEWAY_PORT', '8766')}/v1"
            ),
        }

    def list_runs(self, mode=None):
        if mode not in {None, "live", "demo"}:
            raise ValueError("Choose live, demo or omit the saved-run filter")
        self.recover_interrupted()
        output = []
        for path in sorted(self.runs.glob("*/run.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                run = json.loads(path.read_text())
            except ValueError:
                continue
            if mode is None or run.get("spec", {}).get("mode") == mode:
                output.append(run)
            if len(output) == 30:
                break
        return output

    def get_run(self, run_id: str):
        if not re.fullmatch(r"[a-f0-9-]{36}", run_id):
            raise ValueError("Invalid run ID")
        path = self.runs / run_id / "run.json"
        if not path.exists():
            raise ValueError("Run not found")
        result = json.loads(path.read_text())
        events = path.with_name("events.jsonl")
        result["events"] = (
            [json.loads(line) for line in events.read_text().splitlines()] if events.exists() else []
        )
        return result

    def get_trace(self, run_id: str, episode_id: str):
        from .provenance import build_trace

        run = self.get_run(run_id)
        if not re.fullmatch(r"[a-f0-9-]{36}", episode_id):
            raise ValueError("Invalid episode ID")
        return build_trace(self.runs / run_id, run, episode_id)

    def _managed_story_reference(self, reference: dict) -> dict:
        """Resolve saved public inputs; caller-supplied labels never establish lineage."""
        if not isinstance(reference, dict) or set(reference) != {"run_id", "episode_id", "condition_id"}:
            raise ValueError("Story reference requires only run_id, episode_id and condition_id")
        for value in reference.values():
            try:
                if not isinstance(value, str) or str(uuid.UUID(value)) != value:
                    raise ValueError
            except (ValueError, AttributeError):
                raise ValueError("Story reference requires canonical UUID identities") from None
        run = self.get_run(reference["run_id"])
        if run.get("status") in {"queued", "running"}:
            raise ValueError("Wait for the saved story to stop before preparing a managed condition")
        events = [event for event in run.get("events", [])
                  if event.get("episode_id") == reference["episode_id"]]
        starts = [event for event in events if event.get("type") == "episode_started"]
        if len(starts) != 1 or not starts[0].get("preferences"):
            raise ValueError("This saved episode has no unambiguous original structured preferences")
        first = next((event.get("content") for event in events
                      if event.get("type") == "message" and event.get("role") == "user"), None)
        if not isinstance(first, str) or not 1 <= len(first) <= 12000:
            raise ValueError("This saved episode has no supported first public learner input")
        spec = run.get("spec", {})
        return {
            **reference,
            "source_mode": spec.get("mode"),
            "source_story_id": starts[0].get("story_id") or spec.get("story_id"),
            "source_profile_id": starts[0].get("source_id"),
            "source_harness": spec.get("harness", "deepagents"),
            "source_model_route": spec.get("model_route", "fixed"),
            "source_catalogue_sha256": run.get("catalogue_sha256"),
            "preferences": Preferences.model_validate(starts[0]["preferences"]).model_dump(mode="json"),
            "first_learner_input_sha256": hashlib.sha256(first.encode()).hexdigest(),
            "notice": "A new managed condition reuses public inputs; its memory, packaged catalogue and agent configuration are separate.",
        }

    def get_evidence(self, run_id: str, episode_id: str | None = None):
        from .evidence import build_evidence, sanitize

        run = self.get_run(run_id)
        folder = self.runs / run_id
        if episode_id:
            if episode_id not in {e["episode_id"] for e in run["episodes"]} and not any(
                e.get("episode_id") == episode_id for e in run["events"]
            ):
                raise ValueError("Episode does not belong to the selected experiment")
            folder = folder / episode_id
        return {
            "run_id": run_id,
            "episode_id": episode_id,
            "folder": str(folder.resolve()),
            **build_evidence(folder),
            "gateway": {"scope": "whole_experiment", "calls": run.get("calls", 0),
                        "usage": sanitize(run.get("usage", []))},
        }

    def get_artifact(self, run_id: str, artifact_id: str, episode_id: str | None = None):
        from .evidence import read_artifact

        self.get_evidence(run_id, episode_id)
        folder = self.runs / run_id / episode_id if episode_id else self.runs / run_id
        return read_artifact(folder, artifact_id)

    def dataset_catalogue(self):
        from .datasets import dataset_catalogue

        return dataset_catalogue()

    def persona_facets(self, source="hf-profile-only"):
        from .datasets import persona_facets

        return persona_facets(source)

    def browse_personas(self, params):
        from .datasets import DatasetQuery, browse_personas

        return browse_personas(DatasetQuery.model_validate(params))

    def sample_personas(self, params):
        from .datasets import sample_personas

        allowed = {"source", "count", "seed", "filters"}
        if set(params) - allowed:
            raise ValueError("Unexpected persona sampling fields")
        count = params.get("count", 1)
        if not isinstance(count, int) or not 1 <= count <= 10:
            raise ValueError("Choose one to ten profiles")
        return sample_personas(**params)

    async def start_workbench(self, params):
        from .workbench import WorkbenchSpec

        spec = WorkbenchSpec.model_validate(params)
        if self.lock.locked() or any(not task.done() for task in self.tasks.values()):
            raise ValueError("A model workload is active; wait or cancel it")
        await self._close_chats()
        job_id = str(uuid.uuid4())
        state = {
            "job_id": job_id,
            "status": "queued",
            "started_at": now(),
            "owner_pid": os.getpid(),
            "spec": spec.model_dump(mode="json"),
            "calls": 0,
            "budget": 120,
            "result": None,
        }
        folder = self.runs / "workbench" / job_id
        atomic_json(folder / "job.json", state)
        self.workbench_state[job_id] = state
        self.tasks[job_id] = asyncio.create_task(self._workbench_job(job_id, spec, folder, state))
        return state.copy()

    async def _workbench_job(self, job_id, spec, folder, state):
        from .workbench import run_workbench

        budget = Budget()
        try:
            async with self.lock:
                state["status"] = "running"
                atomic_json(folder / "job.json", state)
                async with Gateway(budget, "live").serving() as gateway:
                    state["result"] = await asyncio.wait_for(run_workbench(spec, folder, gateway), 1800)
                state["status"] = state["result"].get("status", "completed")
        except asyncio.CancelledError:
            state["status"] = "cancelled"
        except Exception as exc:
            state.update(status="failed", error=f"{type(exc).__name__}: {str(exc)[:500]}")
        finally:
            state.update(calls=budget.calls, usage=budget.records, ended_at=now())
            atomic_json(folder / "job.json", state)

    def get_workbench(self, job_id):
        if not re.fullmatch(r"[a-f0-9-]{36}", job_id):
            raise ValueError("Invalid workbench job ID")
        path = self.runs / "workbench" / job_id / "job.json"
        if not path.is_file():
            raise ValueError("Workbench job not found")
        return self.workbench_state.get(job_id) or json.loads(path.read_text())

    def list_workbench(self):
        jobs = []
        for path in sorted(
            (self.runs / "workbench").glob("*/job.json"), key=lambda item: item.stat().st_mtime, reverse=True
        )[:30]:
            try:
                saved = json.loads(path.read_text())
                jobs.append(
                    {
                        key: saved.get(key)
                        for key in ("job_id", "status", "started_at", "spec", "calls", "error")
                    }
                )
            except (ValueError, OSError):
                continue
        return jobs

    async def cancel_workbench(self, job_id):
        self.get_workbench(job_id)
        task = self.tasks.get(job_id)
        if task and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            state = self.get_workbench(job_id)
            if state["status"] in {"queued", "running"}:
                state.update(status="cancelled", ended_at=now())
                atomic_json(self.runs / "workbench" / job_id / "job.json", state)
        return self.get_workbench(job_id)

    def get_platform_job(self, job_id):
        if not re.fullmatch(r"[a-f0-9-]{36}", job_id):
            raise ValueError("Invalid Platform job ID")
        path = self.runs / "platform-jobs" / job_id / "job.json"
        if not path.is_file():
            raise ValueError("Platform job not found")
        return self.platform_state.get(job_id) or json.loads(path.read_text())

    async def platform_action(self, params):
        from .deployment import PlatformBridge, PlatformSpec, OPERATIONS

        target = params.get("target", "local")
        if target not in {"local", "remote"}:
            raise ValueError("Choose an explicit local or remote Platform target")
        operation = params.get("operation", "status")
        if operation == "job":
            return self.get_platform_job(params["job_id"])
        if operation == "cancel_job":
            self.get_platform_job(params["job_id"])
            task = self.tasks.get(params["job_id"])
            if task and not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
                state = self.get_platform_job(params["job_id"])
                if state["status"] in {"queued", "running"}:
                    state.update(status="cancelled", ended_at=now())
                    atomic_json(self.runs / "platform-jobs" / params["job_id"] / "job.json", state)
            return self.get_platform_job(params["job_id"])
        bridge = PlatformBridge(PlatformSpec.configured(target))
        if operation == "status":
            return {**await bridge.status(), "managed_session": self.managed_guard}
        if operation not in OPERATIONS:
            raise ValueError("Unsupported Platform operation")
        if operation == "sessions_create" and (self.managed_sessions or self.managed_guard):
            raise ValueError("Close the current managed session before creating another learner conversation")
        if operation == "sessions_recover":
            retained = self.managed_guard or {}
            scope = (bridge.spec.target, bridge.spec.base_url, bridge.spec.workspace)
            if (tuple(retained.get("scope", ())) != scope
                    or retained.get("session_name") != params.get("arguments", {}).get("name")
                    or retained.get("invocation_state") not in {"uncertain", "running"}):
                raise ValueError("Recover only the retained failed session using its original Platform connection")
        if operation == "undeploy" and self.managed_guard:
            scope = (bridge.spec.target, bridge.spec.base_url, bridge.spec.workspace)
            if (tuple(self.managed_guard.get("scope", ())) == scope
                    and self.managed_guard.get("deployment") == params.get("arguments", {}).get("name")):
                raise ValueError("Close the managed session before undeploying its agent")
        if operation in {"logs", "deployment", "agent"}:
            return await bridge.call(operation, **params.get("arguments", {}))
        if operation != "sessions_close" and (
            self.lock.locked() or any(not task.done() for task in self.tasks.values())
        ):
            raise ValueError("A workload is active; wait or cancel it before this Platform action")
        if operation != "sessions_close":
            await self._close_chats()
        job_id = str(uuid.uuid4())
        state = {
            "job_id": job_id,
            "operation": operation,
            "target": target,
            "status": "queued",
            "started_at": now(),
            "owner_pid": os.getpid(),
            "calls": 0,
        }
        self.platform_state[job_id] = state
        folder = self.runs / "platform-jobs" / job_id
        atomic_json(folder / "job.json", state)
        self.tasks[job_id] = asyncio.create_task(
            self._platform_job(job_id, bridge, operation, params.get("arguments", {}), folder, state)
        )
        return state.copy()

    async def _platform_job(self, job_id, bridge, operation, arguments, folder, state):
        from .evidence import sanitize

        budget = None
        session = None
        arguments = dict(arguments)
        scope = (bridge.spec.target, bridge.spec.base_url, bridge.spec.workspace)
        try:
            async with self.lock:
                state["status"] = "running"
                atomic_json(folder / "job.json", state)
                supplied_reference = arguments.pop("story_reference", None)
                reference = None
                if supplied_reference is not None:
                    if operation not in {"sessions_create", "invoke"}:
                        raise ValueError("Story references apply only to session creation and invocation")
                    reference = self._managed_story_reference(supplied_reference)
                    state["story_reference"] = reference
                if operation == "configure":
                    # Configuration probes /models before any run lease exists.
                    await self._deployment_gateway()
                if operation == "sessions_close":
                    retained = self.managed_guard
                    if retained and retained.get("session_name") == arguments.get("name"):
                        if tuple(retained.get("scope", ())) != scope:
                            raise ValueError("Close the retained session using its original Platform connection")
                        arguments["require_runtime_drain"] = retained.get("invocation_state") != "idle"
                if operation == "sessions_recover":
                    retained = self.managed_guard or {}
                    if (tuple(retained.get("scope", ())) != scope
                            or retained.get("session_name") != arguments.get("name")):
                        raise ValueError("The retained session changed before recovery; inspect its current state")
                    recovery_id = retained.get("recovery_job_id") or job_id
                    if not re.fullmatch(r"[a-f0-9-]{36}", recovery_id):
                        raise ValueError("Invalid retained recovery job identity")
                    self._update_managed_guard(recovery_job_id=recovery_id)
                    # Receipt paths and native identities never come from API arguments.
                    arguments = {"name": retained["session_name"], "receipt_path": str(
                        self.runs / "platform-jobs" / recovery_id / "recovery-receipt.json"
                    )}
                if operation == "invoke":
                    session_id = arguments.get("session_id")
                    session = self.managed_sessions.get((*scope, session_id))
                    if not session or session["deployment"] != arguments.get("deployment"):
                        raise ValueError(
                            "Create a fresh session for this deployment in this application worker"
                        )
                    if session["tainted"]:
                        raise ValueError(
                            "This session has an incomplete invocation; close it before creating a new one"
                        )
                    if session["turns"] >= 3:
                        raise ValueError("The three-turn conversation limit is reached; close this session")
                    preferences = Preferences.model_validate(arguments.pop("preferences", {})).model_dump(
                        mode="json"
                    )
                    bound_reference = session.get("story_reference")
                    if reference and bound_reference and reference != bound_reference:
                        raise ValueError("Use a new managed session when changing the saved story reference")
                    if reference and not bound_reference and session["turns"]:
                        raise ValueError("Bind the saved story before the first managed invocation")
                    reference = reference or bound_reference
                    if reference:
                        # Re-resolve even when a later caller omits the reference,
                        # so modified source records cannot silently change lineage.
                        current = self._managed_story_reference({key: reference[key] for key in (
                            "run_id", "episode_id", "condition_id"
                        )})
                        if current != reference:
                            raise ValueError("The saved story inputs changed; prepare a new managed condition")
                        if preferences != reference["preferences"]:
                            raise ValueError("The managed condition must retain the saved story preferences")
                        text = arguments.get("input")
                        if not session["turns"] and (
                            not isinstance(text, str)
                            or hashlib.sha256(text.encode()).hexdigest() != reference["first_learner_input_sha256"]
                        ):
                            raise ValueError("The first managed invocation must reuse the saved public learner input")
                        session["story_reference"] = reference
                        state["story_reference"] = reference
                    if session.get("frozen_preferences") and preferences != session["frozen_preferences"]:
                        raise ValueError("This sandbox requires its displayed immutable teaching goal, budget and days")
                    if session.get("preferences") and session["preferences"] != preferences:
                        raise ValueError("Use a new session when changing the trusted learner constraints")
                    session["preferences"] = preferences
                    budget = session["budget"]
                    route = arguments.pop("model_route", "fixed")
                    if route != session.setdefault("model_route", route):
                        raise ValueError("Use a new session when changing the model routing condition")
                    from .course_mcp import TOOL_NAMES
                    allowed_tools = TOOL_NAMES if session["harness"] == "deepagents" else None
                    async with Gateway(budget, "live", model_route=route,
                                       allowed_tool_names=allowed_tools).serving() as gateway:
                        await self._deployment_gateway()
                        await self.deployment_bridge.activate(job_id, gateway, preferences)
                        try:
                            session["turns"] += 1
                            session["tainted"] = True
                            self._update_managed_guard(invocation_state="running")
                            state["result"] = sanitize(await bridge.call(operation, **arguments))
                            from .outcomes import require_valid_answer
                            response = state["result"].get("response")
                            if isinstance(response, dict):
                                response = (response.get("choices") or [{}])[0].get("message", {}).get("content")
                            state["answer"] = require_valid_answer(response)
                            session["tainted"] = False
                            self._update_managed_guard(invocation_state="idle")
                        finally:
                            await self.deployment_bridge.deactivate(job_id)
                else:
                    state["result"] = sanitize(await bridge.call(operation, **arguments))
                    if operation == "sessions_create":
                        saved = state["result"].get("session", {})
                        identity = saved.get("name") or saved.get("id") or saved.get("entity_id")
                        if not identity or saved.get("status") != "active":
                            raise ValueError("Platform did not confirm an active session identity")
                        harness = state["result"].get("deployment", {}).get("harness_kind")
                        if harness not in {"deepagents", "hermes"}:
                            raise ValueError("Platform did not identify a supported harness in its deployment snapshot")
                        self.managed_sessions[(*scope, identity)] = {
                            "deployment": arguments.get("deployment"),
                            "harness": harness,
                            "bridge": bridge,
                            "budget": Budget(),
                            "turns": 0,
                            "tainted": False,
                            "frozen_preferences": state["result"].get("deployment", {}).get("frozen_preferences"),
                            "story_reference": reference,
                        }
                        self.managed_guard = {"scope": list(scope), "session_name": identity,
                                              "deployment": arguments.get("deployment"), "harness": harness,
                                              "invocation_state": "idle"}
                        atomic_json(self.managed_guard_path, self.managed_guard)
                    elif operation in {"sessions_close", "sessions_recover"}:
                        if ((operation == "sessions_recover" or arguments.get("require_runtime_drain"))
                                and not state["result"].get("runtime_cleanup_confirmed")):
                            raise ValueError("The remote runtime has not confirmed it stopped; another learner remains blocked")
                        if operation == "sessions_recover" and not state["result"].get("deployment_removed"):
                            raise ValueError("Recovery did not confirm removal of the failed deployment")
                        if state["result"].get("session", {}).get("status") != "closed":
                            raise ValueError(
                                "Platform has not confirmed session closure; inspect its actual state"
                            )
                        self.managed_sessions.pop((*scope, arguments.get("name")), None)
                        if self.managed_guard and self.managed_guard.get("session_name") == arguments.get("name"):
                            self.managed_guard = None
                            self.managed_guard_path.unlink(missing_ok=True)
                state["status"] = "completed"
        except asyncio.CancelledError:
            state["status"] = "cancelled"
        except Exception as exc:
            state.update(status="failed", error=sanitize(f"{type(exc).__name__}: {str(exc)[:900]}"))
        finally:
            if session is not None and session.get("tainted"):
                self._update_managed_guard(invocation_state="uncertain")
            if (operation in {"sessions_close", "sessions_recover"} and state["status"] != "completed"
                    and self.managed_guard and self.managed_guard.get("session_name") == arguments.get("name")
                    and tuple(self.managed_guard.get("scope", ())) == scope):
                # A failed stop is itself uncertainty, even after a valid reply.
                self._update_managed_guard(invocation_state="uncertain")
            if budget is not None:
                state.update(calls=budget.calls, usage=budget.records, conversation_turns=session["turns"])
            state["ended_at"] = now()
            atomic_json(folder / "job.json", state)

    def _update_managed_guard(self, **values):
        if self.managed_guard:
            self.managed_guard.update(values)
            atomic_json(self.managed_guard_path, self.managed_guard)

    async def _deployment_gateway(self):
        from .deployment import DeploymentInferenceBridge

        if self.deployment_bridge is None:
            candidate = DeploymentInferenceBridge()
            self.deployment_bridge = await self.deployment_stack.enter_async_context(
                candidate.serving(
                    host=os.getenv("LAB_DEPLOYMENT_GATEWAY_HOST", "127.0.0.1"),
                    port=int(os.getenv("LAB_DEPLOYMENT_GATEWAY_PORT", "8766")),
                )
            )
        return self.deployment_bridge

    async def start_run(self, spec: RunSpec):
        if any(not task.done() for task in self.tasks.values()) or self.lock.locked():
            raise ValueError("One model workload is already active; wait or cancel it first")
        if not spec.strategies or len(spec.strategies) != len(set(spec.strategies)):
            raise ValueError("Choose one or two distinct strategies")
        if spec.mode == "live":
            load_environment()
            if not inference_configured():
                raise ValueError(
                    "Configure NVIDIA_API_KEY or the LiteLLM proxy URL and key before a live run"
                )
        await self._close_chats()
        from .source_index import code_revision
        from .stories import story

        run_id = str(uuid.uuid4())
        folder = self.runs / run_id
        state = {
            "run_id": run_id,
            "schema_version": 2,
            "code_revision": code_revision(),
            "story": story(spec.story_id),
            "status": "queued",
            "started_at": now(),
            "spec": spec.model_dump(),
            "owner_pid": os.getpid(),
            "episodes": [],
            "calls": 0,
            "budget": 120,
            "models": {role: model_id(role) for role in ["assistant", "user", "judge", "summary"]}
            if spec.mode == "live"
            else {"assistant": "offline-scripted"},
            "source_notice": (
                "Offline scripted scenarios; no real persona sample or model inference."
                if spec.mode == "demo"
                else "HF profile-only: no OCEAN personality conditioning; diagnostic sample, not a population estimate."
                if spec.source == "hf-profile-only"
                else "Data Designer-generated synthetic profiles; not original Nemotron or NGC records."
                if spec.source == "generated"
                else "NGC Extended; source records remain local."
            ),
        }
        self.run_state[run_id] = state
        atomic_json(folder / "run.json", state)
        self.tasks[run_id] = asyncio.create_task(self._run(run_id, folder, spec, state))
        return state.copy()

    async def _run(self, run_id, folder, spec, state):
        budget = Budget()

        async def event(value):
            value = {"at": now(), **value}
            with (folder / "events.jsonl").open("a") as file:
                file.write(json.dumps(value, default=str) + "\n")
            state["calls"] = budget.calls
            if value["type"] == "inputs_frozen":
                state["catalogue_sha256"] = value["catalogue_sha256"]
            if value["type"] == "scenarios_bound":
                state["scenarios"] = value["scenarios"]
            if value["type"] == "episode_completed":
                state["episodes"].append(value)
            atomic_json(folder / "run.json", state)

        try:
            async with self.lock:
                state["status"] = "running"
                atomic_json(folder / "run.json", state)
                selection = None
                resolved = None
                snapshot = None
                if spec.generated_job_id or spec.overlay_job_id:
                    from .workbench import resolved_workbench_profiles

                    job = self.get_workbench(spec.generated_job_id or spec.overlay_job_id)
                    if job["status"] not in {"completed", "completed_with_warnings"}:
                        raise ValueError("Choose a completed Data Designer job")
                    selection = resolved_workbench_profiles(job["result"], spec.source_ids or None)
                    distribution = selection["source_distribution"]
                    if spec.source == "generated" and distribution != "generated-designer":
                        raise ValueError("Choose a generated-profile job for the generated source")
                    if spec.overlay_job_id and distribution != spec.source:
                        raise ValueError("The saved overlay belongs to a different source distribution")
                if spec.parent_run_id:
                    import hashlib
                    from .datasets import profile_hash

                    parent = self.get_run(spec.parent_run_id)
                    parent_folder = self.runs / parent["run_id"]
                    if parent["status"] in {"queued", "running"}:
                        raise ValueError("Wait for the original experiment to finish before comparing")
                    parent_spec = RunSpec.model_validate(parent["spec"])
                    for name in (
                        "mode",
                        "source",
                        "personas",
                        "story_id",
                        "turns",
                        "source_ids",
                        "seed",
                        "generated_job_id",
                        "enrichment",
                    ):
                        if getattr(parent_spec, name) != getattr(spec, name):
                            raise ValueError(f"A controlled comparison must retain the parent's {name}")
                    if spec.mode == "live":
                        resolved = json.loads((parent_folder / "resolved-inputs.json").read_text())
                        if len(resolved) != spec.personas:
                            raise ValueError("A comparison must retain the parent's selected profile count")
                        for row in resolved:
                            row["pair_input_id"] = row["trajectory_id"]
                            row["trajectory_id"] = str(uuid.uuid4())
                    snapshot = folder / "catalogue-snapshot.json"
                    original_snapshot = (parent_folder / "catalogue-snapshot.json").read_bytes()
                    if (
                        not parent.get("catalogue_sha256")
                        or hashlib.sha256(original_snapshot).hexdigest() != parent["catalogue_sha256"]
                    ):
                        raise ValueError(
                            "The original experiment's frozen catalogue failed its recorded hash check"
                        )
                    snapshot.write_bytes(original_snapshot)
                    if selection and resolved:
                        for row in resolved:
                            key = row["persona"]["uuid"]
                            if key not in selection["overlays"] and spec.overlay_job_id:
                                raise ValueError("The overlay does not match the original comparison profile")
                            if spec.overlay_job_id:
                                overlay = selection["overlays"][key]
                                if profile_hash(row["persona"]) != overlay["original_profile_sha256"]:
                                    raise ValueError(
                                        "The overlay's original profile hash differs from the frozen comparison profile"
                                    )
                                row["learning_overlay"] = overlay
                                row.pop("scenario_binding", None)
                async with Gateway(budget, spec.mode, model_route=spec.model_route).serving() as gateway:
                    await asyncio.wait_for(
                        run_experiment(
                            spec.model_dump(),
                            folder,
                            gateway,
                            event,
                            resolved_rows=resolved,
                            catalogue_path=snapshot,
                            profiles_selection=selection,
                        ),
                        timeout=1800,
                    )
                state["status"] = (
                    "completed_with_failures"
                    if any(e["status"] == "failed" for e in state["episodes"])
                    else "completed_with_warnings"
                    if any(e["status"] != "completed" for e in state["episodes"])
                    else "completed"
                )
        except asyncio.CancelledError:
            state["status"] = "cancelled"
        except BudgetExceeded as exc:
            state.update(status="budget_exhausted", error=str(exc))
        except TimeoutError:
            state.update(status="timed_out", error="Experiment exceeded its 30-minute deadline")
        except Exception as exc:
            # SDK diagnostics remain local; the browser gets a bounded error.
            state.update(
                status="budget_exhausted" if budget.calls >= budget.limit else "failed",
                error=f"{type(exc).__name__}: {str(exc)[:600]}",
            )
        finally:
            state.update(ended_at=now(), calls=budget.calls, usage=budget.records)
            atomic_json(folder / "run.json", state)

    async def cancel(self, run_id: str):
        self.get_run(run_id)
        task = self.tasks.get(run_id)
        if task and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            state = self.get_run(run_id)
            if state["status"] in {"queued", "running"}:
                state.pop("events", None)
                state.update(status="cancelled", ended_at=now())
                atomic_json(self.runs / run_id / "run.json", state)
        return self.get_run(run_id)

    async def evaluate_run(self, run_id: str):
        from .evaluation import run_helix, evaluate_saved_run

        run = self.get_run(run_id)
        if run["status"] in {"queued", "running"}:
            raise ValueError("Wait for the run to finish before scoring its saved replies")
        folder = self.runs / run_id
        detailed = evaluate_saved_run(run, folder)
        atomic_json(folder / "evaluation-details.json", detailed)
        atomic_json(folder / "helix-criteria.json", detailed["helix_rows"])
        result = await run_helix(folder / "helix-criteria.json", folder / "helix-results.json")
        result = {
            **result,
            "details": detailed,
            "method": "Deterministic application assertions scored with the real Helix ExactMatch metric.",
        }
        state = json.loads((folder / "run.json").read_text())
        state["evaluation"] = result
        atomic_json(folder / "run.json", state)
        return result

    async def chat(self, spec: ChatSpec):
        from .evidence import sanitize

        if self.lock.locked() or any(not task.done() for task in self.tasks.values()):
            raise ValueError("A model workload is active; wait for it to finish or cancel it")
        async with self.lock:
            session_id = spec.session_id or str(uuid.uuid4())
            if not re.fullmatch(r"[a-f0-9-]{36}", session_id):
                raise ValueError("Invalid chat session ID")
            entry = self.chats.get(session_id)
            if spec.session_id and entry is None:
                raise ValueError("This chat session has ended. Start a new conversation.")
            signature = (spec.mode, spec.engine, spec.strategy, spec.harness, spec.model_route)
            if entry and entry["signature"] != signature:
                raise ValueError("Start a new conversation when changing mode, harness or strategy")
            if not entry:
                # One retained conversation keeps plugin and adapter environments unambiguous.
                await self._close_chats()
                stack = AsyncExitStack()
                budget = Budget()
                folder = self.runs / "chats" / session_id
                entry = {
                    "stack": stack,
                    "budget": budget,
                    "signature": signature,
                    "folder": folder,
                    "state": {
                        "session_id": session_id,
                        "mode": spec.mode,
                        "engine": spec.engine,
                        "harness": spec.harness,
                        "model_route": spec.model_route,
                        "strategy": spec.strategy,
                        "status": "starting",
                        "started_at": now(),
                        "owner_pid": os.getpid(),
                        "turns": [],
                    },
                }
                self._save_chat(entry)
                try:
                    gateway = await stack.enter_async_context(
                        Gateway(budget, spec.mode, model_route=spec.model_route).serving()
                    )
                    if spec.engine == "relay":
                        import nemo_relay

                        await stack.enter_async_context(
                            nemo_relay.plugin.activate({}, str(relay_config(folder)))
                        )
                    cls = FabricTarget if spec.engine == "fabric" else DirectTarget
                    target_kwargs = (
                        {"harness": spec.harness, "model_route": spec.model_route}
                        if cls is FabricTarget
                        else {}
                    )
                    target = await stack.enter_async_context(
                        cls(
                            gateway,
                            folder / "workspace",
                            model_id() if spec.mode == "live" else "offline-scripted",
                            spec.strategy,
                            relay=spec.engine in {"relay", "fabric"},
                            **target_kwargs,
                        )
                    )
                    entry["target"] = target
                    self.chats[session_id] = entry
                except BaseException as exc:
                    entry["state"].update(
                        status="cancelled" if isinstance(exc, asyncio.CancelledError) else "failed",
                        error=sanitize(f"{type(exc).__name__}: {str(exc)[:600]}"),
                        ended_at=now(),
                    )
                    try:
                        await stack.aclose()
                    finally:
                        entry["state"]["closed_at"] = now()
                        self._save_chat(entry)
                    if isinstance(exc, Exception):
                        exc.args = (f"{entry['state']['error']}. Saved evidence: {folder}",)
                    raise
            state = entry["state"]
            if len(state["turns"]) >= 3:
                raise ValueError(
                    f"The three-turn conversation limit is reached. Start a new conversation. Evidence: {entry['folder']}"
                )
            turn = {
                "turn": len(state["turns"]) + 1,
                "status": "running",
                "started_at": now(),
                "preferences": spec.preferences.model_dump(mode="json"),
            }
            state["turns"].append(turn)
            state["status"] = "running"
            self._save_chat(entry)
            try:
                result = await asyncio.wait_for(
                    entry["target"].reply(spec.preferences.goal, spec.preferences), timeout=150
                )
                turn.update(status="completed", ended_at=now(), outcome=result.get("outcome"))
                state["status"] = "ready" if len(state["turns"]) < 3 else "turn_limit_reached"
            except BaseException as exc:
                status = (
                    "cancelled"
                    if isinstance(exc, asyncio.CancelledError)
                    else "timed_out"
                    if isinstance(exc, TimeoutError)
                    else "failed"
                )
                detail = sanitize(f"{type(exc).__name__}: {str(exc)[:600]}")
                turn.update(status=status, ended_at=now(), error=detail)
                state.update(status=status, ended_at=now(), error=detail)
                # An incomplete harness invocation can have unknown memory state.
                # Release it, preserve the budget ledger and require a new ID.
                self.chats.pop(session_id, None)
                try:
                    await entry["stack"].aclose()
                finally:
                    state["closed_at"] = now()
                    self._save_chat(entry)
                if isinstance(exc, Exception):
                    exc.args = (f"{detail}. Start a new conversation. Saved evidence: {entry['folder']}",)
                raise
            finally:
                self._save_chat(entry)
            return {
                "session_id": session_id,
                "mode": spec.mode,
                "engine": spec.engine,
                **result,
                "matches": search_courses(spec.preferences, catalogue_path=entry["target"].catalogue_path)[
                    "matches"
                ],
                "calls": entry["budget"].calls,
                "usage": sanitize(entry["budget"].records),
                "turns": len(state["turns"]),
                "evidence_folder": str(entry["folder"]),
                "manifest": str(entry["folder"] / "chat.json"),
                "usage_file": str(entry["folder"] / "usage.json"),
                "trace": relay_evidence(entry["folder"], spec.mode == "live")
                if spec.engine == "relay"
                else None,
            }

    def _save_chat(self, entry):
        from .evidence import sanitize

        entry["state"].update(
            calls=entry["budget"].calls,
            budget=entry["budget"].limit,
            usage_file="usage.json",
            updated_at=now(),
        )
        atomic_json(entry["folder"] / "chat.json", sanitize(entry["state"]))
        atomic_json(entry["folder"] / "usage.json", sanitize(entry["budget"].records))

    async def close(self):
        for task in self.tasks.values():
            if not task.done():
                task.cancel()
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)
        await self._close_chats()
        for (*_scope, identity), session in list(self.managed_sessions.items()):
            cleanup_id = str(uuid.uuid4())
            folder = self.runs / "platform-jobs" / cleanup_id
            state = {"job_id": cleanup_id, "operation": "sessions_close", "target": session["bridge"].spec.target,
                     "status": "queued", "started_at": now(), "owner_pid": os.getpid(), "calls": 0,
                     "reason": "Application worker shutdown"}
            self.platform_state[cleanup_id] = state
            atomic_json(folder / "job.json", state)
            await self._platform_job(cleanup_id, session["bridge"], "sessions_close",
                                     {"name": identity}, folder, state)
        await self.deployment_stack.aclose()

    async def _close_chats(self):
        for entry in list(self.chats.values()):
            try:
                await entry["stack"].aclose()
            finally:
                entry["state"]["closed_at"] = now()
                if entry["state"]["status"] == "ready":
                    entry["state"]["status"] = "closed"
                self._save_chat(entry)
        self.chats.clear()
