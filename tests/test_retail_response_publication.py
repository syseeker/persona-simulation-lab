"""Offline publication retains application attribution without native proposal text."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import uuid

import pytest


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parents[1] / 'scripts' / filename)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


CAPTURES = module('retail_capture_publication', 'export_capture_evidence.py')
CONTEXT = module('retail_context_publication', 'export_guide_context.py')


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == '.jsonl':
        path.write_text(''.join(json.dumps(row) + '\n' for row in value))
    else:
        path.write_text(json.dumps(value))


def public_exchange():
    return [{'turn': 1, 'role': 'user', 'content': 'Retail data learning?'},
            {'turn': 1, 'role': 'assistant', 'content': 'A sourced course summary.',
             'response_origin': 'application_source_summary'},
            {'turn': 2, 'role': 'user', 'content': 'My monthly salary is S$2,500–3,499.'}]


def acknowledged_request():
    conversation = public_exchange()
    acknowledgement = {'content': conversation[1]['content'],
                       'response_origin': conversation[1]['response_origin'], 'public_turn': 1}
    request = {'turn': 2, 'thread_id': 'fixture-thread', 'request_id': 'fixture-request', 'request': {
        'request_id': 'fixture-request', 'relay_session_root': 'fixture-thread',
        'input': conversation[2]['content'] + '\nAPPLICATION_DELIVERY_RECORD=' + json.dumps(acknowledgement)
        + '\nLAB_PREFERENCES=' + json.dumps({'goal': 'retail'}),
        'context': {'private_context': 'PRIVATE_CONTEXT'}, 'overrides': {'system_prompt': 'PRIVATE_PROMPT'}}}
    return conversation, acknowledgement, request


def test_fabric_request_projection_retains_exact_confirmed_previous_delivery_only():
    conversation, _acknowledgement, request = acknowledged_request()
    projected = CAPTURES.project_requests([request], conversation)
    assert projected[0]['request']['input'] == request['request']['input']
    assert projected[0]['context_present'] and projected[0]['overrides_present']
    assert 'PRIVATE_CONTEXT' not in json.dumps(projected) and 'PRIVATE_PROMPT' not in json.dumps(projected)


@pytest.mark.parametrize('change', [
    {'content': 'PRIVATE_UNDELIVERED_MODEL_PROPOSAL'},
    {'response_origin': 'native_model'}, {'public_turn': 2},
    {'private_context': 'PRIVATE_PROFILE'},
])
def test_request_publication_rejects_tampered_or_private_delivery_acknowledgement(change):
    conversation, acknowledgement, request = acknowledged_request()
    acknowledgement.update(change)
    request['request']['input'] = conversation[2]['content'] + '\nAPPLICATION_DELIVERY_RECORD=' + json.dumps(
        acknowledgement) + '\nLAB_PREFERENCES=' + json.dumps({'goal': 'retail'})
    with pytest.raises(ValueError, match='acknowledgement'):
        CAPTURES.project_requests([request], conversation)


def test_raw_proposal_stays_private_and_public_decisions_retain_attribution_and_violations(tmp_path, monkeypatch):
    monkeypatch.setenv('LAB_RETAIL_PUBLICATION_TEST_SECRET', 'PRIVATE_SECRET_VALUE')
    private = {'original_content': 'PRIVATE_NATIVE_PROPOSAL', 'private_context': 'PRIVATE_PROFILE',
               'model_proposal_sha256': digest('PRIVATE_NATIVE_PROPOSAL')}
    value, kind = CAPTURES.projection(tmp_path / 'retail-model-proposals.jsonl', [private], tmp_path, {})
    assert value is None and kind is None
    decision = {**private, 'schema_version': 1, 'public_turn': 2, 'owner': 'application', 'status': 'delivered',
        'response_origin': 'application_constraint_clarification', 'model_proposal_rule_failures': ['unsupported_source_url'],
        'model_proposal_rule_status': 'failed', 'model_proposal_semantically_certified': False,
        'delivered_content_sha256': digest('What is your total training budget?'),
        'native_tool_evidence': [{'native_id': 'scope-fixture', 'status': 'returned', 'source_ids': ['SF-007']}],
        'reason': 'PRIVATE_REASONING', 'api_key': 'PRIVATE_SECRET_VALUE'}
    projected, _kind = CAPTURES.projection(tmp_path / 'retail-response-decisions.jsonl', [decision], tmp_path, {})
    cleaned = CAPTURES.redactor(tmp_path)(projected)
    assert cleaned[0]['response_origin'] == decision['response_origin']
    assert cleaned[0]['model_proposal_rule_failures'] == ['unsupported_source_url']
    assert cleaned[0]['model_proposal_rule_status'] == 'failed'
    assert cleaned[0]['model_proposal_semantically_certified'] is False
    assert cleaned[0]['model_proposal_sha256'] == digest('PRIVATE_NATIVE_PROPOSAL')
    assert 'PRIVATE_' not in json.dumps(cleaned)
    configuration = {'schema_version': 1, 'owner': 'application', 'maximum_words': 180,
        'inference_calls': 0, 'original_prose_semantically_certified': False,
        'api_key': 'PRIVATE_SECRET_VALUE', 'private_context': 'PRIVATE_PROFILE'}
    projected, kind = CAPTURES.projection(tmp_path / 'retail-response-config.json', configuration, tmp_path, {})
    cleaned = CAPTURES.redactor(tmp_path)(projected)
    assert kind == 'redacted-native-configuration' and cleaned['owner'] == 'application'
    assert cleaned['maximum_words'] == 180 and cleaned['inference_calls'] == 0
    assert 'PRIVATE_' not in json.dumps(cleaned)


@pytest.fixture
def context_fixture(tmp_path, monkeypatch):
    run_id, episode_id = str(uuid.uuid4()), str(uuid.uuid4())
    folder = tmp_path / 'runs' / run_id
    native = folder / episode_id / 'native'
    write(folder / 'run.json', {'run_id': run_id, 'scenario_id': 'dreamjob', 'episode_id': episode_id,
                              'cleanup_confirmed': True})
    write(folder / 'usersim-result.json', {'usersim_config': {}, 'simulation_outcome': {},
                                         'probe_type': 'learning-advisor'})
    write(native / 'fabric-config.json', {'schema_version': 'fixture', 'harness': {}, 'runtime': {},
                                        'tools': {}, 'models': {}, 'instructions': {}})
    write(native / 'fabric-lifecycle.jsonl', [])
    pack_folder = tmp_path / 'immutable-pack'
    write(pack_folder / 'manifest.json', {'fixture': True})
    conversation = [
        {'turn': 1, 'role': 'user', 'content': 'Retail learning?'},
        {'turn': 1, 'role': 'assistant', 'content': 'Application source summary.',
         'response_origin': 'application_source_summary', 'response_policy': {
             'status': 'delivered', 'public_turn': 1, 'model_proposal_sha256': digest('PRIVATE_NATIVE_PROPOSAL'),
             'delivered_content_sha256': digest('Application source summary.')}},
    ]
    outcomes = [{'runtime_status': 'succeeded', 'invocation_id': 'fixture-invocation',
                 'raw_output': {'response': 'PRIVATE_NATIVE_PROPOSAL', 'harness': 'deepagents'},
                 'outcome': {'status': 'valid'}, 'tools': []}]
    monkeypatch.setattr(CONTEXT.recordings, 'load', lambda _identity: {'fixture': True})
    monkeypatch.setattr(CONTEXT.recordings, 'read', lambda _identity, name: json.dumps(
        conversation if name == 'public-conversation.json' else {}))
    monkeypatch.setattr(CONTEXT.recordings, 'pack_folder', lambda _identity: pack_folder)

    def export():
        write(native / 'reply-outcomes.jsonl', outcomes)
        target = tmp_path / 'context'
        CONTEXT.export('dreamjob', run_root=folder.parent, destination=target, run_id=run_id)
        return json.loads((target / 'fabric-invocations.json').read_text())

    return conversation, outcomes, export


def test_companion_links_private_native_proposal_to_confirmed_public_delivery_by_hash_and_turn(context_fixture):
    conversation, _outcomes, export = context_fixture
    invocations = export()
    assert len(invocations) == 1
    output = invocations[0]['output']
    assert output['native_response_published'] is False and 'response' not in output
    assert output['native_response_sha256'] == digest('PRIVATE_NATIVE_PROPOSAL')
    assert output['response_origin'] == conversation[1]['response_origin']
    assert output['delivered_content_sha256'] == digest(conversation[1]['content'])
    assert 'PRIVATE_NATIVE_PROPOSAL' not in json.dumps(invocations)


@pytest.mark.parametrize('change', [
    {'status': 'validated'}, {'public_turn': 2}, {'model_proposal_sha256': '0' * 64},
    {'delivered_content_sha256': '0' * 64},
])
def test_companion_rejects_unconfirmed_or_misattributed_application_delivery(context_fixture, change):
    conversation, _outcomes, export = context_fixture
    conversation[1]['response_policy'].update(change)
    with pytest.raises(ValueError, match='confirmed application delivery'):
        export()


def test_companion_cannot_bypass_confirmation_when_proposal_matches_a_different_public_turn(context_fixture):
    conversation, outcomes, export = context_fixture
    conversation.extend([{'turn': 2, 'role': 'user', 'content': 'A public follow-up?'},
                         {'turn': 2, 'role': 'assistant', 'content': 'PRIVATE_NATIVE_PROPOSAL',
                          'response_origin': 'application_source_summary'}])
    conversation[1]['response_policy']['status'] = 'validated'
    outcomes.append(deepcopy(outcomes[0]))
    with pytest.raises(ValueError, match='confirmed application delivery'):
        export()


def managed_invocation():
    proposal = 'PRIVATE_MANAGED_MODEL_PROPOSAL'
    delivered = 'A source-only application response.'
    return {'public_input': 'My training budget is S$3,000; weekends only.',
        'session_id': 'fixture-managed-session', 'application_delivery_required': True,
        'response': {'id': 'fixture-managed-response', 'choices': [{'index': 0, 'finish_reason': 'stop',
            'message': {'role': 'assistant', 'content': proposal, 'reasoning_content': 'PRIVATE_REASONING'}}]},
        'application_delivery': {'content': delivered, 'response_origin': 'application_source_summary',
            'thread_id': 'fixture-managed-session', 'response_policy': {'status': 'delivered', 'public_turn': 1,
                'model_proposal_sha256': digest(proposal), 'delivered_content_sha256': digest(delivered),
                'model_proposal_rule_failures': ['unsupported_source_url'],
                'model_proposal_semantically_certified': False}}}


def project_managed(tmp_path, invocation):
    from scripts.retail_review import project
    write(tmp_path / 'platform-invocation.json', invocation)
    emitted = {}
    project(tmp_path, lambda name, value, *_args, **_kwargs: emitted.update({name: value}))
    return emitted['platform-invocation.json']


def test_managed_projection_publishes_application_delivery_and_hashes_native_proposal(tmp_path):
    invocation = managed_invocation()
    projected = project_managed(tmp_path, invocation)
    choice = projected['response']['choices'][0]
    assert choice['native_content_published'] is False and 'content' not in choice['message']
    assert choice['native_content_sha256'] == digest('PRIVATE_MANAGED_MODEL_PROPOSAL')
    assert projected['application_delivery'] == invocation['application_delivery']
    assert projected['native_model_content_published'] is False
    assert 'PRIVATE_' not in json.dumps(projected)


def test_managed_projection_without_confirmed_delivery_never_relabels_native_proposal_public(tmp_path):
    invocation = managed_invocation()
    invocation.pop('application_delivery')
    projected = project_managed(tmp_path, invocation)
    assert projected['application_delivery'] is None
    assert projected['native_model_content_published'] is False
    assert 'content' not in projected['response']['choices'][0]['message']
    assert 'PRIVATE_' not in json.dumps(projected)


@pytest.mark.parametrize('change', [
    {'status': 'validated'}, {'model_proposal_sha256': '0' * 64}, {'delivered_content_sha256': '0' * 64},
])
def test_managed_projection_rejects_unconfirmed_or_tampered_delivery(tmp_path, change):
    invocation = managed_invocation()
    invocation['application_delivery']['response_policy'].update(change)
    with pytest.raises(ValueError, match='confirmed proposal/content hashes'):
        project_managed(tmp_path, invocation)


def test_legacy_managed_projection_keeps_its_original_public_reply_contract(tmp_path):
    invocation = managed_invocation()
    invocation.pop('application_delivery')
    invocation.pop('application_delivery_required')
    invocation['response']['choices'][0]['message']['content'] = 'Historical public native answer.'
    projected = project_managed(tmp_path, invocation)
    assert projected['response']['choices'][0]['message']['content'] == 'Historical public native answer.'
    assert 'application_delivery' not in projected
    assert 'PRIVATE_REASONING' not in json.dumps(projected)
