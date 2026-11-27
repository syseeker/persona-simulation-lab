"""Read-only, condition-scoped execution evidence from curated demo packs.

This module never opens a native trace or starts an observability service. The
optional Phoenix links come from a bounded local import receipt; richer native
advisor I/O remains in the explicitly started loopback viewer.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import socket
from urllib.parse import urlparse

from . import guide_metadata, recordings
from .settings import ROOT

PHOENIX_RECEIPT = ROOT / 'runs/observability/import-receipt.json'
MAX_RECEIPT_BYTES = 2 * 1024 * 1024


def _number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0 else None


def _text(value, limit=240):
    return value[:limit] if isinstance(value, str) else None


def _published(inventory, condition_id, requirement):
    """Read only files already checked by the public capture inventory."""
    result, seen = [], set()
    folder = guide_metadata.PACKS / inventory['scenario_id'] / inventory['run_id']
    for row in inventory['rows']:
        if row['id'] != requirement or row['condition_id'] != condition_id:
            continue
        for artifact in row['artifacts']:
            if artifact.get('privacy') == 'private' or not artifact.get('path') or artifact['path'] in seen:
                continue
            seen.add(artifact['path'])
            path = guide_metadata._safe_path(folder, artifact['path'])
            body = path.read_bytes()
            if hashlib.sha256(body).hexdigest() != artifact['sha256']:
                raise ValueError('Execution capture changed after verification')
            if path.suffix == '.jsonl':
                result.extend(json.loads(line) for line in body.splitlines() if line.strip())
            else:
                value = json.loads(body)
                result.extend(value if isinstance(value, list) else [value])
    return result


def _usage(rows):
    """Count calls and known provider tokens without treating missing usage as zero."""
    records = []
    for value in rows:
        if not isinstance(value, dict):
            continue
        row = {key: value[key] for key in ('call', 'public_turn', 'attempt', 'retry_of_call')
               if isinstance(value.get(key), int) and not isinstance(value[key], bool)}
        row.update({key: _text(value.get(key)) for key in
                    ('role', 'status', 'requested_model', 'selected_model', 'model', 'thread_id', 'finish_reason')})
        row['latency_ms'] = _number(value.get('latency_ms'))
        usage = value.get('usage')
        row['usage'] = ({key: _number(usage.get(key)) for key in ('prompt_tokens', 'completion_tokens', 'total_tokens')}
                        if isinstance(usage, dict) else None)
        records.append(row)
    by_role = []
    for role in sorted({row.get('role') or 'unknown' for row in records}):
        selected = [r for r in records if (r.get('role') or 'unknown') == role]
        by_role.append({'role': role, **_usage_total(selected)})
    return {'records': records, 'summary': {**_usage_total(records), 'by_role': by_role}, 'scope': 'condition',
            'notice': 'These are model requests for this condition. Request durations are not end-to-end learner latency. Missing token usage stays unknown; gateway calls are not guessed to be Relay spans.'}


def _usage_total(records):
    known = [row for row in records if row.get('usage') and row['usage'].get('total_tokens') is not None]
    timed = [row for row in records if row.get('latency_ms') is not None]
    return {'calls': len(records), 'known_tokens': sum(row['usage']['total_tokens'] for row in known),
            'unknown_usage_calls': len(records) - len(known),
            'model_request_ms': round(sum(row['latency_ms'] for row in timed), 3),
            'unknown_latency_calls': len(records) - len(timed)}


def _phoenix(scenario_id, run_id, condition_id):
    unavailable = {'available': False, 'url': None, 'project_name': None, 'trace_urls': [],
                   'notice': 'No verified local historical import is recorded. Opening this guide never starts Phoenix or imports traces.'}
    if not _phoenix_running():
        unavailable['notice'] = 'The separate local Phoenix viewer is stopped. Start it explicitly to open historical traces; guide inspection never starts a service.'
        return unavailable
    path = PHOENIX_RECEIPT
    if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents)) or path.stat().st_size > MAX_RECEIPT_BYTES:
        return unavailable
    try:
        value = json.loads(path.read_text())
        if value.get('schema') != 'citizen-phoenix-import/v1' or value.get('status') != 'verified':
            return unavailable
        for row in value.get('conditions', []):
            if (row.get('scenario_id'), row.get('run_id'), row.get('condition_id')) != (scenario_id, run_id, condition_id):
                continue
            urls = [row.get('url'), *row.get('trace_urls', [])]
            if not urls or not all(isinstance(url, str) and len(url) < 1600 and
                                  urlparse(url).scheme == 'http' and urlparse(url).netloc == '127.0.0.1:6006'
                                  and not urlparse(url).username for url in urls):
                return unavailable
            return {'available': True, 'url': row['url'], 'project_name': _text(row.get('project_name')),
                    'trace_urls': row.get('trace_urls', []), 'notice': 'Historical native advisor traces imported into local Phoenix. Phoenix is a separate loopback service; no new simulation runs when you open it.'}
    except (ValueError, TypeError, KeyError):
        pass
    return unavailable


def _phoenix_running():
    """Check the owned PID and listening socket without starting any process."""
    path = PHOENIX_RECEIPT.parent / 'service.json'
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 4096:
        return False
    try:
        service = json.loads(path.read_text())
        pid = service.get('pid')
        if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 1:
            return False
        proc = Path(f'/proc/{pid}')
        fields = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
        expected = str(ROOT / 'integrations/observability/.venv/bin/phoenix').encode()
        if (fields[0] == 'Z' or service.get('process_identity') != f'{pid}:{fields[19]}'
                or expected not in (proc / 'cmdline').read_bytes().split(b'\0')):
            return False
        with socket.create_connection(('127.0.0.1', 6006), timeout=0.25):
            return True
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        return False


def execution(scenario_id='photography', condition_id=None, public_turn=None):
    """Return one scenario/condition's reviewed scopes, tools and model accounting."""
    if public_turn is not None:
        if isinstance(public_turn, str) and re.fullmatch('[1-3]', public_turn):
            public_turn = int(public_turn)
        if isinstance(public_turn, bool) or public_turn not in (1, 2, 3):
            raise ValueError('Choose a public turn from 1 to 3')
    inventory = guide_metadata.metadata(scenario_id)
    conditions = inventory['conditions']
    if condition_id is None:
        condition = next((row for row in conditions if row['purpose'] == 'baseline'), None)
    else:
        condition = next((row for row in conditions if row['id'] == condition_id), None)
        if condition is None:
            raise ValueError('Condition does not belong to the selected scenario recording')
    if condition is None:
        return {'schema': 'citizen-guide-execution/v1', 'scenario_id': scenario_id, 'run_id': inventory['run_id'],
                'available': False, 'conditions': [], 'condition': None, 'spans': [], 'tools': [],
                'usage': _usage([]), 'notices': [inventory['notice']], 'inference_calls_for_inspection': 0}
    run_id, cid = inventory['run_id'], condition['id']
    trace = recordings.trace(run_id)
    conversation = trace.get('conversation', [])
    replies = [row for row in conversation if row.get('role') == 'assistant']
    messages = [row for row in conversation if row.get('role') == 'user']
    if public_turn is not None and public_turn > len(replies):
        raise ValueError('The selected recording has no such public turn')
    relay = _published(inventory, cid, 'CAP-REL-02')
    spans, tools, notices = [], [], []
    for item in relay:
        for source in item.get('scopes', []):
            native_id = source.get('uuid')
            if not isinstance(native_id, str):
                continue
            spans.append({'id': native_id, 'parent_id': source.get('parent_uuid'),
                          **{key: source.get(key) for key in ('parent_available', 'category', 'name', 'status', 'started_at', 'ended_at', 'duration_ms')},
                          'source': 'native-relay', 'payload_availability': 'Model payloads are retained only in the private local trace viewer.'})
        tools.extend(item.get('tools', []))
        notices.extend(item.get('notices', []))
    if condition['purpose'] == 'managed':
        managed = json.loads(recordings.read(run_id, 'platform-trace.json'))
        for source in managed.get('spans', []):
            start, end = source.get('started_at'), source.get('ended_at')
            from .evidence import _duration
            spans.append({'id': source['span_id'], 'parent_id': source.get('parent_span_id'),
                          'category': str(source.get('kind', 'unknown')).lower(), 'name': source.get('name'),
                          'status': source.get('status'), 'started_at': start, 'ended_at': end,
                          'duration_ms': _duration(start, end), 'source': 'native-helix-intake',
                          'model': source.get('model'), 'usage': {key: source.get(key) for key in ('input_tokens', 'output_tokens', 'total_tokens')}})
        tools.extend(managed.get('tools', []))
    ids = {row['id'] for row in spans}
    for row in spans:
        row['parent_available'] = not row.get('parent_id') or row['parent_id'] in ids
    selected_turn = None
    application_only = False
    if public_turn is not None and condition['purpose'] == 'baseline':
        reply = replies[public_turn - 1]
        policy = reply.get('response_policy') or {}
        application_only = policy.get('agent_invoked') is False and policy.get('execution_kind') == 'application_clarification'
        selected_turn = {'number': public_turn, 'input': messages[public_turn - 1].get('content') if len(messages) >= public_turn else None,
                         'output': reply.get('content'), 'execution_kind': policy.get('execution_kind', 'native_agent'),
                         'agent_invoked': not application_only}
    condition_span_count = len(spans)
    if application_only:
        spans, tools = [], []
        correlation = {'status': 'application-only', 'explanation': 'The application returned its configured clarification without calling Fabric, an advisor model or a course tool. UserSim still generated and checked the learner message.'}
    else:
        correlation = {'status': 'condition-only', 'explanation': 'The exported native scopes belong to this condition. No per-turn or gateway-call correlation is invented where the publication does not retain that join.'}
    usage = _usage(_published(inventory, cid, 'CAP-GW-02'))
    coverage = [{'capability': 'Agent/model/tool execution', 'status': 'observed' if spans else 'not-executed' if application_only else 'unavailable'},
                {'capability': 'Tool inputs and returned course facts', 'status': 'observed' if tools else 'not-executed' if application_only else 'unavailable'},
                {'capability': 'Token usage and model-request duration', 'status': 'observed' if usage['records'] else 'unavailable'},
                {'capability': 'Skill execution, spawned subagents and memory access', 'status': 'not-established',
                 'explanation': 'A configured skill or available subagent is not evidence that it ran.'}]
    return {'schema': 'citizen-guide-execution/v1', 'available': True, 'scenario_id': scenario_id, 'run_id': run_id,
            'conditions': conditions, 'condition': condition, 'scope': 'condition', 'public_turn': public_turn,
            'selected_turn': selected_turn, 'correlation': correlation, 'spans': spans, 'tools': tools,
            'condition_span_count': condition_span_count, 'category_counts': dict(Counter(row['category'] for row in spans)),
            'usage': usage, 'run_usage': {'calls': trace.get('usage', {}).get('calls'), 'scope': 'whole-run'},
            'coverage': coverage, 'notices': list(dict.fromkeys(notices)),
            'phoenix': _phoenix(scenario_id, run_id, cid), 'inference_calls_for_inspection': 0}
