"""Run the same application services from a terminal."""

import asyncio
import json

import typer

from .catalogue import Preferences, search_courses
from .service import ChatSpec, LabService, RunSpec
from .settings import ROOT, model_id

app = typer.Typer(no_args_is_help=True, pretty_exceptions_show_locals=False)


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
def chat(goal: str, live: bool = False, engine: str = "direct", budget: float | None = None):
    """Ask the advisor; --live spends a bounded NIM inference budget."""

    async def run():
        service = LabService()
        try:
            result = await service.chat(
                ChatSpec(
                    preferences=Preferences(goal=goal, budget_sgd=budget),
                    mode="live" if live else "demo",
                    engine=engine,
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
        overlays = await generate_overlays(folder / "overlays.json", 3)
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
