"""Shared guide contracts. These are offline fixtures, not live run evidence."""
import base64
import asyncio
import hashlib
import json
import subprocess
import uuid

import pytest

from learning_lab.catalogue import Preferences
from learning_lab.guide_sources import repository_url, source_excerpt
from learning_lab.journey import JourneyService, JourneySpec, PublicTarget, public_photography_preferences
from learning_lab.sandbox import NativeSandbox, native_environment


@pytest.fixture(autouse=True)
def isolated_recording_catalogue(tmp_path, monkeypatch):
    from learning_lab import recordings
    monkeypatch.setattr(recordings, 'PACKS', tmp_path / 'no-installed-recordings')


def saved(service, *, status='failed'):
    identity = str(uuid.uuid4())
    folder = service.folder(identity)
    folder.mkdir(parents=True)
    state = {'run_id': identity, 'episode_id': str(uuid.uuid4()), 'scenario_id': 'photography',
             'status': status, 'kind': 'offline-test-fixture', 'owner_pid': 99999999,
             'created_at': '2026-11-20T00:00:00Z', 'calls': 0}
    (folder / 'run.json').write_text(json.dumps(state))
    return identity, folder


def test_private_profile_constraints_are_never_inferred_from_context():
    empty = public_photography_preferences('Can I learn photography?')
    assert empty.budget_sgd is None and empty.days is None
    public = public_photography_preferences('Beginner photography on Saturday, below S$50 before funding.')
    assert public == Preferences(goal='photography', budget_sgd=50, days=[5])


async def test_public_target_discards_private_preferences(tmp_path):
    calls = []

    class Target:
        async def reply(self, message, preferences):
            calls.append((message, preferences))
            return {'content': 'Offline fixture response'}

    target = PublicTarget(Target(), tmp_path)
    await target.reply('I would like to learn photography.', Preferences(goal='private goal', budget_sgd=9999, days=[0]))
    assert calls[0][1].budget_sgd is None and calls[0][1].days is None
    assert 'private goal' not in calls[0][0]


@pytest.mark.parametrize('fields', [
    {'scenario_id': 'boardgames'}, {'model_route': 'switchyard'}, {'source': 'generated'},
    {'turns': 3}, {'execution': 'local'}, {'budget': 100000}, {'original_sha256': 'invalid'},
])
def test_preset_cannot_be_expanded_by_browser_fields(fields):
    base = {'source_id': 'fixture', 'original_sha256': 'a' * 64}
    with pytest.raises(ValueError):
        JourneySpec.model_validate({**base, **fields})


def test_empty_saved_run_inspection_creates_no_execution_state(tmp_path):
    root = tmp_path / 'not-created'
    service = JourneyService(root)
    assert service.list()['runs'] == []
    assert not root.exists() and not service.tasks and service._lease is None


def test_local_artifacts_are_scoped_to_one_run_and_never_accept_paths(tmp_path):
    service = JourneyService(tmp_path)
    first, folder = saved(service)
    second, other = saved(service)
    (folder / 'usage.json').write_text('{"fixture":"first","usage":null}')
    (other / 'evaluation.json').write_text('{"fixture":"second"}')
    (other / 'usage.json').write_text('{"fixture":"second","usage":null}')
    (folder / 'resolved-inputs.json').write_text('{"profile":"must not be in the log allowlist"}')
    artifacts = service.artifacts(first)['artifacts']
    usage = next(r for r in artifacts if r['path'] == 'usage.json')
    assert first in usage['url']
    assert service.artifact(first, usage['id'])['content']['usage'] is None
    assert not any(r['path'] == 'resolved-inputs.json' for r in artifacts)
    with pytest.raises(ValueError):
        service.artifact(second, usage['id'])
    with pytest.raises(ValueError):
        service.artifact(first, '../usage.json')
    assert not service.tasks and service._lease is None


