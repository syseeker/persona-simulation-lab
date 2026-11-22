"""Start a separately owned routing proxy without changing existing lab services."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import time

import httpx

from learning_lab.settings import ROOT, base_url, load_environment, model_id

NAME = 'citizen-retail-proxy-v1'
IMAGE = 'persona-lab-proxy:0.2.0'


def start():
    load_environment()
    key, nim = os.environ['LAB_PROXY_API_KEY'], os.environ['NVIDIA_API_KEY']
    models = {'FIXED': 'openai/' + model_id(), 'SUPPORT': 'openai/' + model_id('user'),
              'EFFICIENT': os.getenv('LAB_RETAIL_EFFICIENT_MODEL', 'openai/google/gemma-4-31b-it'),
              'CAPABLE': os.getenv('LAB_RETAIL_CAPABLE_MODEL', 'openai/z-ai/glm-5.3-flash')}
    config, plugin = ROOT / 'integrations/proxy/retail-litellm.yaml', ROOT / 'integrations/proxy/lab_routing.py'
    configuration_hash = hashlib.sha256(config.read_bytes() + plugin.read_bytes()).hexdigest()
    inspected = subprocess.run(['docker', 'inspect', NAME], capture_output=True)
    if inspected.returncode == 0:
        observed = json.loads(inspected.stdout)[0]
        labels = observed['Config'].get('Labels') or {}
        if labels.get('citizen.scope') != 'retail-routing' or labels.get('citizen.configuration') != configuration_hash:
            raise ValueError('Existing proxy identity/configuration differs; preserve it for explicit review')
        env = dict(item.split('=', 1) for item in observed['Config']['Env'] if '=' in item)
        if any(env.get('LAB_' + role + '_MODEL') != model for role, model in models.items()):
            raise ValueError('Existing retail model inventory differs; do not replace an owned service implicitly')
    else:
        env = {'LAB_PROXY_API_KEY': key, 'LITELLM_LOG': 'WARNING'}
        for role, model in models.items():
            env.update({f'LAB_{role}_MODEL': model, f'LAB_{role}_API_BASE': base_url(), f'LAB_{role}_API_KEY': nim})
        # The file is private, short-lived and never passed as Docker build input.
        with tempfile.NamedTemporaryFile(mode='w', prefix='citizen-retail-proxy-', dir=ROOT / '.private') as values:
            os.chmod(values.name, 0o600)
            values.write('\n'.join(f'{k}={v}' for k, v in env.items()) + '\n')
            values.flush()
            subprocess.run(['docker', 'run', '-d', '--name', NAME, '--label', 'citizen.scope=retail-routing',
                '--label', 'citizen.configuration=' + configuration_hash, '--env-file', values.name,
                '-p', '127.0.0.1:4001:4000', '-v', f'{config}:/app/lab/litellm.yaml:ro',
                '-v', f'{plugin}:/app/lab-plugin/lab_routing.py:ro', IMAGE,
                '--config', '/app/lab/litellm.yaml', '--port', '4000', '--host', '0.0.0.0'],
                check=True, stdout=subprocess.DEVNULL)
    for _ in range(40):
        try:
            response = httpx.get('http://127.0.0.1:4001/v1/models', headers={'Authorization': 'Bearer ' + key}, timeout=2)
            if response.is_success:
                aliases = {row['id'] for row in response.json()['data']}
                if {'lab-advisor-candidate', 'lab-advisor-capable', 'lab-advisor-routed', 'lab-advisor-fixed', 'lab-support'} <= aliases:
                    receipt = {'container': NAME, 'endpoint': 'http://127.0.0.1:4001/v1', 'models': models,
                        'configuration_sha256': configuration_hash, 'inference_calls': 0,
                        'notice': 'A separately owned service; model inventory is not proof of successful inference.'}
                    folder = ROOT / '.private/retail-proxy'
                    folder.mkdir(exist_ok=True)
                    (folder / 'service.json').write_text(json.dumps(receipt, indent=2))
                    return receipt
        except httpx.HTTPError:
            pass
        time.sleep(.5)
    raise RuntimeError('Retail proxy did not become ready; preserve its service logs')


if __name__ == '__main__':
    print(json.dumps(start()))
