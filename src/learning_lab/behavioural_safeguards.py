"""Public-boundary client for the isolated native Guardrails SDK process."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from .evidence import save_evidence
from .settings import ROOT


class BehaviouralSafeguards:
    def __init__(self, folder: Path, *, location='inside the application sandbox'):
        self.folder, self.process = folder, None
        self.location = location

    async def __aenter__(self):
        integration = ROOT / 'integrations/guardrails'
        python = integration / '.venv/bin/python'
        if not python.is_file():
            raise RuntimeError('Install the pinned isolated Guardrails environment before running this preset')
        self.folder.mkdir(parents=True, exist_ok=True)
        self.error = (self.folder / 'guardrails-stderr.log').open('ab')
        env = {k: v for k, v in os.environ.items() if k in {'PATH', 'HOME', 'LANG', 'PYTHONDONTWRITEBYTECODE'}}
        self.process = await asyncio.create_subprocess_exec(
            str(python), '-u', str(integration / 'runner.py'), env=env,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=self.error,
        )
        save_evidence(self.folder / 'guardrails-config.json', {
            'configuration': (integration / 'config.yml').read_text(),
            'colang': (integration / 'rails.co').read_text(),
            'location': self.location, 'model_generation': False,
        })
        return self

    async def check(self, boundary: str, content: str, *, purpose='public conversation') -> dict:
        if boundary not in {'input', 'output'}:
            raise ValueError('Unknown behavioural boundary')
        self.process.stdin.write((json.dumps({'boundary': boundary, 'content': content}) + '\n').encode())
        await self.process.stdin.drain()
        raw = await asyncio.wait_for(self.process.stdout.readline(), 30)
        if not raw:
            raise RuntimeError('The native Guardrails worker stopped; refusing unchecked execution')
        result = json.loads(raw)
        if result.get('error'):
            raise RuntimeError(result['error'])
        receipt = {**result['result'], 'purpose': purpose}
        save_evidence(self.folder / 'guardrails-decisions.jsonl', receipt, append=True)
        return receipt

    async def __aexit__(self, *args):
        if self.process:
            self.process.stdin.close()
            try:
                await asyncio.wait_for(self.process.wait(), 5)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
        if hasattr(self, 'error'):
            self.error.close()
