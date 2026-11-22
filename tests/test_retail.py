"""Retail disclosure, native score mapping and ownership boundaries."""
import hashlib
import json
import uuid

import pytest

from learning_lab.designer_schema import validate_json_schema
from learning_lab.journey import JourneyService
from learning_lab.retail import OVERLAY_SCHEMA, RetailPublicContext, freeze_retail_catalogue, validate_retail_overlay
from learning_lab.settings import ROOT


def test_curated_retail_pack_preserves_partial_failure_and_separate_native_proof(monkeypatch):
    from learning_lab import guide_lessons
    # Historical endpoint failures remain evidence after a newer demo is promoted.
    monkeypatch.setitem(guide_lessons.CANONICAL_DEMOS, 'dreamjob', '8542330d-d6df-494e-8509-d81a5841d69e')
    result = guide_lessons.lesson_context('dreamjob')
    trace, context = result['trace'], result['context']
    assert trace['run']['status'] == 'failed' and trace['run']['cleanup_confirmed']
    assert trace['evaluation']['passed'] == trace['evaluation']['total'] == 20
    assert context['helix-job.json']['status'] == 'completed'
    comparisons = context['routing-comparison.json']['conditions']
    assert len(comparisons) == 4
    assert all(row['status'] == 'failed' for row in comparisons[:2])
    assert all(row['status'] == 'completed' for row in comparisons[2:])
    assert comparisons[3]['native_decisions'] and all(row['cleanup_confirmed'] for row in comparisons)
    assert len({row['input_sha256'] for row in comparisons}) == 1
    managed = context['platform-condition.json']
    assert managed['status'] == 'completed' and managed['cleanup_confirmed']
    assert managed['fresh_session'] and not managed['private_persona_in_image'] and not managed['local_memory_resumed']
    assert context['platform-trace.json']['spans'] and context['platform-trace.json']['tools']
    assert all(row['boundary_passed'] for row in context['disclosure-audit.jsonl'])
    for name in ['designer-output.json', 'platform-package.json', 'platform-invocation.json', 'platform-trace.json']:
        published = json.dumps(context[name])
        for forbidden in ['original_profile_json', 'reasoning_content', 'behavioral_profile', 'api_key', '/home/']:
            assert forbidden not in published


