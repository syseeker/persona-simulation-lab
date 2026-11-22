"""Export narrow teaching projections for an existing immutable demo.

No original profile, resolved private row, simulator prompt or model reasoning
is published. This is an offline projection, never a new execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from learning_lab import recordings
from learning_lab.guide_lessons import CANONICAL_DEMOS, CONTEXT_ROOT
from learning_lab.settings import ROOT, load_environment
from scripts.export_capture_evidence import BOUNDARY_FIELDS, project_decisions, public_turn
from scripts.export_guide_recording import clean, pick


def application_only(reply):
    policy = reply.get('response_policy') or {}
    return policy.get('execution_kind') == 'application_clarification' or policy.get('agent_invoked') is False


def application_turns(replies, decisions):
    """Publish a clarification only after matching its confirmed delivery receipt."""
    result = []
    required = {'public_turn', 'application_response_id', 'execution_kind', 'agent_invoked', 'inference_calls',
        'response_origin', 'status', 'delivered_content_sha256', 'model_proposal_sha256', 'original_word_count',
        'missing_constraints', 'public_preferences', 'source_ids', 'source_hashes', 'source_provenance'}
    for turn, reply in replies.items():
        candidates = [row for row in decisions if row.get('public_turn') == turn and row.get('status') == 'delivered']
        policy = reply.get('response_policy') or {}
        if len(candidates) != 1:
            raise ValueError('Application clarification receipt is missing or ambiguous')
        receipt = candidates[0]
        if (required - receipt.keys() or receipt.get('execution_kind') != 'application_clarification'
                or receipt.get('agent_invoked') is not False or type(receipt.get('inference_calls')) is not int
                or receipt['inference_calls'] != 0 or receipt.get('model_proposal_sha256') is not None
                or receipt.get('original_word_count') is not None
                or not isinstance(receipt.get('application_response_id'), str) or not receipt['application_response_id']
                or reply.get('application_response_id') != receipt['application_response_id']
                or type(reply.get('public_turn')) is not int or reply['public_turn'] != turn
                or 'fabric' in reply or ('tools' in reply and reply['tools'] != [])
                or receipt.get('response_origin') != 'application_constraint_clarification'
                or reply.get('response_origin') != receipt['response_origin']
                or receipt['delivered_content_sha256'] != hashlib.sha256(reply['content'].encode()).hexdigest()
                or project_decisions([receipt])[0] != project_decisions([policy])[0]):
            raise ValueError('Application clarification receipt does not match the confirmed public response')
        result.append({'turn': turn, 'content': reply['content'], **project_decisions([receipt])[0]})
    return result


def export(scenario_id='photography', *, run_root: Path | None = None, destination: Path | None = None,
           run_id: str | None = None):
    load_environment()
    run_id = run_id or CANONICAL_DEMOS[scenario_id]
    if not run_id:
        raise ValueError('This scenario has no executed demo')
    pack = recordings.load(run_id)
    if pack is None:
        raise ValueError('The immutable recording must exist first')
    folder = (run_root or ROOT / 'runs/journeys') / run_id
    state = json.loads((folder / 'run.json').read_text())
    if state['run_id'] != run_id or state['scenario_id'] != scenario_id or not state.get('cleanup_confirmed'):
        raise ValueError('Native run identity or cleanup does not match the demo')
    target = destination or CONTEXT_ROOT / scenario_id / run_id
    if target.exists():
        raise ValueError('Teaching context is immutable; do not overwrite published evidence')
    native = folder / state['episode_id'] / 'native'
    sources = {}

    def read(path, *, lines=False):
        raw = path.read_bytes()
        sources[path.relative_to(folder).as_posix()] = hashlib.sha256(raw).hexdigest()
        return [json.loads(line) for line in raw.decode().splitlines() if line.strip()] if lines else json.loads(raw)

    usersim = read(folder / 'usersim-result.json')
    config = read(native / 'fabric-config.json')
    outcome = usersim['simulation_outcome']
    if isinstance(outcome, str):
        outcome = json.loads(outcome)
    sim_config = pick(usersim['usersim_config'], [
        'locale', 'max_turns', 'max_steps', 'max_query_attempts', 'max_assistant_attempts',
        'enforce_user_language', 'context_compression', 'persona_grounding_ratio', 'probe_options',
    ])
    sim_outcome = pick(outcome, [
        'status', 'failure_class', 'failure_attribution', 'n_turns', 'n_tool_calls',
        'n_user_query_attempts', 'n_user_followup_retries', 'n_assistant_inline_failures',
        'n_assistant_retries', 'n_api_response_rerolls', 'n_fourth_wall_triggers',
        'n_user_role_violations', 'n_user_language_violations', 'early_stop', 'per_model_calls',
    ])
    sim_outcome['warning_count'] = len(outcome.get('warnings', []))
    setup = {'probe': usersim['probe_type'], 'configuration': sim_config, 'outcome': sim_outcome,
             'behaviour_basis': 'Original NGC Extended behavioural fields interpreted by the native UserSim preamble.',
             'private_context_published': False,
             'counting_notice': 'A UserSim assistant activation calls the application, which may clarify without invoking an agent. Fabric invocations, model calls and course MCP calls are counted separately.',
             'evaluation_notice': 'Native in-loop judges ran. The optional post-loop UserSim eval/report commands were not invoked.'}
    framework = {
        'schema_version': config['schema_version'], 'harness': config['harness'], 'runtime': config['runtime'],
        'tools': config['tools'],
        'models': {name: pick(model, ['provider', 'model', 'max_tokens', 'temperature']) for name, model in config['models'].items()},
        'model_transport': 'In-sandbox loopback bridge to the host budget gateway; credentials remain on the host.',
        'relay': {'enabled': bool(config.get('relay')), 'observability': pick(config.get('relay', {}).get('observability', {}), ['version', 'enable_full_payloads']),
                  'export': 'Native ATOF JSONL file sink; no collector-backed streaming requested.'},
        'instructions_sha256': hashlib.sha256(json.dumps(config['instructions'], sort_keys=True).encode()).hexdigest(),
        'configuration_notice': 'Allowlisted values from the native saved configuration. Host addresses, credentials and prompt text are omitted.',
    }
    conversation = json.loads(recordings.read(run_id, 'public-conversation.json'))
    delivered_replies = [m for m in conversation if m['role'] == 'assistant']
    replies = {public_turn(reply): reply for reply in delivered_replies}
    if len(replies) != len(delivered_replies):
        raise ValueError('Public assistant turn identities must be unique')
    application_replies = {turn: reply for turn, reply in replies.items() if application_only(reply)}
    native_rows = read(native / 'reply-outcomes.jsonl', lines=True)
    legacy = not any('public_turn' in row or 'turn' in row for row in native_rows)
    # Old recordings used positional rows only when every public turn invoked
    # the agent. That fallback must never guess across an application-only turn.
    if native_rows and legacy and (application_replies or len(native_rows) != len(replies)
                                  or list(replies) != list(range(1, len(replies) + 1))):
        raise ValueError('Native outcomes require an explicit public turn when public and native counts differ')
    invocations = []
    seen_turns = set()
    for sequence, row in enumerate(native_rows, start=1):
        turn = sequence if legacy else public_turn(row)
        if (turn not in replies or turn in seen_turns or turn in application_replies
                or row.get('invocation_sequence', sequence) != sequence):
            raise ValueError('Native invocation identity conflicts with the public conversation')
        seen_turns.add(turn)
        raw = row.get('raw_output', {})
        if not isinstance(raw, dict) or not isinstance(raw.get('response'), str):
            raise ValueError('Publish only normalized replies matching the immutable public conversation')
        output = pick(raw, ['adapter', 'harness', 'mode', 'model', 'completed', 'event_count',
                            'message_count', 'runtime_id', 'thread_id', 'resumed', 'response', 'enabled_toolsets'])
        delivered = replies[turn]
        if delivered.get('response_origin', '').startswith('application_') or raw['response'] != delivered['content']:
            policy = delivered.get('response_policy') or {}
            proposal_hash = hashlib.sha256(raw['response'].encode()).hexdigest()
            if (policy.get('status') != 'delivered' or policy.get('model_proposal_sha256') != proposal_hash
                    or policy.get('public_turn') != turn
                    or policy.get('delivered_content_sha256') != hashlib.sha256(delivered.get('content', '').encode()).hexdigest()):
                raise ValueError('Native proposal has no matching confirmed application delivery')
            output.pop('response')
            output.update(native_response_sha256=proposal_hash, native_response_published=False,
                          response_origin=delivered.get('response_origin'),
                          delivered_content_sha256=policy['delivered_content_sha256'])
        invocations.append({**pick(row, BOUNDARY_FIELDS + ['runtime_status', 'runtime_id', 'invocation_id', 'outcome']),
                            'turn': turn, 'public_turn': turn, 'invocation_sequence': sequence,
                            'tool_scope_uuids': [tool['scope_uuid'] for tool in row.get('tools', []) if tool.get('scope_uuid')],
                            'normalized_output_fields': list(raw),
                            'output': output,
                            'usage': pick(raw.get('usage') or {}, ['prompt_tokens', 'completion_tokens', 'total_tokens', 'cost'])})
    if set(replies) != seen_turns | application_replies.keys():
        raise ValueError('Public replies have no matching native invocation or application clarification receipt')
    clarifications = []
    if application_replies:
        path = native / 'retail-response-decisions.jsonl'
        if not path.is_file():
            raise ValueError('Application clarification receipt is missing')
        clarifications = application_turns(application_replies, read(path, lines=True))
    lifecycle = [pick(row, ['at', 'event', 'status', 'harness', 'model_route', 'thread_id', 'runtime_id', 'invocation_id', 'error_type'])
                 for row in read(native / 'fabric-lifecycle.jsonl', lines=True)]
    files = {
        'usersim-setup.json': setup, 'framework-config.json': framework,
        'fabric-invocations.json': invocations, 'fabric-lifecycle.jsonl': lifecycle,
    }
    if clarifications:
        files['application-turns.json'] = clarifications
    traces = usersim.get('simulation_traces', [])
    if isinstance(traces, str):
        traces = json.loads(traces)
    files['usersim-quality-flags.json'] = [pick(row, ['kind', 'turn_idx', 'rating', 'detail'])
        for row in traces if row.get('kind') == 'assistant_quality' and row.get('rating') == 'failure']
    bodies = {name: ('\n'.join(json.dumps(clean(row), ensure_ascii=False) for row in value) + '\n'
                     if name.endswith('.jsonl') else json.dumps(clean(value), indent=2, ensure_ascii=False) + '\n')
              for name, value in files.items()}
    image = json.loads(recordings.read(run_id, 'runtime-receipt.json')).get('image_manifest', {}).get('files', {})
    manifest = {
        'schema': 'citizen-guide-context/v1', 'scenario_id': scenario_id, 'run_id': run_id,
        'recording_manifest_sha256': hashlib.sha256((recordings.pack_folder(run_id) / 'manifest.json').read_bytes()).hexdigest(),
        'projection_notice': 'Offline allowlisted projections of the same completed native run. Original recording bytes are unchanged; no new model calls were made.',
        'source_hashes': {**state.get('source_hashes', {}), **image}, 'native_sources': sources,
        'files': {name: hashlib.sha256(body.encode()).hexdigest() for name, body in bodies.items()},
    }
    target.mkdir(parents=True)
    for name, body in bodies.items():
        (target / name).write_text(body)
    (target / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return {'scenario_id': scenario_id, 'run_id': run_id, 'files': len(bodies)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', default='photography', choices=CANONICAL_DEMOS)
    parser.add_argument('--run-id', help='Explicit new recording to export before changing the tagged demo')
    arguments = parser.parse_args()
    print(json.dumps(export(arguments.scenario, run_id=arguments.run_id)))
