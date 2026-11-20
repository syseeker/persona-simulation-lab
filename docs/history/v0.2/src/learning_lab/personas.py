"""Inspect source records before designing matching scenarios."""

from __future__ import annotations

import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

DATASET = "nvidia/Nemotron-Personas-Singapore"
REVISION = "a3994709410410f834bd949d643d3f2796908969"
OCEAN = ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism")
MATCH_FIELDS = (
    "skills_and_expertise_list",
    "hobbies_and_interests_list",
    "career_goals_and_ambitions",
    "education_level",
    "occupation",
    "industry",
    "planning_area",
)


def parse_list(value: Any) -> list[str]:
    """The public parquet stores list fields as Python-list strings. Never eval them."""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            value = ast.literal_eval(value)
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        raise ValueError("Expected a list of strings in the source field")
    return value


def inspect_dataset(paths: list[Path]) -> dict:
    if not paths:
        raise ValueError("No parquet files supplied")
    rows: list[dict] = []
    schemas = []
    hashes = {}
    for path in paths:
        file = pq.ParquetFile(path)
        schemas.append({f.name: str(f.type) for f in file.schema_arrow})
        rows.extend(file.read().to_pylist())
        hashes[path.name] = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
    if any(s != schemas[0] for s in schemas):
        raise ValueError("Source shards have different schemas")
    fields = schemas[0]
    nulls = {k: sum(r.get(k) in (None, "") for r in rows) for k in fields}
    bad_lists = Counter()
    for r in rows:
        for key in ("skills_and_expertise_list", "hobbies_and_interests_list"):
            try:
                parse_list(r[key])
            except (KeyError, ValueError, SyntaxError, TypeError):
                bad_lists[key] += 1
    age_bins = Counter("18-34" if r["age"] < 35 else "35-59" if r["age"] < 60 else "60+" for r in rows)
    return {
        "dataset": DATASET,
        "revision": REVISION,
        "distribution": "HF public",
        "license": "CC BY 4.0",
        "row_count": len(rows),
        "fields": fields,
        "distinct_ids": len({r["uuid"] for r in rows}),
        "null_counts": nulls,
        "age_range": [min(r["age"] for r in rows), max(r["age"] for r in rows)],
        "age_bins": dict(age_bins),
        "planning_areas": dict(sorted(Counter(r["planning_area"] for r in rows).items())),
        "occupations": dict(sorted(Counter(r["occupation"] for r in rows).items())),
        "unparseable_list_counts": dict(bad_lists),
        "ocean_fields_present": [k for k in OCEAN if k in fields],
        "file_sha256": hashes,
        "limitations": [
            "Synthetic profiles do not measure real course demand or human behaviour.",
            "Country of residence does not establish citizenship or funding entitlement.",
            "Planning area does not establish a precise home location or travel duration.",
            "Course names inside generated narratives are unverified.",
            "Budget, availability and travel limits require explicit scenario inputs.",
            "Public HF records do not supply UserSim's documented OCEAN fields.",
        ],
    }


def choose_review_panel(paths: list[Path]) -> list[dict]:
    """Deterministic diagnostic coverage panel; intentionally not population weighted."""
    rows = [r for p in paths for r in pq.read_table(p).to_pylist()]
    buckets: dict[str, list[dict]] = {}
    for row in rows:
        key = "early" if row["age"] < 35 else "mid" if row["age"] < 60 else "older"
        buckets.setdefault(key, []).append(row)
    panel = []
    for group in ("early", "mid", "older"):
        for row in sorted(buckets.get(group, []), key=lambda x: x["uuid"])[:4]:
            panel.append({"source_id": row["uuid"], "group": group, "source": "HF public", **row})
    return panel
