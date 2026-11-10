"""Application services used by the CLI and SvelteKit worker."""

from __future__ import annotations

import asyncio
from contextlib import AsyncExitStack
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from typing import Literal
import uuid

from pydantic import Field

from .catalogue import Preferences, StrictModel, all_courses, search_courses
from .fabric_target import FabricTarget
from .inference import Budget, BudgetExceeded, Gateway
from .settings import ROOT, load_environment, model_id
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
    source: Literal["hf-profile-only", "ngc"] = "hf-profile-only"
    personas: int = Field(default=1, ge=1, le=3)
    strategies: list[Literal["concise", "clarification-first"]] = Field(default_factory=lambda: ["concise"])


class ChatSpec(StrictModel):
    preferences: Preferences
    session_id: str | None = None
    mode: Literal["demo", "live"] = "demo"
    engine: Literal["direct", "relay", "fabric"] = "direct"
    strategy: Literal["concise", "clarification-first"] = "concise"


class LabService:
    def __init__(self, runs: Path | None = None):
        self.runs = runs or ROOT / "runs"
        self.tasks: dict[str, asyncio.Task] = {}
        self.run_state: dict[str, dict] = {}
        self.lock = asyncio.Lock()
        self.chats: dict[str, dict] = {}
        self.recover_interrupted()

    def recover_interrupted(self):
        for path in self.runs.glob("*/run.json"):
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
            "version": "0.1.0",
            "nim_key_present": bool(os.getenv("NVIDIA_API_KEY")),
            "ngc_key_present": bool(os.getenv("NGC_CLI_API_KEY")),
            "model": model_id(),
            "catalogue_count": len(all_courses()),
            "snapshot_date": "2026-11-10",
            "active_run": next((k for k, task in self.tasks.items() if not task.done()), None),
            "personas_audited": (ROOT / "data/persona-audit.json").exists(),
            "limits": {"calls": 120, "output_tokens_per_call": 1024, "turns": 3, "concurrent_episodes": 1},
        }

    def list_runs(self):
        self.recover_interrupted()
        output = []
        for path in sorted(self.runs.glob("*/run.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:30]:
            try:
                output.append(json.loads(path.read_text()))
            except ValueError:
                continue
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

    async def start_run(self, spec: RunSpec):
        if any(not task.done() for task in self.tasks.values()) or self.lock.locked():
            raise ValueError("One model workload is already active; wait or cancel it first")
        if not spec.strategies or len(spec.strategies) != len(set(spec.strategies)):
            raise ValueError("Choose one or two distinct strategies")
        if spec.mode == "live":
            load_environment()
            if not os.getenv("NVIDIA_API_KEY"):
                raise ValueError("Configure NVIDIA_API_KEY before starting a live run")
        await self._close_chats()
        run_id = str(uuid.uuid4())
        folder = self.runs / run_id
        state = {
            "run_id": run_id,
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
            if value["type"] == "episode_completed":
                state["episodes"].append(value)
            atomic_json(folder / "run.json", state)

        try:
            async with self.lock:
                state["status"] = "running"
                atomic_json(folder / "run.json", state)
                async with Gateway(budget, spec.mode).serving() as gateway:
                    await asyncio.wait_for(
                        run_experiment(spec.model_dump(), folder, gateway, event), timeout=1800
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
        from .evaluation import run_helix, score_response

        run = self.get_run(run_id)
        if run["status"] in {"queued", "running"}:
            raise ValueError("Wait for the run to finish before scoring its saved replies")
        rows = []
        for index, event in enumerate(run["events"]):
            if event.get("role") != "assistant":
                continue
            checks = score_response(
                event["content"],
                Preferences(goal="saved conversation"),
                self.runs / run_id / "catalogue-snapshot.json",
            )
            for criterion in ["catalogue_grounding", "eligibility_caution", "fee_caution", "source_citation"]:
                rows.append(
                    {
                        "case_id": str(index),
                        "criterion": criterion,
                        "output": str(checks[criterion]).lower(),
                        "expected": "true",
                    }
                )
        if not rows:
            raise ValueError("This run has no saved assistant replies to evaluate")
        folder = self.runs / run_id
        atomic_json(folder / "helix-criteria.json", rows)
        result = await run_helix(folder / "helix-criteria.json", folder / "helix-results.json")
        state = json.loads((folder / "run.json").read_text())
        state["evaluation"] = result
        atomic_json(folder / "run.json", state)
        return result

    async def chat(self, spec: ChatSpec):
        if self.lock.locked() or any(not task.done() for task in self.tasks.values()):
            raise ValueError("A model workload is active; wait for it to finish or cancel it")
        async with self.lock:
            session_id = spec.session_id or str(uuid.uuid4())
            if not re.fullmatch(r"[a-f0-9-]{36}", session_id):
                raise ValueError("Invalid chat session ID")
            entry = self.chats.get(session_id)
            if spec.session_id and entry is None:
                raise ValueError("This chat session has ended. Start a new conversation.")
            signature = (spec.mode, spec.engine, spec.strategy)
            if entry and entry["signature"] != signature:
                raise ValueError("Start a new conversation when changing mode, harness or strategy")
            if not entry:
                # One retained conversation keeps plugin and adapter environments unambiguous.
                await self._close_chats()
                stack = AsyncExitStack()
                try:
                    budget = Budget()
                    gateway = await stack.enter_async_context(Gateway(budget, spec.mode).serving())
                    folder = self.runs / "chats" / session_id
                    if spec.engine == "relay":
                        import nemo_relay

                        await stack.enter_async_context(
                            nemo_relay.plugin.activate({}, str(relay_config(folder)))
                        )
                    cls = FabricTarget if spec.engine == "fabric" else DirectTarget
                    target = await stack.enter_async_context(
                        cls(
                            gateway,
                            folder / "workspace",
                            model_id() if spec.mode == "live" else "offline-scripted",
                            spec.strategy,
                            relay=spec.engine in {"relay", "fabric"},
                        )
                    )
                    entry = {
                        "stack": stack,
                        "target": target,
                        "budget": budget,
                        "signature": signature,
                        "folder": folder,
                    }
                    self.chats[session_id] = entry
                except BaseException:
                    await stack.aclose()
                    raise
            result = await asyncio.wait_for(
                entry["target"].reply(spec.preferences.goal, spec.preferences), timeout=150
            )
            return {
                "session_id": session_id,
                "mode": spec.mode,
                "engine": spec.engine,
                **result,
                "matches": search_courses(spec.preferences, catalogue_path=entry["target"].catalogue_path)[
                    "matches"
                ],
                "calls": entry["budget"].calls,
                "trace": relay_evidence(entry["folder"], spec.mode == "live")
                if spec.engine == "relay"
                else None,
            }

    async def close(self):
        for task in self.tasks.values():
            if not task.done():
                task.cancel()
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)
        await self._close_chats()

    async def _close_chats(self):
        for entry in list(self.chats.values()):
            await entry["stack"].aclose()
        self.chats.clear()
