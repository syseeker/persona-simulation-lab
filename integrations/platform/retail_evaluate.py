"""Submit saved Scenario 3 criteria as a real durable Helix evaluation job."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

from nemo_evals.sdk import Evaluator
from nemo_helix_plugin.client.client import NemoClient
from nemo_helix_plugin.client.types import RetryPolicy
from nemo_helix_plugin.evals.client import EvaluatorClient
from nhx_evals_sdk import ExactMatchMetric, RunConfig


def evaluate(criteria: Path, output: Path, spec: dict):
    rows = json.loads(criteria.read_text())
    if not rows or len(rows) > 100:
        raise ValueError('Choose one bounded saved criterion set')
    token = os.getenv(spec.get('token_env') or '')
    receipt = {'engine': 'NeMo Helix Platform Evals', 'mode': 'saved-output durable job',
               'inference_calls': 0, 'criteria': len(rows), 'status': 'not_submitted'}

    def save():
        output.write_text(json.dumps(receipt, indent=2, default=str) + '\n')

    with NemoClient(base_url=spec['base_url'], workspace=spec['workspace'], auth=token,
                    retry=RetryPolicy(max_retries=0), timeout=20) as client:
        evaluator = Evaluator.from_client(client)
        job = evaluator.submit(metric=ExactMatchMetric(reference='{{item.expected}}', candidate='{{item.output}}'),
                               dataset=rows, config=RunConfig(parallelism=1))
        receipt.update(status='submitted', job_name=job.name, submission=job.job.model_dump(mode='json'))
        save()
        try:
            job.wait_until_done(poll_interval_seconds=2, job_timeout_seconds=240, pending_timeout_seconds=90)
            receipt.update(status='completed', native_status=job.get_job_status().model_dump(mode='json'),
                           result=job.get_result().model_dump(mode='json'))
        except BaseException as exc:
            receipt.update(status='failed', error_type=type(exc).__name__, error=str(exc)[:1200],
                           native_status=job.get_job_status().model_dump(mode='json'))
            try:
                EvaluatorClient.from_client(client).cancel_evaluate_job(name=job.name)
                receipt['cancellation_requested'] = True
            except Exception as cleanup:
                receipt['cancellation_error'] = type(cleanup).__name__
            save()
            raise
        save()
    return receipt


if __name__ == '__main__':
    source, destination, spec = sys.argv[1:4]
    result = evaluate(Path(source), Path(destination), json.loads(spec))
    print(json.dumps({'status': result['status'], 'job_name': result['job_name'], 'inference_calls': 0}))
