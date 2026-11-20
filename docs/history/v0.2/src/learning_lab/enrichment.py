"""Isolated Data Designer generation and source-preserving overlay application."""

import asyncio
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import uuid

from .settings import ROOT


async def generate_overlays(output: Path, count=3, *, resolved_rows: list[dict] | None = None) -> dict:
    python = ROOT / "integrations/designer/.venv/bin/python"
    if not python.exists():
        raise ValueError("Install the isolated Data Designer environment first")
    env = {
        key: value
        for key, value in os.environ.items()
        if not re.search(r"KEY|TOKEN|SECRET|PASSWORD", key, flags=re.I)
    }
    if resolved_rows is not None:
        if not resolved_rows or count != len(resolved_rows):
            raise ValueError("Generate one categorical overlay for each frozen source profile")
        output.parent.mkdir(parents=True, exist_ok=True)
        seed = output.with_name("overlay-seed.jsonl")
        entries = []
        for row in resolved_rows:
            profile = row["persona"]
            original = json.dumps(profile, sort_keys=True)
            entries.append(
                {
                    "source_id": profile["uuid"],
                    "source_revision": row.get("source_revision", "unknown"),
                    "original_profile_json": original,
                    "original_profile_sha256": hashlib.sha256(original.encode()).hexdigest(),
                }
            )
        seed.write_text("\n".join(json.dumps(entry) for entry in entries) + "\n")
        env["LAB_SEED_PATH"] = str(seed.absolute())
    process = await asyncio.create_subprocess_exec(
        str(python),
        str(ROOT / "integrations/designer/learning_preferences.py"),
        "--output",
        str(output),
        "--count",
        str(count),
        cwd=ROOT,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
    except BaseException:
        process.kill()
        await process.wait()
        raise
    if process.returncode:
        raise RuntimeError("Data Designer generation failed: " + stderr.decode()[-500:])
    return json.loads(output.read_text())


def apply_overlays(rows: list[dict], overlays: dict) -> list[dict]:
    by_id = {r["source_id"]: r for r in overlays["records"]}
    result = []
    for original in rows:
        row = copy.deepcopy(original)
        overlay = by_id.get(row["persona"].get("uuid"))
        if overlay is None:
            raise ValueError("No generated overlay for one of the selected source profiles")
        original_json = overlay["original_profile_json"]
        if hashlib.sha256(original_json.encode()).hexdigest() != overlay["original_profile_sha256"]:
            raise ValueError("Original-profile hash verification failed")
        if json.loads(original_json) != row["persona"]:
            raise ValueError("Overlay source record does not match the selected persona")
        keys = [
            "learning_goal",
            "prior_familiarity",
            "delivery_preference",
            "budget_sgd",
            "availability",
            "overlay_id",
            "pipeline_version",
            "hypothesis",
        ]
        row["learning_overlay"] = {k: overlay[k] for k in keys}
        row["pair_input_id"] = row["trajectory_id"]
        row["trajectory_id"] = str(
            uuid.uuid5(uuid.NAMESPACE_URL, row["trajectory_id"] + overlay["overlay_id"])
        )
        result.append(row)
    return result
