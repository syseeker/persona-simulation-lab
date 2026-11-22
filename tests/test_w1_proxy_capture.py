"""Inspect proxy settings without model execution or disclosing inspected credentials."""
import hashlib
import json

import httpx
import pytest
import yaml

from learning_lab import proxy_capture


@pytest.fixture
def proxy_fixture(monkeypatch):
    secret = 'fixture-quote"and-backslash\\credential'
    config = {
        'model_list': [{'model_name': 'lab-advisor-fixed', 'litellm_params': {
            'model': 'os.environ/LAB_FIXED_MODEL', 'api_key': 'os.environ/LAB_FIXED_API_KEY'}}],
        'provider_note': {'nested': ['echo:' + secret, {'value': secret}]},
        'general_settings': {'master_key': 'os.environ/LAB_PROXY_API_KEY'},
    }
    raw = yaml.safe_dump(config).encode()
    observed = {
        'Id': 'fixture-container', 'Image': 'fixture-image',
        'NetworkSettings': {'Ports': {'4000/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '4000'}]}},
        'Config': {
            'Cmd': ['--config', '/app/lab/litellm.yaml', '--port', '4000'],
            'Env': ['LAB_PROXY_API_KEY=' + secret, 'LAB_FIXED_API_KEY=' + secret,
                    'LAB_FIXED_MODEL=openai/fixture-mounted-model'],
        },
    }
    calls = {'docker': [], 'http': []}

    async def docker(*args):
        calls['docker'].append(args)
        if args == ('inspect', 'proxy-litellm-1'):
            return json.dumps([observed]).encode()
        if args == ('exec', 'fixture-container', 'cat', '/app/lab/litellm.yaml'):
            return raw
        pytest.fail('Unexpected Docker operation: ' + repr(args))

    runtime = {'data': [{'model_name': 'lab-advisor-fixed', 'litellm_params': {
        'model': 'openai/fixture-runtime-model', 'api_key': secret},
        'diagnostic': [secret, {'nested': 'echo:' + secret}]}]}

    def respond(request):
        calls['http'].append(request)
        assert request.method == 'GET'
        assert request.url == httpx.URL('http://127.0.0.1:4000/model/info')
        assert request.headers['Authorization'] == 'Bearer ' + secret
        return httpx.Response(200, json=runtime)

    client_type = httpx.AsyncClient
    monkeypatch.setattr(proxy_capture, '_docker', docker)
    monkeypatch.setattr(proxy_capture.httpx, 'AsyncClient',
                        lambda **kwargs: client_type(transport=httpx.MockTransport(respond), **kwargs))
    return {'secret': secret, 'raw': raw, 'observed': observed, 'runtime': runtime,
            'calls': calls, 'client_type': client_type}


async def test_proxy_capture_redacts_escaped_credentials_in_nested_nonsensitive_fields(tmp_path, proxy_fixture):
    await proxy_capture.capture_proxy(tmp_path, 'http://127.0.0.1:4000/v1')
    captured = json.loads((tmp_path / 'litellm-effective-config.json').read_text())
    mounted = yaml.safe_load((tmp_path / 'litellm-loaded.yaml').read_text())
    assert mounted['provider_note']['nested'] == ['echo:[redacted]', {'value': '[redacted]'}]
    inventory = captured['runtime_model_inventory']['response']['data'][0]
    assert inventory['diagnostic'] == ['[redacted]', {'nested': 'echo:[redacted]'}]
    for value in (captured, mounted):
        assert proxy_fixture['secret'] not in json.dumps(value)
        assert proxy_fixture['secret'] not in str(value)
    assert len(proxy_fixture['calls']['http']) == 1
    assert captured['inference_calls'] == 0


async def test_proxy_capture_redacts_credentials_inside_json_encoded_diagnostics(tmp_path, proxy_fixture):
    proxy_fixture['runtime']['data'][0]['diagnostic_json'] = json.dumps({'note': proxy_fixture['secret']})
    await proxy_capture.capture_proxy(tmp_path, 'http://127.0.0.1:4000/v1')
    captured = json.loads((tmp_path / 'litellm-effective-config.json').read_text())
    diagnostic = captured['runtime_model_inventory']['response']['data'][0]['diagnostic_json']
    assert json.loads(diagnostic)['note'] == '[redacted]'


async def test_mounted_source_and_live_inventory_remain_separate_evidence(tmp_path, proxy_fixture):
    await proxy_capture.capture_proxy(tmp_path, 'http://127.0.0.1:4000/v1')
    captured = json.loads((tmp_path / 'litellm-effective-config.json').read_text())
    mounted = captured['settings_from_mounted_file_and_environment']['model_list'][0]['litellm_params']
    runtime = captured['runtime_model_inventory']
    assert mounted['model'] == 'openai/fixture-mounted-model'
    assert runtime['response']['data'][0]['litellm_params']['model'] == 'openai/fixture-runtime-model'
    assert runtime['source'] == 'GET /model/info'
    assert captured['loaded_sha256'] == hashlib.sha256(proxy_fixture['raw']).hexdigest()
    assert captured['copy_is_redacted_serialization'] is True
    assert 'do not alone prove startup-loaded memory' in captured['notice']
    assert proxy_fixture['calls']['docker'] == [
        ('inspect', 'proxy-litellm-1'),
        ('exec', 'fixture-container', 'cat', '/app/lab/litellm.yaml'),
    ]


@pytest.mark.parametrize('defect, message', [
    ('port', 'binding'), ('nonloopback', 'binding'), ('config', 'configuration'),
])
async def test_proxy_capture_rejects_wrong_container_boundary_before_read(tmp_path, proxy_fixture, defect, message):
    observed = proxy_fixture['observed']
    if defect == 'port':
        observed['NetworkSettings']['Ports']['4000/tcp'][0]['HostPort'] = '4999'
    elif defect == 'nonloopback':
        observed['NetworkSettings']['Ports']['4000/tcp'][0]['HostIp'] = '0.0.0.0'
    else:
        observed['Config']['Cmd'] = ['--config', '/different/unverified.yaml']
    with pytest.raises(ValueError, match=message):
        await proxy_capture.capture_proxy(tmp_path, 'http://127.0.0.1:4000/v1')
    assert proxy_fixture['calls']['docker'] == [('inspect', 'proxy-litellm-1')]
    assert proxy_fixture['calls']['http'] == []
    assert not list(tmp_path.iterdir())


async def test_proxy_runtime_inventory_denial_is_explicit_not_inferred_from_yaml(tmp_path, proxy_fixture, monkeypatch):
    def denied(request):
        assert request.method == 'GET' and request.url.path == '/model/info'
        return httpx.Response(403, json={'error': 'not authorized'})

    monkeypatch.setattr(proxy_capture.httpx, 'AsyncClient', lambda **kwargs:
                        proxy_fixture['client_type'](transport=httpx.MockTransport(denied), **kwargs))
    await proxy_capture.capture_proxy(tmp_path, 'http://127.0.0.1:4000/v1')
    captured = json.loads((tmp_path / 'litellm-effective-config.json').read_text())
    assert captured['runtime_model_inventory'] == {'availability': 'unavailable', 'http_status': 403}
    assert captured['inference_calls'] == 0
    assert captured['settings_from_mounted_file_and_environment']['model_list']


async def test_unsupported_proxy_does_not_inspect_any_container_or_call_api(tmp_path, proxy_fixture):
    await proxy_capture.capture_proxy(tmp_path, 'https://remote.example/v1')
    captured = json.loads((tmp_path / 'litellm-effective-config.json').read_text())
    assert captured['availability'] == 'unavailable'
    assert captured['inference_calls'] == 0
    assert proxy_fixture['calls'] == {'docker': [], 'http': []}
    assert not (tmp_path / 'litellm-loaded.yaml').exists()
