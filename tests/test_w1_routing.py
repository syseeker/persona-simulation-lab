"""Routing verification distinguishes execution, criteria and candidate coverage."""
from contextlib import asynccontextmanager
from copy import deepcopy
import asyncio
import json
from unittest.mock import AsyncMock

import pytest
import yaml

from learning_lab.inference import Budget
from learning_lab.retail_experiments import (
    comparison_summary,
    condition_verification,
    evaluation_verified,
)
from learning_lab.settings import ROOT


def passing_receipt(route='fixed', label=None):
    return {'route': route, 'label': label or ('switchyard' if route == 'switchyard' else 'fixed-candidate'),
        'status': 'completed', 'execution_status': 'completed',
        'cleanup_confirmed': True, 'native_decisions': [{'source': 'switchyard'}] if route == 'switchyard' else [],
        'evaluation': {'helix_used': True, 'total': 1, 'passed': 1,
                       'rows': [{'status': 'pass', 'helix_score': 1}]},
        'usage': [{'role': 'assistant', 'status': 'completed',
                   'selected_model': 'openai/google/gemma-4-31b-it'}]}


def native_search(**changes):
    return {'name': 'search_courses', 'status': 'completed', 'evidence_origin': 'native_relay',
            'scope_uuid': 'native-search', 'result': {'matches': []}, **changes}


def configuration():
    return {'inventories': {'citizen-retail-proxy-v1': {'models': {
        'EFFICIENT': 'openai/google/gemma-4-31b-it', 'CAPABLE': 'openai/z-ai/glm-5.3-flash'}}}}


def test_completed_transport_does_not_verify_a_failed_criterion():
    receipt = passing_receipt()
    receipt['evaluation'].update(passed=0, rows=[{'status': 'fail', 'helix_score': 0}])
    result = condition_verification(receipt, [native_search()])
    assert result['execution_verified']
    assert not result['evaluation_verified'] and not result['verified']


@pytest.mark.parametrize('evaluation', [
    {}, {'helix_used': True, 'total': 0, 'passed': 0, 'rows': []},
    {'helix_used': True, 'total': 2, 'passed': 1, 'rows': [{'status': 'pass', 'helix_score': 1}]},
    {'helix_used': True, 'total': 1, 'passed': 1, 'rows': [{'status': 'error', 'helix_score': 1}]},
    {'helix_used': False, 'total': 1, 'passed': 1, 'rows': [{'status': 'pass', 'helix_score': 1}]},
])
def test_missing_incomplete_or_failed_native_scores_are_not_a_pass(evaluation):
    assert not evaluation_verified(evaluation)


@pytest.mark.parametrize('tools', [[], [native_search(evidence_origin='application_intent')],
    [native_search(status='running')], [native_search(result={'matches': [], 'error': 'Invalid kind'})]])
def test_passing_scores_still_need_a_successful_native_course_search(tools):
    assert not condition_verification(passing_receipt(), tools)['verified']


def test_honest_native_no_match_is_execution_evidence():
    result = condition_verification(passing_receipt(), [native_search()])
    assert result['verified'] and result['native_course_searches'] == 1
    assert result['native_course_scope_uuids'] == ['native-search']


def test_routed_completion_needs_decision_and_cleanup_and_observed_model():
    receipt = passing_receipt('switchyard')
    assert condition_verification(receipt, [native_search()])['verified']
    for update in [{'native_decisions': []}, {'cleanup_confirmed': False}, {'usage': []}]:
        assert not condition_verification({**receipt, **update}, [native_search()])['verified']


def test_successful_comparison_does_not_claim_an_unselected_candidate_was_exercised():
    receipts = []
    for route in ['fixed', 'switchyard']:
        receipt = passing_receipt(route)
        receipt.update(condition_verification(receipt, [native_search()]))
        receipts.append(receipt)
    summary = comparison_summary(receipts, configuration())
    assert summary['routing_policy_verified'] and not summary['diagnostic_verified']
    assert not summary['verified'] and not summary['requested_access_verified']
    coverage = summary['requested_model_coverage']
    assert coverage['observed_models'] == ['google/gemma-4-31b-it']
    assert coverage['unexercised_models'] == ['z-ai/glm-5.3-flash']
    assert not coverage['all_candidates_observed']
    assert not comparison_summary(receipts[:1], configuration())['verified']


def test_explicit_capable_access_is_required_and_does_not_relabel_routing():
    receipts = []
    for route, label in [('fixed', 'fixed-candidate'), ('switchyard', 'switchyard'),
                         ('fixed', 'capable-access')]:
        receipt = passing_receipt(route, label)
        if label == 'capable-access':
            receipt['usage'][0]['selected_model'] = 'z-ai/glm-5.3-flash'
        receipt.update(condition_verification(receipt, [native_search()]))
        receipts.append(receipt)
    # Labels define the roles, including when diagnostic/access conditions are
    # inserted or reordered. The routed condition itself still exercised Gemma.
    summary = comparison_summary(list(reversed(receipts)), configuration())
    assert summary['verified'] and summary['routing_policy_verified']
    assert summary['requested_access_verified']
    assert summary['requested_model_coverage']['all_candidates_observed']
    assert receipts[1]['actual_selected_models'] == ['openai/google/gemma-4-31b-it']
    receipts[2]['verified'] = False
    failed = comparison_summary(receipts, configuration())
    assert failed['routing_policy_verified'] and not failed['verified']
    assert not failed['requested_access_verified']


