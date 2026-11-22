"""Offline execution/evaluation: an application clarification is not a Fabric call."""
from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

from nemo_fabric import RunResult
import pytest

from learning_lab.catalogue import all_courses
from learning_lab.fabric_target import FabricTarget
from learning_lab.retail import RetailPublicContext, freeze_retail_catalogue
from learning_lab.retail_checks import evaluate_retail
from learning_lab.retail_responses import RetailResponseBoundary
from learning_lab.settings import ROOT


def _records(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _row(result, key='persistent-thread'):
    return next(row for row in result['rows'] if row['id'] == key)


@pytest.fixture
async def recorded_case(tmp_path, monkeypatch):
    from learning_lab import fabric_target

    catalogue = tmp_path / 'catalogue-snapshot.json'
    freeze_retail_catalogue(catalogue)
    smu = next(course for course in all_courses(catalogue) if course.id == 'SF-007')
    tool = {'name': 'search_courses', 'status': 'completed', 'scope_uuid': 'offline-native-tool',
            'evidence_origin': 'native_relay', 'result': {'matches': [{'course': smu.model_dump(mode='json')}]}}
    monkeypatch.setattr(fabric_target, 'native_tool_records', lambda *_args, **_kwargs: [tool])
    # No provider, sandbox or running adapter is used. Each mock dispatch stands
    # for one native model call and retains the actual public turn from context.
    dispatch = AsyncMock(return_value='An offline native proposal.')
    gateway = SimpleNamespace(url='http://127.0.0.1:1/v1', tool_rounds=0, complete=dispatch)
    target = FabricTarget(gateway, tmp_path / 'workspace', 'offline-scripted', catalogue_path=catalogue)
    target.workspace.mkdir()
    context, requests, usage = RetailPublicContext(tmp_path), [], []

    class Runtime:
        async def invoke(self, *, request):
            requests.append(request)
            await context.audit({'messages': [{'role': 'user', 'content': request.input}]},
                                'assistant', {'call': len(requests)})
            content = await gateway.complete(public_turn=context.turn)
            usage.append({'role': 'assistant', 'public_turn': context.turn,
                          'status': 'completed', 'finish_reason': 'stop'})
            return RunResult.from_mapping({
                'agent_name': 'offline-retail', 'harness': 'deepagents', 'adapter_kind': 'python',
                'adapter_id': 'nvidia.fabric.langchain.deepagents', 'runtime_id': 'offline-persistent-runtime',
                'invocation_id': request.request_id, 'request_id': request.request_id,
                'status': 'succeeded', 'output': {'response': content},
            })

    target.runtime = Runtime()
    boundary = target.response_boundary = RetailResponseBoundary(tmp_path, catalogue)
    conversation = []
    for turn, message in enumerate([
        'I work in retail. Tell me about the SMU programme.',
        'My monthly salary is S$2,500–3,499.',
        'My total training budget is S$3,000. Weekends only.',
    ], 1):
        preferences = context.accept(message)
        response = await target.reply(message, preferences)
        response = boundary.confirm_delivery(response)
        conversation.extend([{'turn': turn, 'role': 'user', 'content': message},
                             {'turn': turn, 'role': 'assistant', **response}])
        if turn == 2:
            assert len(requests) == dispatch.await_count == 1
            assert response['tools'] == [] and 'fabric' not in response
    (tmp_path / 'usage.json').write_text(json.dumps({'records': usage}))

    def evaluate(rows=None):
        return evaluate_retail(rows if rows is not None else conversation, catalogue, [tool],
                               {'original_sha256': 'offline-original', 'source_revision': 'offline-revision'}, tmp_path)

    return SimpleNamespace(folder=tmp_path, conversation=conversation, requests=requests, dispatch=dispatch,
                           usage=usage, evaluate=evaluate)


def test_two_native_calls_and_confirmed_application_turn_pass_all_24_criteria(recorded_case):
    case = recorded_case
    result = case.evaluate()
    assert result['passed'] == result['total'] == 24, [row for row in result['rows'] if row['status'] != 'pass']
    assert result['inference_calls'] == 0  # Scoring saved output never generates another reply.
    execution = _row(result)['observed']
    assert execution['native_public_turns'] == [1, 3]
    assert execution['application_public_turns'] == [2]
    assert execution['native_invocation_count'] == 2
    assert len(case.requests) == case.dispatch.await_count == 2
    assert [call.kwargs['public_turn'] for call in case.dispatch.await_args_list] == [1, 3]
    assert [row['public_turn'] for row in _records(case.folder / 'fabric-run-results.jsonl')] == [1, 3]
    assert [row['invocation_sequence'] for row in _records(case.folder / 'fabric-run-results.jsonl')] == [1, 2]
    assert [row['public_turn'] for row in _records(case.folder / 'disclosure-audit.jsonl')] == [1, 3]
    review = result['delivery_review'][1]
    assert review['execution_kind'] == 'application_clarification' and review['agent_invoked'] is False
    assert review['inference_calls'] == 0 and review['delivery_status'] == 'delivered'
    assert review['model_proposal_rule_status'] == 'not_invoked'
    assert review['missing_constraints'] == ['budget_sgd', 'days']
    assert review['application_response_id'] == case.conversation[3]['application_response_id']
    assert 'inference_calls' not in result['delivery_review'][0]
    # The evaluator itself also leaves the dispatch count unchanged.
    assert case.dispatch.await_count == 2


@pytest.mark.parametrize('mutation', [
    'wrong-thread', 'wrong-runtime', 'missing-thread', 'missing-fabric', 'missing-invocation',
    'missing-public-turn', 'duplicate-invocation', 'failed-native', 'failed-outcome',
    'native-agent-not-invoked', 'wrong-policy-turn', 'wrong-public-pair-turn',
])
def test_native_failure_or_missing_identity_cannot_be_relabelled_as_success(recorded_case, mutation):
    case = recorded_case
    conversation = deepcopy(case.conversation)
    first, final = conversation[1], conversation[5]
    if mutation == 'wrong-thread':
        final['thread_id'] = 'different-thread'
    elif mutation == 'wrong-runtime':
        final['fabric']['runtime_id'] = 'different-runtime'
    elif mutation == 'missing-thread':
        final.pop('thread_id')
    elif mutation == 'missing-fabric':
        final.pop('fabric')
    elif mutation == 'missing-invocation':
        final['fabric'].pop('invocation_id')
    elif mutation == 'missing-public-turn':
        final.pop('public_turn')
        final.pop('turn')
    elif mutation == 'duplicate-invocation':
        final['fabric']['invocation_id'] = first['fabric']['invocation_id']
    elif mutation == 'failed-native':
        final['fabric']['status'] = 'failed'
    elif mutation == 'failed-outcome':
        final['outcome'] = {'status': 'invalid', 'code': 'native_failure'}
    elif mutation == 'native-agent-not-invoked':
        final['response_policy']['agent_invoked'] = False
    elif mutation == 'wrong-policy-turn':
        final['response_policy']['public_turn'] = 2
    else:
        conversation[4]['turn'] = 2
    result = case.evaluate(conversation)
    assert result['total'] == 24
    assert _row(result)['status'] == 'fail' and _row(result)['observed']['failures']


@pytest.mark.parametrize('mutation', [
    'not-confirmed', 'has-native-result', 'has-native-tool', 'called-model', 'bool-call-count',
    'missing-call-count', 'wrong-response-id', 'missing-constraints', 'wrong-content-hash',
    'changed-content', 'wrong-preferences', 'has-model-proposal', 'wrong-rule-status', 'missing-public-turn',
])
def test_application_turn_requires_a_matching_confirmed_zero_call_receipt(recorded_case, mutation):
    case = recorded_case
    conversation = deepcopy(case.conversation)
    reply = conversation[3]
    policy = reply['response_policy']
    if mutation == 'not-confirmed':
        policy['status'] = 'validated'
    elif mutation == 'has-native-result':
        reply['fabric'] = deepcopy(conversation[1]['fabric'])
    elif mutation == 'has-native-tool':
        reply['tools'] = [{'name': 'search_courses'}]
    elif mutation == 'called-model':
        policy['inference_calls'] = 1
    elif mutation == 'bool-call-count':
        policy['inference_calls'] = False
    elif mutation == 'missing-call-count':
        policy.pop('inference_calls')
    elif mutation == 'wrong-response-id':
        policy['application_response_id'] = 'different-response'
    elif mutation == 'missing-constraints':
        policy['missing_constraints'] = ['budget_sgd']
    elif mutation == 'wrong-content-hash':
        policy['delivered_content_sha256'] = 'different-content'
    elif mutation == 'changed-content':
        reply['content'] += ' This was not the confirmed delivery.'
    elif mutation == 'wrong-preferences':
        policy['public_preferences']['budget_sgd'] = 999
    elif mutation == 'has-model-proposal':
        policy['model_proposal_sha256'] = 'invented-native-proposal'
    elif mutation == 'wrong-rule-status':
        policy['model_proposal_rule_status'] = 'passed_selected_rules'
    else:
        reply.pop('public_turn')
    assert _row(case.evaluate(conversation))['status'] == 'fail'


@pytest.mark.parametrize('accounting', ['turn-2-call', 'unscoped-call', 'no-calls'])
def test_zero_call_declaration_must_agree_with_gateway_accounting(recorded_case, accounting):
    case = recorded_case
    usage = deepcopy(case.usage)
    if accounting == 'turn-2-call':
        usage.append({'role': 'assistant', 'status': 'completed', 'finish_reason': 'stop', 'public_turn': 2})
    elif accounting == 'unscoped-call':
        usage[0].pop('public_turn')
    else:
        usage = []
    (case.folder / 'usage.json').write_text(json.dumps({'records': usage}))
    assert _row(case.evaluate())['status'] == 'fail'


@pytest.mark.parametrize('legacy', [False, True])
def test_three_actual_native_calls_remain_valid_with_modern_or_older_turn_association(recorded_case, legacy):
    case = recorded_case
    conversation = deepcopy(case.conversation)
    second = conversation[3]
    for key in ['application_response_id', 'response_policy', 'response_origin']:
        second.pop(key)
    second['fabric'] = {**conversation[1]['fabric'], 'invocation_id': 'offline-native-turn-2'}
    if legacy:
        for reply in conversation[1::2]:
            reply.pop('public_turn')
            reply.pop('response_policy', None)
    result = case.evaluate(conversation)
    assert _row(result)['status'] == 'pass'
    assert _row(result)['observed']['native_public_turns'] == [1, 2, 3]
    assert _row(result)['observed']['native_invocation_count'] == 3
    assert _row(result)['observed']['application_public_turns'] == []


def test_immutable_historical_thread_only_record_keeps_its_limited_original_check(recorded_case):
    path = ROOT / 'recordings/dreamjob/8542330d-d6df-494e-8509-d81a5841d69e/public-conversation.json'
    conversation = json.loads(path.read_text())
    assert all('fabric' not in reply and 'response_policy' not in reply for reply in conversation[1::2])
    result = recorded_case.evaluate(conversation)
    assert _row(result)['status'] == 'pass'
    assert _row(result)['observed']['association'] == 'historical thread-only metadata'
    assert _row(result)['observed']['native_invocation_count'] is None
    assert _row(result)['observed']['native_public_turns'] == []
