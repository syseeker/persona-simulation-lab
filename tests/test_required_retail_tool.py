"""Offline checks for the explicit retail lookup contract; no synthetic tool execution."""
from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
from nemo_fabric import RunResult
import pytest

from learning_lab import inference
from learning_lab.catalogue import Preferences
from learning_lab.fabric_target import FabricTarget
from learning_lab.inference import Budget, Gateway
from learning_lab.retail_responses import ResponseConfiguration
from learning_lab.sandbox_runtime import ExecGateway


def schema(name='search_courses'):
    return {'type': 'function', 'function': {'name': name, 'parameters': {'type': 'object'}}}


def completion(name='search_courses', arguments='{"goal":"retail analysis"}'):
    return {'choices': [{'finish_reason': 'tool_calls', 'message': {
        'role': 'assistant', 'content': None, 'tool_calls': [
            {'id': 'offline-call', 'type': 'function', 'function': {'name': name, 'arguments': arguments}}]}}]}


def payload():
    return {'model': 'offline', 'messages': [{'role': 'user', 'content': 'Retail analysis options?'}],
            'tools': [schema(), schema('get_course_details')], 'tool_choice': 'auto'}


@pytest.mark.parametrize('initial_choice', ['auto', 'none'])
async def test_named_choice_is_captured_once_without_mutating_harness_payload(tmp_path, initial_choice):
    gateway = Gateway(Budget(3), mode='demo', allowed_tool_names=['search_courses', 'get_course_details'],
                      evidence_dir=tmp_path)
    original = payload()
    original['tool_choice'] = initial_choice
    saved = deepcopy(original)
    gateway.required_initial_tool = 'search_courses'
    try:
        result = await gateway.complete(original)
        assert result['choices'][0]['message']['tool_calls'][0]['function']['name'] == 'search_courses'
        assert gateway.required_initial_tool is None
        assert gateway.tool_rounds == gateway.budget.calls == 1
        await gateway.complete(original)
        records = [json.loads(line) for line in (tmp_path / 'provider-tool-schemas.jsonl').read_text().splitlines()]
        assert records[0]['tool_choice'] == {'type': 'function', 'function': {'name': 'search_courses'}}
        assert records[1]['tool_choice'] == initial_choice
        assert original == saved
    finally:
        await gateway._client.aclose()


@pytest.mark.parametrize('result', [
    {'choices': [{'message': {'role': 'assistant', 'content': 'What is your budget?'}}]},
    completion('get_course_details'),
    completion('read_file'),
    completion(arguments='not JSON'),
    completion(arguments='[]'),
    completion(arguments='{"goal":""}'),
    {'choices': [{'message': {'tool_calls': []}}, completion()['choices'][0]]},
])
async def test_ignored_or_malformed_first_choice_fails_without_releasing_requirement(monkeypatch, tmp_path, result):
    gateway = Gateway(Budget(1), mode='demo', allowed_tool_names=['search_courses', 'get_course_details'],
                      evidence_dir=tmp_path)
    gateway.required_initial_tool = 'search_courses'
    monkeypatch.setattr(inference, 'scripted_completion', lambda _payload: deepcopy(result))
    try:
        with pytest.raises(ValueError):
            await gateway.complete(payload())
        assert gateway.required_initial_tool == 'search_courses'
        assert gateway.tool_rounds == 0 and gateway.budget.calls == 1
        record = json.loads((tmp_path / 'gateway-calls.jsonl').read_text())
        assert record['status'] == 'failed'
    finally:
        await gateway._client.aclose()


async def test_missing_schema_stops_before_provider_and_four_round_ceiling_stays_enforced(monkeypatch, tmp_path):
    gateway = Gateway(Budget(2), mode='demo', allowed_tool_names=['search_courses'], evidence_dir=tmp_path)
    gateway.required_initial_tool = 'search_courses'
    dispatch = AsyncMock()
    monkeypatch.setattr(inference, 'scripted_completion', dispatch)
    try:
        with pytest.raises(ValueError, match='absent'):
            await gateway.complete({**payload(), 'tools': [schema('read_file')]})
        gateway.tool_rounds = inference.MAX_TOOL_ROUNDS
        with pytest.raises(ValueError, match='absent'):
            await gateway.complete(payload())
        dispatch.assert_not_called()
        assert gateway.required_initial_tool == 'search_courses'
        assert gateway.tool_rounds == inference.MAX_TOOL_ROUNDS
        assert gateway.budget.calls == 2
    finally:
        await gateway._client.aclose()


