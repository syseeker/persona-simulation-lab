"""Isolated native Guardrails validation; stdin is public text, never persona state."""
from __future__ import annotations

import asyncio
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import re
import sys

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.actions import action
from nemoguardrails.rails.llm.options import RailType

HERE = Path(__file__).resolve().parent


async def serve():
    output, sys.stdout = sys.stdout, sys.stderr
    actions = []

    @action(name='citizen_input_allowed', is_system_action=True)
    async def input_allowed(context):
        text = context.get('user_message', '')
        blocked = bool(re.search(r'\b(?:show|reveal|print|disclose|give|send|dump)\b.{0,100}\b(?:api[ _-]?keys?|credentials?|secrets?|passwords?|tokens?)\b', text, re.I | re.S))
        actions.append({'action': 'citizen_input_allowed', 'allowed': not blocked,
                        'rule': 'credential-disclosure request pattern'})
        return not blocked

    @action(name='citizen_output_allowed', is_system_action=True)
    async def output_allowed(context):
        text = context.get('bot_message', '')
        blocked = bool(re.search(r'\b(?:sk-[A-Za-z0-9_-]{16,}|you (?:are guaranteed|will definitely get) (?:a job|hired)|this course guarantees (?:a job|employment))\b', text, re.I))
        actions.append({'action': 'citizen_output_allowed', 'allowed': not blocked,
                        'rule': 'credential-shaped output and selected employment-assurance phrases'})
        return not blocked

    config = RailsConfig.from_content(yaml_content=(HERE / 'config.yml').read_text(),
                                     colang_content=(HERE / 'rails.co').read_text())
    rails = LLMRails(config)
    rails.register_action(input_allowed)
    rails.register_action(output_allowed)
    files = {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in ('config.yml', 'rails.co', 'runner.py')}
    for line in sys.stdin:
        try:
            if len(line) > 1024 * 1024:
                raise ValueError('Public guardrail input exceeds the limit')
            request = json.loads(line)
            boundary = request['boundary']
            if boundary not in {'input', 'output'} or not isinstance(request['content'], str):
                raise ValueError('Choose the public input or output boundary')
            actions.clear()
            result = await rails.check_async(
                [{'role': 'user' if boundary == 'input' else 'assistant', 'content': request['content']}],
                rail_types=[RailType.INPUT if boundary == 'input' else RailType.OUTPUT],
            )
            if not actions:
                raise RuntimeError('The configured native rail did not execute its policy action')
            receipt = {'sdk': 'nemoguardrails', 'version': version('nemoguardrails'),
                       'api': 'LLMRails.check_async', 'boundary': boundary,
                       'native_result': result.model_dump(mode='json'), 'actions': list(actions),
                       'configuration_sha256': files, 'model_calls': 0,
                       'coverage': 'Native Colang execution with application-owned deterministic rules; not a general safety classifier.'}
            output.write(json.dumps({'result': receipt}) + '\n')
        except Exception as exc:
            output.write(json.dumps({'error': type(exc).__name__ + ': ' + str(exc)[:600]}) + '\n')
        output.flush()


if __name__ == '__main__':
    asyncio.run(serve())
