"""Offline stop gates preserve cleanup and never advance past failed evidence."""
from contextlib import asynccontextmanager
from copy import deepcopy
import asyncio
import json
from unittest.mock import AsyncMock
import uuid

import pytest

from learning_lab.journey import JourneyService


def evaluation(passing=True):
    return {'helix_used': True, 'passed': int(passing), 'total': 1,
            'rows': [{'id': 'fixture', 'status': 'pass' if passing else 'fail',
                      'helix_score': int(passing)}]}


@pytest.fixture
def retail_run(tmp_path, monkeypatch):
    from learning_lab import journey, retail, retail_checks, retail_experiments, retail_managed

    class OfflineGateway:
        def __init__(self, *_args, **_kwargs):
            pass

        @asynccontextmanager
        async def serving(self):
            yield self

    class OfflineSandbox:
        def __init__(self, _identity, folder, *_args, **_kwargs):
            self.folder, self.thread_id = folder, 'fixture-thread'

        async def __aenter__(self):
            self.folder.mkdir(parents=True)
            return self

        async def __aexit__(self, *_args):
            (self.folder / 'cleanup.json').write_text('{"native_absence_confirmed": true}')

        async def probe_safeguards(self):
            return {'native_result': {'status': 'blocked'}}

    async def episode(_row, _gateway, _target, event, **_kwargs):
        await event({'role': 'user', 'content': 'Fixture public request'})
        await event({'role': 'assistant', 'content': 'Fixture public reply'})
        return {'simulation_outcome': {'status': 'max_turns_reached'}}

    def freeze(path):
        path.write_text('[]')
        return 'fixture-catalogue-hash'

    monkeypatch.setattr(journey, 'Gateway', OfflineGateway)
    monkeypatch.setattr(journey, 'NativeSandbox', OfflineSandbox)
    monkeypatch.setattr(journey, 'hosted_episode', episode)
    monkeypatch.setattr(journey, 'prepare_rows', lambda *_args, **_kwargs: [{}])
    monkeypatch.setattr(journey, 'native_tool_records', lambda *_args: [])
    monkeypatch.setattr(retail, 'freeze_retail_catalogue', freeze)
    monkeypatch.setattr(retail, 'create_retail_situation', AsyncMock(return_value={}))
    monkeypatch.setattr(retail_checks, 'evaluate_retail', lambda *_args: {})
    scorer = AsyncMock(return_value=evaluation())
    durable = AsyncMock(return_value={'status': 'completed'})
    routing = AsyncMock(return_value={'status': 'completed', 'verified': True})
    managed = AsyncMock(return_value={'status': 'completed', 'verified': True})
    monkeypatch.setattr(retail_experiments, 'score_with_helix', scorer)
    monkeypatch.setattr(retail_experiments, 'durable_evaluation', durable)
    monkeypatch.setattr(retail_experiments, 'compare_routing', routing)
    monkeypatch.setattr(retail_managed, 'run_managed_retail', managed)
    service = JourneyService(tmp_path / 'journeys')
    run_id, episode_id = str(uuid.uuid4()), str(uuid.uuid4())
    service._acquire(run_id)
    service.folder(run_id).mkdir()
    state = {'run_id': run_id, 'episode_id': episode_id, 'scenario_id': 'dreamjob',
             'status': 'queued', 'stage': 'persona', 'spec': {'source': 'ngc'}}
    lock = {'records': [{'source': 'ngc', 'source_id': 'private-fixture',
                        'source_revision': 'fixture-revision', 'original_profile_sha256': 'a' * 64}],
            'lock_sha256': 'b' * 64}
    return service, state, lock, scorer, durable, routing, managed


@pytest.mark.parametrize('failed_evaluation', [evaluation(False),
    {'helix_used': True, 'passed': 0, 'total': 0, 'rows': []}])
async def test_failed_or_empty_baseline_stops_all_later_conditions(retail_run, failed_evaluation):
    service, state, lock, scorer, durable, routing, managed = retail_run
    scorer.return_value = deepcopy(failed_evaluation)
    await service._execute(state, lock)
    for operation in [durable, routing, managed]:
        operation.assert_not_called()
    assert state['status'] == state['baseline_status'] == 'failed'
    assert state['stage'] == 'evaluate' and state['stopped_at'] == 'baseline'
    assert state['requires_user_review'] and state['stop_reason']
    assert state['cleanup_confirmed'] and not service.active.exists()
    assert state['evaluation_passed'] == 0
    assert all(value['status'] == 'not_run' for value in state['verification'].values())
    saved = json.loads((service.folder(state['run_id']) / 'evaluation.json').read_text())
    assert saved == failed_evaluation


