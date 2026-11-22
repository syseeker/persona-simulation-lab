"""Source-only delivery uses native returned facts, with no model calls."""
from copy import deepcopy
import json

import pytest

from learning_lab.catalogue import Course, Preferences
from learning_lab.retail_responses import RetailResponseBoundary


@pytest.fixture
def setup_boundary(tmp_path):
    def course(identity, **changes):
        return Course.model_validate({'id': identity, 'title': f'Retail data {identity}',
            'provider': 'Example Academy', 'kind': 'skillsfuture', 'summary': 'Practise retail data analysis.',
            'tags': ['retail', 'data'], 'source_url': f'https://example.edu/{identity}',
            'captured_on': '2026-11-22', 'duration_hours': 7,
            'price_min_sgd': 100, 'price_max_sgd': 100, 'extra_cost_sgd': 0,
            'weekdays': [5], **changes}).model_dump(mode='json')

    rows = [course('SF-007', title='SMU Retail data programme', provider='SMU Academy',
                   price_min_sgd=20928, price_max_sgd=20928, duration_months=3, duration_hours=330),
            course('SF-101'), course('SF-102', weekdays=[0], price_min_sgd=500, price_max_sgd=500),
            course('SF-103', weekdays=None, price_min_sgd=None, price_max_sgd=None, duration_hours=None)]
    catalogue = tmp_path / 'catalogue.json'
    catalogue.write_text(json.dumps({'courses': rows}))
    boundary = RetailResponseBoundary(tmp_path, catalogue)
    return boundary, rows, tmp_path, catalogue


def native(rows, *, shape='search_courses', origin='relay'):
    payload = {'matches': [{'course': row} for row in rows]} if shape == 'search_courses' else rows[0] if shape == 'get_course_details' else rows
    status = {'status': 'completed', 'scope_uuid': 'fixture-scope', 'evidence_origin': 'native_relay'}
    if origin == 'helix':
        status = {'native_status': 'success', 'result_state': 'returned',
                  'source_span_id': 'fixture-span', 'evidence_origin': 'native_helix_intake'}
    return {'name': shape, 'result': payload, **status}


def proposal(tools, content='Native proposal retained separately.'):
    return {'content': content, 'tools': tools, 'thread_id': 'fixture-thread',
            'fabric': {'status': 'succeeded', 'invocation_id': 'fixture-invocation'}}


@pytest.mark.parametrize('shape', ['search_courses', 'get_course_details', 'compare_courses'])
@pytest.mark.parametrize('origin', ['relay', 'helix'])
def test_programme_summary_uses_validated_native_sources(setup_boundary, shape, origin):
    boundary, rows, folder, _ = setup_boundary
    selected = rows[:2] if shape == 'compare_courses' else rows[:1]
    result = proposal([native(selected, shape=shape, origin=origin)])
    original = deepcopy(result)
    delivered = boundary.apply('Tell me about the SMU programme.', Preferences(goal='retail data'), result)
    assert result == original and delivered['content'] != result['content']
    assert all(fragment in delivered['content'] for fragment in ['S$20,928', '3 months', '330 hours', rows[0]['source_url']])
    assert delivered['response_origin'] == 'application_source_summary'
    assert delivered['response_policy']['model_proposal_rule_status'] == 'passed_selected_rules'
    assert delivered['response_policy']['source_ids'] == ['SF-007']
    assert delivered['response_policy']['status'] == 'validated'
    assert boundary.last_delivery_record is None
    assert boundary.pending_delivery is not None
    delivered = boundary.confirm_delivery(delivered)
    assert delivered['response_policy']['status'] == 'delivered'
    assert boundary.pending_delivery is None
    assert boundary.last_delivery_record == {'content': delivered['content'],
        'response_origin': 'application_source_summary', 'public_turn': 1}
    config = json.loads((folder / 'retail-response-config.json').read_text())
    assert config['inference_calls'] == 0 and config['original_prose_semantically_certified'] is False


def test_clarification_uses_previous_returned_facts_without_another_tool_call(setup_boundary):
    boundary, rows, folder, _ = setup_boundary
    first = boundary.apply('SMU programme?', Preferences(goal='retail data'), proposal([native(rows[:1])]))
    boundary.confirm_delivery(first)
    result = boundary.apply('My salary is S$2,500–3,499.', Preferences(goal='retail data'), proposal([]))
    assert result['response_origin'] == 'application_constraint_clarification'
    assert 'What is your total training budget' in result['content']
    assert 'On which days of the week' in result['content']
    assert 'affordability or funding eligibility' in result['content']
    assert 'SF-007' in result['content'] and result['response_policy']['public_turn'] == 2
    assert result['response_policy']['source_provenance']['SF-007'] == {
        'public_turn': 1, 'native_ids': ['fixture-scope']}
    assert boundary.last_delivery_record['public_turn'] == 1
    boundary.confirm_delivery(result)
    assert boundary.last_delivery_record['public_turn'] == 2
    records = [json.loads(line) for line in (folder / 'retail-model-proposals.jsonl').read_text().splitlines()]
    assert records[1]['original_content'] == 'Native proposal retained separately.'
    assert records[1]['native_identity']['fabric']['invocation_id'] == 'fixture-invocation'


