"""Configuration evidence remains replayable, secret-free and distinct from outcomes."""
import json
import subprocess
from types import SimpleNamespace

import pytest

from learning_lab.settings import ROOT


def isolated(project, script, *arguments):
    python = ROOT / 'integrations' / project / '.venv/bin/python'
    if not python.is_file():
        pytest.skip(f'Install the isolated {project} environment')
    result = subprocess.run([str(python), '-c', script, *map(str, arguments)],
                            cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr[-3000:]
    return result


async def test_usersim_snapshot_records_actual_models_before_runtime(tmp_path, monkeypatch):
    from learning_lab import simulation

    seen = {}

    class Runtime:
        async def advance(self):
            return None

        async def finalize(self):
            return {'done': True}

        async def close(self):
            seen['closed'] = True

    def construct(row, *, models):
        seen['models'] = models
        return Runtime()

    monkeypatch.setattr(simulation.ProbeEpisodeRuntime, 'from_resolved_row', construct)
    monkeypatch.setenv('NIM_USER_MODEL', 'fixture-learner')
    monkeypatch.setenv('NIM_JUDGE_MODEL', 'fixture-judge')
    path = tmp_path / 'usersim-model-config.json'
    assert await simulation.hosted_episode({}, SimpleNamespace(mode='live'), None, None,
                                          model_config_path=path) == {'done': True}
    saved = json.loads(path.read_text())
    assert saved['models'] == simulation.host_model_settings(seen['models'])
    assert saved['models']['user_model']['model_name'] == 'fixture-learner'
    assert saved['models']['judge_model']['model_name'] == 'fixture-judge'
    assert seen['closed'] is True


def test_designer_native_settings_redact_auth_and_failed_profile_has_no_report(tmp_path):
    isolated('designer', '''
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'integrations/designer'))
import data_designer.config as dd
from data_designer.interface import DataDesigner
from data_designer.interface.errors import DataDesignerProfilingError
from learning_preferences import capture_settings, capture_profiling
out = Path(sys.argv[1])
designer = DataDesigner(model_providers=[dd.ModelProvider(name='fixture', endpoint='http://127.0.0.1:9/v1',
    api_key='fixture-private-provider-value', extra_headers={'Authorization': 'Bearer fixture-private-header'})])
designer.set_run_config(dd.RunConfig(max_conversation_restarts=0, max_in_flight_tasks=1, otel_metrics_port=None))
capture_settings(designer, out)
capture_profiling(out, error=DataDesignerProfilingError('NAType: fixture single-row profiler failure'),
                  batches=[out / 'completed.parquet'])
''', tmp_path)
    combined = ''.join(path.read_text() for path in tmp_path.glob('*.json'))
    assert 'fixture-private-provider-value' not in combined
    assert 'fixture-private-header' not in combined
    run_config = json.loads((tmp_path / 'designer-run-config.json').read_text())
    assert run_config['max_conversation_restarts'] == 0
    assert run_config['max_in_flight_tasks'] == 1
    providers = json.loads((tmp_path / 'designer-model-providers.json').read_text())
    assert providers['providers'][0]['endpoint'] == 'http://127.0.0.1:9/v1'
    receipt = json.loads((tmp_path / 'designer-profiling.json').read_text())
    assert receipt['status'] == 'failed' and receipt['analysis_report'] is None
    assert not (tmp_path / 'designer-analysis.json').exists()


def test_helix_saved_native_definition_can_replay_same_pass_and_failure(tmp_path):
    source = tmp_path / 'criteria.json'
    source.write_text(json.dumps([{'output': 'true', 'expected': 'true'},
                                  {'output': 'false', 'expected': 'true'}]))
    isolated('helix', '''
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'integrations/helix'))
from evaluate import evaluate
from nhx_evals_sdk import Evaluator, ExactMatchMetric, RunConfig
folder = Path(sys.argv[1])
rows = json.loads((folder / 'criteria.json').read_text())
first = evaluate(rows, folder / 'helix-evaluator-config.json')
saved = json.loads((folder / 'helix-evaluator-config.json').read_text())
second = Evaluator().run_sync(metrics=[ExactMatchMetric.model_validate(m) for m in saved['metrics']],
    dataset=rows, config=RunConfig.model_validate(saved['run_config'])).model_dump(mode='json')
def scores(result):
    return [row['metrics'] for row in result['row_scores']]
assert scores(first) == scores(second), (scores(first), scores(second))
(folder / 'replayed.json').write_text(json.dumps(second))
''', tmp_path)
    saved = json.loads((tmp_path / 'helix-evaluator-config.json').read_text())
    assert saved['metrics'][0]['reference'] == '{{item.expected}}'
    assert saved['metrics'][0]['candidate'] == '{{item.output}}'
    assert saved['run_config']['parallelism'] == 1
    assert saved['inference_calls'] == 0


def test_platform_create_captures_native_request_not_just_status(tmp_path):
    isolated('platform', '''
import asyncio, json, sys
from pathlib import Path
from types import SimpleNamespace
from pydantic import BaseModel
sys.path.insert(0, str(Path.cwd() / 'integrations/platform'))
from bridge import execute
class Deployment(BaseModel):
    status: str = 'running'
    name: str = 'fixture-deployment'
class Client:
    workspace = 'fixture-workspace'
    async def create_deployment(self, *, body):
        self.body = body
        return SimpleNamespace(data=lambda: Deployment())
async def run():
    client = Client()
    result = await execute(client, 'deploy', {'agent': 'fixture-agent', 'name': 'fixture-deployment',
        'image': 'fixture:1', 'environment': 'fixture-workspace/fixture-environment'})
    assert result['native_operation']['request'] == client.body.model_dump(mode='json')
    assert result['native_operation']['response']['status'] == 'running'
    (Path(sys.argv[1]) / 'deployment.json').write_text(json.dumps(result))
asyncio.run(run())
''', tmp_path)
    native = json.loads((tmp_path / 'deployment.json').read_text())['native_operation']
    assert native['operation'] == 'create_deployment'
    assert native['request']['image'] == 'fixture:1'
    assert native['request']['environment'] == 'fixture-workspace/fixture-environment'
