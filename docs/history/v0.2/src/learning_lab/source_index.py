"""Allowlisted integration entry points for the developer evidence browser."""

from pathlib import Path
import subprocess

from .settings import ROOT

SOURCES = {
    "application": ("src/learning_lab/service.py", "LabService", "Shared UI, CLI and MCP application services"),
    "personas": ("src/learning_lab/datasets.py", "browse_personas", "Pinned original persona records and selection"),
    "usersim": ("src/learning_lab/simulation.py", "hosted_episode", "UserSim activation loop and isolated target"),
    "mcp": ("src/learning_lab/course_mcp.py", "search_courses", "Read-only, constraint-bound course tools"),
    "deepagents": ("src/learning_lab/target.py", "DirectTarget", "Native Deep Agents harness"),
    "fabric": ("src/learning_lab/fabric_target.py", "build_config", "Typed Fabric planning and runtime lifecycle"),
    "relay": ("src/learning_lab/target.py", "relay_config", "Native Relay capture configuration"),
    "budget": ("src/learning_lab/inference.py", "Gateway", "Atomic inference admission and measured usage"),
    "routing": ("integrations/proxy/README.md", "", "LiteLLM and Switchyard deployment profile"),
    "helix": ("src/learning_lab/evaluation.py", "evaluate_saved_run", "Inspectable evaluation criteria and real Helix SDK"),
    "designer": ("integrations/designer/learning_preferences.py", "", "Source-seeded Data Designer configuration"),
    "platform": ("src/learning_lab/deployment.py", "PlatformBridge", "Helix registration, deployments and sessions"),
    "platform-sdk": ("integrations/platform/bridge.py", "async def execute", "Actual native Helix SDK operations"),
    "openshell": ("integrations/platform/package_agent.py", "", "Reviewed agent and catalogue sandbox image"),
    "hermes": ("src/learning_lab/runtime_profiles.py", "hermes_runtime_environment", "Supported Hermes runtime and retry configuration"),
    "recovery": ("integrations/platform/native_cleanup.py", "async def recover_session", "Pinned native sandbox cleanup and resumable session recovery"),
    "north-star": ("docs/project-goals.md", "", "The agreed purpose and decision rule"),
}


def code_revision() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, timeout=3,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return None


def integration_sources() -> list[dict]:
    revision = code_revision()
    records = []
    for key, (relative, symbol, purpose) in SOURCES.items():
        path = ROOT / relative
        lines = path.read_text().splitlines() if path.is_file() else []
        line = next((i + 1 for i, value in enumerate(lines) if symbol and symbol in value), 1)
        records.append({
            "id": key, "path": relative, "absolute_path": str(path), "line": line,
            "symbol": symbol, "purpose": purpose, "available": bool(lines),
            "revision": revision,
            "github_url": f"https://github.com/syseeker/persona-simulation-lab/blob/{revision}/{relative}#L{line}"
            if revision else None,
        })
    return records


def source_excerpt(source_id: str) -> dict:
    if source_id not in SOURCES:
        raise ValueError("Unknown integration source")
    record = next(r for r in integration_sources() if r["id"] == source_id)
    path = Path(record["absolute_path"])
    if not path.is_file():
        return {**record, "content": "This integration source is not installed.", "start_line": 1}
    lines = path.read_text().splitlines()
    start = max(0, record["line"] - 5)
    return {**record, "content": "\n".join(lines[start:start + 110]), "start_line": start + 1,
            "notice": "Current local source; saved run revisions can differ. Uncommitted files may not exist at the GitHub revision."}
