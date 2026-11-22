"""Public capture packs preserve provenance without exposing private payloads."""
import hashlib
import importlib.util
import json
from pathlib import Path
import uuid

import pytest
import yaml

from learning_lab.captures import RULES, build_capture_manifest, write_capture_manifest

SPEC = importlib.util.spec_from_file_location('lab_capture_publication',
    Path(__file__).resolve().parents[1] / 'scripts/export_capture_evidence.py')
EXPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPORTER)
export = EXPORTER.export


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == '.jsonl':
        path.write_text(''.join(json.dumps(row) + '\n' for row in value))
    elif path.suffix in {'.yaml', '.yml'}:
        path.write_text(yaml.safe_dump(value))
    else:
        path.write_text(json.dumps(value))


def complete_run(root):
    run_id, condition, episode = (str(uuid.uuid4()) for _ in range(3))
    folder = root / run_id
    folder.mkdir(parents=True)
    state = {'scenario_id': 'photography', 'run_id': run_id, 'condition_id': condition,
             'episode_id': episode, 'status': 'failed', 'cleanup_confirmed': True, 'source_revision': 'fixture-revision'}
    write(folder / 'run.json', state)
    native = folder / episode / 'native'
    roots = {'root': folder, 'host': folder, 'sandbox': folder / episode, 'native': native}
    # Satisfy the real registry's complete photography requirements. This fixture
    # does not monkeypatch the manifest verifier or publish another run's files.
    initial = build_capture_manifest(folder, state)
    for row in initial['rows']:
        if not row['required']:
            continue
        rule = RULES[row['id']]
        for alternatives in rule.groups:
            pattern = alternatives[0]
            if rule.scope == 'boundary':
                scope, pattern = pattern.split('/', 1)
                base = roots[scope]
            else:
                base = roots[rule.scope]
            path = base / pattern.replace('*', 'fixture-runtime')
            write(path, [] if path.suffix == '.jsonl' else {})
    public = [{'turn': 1, 'role': 'user', 'content': 'Find a photography class.'},
              {'turn': 1, 'role': 'assistant', 'content': 'The catalogue has a photography class.'}]
    write(folder / 'public-conversation.json', public)
    write(folder / 'resolved-inputs.json', [{'persona': {'name': 'PRIVATE_ORIGINAL_PROFILE'},
        'usersim_config': {'locale': 'en_SG', 'max_turns': 1, 'private_context': 'PRIVATE_PREAMBLE'},
        'source_distribution': 'Singapore Extended', 'source_revision': 'fixture'}])
    write(folder / 'usersim-result.json', {'usersim_config': {'locale': 'en_SG', 'max_turns': 1},
        'simulation_outcome': {'status': 'failed', 'n_turns': 1}, 'simulation_traces': 'PRIVATE_TRACES',
        'persona': {'name': 'PRIVATE_ORIGINAL_PROFILE'}})
    write(native / 'fabric-config.json', {'schema_version': 'fixture', 'harness': {'adapter_id': 'deepagents'},
        'models': {'default': {'provider': 'openai-compatible', 'model': 'fixture', 'api_key_env': 'LAB_GATEWAY_KEY'}},
        'instructions': {'system': {'content': 'PRIVATE_APPLICATION_PROMPT'}},
        'environment': {'workspace': '/home/private-developer/work'},
        'mcp': {'servers': {'catalogue': {'env': {'NVIDIA_API_KEY': 'UNKNOWN_SECRET_VALUE'}}}}})
    request = {'request_id': 'request-one', 'thread_id': 'thread-one', 'turn': 1}
    write(native / 'fabric-run-requests.jsonl', [{**request, 'request': {
        'request_id': 'request-one', 'relay_session_root': 'thread-one',
        'input': public[0]['content'] + '\nLAB_PREFERENCES=' + json.dumps({'goal': 'photography'}),
        'context': {'private_context': 'PRIVATE_CONTEXT'}, 'overrides': None}}])
    write(native / 'fabric-run-results.jsonl', [{**request, 'boundary_status': 'returned', 'result': {
        'request_id': 'request-one', 'runtime_id': 'runtime-one', 'invocation_id': 'invocation-one', 'status': 'failed',
        'error': {'code': 'fixture-failure', 'message': 'PRIVATE_FAILURE_PAYLOAD'},
        'output': {'response': public[1]['content'], 'reasoning_content': 'PRIVATE_REASONING',
                   'messages': [{'role': 'system', 'content': 'PRIVATE_APPLICATION_PROMPT'}]},
        'metadata': {'private': 'PRIVATE_RESULT_METADATA'}}}])
    write(native / 'preferences-by-turn.jsonl', [{**request, 'preferences': {'goal': 'photography'}}])
    write(native / 'reply-outcomes.jsonl', [{'runtime_status': 'failed', 'raw_output': {'secret': 'PRIVATE_OUTPUT'}}])
    write(native / 'fabric-traces/fixture-runtime/relay.jsonl', [{
        'uuid': 'scope-one', 'scope_category': 'start', 'category': 'model', 'name': 'model',
        'data': {'system_prompt': 'PRIVATE_RELAY_PROMPT'}}, {
        'uuid': 'scope-one', 'scope_category': 'end', 'category': 'model', 'name': 'model',
        'data': {'reasoning_content': 'PRIVATE_RELAY_REASONING'}}])
    write(folder / 'gateway-effective-config.json', {'schema': 'citizen-gateway-config/v1', 'attempt_limit': 120,
        'request_timeout_seconds': 50, 'api_key': 'UNKNOWN_SECRET_VALUE', 'note': 'ENV_SECRET_VALUE'})
    write(folder / 'usersim-model-config.json', {'user_model': {'model_name': 'fixture', 'max_tokens': 1024,
                                                              'private_context': 'PRIVATE_PREAMBLE'}})
    write_capture_manifest(folder, state)
    return run_id, folder, state


