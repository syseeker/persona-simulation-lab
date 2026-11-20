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
