"""Publish one complete run's allowlisted configuration and evidence offline.

Native private records are never moved or overwritten. The public manifest uses
the shared CAP registry, retains execution failures, and exposes opaque source
references rather than local filesystem locations. Requests and results receive
explicit projections; original personas, prompts and raw Relay streams stay local.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re

import yaml

from learning_lab.captures import REGISTRY, REQUIREMENTS, verify_capture_manifest
from learning_lab.evidence import native_tool_records, relay_scopes, sanitize
from learning_lab.settings import ROOT, load_environment


TERMINAL = {'completed', 'failed', 'cancelled', 'interrupted'}
IDENTITY = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}')
HASH = re.compile(r'[a-f0-9]{64}')
MAX_FILE_BYTES = 64 * 1024 * 1024
PRIVATE_KEYS = {'original_profile_json', 'original_profile', 'persona', 'source_id', 'selection',
                'private_context', 'private_preferences', 'reasoning', 'reasoning_content',
                'analysis', 'thoughts', 'system_prompt', 'prompt', 'messages', 'instructions',
                'adapter_stdout', 'stdout', 'stderr', 'raw_output', 'config_text'}
PUBLIC_PREFERENCES = ['goal', 'budget_sgd', 'days', 'planning_area', 'known_skills', 'kind']
US_CONFIG = ['name', 'locale', 'max_turns', 'max_steps', 'max_query_attempts', 'max_assistant_attempts',
             'enforce_user_language', 'context_compression', 'persona_grounding_ratio']
CALL_FIELDS = ['call', 'role', 'mode', 'status', 'model', 'requested_model', 'selected_model',
               'provider_route', 'usage', 'latency_ms', 'http_status', 'error_type', 'finish_reason',
               'output_token_limit', 'tool_surface', 'routing_decision', 'control_request_id',
               'thread_id', 'transport', 'public_turn']
BOUNDARY_FIELDS = ['schema', 'turn', 'thread_id', 'request_id', 'captured_at']
REPLY_FIELDS = ['adapter', 'harness', 'mode', 'model', 'completed', 'event_count', 'message_count',
                'runtime_id', 'thread_id', 'resumed', 'response', 'enabled_toolsets']


def pick(value, names):
    return {name: value[name] for name in names if name in value} if isinstance(value, dict) else {}


def identity(value):
    if not isinstance(value, str) or not IDENTITY.fullmatch(value) or value in {'.', '..'}:
        raise ValueError('Unsupported scenario/run/condition identity')
    return value


def source_path(folder: Path, relative: str) -> Path:
    """Accept manifest-bound regular files inside this run only."""
    if not isinstance(relative, str):
        raise ValueError('Unsupported capture source path')
    name = PurePosixPath(relative)
    if name.is_absolute() or relative != name.as_posix() or '..' in name.parts or '\\' in relative:
        raise ValueError('Unsupported capture source path')
    path = folder / relative
    if not name.parts or any((folder / Path(*name.parts[:i])).is_symlink() for i in range(1, len(name.parts) + 1)):
        raise ValueError('Unsupported symbolic capture source path')
    if not path.is_file() or not path.resolve().is_relative_to(folder.resolve()):
        raise ValueError('Capture source is unavailable inside this run')
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError('Capture source exceeds the publication bound')
    return path


def read(path):
    raw = path.read_text()
    if path.suffix == '.jsonl':
        return [json.loads(line) for line in raw.splitlines() if line.strip()]
    return yaml.safe_load(raw) if path.suffix in {'.yaml', '.yml'} else json.loads(raw)


def redactor(folder):
    secrets = [value for key, value in os.environ.items()
               if re.search(r'KEY|TOKEN|SECRET|PASSWORD', key, re.I) and len(value) >= 8]

    def clean(value, depth=0):
        if depth > 25:
            return '[publication depth limit]'
        if isinstance(value, dict):
            return {key: clean(item, depth + 1) for key, item in value.items() if key not in PRIVATE_KEYS}
        if isinstance(value, list):
            return [clean(item, depth + 1) for item in value]
        if isinstance(value, str):
            if value.lstrip().startswith(('{', '[')):
                try:
                    decoded = json.loads(value)
                except (ValueError, RecursionError):
                    decoded = None
                if isinstance(decoded, (dict, list)):
                    # The secret may contain quotes/backslashes, so replacing
                    # it in an encoded JSON string cannot reliably match it.
                    return json.dumps(clean(decoded, depth + 1), ensure_ascii=False)
            for secret in secrets:
                value = value.replace(secret, '[redacted]')
            value = value.replace(str(folder), '[private-run]').replace(str(ROOT), '[developer-checkout]')
            value = re.sub(r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b', '[redacted-native-token]', value)
            return re.sub(r'/(?:home|tmp)/[^\s"\'<>]+', '[private-path]', value)
        return value

    return lambda value: clean(sanitize(value))


def fabric_config(value):
    result = pick(value, ['schema_version', 'metadata', 'harness', 'runtime', 'tools'])
    result['models'] = {name: pick(model, ['provider', 'model', 'base_url', 'api_key_env',
        'max_tokens', 'temperature', 'top_p', 'timeout_seconds']) for name, model in value.get('models', {}).items()}
    result['environment'] = pick(value.get('environment'), ['provider', 'workspace', 'artifacts', 'env_names'])
    result['mcp'] = value.get('mcp', {})
    result['relay'] = value.get('relay')
    result['skills'] = value.get('skills')
    if value.get('instructions') is not None:
        result['instructions_sha256'] = hashlib.sha256(json.dumps(value['instructions'], sort_keys=True).encode()).hexdigest()
    return result


def public_messages(folder, row):
    host = folder if row['purpose'] == 'baseline' else folder / 'comparisons' / identity(row['condition_id'])
    path = host / 'public-conversation.json'
    if not path.is_file():
        return []
    source_path(folder, path.relative_to(folder).as_posix())
    values = json.loads(path.read_text())
    if not isinstance(values, list):
        raise ValueError('The public conversation is not a list')
    return values


def project_requests(values, conversation):
    users = {row['turn']: row['content'] for row in conversation if row.get('role') == 'user'}
    replies = {row['turn']: row for row in conversation if row.get('role') == 'assistant'}
    result = []
    for value in values:
        request = value['request']
        supplied = request.get('input')
        if not isinstance(supplied, str) or value['turn'] not in users:
            raise ValueError('Fabric request has no matching public learner turn')
        message, separator, encoded = supplied.rpartition('\nLAB_PREFERENCES=')
        if separator:
            preferences = json.loads(encoded)
            public_message, delivery_separator, delivery_encoded = message.rpartition('\nAPPLICATION_DELIVERY_RECORD=')
            if delivery_separator:
                delivery = json.loads(delivery_encoded)
                previous = replies.get(value['turn'] - 1, {})
                if (not isinstance(delivery, dict) or set(delivery) != {'content', 'response_origin', 'public_turn'}
                        or delivery['content'] != previous.get('content')
                        or delivery['response_origin'] != previous.get('response_origin')
                        or delivery['public_turn'] != value['turn'] - 1):
                    raise ValueError('Fabric delivery acknowledgement does not match the previous public response')
                message = public_message
            if message != users[value['turn']] or not isinstance(preferences, dict) or set(preferences) - set(PUBLIC_PREFERENCES):
                raise ValueError('Fabric request contains input outside the public boundary')
        elif supplied != users[value['turn']]:
            raise ValueError('Fabric request does not match the public learner message')
        # Context and overrides can contain arbitrary SDK payloads. The public
        # receipt retains their presence without publishing their contents.
        result.append({**pick(value, BOUNDARY_FIELDS), 'request': pick(request, ['input', 'request_id', 'relay_session_root']),
                       'context_present': bool(request.get('context')), 'overrides_present': bool(request.get('overrides'))})
    return result


def project_results(values, conversation):
    replies = {row['content'] for row in conversation if row.get('role') == 'assistant'}
    result = []
    for value in values:
        native = value.get('result')
        row = {**pick(value, BOUNDARY_FIELDS), **pick(value, ['boundary_status'])}
        if native is None:
            row.update(result=None, error=pick(value.get('error'), ['type', 'code']))
        else:
            output = pick(native.get('output'), REPLY_FIELDS)
            if 'response' in output and (not isinstance(output['response'], str) or output['response'] not in replies):
                # Invalid/partial answers can be absent from the public transcript.
                # Preserve their status; the original payload stays private.
                output.pop('response')
                output['response_not_in_public_conversation'] = True
            row['result'] = {**pick(native, ['agent_name', 'harness', 'adapter_kind', 'adapter_id', 'runtime_id',
                                            'invocation_id', 'request_id', 'status']),
                             'usage': pick(native.get('usage'), ['input_tokens', 'output_tokens', 'total_tokens',
                                'prompt_tokens', 'completion_tokens', 'cost', 'total_cost', 'currency']),
                             'output': output, 'error': pick(native.get('error'), ['code', 'retryable']),
                             'native_top_level_fields': list(native)}
        result.append(row)
    return result


def project_relay(path):
    # Existing native decoders retain real IDs and parent links. Publish none of
    # their model/system input/output payloads or code references to local paths.
    # Resolve this single native file; a sibling runtime's stream must not enter
    # a projection whose provenance references only this source artifact.
    root = path.parent
    scopes = relay_scopes(root)
    keys = ['uuid', 'parent_uuid', 'category', 'name', 'status', 'started_at', 'ended_at', 'duration_ms', 'parent_available']
    tools = native_tool_records(root)
    tools = [pick(tool, ['name', 'arguments', 'result', 'scope_uuid', 'status', 'evidence_origin'])
             for tool in tools if tool.get('name', '').split('__')[-1] in {'search_courses', 'get_course_details', 'compare_courses'}]
    return {'scopes': [pick(scope, keys) for scope in scopes['scopes']], 'tools': tools,
            'notices': scopes['notices'], 'native_event_count': scopes['events']}


def projection(path, value, folder, row):
    """Return an intentionally reviewed subset, or keep the source private."""
    name = path.name
    if name == 'resolved-inputs.json':
        first = value[0] if isinstance(value, list) and value else {}
        return {'configuration': pick(first.get('usersim_config'), US_CONFIG),
                'source_distribution': first.get('source_distribution'),
                'source_revision': first.get('source_revision'),
                'probe_type': first.get('probe_type'), 'private_preamble_published': False}, 'application-projection'
    if name == 'source-lock.json':
        return pick(value, ['source', 'source_revision', 'original_sha256', 'kind', 'source_url', 'conditioning']), 'application-projection'
    if name == 'fabric-config.json':
        return fabric_config(value), 'application-projection'
    if name == 'fabric-plan.json':
        result = pick(value, ['agent_name', 'resolution', 'capability_plan', 'capabilities'])
        result['agent_config'] = fabric_config(value.get('agent_config') or {})
        result['adapter_descriptor'] = pick(value.get('adapter_descriptor'), ['id', 'name', 'version', 'adapter_id', 'capabilities'])
        return result, 'application-projection'
    if name == 'fabric-run-requests.jsonl':
        return project_requests(value, public_messages(folder, row)), 'application-projection'
    if name == 'fabric-run-results.jsonl':
        return project_results(value, public_messages(folder, row)), 'application-projection'
    if name == 'reply-outcomes.jsonl':
        return [pick(item, ['runtime_status', 'runtime_id', 'invocation_id', 'outcome']) for item in value], 'application-projection'
    if name == 'relay.jsonl':
        return project_relay(path), 'application-projection'
    if name == 'configuration.json' and path.parent.name == 'designer-private':
        columns = [pick(column, ['name', 'column_type', 'model_alias', 'output_format', 'dtype'])
                   for column in value.get('columns', [])]
        return {'columns': columns, 'model_configs': value.get('model_configs', []),
                'constraints': value.get('constraints'), 'profilers': value.get('profilers'),
                'seed_data_published': False}, 'application-projection'
    if name == 'designer-output.json':
        return pick(value, ['engine', 'version', 'hypothesis', 'fields', 'warnings']), 'application-projection'
    if name == 'designer-lineage.json':
        return pick(value, ['kind', 'hypothesis', 'original_profile_sha256', 'overlay_sha256', 'configuration_sha256',
                            'generator', 'source', 'source_revision']), 'application-projection'
    if name == 'designer-generation.json':
        return pick(value, ['engine', 'version', 'status', 'warnings', 'configuration_sha256', 'hypothesis']), 'application-projection'
    if name == 'designer-configuration.json':
        return pick(value, ['engine', 'version', 'schema', 'hypothesis', 'model', 'model_alias', 'num_records',
                            'source_seeded', 'output_schema', 'generation_mode']), 'application-projection'
    if name == 'usersim-result.json':
        outcome = value.get('simulation_outcome') or {}
        outcome = json.loads(outcome) if isinstance(outcome, str) else outcome
        return {'probe_type': value.get('probe_type'), 'usersim_config': pick(value.get('usersim_config'), US_CONFIG),
                'outcome': pick(outcome, ['status', 'failure_class', 'failure_attribution', 'n_turns', 'n_tool_calls',
                    'n_user_query_attempts', 'n_user_followup_retries', 'n_assistant_inline_failures',
                    'n_assistant_retries', 'early_stop', 'per_model_calls']),
                'private_preamble_published': False}, 'application-projection'
    if name == 'usersim-model-config.json':
        return {role: pick(settings, ['model_name', 'max_tokens', 'temperature', 'top_p', 'seed', 'timeout'])
                for role, settings in value.items() if role in {'user_model', 'assistant_model', 'judge_model', 'summary_model'}}, 'application-projection'
    if name == 'usersim-activations.jsonl':
        return [pick(item, ['at', 'phase', 'activation_id', 'role', 'message_count', 'tools_enabled',
                            'continues_turn', 'response_role', 'usage']) for item in value], 'application-projection'
    if name in {'helix-job.json', 'helix-job-config.json'}:
        return pick(value, ['engine', 'version', 'job_id', 'status', 'result', 'evaluation', 'mode', 'inference_calls',
                            'task', 'task_type', 'dataset_rows']), 'application-projection'
    if name in {'platform-operation-requests.jsonl', 'platform-operation-results.jsonl'}:
        return [pick(item, ['schema', 'operation', 'at', 'status', 'request_id', 'response_id', 'error_type']) for item in value], 'application-projection'
    if name.startswith('platform-'):
        return pick(value, ['schema', 'run_id', 'condition_id', 'status', 'provider_status', 'model_alias', 'public_preset',
            'inference_calls', 'native_resource_definitions', 'agent', 'deployment', 'package', 'session', 'invocation',
            'policy', 'probes', 'removed', 'absent', 'cleanup_confirmed', 'native_absence_confirmed', 'boundary',
            'connection', 'executor', 'server', 'configured_executor', 'source_hashes']), 'application-projection'
    if name == 'agent.yaml':
        return pick(value, ['name', 'description', 'harness', 'models', 'runtime', 'tools', 'mcp', 'environment',
                            'skills', 'resources', 'metadata']), 'application-projection'
    if name == 'gateway-calls.jsonl':
        return [pick(item, CALL_FIELDS) for item in value], 'application-projection'
    if name == 'hermes-config-capture.jsonl':
        return [pick(item, ['role', 'runtime_id', 'status', 'reason', 'byte_exact', 'source_sha256', 'sha256'])
                for item in value], 'application-projection'
    if name == 'retail-response-decisions.jsonl':
        return [pick(item, ['schema_version', 'public_turn', 'owner', 'status', 'response_origin',
            'model_proposal_sha256', 'original_word_count', 'model_proposal_rule_failures',
            'model_proposal_rule_status', 'model_proposal_rule_coverage', 'model_proposal_semantically_certified',
            'delivered_word_count', 'delivered_content_sha256', 'source_ids', 'source_hashes',
            'native_tool_evidence', 'excluded_source_ids', 'error_type']) for item in value], 'application-projection'
    native_configs = {'hermes-managed-config.yaml', 'hermes-native-config.yaml', 'fabric-relay.json',
        'preferences-by-turn.jsonl', 'gateway-effective-config.json', 'mcp-tools-list.json', 'mcp-tools-list.jsonl',
        'provider-tool-schemas.jsonl', 'litellm-loaded.yaml', 'litellm-effective-config.json',
        'designer-run-config.json', 'designer-model-providers.json', 'helix-evaluator-config.json',
        'guardrails-config.json', 'requested-policy.yaml', 'effective-policy.yaml', 'effective-policy.json',
        'retail-response-config.json'}
    if name in native_configs:
        return value, 'redacted-native-configuration'
    public_results = {'situation.json', 'public-conversation.json', 'fabric-doctor.json', 'fabric-lifecycle.jsonl',
        'designer-profiling.json', 'routing-configuration.json', 'routing-comparison.json', 'evaluation.json',
        'helix-criteria.json', 'helix-evaluation.json', 'guardrails-decisions.jsonl', 'guardrails-probe.json',
        'boundary-probes.json', 'cleanup.json', 'sandbox-identity.json'}
    if name in public_results:
        return value, 'application-projection'
    return None, None


def export(run_id, *, run_root: Path | None = None, destination: Path | None = None):
    load_environment()
    run_id = identity(run_id)
    folder = (run_root or ROOT / 'runs/journeys') / run_id
    if folder.is_symlink() or any(parent.is_symlink() for parent in folder.parents):
        raise ValueError('Symbolic run directories cannot be published')
    state = read(source_path(folder, 'run.json'))
    if state.get('run_id') != run_id or state.get('scenario_id') not in {'photography', 'boardgames', 'dreamjob'}:
        raise ValueError('The selected run identity does not match its scenario')
    if state.get('status') not in TERMINAL or not state.get('cleanup_confirmed'):
        raise ValueError('Publish only terminal runs with confirmed cleanup')
    manifest = read(source_path(folder, 'capture-manifest.json'))
    # Reject unsafe locations even before recomputing the native coverage.
    for row in manifest.get('rows', []):
        if row.get('condition_id') is not None:
            identity(row['condition_id'])
        if row.get('episode_id') is not None:
            identity(row['episode_id'])
        for artifact in row.get('artifacts', []):
            source_path(folder, artifact['location'])
    verify_capture_manifest(folder, manifest)
    target = destination or ROOT / 'recordings/captures' / state['scenario_id'] / run_id
    if target.name != run_id or target.parent.name != state['scenario_id']:
        raise ValueError('The publication destination must identify this scenario/run')
    if target.exists() or target.is_symlink():
        raise ValueError('Capture packs are immutable; refuse to overwrite an existing destination')
    if any(parent.is_symlink() for parent in target.parents) or target.resolve().is_relative_to(folder.resolve()):
        raise ValueError('Unsupported capture publication destination')
    clean = redactor(folder)
    files, rows, published = {}, [], {}
    for private_row in manifest['rows']:
        row = {**pick(private_row, ['id', 'module', 'lessons', 'operation', 'scenario_ids', 'scenario_id', 'run_id',
            'condition_id', 'episode_id', 'purpose', 'availability', 'required', 'execution_status', 'producer_revision',
            'operation_id', 'turn', 'model_role']), 'description': REQUIREMENTS[private_row['id']]['description']}
        artifacts = []
        for source in private_row['artifacts']:
            opaque = pick(source, ['id', 'sha256', 'size_bytes', 'captured_at', 'role', 'schema'])
            if not HASH.fullmatch(source.get('sha256', '')):
                raise ValueError('Invalid source artifact hash')
            artifacts.append({**opaque, 'access': 'private'})
            key = (private_row['condition_id'], source['id'])
            if key not in published:
                path = source_path(folder, source['location'])
                value, kind = projection(path, read(path), folder, private_row)
                if value is None:
                    published[key] = None
                else:
                    value = clean(value)
                    phase = 'baseline' if private_row['purpose'] == 'baseline' else 'managed' if private_row['purpose'] == 'managed' else 'comparisons'
                    suffix = '.json' if path.name == 'relay.jsonl' else path.suffix
                    stem = path.stem + ('.projection' if kind == 'application-projection' else '')
                    name = f'{phase}/{identity(private_row["condition_id"])}/{source["id"]}-{stem}{suffix}'
                    if suffix == '.jsonl':
                        body = ''.join(json.dumps(item, ensure_ascii=False) + '\n' for item in value)
                    elif suffix in {'.yaml', '.yml'}:
                        body = yaml.safe_dump(value, sort_keys=False)
                    else:
                        body = json.dumps(value, indent=2, ensure_ascii=False) + '\n'
                    files[name] = body
                    published[key] = {'id': hashlib.sha256(name.encode()).hexdigest()[:24], 'location': name,
                        'sha256': hashlib.sha256(body.encode()).hexdigest(), 'size_bytes': len(body.encode()),
                        'access': 'public', 'role': kind,
                        'schema': source['schema'] if kind == 'redacted-native-configuration' else 'citizen-capture-projection/v1',
                        'source_artifact_ids': [source['id']], 'source_sha256': source['sha256'],
                        'source_role': source['role'], 'source_schema': source['schema']}
            if published[key]:
                artifacts.append(published[key])
        public = [artifact for artifact in artifacts if artifact['access'] == 'public']
        row.update(artifacts=artifacts, access='public' if public else 'private',
                   publication_availability='exists' if public else 'not-used' if row['availability'] == 'not-used' else 'private',
                   publication_kind='projection' if any(a['role'] == 'application-projection' for a in public)
                   else 'redacted-native-configuration' if public else None)
        rows.append(row)
    public_manifest = {'schema': 'citizen-public-captures/v1', 'registry_schema': REGISTRY['schema'],
        'scenario_id': state['scenario_id'], 'run_id': run_id, 'execution_status': state['status'],
        'source_revision': state.get('source_revision'), 'host_sdk_versions': manifest.get('host_sdk_versions', {}),
        'source_manifest_sha256': hashlib.sha256((folder / 'capture-manifest.json').read_bytes()).hexdigest(),
        'coverage': manifest['coverage'], 'rows': rows,
        'files': {name: hashlib.sha256(body.encode()).hexdigest() for name, body in sorted(files.items())},
        'notice': 'Offline publication. Private native captures are represented by opaque IDs/hashes without local locations. Public projections are explicitly labelled; complete capture does not imply successful execution.'}
    # No publication folder is created if final validation detects changed input.
    verify_capture_manifest(folder, manifest)
    target.mkdir(parents=True, exist_ok=False)
    for name, body in files.items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x') as stream:
            stream.write(body)
    with (target / 'manifest.json').open('x') as stream:
        stream.write(json.dumps(public_manifest, indent=2, ensure_ascii=False) + '\n')
    return {'scenario_id': state['scenario_id'], 'run_id': run_id, 'directory': str(target),
            'files': len(files), 'rows': len(rows)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_id')
    print(json.dumps(export(parser.parse_args().run_id)))
