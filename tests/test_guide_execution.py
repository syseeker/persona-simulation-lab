"""Public execution inspection stays condition-scoped and never reads native I/O."""
import json

import pytest

from learning_lab import guide_execution as guide


def test_retail_baseline_accounting_does_not_include_comparison_calls(monkeypatch):
    monkeypatch.setattr(guide, '_phoenix_running', lambda: False)
    result = guide.execution('dreamjob', public_turn=1)
    assert result['condition']['purpose'] == 'baseline'
    assert result['usage']['summary']['calls'] == 16
    assert result['run_usage'] == {'calls': 42, 'scope': 'whole-run'}
    assert result['usage']['summary']['known_tokens'] == 27983
    assert result['condition_span_count'] == len(result['spans']) == 10
    assert result['correlation']['status'] == 'condition-only'
    assert result['inference_calls_for_inspection'] == 0
    assert result['coverage'][-1]['status'] == 'not-established'
    assert all('input.value' not in row and 'annotated_request' not in row for row in result['spans'])


def test_comparison_condition_uses_its_own_accounting():
    baseline = guide.execution('dreamjob')
    condition = next(c for c in baseline['conditions'] if c['purpose'] == 'fixed-candidate')
    result = guide.execution('dreamjob', condition['id'])
    assert result['condition']['id'] == condition['id']
    assert result['usage']['summary']['calls'] == 4
    assert len(result['spans']) == 10
    assert result['selected_turn'] is None
    with pytest.raises(ValueError, match='does not belong'):
        guide.execution('photography', condition['id'])


def test_application_clarification_has_no_native_subtree():
    result = guide.execution('dreamjob', public_turn='2')
    assert result['selected_turn']['execution_kind'] == 'application_clarification'
    assert result['selected_turn']['agent_invoked'] is False
    assert result['correlation']['status'] == 'application-only'
    assert result['spans'] == result['tools'] == []
    assert result['condition_span_count'] == 10
    assert result['usage']['scope'] == 'condition'
    assert result['usage']['summary']['calls'] == 16


@pytest.mark.parametrize('turn', [True, 0, 4, '01', '../2'])
def test_invalid_turns_are_rejected(turn):
    with pytest.raises(ValueError, match='public turn'):
        guide.execution('dreamjob', public_turn=turn)


def test_missing_usage_is_unknown_and_provider_fields_are_allowlisted():
    result = guide._usage([
        {'role': 'assistant', 'latency_ms': 12, 'usage': {'total_tokens': 15},
         'headers': {'authorization': 'private'}, 'request': 'private'},
        {'role': 'assistant', 'latency_ms': None, 'usage': None},
        {'role': 'judge', 'latency_ms': float('nan'), 'usage': {'total_tokens': -5}},
    ])
    assert result['summary']['calls'] == 3
    assert result['summary']['known_tokens'] == 15
    assert result['summary']['unknown_usage_calls'] == 2
    assert result['summary']['unknown_latency_calls'] == 2
    assert 'private' not in json.dumps(result)


def test_stopped_or_foreign_phoenix_is_not_advertised(tmp_path, monkeypatch):
    path = tmp_path / 'import-receipt.json'
    path.write_text(json.dumps({'schema': 'citizen-phoenix-import/v1', 'status': 'verified',
                               'conditions': [{'scenario_id': 'photography', 'run_id': 'run',
                                               'condition_id': 'condition', 'project_name': 'project',
                                               'url': 'http://127.0.0.1:6006/projects/project/traces',
                                               'trace_urls': []}]}))
    monkeypatch.setattr(guide, 'PHOENIX_RECEIPT', path)
    assert not guide._phoenix('photography', 'run', 'condition')['available']
    monkeypatch.setattr(guide, '_phoenix_running', lambda: True)
    assert guide._phoenix('photography', 'run', 'condition')['available']
    assert not guide._phoenix('photography', 'run', 'other-condition')['available']
    value = json.loads(path.read_text())
    value['conditions'][0]['url'] = 'https://external.invalid/trace'
    path.write_text(json.dumps(value))
    assert not guide._phoenix('photography', 'run', 'condition')['available']


def test_recording_reads_do_not_open_raw_run_paths(monkeypatch):
    original = guide.Path.read_bytes

    def published_only(path):
        assert '/runs/journeys/' not in str(path)
        return original(path)

    monkeypatch.setattr(guide.Path, 'read_bytes', published_only)
    result = guide.execution('boardgames', public_turn=1)
    assert len(result['spans']) == 14
    assert result['usage']['summary']['calls'] == 11
