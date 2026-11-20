"""A new Helix-managed condition with explicitly selected public constraints."""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
import secrets
import uuid

from .behavioural_safeguards import BehaviouralSafeguards
from .course_mcp import TOOL_NAMES
from .deployment import DeploymentInferenceBridge, PlatformBridge, PlatformUnavailable
from .evidence import save_evidence
from .inference import Gateway
from .outcomes import require_valid_answer
from .retail import RetailPublicContext
from .sandbox import NativeSandbox
from .settings import ROOT

IMAGE = 'citizen-retail-helix:0.4.0'
AGENT = 'citizen-retail-advisor-deepagents-v1'


def publishable_intake(logs: dict) -> dict:
    """Keep native relationships and decoded public tool facts, never model payloads."""
    intake = logs.get('intake') or {}
    spans, tools = [], []
    for row in intake.get('spans', []):
        spans.append({key: row[key] for key in ['span_id', 'parent_span_id', 'trace_id', 'kind', 'name',
            'source', 'status', 'error_type', 'started_at', 'ended_at', 'provider', 'model',
            'tool_name', 'input_tokens', 'output_tokens', 'total_tokens'] if key in row})
        if row.get('name') not in TOOL_NAMES:
            continue
        request, result = {}, None
        try:
            request = json.loads(row.get('input') or '{}')
            raw = json.loads(row.get('output') or '{}')
            content = raw.get('content') or []
            if content and content[0].get('type') == 'text':
                result = json.loads(content[0]['text'])
        except (ValueError, TypeError, KeyError):
            pass
        tools.append({'name': row['name'], 'source_span_id': row['span_id'], 'native_status': row.get('status'),
            'arguments': request.get('arguments'), 'result': result,
            'evidence_origin': 'native_helix_intake',
            'result_state': 'unavailable' if result is None else 'domain_error' if isinstance(result, dict) and result.get('error') else 'returned'})
    return {'source': 'native-helix-intake', 'status': intake.get('status', 'unavailable'),
        'session_identity': intake.get('session_identity'), 'spans': spans, 'tools': tools,
        'notice': 'Native Intake IDs/parents/status retained. Model prompts/reasoning and arbitrary payloads omitted. A successful span alone does not prove a valid tool result; gateway calls have separate identities.'}


