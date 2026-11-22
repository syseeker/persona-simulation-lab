"""Offline recovery checks: each actual 429 attempt is bounded and observable."""

import asyncio
from collections import deque
from contextlib import asynccontextmanager
from copy import deepcopy
from datetime import datetime, timezone
from email.utils import format_datetime
import json
from types import SimpleNamespace

import httpx
import pytest

from learning_lab import inference
from learning_lab.inference import Budget, BudgetExceeded, Gateway, ProviderRateLimited


def captured(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


@asynccontextmanager
async def mocked_gateway(monkeypatch, tmp_path, outcomes, *, retry_delays=(30, 60), **options):
    """A real Gateway and HTTPX transport, with a private clock and no real waits."""
    state = SimpleNamespace(now=1000.0, requests=[], sleeps=[], before_sleep=[],
                            timeouts=[], cancel_wait=False, sleep_overhead=0.0)
    pending = deque(outcomes)
    monkeypatch.setattr(inference, 'load_environment', lambda: None)
    monkeypatch.setenv('LAB_PROXY_API_KEY', 'offline-provider-secret-value')
    monkeypatch.setattr(inference, 'time', SimpleNamespace(
        monotonic=lambda: state.now, perf_counter=lambda: state.now))

    async def fake_sleep(delay):
        state.sleeps.append(delay)
        # The failed response must be on disk even if cancellation interrupts recovery.
        state.before_sleep.append(deepcopy(captured(tmp_path / 'gateway-calls.jsonl')))
        if state.cancel_wait:
            raise asyncio.CancelledError('Offline cancellation while awaiting rate-limit recovery')
        state.now += delay + state.sleep_overhead

    def bounded_timeout(delay):
        state.timeouts.append(delay)
        return asyncio.timeout(delay)

    # Do not replace asyncio's actual event-loop clock or globally replace sleep.
    monkeypatch.setattr(inference, 'asyncio', SimpleNamespace(
        sleep=fake_sleep, timeout=bounded_timeout, current_task=asyncio.current_task,
        CancelledError=asyncio.CancelledError))

    async def handle(request):
        state.requests.append(json.loads(request.content))
        assert pending, 'The gateway dispatched an unexpected additional attempt'
        outcome = pending.popleft()
        if isinstance(outcome, BaseException):
            raise outcome
        state.now += outcome.get('elapsed', 0)
        status = outcome.get('status', 200)
        response = {
            'id': 'offline-completion', 'model': 'fixture-provider-model',
            'choices': [{'finish_reason': 'stop',
                         'message': {'role': 'assistant', 'content': 'A source-supported answer.'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5, 'total_tokens': 15},
        } if status == 200 else {'error': {'message': 'Offline provider failure', 'type': 'fixture'}}
        return httpx.Response(status, json=outcome.get('response', response),
                              headers=outcome.get('headers', {}), request=request)

    budget = options.pop('budget', Budget())
    kwargs = {} if retry_delays is None else {'rate_limit_retry_delays': retry_delays}
    gateway = Gateway(budget, proxy_url='http://offline.invalid/v1', evidence_dir=tmp_path,
                      request_timeout=options.pop('request_timeout', 300), **kwargs, **options)
    await gateway._client.aclose()
    gateway._client = httpx.AsyncClient(transport=httpx.MockTransport(handle))
    state.gateway, state.budget = gateway, budget
    state.payload = {'model': 'fixture-input', 'messages': [{'role': 'user', 'content': 'Find a course.'}]}
    try:
        yield state
    finally:
        await gateway._client.aclose()


@pytest.mark.parametrize('failures, expected_waits', [(1, [30]), (2, [30, 60])])
async def test_429_recovery_records_every_attempt_before_waiting(
    monkeypatch, tmp_path, failures, expected_waits
):
    outcomes = [{'status': 429}] * failures + [{}]
    context = {'control_request_id': 'public-invocation', 'thread_id': 'persistent-thread',
               'transport': 'sandbox', 'public_turn': 2, 'private_profile': 'must-not-copy'}
    async with mocked_gateway(monkeypatch, tmp_path, outcomes) as case:
        result = await case.gateway.complete(case.payload, evidence_context=context)
        assert result['choices'][0]['message']['content'] == 'A source-supported answer.'
        assert case.sleeps == expected_waits
        assert case.budget.calls == len(case.requests) == failures + 1
        rows = captured(tmp_path / 'gateway-calls.jsonl')
        assert [row['attempt'] for row in rows] == list(range(1, failures + 2))
        assert len({row['logical_request_id'] for row in rows}) == 1
        assert [row['retry_of_call'] for row in rows] == [None, *range(1, failures + 1)]
        assert [row['http_status'] for row in rows] == [429] * failures + [200]
        assert [row['status'] for row in rows] == ['failed'] * failures + ['completed']
        assert 'retry_wait_seconds' not in rows[0]
        assert [row['retry_wait_seconds'] for row in rows[1:]] == expected_waits
        for index, receipt in enumerate(case.before_sleep):
            assert len(receipt) == index + 1
            assert receipt[-1]['http_status'] == 429 and receipt[-1]['status'] == 'failed'
            assert receipt[-1]['retry_status'] == 'scheduled'
            assert receipt[-1]['retry_delay_seconds'] == expected_waits[index]
            assert 'usage' not in receipt[-1]  # An unsuccessful provider response reported none.
        for row in rows:
            assert all(row[key] == value for key, value in context.items() if key != 'private_profile')
            assert 'private_profile' not in row
        assert rows[-1]['usage']['total_tokens'] == 15
        assert case.gateway.configuration()['provider_retries'] == 0


async def test_observed_recovery_wait_is_distinct_from_the_planned_delay(monkeypatch, tmp_path):
    async with mocked_gateway(monkeypatch, tmp_path, [{'status': 429}, {}]) as case:
        case.sleep_overhead = 0.375
        await case.gateway.complete(case.payload)
        rows = captured(tmp_path / 'gateway-calls.jsonl')
        assert rows[0]['retry_delay_seconds'] == 30
        assert 'retry_wait_seconds' not in rows[0]
        assert rows[1]['retry_wait_seconds'] == 30.375
        assert 'retry_delay_seconds' not in rows[1]
        assert case.timeouts == [300, 269.625]


async def test_repeated_429_exhausts_two_retries_without_an_unbudgeted_fourth_attempt(monkeypatch, tmp_path):
    async with mocked_gateway(monkeypatch, tmp_path, [{'status': 429}] * 3) as case:
        with pytest.raises(ProviderRateLimited):
            await case.gateway.complete(case.payload)
        assert case.sleeps == [30, 60]
        assert case.budget.calls == len(case.requests) == 3
        rows = captured(tmp_path / 'gateway-calls.jsonl')
        assert rows[-1]['retry_status'] == 'exhausted'
        assert [row['retry_wait_seconds'] for row in rows[1:]] == [30, 60]
        assert all(row['status'] == 'failed' and row['http_status'] == 429 for row in rows)


async def test_retry_is_not_scheduled_when_the_shared_call_budget_is_exhausted(monkeypatch, tmp_path):
    async with mocked_gateway(monkeypatch, tmp_path, [{'status': 429}] * 2, budget=Budget(limit=2)) as case:
        with pytest.raises(BudgetExceeded):
            await case.gateway.complete(case.payload)
        assert case.sleeps == [30]
        assert case.budget.calls == len(case.requests) == 2
        rows = captured(tmp_path / 'gateway-calls.jsonl')
        assert rows[-1]['retry_status'] == 'budget_exhausted'
        assert rows[-1]['error_type'] == 'ProviderRateLimited'


@pytest.mark.parametrize('role, delays, alias', [
    ('assistant', None, 'lab-advisor-fixed'),
    ('judge', (30, 60), 'lab-support'),
    ('simulator', (30, 60), 'lab-support'),
])
async def test_default_and_support_roles_do_not_recover_429(monkeypatch, tmp_path, role, delays, alias):
    async with mocked_gateway(monkeypatch, tmp_path, [{'status': 429}], retry_delays=delays) as case:
        with pytest.raises(ProviderRateLimited):
            await case.gateway.complete(case.payload, role=role)
        assert case.sleeps == [] and case.budget.calls == len(case.requests) == 1
        assert case.requests[0]['model'] == alias
        row = captured(tmp_path / 'gateway-calls.jsonl')[0]
        assert 'logical_request_id' not in row and 'attempt' not in row and 'retry_status' not in row


@pytest.mark.parametrize('outcome, error', [
    ({'status': 400}, RuntimeError), ({'status': 401}, RuntimeError), ({'status': 500}, RuntimeError),
    (httpx.ReadTimeout('Offline provider read timed out'), httpx.ReadTimeout),
    (TimeoutError('Offline logical request timeout'), TimeoutError),
])
async def test_only_a_real_provider_429_is_retriable(monkeypatch, tmp_path, outcome, error):
    async with mocked_gateway(monkeypatch, tmp_path, [outcome]) as case:
        with pytest.raises(error) as raised:
            await case.gateway.complete(case.payload)
        assert not isinstance(raised.value, ProviderRateLimited)
        assert case.sleeps == [] and case.budget.calls == len(case.requests) == 1
        row = captured(tmp_path / 'gateway-calls.jsonl')[0]
        assert row['status'] == 'failed' and 'retry_status' not in row


async def test_cancellation_during_wait_preserves_429_without_starting_another_attempt(monkeypatch, tmp_path):
    async with mocked_gateway(monkeypatch, tmp_path, [{'status': 429}, {}]) as case:
        case.cancel_wait = True
        with pytest.raises(asyncio.CancelledError):
            await case.gateway.complete(case.payload)
        assert case.sleeps == [30] and len(case.requests) == case.budget.calls == 1
        rows = captured(tmp_path / 'gateway-calls.jsonl')
        assert len(rows) == 1 and rows[0]['status'] == 'failed'
        assert rows[0]['error_type'] == 'ProviderRateLimited' and rows[0]['http_status'] == 429
        assert 'retry_wait_seconds' not in rows[0]


async def test_only_allowlisted_rate_headers_are_saved_with_credential_values_redacted(monkeypatch, tmp_path):
    headers = {'retry-after': '30', 'x-ratelimit-limit-requests': '120',
               'x-ratelimit-remaining-requests': 'offline-provider-secret-value',
               'authorization': 'Bearer offline-provider-secret-value',
               'set-cookie': 'session=private-cookie-value', 'x-private-debug': 'private-debug-value'}
    async with mocked_gateway(monkeypatch, tmp_path, [{'status': 429, 'headers': headers}, {}]) as case:
        await case.gateway.complete(case.payload)
        row = captured(tmp_path / 'gateway-calls.jsonl')[0]
        assert row['rate_limit_headers'] == {
            'retry-after': '30', 'x-ratelimit-limit-requests': '120',
            'x-ratelimit-remaining-requests': '[redacted]',
        }
        assert row['rate_limit_header_source'] == 'litellm'
        assert row['retry_after_seconds'] == 30
        serialized = (tmp_path / 'gateway-calls.jsonl').read_text()
        assert all(secret not in serialized for secret in (
            'offline-provider-secret-value', 'private-cookie-value', 'private-debug-value'))


@pytest.mark.parametrize('retry_after, expected_delay', [('5', 30), ('45', 45), ('60', 60)])
async def test_numeric_retry_after_preserves_the_authorized_minimum_wait(
    monkeypatch, tmp_path, retry_after, expected_delay
):
    async with mocked_gateway(monkeypatch, tmp_path, [
        {'status': 429, 'headers': {'retry-after': retry_after}}, {},
    ]) as case:
        await case.gateway.complete(case.payload)
        assert case.sleeps == [expected_delay] and case.budget.calls == 2
        rows = captured(tmp_path / 'gateway-calls.jsonl')
        assert rows[0]['retry_after_seconds'] == float(retry_after)
        assert rows[0]['retry_delay_seconds'] == expected_delay
        assert rows[1]['retry_wait_seconds'] == expected_delay


@pytest.mark.parametrize('retry_after', ['61', '120'])
async def test_provider_wait_above_sixty_seconds_stops_without_a_retry(monkeypatch, tmp_path, retry_after):
    async with mocked_gateway(monkeypatch, tmp_path, [
        {'status': 429, 'headers': {'retry-after': retry_after}}, {},
    ]) as case:
        with pytest.raises(ProviderRateLimited) as raised:
            await case.gateway.complete(case.payload)
        assert raised.value.retry_after_seconds == float(retry_after)
        assert case.sleeps == [] and case.budget.calls == len(case.requests) == 1
        row = captured(tmp_path / 'gateway-calls.jsonl')[0]
        assert row['retry_status'] == 'provider_wait_exceeds_bound'
        assert row['retry_after_seconds'] == float(retry_after)


@pytest.mark.parametrize('seconds, should_recover', [(45, True), (75, False)])
async def test_http_date_retry_after_is_interpreted_and_bounded(monkeypatch, tmp_path, seconds, should_recover):
    now = datetime(2026, 11, 22, 8, 0, tzinfo=timezone.utc)

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now if tz else now.replace(tzinfo=None)

    monkeypatch.setattr(inference, 'datetime', FixedDateTime)
    retry_date = format_datetime(datetime.fromtimestamp(now.timestamp() + seconds, tz=timezone.utc), usegmt=True)
    async with mocked_gateway(monkeypatch, tmp_path, [
        {'status': 429, 'headers': {'retry-after': retry_date}}, {},
    ]) as case:
        if should_recover:
            await case.gateway.complete(case.payload)
            assert case.sleeps == [seconds] and case.budget.calls == 2
        else:
            with pytest.raises(ProviderRateLimited):
                await case.gateway.complete(case.payload)
            assert case.sleeps == [] and case.budget.calls == 1
        rows = captured(tmp_path / 'gateway-calls.jsonl')
        assert rows[0]['retry_after_seconds'] == seconds
        if should_recover:
            assert rows[0]['retry_delay_seconds'] == seconds
            assert rows[1]['retry_wait_seconds'] == seconds


async def test_wait_and_attempt_time_share_one_logical_request_deadline(monkeypatch, tmp_path):
    # 20 seconds upstream + 30 recovery + 20 upstream leaves 30, not a fresh 100.
    async with mocked_gateway(monkeypatch, tmp_path, [
        {'status': 429, 'elapsed': 20}, {'status': 429, 'elapsed': 20}, {},
    ], request_timeout=100) as case:
        with pytest.raises(ProviderRateLimited):
            await case.gateway.complete(case.payload)
        assert case.sleeps == [30] and case.now == 1070
        assert case.timeouts == [100, 50]
        assert case.budget.calls == len(case.requests) == 2
        row = captured(tmp_path / 'gateway-calls.jsonl')[-1]
        assert row['retry_status'] == 'request_deadline_exhausted'


async def test_retried_model_attempts_do_not_duplicate_tool_rounds_or_mutate_the_request(monkeypatch, tmp_path):
    native = {
        'model': 'fixture-provider-model', 'choices': [{'finish_reason': 'tool_calls', 'message': {
            'role': 'assistant', 'content': None, 'tool_calls': [{
                'id': 'native-course-lookup', 'type': 'function',
                'function': {'name': 'get_course_details', 'arguments': '{"course_id":"course-1"}'},
            }],
        }}], 'usage': {'prompt_tokens': 10, 'completion_tokens': 5, 'total_tokens': 15},
    }
    async with mocked_gateway(monkeypatch, tmp_path, [
        {'status': 429}, {'status': 429}, {'response': native},
    ], allowed_tool_names={'get_course_details'}) as case:
        case.gateway.tool_rounds = inference.MAX_TOOL_ROUNDS - 1
        case.payload.update(max_completion_tokens=512, tools=[{'type': 'function', 'function': {
            'name': 'get_course_details', 'parameters': {'type': 'object'},
        }}])
        original = deepcopy(case.payload)
        rounds_at_dispatch = []

        async def on_request(payload, role, record):
            rounds_at_dispatch.append(case.gateway.tool_rounds)

        case.gateway.on_request = on_request
        result = await case.gateway.complete(case.payload)
        assert result == native
        assert case.gateway.tool_rounds == inference.MAX_TOOL_ROUNDS
        assert rounds_at_dispatch == [inference.MAX_TOOL_ROUNDS - 1] * 3
        assert case.payload == original
        assert case.requests[0] == case.requests[1] == case.requests[2]
        assert case.requests[0]['max_tokens'] == 512
        assert 'max_completion_tokens' not in case.requests[0]
        assert case.requests[0]['tools'][0]['function']['name'] == 'get_course_details'


async def test_recovery_does_not_sleep_when_first_delay_consumes_the_remaining_deadline(monkeypatch, tmp_path):
    async with mocked_gateway(monkeypatch, tmp_path, [{'status': 429}], request_timeout=30) as case:
        with pytest.raises(ProviderRateLimited):
            await case.gateway.complete(case.payload)
        assert case.sleeps == [] and case.budget.calls == len(case.requests) == 1
        assert captured(tmp_path / 'gateway-calls.jsonl')[0]['retry_status'] == 'request_deadline_exhausted'


@pytest.mark.parametrize('delays', [(30, 60, 60), (0,), (61,), (float('inf'),), (float('nan'),), (True,)])
def test_retry_schedule_cannot_exceed_the_authorized_bounds(delays):
    with pytest.raises(ValueError, match='at most two'):
        Gateway(Budget(), rate_limit_retry_delays=delays)
