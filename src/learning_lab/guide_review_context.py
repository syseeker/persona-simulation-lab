"""Read-only, hash-bound supplements to immutable scenario capture packs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import quote

from .guide_sources import _git, repository_url
from .settings import ROOT

SCHEMA = 'citizen-review-context/v1'
FILES = {'managed-client-config.json': 'CAP-PLAT-01', 'managed-agent-config.json': 'CAP-PLAT-02'}
HASH = re.compile(r'[a-f0-9]{64}')
IDENTITY = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}')


def companion(scenario_id: str, run_id: str, *, root: Path = ROOT) -> dict:
    for value in (scenario_id, run_id):
        if not isinstance(value, str) or not IDENTITY.fullmatch(value) or value in {'.', '..'}:
            raise ValueError('Invalid review-context identity')
    folder = root / 'recordings/review-context' / scenario_id / run_id
    manifest_path = folder / 'manifest.json'
    if not manifest_path.exists():
        return {'available': False, 'data': {}, 'artifacts': []}
    if any(p.is_symlink() for p in (manifest_path, *manifest_path.parents)):
        raise ValueError('Symbolic review-context paths are not accepted')
    if manifest_path.stat().st_size > 128 * 1024:
        raise ValueError('Review-context manifest exceeds its bound')
    manifest = json.loads(manifest_path.read_text())
    native_manifest = root / 'recordings' / scenario_id / run_id / 'manifest.json'
    capture_manifest = root / 'recordings/captures' / scenario_id / run_id / 'manifest.json'
    if (manifest.get('schema') != SCHEMA or manifest.get('scenario_id') != scenario_id
            or manifest.get('run_id') != run_id or not native_manifest.is_file() or not capture_manifest.is_file()
            or any(p.is_symlink() for p in (native_manifest, capture_manifest))
            or manifest.get('recording_manifest_sha256') != hashlib.sha256(native_manifest.read_bytes()).hexdigest()
            or manifest.get('capture_manifest_sha256') != hashlib.sha256(capture_manifest.read_bytes()).hexdigest()
            or not isinstance(manifest.get('files'), dict) or set(manifest['files']) != set(FILES)):
        raise ValueError('Review context does not match the selected recording and capture pack')
    captures = json.loads(capture_manifest.read_text())
    recording = json.loads(native_manifest.read_text())
    repository, revision = repository_url(), _git('rev-parse', 'HEAD')
    data, artifacts = {}, []
    for name, binding in manifest['files'].items():
        if not isinstance(binding, dict) or binding.get('requirement_id') != FILES[name]:
            raise ValueError('Invalid review-context artifact binding')
        condition = binding.get('condition_id')
        rows = [r for r in captures.get('rows', []) if r.get('id') == FILES[name]
                and r.get('condition_id') == condition and r.get('purpose') == 'managed']
        original = [a for r in rows for a in r.get('artifacts', []) if a.get('access') == 'private'
                    and a.get('id') == binding.get('source_artifact_id')
                    and a.get('sha256') == binding.get('source_sha256')]
        if len(original) != 1 or not HASH.fullmatch(binding.get('sha256', '')):
            raise ValueError('Review-context artifact does not match its captured source')
        secondary = binding.get('secondary_source_sha256')
        expected_secondary = ({'platform-deployment.json': recording.get('files', {}).get('platform-deployment.json')}
                              if name == 'managed-agent-config.json' else {})
        if secondary != expected_secondary:
            raise ValueError('Review-context secondary source binding does not match the recording')
        for secondary_name, digest in secondary.items():
            source = native_manifest.parent / secondary_name
            if (not isinstance(digest, str) or not HASH.fullmatch(digest)
                    or any(p.is_symlink() for p in (source, *source.parents))
                    or not source.is_file() or source.stat().st_size > 1024 * 1024
                    or hashlib.sha256(source.read_bytes()).hexdigest() != digest):
                raise ValueError('Review-context secondary source changed after recording')
        path = folder / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 256 * 1024:
            raise ValueError('Review-context artifact is unavailable or exceeds its bound')
        if hashlib.sha256(path.read_bytes()).hexdigest() != binding['sha256']:
            raise ValueError('Review-context artifact integrity check failed')
        value = json.loads(path.read_text())
        if (value.get('scenario_id') != scenario_id or value.get('run_id') != run_id
                or value.get('condition_id') != condition or value.get('source_sha256') != binding['source_sha256']
                or value.get('secondary_source_sha256') != secondary):
            raise ValueError('Review-context content has inconsistent provenance')
        relative = path.relative_to(root).as_posix()
        url = None
        if repository and revision and re.fullmatch(r'[a-f0-9]{40,64}', revision):
            try:
                committed = subprocess.check_output(['git', 'show', f'{revision}:{relative}'],
                    cwd=root, stderr=subprocess.DEVNULL, timeout=3)
                if hashlib.sha256(committed).hexdigest() == binding['sha256']:
                    url = f'{repository}/blob/{revision}/{quote(relative)}'
            except (OSError, subprocess.SubprocessError):
                pass
        data[name] = value
        artifacts.append({'id': hashlib.sha256(relative.encode()).hexdigest()[:24], 'path': name,
            'sha256': binding['sha256'], 'url': url, 'kind': 'application-projection',
            'source_kind': original[0].get('role'), 'source_schema': original[0].get('schema'),
            'condition_id': condition, 'requirement_id': FILES[name], 'privacy': 'projection',
            'status': 'exists', 'link_status': 'committed' if url else 'not-committed'})
    return {'available': True, 'data': data, 'artifacts': artifacts}
