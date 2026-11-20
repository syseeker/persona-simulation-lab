"""Portable, allowlisted working-tree excerpts and repository-specific GitHub links."""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
from urllib.parse import quote, urlsplit

from .settings import ROOT

SOURCES = {
    'application': ('src/learning_lab/journey.py', 'class JourneyService'),
    'personas': ('src/learning_lab/datasets.py', 'def lock_personas'),
    'personas/Load source': ('src/learning_lab/datasets.py', 'def _dataset'),
    'personas/Sample & preview': ('src/learning_lab/datasets.py', 'def sample_personas'),
    'personas/Lock identity': ('src/learning_lab/datasets.py', 'def lock_personas'),
    'situation': ('src/learning_lab/stories.py', 'STORIES'),
    'usersim': ('src/learning_lab/simulation.py', 'async def hosted_episode'),
    'usersim/Activate profile': ('src/learning_lab/simulation.py', 'def prepare_rows'),
    'usersim/Learner message': ('src/learning_lab/journey.py', 'class PublicTarget'),
    'fabric': ('src/learning_lab/fabric_target.py', 'def build_config'),
    'fabric/Plan & doctor': ('src/learning_lab/fabric_target.py', 'async def __aenter__'),
    'fabric/Start runtime': ('src/learning_lab/sandbox_runtime.py', 'async def serve'),
    'deepagents': ('src/learning_lab/fabric_target.py', 'async def reply'),
    'deepagents/Application policy': ('src/learning_lab/target.py', 'def system_prompt'),
    'deepagents/Tool allowlist': ('src/learning_lab/fabric_target.py', 'def build_config'),
    'mcp': ('src/learning_lab/course_mcp.py', 'def search_courses'),
    'mcp/Get course details': ('src/learning_lab/course_mcp.py', 'def get_course_details'),
    'mcp/Read constraints': ('src/learning_lab/course_mcp.py', 'def bound_preferences'),
    'catalogue': ('src/learning_lab/catalogue.py', 'def all_courses'),
    'catalogue/Match constraints': ('src/learning_lab/catalogue.py', 'def search_courses'),
    'gateway': ('src/learning_lab/inference.py', 'async def complete'),
    'budget': ('src/learning_lab/inference.py', 'async def admit'),
    'litellm': ('integrations/proxy/litellm.yaml', ''),
    'providers': ('src/learning_lab/settings.py', 'def model_id'),
    'relay': ('src/learning_lab/fabric_target.py', 'config.enable_relay'),
    'relay/Native scopes': ('src/learning_lab/evidence.py', 'def relay_scopes'),
    'relay/Tool inputs / outputs': ('src/learning_lab/evidence.py', 'def native_tool_records'),
    'records': ('src/learning_lab/journey.py', 'def artifact'),
    'checks': ('src/learning_lab/journey_checks.py', 'def evaluate_photography'),
    'openshell': ('src/learning_lab/sandbox.py', 'class NativeSandbox'),
    'openshell/Network policy': ('integrations/openshell/policy.yaml', ''),
    'openshell/Access review': ('integrations/openshell/policy.yaml', ''),
    'standalone': ('src/learning_lab/sandbox.py', 'async def __aenter__'),
    'transport': ('src/learning_lab/sandbox_runtime.py', 'class ExecGateway'),
}

