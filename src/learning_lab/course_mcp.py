"""Read-only MCP surface shared by the direct and Fabric targets."""

from mcp.server.fastmcp import FastMCP
from typing import Annotated
import hashlib
import os
from pathlib import Path
import re
import httpx
from pydantic import Field
from .catalogue import Preferences, get_course, search_courses as match

mcp = FastMCP("Singapore learning catalogue")
TOOL_NAMES = ["search_courses", "get_course_details", "compare_courses"]


def normalize_days(days: list[int | str] | str | None) -> list[int] | None:
    """Accept readable weekdays without treating an invalid value as unrestricted."""
    if isinstance(days, list):
        normalized = []
        for day in days:
            if isinstance(day, str):
                normalized.extend(normalize_days(day))
            elif isinstance(day, int) and not isinstance(day, bool) and day in range(7):
                normalized.append(day)
            else:
                raise ValueError('Days must be weekday names or Monday=0 through Sunday=6')
        return list(dict.fromkeys(normalized))
    if not isinstance(days, str):
        return days
    names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    mapping = {key: day for day, name in enumerate(names) for key in (name, name[:3], str(day))}
    parts = [part for part in re.split(r"[,;/\s]+", days.strip().lower()) if part and part != "and"]
    if not parts or any(part not in mapping for part in parts):
        raise ValueError("Days must be weekday names or Monday=0 through Sunday=6")
    return list(dict.fromkeys(mapping[part] for part in parts))


def bound_preferences(values: dict) -> Preferences:
    remote = os.getenv("LAB_PREFERENCES_URL")
    preset_file = os.getenv("LAB_PREFERENCES_PRESET_FILE")
    if preset_file:
        if remote:
            raise ValueError("Choose exactly one deployed learner-constraint channel")
        raw = Path(preset_file).read_bytes()
        expected = os.getenv("LAB_PREFERENCES_PRESET_SHA256", "")
        if len(raw) > 16000 or len(expected) != 64 or hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("The frozen teaching preset failed its declared integrity check")
        explicit = Preferences.model_validate_json(raw).model_dump(exclude_none=True)
        for name in ["goal", "budget_sgd", "days", "known_skills", "kind", "planning_area"]:
            if name in explicit:
                values[name] = explicit[name]
            elif name != "goal":
                values[name] = None
        return Preferences.model_validate(values)
    if os.getenv("LAB_REQUIRE_PREFERENCES") == "1" and not remote:
        raise ValueError("This deployed catalogue requires its authenticated learner-constraint callback")
    if remote:
        token = os.getenv("LAB_PREFERENCES_TOKEN")
        if not token or len(token) < 24:
            raise ValueError("The trusted deployment preference channel is not configured")
        try:
            response = httpx.get(remote, headers={"Authorization": f"Bearer {token}"}, timeout=5)
            if response.status_code != 200:
                raise ValueError("No active trusted preference lease for this deployment")
            body = response.json()
            if body.get("version") != 1 or not body.get("run_id"):
                raise ValueError("The trusted preference service returned an unsupported response")
            explicit = Preferences.model_validate(body["preferences"]).model_dump(exclude_none=True)
        except (httpx.HTTPError, KeyError, TypeError) as exc:
            raise ValueError("Trusted deployment constraints are unavailable; the tool did not relax them") from exc
        for name in ["budget_sgd", "days", "known_skills", "kind", "planning_area"]:
            if name in explicit:
                values[name] = explicit[name]
        return Preferences.model_validate(values)
    path = os.getenv("LAB_PREFERENCES_FILE")
    if path and Path(path).exists():
        explicit = Preferences.model_validate_json(Path(path).read_text()).model_dump(exclude_none=True)
        # Hard constraints supplied through the application cannot be omitted or relaxed by the model.
        for name in ["budget_sgd", "days", "known_skills", "kind", "planning_area"]:
            if name in explicit:
                values[name] = explicit[name]
    return Preferences.model_validate(values)


@mcp.tool()
def search_courses(
    goal: str,
    budget_sgd: float | None = None,
    days: list[int | str] | str | None = None,
    planning_area: str | None = None,
    known_skills: list[str] | None = None,
    kind: Annotated[str | None, Field(json_schema_extra={'enum': ['skillsfuture', 'community', None]})] = None,
) -> dict:
    """Find up to five sourced courses; preserve unknown fees, schedules and eligibility.

    days uses Monday=0 through Sunday=6, e.g. [5] for Saturday. Weekday names such
    as "Saturday" or "Saturday, Sunday" are also accepted and normalized.
    kind accepts "skillsfuture", "community" or JSON null, never the string
    "none". Invalid domain input returns an explicit error, not a no-match.
    """
    try:
        # Validate domain values inside the tool so maintained harnesses can
        # inspect a structured error and repair a model argument. Do not coerce
        # "none" into an unrestricted search, even with a trusted preset.
        normalized = Preferences(goal=goal, budget_sgd=budget_sgd, days=normalize_days(days),
                                 planning_area=planning_area, known_skills=known_skills, kind=kind)
        return match(
            bound_preferences(
                normalized.model_dump(mode='json')
            )
        )
    except ValueError as exc:
        return {
            "error": str(exc),
            "hint": "Correct invalid inputs before retrying: days use Monday=0 through Sunday=6; kind is skillsfuture, community or JSON null. This error is not a catalogue no-match.",
            "error_kind": "invalid_input",
            "matches": [],
        }


@mcp.tool()
def get_course_details(course_id: str) -> dict:
    """Return the verified snapshot and official URL for one stable course ID."""
    course = get_course(course_id)
    result = course.model_dump(mode="json")
    checked = match(bound_preferences({"goal": course.title}))
    result["constraint_notes"] = [e["reason"] for e in checked["excluded"] if e["id"] == course.id]
    return result


@mcp.tool()
def compare_courses(course_ids: list[str]) -> list[dict]:
    """Compare two to three distinct catalogue entries without inventing absent facts."""
    if not 2 <= len(set(course_ids)) <= 3 or len(course_ids) != len(set(course_ids)):
        raise ValueError("Choose two to three distinct course IDs")
    return [get_course_details(course_id) for course_id in course_ids]


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
