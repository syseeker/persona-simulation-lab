"""Run the same application services from a terminal."""

import asyncio
import json

import typer

from .catalogue import Preferences, search_courses
from .service import ChatSpec, LabService, RunSpec
from .settings import ROOT, model_id

app = typer.Typer(no_args_is_help=True, pretty_exceptions_show_locals=False)
personas_app = typer.Typer(no_args_is_help=True, help="Browse and sample original local profiles.")
workbench_app = typer.Typer(
    no_args_is_help=True, help="Preview and run the same Data Designer jobs as the UI."
)
platform_app = typer.Typer(
    no_args_is_help=True, help="Explicit Helix Platform operations; status is read-only."
)
app.add_typer(personas_app, name="personas")
app.add_typer(workbench_app, name="workbench")
app.add_typer(platform_app, name="platform")
guide_app = typer.Typer(no_args_is_help=True, help='Photography guide: shared services and exact saved-run evidence.')
app.add_typer(guide_app, name='guide')


def _guide_command(action: str, parameters: dict):
    async def run():
        from .journey import JourneyService
        service = JourneyService()
        try:
            result = await service.dispatch({'action': action, **parameters})
            if action == 'start':
                await service.tasks[result['run_id']]
                result = service.get(result['run_id'])
            print(json.dumps(result, indent=2, default=str))
            if result.get('status') in {'failed', 'cancelled'}:
                raise typer.Exit(1)
        finally:
            await service.close()
    asyncio.run(run())


@guide_app.command('status')
def guide_status():
    """Check dataset/proxy/native prerequisites without inference."""
    _guide_command('readiness', {})


@guide_app.command('sample')
def guide_sample(source: str = 'ngc'):
    """Sample and lock one original; use its ID and hash in an explicit start."""
    _guide_command('sample', {'source': source})


@guide_app.command('start')
def guide_start(source_id: str, original_sha256: str, source: str = 'ngc'):
    """Run one actual bounded photography condition, await evidence and cleanup."""
    _guide_command('start', {'spec': {'scenario_id': 'photography', 'source': source,
                                    'source_id': source_id, 'original_sha256': original_sha256}})


@guide_app.command('runs')
def guide_runs():
    _guide_command('list', {'scenario_id': 'photography'})


@guide_app.command('trace')
def guide_trace(run_id: str):
    _guide_command('trace', {'run_id': run_id})


@guide_app.command('artifact')
def guide_artifact(run_id: str, artifact_id: str):
    _guide_command('artifact', {'run_id': run_id, 'artifact_id': artifact_id})


@guide_app.command('recover')
def guide_recover(run_id: str):
    """Explicitly verify ownership and clean up only this interrupted condition."""
    _guide_command('recover', {'run_id': run_id})


def _object(value: str) -> dict:
    try:
        result = json.loads(value)
    except ValueError as exc:
        raise typer.BadParameter("Supply a JSON object") from exc
    if not isinstance(result, dict):
        raise typer.BadParameter("Supply a JSON object")
    return result


def _service_command(operation):
    """Keep the service alive until any job created by this command is terminal."""

    async def run():
        service = LabService()
        try:
            result = operation(service)
            if asyncio.iscoroutine(result):
                result = await result
            if isinstance(result, dict) and result.get("job_id") in service.tasks:
                await service.tasks[result["job_id"]]
                if result["job_id"] in getattr(service, "workbench_state", {}):
                    result = service.get_workbench(result["job_id"])
                elif result["job_id"] in getattr(service, "platform_state", {}):
                    result = service.get_platform_job(result["job_id"])
            print(json.dumps(result, indent=2, default=str))
            if isinstance(result, dict) and result.get("status") in {"failed", "cancelled", "timed_out"}:
                raise typer.Exit(1)
        finally:
            await service.close()

    asyncio.run(run())


@app.command()
def stories():
    """List the distinct guided stories and their intended learning outcomes."""
    from .stories import list_stories

    print(json.dumps(list_stories(), indent=2))


@app.command()
def datasets():
    """Inspect available dataset distributions without downloading or inference."""
    _service_command(lambda service: service.dataset_catalogue())


