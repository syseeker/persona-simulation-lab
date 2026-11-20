"""Read-only review contracts; fixtures never count as executed scenario evidence."""
import hashlib
import json

import pyarrow as pa
import pyarrow.dataset as pads
import pytest

from learning_lab import guide_lessons as guide, recordings
from learning_lab.datasets import profile_hash
from learning_lab.guide_sources import OPERATIONS, operation_links
from learning_lab.journey import JourneyService


def fixture_source(tmp_path, monkeypatch):
    rows = [dict(uuid='first', first_name='Fixture', last_name='One', age=24, occupation='Student'),
            dict(uuid='second', first_name='Fixture', last_name='Two', age=45, occupation='Retail')]
    dataset = pads.dataset(pa.Table.from_pylist(rows))
    monkeypatch.setattr(guide, '_dataset', lambda query: (dataset, None, {'revision': 'fixture-v1'}))
    monkeypatch.setattr(guide, 'INDEX_PATH', tmp_path / 'cache/index.json')
    return rows


def test_original_resolution_verifies_the_hash_and_does_not_store_profile_values(tmp_path, monkeypatch):
    rows = fixture_source(tmp_path, monkeypatch)
    digest = profile_hash(rows[1])
    result = guide.resolve_original('ngc', 'fixture-v1', digest)
    assert result['available'] and result['name'] == 'Fixture Two'
    assert result['original_sha256'] == digest
    cache = json.loads(guide.INDEX_PATH.read_text())
    assert list(cache.values()) == ['second']
    assert 'occupation' not in guide.INDEX_PATH.read_text()
    # A stale hint is not trusted; rehash and locate the actual original.
    guide.INDEX_PATH.write_text(json.dumps({next(iter(cache)): 'first'}))
    assert guide.resolve_original('ngc', 'fixture-v1', digest)['name'] == 'Fixture Two'


def test_missing_or_changed_original_never_samples_a_substitute(tmp_path, monkeypatch):
    rows = fixture_source(tmp_path, monkeypatch)
    assert not guide.resolve_original('ngc', 'other-revision', profile_hash(rows[0]))['available']
    assert not guide.resolve_original('ngc', 'fixture-v1', 'a' * 64)['available']
    monkeypatch.setattr(guide, '_dataset', lambda query: (_ for _ in ()).throw(ValueError('Source unavailable')))
    assert guide.resolve_original('ngc', 'fixture-v1', 'a' * 64) == {'available': False, 'notice': 'Source unavailable'}


@pytest.mark.parametrize('scenario', ['boardgames', 'dreamjob'])
async def test_planned_context_never_discovers_private_runs_or_photography_evidence(tmp_path, monkeypatch, scenario):
    monkeypatch.setitem(guide.CANONICAL_DEMOS, scenario, None)
    monkeypatch.setattr(recordings, 'trace', lambda *_: pytest.fail('Must not load a recording for a planned scenario'))
    service = JourneyService(tmp_path / 'not-created')
    context = await service.dispatch({'action': 'lesson', 'scenario_id': scenario})
    assert context['state'] == 'planned' and context['trace'] is None and context['artifacts'] == []
    assert context['inference_calls_for_inspection'] == 0
    assert not service.root.exists() and not service.tasks
    assert not (await service.dispatch({'action': 'demo-persona', 'scenario_id': scenario}))['available']


def test_missing_curated_demo_never_falls_back_to_any_other_run(monkeypatch):
    requested = []
    monkeypatch.setattr(recordings, 'trace', lambda identity: requested.append(identity))
    context = guide.lesson_context('photography')
    assert requested == [guide.CANONICAL_DEMOS['photography']]
    assert context['state'] == 'unavailable' and context['trace'] is None
    with pytest.raises(ValueError):
        guide.lesson_context('../photography')


def context_pack(tmp_path, monkeypatch):
    monkeypatch.setattr(guide, 'ROOT', tmp_path)
    monkeypatch.setattr(guide, 'CONTEXT_ROOT', tmp_path / 'recordings/guide-context')
    native = tmp_path / 'native'
    native.mkdir()
    (native / 'manifest.json').write_text('immutable native manifest')
    monkeypatch.setattr(recordings, 'pack_folder', lambda identity: native)
    folder = guide.CONTEXT_ROOT / 'photography/demo'
    folder.mkdir(parents=True)
    body = '{"safe":true}\n'
    (folder / 'setup.json').write_text(body)
    manifest = {'schema': 'citizen-guide-context/v1', 'scenario_id': 'photography', 'run_id': 'demo',
                'recording_manifest_sha256': hashlib.sha256((native / 'manifest.json').read_bytes()).hexdigest(),
                'projection_notice': 'Offline fixture', 'source_hashes': {},
                'files': {'setup.json': hashlib.sha256(body.encode()).hexdigest()}}
    (folder / 'manifest.json').write_text(json.dumps(manifest))
    return folder, manifest


def test_companion_is_bound_to_unchanged_pack_and_rejects_tampering(tmp_path, monkeypatch):
    folder, manifest = context_pack(tmp_path, monkeypatch)
    assert guide.companion('photography', 'demo')['data'] == {'setup.json': {'safe': True}}
    (folder / 'setup.json').write_text('{"safe":false}')
    with pytest.raises(ValueError, match='integrity'):
        guide.companion('photography', 'demo')
    manifest['recording_manifest_sha256'] = 'b' * 64
    (folder / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='does not match'):
        guide.companion('photography', 'demo')


def test_companion_rejects_unsafe_names_and_symlinks(tmp_path, monkeypatch):
    folder, manifest = context_pack(tmp_path, monkeypatch)
    manifest['files'] = {'../private.json': 'a' * 64}
    (folder / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='identifier'):
        guide.companion('photography', 'demo')
    (folder / 'manifest.json').unlink()
    (folder / 'manifest.json').symlink_to(tmp_path / 'native/manifest.json')
    with pytest.raises(ValueError, match='Symbolic'):
        guide.companion('photography', 'demo')


def test_exact_operation_links_resolve_committed_symbols_and_compare_captured_hashes():
    from learning_lab.settings import ROOT
    captured = {'src/learning_lab/fabric_target.py': hashlib.sha256((ROOT / 'src/learning_lab/fabric_target.py').read_bytes()).hexdigest()}
    links = operation_links(captured)
    assert set(links) == set(OPERATIONS)
    assert all(link['available'] and link['line'] and '/blob/' in link['url'] for link in links.values())
    assert links['fabric.invoke']['recording_match'] == 'matched'
    assert 'self.runtime.invoke' in links['fabric.invoke']['symbol']
    assert 'content' not in links['fabric.invoke']


@pytest.mark.parametrize('scenario', ['photography', 'boardgames'])
def test_published_companion_excludes_private_rows_prompts_and_reasoning(scenario):
    folder = guide.CONTEXT_ROOT / scenario / guide.CANONICAL_DEMOS[scenario]
    values = [json.loads(p.read_text()) for p in folder.glob('*.json') if p.name != 'manifest.json']
    serialized = json.dumps(values)
    for forbidden in ['behavioral_profile', 'persona_text', 'source_id', 'api_key', 'reasoning_content', '/home/']:
        assert forbidden not in serialized
    result = guide.lesson_context(scenario)
    assert result['state'] == 'recorded'
    assert result['context']['fabric-invocations.json'][0]['output']['response'] in [m['content'] for m in result['trace']['conversation']]
