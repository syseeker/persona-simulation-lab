"""Generate held-out advisor outputs and export transparent deterministic criteria."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import re

from .catalogue import Preferences, all_courses, freeze_catalogue, search_courses
from .inference import Budget, Gateway
from .settings import ROOT, model_id
from .target import DirectTarget


def score_response(
    content: str, preferences: Preferences, catalogue_path: Path | None = None
) -> dict[str, bool]:
    content = content.translate(str.maketrans({"\u2011": "-", "\u2013": "-", "\u2010": "-"}))
    permitted = {c.id for c in all_courses(catalogue_path)}
    matched = {
        item["course"]["id"] for item in search_courses(preferences, catalogue_path=catalogue_path)["matches"]
    }
    cited = set(re.findall(r"\b(?:CC|SF)-\d{3}\b", content))
    lower = content.lower()
    known_urls = {str(c.source_url) for c in all_courses(catalogue_path)}
    urls = set(re.findall(r"https://[^\s)\]>]+", content))
    return {
        "catalogue_grounding": cited <= permitted and urls <= known_urls,
        "constraint_compliance": cited <= matched,
        "eligibility_caution": not bool(
            re.search(r"you (?:are eligible|qualify|will receive)|guaranteed (?:funding|subsidy)", lower)
        ),
        "fee_caution": not bool(re.search(r"no (?:additional|extra|material) (?:fees|costs)", lower)),
        "source_citation": bool(urls) if cited else True,
    }


async def compare_strategies(output: Path, mode="demo") -> dict:
    suite = json.loads((ROOT / "evaluations/heldout.json").read_text())
    output.mkdir(parents=True, exist_ok=True)
    catalogue_path = output / "catalogue-snapshot.json"
    catalogue_hash = freeze_catalogue(catalogue_path)
    records, scores = [], []
    async with Gateway(Budget(120), mode).serving() as gateway:
        for strategy in ["concise", "clarification-first"]:
            for case in suite["cases"]:
                preferences = Preferences.model_validate(case["preferences"])
                failure = None
                try:
                    async with DirectTarget(
                        gateway,
                        output / strategy / case["id"] / "workspace",
                        model_id() if mode == "live" else "offline-scripted",
                        strategy=strategy,
                        catalogue_path=catalogue_path,
                    ) as target:
                        response = await target.reply(
                            preferences.goal
                            + ". Please include a short sourced shortlist, course IDs and any unresolved costs or eligibility.",
                            preferences,
                        )
                    criteria = {
                        "execution_success": True,
                        **score_response(response["content"], preferences, catalogue_path),
                    }
                except Exception as exc:
                    response = {"content": ""}
                    failure = f"{type(exc).__name__}: {str(exc)[:400]}"
                    criteria = {
                        "execution_success": False,
                        **{k: False for k in score_response("", preferences, catalogue_path)},
                    }
                if case.get("must_include"):
                    course = next(c for c in all_courses(catalogue_path) if c.id == case["must_include"])
                    criteria["reference_choice"] = (
                        course.id in response["content"]
                        or course.title.casefold() in response["content"].casefold()
                    )
                if case.get("must_exclude"):
                    course = next(c for c in all_courses(catalogue_path) if c.id == case["must_exclude"])
                    criteria["reference_exclusion"] = (
                        not failure
                        and course.id not in response["content"]
                        and str(course.source_url) not in response["content"]
                    )
                records.append(
                    {
                        "condition": strategy,
                        "case_id": case["id"],
                        "preferences": preferences.model_dump(),
                        "response": response["content"],
                        "criteria": criteria,
                        "error": failure,
                    }
                )
                for name, value in criteria.items():
                    scores.append(
                        {
                            "condition": strategy,
                            "case_id": case["id"],
                            "criterion": name,
                            "output": str(value).lower(),
                            "expected": "true",
                        }
                    )
                (output / "responses.json").write_text(json.dumps(records, indent=2))
                (output / "criteria.json").write_text(json.dumps(scores, indent=2))
        manifest = {
            "suite": suite["version"],
            "mode": mode,
            "model": model_id() if mode == "live" else "offline-scripted",
            "catalogue_sha256": catalogue_hash,
            "calls": gateway.budget.calls,
            "usage": gateway.budget.records,
            "failed_cases": sum(bool(r["error"]) for r in records),
            "caveat": "Deterministic checks are narrow. They do not validate every factual claim or human learning outcome.",
        }
    (output / "responses.json").write_text(json.dumps(records, indent=2))
    (output / "criteria.json").write_text(json.dumps(scores, indent=2))
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


async def run_helix(criteria: Path, output: Path) -> dict:
    python = ROOT / "integrations/helix/.venv/bin/python"
    if not python.exists():
        raise ValueError("Install the isolated Helix environment first")
    process = await asyncio.create_subprocess_exec(
        str(python),
        str(ROOT / "integrations/helix/evaluate.py"),
        str(criteria),
        str(output),
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
        raise RuntimeError("Helix evaluation failed: " + stderr.decode()[-500:])
    return json.loads(stdout)
