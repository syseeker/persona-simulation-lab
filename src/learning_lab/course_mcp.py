"""Read-only MCP surface shared by the direct and Fabric targets."""

from mcp.server.fastmcp import FastMCP
from typing import Literal
import os
from pathlib import Path
from .catalogue import Preferences, get_course, search_courses as match

mcp = FastMCP("Singapore learning catalogue")
TOOL_NAMES = ["search_courses", "get_course_details", "compare_courses"]


def bound_preferences(values: dict) -> Preferences:
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
    days: list[int] | None = None,
    planning_area: str | None = None,
    known_skills: list[str] | None = None,
    kind: Literal["skillsfuture", "community"] | None = None,
) -> dict:
    """Find up to five sourced courses; preserve unknown fees, schedules and eligibility."""
    try:
        return match(
            bound_preferences(
                dict(
                    goal=goal,
                    budget_sgd=budget_sgd,
                    days=days,
                    planning_area=planning_area,
                    known_skills=known_skills,
                    kind=kind,
                )
            )
        )
    except ValueError as exc:
        return {
            "error": str(exc),
            "hint": "Use Monday=0 through Sunday=6. Correct invalid inputs before retrying.",
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
