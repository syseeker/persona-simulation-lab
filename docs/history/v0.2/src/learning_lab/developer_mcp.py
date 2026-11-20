"""Host-only developer MCP service, separate from the advisor's course tools.

Run with learning-lab-developer-mcp. One asynchronous lifespan owns one service
and its queued tasks; disconnecting closes owned jobs and SDK resources. Never
register this server in DirectTarget, FabricTarget or a packaged citizen agent.
"""

from contextlib import asynccontextmanager

from mcp.server.fastmcp import Context, FastMCP

from .service import LabService, RunSpec


@asynccontextmanager
async def lifespan(_server):
    service = LabService()
    try:
        yield {"service": service}
    finally:
        await service.close()


mcp = FastMCP("Learning lab developer services", lifespan=lifespan)


def _service(ctx: Context) -> LabService:
    return ctx.request_context.lifespan_context["service"]


@mcp.tool()
def lab_status(ctx: Context) -> dict:
    """Read configuration presence and bounded-workload status; no inference."""
    return _service(ctx).status()


@mcp.tool()
def lab_stories() -> list[dict]:
    """Read the guided stories and their distinct learning goals."""
    from .stories import list_stories

    return list_stories()


@mcp.tool()
def lab_datasets(ctx: Context) -> dict:
    """Read dataset distributions and local availability without downloading assets."""
    return _service(ctx).dataset_catalogue()


@mcp.tool()
def lab_personas_browse(query: dict, ctx: Context) -> dict:
    """Browse original profiles using the same validated DatasetQuery as the UI."""
    return _service(ctx).browse_personas(query)


@mcp.tool()
def lab_personas_sample(
    source: str, count: int, seed: int, ctx: Context, filters: dict | None = None
) -> dict:
    """Sample original profiles without replacement; no model calls."""
    return _service(ctx).sample_personas(
        {"source": source, "count": count, "seed": seed, "filters": filters or {}}
    )


@mcp.tool()
def lab_sources() -> list[dict]:
    """List allowlisted source-code integration entry points."""
    from .source_index import integration_sources

    return integration_sources()


@mcp.tool()
def lab_source(source_id: str) -> dict:
    """Read one known integration source ID; arbitrary paths are not accepted."""
    from .source_index import source_excerpt

    return source_excerpt(source_id)


@mcp.tool()
def lab_runs(ctx: Context, mode: str | None = None) -> list[dict]:
    """List the most recent saved experiments for an inference mode."""
    return _service(ctx).list_runs(mode)


@mcp.tool()
def lab_run(run_id: str, ctx: Context) -> dict:
    """Inspect one saved experiment, including partial results and failures."""
    return _service(ctx).get_run(run_id)


@mcp.tool()
def lab_evidence(run_id: str, ctx: Context, episode_id: str | None = None) -> dict:
    """Inspect native Relay scopes, Fabric lifecycle and allowed artifact IDs."""
    return _service(ctx).get_evidence(run_id, episode_id)


@mcp.tool()
def lab_artifact(run_id: str, artifact_id: str, ctx: Context, episode_id: str | None = None) -> dict:
    """Read an allowlisted sanitized artifact by ID, never an arbitrary path."""
    return _service(ctx).get_artifact(run_id, artifact_id, episode_id)


@mcp.tool()
async def lab_simulation_start(spec: dict, ctx: Context) -> dict:
    """Explicitly start a validated simulation. Live mode spends a capped model budget."""
    return await _service(ctx).start_run(RunSpec.model_validate(spec))


@mcp.tool()
async def lab_simulation_cancel(run_id: str, ctx: Context) -> dict:
    """Cancel a simulation owned by this developer MCP session and retain evidence."""
    service = _service(ctx)
    state = service.get_run(run_id)
    if state.get("status") in {"queued", "running"} and run_id not in service.tasks:
        raise ValueError("Cancel this run through the worker that started it")
    return await service.cancel(run_id)


@mcp.tool()
async def lab_evaluate(run_id: str, ctx: Context) -> dict:
    """Score saved replies with the real local Helix SDK; no new inference."""
    return await _service(ctx).evaluate_run(run_id)


@mcp.tool()
def lab_workbench_preview(spec: dict) -> dict:
    """Preview a validated Data Designer job and source lineage without generation."""
    from .workbench import prepare_workbench

    return prepare_workbench(spec)


@mcp.tool()
async def lab_workbench_start(spec: dict, ctx: Context) -> dict:
    """Explicitly start a bounded Data Designer job; live generation uses the model budget."""
    return await _service(ctx).start_workbench(spec)


@mcp.tool()
def lab_workbench_job(job_id: str, ctx: Context) -> dict:
    """Inspect a saved Designer job without rerunning it."""
    return _service(ctx).get_workbench(job_id)


@mcp.tool()
async def lab_workbench_cancel(job_id: str, ctx: Context) -> dict:
    """Cancel a Designer task owned by this session; keep partial saved results."""
    service = _service(ctx)
    state = service.get_workbench(job_id)
    if state.get("status") in {"queued", "running"} and job_id not in service.tasks:
        raise ValueError("Cancel this job through the worker that started it")
    return await service.cancel_workbench(job_id)


@mcp.tool()
async def lab_platform_status(ctx: Context, target: str = "local") -> dict:
    """Probe the selected configured Platform; does not register, deploy or invoke."""
    return await _service(ctx).platform_action({"operation": "status", "target": target})


@mcp.tool()
async def lab_platform_action(
    operation: str, ctx: Context, arguments: dict | None = None, target: str = "local"
) -> dict:
    """Explicit allowlisted Platform action. Invoke can spend a bounded inference budget; resource changes remain real."""
    return await _service(ctx).platform_action(
        {"operation": operation, "arguments": arguments or {}, "target": target}
    )


@mcp.tool()
def lab_platform_job(job_id: str, ctx: Context) -> dict:
    """Read the saved state of a queued Platform action."""
    return _service(ctx).get_platform_job(job_id)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
