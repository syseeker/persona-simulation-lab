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
from .retail import RetailPublicContext
from .retail_checks import evaluate_retail
from .sandbox import NativeSandbox
from .settings import ROOT


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
    await routing_configuration(folder)
    conditions = [
        ('fixed-candidate', 'lab-advisor-candidate', 'fixed', proxy, 'requested Gemma/GLM pool'),
        ('switchyard', 'lab-advisor-routed', 'switchyard', proxy, 'requested Gemma/GLM pool'),
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
            'route': route, 'purpose': purpose, 'status': 'running', 'input_sha256': hashlib.sha256(json.dumps(messages).encode()).hexdigest(),
            'catalogue_sha256': state['catalogue_sha256'], 'fresh_memory': True,
            'public_inputs': messages, 'input_basis': 'Exact public messages saved from the baseline; no new UserSim generation'}
        state.setdefault('comparison_conditions', []).append(identity)
        save_evidence(work / 'condition.json', receipt)
        try:
            async with Gateway(budget, mode='live', model_route=route, assistant_alias=alias,
                               proxy_url=endpoint, allowed_tool_names=TOOL_NAMES, on_request=public.audit,
                               request_timeout=300 if purpose.startswith('requested') else 50).serving() as gateway:
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
            tools = native_tool_records(work / 'runtime/native')
            save_evidence(work / 'usage.json', {'calls': budget.calls - before, 'records': budget.records[before:]})
            evaluation = await score_with_helix(evaluate_retail(rows, catalogue, tools, source_lock, work), work)
            save_evidence(work / 'evaluation.json', evaluation)
            receipt.update(status='completed', conversation=rows, evaluation=evaluation)
        except Exception as exc:
            receipt.update(status='failed', error_type=type(exc).__name__, error=str(exc)[:600], conversation=rows)
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
        save_evidence(work / 'condition.json', receipt)
        receipts.append(receipt)
        save_evidence(folder / 'routing-comparison.json', {'conditions': receipts,
            'comparison': 'Within each named inventory: one fixed efficient candidate versus the same pool with Switchyard; identical public inputs/catalogue/harness, fresh memory. The available Nemotron inventory is a separate diagnostic, not verification of Gemma/GLM access.',
            'baseline_notice': 'The main Nemotron condition also changes model inventory and output ceiling (1024 versus 384 in the requested pool); it is not a routing-policy-only comparison. Both requested-pool conditions share the lower ceiling and low reasoning setting.'})
        if not receipt['cleanup_confirmed']:
            raise RuntimeError('A comparison retains unresolved native ownership; stop before another condition')
    return {'conditions': receipts,
            'verified': all(row['status'] == 'completed' for row in receipts[:2]) and bool(receipts[1]['native_decisions']),
            'diagnostic_verified': all(row['status'] == 'completed' for row in receipts[2:]) and bool(receipts[3]['native_decisions']),
            'provider_notice': 'Gemma/GLM access and the separate available-inventory diagnostic retain independent verification states.'}
