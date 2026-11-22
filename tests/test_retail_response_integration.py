"""Offline integration: native proposals and application delivery stay distinct."""
from collections import deque
from contextlib import asynccontextmanager
from copy import deepcopy
import asyncio
import hashlib
import json
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
from nemo_fabric import RunResult
import pytest

from learning_lab.catalogue import Course, Preferences
from learning_lab.fabric_target import FabricTarget
from learning_lab.inference import Budget, Gateway
from learning_lab.retail_responses import RetailResponseBoundary


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def make_target(tmp_path, *, status='succeeded', content='A native model proposal.'):
    target = FabricTarget(SimpleNamespace(url='http://127.0.0.1:1/v1', tool_rounds=0),
                          tmp_path / 'workspace', 'offline-scripted')
    target.workspace.mkdir()
    requests = []

    class Runtime:
        async def invoke(self, *, request):
            requests.append(request)
            return RunResult.from_mapping({
                'agent_name': 'offline-retail', 'harness': 'deepagents', 'adapter_kind': 'python',
                'adapter_id': 'nvidia.fabric.langchain.deepagents', 'runtime_id': 'persistent-fixture',
                'invocation_id': request.request_id, 'request_id': request.request_id,
                'status': status, 'output': {'response': content},
                'error': {'code': 'fixture-failure', 'message': 'Native invocation failed.'}
                if status == 'failed' else None,
            })

    target.runtime = Runtime()
    return target, requests


async def test_three_native_invocations_keep_proposals_and_acknowledge_exact_public_delivery(tmp_path):
    proposal = 'A native proposal with an unsupported assurance.'
    target, requests = make_target(tmp_path, content=proposal)

    class Boundary:
        last_delivery_record = None

        def __init__(self):
            self.inputs = []
            self.pending = None

        def prepare_clarification(self, *_args, **_kwargs):
            return None  # This fixture verifies the native path when no early branch is selected.

        def apply(self, message, preferences, result):
            # Raw SDK evidence must already exist before application rendering.
            captured = records(tmp_path / 'fabric-run-results.jsonl')
            assert captured[-1]['result']['output']['response'] == proposal
            assert result['content'] == proposal
            self.inputs.append((message, preferences, deepcopy(result)))
            delivered = f'Application delivery for public turn {len(self.inputs)}.'
            self.pending = {**result, 'content': delivered, 'proposal_content': proposal,
                            'response_origin': 'application_source_only'}
            return self.pending

        def confirm_delivery(self, result):
            assert result is self.pending
            self.last_delivery_record = {'turn': len(self.inputs), 'delivered_content': result['content'],
                                         'response_origin': result['response_origin']}
            self.pending = None
            return result

    boundary = target.response_boundary = Boundary()
    messages = ['Retail data learning?', 'My salary is S$2,500–3,499.',
                'My total training budget is S$3,000. Weekends only.']
    preferences = [Preferences(goal='retail'), Preferences(goal='retail'),
                   Preferences(goal='retail', budget_sgd=3000, days=[5, 6])]
    delivered, acknowledgements = [], []
    for message, preference in zip(messages, preferences):
        prior_ack = deepcopy(boundary.last_delivery_record)
        response = await target.reply(message, preference)
        assert boundary.last_delivery_record == prior_ack
        response = boundary.confirm_delivery(response)  # Runtime confirms only after output rails pass.
        delivered.append(response)
        acknowledgements.append(deepcopy(boundary.last_delivery_record))
    assert len(requests) == target.invocation_count == len(boundary.inputs) == 3
    assert len({request.relay_session_root for request in requests}) == 1
    assert len({response['fabric']['runtime_id'] for response in delivered}) == 1
    assert len({request.request_id for request in requests}) == 3
    assert 'APPLICATION_DELIVERY_RECORD=' not in requests[0].input
    for index, request in enumerate(requests):
        assert request.input.startswith(messages[index] + '\n')
        assert json.loads(request.input.rsplit('\nLAB_PREFERENCES=', 1)[1]) == preferences[index].model_dump(
            mode='json', exclude_none=True)
        assert boundary.inputs[index][0] == messages[index]
        if index:
            encoded = request.input.split('\nAPPLICATION_DELIVERY_RECORD=', 1)[1].split('\nLAB_PREFERENCES=', 1)[0]
            assert json.loads(encoded) == acknowledgements[index - 1]
            assert json.loads(encoded)['delivered_content'] == delivered[index - 1]['content']
            assert proposal not in encoded
    native = records(tmp_path / 'fabric-run-results.jsonl')
    outcomes = records(tmp_path / 'reply-outcomes.jsonl')
    assert [row['result']['output']['response'] for row in native] == [proposal] * 3
    assert [row['content'] for row in outcomes] == [proposal] * 3
    assert all(response['content'] != proposal and response['proposal_content'] == proposal
               for response in delivered)
    assert [row['request_id'] for row in native] == [request.request_id for request in requests]