def test_a_wrong_returned_model_does_not_verify_requested_capable_access():
    receipts = []
    for route, label in [('fixed', 'fixed-candidate'), ('switchyard', 'switchyard'),
                         ('fixed', 'capable-access')]:
        receipt = passing_receipt(route, label)
        receipt.update(condition_verification(receipt, [native_search()]))
        receipts.append(receipt)
    result = comparison_summary(receipts, configuration())
    assert result['routing_policy_verified'] and not result['requested_access_verified']
    assert result['requested_model_access'][1]['verified'] is False


def test_requested_pool_has_model_specific_settings_in_both_selection_modes():
    source = yaml.safe_load((ROOT / 'integrations/proxy/retail-litellm.yaml').read_text())
    groups = {}
    for row in source['model_list']:
        groups.setdefault(row['model_name'], []).append(row['litellm_params'])
    fixed = groups['lab-advisor-candidate'][0]
    capable, efficient = groups['lab-advisor-routed']
    assert groups['lab-advisor-capable'][0] == capable
    # Same Gemma deployment policy for fixed and routed; GLM uses its own
    # supported effort instead of inheriting a shared "none" or "low".
    assert fixed == efficient
    assert efficient['extra_body'] == {'chat_template_kwargs': {'enable_thinking': False}}
    assert 'reasoning_effort' not in efficient
    assert capable['reasoning_effort'] == 'low'
    assert capable['extra_body'] == {'chat_template_kwargs': {'clear_thinking': True}}
    assert all(row['num_retries'] == 0 for row in [fixed, capable, efficient])
    assert source['router_settings']['fallbacks'] == []


@pytest.mark.parametrize('cancelled', [False, True])
async def test_failed_conditions_retain_usage_and_cannot_become_verified(tmp_path, monkeypatch, cancelled):
    from learning_lab import retail_experiments as experiments
    budget = Budget()
    (tmp_path / 'source-lock.json').write_text('{}')
    monkeypatch.setenv('LAB_PROXY_BASE_URL', 'http://127.0.0.1:4000/v1')
    monkeypatch.setenv('LAB_RETAIL_PROXY_URL', 'http://127.0.0.1:4001/v1')
    monkeypatch.setattr(experiments, 'routing_configuration', AsyncMock(return_value=configuration()))
    scorer = AsyncMock()
    monkeypatch.setattr(experiments, 'score_with_helix', scorer)
    monkeypatch.setattr(experiments, 'native_tool_records', lambda *_: [])

    class FailedGateway:
        def __init__(self, budget, **options):
            self.budget = budget
            self.options = options

        @asynccontextmanager
        async def serving(self):
            yield self

    class FailedSandbox:
        def __init__(self, identity, folder, gateway, **_):
            self.folder, self.gateway = folder, gateway

        async def __aenter__(self):
            self.folder.mkdir(parents=True)
            return self

        async def __aexit__(self, *_):
            (self.folder / 'cleanup.json').write_text(json.dumps({'native_absence_confirmed': True}))

        async def reply(self, *_):
            record = await self.gateway.budget.admit('assistant', 'fixture')
            record.update(status='failed', error_type='CancelledError' if cancelled else 'TimeoutError')
            if cancelled:
                raise asyncio.CancelledError()
            raise TimeoutError('fixture provider timeout')

    monkeypatch.setattr(experiments, 'Gateway', FailedGateway)
    monkeypatch.setattr(experiments, 'NativeSandbox', FailedSandbox)
    conversation = [{'role': 'user', 'content': text} for text in [
        'Retail data analysis?', 'My monthly salary is S$2,500–3,499.',
        'My total training budget is S$3,000, weekends only.']]
    with pytest.raises(asyncio.CancelledError if cancelled else RuntimeError,
                       match=None if cancelled else 'fixture provider timeout'):
        await experiments.compare_routing({'catalogue_sha256': 'fixture'}, tmp_path,
                                          budget, conversation, tmp_path / 'catalogue.json')
    result = json.loads((tmp_path / 'routing-comparison.json').read_text())
    assert budget.calls == 1 and not result['verified'] and not result['diagnostic_verified']
    assert result['stopped_at'] == 'fixed-candidate' and result['requires_user_review']
    assert result['diagnostic_status'] == 'not_run'
    assert len(result['conditions']) == 1
    assert all(row['status'] == 'not_run' and row['blocked_by'] == 'fixed-candidate'
               for row in result['condition_plan'][1:])
    assert len({row['input_sha256'] for row in result['conditions']}) == 1
    assert all(row['fresh_memory'] for row in result['conditions'])
    scorer.assert_not_called()
    for row in result['conditions']:
        assert row['status'] == row['execution_status'] == ('cancelled' if cancelled else 'failed')
        assert row['evaluation_status'] == 'not_run' and not row['evaluation_verified']
        assert row['cleanup_confirmed'] and row['actual_selected_models'] == []
        saved = json.loads((tmp_path / 'comparisons' / row['condition_id'] / 'usage.json').read_text())
        assert saved['calls'] == 1 and saved['records'][0].get('usage') is None


def test_failed_provider_identity_is_not_counted_as_observed_execution():
    receipt = deepcopy(passing_receipt())
    receipt['usage'][0]['status'] = 'failed'
    assert condition_verification(receipt, [native_search()])['actual_selected_models'] == []
