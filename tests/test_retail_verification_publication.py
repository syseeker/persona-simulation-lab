"""Published comparisons preserve distinct verification and stop states."""
from copy import deepcopy
import json

from learning_lab.retail_experiments import comparison_summary, condition_verification
from scripts.export_guide_recording import clean
from scripts.retail_review import project


EFFICIENT = 'minimaxai/minimax-m3.1-flash'
CAPABLE = 'mistralai/mistral-large-4-1t-a52b'
CONFIGURATION = {'inventories': {'citizen-retail-proxy-v1': {
    'models': {'EFFICIENT': 'openai/' + EFFICIENT, 'CAPABLE': 'openai/' + CAPABLE}}}}


def condition(label, model=EFFICIENT, *, evaluation_passed=True):
    routed = label.endswith('switchyard')
    receipt = {'condition_id': label + '-fixture', 'label': label, 'harness': 'deepagents',
        'route': 'switchyard' if routed else 'fixed', 'status': 'completed', 'execution_status': 'completed',
        'evaluation_status': 'passed' if evaluation_passed else 'failed', 'cleanup_confirmed': True,
        'native_decisions': [{'source': 'switchyard'}] if routed else [],
        'evaluation': {'helix_used': True, 'total': 1, 'passed': int(evaluation_passed),
            'rows': [{'status': 'pass' if evaluation_passed else 'fail', 'helix_score': int(evaluation_passed)}],
            'delivery_review': [{'public_turn': 1, 'response_origin': 'application_source_summary',
                                'model_proposal_rule_failures': ['word_limit']}]},
        'usage': [{'call': 1, 'role': 'assistant', 'status': 'completed', 'selected_model': model}]}
    tool = {'name': 'search_courses', 'status': 'completed', 'scope_uuid': label + '-native-scope',
            'evidence_origin': 'native_relay', 'result': {'matches': []}}
    receipt.update(condition_verification(receipt, [tool]))
    return receipt


def publish(tmp_path, summary):
    source = tmp_path / 'routing-comparison.json'
    source.write_text(json.dumps(summary))
    before = source.read_bytes()
    emitted = {}
    project(tmp_path, lambda name, value, *_args, **_kwargs: emitted.update({name: clean(value)}))
    assert source.read_bytes() == before
    return emitted['routing-comparison.json']


def test_successful_publication_keeps_access_coverage_and_selected_models_separate(tmp_path):
    receipts = [condition('fixed-candidate'), condition('switchyard'), condition('capable-access', CAPABLE),
                condition('available-fixed', 'nvidia/diagnostic'),
                condition('available-switchyard', 'nvidia/diagnostic')]
    summary = comparison_summary(receipts, CONFIGURATION)
    result = publish(tmp_path, summary)
    assert result['status'] == 'completed' and result['verified']
    assert result['routing_policy_verified'] and result['requested_access_verified']
    assert result['diagnostic_verified'] and result['diagnostic_status'] == 'passed'
    assert result['condition_plan'] == summary['condition_plan']
    assert result['requested_model_access'] == summary['requested_model_access']
    assert result['requested_model_coverage']['all_candidates_observed']
    assert result['requested_model_coverage']['configured_models'] == sorted([EFFICIENT, CAPABLE])
    routed = next(row for row in result['conditions'] if row['label'] == 'switchyard')
    assert routed['actual_selected_models'] == [EFFICIENT]
    assert routed['native_course_searches'] == 1
    assert routed['native_course_scope_uuids'] == ['switchyard-native-scope']
    assert routed['verified'] and routed['execution_verified'] and routed['evaluation_verified']
    assert 'Application-delivered responses' in routed['evaluation_scope']
    assert routed['proposal_review'][0]['model_proposal_rule_failures'] == ['word_limit']
    assert result['provider_notice'] == summary['provider_notice']