def test_current_retail_demo_preserves_complete_execution_and_public_boundaries():
    from learning_lab.guide_lessons import lesson_context

    result = lesson_context('dreamjob')
    trace, context = result['trace'], result['context']
    assert result['run_id'] == '8ce3ace2-0bb4-46f7-898c-795bc7da4794'
    assert trace['run']['status'] == 'completed' and trace['run']['cleanup_confirmed']
    assert trace['evaluation']['passed'] == trace['evaluation']['total'] == 24
    assert context['helix-job.json']['status'] == 'completed'

    comparison = context['routing-comparison.json']
    assert comparison['status'] == 'completed' and comparison['verified']
    assert comparison['routing_policy_verified'] and comparison['requested_access_verified']
    assert comparison['diagnostic_verified'] and comparison['diagnostic_status'] == 'passed'
    assert comparison['requested_model_coverage']['all_candidates_observed']
    conditions = comparison['conditions']
    assert [row['label'] for row in conditions] == [
        'fixed-candidate', 'switchyard', 'capable-access', 'available-fixed', 'available-switchyard']
    assert len({row['condition_id'] for row in conditions}) == 5
    assert len({row['input_sha256'] for row in conditions}) == 1
    assert len({row['catalogue_sha256'] for row in conditions}) == 1
    for row in conditions:
        assert row['status'] == row['execution_status'] == 'completed'
        assert row['verified'] and row['execution_verified'] and row['evaluation_verified']
        assert row['fresh_memory'] and row['cleanup_confirmed']
        assert row['evaluation']['passed'] == row['evaluation']['total'] == 24
        assert row['native_course_searches'] and row['actual_selected_models']
        if row['route'] == 'switchyard':
            assert row['native_decisions']
        else:
            assert row['native_decisions'] == []

    # Public turn 2 is a confirmed application clarification, never a fake Fabric call.
    native = context['fabric-invocations.json']
    assert [(row['public_turn'], row['invocation_sequence']) for row in native] == [(1, 1), (3, 2)]
    replies = [row for row in trace['conversation'] if row['role'] == 'assistant']
    assert [row['public_turn'] for row in replies] == [1, 2, 3]
    assert [row['response_policy']['execution_kind'] for row in replies] == [
        'native_agent', 'application_clarification', 'native_agent']
    assert len(context['application-turns.json']) == 1
    clarification = context['application-turns.json'][0]
    assert clarification['public_turn'] == 2 and clarification['status'] == 'delivered'
    assert clarification['agent_invoked'] is False and clarification['inference_calls'] == 0
    assert clarification['application_response_id'] == replies[1]['application_response_id']
    assert clarification['model_proposal_sha256'] is None
    assert clarification['missing_constraints'] == ['budget_sgd', 'days']
    assert clarification['delivered_content_sha256'] == hashlib.sha256(replies[1]['content'].encode()).hexdigest()
    assert all(row['response_policy']['model_proposal_semantically_certified'] is False for row in replies)

    audit = context['disclosure-audit.jsonl']
    assert audit and all(row['boundary_passed'] for row in audit)
    assert {row['public_turn'] for row in audit} == {1, 3}
    assert all(not row['salary_band_in_request'] and not row['public_salary_disclosed']
               for row in audit if row['public_turn'] == 1)
    constraints = context['public-constraints.jsonl']
    assert [row['salary_publicly_disclosed'] for row in constraints] == [False, True, True]
    assert [row['preferences']['budget_sgd'] for row in constraints] == [None, None, 3000]
    assert [row['preferences']['days'] for row in constraints] == [None, None, [5, 6]]

    managed = context['platform-condition.json']
    assert managed['parent_run_id'] == result['run_id']
    assert managed['status'] == 'completed' and managed['fresh_session'] and managed['cleanup_confirmed']
    assert not managed['private_persona_in_image'] and not managed['local_memory_resumed']
    assert managed['public_preferences'] == constraints[2]['preferences']
    assert context['platform-cleanup.json']['native_absence_confirmed']
    assert context['platform-cleanup.json']['errors'] == []
    intake = context['platform-trace.json']
    assert intake['status'] == 'observed' and intake['spans']
    assert intake['session_identity'] == context['platform-session.json']['session_identity']
    assert all(row['native_status'] == 'success' and row['result_state'] == 'returned' for row in intake['tools'])
    assert {row['name'] for row in intake['tools']} >= {'search_courses', 'get_course_details', 'compare_courses'}
    invocation = context['platform-invocation.json']
    assert invocation['session_id'] == managed['session_id']
    assert invocation['native_model_content_published'] is False
    assert invocation['application_delivery']['response_policy']['status'] == 'delivered'
    assert invocation['application_delivery']['response_origin'] == 'application_source_summary'
    for name in ['designer-output.json', 'platform-package.json', 'platform-invocation.json', 'platform-trace.json']:
        published = json.dumps(context[name])
        for forbidden in ['original_profile_json', 'reasoning_content', 'behavioral_profile', 'api_key', '/home/']:
            assert forbidden not in published


def test_salary_and_a_quoted_course_fee_never_become_training_budget(tmp_path):
    context = RetailPublicContext(tmp_path)
    one = context.accept('I work in retail. What is the fee for the SMU data programme, perhaps S$20,928?')
    two = context.accept('My monthly salary is S$2,500–3,499. I am worried about the cost.')
    three = context.accept('My total training budget is S$3,000. Weekends only, and a shorter option please.')
    assert one.budget_sgd is None and one.days is None
    assert two.budget_sgd is None and two.days is None
    assert three.budget_sgd == 3000 and three.days == [5, 6]
    assert context.salary_disclosed


async def test_actual_request_audit_stops_hidden_salary_before_dispatch(tmp_path):
    context = RetailPublicContext(tmp_path)
    context.accept('I want retail data analysis skills.')
    await context.audit({'messages': [{'role': 'user', 'content': 'SMU data analysis?'}]}, 'assistant', {'call': 1})
    with pytest.raises(ValueError, match='before public disclosure'):
        await context.audit({'messages': [{'role': 'system', 'content': 'Hidden salary 2500-3499'}]}, 'assistant', {'call': 2})
    context.accept('My monthly salary is S$2,500–3,499.')
    await context.audit({'messages': [{'role': 'user', 'content': 'Salary 2500-3499'}]}, 'assistant', {'call': 3})
    rows = [json.loads(line) for line in (tmp_path / 'disclosure-audit.jsonl').read_text().splitlines()]
    assert [row['boundary_passed'] for row in rows] == [True, False, True]
    assert all('messages' not in row for row in rows)


def test_designer_closed_schema_and_catalogue_preserve_their_boundaries(tmp_path):
    valid = {'preferred_brands': ['UNIQLO'], 'monthly_salary_range_sgd': '2500-3499',
             'learning_situation': 'Learn to analyse retail sales and inventory.'}
    validate_json_schema(valid, OVERLAY_SCHEMA)
    for bad in [{**valid, 'preferred_brands': ['invented brand']}, {**valid, 'monthly_salary_range_sgd': '9999'},
                {**valid, 'funding_eligibility': True}]:
        with pytest.raises(ValueError):
            validate_json_schema(bad, OVERLAY_SCHEMA)
    base = ROOT / 'catalogue/courses.json'
    before = hashlib.sha256(base.read_bytes()).hexdigest()
    snapshot = tmp_path / 'courses.json'
    freeze_retail_catalogue(snapshot)
    from learning_lab.catalogue import all_courses
    course = next(row for row in all_courses(snapshot) if row.id == 'SF-007')
    assert (course.price_max_sgd, course.duration_hours, course.duration_months) == (20928, 330, 3)
    assert hashlib.sha256(base.read_bytes()).hexdigest() == before


