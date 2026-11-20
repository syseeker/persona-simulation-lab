"""Versioned course facts and deterministic, uncertainty-aware matching."""

from __future__ import annotations

from datetime import date
import hashlib
import os
from pathlib import Path
import json
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .settings import ROOT


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Course(StrictModel):
    id: str
    title: str
    provider: str
    kind: Literal["skillsfuture", "community"]
    summary: str
    tags: list[str]
    source_url: HttpUrl
    captured_on: date
    venue: str | None = None
    planning_area: str | None = None
    price_min_sgd: float | None = Field(default=None, ge=0)
    price_max_sgd: float | None = Field(default=None, ge=0)
    extra_cost_sgd: float | None = Field(default=None, ge=0)
    cost_note: str = "Confirm total fees with the provider."
    start_date: date | None = None
    end_date: date | None = None
    registration_closes: date | None = None
    weekdays: list[int] | None = None
    schedule_note: str = "Confirm the next intake and timetable."
    duration_hours: float | None = None
    prerequisites: list[str] = Field(default_factory=list)
    prerequisite_note: str = "Confirm entry requirements with the provider."
    languages: list[str] | None = None
    funding_note: str = "Individual funding eligibility has not been verified."
    availability: Literal["listed", "unknown", "closed"] = "unknown"


class Preferences(StrictModel):
    goal: str = Field(min_length=1, max_length=3000)
    budget_sgd: float | None = Field(default=None, ge=0)
    days: list[int] | None = None
    planning_area: str | None = Field(default=None, max_length=80)
    known_skills: list[str] | None = None
    kind: Literal["skillsfuture", "community"] | None = None


def all_courses(path: Path | None = None) -> list[Course]:
    source = path or Path(os.getenv("LAB_CATALOGUE_FILE", str(ROOT / "catalogue/courses.json")))
    payload = json.loads(source.read_text())
    courses = [Course.model_validate(c) for c in payload["courses"]]
    if len({c.id for c in courses}) != len(courses):
        raise ValueError("Duplicate catalogue course IDs")
    return courses


def freeze_catalogue(path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes((ROOT / "catalogue/courses.json").read_bytes())
    all_courses(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_course(course_id: str) -> Course:
    return next((c for c in all_courses() if c.id == course_id), None) or _unknown(course_id)


def _unknown(course_id):
    raise ValueError(f"Unknown course ID: {course_id}")


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower())) - {
        "i",
        "a",
        "the",
        "to",
        "and",
        "for",
        "learn",
        "course",
        "want",
    }


def search_courses(
    prefs: Preferences, limit: int = 5, *, as_of: date | None = None, catalogue_path: Path | None = None
) -> dict:
    if prefs.days is not None and any(day not in range(7) for day in prefs.days):
        raise ValueError("Days must use Monday=0 through Sunday=6")
    today = as_of or date.today()
    query = tokens(prefs.goal)
    for keys, expansion in [
        ({"excel", "spreadsheet", "office"}, {"excel", "spreadsheet", "office", "data"}),
        ({"photo", "photography", "camera"}, {"photo", "photography", "smartphone"}),
        ({"tai", "chi", "taichi"}, {"taijiquan", "wellness"}),
        ({"bake", "baking", "pastry", "cooking"}, {"baking", "pastry", "culinary"}),
        ({"computer", "digital", "literacy"}, {"computer", "digital", "literacy"}),
    ]:
        if query & keys:
            query |= expansion
    matches = []
    excluded = []
    for course in all_courses(catalogue_path):
        if prefs.kind and prefs.kind != course.kind:
            continue
        reason = None
        if course.availability == "closed" or (
            course.registration_closes and course.registration_closes < today
        ):
            reason = "Registration closed for this listed intake"
        elif course.end_date and course.end_date < today:
            reason = "Listed intake has ended"
        elif prefs.budget_sgd is not None and course.price_max_sgd is not None:
            total = course.price_max_sgd + (course.extra_cost_sgd or 0)
            if total > prefs.budget_sgd:
                reason = "Published upper fee including known extras exceeds the budget"
        if (
            prefs.days is not None
            and course.weekdays is not None
            and not set(course.weekdays) <= set(prefs.days)
        ):
            reason = "Published class days conflict with availability"
        if course.prerequisites and prefs.known_skills is not None:
            if not set(course.prerequisites) <= set(prefs.known_skills):
                reason = "An explicit prerequisite has not been met"
        if reason:
            excluded.append({"id": course.id, "reason": reason})
            continue
        overlap = sorted(query & tokens(course.title + " " + course.summary + " " + " ".join(course.tags)))
        if not overlap:
            continue
        unknowns = ["Confirm a place is still available", "Confirm personal funding eligibility"]
        if course.start_date is None:
            unknowns.append("Next intake is unknown")
        if course.price_max_sgd is None:
            unknowns.append("Total fee is unknown; budget fit is unconfirmed")
        elif course.extra_cost_sgd is None:
            unknowns.append("Additional costs are unconfirmed")
        if prefs.days is not None and course.weekdays is None:
            unknowns.append("Timetable fit is unconfirmed")
        if course.prerequisites and prefs.known_skills is None:
            unknowns.append("Confirm the stated prerequisite")
        score = len(overlap) * 10
        if (
            prefs.planning_area
            and course.planning_area
            and prefs.planning_area.casefold() == course.planning_area.casefold()
        ):
            score += 3
        matches.append(
            {
                "course": course.model_dump(mode="json"),
                "score": score,
                "matched_terms": overlap,
                "confirm": unknowns,
            }
        )
    matches.sort(key=lambda m: (-m["score"], m["course"]["id"]))
    return {
        "snapshot_date": "2026-11-10",
        "as_of": today.isoformat(),
        "matches": matches[: max(1, min(limit, 5))],
        "excluded": excluded,
        "notice": "Curated snapshot. Check the official listing before acting; individual eligibility is unknown.",
    }