@pytest.mark.parametrize('status,content', [
    ('failed', 'A plausible native response does not repair failed execution.'),
    ('succeeded', ''), ('succeeded', '[ERROR: provider failure]'),
    ('succeeded', '<tool_call>search_courses</tool_call>'),
])
async def test_invalid_or_failed_native_proposal_cannot_be_rendered_into_success(tmp_path, status, content):
    target, requests = make_target(tmp_path, status=status, content=content)
    boundary = SimpleNamespace(last_delivery_record=None, apply=AsyncMock(),
                               prepare_clarification=lambda *_args, **_kwargs: None)
    target.response_boundary = boundary
    with pytest.raises(RuntimeError):
        await target.reply('Retail learning?', Preferences(goal='retail'))
    boundary.apply.assert_not_called()
    assert len(requests) == 1
    result = records(tmp_path / 'fabric-run-results.jsonl')[0]['result']
    assert result['status'] == status and result['output']['response'] == content
    assert records(tmp_path / 'reply-outcomes.jsonl')[0]['outcome']['status'] == 'invalid'


async def test_real_pre_agent_clarification_keeps_three_public_turns_but_only_two_native_invocations(
    tmp_path, monkeypatch,
):
    from learning_lab import fabric_target

    course = Course.model_validate({'id': 'SF-007', 'title': 'SMU Retail data programme',
        'provider': 'SMU Academy', 'kind': 'skillsfuture', 'summary': 'Practise retail data analysis.',
        'tags': ['retail', 'data'], 'source_url': 'https://example.edu/SF-007',
        'captured_on': '2026-11-22', 'duration_hours': 330, 'duration_months': 3,
        'price_min_sgd': 20928, 'price_max_sgd': 20928, 'weekdays': None}).model_dump(mode='json')
    catalogue = tmp_path / 'catalogue.json'
    catalogue.write_text(json.dumps({'courses': [course]}))
    tool = {'name': 'get_course_details', 'result': course, 'status': 'completed',
            'scope_uuid': 'offline-course-result', 'evidence_origin': 'native_relay'}
    monkeypatch.setattr(fabric_target, 'native_tool_records', lambda *_args, **_kwargs: [tool])
    native_proposal = 'Native proposal retained only as native evidence.'
    target, requests = make_target(tmp_path, content=native_proposal)
    boundary = target.response_boundary = RetailResponseBoundary(tmp_path, catalogue)
    first = await target.reply('Tell me about the SMU programme.', Preferences(goal='retail'))
    boundary.confirm_delivery(first)
    receipts_before = {name: (tmp_path / name).read_bytes() for name in (
        'fabric-run-requests.jsonl', 'fabric-run-results.jsonl',
        'reply-outcomes.jsonl', 'preferences-by-turn.jsonl', 'retail-model-proposals.jsonl')}
    lifecycle_before = records(tmp_path / 'fabric-lifecycle.jsonl')

    clarification = await target.reply('My salary is S$2,500–3,499.', Preferences(goal='retail'))
    assert len(requests) == target.invocation_count == 1
    assert clarification['response_origin'] == 'application_constraint_clarification'
    assert clarification['public_turn'] == clarification['response_policy']['public_turn'] == 2
    assert clarification['tools'] == [] and 'fabric' not in clarification
    for name, before in receipts_before.items():
        assert (tmp_path / name).read_bytes() == before
    lifecycle = records(tmp_path / 'fabric-lifecycle.jsonl')
    assert lifecycle[:-1] == lifecycle_before
    assert lifecycle[-1]['event'] == 'application_clarification_prepared'
    assert lifecycle[-1]['public_turn'] == 2 and lifecycle[-1]['agent_invoked'] is False
    assert boundary.last_delivery_record['public_turn'] == 1
    boundary.confirm_delivery(clarification)

    final = await target.reply('My total training budget is S$3,000. Weekends only.',
                               Preferences(goal='retail', budget_sgd=3000, days=[5, 6]))
    boundary.confirm_delivery(final)
    assert len(requests) == target.invocation_count == 2
    assert len({request.relay_session_root for request in requests}) == 1
    assert final['response_policy']['public_turn'] == 3
    ack = requests[1].input.split('\nAPPLICATION_DELIVERY_RECORD=', 1)[1].split('\nLAB_PREFERENCES=', 1)[0]
    acknowledgement = json.loads(ack)
    assert acknowledgement['content'] == clarification['content']
    assert acknowledgement['public_turn'] == 2
    assert native_proposal not in ack and '2,500' not in requests[1].input
    for name in ('fabric-run-requests.jsonl', 'fabric-run-results.jsonl', 'preferences-by-turn.jsonl'):
        native = records(tmp_path / name)
        assert [row['turn'] for row in native] == [1, 3]
        assert [row['public_turn'] for row in native] == [1, 3]
        assert [row['invocation_sequence'] for row in native] == [1, 2]
    assert [row['result']['output']['response'] for row in records(
        tmp_path / 'fabric-run-results.jsonl')] == [native_proposal, native_proposal]
    assert len(records(tmp_path / 'retail-model-proposals.jsonl')) == 2
    delivered = [row for row in records(tmp_path / 'retail-response-decisions.jsonl')
                 if row['status'] == 'delivered']
    assert [row['public_turn'] for row in delivered] == [1, 2, 3]


