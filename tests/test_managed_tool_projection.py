"""Decode the complete native Helix MCP result before validating source-only delivery."""
from copy import deepcopy
import json

import pytest

from learning_lab.catalogue import Course, Preferences
from learning_lab.retail_managed import publishable_intake
from learning_lab.retail_responses import RetailResponseBoundary


def course(identity, **changes):
    return Course.model_validate({'id': identity, 'title': f'Retail data {identity}',
        'provider': 'Example Academy', 'kind': 'skillsfuture', 'summary': 'Practise retail data analysis.',
        'tags': ['retail', 'data'], 'source_url': f'https://example.edu/{identity}',
        'captured_on': '2026-11-22', 'duration_hours': 7, 'weekdays': [5],
        'price_min_sgd': 100, 'price_max_sgd': 100, 'extra_cost_sgd': 0,
        **changes}).model_dump(mode='json')


def intake(name, blocks, *, arguments=None, status='success'):
    return {'intake': {'status': 'observed', 'session_identity': {'resource_name': 'fixture-session'}, 'spans': [
        {'span_id': 'fixture-model-span', 'name': 'model', 'input': 'PRIVATE_PROMPT', 'output': 'PRIVATE_PROPOSAL'},
        {'span_id': 'fixture-tool-span', 'parent_span_id': 'fixture-model-span',
         'name': name, 'status': status, 'input': json.dumps({'arguments': arguments or {}}),
         'output': json.dumps({'source_call_id': 'fixture-call', 'content': blocks, 'extra': {}})}]}}


def text(value):
    return {'type': 'text', 'text': json.dumps(value)}


@pytest.mark.parametrize('count', [2, 3])
def test_native_comparison_preserves_every_course_text_block_and_native_identity(count):
    courses = [course(f'SF-{i:03}') for i in range(count)]
    source = intake('compare_courses', [text(row) for row in courses],
                    arguments={'course_ids': [row['id'] for row in courses]})
    before = deepcopy(source)
    projection = publishable_intake(source)
    tool = projection['tools'][0]
    assert tool['result'] == courses
    assert tool['result_state'] == 'returned' and tool['native_status'] == 'success'
    assert tool['source_span_id'] == 'fixture-tool-span'
    assert projection['spans'][1]['parent_span_id'] == 'fixture-model-span'
    assert tool['arguments']['course_ids'] == [row['id'] for row in courses]
    assert source == before and 'PRIVATE_' not in json.dumps(projection)


@pytest.mark.parametrize('name,value', [
    ('get_course_details', course('SF-007')),
    ('search_courses', {'matches': [{'course': course('SF-101')}], 'excluded': []}),
    ('search_courses', {'matches': [], 'excluded': [], 'error': 'Invalid argument', 'error_kind': 'invalid_input'}),
])
def test_single_text_search_details_and_domain_error_keep_their_actual_shape(name, value):
    tool = publishable_intake(intake(name, [text(value)]))['tools'][0]
    assert tool['result'] == value
    assert tool['result_state'] == ('domain_error' if value.get('error') else 'returned')


def test_native_comparison_single_text_array_is_not_wrapped_in_another_array():
    courses = [course('SF-101'), course('SF-102')]
    result = publishable_intake(intake('compare_courses', [text(courses)]))['tools'][0]
    assert result['result'] == courses and result['result_state'] == 'returned'


@pytest.mark.parametrize('blocks', [
    [], [text(course('SF-101'))],
    [text(course('SF-101')), {'type': 'text', 'text': 'invalid JSON'}],
    [text(course('SF-101')), {'type': 'image', 'data': 'PRIVATE_BINARY'}],
    [text([course('SF-101')])],
    [text(course(f'SF-{i:03}')) for i in range(4)],
    {'type': 'text', 'text': '{}'}, [text(None)],
])
def test_malformed_comparison_does_not_publish_a_partial_first_course_as_a_valid_result(blocks):
    tool = publishable_intake(intake('compare_courses', blocks))['tools'][0]
    assert tool['result'] is None and tool['result_state'] == 'unavailable'
    assert tool['native_status'] == 'success'  # Transport status is preserved independently.


def test_real_intake_comparison_shape_reaches_unchanged_source_only_validation(tmp_path):
    courses = [course('SF-007', provider='SMU Academy', price_min_sgd=20928, price_max_sgd=20928),
               course('SF-006'), course('SF-003')]
    catalogue = tmp_path / 'catalogue.json'
    catalogue.write_text(json.dumps({'courses': courses}))
    boundary = RetailResponseBoundary(tmp_path, catalogue)
    tools = publishable_intake(intake('compare_courses', [text(row) for row in courses]))['tools']
    candidate = boundary.apply('Compare the SMU programme and analysis options.',
        Preferences(goal='retail data', budget_sgd=3000, days=[5, 6]),
        {'content': 'Native comparison proposal.', 'tools': tools, 'thread_id': 'fixture-session'})
    assert candidate['response_policy']['source_ids'] == ['SF-006', 'SF-003']
    assert candidate['response_policy']['excluded_source_ids'] == ['SF-007']
    assert candidate['response_policy']['native_tool_evidence'][0]['native_id'] == 'fixture-tool-span'
    assert candidate['response_policy']['status'] == 'validated'
    assert boundary.last_delivery_record is None


@pytest.mark.parametrize('change,reason', [
    ('duplicate', 'duplicate course identities'), ('mismatch', 'frozen catalogue'),
    ('failed_span', 'successful attributable native evidence'), ('missing_identity', 'successful attributable native evidence'),
])
def test_projection_does_not_weaken_duplicate_fact_or_native_identity_checks(tmp_path, change, reason):
    courses = [course('SF-101'), course('SF-102')]
    catalogue = tmp_path / 'catalogue.json'
    catalogue.write_text(json.dumps({'courses': courses}))
    returned = deepcopy(courses)
    if change == 'duplicate':
        returned[1] = deepcopy(returned[0])
    if change == 'mismatch':
        returned[1]['price_max_sgd'] = 1
    tools = publishable_intake(intake('compare_courses', [text(row) for row in returned]))['tools']
    if change == 'failed_span':
        tools[0]['native_status'] = 'error'
    if change == 'missing_identity':
        tools[0]['source_span_id'] = None
    boundary = RetailResponseBoundary(tmp_path, catalogue)
    with pytest.raises(ValueError, match=reason):
        boundary.apply('Compare retail courses.', Preferences(goal='retail', budget_sgd=3000, days=[5, 6]),
                       {'content': 'Native proposal.', 'tools': tools})