# Stable operation identifiers used by both levels of the teaching diagram.
# These are exact call sites, not a fallback to a vaguely related component.
OPERATIONS = {
    'persona.source': ('src/learning_lab/datasets.py', 'def _dataset'),
    'persona.select': ('src/learning_lab/datasets.py', 'def sample_personas'),
    'persona.lock': ('src/learning_lab/datasets.py', 'def lock_personas'),
    'situation.authored': ('src/learning_lab/stories.py', 'STORIES'),
    'situation.bind': ('src/learning_lab/simulation.py', 'def bind_scenario'),
    'designer.schema': ('integrations/designer/learning_preferences.py', 'def workbench_builder'),
    'designer.generate': ('integrations/designer/learning_preferences.py', 'def generate_workbench'),
    'designer.lineage': ('src/learning_lab/workbench.py', 'def validate_generated_payload'),
    'usersim.prepare': ('src/learning_lab/simulation.py', 'def prepare_rows'),
    'usersim.probe': ('src/learning_lab/probe.py', 'def get_user_system_prompt'),
    'usersim.loop': ('src/learning_lab/simulation.py', 'async def hosted_episode'),
    'usersim.finalize': ('src/learning_lab/simulation.py', 'return await runtime.finalize()'),
    'fabric.config': ('src/learning_lab/fabric_target.py', 'def build_config'),
    'fabric.plan': ('src/learning_lab/fabric_target.py', 'self.plan = self.fabric.plan'),
    'fabric.start': ('src/learning_lab/fabric_target.py', 'self.runtime = await self.fabric.start_runtime'),
    'fabric.invoke': ('src/learning_lab/fabric_target.py', 'result = await self.runtime.invoke'),
    'fabric.result': ('src/learning_lab/fabric_target.py', 'output = result.output.to_dict()'),
    'harness.context': ('src/learning_lab/fabric_target.py', 'config.add_mcp_server'),
    'harness.policy': ('src/learning_lab/target.py', 'def system_prompt'),
    'hermes.environment': ('src/learning_lab/runtime_profiles.py', 'def hermes_runtime_environment'),
    'mcp.search': ('src/learning_lab/course_mcp.py', 'def search_courses'),
    'mcp.details': ('src/learning_lab/course_mcp.py', 'def get_course_details'),
    'mcp.compare': ('src/learning_lab/course_mcp.py', 'def compare_courses'),
    'catalogue.freeze': ('src/learning_lab/catalogue.py', 'def freeze_catalogue'),
    'catalogue.facts': ('src/learning_lab/catalogue.py', 'def all_courses'),
    'models.admit': ('src/learning_lab/inference.py', 'async def admit'),
    'models.request': ('src/learning_lab/inference.py', 'async def complete'),
    'models.alias': ('integrations/proxy/litellm.yaml', 'model_list:'),
    'routing.policy': ('integrations/proxy/lab_routing.py', 'self.stage = StageRoutingPlugin'),
    'routing.decision': ('integrations/proxy/lab_routing.py', 'result = await self.stage.run'),
    'routing.receipt': ('integrations/proxy/lab_routing.py', 'async def async_post_call_response_headers_hook'),
    'relay.configure': ('src/learning_lab/fabric_target.py', 'config.enable_relay'),
    'relay.scopes': ('src/learning_lab/evidence.py', 'def relay_scopes'),
    'relay.tools': ('src/learning_lab/evidence.py', 'def native_tool_records'),
    'records.read': ('src/learning_lab/recordings.py', 'def trace'),
    'checks.evaluate': ('src/learning_lab/journey_checks.py', 'def evaluate_photography'),
    'checks.coverage': ('src/learning_lab/journey_checks.py', "'coverage':"),
    'helix.evaluate': ('integrations/helix/evaluate.py', 'def evaluate'),
    'platform.register': ('integrations/platform/bridge.py', 'response = await client.register_agent'),
    'platform.deploy': ('integrations/platform/bridge.py', 'await client.create_deployment'),
    'platform.session': ('integrations/platform/bridge.py', 'await client.create_session'),
    'platform.cleanup': ('integrations/platform/bridge.py', 'await client.delete_deployment'),
    'openshell.create': ('src/learning_lab/sandbox.py', 'async def __aenter__'),
    'openshell.policy': ('src/learning_lab/sandbox.py', 'policy_text ='),
    'openshell.execute': ('src/learning_lab/sandbox.py', 'self.process = await asyncio.create_subprocess_exec'),
    'openshell.probe': ('src/learning_lab/sandbox.py', 'async def probe_boundary'),
    'openshell.cleanup': ('src/learning_lab/sandbox.py', 'async def cleanup_native'),
    'openshell.yaml': ('integrations/openshell/policy.yaml', ''),
}


def _git(*args, binary=False):
    try:
        return subprocess.check_output(['git', *args], cwd=ROOT, timeout=3,
                                       stderr=subprocess.DEVNULL, text=not binary).strip()
    except (OSError, subprocess.SubprocessError):
        return b'' if binary else ''


