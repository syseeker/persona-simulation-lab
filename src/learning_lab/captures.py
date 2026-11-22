"""One scenario-aware capture contract for publication, teaching and Metadata.

Presence, privacy and execution are independent. Inspection is file-only and
does not import execution services. Native records stay in ignored run folders.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path

from .evidence import save_evidence

REGISTRY = json.loads(Path(__file__).with_name('capture_registry.json').read_text())
REQUIREMENTS = {entry['id']: entry for entry in REGISTRY['requirements']}
CAPTURE_CONTRACT_VERSION = 2


@dataclass(frozen=True)
class CaptureRule:
    scope: str
    # Each group needs at least one retained file. Multiple groups are required
    # together, e.g. a request and its result cannot satisfy each other.
    groups: tuple[tuple[str, ...], ...]
    role: str
    native_schema: str
    optional: bool = False


def rule(scope, names, role='native-effective-configuration', schema='application/v1', *, optional=False):
    return CaptureRule(scope, tuple(tuple(group.split('|')) for group in names.split(';') if group), role, schema, optional)


RULES = {
    'CAP-PER-01': rule('root', 'source-lock.json;resolved-inputs.json', 'application-input', 'source-lock/v1'),
    'CAP-SIT-01': rule('root', 'situation.json', 'authored-source'),
    'CAP-DD-01': rule('root', 'designer-private/configuration.json', schema='DataDesignerConfigBuilder'),
    'CAP-DD-02': rule('root', 'designer-configuration.json', 'application-projection'),
    'CAP-DD-03': rule('root', 'designer-private/designer-run-config.json;designer-private/designer-model-providers.json', schema='RunConfig / ModelProvider'),
    'CAP-DD-04': rule('root', 'designer-output.json;designer-generation.json;designer-lineage.json', 'application-result'),
    'CAP-DD-05': rule('root', 'designer-private/designer-profiling.json;designer-private/designer-analysis.json', 'profiling-outcome'),
    'CAP-US-01': rule('root', 'resolved-inputs.json', 'native-input', 'ConversationSimulatorConfig / episode preamble'),
    'CAP-US-02': rule('root', 'resolved-inputs.json', 'native-input'),
    'CAP-US-03': rule('root', 'usersim-model-config.json', schema='HostRoleModel'),
    'CAP-US-04': rule('root', 'usersim-activations.jsonl;public-conversation.json;usersim-result.json', 'native-response', 'UserSim external runtime'),
    'CAP-US-05': rule('unused', '', optional=True),
    'CAP-FAB-01': rule('native', 'fabric-config.json', schema='FabricConfig'),
    'CAP-FAB-02': rule('native', 'fabric-config.json', schema='FabricConfig'),
    'CAP-FAB-03': rule('native', 'fabric-plan.json;fabric-doctor.json', 'native-response', 'ResolvedPlan / DoctorReport'),
    'CAP-FAB-04': rule('native', 'fabric-lifecycle.jsonl', 'application-lifecycle'),
    'CAP-FAB-05': rule('native', 'fabric-run-requests.jsonl', 'native-request', 'RunRequest'),
    'CAP-FAB-06': rule('native', 'fabric-run-results.jsonl', 'native-response', 'RunResult / terminal exception'),
    'CAP-FAB-07': rule('native', 'reply-outcomes.jsonl', 'application-projection'),
    'CAP-DA-01': rule('native', 'fabric-config.json;fabric-plan.json', schema='Fabric Deep Agents adapter'),
    'CAP-HER-01': rule('native', 'hermes-managed-config.yaml;hermes-native-config.yaml;hermes-config-capture.jsonl', schema='Hermes native config'),
    'CAP-HER-02': rule('native', 'reply-outcomes.jsonl', 'native-response', 'Hermes adapter output'),
    'CAP-MCP-01': rule('native', 'fabric-config.json', schema='Fabric MCP server settings'),
    'CAP-MCP-02': rule('boundary', 'native/mcp-tools-list.json|native/mcp-tools-list.jsonl;host/provider-tool-schemas.jsonl', 'native-schema', 'MCP ListToolsResult / OpenAI tools'),
    'CAP-MCP-03': rule('native', 'fabric-traces/*/relay.jsonl', 'native-events', 'Relay ATOF tool events'),
    'CAP-MCP-04': rule('native', 'preferences-by-turn.jsonl', 'public-input', 'Preferences'),
    'CAP-GW-01': rule('host', 'gateway-effective-config.json', schema='citizen-gateway-config/v1'),
    'CAP-GW-02': rule('host', 'gateway-calls.jsonl', 'application-accounting'),
    'CAP-LLM-01': rule('host', 'litellm-loaded.yaml', 'redacted-loaded-source', 'LiteLLM YAML'),
    'CAP-LLM-02': rule('requested', 'litellm-loaded.yaml', 'redacted-loaded-source', 'LiteLLM YAML'),
    'CAP-LLM-03': rule('host', 'litellm-loaded.yaml;litellm-effective-config.json', schema='LiteLLM resolved settings'),
    'CAP-SW-01': rule('root', 'routing-configuration.json', 'application-projection'),
    'CAP-SW-02': rule('root', 'routing-comparison.json', 'application-result'),
    'CAP-REL-01': rule('native', 'fabric-relay.json', schema='Relay plugin config v1 / observability v4'),
    'CAP-REL-02': rule('native', 'fabric-traces/*/relay.jsonl', 'native-events', 'Relay ATOF'),
    'CAP-REL-03': rule('native', 'fabric-traces/*/relay.jsonl', 'native-events', 'Relay ATOF'),
    'CAP-REL-04': rule('unused', '', optional=True),
    'CAP-EVAL-01': rule('root', 'evaluation.json', 'application-result'),
    'CAP-HX-01': rule('evaluation', 'helix-criteria.json;helix-evaluation.json;evaluation.json', 'native-response', 'Helix evaluation result'),
    'CAP-HX-02': rule('evaluation', 'helix-evaluator-config.json', schema='Helix metric templates / RunConfig'),
    'CAP-HX-03': rule('root', 'helix-job.json;helix-job-config.json', 'native-request-response', 'Helix durable evaluation job'),
    'CAP-GR-01': rule('native', 'guardrails-config.json', schema='RailsConfig YAML / Colang'),
    'CAP-GR-02': rule('safeguards', 'native/guardrails-decisions.jsonl;host/guardrails-probe.json', 'native-response', 'Guardrails decisions'),
    'CAP-PLAT-01': rule('managed', 'platform-effective-config.json', schema='Helix Platform client / selected executor file'),
    'CAP-PLAT-02': rule('managed', 'agent.yaml', 'redacted-submitted-source', 'Helix agent YAML'),
    'CAP-PLAT-03': rule('managed', 'parent/platform-setup.json', 'native-request-response', 'Platform providers/environments'),
    'CAP-PLAT-04': rule('managed', 'parent/platform-registration.json;parent/platform-deployment.json;parent/platform-package.json', 'native-request-response'),
    'CAP-PLAT-05': rule('managed', 'parent/platform-session.json;parent/platform-invocation.json;parent/platform-cleanup.json;platform-operation-requests.jsonl;platform-operation-results.jsonl', 'native-request-response'),
    'CAP-OS-01': rule('sandbox', 'requested-policy.yaml', 'requested-policy', 'OpenShell policy YAML'),
    'CAP-OS-02': rule('sandbox', 'effective-policy.yaml;effective-policy.json;boundary-probes.json;cleanup.json;sandbox-identity.json', 'enforcement-receipt'),
    'CAP-OS-03': rule('managed', 'parent/platform-effective-policy.json;parent/platform-boundary-probes.json;parent/platform-cleanup.json', 'enforcement-receipt'),
}


def _files(root, pattern):
    for path in sorted(root.glob(pattern)):
        if path.is_file() and not path.is_symlink() and not any(p.is_symlink() for p in path.parents):
            yield path


def _contexts(folder, state):
    baseline = {'condition_id': state.get('condition_id'), 'episode_id': state.get('episode_id'),
                'purpose': 'baseline', 'execution_status': state.get('baseline_status', state.get('status')), 'host': folder,
                'sandbox': folder / str(state.get('episode_id')), 'evaluation': folder}
    baseline['native'] = baseline['sandbox'] / 'native'
    yield baseline
    for identity in state.get('comparison_conditions', []):
        if not isinstance(identity, str) or Path(identity).name != identity or identity in {'.', '..'}:
            raise ValueError('Invalid condition identity')
        host = folder / 'comparisons' / identity
        receipt = json.loads((host / 'condition.json').read_text()) if (host / 'condition.json').is_file() else {}
        if receipt and receipt.get('condition_id') != identity:
            raise ValueError('Comparison receipt belongs to another condition')
        yield {'condition_id': identity, 'episode_id': None, 'purpose': receipt.get('label', 'comparison'),
               'execution_status': receipt.get('status', 'unavailable'), 'host': host,
               'sandbox': host / 'runtime', 'native': host / 'runtime/native', 'evaluation': host}


def _boundary_errors(native):
    paths = {name: native / name for name in
             ['fabric-run-requests.jsonl', 'fabric-run-results.jsonl', 'preferences-by-turn.jsonl']}
    if not all(path.is_file() and not path.is_symlink() for path in paths.values()):
        return []  # Missing files are reported by the ordinary coverage rules.
    try:
        records = {name: [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
                   for name, path in paths.items()}
        identities = {}
        for name, values in records.items():
            keys = [(row['request_id'], row['thread_id'], row['turn']) for row in values]
            identities[name] = keys
            if len(set(keys)) != len(keys):
                return ['Duplicate native invocation boundary in ' + name]
        requests = identities['fabric-run-requests.jsonl']
        if not requests or any(keys != requests for keys in identities.values()):
            return ['Native requests, terminal results and public preference snapshots are not one-to-one']
        return []
    except (ValueError, KeyError, TypeError):
        return ['Invalid native invocation boundary record']


def _designer_profiling_errors(artifacts, folder):
    paths = {Path(item['location']).name: folder / item['location'] for item in artifacts}
    receipt = paths.get('designer-profiling.json')
    if receipt is None:
        return []  # Ordinary coverage reports missing files.
    try:
        outcome = json.loads(receipt.read_text())
        if (not isinstance(outcome, dict) or outcome.get('status') != 'completed'
                or outcome.get('analysis_report') != 'designer-analysis.json'
                or outcome.get('error') is not None or outcome.get('error_type') is not None):
            return ['Native Designer profiling has no completed analysis receipt']
        report_path = paths.get('designer-analysis.json')
        if report_path is None:
            return []

        def invalid_constant(_value):
            raise ValueError('Nonfinite JSON statistic')

        report = json.loads(report_path.read_text(), parse_constant=invalid_constant)
        if (not isinstance(report, dict) or type(report.get('num_records')) is not int
                or type(report.get('target_num_records')) is not int
                or report['num_records'] < 1 or report['num_records'] != report['target_num_records']
                or not isinstance(report.get('column_statistics'), list) or not report['column_statistics']
                or any(not isinstance(column, dict) or not isinstance(column.get('column_name'), str)
                       or not column['column_name'] for column in report['column_statistics'])):
            return ['Native Designer analysis report is invalid or incomplete']
        return []
    except (OSError, ValueError, TypeError):
        return ['Invalid native Designer profiling receipt or analysis report']


def build_capture_manifest(folder: Path, state: dict, *, contract_version=CAPTURE_CONTRACT_VERSION):
    """Resolve only this run's explicit condition roots; never borrow another run."""
    if type(contract_version) is not int or contract_version not in {1, CAPTURE_CONTRACT_VERSION}:
        raise ValueError('Unsupported capture contract version')
    scenario = state['scenario_id']
    rows = []
    contexts = list(_contexts(folder, state))
    managed_id = state.get('managed_condition_id')
    managed_work = folder / 'managed' / str(managed_id)
    managed_receipt = folder / 'platform-condition.json'
    if managed_id and (not isinstance(managed_id, str) or Path(managed_id).name != managed_id or managed_id in {'.', '..'}):
        raise ValueError('Invalid managed condition identity')
    if managed_id and managed_receipt.is_file() and json.loads(managed_receipt.read_text()).get('condition_id') != managed_id:
        raise ValueError('Managed receipt belongs to another condition')
    managed_context = {**contexts[0], 'purpose': 'managed', 'episode_id': None,
        'condition_id': managed_id, 'host': managed_work, 'native': managed_work,
        'execution_status': json.loads(managed_receipt.read_text()).get('status') if managed_receipt.is_file() else 'unavailable'}
    for requirement in REQUIREMENTS.values():
        rid = requirement['id']
        spec = RULES[rid]
        if rid == 'CAP-DD-05' and contract_version == 1:
            # Recompute immutable pre-v2 manifests under their receipt-only
            # contract, including retained historical profiling failures.
            spec = rule('root', 'designer-private/designer-profiling.json', 'profiling-outcome')
        applicable = scenario in requirement['scenario_ids'] and spec.scope != 'unused'
        selected = contexts if spec.scope in {'native', 'host', 'boundary', 'sandbox', 'evaluation', 'safeguards', 'requested'} else contexts[:1]
        if managed_id and (spec.scope in {'host', 'boundary', 'safeguards'} or rid == 'CAP-GR-01'):
            selected = [*selected, managed_context]
        if spec.scope == 'managed':
            selected = [managed_context]
        for context in selected:
            purpose = context['purpose']
            applies = applicable
            if rid == 'CAP-DA-01':
                applies &= scenario != 'boardgames'
            if spec.scope == 'requested':
                applies &= purpose in {'fixed-candidate', 'switchyard', 'capable-access'}
            roots = {'root': folder, **{key: context[key] for key in ['host', 'native', 'sandbox', 'evaluation']}}
            roots['requested'] = roots['host']
            if spec.scope == 'managed':
                roots['managed'] = folder / 'managed' / str(state.get('managed_condition_id'))
            artifacts, missing = [], []
            if applies:
                groups = spec.groups
                if scenario == 'dreamjob' and rid in {'CAP-FAB-07', 'CAP-PLAT-05'}:
                    # Application delivery is separate from the immutable native
                    # proposal. The proposal payload stays private in publication.
                    groups = (*groups, *((name,) for name in (
                        'retail-response-config.json', 'retail-response-decisions.jsonl',
                        'retail-model-proposals.jsonl')))
                if spec.scope == 'safeguards' and purpose != 'baseline':
                    # Comparisons run boundary checks but do not repeat the
                    # separate negative policy demonstration.
                    groups = (('native/guardrails-decisions.jsonl',),)
                for alternatives in groups:
                    found = []
                    for pattern in alternatives:
                        if pattern.startswith('parent/'):
                            root, pattern = folder, pattern.removeprefix('parent/')
                        elif spec.scope in {'boundary', 'safeguards'}:
                            scope, pattern = pattern.split('/', 1)
                            root = roots[scope]
                        else:
                            root = roots[spec.scope]
                        found.extend(_files(root, pattern))
                    if not found:
                        missing.append(list(alternatives))
                    for path in dict.fromkeys(found):
                        relative = path.relative_to(folder).as_posix()
                        artifacts.append({'id': hashlib.sha256(relative.encode()).hexdigest()[:24],
                            'location': relative, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                            'size_bytes': path.stat().st_size,
                            'captured_at': datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                            'access': 'private', 'role': spec.role,
                            'schema': ('DatasetProfilerResults' if rid == 'CAP-DD-05'
                                       and path.name == 'designer-analysis.json' else spec.native_schema)})
            rows.append({**requirement, 'scenario_id': scenario, 'run_id': state['run_id'],
                'condition_id': context['condition_id'], 'episode_id': context['episode_id'], 'purpose': purpose,
                'availability': ('exists' if not missing else 'missing') if applies else 'not-used',
                'required': applies and not spec.optional, 'access': 'private',
                'execution_status': context['execution_status'], 'artifacts': artifacts, 'missing': missing,
                'producer_revision': state.get('source_revision'), 'operation_id': rid.lower(),
                'publication_availability': 'not-published',
                'publication_kind': 'projection-pending' if rid in {'CAP-US-02', 'CAP-FAB-02', 'CAP-REL-03'} else None,
                'turn': None, 'model_role': None})
            if applies and rid == 'CAP-DD-05' and contract_version >= 2:
                errors = _designer_profiling_errors(artifacts, folder)
                if errors:
                    rows[-1]['integrity_errors'] = errors
    for context in contexts:
        errors = _boundary_errors(context['native'])
        if errors:
            for row in rows:
                if row['id'] in {'CAP-FAB-05', 'CAP-FAB-06', 'CAP-MCP-04'} and row['condition_id'] == context['condition_id']:
                    row['integrity_errors'] = errors
    required = [row for row in rows if row['required']]
    missing_ids = [row['id'] + ':' + str(row['condition_id']) for row in required
                   if row['availability'] != 'exists' or row.get('integrity_errors')]
    versions = {}
    for package in ['nemo-fabric', 'nemo-relay', 'usersim', 'data-designer']:
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            versions[package] = None
    return {'schema': 'citizen-captures/v1', 'registry_schema': REGISTRY['schema'],
        'contract_version': contract_version,
        'host_sdk_versions': versions,
        'scenario_id': scenario, 'run_id': state['run_id'], 'rows': rows,
        'coverage': {'required': len(required), 'captured': len(required) - len(missing_ids),
                     'complete': not missing_ids, 'missing': missing_ids},
        'notice': 'Capture completeness does not establish successful execution. Row records may contain per-turn/model identifiers; no unrecorded correlations are inferred.'}


def write_capture_manifest(folder: Path, state: dict):
    result = build_capture_manifest(folder, state)
    save_evidence(folder / 'capture-manifest.json', result)
    return result


def verify_capture_manifest(folder: Path, manifest: dict):
    """Reject identity swaps, missing native captures and changed bytes before publication."""
    state = json.loads((folder / 'run.json').read_text())
    if any(state[key] != manifest[key] for key in ['scenario_id', 'run_id']):
        raise ValueError('Capture manifest belongs to another scenario/run')
    expected = build_capture_manifest(folder, state, contract_version=manifest.get('contract_version', 1))
    if expected['rows'] != manifest['rows'] or expected['coverage'] != manifest['coverage']:
        raise ValueError('Capture manifest no longer matches the retained artifacts')
    if not manifest['coverage']['complete']:
        raise ValueError('Required capture coverage is incomplete')