async def test_default_nonretail_fabric_path_keeps_original_answer_and_inputs(tmp_path):
    target, requests = make_target(tmp_path, content='A supported photography answer.')
    assert target.response_boundary is None
    for message in ['Saturday photography?', 'What is the venue?']:
        result = await target.reply(message, Preferences(goal='photography'))
        assert result['content'] == 'A supported photography answer.'
        assert 'response_origin' not in result and 'proposal_content' not in result
        assert requests[-1].input == message + '\nLAB_PREFERENCES=' + Preferences(
            goal='photography').model_dump_json(exclude_none=True)


@pytest.mark.parametrize('enabled,role,rejected', [
    (True, 'assistant', True), (False, 'assistant', False), (True, 'usersim', False),
])
async def test_retail_gateway_stops_truncation_without_losing_usage_or_changing_other_roles(
    tmp_path, monkeypatch, enabled, role, rejected,
):
    monkeypatch.setenv('LAB_PROXY_API_KEY', 'offline-fixture-proxy-key')
    usage = {'prompt_tokens': 100, 'completion_tokens': 1024, 'total_tokens': 1124}
    native = {'model': 'fixture-provider-model', 'usage': usage,
              'choices': [{'finish_reason': 'length',
                           'message': {'role': 'assistant', 'content': 'An unfinished native answer'}}]}
    gateway = Gateway(Budget(), proxy_url='http://fixture.invalid/v1', evidence_dir=tmp_path,
                      fail_on_truncated_output=enabled)
    gateway._client.post = AsyncMock(return_value=httpx.Response(200, json=native,
        request=httpx.Request('POST', 'http://fixture.invalid/v1/chat/completions')))
    try:
        call = gateway.complete({'model': 'fixture', 'messages': []}, role=role)
        if rejected:
            with pytest.raises(ValueError, match='truncat|token|length'):
                await call
        else:
            assert await call == native
        gateway._client.post.assert_awaited_once()
        assert gateway.budget.calls == 1
        recorded = gateway.budget.records[0]
        assert recorded['status'] == ('failed' if rejected else 'completed')
        assert recorded['finish_reason'] == 'length' and recorded['usage'] == usage
        assert records(tmp_path / 'gateway-calls.jsonl')[0] == recorded
        assert json.loads((tmp_path / 'gateway-effective-config.json').read_text())[
            'fail_on_truncated_output'] is enabled
    finally:
        await gateway._client.aclose()


