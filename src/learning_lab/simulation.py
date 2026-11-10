"""Paired experiments using UserSim's external runtime and immutable resolved inputs."""

from __future__ import annotations

from contextlib import AsyncExitStack
import copy
import json
from pathlib import Path
import uuid

from usersim.engine.config import ConversationSimulatorConfig
from usersim.engine.external import (
    ActivationRequest,
    HostRoleModel,
    ProbeEpisodeRuntime,
    construct_episode_preamble,
    materialize_episode_inputs,
)

from .catalogue import Preferences, freeze_catalogue
from .fabric_target import FabricTarget
from .inference import Gateway
from .personas import DATASET, REVISION
from .probe import LearningAdvisorProbe  # Registers the extension before resolving inputs.
from .settings import ROOT, model_id
from .target import DirectTarget, relay_config


def host_models(mode="live"):
    return {
        f"{role}_model": HostRoleModel(
            model_name=model_id(role) if mode == "live" else "offline-scripted", max_tokens=1024
        )
        for role in ["user", "assistant", "judge", "summary"]
    }


def prepare_rows(source: str, count: int = 3, max_turns: int = 3) -> list[dict]:
    if source == "ngc":
        return materialize_episode_inputs(
            locale="en_SG",
            num_rows=count,
            probe_mix={"learning_advisor": 1.0},
            random_seed=42,
            max_turns=max_turns,
            max_assistant_attempts=1,
            models_path=ROOT / "configs/models.toml",
        )
    if source != "hf-profile-only":
        raise ValueError("Choose ngc or explicitly labelled hf-profile-only")
    path = ROOT / "data/persona-review-panel.json"
    if not path.exists():
        raise ValueError("Run scripts/inspect_personas.py --download before selecting public profiles")
    panel = json.loads(path.read_text())
    chosen = [next(r for r in panel if r["group"] == group) for group in ["early", "mid", "older"]][:count]
    config = ConversationSimulatorConfig(
        name="conversation",
        locale="en_SG",
        max_turns=max_turns,
        max_query_attempts=1,
        max_assistant_attempts=1,
        context_compression=False,
        persona_grounding_ratio=1,
        probe_options={"learning_advisor": {"profile_only": True}},
    )
    rows = []
    for i, person in enumerate(chosen):
        data = {
            "persona": person,
            "probe_type": "learning_advisor",
            "theme": LearningAdvisorProbe.themes("en_SG")[i % 3],
            "behavioral_profile": {},
            "user_interaction_style": "neutral",
            "persona_grounding": True,
        }
        row = construct_episode_preamble(data, config=config, models=host_models()).to_row()
        row.update(
            usersim_config=config.model_dump(mode="json"),
            source_distribution="hf-profile-only",
            source_revision=REVISION,
            source_dataset=DATASET,
            behavior_basis="No OCEAN conditioning. UserSim loop defaults are operational settings, not source traits.",
        )
        rows.append(row)
    return rows


async def hosted_episode(row: dict, gateway: Gateway, target, on_event) -> dict:
    runtime = ProbeEpisodeRuntime.from_resolved_row(copy.deepcopy(row), models=host_models(gateway.mode))
    try:
        event = await runtime.advance()
        while isinstance(event, ActivationRequest):
            if event.role == "assistant":
                if event.continues_turn:
                    raise RuntimeError("Unexpected assistant resampling in a side-effectful external target")
                message = next(m["content"] for m in reversed(event.messages) if m["role"] == "user")
                await on_event({"role": "user", "content": message})
                previous = len(gateway.budget.records)
                reply = await target.reply(message)
                await on_event({"role": "assistant", **reply})
                response = {"role": "assistant", "content": reply["content"]}
                calls = gateway.budget.records[previous:]
                usage = (
                    {
                        "input_tokens": sum(c["usage"]["prompt_tokens"] for c in calls),
                        "output_tokens": sum(c["usage"]["completion_tokens"] for c in calls),
                    }
                    if calls and all(c.get("usage") for c in calls)
                    else None
                )
            else:
                payload = {
                    **event.parameters,
                    "model": model_id(event.role),
                    "messages": list(event.messages),
                    "reasoning_effort": "none",
                }
                if event.tools_enabled and event.tools:
                    payload["tools"] = list(event.tools)
                result = await gateway.complete(payload, role=event.role)
                raw = result["choices"][0]["message"]
                response = {
                    k: v
                    for k, v in raw.items()
                    if k in {"role", "content", "reasoning_content", "tool_calls"} and v is not None
                }
                response.setdefault("content", "")
                raw_usage = result.get("usage") or {}
                usage = {
                    "input_tokens": raw_usage.get("prompt_tokens"),
                    "output_tokens": raw_usage.get("completion_tokens"),
                }
            recorded = {"activation_id": event.activation_id, "response": response}
            if usage and all(v is not None for v in usage.values()):
                recorded["usage"] = usage
            event = await runtime.advance(recorded)
        return await runtime.finalize()
    finally:
        await runtime.close()