def test_partial_publication_preserves_unrun_required_access_and_diagnostics(tmp_path):
    summary = comparison_summary([condition('fixed-candidate'), condition('switchyard')], CONFIGURATION)
    result = publish(tmp_path, summary)
    assert result['routing_policy_verified'] and not result['requested_access_verified']
    assert not result['verified'] and result['diagnostic_status'] == 'not_run'
    assert not result['diagnostic_verified']
    assert result['requested_model_coverage']['unexercised_models'] == [CAPABLE]
    assert next(row for row in result['condition_plan'] if row['label'] == 'capable-access')['status'] == 'not_run'


def test_rate_limit_failure_retains_stop_state_and_never_claims_unstarted_work(tmp_path):
    failed = condition('fixed-candidate')
    failed.update(status='failed', execution_status='failed', evaluation_status='not_run',
                  execution_verified=False, evaluation_verified=False, actual_selected_models=[], verified=False,
                  stopped_at='fixed-candidate', requires_user_review=True,
                  stop_reason='Hosted comparison stopped after HTTP 429.')
    failed['usage'] = [{'call': 1, 'role': 'assistant', 'status': 'failed', 'http_status': 429,
                        'usage': None, 'logical_request_id': 'fixture-request', 'attempt': 1,
                        'retry_of_call': None, 'retry_status': 'exhausted'}]
    result = publish(tmp_path, comparison_summary([failed], CONFIGURATION))
    assert result['status'] == 'failed' and not result['verified']
    assert result['requires_user_review'] and result['stopped_at'] == 'fixed-candidate'
    assert result['stop_reason'] == 'Hosted comparison stopped after HTTP 429.'
    assert all(row['status'] == 'not_run' and row['blocked_by'] == 'fixed-candidate'
               for row in result['condition_plan'][1:])
    row = result['conditions'][0]
    assert row['execution_status'] == 'failed' and row['evaluation_status'] == 'not_run'
    assert row['requires_user_review'] and row['stop_reason'] == result['stop_reason']
    assert row['actual_selected_models'] == [] and row['usage'][0]['http_status'] == 429
    assert row['usage'][0]['retry_status'] == 'exhausted' and row['usage'][0]['usage'] is None


def test_completed_execution_does_not_become_verified_when_evaluation_failed(tmp_path):
    failed = condition('fixed-candidate', evaluation_passed=False)
    failed.update(status='failed', requires_user_review=True, stopped_at='fixed-candidate',
                  stop_reason='Saved-response evaluation failed.')
    result = publish(tmp_path, comparison_summary([failed], CONFIGURATION))
    row = result['conditions'][0]
    assert row['execution_status'] == 'completed' and row['execution_verified']
    assert row['evaluation_status'] == 'failed' and not row['evaluation_verified']
    assert not row['verified'] and not result['verified']


def test_legacy_record_does_not_acquire_new_verification_claims(tmp_path):
    legacy = {'comparison': 'Historical fixed/routed comparison.',
              'conditions': [{'condition_id': 'historical-condition', 'label': 'fixed-candidate',
                              'status': 'completed', 'usage': [], 'conversation': []}]}
    result = publish(tmp_path, legacy)
    assert result == legacy
    assert 'verified' not in result and 'execution_verified' not in result['conditions'][0]


def test_new_public_fields_do_not_open_arbitrary_native_payloads(tmp_path, monkeypatch):
    monkeypatch.setenv('LAB_RETAIL_VERIFICATION_PUBLICATION_SECRET', 'PRIVATE_CONFIGURED_SECRET')
    receipt = condition('fixed-candidate')
    receipt.update(stop_reason='Provider stopped: PRIVATE_CONFIGURED_SECRET',
                   original_content='PRIVATE_MODEL_PROPOSAL', private_context='PRIVATE_SOURCE_PROFILE',
                   headers={'Authorization': 'PRIVATE_AUTH_HEADER'})
    summary = comparison_summary([receipt], CONFIGURATION)
    summary.update(raw_output='PRIVATE_RAW_OUTPUT', private_context='PRIVATE_ORIGINAL_PROFILE')
    before = deepcopy(summary)
    result = publish(tmp_path, summary)
    assert result['conditions'][0]['stop_reason'] == 'Provider stopped: [REDACTED]'
    assert 'PRIVATE_' not in json.dumps(result)
    assert summary == before