@personas_app.command("browse")
def personas_browse(query: str = "{}"):
    """Browse using a JSON DatasetQuery, including source, filters and pagination."""
    params = _object(query)
    _service_command(lambda service: service.browse_personas(params))


@personas_app.command("options")
def personas_options(source: str = "hf-profile-only"):
    """Show location and education filter options from the installed source."""
    _service_command(lambda service: service.persona_facets(source))


@personas_app.command("sample")
def personas_sample(source: str = "hf-profile-only", count: int = 1, seed: int = 42, filters: str = "{}"):
    """Seeded sampling without replacement; no model calls."""
    params = {"source": source, "count": count, "seed": seed, "filters": _object(filters)}
    _service_command(lambda service: service.sample_personas(params))


@app.command()
def evidence(run_id: str, episode_id: str | None = None):
    """Read native Relay scopes, Fabric lifecycle and allowlisted saved artifacts."""
    _service_command(lambda service: service.get_evidence(run_id, episode_id))


@app.command()
def artifact(run_id: str, artifact_id: str, episode_id: str | None = None):
    """Read one sanitized artifact ID returned by evidence; paths are not accepted."""
    _service_command(lambda service: service.get_artifact(run_id, artifact_id, episode_id))


@app.command()
def source(source_id: str = typer.Argument("application")):
    """Read an allowlisted integration entry point by ID."""
    from .source_index import source_excerpt

    print(json.dumps(source_excerpt(source_id), indent=2))


@workbench_app.command("preview")
def workbench_preview(spec: str):
    """Preview a JSON WorkbenchSpec and source lineage without generation."""
    from .workbench import prepare_workbench

    print(json.dumps(prepare_workbench(_object(spec)), indent=2, default=str))


@workbench_app.command("start")
def workbench_start(spec: str):
    """Start a JSON WorkbenchSpec and await its terminal result before exiting."""
    params = _object(spec)
    _service_command(lambda service: service.start_workbench(params))


@workbench_app.command("job")
def workbench_job(job_id: str):
    """Inspect a saved Designer job."""
    _service_command(lambda service: service.get_workbench(job_id))


@workbench_app.command("cancel")
def workbench_cancel(job_id: str):
    """Cancel only a task owned by this worker; another worker must cancel its own job."""

    async def cancel_owned(service):
        state = service.get_workbench(job_id)
        if state.get("status") in {"queued", "running"} and job_id not in service.tasks:
            return {
                "job_id": job_id,
                "status": state["status"],
                "cancellation_requested": False,
                "reason": "This job belongs to another worker. Cancel it through the UI or MCP session that started it.",
            }
        return await service.cancel_workbench(job_id)

    _service_command(cancel_owned)


@platform_app.command("status")
def platform_status(target: str = "local"):
    """Probe configured Platform reachability without deployment or inference."""
    _service_command(lambda service: service.platform_action({"operation": "status", "target": target}))


@platform_app.command("action")
def platform_action(operation: str, arguments: str = "{}", target: str = "local"):
    """Run an explicit allowlisted Platform operation and await any created job."""
    params = {"operation": operation, "arguments": _object(arguments), "target": target}
    _service_command(lambda service: service.platform_action(params))


@platform_app.command("job")
def platform_job(job_id: str):
    """Inspect a saved Platform action job; this does not re-run the action."""
    _service_command(lambda service: service.get_platform_job(job_id))


async def _platform_conversation(service, deployment, messages, preferences, model_route, target):
    """Keep session ownership and its original constraints in one service lifespan."""

    async def action(operation, **arguments):
        result = await service.platform_action(
            {"operation": operation, "target": target, "arguments": arguments}
        )
        if result.get("job_id") in service.tasks:
            await service.tasks[result["job_id"]]
            result = service.get_platform_job(result["job_id"])
        return result

    created = await action("sessions_create", deployment=deployment)
    result = {"status": created["status"], "created": created, "turns": [], "closure": None}
    if created["status"] != "completed":
        return result
    session = created.get("result", {}).get("session", {})
    session_id = session.get("name") or session.get("id") or session.get("entity_id")
    if not session_id:
        raise ValueError("Platform did not return a confirmed conversation session identity")
    result["session_id"] = session_id
    try:
        for message in messages:
            turn = await action(
                "invoke",
                deployment=deployment,
                session_id=session_id,
                input=message,
                preferences=preferences,
                model_route=model_route,
            )
            result["turns"].append(turn)
            if turn["status"] != "completed":
                result["status"] = turn["status"]
                break
    finally:
        result["closure"] = await action("sessions_close", name=session_id)
        if result["closure"]["status"] != "completed":
            result["status"] = result["closure"]["status"]
    return result


