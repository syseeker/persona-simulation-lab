"""Local Helix SDK scoring, using exact comparisons for transparent boolean criteria."""

import json
from pathlib import Path
import sys

from nhx_evals_sdk import Evaluator, ExactMatchMetric, RunConfig


def evaluate(rows: list[dict]) -> dict:
    if not rows:
        raise ValueError("No evaluation rows supplied")
    result = Evaluator().run_sync(
        metrics=[ExactMatchMetric(reference="{{item.expected}}", candidate="{{item.output}}")],
        dataset=rows,
        config=RunConfig(parallelism=1),
    )
    return result.model_dump(mode="json")


def main():
    source, destination = map(Path, sys.argv[1:3])
    rows = json.loads(source.read_text())
    result = evaluate(rows)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2))
    summary = {}
    for condition in sorted({r.get("condition", "default") for r in rows}):
        selected = [r for r in rows if r.get("condition", "default") == condition]
        summary[condition] = {
            "criteria": len(selected),
            "passed": sum(r["output"] == r["expected"] for r in selected),
        }
    print(json.dumps({"engine": "NeMo Helix Evals SDK", "summary": summary, "result_file": str(destination)}))


if __name__ == "__main__":
    main()
