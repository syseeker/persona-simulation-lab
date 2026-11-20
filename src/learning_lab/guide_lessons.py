"""Read-only teaching context, bound to one reviewed recording per scenario.

This module never creates an execution service, samples a replacement persona,
checks remote readiness or reads arbitrary run paths supplied by the browser.
"""
from __future__ import annotations

import hashlib
import json
import re
from urllib.parse import quote

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as pads

from . import recordings
from .datasets import DatasetQuery, _dataset, profile_hash
from .guide_sources import _git, operation_links, repository_url
from .settings import ROOT

CANONICAL_DEMOS = {'photography': '7863c607-cb99-4a31-b60c-381bf2099f0e',
                   'boardgames': '938bdb3f-568e-442e-889f-fed046edf5a0',
                   'dreamjob': '8542330d-d6df-494e-8509-d81a5841d69e'}
CONTEXT_ROOT = ROOT / 'recordings/guide-context'
INDEX_PATH = ROOT / '.private/cache/guide-original-index.json'


def _scenario(scenario_id):
    if scenario_id not in CANONICAL_DEMOS:
        raise ValueError('Unknown teaching scenario')
    return CANONICAL_DEMOS[scenario_id]


def companion(scenario_id: str, run_id: str) -> dict:
    """Verify the companion and its relationship to the unchanged native pack."""
    folder = CONTEXT_ROOT / scenario_id / run_id
    manifest = folder / 'manifest.json'
    if not manifest.is_file():
        return {'available': False, 'data': {}, 'artifacts': [],
                'notice': 'Additional configuration and lifecycle context was not published.'}
    if any(p.is_symlink() for p in (CONTEXT_ROOT, folder.parent, folder, manifest)):
        raise ValueError('Symbolic teaching-context paths are not accepted')
    value = json.loads(manifest.read_text())
    native_manifest = recordings.pack_folder(run_id) / 'manifest.json'
    if (value.get('schema') != 'citizen-guide-context/v1'
            or value.get('scenario_id') != scenario_id or value.get('run_id') != run_id
            or value.get('recording_manifest_sha256') != hashlib.sha256(native_manifest.read_bytes()).hexdigest()):
        raise ValueError('Teaching context does not match the selected recording')
    relative = folder.relative_to(ROOT).as_posix()
    revision = _git('log', '-1', '--format=%H', '--', relative)
    repository = repository_url()
    data, artifacts = {}, []
    for name, digest in value.get('files', {}).items():
        if not re.fullmatch(r'[a-z][a-z0-9-]*\.(?:json|jsonl)', name) or not re.fullmatch(r'[a-f0-9]{64}', digest):
            raise ValueError('Invalid teaching-context file identifier')
        path = folder / name
        if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Teaching-context integrity check failed: ' + name)
        data[name] = (json.loads(path.read_text()) if path.suffix == '.json'
                      else [json.loads(line) for line in path.read_text().splitlines() if line.strip()])
        artifacts.append({'path': name, 'sha256': digest, 'kind': 'recorded-companion',
                          'url': f'{repository}/blob/{revision}/{quote(relative)}/{name}' if repository and revision else None})
    return {'available': True, 'data': data, 'artifacts': artifacts,
            'notice': value['projection_notice'], 'source_hashes': value.get('source_hashes', {})}


def lesson_context(scenario_id='photography') -> dict:
    run_id = _scenario(scenario_id)
    result = {'schema': 'citizen-lessons/v1', 'scenario_id': scenario_id, 'run_id': run_id,
              'state': 'planned', 'trace': None, 'context': {}, 'artifacts': [],
              'inference_calls_for_inspection': 0}
    hashes = {}
    if run_id:
        # No fallback to another run, private history or another scenario.
        trace = recordings.trace(run_id)
        if trace is None:
            result.update(state='unavailable', notice='The tagged demo recording is unavailable. No other recording was substituted.')
        else:
            extra = companion(scenario_id, run_id)
            hashes = extra.get('source_hashes', {})
            context = dict(extra['data'])
            for name in ['fabric-plan.json', 'fabric-doctor.json', 'effective-policy.json',
                         'boundary-probes.json', 'cleanup.json', 'runtime-receipt.json',
                         'guardrails-config.json', 'guardrails-probe.json',
                         'designer-configuration.json', 'designer-output.json', 'designer-generation.json', 'designer-lineage.json',
                         'helix-criteria.json', 'helix-evaluation.json', 'helix-job.json',
                         'routing-configuration.json', 'routing-comparison.json',
                         'platform-package.json', 'platform-registration.json', 'platform-deployment.json',
                         'platform-session.json', 'platform-invocation.json', 'platform-condition.json',
                         'platform-cleanup.json', 'platform-boundary-probes.json', 'platform-effective-policy.json', 'platform-trace.json']:
                if name in recordings.load(run_id)['files']:
                    context[name] = json.loads(recordings.read(run_id, name))
            if 'guardrails-decisions.jsonl' in recordings.load(run_id)['files']:
                context['guardrails-decisions.jsonl'] = [json.loads(line) for line in
                    recordings.read(run_id, 'guardrails-decisions.jsonl').splitlines() if line.strip()]
            for name in ['public-constraints.jsonl', 'disclosure-audit.jsonl']:
                if name in recordings.load(run_id)['files']:
                    context[name] = [json.loads(line) for line in recordings.read(run_id, name).splitlines() if line.strip()]
            result.update(state='recorded', trace=trace, context=context,
                          artifacts=trace['artifacts'] + extra['artifacts'],
                          notice=extra['notice'])
    else:
        result['notice'] = 'Planned scenario: no conversation, native decisions or execution logs have been recorded.'
    result['sources'] = operation_links(hashes)
    return result


