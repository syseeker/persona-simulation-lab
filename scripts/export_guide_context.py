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
from scripts.export_guide_recording import clean, pick


def export(scenario_id='photography', *, run_root: Path | None = None, destination: Path | None = None):
    load_environment()
    run_id = CANONICAL_DEMOS[scenario_id]
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
             'counting_notice': 'One UserSim assistant activation delegates a whole Fabric agent turn. UserSim simulated-tool counts do not count the advisor\'s real MCP calls.',
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
    replies = [m['content'] for m in conversation if m['role'] == 'assistant']
    invocations = []
    for row in read(native / 'reply-outcomes.jsonl', lines=True):
        raw = row.get('raw_output', {})
        if not isinstance(raw, dict) or raw.get('response') not in replies:
            raise ValueError('Publish only normalized replies matching the immutable public conversation')
        invocations.append({**pick(row, ['runtime_status', 'runtime_id', 'invocation_id', 'outcome']),
                            'normalized_output_fields': list(raw),
                            'output': pick(raw, ['adapter', 'harness', 'mode', 'model', 'completed', 'event_count',
                                                 'message_count', 'runtime_id', 'thread_id', 'resumed', 'response']),
                            'usage': pick(raw.get('usage') or {}, ['prompt_tokens', 'completion_tokens', 'total_tokens', 'cost'])})
    lifecycle = [pick(row, ['at', 'event', 'status', 'harness', 'model_route', 'thread_id', 'runtime_id', 'invocation_id', 'error_type'])
                 for row in read(native / 'fabric-lifecycle.jsonl', lines=True)]
    files = {
        'usersim-setup.json': setup, 'framework-config.json': framework,
        'fabric-invocations.json': invocations, 'fabric-lifecycle.jsonl': lifecycle,
    }
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
    print(json.dumps(export(parser.parse_args().scenario)))
