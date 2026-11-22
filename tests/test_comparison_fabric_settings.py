"""Offline regression through installed Fabric normalization and provider payloads."""
import asyncio
import json

import httpx
from nemo_fabric import Fabric
from nemo_fabric_adapter_contract.models import AgentConfig
from nemo_fabric_adapters.deepagents.adapter import build_chat_model, selected_model_config
import pytest

from learning_lab.fabric_target import build_config
from learning_lab.inference import Budget, Gateway


COMPARISONS = [
    ('lab-advisor-candidate', 'fixed'),
    ('lab-advisor-capable', 'fixed'),
    ('lab-advisor-routed', 'switchyard'),
]
BASELINE_MODEL = 'nvidia/nemotron-3.5-lightning-30b-a3b'


@pytest.mark.parametrize('model,route', COMPARISONS)
def test_comparison_typed_config_omits_shared_effort_before_fabric_normalization(tmp_path, model, route):
    configuration = build_config(tmp_path / 'workspace', model, 'http://fixture.invalid/v1',
                                 model_route=route, relay=False)
    assert configuration.harness.adapter_id == 'nvidia.fabric.langchain.deepagents'
    assert 'reasoning_effort' not in configuration.harness.settings
    assert configuration.models['default'].temperature == 0
    assert configuration.models['default'].max_tokens == 1024
    plan = Fabric().plan(configuration, base_dir=tmp_path)
    native = AgentConfig.from_mapping(plan.agent_config)
    settings = native.harness.settings if native.harness else {}
    assert 'reasoning_effort' not in settings
    assert selected_model_config(native).model == model


@pytest.mark.parametrize('model', [BASELINE_MODEL, 'unrelated-vendor/unrelated-model'])
def test_noncomparison_deepagents_preserves_existing_effort_configuration(tmp_path, model):
    configuration = build_config(tmp_path / 'workspace', model, 'http://fixture.invalid/v1', relay=False)
    assert configuration.harness.settings == {'reasoning_effort': 'none'}
    native = AgentConfig.from_mapping(Fabric().plan(configuration, base_dir=tmp_path).agent_config)
    assert native.harness.settings == {'reasoning_effort': 'none'}


@pytest.mark.parametrize('model', [BASELINE_MODEL, *[model for model, _route in COMPARISONS]])
def test_hermes_native_policy_remains_unchanged_even_when_model_is_comparison_alias(tmp_path, model):
    configuration = build_config(tmp_path / 'workspace', model, 'http://fixture.invalid/v1',
                                 harness='hermes', relay=False)
    assert configuration.harness.adapter_id == 'nvidia.fabric.hermes'
    assert configuration.harness.settings == {
        'reasoning_config': {'enabled': False, 'effort': 'none'}, 'save_trajectories': False}


@pytest.mark.parametrize('model,route', [*COMPARISONS, (BASELINE_MODEL, 'fixed')])
async def test_installed_adapter_and_gateway_forward_actual_comparison_payload_without_none(
    tmp_path, monkeypatch, model, route,
):
    from learning_lab import inference

    monkeypatch.setenv('LAB_GATEWAY_KEY', 'offline-adapter-fixture-key')
    monkeypatch.setenv('LAB_PROXY_API_KEY', 'offline-proxy-fixture-key')
    monkeypatch.setattr(inference, 'load_environment', lambda: None)
    configuration = build_config(tmp_path / 'workspace', model, 'http://fabric-fixture.invalid/v1',
                                 model_route=route, relay=False)
    plan = Fabric().plan(configuration, base_dir=tmp_path)
    native = AgentConfig.from_mapping(plan.agent_config)
    settings = native.harness.settings if native.harness else {}
    chat_model, selected, endpoint = build_chat_model(selected_model_config(native), settings)
    assert selected == model and endpoint == 'http://fabric-fixture.invalid/v1'
    adapter_requests, provider_requests = [], []
    comparison = model.startswith('lab-advisor-')
    gateway = Gateway(Budget(), proxy_url='http://provider-fixture.invalid/v1', model_route=route,
                      assistant_alias=model if comparison else None, evidence_dir=tmp_path / 'gateway')

    async def provider_transport(request):
        assert str(request.url) == 'http://provider-fixture.invalid/v1/chat/completions'
        body = json.loads(request.content)
        provider_requests.append(body)
        return httpx.Response(200, json={
            'id': 'offline-chat-completion', 'object': 'chat.completion', 'created': 1,
            'model': body['model'], 'choices': [{'index': 0, 'finish_reason': 'stop',
                'message': {'role': 'assistant', 'content': 'Offline transport fixture answer.'}}],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5, 'total_tokens': 15},
        })

    async def gateway_transport(request):
        assert str(request.url) == 'http://fabric-fixture.invalid/v1/chat/completions'
        body = json.loads(request.content)
        adapter_requests.append(body)
        return httpx.Response(200, json=await gateway.complete(body))

    original_client = chat_model.root_async_client
    await gateway._client.aclose()
    try:
        async with httpx.AsyncClient(transport=httpx.MockTransport(provider_transport)) as provider_client:
            gateway._client = provider_client
            async with httpx.AsyncClient(transport=httpx.MockTransport(gateway_transport)) as adapter_client:
                replacement = original_client.with_options(http_client=adapter_client)
                chat_model.root_async_client = replacement
                chat_model.async_client = replacement.chat.completions
                reply = await asyncio.wait_for(
                    chat_model.ainvoke('An entirely public offline fixture request.'), timeout=3)
                assert reply.content == 'Offline transport fixture answer.'
        assert len(adapter_requests) == len(provider_requests) == gateway.budget.calls == 1
        for body in [adapter_requests[0], provider_requests[0]]:
            if comparison:
                assert 'reasoning_effort' not in body
            else:
                assert body['reasoning_effort'] == 'none'
            assert body['temperature'] == 0
        assert provider_requests[0]['max_tokens'] == 1024
        assert 'max_completion_tokens' not in provider_requests[0]
        assert provider_requests[0]['model'] == (model if comparison else 'lab-advisor-fixed')
        assert gateway.budget.records[0]['status'] == 'completed'
    finally:
        await original_client.close()
        chat_model.root_client.close()
