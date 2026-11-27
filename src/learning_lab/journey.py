"""Shared Integration Guide service: explicit runs, frozen inputs and local evidence.

The UI, CLI and developer MCP use this boundary. Reads never initialize native
execution or recover another worker's workloads. Presets become executable only
when their integrations exist; curated recordings are a separate review gate.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Literal
import uuid

import httpx
from pydantic import Field

from .catalogue import Preferences, StrictModel, freeze_catalogue
from .datasets import dataset_catalogue, lock_personas, sample_personas
from .evidence import native_tool_records, relay_scopes, sanitize, save_evidence
from .guide_sources import source_excerpt, repository_url, SOURCES
from .guide_scenarios import PRESETS, scenario_presets
from .inference import Budget, Gateway
from .sandbox import NativeSandbox, native_readiness
from .settings import ROOT, load_environment
from .simulation import hosted_episode, prepare_rows
from . import recordings

STAGES = ('persona', 'situation', 'build', 'run', 'investigate', 'evaluate', 'routing', 'safeguards', 'deploy')
TERMINAL = {'completed', 'failed', 'cancelled', 'interrupted'}
ARTIFACT_NAMES = {
    'run.json', 'source-lock.json', 'situation.json', 'catalogue-snapshot.json',
    'public-conversation.json', 'public-constraints.jsonl', 'events.jsonl', 'usersim-activations.jsonl', 'usersim-result.json',
    'usage.json', 'evaluation.json', 'review-notes.json', 'sandbox-lifecycle.jsonl', 'sandbox-identity.json',
    'requested-policy.yaml', 'effective-policy.yaml', 'effective-policy.json', 'boundary-probes.json',
    'cleanup.json', 'runtime-receipt.json', 'sandbox-stderr.log', 'fabric-config.json', 'fabric-plan.json',
    'fabric-doctor.json', 'fabric-lifecycle.jsonl', 'reply-outcomes.jsonl', 'relay.jsonl',
    'guardrails-config.json', 'guardrails-decisions.jsonl', 'guardrails-probe.json',
    'designer-configuration.json', 'designer-output.json', 'designer-generation.json', 'designer-lineage.json',
    'disclosure-audit.jsonl', 'helix-criteria.json', 'helix-evaluation.json', 'helix-job.json',
    'routing-comparison.json', 'condition.json', 'platform-condition.json', 'platform-package.json',
    'platform-setup.json', 'platform-registration.json', 'platform-deployment.json', 'platform-session.json',
    'platform-invocation.json', 'platform-effective-policy.yaml', 'platform-effective-policy.json',
    'platform-boundary-probes.json', 'platform-session-close.json', 'platform-cleanup.json',
}


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, default=str, indent=2) + '\n')
    temporary.replace(path)


def browser_projection(value):
    """Retain exact native uint64 values across the JSON/JavaScript boundary."""
    if isinstance(value, int) and not isinstance(value, bool) and abs(value) > 2**53 - 1:
        return str(value)
    if isinstance(value, dict):
        return {key: browser_projection(item) for key, item in value.items()}
    if isinstance(value, list):
        return [browser_projection(item) for item in value]
    return value


def public_photography_preferences(message: str) -> Preferences:
    """Bind only explicit public facts; salary/profile context cannot enter tools."""
    if not isinstance(message, str) or not re.search(r'\bphoto(?:graphy|graph|s)?\b', message, re.I):
        raise ValueError('The public learner turn did not express the selected photography goal')
    amount = re.search(r'(?:S\$|SGD\s*|\$)\s*(\d+(?:\.\d+)?)|\b(\d+(?:\.\d+)?)\s*(?:SGD|dollars)\b', message, re.I)
    budget = float(next(v for v in amount.groups() if v)) if amount else None
    days = [5] if re.search(r'\bSaturday(?:s)?\b', message, re.I) else None
    return Preferences(goal='photography', budget_sgd=budget, days=days)


class JourneySpec(StrictModel):
    scenario_id: Literal['photography', 'boardgames', 'dreamjob'] = 'photography'
    source: Literal['hf-profile-only', 'ngc'] = 'ngc'
    source_id: str = Field(min_length=1, max_length=200)
    original_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')


class PublicTarget:
    """Adapter sees the latest public turn, not the private UserSim preamble."""
    def __init__(self, native, folder, scenario_id='photography', retail_context=None):
        self.native, self.folder = native, folder
        self.scenario_id, self.public_turns = scenario_id, 0
        self.retail_context = retail_context

    async def reply(self, message, _private_preferences=None):
        if self.scenario_id == 'photography':
            prefs = public_photography_preferences(message)
        elif self.scenario_id == 'boardgames':
            if self.public_turns == 0 and not re.search(r'\bboard[ -]?games?\b', message, re.I):
                raise ValueError('The public opening did not express a board-games goal')
            # Follow-up pronouns refer to the goal already stated publicly.
            prefs = Preferences(goal='board games')
        elif self.scenario_id == 'dreamjob':
            if self.retail_context is None:
                raise ValueError('Retail execution requires its public-context boundary')
            return await self.native.reply(message, self.retail_context.accept(message))
        else:
            raise ValueError('Unknown public scenario boundary')
        self.public_turns += 1
        save_evidence(self.folder / 'public-constraints.jsonl',
                      {'basis': 'public learner message only', 'message_sha256': hashlib.sha256(message.encode()).hexdigest(),
                       'turn': self.public_turns, 'preferences': prefs.model_dump(mode='json')}, append=True)
        return await self.native.reply(message, prefs)


class JourneyService:
    def __init__(self, root: Path | None = None):
        self.root = root or ROOT / 'runs/journeys'
        self.tasks = {}
        self.active = self.root / 'active.json'
        self._lease = None

    def folder(self, run_id):
        try:
            if not isinstance(run_id, str) or str(uuid.UUID(run_id)) != run_id:
                raise ValueError
        except (ValueError, AttributeError):
            raise ValueError('Choose a canonical saved run identity') from None
        folder = self.root / run_id
        if folder.is_symlink():
            raise ValueError('Symbolic run directories are not accepted')
        return folder

    def get(self, run_id):
        recorded = recordings.trace(run_id)
        if recorded is not None:
            return recorded['run']
        path = self.folder(run_id) / 'run.json'
        if not path.is_file() or path.is_symlink():
            raise ValueError('Saved scenario run not found')
        state = json.loads(path.read_text())
        state['owned_by_this_worker'] = run_id in self.tasks
        state['run_directory'] = 'runs/journeys/' + run_id
        if state.get('status') not in TERMINAL:
            try:
                os.kill(int(state['owner_pid']), 0)
            except ProcessLookupError:
                state['ownership_notice'] = 'Owner is absent. Recover this run explicitly before starting another.'
        return sanitize(state)

    def list(self, scenario_id='photography'):
        if scenario_id not in {'photography', 'boardgames', 'dreamjob'}:
            raise ValueError('Unknown scenario')
        records = [recordings.trace(pack['run_id'])['run'] for pack in recordings.listed() if pack['scenario_id'] == scenario_id]
        published = {record['run_id'] for record in records}
        for path in sorted(self.root.glob('*/run.json'), key=lambda p: p.stat().st_mtime, reverse=True):
            if path.parent.is_symlink() or path.is_symlink():
                continue
            if path.parent.name in published:
                continue
            state = self.get(path.parent.name)
            if state['scenario_id'] == scenario_id:
                records.append(state)
            if len(records) >= 30:
                break
        records.sort(key=lambda r:r['created_at'], reverse=True)
        # Checked-in packs are the fixed review experience. Local-run linking
        # retains its existing behavior and is not this publication feature.
        records.sort(key=lambda r:not r.get('recording', False))
        return {'runs': records, 'scenario_id': scenario_id}

    async def readiness(self):
        load_environment()
        native = await native_readiness()
        proxy = {'configured': bool(os.getenv('LAB_PROXY_BASE_URL') and os.getenv('LAB_PROXY_API_KEY')),
                 'reachable': False, 'fixed_alias_available': False, 'support_alias_available': False}
        if proxy['configured']:
            try:
                async with httpx.AsyncClient(timeout=8) as client:
                    response = await client.get(os.environ['LAB_PROXY_BASE_URL'].rstrip('/') + '/models',
                                  headers={'Authorization': 'Bearer ' + os.environ['LAB_PROXY_API_KEY']})
                    if response.status_code == 200:
                        aliases = {r['id'] for r in response.json().get('data', [])}
                        proxy.update(reachable=True, fixed_alias_available='lab-advisor-fixed' in aliases,
                                     support_alias_available='lab-support' in aliases)
            except (httpx.HTTPError, ValueError, KeyError):
                pass
        datasets = [{k: d.get(k) for k in ('source', 'name', 'ready', 'row_count', 'revision', 'notice')}
                    for d in dataset_catalogue()['datasets']]
        guarded = json.loads(self.active.read_text()) if self.active.is_file() else None
        ready = all((native['cli'], native['gateway'], native['image'], proxy['reachable'],
                     proxy['fixed_alias_available'], proxy['support_alias_available'], not guarded))
        return {'ready': ready, 'native': native, 'proxy': proxy, 'datasets': datasets,
                'active': guarded, 'inference_calls': 0,
                'notice': 'Readiness checks inventory and connectivity, not model quality or a successful inference.'}

    def sample(self, source='ngc'):
        if source not in {'ngc', 'hf-profile-only'}:
            raise ValueError('Choose public HF or Singapore NGC Extended')
        locked = sample_personas(source, count=1)
        record = locked['records'][0]
        profile = record['profile']
        return {'source': source, 'source_id': record['source_id'],
                'original_sha256': record['original_profile_sha256'], 'source_revision': record['source_revision'],
                'summary': {k: profile.get(k) for k in ('name', 'age', 'occupation', 'education_level', 'planning_area', 'district') if profile.get(k) is not None},
                'ocean_conditioning': source == 'ngc', 'inference_calls': 0}

    def _acquire(self, run_id):
        self.root.mkdir(parents=True, exist_ok=True)
        lease = (self.root / '.workload.lock').open('a+')
        try:
            fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if self.active.exists():
                raise ValueError('An active or unresolved run requires cancellation/recovery first')
            write_json(self.active, {'run_id': run_id, 'owner_pid': os.getpid(), 'started_at': now()})
        except (ValueError, BlockingIOError):
            lease.close()
            raise ValueError('Another run owns the workload or requires explicit recovery') from None
        self._lease = lease

    def _release(self, run_id, cleanup_confirmed):
        if cleanup_confirmed and self.active.is_file():
            guard = json.loads(self.active.read_text())
            if guard['run_id'] == run_id:
                self.active.unlink()
        if self._lease:
            fcntl.flock(self._lease, fcntl.LOCK_UN)
            self._lease.close()
            self._lease = None

    async def start(self, data):
        spec = JourneySpec.model_validate(data)
        preset = PRESETS[spec.scenario_id]
        if not preset.implemented:
            raise ValueError('This scenario is still illustrative')
        ready = await self.readiness()
        if not ready['ready']:
            raise ValueError('Scenario prerequisites are not ready; inspect readiness. No model call was started.')
        lock = lock_personas(spec.source, [spec.source_id])
        if lock['records'][0]['original_profile_sha256'] != spec.original_sha256:
            raise ValueError('The original persona changed; inspect and select it again')
        run_id, episode_id = str(uuid.uuid4()), str(uuid.uuid4())
        self._acquire(run_id)
        folder = self.folder(run_id)
        folder.mkdir()
        state = {'schema': 'citizen-journey/v1', 'run_id': run_id, 'condition_id': str(uuid.uuid4()),
                 'episode_id': episode_id, 'scenario_id': spec.scenario_id, 'kind': 'live', 'status': 'queued',
                 'created_at': now(), 'owner_pid': os.getpid(), 'stage': 'persona',
                 'spec': spec.model_dump(), 'configuration': {'harness': preset.harness, 'fabric': True,
                 'route': 'fixed', 'proxy': 'LiteLLM', 'execution': preset.deployment if spec.scenario_id != 'dreamjob' else 'standalone baseline + separate Helix-managed condition',
                 'designer': spec.scenario_id == 'dreamjob', 'guardrails': spec.scenario_id != 'photography',
                 'helix': spec.scenario_id == 'dreamjob', 'turn_limit': preset.public_turns,
                 'model_call_limit': 120, 'output_tokens': 1024}, 'calls': 0, 'cleanup_confirmed': False}
        state['capture_schema'] = 'citizen-captures/v1'
        sources = {component: source_excerpt(component) for component in SOURCES if '/' not in component}
        state['source_revision'] = next((r.get('revision') for r in sources.values() if r.get('revision')), None)
        state['source_hashes'] = {r['path']: r['sha256'] for r in sources.values() if r.get('available')}
        if spec.scenario_id == 'dreamjob':
            for relative in ['src/learning_lab/retail.py', 'src/learning_lab/retail_checks.py',
                'src/learning_lab/retail_experiments.py', 'src/learning_lab/retail_managed.py',
                'src/learning_lab/probe.py', 'integrations/designer/retail_situation.py',
                'integrations/designer/learning_preferences.py', 'integrations/designer/profiling_compat.py',
                'integrations/platform/retail_resources.py', 'integrations/platform/retail_evaluate.py',
                'integrations/platform/package_agent.py', 'integrations/helix/evaluate.py',
                'src/learning_lab/retail_policy.py', 'integrations/proxy/retail-litellm.yaml',
                'integrations/proxy/lab_routing.py']:
                state['source_hashes'][relative] = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        write_json(folder / 'run.json', state)
        self.tasks[run_id] = asyncio.create_task(self._execute(state, lock))
        return self.get(run_id)

    async def _execute(self, state, lock):
        run_id = state['run_id']
        folder, budget, native = self.folder(run_id), Budget(), None
        conversation = []
        catalogue = folder / 'catalogue-snapshot.json'
        if state['scenario_id'] == 'dreamjob':
            state['verification'] = {key: {'status': 'not_run', 'verified': False}
                                     for key in ['helix_job', 'routing', 'managed']}

        def stop_for_review(operation, reason):
            state.update(stopped_at=operation, requires_user_review=True, stop_reason=reason)

        def persist(stage=None):
            if stage:
                state['stage'] = stage
            state['calls'] = budget.calls
            write_json(folder / 'run.json', state)
            write_json(folder / 'usage.json', {'calls': budget.calls, 'records': budget.records})

        async def event(value):
            save_evidence(folder / 'events.jsonl', {'at': now(), 'run_id': run_id, **value}, append=True)
            if value.get('role') in {'user', 'assistant'}:
                conversation.append({'turn': (len(conversation) // 2) + 1, **value})
                write_json(folder / 'public-conversation.json', conversation)
            persist('run')

        async def activation(value):
            save_evidence(folder / 'usersim-activations.jsonl', {'at': now(), **value}, append=True)
            persist()

        async def progress():
            while True:
                await asyncio.sleep(1)
                persist()

        watcher = asyncio.create_task(progress())

        try:
            state.update(status='running', started_at=now())
            retail = state['scenario_id'] == 'dreamjob'
            source = lock['records'][0]
            from .ngc_personas import CATALOGUE_URL
            write_json(folder / 'source-lock.json', {'source': source['source'], 'source_id': source['source_id'],
                       'source_revision': source['source_revision'], 'original_sha256': source['original_profile_sha256'],
                       'lock_sha256': lock['lock_sha256'], 'kind': 'immutable original',
                       'source_url': CATALOGUE_URL if source['source'] == 'ngc' else 'https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore/viewer',
                       'conditioning': 'Original synthetic OCEAN fields' if source['source'] == 'ngc' else 'Profile-only; no OCEAN fields'})
            if retail:
                from .retail import RetailPublicContext, create_retail_situation, freeze_retail_catalogue
                state['catalogue_sha256'] = freeze_retail_catalogue(catalogue)
            else:
                state['catalogue_sha256'] = freeze_catalogue(catalogue)
            situation = ({'goal': 'beginner photography', 'day': 'Saturday', 'budget_sgd': 50}
                         if state['scenario_id'] == 'photography' else
                         {'goal': 'retail sales/inventory analysis; explore the SMU programme, then shorter options',
                          'salary_disclosure': 'hypothetical S$2500–3499 monthly range only in public turn 2',
                          'budget_disclosure': 'S$3000 total training limit and weekends only in public turn 3'} if retail else
                         {'goal': 'learn to play board games', 'followup': 'Is video-game design the same as playing board games?',
                          'expected': 'Honest no-match in this frozen catalogue; no design-course substitution.'})
            write_json(folder / 'situation.json', {'kind': 'source-seeded Designer overlay with authored disclosure protocol' if retail else 'authored situation; Designer intentionally skipped', **situation,
                       'disclosure': 'The advisor receives only what the public user messages state.'})
            # Exact resolved native UserSim input stays private; not an advisor input.
            preset = PRESETS[state['scenario_id']]
            persist('build')
            from .course_mcp import TOOL_NAMES
            allowed_tools = TOOL_NAMES if preset.harness == 'deepagents' else [f'mcp__catalogue__{name}' for name in TOOL_NAMES]
            public_context = RetailPublicContext(folder) if retail else None
            async with Gateway(budget, mode='live', model_route='fixed', allowed_tool_names=allowed_tools,
                               on_request=public_context.audit if public_context else None,
                               evidence_dir=folder, fail_on_truncated_output=retail).serving() as gateway:
                selected = await create_retail_situation(lock, folder, gateway) if retail else lock
                rows = prepare_rows(state['spec']['source'], 1, preset.public_turns, source_ids=[source['source_id']],
                                    story_id=state['scenario_id'], profiles_selection=selected)
                write_json(folder / 'resolved-inputs.json', rows)
                native = NativeSandbox(run_id, folder / state['episode_id'], gateway, catalogue=catalogue,
                                       scenario_id=state['scenario_id'], harness=preset.harness)
                async with native:
                    state['native_thread_id'] = native.thread_id
                    persist('run')
                    result = await hosted_episode(rows[0], gateway, PublicTarget(native, folder, state['scenario_id'], public_context), event,
                                                   on_activation=activation,
                                                   model_config_path=folder / 'usersim-model-config.json')
                    write_json(folder / 'usersim-result.json', result)
                    outcome = result.get('simulation_outcome', {})
                    if isinstance(outcome, str):
                        outcome = json.loads(outcome)
                    state['usersim_outcome'] = outcome
                    if outcome.get('status', 'ok') not in {'ok', 'max_turns_reached'}:
                        state['usersim_notice'] = 'Inspect the native UserSim outcome; transport completion is separate.'
                    if state['scenario_id'] != 'photography':
                        probe = await native.probe_safeguards()
                        write_json(folder / 'guardrails-probe.json', probe)
                        if probe['native_result']['status'] != 'blocked':
                            raise RuntimeError('The separate native Guardrails negative probe was not blocked')
            persist('evaluate')
            from .journey_checks import evaluate_boardgames, evaluate_photography
            tools = native_tool_records(folder / state['episode_id'] / 'native')
            if retail:
                from .retail_checks import evaluate_retail
                from .retail_experiments import score_with_helix, durable_evaluation, compare_routing, evaluation_verified
                from .retail_managed import run_managed_retail
                evaluation = await score_with_helix(evaluate_retail(conversation, catalogue, tools,
                    json.loads((folder / 'source-lock.json').read_text()), folder), folder)
                write_json(folder / 'evaluation.json', evaluation)
                state.update(baseline_status='completed' if evaluation_verified(evaluation) else 'failed',
                             evaluation_passed=evaluation['passed'], evaluation_total=evaluation['total'])
                if state['baseline_status'] != 'completed':
                    reason = 'Retail baseline evaluation failed; review its criteria before any later condition.'
                    stop_for_review('baseline', reason)
                    persist()
                    raise RuntimeError(reason)
                # Saved scoring, routing and managed execution each retain their
                # own evidence. Every failed condition stops later execution.
                for key, operation in [('helix_job', lambda: durable_evaluation(folder)),
                    ('routing', lambda: compare_routing(state, folder, budget, conversation, catalogue)),
                    ('managed', lambda: run_managed_retail(state, folder, budget, catalogue))]:
                    persist('routing' if key == 'routing' else 'deploy' if key == 'managed' else 'evaluate')
                    state['verification'][key] = {'status': 'running', 'verified': False}
                    persist()
                    try:
                        evidence = await operation()
                        state['verification'][key] = {'verified': evidence.get('verified', evidence.get('status') == 'completed'),
                                                       'status': evidence.get('status', 'recorded'),
                                                       **{name: evidence[name] for name in ['diagnostic_verified', 'provider_notice'] if name in evidence}}
                        if not state['verification'][key]['verified']:
                            state['verification'][key]['status'] = 'failed'
                            raise RuntimeError(f'Retail {key} verification failed; review its saved evidence before continuing.')
                    except asyncio.CancelledError:
                        state['verification'][key] = {'status': 'cancelled', 'verified': False}
                        stop_for_review(key, 'Execution was cancelled; later conditions were not started.')
                        persist()
                        raise
                    except Exception as exc:
                        state['verification'][key] = {**state['verification'][key], 'verified': False,
                                                       'status': 'failed', 'error_type': type(exc).__name__,
                                                       'error': str(sanitize(str(exc)))[:1000]}
                        stop_for_review(key, str(sanitize(str(exc)))[:1000])
                        persist()
                        raise
                    persist()
            else:
                evaluator = evaluate_photography if state['scenario_id'] == 'photography' else evaluate_boardgames
                evaluation = evaluator(conversation, catalogue, tools,
                                       json.loads((folder / 'source-lock.json').read_text()))
            write_json(folder / 'evaluation.json', evaluation)
            state.update(status='completed' if all(r['status'] == 'pass' for r in evaluation['rows']) else 'failed',
                         evaluation_passed=evaluation['passed'], evaluation_total=evaluation['total'])
            state.setdefault('baseline_status', state['status'])
            if retail and not all(result.get('verified') for result in state.get('verification', {}).values()):
                state['status'] = 'failed'
            if state['status'] == 'failed' and not state.get('requires_user_review'):
                stop_for_review('baseline', 'Application evaluation failed; review the saved criteria before continuing.')
        except asyncio.CancelledError:
            state.update(status='cancelled', error='Cancelled explicitly; partial evidence is preserved.')
            if not state.get('requires_user_review'):
                stop_for_review(state['stage'], state['error'])
        except Exception as exc:
            state.update(status='failed', error=str(sanitize(type(exc).__name__ + ': ' + str(exc)))[:1200])
            state.setdefault('baseline_status', 'failed')
            if not state.get('requires_user_review'):
                stop_for_review(state['stage'], state['error'])
        finally:
            watcher.cancel()
            await asyncio.gather(watcher, return_exceptions=True)
            episode = folder / state['episode_id']
            cleanup = episode / 'cleanup.json'
            confirmed = bool(cleanup.is_file() and json.loads(cleanup.read_text()).get('native_absence_confirmed'))
            if native is None:
                confirmed = True  # No native creation was attempted.
            confirmed = confirmed and self._auxiliary_cleanup(state, folder)
            state.update(cleanup_confirmed=confirmed, ended_at=now())
            if not confirmed:
                state.update(status='failed', recovery_required=True)
                if not state.get('requires_user_review'):
                    stop_for_review(state['stage'], 'Native cleanup is unconfirmed; resolve ownership before continuing.')
            if state.get('capture_schema'):
                from .captures import write_capture_manifest
                try:
                    capture = write_capture_manifest(folder, state)
                    state['capture_coverage'] = capture['coverage']
                    if not capture['coverage']['complete'] and state['status'] == 'completed':
                        state['status'] = 'failed'
                        stop_for_review('capture', 'Required captures are incomplete; inspect coverage before continuing.')
                except Exception as exc:
                    state['capture_coverage'] = {'complete': False, 'error_type': type(exc).__name__}
                    if state['status'] == 'completed':
                        state['status'] = 'failed'
                        stop_for_review('capture', 'Capture manifest generation failed; inspect the saved run before continuing.')
            persist('deploy' if state['status'] == 'completed' else None)
            self._release(run_id, confirmed)

    @staticmethod
    def _auxiliary_cleanup(state, folder):
        for identity in state.get('comparison_conditions', []):
            work = folder / 'comparisons' / str(uuid.UUID(identity)) / 'runtime'
            if (work / 'sandbox-identity.json').exists():
                cleanup = work / 'cleanup.json'
                if not cleanup.is_file() or not json.loads(cleanup.read_text()).get('native_absence_confirmed'):
                    return False
        managed = state.get('managed_condition_id')
        if managed:
            work = folder / 'managed' / str(uuid.UUID(managed)) / 'condition.json'
            if work.is_file():
                receipt = json.loads(work.read_text())
                if receipt.get('resource_creation_attempted') and not receipt.get('cleanup_confirmed'):
                    return False
        return True

    async def cancel(self, run_id):
        state = self.get(run_id)
        if state.get('recording'):
            raise ValueError('A fixed recording cannot be cancelled')
        task = self.tasks.get(run_id)
        if not task and state['status'] not in TERMINAL:
            raise ValueError('This worker does not own that live run; use its owner or explicit recovery')
        if task and not task.done():
            task.cancel()
        return {'run_id': run_id, 'cancellation_requested': bool(task and not task.done())}

    async def recover(self, run_id):
        state = self.get(run_id)
        if state.get('recording'):
            raise ValueError('A fixed recording has no live workload to recover')
        if run_id in self.tasks and not self.tasks[run_id].done():
            raise ValueError('Cancel the active run and wait for cleanup before recovery')
        try:
            os.kill(int(state['owner_pid']), 0)
        except ProcessLookupError:
            pass
        else:
            if state['owner_pid'] != os.getpid():
                raise ValueError('The recorded owner is alive; do not steal its workload')
        native = NativeSandbox(run_id, self.folder(run_id) / state['episode_id'], None,
                               catalogue=self.folder(run_id) / 'catalogue-snapshot.json')
        identity = native.folder / 'sandbox-identity.json'
        if identity.is_file():
            native.identity = json.loads(identity.read_text())
            if native.identity.get('name'):
                native.name = native.identity['name']
        await native.cleanup_native()
        for other_id in state.get('comparison_conditions', []):
            other = NativeSandbox(other_id, self.folder(run_id) / 'comparisons' / str(uuid.UUID(other_id)) / 'runtime', None,
                                  catalogue=self.folder(run_id) / 'catalogue-snapshot.json', scenario_id='dreamjob')
            record = other.folder / 'sandbox-identity.json'
            if record.is_file():
                other.identity = json.loads(record.read_text())
                other.name = other.identity.get('name', other.name)
                await other.cleanup_native()
        if not self._auxiliary_cleanup(state, self.folder(run_id)):
            raise ValueError('The managed condition still needs its recorded Helix session/deployment recovery; ownership is retained')
        state.update(status='interrupted' if state['status'] not in TERMINAL else state['status'],
                     cleanup_confirmed=True, recovery_required=False, recovered_at=now())
        state.pop('owned_by_this_worker', None)
        write_json(self.folder(run_id) / 'run.json', state)
        self._release(run_id, True)
        return self.get(run_id)

    def artifacts(self, run_id):
        if recordings.load(run_id) is not None:
            scenario_id = recordings.load(run_id)['scenario_id']
            return {'run_id':run_id, 'scenario_id':scenario_id, 'directory':f'recordings/{scenario_id}/{run_id}',
                    'artifacts':recordings.artifacts(run_id)}
        state, folder = self.get(run_id), self.folder(run_id)
        records = []
        for path in sorted(folder.rglob('*')):
            if not path.is_file() or path.is_symlink() or path.name not in ARTIFACT_NAMES:
                continue
            relative = path.relative_to(folder).as_posix()
            if 'designer-private' in path.relative_to(folder).parts:
                continue
            if any(parent.is_symlink() for parent in path.parents if parent.is_relative_to(folder)):
                continue
            artifact_id = hashlib.sha256((run_id + ':' + relative).encode()).hexdigest()[:24]
            records.append({'id': artifact_id, 'path': relative,
                            'bytes': path.stat().st_size,
                            'url': f'/api/journey/artifact?run_id={run_id}&artifact_id=' + artifact_id})
        return {'run_id': run_id, 'scenario_id': state['scenario_id'], 'directory': state['run_directory'], 'artifacts': records}

    def artifact(self, run_id, artifact_id):
        if recordings.load(run_id) is not None:
            return recordings.artifact(run_id, artifact_id)
        record = next((r for r in self.artifacts(run_id)['artifacts'] if r['id'] == artifact_id), None)
        if record is None:
            raise ValueError('Artifact does not belong to the selected scenario run')
        path = self.folder(run_id) / record['path']
        raw = path.read_bytes()
        clipped = raw[:1024 * 1024].decode(errors='replace')
        try:
            content = sanitize(json.loads(clipped))
        except ValueError:
            # YAML/JSONL text is redacted before a bounded local browser preview.
            content = sanitize(clipped)
        return {**record, 'run_id': run_id, 'scenario_id': self.get(run_id)['scenario_id'],
                'content': content, 'truncated': len(raw) > 1024 * 1024,
                'sha256': hashlib.sha256(raw).hexdigest()}

    def trace(self, run_id):
        recorded = recordings.trace(run_id)
        if recorded is not None:
            return {**recorded, 'inference_calls_for_inspection':0}
        state = self.get(run_id)
        folder = self.folder(run_id)

        def read(name, default):
            path = folder / name
            return json.loads(path.read_text()) if path.is_file() else default

        return {'run': state, 'artifacts': self.artifacts(run_id)['artifacts'],
                'conversation': read('public-conversation.json', []), 'source_lock': read('source-lock.json', None),
                'situation': read('situation.json', None), 'usage': read('usage.json', {'calls': 0, 'records': []}),
                'evaluation': read('evaluation.json', None),
                'developer_review': read('review-notes.json', None),
                'relay': relay_scopes(folder / state['episode_id'] / 'native'),
                'tools': native_tool_records(folder / state['episode_id'] / 'native'),
                'repository_url': repository_url(), 'inference_calls_for_inspection': 0}

    async def dispatch(self, params):
        params = dict(params)
        action = params.pop('action', None)
        keys = {'presets': set(), 'readiness': set(), 'sample': {'source'}, 'start': {'spec'}, 'list': {'scenario_id'},
                'lesson': {'scenario_id'}, 'demo-persona': {'scenario_id'}, 'metadata': {'scenario_id'},
                'execution': {'scenario_id', 'condition_id', 'public_turn'},
                'get': {'run_id'}, 'trace': {'run_id'}, 'cancel': {'run_id'}, 'recover': {'run_id'},
                'source': {'component', 'module'}, 'artifacts': {'run_id'}, 'artifact': {'run_id', 'artifact_id'}}
        if action not in keys or set(params) - keys[action]:
            raise ValueError('Unknown guide operation or unexpected fields')
        if action == 'presets':
            return scenario_presets()
        if action in {'lesson', 'demo-persona'}:
            from .guide_lessons import demo_persona, lesson_context
            return browser_projection((lesson_context if action == 'lesson' else demo_persona)(**params))
        if action == 'metadata':
            from .guide_metadata import metadata
            return metadata(**params)
        if action == 'execution':
            from .guide_execution import execution
            return execution(**params)
        if action == 'readiness':
            return await self.readiness()
        if action == 'sample':
            return self.sample(**params)
        if action == 'start':
            return await self.start(params['spec'])
        if action in {'cancel', 'recover'}:
            return await getattr(self, action)(**params)
        if action == 'source':
            return source_excerpt(**params)
        return browser_projection(getattr(self, action)(**params))

    async def close(self):
        for task in self.tasks.values():
            if not task.done():
                task.cancel()
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)