async def test_exec_gateway_forwards_named_choice_and_checks_actual_host_response():
    forwarded = []

    class Channel:
        async def model(self, value):
            forwarded.append(deepcopy(value))
            return completion() if len(forwarded) == 2 else {'choices': [{'message': {'content': 'No lookup.'}}]}

    gateway = ExecGateway(Channel())
    gateway.required_initial_tool = 'search_courses'
    try:
        with pytest.raises(ValueError, match='ignored'):
            await gateway.complete(payload())
        assert gateway.required_initial_tool == 'search_courses'
        await gateway.complete(payload())
        assert gateway.required_initial_tool is None
        assert all(value['tool_choice']['function']['name'] == 'search_courses' for value in forwarded)
    finally:
        await gateway._client.aclose()


async def test_429_recovery_keeps_same_named_choice_and_admits_each_attempt(monkeypatch, tmp_path):
    monkeypatch.setattr(inference, 'load_environment', lambda: None)
    monkeypatch.setenv('LAB_PROXY_API_KEY', 'offline-key-not-a-credential')
    monkeypatch.setattr(inference.asyncio, 'sleep', AsyncMock())
    requests = []

    def provider(request):
        requests.append(json.loads(request.content))
        return httpx.Response(429, json={'error': {'message': 'test quota'}}) if len(requests) == 1 else httpx.Response(200, json=completion())

    gateway = Gateway(Budget(2), allowed_tool_names=['search_courses'], proxy_url='http://offline.invalid/v1',
                      evidence_dir=tmp_path, rate_limit_retry_delays=(30, 60), request_timeout=300)
    await gateway._client.aclose()
    gateway._client = httpx.AsyncClient(transport=httpx.MockTransport(provider))
    gateway.required_initial_tool = 'search_courses'
    try:
        await gateway.complete(payload())
        assert len(requests) == gateway.budget.calls == 2
        assert all(value['tool_choice'] == {'type': 'function', 'function': {'name': 'search_courses'}} for value in requests)
        assert [row['status'] for row in gateway.budget.records] == ['failed', 'completed']
        assert gateway.tool_rounds == 1 and gateway.required_initial_tool is None
    finally:
        await gateway._client.aclose()


@pytest.mark.parametrize('retail,budget,days,clarifies,expected', [
    (False, 3000, [5, 6], False, None),
    (True, None, None, False, None),
    (True, 3000, None, False, None),
    (True, 3000, [5, 6], False, 'search_courses'),
    (True, None, None, True, None),
])
async def test_fabric_arms_only_constrained_retail_native_dispatch_and_resets_each_turn(tmp_path, retail, budget, days, clarifies, expected):
    gateway = SimpleNamespace(url='http://127.0.0.1:1/v1', tool_rounds=0, required_initial_tool='stale')
    target = FabricTarget(gateway, tmp_path / 'workspace', 'offline-scripted')
    target.workspace.mkdir()
    observed = []

    class Runtime:
        async def invoke(self, *, request):
            observed.append(gateway.required_initial_tool)
            return RunResult.from_mapping({'agent_name': 'offline', 'harness': 'deepagents', 'adapter_kind': 'python',
                'adapter_id': 'nvidia.fabric.langchain.deepagents', 'status': 'succeeded',
                'runtime_id': 'offline-runtime', 'invocation_id': request.request_id, 'request_id': request.request_id,
                'output': {'response': 'An offline native proposal.'}})

    target.runtime = Runtime()
    if retail:
        target.response_boundary = SimpleNamespace(last_delivery_record=None,
            prepare_clarification=lambda *_args, **_kwargs: {'content': 'Clarify.', 'application_response_id': 'offline-app'} if clarifies else None,
            apply=lambda _message, _preferences, result: result)
    await target.reply('Retail learning.', Preferences(goal='retail', budget_sgd=budget, days=days))
    assert gateway.required_initial_tool == expected
    assert observed == ([] if clarifies else [expected])


def test_effective_response_policy_distinguishes_standalone_requirement_and_managed_path():
    policy = ResponseConfiguration(catalogue_sha256='offline-catalogue').model_dump()['required_initial_tool']
    assert policy['name'] == 'search_courses' and policy['harness_executes_tool'] is True
    assert policy['scope'] == 'standalone-retail-explicit-budget-and-study-days'
    assert policy['managed_enabled'] is False
