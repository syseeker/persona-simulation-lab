"""Historical conversion has no inference dependency and preserves provenance limits."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


MODULE = Path(__file__).resolve().parents[1] / 'integrations/observability/manage.py'
SPEC = importlib.util.spec_from_file_location('citizen_observability', MODULE)
observe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(observe)


def relay_source():
    common = {'uuid': 'llm1', 'parent_uuid': 'external-parent', 'propagation_root_uuid': 'root',
              'category': 'llm', 'name': 'advisor', 'metadata': {}}
    return {'scenario_id': 'scenario', 'run_id': 'run', 'condition_id': 'condition', 'purpose': 'baseline',
            'source': 'native-relay', 'source_path': 'saved/relay.jsonl', 'source_sha256': 'a' * 64,
            'events': [
                {**common, 'scope_category': 'start', 'timestamp': '2026-11-22T12:00:00.123456789Z',
                 'category_profile': {'annotated_request': {'model': 'advisor-model', 'messages': [
                     {'role': 'system', 'content': 'private system'},
                     {'role': 'user', 'content': 'public request'}], 'headers': {'Authorization': 'secret'}}}},
                {**common, 'scope_category': 'end', 'timestamp': '2026-11-22T12:00:01.123456999Z',
                 'category_profile': {'annotated_response': {'model': 'advisor-model',
                     'message': {'role': 'assistant', 'content': 'public reply', 'reasoning_content': 'private reasoning'},
                     'usage': {'prompt_tokens': 10, 'completion_tokens': 4, 'total_tokens': 14}}}},
                {'scope_category': 'mark', 'name': 'skills configured', 'parent_uuid': 'llm1',
                 'timestamp': '2026-11-22T12:00:00.223456789Z', 'data': {'private': 'not retained'}},
            ]}


def test_native_ids_intervals_and_missing_parent_are_preserved_without_fabrication():
    result = observe.convert(relay_source())
    span = result['spans'][0]
    assert span['start_ns'] == 1795348800123456789
    assert span['end_ns'] == 1795348801123456999
    assert len(span['trace_id']) == 32 and len(span['span_id']) == 16
    assert span['attributes']['citizen.import.parent_missing'] is True
    assert span['attributes']['citizen.native.start_time_unix_nano'] == str(span['start_ns'])
    assert span['events'][0]['name'] == 'skills configured'
    assert 'data' not in span['events'][0]
    again = observe.convert(relay_source())['spans'][0]
    assert span['span_id'] == again['span_id']
    other = relay_source()
    other['condition_id'] = 'another-condition'
    assert span['span_id'] != observe.convert(other)['spans'][0]['span_id']


def test_advisor_only_input_output_removes_provider_headers_system_prompts_and_reasoning():
    span = observe.convert(relay_source())['spans'][0]
    assert span['input']['messages'] == [{'role': 'user', 'content': 'public request'}]
    assert span['output']['message']['content'] == 'public reply'
    assert 'private' not in json.dumps(span)
    assert span['attributes']['llm.token_count.total'] == 14
    clean = observe.clean({'reasoning_content': 'private', 'nested': '{"api_key":"secret", "answer":"ok"}',
                           'text': '<think>private</think>public'})
    assert clean == {'nested': {'answer': 'ok'}, 'text': '[reasoning omitted]public'}


def test_duplicate_phase_fails_and_incomplete_scope_is_a_diagnostic():
    source = relay_source()
    source['events'].append(deepcopy(source['events'][0]))
    with pytest.raises(ValueError, match='Duplicate'):
        observe.convert(source)
    source = relay_source()
    source['events'].pop(1)
    result = observe.convert(source)
    assert not result['spans']
    assert result['diagnostics'][0]['status'] == 'incomplete'


def test_open_managed_record_is_an_explicit_marker_with_unknown_duration():
    source = {key: value for key, value in relay_source().items() if key != 'events'}
    source.update(source='native-helix-intake', purpose='managed', intake={
        'status': 'observed', 'spans': [{'span_id': 'open', 'trace_id': 'trace', 'kind': 'LLM',
            'name': 'open model span', 'started_at': '2026-11-22T12:00:00.123456', 'ended_at': None,
            'input': 'unbound prompt', 'output': 'unbound output'}], 'tools': []})
    result = observe.convert(source)
    span = result['spans'][0]
    assert span['status'] == 'UNSET' and span['end_ns'] == span['start_ns']
    assert span['attributes']['citizen.import.end_missing'] is True
    assert span['attributes']['citizen.native.end_time_unix_nano'] == ''
    assert span['input'] is None and span['output'] is None
    assert result['diagnostics'][0]['status'] == 'end-not-captured'


def test_source_hash_and_symbolic_links_are_rejected(tmp_path):
    path = tmp_path / 'source.json'
    path.write_text('{"safe":true}')
    assert observe.read_json(path, hashlib.sha256(path.read_bytes()).hexdigest()) == {'safe': True}
    with pytest.raises(ValueError, match='hash mismatch'):
        observe.read_json(path, 'f' * 64)
    link = tmp_path / 'link.json'
    link.symlink_to(path)
    with pytest.raises(ValueError, match='symbolic'):
        observe.read_json(link)


def test_credential_scan_fails_without_echoing_the_match(tmp_path, monkeypatch):
    monkeypatch.setattr(observe, 'ROOT', tmp_path)
    (tmp_path / '.env').write_text('PROVIDER_API_KEY=test-credential-12345\n')
    with pytest.raises(ValueError) as error:
        observe.scan_secrets({'content': 'test-credential-12345'})
    assert 'test-credential-12345' not in str(error.value)


def test_selected_sources_require_the_bound_private_manifest_and_managed_projection(tmp_path, monkeypatch):
    demos = {name: 'run-' + name for name in ('photography', 'boardgames', 'dreamjob')}
    monkeypatch.setattr(observe, 'ROOT', tmp_path)
    monkeypatch.setattr(observe, 'selected_demos', lambda: demos)
    for scenario, run_id in demos.items():
        run = tmp_path / 'runs/journeys' / run_id
        public = tmp_path / 'recordings/captures' / scenario / run_id
        run.mkdir(parents=True)
        public.mkdir(parents=True)
        relay = run / 'relay.jsonl'
        relay.write_text('\n'.join(json.dumps(row) for row in relay_source()['events']))
        private = run / 'capture-manifest.json'
        private.write_text(json.dumps({'scenario_id': scenario, 'run_id': run_id, 'rows': [{
            'id': 'CAP-REL-02', 'scenario_id': scenario, 'run_id': run_id,
            'condition_id': 'condition', 'purpose': 'baseline', 'availability': 'exists',
            'artifacts': [{'location': 'relay.jsonl', 'sha256': observe.digest(relay.read_bytes())}]}]}))
        (public / 'manifest.json').write_text(json.dumps({'scenario_id': scenario, 'run_id': run_id,
            'source_manifest_sha256': observe.digest(private.read_bytes())}))
        if scenario == 'dreamjob':
            condition = run / 'platform-condition.json'
            condition.write_text('{"condition_id":"managed-condition"}')
            projection = run / 'platform-trace.json'
            projection.write_text('{"status":"observed","spans":[],"tools":[]}')
            base = tmp_path / 'recordings' / scenario / run_id
            base.mkdir(parents=True)
            (base / 'manifest.json').write_text(json.dumps({'original_private_artifact_sha256': {
                p.name: observe.digest(p.read_bytes()) for p in (condition, projection)}}))
    results = observe.sources()
    assert len(results) == 4
    assert results[-1]['source_path'].endswith('/platform-trace.json')
    assert results[-1]['purpose'] == 'managed'
    projection.write_text('{"status":"observed","spans":["changed"]}')
    with pytest.raises(ValueError, match='hash mismatch'):
        observe.sources()


def test_stop_does_not_signal_a_foreign_process(monkeypatch):
    monkeypatch.setattr(observe, 'status', lambda: {'owned': False})
    monkeypatch.setattr(observe.os, 'kill', lambda *_args: pytest.fail('No foreign PID may be signalled'))
    assert observe.stop()['stopped'] is False
