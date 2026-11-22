"""Run-owned Helix provider/environment resources; never change older deployments."""
from __future__ import annotations

import asyncio
import os
import uuid


def names(run_id):
    if str(uuid.UUID(run_id)) != run_id:
        raise ValueError('A canonical owning run is required')
    prefix = 'citizen-retail-' + uuid.UUID(run_id).hex[:12]
    return {'provider': prefix + '-model', 'secret': prefix + '-key', 'environment': prefix + '-preset'}


async def setup(client, args):
    from bridge import clean
    from presets import preset_metadata
    from nemo_helix_plugin.agents.types import CreateEnvironmentRequest, EnvironmentSpecInline, McpFulfillment
    from nemo_helix_plugin.models.client import AsyncModelsClient
    from nemo_helix_plugin.models.types import CreateModelProviderRequest
    from nemo_helix_plugin.secrets.client import AsyncSecretsClient
    from nemo_helix_plugin.secrets.types import HelixSecretCreateRequest
    from nemo_helix_plugin.client.errors import NotFoundError

    selected = names(args['run_id'])
    # Deliberately local: this demonstration never redirects a remote Platform
    # to an arbitrary host-side process or reuses another worker's provider.
    if args.get('provider_url') != 'http://127.0.0.1:8876/v1':
        raise ValueError('The retail demonstration uses its dedicated local admission bridge')
    key = os.environ.get('LAB_DEPLOYMENT_GATEWAY_KEY', '')
    if len(key) < 24:
        raise ValueError('The dedicated admission key is missing')
    secrets, models = AsyncSecretsClient.from_client(client), AsyncModelsClient.from_client(client)
    definitions = {}
    try:
        await secrets.get_secret(name=selected['secret'])
    except NotFoundError:
        await secrets.create_secret(body=HelixSecretCreateRequest(name=selected['secret'], value=key,
                                      description='Owned retail review admission bridge; no inference-provider credential'))
    provider_body = CreateModelProviderRequest(name=selected['provider'], host_url=args['provider_url'],
        api_key_secret_name=selected['secret'], enabled_models=['citizen-retail-advisor'],
        description='Scenario 3 owned fixed-model admission lease')
    try:
        provider = (await models.get_provider(name=selected['provider'])).data()
        if provider.host_url.rstrip('/') != args['provider_url'] or set(provider.enabled_models or []) != {'citizen-retail-advisor'}:
            raise ValueError('The owned provider differs; preserve it for review')
        definitions['provider'] = {'operation': 'get_provider', 'creation_submitted': False,
                                   'requested_definition': clean(provider_body)}
    except NotFoundError:
        provider = (await models.create_provider(body=provider_body)).data()
        definitions['provider'] = {'operation': 'create_provider', 'creation_submitted': True,
                                   'request': clean(provider_body), 'response': clean(provider)}
    for _ in range(30):
        if provider.status.value == 'READY':
            break
        if provider.status.value == 'ERROR':
            raise RuntimeError('The owned model provider entered ERROR; preserve its native status')
        await asyncio.sleep(1)
        provider = (await models.get_provider(name=selected['provider'])).data()
    else:
        raise TimeoutError('The owned provider did not become ready within 30 seconds')
    definitions['provider']['ready_response'] = clean(provider)
    metadata = preset_metadata('dreamjob')
    body = CreateEnvironmentRequest(name=selected['environment'], description='Explicit public retail budget/weekend preset; no persona or salary',
        environment_spec=EnvironmentSpecInline(metadata=metadata, mcp={'catalogue': McpFulfillment(
            url='/workspace/.venv/bin/learning-lab-courses', env={
                'LAB_PREFERENCES_PRESET_FILE': '/workspace/scenarios/dreamjob/preferences.json',
                'LAB_PREFERENCES_PRESET_SHA256': metadata['preferences_sha256'], 'LAB_REQUIRE_PREFERENCES': '1',
                'LAB_MCP_EVIDENCE_FILE': '/workspace/artifacts/mcp-tools-list.jsonl'})}))
    try:
        stored = (await client.get_environment(name=selected['environment'])).data()
        if stored.environment_spec != body.environment_spec:
            raise ValueError('The owned environment differs; no replacement was attempted')
        definitions['environment'] = {'operation': 'get_environment', 'creation_submitted': False,
                                      'requested_definition': clean(body), 'response': clean(stored)}
    except NotFoundError:
        created = (await client.create_environment(body=body)).data()
        definitions['environment'] = {'operation': 'create_environment', 'creation_submitted': True,
                                      'request': clean(body), 'response': clean(created)}
    return {'run_id': args['run_id'], **selected, 'provider_status': str(provider.status),
            'environment_qualified': f"{client.workspace}/{selected['environment']}", 'public_preset': metadata,
            'model_alias': 'citizen-retail-advisor', 'inference_calls': 0,
            'native_resource_definitions': definitions}


async def cleanup(client, args):
    from nemo_agents_plugin.entities import ethos_fileset_name
    from nemo_helix_plugin.files.client import AsyncFilesClient
    from nemo_helix_plugin.models.client import AsyncModelsClient
    from nemo_helix_plugin.secrets.client import AsyncSecretsClient
    from nemo_helix_plugin.client.errors import NotFoundError
    selected = names(args['run_id'])
    agent = 'citizen-retail-' + uuid.UUID(args['run_id']).hex[:12] + '-agent'
    try:
        await client.get_agent(name=agent)
    except NotFoundError:
        pass
    else:
        raise RuntimeError('Retain owned provider/files until the agent registration is absent')
    files = AsyncFilesClient.from_client(client)
    removed = []
    for name, remove, get in [
        (ethos_fileset_name(agent), files.delete_fileset, files.get_fileset),
        (selected['environment'], client.delete_environment, client.get_environment),
        (selected['provider'], AsyncModelsClient.from_client(client).delete_provider, AsyncModelsClient.from_client(client).get_provider),
        (selected['secret'], AsyncSecretsClient.from_client(client).delete_secret, AsyncSecretsClient.from_client(client).get_secret),
    ]:
        try:
            await remove(name=name)
        except NotFoundError:
            pass
        try:
            await get(name=name)
        except NotFoundError:
            removed.append(name)
        else:
            raise RuntimeError('Owned resource absence is not confirmed: ' + name)
    return {'run_id': args['run_id'], 'absence_confirmed': True, 'removed': removed}
