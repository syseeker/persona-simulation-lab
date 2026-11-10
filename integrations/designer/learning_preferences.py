# /// script
# dependencies = ["data-designer==0.10.0"]
# ///
"""Generate labelled learning-preference hypotheses while preserving original profiles."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import data_designer.config as dd
from data_designer.interface import DataDesigner

ROOT = Path(__file__).resolve().parents[2]
PIPELINE_VERSION = "learning-overlay-v1"


def prepare_seed(destination: Path) -> Path:
    panel = json.loads((ROOT / "data/persona-review-panel.json").read_text())
    first = [next(p for p in panel if p["group"] == group) for group in ["early", "mid", "older"]]
    panel = first + [p for p in panel if p not in first]
    destination.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for person in panel:
        original = json.dumps(person, sort_keys=True)
        rows.append(
            {
                "source_id": person["source_id"],
                "source_revision": "a3994709410410f834bd949d643d3f2796908969",
                "original_profile_json": original,
                "original_profile_sha256": hashlib.sha256(original.encode()).hexdigest(),
            }
        )
    destination.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    return destination


def load_config_builder() -> dd.DataDesignerConfigBuilder:
    seed = Path(os.getenv("LAB_SEED_PATH", str(ROOT / "data/designer-seed.jsonl")))
    if not os.getenv("LAB_SEED_PATH") or not seed.exists():
        prepare_seed(seed)
    builder = dd.DataDesignerConfigBuilder()
    builder.with_seed_dataset(dd.LocalFileSeedSource(path=str(seed)))
    choices = {
        "learning_goal": [
            "Build workplace digital skills",
            "Explore a creative hobby",
            "Learn a practical community skill",
        ],
        "prior_familiarity": ["beginner", "some experience"],
        "delivery_preference": ["in person", "online", "either"],
        "budget_sgd": [50, 150, 300],
        "availability": ["weekends", "weekday evenings", "flexible"],
    }
    for name, values in choices.items():
        builder.add_column(
            dd.SamplerColumnConfig(
                name=name,
                sampler_type=dd.SamplerType.CATEGORY,
                params=dd.CategorySamplerParams(values=values),
            )
        )
    builder.add_column(
        dd.SamplerColumnConfig(
            name="overlay_id", sampler_type=dd.SamplerType.UUID, params=dd.UUIDSamplerParams()
        )
    )
    builder.add_column(dd.ExpressionColumnConfig(name="hypothesis", expr="True", dtype="bool"))
    builder.add_column(dd.ExpressionColumnConfig(name="pipeline_version", expr=PIPELINE_VERSION))
    return builder


def generate(output: Path, count=3):
    provider = dd.ModelProvider(
        name="nvidia", endpoint="https://integrate.api.nvidia.com/v1", api_key=os.getenv("NVIDIA_API_KEY")
    )
    result = DataDesigner(model_providers=[provider]).preview(load_config_builder(), num_records=count)
    records = result.dataset.to_dict(orient="records")
    for record in records:
        if (
            hashlib.sha256(record["original_profile_json"].encode()).hexdigest()
            != record["original_profile_sha256"]
        ):
            raise ValueError("An original profile changed during enrichment")
        if not record["hypothesis"]:
            raise ValueError("Every generated overlay must be labelled as hypothetical")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "pipeline_version": PIPELINE_VERSION,
                "record_count": len(records),
                "generator": "NeMo Data Designer 0.10.0 categorical samplers; zero inference calls",
                "records": records,
            },
            indent=2,
        )
    )
    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/learning-overlays.json")
    parser.add_argument("--count", type=int, default=3)
    args = parser.parse_args()
    if not 1 <= args.count <= 12:
        parser.error("This learning pipeline supports one to twelve preview records")
    records = generate(args.output, args.count)
    print(json.dumps({"records": len(records), "file": str(args.output), "inference_calls": 0}))