def test_private_designer_artifacts_are_not_made_public_by_matching_a_filename(tmp_path):
    service = JourneyService(tmp_path)
    identity, episode = str(uuid.uuid4()), str(uuid.uuid4())
    folder = service.folder(identity)
    private = folder / 'designer-private' / 'artifacts'
    private.mkdir(parents=True)
    (private / 'run.json').write_text('{"persona":"private fixture"}')
    (folder / 'run.json').write_text(json.dumps({'run_id': identity, 'episode_id': episode,
        'scenario_id': 'dreamjob', 'status': 'failed', 'created_at': 'fixture'}))
    assert not any('designer-private' in row['path'] for row in service.artifacts(identity)['artifacts'])


def test_primary_cleanup_cannot_hide_an_unresolved_comparison(tmp_path):
    identity = str(uuid.uuid4())
    runtime = tmp_path / 'comparisons' / identity / 'runtime'
    runtime.mkdir(parents=True)
    (runtime / 'sandbox-identity.json').write_text('{}')
    state = {'comparison_conditions': [identity]}
    assert not JourneyService._auxiliary_cleanup(state, tmp_path)
    (runtime / 'cleanup.json').write_text('{"native_absence_confirmed":true}')
    assert JourneyService._auxiliary_cleanup(state, tmp_path)


async def test_native_helix_scores_are_mapped_back_to_the_saved_criteria(tmp_path):
    from learning_lab.retail_experiments import score_with_helix
    if not (ROOT / 'integrations/helix/.venv/bin/python').is_file():
        pytest.skip('Compatible native Helix SDK environment not installed')
    evaluation = {'rows': [{'id': 'expected-pass', 'expected': True, 'actual': True},
                           {'id': 'expected-failure', 'expected': 20928, 'actual': 20000}]}
    result = await score_with_helix(evaluation, tmp_path)
    assert result['helix_used'] and result['passed'] == 1
    assert [row['helix_score'] for row in result['rows']] == [1, 0]
    assert result['sdk_version'] == '0.9.1'


def test_designer_text_cannot_redefine_money_constraints_or_publish_a_source_name():
    fields = {'preferred_brands': ['UNIQLO'], 'monthly_salary_range_sgd': '2500-3499',
              'learning_situation': 'Analyse retail sales and inventory with spreadsheets.'}
    original = {'first_name': 'PrivateFixtureName'}
    validate_retail_overlay(fields, original)
    for text in ['A budget of S$3000 per weekend.', 'PrivateFixtureName wants retail analysis skills.',
                 'Infer a salary from the source profile.']:
        with pytest.raises(ValueError):
            validate_retail_overlay({**fields, 'learning_situation': text}, original)


def test_duration_check_accepts_unicode_spaces_without_changing_the_saved_reply(tmp_path):
    from learning_lab.retail_checks import evaluate_retail
    catalogue = tmp_path / 'catalogue.json'
    freeze_retail_catalogue(catalogue)
    answer = 'The full fee is S$20,928. Duration: 3\u202fmonths (12\u202fweeks).'
    rows = [{'role': 'user', 'content': 'SMU retail learning?'}, {'role': 'assistant', 'content': answer}]
    result = evaluate_retail(rows, catalogue, [], {}, tmp_path)
    assert next(row for row in result['rows'] if row['id'] == 'published-duration')['status'] == 'pass'
    assert rows[1]['content'] == answer


async def test_empty_provider_timeout_is_a_nonempty_control_error(tmp_path):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock
    import httpx
    from learning_lab.sandbox import NativeSandbox
    sandbox = NativeSandbox(str(uuid.uuid4()), tmp_path, None, catalogue=tmp_path / 'catalogue.json')
    sandbox.image_verified = True
    sandbox.gateway = SimpleNamespace(complete=AsyncMock(side_effect=httpx.ReadTimeout('')))
    sandbox.send = AsyncMock()
    await sandbox.model({'id': 'fixture-control', 'payload': {}})
    sent = sandbox.send.call_args.args[0]
    assert sent['id'] == 'fixture-control' and sent['error'].startswith('ReadTimeout: ')
    assert 'result' not in sent


