"""Read the selected local proxy's loaded settings without invoking a model.

Container inspection is never returned to the caller: only an allowlisted,
credential-redacted projection is retained in the private run directory.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from .evidence import sanitize, save_evidence
from .settings import ROOT


def resolve_settings(value, environment):
    if isinstance(value, dict):
        return {key: resolve_settings(item, environment) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_settings(item, environment) for item in value]
    if isinstance(value, str) and value.startswith('os.environ/'):
        name = value.removeprefix('os.environ/')
        if re.search(r'KEY|SECRET|TOKEN|PASSWORD', name, re.I):
            return {'environment': name, 'present': bool(environment.get(name)), 'value': '[redacted]'}
        return environment.get(name, '[unset: ' + name + ']')
    return value


async def _docker(*args):
    process = await asyncio.create_subprocess_exec('docker', *args,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        out, _ = await asyncio.wait_for(process.communicate(), 15)
    except BaseException:
        if process.returncode is None:
            process.kill()
        await process.wait()
        raise
    if process.returncode:
        raise RuntimeError('Selected proxy settings could not be inspected')
    return out


async def capture_proxy(folder: Path, endpoint: str):
    """Capture mounted bytes, container environment and authenticated runtime model inventory."""
    import yaml

    parsed = urlsplit(endpoint)
    names = {4000: 'proxy-litellm-1', 4001: 'citizen-retail-proxy-v1'}
    if parsed.hostname not in {'localhost', '127.0.0.1'} or parsed.port not in names:
        save_evidence(folder / 'litellm-effective-config.json', {
            'availability': 'unavailable', 'reason': 'No supported local proxy identity for selected endpoint',
            'inference_calls': 0})
        return
    observed = json.loads(await _docker('inspect', names[parsed.port]))[0]
    ports = observed.get('NetworkSettings', {}).get('Ports', {}).get('4000/tcp') or []
    if not any(p.get('HostPort') == str(parsed.port) and p.get('HostIp') in {'127.0.0.1', '::1'} for p in ports):
        raise ValueError('Proxy endpoint does not match inspected container binding')
    command = observed['Config'].get('Cmd') or []
    if '--config' not in command or command[command.index('--config') + 1] != '/app/lab/litellm.yaml':
        raise ValueError('Selected proxy does not use the expected loaded configuration')
    raw = await _docker('exec', observed['Id'], 'cat', '/app/lab/litellm.yaml')
    loaded = yaml.safe_load(raw)
    environment = dict(item.split('=', 1) for item in observed['Config']['Env'] if '=' in item)
    secrets = [value for key, value in environment.items()
               if re.search(r'KEY|SECRET|TOKEN|PASSWORD', key, re.I) and len(value) >= 8]

    def safe(value):
        def redact(item, depth=0):
            if depth > 25:
                return '[depth limit]'
            if isinstance(item, str):
                if item.lstrip().startswith(('{', '[')):
                    try:
                        decoded = json.loads(item)
                        if isinstance(decoded, (dict, list)):
                            return json.dumps(redact(decoded, depth + 1))
                    except ValueError:
                        pass
                for secret in secrets:
                    item = item.replace(secret, '[redacted]')
                return item
            if isinstance(item, dict):
                return {redact(key, depth + 1): redact(child, depth + 1) for key, child in item.items()}
            if isinstance(item, list):
                return [redact(child, depth + 1) for child in item]
            return item
        return redact(sanitize(value))

    safe_loaded = safe(loaded)
    runtime = {'availability': 'unavailable'}
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(endpoint.rstrip('/').removesuffix('/v1') + '/model/info',
            headers={'Authorization': 'Bearer ' + environment.get('LAB_PROXY_API_KEY', '')})
        if response.is_success:
            runtime = {'availability': 'exists', 'source': 'GET /model/info', 'response': safe(response.json())}
        else:
            runtime['http_status'] = response.status_code
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'litellm-loaded.yaml').write_text(yaml.safe_dump(safe_loaded, sort_keys=False))
    save_evidence(folder / 'litellm-effective-config.json', {
        'schema': 'citizen-proxy-capture/v1', 'availability': 'exists',
        'container_id': observed['Id'], 'image_id': observed['Image'],
        'loaded_path': '/app/lab/litellm.yaml', 'loaded_sha256': hashlib.sha256(raw).hexdigest(),
        'loaded_copy': 'litellm-loaded.yaml', 'copy_is_redacted_serialization': True,
        'settings_from_mounted_file_and_environment': safe(resolve_settings(loaded, environment)),
        'runtime_model_inventory': runtime,
        'definition': {'command': safe(command), 'port_bindings': ports,
                       'environment_names': sorted(environment)},
        'source_references': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                              for name in ['integrations/proxy/compose.yaml', 'integrations/proxy/lab_routing.py']},
        'notice': 'Mounted YAML and environment were inspected in this container. They do not alone prove startup-loaded memory; the separately identified runtime API response provides the live model inventory. Source references are current authored files.',
        'inference_calls': 0})