def test_log_browser_rejects_symlinked_files_and_run_directories(tmp_path):
    service = JourneyService(tmp_path / 'runs')
    identity, folder = saved(service)
    outside = tmp_path / 'outside'
    outside.write_text('private marker')
    (folder / 'usage.json').symlink_to(outside)
    assert not any(r['path'] == 'usage.json' for r in service.artifacts(identity)['artifacts'])
    linked = str(uuid.uuid4())
    (service.root / linked).symlink_to(folder, target_is_directory=True)
    with pytest.raises(ValueError):
        service.get(linked)


@pytest.mark.parametrize('identity', ['../secret', '/tmp/secret', 'not-a-uuid', None])
def test_run_paths_are_not_user_selected_paths(tmp_path, identity):
    with pytest.raises(ValueError):
        JourneyService(tmp_path).get(identity)


def test_cross_worker_lease_and_unresolved_guard_prevent_second_run(tmp_path):
    first, second = JourneyService(tmp_path), JourneyService(tmp_path)
    identity = str(uuid.uuid4())
    first._acquire(identity)
    try:
        with pytest.raises(ValueError):
            second._acquire(str(uuid.uuid4()))
    finally:
        first._release(identity, False)
    assert first.active.is_file()
    with pytest.raises(ValueError):
        second._acquire(str(uuid.uuid4()))
    first._release(identity, True)
    second._acquire(str(uuid.uuid4()))
    second._release(json.loads(second.active.read_text())['run_id'], True)


async def test_read_dispatch_cannot_smuggle_execution_fields(tmp_path):
    service = JourneyService(tmp_path)
    with pytest.raises(ValueError):
        await service.dispatch({'action': 'get', 'run_id': 'x', 'execute': True})
    with pytest.raises(ValueError):
        await service.dispatch({'action': 'start_run', 'spec': {}})
    assert not tmp_path.joinpath('active.json').exists()


async def test_cancellation_cannot_steal_a_foreign_live_workload(tmp_path):
    service = JourneyService(tmp_path)
    identity, _ = saved(service, status='running')
    with pytest.raises(ValueError, match='does not own'):
        await service.cancel(identity)
    assert service.get(identity)['status'] == 'running'


async def test_native_cleanup_refuses_another_run_label(tmp_path):
    identity = str(uuid.uuid4())
    native = NativeSandbox(identity, tmp_path, None, catalogue=tmp_path / 'catalogue.json')
    calls = []

    async def cli(*args, **kwargs):
        calls.append(args)
        return json.dumps({'sandboxes': [{'name': native.name, 'id': 'fixture-sandbox',
                           'labels': {'citizen.scope': 'journey', 'citizen.run': str(uuid.uuid4())}}]})

    native.cli = cli
    with pytest.raises(ValueError, match='not owned'):
        await native.cleanup_native()
    assert all('delete' not in call for call in calls)


async def test_native_cleanup_requires_matching_native_identity(tmp_path):
    identity = str(uuid.uuid4())
    native = NativeSandbox(identity, tmp_path, None, catalogue=tmp_path / 'catalogue.json')
    native.identity = {'id': 'old-fixture'}

    async def cli(*args, **kwargs):
        return json.dumps({'sandboxes': [{'name': native.name, 'id': 'different-fixture',
                           'labels': {'citizen.scope': 'journey', 'citizen.run': identity}}]})

    native.cli = cli
    with pytest.raises(ValueError, match='identity changed'):
        await native.cleanup_native()