async def run_experiment(
    spec: dict, folder: Path, gateway: Gateway, save_event, resolved_rows=None, catalogue_path=None
):
    """Run isolated conditions; preserve failures and never exceed the shared inference cap."""
    catalogue_path = catalogue_path or folder / "catalogue-snapshot.json"
    catalogue_hash = freeze_catalogue(catalogue_path)
    await save_event(
        {
            "type": "inputs_frozen",
            "catalogue_sha256": catalogue_hash,
            "models": {role: model_id(role) for role in ["assistant", "user", "judge", "summary"]}
            if spec["mode"] == "live"
            else {"assistant": "offline-scripted"},
        }
    )
    rows = (
        (
            copy.deepcopy(resolved_rows)
            if resolved_rows is not None
            else prepare_rows(spec["source"], spec["personas"], spec.get("turns", 3))
        )
        if spec["mode"] == "live"
        else []
    )
    if spec.get("enrichment"):
        if spec["source"] != "hf-profile-only" or spec["mode"] != "live":
            raise ValueError("This enrichment seed is the audited HF panel; choose live HF profile-only mode")
        from .enrichment import apply_overlays, generate_overlays

        rows = apply_overlays(rows, await generate_overlays(folder / "overlays.json", 3))
    if rows:
        (folder / "resolved-inputs.json").write_text(json.dumps(rows, indent=2, default=str))
    results = []
    demo_goals = ["project management", "photography", "calligraphy"]
    for index in range(spec["personas"]):
        for strategy in spec["strategies"]:
            episode_id = str(uuid.uuid4())
            episode_folder = folder / episode_id
            summary = {
                "episode_id": episode_id,
                "persona_index": index,
                "strategy": strategy,
                "source": spec["source"] if spec["mode"] == "live" else "scripted-demo",
            }
            await save_event({"type": "episode_started", **summary})
            try:
                target_class = FabricTarget if spec["engine"] == "fabric" else DirectTarget
                async with AsyncExitStack() as stack:
                    if spec["engine"] == "relay":
                        import nemo_relay

                        await stack.enter_async_context(
                            nemo_relay.plugin.activate({}, str(relay_config(episode_folder)))
                        )
                    target = await stack.enter_async_context(
                        target_class(
                            gateway,
                            episode_folder / "workspace",
                            model_id() if spec["mode"] == "live" else "offline-scripted",
                            strategy=strategy,
                            relay=spec["engine"] in {"relay", "fabric"},
                            catalogue_path=catalogue_path,
                        )
                    )

                    async def emit(event):
                        await save_event({"episode_id": episode_id, "type": "message", **event})

                    if spec["mode"] == "demo":
                        message = f"I want to learn {demo_goals[index]}"
                        await emit({"role": "user", "content": message})
                        reply = await target.reply(message, Preferences(goal=demo_goals[index]))
                        await emit({"role": "assistant", **reply})
                        result = {"mode": "demo", "source": "scripted goals; no persona sampled"}
                    else:
                        result = await hosted_episode(rows[index], gateway, target, emit)
                        (episode_folder / "usersim-result.json").write_text(
                            json.dumps(result, indent=2, default=str)
                        )
                    outcome = result.get("simulation_outcome", {})
                    if isinstance(outcome, str):
                        outcome = json.loads(outcome)
                    summary.update(
                        status="completed" if outcome.get("status", "ok") == "ok" else outcome["status"],
                        turns=result.get("num_turns"),
                        outcome=outcome,
                    )
            except Exception as exc:
                from .inference import BudgetExceeded

                if isinstance(exc, BudgetExceeded) or gateway.budget.calls >= gateway.budget.limit:
                    raise BudgetExceeded("The experiment reached its model or tool-call budget") from exc
                summary.update(status="failed", error=f"{type(exc).__name__}: {str(exc)[:500]}")
            results.append(summary)
            await save_event({"type": "episode_completed", **summary})
    return results
