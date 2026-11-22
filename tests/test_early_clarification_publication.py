"""An application-only public turn must never become fabricated Fabric evidence."""
from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace

import pytest

from scripts import export_capture_evidence as captures
from scripts import export_guide_context as context
from scripts import export_guide_recording as recording


def digest(content):
    return hashlib.sha256(content.encode()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(row) + '\n' for row in value)
                    if path.suffix == '.jsonl' else json.dumps(value))


@pytest.fixture
def early_run(tmp_path, monkeypatch):
    run_id = 'early-clarification-fixture'
    folder = tmp_path / 'runs' / run_id
    native = folder / 'episode' / 'native'
    target = tmp_path / 'context'
    pack = tmp_path / 'pack'
    write(pack / 'manifest.json', {'fixture': True})
    write(folder / 'run.json', {'run_id': run_id, 'scenario_id': 'dreamjob',
                               'episode_id': 'episode', 'cleanup_confirmed': True})
    write(folder / 'usersim-result.json', {'probe_type': 'learning_advisor',
        'usersim_config': {'locale': 'en_SG', 'max_turns': 3},
        'simulation_outcome': {'status': 'ok', 'n_turns': 3, 'n_tool_calls': 3}})
    write(native / 'fabric-config.json', {'schema_version': 'fixture', 'harness': {'adapter_id': 'deepagents'},
        'runtime': {}, 'tools': {}, 'models': {}, 'instructions': {'content': 'PRIVATE_INSTRUCTIONS'}})
    write(native / 'fabric-lifecycle.jsonl', [])
    conversation, outcomes = [], []
    for turn in (1, 2, 3):
        content = f'Public source summary {turn}.' if turn != 2 else 'What is your total budget and study availability?'
        origin = 'application_source_summary' if turn != 2 else 'application_constraint_clarification'
        policy = {'status': 'delivered', 'public_turn': turn, 'response_origin': origin,
                  'model_proposal_sha256': digest(f'PRIVATE_NATIVE_PROPOSAL_{turn}'),
                  'delivered_content_sha256': digest(content)}
        if turn == 2:
            policy.update(schema_version=1, owner='application', application_response_id='application-fixture',
                execution_kind='application_clarification', agent_invoked=False, inference_calls=0,
                missing_constraints=['budget_sgd', 'days'], public_preferences={'goal': 'retail data',
                    'budget_sgd': None, 'days': None},
                model_proposal_sha256=None, original_word_count=None, model_proposal_rule_status='not_invoked',
                delivered_word_count=len(content.split()), source_ids=['SF-007'], source_hashes={'SF-007': 'a' * 64},
                source_provenance={'SF-007': {'public_turn': 1, 'native_ids': ['scope-1']}}, native_tool_evidence=[])
        else:
            outcomes.append({'turn': turn, 'public_turn': turn, 'invocation_sequence': len(outcomes) + 1,
                'thread_id': 'native-thread', 'request_id': f'request-{turn}',
                'runtime_status': 'succeeded', 'runtime_id': 'native-runtime', 'invocation_id': f'invocation-{turn}',
                'outcome': {'status': 'valid'}, 'tools': [{'scope_uuid': f'scope-{turn}'}],
                'raw_output': {'response': f'PRIVATE_NATIVE_PROPOSAL_{turn}', 'harness': 'deepagents'}})
        conversation.extend([{'turn': turn, 'role': 'user', 'content': f'Public learner turn {turn}.'},
            {'turn': turn, 'role': 'assistant', 'content': content,
             'response_origin': origin, 'response_policy': policy}])
        if turn == 2:
            conversation[-1].update(public_turn=turn, application_response_id='application-fixture', tools=[])
    receipt = deepcopy(conversation[3]['response_policy'])
    decisions = [{**receipt, 'status': 'validated'}, receipt]
    monkeypatch.setattr(context, 'load_environment', lambda: None)
    monkeypatch.setattr(context.recordings, 'load', lambda _run_id: {'fixture': True})
    monkeypatch.setattr(context.recordings, 'pack_folder', lambda _run_id: pack)
    monkeypatch.setattr(context.recordings, 'read', lambda _run_id, name: json.dumps(
        conversation if name == 'public-conversation.json' else {}))

    def export():
        write(native / 'reply-outcomes.jsonl', outcomes)
        write(native / 'retail-response-decisions.jsonl', decisions)
        context.export('dreamjob', run_root=folder.parent, destination=target, run_id=run_id)
        return {path.name: json.loads(path.read_text()) for path in target.glob('*.json')}

    return conversation, outcomes, decisions, target, export


