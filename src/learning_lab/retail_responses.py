"""Explicit application-owned retail presentation; never a model reply repair."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from typing import Literal
import uuid

from pydantic import BaseModel, ConfigDict

from .catalogue import Course, Preferences, all_courses
from .evidence import decode_native, save_evidence


class ResponseConfiguration(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    schema_version: Literal[1] = 1
    owner: Literal['application'] = 'application'
    rendering: Literal['validated-returned-course-facts-only'] = 'validated-returned-course-facts-only'
    maximum_words: Literal[180] = 180
    maximum_options: Literal[3] = 3
    inference_calls: Literal[0] = 0
    original_prose_semantically_certified: Literal[False] = False
    catalogue_sha256: str
    clarification: str = 'Ask missing total training budget/study days; salary establishes neither affordability nor eligibility.'
    clarification_dispatch: str = 'Before Fabric/model/tool execution for salary or partially supplied decision constraints; programme-information questions still use native tools.'
    tool_evidence: str = 'Successful native Relay or Helix Intake result; previous facts only for clarification.'
    unknowns: str = 'Unknown full costs, timetable, duration and personal eligibility remain unconfirmed.'
    guardrails_relationship: str = 'Application delivery policy, separate from native behavioural Guardrails.'


def _hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _words(text: str) -> int:
    return sum(bool(re.search(r'\w', token)) for token in text.split())


class RetailResponseBoundary:
    """Keep native proposals intact while delivering a clearly attributed factual view."""

    def __init__(self, folder: Path, catalogue: Path):
        self.folder, self.catalogue, self.turn = folder, catalogue, 0
        self.facts = {course.id: course for course in all_courses(catalogue)}
        self.returned: dict[str, Course] = {}
        self.provenance: dict[str, dict] = {}
        self.last_delivery_record: dict | None = None
        self.pending_delivery: dict | None = None
        self.configuration = ResponseConfiguration(catalogue_sha256=hashlib.sha256(catalogue.read_bytes()).hexdigest())
        save_evidence(folder / 'retail-response-config.json', self.configuration)

    def _course(self, value: dict) -> Course:
        if not isinstance(value, dict):
            raise ValueError('Native course result is not an object')
        value = dict(value)
        notes = value.pop('constraint_notes', [])
        if not isinstance(notes, list) or any(not isinstance(note, str) for note in notes):
            raise ValueError('Native course constraint notes are malformed')
        course = Course.model_validate(value)
        if course.weekdays is not None and any(day not in range(7) for day in course.weekdays):
            raise ValueError('Native course has invalid study days')
        original = self.facts.get(course.id)
        if original is None or original.model_dump(mode='json') != course.model_dump(mode='json'):
            raise ValueError('Native returned course fields do not match the frozen catalogue')
        return course

    def _tools(self, tools: list) -> tuple[dict[str, Course], list[dict]]:
        found, evidence = {}, []
        if not isinstance(tools, list):
            raise ValueError('Native tool evidence must be a list')
        for tool in tools:
            if not isinstance(tool, dict) or tool.get('name') not in {'search_courses', 'get_course_details', 'compare_courses'}:
                continue
            relay = tool.get('evidence_origin') == 'native_relay' and tool.get('status') == 'completed' and tool.get('scope_uuid')
            intake = (tool.get('evidence_origin') == 'native_helix_intake'
                      and tool.get('native_status') == 'success' and tool.get('source_span_id')
                      and tool.get('result_state') == 'returned')
            if not relay and not intake:
                raise ValueError('Course tool lacks successful attributable native evidence')
            payload = decode_native(tool.get('result'))
            if isinstance(payload, dict) and payload.get('error'):
                evidence.append({'name': tool['name'], 'origin': tool['evidence_origin'],
                    'native_id': tool.get('scope_uuid') or tool.get('source_span_id'),
                    'status': 'domain_error', 'source_ids': [], 'result_sha256': _hash(payload),
                    'error_kind': payload.get('error_kind'), 'error': payload['error']})
                continue
            if tool['name'] == 'search_courses':
                if not isinstance(payload, dict) or not isinstance(payload.get('matches'), list):
                    raise ValueError('Native search result has no matches list')
                values = [row['course'] for row in payload['matches'] if isinstance(row, dict) and 'course' in row]
                if len(values) != len(payload['matches']):
                    raise ValueError('Native search match has no course fields')
            elif tool['name'] == 'compare_courses':
                if not isinstance(payload, list) or not 2 <= len(payload) <= 3:
                    raise ValueError('Native comparison requires two or three returned courses')
                values = [row.get('text') if isinstance(row, dict) and row.get('type') == 'text' else row for row in payload]
                values = [decode_native(row) for row in values]
            else:
                values = [payload]
            courses = [self._course(value) for value in values]
            if len({course.id for course in courses}) != len(courses):
                raise ValueError('Native tool returned duplicate course identities')
            found.update({course.id: course for course in courses})
            evidence.append({'name': tool['name'], 'origin': tool['evidence_origin'],
                             'native_id': tool.get('scope_uuid') or tool.get('source_span_id'),
                             'status': 'returned', 'source_ids': [course.id for course in courses],
                             'result_sha256': _hash(payload)})
        return found, evidence

    @staticmethod
    def _duration(course: Course) -> str:
        parts = ([f'{course.duration_months} months'] if course.duration_months is not None else [])
        parts += [f'{course.duration_hours:g} hours'] if course.duration_hours is not None else []
        return ', '.join(parts) if parts else 'duration unconfirmed'

    @staticmethod
    def _fee(course: Course) -> str:
        if course.price_max_sgd is None:
            return 'full fee unconfirmed'
        value = 'S$' + f'{course.price_max_sgd:,.2f}'.rstrip('0').rstrip('.')
        if course.price_min_sgd is not None and course.price_min_sgd != course.price_max_sgd:
            value = 'S$' + f'{course.price_min_sgd:,.2f}'.rstrip('0').rstrip('.') + '–' + value
        if course.extra_cost_sgd is not None:
            value += f'; listed extra cost S${course.extra_cost_sgd:g}'
        return value

    def _programme(self, message: str, current: dict[str, Course]) -> tuple[str, list[Course]]:
        candidates = [course for course in current.values() if course.id.casefold() in message.casefold()
                      or course.title.casefold() in message.casefold()
                      or ('smu' in message.casefold() and 'smu' in course.provider.casefold())]
        if len(candidates) != 1:
            raise ValueError('Requested programme was not uniquely returned by the native tools')
        course = candidates[0]
        text = (f'{course.title} ({course.id}), {course.provider}.\n\n{course.summary}\n\n'
                f'Published full fee: {self._fee(course)}. Duration: {self._duration(course)}.\n\n'
                'Confirm additional costs, intake and study timetable with the provider. '
                'Personal funding eligibility is unknown.\n\n'
                f'Official source: {course.source_url}')
        return text, [course]

    def _clarify(self, preferences: Preferences) -> tuple[str, list[Course]]:
        missing = []
        if preferences.budget_sgd is None:
            missing.append('What is your total training budget in Singapore dollars?')
        if not preferences.days:
            missing.append('On which days of the week can you study?')
        text = ('Salary alone does not establish a training budget, affordability or funding eligibility. '
                + ' '.join(missing))
        # Previously returned facts provide context, never a new recommendation.
        course = next((course for course in self.returned.values() if course.id == 'SF-007'), None)
        if course:
            text += f'\n\nPreviously retrieved programme: {course.title} ({course.id}). Official source: {course.source_url}'
        return text, [course] if course else []

    def prepare_clarification(self, message: str, preferences: Preferences, *, thread_id: str) -> dict | None:
        """Ask for decision constraints before dispatch; never repair a native failure."""
        if self.pending_delivery is not None:
            raise ValueError('Previous retail delivery is still unconfirmed')
        missing = (["budget_sgd"] if preferences.budget_sgd is None else [])
        missing += ["days"] if not preferences.days else []
        salary_context = bool(re.search(r'\bsalary|\bincome|\bearn|\bmonthly pay|\bper month', message, re.I))
        if not missing or not (salary_context or preferences.budget_sgd is not None or preferences.days is not None):
            return None
        if hashlib.sha256(self.catalogue.read_bytes()).hexdigest() != self.configuration.catalogue_sha256:
            raise ValueError('Frozen catalogue changed before retail clarification')
        content, used = self._clarify(preferences)
        if _words(content) > self.configuration.maximum_words:
            raise ValueError('Application clarification exceeds the 180-word limit')
        self.turn += 1
        response_id = 'application-' + uuid.uuid4().hex
        decision = {'schema_version': 1, 'owner': 'application', 'public_turn': self.turn,
            'application_response_id': response_id, 'execution_kind': 'application_clarification',
            'agent_invoked': False, 'inference_calls': 0, 'missing_constraints': missing,
            'public_preferences': preferences.model_dump(mode='json'),
            'model_proposal_sha256': None, 'original_word_count': None,
            'model_proposal_rule_status': 'not_invoked', 'model_proposal_rule_failures': [],
            'model_proposal_semantically_certified': False,
            'response_origin': 'application_constraint_clarification',
            'delivered_word_count': _words(content),
            'delivered_content_sha256': hashlib.sha256(content.encode()).hexdigest(),
            'source_ids': [course.id for course in used],
            'source_hashes': {course.id: _hash(course.model_dump(mode='json')) for course in used},
            'source_provenance': {course.id: deepcopy(self.provenance[course.id]) for course in used},
            'native_tool_evidence': [], 'excluded_source_ids': [], 'status': 'validated'}
        candidate = {'content': content, 'thread_id': thread_id, 'public_turn': self.turn,
            'application_response_id': response_id, 'tools': [],
            'response_origin': decision['response_origin'], 'response_policy': decision,
            'preferences': preferences.model_dump(mode='json'),
            'outcome': {'status': 'valid', 'code': 'application_clarification',
                        'reason': 'The application asks for missing constraints before agent execution.'}}
        save_evidence(self.folder / 'retail-response-decisions.jsonl', decision, append=True)
        self.pending_delivery = {'candidate': deepcopy(candidate), 'decision': deepcopy(decision)}
        return candidate

    def _options(self, preferences: Preferences, current: dict[str, Course]) -> tuple[str, list[Course], list[str]]:
        if not preferences.days or any(day not in range(7) for day in preferences.days):
            raise ValueError('Study days must explicitly identify valid weekdays')
        candidates, excluded = [], []
        for course in current.values():
            over = course.price_max_sgd is not None and course.price_max_sgd + (course.extra_cost_sgd or 0) > preferences.budget_sgd
            conflict = course.weekdays is not None and not set(course.weekdays) <= set(preferences.days)
            if over or conflict or course.availability == 'closed':
                excluded.append(course.id)
            else:
                candidates.append(course)
        selected = candidates[:self.configuration.maximum_options]
        lines = ['Returned course facts for your stated budget and study days; fit remains unconfirmed.']
        for course in selected:
            days = ', '.join(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day]
                             for day in course.weekdays) if course.weekdays else 'unconfirmed'
            lines.append(f'- {course.title} ({course.id}), {course.provider}: {self._duration(course)}; '
                         f'published fee {self._fee(course)}; study days {days}. {course.source_url}')
        if not selected:
            lines.append('No returned option can be offered against these constraints; known conflicting options were excluded.')
        lines.append('Unknown fees, additional costs, timetables or places prevent a guaranteed fit. '
                     'Confirm full costs, study days, availability and personal funding eligibility with each provider.')
        return '\n\n'.join(lines), selected, excluded

    def apply(self, message: str, preferences: Preferences, result: dict) -> dict:
        if self.pending_delivery is not None:
            raise ValueError('Previous retail delivery is still unconfirmed')
        self.turn += 1
        original = result.get('content') if isinstance(result, dict) else None
        proposal = original if isinstance(original, str) else ''
        urls = {url.rstrip('.,;') for url in re.findall(r'https?://[^\s)\]>]+', proposal)}
        ids = set(re.findall(r'\b(?:CC|SF)-\d{3}\b', proposal))
        failures = []
        if _words(proposal) > self.configuration.maximum_words:
            failures.append('word_limit')
        if urls - {str(course.source_url) for course in self.facts.values()}:
            failures.append('unsupported_source_url')
        if ids - self.facts.keys():
            failures.append('unsupported_course_id')
        decision = {'schema_version': 1, 'public_turn': self.turn, 'owner': 'application',
                    'execution_kind': 'native_agent', 'agent_invoked': True,
                    'model_proposal_sha256': hashlib.sha256(proposal.encode()).hexdigest(),
                    'original_word_count': _words(proposal), 'model_proposal_rule_failures': failures,
                    'model_proposal_rule_status': 'failed' if failures else 'passed_selected_rules',
                    'model_proposal_rule_coverage': 'word limit + frozen catalogue URL/ID membership only; financial prose not semantically certified',
                    'model_proposal_semantically_certified': False, 'source_ids': [], 'source_hashes': {}}
        save_evidence(self.folder / 'retail-model-proposals.jsonl', {**decision, 'privacy': 'private',
            'original_content': original, 'native_identity': {key: result[key] for key in ['thread_id', 'fabric', 'outcome']
                if isinstance(result, dict) and key in result}}, append=True)
        try:
            if not isinstance(original, str) or not original.strip():
                raise ValueError('Native model proposal is missing or empty')
            outcome, fabric = result.get('outcome', {}), result.get('fabric', {})
            if not isinstance(outcome, dict) or not isinstance(fabric, dict):
                raise ValueError('Native model outcome metadata is malformed')
            if outcome.get('status', 'valid') != 'valid' or fabric.get('status', 'succeeded') != 'succeeded':
                raise ValueError('Native model proposal failed its upstream outcome')
            if result.get('finish_reason') == 'length':
                raise ValueError('Native model proposal was token-truncated')
            if hashlib.sha256(self.catalogue.read_bytes()).hexdigest() != self.configuration.catalogue_sha256:
                raise ValueError('Frozen catalogue changed during retail delivery')
            current, evidence = self._tools(result.get('tools', []))
            decision['native_tool_evidence'] = evidence
            if evidence and not any(row['status'] == 'returned' for row in evidence):
                raise ValueError('Native course tools returned only domain errors, with no usable result')
            self.returned.update(current)
            for course_id in current:
                self.provenance[course_id] = {'public_turn': self.turn,
                    'native_ids': [row['native_id'] for row in evidence if course_id in row['source_ids']]}
            salary_context = bool(re.search(r'\bsalary|\bincome|\bearn|\bmonthly pay|\bper month', message, re.I))
            missing = preferences.budget_sgd is None or preferences.days is None
            if missing and (salary_context or preferences.budget_sgd is not None or preferences.days is not None):
                if not evidence and not self.returned:
                    raise ValueError('Clarification has no current or previous native course evidence')
                content, used = self._clarify(preferences)
                mode, excluded = 'constraint_clarification', []
            else:
                if not evidence:
                    raise ValueError('Delivery has no successful current native course-tool evidence')
                if missing:
                    content, used = self._programme(message, current)
                    mode, excluded = 'source_summary', []
                else:
                    content, used, excluded = self._options(preferences, current)
                    mode = 'source_summary'
            delivered_urls = {url.rstrip('.,;') for url in re.findall(r'https?://[^\s)\]>]+', content)}
            decision.update(response_origin=f'application_{mode}',
                delivered_word_count=_words(content), delivered_content_sha256=hashlib.sha256(content.encode()).hexdigest(),
                source_ids=[course.id for course in used],
                source_hashes={course.id: _hash(course.model_dump(mode='json')) for course in used},
                source_provenance={course.id: self.provenance[course.id] for course in used},
                native_tool_evidence=evidence, excluded_source_ids=excluded)
            if delivered_urls - {str(course.source_url) for course in used} or _words(content) > self.configuration.maximum_words:
                raise ValueError('Application delivery violates the source allowlist or 180-word limit')
            decision['status'] = 'validated'
            save_evidence(self.folder / 'retail-response-decisions.jsonl', decision, append=True)
            delivered = deepcopy(result)
            delivered.update(content=content, response_origin=decision['response_origin'], response_policy=decision)
            self.pending_delivery = {'candidate': deepcopy(delivered), 'decision': deepcopy(decision)}
            return delivered
        except (ValueError, TypeError, KeyError) as exc:
            decision.update(status='rejected', error_type=type(exc).__name__, reason=str(exc))
            save_evidence(self.folder / 'retail-response-decisions.jsonl', decision, append=True)
            raise

    def confirm_delivery(self, result: dict) -> dict:
        """Acknowledge only after the caller's output safeguards permit delivery."""
        if self.pending_delivery is None:
            raise ValueError('There is no validated retail delivery to confirm')
        candidate = self.pending_delivery['candidate']
        decision = deepcopy(self.pending_delivery['decision'])
        content = result.get('content') if isinstance(result, dict) else None
        if (not isinstance(result, dict) or result != candidate or not isinstance(content, str)
                or hashlib.sha256(content.encode()).hexdigest() != decision['delivered_content_sha256']
                or result.get('response_origin') != decision['response_origin']
                or not isinstance(result.get('response_policy'), dict)
                or result['response_policy'].get('public_turn') != decision['public_turn']):
            raise ValueError('Retail delivery confirmation does not match the validated candidate')
        decision['status'] = 'delivered'
        save_evidence(self.folder / 'retail-response-decisions.jsonl', decision, append=True)
        confirmed = deepcopy(candidate)
        confirmed['response_policy'] = decision
        self.last_delivery_record = {'content': content, 'response_origin': decision['response_origin'],
                                     'public_turn': decision['public_turn']}
        self.pending_delivery = None
        return confirmed

    def reject_delivery(self, reason: str) -> None:
        """Retain a blocked candidate without acknowledging it as public output."""
        if self.pending_delivery is None:
            return
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError('Retail delivery rejection requires a reason')
        decision = {**self.pending_delivery['decision'], 'status': 'rejected', 'reason': reason}
        save_evidence(self.folder / 'retail-response-decisions.jsonl', decision, append=True)
        self.pending_delivery = None
