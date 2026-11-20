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
)

from .catalogue import Preferences, freeze_catalogue
from .fabric_target import FabricTarget
from .inference import Gateway
from .personas import DATASET, REVISION
from .probe import LearningAdvisorProbe  # Registers the extension before resolving inputs.
from .settings import model_id
from .target import DirectTarget, relay_config


def host_models(mode="live"):
    return {
        f"{role}_model": HostRoleModel(
            model_name=model_id(role) if mode == "live" else "offline-scripted", max_tokens=1024
        )
        for role in ["user", "assistant", "judge", "summary"]
    }


def prepare_rows(
    source: str,
    count: int = 1,
    max_turns: int = 3,
    *,
    source_ids=None,
    seed=None,
    story_id="profile-goal",
    profiles_selection=None,
) -> list[dict]:
    if source not in {"hf-profile-only", "ngc", "generated"}:
        raise ValueError("Choose Singapore HF profile-only, NGC Extended, or a saved generated dataset")
    from .datasets import lock_personas, sample_personas

    if source == "generated" and profiles_selection is None:
        raise ValueError("Choose a saved Data Designer job for generated profiles")
    selection = profiles_selection or (
        lock_personas(source, source_ids) if source_ids else sample_personas(source, count=count, seed=seed)
    )
    chosen = selection["rows"]
    if len(chosen) != count:
        raise ValueError("The locked profile count does not match the requested episode count")
    config = ConversationSimulatorConfig(
        name="conversation",
        locale="en_SG",
        max_turns=max_turns,
        max_query_attempts=1,
        max_assistant_attempts=1,
        context_compression=False,
        persona_grounding_ratio=1,
        probe_options={"learning_advisor": {"profile_only": source != "ngc"}},
    )
    rows = []
    for i, person in enumerate(chosen):
        from .stories import story

        selected_story = story(story_id)
        theme = (
            {"description": selected_story["question"]}
            if selected_story["question"]
            else LearningAdvisorProbe.themes("en_SG")[i % 3]
        )
        data = {
            "persona": person,
            "probe_type": "learning_advisor",
            "theme": theme,
            "persona_grounding": True,
        }
        if source != "ngc":
            data.update(behavioral_profile={}, user_interaction_style="neutral")
        overlay = selection.get("overlays", {}).get(person.get("uuid"))
        if overlay:
            data["learning_overlay"] = overlay
        row = construct_episode_preamble(data, config=config, models=host_models()).to_row()
        row.update(
            usersim_config=config.model_dump(mode="json"),
            source_distribution=selection.get("source_distribution", source),
            source_revision=selection.get("source_revision", REVISION),
            source_dataset=selection.get("source_dataset", selection.get("dataset", DATASET)),
            behavior_basis=(
                "Source behavioural fields interpreted by the public UserSim preamble API."
                if source == "ngc"
                else "No OCEAN conditioning. UserSim loop defaults are operational settings, not source traits."
            ),
            source_lineage=selection.get("lineage", {}).get(person.get("uuid")),
            selection=selection.get("selection", {"seed": seed, "source_ids": source_ids}),
            story_id=story_id,
            scenario_base_theme=copy.deepcopy(theme),
        )
        rows.append(row)
    return rows


def bind_scenario(
    row: dict, selected_story: dict, budget_override_sgd=None
) -> tuple[dict, Preferences | None]:
    """Bind an explicitly selected saved scenario; custom columns never become policy.

    Only the closed Designer scenario's typed goal/budget enter Preferences.
    Availability remains narrative: days are not inferred from generated text.
    """
    overlay = row.get("learning_overlay") or {}
    scenario = overlay.get("scenario")
    raw = copy.deepcopy(selected_story["preferences"])
    theme = copy.deepcopy(row.get("scenario_base_theme", row.get("theme", {})))
    binding = {
        "kind": "named-story" if raw else "profile-goal",
        "title": selected_story["title"],
        "story_id": selected_story["id"],
        "hypothesis": False,
    }
    if scenario is not None:
        from .designer_schema import SCENARIO_SCHEMA, validate_json_schema

        validate_json_schema(scenario, SCENARIO_SCHEMA)
        raw = {"goal": scenario["learning_goal"], "budget_sgd": scenario["budget_sgd"]}
        theme = {"description": scenario["opening_message"]}
        binding.update(
            kind="approved-designer-scenario",
            title=scenario["story_title"],
            hypothesis=True,
            overlay_id=overlay["overlay_id"],
            original_profile_sha256=overlay["original_profile_sha256"],
            basis="Developer explicitly selected this saved hypothetical scenario as simulation input",
        )
    elif selected_story["question"]:
        theme = {"description": selected_story["question"]}
    overrides = {}
    if budget_override_sgd is not None:
        overrides["budget_sgd"] = budget_override_sgd
        if raw:
            raw["budget_sgd"] = budget_override_sgd
        theme = {
            "description": theme.get("description", "Explore learning")
            + f" The explicit total budget is now S${budget_override_sgd}; this replaces any earlier scenario budget."
        }
    prefs = Preferences.model_validate(raw) if raw else None
    binding.update(
        preferences=prefs.model_dump(mode="json") if prefs else None, constraint_overrides=overrides
    )
    row.update(theme=theme, scenario_binding=binding)
    return binding, prefs