def test_funding_checks_preserve_unsupported_numerical_claims():
    from learning_lab.retail_policy import unsupported_funding_claims
    assert unsupported_funding_claims('Personal funding eligibility and the timetable are unknown.') == []
    assert unsupported_funding_claims('If you qualify for a typical SSG 50% subsidy, the net fee is lower.')
    assert unsupported_funding_claims('SkillsFuture Credit is capped at $500 per year.')


def test_native_tool_transport_success_does_not_turn_invalid_input_into_a_match():
    from learning_lab.journey_checks import valid_native_search
    tool = {'name': 'search_courses', 'status': 'completed', 'evidence_origin': 'native_relay'}
    assert valid_native_search({**tool, 'result': {'matches': []}})
    assert not valid_native_search({**tool, 'result': {'matches': [], 'error': 'Invalid kind'}})
    assert not valid_native_search(tool)


async def test_gateway_total_timeout_keeps_one_failed_admission_and_unknown_usage(monkeypatch):
    import asyncio
    from unittest.mock import AsyncMock
    from learning_lab.inference import Budget, Gateway
    monkeypatch.setenv('LAB_PROXY_API_KEY', 'fixture-proxy-key-no-network')
    gateway = Gateway(Budget(), proxy_url='http://fixture.invalid/v1', request_timeout=1)

    async def stalls(*_args, **_kwargs):
        await asyncio.sleep(30)

    gateway._client.post = AsyncMock(side_effect=stalls)
    try:
        with pytest.raises(TimeoutError):
            await gateway.complete({'model': 'fixture', 'messages': [{'role': 'user', 'content': 'Fixture'}]})
        assert gateway.budget.calls == 1 and gateway._client.post.await_count == 1
        record = gateway.budget.records[0]
        assert record['status'] == 'failed' and record['error_type'] == 'TimeoutError'
        assert record.get('usage') is None
    finally:
        await gateway._client.aclose()


async def test_gateway_preserves_the_fabric_adapter_output_limit(monkeypatch):
    from unittest.mock import AsyncMock
    import httpx
    from learning_lab.inference import Budget, Gateway
    monkeypatch.setenv('LAB_PROXY_API_KEY', 'fixture-proxy-key-no-network')
    gateway = Gateway(Budget(), proxy_url='http://fixture.invalid/v1')
    gateway._client.post = AsyncMock(return_value=httpx.Response(200, json={
        'model': 'fixture', 'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': 'Fixture reply'}}]},
        request=httpx.Request('POST', 'http://fixture.invalid/v1/chat/completions')))
    try:
        await gateway.complete({'model': 'fixture', 'messages': [], 'max_completion_tokens': 384})
        body = gateway._client.post.call_args.kwargs['json']
        assert body['max_tokens'] == 384 and 'max_completion_tokens' not in body
        assert gateway.budget.records[0]['output_token_limit'] == 384
    finally:
        await gateway._client.aclose()


def test_managed_recording_projection_omits_reasoning_and_auth_payloads(tmp_path):
    from scripts.retail_review import project
    from scripts.export_guide_recording import clean
    (tmp_path / 'platform-invocation.json').write_text(json.dumps({'public_input': 'Public budget',
        'response': {'id': 'native-fixture', 'api_key': 'PRIVATE-AUTH', 'choices': [{'index': 0,
            'message': {'role': 'assistant', 'content': 'Public reply', 'reasoning_content': 'PRIVATE-REASONING'}}]}}))
    projected = {}
    project(tmp_path, lambda name, value, *args, **kwargs: projected.update({name: clean(value)}))
    serialized = json.dumps(projected)
    assert 'native-fixture' in serialized and 'Public reply' in serialized
    assert 'PRIVATE-' not in serialized and 'reasoning_content' not in serialized and 'api_key' not in serialized


def test_managed_native_span_success_does_not_invent_a_missing_tool_result():
    from learning_lab.retail_managed import publishable_intake
    logs = {'intake': {'status': 'observed', 'spans': [
        {'span_id': 'fixture-one', 'parent_span_id': 'fixture-parent', 'name': 'search_courses',
         'kind': 'tool', 'status': 'success', 'input': '{"arguments":{"kind":"none"}}', 'output': None},
        {'span_id': 'fixture-two', 'name': 'model', 'kind': 'llm', 'status': 'success',
         'input': 'PRIVATE-PROMPT', 'output': 'PRIVATE-REASONING'},
    ]}}
    result = publishable_intake(logs)
    assert result['spans'][0]['parent_span_id'] == 'fixture-parent'
    assert result['tools'][0]['native_status'] == 'success' and result['tools'][0]['result_state'] == 'unavailable'
    assert result['tools'][0]['result'] is None
    assert 'PRIVATE-' not in json.dumps(result)