@platform_app.command("conversation")
def platform_conversation(
    deployment: str,
    messages: str = typer.Option(..., help="JSON array of one to three public learner messages."),
    preferences: str = typer.Option(..., help="JSON Preferences object with a goal and budget_sgd."),
    model_route: str = "fixed",
    target: str = "local",
):
    """Create, invoke and close a live Platform conversation in one owned service."""
    try:
        turns = json.loads(messages)
    except ValueError as exc:
        raise typer.BadParameter("Supply one to three messages as a JSON array") from exc
    if (
        not isinstance(turns, list)
        or not 1 <= len(turns) <= 3
        or any(
            not isinstance(message, str) or not message.strip() or len(message) > 10_000 for message in turns
        )
    ):
        raise typer.BadParameter("Supply one to three nonempty messages of at most 10,000 characters each")
    params = _object(preferences)
    if params.get("budget_sgd") is None or isinstance(params["budget_sgd"], bool):
        raise typer.BadParameter("Supply an explicit nonnegative budget_sgd with the learning goal")
    try:
        prefs = Preferences.model_validate(params).model_dump(mode="json")
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    if model_route not in {"fixed", "switchyard"} or target not in {"local", "remote"}:
        raise typer.BadParameter("Choose model route fixed or switchyard and target local or remote")
    _service_command(
        lambda service: _platform_conversation(service, deployment, turns, prefs, model_route, target)
    )


@app.command()
def doctor():
    """Check configuration without making any inference call."""
    from nemo_fabric import Fabric
    from .fabric_target import build_config

    service = LabService()
    status = service.status()
    plan = Fabric().plan(
        build_config(ROOT / "runs/doctor/workspace", model_id(), "http://127.0.0.1:1/v1"), base_dir=ROOT
    )
    status["fabric_adapter"] = plan.adapter.adapter_id
    status["isolated_environments"] = {
        name: (ROOT / f"integrations/{name}/.venv/bin/python").exists() for name in ["helix", "designer"]
    }
    print(json.dumps(status, indent=2))


@app.command()
def search(goal: str, budget: float | None = None):
    print(json.dumps(search_courses(Preferences(goal=goal, budget_sgd=budget)), indent=2))


@app.command()
def chat(
    goal: str,
    live: bool = False,
    engine: str = "direct",
    budget: float | None = None,
    harness: str = "deepagents",
    model_route: str = "fixed",
):
    """Ask the advisor; --live spends a bounded NIM inference budget."""

    async def run():
        service = LabService()
        try:
            result = await service.chat(
                ChatSpec(
                    preferences=Preferences(goal=goal, budget_sgd=budget),
                    mode="live" if live else "demo",
                    engine=engine,
                    harness=harness,
                    model_route=model_route,
                )
            )
            print(json.dumps(result, indent=2))
        finally:
            await service.close()

    asyncio.run(run())


@app.command()
def simulate(
    live: bool = False,
    engine: str = "direct",
    source: str = "hf-profile-only",
    personas: int = 1,
    paired: bool = False,
    turns: int = 3,
    story: str = "profile-goal",
    seed: int | None = None,
    source_ids: str = "",
    harness: str = "deepagents",
    model_route: str = "fixed",
    generated_job_id: str | None = None,
    overlay_job_id: str | None = None,
):
    """Run one episode; --paired compares two strategies on saved identical inputs."""

    async def run():
        service = LabService()
        spec = RunSpec(
            mode="live" if live else "demo",
            engine=engine,
            source=source,
            personas=personas,
            turns=turns,
            story_id=story,
            seed=seed,
            source_ids=[value.strip() for value in source_ids.split(",") if value.strip()],
            harness=harness,
            model_route=model_route,
            generated_job_id=generated_job_id,
            overlay_job_id=overlay_job_id,
            strategies=["concise", "clarification-first"] if paired else ["concise"],
        )
        try:
            state = await service.start_run(spec)
            print(
                json.dumps(
                    {
                        "run_id": state["run_id"],
                        "spec": spec.model_dump(),
                        "limits": service.status()["limits"],
                    }
                ),
                flush=True,
            )
            await service.tasks[state["run_id"]]
            final = service.get_run(state["run_id"])
            print(json.dumps({k: v for k, v in final.items() if k not in {"events", "usage"}}, indent=2))
            if final["status"] not in {"completed", "completed_with_warnings"}:
                raise typer.Exit(1)
        finally:
            await service.close()

    asyncio.run(run())