def test_companion_keeps_native_public_turns_one_and_three_and_separate_confirmed_clarification(early_run):
    conversation, _outcomes, _decisions, target, export = early_run
    files = export()
    native = files['fabric-invocations.json']
    assert [(row['turn'], row['public_turn'], row['invocation_sequence']) for row in native] == [(1, 1, 1), (3, 3, 2)]
    assert [row['invocation_id'] for row in native] == ['invocation-1', 'invocation-3']
    assert [row['request_id'] for row in native] == ['request-1', 'request-3']
    assert [row['output']['native_response_sha256'] for row in native] == [
        digest('PRIVATE_NATIVE_PROPOSAL_1'), digest('PRIVATE_NATIVE_PROPOSAL_3')]
    assert [row['output']['delivered_content_sha256'] for row in native] == [
        digest(conversation[1]['content']), digest(conversation[5]['content'])]
    application = files['application-turns.json']
    assert len(application) == 1 and application[0]['public_turn'] == application[0]['turn'] == 2
    assert application[0]['content'] == conversation[3]['content']
    assert application[0]['status'] == 'delivered' and application[0]['agent_invoked'] is False
    assert application[0]['inference_calls'] == 0
    assert application[0]['model_proposal_sha256'] is None and application[0]['original_word_count'] is None
    assert application[0]['application_response_id'] == 'application-fixture'
    assert application[0]['source_provenance'] == conversation[3]['response_policy']['source_provenance']
    assert not {'runtime_id', 'invocation_id', 'request_id'} & application[0].keys()
    assert 'PRIVATE_' not in '\n'.join(path.read_text() for path in target.iterdir())
    manifest = files['manifest.json']
    assert any(name.endswith('retail-response-decisions.jsonl') for name in manifest['native_sources'])
    for name, expected in manifest['files'].items():
        assert hashlib.sha256((target / name).read_bytes()).hexdigest() == expected


@pytest.mark.parametrize('change', [
    {'status': 'validated'}, {'public_turn': 3}, {'application_response_id': 'another-response'},
    {'delivered_content_sha256': '0' * 64}, {'response_origin': 'native_model_reply'},
    {'agent_invoked': True}, {'inference_calls': 1}, {'model_proposal_sha256': digest('invented proposal')},
    {'original_word_count': 0}, {'source_provenance': {}}, {'public_preferences': {'budget_sgd': 3000}},
])
def test_companion_refuses_unconfirmed_or_mismatched_application_receipt(early_run, change):
    _conversation, _outcomes, decisions, target, export = early_run
    decisions[1].update(change)
    with pytest.raises(ValueError, match='clarification receipt'):
        export()
    assert not target.exists()


def test_companion_refuses_missing_application_receipt(early_run):
    _conversation, _outcomes, decisions, target, export = early_run
    decisions.clear()
    with pytest.raises(ValueError, match='clarification receipt'):
        export()
    assert not target.exists()


@pytest.mark.parametrize('change', [
    {'application_response_id': 'another-response'}, {'application_response_id': None},
    {'fabric': {'status': 'succeeded', 'invocation_id': 'fabricated'}}, {'fabric': {}},
    {'tools': [{'name': 'search_courses', 'scope_uuid': 'fabricated'}]}, {'tools': None},
])
def test_companion_rejects_public_clarification_identity_or_native_activity_conflicts(early_run, change):
    conversation, _outcomes, _decisions, target, export = early_run
    conversation[3].update(change)
    with pytest.raises(ValueError, match='clarification receipt'):
        export()
    assert not target.exists()