def resolve_original(source: str, revision: str, digest: str) -> dict:
    """Find the exact original by content hash, using a verified local ID hint.

    The optional index stores only a hash-to-ID hint, outside Git. Every hit is
    read from the current source and hashed again. Missing data never samples a
    replacement. Neither source rows nor their display fields enter the index.
    """
    if source not in {'ngc', 'hf-profile-only'} or not re.fullmatch(r'[a-f0-9]{64}', digest or ''):
        raise ValueError('Invalid original-profile reference')
    try:
        dataset, _, meta = _dataset(DatasetQuery(source=source))
    except (ValueError, OSError) as error:
        return {'available': False, 'notice': str(error)}
    if meta['revision'] != revision:
        return {'available': False, 'notice': 'The installed distribution revision differs from this recording. No profile was substituted.'}
    identity = source + ':' + revision + ':' + digest
    index = {}
    if INDEX_PATH.is_file() and not INDEX_PATH.is_symlink():
        try:
            index = json.loads(INDEX_PATH.read_text())
            if not isinstance(index, dict):
                index = {}
        except (OSError, ValueError):
            pass
    row = None
    hint = index.get(identity)
    if isinstance(hint, str) and len(hint) < 200:
        candidates = dataset.to_table(filter=pc.is_in(pads.field('uuid'), value_set=pa.array([hint]))).to_pylist()
        row = next((candidate for candidate in candidates if profile_hash(candidate) == digest), None)
    if row is None:
        for batch in dataset.to_batches(batch_size=512):
            row = next((candidate for candidate in batch.to_pylist() if profile_hash(candidate) == digest), None)
            if row is not None:
                break
    if row is None:
        return {'available': False, 'notice': 'No original row matches the recorded hash in this distribution and revision. No profile was substituted.'}
    index[identity] = str(row['uuid'])
    # A disposable cache cannot make source inspection fail or alter the source.
    try:
        if not INDEX_PATH.is_symlink() and not any(p.is_symlink() for p in INDEX_PATH.parents if p.is_relative_to(ROOT)):
            INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
            INDEX_PATH.write_text(json.dumps(index))
    except OSError:
        pass
    fields = []
    for key, label in [('age', 'Age'), ('sex', 'Sex'), ('district', 'District'), ('occupation', 'Occupation'),
                       ('education_level', 'Education'), ('skills_and_expertise', 'Skills'),
                       ('hobbies_and_interests', 'Interests'), ('career_goals_and_ambitions', 'Learning and career interests')]:
        value = row.get(key)
        if value is not None:
            fields.append({'key': key, 'label': label, 'value': value})
    traits = []
    for key in ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']:
        value = row.get(key)
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except ValueError:
                value = {'label': value}
        if isinstance(value, dict):
            traits.append({'name': key, 'label': value.get('label'), 'description': value.get('description')})
    name = ' '.join(str(row[k]) for k in ['first_name', 'middle_name', 'last_name'] if row.get(k))
    return {'available': True, 'name': name or 'Selected original synthetic profile', 'fields': fields, 'traits': traits,
            'source': source, 'revision': revision, 'original_sha256': digest,
            'notice': 'Exact original matched against the recorded SHA-256. Synthetic test data, not a real resident.'}


def demo_persona(scenario_id='photography') -> dict:
    run_id = _scenario(scenario_id)
    if not run_id:
        return {'available': False, 'notice': 'This scenario has no recorded persona selection yet.'}
    if recordings.load(run_id) is None:
        return {'available': False, 'notice': 'The tagged demo recording is unavailable.'}
    lock = json.loads(recordings.read(run_id, 'source-lock.json'))
    return resolve_original(lock['source'], lock['source_revision'], lock['original_sha256'])
