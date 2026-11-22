"""Saved-response scoring and controlled, fresh-memory routing comparisons."""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import uuid

from .course_mcp import TOOL_NAMES
from .evidence import native_tool_records, save_evidence
from .inference import Gateway
from .journey_checks import valid_native_search
from .retail import RetailPublicContext
from .retail_checks import evaluate_retail
from .sandbox import NativeSandbox
from .settings import ROOT

COMPARISON_LABELS = ('fixed-candidate', 'switchyard', 'capable-access',
                     'available-fixed', 'available-switchyard')


async def routing_configuration(folder: Path) -> dict:
    """Read only model IDs/ownership from the two installed local proxies."""
    inventories = {}
    for name in ['citizen-retail-proxy-v1', 'proxy-litellm-1']:
        process = await asyncio.create_subprocess_exec('docker', 'inspect', name,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        out, _ = await asyncio.wait_for(process.communicate(), 10)
        if process.returncode:
            raise ValueError('A selected local comparison proxy is unavailable')
        observed = json.loads(out)[0]
        values = dict(item.split('=', 1) for item in observed['Config']['Env'] if '=' in item)
        models = {role: values.get('LAB_' + role + '_MODEL') for role in ['FIXED', 'SUPPORT', 'EFFICIENT', 'CAPABLE']}
        if not all(models.values()) or models['EFFICIENT'] == models['CAPABLE']:
            raise ValueError('The selected proxy must expose two distinct explicit candidate models')
        if name == 'proxy-litellm-1' and models['SUPPORT'] != models['EFFICIENT']:
            raise ValueError('The fixed diagnostic must use the efficient candidate from the same pool')
        inventories[name] = {'container_id': observed['Id'], 'image_id': observed['Image'], 'models': models}
    configuration = {'inventories': inventories,
        'policy': {'picker': 'efficient_first', 'confidence_threshold': .5, 'recent_window': 3,
                   'only_on_wrong_signal_escalation': True},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in ['integrations/proxy/retail-litellm.yaml', 'integrations/proxy/litellm.yaml', 'integrations/proxy/lab_routing.py']},
        'notice': 'Declared inventory and policy are configuration. Completed calls/native decisions separately establish observed behaviour.'}
    access = ROOT / '.private/verification/scenario3-tool-access.json'
    if access.is_file():
        configuration['endpoint_probe'] = json.loads(access.read_text())
    recheck = ROOT / '.private/verification/scenario3-glm-tool-access-300.json'
    if recheck.is_file():
        configuration['later_glm_tool_recheck'] = json.loads(recheck.read_text())
    save_evidence(folder / 'routing-configuration.json', configuration)
    return configuration


async def score_with_helix(evaluation: dict, folder: Path) -> dict:
    from .evaluation import run_helix
    criteria = [{'case_id': row['id'], 'condition': 'retail-learning',
                 'expected': json.dumps(row['expected'], sort_keys=True),
                 'output': json.dumps(row['actual'], sort_keys=True)} for row in evaluation['rows']]
    source, destination = folder / 'helix-criteria.json', folder / 'helix-evaluation.json'
    save_evidence(source, criteria)
    receipt = await run_helix(source, destination)
    native = json.loads(destination.read_text())
    scores = {row['item']['case_id']: row for row in native['row_scores']}
    if len(scores) != len(criteria):
        raise ValueError('Helix did not return one attributable score for every criterion')
    for row in evaluation['rows']:
        native_row = scores[row['id']]
        row['helix_row_index'] = native_row['row_index']
        row['helix_score'] = native_row['metrics']['exact-match'][0]['value']
        row['status'] = ('error' if native_row.get('metric_errors') else
                         'pass' if row['helix_score'] == 1 else 'fail')
    evaluation.update(helix_used=True, passed=sum(row['status'] == 'pass' for row in evaluation['rows']),
                      native_result='helix-evaluation.json', sdk_version=receipt['version'],
                      metric='ExactMatchMetric over explicit application-defined values')
    return evaluation


