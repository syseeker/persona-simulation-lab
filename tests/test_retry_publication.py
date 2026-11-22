"""A recovered request keeps its failed admission and bounded retry evidence."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import uuid

import pytest

from scripts import export_capture_evidence as captures
from scripts import export_guide_recording as recording
from scripts import retail_review


@pytest.fixture
def attempts(monkeypatch):
    monkeypatch.setenv('LAB_RETRY_PUBLICATION_TEST_SECRET', 'PRIVATE_RETRY_FIXTURE_SECRET')
    return [
        {'call': 1, 'role': 'assistant', 'mode': 'live', 'status': 'failed', 'http_status': 429,
         'error_type': 'ProviderRateLimited', 'usage': None,
         'logical_request_id': 'fixture-logical-request', 'attempt': 1, 'retry_of_call': None,
         'retry_status': 'scheduled', 'retry_delay_seconds': 30, 'retry_wait_seconds': 30.02,
         'retry_after_seconds': 15,
         'rate_limit_headers': {'retry-after': '15', 'x-ratelimit-remaining-requests': '0',
                               'x-ratelimit-fixture': 'PRIVATE_RETRY_FIXTURE_SECRET'},
         'rate_limit_header_source': 'litellm',
         'headers': {'Authorization': 'PRIVATE_RAW_HEADERS'}, 'private_context': 'PRIVATE_SIMULATOR'},
        {'call': 2, 'role': 'assistant', 'mode': 'live', 'status': 'completed', 'http_status': 200,
         'logical_request_id': 'fixture-logical-request', 'attempt': 2, 'retry_of_call': 1,
         'selected_model': 'fixture-vendor/model', 'usage': {'total_tokens': 10}},
    ]


def assert_public_attempts(actual, original):
    assert len(actual) == 2
    assert [(row['call'], row['status']) for row in actual] == [(1, 'failed'), (2, 'completed')]
    for public, private in zip(actual, original, strict=True):
        for key in ['logical_request_id', 'attempt', 'retry_of_call', 'retry_status', 'retry_delay_seconds',
                    'retry_wait_seconds', 'retry_after_seconds', 'rate_limit_header_source']:
            if key in private:
                assert public[key] == private[key]
    assert actual[0]['http_status'] == 429 and actual[0]['usage'] is None
    assert actual[0]['rate_limit_headers']['retry-after'] == '15'
    assert actual[0]['rate_limit_headers']['x-ratelimit-remaining-requests'] == '0'
    assert 'PRIVATE_' not in json.dumps(actual)


def test_capture_projection_preserves_failed_attempt_and_retry_chain_with_redaction(tmp_path, attempts):
    before = deepcopy(attempts)
    projected, kind = captures.projection(Path('gateway-calls.jsonl'), attempts, tmp_path, {})
    assert kind == 'application-projection'
    assert_public_attempts(captures.redactor(tmp_path)(projected), attempts)
    assert attempts == before


def test_ordinary_recording_preserves_retry_metadata_without_raw_headers(tmp_path, monkeypatch, attempts):
    run_id, episode_id = str(uuid.uuid4()), str(uuid.uuid4())
    source = tmp_path / 'private' / run_id
    source.mkdir(parents=True)
    (source / 'run.json').write_text(json.dumps({'run_id': run_id, 'episode_id': episode_id,
        'scenario_id': 'photography', 'status': 'completed', 'cleanup_confirmed': True}))
    (source / 'catalogue-snapshot.json').write_text('{"courses":[]}')
    (source / 'usersim-activations.jsonl').write_text('')
    trace = {'conversation': [], 'relay': {'scopes': []}, 'tools': [],
             'usage': {'calls': 2, 'records': attempts}, 'source_lock': {}, 'situation': {}, 'evaluation': None}
    monkeypatch.setattr(recording, 'load_environment', lambda: None)
    monkeypatch.setattr(recording, 'JourneyService', lambda: SimpleNamespace(folder=lambda _run: source,
                                                                          trace=lambda _run: trace))
    target = tmp_path / 'public' / run_id
    recording.export(run_id, note='Offline publication fixture; no model calls.', destination=target)
    published = json.loads((target / 'usage.json').read_text())
    assert published['calls'] == 2
    assert_public_attempts(published['records'], attempts)
    trace_publication = json.loads((target / 'trace.json').read_text())
    assert trace_publication['usage'] == published


def test_retail_condition_projection_keeps_both_attempts_and_their_context(tmp_path, attempts):
    (tmp_path / 'routing-comparison.json').write_text(json.dumps({
        'conditions': [{'condition_id': 'fixture-condition', 'label': 'fixed-candidate', 'usage': attempts}]}))
    emitted = {}
    retail_review.project(tmp_path, lambda name, value, *_args, **_kwargs:
                          emitted.update({name: recording.clean(value)}))
    condition = emitted['routing-comparison.json']['conditions'][0]
    assert condition['condition_id'] == 'fixture-condition'
    assert_public_attempts(condition['usage'], attempts)
