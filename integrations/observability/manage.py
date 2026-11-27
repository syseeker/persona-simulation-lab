"""Explicit local Phoenix lifecycle and historical import. Never runs an agent.

Run using this integration's isolated interpreter. The converter uses saved
ATOF / Intake records and the stable OTLP protobuf protocol, not Relay replay.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, build_opener, ProxyHandler

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / 'runs/observability'
ENDPOINT = 'http://127.0.0.1:6006'
PYTHON = ROOT / 'integrations/observability/.venv/bin/python'
MAX_SOURCE = 64 * 1024 * 1024
NAMESPACE = 'citizen-historical/v1'
SAFE_ID = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}')
FORBIDDEN_KEYS = re.compile(r'^(?:headers?|authorization|api[_-]?key|access[_-]?token|password|secret|reasoning(?:_content)?|analysis|thoughts?|original_profile(?:_json)?|persona|private_context|system_prompt)$', re.I)
OPEN = build_opener(ProxyHandler({}))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.chmod(0o600)
    temporary.replace(path)


def read_json(path, expected=None):
    if (not path.is_file() or path.stat().st_size > MAX_SOURCE or
            any(p.is_symlink() for p in (path, *path.parents))):
        raise ValueError('Missing, oversized or symbolic source: ' + path.name)
    body = path.read_bytes()
    if expected is not None and digest(body) != expected:
        raise ValueError('Historical source hash mismatch: ' + path.name)
    if path.suffix == '.jsonl':
        return [json.loads(line) for line in body.splitlines() if line.strip()]
    return json.loads(body)


def _request(path, payload=None, project=None):
    if not path.startswith('/') or path.startswith('//'):
        raise ValueError('Only the fixed local Phoenix endpoint is supported')
    headers = {'Accept': 'application/json'}
    if payload is not None:
        headers['Content-Type'] = 'application/x-protobuf'
    if project:
        headers['x-project-name'] = project
    request = Request(ENDPOINT + path, data=payload, headers=headers)
    with OPEN.open(request, timeout=15) as response:
        return response.status, response.read(4 * 1024 * 1024)


def status():
    path = STATE / 'service.json'
    if not path.exists():
        return {'running': False, 'owned': False, 'url': ENDPOINT}
    receipt = read_json(path)
    pid = receipt.get('pid')
    owned = False
    if isinstance(pid, int) and pid > 1:
        try:
            cmd = Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
            owned = (str(PYTHON.parent / 'phoenix').encode() in cmd and
                     str(pid) == receipt.get('process_identity', '').split(':')[0] and
                     _process_identity(pid) == receipt.get('process_identity'))
        except OSError:
            pass
    healthy = False
    if owned:
        try:
            healthy = _request('/v1/projects')[0] == 200
        except (OSError, URLError, ValueError):
            pass
    return {'running': healthy, 'owned': owned, 'pid': pid if owned else None,
            'url': ENDPOINT, 'version': receipt.get('version'), 'working_directory': str(STATE / 'phoenix')}


def _process_identity(pid):
    # Linux start ticks protect against PID reuse. stat's comm may contain spaces.
    raw = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
    return f'{pid}:{raw[19]}'


def start():
    current = status()
    if current['running']:
        return current
    if current['owned']:
        raise RuntimeError('The owned Phoenix process is not healthy; inspect its local log before restarting')
    for port in (6006, 6007):
        with socket.socket() as stream:
            # A previous owned service can leave accepted sockets in TIME_WAIT.
            # Reuse avoids mistaking those for a foreign listening process.
            stream.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                stream.bind(('127.0.0.1', port))
            except OSError as exc:
                raise RuntimeError(f'Port {port} is already owned; no process was stopped') from exc
    if not (PYTHON.parent / 'phoenix').exists():
        raise RuntimeError('Install the isolated observability environment first')
    STATE.mkdir(parents=True, exist_ok=True)
    STATE.chmod(0o700)
    safe = {key: os.environ[key] for key in ('PATH', 'LANG', 'LC_ALL', 'TZ', 'HOME') if key in os.environ}
    safe.update(PHOENIX_HOST='127.0.0.1', PHOENIX_PORT='6006', PHOENIX_GRPC_PORT='6007',
                PHOENIX_WORKING_DIR=str(STATE / 'phoenix'), PHOENIX_TELEMETRY_ENABLED='false',
                PHOENIX_ALLOW_EXTERNAL_RESOURCES='false', PHOENIX_ENABLE_AUTH='false',
                DO_NOT_TRACK='1', PYTHONNOUSERSITE='1')
    log = (STATE / 'phoenix.log').open('ab')
    process = subprocess.Popen([str(PYTHON.parent / 'phoenix'), 'serve', '--port', '6006'],
                               cwd=ROOT, env=safe, stdin=subprocess.DEVNULL, stdout=log,
                               stderr=subprocess.STDOUT, start_new_session=True)
    log.close()
    write_json(STATE / 'service.json', {'schema': 'citizen-phoenix-service/v1', 'pid': process.pid,
               'process_identity': _process_identity(process.pid), 'version': '22.1.0',
               'url': ENDPOINT, 'started_at': datetime.now(timezone.utc).isoformat(),
               'bind': '127.0.0.1', 'model_credentials_inherited': False})
    deadline = time.monotonic() + 55
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError('Phoenix exited during startup; inspect runs/observability/phoenix.log')
        current = status()
        if current['running']:
            return current
        time.sleep(0.5)
    raise RuntimeError('Phoenix is not ready; its owned process and log were preserved')


def stop():
    current = status()
    if not current['owned']:
        return {'stopped': False, 'reason': 'No owned Phoenix process; no other process was touched'}
    os.kill(current['pid'], signal.SIGTERM)
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        if not status()['owned']:
            return {'stopped': True, 'pid': current['pid']}
        time.sleep(0.2)
    raise RuntimeError('Owned Phoenix process did not exit after SIGTERM; no forced kill was issued')


def selected_demos():
    # Parse the literal tagging table without importing any execution module.
    import ast
    module = ast.parse((ROOT / 'src/learning_lab/guide_lessons.py').read_text())
    for node in module.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'CANONICAL_DEMOS' for t in node.targets):
            result = ast.literal_eval(node.value)
            if set(result) != {'photography', 'boardgames', 'dreamjob'}:
                break
            return result
    raise ValueError('Cannot resolve the explicitly tagged demo recordings')


def _source(run_root, artifact):
    relative = Path(artifact['location'])
    if relative.is_absolute() or any(p in {'.', '..'} for p in relative.parts):
        raise ValueError('Unsafe native capture location')
    path = run_root / relative
    return path, read_json(path, artifact['sha256'])


def sources():
    """Resolve only hash-bound native captures for the currently selected demos."""
    result = []
    for scenario, run_id in selected_demos().items():
        run_root = ROOT / 'runs/journeys' / run_id
        public_root = ROOT / 'recordings/captures' / scenario / run_id
        public = read_json(public_root / 'manifest.json')
        private_path = run_root / 'capture-manifest.json'
        private = read_json(private_path, public['source_manifest_sha256'])
        if public.get('scenario_id') != scenario or public.get('run_id') != run_id:
            raise ValueError('Selected public source identity mismatch')
        if private.get('scenario_id') != scenario or private.get('run_id') != run_id:
            raise ValueError('Selected native source identity mismatch')
        seen = set()
        for row in private['rows']:
            if row.get('id') != 'CAP-REL-02' or row.get('availability') != 'exists':
                continue
            if row.get('scenario_id') != scenario or row.get('run_id') != run_id:
                raise ValueError('Native row identity mismatch')
            for artifact in row['artifacts']:
                key = (row['condition_id'], artifact['location'])
                if key in seen:
                    continue
                seen.add(key)
                path, events = _source(run_root, artifact)
                result.append({'scenario_id': scenario, 'run_id': run_id,
                               'condition_id': row['condition_id'], 'purpose': row['purpose'],
                               'source': 'native-relay', 'source_path': path.relative_to(ROOT).as_posix(),
                               'source_sha256': artifact['sha256'], 'events': events})
        if scenario == 'dreamjob':
            manifest = read_json(ROOT / 'recordings' / scenario / run_id / 'manifest.json')
            hashes = manifest.get('original_private_artifact_sha256') or {}
            condition = read_json(run_root / 'platform-condition.json', hashes['platform-condition.json'])
            cid = condition['condition_id']
            if not SAFE_ID.fullmatch(cid):
                raise ValueError('Invalid managed condition identity')
            # The raw managed Intake file was not included in the original
            # capture hashes. Use its hash-bound projection instead. This keeps
            # all 12 native identities/times and tool facts, but cannot provide
            # the unbound raw LLM payloads.
            path = run_root / 'platform-trace.json'
            expected = hashes.get('platform-trace.json')
            if not expected:
                raise ValueError('Managed native projection has no stored source hash')
            native = read_json(path, expected)
            result.append({'scenario_id': scenario, 'run_id': run_id, 'condition_id': cid,
                           'purpose': 'managed', 'source': 'native-helix-intake',
                           'source_path': path.relative_to(ROOT).as_posix(), 'source_sha256': expected,
                           'intake': native})
    return result


def nanos(value):
    """RFC3339 to integer nanoseconds, retaining Relay's sub-microsecond precision."""
    if not isinstance(value, str):
        raise ValueError('Missing native execution timestamp')
    match = re.fullmatch(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?(Z|[+-]\d\d:\d\d)', value)
    if not match:
        raise ValueError('Invalid native execution timestamp')
    base, fraction, zone = match.groups()
    parsed = datetime.fromisoformat(base + ('+00:00' if zone == 'Z' else zone))
    seconds = int((parsed.astimezone(timezone.utc) - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds())
    return seconds * 1_000_000_000 + int((fraction or '').ljust(9, '0'))


def mapped_id(context, native, size):
    if not isinstance(native, str) or not native:
        raise ValueError('Missing native trace identifier')
    return hashlib.sha256((NAMESPACE + '|' + context + '|' + native).encode()).digest()[:size].hex()


def clean(value, depth=0):
    """Advisor-only content; no headers, source personas, simulator prompts or reasoning."""
    if depth > 15:
        return '[bounded nested value]'
    if isinstance(value, dict):
        return {str(k): clean(v, depth + 1) for k, v in value.items() if not FORBIDDEN_KEYS.fullmatch(str(k))}
    if isinstance(value, list):
        return [clean(v, depth + 1) for v in value[:512]]
    if isinstance(value, str):
        if value.lstrip().startswith(('{', '[')):
            try:
                return clean(json.loads(value), depth + 1)
            except ValueError:
                pass
        # Never retain hidden chain-of-thought text from text-only providers.
        return re.sub(r'<think(?:ing)?>.*?</think(?:ing)?>', '[reasoning omitted]', value, flags=re.I | re.S)[:262144]
    return value if value is None or isinstance(value, (bool, int, float)) else str(value)


def _model_input(request):
    if not isinstance(request, dict):
        return None
    # Keep actual advisor API context but remove system/developer messages and
    # all provider-only headers/parameters. Their application source stays in Git.
    messages = []
    for message in request.get('messages', []):
        if not isinstance(message, dict) or message.get('role') not in {'user', 'assistant', 'tool'}:
            continue
        messages.append(clean({key: message[key] for key in ('role', 'content', 'tool_calls', 'tool_call_id', 'name') if key in message}))
    return {'messages': messages, 'tools': clean(request.get('tools', []))}


def _model_output(response, data):
    if isinstance(response, dict):
        selected = {key: response[key] for key in ('message', 'tool_calls', 'finish_reason') if key in response}
        if selected:
            return clean(selected)
    if isinstance(data, dict) and isinstance(data.get('choices'), list):
        return clean({'choices': [{k: c[k] for k in ('message', 'finish_reason') if k in c} for c in data['choices']]})
    return None


def convert(source):
    base = '|'.join(source[key] for key in ('scenario_id', 'run_id', 'condition_id', 'source'))
    spans, diagnostics, marks = [], [], []
    if source['source'] == 'native-relay':
        grouped = {}
        for event in source['events']:
            if event.get('scope_category') not in {'start', 'end'}:
                marks.append(event)
                continue
            key = (event.get('uuid'), event.get('category'))
            group = grouped.setdefault(key, {})
            phase = event['scope_category']
            if phase in group:
                raise ValueError('Duplicate historical Relay phase')
            group[phase] = event
        parent_map = {key[0]: (group.get('start') or group.get('end')) for key, group in grouped.items()}
        for (native_id, category), group in grouped.items():
            if set(group) != {'start', 'end'}:
                diagnostics.append({'native_id': native_id, 'status': 'incomplete', 'reason': 'Missing native scope phase'})
                continue
            start, end = group['start'], group['end']
            root = start.get('propagation_root_uuid')
            cursor, visited = start, set()
            while not root and cursor.get('parent_uuid') in parent_map and cursor['parent_uuid'] not in visited:
                visited.add(cursor['uuid'])
                cursor = parent_map[cursor['parent_uuid']]
                root = cursor.get('propagation_root_uuid')
            root = root or cursor['uuid']
            trace_context = base + '|' + root
            profile_start, profile_end = start.get('category_profile') or {}, end.get('category_profile') or {}
            metadata = {**(start.get('metadata') or {}), **(end.get('metadata') or {})}
            failed = str(metadata.get('otel.status_code', '')).upper() == 'ERROR' or isinstance(end.get('data'), dict) and end['data'].get('is_error') is True
            span = {'trace_id': mapped_id(base, root, 16), 'span_id': mapped_id(trace_context, native_id, 8),
                    'parent_span_id': mapped_id(trace_context, start['parent_uuid'], 8) if start.get('parent_uuid') else None,
                    'native_id': native_id, 'native_parent_id': start.get('parent_uuid'), 'native_trace_id': root,
                    'name': start.get('name', category), 'category': category,
                    'start_ns': nanos(start['timestamp']), 'end_ns': nanos(end['timestamp']),
                    'status': 'ERROR' if failed else 'OK', 'events': [], 'attributes': {}}
            attrs = span['attributes']
            attrs.update({'openinference.span.kind': {'agent': 'AGENT', 'llm': 'LLM', 'tool': 'TOOL'}.get(category, 'CHAIN'),
                          'citizen.native.uuid': native_id, 'citizen.native.parent_uuid': start.get('parent_uuid') or '',
                          'citizen.import.parent_missing': bool(start.get('parent_uuid') and start['parent_uuid'] not in parent_map)})
            for key in ('nemo_fabric_invocation_id', 'nemo_fabric_request_id', 'nemo_fabric_runtime_id', 'thread_id'):
                if isinstance(metadata.get(key), str):
                    attrs['citizen.native.' + key] = metadata[key]
            if category == 'llm':
                request, response = profile_start.get('annotated_request') or {}, profile_end.get('annotated_response') or {}
                span['input'] = _model_input(request)
                span['output'] = _model_output(response, end.get('data'))
                attrs['llm.model_name'] = response.get('model') or profile_end.get('model_name') or request.get('model') or profile_start.get('model_name') or 'unknown'
                usage = response.get('usage') or {}
                for native, attr in [('prompt_tokens', 'llm.token_count.prompt'), ('completion_tokens', 'llm.token_count.completion'), ('total_tokens', 'llm.token_count.total')]:
                    if isinstance(usage.get(native), int):
                        attrs[attr] = usage[native]
            elif category == 'tool':
                span['input'], span['output'] = clean(start.get('data')), clean(end.get('data'))
                attrs['tool.name'] = span['name']
            spans.append(span)
        lookup = {span['native_id']: span for span in spans}
        for event in marks:
            parent = lookup.get(event.get('parent_uuid'))
            if parent is None:
                diagnostics.append({'name': event.get('name'), 'status': 'unattached-mark', 'reason': 'Native parent was not captured'})
                continue
            # Stream chunks duplicate response content; keep the event identity
            # and timestamp, rather than duplicate private payload fragments.
            parent['events'].append({'name': event.get('name', 'native mark'), 'time_ns': nanos(event['timestamp']),
                                     'attributes': {'citizen.native.mark': True}})
    else:
        intake = source['intake']
        if intake.get('status') != 'observed' or intake.get('truncated'):
            raise ValueError('Managed Intake source is incomplete')
        rows = intake['spans']
        tools = {row['source_span_id']: row for row in intake.get('tools', [])}
        ids = {row['span_id'] for row in rows}
        for row in rows:
            trace_context = base + '|' + row['trace_id']
            # Intake exports naive UTC values. Its installed trace_ingest
            # loader applies timezone.utc to these same naive timestamps.
            started_at = row['started_at']
            ended_at = row.get('ended_at')
            start_ns = nanos(started_at + 'Z' if not re.search(r'Z|[+-]\d\d:\d\d$', started_at) else started_at)
            end_ns = (nanos(ended_at + 'Z' if not re.search(r'Z|[+-]\d\d:\d\d$', ended_at) else ended_at)
                      if ended_at else start_ns)
            attrs = {'openinference.span.kind': row['kind'], 'citizen.native.uuid': row['span_id'],
                     'citizen.native.parent_uuid': row.get('parent_span_id') or '',
                     'citizen.import.parent_missing': bool(row.get('parent_span_id') and row['parent_span_id'] not in ids),
                     'citizen.native.started_at': started_at, 'citizen.native.ended_at': ended_at or '',
                     'citizen.import.timezone': 'UTC per Intake loader convention',
                     'citizen.import.end_missing': not bool(ended_at)}
            if not ended_at:
                attrs['citizen.import.display_interval'] = 'zero-length marker; native end not captured; duration unknown'
                diagnostics.append({'native_id': row['span_id'], 'status': 'end-not-captured',
                                    'reason': 'Zero-length display marker; duration remains unknown'})
            if row.get('model'):
                attrs['llm.model_name'] = row['model']
            for native, attr in [('input_tokens', 'llm.token_count.prompt'), ('output_tokens', 'llm.token_count.completion'), ('total_tokens', 'llm.token_count.total')]:
                if isinstance(row.get(native), int):
                    attrs[attr] = row[native]
            tool = tools.get(row['span_id'], {})
            attrs['citizen.import.payload_coverage'] = 'verified tool facts' if tool else 'managed LLM payload not source-hash-bound'
            spans.append({'trace_id': mapped_id(base, row['trace_id'], 16), 'span_id': mapped_id(trace_context, row['span_id'], 8),
                          'parent_span_id': mapped_id(trace_context, row['parent_span_id'], 8) if row.get('parent_span_id') else None,
                          'native_id': row['span_id'], 'native_parent_id': row.get('parent_span_id'), 'native_trace_id': row['trace_id'],
                          'name': row['name'], 'category': row['kind'].lower(), 'start_ns': start_ns,
                          'end_ns': end_ns, 'status': 'UNSET' if not ended_at else 'ERROR' if row.get('status') in {'failed', 'error'} else 'OK',
                          'input': clean(tool.get('arguments')), 'output': clean(tool.get('result')), 'attributes': attrs, 'events': []})
    seen = set()
    for span in spans:
        if span['end_ns'] < span['start_ns'] or int(span['span_id'], 16) == 0 or int(span['trace_id'], 16) == 0:
            raise ValueError('Invalid historical span interval or identifier')
        identity = span['span_id']
        if identity in seen:
            raise ValueError('Historical span ID collision')
        seen.add(identity)
        span['attributes'].update({'citizen.scenario_id': source['scenario_id'], 'citizen.run_id': source['run_id'],
             'citizen.condition_id': source['condition_id'], 'citizen.condition_purpose': source['purpose'],
             'citizen.evidence_source': source['source'], 'citizen.import.historical': True,
             'citizen.import.source_sha256': source['source_sha256'], 'citizen.import.schema': NAMESPACE,
             # Phoenix's Python datetime storage has microsecond precision.
             # Original nanoseconds are retained verbatim for audit/export.
             'citizen.native.start_time_unix_nano': str(span['start_ns']),
             'citizen.native.end_time_unix_nano': '' if span['attributes'].get('citizen.import.end_missing') else str(span['end_ns'])})
    return {**{key: value for key, value in source.items() if key not in {'events', 'intake'}},
            'spans': spans, 'diagnostics': diagnostics, 'project_name': f"citizen-{source['scenario_id']}-{source['run_id'][:8]}-{source['purpose']}"}


def scan_secrets(value):
    """Fail closed without printing a credential or the matching payload."""
    serialized = json.dumps(value, ensure_ascii=False)
    if re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|(?:nvapi-|sk-proj-)[A-Za-z0-9_-]{18,}', serialized):
        raise ValueError('A possible credential was found in the historical projection; nothing was uploaded')
    for path in (ROOT / '.env', ROOT / '.private/v02-runtime.env'):
        if not path.is_file():
            continue
        for line in path.read_text().splitlines():
            if '=' not in line or line.lstrip().startswith('#'):
                continue
            key, secret = line.split('=', 1)
            secret = secret.strip().strip('"\'')
            if re.search('KEY|TOKEN|SECRET|PASSWORD', key, re.I) and len(secret) >= 8 and secret in serialized:
                raise ValueError('A configured credential was found in the historical projection; nothing was uploaded')


def protobuf(spans, project):
    from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
    from opentelemetry.proto.common.v1.common_pb2 import AnyValue, KeyValue, InstrumentationScope
    from opentelemetry.proto.resource.v1.resource_pb2 import Resource
    from opentelemetry.proto.trace.v1.trace_pb2 import ResourceSpans, ScopeSpans, Span, Status

    def attribute(key, value):
        field = 'bool_value' if isinstance(value, bool) else 'int_value' if isinstance(value, int) else 'double_value' if isinstance(value, float) else 'string_value'
        return KeyValue(key=key, value=AnyValue(**{field: value if field != 'string_value' or isinstance(value, str) else json.dumps(value, ensure_ascii=False)}))

    values = []
    for span in spans:
        attrs = dict(span['attributes'])
        for direction in ('input', 'output'):
            if span.get(direction) is not None:
                attrs[direction + '.value'] = json.dumps(span[direction], ensure_ascii=False)
                attrs[direction + '.mime_type'] = 'application/json'
        values.append(Span(trace_id=bytes.fromhex(span['trace_id']), span_id=bytes.fromhex(span['span_id']),
                           parent_span_id=bytes.fromhex(span['parent_span_id']) if span.get('parent_span_id') else b'',
                           name=span['name'], kind=Span.SPAN_KIND_INTERNAL,
                           start_time_unix_nano=span['start_ns'], end_time_unix_nano=span['end_ns'],
                           attributes=[attribute(k, v) for k, v in attrs.items()],
                           status=Status(code=Status.STATUS_CODE_ERROR if span['status'] == 'ERROR' else Status.STATUS_CODE_UNSET if span['status'] == 'UNSET' else Status.STATUS_CODE_OK),
                           events=[Span.Event(time_unix_nano=e['time_ns'], name=e['name'], attributes=[attribute(k, v) for k, v in e['attributes'].items()]) for e in span['events']]))
    request = ExportTraceServiceRequest(resource_spans=[ResourceSpans(
        resource=Resource(attributes=[attribute('service.name', 'citizen-lab-historical'), attribute('openinference.project.name', project)]),
        scope_spans=[ScopeSpans(scope=InstrumentationScope(name='citizen-lab-historical-import', version='0.3.0'), spans=values)])])
    return request.SerializeToString()


def query_spans(project):
    result, cursor = [], None
    while True:
        path = '/v1/projects/' + quote(project, safe='') + '/spans?limit=1000'
        if cursor:
            path += '&cursor=' + quote(cursor, safe='')
        try:
            _, body = _request(path)
        except HTTPError as exc:
            if exc.code == 404:
                return []
            raise
        value = json.loads(body)
        result.extend(value['data'])
        cursor = value.get('next_cursor')
        if not cursor:
            return result


def import_history():
    if not status()['running']:
        raise RuntimeError('Start the owned local Phoenix service explicitly before importing')
    converted = [convert(source) for source in sources()]
    scan_secrets(converted)
    conditions = []
    from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceResponse
    for value in converted:
        project, spans = value['project_name'], value['spans']
        old = {row['context']['span_id']: row for row in query_spans(project)}
        for span in spans:
            if span['span_id'] in old:
                found = old[span['span_id']]
                if found.get('attributes', {}).get('citizen.import.source_sha256') != value['source_sha256']:
                    raise ValueError('An existing Phoenix span has conflicting historical provenance')
        missing = [span for span in spans if span['span_id'] not in old]
        if missing:
            _, body = _request('/v1/traces', protobuf(missing, project), project)
            response = ExportTraceServiceResponse.FromString(body)
            if response.partial_success.rejected_spans:
                raise RuntimeError('Phoenix rejected historical spans; source files were preserved')
        deadline = time.monotonic() + 20
        while True:
            actual = query_spans(project)
            lookup = {row['context']['span_id']: row for row in actual}
            if all(span['span_id'] in lookup for span in spans):
                break
            if time.monotonic() >= deadline:
                raise RuntimeError('Historical import was not confirmed by a read-back; do not assume success')
            time.sleep(0.25)
        for span in spans:
            row = lookup[span['span_id']]
            expected_start = nanos(datetime.fromtimestamp(span['start_ns'] / 1e9, tz=timezone.utc).isoformat())
            expected_end = nanos(datetime.fromtimestamp(span['end_ns'] / 1e9, tz=timezone.utc).isoformat())
            if row['context']['trace_id'] != span['trace_id'] or nanos(row['start_time']) != expected_start or nanos(row['end_time']) != expected_end:
                raise ValueError('Historical trace identity/timestamp changed during ingestion')
            if (row.get('parent_id') != span.get('parent_span_id') or row.get('name') != span['name']
                    or row.get('status_code') != span['status']
                    or row.get('span_kind') != span['attributes']['openinference.span.kind']
                    or any(row['attributes'].get(key) != expected for key, expected in span['attributes'].items()
                           if key != 'openinference.span.kind')):
                raise ValueError('Historical parent, status or provenance changed during ingestion')
            for direction in ('input', 'output'):
                if span.get(direction) is not None and json.loads(row['attributes'].get(direction + '.value', 'null')) != span[direction]:
                    raise ValueError('Historical filtered input/output changed during ingestion')
        # Projects are created by OTLP ingestion. Resolve the actual GlobalID
        # rather than inventing a UI identifier from the project name.
        _, body = _request('/v1/projects?limit=1000')
        projects = json.loads(body)['data']
        project_id = next(row['id'] for row in projects if row['name'] == project)
        traces = sorted({row['trace_id'] for row in spans})
        conditions.append({**{k: value[k] for k in ('scenario_id', 'run_id', 'condition_id', 'purpose', 'source', 'source_sha256', 'source_path')},
                           'project_name': project, 'project_id': project_id,
                           'url': ENDPOINT + '/projects/' + quote(project_id, safe='') + '/traces',
                           'trace_urls': [ENDPOINT + '/projects/' + quote(project_id, safe='') + '/traces/' + trace for trace in traces],
                           'span_count': len(spans), 'trace_count': len(traces), 'new_spans': len(missing),
                           'diagnostics': value['diagnostics'], 'id_mapping': [{k: span.get(k) for k in ('native_id', 'native_parent_id', 'native_trace_id', 'trace_id', 'span_id', 'parent_span_id')} for span in spans]})
    receipt = {'schema': 'citizen-phoenix-import/v1', 'status': 'verified', 'version': '22.1.0',
               'imported_at': datetime.now(timezone.utc).isoformat(), 'inference_calls': 0,
               'span_count': sum(row['span_count'] for row in conditions),
               'trace_count': sum(row['trace_count'] for row in conditions),
               'notice': 'Historical records only. Native nanoseconds are retained as attributes; Phoenix displays microseconds. Six managed records have unknown ends and use explicit zero-length display markers.',
               'conditions': conditions}
    write_json(STATE / 'import-receipt.json', receipt)
    return {key: receipt[key] for key in ('schema', 'status', 'version', 'span_count', 'trace_count', 'inference_calls')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['start', 'status', 'import', 'stop', 'inspect'])
    action = parser.parse_args().action
    if action == 'inspect':
        converted = [convert(source) for source in sources()]
        scan_secrets(converted)
        result = {'conditions': len(converted), 'spans': sum(len(row['spans']) for row in converted),
                  'traces': sum(len({span['trace_id'] for span in row['spans']}) for row in converted),
                  'inference_calls': 0}
    else:
        result = {'start': start, 'status': status, 'import': import_history, 'stop': stop}[action]()
    print(json.dumps(result))


if __name__ == '__main__':
    main()
