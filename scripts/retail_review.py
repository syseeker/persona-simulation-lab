"""Allowlisted public review projections for an actually executed retail run."""
from __future__ import annotations

import hashlib
import json


def project(folder, emit):
    from scripts.export_guide_recording import pick

    def source(name):
        path = folder / name
        return json.loads(path.read_text()) if path.is_file() else None

    for name in ['designer-configuration.json', 'designer-output.json', 'designer-generation.json',
                 'designer-lineage.json', 'helix-criteria.json', 'helix-evaluation.json',
                 'routing-configuration.json', 'platform-boundary-probes.json', 'platform-trace.json']:
        value = source(name)
        if value is not None:
            emit(name, value, folder / name)
    for name in ['public-constraints.jsonl', 'disclosure-audit.jsonl']:
        path = folder / name
        if path.is_file():
            emit(name, [json.loads(line) for line in path.read_text().splitlines() if line.strip()], path, jsonl=True)
    job = source('helix-job.json')
    if job:
        emit('helix-job.json', {**pick(job, ['engine', 'mode', 'inference_calls', 'criteria', 'status', 'job_name',
            'error_type', 'error', 'native_status', 'result', 'cancellation_requested', 'cancellation_error']),
            'projection': 'Native job status and saved-criterion results; submission headers and arbitrary payloads omitted.'},
            folder / 'helix-job.json')
    routing = source('routing-comparison.json')
    if routing:
        conditions = []
        for row in routing['conditions']:
            condition = pick(row, ['condition_id', 'label', 'harness', 'alias', 'route', 'status', 'input_sha256',
                'catalogue_sha256', 'fresh_memory', 'cleanup_confirmed', 'calls', 'native_decisions',
                'purpose', 'evaluation', 'error_type', 'error', 'public_inputs', 'input_basis', 'fabric_configuration', 'fabric_results',
                'execution_status', 'evaluation_status', 'execution_verified', 'evaluation_verified',
                'evaluation_scope', 'proposal_review', 'native_course_searches', 'native_course_scope_uuids',
                'actual_selected_models', 'verified', 'stopped_at', 'requires_user_review', 'stop_reason'])
            condition['usage'] = [pick(call, ['call', 'role', 'mode', 'status', 'requested_model', 'selected_model',
                'usage', 'latency_ms', 'routing_decision', 'http_status', 'error_type', 'control_request_id',
                'thread_id', 'transport', 'finish_reason', 'output_token_limit',
                'logical_request_id', 'attempt', 'retry_of_call', 'retry_status', 'retry_delay_seconds',
                'retry_wait_seconds', 'retry_after_seconds', 'rate_limit_headers', 'rate_limit_header_source'])
                for call in row.get('usage', [])]
            condition['conversation'] = [pick(message, ['turn', 'role', 'content', 'thread_id', 'outcome',
                                                       'response_origin', 'response_policy'])
                                         for message in row.get('conversation', [])]
            conditions.append(condition)
        emit('routing-comparison.json', {**pick(routing, ['comparison', 'baseline_notice',
            'condition_plan', 'status', 'stopped_at', 'requires_user_review', 'stop_reason', 'verified',
            'routing_policy_verified', 'requested_access_verified', 'requested_model_access',
            'diagnostic_verified', 'diagnostic_status', 'requested_model_coverage', 'provider_notice']),
            'conditions': conditions},
             folder / 'routing-comparison.json')
    for name, keys in {
        'platform-package.json': ['harness', 'scenario_id', 'image', 'built', 'stage', 'files', 'catalogue_sha256', 'public_preset'],
        'platform-setup.json': ['run_id', 'provider', 'environment', 'provider_status', 'model_alias', 'public_preset'],
        'platform-registration.json': ['registered', 'registration_reused', 'agent', 'name', 'source_fileset', 'image', 'harness', 'scenario_id'],
        'platform-deployment.json': ['ready', 'deployment', 'configuration'],
        'platform-session.json': ['session', 'session_identity', 'deployment'],
        'platform-condition.json': ['condition_id', 'parent_run_id', 'status', 'fresh_session', 'public_preferences',
            'private_persona_in_image', 'local_memory_resumed', 'cleanup_confirmed', 'image', 'input_kind',
            'guardrails_location', 'agent', 'deployment_name', 'stage', 'resource_creation_attempted',
            'registration_created', 'session_id', 'sandbox', 'reply', 'response_origin', 'response_policy',
            'error_type', 'error', 'cleanup_errors'],
        'platform-cleanup.json': ['condition_id', 'native_absence_confirmed', 'errors', 'deployment_name', 'session_id'],
        'platform-effective-policy.json': ['active_version', 'config_revision', 'hash', 'policy', 'policy_source', 'status', 'version'],
    }.items():
        value = source(name)
        if value is not None:
            emit(name, {'projection': 'Allowlisted native/public configuration fields.', **pick(value, keys)}, folder / name)
    invocation = source('platform-invocation.json')
    if invocation:
        response = invocation.get('response') or {}
        application = invocation.get('application_delivery')
        mediated = invocation.get('application_delivery_required') or application is not None
        choices = []
        for row in response.get('choices', []):
            message = row.get('message') or {}
            choice = {**pick(row, ['index', 'finish_reason']),
                      'message': pick(message, ['role'] if mediated else ['role', 'content'])}
            if mediated:
                choice.update(native_content_published=False,
                    native_content_sha256=hashlib.sha256(str(message.get('content') or '').encode()).hexdigest())
            choices.append(choice)
        delivery = None
        if application is not None:
            policy = application.get('response_policy') or {}
            content = application.get('content')
            if (policy.get('status') != 'delivered' or not isinstance(content, str)
                    or policy.get('delivered_content_sha256') != hashlib.sha256(content.encode()).hexdigest()
                    or not choices or policy.get('model_proposal_sha256') != choices[0].get('native_content_sha256')):
                raise ValueError('Managed application delivery has no matching confirmed proposal/content hashes')
            delivery = pick(application, ['content', 'response_origin', 'response_policy', 'thread_id'])
        emit('platform-invocation.json', {**pick(invocation, ['public_input', 'session_id', 'deployment']),
            'response': {**pick(response, ['id', 'object', 'model', 'usage']), 'choices': choices},
            **({'application_delivery': delivery, 'native_model_content_published': False} if mediated else {}),
            'projection': ('Native proposal identifiers/hashes and separately confirmed application delivery; proposal text stays private.'
                           if mediated else 'Public reply and native identifiers; reasoning and arbitrary response fields omitted.')},
            folder / 'platform-invocation.json')