@pytest.mark.parametrize('known, missing, absent', [
    ({'budget_sgd': 300}, 'On which days', 'What is your total training budget'),
    ({'days': [0]}, 'What is your total training budget', 'On which days'),
])
def test_clarification_asks_only_missing_constraints(setup_boundary, known, missing, absent):
    boundary, rows, _, _ = setup_boundary
    delivered = boundary.apply('My salary is context.', Preferences(goal='retail', **known), proposal([native(rows[:1])]))
    assert missing in delivered['content'] and absent not in delivered['content']


@pytest.mark.parametrize('budget, days, included, excluded', [
    (200, [5], ['SF-101', 'SF-103'], ['SF-007', 'SF-102']),
    (1000, [0], ['SF-102', 'SF-103'], ['SF-007', 'SF-101']),
    (50, [5, 6], ['SF-103'], ['SF-007', 'SF-101', 'SF-102']),
])
def test_budget_and_schedule_variations_filter_known_conflicts(setup_boundary, budget, days, included, excluded):
    boundary, rows, _, _ = setup_boundary
    result = boundary.apply('Compare courses for my spending limit and study days.',
        Preferences(goal='retail data', budget_sgd=budget, days=days), proposal([native(rows)]))
    assert result['response_policy']['source_ids'] == included
    assert result['response_policy']['excluded_source_ids'] == excluded
    assert 'fit remains unconfirmed' in result['content']
    assert 'duration unconfirmed' in result['content'] and 'shorter' not in result['content']
    assert result['response_policy']['delivered_word_count'] <= 180


@pytest.mark.parametrize('mutation', [
    {'title': 'Altered course'}, {'price_max_sgd': 1}, {'weekdays': [6]},
    {'source_url': 'https://example.edu/invented'}, {'unexpected_field': True},
])
def test_mismatched_or_open_ended_tool_facts_fail_closed(setup_boundary, mutation):
    boundary, rows, folder, _ = setup_boundary
    changed = {**rows[0], **mutation}
    with pytest.raises(ValueError):
        boundary.apply('SMU programme?', Preferences(goal='retail data'), proposal([native([changed])]))
    decision = json.loads((folder / 'retail-response-decisions.jsonl').read_text())
    assert decision['status'] == 'rejected' and boundary.last_delivery_record is None


@pytest.mark.parametrize('tools', [[], [{'name': 'search_courses', 'status': 'completed', 'result': {'matches': []}}]])
def test_absent_or_intent_only_evidence_cannot_produce_a_plausible_reply(setup_boundary, tools):
    boundary, _, folder, _ = setup_boundary
    with pytest.raises(ValueError):
        boundary.apply('SMU programme?', Preferences(goal='retail data'), proposal(tools))
    assert json.loads((folder / 'retail-response-decisions.jsonl').read_text())['status'] == 'rejected'


def test_real_empty_search_is_an_honest_no_match(setup_boundary):
    boundary, _, _, _ = setup_boundary
    delivered = boundary.apply('Budget S$50, weekends.', Preferences(goal='retail', budget_sgd=50, days=[5, 6]),
                               proposal([native([])]))
    assert delivered['response_policy']['source_ids'] == []
    assert 'No returned option' in delivered['content']


def test_unreturned_programme_is_not_loaded_as_a_fallback(setup_boundary):
    boundary, rows, _, _ = setup_boundary
    with pytest.raises(ValueError, match='not uniquely returned'):
        boundary.apply('SMU programme?', Preferences(goal='retail'), proposal([native(rows[1:2])]))


def test_native_noncompliance_is_not_relabelled_as_improved_model_output(setup_boundary):
    boundary, rows, folder, _ = setup_boundary
    text = ' '.join(['word'] * 181) + ' https://example.edu/invented SF-999'
    result = proposal([native(rows[:1])], text)
    delivered = boundary.apply('SMU programme?', Preferences(goal='retail'), result)
    assert set(delivered['response_policy']['model_proposal_rule_failures']) == {
        'word_limit', 'unsupported_source_url', 'unsupported_course_id'}
    assert delivered['response_policy']['model_proposal_rule_status'] == 'failed'
    assert 'financial prose not semantically certified' in delivered['response_policy']['model_proposal_rule_coverage']
    assert delivered['response_policy']['model_proposal_semantically_certified'] is False
    assert result['content'] == text
    assert json.loads((folder / 'retail-model-proposals.jsonl').read_text())['original_content'] == text


def test_oversized_source_title_fails_without_arbitrary_truncation(setup_boundary):
    boundary, rows, folder, catalogue = setup_boundary
    rows[0]['title'] = ' '.join(['Long'] * 181)
    catalogue.write_text(json.dumps({'courses': rows}))
    boundary = RetailResponseBoundary(folder, catalogue)
    with pytest.raises(ValueError, match='180-word limit'):
        boundary.apply('SMU programme?', Preferences(goal='retail'), proposal([native(rows[:1])]))
    assert boundary.last_delivery_record is None
    decision = json.loads((folder / 'retail-response-decisions.jsonl').read_text())
    assert decision['status'] == 'rejected' and decision['delivered_word_count'] > 180
    assert decision['source_ids'] == ['SF-007']


