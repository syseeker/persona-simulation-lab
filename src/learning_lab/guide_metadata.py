"""File-only Metadata over the selected demo's immutable public capture pack.

Private originals are represented by opaque references. This reader never opens
run folders, reconstructs missing captures or initializes an execution service.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from urllib.parse import quote

from .captures import REGISTRY, REQUIREMENTS, RULES
from .guide_sources import _git, repository_url
from .settings import ROOT

PACKS = ROOT / 'recordings/captures'
HASH = re.compile(r'[a-f0-9]{64}')
ARTIFACT_ID = re.compile(r'[a-f0-9]{24}')
IDENTITY = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}')
AVAILABILITY = {'exists', 'missing', 'not-used', 'unavailable'}
SOURCE_ROLES = {spec.role for spec in RULES.values()}
MAX_MANIFEST_BYTES = 4 * 1024 * 1024
MAX_ARTIFACT_BYTES = 64 * 1024 * 1024


def _identity(value):
    if not isinstance(value, str) or not IDENTITY.fullmatch(value) or value in {'.', '..'}:
        raise ValueError('Invalid published capture identity')
    return value


def _safe_path(folder: Path, name: str) -> Path:
    if not isinstance(name, str) or len(name) > 600 or '\\' in name:
        raise ValueError('Invalid published capture path')
    relative = PurePosixPath(name)
    if (relative.is_absolute() or relative.as_posix() != name or not relative.parts
            or any(not IDENTITY.fullmatch(part) or part in {'.', '..'} for part in relative.parts)):
        raise ValueError('Invalid published capture path')
    path = folder.joinpath(*relative.parts)
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError('Symbolic published capture paths are not accepted')
    return path


def _digest(path: Path) -> str:
    if not path.is_file() or path.stat().st_size > MAX_ARTIFACT_BYTES:
        raise ValueError('Published capture is missing or exceeds its size bound')
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def _public_url(path: Path, digest: str, repository: str | None, revision: str | None) -> str | None:
    """Only link a committed blob whose exact bytes match this publication."""
    if not repository or not revision or not re.fullmatch(r'[a-f0-9]{40,64}', revision):
        return None
    try:
        relative = path.relative_to(ROOT).as_posix()
        committed = subprocess.check_output(['git', 'show', f'{revision}:{relative}'],
            cwd=ROOT, stderr=subprocess.DEVNULL, timeout=3)
    except (ValueError, OSError, subprocess.SubprocessError):
        return None
    if hashlib.sha256(committed).hexdigest() != digest:
        return None
    return f'{repository}/blob/{revision}/{quote(relative)}'


def _filenames(requirement_id, artifacts):
    names = {PurePosixPath(pattern).name for group in RULES[requirement_id].groups for pattern in group}
    for artifact in artifacts:
        if artifact.get('path'):
            # Publication filenames have an opaque prefix; retain the actual suffix.
            names.add(re.sub(r'^[a-f0-9]{24}-', '', PurePosixPath(artifact['path']).name))
    return sorted(names)


def _unavailable(scenario_id, run_id):
    rows = []
    for requirement in REQUIREMENTS.values():
        applies = scenario_id in requirement['scenario_ids']
        rows.append({'id': requirement['id'], 'module': requirement['module'],
            'steps': requirement['lessons'], 'operation': requirement['operation'],
            'scenario_ids': requirement['scenario_ids'], 'filenames': _filenames(requirement['id'], []),
            'status': 'unavailable' if applies else 'not-used', 'privacy': 'unknown',
            'condition_id': None, 'condition_purpose': None, 'execution_status': 'unavailable',
            'artifacts': []})
    return {'schema': 'citizen-guide-metadata/v1', 'scenario_id': scenario_id, 'run_id': run_id,
        'available': False, 'inference_calls_for_inspection': 0, 'conditions': [], 'rows': rows,
        'notice': 'The selected demo has no published capture inventory. Its private capture status is unknown; no other run was substituted.'}


def metadata(scenario_id='photography') -> dict:
    """Resolve registry requirements against one tagged scenario/run publication."""
    from .guide_lessons import _scenario

    run_id = _scenario(scenario_id)
    if run_id is None:
        return _unavailable(scenario_id, None)
    _identity(run_id)
    folder = PACKS / scenario_id / run_id
    manifest_path = _safe_path(folder, 'manifest.json')
    if not manifest_path.exists():
        return _unavailable(scenario_id, run_id)
    if not manifest_path.is_file() or manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
        raise ValueError('Invalid published capture manifest')
    manifest = json.loads(manifest_path.read_text())
    if (not isinstance(manifest, dict) or manifest.get('schema') != 'citizen-public-captures/v1'
            or manifest.get('registry_schema') != REGISTRY['schema']
            or manifest.get('scenario_id') != scenario_id or manifest.get('run_id') != run_id
            or not isinstance(manifest.get('source_manifest_sha256'), str)
            or not HASH.fullmatch(manifest['source_manifest_sha256'])):
        raise ValueError('Capture manifest does not match the selected scenario/run')
    files, source_rows = manifest.get('files'), manifest.get('rows')
    if (not isinstance(files, dict) or len(files) > 4096 or not isinstance(source_rows, list)
            or len(source_rows) > len(REQUIREMENTS) * 64):
        raise ValueError('Invalid published capture inventory')
    checked_files = {}
    for name, digest in files.items():
        parts = PurePosixPath(name).parts if isinstance(name, str) else ()
        if (len(parts) != 3 or parts[0] not in {'baseline', 'comparisons', 'managed'}
                or PurePosixPath(name).suffix not in {'.json', '.jsonl', '.yaml', '.yml'}
                or not isinstance(digest, str) or not HASH.fullmatch(digest)):
            raise ValueError('Invalid published capture file binding')
        _identity(parts[1])
        path = _safe_path(folder, name)
        if _digest(path) != digest:
            raise ValueError('Published capture integrity check failed')
        checked_files[name] = path

    repository, revision = repository_url(), _git('rev-parse', 'HEAD') or None
    rows, conditions, seen, referenced, links = [], {}, set(), set(), {}
    for source_row in source_rows:
        if not isinstance(source_row, dict) or source_row.get('id') not in REQUIREMENTS:
            raise ValueError('Unknown published capture requirement')
        rid = source_row['id']
        condition_id, purpose = source_row.get('condition_id'), source_row.get('purpose')
        status, execution = source_row.get('availability'), source_row.get('execution_status')
        if (source_row.get('scenario_id') != scenario_id or source_row.get('run_id') != run_id
                or status not in AVAILABILITY or not isinstance(purpose, str) or not IDENTITY.fullmatch(purpose)
                or not isinstance(execution, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,79}', execution)
                or (scenario_id not in REQUIREMENTS[rid]['scenario_ids'] and status != 'not-used')):
            raise ValueError('Published capture row has inconsistent identity or status')
        if condition_id is not None:
            _identity(condition_id)
        elif status != 'not-used':
            raise ValueError('Applicable capture row has no condition identity')
        key = (rid, condition_id)
        if key in seen:
            raise ValueError('Duplicate published requirement/condition binding')
        seen.add(key)
        if condition_id is not None:
            context = {'id': condition_id, 'purpose': purpose, 'execution_status': execution}
            if condition_id in conditions and conditions[condition_id] != context:
                raise ValueError('Published condition identity has conflicting metadata')
            conditions[condition_id] = context
        source_artifacts = source_row.get('artifacts')
        if not isinstance(source_artifacts, list):
            raise ValueError('Invalid published artifact references')
        if status == 'exists' and not source_artifacts:
            raise ValueError('Existing capture requirement has no retained artifact')
        private, artifacts, artifact_ids = {}, [], set()
        for artifact in source_artifacts:
            if (not isinstance(artifact, dict) or not isinstance(artifact.get('id'), str)
                    or not ARTIFACT_ID.fullmatch(artifact['id']) or not isinstance(artifact.get('sha256'), str)
                    or not HASH.fullmatch(artifact['sha256'])
                    or artifact.get('access') not in {'private', 'public'}):
                raise ValueError('Invalid published artifact identity')
            if artifact['id'] in artifact_ids:
                raise ValueError('Duplicate published artifact reference')
            artifact_ids.add(artifact['id'])
            if artifact['access'] == 'private':
                if 'location' in artifact or 'path' in artifact or 'url' in artifact:
                    raise ValueError('Private capture locations cannot be published')
                if artifact.get('role') not in SOURCE_ROLES:
                    raise ValueError('Unknown private capture role')
                private[artifact['id']] = artifact
        for artifact in source_artifacts:
            identity, digest = artifact['id'], artifact['sha256']
            if artifact['access'] == 'private':
                artifacts.append({'id': identity, 'sha256': digest, 'privacy': 'private',
                    'status': 'exists', 'kind': artifact.get('role', 'native-capture')})
                continue
            name = artifact.get('location')
            source_ids = artifact.get('source_artifact_ids')
            phase = 'baseline' if purpose == 'baseline' else 'managed' if purpose == 'managed' else 'comparisons'
            if (not isinstance(name, str) or name not in checked_files or files[name] != digest
                    or PurePosixPath(name).parts[:2] != (phase, condition_id)
                    or not isinstance(source_ids, list) or not source_ids
                    or any(not isinstance(source_id, str) for source_id in source_ids)
                    or any(source_id not in private for source_id in source_ids)
                    or artifact.get('source_role') not in SOURCE_ROLES
                    or any(private[source_id]['sha256'] != artifact.get('source_sha256') for source_id in source_ids)):
                raise ValueError('Published artifact does not match its condition/source binding')
            referenced.add(name)
            if name not in links:
                links[name] = _public_url(checked_files[name], digest, repository, revision)
            kind = artifact.get('role', 'application-projection')
            if kind not in {'application-projection', 'redacted-native-configuration'}:
                raise ValueError('Unknown public capture publication kind')
            artifacts.append({'id': identity, 'path': name, 'url': links[name], 'kind': kind,
                'source_kind': artifact.get('source_role'), 'sha256': digest,
                'privacy': 'projection' if kind == 'application-projection' else 'public',
                'status': 'exists', 'link_status': 'committed' if links[name] else 'not-committed'})
        public = [artifact for artifact in artifacts if artifact['privacy'] != 'private']
        if status == 'not-used' and artifacts:
            raise ValueError('Unused capture requirement cannot claim retained artifacts')
        requirement = REQUIREMENTS[rid]
        rows.append({'id': rid, 'module': requirement['module'], 'steps': requirement['lessons'],
            'operation': requirement['operation'], 'scenario_ids': requirement['scenario_ids'],
            'filenames': _filenames(rid, artifacts), 'status': status,
            'privacy': ('projection' if any(a['privacy'] == 'projection' for a in public)
                        else 'public' if public else 'private' if artifacts else 'unknown'),
            'condition_id': condition_id, 'condition_purpose': purpose, 'execution_status': execution,
            'artifacts': artifacts})
    if {row['id'] for row in rows} != set(REQUIREMENTS) or referenced != set(files):
        raise ValueError('Published inventory has missing requirements or unbound files')
    return {'schema': 'citizen-guide-metadata/v1', 'scenario_id': scenario_id, 'run_id': run_id,
        'available': True, 'inference_calls_for_inspection': 0, 'rows': rows,
        'conditions': list(conditions.values()),
        'notice': 'Each row describes the selected demo and condition. Capture availability, public access and condition execution are separate; a retained error is evidence of a failed operation.'}
