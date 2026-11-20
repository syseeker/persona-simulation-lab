"""Standalone native OpenShell lifecycle and bounded Fabric control channel.

Only this condition's labelled sandbox may be deleted. Reading saved evidence
never calls this module. Existing Helix deployments and credentials are untouched.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import uuid

from .evidence import sanitize, save_evidence
from .runtime_profiles import openshell_binary
from .settings import ROOT

IMAGE = 'citizen-learning-advisor:0.3.0'
EXPORT_FILES = {'fabric-config.json', 'fabric-plan.json', 'fabric-doctor.json',
                'fabric-lifecycle.jsonl', 'reply-outcomes.jsonl', 'relay.jsonl'}


def native_environment() -> dict:
    """Native auth stays in OpenShell's store; inference keys are not inherited."""
    allowed = {'PATH', 'HOME', 'USER', 'LANG', 'SHELL', 'XDG_CONFIG_HOME', 'XDG_DATA_HOME',
               'OPENSHELL_GATEWAY', 'OPENSHELL_GATEWAY_ENDPOINT', 'OPENSHELL_WORKSPACE',
               'OPENSHELL_LOCAL_TLS_DIR', 'OPENSHELL_OIDC_CLIENT_ID', 'OPENSHELL_OIDC_CLIENT_SECRET'}
    env = {key: value for key, value in os.environ.items() if key in allowed}
    local = Path(os.getenv('LAB_OPENSHELL_STATE_DIR', str(ROOT / '.private/openshell')))
    if (local / 'config/openshell/active_gateway').is_file():
        env.setdefault('XDG_CONFIG_HOME', str(local / 'config'))
        env.setdefault('XDG_DATA_HOME', str(local / 'state'))
    env['OPENSHELL_NO_BROWSER'] = '1'
    env['OPENSHELL_COLOR'] = 'never'
    env['OPENSHELL_WORKSPACE'] = os.getenv('LAB_OPENSHELL_WORKSPACE', env.get('OPENSHELL_WORKSPACE', 'default'))
    return env


async def command(*args, input_bytes=None, timeout=40, env=None):
    process = await asyncio.create_subprocess_exec(*map(str, args), env=env,
              stdin=asyncio.subprocess.PIPE if input_bytes is not None else asyncio.subprocess.DEVNULL,
              stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        output, error = await asyncio.wait_for(process.communicate(input_bytes), timeout)
        return process.returncode, output.decode(errors='replace'), error.decode(errors='replace')
    except BaseException:
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), 3)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
        raise


async def native_readiness() -> dict:
    binary = openshell_binary()
    result = {'cli': bool(binary), 'gateway': False, 'image': False,
              'image_name': os.getenv('LAB_OPENSHELL_IMAGE', IMAGE), 'workspace': native_environment()['OPENSHELL_WORKSPACE']}
    if not binary:
        return {**result, 'reason': 'Install and configure OpenShell; see the deployment documentation.'}
    try:
        code, output, _ = await command(binary, '--version', env=native_environment(), timeout=8)
        result['version'] = output.strip() if code == 0 else None
        code, _, error = await command(binary, 'sandbox', 'list', '-o', 'json', env=native_environment(), timeout=8)
        result['gateway'] = code == 0
        if code:
            result['reason'] = sanitize(error[:400])
        code, output, _ = await command('docker', 'image', 'inspect', '--format', '{{.Id}}', result['image_name'], timeout=8)
        result.update(image=code == 0, image_id=output.strip() if code == 0 else None)
    except (OSError, asyncio.TimeoutError) as exc:
        result['reason'] = 'Native prerequisite unavailable: ' + type(exc).__name__
    return result


