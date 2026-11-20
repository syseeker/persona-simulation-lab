"""Read-only explorer for the two Singapore persona distributions.

Queries scan the pinned local parquet corpus, never the diagnostic review panel.
The browser supplies dataset identifiers and filters, never filesystem paths.
"""

from __future__ import annotations

import hashlib
import json
import random
import secrets
from typing import Literal

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as pads
from pydantic import Field, model_validator

from .catalogue import StrictModel
from .ngc_personas import CATALOGUE_URL, audit_installed_source, resolve_ngc
from .personas import DATASET, OCEAN, REVISION
from .settings import ROOT, load_environment

PersonaSource = Literal["hf-profile-only", "ngc"]


class DatasetQuery(StrictModel):
    source: PersonaSource = "hf-profile-only"
    offset: int = Field(default=0, ge=0, le=1_000_000)
    limit: int = Field(default=20, ge=1, le=100)
    search: str = Field(default="", max_length=200)
    age_min: int | None = Field(default=None, ge=18, le=120)
    age_max: int | None = Field(default=None, ge=18, le=120)
    planning_area: str | None = Field(default=None, max_length=100)
    occupation: str | None = Field(default=None, max_length=150)
    education_level: str | None = Field(default=None, max_length=150)

    @model_validator(mode="after")
    def ordered_ages(self):
        if self.age_min is not None and self.age_max is not None and self.age_min > self.age_max:
            raise ValueError("Minimum age must not exceed maximum age")
        return self


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def profile_hash(profile: dict) -> str:
    return hashlib.sha256(canonical_json(profile).encode()).hexdigest()


def _paths(source: PersonaSource):
    if source == "hf-profile-only":
        return sorted((ROOT / "data/hf/data").glob("*.parquet"))
    if source != "ngc":
        raise ValueError("Choose hf-profile-only or Singapore NGC Extended")
    location = resolve_ngc(ROOT)
    return [location.path] if location.path else []


def _description(source: PersonaSource) -> dict:
    load_environment()
    paths = _paths(source)
    is_hf = source == "hf-profile-only"
    location = None if is_hf else resolve_ngc(ROOT)
    result = {
        "source": source,
        "name": "Nemotron Personas Singapore · HF public" if is_hf else "Singapore NGC Extended",
        "country": "Singapore",
        "dataset": DATASET if is_hf else "NGC Nemotron Personas Singapore Extended · en_SG",
        "revision": REVISION if is_hf else location.revision,
        "source_url": f"https://huggingface.co/datasets/{DATASET}" if is_hf else CATALOGUE_URL,
        "license": "CC BY 4.0" if is_hf else "Review the terms accompanying the installed NGC dataset",
        "available": bool(paths),
        "ready": False,
        "row_count": 0,
        "columns": [],
        "ocean_fields": [],
        "notice": (
            "Synthetic source profiles; HF has no OCEAN conditioning. Not real citizens or measured behaviour."
            if is_hf else
            "Singapore Extended only. Dataset access is separate from inference access; no HF substitution."
        ),
        "setup": "uv run python scripts/inspect_personas.py --download" if is_hf else (
            "Run uv run python scripts/install_ngc_personas.py --download for pinned Singapore Extended, "
            "use an existing Data Designer managed asset, or set LAB_NGC_PERSONAS_PATH locally. "
            "An inference key alone does not grant dataset access."
        ),
    }
    if location:
        result["installation"] = location.origin
        if location.audit is not None:
            result["behaviour_audit"] = location.audit
            result["source_sha256"] = location.sha256
    if not paths:
        result["reason"] = location.reason if location else "Dataset is not installed locally"
        return result
    try:
        dataset = pads.dataset([str(path) for path in paths], format="parquet")
        result["row_count"] = dataset.count_rows()
        result["columns"] = [{"name": field.name, "type": str(field.type)} for field in dataset.schema]
        result["ocean_fields"] = [key for key in OCEAN if key in dataset.schema.names]
        missing = {"uuid"} - set(dataset.schema.names)
        if not is_hf:
            missing |= set(OCEAN) - set(dataset.schema.names)
        result["ready"] = not missing and result["row_count"] > 0
        if missing:
            result["reason"] = "Required source fields missing: " + ", ".join(sorted(missing))
        elif not result["row_count"]:
            result["reason"] = "Installed dataset is empty"
        elif not is_hf:
            audit = location.audit if location.audit is not None else audit_installed_source(paths[0])
            result["behaviour_audit"] = audit
            result["ready"] = audit["ready"]
            if not audit["ready"]:
                result["reason"] = "Installed NGC dataset contains missing or invalid original IDs or OCEAN values"
    except (OSError, ValueError, pa.ArrowException):
        result["ready"] = False
        result["reason"] = "Installed dataset could not be read as a persona parquet dataset"
    return result


def dataset_catalogue() -> dict:
    """Report local readiness without network access, downloads or inference."""
    load_environment()
    return {"datasets": [_description(source) for source in ("hf-profile-only", "ngc")], "inference_calls": 0}