@pytest.mark.parametrize('scenario,harness,rendered,output_status,early,input_status', [
    ('photography', 'deepagents', False, 'passed', False, 'passed'),
    ('boardgames', 'hermes', False, 'passed', False, 'passed'),
    ('dreamjob', 'deepagents', True, 'passed', False, 'passed'),
    ('dreamjob', 'deepagents', True, 'blocked', False, 'passed'),
    ('dreamjob', 'deepagents', True, 'passed', True, 'passed'),
    ('dreamjob', 'deepagents', True, 'blocked', True, 'passed'),
    ('dreamjob', 'deepagents', True, 'passed', True, 'blocked'),
])
async def test_sandbox_enables_retail_boundary_only_and_checks_delivered_output(
    tmp_path, monkeypatch, scenario, harness, rendered, output_status, early, input_status,
):
    from learning_lab import sandbox_runtime

    events, emitted, targets = [], [], []
    raw_catalogue = '{"courses": []}' if early else '{"fixture": true}'
    incoming = deque([json.dumps({'id': 'init', 'method': 'init', 'scenario_id': scenario,
        'harness': harness, 'model': 'offline-scripted', 'catalogue': raw_catalogue,
        'catalogue_sha256': hashlib.sha256(raw_catalogue.encode()).hexdigest()}) + '\n'])

    class Channel:
        def __init__(self, _output):
            self.pending = {}

        def emit(self, value):
            emitted.append(value)
            if value.get('id') == 'init':
                message = 'My salary is context.' if early else 'Public learning request'
                incoming.append(json.dumps({'id': 'invoke', 'method': 'invoke', 'message': message,
                    'preferences': {'goal': 'retail' if rendered else 'photography'}}) + '\n')
            if value.get('id') == 'invoke':
                incoming.append('{"id": "close", "method": "close"}\n')

    class Boundary:
        def __init__(self, *_args):
            events.append('boundary-enabled')
            self.last_delivery_record = None
            self.pending = None

        def prepare_clarification(self, *_args, **_kwargs):
            return None

        def apply(self, *_args):
            events.append('render')
            self.pending = {'content': 'Application-delivered answer', 'response_origin': 'application_source_only'}
            return self.pending

        def confirm_delivery(self, result):
            events.append('confirm-delivery')
            assert result is self.pending
            self.last_delivery_record = {'content': result['content']}
            self.pending = None
            return result

        def reject_delivery(self, reason):
            events.append(('reject-delivery', reason))
            self.pending = None

    class EarlyBoundary(RetailResponseBoundary):
        def __init__(self, *args):
            events.append('boundary-enabled')
            super().__init__(*args)

        def prepare_clarification(self, *args, **kwargs):
            events.append('prepare-clarification')
            return super().prepare_clarification(*args, **kwargs)

        def confirm_delivery(self, result):
            events.append('confirm-delivery')
            return super().confirm_delivery(result)

        def reject_delivery(self, reason):
            events.append(('reject-delivery', reason))
            return super().reject_delivery(reason)

    class Target(FabricTarget):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            targets.append(self)

            class Runtime:
                async def invoke(_self, *, request):
                    events.append('native-invocation')
                    assert not early, 'Application clarification must never invoke the native runtime'
                    return RunResult.from_mapping({'agent_name': 'offline-sandbox', 'harness': harness,
                        'adapter_kind': 'python', 'runtime_id': 'fixture-persistent-runtime',
                        'invocation_id': request.request_id, 'request_id': request.request_id,
                        'status': 'succeeded', 'output': {'response': 'Native proposal'}})

            self.runtime = Runtime()

        async def __aenter__(self):
            self.workspace.mkdir()
            return self

        async def __aexit__(self, *_args):
            pass

    class Rails:
        def __init__(self, *_args):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            pass

        async def check(self, boundary, text):
            events.append((boundary, text))
            decision = {'native_result': {'status': output_status if boundary == 'output' else input_status,
                                          'content': 'Configured Guardrails response'}}
            with (tmp_path / 'guardrails-decisions.jsonl').open('a') as output:
                output.write(json.dumps({'boundary': boundary, 'content': text, **decision}) + '\n')
            return decision

    class OfflineGateway:
        def __init__(self, *_args):
            self.url, self.tool_rounds = 'http://127.0.0.1:1/v1', 0

        @asynccontextmanager
        async def serving(self, **_kwargs):
            yield self

    async def next_line(function):
        await asyncio.sleep(0)
        return function()

    manifest = tmp_path / 'image-manifest.json'
    manifest.write_text('{"fixture": true}')
    monkeypatch.setattr(sandbox_runtime, 'RUN', tmp_path)
    monkeypatch.setattr(sandbox_runtime, 'ControlChannel', Channel)
    monkeypatch.setattr(sandbox_runtime, 'FabricTarget', Target)
    monkeypatch.setattr(sandbox_runtime, 'ExecGateway', OfflineGateway)
    monkeypatch.setattr(sandbox_runtime, 'export_artifacts', lambda *_args: None)
    monkeypatch.setattr(sandbox_runtime, 'Path', lambda _path: manifest)
    monkeypatch.setattr(sandbox_runtime.asyncio, 'to_thread', next_line)
    monkeypatch.setattr(sys, 'stdin', SimpleNamespace(readline=incoming.popleft))
    monkeypatch.setitem(sys.modules, 'learning_lab.retail_responses', SimpleNamespace(
        RetailResponseBoundary=EarlyBoundary if early else Boundary))
    monkeypatch.setitem(sys.modules, 'learning_lab.behavioural_safeguards', SimpleNamespace(BehaviouralSafeguards=Rails))
    original_stdout = sys.stdout
    try:
        await asyncio.wait_for(sandbox_runtime.serve(), timeout=2)
    finally:
        sys.stdout = original_stdout
    assert len(targets) == 1
    assert (targets[0].response_boundary is not None) is rendered
    invocation = next(value for value in emitted if value.get('id') == 'invoke')
    native = records(tmp_path / 'fabric-run-results.jsonl')
    if early:
        assert not native and targets[0].invocation_count == 0
        assert 'native-invocation' not in events
        assert not (tmp_path / 'retail-model-proposals.jsonl').exists()
        assert not (tmp_path / 'fabric-run-requests.jsonl').exists()
        assert not (tmp_path / 'preferences-by-turn.jsonl').exists()
        checked = records(tmp_path / 'guardrails-decisions.jsonl')
        assert checked[0]['boundary'] == 'input'
        if input_status == 'blocked':
            assert invocation['result']['guardrails_blocked'] is True
            assert len(checked) == 1 and 'prepare-clarification' not in events
            assert targets[0].response_boundary.last_delivery_record is None
            assert not (tmp_path / 'retail-response-decisions.jsonl').exists()
            return
        assert [row['boundary'] for row in checked] == ['input', 'output']
        clarification = checked[1]['content']
        assert 'What is your total training budget' in clarification
        assert 'On which days of the week' in clarification
        assert events.index(('input', 'My salary is context.')) < events.index('prepare-clarification')
        assert events.index('prepare-clarification') < events.index(('output', clarification))
        decisions = records(tmp_path / 'retail-response-decisions.jsonl')
        if output_status == 'blocked':
            assert 'error' in invocation and 'result' not in invocation
            assert [row['status'] for row in decisions] == ['validated', 'rejected']
            assert 'confirm-delivery' not in events
            assert targets[0].response_boundary.pending_delivery is None
            assert targets[0].response_boundary.last_delivery_record is None
        else:
            assert [row['status'] for row in decisions] == ['validated', 'delivered']
            result = invocation['result']
            assert result['content'] == clarification and 'fabric' not in result
            assert result['response_policy']['agent_invoked'] is False
            assert result['response_policy']['inference_calls'] == 0
            assert events.index(('output', clarification)) < events.index('confirm-delivery')
            assert targets[0].response_boundary.last_delivery_record['content'] == clarification
        return
    assert len(native) == 1 and native[0]['result']['output']['response'] == 'Native proposal'
    if output_status != 'passed':
        assert 'error' in invocation and 'result' not in invocation
        assert targets[0].response_boundary.last_delivery_record is None
        assert targets[0].response_boundary.pending is None
        assert 'confirm-delivery' not in events
        assert any(isinstance(event, tuple) and event[0] == 'reject-delivery' for event in events)
        checked = records(tmp_path / 'guardrails-decisions.jsonl')[-1]
        assert checked['content'] == 'Application-delivered answer'
        assert checked['native_result']['status'] == 'blocked'
        return
    result = invocation['result']
    assert result['content'] == ('Application-delivered answer' if rendered else 'Native proposal')
    if rendered:
        assert events.index('native-invocation') < events.index('render') < events.index(
            ('output', 'Application-delivered answer')) < events.index('confirm-delivery')
        assert ('output', 'Native proposal') not in events
        assert targets[0].response_boundary.last_delivery_record == {'content': result['content']}
    elif scenario == 'boardgames':
        assert ('output', 'Native proposal') in events
    else:
        assert not any(isinstance(event, tuple) for event in events)
