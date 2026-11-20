"""Scenario 3 situations and public constraints; private overlays never enter tools."""
from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import uuid

from .catalogue import Course, Preferences, all_courses
from .datasets import canonical_json
from .evidence import save_evidence
from .settings import ROOT, model_id

OVERLAY_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'properties': {
        'preferred_brands': {'type': 'array', 'items': {'type': 'string', 'enum': ['UNIQLO', 'Decathlon']},
                             'minItems': 1, 'maxItems': 2, 'uniqueItems': True},
        'monthly_salary_range_sgd': {'type': 'string', 'enum': ['2500-3499']},
        'learning_situation': {'type': 'string', 'minLength': 20, 'maxLength': 800},
    },
    'required': ['preferred_brands', 'monthly_salary_range_sgd', 'learning_situation'],
}


def freeze_retail_catalogue(path: Path) -> str:
    base = json.loads((ROOT / 'catalogue/courses.json').read_text())
    supplement = json.loads((ROOT / 'catalogue/retail-supplement.json').read_text())
    base['courses'] += [Course.model_validate(c).model_dump(mode='json') for c in supplement['courses']]
    base['notice'] = 'Mixed dated sources: inspect each course captured_on; Scenario 3 adds the verified SMU listing.'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(base, indent=2) + '\n')
    all_courses(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_retail_overlay(fields: dict, original: dict):
    from .designer_schema import validate_json_schema
    validate_json_schema(fields, OVERLAY_SCHEMA)
    situation = fields['learning_situation']
    if re.search(r'\d|salary|income|budget|spend|funding|eligible', situation, re.I):
        raise ValueError('Designer learning_situation must describe skills; money/disclosure constraints belong to the separate authored protocol')
    for key in ['first_name', 'middle_name', 'last_name']:
        name = str(original.get(key) or '').strip()
        if name and re.search(r'(?<!\w)' + re.escape(name) + r'(?!\w)', situation, re.I):
            raise ValueError('Designer learning_situation must not copy an original profile name')


async def create_retail_situation(lock: dict, folder: Path, gateway) -> dict:
    """One native source-seeded structured generation in the isolated Designer SDK."""
    from .workbench import designer_endpoint

    original = lock['records'][0]
    request = {'original_profile_json': canonical_json(original['profile']),
               'original_profile_sha256': original['original_profile_sha256'], 'schema': OVERLAY_SCHEMA}
    private = folder / 'designer-private'
    private.mkdir()
    input_path, output_path = private / 'request.json', private / 'native.json'
    input_path.write_text(json.dumps(request))
    env = {k: v for k, v in os.environ.items() if not re.search(r'KEY|TOKEN|SECRET|PASSWORD', k, re.I)}
    env.update(LAB_DESIGNER_GATEWAY_KEY=gateway.key, LAB_DESIGNER_MODEL=model_id('designer'))
    before = gateway.budget.calls
    async with designer_endpoint(gateway) as endpoint:
        env['LAB_DESIGNER_GATEWAY_URL'] = endpoint
        process = await asyncio.create_subprocess_exec(
            str(ROOT / 'integrations/designer/.venv/bin/python'),
            str(ROOT / 'integrations/designer/retail_situation.py'), str(input_path), str(output_path),
            env=env, cwd=ROOT, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            out, error = await asyncio.wait_for(process.communicate(), 300)
        except BaseException:
            process.kill()
            await process.wait()
            raise
    (private / 'generation.log').write_bytes((out + b'\n' + error).replace(gateway.key.encode(), b'[REDACTED]'))
    if process.returncode:
        raise RuntimeError('Native retail Designer generation failed; inspect the private generation log and usage')
    payload = json.loads(output_path.read_text())
    if payload['original_profile_sha256'] != original['original_profile_sha256']:
        raise ValueError('Designer seed identity changed')
    fields = payload['fields']
    validate_retail_overlay(fields, original['profile'])
    if gateway.budget.calls <= before:
        raise ValueError('No attributable native Designer model call was recorded')
    overlay_id = str(uuid.uuid4())
    overlay = {'id': overlay_id, 'hypothesis': True, 'fields': fields,
               'original_profile_sha256': original['original_profile_sha256'],
               'selected_as_input': True, 'disclosure': {'salary': 'public turn 2', 'budget_and_schedule': 'public turn 3'}}
    save_evidence(folder / 'designer-output.json', overlay)
    save_evidence(folder / 'designer-configuration.json', {'engine': payload['engine'], 'schema': OVERLAY_SCHEMA,
        'column': 'retail_situation', 'sdk_call': 'DataDesigner.create', 'seed_count': 1,
        'seed_sha256': original['original_profile_sha256'], 'model': model_id('designer'),
        'configuration_sha256': payload['configuration_sha256']})
    save_evidence(folder / 'designer-generation.json', {'engine': payload['engine'], 'version': payload['version'],
        'model_calls': gateway.budget.calls - before, 'native_output_sha256': hashlib.sha256(output_path.read_bytes()).hexdigest(),
        'warnings': payload['warnings'], 'record_count': 1})
    save_evidence(folder / 'designer-lineage.json', {'original_sha256': original['original_profile_sha256'],
        'source': original['source'], 'source_revision': original['source_revision'], 'overlay_id': overlay_id,
        'derived_sha256': hashlib.sha256(canonical_json(overlay).encode()).hexdigest(),
        'original_preserved': canonical_json(lock['rows'][0]) == request['original_profile_json'],
        'explicit_selection': True, 'private_context_is_not_advisor_input': True})
    selected = copy.deepcopy(lock)
    selected['overlays'] = {original['source_id']: {'hypothesis': True, 'generated_fields': fields,
                          'overlay_id': overlay_id, 'original_profile_sha256': original['original_profile_sha256']}}
    return selected


class RetailPublicContext:
    """Accumulate only facts actually stated in the public conversation."""
    def __init__(self, folder: Path):
        self.folder, self.turn, self.messages = folder, 0, []
        self.salary_disclosed, self.budget, self.days = False, None, None

    def accept(self, message: str) -> Preferences:
        if self.turn == 0 and not re.search(r'retail|sales|inventory|data|visuali[sz]|SMU|Excel', message, re.I):
            raise ValueError('The public opening did not express a retail-learning goal')
        self.turn += 1
        self.messages.append(message)
        salary = bool(re.search(r'(?:salary|earn|income|pay).{0,70}(?:2,?500|3,?499)|(?:2,?500).{0,35}(?:3,?499)', message, re.I))
        self.salary_disclosed |= salary
        amount = re.search(r'(?:budget|spending limit|spend|maximum|cap).{0,45}?(?:S\$|SGD\s*|\$)\s*([\d,]+(?:\.\d+)?)', message, re.I)
        if amount:
            self.budget = float(amount[1].replace(',', ''))
        if re.search(r'weekends?|Saturday.{0,12}Sunday', message, re.I):
            self.days = [5, 6]
        prefs = Preferences(goal='retail sales inventory data analytics visualisation Excel', budget_sgd=self.budget, days=self.days)
        save_evidence(self.folder / 'public-constraints.jsonl', {'turn': self.turn,
            'basis': 'public conversation only; salary is never converted to a training budget',
            'message_sha256': hashlib.sha256(message.encode()).hexdigest(),
            'salary_publicly_disclosed': self.salary_disclosed, 'preferences': prefs.model_dump(mode='json')}, append=True)
        return prefs

    async def audit(self, payload: dict, role: str, record: dict):
        if role != 'assistant':
            return
        raw = json.dumps(payload, ensure_ascii=False)
        contains = bool(re.search(r'2,?500|3,?499', raw))
        valid = self.salary_disclosed or not contains
        save_evidence(self.folder / 'disclosure-audit.jsonl', {'call': record['call'], 'public_turn': self.turn,
            'public_salary_disclosed': self.salary_disclosed, 'salary_band_in_request': contains,
            'boundary_passed': valid, 'request_sha256': hashlib.sha256(raw.encode()).hexdigest(),
            'coverage': 'Actual provider-bound request checked for the selected hidden salary-band values; other public constraints are recorded separately.'}, append=True)
        if not valid:
            raise ValueError('Private salary reached an advisor request before public disclosure; dispatch denied')
