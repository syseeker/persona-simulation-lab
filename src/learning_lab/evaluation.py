"""Generate held-out advisor outputs and export transparent deterministic criteria."""

from __future__ import annotations

import asyncio
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

from .catalogue import Preferences, all_courses, freeze_catalogue, search_courses
from .inference import Budget, Gateway
from .settings import ROOT, model_id
from .target import DirectTarget
from .outcomes import answer_outcome, answer_text
from .evidence import decode_native, sanitize


def score_response(
    content: str, preferences: Preferences, catalogue_path: Path | None = None
) -> dict[str, bool]:
    if answer_outcome(content)["status"] != "valid":
        return {
            key: False
            for key in [
                "catalogue_grounding",
                "constraint_compliance",
                "eligibility_caution",
                "fee_caution",
                "source_citation",
            ]
        }
    content = answer_text(content)
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


def evaluate_saved_run(run: dict, folder: Path) -> dict:
    """Build auditable per-turn criteria without new inference or guessed constraints.

    Helix receives only applicable criterion rows. Missing answers and missing
    evidence are distinct from a failed assertion. Historical manifests are not
    changed, and unavailable structured preferences are never reconstructed from
    a model's tool arguments or replaced with a generic artificial goal.
    """
    episodes = {item["episode_id"]: dict(item) for item in run.get("episodes", [])}
    conversations = {}
    for event in run.get("events", []):
        episode = event.get("episode_id")
        if not episode:
            continue
        if event.get("type") == "episode_started":
            episodes.setdefault(episode, {}).update(
                {k: event[k] for k in ["strategy", "persona_index"] if k in event}
            )
        if event.get("type") != "message":
            continue
        turns = conversations.setdefault(episode, [])
        if event.get("role") == "user":
            turns.append({"user": event.get("content", ""), "assistant": None})
        elif event.get("role") == "assistant":
            if not turns or turns[-1]["assistant"] is not None:
                turns.append({"user": "", "assistant": None})
            turns[-1]["assistant"] = event
    for episode in episodes:
        conversations.setdefault(episode, [{"user": "", "assistant": None}])

    snapshot = folder / "catalogue-snapshot.json"
    courses, snapshot_error = {}, None
    try:
        courses = {course.id: course for course in all_courses(snapshot)}
        if (
            run.get("catalogue_sha256")
            and hashlib.sha256(snapshot.read_bytes()).hexdigest() != run["catalogue_sha256"]
        ):
            snapshot_error = "The saved catalogue differs from the run's recorded hash; its grounding checks cannot be trusted."
    except (OSError, ValueError):
        snapshot_error = (
            "The run's frozen catalogue is unavailable or invalid; current facts were not substituted."
        )
    as_of = None
    try:
        as_of = datetime.fromisoformat(run["started_at"].replace("Z", "+00:00")).date()
    except (ValueError, KeyError, AttributeError):
        pass
    rows = []
    for episode, turns in conversations.items():
        condition = episodes.get(episode, {}).get("strategy", "unknown")
        records = []
        # Episode IDs originate in saved data too; never use arbitrary paths.
        if re.fullmatch(r"[a-f0-9-]{36}", episode):
            path = folder / episode / "reply-outcomes.jsonl"
            if path.exists() and not path.is_symlink() and path.resolve().is_relative_to(folder.resolve()):
                try:
                    if path.stat().st_size <= 1024 * 1024:
                        records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
                except (OSError, ValueError):
                    records = []
        for index, turn in enumerate(turns):
            event = turn["assistant"] or {}
            record = records[index] if index < len(records) else {}
            content = event.get("content", record.get("content"))
            outcome = answer_outcome(content)
            text = answer_text(content).translate(
                str.maketrans({"\u2011": "-", "\u2013": "-", "\u2010": "-"})
            )
            cited = set(re.findall(r"\b(?:CC|SF)-\d{3}\b", text))
            urls = set(re.findall(r"https://[^\s)\]>]+", text))
            mentioned = cited | {
                key for key, course in courses.items() if course.title.casefold() in text.casefold()
            }
            base = {
                "episode_id": episode,
                "turn": index + 1,
                "condition": condition,
                "case_id": f"{episode}:{index + 1}",
            }

            def add(criterion, status, reason, evidence=None):
                rows.append(
                    {
                        **base,
                        "criterion": criterion,
                        "status": status,
                        "reason": reason,
                        "expected": "true",
                        "output": "true"
                        if status == "pass"
                        else "false"
                        if status in {"fail", "error"}
                        else None,
                        "evidence": sanitize(evidence or {}),
                    }
                )

            missing = content is None
            add(
                "answer_validity",
                "error" if missing else "pass" if outcome["status"] == "valid" else "fail",
                "No assistant answer was saved; inspect the execution failure and partial trace."
                if missing
                else outcome["reason"],
                {
                    "code": outcome["code"],
                    "answer_excerpt": text[:600],
                    "runtime_status": record.get("runtime_status", "not saved"),
                },
            )
            criteria = [
                "catalogue_grounding",
                "constraint_compliance",
                "source_citation",
                "eligibility_caution",
                "fee_caution",
                "no_match_handling",
            ]
            if outcome["status"] != "valid":
                for criterion in criteria:
                    add(
                        criterion,
                        "not_applicable",
                        "There is no valid public answer to assess. Answer validity remains a failed or errored check.",
                    )
                continue
            if snapshot_error:
                add("catalogue_grounding", "error", snapshot_error)
                add("source_citation", "error", snapshot_error)
            elif not mentioned and not urls:
                add(
                    "catalogue_grounding",
                    "not_applicable",
                    "No course identifier, exact course title or URL was present; this does not establish factual correctness.",
                )
                add(
                    "source_citation",
                    "not_applicable",
                    "No identifiable course recommendation to match to an official source.",
                )
            else:
                known_urls = {str(course.source_url) for course in courses.values()}
                grounded = cited <= courses.keys() and urls <= known_urls
                add(
                    "catalogue_grounding",
                    "pass" if grounded else "fail",
                    "Compare mentioned IDs and URLs with the frozen catalogue; other factual claims require review.",
                    {
                        "cited_ids": sorted(cited),
                        "unknown_ids": sorted(cited - courses.keys()),
                        "unknown_urls": sorted(urls - known_urls),
                    },
                )
                missing_links = [
                    key
                    for key in sorted(mentioned)
                    if key not in courses or str(courses[key].source_url) not in urls
                ]
                add(
                    "source_citation",
                    "fail" if missing_links else "pass",
                    "Every identifiable course needs its corresponding official source URL.",
                    {"missing_source_ids": missing_links},
                )
            prefs_data = event.get("preferences") or record.get("preferences")
            if not prefs_data:
                add(
                    "constraint_compliance",
                    "not_applicable",
                    "Original structured constraints were not saved for this turn. Model tool arguments are not substituted for learner constraints.",
                )
            elif snapshot_error:
                add("constraint_compliance", "error", snapshot_error)
            elif as_of is None:
                add(
                    "constraint_compliance",
                    "error",
                    "The run date is unavailable; current intake dates are not substituted.",
                )
            else:
                try:
                    preferences = Preferences.model_validate(prefs_data)
                    matched = {
                        item["course"]["id"]
                        for item in search_courses(preferences, catalogue_path=snapshot, as_of=as_of)[
                            "matches"
                        ]
                    }
                    if mentioned:
                        add(
                            "constraint_compliance",
                            "pass" if mentioned <= matched else "fail",
                            "Narrow ID-based check against the saved constraints and run date; an excluded course mentioned as an explanation can require manual review.",
                            {
                                "preferences": preferences.model_dump(mode="json"),
                                "matching_ids": sorted(matched),
                                "outside_matches": sorted(mentioned - matched),
                            },
                        )
                    else:
                        add(
                            "constraint_compliance",
                            "not_applicable",
                            "No identifiable course recommendation to compare with the saved constraints.",
                        )
                except ValueError:
                    add(
                        "constraint_compliance",
                        "error",
                        "Saved structured constraints do not match the supported schema.",
                    )
            lower = text.lower()
            for criterion, relevant, forbidden, reason in [
                (
                    "eligibility_caution",
                    r"fund|eligib|credit|subsid|qualif",
                    r"you (?:are eligible|qualify|will receive)|guaranteed (?:funding|subsidy)",
                    "Detect unsupported direct eligibility or guaranteed-funding assertions; paraphrases still require manual review.",
                ),
                (
                    "fee_caution",
                    r"fee|cost|price|s\$|sgd",
                    r"no (?:additional|extra|material) (?:fees|costs)",
                    "Detect unsupported assurances that there are no extra fees; this is a narrow text check.",
                ),
            ]:
                if not re.search(relevant, lower):
                    add(
                        criterion,
                        "not_applicable",
                        "No relevant assertion was found by this narrow text check.",
                    )
                else:
                    hit = re.search(forbidden, lower)
                    add(
                        criterion,
                        "fail" if hit else "pass",
                        reason,
                        {"matched_assurance": hit.group(0) if hit else None},
                    )
            searches, search_errors = [], []
            for tool in event.get("tools", record.get("tools", [])):
                if not str(tool.get("name", "")).endswith("search_courses"):
                    continue
                value = decode_native(tool.get("result", tool.get("content")))
                for _ in range(4):
                    if isinstance(value, str):
                        try:
                            value = json.loads(value)
                        except ValueError:
                            break
                    elif (
                        isinstance(value, list)
                        and value
                        and isinstance(value[0], dict)
                        and "text" in value[0]
                    ):
                        value = value[0]["text"]
                    elif isinstance(value, dict) and "result" in value:
                        value = decode_native(value["result"])
                    else:
                        break
                if (
                    tool.get("status") in {"failed", "incomplete"}
                    or isinstance(value, dict)
                    and (value.get("error") or value.get("isError") is True or value.get("is_error") is True)
                ):
                    search_errors.append({"status": tool.get("status"), "result": value})
                elif isinstance(value, dict) and isinstance(value.get("matches"), list):
                    searches.append(value)
            if not searches and search_errors:
                add(
                    "no_match_handling",
                    "error",
                    "The saved catalogue search failed or remained incomplete; this does not establish that no matching course exists.",
                    {"search_errors": search_errors},
                )
            elif searches and all(not item["matches"] for item in searches):
                acknowledges = bool(
                    re.search(
                        r"(?:no|not|couldn.t|cannot|can.t|don.t|doesn.t|unable)[^.\n]{0,100}(?:match|catalog|find|list|offer|available|class|course)|(?:catalog|list)[^.\n]{0,60}(?:no |not |doesn.t|don.t)",
                        lower,
                    )
                )
                add(
                    "no_match_handling",
                    "pass" if acknowledges and not mentioned and not urls else "fail",
                    "Empty saved search results require an explicit catalogue limitation without invented course references.",
                    {"search_count": len(searches), "empty_results": True},
                )
            else:
                add(
                    "no_match_handling",
                    "not_applicable",
                    "No all-empty saved catalogue search was available for this turn.",
                )
    summary = {}
    for row in rows:
        total = summary.setdefault(
            row["condition"], {"criteria": 0, "passed": 0, "failed": 0, "errors": 0, "not_applicable": 0}
        )
        total[
            {"pass": "passed", "fail": "failed", "error": "errors", "not_applicable": "not_applicable"}[
                row["status"]
            ]
        ] += 1
        if row["status"] != "not_applicable":
            total["criteria"] += 1
    return {
        "version": 2,
        "rows": rows,
        "summary": summary,
        "helix_rows": [
            {k: row[k] for k in ["case_id", "condition", "criterion", "expected", "output"]}
            for row in rows
            if row["status"] != "not_applicable"
        ],
        "limitations": [
            "Deterministic checks are narrow and do not verify every claim or human outcome.",
            "Missing original constraints and absent tool evidence remain explicit; no facts are inferred from a final answer.",
        ],
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
    result = json.loads(stdout)
    # Surface actual SDK metrics as well as the human-readable summary. The
    # details file remains the authoritative complete Helix result artifact.
    metrics = json.loads(output.read_text())
    result["row_scores"] = sanitize(metrics.get("row_scores", []))
    return result