class NativeSandbox:
    def __init__(self, run_id: str, folder: Path, gateway, *, catalogue: Path):
        if str(uuid.UUID(run_id)) != run_id:
            raise ValueError('A canonical run identity is required')
        self.run_id, self.folder, self.gateway, self.catalogue = run_id, folder, gateway, catalogue
        # OpenShell 0.1.6 permits at most 19 characters. Full identity remains
        # in the mandatory ownership label and persisted receipt.
        self.name = 'cl-' + uuid.UUID(run_id).hex[:16]
        self.env = native_environment()
        self.binary = openshell_binary()
        self.process = self.reader = None
        self.pending, self.model_tasks, self.artifacts = {}, set(), {}
        self.identity = None
        self.thread_id = None
        self.closing = False
        self.image_verified = False
        self.creation_uncertain = False

    def event(self, event, **values):
        save_evidence(self.folder / 'sandbox-lifecycle.jsonl',
                      {'event': event, 'run_id': self.run_id, 'sandbox_name': self.name, **values}, append=True)

    async def cli(self, *args, timeout=40):
        if not self.binary:
            raise ValueError('OpenShell CLI is unavailable')
        code, output, error = await command(self.binary, *args, env=self.env, timeout=timeout)
        if code:
            raise RuntimeError('OpenShell ' + ' '.join(args[:2]) + ': ' + str(sanitize(error[:800])))
        return output

    async def __aenter__(self):
        self.folder.mkdir(parents=True, exist_ok=True)
        # Persist the intended name before native creation: a timeout may still
        # have created native state and must remain recoverable by exact identity.
        save_evidence(self.folder / 'sandbox-identity.json', {'run_id': self.run_id, 'name': self.name,
                      'workspace': self.env['OPENSHELL_WORKSPACE'], 'cleanup_confirmed': False})
        policy = ROOT / 'integrations/openshell/policy.yaml'
        (self.folder / 'requested-policy.yaml').write_bytes(policy.read_bytes())
        image = os.getenv('LAB_OPENSHELL_IMAGE', IMAGE)
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/:@-]{0,250}', image):
            raise ValueError('Choose a configured container image, not a filesystem path')
        self.event('creation_requested', image=image)
        try:
            creation = asyncio.create_task(self.cli('sandbox', 'create', '--name', self.name, '--from', image,
                           '--policy', str(policy), '--detach', '--no-tty', '--no-auto-providers',
                           '--approval-mode', 'manual', '--label', 'citizen.scope=journey',
                           '--label', 'citizen.run=' + self.run_id, '-o', 'json', '--', 'sleep', 'infinity'))
            try:
                # Cancellation must not abandon an in-flight native create RPC
                # and then report absence before that RPC finishes creating it.
                await asyncio.shield(creation)
            except asyncio.CancelledError:
                try:
                    await creation
                except BaseException:
                    self.creation_uncertain = True
                raise
            except BaseException:
                self.creation_uncertain = True
                raise
            raw = json.loads(await self.cli('sandbox', 'get', self.name, '-o', 'json'))
            sandbox = raw.get('sandbox', raw)
            self.identity = {k: sandbox.get(k) for k in ('id', 'name', 'phase', 'workspace',
                             'configuration_admission', 'current_policy_version', 'host_key_fingerprint')}
            save_evidence(self.folder / 'sandbox-identity.json', {'run_id': self.run_id, **self.identity})
            self.event('ready', **self.identity)
            policy_text = await self.cli('sandbox', 'get', self.name, '--policy-only')
            (self.folder / 'effective-policy.yaml').write_text(policy_text)
            policy_record = json.loads(await self.cli('policy', 'get', self.name, '--full', '-o', 'json'))
            save_evidence(self.folder / 'effective-policy.json', policy_record)
            await self.probe_boundary()
            self.stderr = (self.folder / 'sandbox-stderr.log').open('ab')
            self.process = await asyncio.create_subprocess_exec(str(self.binary), 'sandbox', 'exec', self.name,
                '--no-tty', '--no-login-shell', '--timeout', '900', '--',
                '/opt/lab/.venv/bin/python', '-u', '-m', 'learning_lab.sandbox_runtime',
                env=self.env, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=self.stderr, limit=4 * 1024 * 1024)
            self.reader = asyncio.create_task(self.read_messages())
            raw_catalogue = self.catalogue.read_text()
            from .settings import model_id
            receipt = await self.request('init', catalogue=raw_catalogue,
                        catalogue_sha256=hashlib.sha256(raw_catalogue.encode()).hexdigest(), model=model_id())
            manifest = receipt.get('image_manifest', {})
            required = ['src/learning_lab/' + name for name in (
                'fabric_target.py', 'sandbox_runtime.py', 'inference.py', 'course_mcp.py',
                'catalogue.py', 'target.py', 'evidence.py', 'settings.py')]
            required += ['uv.lock', 'runtime-skills/course-advisor/SKILL.md']
            if manifest.get('version') != 1 or any(
                manifest.get('files', {}).get(relative) != hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
                for relative in required
            ):
                raise ValueError('The installed image does not match the current runtime sources; rebuild it before inference')
            self.image_verified = True
            self.thread_id = receipt['thread_id']
            save_evidence(self.folder / 'runtime-receipt.json', receipt)
            self.event('runtime_started', thread_id=self.thread_id)
            return self
        except BaseException:
            await self.close()
            raise

    async def send(self, value):
        if not self.process or self.process.returncode is not None:
            raise RuntimeError('The native sandbox exec process stopped')
        self.process.stdin.write((json.dumps(value) + '\n').encode())
        await self.process.stdin.drain()

    async def request(self, method, **params):
        key = str(uuid.uuid4())
        future = asyncio.get_running_loop().create_future()
        self.pending[key] = future
        try:
            await self.send({'id': key, 'method': method, **params})
            return await asyncio.wait_for(future, 150 if method == 'invoke' else 90)
        finally:
            self.pending.pop(key, None)

    async def model(self, message):
        try:
            if self.closing or not self.image_verified:
                raise RuntimeError('This workload is closing or its image is unverified; no model call was admitted')
            result = await self.gateway.complete(message['payload'], role='assistant')
            self.gateway.budget.records[-1].update(control_request_id=message['id'],
                                                  thread_id=self.thread_id, transport='openshell-native-exec')
            await self.send({'type': 'model_result', 'id': message['id'], 'result': result})
        except Exception as exc:
            await self.send({'type': 'model_result', 'id': message['id'],
                             'error': str(sanitize(str(exc)))[:800]})

    def artifact(self, message):
        relative = message['path']
        name = PurePosixPath(relative)
        if (relative != str(name) or name.is_absolute() or '..' in name.parts or '\\' in relative
                or name.name not in EXPORT_FILES or len(name.parts) > 3):
            raise ValueError('Invalid native artifact identifier')
        path = self.folder / 'native' / relative
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p.is_relative_to(self.folder)):
            raise ValueError('Symbolic native artifact paths are not accepted')
        path.parent.mkdir(parents=True, exist_ok=True)
        part = path.with_suffix(path.suffix + '.part')
        offset = message['offset']
        raw = base64.b64decode(message['data'], validate=True)
        if message['bytes'] > 64 * 1024 * 1024 or len(raw) > 48 * 1024:
            raise ValueError('Native artifact exceeds the declared bound')
        if offset == 0:
            part.write_bytes(raw)
        elif part.is_file() and part.stat().st_size == offset:
            with part.open('ab') as stream:
                stream.write(raw)
        else:
            raise ValueError('Native artifact chunks are incomplete')
        if part.stat().st_size == message['bytes']:
            if hashlib.sha256(part.read_bytes()).hexdigest() != message['sha256']:
                raise ValueError('Native artifact checksum mismatch')
            part.replace(path)
            self.artifacts[relative] = message['sha256']

    async def read_messages(self):
        try:
            while line := await self.process.stdout.readline():
                message = json.loads(line)
                if message.get('type') == 'model_call':
                    task = asyncio.create_task(self.model(message))
                    self.model_tasks.add(task)
                    task.add_done_callback(self.model_tasks.discard)
                elif message.get('type') == 'artifact':
                    self.artifact(message)
                else:
                    future = self.pending.get(message.get('id'))
                    if future and not future.done():
                        if message.get('error'):
                            future.set_exception(RuntimeError(message['error']))
                        else:
                            future.set_result(message['result'])
            if not self.closing:
                raise RuntimeError('Native exec stopped before completing the workload')
        except BaseException as exc:
            for future in self.pending.values():
                if not future.done():
                    future.set_exception(RuntimeError('Native control channel failed: ' + type(exc).__name__))
            if not isinstance(exc, asyncio.CancelledError):
                self.event('control_channel_failed', error_type=type(exc).__name__)

    async def reply(self, message, preferences):
        self.gateway.tool_rounds = 0
        return await self.request('invoke', message=message, preferences=preferences.model_dump(mode='json'))

    async def probe_boundary(self):
        script = '''import json,errno,socket
results=[]
try:
 open('/lab-denied.txt').read(); results.append({'probe':'world-readable-file-outside-policy','denied':False})
except OSError as e: results.append({'probe':'world-readable-file-outside-policy','denied':e.errno in (errno.EACCES,errno.EPERM),'errno':e.errno})
try:
 s=socket.create_connection(('1.1.1.1',443),timeout=3);s.close();results.append({'probe':'unlisted-network-egress','denied':False})
except OSError as e: results.append({'probe':'unlisted-network-egress','denied':e.errno in (errno.EACCES,errno.EPERM),'errno':e.errno,'error_type':type(e).__name__})
print(json.dumps({'probes':results}))'''
        result = json.loads(await self.cli('sandbox', 'exec', self.name, '--no-login-shell', '--timeout', '10',
                            '--', '/opt/lab/.venv/bin/python', '-c', script, timeout=15))
        save_evidence(self.folder / 'boundary-probes.json', result)
        if not all(row['denied'] for row in result['probes']):
            raise RuntimeError('Native policy-denial probes did not establish both boundaries; inspect the saved evidence')

    async def close(self):
        self.closing = True
        for task in list(self.model_tasks):
            task.cancel()
        await asyncio.gather(*self.model_tasks, return_exceptions=True)
        if self.process and self.process.returncode is None:
            try:
                await self.request('close')
            except Exception as exc:
                self.event('runtime_close_failed', error_type=type(exc).__name__)
            self.process.stdin.close()
            try:
                await asyncio.wait_for(self.process.wait(), 8)
            except asyncio.TimeoutError:
                self.process.terminate()
                await self.process.wait()
        if self.reader:
            self.reader.cancel()
            await asyncio.gather(self.reader, return_exceptions=True)
        if hasattr(self, 'stderr'):
            self.stderr.close()
        await self.cleanup_native()

    async def cleanup_native(self):
        inventory = json.loads(await self.cli('sandbox', 'list', '-o', 'json', timeout=12))
        item = next((s for s in inventory.get('sandboxes', []) if s.get('name') == self.name), None)
        if item:
            if item.get('labels', {}).get('citizen.run') != self.run_id or item.get('labels', {}).get('citizen.scope') != 'journey':
                raise ValueError('Native cleanup refused a sandbox not owned by this condition')
            if self.identity and self.identity.get('id') and item.get('id') != self.identity['id']:
                raise ValueError('Native sandbox identity changed; automatic cleanup refused')
            await self.cli('sandbox', 'delete', self.name, timeout=25)
        for _ in range(10):
            inventory = json.loads(await self.cli('sandbox', 'list', '-o', 'json', timeout=8))
            if not any(s.get('name') == self.name for s in inventory.get('sandboxes', [])):
                if self.creation_uncertain and not item:
                    raise RuntimeError('Native creation ended ambiguously; explicit recovery must verify absence before releasing ownership')
                save_evidence(self.folder / 'cleanup.json', {'run_id': self.run_id, 'sandbox_name': self.name,
                              'native_absence_confirmed': True, 'runtime_process_exited': not self.process or self.process.returncode is not None,
                              'native_artifact_sha256': self.artifacts})
                self.event('cleanup_confirmed')
                return
            await asyncio.sleep(1)
        raise RuntimeError('Native cleanup is not confirmed; the run guard remains for recovery')

    async def __aexit__(self, *_):
        await self.close()
