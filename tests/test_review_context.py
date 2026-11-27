"""Offline same-run supplements preserve original captures and private values."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import uuid

import pytest
import yaml

from learning_lab import guide_review_context as reader
from learning_lab.capture_semantics import artifact_semantics

spec = importlib.util.spec_from_file_location('review_exporter', Path(__file__).parents[1] / 'scripts/export_review_context.py')
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def saved_run(tmp_path, monkeypatch):
    monkeypatch.setattr(reader, '_git', lambda *_args: '')
    run_id, condition = str(uuid.uuid4()), str(uuid.uuid4())
    native = tmp_path / 'runs/journeys' / run_id
    public = tmp_path / 'recordings/dreamjob' / run_id
    capture = tmp_path / 'recordings/captures/dreamjob' / run_id
    put(native / 'run.json', {'scenario_id': 'dreamjob', 'status': 'completed'})
    instructions = {'system': {'content': 'Find public courses; preserve unknown facts.'}}
    config = {'config_format': 'nemo-agents-spec-v1', 'name': 'owned-agent', 'default_harness': 'deepagents',
        'harnesses': {'deepagents': {'kind': 'deepagents'}}, 'instructions': instructions,
        'models': {'default': {'model': 'public-alias'}}, 'mcp': {}, 'environment': {}, 'telemetry': {}}
    agent = native / 'managed' / condition / 'agent.yaml'
    agent.parent.mkdir(parents=True)
    agent.write_text(yaml.safe_dump(config))
    settings = native / 'managed' / condition / 'platform-effective-config.json'
    put(settings, {'condition_id': condition, 'client': {'base_url': 'http://127.0.0.1:8080', 'workspace': 'test', 'token_env': 'PRIVATE_ENV_NAME'},
        'server_executor': {'source': '/home/private/settings.yaml', 'source_sha256': 'a' * 64, 'scope': 'saved local executor selection',
            'settings': {'secrets': 'DO_NOT_PUBLISH', 'agents': {'deployments': {'openshell_executor': 'lab-openshell'}},
                'deployments': {'executors': [{'name': 'lab-openshell', 'backend': 'openshell', 'config': {
                    'gateway_endpoint': 'https://127.0.0.1:17670', 'platform_egress': {'host': 'host.docker.internal', 'port': 8080},
                    'serve_workdir': '/tmp', 'landlock_compatibility': 'hard_requirement', 'tls': {'client_key_path': '/home/private/key'}}}]}}}})
    rows = []
    for requirement, path in [('CAP-PLAT-01', settings), ('CAP-PLAT-02', agent)]:
        rows.append({'id': requirement, 'purpose': 'managed', 'condition_id': condition, 'artifacts': [{
            'id': sha(requirement.encode())[:24], 'location': path.relative_to(native).as_posix(),
            'sha256': sha(path.read_bytes()), 'role': 'native-effective-configuration', 'schema': 'FixtureConfig', 'access': 'private'}]})
    put(native / 'capture-manifest.json', {'rows': rows})
    public_rows = deepcopy(rows)
    for row in public_rows:
        for artifact in row['artifacts']:
            artifact.pop('location')
    put(capture / 'manifest.json', {'scenario_id': 'dreamjob', 'run_id': run_id, 'rows': public_rows,
        'source_manifest_sha256': sha((native / 'capture-manifest.json').read_bytes())})
    # The native SDK may add defaults to the submitted public instructions.
    registered = deepcopy(config)
    registered['instructions']['system']['mode'] = 'replace'
    put(public / 'platform-deployment.json', {'deployment': {'config': registered}})
    put(public / 'manifest.json', {'schema': 'citizen-recording/v1', 'scenario_id': 'dreamjob', 'run_id': run_id,
        'files': {'platform-deployment.json': sha((public / 'platform-deployment.json').read_bytes())}})
    return tmp_path, run_id, condition, native, public, capture


def test_offline_export_and_reader_keep_unchanged_originals_and_publish_useful_settings(saved_run):
    root, run_id, condition, native, public, capture = saved_run
    before = {str(p): sha(p.read_bytes()) for folder in [native, public, capture] for p in folder.rglob('*') if p.is_file()}
    target = exporter.export(run_id, root=root)
    result = reader.companion('dreamjob', run_id, root=root)
    assert result['available'] and len(result['artifacts']) == 2
    client = result['data']['managed-client-config.json']['configuration']
    assert client['selected_executor']['backend'] == 'openshell'
    assert client['selected_executor']['config']['landlock_compatibility'] == 'hard_requirement'
    agent = result['data']['managed-agent-config.json']['configuration']
    assert agent['default_harness'] == 'deepagents' and agent['instructions']['system']['content']
    serialized = json.dumps(result)
    assert all(value not in serialized for value in ['DO_NOT_PUBLISH', '/home/private', 'PRIVATE_ENV_NAME', 'client_key_path'])
    assert before == {path: sha(Path(path).read_bytes()) for path in before}
    assert target.exists() and not any(a['url'] for a in result['artifacts'])
    assert all(a['condition_id'] == condition and a['source_schema'] == 'FixtureConfig' for a in result['artifacts'])
    generated = result['data']['managed-agent-config.json']
    assert generated['secondary_source_sha256'] == {'platform-deployment.json': before[str(public / 'platform-deployment.json')]}
    with pytest.raises(ValueError, match='immutable'):
        exporter.export(run_id, root=root)


@pytest.mark.parametrize('change', ['file', 'condition', 'source-hash', 'recording', 'capture', 'symlink',
                                   'secondary-source', 'secondary-binding'])
def test_supplement_rejects_tampering_and_different_condition_sources(saved_run, change):
    root, run_id, _, _, public, capture = saved_run
    target = exporter.export(run_id, root=root)
    path = target / 'manifest.json'
    manifest = json.loads(path.read_text())
    if change == 'file':
        (target / 'managed-client-config.json').write_text('{}')
    elif change == 'condition':
        manifest['files']['managed-client-config.json']['condition_id'] = str(uuid.uuid4())
    elif change == 'source-hash':
        manifest['files']['managed-client-config.json']['source_sha256'] = 'b' * 64
    elif change == 'recording':
        (public / 'manifest.json').write_text('{}')
    elif change == 'capture':
        (capture / 'manifest.json').write_text('{}')
    elif change == 'secondary-source':
        (public / 'platform-deployment.json').write_text('{}')
    elif change == 'secondary-binding':
        manifest['files']['managed-agent-config.json']['secondary_source_sha256']['platform-deployment.json'] = 'b' * 64
    elif change == 'symlink':
        source = target / 'managed-client-config.json'
        outside = root / 'outside.json'
        source.rename(outside)
        source.symlink_to(outside)
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        reader.companion('dreamjob', run_id, root=root)


def test_missing_supplement_has_no_fallback_or_side_effects(tmp_path):
    assert reader.companion('photography', str(uuid.uuid4()), root=tmp_path) == {'available': False, 'data': {}, 'artifacts': []}
    assert not list(tmp_path.iterdir())


def test_export_rejects_modified_public_deployment_before_creating_output(saved_run):
    root, run_id, _, _, public, _ = saved_run
    path = public / 'platform-deployment.json'
    value = json.loads(path.read_text())
    value['deployment']['config']['models']['default']['model'] = 'unrecorded-model'
    put(path, value)
    with pytest.raises(ValueError, match='immutable recording hash'):
        exporter.export(run_id, root=root)
    assert not (root / 'recordings/review-context').exists()


def test_artifact_explanation_distinguishes_native_format_projection_and_application_receipts():
    result = artifact_semantics('CAP-FAB-01', {'path': 'fabric-config.projection.json', 'kind': 'application-projection'})
    assert result['direction'] == 'input' and 'FabricConfig' in result['purpose'] and 'omits' in result['purpose']
    result = artifact_semantics('CAP-GW-02', {'path': 'gateway-calls.projection.jsonl', 'kind': 'application-projection'})
    assert result['direction'] == 'output' and 'Application Gateway' == result['producer']
    result = artifact_semantics('CAP-HX-01', {'path': 'helix-criteria.projection.json', 'kind': 'application-projection'})
    assert result['direction'] == 'input' and 'does not author' in result['purpose']