def repository_url() -> str | None:
    value = os.getenv('LAB_REPOSITORY_URL') or _git('config', '--get', 'remote.origin.url')
    if value.startswith('git@'):
        value = 'https://' + value[4:].replace(':', '/', 1)
    parsed = urlsplit(value)
    path = parsed.path.removesuffix('.git').strip('/')
    if parsed.scheme != 'https' or not parsed.hostname or not re.fullmatch(r'[\w.-]+/[\w.-]+', path):
        return None
    # Never propagate userinfo, query parameters or embedded Git credentials.
    return f'https://{parsed.hostname}/{path}'


def operation_links(recorded_hashes: dict | None = None) -> dict:
    """Return links only; no snippets, caller-supplied paths or private payloads."""
    repository, revision = repository_url(), _git('rev-parse', 'HEAD')
    captured = recorded_hashes or {}
    files = {}
    result = {}
    for identity, (relative, symbol) in OPERATIONS.items():
        if relative not in files:
            try:
                current = (ROOT / relative).read_bytes()
                committed = subprocess.check_output(
                    ['git', 'show', f'HEAD:{relative}'], cwd=ROOT, timeout=3,
                    stderr=subprocess.DEVNULL,
                ) if revision else b''
                files[relative] = current, committed
            except (OSError, subprocess.SubprocessError):
                files[relative] = b'', b''
        current, committed = files[relative]
        lines = committed.decode(errors='replace').splitlines()
        line = next((i + 1 for i, text in enumerate(lines) if symbol in text), None) if symbol else 1
        available = bool(committed and line and repository and revision)
        digest = hashlib.sha256(committed).hexdigest() if committed else None
        match = 'not-captured' if relative not in captured else 'matched' if digest == captured[relative] else 'different'
        result[identity] = {
            'available': available, 'path': relative, 'symbol': symbol, 'line': line,
            'url': f'{repository}/blob/{revision}/{quote(relative)}#L{line}' if available else None,
            'revision': revision or None, 'recording_match': match,
            'working_tree_differs': bool(current != committed),
            'notice': ('Committed code matches the recorded source hash.' if match == 'matched'
                       else 'Current committed reference; the recording captured different source bytes.' if match == 'different'
                       else 'Current committed integration reference; no matching source hash was captured.'),
        }
    return result


def source_excerpt(component: str, module: str = '') -> dict:
    key = component + '/' + module if module else component
    if key not in SOURCES:
        key = component
    if key not in SOURCES:
        return {'available': False, 'component': component,
                'notice': 'This component is not implemented in the photography preset.'}
    relative, symbol = SOURCES[key]
    path = ROOT / relative
    lines = path.read_text().splitlines()
    line = next((i + 1 for i, text in enumerate(lines) if symbol and symbol in text), 1)
    revision = _git('rev-parse', 'HEAD') or None
    committed = _git('show', f'HEAD:{relative}', binary=True)
    current = path.read_bytes()
    repository = repository_url()
    published_file = bool(committed)
    old_lines = committed.decode(errors='replace').splitlines()
    old_line = next((i + 1 for i, text in enumerate(old_lines) if symbol and symbol in text), None)
    github = (f'{repository}/blob/{revision}/{quote(relative)}' + (f'#L{old_line}' if old_line else '')) if repository and revision and published_file else None
    start = max(0, line - 4)
    return {'available': True, 'component': component, 'path': relative, 'symbol': symbol,
            'line': line, 'start_line': start + 1, 'content': '\n'.join(lines[start:start + 100]),
            'sha256': hashlib.sha256(current).hexdigest(), 'revision': revision,
            'working_tree_differs': committed != current.strip(),
            'repository_url': repository, 'github_url': github,
            'github_ref_kind': 'last-committed-reference' if github else 'publication-pending',
            'github_notice': ('GitHub opens the committed reference; the excerpt is the current checkout.' if github
                              else 'This new implementation file needs publication before a direct GitHub code link can resolve.'),
            'recording_revision_notice': 'A saved run retains its own source hashes; current checkout code may differ.'}