def test_native_artifacts_preserve_bytes_and_reject_unsafe_or_missing_chunks(tmp_path):
    native = NativeSandbox(str(uuid.uuid4()), tmp_path, None, catalogue=tmp_path / 'catalogue.json')
    raw = b'{"status":"failed","usage":null}\n'
    frame = {'path': 'fabric-traces/fixture/relay.jsonl', 'offset': 0,
             'data': base64.b64encode(raw).decode(), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    native.artifact(frame)
    assert (tmp_path / 'native' / frame['path']).read_bytes() == raw
    with pytest.raises(ValueError):
        native.artifact({**frame, 'path': '../relay.jsonl'})
    with pytest.raises(ValueError):
        native.artifact({**frame, 'path': 'another/relay.jsonl', 'offset': 4})


def test_native_environment_withholds_inference_and_dataset_credentials(monkeypatch):
    for key in ('NVIDIA_API_KEY', 'NGC_CLI_API_KEY', 'LAB_PROXY_API_KEY', 'AWS_SECRET_ACCESS_KEY'):
        monkeypatch.setenv(key, 'offline-fixture-must-not-be-inherited')
    env = native_environment()
    assert all(key not in env for key in ('NVIDIA_API_KEY','NGC_CLI_API_KEY','LAB_PROXY_API_KEY','AWS_SECRET_ACCESS_KEY'))
    assert env['OPENSHELL_NO_BROWSER'] == '1'


def test_repository_url_follows_configuration_and_removes_credentials(monkeypatch):
    monkeypatch.setenv('LAB_REPOSITORY_URL', 'https://user:password@github.com/example/citizen-app.git?token=secret')
    assert repository_url() == 'https://github.com/example/citizen-app'
    info = source_excerpt('fabric')
    assert info['github_url'].startswith('https://github.com/example/citizen-app/blob/')
    assert info['path'] == 'src/learning_lab/fabric_target.py'
    assert 'absolute_path' not in info
    assert source_excerpt('../../.env')['available'] is False


def test_native_policy_revision_keeps_exact_precision_in_browser_projection():
    from learning_lab.journey import browser_projection
    revision = 1851495197734358921
    original = {'revision': revision, 'other': [5, True, None]}
    assert browser_projection(original) == {'revision': str(revision), 'other': [5, True, None]}
    assert original['revision'] == revision  # Original native record is unchanged.


@pytest.mark.parametrize('failure', [FileNotFoundError(), TimeoutError()])
async def test_unavailable_native_prerequisite_is_a_readiness_result(monkeypatch, failure):
    import learning_lab.sandbox as sandbox

    async def unavailable(*args, **kwargs):
        raise failure

    monkeypatch.setattr(sandbox, 'openshell_binary', lambda: '/fixture/openshell')
    monkeypatch.setattr(sandbox, 'command', unavailable)
    result = await sandbox.native_readiness()
    assert not result['gateway'] and not result['image'] and result['reason']


async def test_unverified_sandbox_cannot_call_provider(tmp_path):
    class Gateway:
        async def complete(self, *args, **kwargs):
            pytest.fail('Unverified image must never reach inference')

    native = NativeSandbox(str(uuid.uuid4()), tmp_path, Gateway(), catalogue=tmp_path / 'facts.json')
    responses = []

    async def send(response):
        responses.append(response)

    native.send = send
    await native.model({'id': 'offline-fixture', 'payload': {}})
    assert 'unverified' in responses[0]['error']


@pytest.mark.parametrize('variant,passes', [('exact-link', True), ('unknown-link', False), ('wrong-day', False), ('fabricated-native', False), ('missing-budget', False), ('invented-area', False), ('correct-area', True), ('wrong-fee', False), ('correct-fee', True), ('wrong-area-field', False), ('correct-area-field', True)])
def test_saved_response_assertions_follow_facts_and_native_provenance(tmp_path, variant, passes):
    from learning_lab.catalogue import freeze_catalogue, search_courses
    from learning_lab.journey_checks import evaluate_photography
    catalogue = tmp_path / 'catalogue.json'
    freeze_catalogue(catalogue)
    course = search_courses(Preferences(goal='photography', budget_sgd=50, days=[5]), catalogue_path=catalogue)['matches'][0]['course']
    question = 'I want beginner photography on Saturday, under S$50.'
    reply = course['title'] + ' ' + course['source_url']
    tool = {'name': 'search_courses', 'evidence_origin': 'native_relay', 'status': 'completed', 'result': {'matches': [course]}}
    if variant == 'unknown-link':
        reply += ' https://invalid.example/invented-course'
    if variant == 'wrong-day':
        reply += ' CC-002'
    if variant == 'fabricated-native':
        tool['evidence_origin'] = 'application'
    if variant == 'missing-budget':
        question = 'I want beginner photography on Saturday.'
    if variant == 'invented-area':
        reply += '\nVenue: Toa Payoh West CC, within the Bukit Timah planning area.'
    if variant == 'correct-area':
        reply += '\nVenue: Toa Payoh West CC, in the Toa Payoh planning area.'
    if variant == 'wrong-fee':
        reply += '\n**Fee**: S$49'
    if variant == 'correct-fee':
        reply += '\n**Fee**: S$10'
    if variant == 'wrong-area-field':
        reply += '\n**Planning area:** Bukit Timah'
    if variant == 'correct-area-field':
        reply += '\n**Planning area:** Toa Payoh'
    result = evaluate_photography([{'role':'user','content':question}, {'role':'assistant','content':reply}], catalogue, [tool],
                                 {'original_sha256': 'a' * 64, 'source_revision': 'fixture'})
    assert all(row['status'] == 'pass' for row in result['rows']) == passes
    assert result['inference_calls'] == 0 and result['helix_used'] is False


async def test_cancelling_native_start_waits_for_creation_before_confirming_cleanup(tmp_path):
    native = NativeSandbox(str(uuid.uuid4()), tmp_path, None, catalogue=tmp_path / 'facts.json')
    starting, release = asyncio.Event(), asyncio.Event()
    events = []

    async def cli(*args, **kwargs):
        if args[:2] == ('sandbox', 'create'):
            starting.set()
            await release.wait()
            events.append('creation-settled')
        else:
            events.append('inventory')
            return '{"sandboxes":[]}'

    native.cli = cli
    task = asyncio.create_task(native.__aenter__())
    await starting.wait()
    task.cancel()
    await asyncio.sleep(0)
    assert not task.done() and 'inventory' not in events
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert events[0] == 'creation-settled'
    assert json.loads((tmp_path / 'cleanup.json').read_text())['native_absence_confirmed']


async def test_ambiguous_creation_keeps_the_recovery_boundary(tmp_path):
    native = NativeSandbox(str(uuid.uuid4()), tmp_path, None, catalogue=tmp_path / 'facts.json')
    native.creation_uncertain = True

    async def cli(*args, **kwargs):
        return '{"sandboxes":[]}'

    native.cli = cli
    with pytest.raises(RuntimeError, match='ambiguously'):
        await native.cleanup_native()
    assert not (tmp_path / 'cleanup.json').exists()


def test_source_links_follow_another_checkout_location(tmp_path, monkeypatch):
    import learning_lab.guide_sources as sources
    checkout = tmp_path / 'another checkout'
    source = checkout / 'src/learning_lab/fabric_target.py'
    source.parent.mkdir(parents=True)
    source.write_text('def build_config():\n    return "offline fixture"\n')

    def git(*args):
        return subprocess.check_output(['git', *args], cwd=checkout, stderr=subprocess.DEVNULL)

    git('init', '--initial-branch=main')
    git('remote', 'add', 'origin', 'git@github.com:example/portable-guide.git')
    git('add', 'src')
    git('-c', 'user.name=Offline Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', 'Offline source fixture')
    monkeypatch.setattr(sources, 'ROOT', checkout)
    monkeypatch.delenv('LAB_REPOSITORY_URL', raising=False)
    result = sources.source_excerpt('fabric')
    revision = git('rev-parse', 'HEAD').decode().strip()
    assert result['github_url'] == f'https://github.com/example/portable-guide/blob/{revision}/src/learning_lab/fabric_target.py#L1'
    assert result['path'] == 'src/learning_lab/fabric_target.py'
    assert str(checkout) not in json.dumps(result)