@app.command()
def benchmark(live: bool = False):
    """Generate fresh held-out responses, then score with the isolated Helix SDK."""
    from .evaluation import compare_strategies, run_helix
    from uuid import uuid4

    async def run():
        folder = ROOT / "runs/benchmarks" / str(uuid4())
        manifest = await compare_strategies(folder, "live" if live else "demo")
        result = await run_helix(folder / "criteria.json", folder / "helix-results.json")
        print(
            json.dumps({"manifest": {k: v for k, v in manifest.items() if k != "usage"}, **result}, indent=2)
        )

    asyncio.run(run())


@app.command()
def evaluate(run_id: str):
    """Score saved replies with local Helix checks; no additional model calls."""

    async def run():
        service = LabService()
        try:
            print(json.dumps(await service.evaluate_run(run_id), indent=2))
        finally:
            await service.close()

    asyncio.run(run())


@app.command()
def enrich(count: int = 3):
    """Generate labelled preference overlays in the isolated Data Designer environment."""
    from .enrichment import generate_overlays

    async def run():
        result = await generate_overlays(ROOT / "data/learning-overlays.json", count)
        print(json.dumps({k: v for k, v in result.items() if k != "records"}, indent=2))

    asyncio.run(run())


@app.command()
def ablate(live: bool = False):
    """Compare one identical source profile with and without a hypothetical preference overlay."""
    import uuid
    from .enrichment import apply_overlays, generate_overlays
    from .catalogue import freeze_catalogue
    from .inference import Budget, Gateway
    from .simulation import prepare_rows, run_experiment
    from .service import atomic_json

    async def run():
        folder = ROOT / "runs/ablations" / str(uuid.uuid4())
        folder.mkdir(parents=True)
        rows = prepare_rows("hf-profile-only", 1)
        overlays = await generate_overlays(folder / "overlays.json", len(rows), resolved_rows=rows)
        enriched = apply_overlays(rows, overlays)
        assert rows[0]["persona"] == enriched[0]["persona"]
        atomic_json(folder / "without-overlay.json", rows)
        atomic_json(folder / "with-overlay.json", enriched)
        results = {}
        catalogue_path = folder / "catalogue-snapshot.json"
        catalogue_hash = freeze_catalogue(catalogue_path)
        if live:
            async with Gateway(Budget(120), "live").serving() as gateway:
                for condition, inputs in [("without-overlay", rows), ("with-overlay", enriched)]:
                    destination = folder / condition
                    destination.mkdir()

                    async def event(value):
                        with (destination / "events.jsonl").open("a") as stream:
                            stream.write(json.dumps(value, default=str) + "\n")

                    results[condition] = await run_experiment(
                        {
                            "mode": "live",
                            "source": "hf-profile-only",
                            "personas": 1,
                            "engine": "direct",
                            "strategies": ["concise"],
                        },
                        destination,
                        gateway,
                        event,
                        resolved_rows=inputs,
                        catalogue_path=catalogue_path,
                    )
                calls = gateway.budget.calls
        else:
            calls = 0
        report = {
            "source_profile_preserved": True,
            "live": live,
            "calls": calls,
            "catalogue_sha256": catalogue_hash,
            "results": results,
            "notice": "Generated preferences are hypotheses. This small ablation does not establish human validity.",
        }
        atomic_json(folder / "report.json", report)
        print(json.dumps({**report, "folder": str(folder)}, indent=2))

    asyncio.run(run())


def main():
    app()


if __name__ == "__main__":
    main()