def target(root, run_id):
    return root / 'published/captures/photography' / run_id


def test_complete_publication_retains_cap_rows_hashes_execution_failure_and_opaque_private_sources(tmp_path, monkeypatch):
    monkeypatch.setenv('LAB_CAPTURE_TEST_API_KEY', 'ENV_SECRET_VALUE')
    run_id, folder, state = complete_run(tmp_path / 'runs')
    before = {p.relative_to(folder): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
    destination = target(tmp_path, run_id)
    result = export(run_id, run_root=tmp_path / 'runs', destination=destination)
    manifest = json.loads((destination / 'manifest.json').read_text())
    assert result['rows'] == 51 and manifest['coverage']['complete'] is True
    assert manifest['scenario_id'] == state['scenario_id'] and manifest['run_id'] == run_id
    assert manifest['execution_status'] == 'failed'  # Completeness is not success.
    assert manifest['source_manifest_sha256'] == hashlib.sha256((folder / 'capture-manifest.json').read_bytes()).hexdigest()
    for name, digest in manifest['files'].items():
        assert hashlib.sha256((destination / name).read_bytes()).hexdigest() == digest
    for row in manifest['rows']:
        assert row['scenario_id'] == 'photography' and row['run_id'] == run_id
        for artifact in row['artifacts']:
            if artifact['access'] == 'private':
                assert 'location' not in artifact and artifact['id'] and artifact['sha256']
            else:
                assert artifact['source_artifact_ids'] and artifact['source_sha256']
                assert artifact['location'] in manifest['files']
    fabric = next(row for row in manifest['rows'] if row['id'] == 'CAP-FAB-02')
    assert fabric['publication_kind'] == 'projection' and fabric['publication_availability'] == 'exists'
    relay = next(row for row in manifest['rows'] if row['id'] == 'CAP-REL-03')
    assert relay['publication_kind'] == 'projection'
    configs = next(row for row in manifest['rows'] if row['id'] == 'CAP-GW-01')
    assert configs['publication_kind'] == 'redacted-native-configuration'
    serialized = '\n'.join(p.read_text() for p in destination.rglob('*') if p.is_file())
    for private in ['PRIVATE_ORIGINAL_PROFILE', 'PRIVATE_PREAMBLE', 'PRIVATE_APPLICATION_PROMPT', 'PRIVATE_CONTEXT',
                    'PRIVATE_REASONING', 'PRIVATE_RELAY_PROMPT', 'PRIVATE_RELAY_REASONING', 'PRIVATE_FAILURE_PAYLOAD',
                    'PRIVATE_RESULT_METADATA', 'PRIVATE_OUTPUT', 'UNKNOWN_SECRET_VALUE', 'ENV_SECRET_VALUE',
                    '/home/private-developer', str(folder)]:
        assert private not in serialized
    assert 'The catalogue has a photography class.' in serialized
    assert {p.relative_to(folder): p.read_bytes() for p in folder.rglob('*') if p.is_file()} == before


def test_capture_publication_is_immutable_and_rejects_destination_identity_swap(tmp_path):
    run_id, folder, _ = complete_run(tmp_path / 'runs')
    destination = target(tmp_path, run_id)
    export(run_id, run_root=folder.parent, destination=destination)
    before = (destination / 'manifest.json').read_bytes()
    with pytest.raises(ValueError, match='immutable'):
        export(run_id, run_root=folder.parent, destination=destination)
    assert (destination / 'manifest.json').read_bytes() == before
    with pytest.raises(ValueError, match='identify this scenario/run'):
        export(run_id, run_root=folder.parent, destination=tmp_path / 'boardgames' / run_id)


def test_capture_publication_refuses_missing_coverage_changed_bytes_and_cross_run_manifest(tmp_path):
    run_id, folder, _ = complete_run(tmp_path / 'runs')
    native = folder / json.loads((folder / 'run.json').read_text())['episode_id'] / 'native'
    (native / 'fabric-relay.json').unlink()
    state = json.loads((folder / 'run.json').read_text())
    write_capture_manifest(folder, state)
    with pytest.raises(ValueError, match='coverage is incomplete'):
        export(run_id, run_root=folder.parent, destination=target(tmp_path, run_id))
    assert not target(tmp_path, run_id).exists()
    write(native / 'fabric-relay.json', {})
    write_capture_manifest(folder, state)
    write(native / 'fabric-relay.json', {'changed': True})
    with pytest.raises(ValueError, match='no longer matches'):
        export(run_id, run_root=folder.parent, destination=target(tmp_path, run_id))
    other_id, other, _ = complete_run(tmp_path / 'runs')
    (folder / 'capture-manifest.json').write_bytes((other / 'capture-manifest.json').read_bytes())
    with pytest.raises(ValueError):
        export(run_id, run_root=folder.parent, destination=target(tmp_path, run_id))
    assert other_id != run_id and not target(tmp_path, run_id).exists()


@pytest.mark.parametrize('bad_location', ['../outside.json', '/tmp/outside.json', 'nested/../../outside.json', 'native\\outside.json'])
def test_unsupported_manifest_paths_never_become_public_locations(tmp_path, bad_location):
    run_id, folder, _ = complete_run(tmp_path / 'runs')
    path = folder / 'capture-manifest.json'
    value = json.loads(path.read_text())
    next(row for row in value['rows'] if row['artifacts'])['artifacts'][0]['location'] = bad_location
    write(path, value)
    with pytest.raises(ValueError, match='Unsupported capture source path'):
        export(run_id, run_root=folder.parent, destination=target(tmp_path, run_id))
    assert not target(tmp_path, run_id).exists()


def test_request_that_is_not_the_public_learner_message_is_never_published(tmp_path):
    run_id, folder, state = complete_run(tmp_path / 'runs')
    path = folder / state['episode_id'] / 'native/fabric-run-requests.jsonl'
    value = json.loads(path.read_text())
    value['request']['input'] = 'PRIVATE_SIMULATOR_PREAMBLE'
    write(path, [value])
    write_capture_manifest(folder, state)
    with pytest.raises(ValueError, match='does not match the public learner message'):
        export(run_id, run_root=folder.parent, destination=target(tmp_path, run_id))
    assert not target(tmp_path, run_id).exists()


def test_unconfirmed_cleanup_never_creates_a_publication_folder(tmp_path):
    run_id, folder, state = complete_run(tmp_path / 'runs')
    state['cleanup_confirmed'] = False
    write(folder / 'run.json', state)
    with pytest.raises(ValueError, match='confirmed cleanup'):
        export(run_id, run_root=folder.parent, destination=target(tmp_path, run_id))


def test_encoded_json_echo_redacts_secret_values_with_quotes_and_backslashes(tmp_path, monkeypatch):
    secret = 'private-value-"quoted"-back\\slash'
    monkeypatch.setenv('LAB_PUBLICATION_ECHO_SECRET', secret)
    run_id, folder, state = complete_run(tmp_path / 'runs')
    path = folder / 'gateway-effective-config.json'
    write(path, {'schema': 'citizen-gateway-config/v1',
                 'provider_echo': json.dumps({'echo': secret, 'nested': [json.dumps({'echo': secret})]})})
    write_capture_manifest(folder, state)
    destination = target(tmp_path, run_id)
    export(run_id, run_root=folder.parent, destination=destination)
    body = next(destination.rglob('*-gateway-effective-config.json')).read_text()
    assert secret not in body and 'private-value' not in body
    projected = json.loads(body)
    echo = json.loads(projected['provider_echo'])
    assert echo['echo'] == '[redacted]' and json.loads(echo['nested'][0])['echo'] == '[redacted]'
