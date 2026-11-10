"""Download the pinned public HF release and audit it locally (no model calls)."""

import argparse
import json

from huggingface_hub import hf_hub_download
from learning_lab.personas import DATASET, REVISION, choose_review_panel, inspect_dataset
from learning_lab.settings import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    folder = ROOT / "data" / "hf"
    if args.download:
        for i in range(2):
            hf_hub_download(
                DATASET,
                filename=f"data/train-{i:05d}-of-00002.parquet",
                repo_type="dataset",
                revision=REVISION,
                local_dir=folder,
            )
    paths = sorted((folder / "data").glob("*.parquet"))
    report = inspect_dataset(paths)
    output = ROOT / "data" / "persona-audit.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    (ROOT / "data" / "persona-review-panel.json").write_text(
        json.dumps(choose_review_panel(paths), indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                k: report[k]
                for k in [
                    "row_count",
                    "distinct_ids",
                    "age_range",
                    "age_bins",
                    "null_counts",
                    "unparseable_list_counts",
                    "ocean_fields_present",
                ]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
