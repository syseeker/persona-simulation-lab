"""Metadata resolves only verified public captures belonging to the tagged demo."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import uuid

import pytest

from learning_lab import guide_lessons, guide_metadata as guide
from learning_lab.captures import REGISTRY, REQUIREMENTS
from learning_lab.journey import JourneyService


def digest(value):
    return hashlib.sha256(value).hexdigest()


@pytest.fixture
def pack(tmp_path, monkeypatch):
    run_id, condition_id = str(uuid.uuid4()), str(uuid.uuid4())
    monkeypatch.setattr(guide, 'ROOT', tmp_path)
    monkeypatch.setattr(guide, 'PACKS', tmp_path / 'recordings/captures')
    monkeypatch.setitem(guide_lessons.CANONICAL_DEMOS, 'photography', run_id)
    monkeypatch.setattr(guide, '_public_url', lambda *_args: None)
    folder = guide.PACKS / 'photography' / run_id
    folder.mkdir(parents=True)
    rows, files = [], {}
    for requirement in REQUIREMENTS.values():
        rid = requirement['id']
        applies = 'photography' in requirement['scenario_ids']
        row = {**deepcopy(requirement), 'scenario_id': 'photography', 'run_id': run_id,
            'condition_id': condition_id, 'purpose': 'baseline', 'execution_status': 'failed',
            'availability': 'exists' if applies else 'not-used', 'artifacts': []}
        if applies:
            original_id = digest(('original:' + rid).encode())[:24]
            original_hash = digest(('private original ' + rid).encode())
            row['artifacts'].append({'id': original_id, 'sha256': original_hash,
                'access': 'private', 'role': 'native-effective-configuration', 'schema': 'FixtureConfig'})
            if rid != 'CAP-PER-01':
                name = f'baseline/{condition_id}/{original_id}-{rid.lower()}.json'
                body = json.dumps({'safe': True, 'requirement': rid}).encode()
                path = folder / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(body)
                files[name] = digest(body)
                row['artifacts'].append({'id': digest(name.encode())[:24], 'location': name,
                    'sha256': files[name], 'access': 'public', 'source_artifact_ids': [original_id],
                    'source_sha256': original_hash, 'source_role': 'native-effective-configuration',
                    'role': 'redacted-native-configuration' if rid == 'CAP-GW-01' else 'application-projection'})
        rows.append(row)
    manifest = {'schema': 'citizen-public-captures/v1', 'registry_schema': REGISTRY['schema'],
        'scenario_id': 'photography', 'run_id': run_id, 'source_manifest_sha256': 'a' * 64,
        'rows': rows, 'files': files, 'execution_status': 'failed'}
    (folder / 'manifest.json').write_text(json.dumps(manifest))
    return folder, manifest


def save(pack):
    folder, manifest = pack
    (folder / 'manifest.json').write_text(json.dumps(manifest))


def row(manifest, identity='CAP-FAB-02'):
    return next(item for item in manifest['rows'] if item['id'] == identity)


def test_metadata_joins_one_registry_without_exposing_private_payloads_or_claiming_execution_success(pack):
    _, manifest = pack
    result = guide.metadata('photography')
    assert result['available'] and result['run_id'] == manifest['run_id']
    assert result['inference_calls_for_inspection'] == 0
    assert {item['id'] for item in result['rows']} == set(REQUIREMENTS)
    assert result['conditions'] == [{'id': manifest['rows'][0]['condition_id'],
                                    'purpose': 'baseline', 'execution_status': 'failed'}]
    persona = row(result, 'CAP-PER-01')
    assert persona['status'] == 'exists' and persona['privacy'] == 'private'
    assert all('path' not in artifact and 'url' not in artifact for artifact in persona['artifacts'])
    fabric = row(result)
    assert fabric['privacy'] == 'projection' and fabric['execution_status'] == 'failed'
    assert fabric['steps'] == REQUIREMENTS['CAP-FAB-02']['lessons']
    assert 'fabric-config.json' in fabric['filenames']
    assert row(result, 'CAP-GW-01')['privacy'] == 'public'
    assert row(result, 'CAP-DD-01')['status'] == 'not-used'
    assert all(artifact.get('url') is None and artifact['link_status'] == 'not-committed'
               for item in result['rows'] for artifact in item['artifacts'] if artifact['privacy'] != 'private')
    serialized = json.dumps(result)
    assert 'source_artifact_ids' not in serialized and 'private original' not in serialized


def test_missing_tagged_pack_is_unavailable_and_never_discovers_another_run(tmp_path, monkeypatch):
    monkeypatch.setattr(guide, 'PACKS', tmp_path / 'not-created')
    selected = str(uuid.uuid4())
    monkeypatch.setitem(guide_lessons.CANONICAL_DEMOS, 'photography', selected)
    monkeypatch.setattr(guide, '_git', lambda *_args: pytest.fail('Missing inventory requires no Git lookup'))
    result = guide.metadata('photography')
    assert not result['available'] and result['run_id'] == selected
    assert row(result, 'CAP-FAB-01')['status'] == 'unavailable'
    assert row(result, 'CAP-FAB-01')['privacy'] == 'unknown'
    assert row(result, 'CAP-HER-01')['status'] == 'not-used'
    assert result['conditions'] == [] and not guide.PACKS.exists()
    with pytest.raises(ValueError, match='Unknown teaching scenario'):
        guide.metadata('../photography')


@pytest.mark.parametrize('change', ['scenario', 'run', 'row-scenario', 'row-run', 'condition',
                                   'source-hash', 'source-id', 'private-path', 'public-hash',
                                   'duplicate-row', 'missing-row', 'empty-existing', 'public-kind',
                                   'private-kind', 'status-path'])
def test_metadata_rejects_identity_swaps_false_claims_and_broken_source_projection_bindings(pack, change):
    _, manifest = pack
    target = row(manifest)
    if change == 'scenario':
        manifest['scenario_id'] = 'boardgames'
    elif change == 'run':
        manifest['run_id'] = str(uuid.uuid4())
    elif change == 'row-scenario':
        target['scenario_id'] = 'boardgames'
    elif change == 'row-run':
        target['run_id'] = str(uuid.uuid4())
    elif change == 'condition':
        target['condition_id'] = str(uuid.uuid4())
    elif change == 'source-hash':
        target['artifacts'][1]['source_sha256'] = 'b' * 64
    elif change == 'source-id':
        target['artifacts'][1]['source_artifact_ids'] = ['c' * 24]
    elif change == 'private-path':
        target['artifacts'][0]['location'] = '/home/private-developer/raw-output.json'
    elif change == 'public-hash':
        target['artifacts'][1]['sha256'] = 'b' * 64
    elif change == 'duplicate-row':
        manifest['rows'].append(deepcopy(target))
    elif change == 'missing-row':
        manifest['rows'].pop()
    elif change == 'empty-existing':
        target['artifacts'] = []
    elif change == 'public-kind':
        target['artifacts'][1]['role'] = 'complete-native-result'
    elif change == 'private-kind':
        target['artifacts'][0]['role'] = '/home/private-developer/raw-output.json'
    elif change == 'status-path':
        target['execution_status'] = '/home/private-developer/raw-output.json'
    save(pack)
    with pytest.raises(ValueError):
        guide.metadata('photography')


def test_metadata_checks_published_bytes_and_does_not_return_extra_manifest_fields(pack):
    folder, manifest = pack
    manifest['private_environment'] = 'PRIVATE_ENVIRONMENT'
    row(manifest)['private_profile'] = 'PRIVATE_PROFILE'
    save(pack)
    assert 'PRIVATE_' not in json.dumps(guide.metadata('photography'))
    name = row(manifest)['artifacts'][1]['location']
    (folder / name).write_text('{"changed":true}')
    with pytest.raises(ValueError, match='integrity'):
        guide.metadata('photography')


@pytest.mark.parametrize('unsafe', ['../outside.json', '/tmp/outside.json',
                                  'baseline/../outside.json', 'baseline\\outside.json'])
def test_metadata_rejects_unsafe_nested_locations(pack, unsafe):
    _, manifest = pack
    manifest['files'][unsafe] = 'a' * 64
    save(pack)
    with pytest.raises(ValueError):
        guide.metadata('photography')


@pytest.mark.parametrize('symbolic', ['manifest', 'artifact', 'condition-directory'])
def test_metadata_refuses_symbolic_publication_paths(pack, tmp_path, symbolic):
    folder, manifest = pack
    path = folder / 'manifest.json' if symbolic == 'manifest' else folder / row(manifest)['artifacts'][1]['location']
    if symbolic == 'condition-directory':
        path = path.parent
    outside = tmp_path / 'outside'
    path.rename(outside)
    path.symlink_to(outside, target_is_directory=outside.is_dir())
    with pytest.raises(ValueError, match='Symbolic'):
        guide.metadata('photography')


def test_published_files_must_be_referenced_by_a_requirement(pack):
    folder, manifest = pack
    name = f'baseline/{manifest["rows"][0]["condition_id"]}/orphan.json'
    (folder / name).write_text('{}')
    manifest['files'][name] = digest(b'{}')
    save(pack)
    with pytest.raises(ValueError, match='unbound'):
        guide.metadata('photography')


def test_public_url_requires_exact_committed_bytes_without_falling_back_to_working_tree(tmp_path, monkeypatch):
    monkeypatch.setattr(guide, 'ROOT', tmp_path)
    path = tmp_path / 'recordings/captures/photography/demo/baseline/condition/settings.yaml'
    body = b'output_tokens: 1024\n'
    revision = '1' * 40
    calls = []

    def git_show(command, **options):
        calls.append((command, options))
        return body

    monkeypatch.setattr(guide.subprocess, 'check_output', git_show)
    url = guide._public_url(path, digest(body), 'https://github.com/example/lab', revision)
    assert url == f'https://github.com/example/lab/blob/{revision}/{path.relative_to(tmp_path)}'
    assert calls[0][0] == ['git', 'show', f'{revision}:{path.relative_to(tmp_path)}']
    assert guide._public_url(path, digest(b'changed'), 'https://github.com/example/lab', revision) is None
    monkeypatch.setattr(guide.subprocess, 'check_output', lambda *_args, **_kwargs: (_ for _ in ()).throw(
        subprocess.CalledProcessError(128, 'git')))
    assert guide._public_url(path, digest(body), 'https://github.com/example/lab', revision) is None
    assert guide._public_url(path, digest(body), 'https://github.com/example/lab', None) is None


async def test_journey_metadata_dispatch_remains_file_only_and_rejects_run_or_path_parameters(pack, tmp_path):
    service = JourneyService(tmp_path / 'uncreated-execution-root')
    result = await service.dispatch({'action': 'metadata', 'scenario_id': 'photography'})
    assert result['available'] and result['inference_calls_for_inspection'] == 0
    assert not service.root.exists() and not service.tasks
    with pytest.raises(ValueError, match='unexpected fields'):
        await service.dispatch({'action': 'metadata', 'scenario_id': 'photography', 'run_id': str(uuid.uuid4())})
    with pytest.raises(ValueError, match='unexpected fields'):
        await service.dispatch({'action': 'metadata', 'path': '/tmp/private.json'})


def test_reader_accepts_an_actual_registry_driven_capture_publication(tmp_path, monkeypatch):
    specification = importlib.util.spec_from_file_location('metadata_capture_fixture',
        Path(__file__).with_name('test_w1_capture_publication.py'))
    fixtures = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(fixtures)
    run_id, original, _ = fixtures.complete_run(tmp_path / 'private-runs')
    destination = tmp_path / 'recordings/captures/photography' / run_id
    fixtures.export(run_id, run_root=original.parent, destination=destination)
    monkeypatch.setattr(guide, 'ROOT', tmp_path)
    monkeypatch.setattr(guide, 'PACKS', tmp_path / 'recordings/captures')
    monkeypatch.setitem(guide_lessons.CANONICAL_DEMOS, 'photography', run_id)
    monkeypatch.setattr(guide, '_public_url', lambda *_args: None)
    result = guide.metadata('photography')
    assert result['available'] and len(result['rows']) == len(REQUIREMENTS)
    assert row(result, 'CAP-US-01')['privacy'] == 'projection'
    assert row(result, 'CAP-PLAT-01')['condition_id'] is None
    assert row(result, 'CAP-PLAT-01')['status'] == 'not-used'
