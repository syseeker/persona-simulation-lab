"""Local Helix SDK scoring, using exact comparisons for transparent boolean criteria."""

import json
from importlib.metadata import version
from pathlib import Path
import sys

from nhx_evals_sdk import Evaluator, ExactMatchMetric, RunConfig


def evaluate(rows: list[dict], configuration_path: Path | None = None) -> dict:
    if not rows:
        raise ValueError("No evaluation rows supplied")
    metrics = [ExactMatchMetric(reference="{{item.expected}}", candidate="{{item.output}}")]
    config = RunConfig(parallelism=1)
    if configuration_path is not None:
        configuration_path.parent.mkdir(parents=True, exist_ok=True)
        configuration_path.write_text(json.dumps({
            'engine': 'NeMo Helix Evals SDK', 'version': version('nemo-helix'),
            'mode': 'saved-output local evaluation', 'inference_calls': 0,
            'metrics': [metric.model_dump(mode='json') for metric in metrics],
            'run_config': config.model_dump(mode='json'),
            'dataset_rows': len(rows),
        }, indent=2) + '\n')
    result = Evaluator().run_sync(
        metrics=metrics,
        dataset=rows,
        config=config,
    )
    return result.model_dump(mode="json")


def main():
    source, destination = map(Path, sys.argv[1:3])
    rows = json.loads(source.read_text())
    result = evaluate(rows, destination.parent / 'helix-evaluator-config.json')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2))
    summary = {}
    for condition in sorted({r.get("condition", "default") for r in rows}):
        selected = [r for r in rows if r.get("condition", "default") == condition]
        summary[condition] = {
            "criteria": len(selected),
            "passed": sum(r["output"] == r["expected"] for r in selected),
        }
    print(json.dumps({"engine": "NeMo Helix Evals SDK", "version": version('nemo-helix'),
                      "summary": summary, "result_file": str(destination)}))


if __name__ == "__main__":
    main()
