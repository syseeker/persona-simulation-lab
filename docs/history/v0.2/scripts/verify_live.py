"""Explicit, bounded live acceptance checks. Writes evidence only under ignored runs/."""

import argparse
import asyncio
import json
import sys
import uuid

from learning_lab.catalogue import Preferences
from learning_lab.evaluation import compare_strategies, run_helix
from learning_lab.service import ChatSpec, LabService, RunSpec, atomic_json
from learning_lab.settings import ROOT


async def verify():
    evidence = {"state": "running", "stages": {}}
    destination = ROOT / "runs/verification.json"
    if destination.exists():
        (ROOT / "runs" / f"verification-{uuid.uuid4()}.json").write_bytes(destination.read_bytes())
    atomic_json(destination, evidence)
    service = LabService()
    try:
        state = await service.start_run(
            RunSpec(
                mode="live",
                engine="relay",
                source="hf-profile-only",
                personas=3,
                turns=2,
                strategies=["concise", "clarification-first"],
            )
        )
        await service.tasks[state["run_id"]]
        result = service.get_run(state["run_id"])
        evaluation = await service.evaluate_run(state["run_id"])
        evidence["stages"]["paired_usersim_relay"] = {
            "run_id": state["run_id"],
            "status": result["status"],
            "calls": result["calls"],
            "episodes": [
                {k: e.get(k) for k in ["strategy", "persona_index", "status", "turns", "error"]}
                for e in result["episodes"]
            ],
            "helix": evaluation,
        }
        atomic_json(destination, evidence)
        reply = await service.chat(
            ChatSpec(
                mode="live",
                engine="fabric",
                preferences=Preferences(goal="Find a Saturday photography class", budget_sgd=50, days=[5]),
            )
        )
        evidence["stages"]["fabric_nim"] = {
            "status": reply["fabric"]["status"],
            "calls": reply["calls"],
            "content": reply["content"],
            "runtime_id": reply["fabric"]["runtime_id"],
        }
        atomic_json(destination, evidence)
    except Exception as exc:
        evidence["stages"]["integration_error"] = f"{type(exc).__name__}: {str(exc)[:500]}"
    finally:
        await service.close()
    try:
        folder = ROOT / "runs" / f"heldout-{uuid.uuid4()}"
        manifest = await compare_strategies(folder, "live")
        scores = await run_helix(folder / "criteria.json", folder / "helix-results.json")
        evidence["stages"]["heldout_helix"] = {
            "manifest": {k: v for k, v in manifest.items() if k != "usage"},
            **scores,
        }
        atomic_json(destination, evidence)
    except Exception as exc:
        evidence["stages"]["heldout_error"] = f"{type(exc).__name__}: {str(exc)[:500]}"
    try:
        previous = set((ROOT / "runs/ablations").glob("*/report.json"))
        log_path = ROOT / ".private/checks/ablation-live.log"
        with log_path.open("w") as log:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "learning_lab.cli",
                "ablate",
                "--live",
                cwd=ROOT,
                stdout=log,
                stderr=asyncio.subprocess.STDOUT,
            )
            try:
                await asyncio.wait_for(process.wait(), timeout=240)
            except BaseException:
                process.kill()
                await process.wait()
                raise
        if process.returncode:
            raise RuntimeError("Live ablation failed; inspect its local log")
        paths = set((ROOT / "runs/ablations").glob("*/report.json")) - previous
        report = json.loads(next(iter(paths)).read_text())
        evidence["stages"]["designer_ablation"] = report
    except Exception as exc:
        evidence["stages"]["ablation_error"] = f"{type(exc).__name__}: {str(exc)[:500]}"
    evidence["state"] = "finished"
    atomic_json(destination, evidence)
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", required=True)
    parser.parse_args()
    asyncio.run(verify())