async def hosted_episode(
    row: dict, gateway: Gateway, target, on_event, preferences=None, constraint_overrides=None
) -> dict:
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
                explicit = preferences
                if explicit is None and constraint_overrides:
                    explicit = Preferences(goal=message, **constraint_overrides)
                reply = await target.reply(message, explicit) if explicit else await target.reply(message)
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
    spec: dict,
    folder: Path,
    gateway: Gateway,
    save_event,
    resolved_rows=None,
    catalogue_path=None,
    profiles_selection=None,
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
            else prepare_rows(
                spec["source"],
                spec["personas"],
                spec.get("turns", 3),
                source_ids=spec.get("source_ids"),
                seed=spec.get("seed"),
                story_id=spec.get("story_id", "profile-goal"),
                profiles_selection=profiles_selection,
            )
        )
        if spec["mode"] == "live"
        else []
    )
    if spec.get("enrichment"):
        if spec["source"] != "hf-profile-only" or spec["mode"] != "live":
            raise ValueError("Legacy categorical overlays apply only to live HF profile-only inputs")
        from .enrichment import apply_overlays, generate_overlays

        rows = apply_overlays(
            rows, await generate_overlays(folder / "overlays.json", len(rows), resolved_rows=rows)
        )
    results = []
    from .stories import story

    selected_story = story(spec.get("story_id", "profile-goal"))
    scenario_rows = rows or [{} for _ in range(spec["personas"])]
    if not rows and profiles_selection:
        if len(profiles_selection["rows"]) != spec["personas"]:
            raise ValueError("The saved scenario selection does not match the requested episode count")
        for row, profile in zip(scenario_rows, profiles_selection["rows"]):
            row["learning_overlay"] = profiles_selection.get("overlays", {}).get(profile["uuid"], {})
    bound = [bind_scenario(row, selected_story, spec.get("budget_override_sgd")) for row in scenario_rows]
    if rows:
        (folder / "resolved-inputs.json").write_text(json.dumps(rows, indent=2, default=str))
    await save_event({"type": "scenarios_bound", "scenarios": [binding for binding, _prefs in bound]})
    demo_goals = ["project management", "photography", "calligraphy"]
    for index in range(spec["personas"]):
        binding, scenario_preferences = bound[index]
        for strategy in spec["strategies"]:
            episode_id = str(uuid.uuid4())
            episode_folder = folder / episode_id
            summary = {
                "episode_id": episode_id,
                "persona_index": index,
                "strategy": strategy,
                "source": spec["source"] if spec["mode"] == "live" else "scripted-demo",
                "story_id": selected_story["id"],
                "source_id": rows[index].get("persona", {}).get("uuid") if rows else None,
                "preferences": scenario_preferences.model_dump(mode="json") if scenario_preferences else None,
                "scenario_binding": binding,
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
                    target_kwargs = (
                        {
                            "harness": spec.get("harness", "deepagents"),
                            "model_route": spec.get("model_route", "fixed"),
                        }
                        if target_class is FabricTarget
                        else {}
                    )
                    target = await stack.enter_async_context(
                        target_class(
                            gateway,
                            episode_folder / "workspace",
                            model_id() if spec["mode"] == "live" else "offline-scripted",
                            strategy=strategy,
                            relay=spec["engine"] in {"relay", "fabric"},
                            catalogue_path=catalogue_path,
                            **target_kwargs,
                        )
                    )

                    async def emit(event):
                        await save_event({"episode_id": episode_id, "type": "message", **event})

                    if spec["mode"] == "demo":
                        message = (
                            scenario_rows[index].get("theme", {}).get("description")
                            or selected_story["question"]
                            or f"I want to learn {demo_goals[index % len(demo_goals)]}"
                        )
                        await emit({"role": "user", "content": message})
                        reply = await target.reply(
                            message,
                            scenario_preferences
                            or Preferences(
                                goal=demo_goals[index % len(demo_goals)], **binding["constraint_overrides"]
                            ),
                        )
                        await emit({"role": "assistant", **reply})
                        result = {"mode": "demo", "source": "scripted goals; no persona sampled"}
                    else:
                        result = await hosted_episode(
                            rows[index],
                            gateway,
                            target,
                            emit,
                            scenario_preferences,
                            binding["constraint_overrides"],
                        )
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