@pytest.mark.parametrize('operation,failure,expected_calls,stage', [
    ('helix_job', RuntimeError('fixture durable failure'), (1, 0, 0), 'evaluate'),
    ('helix_job', {'status': 'failed'}, (1, 0, 0), 'evaluate'),
    ('routing', RuntimeError('fixture comparison failure'), (1, 1, 0), 'routing'),
    ('routing', {'status': 'failed', 'verified': False}, (1, 1, 0), 'routing'),
    ('managed', {'status': 'failed', 'verified': False}, (1, 1, 1), 'deploy'),
])
async def test_auxiliary_failure_stops_after_cleanup(retail_run, operation, failure, expected_calls, stage):
    service, state, lock, _scorer, durable, routing, managed = retail_run
    operations = {'helix_job': durable, 'routing': routing, 'managed': managed}
    selected = operations[operation]
    if isinstance(failure, Exception):
        selected.side_effect = failure
    else:
        selected.return_value = failure
    await service._execute(state, lock)
    assert tuple(value.await_count for value in operations.values()) == expected_calls
    assert state['status'] == 'failed' and state['baseline_status'] == 'completed'
    assert state['stage'] == stage and state['stopped_at'] == operation
    assert state['requires_user_review'] and state['stop_reason']
    assert state['verification'][operation]['status'] == 'failed'
    assert state['cleanup_confirmed'] and not service.active.exists()
    labels = list(operations)
    assert all(state['verification'][label]['status'] == 'not_run'
               for label in labels[labels.index(operation) + 1:])


async def test_cancelled_condition_stops_and_retains_baseline(retail_run):
    service, state, lock, _scorer, durable, routing, managed = retail_run
    routing.side_effect = asyncio.CancelledError()
    await service._execute(state, lock)
    durable.assert_awaited_once()
    managed.assert_not_called()
    assert state['status'] == 'cancelled' and state['baseline_status'] == 'completed'
    assert state['stopped_at'] == state['stage'] == 'routing'
    assert state['verification']['routing']['status'] == 'cancelled'
    assert state['cleanup_confirmed'] and not service.active.exists()


@pytest.mark.parametrize('capture_result', [RuntimeError('fixture manifest failure'),
    {'coverage': {'complete': False, 'missing': ['fixture-required']}}])
async def test_capture_failure_cannot_leave_run_completed(retail_run, monkeypatch, capture_result):
    from learning_lab import captures
    service, state, lock, *_ = retail_run
    state['capture_schema'] = 'citizen-captures/v1'

    def manifest(*_args):
        if isinstance(capture_result, Exception):
            raise capture_result
        return capture_result

    monkeypatch.setattr(captures, 'write_capture_manifest', manifest)
    await service._execute(state, lock)
    assert state['status'] == 'failed' and state['stopped_at'] == 'capture'
    assert state['requires_user_review'] and not state['capture_coverage']['complete']
    assert state['cleanup_confirmed'] and not service.active.exists()


async def test_capture_error_does_not_overwrite_original_failed_stop(retail_run, monkeypatch):
    from learning_lab import captures
    service, state, lock, scorer, *_ = retail_run
    state['capture_schema'] = 'citizen-captures/v1'
    scorer.return_value = evaluation(False)

    def manifest(*_args):
        raise RuntimeError('fixture manifest failure')

    monkeypatch.setattr(captures, 'write_capture_manifest', manifest)
    await service._execute(state, lock)
    assert state['status'] == 'failed' and state['stopped_at'] == 'baseline'
    assert state['stage'] == 'evaluate' and 'baseline evaluation failed' in state['stop_reason']
    assert not state['capture_coverage']['complete']
    assert state['cleanup_confirmed'] and not service.active.exists()


async def test_unconfirmed_cleanup_keeps_ownership_after_stop(retail_run, monkeypatch):
    service, state, lock, *_ = retail_run
    monkeypatch.setattr(service, '_auxiliary_cleanup', lambda *_args: False)
    try:
        await service._execute(state, lock)
        assert state['status'] == 'failed' and state['recovery_required']
        assert not state['cleanup_confirmed'] and service.active.exists()
        assert state['requires_user_review'] and 'cleanup is unconfirmed' in state['stop_reason']
    finally:
        service._release(state['run_id'], True)