def _dataset(query: DatasetQuery):
    meta = _description(query.source)
    if not meta["ready"]:
        raise ValueError(meta.get("reason", "Dataset is not ready") + ". " + meta["setup"])
    dataset = pads.dataset([str(path) for path in _paths(query.source)], format="parquet")
    expression = None

    def add(part):
        nonlocal expression
        expression = part if expression is None else expression & part

    names = dataset.schema.names
    for value, compare in ((query.age_min, "min"), (query.age_max, "max")):
        if value is not None:
            if "age" not in names:
                raise ValueError("This source has no age field to filter")
            field = pads.field("age").cast(pa.int64())
            add(field >= value if compare == "min" else field <= value)
    for key, value in (("planning_area", query.planning_area), ("occupation", query.occupation),
                       ("education_level", query.education_level)):
        if value:
            # NGC Singapore stores a district rather than HF's planning_area.
            actual = "district" if key == "planning_area" and key not in names and "district" in names else key
            if actual not in names:
                raise ValueError(f"This source has no {key} field to filter")
            add(pc.utf8_lower(pads.field(actual).cast(pa.string())) == value.casefold())
    if query.search.strip():
        parts = [
            pc.match_substring(pads.field(key).cast(pa.string()), query.search.strip(), ignore_case=True)
            for key in names if key not in OCEAN
        ]
        any_field = parts[0]
        for part in parts[1:]:
            any_field = any_field | part
        add(any_field)
    return dataset, expression, meta


def persona_facets(source: PersonaSource = "hf-profile-only") -> dict:
    """Exact location and education options from this installed distribution.

    These are source-wide counts, not filtered counts or inferred attributes.
    Only the two projected columns are scanned; no persona narratives are returned.
    """
    dataset, _, meta = _dataset(DatasetQuery(source=source))
    geography = "planning_area" if "planning_area" in dataset.schema.names else "district"
    fields = [name for name in (geography, "education_level") if name in dataset.schema.names]
    table = dataset.to_table(columns=fields)
    facets = {}
    for name in fields:
        values = pc.value_counts(table[name]).to_pylist()
        facets[name] = sorted(
            [{"value": str(item["values"]), "count": item["counts"]} for item in values
             if item["values"] is not None and str(item["values"]).strip()],
            key=lambda item: item["value"].casefold(),
        )
    return {"source": source, "source_revision": meta["revision"], "row_count": meta["row_count"],
            "geography_field": geography, "fields": facets, "inference_calls": 0}


def _record(row: dict, meta: dict) -> dict:
    return {
        "source_id": str(row["uuid"]),
        "source": meta["source"],
        "source_revision": meta["revision"],
        "original_profile_sha256": profile_hash(row),
        "profile": row,
        "kind": "original",
    }


def browse_personas(query: DatasetQuery | dict | None = None) -> dict:
    query = query if isinstance(query, DatasetQuery) else DatasetQuery.model_validate(query or {})
    dataset, expression, meta = _dataset(query)
    matched = dataset.count_rows(filter=expression)
    remaining, collected = query.offset, []
    for batch in dataset.scanner(filter=expression, batch_size=1024, use_threads=False).to_batches():
        if remaining >= batch.num_rows:
            remaining -= batch.num_rows
            continue
        take = min(query.limit - len(collected), batch.num_rows - remaining)
        collected.extend(batch.slice(remaining, take).to_pylist())
        remaining = 0
        if len(collected) >= query.limit:
            break
    return {
        "dataset": meta,
        "records": [_record(row, meta) for row in collected],
        "offset": query.offset,
        "limit": query.limit,
        "total": matched,
        "has_more": query.offset + len(collected) < matched,
        "inference_calls": 0,
    }


def sample_personas(source: PersonaSource = "hf-profile-only", count: int = 1,
                    seed: int | None = None, filters: dict | None = None) -> dict:
    """Uniform reservoir sample over the actual filtered corpus, not the panel."""
    if not 1 <= count <= 20:
        raise ValueError("Choose one to twenty profiles")
    if seed is not None and (not isinstance(seed, int) or isinstance(seed, bool) or not 0 <= seed <= 2**63 - 1):
        raise ValueError("Sampling seed must be a nonnegative 63-bit integer")
    query = DatasetQuery.model_validate({**(filters or {}), "source": source, "offset": 0, "limit": 1})
    dataset, expression, meta = _dataset(query)
    chosen_seed = secrets.randbits(63) if seed is None else seed
    rng, selected, seen = random.Random(chosen_seed), [], 0
    # Scan only IDs until selected; then resolve full rows once.
    for batch in dataset.scanner(columns=["uuid"], filter=expression, batch_size=8192,
                                 use_threads=False).to_batches():
        for source_id in batch.column(0).to_pylist():
            seen += 1
            if len(selected) < count:
                selected.append(str(source_id))
            else:
                index = rng.randrange(seen)
                if index < count:
                    selected[index] = str(source_id)
    if seen < count:
        raise ValueError(f"Only {seen} profiles match these filters; requested {count}")
    locked = lock_personas(source, selected)
    return {**locked, "seed": chosen_seed, "sampling": "uniform without replacement over filtered local corpus",
            "matched_profiles": seen}


def lock_personas(source: PersonaSource, source_ids: list[str]) -> dict:
    """Resolve exact selected rows for freezing in a run, preserving requested order."""
    if not source_ids or len(source_ids) > 20 or len(source_ids) != len(set(source_ids)):
        raise ValueError("Select one to twenty distinct source IDs")
    if any(not isinstance(value, str) or not value or len(value) > 200 for value in source_ids):
        raise ValueError("Invalid source profile ID")
    dataset, _, meta = _dataset(DatasetQuery(source=source))
    matching = dataset.to_table(filter=pc.is_in(pads.field("uuid"), value_set=pa.array(source_ids))).to_pylist()
    by_id = {str(row["uuid"]): row for row in matching}
    if len(by_id) != len(matching):
        raise ValueError("Source IDs are not unique in this dataset")
    if any(source_id not in by_id for source_id in source_ids):
        raise ValueError("One or more selected IDs do not exist in this distribution")
    records = [_record(by_id[source_id], meta) for source_id in source_ids]
    return {"source": source, "dataset": meta["dataset"], "source_revision": meta["revision"],
            "source_ids": source_ids, "rows": [by_id[source_id] for source_id in source_ids], "records": records,
            "lock_sha256": profile_hash(records), "inference_calls": 0}