def test_published_cents_are_not_rounded_into_different_facts(setup_boundary):
    _, rows, folder, catalogue = setup_boundary
    rows[0].update(price_min_sgd=100.51, price_max_sgd=100.51)
    catalogue.write_text(json.dumps({'courses': rows}))
    boundary = RetailResponseBoundary(folder, catalogue)
    result = boundary.apply('SMU programme?', Preferences(goal='retail'), proposal([native(rows[:1])]))
    assert 'S$100.51' in result['content']


def test_repaired_domain_error_remains_visible_without_becoming_a_fact(setup_boundary):
    boundary, rows, _, _ = setup_boundary
    error = native([])
    error['result'] = {'error': 'Invalid kind', 'error_kind': 'invalid_input', 'matches': []}
    tools = [error, native(rows[:1])]
    delivered = boundary.apply('SMU programme?', Preferences(goal='retail'), proposal(tools))
    assert delivered['tools'] == tools
    evidence = delivered['response_policy']['native_tool_evidence']
    assert [row['status'] for row in evidence] == ['domain_error', 'returned']
    assert evidence[0]['source_ids'] == [] and evidence[0]['error_kind'] == 'invalid_input'


def test_unrepaired_domain_error_is_not_a_legitimate_empty_search(setup_boundary):
    boundary, _, folder, _ = setup_boundary
    error = native([])
    error['result'] = {'error': 'Invalid kind', 'error_kind': 'invalid_input', 'matches': []}
    with pytest.raises(ValueError, match='only domain errors'):
        boundary.apply('Budget S$500, weekends.', Preferences(goal='retail', budget_sgd=500, days=[5, 6]),
                       proposal([error]))
    decision = json.loads((folder / 'retail-response-decisions.jsonl').read_text())
    assert decision['native_tool_evidence'][0]['status'] == 'domain_error'


@pytest.mark.parametrize('changes', [
    {'content': 'Changed output'}, {'response_origin': 'model_generated'},
    {'response_policy': {'public_turn': 999}}, {'response_policy': None},
])
def test_confirmation_rejects_a_different_candidate(setup_boundary, changes):
    boundary, rows, _, _ = setup_boundary
    candidate = boundary.apply('SMU programme?', Preferences(goal='retail'), proposal([native(rows[:1])]))
    with pytest.raises(ValueError, match='does not match'):
        boundary.confirm_delivery({**candidate, **changes})
    assert boundary.last_delivery_record is None and boundary.pending_delivery is not None
    boundary.reject_delivery('Caller rejected the mismatched candidate.')
    assert boundary.pending_delivery is None


def test_blocked_candidate_never_advances_public_delivery_state(setup_boundary):
    boundary, rows, folder, _ = setup_boundary
    candidate = boundary.apply('SMU programme?', Preferences(goal='retail'), proposal([native(rows[:1])]))
    boundary.confirm_delivery(candidate)
    last = deepcopy(boundary.last_delivery_record)
    second = boundary.apply('My salary is context.', Preferences(goal='retail'), proposal([]))
    assert second['response_policy']['status'] == 'validated'
    boundary.reject_delivery('Native output Guardrails blocked delivery.')
    assert boundary.last_delivery_record == last and boundary.pending_delivery is None
    records = [json.loads(line) for line in (folder / 'retail-response-decisions.jsonl').read_text().splitlines()]
    assert [record['status'] for record in records] == ['validated', 'delivered', 'validated', 'rejected']
    assert records[-1]['reason'] == 'Native output Guardrails blocked delivery.'


def test_unconfirmed_candidate_must_be_resolved_before_another_turn(setup_boundary):
    boundary, rows, _, _ = setup_boundary
    first = boundary.apply('SMU programme?', Preferences(goal='retail'), proposal([native(rows[:1])]))
    with pytest.raises(ValueError, match='still unconfirmed'):
        boundary.apply('My salary is context.', Preferences(goal='retail'), proposal([]))
    assert boundary.turn == 1
    boundary.confirm_delivery(first)
    with pytest.raises(ValueError, match='no validated'):
        boundary.confirm_delivery(first)


@pytest.mark.parametrize('alteration', [
    {'content': ''}, {'content': None}, {'outcome': {'status': 'invalid'}},
    {'fabric': {'status': 'failed'}}, {'finish_reason': 'length'},
    {'outcome': None}, {'fabric': None},
])
def test_invalid_upstream_proposals_still_stop(setup_boundary, alteration):
    boundary, rows, _, _ = setup_boundary
    with pytest.raises(ValueError):
        boundary.apply('SMU programme?', Preferences(goal='retail'),
                       {**proposal([native(rows[:1])]), **alteration})