async def durable_evaluation(folder: Path) -> dict:
    from .deployment import PlatformSpec
    spec = PlatformSpec.configured()
    env = {k: v for k, v in os.environ.items() if not re.search(r'KEY|TOKEN|SECRET|PASSWORD', k, re.I)}
    if spec.token_env and os.getenv(spec.token_env):
        env[spec.token_env] = os.environ[spec.token_env]
    process = await asyncio.create_subprocess_exec(str(ROOT / 'integrations/platform/.venv/bin/python'),
        str(ROOT / 'integrations/platform/retail_evaluate.py'), str(folder / 'helix-criteria.json'),
        str(folder / 'helix-job.json'), spec.model_dump_json(), env=env, cwd=ROOT,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        out, error = await asyncio.wait_for(process.communicate(), 300)
    except BaseException:
        process.kill()
        await process.wait()
        raise
    (folder / 'helix-job.stderr').write_bytes(out + b'\n' + error)
    if process.returncode:
        raise RuntimeError('The durable Helix evaluation job failed; inspect helix-job.json and its native status')
    return json.loads((folder / 'helix-job.json').read_text())


def evaluation_verified(evaluation: dict) -> bool:
    """Only a complete set of passing native scores verifies these criteria."""
    criteria = evaluation.get('rows') or []
    return bool(evaluation.get('helix_used') and criteria
        and evaluation.get('total') == len(criteria) and evaluation.get('passed') == len(criteria)
        and all(row.get('status') == 'pass' and row.get('helix_score') == 1 for row in criteria))


def condition_verification(receipt: dict, tools: list[dict]) -> dict:
    """Keep execution, criteria, native tools and observed model coverage distinct."""
    evaluated = evaluation_verified(receipt.get('evaluation') or {})
    searches = [tool for tool in tools if valid_native_search(tool)]
    calls = [row for row in receipt.get('usage', [])
             if row.get('role') == 'assistant' and row.get('status') == 'completed']
    selected = sorted({row['selected_model'] for row in calls if row.get('selected_model')})
    executed = receipt.get('execution_status') == 'completed'
    routed = receipt.get('route') == 'switchyard'
    return {'execution_verified': executed, 'evaluation_verified': evaluated,
        'evaluation_scope': 'Application-delivered responses, not native proposal quality or a model ranking.',
        'proposal_review': (receipt.get('evaluation') or {}).get('delivery_review', []),
        'native_course_searches': len(searches),
        'native_course_scope_uuids': [tool['scope_uuid'] for tool in searches if tool.get('scope_uuid')],
        'actual_selected_models': selected,
        'verified': bool(executed and evaluated and searches and selected and receipt.get('cleanup_confirmed')
                         and (not routed or receipt.get('native_decisions')))}


def comparison_summary(receipts: list[dict], configuration: dict) -> dict:
    """A successful routing comparison does not prove every candidate was invoked."""
    configured = configuration['inventories']['citizen-retail-proxy-v1']['models']
    by_label = {row['label']: row for row in receipts}

    def provider_model(model):
        return model.removeprefix('openai/')

    candidates = {provider_model(configured[role]) for role in ['EFFICIENT', 'CAPABLE']}
    requested = [by_label[label] for label in ['fixed-candidate', 'switchyard', 'capable-access']
                 if label in by_label]
    observed = {provider_model(model) for row in requested
                for model in row.get('actual_selected_models', [])}

    def verified(labels):
        return all(label in by_label and by_label[label].get('verified') for label in labels)

    access = []
    for role, label in [('EFFICIENT', 'fixed-candidate'), ('CAPABLE', 'capable-access')]:
        row = by_label.get(label, {})
        model = provider_model(configured[role])
        selected = {provider_model(value) for value in row.get('actual_selected_models', [])}
        access.append({'model': model, 'condition': label, 'actual_selected_models': sorted(selected),
                       'verified': bool(row.get('verified') and selected == {model})})
    policy_verified = verified(['fixed-candidate', 'switchyard'])
    access_verified = all(row['verified'] for row in access)
    stopped = next((row for row in receipts if not row.get('verified')), None)
    planned = [{'label': label, 'required': label in COMPARISON_LABELS[:3],
                'status': by_label[label].get('status', 'unavailable') if label in by_label else 'not_run',
                'blocked_by': stopped['label'] if stopped and label not in by_label else None}
               for label in COMPARISON_LABELS]
    diagnostic = [by_label[label] for label in COMPARISON_LABELS[3:] if label in by_label]
    diagnostic_status = ('not_run' if not diagnostic else
                         'cancelled' if any(row.get('status') == 'cancelled' for row in diagnostic) else
                         'failed' if any(not row.get('verified') for row in diagnostic) else
                         'passed' if len(diagnostic) == 2 else 'partial')
    return {'conditions': receipts,
        'condition_plan': planned,
        'status': ('cancelled' if stopped and stopped.get('status') == 'cancelled' else
                   'failed' if stopped else 'completed' if len(receipts) == len(COMPARISON_LABELS) else 'running'),
        'stopped_at': stopped['label'] if stopped else None,
        'requires_user_review': bool(stopped),
        'stop_reason': stopped.get('stop_reason') if stopped else None,
        'verified': policy_verified and access_verified,
        'routing_policy_verified': policy_verified,
        'requested_access_verified': access_verified,
        'requested_model_access': access,
        'diagnostic_verified': verified(['available-fixed', 'available-switchyard']),
        'diagnostic_status': diagnostic_status,
        'requested_model_coverage': {'configured_models': sorted(candidates),
            'observed_models': sorted(observed), 'unexercised_models': sorted(candidates - observed),
            'all_candidates_observed': candidates <= observed,
            'meaning': 'Only completed requests with returned model identity establish execution. A configured or unselected candidate has no execution proof.'},
        'comparison': 'Within each named inventory: one fixed efficient candidate versus the same pool with Switchyard; identical public inputs/catalogue/harness, fresh memory. A separate fixed capable-access condition replays all three public inputs to verify GLM access; it does not force a routed selection. The available Nemotron inventory remains a separate diagnostic.',
        'baseline_notice': 'The main Nemotron baseline changes model inventory, so it is not a routing-policy-only comparison. Fixed and routed requested-pool conditions share the 1,024-token ceiling and the same per-model provider settings.',
        'provider_notice': 'Each verified condition requires completed execution, passing criteria, native course search and cleanup; routed execution also requires native decisions. Overall verification additionally requires full fixed-condition access to each requested model. Candidate call coverage remains separate.'}


async def compare_routing(state: dict, folder: Path, budget, conversation: list, catalogue: Path) -> dict:
    messages = [row['content'] for row in conversation if row['role'] == 'user']
    if len(messages) != 3:
        raise ValueError('Routing comparisons require the saved three-turn public input')
    source_lock = json.loads((folder / 'source-lock.json').read_text())
    receipts = []
    proxy = os.getenv('LAB_RETAIL_PROXY_URL', 'http://127.0.0.1:4001/v1')
    diagnostic_proxy = os.getenv('LAB_PROXY_BASE_URL', '').rstrip('/')
    if proxy != 'http://127.0.0.1:4001/v1' or diagnostic_proxy not in {'http://127.0.0.1:4000', 'http://127.0.0.1:4000/v1'}:
        raise ValueError('The recorded comparison requires its two explicitly selected local proxies')
    configuration = await routing_configuration(folder)
    conditions = [
        ('fixed-candidate', 'lab-advisor-candidate', 'fixed', proxy, 'requested Gemma/GLM pool'),
        ('switchyard', 'lab-advisor-routed', 'switchyard', proxy, 'requested Gemma/GLM pool'),
        ('capable-access', 'lab-advisor-capable', 'fixed', proxy, 'requested Gemma/GLM pool: explicit capable-model access'),
        ('available-fixed', 'lab-support', 'fixed', diagnostic_proxy, 'separate available-inventory diagnostic'),
        ('available-switchyard', 'lab-advisor-routed', 'switchyard', diagnostic_proxy, 'separate available-inventory diagnostic'),
    ]
    for label, alias, route, endpoint, purpose in conditions:
        identity = str(uuid.uuid4())
        work = folder / 'comparisons' / identity
        work.mkdir(parents=True)
        public = RetailPublicContext(work)
        rows, native = [], None
        before = budget.calls
        receipt = {'condition_id': identity, 'label': label, 'harness': 'deepagents', 'alias': alias,
            'route': route, 'purpose': purpose, 'status': 'running',
            'execution_status': 'running', 'evaluation_status': 'not_run',
            'input_sha256': hashlib.sha256(json.dumps(messages).encode()).hexdigest(),
            'catalogue_sha256': state['catalogue_sha256'], 'fresh_memory': True,
            'public_inputs': messages, 'input_basis': 'Exact public messages saved from the baseline; no new UserSim generation'}
        state.setdefault('comparison_conditions', []).append(identity)
        save_evidence(work / 'condition.json', receipt)
        cancellation = None
        try:
            async with Gateway(budget, mode='live', model_route=route, assistant_alias=alias,
                               proxy_url=endpoint, allowed_tool_names=TOOL_NAMES, on_request=public.audit,
                               request_timeout=300 if purpose.startswith('requested') else 50,
                               evidence_dir=work, fail_on_truncated_output=True).serving() as gateway:
                native = NativeSandbox(identity, work / 'runtime', gateway, catalogue=catalogue,
                                       scenario_id='dreamjob', harness='deepagents', model_route=route,
                                       model=alias if purpose.startswith('requested') else None)
                async with native:
                    for index, message in enumerate(messages):
                        preferences = public.accept(message)
                        rows.append({'turn': index + 1, 'role': 'user', 'content': message})
                        save_evidence(work / 'public-conversation.json', rows)
                        reply = await native.reply(message, preferences)
                        rows.append({'turn': index + 1, 'role': 'assistant', **reply})
                        save_evidence(work / 'public-conversation.json', rows)
            receipt.update(execution_status='completed', evaluation_status='running')
            tools = native_tool_records(work / 'runtime/native')
            save_evidence(work / 'native-tools.json', tools)
            save_evidence(work / 'usage.json', {'calls': budget.calls - before, 'records': budget.records[before:]})
            evaluation = await score_with_helix(evaluate_retail(rows, catalogue, tools, source_lock, work), work)
            save_evidence(work / 'evaluation.json', evaluation)
            receipt.update(status='completed', conversation=rows, evaluation=evaluation,
                           evaluation_status='passed' if evaluation_verified(evaluation) else 'failed')
        except asyncio.CancelledError as exc:
            cancellation = exc
            receipt.update(status='cancelled', error_type='CancelledError',
                           error='Cancelled explicitly; partial evidence is preserved.', conversation=rows)
            if receipt['execution_status'] == 'running':
                receipt['execution_status'] = 'cancelled'
            if receipt['evaluation_status'] == 'running':
                receipt['evaluation_status'] = 'cancelled'
        except Exception as exc:
            receipt.update(status='failed', error_type=type(exc).__name__, error=str(exc)[:600], conversation=rows)
            if receipt['execution_status'] == 'running':
                receipt['execution_status'] = 'failed'
            if receipt['evaluation_status'] == 'running':
                receipt['evaluation_status'] = 'failed'
        config_path = work / 'runtime/native/fabric-config.json'
        if config_path.is_file():
            config = json.loads(config_path.read_text())
            receipt['fabric_configuration'] = {'harness': config['harness'], 'runtime': config['runtime'],
                'models': {name: {key: value for key, value in model.items() if key in ['provider', 'model', 'max_tokens', 'temperature']}
                           for name, model in config['models'].items()},
                'native_configuration_sha256': hashlib.sha256(config_path.read_bytes()).hexdigest()}
        outcomes = work / 'runtime/native/reply-outcomes.jsonl'
        if outcomes.is_file():
            receipt['fabric_results'] = [{key: row[key] for key in ['runtime_status', 'runtime_id', 'invocation_id', 'outcome'] if key in row}
                for row in [json.loads(line) for line in outcomes.read_text().splitlines() if line.strip()]]
        cleanup = work / 'runtime/cleanup.json'
        receipt['cleanup_confirmed'] = bool(cleanup.is_file() and json.loads(cleanup.read_text()).get('native_absence_confirmed'))
        receipt['calls'] = budget.calls - before
        receipt['usage'] = budget.records[before:]
        receipt['native_decisions'] = [row['routing_decision'] for row in receipt['usage'] if row.get('routing_decision')]
        tools = native_tool_records(work / 'runtime/native')
        save_evidence(work / 'native-tools.json', tools)
        save_evidence(work / 'usage.json', {'calls': receipt['calls'], 'records': receipt['usage']})
        receipt.update(condition_verification(receipt, tools))
        if not receipt['verified']:
            reason = ('A comparison retains unresolved native ownership; resolve cleanup before continuing.'
                      if not receipt['cleanup_confirmed'] else
                      receipt.get('error') or f'Comparison {label} failed verification; review its saved evidence before continuing.')
            receipt.update(stopped_at=label, requires_user_review=True, stop_reason=reason)
            if receipt['status'] != 'cancelled':
                receipt['status'] = 'failed'
        save_evidence(work / 'condition.json', receipt)
        receipts.append(receipt)
        save_evidence(folder / 'routing-comparison.json', comparison_summary(receipts, configuration))
        if cancellation is not None:
            raise cancellation
        if not receipt['verified']:
            raise RuntimeError(receipt['stop_reason'])
    return comparison_summary(receipts, configuration)