@pytest.mark.parametrize('field', ['application_response_id', 'public_turn'])
def test_companion_requires_explicit_new_application_reply_identity(early_run, field):
    conversation, _outcomes, _decisions, target, export = early_run
    conversation[3].pop(field)
    with pytest.raises(ValueError, match='clarification receipt'):
        export()
    assert not target.exists()


def test_companion_refuses_positional_mapping_across_an_application_only_turn(early_run):
    _conversation, outcomes, _decisions, target, export = early_run
    for row in outcomes:
        for key in ('turn', 'public_turn', 'invocation_sequence'):
            row.pop(key)
    with pytest.raises(ValueError, match='explicit public turn'):
        export()
    assert not target.exists()


@pytest.mark.parametrize('change', [{'public_turn': 2, 'turn': 2}, {'public_turn': 1}, {'invocation_sequence': 3}])
def test_companion_refuses_misattributed_native_invocation(early_run, change):
    _conversation, outcomes, _decisions, target, export = early_run
    outcomes[1].update(change)
    with pytest.raises(ValueError):
        export()
    assert not target.exists()


def acknowledged_third_request(conversation):
    previous = conversation[3]
    acknowledgement = {'public_turn': 2, 'content': previous['content'], 'response_origin': previous['response_origin']}
    return {'turn': 3, 'public_turn': 3, 'invocation_sequence': 2,
        'thread_id': 'native-thread', 'request_id': 'request-3', 'request': {
            'request_id': 'request-3', 'input': conversation[4]['content']
            + '\nAPPLICATION_DELIVERY_RECORD=' + json.dumps(acknowledgement)
            + '\nLAB_PREFERENCES=' + json.dumps({'goal': 'retail data', 'budget_sgd': 3000, 'days': [5, 6]})}}


def test_request_capture_uses_previous_public_clarification_not_previous_native_invocation(early_run):
    conversation, _outcomes, _decisions, _target, _export = early_run
    request = acknowledged_third_request(conversation)
    projected = captures.project_requests([request], conversation)[0]
    assert projected['public_turn'] == projected['turn'] == 3 and projected['invocation_sequence'] == 2
    assert projected['request']['input'] == request['request']['input']
    assert conversation[3]['content'] in projected['request']['input']
    wrong = deepcopy(request)
    wrong['request']['input'] = wrong['request']['input'].replace(conversation[3]['content'], conversation[1]['content'])
    with pytest.raises(ValueError, match='acknowledgement'):
        captures.project_requests([wrong], conversation)


def test_capture_results_and_outcomes_preserve_only_actual_native_identities(early_run, tmp_path):
    conversation, outcomes, _decisions, _target, _export = early_run
    values = [{**{key: row[key] for key in ('turn', 'public_turn', 'invocation_sequence', 'request_id')},
        'boundary_status': 'returned', 'result': {'status': 'succeeded', 'invocation_id': row['invocation_id'],
            'output': row['raw_output']}} for row in outcomes]
    results = captures.project_results(values, conversation)
    assert [(row['turn'], row['public_turn'], row['invocation_sequence']) for row in results] == [(1, 1, 1), (3, 3, 2)]
    assert 'PRIVATE_NATIVE_' not in json.dumps(results)
    projected, kind = captures.projection(tmp_path / 'reply-outcomes.jsonl', outcomes, tmp_path, {})
    assert kind == 'application-projection'
    assert [(row['turn'], row['public_turn'], row['invocation_sequence']) for row in projected] == [(1, 1, 1), (3, 3, 2)]
    assert [row['request_id'] for row in projected] == ['request-1', 'request-3']
    assert 'PRIVATE_NATIVE_' not in json.dumps(projected)