async def run_managed_retail(state: dict, folder: Path, budget, catalogue: Path) -> dict:
    constraints = [json.loads(line) for line in (folder / 'public-constraints.jsonl').read_text().splitlines()]
    public = constraints[-1]['preferences']
    if public['budget_sgd'] != 3000 or public['days'] != [5, 6]:
        raise ValueError('The managed public preset must match the explicitly disclosed spending/weekend constraints')
    condition = str(uuid.uuid4())
    work = folder / 'managed' / condition
    work.mkdir(parents=True)
    state['managed_condition_id'] = condition
    receipt = {'condition_id': condition, 'parent_run_id': state['run_id'], 'status': 'preparing',
        'fresh_session': True, 'public_preferences': public, 'private_persona_in_image': False,
        'local_memory_resumed': False, 'cleanup_confirmed': False, 'image': IMAGE,
        'input_kind': 'developer-selected public constraints for a new managed condition; not a new UserSim turn',
        'guardrails_location': 'host caller boundary for this managed condition; local baseline rails execute inside its own sandbox'}

    def persist():
        save_evidence(work / 'condition.json', receipt)
        save_evidence(folder / 'platform-condition.json', receipt)

    persist()
    bridge = PlatformBridge()
    if bridge.spec.target != 'local':
        raise ValueError('This managed reference requires the explicitly configured local Platform')
    bundle = ROOT / 'integrations/platform/.bundle/dreamjob-deepagents'
    manifest = json.loads((bundle / 'source-manifest.json').read_text())
    if not manifest.get('built') or manifest.get('image') != IMAGE:
        raise ValueError('Build the new retail Helix package before managed execution')
    if manifest.get('catalogue_sha256') != hashlib.sha256(catalogue.read_bytes()).hexdigest():
        raise ValueError('The managed image catalogue does not match the selected frozen facts')
    save_evidence(folder / 'platform-package.json', manifest)
    deployment = 'citizen-retail-' + uuid.UUID(condition).hex[:12]
    agent = deployment + '-agent'
    receipt.update(agent=agent, deployment_name=deployment, stage='resource_setup')
    persist()
    old_key = os.environ.get('LAB_DEPLOYMENT_GATEWAY_KEY')
    key = secrets.token_urlsafe(32)
    os.environ['LAB_DEPLOYMENT_GATEWAY_KEY'] = key
    session_id, registered, deployed, configured, inspector = None, False, False, False, None
    cleanup_errors = []
    public_context = RetailPublicContext(work)
    message = ('I want to learn retail sales and inventory analysis. For this new managed condition, '
               'my explicitly selected total training budget is S$3,000 and I can study on weekends only. '
               'Please compare the SMU data communications/visualisation programme with shorter analysis or Excel options. '
               'Use published facts and explain what still needs confirmation; no job or funding outcome is assumed.')
    preferences = public_context.accept(message)

    async def mutate(operation, remember=None, **arguments):
        # Do not lose a resource identity if cancellation arrives after the
        # server has created it but before its response reaches this caller.
        pending = asyncio.create_task(bridge.call(operation, **arguments))
        cancelled = False
        try:
            result = await asyncio.shield(pending)
        except asyncio.CancelledError:
            cancelled = True
            result = await pending
        if remember:
            remember(result)
        if cancelled:
            raise asyncio.CancelledError
        return result

    def remember_registration(result):
        nonlocal registered
        registered = not result.get('registration_reused', False)
        receipt['registration_created'] = registered
        save_evidence(folder / 'platform-registration.json', result)
        persist()

    def remember_session(result):
        nonlocal session_id
        session_id = result['session_identity']['resource_name']
        receipt['session_id'] = session_id
        save_evidence(folder / 'platform-session.json', result)
        persist()

    try:
        async with Gateway(budget, mode='live', allowed_tool_names=TOOL_NAMES, on_request=public_context.audit).serving() as gateway:
            admission = DeploymentInferenceBridge(key=key, model_aliases=['citizen-retail-advisor'])
            async with admission.serving(port=8876):
                await admission.activate(condition, gateway, preferences.model_dump(mode='json'))
                try:
                    # Intent is saved before the first resource mutation. Names
                    # derive only from this condition's server-generated UUID.
                    configured = True
                    receipt['resource_creation_attempted'] = True
                    persist()
                    setup = await mutate('retail_setup', run_id=condition, provider_url=admission.url)
                    save_evidence(folder / 'platform-setup.json', setup)
                    receipt['stage'] = 'registration'
                    persist()
                    await mutate('register', remember=remember_registration, harness='deepagents', scenario_id='dreamjob',
                                 name=agent, run_id=condition)
                    deployed = True  # Persist exact intent even if the create reply is interrupted.
                    receipt['stage'] = 'deployment'
                    persist()
                    deployment_result = await mutate('deploy', agent=agent, name=deployment, image=IMAGE,
                                                     environment=setup['environment_qualified'], mode='openshell')
                    for _ in range(60):
                        if deployment_result.get('ready'):
                            break
                        if deployment_result.get('deployment', {}).get('status') == 'failed':
                            raise RuntimeError('The managed deployment failed; inspect its native status')
                        await asyncio.sleep(2)
                        deployment_result = await bridge.call('deployment', name=deployment)
                        save_evidence(folder / 'platform-deployment.json', deployment_result)
                    if not deployment_result.get('ready'):
                        raise TimeoutError('The managed deployment did not become ready within its bounded window')
                    save_evidence(folder / 'platform-deployment.json', deployment_result)
                    # Borrow only native CLI read/probe methods. Helix retains
                    # lifecycle ownership; this object never creates/deletes it.
                    inspector = NativeSandbox(condition, work, None, catalogue=catalogue)
                    inventory = json.loads(await inspector.cli('sandbox', 'list', '-o', 'json'))
                    matches = [s for s in inventory.get('sandboxes', [])
                        if s.get('labels', {}).get('nemo.nvidia.com/deployment-name') == deployment
                        and s.get('labels', {}).get('nemo.nvidia.com/deployment-workspace') == bridge.spec.workspace]
                    if len(matches) != 1:
                        raise ValueError('No unique native sandbox matches the owned Helix deployment')
                    inspector.name, inspector.identity = matches[0]['name'], {'id': matches[0]['id']}
                    receipt['sandbox'] = {key: matches[0].get(key) for key in ['id', 'name', 'labels']}
                    persist()
                    policy = await inspector.cli('sandbox', 'get', inspector.name, '--policy-only')
                    (folder / 'platform-effective-policy.yaml').write_text(policy)
                    full_policy = json.loads(await inspector.cli('policy', 'get', inspector.name, '--full', '-o', 'json'))
                    save_evidence(folder / 'platform-effective-policy.json', full_policy)
                    await inspector.probe_boundary('/workspace/.venv/bin/python')
                    save_evidence(folder / 'platform-boundary-probes.json', json.loads((work / 'boundary-probes.json').read_text()))
                    receipt['stage'] = 'session'
                    persist()
                    await mutate('sessions_create', remember=remember_session, deployment=deployment,
                                 name=deployment + '-review')
                    async with BehaviouralSafeguards(work, location='host public caller of the separate Helix-managed condition') as rails:
                        check = await rails.check('input', message, purpose='separate managed condition')
                        if check['native_result']['status'] != 'passed':
                            raise ValueError('The managed public input did not pass its configured check')
                        receipt['stage'] = 'invoke'
                        persist()
                        result = await bridge.call('invoke', deployment=deployment, session_id=session_id, input=message)
                        response = result['response']
                        content = (response.get('choices') or [{}])[0].get('message', {}).get('content')
                        content = require_valid_answer(content)
                        checked = await rails.check('output', content, purpose='separate managed condition')
                        if checked['native_result']['status'] != 'passed':
                            raise ValueError('The managed reply did not pass its configured check')
                    save_evidence(folder / 'platform-invocation.json', {'public_input': message, **result})
                    logs = await bridge.call('logs', name=deployment, session_id=session_id, tail=100)
                    save_evidence(work / 'native-platform-logs.json', logs)
                    save_evidence(folder / 'platform-trace.json', publishable_intake(logs))
                    receipt.update(status='completed', reply=content, session_id=session_id, stage='cleanup')
                    persist()
                finally:
                    await admission.deactivate(condition)
    except asyncio.CancelledError:
        receipt.update(status='cancelled', stage='cleanup')
        persist()
        raise
    except Exception as exc:
        receipt.update(status='failed', error_type=type(exc).__name__, error=str(exc)[:1200])
        persist()
        if deployed:
            try:
                logs = await bridge.call('logs', name=deployment,
                                         **({'session_id': session_id} if session_id else {}), tail=100)
                save_evidence(work / 'native-platform-logs.json', logs)
                save_evidence(folder / 'platform-trace.json', publishable_intake(logs))
            except Exception as log_error:
                receipt['log_error_type'] = type(log_error).__name__
                persist()
    finally:
        if session_id:
            try:
                closed = await bridge.call('sessions_close', session_id=session_id, require_runtime_drain=True)
                save_evidence(folder / 'platform-session-close.json', closed)
            except Exception as exc:
                cleanup_errors.append('session: ' + str(exc)[:400])
        if deployed:
            try:
                try:
                    await bridge.call('undeploy', name=deployment)
                except PlatformUnavailable as exc:
                    if not any(marker in str(exc).lower() for marker in ['not found', 'notfound', '404']):
                        raise
                for _ in range(30):
                    try:
                        await bridge.call('deployment', name=deployment)
                    except PlatformUnavailable as exc:
                        if any(marker in str(exc).lower() for marker in ['not found', 'notfound', '404']):
                            break
                        raise
                    await asyncio.sleep(1)
                else:
                    raise RuntimeError('Managed deployment absence is not confirmed')
                if inspector and inspector.identity:
                    inventory = json.loads(await inspector.cli('sandbox', 'list', '-o', 'json'))
                    if any(s.get('id') == inspector.identity['id'] or s.get('name') == inspector.name for s in inventory.get('sandboxes', [])):
                        raise RuntimeError('The managed native sandbox remains present')
            except Exception as exc:
                cleanup_errors.append('deployment: ' + str(exc)[:400])
        if registered and not cleanup_errors:
            try:
                await bridge.call('delete_agent', name=agent)
                for _ in range(30):
                    try:
                        await bridge.call('agent', name=agent)
                    except PlatformUnavailable as exc:
                        if any(marker in str(exc).lower() for marker in ['not found', 'notfound', '404']):
                            break
                        raise
                    await asyncio.sleep(1)
                else:
                    raise RuntimeError('Owned registration absence is not confirmed')
            except Exception as exc:
                cleanup_errors.append('registration: ' + str(exc)[:400])
        if configured and not cleanup_errors:
            try:
                cleanup = await bridge.call('retail_cleanup', run_id=condition)
                save_evidence(work / 'resource-cleanup.json', cleanup)
            except Exception as exc:
                cleanup_errors.append('resources: ' + str(exc)[:400])
        if old_key is None:
            os.environ.pop('LAB_DEPLOYMENT_GATEWAY_KEY', None)
        else:
            os.environ['LAB_DEPLOYMENT_GATEWAY_KEY'] = old_key
        receipt.update(cleanup_confirmed=not cleanup_errors, cleanup_errors=cleanup_errors)
        save_evidence(folder / 'platform-cleanup.json', {'condition_id': condition,
            'native_absence_confirmed': not cleanup_errors, 'errors': cleanup_errors,
            'deployment_name': deployment, 'session_id': session_id})
        persist()
    if not receipt['cleanup_confirmed']:
        raise RuntimeError('Managed condition retains unresolved ownership; preserve its records and run guard')
    return receipt
