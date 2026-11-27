"""Publish two missing managed-configuration views from an existing saved run.

This is offline publication only. Existing recordings/capture packs and private
originals are never edited; an existing supplement destination is refused.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

import yaml

from learning_lab.guide_review_context import FILES, SCHEMA
from learning_lab.settings import ROOT


def _read(path: Path, expected_sha256: str | None = None):
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise ValueError('Expected a bounded, regular captured source')
    body = path.read_bytes()
    if expected_sha256 is not None and hashlib.sha256(body).hexdigest() != expected_sha256:
        raise ValueError('Captured source does not match its immutable recording hash')
    return yaml.safe_load(body.decode()) if path.suffix == '.yaml' else json.loads(body)


def _pick(value, keys):
    return {k: value[k] for k in keys if k in value} if isinstance(value, dict) else {}


def export(run_id: str, *, root: Path = ROOT, run_root: Path | None = None) -> Path:
    if not re.fullmatch(r'[a-f0-9-]{36}', run_id):
        raise ValueError('Select one existing canonical run identity')
    original = (run_root or root / 'runs/journeys') / run_id
    state = _read(original / 'run.json')
    scenario = state['scenario_id']
    if scenario != 'dreamjob' or state.get('status') != 'completed':
        raise ValueError('This supplement requires the completed retail recording')
    private_manifest = _read(original / 'capture-manifest.json')
    native_folder = root / 'recordings' / scenario / run_id
    captures_folder = root / 'recordings/captures' / scenario / run_id
    public_manifest = _read(captures_folder / 'manifest.json')
    if (public_manifest.get('run_id') != run_id or public_manifest.get('scenario_id') != scenario
            or public_manifest.get('source_manifest_sha256') != hashlib.sha256((original / 'capture-manifest.json').read_bytes()).hexdigest()):
        raise ValueError('Existing capture publication does not match this saved source')
    target = root / 'recordings/review-context' / scenario / run_id
    if target.exists() or any(p.is_symlink() for p in (target, *target.parents)):
        raise ValueError('Supplement publication is immutable; destination must be new and nonsymbolic')
    recording = _read(native_folder / 'manifest.json')
    if (recording.get('schema') != 'citizen-recording/v1' or recording.get('run_id') != run_id
            or recording.get('scenario_id') != scenario):
        raise ValueError('Recording manifest does not match the selected scenario and run')
    deployment_sha256 = (recording.get('files') or {}).get('platform-deployment.json')
    if not isinstance(deployment_sha256, str) or not re.fullmatch('[a-f0-9]{64}', deployment_sha256):
        raise ValueError('Managed deployment has no immutable recording file binding')
    deployment = _read(native_folder / 'platform-deployment.json', deployment_sha256)
    payloads, bindings = {}, {}
    for name, requirement in FILES.items():
        rows = [r for r in private_manifest['rows'] if r['id'] == requirement and r['purpose'] == 'managed']
        if len(rows) != 1:
            raise ValueError('Expected one managed source for the selected requirement')
        row = rows[0]
        source_name = 'platform-effective-config.json' if requirement == 'CAP-PLAT-01' else 'agent.yaml'
        sources = [a for a in row['artifacts'] if Path(a['location']).name == source_name]
        if len(sources) != 1:
            raise ValueError('Managed source capture is missing or ambiguous')
        source = sources[0]
        relative = Path(source['location'])
        if relative.is_absolute() or '..' in relative.parts or any((original / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)):
            raise ValueError('Unsafe managed source capture location')
        path = original / relative
        raw = _read(path, source['sha256'])
        public_rows = [r for r in public_manifest['rows'] if r['id'] == requirement and r['condition_id'] == row['condition_id']]
        if len(public_rows) != 1 or not any(a.get('id') == source['id'] and a.get('sha256') == source['sha256']
                and a.get('access') == 'private' for a in public_rows[0]['artifacts']):
            raise ValueError('Managed source is not bound to the immutable public capture pack')
        if requirement == 'CAP-PLAT-01':
            client = _pick(raw.get('client'), ['base_url', 'workspace', 'target', 'authentication_configured', 'max_retries', 'timeout_seconds', 'sdk_versions'])
            server = raw.get('server_executor') or {}
            settings = server.get('settings') or {}
            selected = settings.get('agents', {}).get('deployments', {}).get('openshell_executor')
            executors = [item for item in settings.get('deployments', {}).get('executors', []) if item.get('name') == selected]
            if not client or len(executors) != 1:
                raise ValueError('Saved client or selected executor settings are unavailable')
            executor = executors[0]
            configuration = {'client': client, 'selected_executor': {'name': executor.get('name'), 'backend': executor.get('backend'),
                'config': _pick(executor.get('config'), ['gateway_endpoint', 'platform_egress', 'serve_workdir', 'landlock_compatibility']),
                'tls_configured': bool(executor.get('config', {}).get('tls'))},
                'executor_configuration_sha256': server.get('source_sha256'),
                'scope': server.get('scope'), 'private_connection_material_published': False}
        else:
            # Publish instructions only if they are already present verbatim in
            # the reviewed public deployment record. Never publish simulator prompts.
            registered = deployment.get('deployment', {}).get('config', {})
            instructions = raw.get('instructions') or {}
            reviewed = registered.get('instructions') or {}
            if (not instructions or set(instructions) != set(reviewed)
                    or any(not isinstance(item, dict) or item.get('content') != reviewed[key].get('content')
                           for key, item in instructions.items())):
                raise ValueError('Agent instructions are not the already reviewed public application instructions')
            configuration = _pick(raw, ['config_format', 'name', 'description', 'default_harness', 'harnesses',
                'models', 'instructions', 'skills', 'mcp', 'tools', 'runtime', 'environment', 'telemetry'])
            # The registered public form supplies only the allowlisted model and
            # MCP/environment fields and has already omitted secret material.
            for key in ['models', 'mcp', 'environment', 'telemetry']:
                configuration[key] = registered.get(key, {})
        secondary = {'platform-deployment.json': deployment_sha256} if requirement == 'CAP-PLAT-02' else {}
        payload = {'schema': 'citizen-managed-configuration-review/v1', 'scenario_id': scenario, 'run_id': run_id,
            'condition_id': row['condition_id'], 'source_sha256': source['sha256'],
            'secondary_source_sha256': secondary,
            'representation': 'Sanitized configuration capture; omitted private connection material must be supplied locally.',
            'configuration': configuration}
        body = json.dumps(payload, indent=2, ensure_ascii=False) + '\n'
        if re.search(r'-----BEGIN .*PRIVATE KEY-----|\b(?:nvapi-[A-Za-z0-9_-]{12,}|sk-[A-Za-z0-9_-]{24,})\b', body):
            raise ValueError('Refuse credential-shaped supplement content')
        payloads[name] = body
        bindings[name] = {'requirement_id': requirement, 'condition_id': row['condition_id'],
            'sha256': hashlib.sha256(body.encode()).hexdigest(), 'source_artifact_id': source['id'],
            'source_sha256': source['sha256'], 'secondary_source_sha256': secondary}
    manifest = {'schema': SCHEMA, 'scenario_id': scenario, 'run_id': run_id,
        'recording_manifest_sha256': hashlib.sha256((native_folder / 'manifest.json').read_bytes()).hexdigest(),
        'capture_manifest_sha256': hashlib.sha256((captures_folder / 'manifest.json').read_bytes()).hexdigest(), 'files': bindings,
        'notice': 'Offline supplement from unchanged same-run captures. No model, agent, evaluation or deployment was executed.'}
    target.mkdir(parents=True)
    for name, body in payloads.items():
        (target / name).write_text(body)
    (target / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_id')
    args = parser.parse_args()
    print(export(args.run_id))