def test_capture_does_not_publish_a_proposal_matching_a_different_public_turn(early_run):
    conversation, _outcomes, _decisions, _target, _export = early_run
    value = {'turn': 3, 'public_turn': 3, 'invocation_sequence': 2,
             'result': {'status': 'succeeded', 'output': {'response': conversation[3]['content']}}}
    projected = captures.project_results([value], conversation)
    assert 'response' not in projected[0]['result']['output']
    assert projected[0]['result']['output']['response_not_in_public_conversation'] is True


def test_application_receipt_projection_retains_no_call_and_source_provenance_without_private_data(early_run, tmp_path):
    _conversation, _outcomes, decisions, _target, _export = early_run
    receipt = deepcopy(decisions[1])
    receipt['public_preferences']['private_context'] = 'PRIVATE_PROFILE'
    receipt['source_provenance']['SF-007']['system_prompt'] = 'PRIVATE_PROMPT'
    receipt['original_content'] = 'PRIVATE_PROPOSAL'
    projected, _kind = captures.projection(tmp_path / 'retail-response-decisions.jsonl', [receipt], tmp_path, {})
    cleaned = captures.redactor(tmp_path)(projected)[0]
    for key in ('execution_kind', 'agent_invoked', 'inference_calls', 'application_response_id',
                'missing_constraints', 'source_provenance'):
        assert cleaned[key] == decisions[1][key]
    assert cleaned['public_preferences'] == decisions[1]['public_preferences']
    assert cleaned['original_word_count'] is None and cleaned['model_proposal_sha256'] is None
    assert 'PRIVATE_' not in json.dumps(cleaned)


def test_ordinary_recording_preserves_application_identity_for_strict_companion_without_private_payloads(
    early_run, monkeypatch
):
    conversation, _outcomes, _decisions, target, export = early_run
    run_id = 'early-clarification-fixture'
    folder = target.parent / 'runs' / run_id
    state = json.loads((folder / 'run.json').read_text())
    write(folder / 'run.json', {**state, 'status': 'completed'})
    write(folder / 'catalogue-snapshot.json', {'courses': []})
    write(folder / 'usersim-activations.jsonl', [])
    write(folder / 'episode/native/runtime-receipt.json', {'ready': True, 'image_manifest': {'files': {}}})
    trace = {'conversation': deepcopy(conversation), 'relay': {'scopes': []}, 'tools': [],
             'usage': {'calls': 2, 'records': []}, 'source_lock': {}, 'situation': {}, 'evaluation': None}
    trace['conversation'][1].update(fabric={'raw_output': 'PRIVATE_NATIVE_PROPOSAL'},
                                    tools=[{'result': 'PRIVATE_TOOL_PAYLOAD'}], private_context='PRIVATE_PROFILE')
    monkeypatch.setattr(recording, 'load_environment', lambda: None)
    monkeypatch.setattr(recording, 'JourneyService', lambda: SimpleNamespace(
        folder=lambda _run_id: folder, trace=lambda _run_id: trace))
    public = target.parent / 'ordinary-pack'
    recording.export(run_id, note='Offline synthetic publication regression.', destination=public)
    published = json.loads((public / 'public-conversation.json').read_text())
    assert published[3]['public_turn'] == 2
    assert published[3]['application_response_id'] == conversation[3]['application_response_id']
    assert published[3]['response_policy'] == conversation[3]['response_policy']
    assert all(not {'fabric', 'tools', 'private_context'} & row.keys() for row in published)
    assert 'PRIVATE_' not in '\n'.join(path.read_text() for path in public.iterdir())
    monkeypatch.setattr(context.recordings, 'read', lambda _run_id, name: (public / name).read_text())
    monkeypatch.setattr(context.recordings, 'pack_folder', lambda _run_id: public)
    files = export()
    assert [row['public_turn'] for row in files['fabric-invocations.json']] == [1, 3]
    assert files['application-turns.json'][0]['application_response_id'] == published[3]['application_response_id']
